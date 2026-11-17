"""The Giant Volcano, walked as a Charmander (src/world/mystery_dungeon.py has the story; Jordan, 11-16).

A DungeonState with a Mystery Dungeon's look and rules: Explorers of Sky's own tiles (the lava glowing), every
Pokemon drawn with its PMD sprite (shiny ones in their shiny colours), you as the Charmander with your Vulpix a step
behind. Floors are made fresh each climb, there's no way back down, and HP comes back as you walk. Every battle,
Moltres's too, is fought right on the map (the OVERWORLD style), and wild Pokemon can't be caught. The top floor
holds the shiny Moltres (until it has joined you), else the way out at the summit."""
import pygame

from src.dungeon import core
from src.dungeon import pmd
from src.pokemon.data import Pokemon
from src.states.overworld.dungeon import TILE, DungeonState
from src.states.overworld.overworld_battle import OverworldView
from src.world import mystery_dungeon as md

SUMMIT = "SUMMIT"
SCALE = TILE / pmd.CHUNK        # (the sprites as big against the tiles as in the game)
REGEN_STEPS = 2                  # (a step or two of walking: a little HP back, as in the Mystery Dungeon games)

INTRO = ["...Ow... Where am I? Everything looks so big...",
         "You look down at your hands. Small orange paws! You've turned into a Charmander!",
         "Vulpix: Are you okay? You dropped right out of the sky!",
         "Vulpix: I'm Vulpix. I live here on the volcano. It's been rumbling for days, and the fire at the top won't settle.",
         "Vulpix: Will you climb to the summit with me and find out why?",
         "Vulpix joined you as your partner! Find the stairs on each floor and climb to the top!"]
INTRO_AGAIN = ["...You're a Charmander again!",
               "Vulpix: It's you! Back for another climb? Let's race to the summit!"]
THANKS = ["Vulpix: You did it! Listen... the volcano's gone quiet.",
          "Vulpix: Thank you for helping save the volcano. I couldn't have done it alone!",
          "Vulpix: I hope we'll see each other again soon!",
          "A bright light washes over everything..."]
THANKS_AGAIN = ["Vulpix: The summit! What a climb!",
                "Vulpix: Thanks for coming back to help the volcano. I hope we'll see each other again soon!",
                "A bright light washes over everything..."]


class PMDView(OverworldView):
    """A battle on the map, the Mystery Dungeon way: a boss fights where it stands too, and each side plays its
    attack and its hurt animations."""
    _line_up = staticmethod(OverworldView._line_up_wild)

    def _watch(self, battle):
        shots, fx = len(self.shots), len(self.fx)
        super()._watch(battle)
        play, now = self.play, pygame.time.get_ticks()
        for s in self.shots[shots:]:
            user = battle.player_pokemon if s[0] == "me" else battle.opponent_pokemon
            play._pmd_act[id(user)] = ("Attack", now)
        for f in self.fx[fx:]:
            hurt = battle.opponent_pokemon if f[0] == "foe" else battle.player_pokemon
            play._pmd_act[id(hurt)] = ("Hurt", now + 250)   # (once the attack has reached it)

    def _hp_bar(self, screen, name, hp, top, level, rect, mine):
        """As the classic, but when the foe stands below yours (a fight lined up down a corridor) the bars swap sides,
        so the two never overlap between them."""
        if self.spot[1] > self.mine[1] and self.spot[0] == self.mine[0]:
            return self._hp_bar_at(screen, name, hp, top, level, rect, mine, below=not mine)
        return super()._hp_bar(screen, name, hp, top, level, rect, mine)

    def _hp_bar_at(self, screen, name, hp, top, level, rect, mine, below):
        from src.ui import theme
        fonts = self.play.game.assets.fonts
        w = 84
        bar = pygame.Rect(0, 0, w, 10)
        if below:
            bar.midtop = (rect.centerx, rect.bottom + 14)
        else:
            bar.midbottom = (rect.centerx, rect.top - 30)
        pygame.draw.rect(screen, (20, 20, 30), bar.inflate(4, 4), border_radius=4)
        k = max(0, hp) / max(1, top)
        col = (90, 220, 110) if k > 0.5 else (240, 200, 60) if k > 0.2 else (230, 70, 60)
        pygame.draw.rect(screen, col, (bar.x, bar.y, int(w * k), bar.h), border_radius=3)
        tag = fonts["caption"].render(f"{name} Lv{level}", True, (255, 255, 255))
        box = tag.get_rect(midtop=(bar.centerx, bar.bottom + 2)) if below else tag.get_rect(midbottom=(bar.centerx, bar.y - 2))
        shade = pygame.Surface(box.inflate(10, 4).size, pygame.SRCALPHA)
        shade.fill((10, 14, 24, 150))
        screen.blit(shade, box.inflate(10, 4))
        screen.blit(tag, box)
        if mine:
            pygame.draw.rect(screen, (120, 200, 255), bar.inflate(4, 4), 2, border_radius=4)


