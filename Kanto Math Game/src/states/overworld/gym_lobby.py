"""The Gym lobby: the Gym challenge, the Leader, and League rematches."""

import pygame
import random
from src.states.base import GameState
from src.utils import Utils
from src.ui.widgets import Button
from src.ui import theme
from src.world import league_redo
from src.world import black_fog
from src import minigames
from src.world import levels
from src.pokemon import forms
from src.pokemon.data import Pokemon
from src.config import BLACK, GREEN, BLUE, GOLD, RED, PURPLE, GRAY
from src.states.overworld.common import (
    _cast_trainer, _fill_names, _region_starter_id, _resolve_lines, _trainer_sprite, rival_image
)


# [REF-0035: Gym Lobby State]
# League rematches after the title (Jordan, 11-02): every Pokemon at least Lv 70; once your
# strongest Pokemon is above Lv 80, the team rises with it (the ace matches yours).
LEAGUE_REMATCH_MIN = 70


LEAGUE_REMATCH_SCALE_FROM = 80


def league_rematch_levels(story, team_levels):
    lv = [max(LEAGUE_REMATCH_MIN, int(x)) for x in team_levels]
    ace = black_fog.ace_level(story)
    if lv and ace > LEAGUE_REMATCH_SCALE_FROM and ace > max(lv):
        lift = ace - max(lv)
        lv = [min(100, x + lift) for x in lv]
    return lv


def in_room(game):
    """Is this Gym challenge being taken in the Gym's own room (walked inside), not the lobby screen?"""
    return getattr(game, "gym_room_return", None) == game.story_manager.current_area_key


def back_to_room(game, state=None):
    """Back into the Gym's room, where you stood (after the game or the battle)."""
    from src.states.overworld import CityState
    game.gym_room_return = None
    game.change_state(state or CityState(game))


def leader_in_room(state):
    """The Leader in their Gym's room (Jordan, 11-13: the game before the Leader stays; "have the leader say he wants to
    play a game before battling"): the challenge's minigame first, till it's won, then the battle; back in the room after.
    The Gym's own trainers stand in the room (battled there), so the Leader is next."""
    game = state.game
    story = game.story_manager
    lobby = GymLobbyState(game, state)
    name = _fill_names(game, (lobby.leader or {}).get("name", "The Leader"))
    if lobby.is_league:
        game.change_state(lobby)
        return
    if lobby.is_cleared:
        state.show_message([f"{name}: You've already beaten me and earned my Badge. Keep it up!"])
        return
    if not lobby.challenge and not lobby.redo and lobby.progress < len(lobby.trainers):
        story.story_flags[lobby.prog_key] = len(lobby.trainers)  # (the room's trainers are the Gym's: the Leader is next)
        lobby = GymLobbyState(game, state)
    game.gym_room_return = story.current_area_key
    if lobby.challenge:
        state.show_message([f"{name}: Welcome, challenger! Before we battle, I want to play a game with you.",
                            f"{name}: Win it, and then we'll see how strong you really are!"], callback=lobby._start_challenge)
        return
    state.show_message([f"{name}: Now then. Let's battle!"], callback=lobby.challenge_gym)


def league_member(state, opt):
    """An Elite Four member (or the Champion) in their own room of the League (Emerald's rooms, one battle each, in the
    League's order: opt "index"). Win, and their room's door on opens (battle.py: "league_won_<area>_<n>")."""
    game = state.game
    story = game.story_manager
    closed = state.gym_closed()
    if closed:
        state.show_message(closed)
        return
    lobby = GymLobbyState(game, state)
    i, name = int(opt.get("index", 0)), _fill_names(game, opt.get("text", ""))
    if lobby.is_cleared or lobby.progress > i:
        state.show_message([f"{name}: You've beaten me already. Go on ahead, the next challenge awaits!"])
        return
    if lobby.progress < i:
        state.show_message([f"{name}: You'll need to get past the others first."])
        return
    game.gym_room_return = story.current_area_key
    state.show_message([_fill_names(game, x) for x in (opt.get("lines") or [f"{name}: Welcome. Let's battle!"])],
                       callback=lobby.challenge_gym)


