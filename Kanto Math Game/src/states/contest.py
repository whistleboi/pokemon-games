# [REF-0071: Pokemon Contests]
"""
Contest Hall lobby and the contest itself.

A contest has two rounds, as in Ruby/Sapphire/Emerald:
  1. Condition judging: the Pokemon's condition in the contest's category
     (raised with Pokeblocks) earns opening hearts.
  2. Five appeal turns: pick one of four moves, then answer a math problem.
     A right answer makes the appeal; a quick one earns a bonus, a move that
     suits the contest pleases the crowd, and repeating a move bores the judges.
     Filling the shared crowd meter sets off a Spectacular Talent bonus.
The highest total wins a ribbon; winning a rank opens the next one.
"""
import math
import random
import pygame

from src.states.base import GameState
from src.ui.dialogue import ClassicDialogueBox
from src.ui.widgets import Button, MathBattleUI
from src.utils import Utils
from src.config import WHITE, BLACK, GOLD, GRAY, RED
from src.pokemon.data import Pokemon
from src.pokemon.contest import (
    CATEGORIES, RANKS, RANK_BADGES, RANK_PRIZE, CATEGORY_COLOR, TYPE_CATEGORY, POKEBLOCKS,
    move_category, ribbon_id, ribbon_label,
)

APPEAL_TURNS = 5
CROWD_MAX = 5
SPECTACULAR_BONUS = 4
QUICK_ANSWER_MS = 6000

# Rival strength per rank: condition range, chance of a good appeal, chance of a fitting move.
RIVAL_SKILL = {
    "NORMAL": ((20, 60), 0.55, 0.45),
    "SUPER": ((60, 110), 0.65, 0.55),
    "HYPER": ((110, 170), 0.75, 0.65),
    "MASTER": ((160, 230), 0.85, 0.75),
}
COORDINATORS = ["Lady Mia", "Tuber Kai", "Beauty Ana", "Pokefan Jo", "Ace Rin", "Lass Ivy",
                "Artist Paz", "Expert Lu", "Idol Mae", "Parasol Vi", "Coord. Ren", "Coord. Sol"]


def contest_won(story, category, rank):
    return story.story_flags.get(f"contest_won_{category}_{rank}", False)


def rank_status(story, region, category, rank):
    """(unlocked, reason it is locked)."""
    needed = RANK_BADGES[rank]
    have = len(story.badges.get(region, []))
    if have < needed:
        return False, f"{needed} badges"
    idx = RANKS.index(rank)
    if idx and not contest_won(story, category, RANKS[idx - 1]):
        return False, f"win {RANKS[idx - 1].title()}"
    return True, ""


def draw_stage(surface, width, height, tint=(120, 60, 160)):
    """Contest stage: dark hall, red curtains, spotlights and a lit floor."""
    t = pygame.time.get_ticks() / 1000
    surface.fill((18, 10, 30))
    floor = pygame.Rect(0, int(height * 0.62), width, height - int(height * 0.62))
    pygame.draw.rect(surface, (60, 40, 30), floor)
    pygame.draw.ellipse(surface, (110, 80, 50), floor.inflate(-width * 0.2, -floor.height * 0.3))
    glow = pygame.Surface((width, height), pygame.SRCALPHA)
    for i, base_x in enumerate((0.25, 0.5, 0.75)):
        x = int(width * (base_x + 0.04 * math.sin(t * 0.8 + i * 2)))
        pygame.draw.polygon(glow, (*tint, 45), [(x - 30, 0), (x + 30, 0), (x + 170, int(height * 0.8)),
                                                  (x - 170, int(height * 0.8))])
    surface.blit(glow, (0, 0))
    curtain_w = int(width * 0.09)
    for side in (0, width - curtain_w):
        pygame.draw.rect(surface, (140, 20, 30), (side, 0, curtain_w, height))
        for k in range(4):
            fx = side + k * curtain_w // 4
            pygame.draw.line(surface, (100, 10, 20), (fx, 0), (fx, height), 3)
    pygame.draw.rect(surface, (160, 30, 40), (0, 0, width, 28))


def _hearts_text(n):
    return f"{n} hearts"


