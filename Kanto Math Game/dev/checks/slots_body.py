

# ---- 100 save slots (c_01): save + load in slots 0, 57 and 99, paging, cheap empty slots
import importlib, json, tempfile, shutil
fails = 0


def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m)
    fails += 0 if c else 1


import src.core.data as dm_mod
from src.core import save_slots
from src.states.menus import SaveState, LoadState, MainMenuState
_stub_save = DataManager.save
import importlib.util  # the harness stubs saving; this check needs the real one (fresh copy, not reloaded)
_spec = importlib.util.spec_from_file_location("kmg_real_data", dm_mod.__file__)
_real = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_real)
real_save = _real.DataManager.save
DataManager.save = real_save
check(save_slots.SAVE_SLOTS == 100, f"SAVE_SLOTS = {save_slots.SAVE_SLOTS}")
tmp = tempfile.mkdtemp(prefix="kmg_slots_")
old_dir, g.assets.save_dir = getattr(g.assets, "save_dir", None), tmp
home = g.current_state
g.data.save_file = os.path.join(tmp, "game_data.json")
story.current_area_key = "PALLET_TOWN"
for i in (0, 57, 99):
    s = SaveState(g, home); g.change_state(s)
    s.save_to_slot(i, f"Slot test {i}")
    check(os.path.exists(os.path.join(tmp, f"game_data_{i}.json")), f"slot {i} written as game_data_{i}.json")
check(save_slots.used_slots(tmp) == {0, 57, 99}, f"used slots {sorted(save_slots.used_slots(tmp))}")
check(save_slots.first_empty(tmp) == 1, "first empty slot is 1")
# a second save in the same slot keeps a .bak, like slots 0-4 always did
s = SaveState(g, home); g.change_state(s); s.save_to_slot(57, "Slot test 57")
check(os.path.exists(os.path.join(tmp, "game_data_57.json.bak")), "slot 57 keeps a .bak")

reads = []
_rj = DataManager.read_json
DataManager.read_json = staticmethod(lambda p: (reads.append(p), _rj(p))[1])
save_slots.forget()
ls = LoadState(g, home); g.change_state(ls)
ls.draw()
check(len(reads) == 1, f"page 1 drawn with {len(reads)} file read(s) (only the used slot on screen)")
check(ls.slot_list.page_count == 13, f"{ls.slot_list.page_count} pages of 8")
reads.clear(); ls.draw(); ls.slot_list.goto_page(12); ls.draw(); ls.slot_list.goto_page(0); ls.draw()
check(len(reads) == 1, f"paging re-reads only what is new ({len(reads)} read(s), cached)")
DataManager.read_json = staticmethod(_rj)
# keyboard: End / Page Up / Down
ev = lambda k: pygame.event.Event(pygame.KEYDOWN, key=k, mod=0, unicode="")
ls.handle_events([ev(pygame.K_END)]); check(ls.slot_list.selected == 99 and ls.slot_list.page == 12, "End -> slot 100, last page")
ls.handle_events([ev(pygame.K_PAGEUP)]); check(ls.slot_list.selected == 91 and ls.slot_list.page == 11, "Page Up -> previous page")
ls.handle_events([ev(pygame.K_HOME), ev(pygame.K_DOWN)]); check(ls.slot_list.selected == 1, "Home, Down -> slot 2")
ls.handle_events([ev(pygame.K_PAGEDOWN)]); check(ls.slot_list.page == 1, "Page Down -> page 2")
ls.handle_events([ev(pygame.K_RETURN)]); check(ls.phase == "SELECT", "Enter on an empty slot does nothing")
for i in (0, 57, 99):
    story.current_area_key = "VIRIDIAN_CITY"; g.data.data["save_name"] = "changed"
    ls = LoadState(g, home); g.change_state(ls)
    ls.slot_list.select(i); ls.handle_events([ev(pygame.K_RETURN)])
    check(ls.phase == "CONFIRM", f"slot {i}: Enter asks to load")
    ls.do_load()
    check(g.data.save_file.endswith(f"game_data_{i}.json") and g.data.data.get("save_name") == f"Slot test {i}"
          and g.story_manager.current_area_key == "PALLET_TOWN", f"slot {i} loads back ({g.data.data.get('save_name')})")
# old-style save (slots 0-4 from before) still lists and loads
json.dump({"save_name": "Old", "save_area": "Cerulean City", "story": {}}, open(os.path.join(tmp, "game_data_4.json.bak"), "w"))
check(save_slots.summary(tmp, 4)["restored"], "slot 4 with only a .bak lists as restored")
check(MainMenuState(g).btn_load.callback is not None, "main menu LOAD enabled by any slot 0-99")
# New Game picker: an empty slot starts at once and becomes the live file
DataManager.save = _stub_save
ng = LoadState(g, home, mode="new"); g.change_state(ng)
check(ng.slot_list.selected == 1, f"new game picker starts on the first empty slot ({ng.slot_list.selected})")
ng.pick(1)
check(g.data.save_file.endswith("game_data_1.json"), "new game lives in the picked slot")
ng = LoadState(g, home, mode="new"); g.change_state(ng); ng.pick(57)
check(ng.phase == "CONFIRM", "new game on a used slot asks first")
g.assets.save_dir = old_dir
shutil.rmtree(tmp, ignore_errors=True)
print(f"slots done, {fails} fails")