class GymLobbyState(GameState):
    def __init__(self, game, previous_state=None):
        from src.states.overworld.area_transition import _collapse_hud, is_league
        super().__init__(game)
        self.area_key = game.story_manager.current_area_key
        self.area_data = game.story_manager.get_current_area_data()
        self.gym_data = self.area_data.get("gym", {})

        self.prog_key = f"gym_progress_{self.area_key}"
        self.progress = game.story_manager.story_flags.get(self.prog_key, 0)
        self.trainers = self.gym_data.get("trainers", [])
        self.leader = self.gym_data.get("leader")

        self.next_opponent = None
        self.is_cleared = False
        self.region = game.story_manager.get_current_region()
        self.is_league = is_league(self.gym_data)
        self.redo = False  # a League Redo battle (src/world/league_redo.py)

        if self.is_league:
            # Every region's League: the Elite Four and the Champion in a row. A loss starts it
            # over (see reset_league_after_loss), and after the title it's a rematch run.
            if self.progress > len(self.trainers):
                self.progress = 0
                game.story_manager.story_flags[self.prog_key] = 0

            self.gauntlet = self.trainers + [self.leader]
            self.rematch = game.story_manager.is_region_champion(self.region)
            mode_text = "Rematch" if self.rematch else "League Challenge"
            if league_redo.league_open(game.story_manager, self.region):  # all 8 badges won again
                self.redo, self.rematch, mode_text = True, False, "League Redo"

            if self.progress < len(self.gauntlet):
                self.next_opponent = self.gauntlet[self.progress]
                if self.progress == len(self.gauntlet) - 1:
                    if self.area_key == "INDIGO_PLATEAU":
                        r_name = ((game.story_manager.region_rivals.get("KANTO") or {}).get("name")
                                  or getattr(self.game, "rival_name", "CHAMPION"))
                    else:
                        r_name = _fill_names(self.game, self.leader.get("name", "the Champion"))
                    self.status_text = f"{mode_text} - Final Match: Champion {r_name}"
                else:
                    self.status_text = f"{mode_text}: Match {self.progress + 1}/{len(self.gauntlet)}"
            else:
                self.is_cleared = True
                self.status_text = "The League has been conquered!"
        else:
            # Orange Islands post-game (Jordan): after Drake, a cleared Orange Gym can be battled
            # again from its first trainer, at the Orange Champion's post-game band (no badge again).
            self.orange_rematch = (self.region == "ORANGE" and bool(self.leader)
                                   and game.story_manager.is_region_champion("ORANGE"))
            badge = (self.leader or {}).get("badge_reward")
            self.redo = bool(badge and league_redo.active_here(game.story_manager, self.region)
                             and not league_redo.has_badge(game.story_manager, self.region, badge))
            # Gym challenge (Jordan, 11-01): in place of the trainers, a minigame (src/minigames) to
            # win before the Leader, until the badge is earned.
            story = game.story_manager
            self.challenge = None
            if (not self.redo and badge and not story.has_badge(badge)
                    and not story.story_flags.get(minigames.done_flag(self.area_key))):
                self.challenge = minigames.pick(game, self.area_key, self._leader_team())
            elif not self.redo and story.story_flags.get(minigames.done_flag(self.area_key))                     and self.progress < len(self.trainers):
                self.progress = len(self.trainers)  # the challenge stood in for the trainers
                story.story_flags[self.prog_key] = self.progress
            if self.redo:  # the Leader alone, at full strength; the badge again, with a star
                self.next_opponent = self.leader
                self.status_text = (f"League Redo: {_fill_names(game, self.leader.get('name', 'The Leader'))}"
                                    " is waiting, at full strength!")
            elif self.challenge:
                self.status_text = (f"Gym Challenge: {self.challenge.title_for(game)}! Win it to face "
                                    f"{_fill_names(game, self.leader.get('name', 'the Leader'))}.")
            elif self.orange_rematch and self.progress > len(self.trainers):
                self.progress = 0
                game.story_manager.story_flags[self.prog_key] = 0
            if self.redo or self.challenge:
                pass
            elif self.progress < len(self.trainers):
                self.next_opponent = self.trainers[self.progress]
                self.status_text = f"Trainer {self.progress + 1}/{len(self.trainers) + 1} is up next!"
            elif self.progress == len(self.trainers) and self.leader:
                self.next_opponent = self.leader
                self.status_text = "The Gym Leader is ready for you."
            else:
                self.is_cleared = True
                self.status_text = "You have defeated this Gym!"

        self.bg = self._load_bg()

        self.bottom_rect = Utils.get_full_dialogue_rect(game)
        self.right_rect = pygame.Rect(
            self.bottom_rect.x + int(self.bottom_rect.width * 0.55),
            self.bottom_rect.y,
            self.bottom_rect.width - int(self.bottom_rect.width * 0.55),
            self.bottom_rect.height
        )

        self.btn_challenge = Button(
            rect=(self.right_rect.centerx - 100, self.right_rect.y + 25, 200, 60),
            text="CHALLENGE",
            font=game.assets.fonts["s_med"],
            callback=self.challenge_gym,
            bg_color=RED if not self.is_cleared else GRAY
        )

        self.btn_exit = Button(
            rect=(self.right_rect.centerx - 100, self.right_rect.y + 100, 200, 60),
            text="EXIT GYM",
            font=game.assets.fonts["s_med"],
            callback=self.exit_gym,
            bg_color=BLUE
        )
        # MENU, as in towns (Jordan): heal with the Bag and check the party between battles. No PC,
        # saving or Fly inside a Gym or the League, as in the games.
        tiny = game.assets.fonts["tiny"]
        self.hud_buttons = [
            Button((0, 0, 1, 1), "BAG", tiny, self._open_bag, bg_color=BLUE),
            Button((0, 0, 1, 1), "POKEMON", tiny, self._open_party, bg_color=GREEN),
            Button((0, 0, 1, 1), "BADGES", tiny, self._open_badges, bg_color=GOLD),
            Button((0, 0, 1, 1), "JOURNAL", tiny, self._open_journal, bg_color=PURPLE),
            Button((0, 0, 1, 1), "OPTIONS", tiny, self._open_options, bg_color=GRAY),
        ]
        _collapse_hud(self)

    def _open_bag(self):
        from src.states.systems import BagState
        self.game.change_state(BagState(self.game, self))

    def _open_party(self):
        from src.states.systems import PokemonPartyMenuState
        self.game.change_state(PokemonPartyMenuState(self.game, self, context="normal"))

    def _open_badges(self):
        from src.states.systems import BadgeCaseState
        self.game.change_state(BadgeCaseState(self.game, self))

    def _open_journal(self):
        from src.states.systems import JournalState
        self.game.change_state(JournalState(self.game, self))

    def _open_options(self):
        from src.states.menus import open_difficulty_options
        open_difficulty_options(self.game, self)

    def start(self):
        self.game.transitioning = False

        self.game.ui_manager.elements.clear()
        self.game.ui_manager.add_element(self.btn_challenge)
        self.game.ui_manager.add_element(self.btn_exit)
        for btn in self.hud_buttons:
            self.game.ui_manager.add_element(btn)

    # Kanto Champion (FireRed/LeafGreen): the rival's team by the starter they took.
    FRLG_RIVAL_LINE = {1: 1, 2: 1, 3: 1, 152: 1, 4: 4, 5: 4, 6: 4, 155: 4, 7: 7, 8: 7, 9: 7, 158: 7}
    FRLG_CHAMPION = {
        1: ([18, 65, 112, 130, 59, 3], [59, 57, 59, 59, 61, 63]),    # Venusaur
        4: ([18, 65, 112, 103, 130, 6], [59, 57, 59, 59, 61, 63]),   # Charizard
        7: ([18, 65, 112, 59, 103, 9], [59, 57, 59, 59, 61, 63]),    # Blastoise
    }

    # FireRed/LeafGreen rematch (post-Sevii) teams, used once the Champion has been beaten.
    FRLG_E4_REMATCH = {
        "LORELEI": ([87, 91, 221, 124, 131], [64, 63, 63, 66, 66]),
        "BRUNO": ([208, 107, 106, 208, 68], [65, 65, 65, 66, 68]),
        "AGATHA": ([94, 169, 200, 24, 94], [66, 66, 65, 68, 70]),
        "LANCE": ([130, 149, 230, 142, 149], [68, 66, 66, 70, 72]),
    }
    FRLG_CHAMPION_REMATCH = {
        1: ([214, 65, 248, 59, 130, 3], [72, 73, 72, 73, 73, 75]),   # Venusaur
        4: ([214, 65, 248, 130, 103, 6], [72, 73, 72, 73, 73, 75]),  # Charizard
        7: ([214, 65, 248, 103, 59, 9], [72, 73, 72, 73, 73, 75]),   # Blastoise
    }

    def _leader_team(self):
        """The Leader's team as it will be (some depend on your first partner)."""
        leader = self.leader or {}
        return list((leader.get("team_choice") or {}).get(str(_region_starter_id(self.game))) or leader.get("team") or [])

    def _start_challenge(self):
        """The Gym's minigame; win it and the Leader is next (its trainers' Poke Balls too)."""
        story = self.game.story_manager
        lead = next((p for p in story.player_team if p), None)

        def done(won):
            if won:
                story.story_flags[minigames.done_flag(self.area_key)] = True
                story.story_flags[self.prog_key] = len(self.trainers)
                story.balls_left += sum((t.get("rewards") or {}).get("balls", 0) for t in self.trainers) or 3
            if in_room(self.game):  # (a Gym walked inside: won, and the Leader's battle is next; lost, back in the room)
                if won:
                    GymLobbyState(self.game, None).challenge_gym()
                else:
                    back_to_room(self.game)
                return
            self.game.change_state(GymLobbyState(self.game, None))

        self.game.change_state(self.challenge(
            self.game, done, level=len(story.badges.get(self.region, [])), background=self.bg,
            leader=dict(self.leader or {}, name=_fill_names(self.game, (self.leader or {}).get("name"))),
            team=self._leader_team(), partner=getattr(lead, "id", 25)))

    def challenge_gym(self):
        if getattr(self, "challenge", None) and not self.game.transitioning:
            self._start_challenge()
            return
        if self.is_cleared or not self.next_opponent or self.game.transitioning:
            return

        self.game.transitioning = True

        t_data = _cast_trainer(self.game, self.next_opponent.copy())
        from src.states.battle import TrainerBattleState, TrainerIntroState

        is_leader = (self.next_opponent == self.leader)
        if self.area_key == "INDIGO_PLATEAU" and is_leader:
            # Champion: your KANTO rival (never the rival of a region you moved to), with their
            # FireRed/LeafGreen team and levels.
            kr = self.game.story_manager.region_rivals.get("KANTO") or {}
            rival_name = kr.get("name") or getattr(self.game, "rival_name", "BLUE")
            rival_char = kr.get("character") or getattr(self.game, "rival_character", "blue")
            trainer_sprite = rival_image(self.game, rival_char) or self.game.assets.get_trainer_image("rival.png")
            starter_id = self.game.story_manager.rival_starter_id("KANTO", 1)
            rematch = bool(self.game.story_manager.story_flags.get("beat_champion"))
            table = self.FRLG_CHAMPION_REMATCH if rematch else self.FRLG_CHAMPION
            team, team_levels = table.get(self.FRLG_RIVAL_LINE.get(starter_id, 4))
            t_data.update({"name": rival_name, "class": "CHAMPION", "team": list(team),
                           "levels": list(team_levels)})
            t_data["dialogue"] = {
                "intro": [f"{rival_name}: Hey, {self.game.player_name}!",
                          "I was looking forward to seeing you here.",
                          "My rival should be strong to keep me sharp. While working on the Pokedex, "
                          "I looked all over for powerful Pokemon. And now... I'm the Pokemon League Champion!",
                          f"{self.game.player_name}! Do you know what that means? I'll tell you. "
                          "I am the most powerful trainer in the world!"],
                "player_won": ["NO! That can't be! You beat my best!",
                               "After all that work to become League Champ? My reign is over already? "
                               "It's not fair!"],
                "player_lost": ["Hahaha! I won, I won! I'm too good for you, "
                                f"{self.game.player_name}!"],
            }
        else:
            trainer_sprite = _trainer_sprite(self.game, t_data.get("sprite"))
            choice = (t_data.get("team_choice") or {}).get(str(_region_starter_id(self.game)))
            if choice:
                t_data["team"] = list(choice)
            t_data["name"] = _fill_names(self.game, t_data.get("name"))
            if t_data.get("dialogue"):
                t_data["dialogue"] = {k: _resolve_lines(self.game, v) for k, v in t_data["dialogue"].items()}
        if self.redo:  # League Redo: six Pokemon at level 100, a starred badge instead of the badge
            name = t_data.get("name") or "Leader"
            t_data["team"] = league_redo.redo_team(self.game, self.region, t_data.get("team", []))
            t_data["levels"] = [league_redo.redo_level(self.game.story_manager)] * len(t_data["team"])
            badge = None if self.is_league else t_data.get("badge_reward")
            t_data["badge_reward"] = None
            if badge:
                t_data["victory_flag"] = league_redo.badge_flag(self.region, badge)
            elif is_leader:
                t_data["victory_flag"] = league_redo.champion_flag(self.region)
            else:
                t_data["victory_flag"] = None
            t_data["dialogue"] = dict(t_data.get("dialogue") or {},
                                      intro=league_redo.intro_lines(name, league=self.is_league),
                                      player_won=league_redo.won_lines(name, badge))
        # Rematches after the title: the games' rematch teams where we have them (FireRed/LeafGreen
        # for Kanto, HeartGold/SoulSilver for Johto: "rematch" in the data), else 10 levels up.
        rematch_boost = 0
        # A League rematch roster's non-League trainers (Galar's Marnie/Hop, Paldea's Nemona) are
        # post-game rematches: they follow the post-game cap. The Elite Four and Champion don't.
        cap_rematch = (getattr(self, "rematch", False) and not is_leader
                       and t_data.get("class") not in levels.LEAGUE_CLASSES and not t_data.get("rematch"))
        if (getattr(self, "rematch", False) and not cap_rematch
                and not (self.area_key == "INDIGO_PLATEAU" and is_leader)):
            rm = self.next_opponent.get("rematch")
            if not rm and self.area_key == "INDIGO_PLATEAU":
                frlg = self.FRLG_E4_REMATCH.get(str(t_data.get("name", "")).upper())
                rm = {"team": frlg[0], "levels": frlg[1]} if frlg else None
            if rm:  # a rematch without its own "team" keeps the (starter-dependent) team, canon levels
                t_data["team"] = list(rm.get("team") or t_data.get("team", []))
                t_data["levels"] = list(rm["levels"])
                if rm.get("movesets"):  # the rematch team's own canon moves
                    t_data["movesets"] = rm["movesets"]
            else:
                rematch_boost = 10

        team_ids = t_data.get("team", [])
        opponent_team = []
        for pid in team_ids:
            raw = self.game.loader.fetch_specific(pid)
            opponent_team.append(Pokemon(raw, self.game.assets, size_mult=3.125))
        forms.mark_trainer_team(opponent_team, t_data)
        region = self.game.story_manager.get_current_region()
        t_class = t_data.get("class", "GYM_LEADER")
        if cap_rematch:  # the region's title is won, so the League area is post-game: cap-2..cap
            team_levels = levels.trainer_team_levels(self.game, self.area_key, len(opponent_team))
        elif t_data.get("levels"):
            team_levels = t_data["levels"]  # exact levels from the games (Kanto's Champion)
        elif t_class == "ELITE_FOUR":
            team_levels = levels.elite_levels(region, self.progress, len(opponent_team))
        elif is_leader and (t_class in ("CHAMPION", "CHALLENGER") or self.leader.get("class") == "CHAMPION"):
            team_levels = levels.gym_team_levels(region, self.area_key, len(opponent_team), "champion")
            if t_class == "CHALLENGER":
                team_levels = [lv + 5 for lv in team_levels]  # title defenses after becoming Champion
        else:
            team_levels = levels.gym_team_levels(region, self.area_key, len(opponent_team),
                                                 levels.gym_role(t_class, is_leader))
        if getattr(self, "orange_rematch", False) and not self.is_league:
            team_levels = levels.orange_postgame_levels(self.gym_data, team_levels)
            t_data["badge_reward"] = None  # the badge was won before the title
        if rematch_boost:
            team_levels = [min(100, int(lv) + rematch_boost) for lv in team_levels]
        exact = bool(t_data.get("levels"))
        if self.is_league and getattr(self, "rematch", False) and not self.redo:
            team_levels, exact = league_rematch_levels(self.game.story_manager, team_levels), True
        levels.set_team(opponent_team, team_levels, exact=exact)

        bg_file = self.game.story_manager.get_gym_battle_background(
            self.area_key, trainer_index=self.progress, is_leader=is_leader
        )

        battle_state = TrainerBattleState(
            self.game, opponent_team, trainer_sprite=trainer_sprite,
            trainer_class=t_data.get("class", "GYM_LEADER"), trainer_name=t_data.get("name"),
            custom_dialogue=t_data.get("dialogue", {}), rewards=t_data.get("rewards"),
            battle_type="gym", is_boss_battle=True, area_name=self.area_key,
            badge_reward=t_data.get("badge_reward"), background_image=bg_file,
            victory_flag=t_data.get("victory_flag")  # Lance: beat_elite_four, Champion: beat_champion
        )

        intro_text = random.choice(t_data.get("dialogue", {}).get("intro", ["Prepare to battle!"]))
        self.game.change_state(TrainerIntroState(self.game, trainer_sprite, intro_text, battle_state))

    def exit_gym(self):
        from src.states.overworld.town import CityState
        from src.states.overworld import CityState
        self.game.change_state(CityState(self.game))

    def handle_events(self, events):
        pass

    def _load_bg(self):
        """The Gym's picture. A list of pictures is the Gym's rooms in order (a League's: one for each
        member): the trainers share the rooms before the last, the Leader (or Champion) has the last."""
        game = self.game
        bg_config = self.area_data.get("backgrounds", {}).get("gym")
        if isinstance(bg_config, list):
            n, t = len(bg_config), len(self.trainers)
            if not n:
                bg_config = None
            elif n > 1 and t and not self.redo and self.progress < t:
                bg_config = bg_config[self.progress * (n - 1) // t]
            else:
                bg_config = bg_config[0] if n == 1 or getattr(self, "challenge", None) else bg_config[-1]

        # ARCHITECT: Standardized fallback to [area_key]_gym.png (e.g. azalea_town_gym.png)
        fallback_name = f"{self.area_key.lower()}_gym.png"
        filenames = [bg_config, fallback_name] if bg_config else [fallback_name]
        size = (game.width, Utils.get_full_dialogue_rect(game).top)
        for filename in filenames:
            img = game.assets.get_background(filename)
            if img:
                return pygame.transform.scale(img, size)
        img = game.assets.get_generic_background("gym")
        if img:
            return pygame.transform.scale(img, size)
        bg = pygame.Surface((game.width, int(game.height * 0.75)))
        bg.fill((40, 40, 60))
        return bg

    def update(self):
        pass

    def draw(self):
        screen = self.game.screen
        screen.fill(BLACK)
        if self.bg:
            screen.blit(self.bg, (0, 0))
        theme.draw_textbox(screen, self.bottom_rect)
        from src.ui.dialogue import wrap_text
        f = self.game.assets.fonts["dialog"]
        rows = wrap_text(self.status_text, f, int(self.bottom_rect.width * 0.55) - 40)
        lh = int(f.get_linesize() * 1.2)
        top = self.bottom_rect.centery - lh * len(rows) // 2
        for k, row in enumerate(rows):
            theme.shadow_text(screen, row, f, self.bottom_rect.x + 40, top + k * lh)
        self.game.ui_manager.draw(screen)
