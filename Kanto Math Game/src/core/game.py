# [REF-0001: System Imports]
import pygame
import os
import json
import sys

# [FIX] Import config to trigger pygame.init()
import src.config
from src.config import FPS, VOLUME, MUSIC_ENDED_EVENT, LOGICAL_W, LOGICAL_H

# [FIX] Import necessary modules
from src.utils import Utils
from src.core.assets import AssetManager
from src.core.data import DataManager
from src.core.math_engine import MathEngine
from src.core.music import MusicManager
from src.ui.keyboard import KeyboardNav
from src.world.story import StoryManager
from src.pokemon.loader import PokemonLoader
from src.ui.manager import UIManager
from src.ui.dialogue import ClassicDialogueBox
from src.states.menus import MainMenuState, CharacterSelectionState
from src.states.overworld import PlayState, CityState


# [REF-0043: Main Game Class]
class Game:
    def __init__(self):
        # One fixed canvas on every device: the game always lays out at 1280x720 and SDL scales
        # it to the window (letterboxed, taps mapped back). Every screen looks the same on any
        # monitor or tablet, and the window can be resized freely.
        self.width, self.height = LOGICAL_W, LOGICAL_H

        # Platform Detection
        is_android = "ANDROID_ARGUMENT" in os.environ or "ANDROID_PRIVATE" in os.environ
        self.is_pc = (sys.platform in ["win32", "linux", "darwin"]) and not is_android
        os.environ.setdefault("SDL_RENDER_SCALE_QUALITY", "1")  # smooth scaling, not blocky
        # Fullscreen everywhere (Jordan). On a PC, F11 switches between fullscreen and a window.
        mode = pygame.SCALED | pygame.FULLSCREEN
        try:
            self.screen = pygame.display.set_mode((self.width, self.height), mode)
        except pygame.error:  # no renderer (headless tests): a plain window of the same size
            self.screen = pygame.display.set_mode((self.width, self.height))

        self.assets = AssetManager(self.width, self.height)
        from src.ui.widgets import Button
        Button.sounds = {k: v for k, v in self.assets.ui_sfx.items() if v}
        self.data = DataManager(self.assets.base_dir)
        self.math = MathEngine(
            Utils.find_json_file(self.assets.assets_dir, "math_levels.json")
        )
        self.story_manager = StoryManager()
        self.story_manager.game = self
        self.debug_mode = False
        self.player_name = "TRAINER"
        self.player_character = "red"
        self.rival_character = "blue"
        self.preloaded_starter_data = []

        # === ROBUST JSON LOADING ===
        data_files = {
            "names": "pokemon_names.json",
            "movesets": "pokemon_movesets.json",
            "evolutions": "pokemon_evolutions.json",
            "area_data": "pokemon_area_data.json",
            "johto": "johto_area_data.json",
            "hoenn": "hoenn_area_data.json",
            "sinnoh": "sinnoh_area_data.json",
            "unova": "unova_area_data.json",
            "kalos": "kalos_area_data.json",
            "alola": "alola_area_data.json",
            "galar": "galar_area_data.json",
            "paldea": "paldea_area_data.json",
            "orange": "orange_area_data.json",
            "sevii": "sevii_area_data.json",
            "decolore": "decolore_area_data.json",
            "sinjoh": "sinjoh_area_data.json",
            "orre": "orre_area_data.json",
            "dlc": "dlc_area_data.json",
        }

        loaded_evolutions = {}
        loaded_area_data = {}

        print("\n=== JSON LOADING ===")
        for key, base_name in data_files.items():
            path = Utils.find_json_file(self.assets.assets_dir, base_name)
            if path:
                try:
                    with open(path, "r", encoding="utf-8-sig") as f:
                        data = json.load(f)
                    if key == "names":
                        self.assets.pokemon_names = data
                    elif key == "movesets":
                        self.assets.movesets = data
                        # Fallback: if names still missing, use movesets names
                        if not self.assets.pokemon_names:
                            self.assets.pokemon_names = {k: v.get("name", f"#{k}") for k, v in data.items()}
                    elif key == "evolutions":
                        loaded_evolutions = data
                    elif key == "area_data":
                        loaded_area_data = data
                        self.boss_warnings = data.get(
                            "BOSS_WARNINGS", {}
                        )
                        self.assets.game_text = data.get("GAME_TEXT", {})
                    else:
                        # [UPDATE] Generic Regional Data Merging (Johto, Hoenn, etc.)
                        if "STORY_PROGRESSION" in data:
                            if "STORY_PROGRESSION" not in loaded_area_data:
                                loaded_area_data["STORY_PROGRESSION"] = {}
                            loaded_area_data["STORY_PROGRESSION"].update(data["STORY_PROGRESSION"])
                        # Each mission belongs to the region whose file it came from.
                        file_region = os.path.basename(path).split("_area_data")[0].upper()
                        for m in data.get("JOURNAL_MISSIONS", []) or []:
                            m.setdefault("region", file_region)
                        for k, v in data.items():
                            if k == "STORY_PROGRESSION":
                                continue
                            
                            # Merge Dictionaries (GAME_TEXT, FORM_MAP, TYPE_CHART)
                            if isinstance(v, dict) and k in loaded_area_data and isinstance(loaded_area_data[k], dict):
                                loaded_area_data[k].update(v)
                            # Concatenate Lists (JOURNAL_MISSIONS)
                            elif isinstance(v, list) and k in loaded_area_data and isinstance(loaded_area_data[k], list):
                                loaded_area_data[k].extend(v)
                            else:
                                loaded_area_data[k] = v

                    print(f"✓ Loaded {os.path.basename(path)}")
                except Exception as e:
                    print(f"✗ Parse error on {os.path.basename(path)}: {e}")

        # Kanto's missions live in its GAME_CONFIG; put them in the journal list too.
        kanto_missions = loaded_area_data.get("GAME_CONFIG", {}).get("JOURNAL_MISSIONS", [])
        for m in kanto_missions:
            m.setdefault("region", "KANTO")
        known = {m.get("id") for m in loaded_area_data.get("JOURNAL_MISSIONS", [])}
        loaded_area_data["JOURNAL_MISSIONS"] = (
            [m for m in kanto_missions if m.get("id") not in known]
            + loaded_area_data.get("JOURNAL_MISSIONS", []))

        print("=== JSON LOADING COMPLETE ===\n")

        self.loader = PokemonLoader(self)
        if loaded_evolutions:
            self.loader.evolution_map = loaded_evolutions
        self.loader.load_level_data(self.assets.assets_dir)

        if loaded_area_data:
            self.loader.area_data = loaded_area_data
            # [FIX] Ensure the AssetManager text dictionary is pointed to the final merged result.
            # This ensures Johto keys like 'johto_mom_home' are actually accessible.
            if "GAME_TEXT" in loaded_area_data:
                self.assets.game_text = loaded_area_data["GAME_TEXT"]

        self.loader.start()

        self.name_to_id = {}
        for pid in range(1, 1026):
            try:
                data = self.loader.fetch_specific(pid)
                self.name_to_id[data["name"].upper()] = pid
            except:
                continue
        # Names like "WORMADAM-PLANT" also answer to their base name ("WORMADAM"),
        # which is how the evolution map refers to them.
        for name, pid in sorted(self.name_to_id.items(), key=lambda kv: kv[1]):
            if "-" in name:
                self.name_to_id.setdefault(name.split("-", 1)[0], pid)

        self.ui_manager = UIManager()
        self.clock = pygame.time.Clock()
        self.current_song_index = 0
        self.event_handlers = []
        self.states = {
            "play": PlayState(self),
        }
        self.ui_manager.elements.clear()

        self.current_state = MainMenuState(self)

        self.current_state.start()

        self.keyboard = KeyboardNav(self)
        self.music = MusicManager(self)
        self.music.for_state(self.current_state)

    def show_dialogue(self, lines, callback=None):
        """One-line way to show a golden text box anywhere"""
        box_rect = pygame.Rect(40, self.height - 200, self.width - 80, 160)
        box = ClassicDialogueBox(box_rect, lines, self.assets.fonts["med"], callback, auto_hide=True)
        # Nothing else updates this box, so it types itself out as it's drawn (the Bag's "grew to
        # Lv 12!" and "can't grow past the cap" messages used to stay blank).
        box.self_update = True
        self.ui_manager.add_element(box)
        return box

    def play_music(self):
        try:
            pygame.mixer.music.load(self.assets.music_playlist[self.current_song_index])
            pygame.mixer.music.set_volume(VOLUME)
            pygame.mixer.music.play()
            pygame.mixer.music.set_endevent(MUSIC_ENDED_EVENT)
        except Exception:
            pass

    def add_event_handler(self, handler):
        self.event_handlers.append(handler)

    def start_new_game(self):
        self.data.wipe_data()
        self.story_manager = StoryManager()
        self.story_manager.game = self

        config = self.loader.area_data.get("GAME_CONFIG", {})
        self.story_manager.initialize_new_game(config)
        
        self.change_state(CharacterSelectionState(self))

    def update_save_data(self):
        # The route keeps its own ball count; saving from a menu on top of it must use it too.
        route = self.current_state if isinstance(self.current_state, PlayState) else None
        prev = getattr(self.current_state, "previous_state", None)
        if route is None and isinstance(prev, PlayState):
            route = prev
        if route is not None:
            self.story_manager.balls_left = route.balls_left
            self.story_manager.current_streak = route.current_streak
            
        self.data.data["story"] = self.story_manager.serialize()
        self.data.data["story"]["player_name"] = self.player_name
        self.data.data["story"]["player_char"] = self.player_character
        self.data.data["story"]["rival_char"] = self.rival_character

    def load_game_data(self):
        story_data = self.data.data.get("story")
        if not story_data:
            return False

        self.player_name = story_data.get("player_name", "TRAINER")
        self.player_character = story_data.get("player_char", "red")
        self.rival_character = story_data.get("rival_char", "blue")
        self.rival_name = story_data.get("rival_name", "???")
        self.rival_true_name = story_data.get("rival_true_name", "BLUE")

        self.story_manager = StoryManager()
        self.story_manager.game = self
        self.story_manager.deserialize(story_data, self.loader)
        prog = self.loader.area_data.get("STORY_PROGRESSION", {})
        if self.story_manager.current_area_key not in prog:  # unknown area: back to the region's start
            self.story_manager.current_area_key = self.story_manager.get_region_start().get("start_area", "PALLET_TOWN")

        area_key = self.story_manager.current_area_key
        area_info = self.loader.area_data.get("STORY_PROGRESSION", {}).get(area_key, {})
        if area_info.get("area_type") == "town":
            self.states["city"] = CityState(self)
            self.change_state(self.states["city"])
        else:
            self.states["play"] = PlayState(self)
            self.change_state(self.states["play"])
        return True

    FADE_FRAMES = 6  # ~0.25 s crossfade between screens

    def change_state(self, new_state):
        if getattr(self, "screen", None) is not None and getattr(self, "current_state", None) is not None:
            self._fade_from = self.screen.copy()
            self._fade_left = self.FADE_FRAMES
        self.ui_manager.elements.clear()
        self.event_handlers.clear()
        pygame.event.clear()
        self.state_changed_at = pygame.time.get_ticks()
        self.current_state = new_state
        if hasattr(self, "music"):
            self.music.for_state(new_state)
        self.current_state.start()
        if hasattr(new_state, "ui_elements"):
            self.ui_manager.elements = new_state.ui_elements

    def run(self):
        while True:
            if not pygame.display.get_active():
                # Minimized: keep answering the window's events (Windows marks a window that
                # stops reading them as "Not Responding" and offers to close it), but skip drawing.
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                pygame.time.wait(100)
                continue
            try:
                self._frame()
            except SystemExit:
                raise
            except Exception:
                self._recover_from_error()
            try:
                pygame.display.flip()
            except pygame.error:  # the screen can be lost for a moment while the window comes back
                pass
            self.clock.tick(FPS)

    def toggle_fullscreen(self):
        """F11 on a PC: fullscreen <-> a window."""
        try:
            pygame.display.toggle_fullscreen()
        except pygame.error:
            pass

    def _recover_from_error(self):
        """Safety net: an unexpected error writes crash.log and returns to the current town or
        route instead of closing the game. Errors that keep repeating still stop it."""
        import time
        import traceback
        now = time.time()
        recent = [t for t in getattr(self, "_error_times", []) if now - t < 10] + [now]
        self._error_times = recent
        try:
            with open(os.path.join(self.assets.base_dir, "crash.log"), "a", encoding="utf-8") as f:
                f.write(f"\n=== {time.ctime(now)} in {type(self.current_state).__name__} ===\n")
                f.write(traceback.format_exc())
        except OSError:
            pass
        traceback.print_exc()
        if len(recent) >= 3:
            raise  # the same thing keeps going wrong: don't loop forever
        story = self.story_manager
        area = self.loader.area_data.get("STORY_PROGRESSION", {}).get(story.current_area_key, {})
        try:
            safe = CityState(self) if area.get("area_type") == "town" else PlayState(self)
            self.change_state(safe)
            self.show_dialogue(["Oops! Something went wrong, so we came back here.",
                                "Your progress is safe."])
        except Exception:
            self.change_state(MainMenuState(self))

    def _frame(self):
        """One frame: input, update, draw (run() wraps it in the safety net)."""
        events = pygame.event.get()
        # Arrow keys / Enter / Esc drive the on-screen buttons (see src/ui/keyboard.py).
        events = [e for e in events if not self.keyboard.handle(e)]
        # Capture current state to detect changes mid-loop
        frame_start_state = self.current_state

        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F3:
                self.debug_mode = not self.debug_mode
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F11 and self.is_pc:
                self.toggle_fullscreen()
            if event.type == MUSIC_ENDED_EVENT:
                self.music.on_track_end()
            for handler in self.event_handlers:
                handler(event)

            # Ghost Click Prevention:
            # If state changed during event processing (e.g. button click),
            # abort processing remaining events for the old state.
            if self.current_state != frame_start_state:
                break

        # Taps right after a screen change are ignored (a double-tap must not press a
        # button on the new screen), and each tap is routed on its own.
        if pygame.time.get_ticks() - getattr(self, "state_changed_at", -10**6) < 150:
            events = [e for e in events if e.type not in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP)]
        if self.current_state is frame_start_state:
            remaining = self.ui_manager.unconsumed(
                events, lambda: self.current_state is not frame_start_state)
            if remaining and self.current_state is frame_start_state:
                self.current_state.handle_events(remaining)
        self.current_state.update()
        if hasattr(self, "music"):
            self.music.update()  # a fanfare that ended lets the music carry on
        self.current_state.draw()
        self.keyboard.draw(self.screen)
        if getattr(self, "_fade_left", 0) > 0 and self._fade_from is not None:
            self._fade_from.set_alpha(int(255 * self._fade_left / self.FADE_FRAMES))
            self.screen.blit(self._fade_from, (0, 0))
            self._fade_left -= 1


# [REF-0059: Main Execution]
if __name__ == "__main__":
    Game().run()