def draw_heart(surface, x, y, size, color=(255, 110, 150)):
    """A small filled heart with its top-left at (x, y)."""
    r = size // 4
    pygame.draw.circle(surface, color, (x + r, y + r), r)
    pygame.draw.circle(surface, color, (x + 3 * r, y + r), r)
    pygame.draw.polygon(surface, color, [(x, y + r), (x + size, y + r), (x + size // 2, y + size)])


# ---------------------------------------------------------------------------
class ContestHallState(GameState):
    """Lobby: receptionist, Pokeblock stand, and choosing category / rank / Pokemon."""

    def __init__(self, game, previous_state, result=None):
        super().__init__(game)
        self.previous_state = previous_state
        self.story = game.story_manager
        self.region = self.story.get_current_region()
        self.box_rect = Utils.get_full_dialogue_rect(game)
        self.dialogue_box = ClassicDialogueBox(self.box_rect, [], game.assets.fonts["med"], visible=False)
        self.menu_buttons = []
        self.category = None
        self.npc_sprite = game.assets.get_trainer_image("beauty.png")
        self.pending_lines = self._welcome_lines() if result is None else result

    # -- story ----------------------------------------------------------
    def _welcome_lines(self):
        flags, inv = self.story.story_flags, self.story.inventory
        if not flags.get("contest_pass_received"):
            flags["contest_pass_received"] = True
            inv["CONTEST_PASS"] = 1
            inv["POKEBLOCK_CASE"] = 1
            for block in POKEBLOCKS:
                inv[block] = inv.get(block, 0) + 3
            if self.region == "HOENN":
                lines = ["Hi there! I'm LISIA, the Contest Idol!",
                         "Pokemon Contests are where Pokemon show off how Cool, Beautiful,",
                         "Cute, Smart or Tough they are!",
                         "Each appeal is powered by a quick, correct answer. Think fast!",
                         "Here's a CONTEST PASS and a POKeBLOCK CASE with a few Pokeblocks!",
                         "Feed Pokeblocks from your Bag to raise a Pokemon's condition.",
                         "Oh! And a FEEBAS that's beautiful enough turns into MILOTIC...",
                         "Start in Normal Rank. Win, and the next rank opens up!"]
            else:
                lines = ["Welcome to the Contest Hall!",
                         "This is your CONTEST PASS, and a POKeBLOCK CASE to start you off.",
                         "Feed Pokeblocks to raise condition, then dazzle the crowd!"]
            lines.append("You received the CONTEST PASS and POKeBLOCK CASE!")
            return lines
        return ["Welcome to the Contest Hall!", "Would you like to enter a contest today?"]

    # -- menus ----------------------------------------------------------
    def _clear_menu(self):
        for btn in self.menu_buttons:
            if btn in self.game.ui_manager.elements:
                self.game.ui_manager.elements.remove(btn)
        self.menu_buttons = []

    def _add_buttons(self, specs, y=None, width=220):
        """specs: (text, callback, color or None). Laid out in a row (two rows if needed)."""
        self._clear_menu()
        per_row = 5
        rows = [specs[i:i + per_row] for i in range(0, len(specs), per_row)]
        y = y if y is not None else self.box_rect.top + 30
        for r, row in enumerate(rows):
            total = len(row) * (width + 16) - 16
            x = self.game.width // 2 - total // 2
            for i, (text, cb, color) in enumerate(row):
                btn = Button((x + i * (width + 16), y + r * 80, width, 64), text,
                             self.game.assets.fonts["caption"], cb, autosize=False,
                             bg_color=color or (60, 90, 200))
                self.menu_buttons.append(btn)
                self.game.ui_manager.add_element(btn)

    def show_main_menu(self):
        self.dialogue_box.set_visibility(False)
        self.category = None
        self._add_buttons([("ENTER CONTEST", self.choose_category, None),
                           ("POKeBLOCKS", self.open_pokeblocks, (200, 90, 160)),
                           ("RIBBONS", self.show_record, (180, 140, 40)),
                           ("LEAVE", self.leave, RED)])

    def choose_category(self):
        specs = [(c, (lambda c=c: self.choose_rank(c)), CATEGORY_COLOR[c]) for c in CATEGORIES]
        specs.append(("BACK", self.show_main_menu, GRAY))
        self._add_buttons(specs, width=190)

    def choose_rank(self, category):
        self.category = category
        specs = []
        for rank in RANKS:
            ok, why = rank_status(self.story, self.region, category, rank)
            won = contest_won(self.story, category, rank)
            label = f"{rank}" + (" ★" if won else "") if ok else f"{rank} ({why})"
            specs.append((label, (lambda r=rank: self.choose_pokemon(r)) if ok else self._locked,
                          CATEGORY_COLOR[category] if ok else GRAY))
        specs.append(("BACK", self.choose_category, GRAY))
        self._add_buttons(specs, width=200)

    def _locked(self):
        pass

    def choose_pokemon(self, rank):
        from src.states.systems import PokemonPartyMenuState
        self._clear_menu()
        category = self.category

        def picked(index):
            team = self.story.player_team
            if index < len(team):
                self.game.change_state(ContestState(self.game, self, team[index], category, rank))

        def cancel():
            self.game.change_state(self)

        self.game.change_state(PokemonPartyMenuState(self.game, previous_state=self, context="use_item",
                                                     on_select=picked, on_cancel=cancel))

    def open_pokeblocks(self):
        from src.states.systems import PokeMartState
        self._clear_menu()
        self.game.change_state(PokeMartState(self.game, self, stock=list(POKEBLOCKS)))

    def show_record(self):
        """RIBBONS: the display case of each Pokemon's contest ribbons."""
        self._clear_menu()
        self.game.change_state(RibbonCaseState(self.game, self))

    def leave(self):
        self._clear_menu()
        self.game.change_state(self.previous_state)

    def _say(self, lines):
        self._clear_menu()
        self.dialogue_box.reset(lines)
        self.dialogue_box.callback = self.show_main_menu

    # -- state ----------------------------------------------------------
    def start(self):
        self.game.ui_manager.add_element(self.dialogue_box)
        if self.pending_lines:
            lines, self.pending_lines = self.pending_lines, None
            self._say(lines)
        else:
            self.show_main_menu()

    def handle_events(self, events):
        pass

    def update(self):
        self.dialogue_box.update()

    def draw(self):
        draw_stage(self.game.screen, self.game.width, self.box_rect.top)
        if self.npc_sprite:
            img = pygame.transform.smoothscale(self.npc_sprite, (260, 260))
            self.game.screen.blit(img, img.get_rect(midbottom=(self.game.width // 2, self.box_rect.top - 10)))
        Utils.draw_text_outline(self.game.screen, "CONTEST HALL", self.game.assets.fonts["big"], GOLD,
                                self.game.width // 2, 70)
        if not self.dialogue_box.visible:
            Utils.draw_textbox(self.game.screen, *self.box_rect)
        self.game.ui_manager.draw(self.game.screen)


# ---------------------------------------------------------------------------
class Contestant:
    def __init__(self, name, pokemon, condition, is_player=False, skill=None):
        self.name = name
        self.pokemon = pokemon
        self.condition = condition
        self.is_player = is_player
        self.skill = skill
        self.hearts = 0
        self.last_gain = 0
        self.last_move = None
        icon = pokemon.image
        self.icon = pygame.transform.smoothscale(icon, (96, 96)) if icon else None


class ContestState(GameState):
    def __init__(self, game, hall, pokemon, category, rank):
        super().__init__(game)
        self.hall = hall
        self.category = category
        self.rank = rank
        self.story = game.story_manager
        self.box_rect = Utils.get_full_dialogue_rect(game)
        self.dialogue_box = ClassicDialogueBox(self.box_rect, [], game.assets.fonts["med"], visible=False)
        self.move_buttons = []
        self.math_ui = None
        self.turn = 0
        self.crowd = 0
        self.phase = "INTRO"
        self.started = False

        me = Contestant(game.player_name or "YOU", pokemon, pokemon.condition.get(category, 0), is_player=True)
        self.contestants = [me] + self._make_rivals()
        self.player = me
        self.moves = self._pick_moves(pokemon)

    # -- setup ----------------------------------------------------------
    def _make_rivals(self):
        cond_range, good, fit = RIVAL_SKILL[self.rank]
        wanted_types = [t for t, c in TYPE_CATEGORY.items() if c == self.category]
        movesets = self.game.assets.movesets
        lo, hi = 252, 386
        if self.region_dex():
            lo, hi = self.region_dex()
        allowed = self._stages_for_rank()
        # Legendaries (catch rate 3 or less) don't enter contests.
        everyday = [pid for pid in range(lo, hi + 1)
                    if (movesets.get(str(pid), {}).get("capture_rate") or 45) > 3] or list(range(lo, hi + 1))
        in_region = [pid for pid in everyday if self._evo_stage(pid) in allowed] or everyday
        candidates = [pid for pid in in_region
                      if set(movesets.get(str(pid), {}).get("types", [])) & set(wanted_types)] or in_region
        rivals = []
        for name, pid in zip(random.sample(COORDINATORS, 3), random.sample(candidates, 3)):
            mon = Pokemon(self.game.loader.fetch_specific(pid), self.game.assets, size_mult=3.0)
            rivals.append(Contestant(name, mon, random.randint(*cond_range), skill=(good, fit)))
        return rivals

    def _stages_for_rank(self):
        """Lower ranks bring younger Pokemon: Normal/Super unevolved, Hyper up to middle, Master any."""
        return {"NORMAL": {1}, "SUPER": {1, 2}, "HYPER": {2, 3}, "MASTER": {2, 3}}[self.rank]

    def _evo_stage(self, pid):
        """1 = unevolved, 2 = evolved once, 3 = evolved twice (from the evolution table)."""
        evo = self.game.loader.evolution_map
        if not hasattr(ContestState, "_parents"):
            parents = {}
            for base, targets in evo.items():
                if isinstance(targets, list):
                    for t in targets:
                        parents.setdefault(str(t).split("_")[0].upper(), base.split("_")[0].upper())
            ContestState._parents = parents
        name = str(self.game.assets.movesets.get(str(pid), {}).get("name", "")).upper()
        stage = 1
        while name in ContestState._parents and stage < 3:
            name = ContestState._parents[name]
            stage += 1
        return stage

    def region_dex(self):
        cfg = self.story.get_region_start(self.story.get_current_region())
        rng = cfg.get("dex_range")
        return tuple(rng) if rng and len(rng) == 2 else None

    def _pick_moves(self, pokemon):
        """Four different moves: up to two that suit this contest, the rest from other categories."""
        moves = self.game.assets.movesets.get(str(getattr(pokemon, "meta_id", pokemon.id)), {}).get("moves", [])
        seen, pool = set(), []
        for m in moves:
            name = (m.get("name") or "").upper()
            if name and name not in seen:
                seen.add(name)
                pool.append((name, move_category(m.get("type"))))
        random.shuffle(pool)
        fitting = [m for m in pool if m[1] == self.category][:2]
        others, used = [], {c for _, c in fitting}
        for m in pool:
            if len(fitting) + len(others) >= 4:
                break
            if m in fitting or m in others:
                continue
            if m[1] not in used or len(pool) <= 4:
                others.append(m)
                used.add(m[1])
        chosen = fitting + others
        for m in pool:  # top up if the categories ran out
            if len(chosen) >= 4:
                break
            if m not in chosen:
                chosen.append(m)
        return chosen or [("TACKLE", "CUTE")]

    # -- flow -----------------------------------------------------------
    def say(self, lines, then):
        self._hide_moves()
        self.dialogue_box.reset(lines)
        self.dialogue_box.callback = then

    def intro(self):
        rank, cat = self.rank.title(), self.category.title()
        lines = [f"Welcome to the {rank} Rank {cat} Contest!"]
        for c in self.contestants:
            who = "And our challenger" if c.is_player else "Entering"
            lines.append(f"{who}: {c.name} and {c.pokemon.display_name.upper()}!")
        self.say(lines, self.condition_round)

    def condition_round(self):
        lines = [f"Round 1: the judges look over each Pokemon's {self.category.title()} condition!"]
        for c in self.contestants:
            gain = c.condition // 16
            c.hearts += gain
            c.last_gain = gain
            lines.append(f"{c.pokemon.display_name.upper()}: {self._condition_word(c.condition)} (+{gain})")
        lines.append("Round 2: the appeals! Five turns, so make every answer count!")
        self.say(lines, self.next_turn)

    @staticmethod
    def _condition_word(value):
        if value >= 200:
            return "simply dazzling!"
        if value >= 140:
            return "really striking!"
        if value >= 80:
            return "nicely polished."
        if value >= 30:
            return "looking good."
        return "could use some Pokeblocks."

    def next_turn(self):
        self.turn += 1
        if self.turn > APPEAL_TURNS:
            self.results()
            return
        self.phase = "CHOOSE"
        self.dialogue_box.set_visibility(False)
        self._show_moves()

    def _show_moves(self):
        self._hide_moves()
        w, h, gap = 320, 60, 12
        cols = 2
        x0 = self.box_rect.centerx - (cols * (w + 20) - 20) // 2
        y0 = self.box_rect.centery - h - gap // 2
        for i, (name, cat) in enumerate(self.moves):
            x = x0 + (i % cols) * (w + 20)
            y = y0 + (i // cols) * (h + gap)
            label = f"{name.replace('-', ' ')}  [{cat.title()}]"
            btn = Button((x, y, w, h), label, self.game.assets.fonts["caption"],
                         lambda i=i: self.choose_move(i), autosize=False, bg_color=CATEGORY_COLOR[cat])
            self.move_buttons.append(btn)
            self.game.ui_manager.add_element(btn)

    def _hide_moves(self):
        for btn in self.move_buttons:
            if btn in self.game.ui_manager.elements:
                self.game.ui_manager.elements.remove(btn)
        self.move_buttons = []

    def choose_move(self, index):
        self._hide_moves()
        self.chosen = self.moves[index]
        self.phase = "MATH"
        play = self.game.states["play"]
        self.problem, self.answer, self.options = play.generate_math_set(0, num_options=4)
        if self.math_ui and self.math_ui in self.game.ui_manager.elements:
            self.game.ui_manager.elements.remove(self.math_ui)
        self.math_ui = MathBattleUI(self.game, self.problem, self.options, self.on_answer)
        self.game.ui_manager.add_element(self.math_ui)
        self.asked_at = pygame.time.get_ticks()

    def on_answer(self, index):
        correct = self.options[index] == self.answer
        quick = pygame.time.get_ticks() - self.asked_at <= QUICK_ANSWER_MS
        self.math_ui.set_visibility(False)
        lines = self._player_appeal(correct, quick)
        for rival in self.contestants[1:]:
            lines.extend(self._rival_appeal(rival))
        self.say(lines, self.next_turn)

    # -- scoring --------------------------------------------------------
    def _appeal(self, contestant, move, good, quick=False):
        """Apply one appeal. Returns the lines describing it."""
        name, cat = move
        mon = contestant.pokemon.display_name.upper()
        prefix = "" if contestant.is_player else f"{contestant.name}'s "
        lines = [f"{prefix}{mon} appealed with {name.replace('-', ' ')}!"]
        gain = 0
        if not good:
            lines.append(f"{mon} got nervous... the appeal fell flat." if contestant.is_player
                         else "It didn't go over well.")
        else:
            gain = 2
            notes = []
            if cat == self.category:
                gain += 1
                notes.append("The crowd loves it!")
                self.crowd += 1
            if quick:
                gain += 1
                notes.append("Perfect timing!")
            if contestant.last_move == name:
                gain -= 1
                notes.append("The judges have seen that move already...")
            if self.crowd >= CROWD_MAX:
                gain += SPECTACULAR_BONUS
                self.crowd = 0
                notes.append(f"SPECTACULAR TALENT! The crowd goes wild! (+{SPECTACULAR_BONUS})")
            gain = max(0, gain)
            lines.extend(notes)
        contestant.last_move = name
        contestant.hearts += gain
        contestant.last_gain = gain
        if contestant.is_player:
            lines.append(f"+{gain} hearts!")
        return lines

    def _player_appeal(self, correct, quick):
        return self._appeal(self.player, self.chosen, correct, quick and correct)

    def _rival_appeal(self, rival):
        good_chance, fit_chance = rival.skill
        options = self.rival_moves(rival)
        fitting = [m for m in options if m[1] == self.category]
        if fitting and random.random() < fit_chance:
            move = random.choice(fitting)
        else:
            move = random.choice(options)
        if move[0] == rival.last_move and len(options) > 1:
            move = random.choice([m for m in options if m[0] != rival.last_move])
        good = random.random() < good_chance
        quick = good and random.random() < good_chance * 0.5
        return self._appeal(rival, move, good, quick)

    def rival_moves(self, rival):
        if not hasattr(rival, "moves"):
            rival.moves = self._pick_moves(rival.pokemon)
        return rival.moves

    def results(self):
        self.phase = "RESULTS"
        order = sorted(self.contestants, key=lambda c: (c.hearts, c.condition, c.is_player), reverse=True)
        lines = ["The results are in!"]
        for place, c in reversed(list(enumerate(order, start=1))):
            lines.append(f"#{place}: {c.name} and {c.pokemon.display_name.upper()} - {_hearts_text(c.hearts)}")
        won = order[0] is self.player
        self.outcome_lines = self._rewards(won) if won else [
            f"{self.player.pokemon.display_name.upper()} placed #{order.index(self.player) + 1}.",
            "Feed it Pokeblocks and answer quickly to win next time!"]
        self.say(lines + self.outcome_lines, self.finish)

    def _rewards(self, won):
        story, flags = self.story, self.story.story_flags
        mon = self.player.pokemon
        rib = ribbon_id(self.category, self.rank)
        prize = RANK_PRIZE[self.rank]
        story.money += prize
        lines = [f"{self.player.name} and {mon.display_name.upper()} win!"]
        if rib not in mon.ribbons:
            mon.ribbons.append(rib)
            lines.append(f"{mon.display_name.upper()} received the {ribbon_label(rib)}!")
        lines.append(f"You received ${prize} in prize money!")
        first_win = not flags.get(f"contest_won_{self.category}_{self.rank}")
        flags[f"contest_won_{self.category}_{self.rank}"] = True
        if first_win and self.rank != "MASTER":
            nxt = RANKS[RANKS.index(self.rank) + 1]
            lines.append(f"{nxt.title()} Rank {self.category.title()} is now open (with "
                         f"{RANK_BADGES[nxt]} badges)!")
        if self.rank == "MASTER" and first_win:
            lines.append(f"The Lilycove Museum wants to hang a painting of {mon.display_name.upper()}!"
                         if self.story.get_current_region() == "HOENN" else
                         "You're a Master Rank champion!")
            if not flags.get("contest_lisia_master"):
                flags["contest_lisia_master"] = True
                story.inventory["RARE_CANDY"] = story.inventory.get("RARE_CANDY", 0) + 3
                lines.append("LISIA: That was amazing! Please take these 3 RARE CANDIES!")
        return lines

    def finish(self):
        self._hide_moves()
        self.game.data.save()
        self.game.change_state(ContestHallState(self.game, self.hall.previous_state, result=[]))

    # -- state ----------------------------------------------------------
    def start(self):
        self.game.ui_manager.add_element(self.dialogue_box)
        if not self.started:
            self.started = True
            self.intro()

    def handle_events(self, events):
        pass

    def update(self):
        self.dialogue_box.update()

    def draw(self):
        screen = self.game.screen
        draw_stage(screen, self.game.width, self.box_rect.top, CATEGORY_COLOR[self.category])
        font, small = self.game.assets.fonts["caption"], self.game.assets.fonts["label"]

        # Contestant cards along the top.
        card_w, gap = 270, 16
        x0 = self.game.width // 2 - (4 * card_w + 3 * gap) // 2
        for i, c in enumerate(self.contestants):
            rect = pygame.Rect(x0 + i * (card_w + gap), 40, card_w, 150)
            from src.ui import theme
            theme.card(screen, rect, selected=c.is_player, accent=theme.BAG)  # the menu redesign's cards
            if c.icon:
                screen.blit(c.icon, (rect.x + 6, rect.y + 30))
            theme.shadow_text(screen, c.name, font, rect.x + 12, rect.y + 8,
                              color=(170, 120, 20) if c.is_player else theme.TEXT)
            theme.shadow_text(screen, c.pokemon.display_name.upper(), font, rect.x + 108, rect.y + 44)
            draw_heart(screen, rect.x + 108, rect.y + 80, 24)
            theme.shadow_text(screen, str(c.hearts), small, rect.x + 142, rect.y + 74, color=(214, 70, 110))
            if c.last_gain:
                theme.shadow_text(screen, f"+{c.last_gain}", small, rect.x + 108, rect.y + 112, color=(170, 120, 20))

        # Crowd meter and turn counter.
        meter_y = 210
        label = f"{self.rank} RANK {self.category}  -  TURN {min(self.turn, APPEAL_TURNS)}/{APPEAL_TURNS}"
        Utils.draw_text_outline(screen, label, font, WHITE, self.game.width // 2, meter_y)
        for k in range(CROWD_MAX):
            cx = self.game.width // 2 - (CROWD_MAX - 1) * 22 + k * 44
            color = CATEGORY_COLOR[self.category] if k < self.crowd else (60, 50, 70)
            pygame.draw.circle(screen, color, (cx, meter_y + 36), 16)
            pygame.draw.circle(screen, BLACK, (cx, meter_y + 36), 16, 2)

        # The player's Pokemon on stage.
        mon = self.player.pokemon
        if mon.image:
            img = pygame.transform.smoothscale(mon.image, (220, 220))
            bob = int(6 * math.sin(pygame.time.get_ticks() / 300))
            screen.blit(img, img.get_rect(midbottom=(self.game.width // 2, self.box_rect.top - 8 + bob)))

        if not self.dialogue_box.visible and self.phase != "MATH":
            Utils.draw_textbox(screen, *self.box_rect)
        self.game.ui_manager.draw(screen)


def museum_lines(story):
    """Lilycove Museum: one painting per Master Rank category won; all five earns a prize."""
    flags = story.story_flags
    painted = [c for c in CATEGORIES if contest_won(story, c, "MASTER")]
    lines = ["CURATOR: Welcome to the Lilycove Museum.",
             "Our new wing displays paintings of Master Rank contest winners."]
    if not painted:
        lines.append("The frames are empty for now. Perhaps your Pokemon could fill them?")
        return lines
    lines.append("Paintings on display: " + ", ".join(c.title() for c in painted) + ".")
    if len(painted) < len(CATEGORIES):
        missing = [c.title() for c in CATEGORIES if c not in painted]
        lines.append("Still waiting for: " + ", ".join(missing) + ".")
        return lines
    if not flags.get("contest_master"):
        flags["contest_master"] = True
        inv = story.inventory
        inv["RARE_CANDY"] = inv.get("RARE_CANDY", 0) + 5
        for block in POKEBLOCKS:
            inv[block] = inv.get(block, 0) + 5
        story.money += 10000
        lines += ["Every frame is filled! You are a true Contest Master!",
                  "Please accept the museum's thanks: 5 RARE CANDIES, a case of Pokeblocks and $10000!"]
    else:
        lines.append("Every frame is filled. Visitors come from all over Hoenn to see them!")
    return lines


# ---------------------------------------------------------------------------
class RibbonCaseState(GameState):
    """The ribbon display case (Jordan): your Pokemon at the left, and for the one picked a velvet
    case with a rosette for each contest category and rank (earned ones in colour, the rest faint)."""

    def __init__(self, game, previous_state):
        super().__init__(game)
        from src.ui import theme
        from src.ui.panels import CommandButton
        self.previous_state = previous_state
        story = game.story_manager
        mons = [p for p in story.player_team if p] + [p for p in story.pc_pokemon if p and getattr(p, "ribbons", None)]
        mons.sort(key=lambda p: -len(getattr(p, "ribbons", []) or []))
        self.mons = mons[:12]
        self.selected = 0
        f = game.assets.fonts
        self.btn_back = CommandButton((16, 14, 140, 56), "BACK", f["button"], self.go_back,
                                      bg_color=theme.BACK, autosize=False)
        top = theme.HEADER_H + 16
        self.list_rect = pygame.Rect(24, top, 360, game.height - 16 - top)
        self.case_rect = pygame.Rect(self.list_rect.right + 16, top, game.width - 24 - self.list_rect.right - 16,
                                     self.list_rect.h)

    def go_back(self):
        self.game.change_state(self.previous_state)

    def start(self):
        self.game.ui_manager.elements.clear()
        self.game.ui_manager.add_element(self.btn_back)

    def row_rect(self, i):
        r = self.list_rect
        h = (r.h - 24 - 11 * 6) // 12
        return pygame.Rect(r.x + 12, r.y + 12 + i * (h + 6), r.w - 24, h)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for i in range(len(self.mons)):
                    if self.row_rect(i).collidepoint(event.pos):
                        self.selected = i
            elif event.type == pygame.KEYDOWN and event.key in (pygame.K_UP, pygame.K_DOWN) and self.mons:
                self.selected = (self.selected + (1 if event.key == pygame.K_DOWN else -1)) % len(self.mons)

    def update(self):
        pass

    @staticmethod
    def _rosette(surface, center, color, rank_i, earned):
        """A ribbon: two tails and a pleated rosette, its middle showing the rank (1-4 stars)."""
        import math
        cx, cy = center
        col = color if earned else (96, 82, 100)
        dark = tuple(max(0, int(c * 0.6)) for c in col)
        for dx in (-12, 12):  # the tails
            pts = [(cx + dx // 2, cy + 6), (cx + dx, cy + 44), (cx + dx // 2 + (4 if dx < 0 else -4), cy + 36),
                   (cx + dx // 4, cy + 44)]
            pygame.draw.polygon(surface, dark, pts)
        for k in range(14):  # the pleats
            a = k * 2 * math.pi / 14
            pygame.draw.circle(surface, col if k % 2 else dark, (int(cx + math.cos(a) * 18), int(cy + math.sin(a) * 18)), 9)
        pygame.draw.circle(surface, (250, 246, 230) if earned else (130, 120, 136), (cx, cy), 14)
        pygame.draw.circle(surface, dark, (cx, cy), 14, 2)
        gold = (240, 196, 40) if earned else (110, 100, 110)
        for s in range(rank_i + 1):  # stars for the rank
            x = cx - rank_i * 5 + s * 10
            pygame.draw.circle(surface, gold, (x, cy), 3)

    def draw(self):
        from src.ui import theme
        from src.utils import Utils
        from src.states.systems import fit_sprite
        screen, f = self.game.screen, self.game.assets.fonts
        accent = (170, 40, 70)
        theme.menu_background(screen, accent, "RIBBON CASE", f["button"], title_x=176)
        mouse = pygame.mouse.get_pos()

        theme.draw_panel(screen, self.list_rect)
        for i, p in enumerate(self.mons):
            r = self.row_rect(i)
            theme.card(screen, r, hover=r.collidepoint(mouse), selected=i == self.selected, accent=accent, radius=10)
            if p.image:
                spr = fit_sprite(p.image, r.h - 6, r.h - 6)
                screen.blit(spr, spr.get_rect(center=(r.x + 6 + r.h // 2, r.centery)))
            theme.shadow_text(screen, p.display_name.title(), f["label"], r.x + r.h + 14,
                              r.centery - f["label"].get_height() // 2)
            n = len(getattr(p, "ribbons", []) or [])
            theme.shadow_text(screen, f"{n}", f["label"], r.right - 14, r.centery - f["label"].get_height() // 2,
                              color=accent if n else (150, 156, 172), align="right")

        case = self.case_rect
        pygame.draw.rect(screen, (60, 20, 34), case, border_radius=16)            # the velvet
        pygame.draw.rect(screen, (196, 150, 70), case, 6, border_radius=16)        # the gilt frame
        if not self.mons:
            theme.shadow_text(screen, "No Pokemon yet.", f["s_med"], case.centerx, case.centery,
                              color=WHITE, shadow=(30, 10, 20), align="center")
            self.game.ui_manager.draw(screen)
            return
        mon = self.mons[min(self.selected, len(self.mons) - 1)]
        won = set(getattr(mon, "ribbons", []) or [])
        Utils.draw_text_outline(screen, f"{mon.display_name.upper()}'s RIBBONS", f["button"], (250, 230, 190),
                                case.centerx, case.y + 34, outline_color=(40, 10, 20), thickness=3)
        left = case.x + 150
        col_w = (case.right - 30 - left) // len(RANKS)
        row_h = (case.bottom - 30 - (case.y + 80)) // len(CATEGORIES)
        for j, rank in enumerate(RANKS):
            Utils.draw_text_outline(screen, rank.title(), f["label"], (230, 210, 170), left + j * col_w + col_w // 2,
                                    case.y + 72, outline_color=(40, 10, 20), thickness=2)
        for i, cat in enumerate(CATEGORIES):
            y = case.y + 92 + i * row_h + row_h // 2 - 10
            Utils.draw_text_outline(screen, cat.title(), f["label"], CATEGORY_COLOR[cat], case.x + 30, y,
                                    align="left", outline_color=(30, 8, 16), thickness=3)
            for j, rank in enumerate(RANKS):
                self._rosette(screen, (left + j * col_w + col_w // 2, y - 6), CATEGORY_COLOR[cat], j,
                              ribbon_id(cat, rank) in won)
        self.game.ui_manager.draw(screen)
