"""Background music by situation: towns, routes, wild/trainer/gym battles, and a victory jingle.

Tracks are found in assets/sounds by name: every file whose name has the kind's word in it
(kanto_wild2.ogg, music_town.wav, kanto_battle1.mp3 for gyms). If the current region has its
own files (johto_town1.ogg) only those are used. New files dropped in are picked up automatically.

Kanto has its own soundtrack (assets/music/kanto, from Pokemon Journeys V18 - Jordan): every town,
route and dungeon plays its own theme, as in the games, and battles use the Kanto battle themes.
The title screen plays the Hall of Fame theme.

The rest of that soundtrack plays everywhere: the Pokemon Center, labs, Mom's house, Professor
Oak, the Game Corner, evolution and the trainer-encounter themes as screen music; and the
fanfares (healed, item, key item, caught, level up, badge, evolved) as jingles that pause the
music, play once and let it carry on where it was. Jingles are cued by the text box lines that
announce those moments ("... grew to Lv 12!"), see line_cue.
"""
import re
import os
import random

import pygame

from src.config import VOLUME

# kind -> file-name keywords, best first
KINDS = {
    "town": ("town",),
    "route": ("route",),
    "wild": ("wild",),
    "trainer": ("trainer",),
    "gym": ("gym", "battle"),
    "victory": ("victory",),
    "final": ("gym", "battle"),     # Elite Four and Champion (Kanto: the final battle theme)
    "gym_lobby": ("gym",),
    "title": ("town",),
}

# Kanto (assets/music/kanto): the area's own theme, as the games share them out.
KANTO_AREAS = {
    "PALLET_TOWN": "pallet_town", "VIRIDIAN_CITY": "pewter_city", "PEWTER_CITY": "pewter_city",
    "SAFFRON_CITY": "pewter_city", "CERULEAN_CITY": "cerulean_city", "FUCHSIA_CITY": "cerulean_city",
    "VERMILLION_CITY": "vermilion_city", "LAVENDER_TOWN": "lavender_town", "CELADON_CITY": "celadon_city",
    "CINNABAR_ISLAND": "cinnabar_island", "INDIGO_PLATEAU": "pokemon_center", "BILLS_HOUSE": "route_24",
    "SILPH_CITY": "silph_co", "MT_MOON_CITY": "mt_moon", "ROCK_TUNNEL_CITY": "mt_moon",
    "POKEMON_LEAGUE_GATE": "route_22", "UNDERGROUND_PATH": "route_11",
    "VIRIDIAN_FOREST": "viridian_forest", "MT_MOON": "mt_moon", "ROCK_TUNNEL": "mt_moon",
    "DIGGLETT_CAVE": "mt_moon", "SEAFOAM_ISLANDS": "mt_moon", "CERULEAN_CAVE": "mt_moon",
    "VICTORY_ROAD": "mt_moon", "CINNABAR_VOLCANO": "pokemon_mansion", "KANTO_POKEMON_TOWER": "pokemon_tower",
    "KANTO_SS_ANNE": "ss_anne", "SAFARI_ZONE": "safari_zone", "POWER_PLANT": "rocket_hideout",
}
for _n in (1, 2):
    KANTO_AREAS[f"KANTO_ROUTE_{_n}"] = "route_1"
for _n in range(3, 11):
    KANTO_AREAS[f"KANTO_ROUTE_{_n}"] = "route_3"
for _n in range(11, 16):
    KANTO_AREAS[f"KANTO_ROUTE_{_n}"] = "route_11"
for _n in range(16, 19):
    KANTO_AREAS[f"KANTO_ROUTE_{_n}"] = "route_16"
for _n in range(19, 22):
    KANTO_AREAS[f"KANTO_ROUTE_{_n}"] = "route_19"
for _n in (22, 23, 26, 27, 28):
    KANTO_AREAS[f"KANTO_ROUTE_{_n}"] = "route_22"
for _n in (24, 25):
    KANTO_AREAS[f"KANTO_ROUTE_{_n}"] = "route_24"
KANTO_KINDS = {"wild": "wild_pokemon_battle", "trainer": "trainer_battle", "gym": "gym_battle",
               "final": "final_battle", "gym_lobby": "pokemon_gym", "victory": "victory_trainer"}
# Screen music from the same soundtrack, in every region.
THEMES = {"center": "pokemon_center", "lab": "oak_lab", "oak": "professor_oak", "home": "home",
          "game_corner": "game_corner", "evolution": "evolution", "enc_male": "male_trainer_appears",
          "enc_female": "female_trainer_appears", "enc_rocket": "team_rocket_appears",
          "enc_rival": "rival_theme", "enc_jessie": "jessie_james"}
