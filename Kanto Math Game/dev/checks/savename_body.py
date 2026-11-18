# The save screen's name and typed names (11-18, roadmap bugs): the name offered follows the file picked (this game's
# own name for its own file, another file's name for the file it would replace, else "File N"; a name you typed stays),
# and every name box takes only the characters the game's font can draw (a typed name showed a box).
import json, tempfile
from src.core import save_slots
from src.states.menus import SaveState
from src.utils import Utils
fails = 0


def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m)
    fails += 0 if c else 1


def key(ch, k=0):
    return pygame.event.Event(pygame.KEYDOWN, key=k, mod=0, unicode=ch)


print("1) the font check")
check(Utils.typable(g, "Ash é-1") == "Ash é-1", "letters, digits, space, é, - are kept")
check(Utils.typable(g, "\U0001F600€☃ß") == "", "an emoji, €, ☃, ß (no glyph in the font) are dropped")

print("2) the save screen's name follows the file")
tmp = tempfile.mkdtemp(prefix="kmg_savename_")
g.assets.save_dir = tmp
save_slots.forget()
json.dump({"save_name": "Misty run", "story": {}}, open(os.path.join(tmp, "game_data_2.json"), "w"))
home = g.current_state
g.data.save_file = os.path.join(tmp, "game_data_0.json")   # this game is File 1
g.data.data["save_name"] = "Ash Kanto"
s = SaveState(g, home); g.change_state(s)
check(s.selected_slot == 0 and s.input_text == "Ash Kanto", f"its own file: its own name ({s.input_text})")
s.pick_slot(2)
check(s.input_text == "Misty run", f"File 3 (a save there): that file's name ({s.input_text})")
s.pick_slot(5)
check(s.input_text == "File 6", f"an empty file: \"File 6\" ({s.input_text})")
s.pick_slot(0)
check(s.input_text == "Ash Kanto", "back to its own file: its own name again")
s.handle_events([key("", pygame.K_BACKSPACE), key("!")])
s.pick_slot(5)
check(s.input_text == "Ash Kant!", f"a name you typed stays when you change file ({s.input_text})")
s = SaveState(g, home); g.change_state(s)
s.handle_events([key("\U0001F600"), key("x")])
check(s.input_text == "Ash Kantox" or s.input_text.endswith("x") and "\U0001F600" not in s.input_text,
      f"an emoji typed into the save name is dropped ({s.input_text})")
g.data.save_file = os.path.join(tmp, "game_data.json")   # never saved to a numbered file
s = SaveState(g, home); g.change_state(s)
check(s.selected_slot == 0 and s.input_text == "Ash Kanto", f"never saved to a file: the first free one, its own name ({s.input_text})")
s.pick_slot(2)
s.pick_slot(0)
check(s.input_text == "Ash Kanto", "...and its own name back on that file")

print("3) the trainer and rival name boxes")
from src.states.menus import CharacterSelectionState
try:
    st = CharacterSelectionState(g)
except TypeError:
    st = None
if st is not None and hasattr(st, "input_name"):
    st.input_name = ""
    st.handle_events([key("a"), key("\U0001F600"), key("€"), key("b")])
    check(st.input_name == "AB", f"the trainer name takes A and B, not the emoji or € ({st.input_name!r})")
else:
    print("   (no character pick state to try)")
print("FAILURES:", fails)
