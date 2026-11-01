"""A post-game Orre save for testing (Jordan, 11-01): a new game started in Orre, the whole story done
(every story flag the Orre walk-through check steps through, all four badges, Evice beaten), every
Orre place visited, a Lv 60 team led by the Eeveelution partner. Written to the first empty save slot,
named ORRE TEST; no other file is touched.

    python dev/tools/make_orre_test_save.py
"""
import os
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
sys.path.insert(0, os.getcwd())
import pygame  # noqa: E402

pygame.display.init()
pygame.display.set_mode((1280, 720))
pygame.display.Info = lambda: type("I", (), {"current_w": 1280, "current_h": 720})()
import src.core.game as gm  # noqa: E402
from src.core import save_slots  # noqa: E402
from src.pokemon.data import Pokemon  # noqa: E402

NAME = "ORRE TEST"
STORY = ["received_starter_orre", "orre_beat_willie", "phenac_cipher_beaten", "got_snag_machine", "orre_miror_cave",
         "met_agate_elder", "orre_dakim_mt_battle", "cleared_the_under", "orre_ein_lab", "xd_lovrina_beaten",
         "xd_exol_beaten", "orre_snattle_phenac", "beat_gonzap", "xd_gorigan_beaten", "beat_orre_champion"]
BADGES = ["PYRITE", "UNDER", "PHENAC", "ORRE"]
TEAM = [(196, 62), (197, 62), (229, 60), (215, 60), (241, 60), (217, 60)]  # partners, then Shadow-story favourites
LEVEL_OF = dict(TEAM)

g = gm.Game()
slot = save_slots.first_empty(save_slots.folder(g))
g.data.save_file = save_slots.slot_path(save_slots.folder(g), slot)  # before anything can write
g.start_new_game()
g.player_name, g.player_character = "TESTER", "red"

story = g.story_manager
story.starting_region = "ORRE"
story.current_area_key = "PHENAC_CITY"  # first: each region keeps its own team, PC and Bag
story.enter_region("ORRE")
prog = g.loader.area_data["STORY_PROGRESSION"]
orre = [k for k, a in prog.items() if (a or {}).get("region") == "ORRE"]
for flag in STORY:
    story.story_flags[flag] = True
for k in orre:
    story.story_flags[f"visited_{k}"] = True
story.badges["ORRE"] = list(BADGES)
story.story_flags["unlocked_orre_badges"] = True
story.active_badge_region = "ORRE"  # the slot list and badge case show Orre
for item, n in (("SNAG_MACHINE", 1), ("TOWN_MAP", 1), ("EXP_SHARE", 1)):
    story.inventory[item] = n
story.balls_left = 99

team = []
for pid, lv in TEAM:
    p = Pokemon(g.loader.fetch_specific(pid), g.assets, size_mult=2.5)
    p.level = lv
    p.current_hp = p.get_max_hp()
    team.append(p)
story.player_team = team

g.update_save_data()
g.data.data["save_name"] = NAME
g.data.data["save_area"] = prog["PHENAC_CITY"].get("route_name", "Phenac City")
g.data.save()
blank = g.data.save_file + ".bak"  # (the blank new game the first save wrote: not a real backup)
if os.path.exists(blank) and os.path.getsize(blank) < 1000:
    os.remove(blank)
print(f"slot {slot + 1} ({os.path.basename(g.data.save_file)}): {NAME}, Phenac City,"
      f" team {[(p.display_name, p.level) for p in team]}")