# Jingles, cued by the line that announces the moment (first match wins).
JINGLE_CUES = (
    (re.compile(r"received the .*badge", re.I), "earn_gym_badge"),
    (re.compile(r"grew to lv", re.I), "level_up"),
    (re.compile(r"evolved into", re.I), "congrats_evolve"),
    (re.compile(r"you caught .*!|was caught!", re.I), "pokemon_caught"),
    (re.compile(r"restored your team|team is (fully )?healed|back to full health", re.I), "pokemon_healed"),
    (re.compile(r"received the ", re.I), "key_item"),
    (re.compile(r"\byou (picked|got) \d", re.I), "picked_up_an_item"),
)
# Trainer classes whose encounter is the girls' theme, and the villain teams.
FEMALE_CLASSES = {"LASS", "BEAUTY", "PICNICKER", "AROMA_LADY", "BATTLE_GIRL", "PARASOL_LADY", "SWIMMER_F",
                  "COOLTRAINER_F", "TWINS", "KIMONO_GIRL", "MEDIUM", "CHANNELER", "LADY", "NURSE", "IDOL",
                  "POKEFAN_F", "SCHOOL_KID_F", "PSYCHIC_F", "TUBER_F", "CRUSH_GIRL", "ACE_TRAINER_F",
                  "SKIER", "MAID", "WAITRESS", "DANCER", "ARTIST_F", "VETERAN_F", "SCIENTIST_F"}
VILLAIN_WORDS = ("ROCKET", "MAGMA", "AQUA", "GALACTIC", "PLASMA", "FLARE", "SKULL", "MACRO", "YELL", "STAR",
                 "CIPHER", "GRUNT", "ADMIN", "BOSS")

_current = None  # the game's MusicManager (for line_cue)


def line_cue(text):
    """A text box line just came up: play its fanfare, if it announces one."""
    if _current is not None:
        _current.cue(text)
EXTS = (".ogg", ".mp3", ".wav")