class MysteryDungeonState(DungeonState):

    def __init__(self, game, restore_data=None, classic=False):
        fresh = not getattr(self, "_dungeon_ready", False)
        super().__init__(game, restore_data=restore_data, classic=classic)
        if fresh:
            self._pmd_act = {}       # id(pokemon) -> (animation, when it began): attacking, hurt
            self._glow = {}
            self._tiles = pmd.tileset(game, self.recipe.get("pmd") or "giant_volcano", TILE)
            self._said_intro = False
            self._regen = 0
            self._summit()
            self._partner_beside()

    # ---------------------------------------------------------------- who's who
    def _team(self):
        team = [p for p in self.game.story_manager.player_team if p]
        return (team + [None, None])[:2]

    def lead(self):
        """The one walking a step behind you: your partner (while it can). (In the top bar: you.)"""
        hero, partner = self._team()
        if self.__dict__.get("_in_hud"):
            return hero
        return partner if partner is not None and partner.current_hp > 0 else None

    def _draw_hud(self, screen):
        self._in_hud = True   # (the bar shows your own HP: the Charmander's)
        try:
            return super()._draw_hud(screen)
        finally:
            self._in_hud = False

    def _partner_beside(self, at=None):
        """Your partner on a free tile next to you (arriving on a floor, it isn't on top of you)."""
        if at is not None:
            return super()._partner_beside(at)
        f = self.run.floor
        px, py = self.run.player
        for dx, dy in ((0, 1), (-1, 0), (1, 0), (0, -1)):
            t = (px + dx, py + dy)
            if f.walkable(*t) and f.mover_at(*t) is None and t not in f.exits:
                self.partner = self.partner_from = t
                return

    def _ow_on(self):
        return True   # (every battle here is on the map)

    def _can_catch(self):
        return False

    # ---------------------------------------------------------------- the floors
    def _render_floor(self):
        if self._tiles is None or self.run.recipe.get("art") or self.run.recipe.get("image"):
            return super()._render_floor()
        f = self.run.floor
        self._floor_surf, self._glow = self._tiles.render(f, seed=self.run.index * 7919 + f.w)
        self._floor_index = self.run.index

    def _draw_tap_marks(self, screen, at):
        """(Just after the floor is drawn:) the lava's glow, on the tiles in view."""
        if self._tiles is not None and self._glow:
            k = self._tiles.frame_now()
            if k:
                clip = screen.get_clip()
                for (x, y), i in self._glow.items():
                    r = at(x, y)
                    if clip.colliderect(r):
                        screen.blit(self._tiles.chunk(i, k), r)
        super()._draw_tap_marks(screen, at)

    def _summit(self):
        """The top floor's way out (to wake up back home), in the room farthest from the stairs you came up by:
        once Moltres isn't there (beaten, or already with you)."""
        run = self.run
        if run.index != run.n_floors - 1:
            return
        f = run.floor
        if SUMMIT in f.exits.values() or any(m.kind == "figure" and isinstance(m.payload, dict)
                                              and m.payload.get("action") == "BOSS" for m in f.movers):
            return
        dist = core.distances(f, run.player)
        spots = [t for t, d in dist.items() if t not in f.exits and t not in f.items and f.mover_at(*t) is None
                 and f.tile(*t) == core.FLOOR]
        if spots:
            f.exits[max(spots, key=lambda t: dist[t])] = SUMMIT

    def _descend(self):
        super()._descend()
        self._summit()
        self._partner_beside()

    def _floor_name(self, index):
        return f"{index + 1}F"

    def _area_name(self, key):
        return "Summit" if key == SUMMIT else super()._area_name(key)

    def _gate(self, target):
        return None if target == SUMMIT else super()._gate(target)

    def _try_exit(self, target):
        if target == SUMMIT:
            self.walk_goal = None
            self._finish()
            return
        return super()._try_exit(target)

    # ---------------------------------------------------------------- arriving, walking
    def start(self):
        super().start()
        if not self._said_intro and self.mode == "MAP":
            self._said_intro = True
            again = self.game.story_manager.story_flags.get(md.CLEARS_FLAG)
            self.say(INTRO_AGAIN if again else INTRO)

    def step(self, dx, dy):
        before = self.run.player
        super().step(dx, dy)
        if self.run.player != before:
            self._regen += 1
            if self._regen >= REGEN_STEPS:
                self._regen = 0
                for p in self._team():
                    if p is not None and 0 < p.current_hp < p.get_max_hp():
                        p.current_hp = min(p.get_max_hp(), p.current_hp + max(1, p.get_max_hp() // 50))

    # ---------------------------------------------------------------- the wild Pokemon: Giant Volcano's, by floor
    def _wild_for_pool(self, rng, kind=None):
        pid, level = md.pick_wild(core.CURRENT_FLOOR + 1, rng)
        raw = self.game.loader._fetch_raw(id_pool=[pid], area_data=self.area_data)   # (rolls for a shiny, as anywhere)
        if not raw or raw.get("id", 0) == 0:
            return None
        p = Pokemon(raw, self.game.assets, size_mult=3.125)
        p.level = level
        p.current_hp = p.get_max_hp()
        return p

    def _meet_wild(self, mover):
        """Bump into one (or it into you): straight into a battle, right here."""
        self.walk_goal = None
        self.encounter = mover
        p = mover.payload
        self.game.data.mark_seen(p.id)
        if p.cry:
            p.cry.play()
        self._battle_wild(mover)

    def _battle_wild(self, mover):
        from src.states.battle import WildBattleState
        self.pending = ("wild", mover)
        self.mode = "MAP"
        self.rounds_completed += 1
        battle = WildBattleState(self.game, mover.payload, self.area_key,
                                 background_image=self._get_battle_background_for_area())
        battle.play_state_data = self._play_data()
        battle.no_catch = True   # (wild ones here can only be fought)
        battle.overworld = PMDView(self, mover)
        pygame.event.clear()
        self.game.change_state(battle)

    # ---------------------------------------------------------------- Moltres
    def _use_figure(self, mover):
        item = mover.payload
        if isinstance(item, dict) and item.get("action") == "BOSS":
            self.walk_goal = None
            boss = dict(self.area_data.get("area_boss") or {})
            self.say(boss.get("lines") or ["..."], then=lambda: self._boss_fight(mover, boss))
            return
        return super()._use_figure(mover)

    def _boss_fight(self, mover, boss):
        battle = self._capture_state(lambda: self.action_challenge_boss(dict(boss, lines=None)))
        if battle is None:
            return
        battle.no_catch = True   # (it joins you once you're home)
        battle.play_state_data = self._play_data()   # (back to this floor afterwards)
        battle.overworld = PMDView(self, mover)
        self.pending = ("boss", mover)
        self.mode = "MAP"
        pygame.event.clear()
        self.game.change_state(battle)

    def _back_from_battle(self):
        kind, mover = self.pending or (None, None)
        if kind == "boss":
            self.pending = None
            self._ow_foe = None
            self.encounter = None
            self.mode = "MAP"
            self.walk_goal = None
            if self.game.story_manager.story_flags.get(md.BEATEN_FLAG):
                self.run.remove(mover)
                self._finish_due = True   # (on the next frame: the battle's way back hides what's said now)
            return
        super()._back_from_battle()
        hero, partner = self._team()
        for down, up in ((hero, partner), (partner, hero)):   # (one of you fainted, the other won: back on your feet)
            if down is not None and up is not None and down.current_hp <= 0 < up.current_hp:
                down.current_hp = max(1, down.get_max_hp() // 4)
                if hasattr(down, "cure_status"):
                    down.cure_status()
                self.flash(f"{up.display_name.upper()} helped {down.display_name.upper()} back up!", 150)

    def update(self):
        super().update()
        if self.__dict__.get("_finish_due") and self.mode == "MAP" and not self.dialogue_box.visible:
            self._finish_due = False
            self._finish()

    def _finish(self):
        """The summit: Vulpix's thanks, then a flash of light and you wake up in the Lab."""
        story = self.game.story_manager
        moltres = story.story_flags.get(md.BEATEN_FLAG) and not story.story_flags.get(md.MOLTRES_FLAG)
        story.story_flags[md.CLEARS_FLAG] = int(story.story_flags.get(md.CLEARS_FLAG) or 0) + 1
        self.say(THANKS if moltres or story.story_flags[md.CLEARS_FLAG] == 1 else THANKS_AGAIN,
                 then=lambda: md.wake_in_lab(self.game, md.WON_MOLTRES if moltres else md.WON))

    # ---------------------------------------------------------------- the sprites
    def _pmd_anim(self, pokemon, moving):
        act = self._pmd_act.get(id(pokemon))
        if act:
            name, began = act
            ms = pygame.time.get_ticks() - began
            length = pmd.length_ms(self.game, self._pid(pokemon), name, bool(getattr(pokemon, "is_shiny", False)))
            if 0 <= ms < max(length, 300):
                return name, ms
            if ms >= 0:
                self._pmd_act.pop(id(pokemon), None)
        return ("Walk" if moving else "Idle"), None

    @staticmethod
    def _pid(pokemon):
        return int(getattr(pokemon, "meta_id", None) or pokemon.id) if int(pokemon.id) >= 2000 else int(pokemon.id)

    def _follower_img(self, pokemon, facing):
        pid = self._pid(pokemon)
        if not pmd.has(self.game, pid):
            return super()._follower_img(pokemon, facing)
        moving = pokemon is self.lead() and self.anim > 0
        anim, ms = self._pmd_anim(pokemon, moving)
        return pmd.image(self.game, pid, bool(getattr(pokemon, "is_shiny", False)), anim, facing, ms=ms, scale=SCALE,
                         loop=ms is None)

    def _player_img(self):
        """You: the Charmander. (In a battle on the map, the one of you not fighting stands where you stand.)"""
        hero, partner = self._team()
        me = hero
        if self._backdrop:
            fighting = getattr(getattr(self.game, "current_state", None), "player_pokemon", None)
            if fighting is hero:
                me = partner if partner is not None and partner.current_hp > 0 else None
        if me is None:
            return None
        if me is not hero:
            return self._follower_img(me, self.facing)
        anim, ms = self._pmd_anim(me, self.anim > 0)
        return pmd.image(self.game, md.HERO, bool(getattr(me, "is_shiny", False)), anim, self.facing, ms=ms,
                         scale=SCALE, loop=ms is None)
