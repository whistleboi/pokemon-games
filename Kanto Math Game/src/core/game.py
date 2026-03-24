# [REF-0001: System Imports]
import pygame
import os
import json
import sys

# [FIX] Import config to trigger pygame.init()
import src.config
from src.config import FPS, VOLUME, MUSIC_ENDED_EVENT

# [FIX] Import necessary modules
from src.utils import Utils
from src.core.assets import AssetManager
from src.core.data import DataManager
from src.world.story import StoryManager
from src.pokemon.loader import PokemonLoader
from src.ui.manager import UIManager
from src.ui.dialogue import ClassicDialogueBox
from src.states.menus import MainMenuState, CharacterSelectionState
from src.states.overworld import PlayState, CityState


# [REF-0043: Main Game Class]
class Game:
    def __init__(self):
        info = pygame.display.Info()
        self.width, self.height = info.current_w, info.current_h

        # Platform Detection
        is_android = "ANDROID_ARGUMENT" in os.environ or "ANDROID_PRIVATE" in os.environ
        self.is_pc = (sys.platform in ["win32", "linux", "darwin"]) and not is_android
        if self.is_pc:
            self.screen = pygame.display.set_mode(
                (self.width, self.height), pygame.RESIZABLE
            )
        else:
            self.screen = pygame.display.set_mode(
                (self.width, self.height), pygame.FULLSCREEN
            )

        self.assets = AssetManager(self.width, self.height)
        self.data = DataManager(self.assets.base_dir)
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
            "johto_data": "johto_area_data.json",
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
                    elif key == "johto_data":
                        if "STORY_PROGRESSION" in data:
                            if "STORY_PROGRESSION" not in loaded_area_data:
                                loaded_area_data["STORY_PROGRESSION"] = {}
                            loaded_area_data["STORY_PROGRESSION"].update(data["STORY_PROGRESSION"])
                        # Merge other keys (wild pools, dialogue, etc)
                        for k, v in data.items():
                            if k != "STORY_PROGRESSION":
                                loaded_area_data[k] = v

                    print(f"✓ Loaded {os.path.basename(path)}")
                except Exception as e:
                    print(f"✗ Parse error on {os.path.basename(path)}: {e}")

        print("=== JSON LOADING COMPLETE ===\n")

        self.loader = PokemonLoader(self)
        if loaded_evolutions:
            self.loader.evolution_map = loaded_evolutions

        if loaded_area_data:
            self.loader.area_data = loaded_area_data

        self.loader.start()

        self.name_to_id = {}
        for pid in range(1, 1026):
            try:
                data = self.loader.fetch_specific(pid)
                self.name_to_id[data["name"].upper()] = pid
            except:
                continue

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

        if self.assets.music_playlist:
            self.play_music()

    def show_dialogue(self, lines, callback=None):
        """One-line way to show a golden text box anywhere"""
        box_rect = pygame.Rect(40, self.height - 200, self.width - 80, 160)
        box = ClassicDialogueBox(box_rect, lines, self.assets.fonts["med"], callback)
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
        if isinstance(self.current_state, PlayState):
            self.story_manager.balls_left = self.current_state.balls_left
            self.story_manager.current_streak = self.current_state.current_streak
            
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

        self.story_manager = StoryManager()
        self.story_manager.game = self
        self.story_manager.deserialize(story_data, self.loader)

        area_key = self.story_manager.current_area_key
        area_info = self.loader.area_data.get("STORY_PROGRESSION", {}).get(area_key, {})
        if area_info.get("area_type") == "town":
            self.states["city"] = CityState(self)
            self.change_state(self.states["city"])
        else:
            self.states["play"] = PlayState(self)
            self.change_state(self.states["play"])
        return True

    def change_state(self, new_state):
        self.ui_manager.elements.clear()
        self.event_handlers.clear()
        pygame.event.clear()
        self.current_state = new_state
        self.current_state.start()
        if hasattr(new_state, "ui_elements"):
            self.ui_manager.elements = new_state.ui_elements

    def run(self):
        while True:
            if not pygame.display.get_active():
                pygame.time.wait(250)
                continue

            events = pygame.event.get()
            # Capture current state to detect changes mid-loop
            frame_start_state = self.current_state

            for event in events:
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_F3:
                    self.debug_mode = not self.debug_mode
                if event.type == MUSIC_ENDED_EVENT:
                    if self.assets.music_playlist:
                        self.current_song_index = (self.current_song_index + 1) % len(
                            self.assets.music_playlist
                        )
                        self.play_music()
                for handler in self.event_handlers:
                    handler(event)

                # Ghost Click Prevention:
                # If state changed during event processing (e.g. button click),
                # abort processing remaining events for the old state.
                if self.current_state != frame_start_state:
                    break

            if not self.ui_manager.handle_events(events):
                self.current_state.handle_events(events)
            self.current_state.update()
            self.current_state.draw()

            pygame.display.flip()
            self.clock.tick(FPS)


# [REF-0059: Main Execution]
if __name__ == "__main__":
    Game().run()