class MusicManager:
    def __init__(self, game):
        self.game = game
        global _current
        _current = self
        self.kind = None
        self.path = None      # the track playing
        self.jingle_channel = None  # a fanfare playing over the paused music
        self.pending = None   # what to play once the victory jingle ends

    def tracks(self, kind, region=None):
        files = getattr(self.game.assets, "sound_map", {})
        names = [f for f in files if f.endswith(EXTS)]
        words = KINDS.get(kind, ())
        matches = [f for f in names if any(w in os.path.splitext(f)[0] for w in words)]
        if region:
            own = [f for f in matches if f.startswith(region.lower() + "_")]
            if own:  # this region's tracks (plus the built-in ones), not other regions'
                return [files[f] for f in matches if f in own or f.startswith("music_")]
        return [files[f] for f in matches]

    def kanto_track(self, kind, region):
        """Kanto's own track for this kind of music here (the area's theme, the battle themes),
        or None. The title screen's Hall of Fame theme plays anywhere."""
        folder = os.path.join(getattr(self.game.assets, "assets_dir", "") or "", "music", "kanto")
        if not os.path.isdir(folder):
            return None
        if kind == "title":
            name = "hall_of_fame"
        elif kind in THEMES:
            name = THEMES[kind]
        elif region != "KANTO":
            return None
        elif kind in ("town", "route"):
            name = KANTO_AREAS.get(getattr(self.game.story_manager, "current_area_key", ""))
        elif kind == "victory":
            name = "gym_victory" if self.kind in ("gym", "final") else KANTO_KINDS["victory"]
        else:
            name = KANTO_KINDS.get(kind)
        path = os.path.join(folder, f"{name}.mp3") if name else None
        return path if path and os.path.isfile(path) else None

    def play(self, kind, force=False):
        """Switch to this kind of music (no restart if the same track is already playing)."""
        if not pygame.mixer.get_init():
            return
        if self.kind == "victory" and kind != "victory" and pygame.mixer.music.get_busy():
            self.pending = kind  # let the jingle finish first
            return
        region = None
        try:
            region = self.game.story_manager.get_current_region()
        except Exception:
            pass
        path = self.kanto_track(kind, region)
        if path and path == self.path and pygame.mixer.music.get_busy() and not force:
            return
        if not path:
            if kind == self.kind and pygame.mixer.music.get_busy() and not force and not self._was_kanto():
                return
            choices = self.tracks(kind, region)
            if not choices:
                return
            path = os.path.join(self.game.assets.sounds_dir, random.choice(choices))
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(VOLUME)
            pygame.mixer.music.play(0 if kind == "victory" else -1)
            pygame.mixer.music.set_endevent(self._end_event())
            self.kind = kind
            self.path = path
        except Exception as e:
            print(f"Music: couldn't play {path}: {e}")

    # ---- jingles
    def cue(self, text):
        for pattern, name in JINGLE_CUES:
            if pattern.search(str(text)):
                self.jingle(name)
                return

    def jingle(self, name):
        """Pause the music, play the fanfare once; update() lets the music carry on after it."""
        if not pygame.mixer.get_init():
            return
        path = os.path.join(getattr(self.game.assets, "assets_dir", "") or "", "music", "kanto", f"{name}.mp3")
        if not os.path.isfile(path):
            return
        try:
            sound = pygame.mixer.Sound(path)
        except Exception as e:
            print(f"Music: couldn't play {path}: {e}")
            return
        if self.jingle_channel and self.jingle_channel.get_busy():
            self.jingle_channel.stop()
        pygame.mixer.music.pause()
        sound.set_volume(VOLUME)
        self.jingle_channel = sound.play()

    def update(self):
        """Each frame: once a fanfare ends, the music goes on from where it paused."""
        if self.jingle_channel is not None and not self.jingle_channel.get_busy():
            self.jingle_channel = None
            pygame.mixer.music.unpause()

    def encounter_kind(self, battle):
        """The 'eyes meet' theme for the trainer about to battle (None for leaders and the like)."""
        cls = str(getattr(battle, "trainer_class", "") or "").upper()
        name = str(getattr(battle, "trainer_name", "") or "").upper()
        if cls in ("GYM_LEADER", "ELITE_FOUR", "CHAMPION", "WILD", ""):
            return None
        if "JESSIE" in name or "JAMES" in name:
            return "enc_jessie"
        if cls.startswith("RIVAL") or name == str(getattr(self.game, "rival_name", "")).upper():
            return "enc_rival"
        if any(w in cls for w in VILLAIN_WORDS):
            return "enc_rocket"
        if cls in FEMALE_CLASSES or cls.endswith("_F"):
            return "enc_female"
        return "enc_male"

    def _was_kanto(self):
        """True while a Kanto area theme plays (leaving it for another kind of place changes it)."""
        return bool(self.path) and os.sep + "kanto" + os.sep in self.path

    def victory(self):
        self.pending = None
        self.play("victory", force=True)

    def on_track_end(self):
        """MUSIC_ENDED_EVENT: after the jingle, go back to the area's music."""
        if self.kind == "victory":
            self.kind = None
            if self.pending:
                kind, self.pending = self.pending, None
                self.play(kind)

    def for_state(self, state):
        """Pick the music for a screen the game just switched to (menus keep what's playing)."""
        from src.states.battle import TrainerBattleState, WildBattleState
        from src.states.overworld import CityState, PlayState, GymLobbyState
        from src.states.menus import MainMenuState
        if isinstance(state, WildBattleState):
            kind = "gym" if getattr(state, "is_boss_battle", False) else "wild"
        elif isinstance(state, TrainerBattleState):
            big = (state.battle_type == "gym" or getattr(state, "is_boss_battle", False)
                   or state.trainer_class in ("GYM_LEADER", "ELITE_FOUR", "CHAMPION"))
            kind = ("final" if state.trainer_class in ("ELITE_FOUR", "CHAMPION")
                    else "gym" if big else "trainer")
        elif isinstance(state, GymLobbyState):
            kind = "gym_lobby"
        elif type(state).__name__ == "PokeCenterState":
            kind = "center"
        elif type(state).__name__ == "EvolutionState":
            kind = "evolution"
        elif type(state).__name__ in ("GameCornerState", "SlotMachineState", "GameCornerShopState"):
            kind = "game_corner"
        elif type(state).__name__ == "StarterSelectionState":
            kind = "lab"
        elif type(state).__name__ == "TrainerIntroState":
            kind = self.encounter_kind(getattr(state, "next_state", None))
            if kind is None:
                return
        elif isinstance(state, MainMenuState):
            kind = "title"
        elif isinstance(state, CityState):
            kind = "town"
        elif isinstance(state, PlayState):
            kind = "route"
        else:
            return
        self.play(kind)

    @staticmethod
    def _end_event():
        from src.config import MUSIC_ENDED_EVENT
        return MUSIC_ENDED_EVENT
