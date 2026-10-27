
# Lumiose City's neighbourhoods (Jordan, 10-26): a hub with districts that are their own small
# areas, each with something to do.
from src.states.overworld import CityState, PlayState
from src.states.systems import PokeMartState
from src.states import gym_puzzles
fails = 0


def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m)
    fails += 0 if c else 1


g.data.save = lambda *a, **k: None
prog = g.loader.area_data["STORY_PROGRESSION"]
DISTRICTS = ["LUMIOSE_VERT_DISTRICT", "LUMIOSE_ROUGE_DISTRICT", "LUMIOSE_MAGENTA_DISTRICT",
             "LUMIOSE_BLEU_DISTRICT", "LUMIOSE_HIBERNAL_DISTRICT"]
hub = {o.get("target_area") for o in prog["LUMIOSE_CITY"]["travel_options"]}
check(set(DISTRICTS) <= hub, "every district is a stop from Centrico Plaza")
for d in DISTRICTS:
    a = prog[d]
    back = {o.get("target_area") or o.get("target") for o in (a.get("travel_options") or []) + (a.get("route_menu") or [])}
    things = [o for o in (a.get("explore_options") or []) + (a.get("route_menu") or [])
              if o.get("action") not in ("EXIT", None, "TRAVEL")]
    story.current_area_key = d
    try:
        st = CityState(g) if a["area_type"] == "town" else PlayState(g)
        g.change_state(st)
        st.draw()
        opened = True
    except Exception as e:
        opened = False
        print("     ", type(e).__name__, e)
    check(opened and "LUMIOSE_CITY" in back and len(things) >= 2, f"{d}: opens, leads back, {len(things)} things to do")
for kind in ("cafe", "galette"):
    ok = True
    for step in range(3):
        prompt, pic, opts = gym_puzzles.make_step(kind, step)
        ok = ok and sum(1 for _, right in opts if right) == 1
    check(ok and kind in gym_puzzles.INTRO and kind in gym_puzzles.DONE, f"the {kind} job: one right answer per step")
story.current_area_key = "LUMIOSE_BLEU_DISTRICT"
town = CityState(g)
g.change_state(town)
shop = next(o for o in prog["LUMIOSE_BLEU_DISTRICT"]["explore_options"] if o.get("stock"))
town._get_callback_for_option(shop)()
check(isinstance(g.current_state, PokeMartState) and "FIRE_STONE" in g.current_state._shop_items(), "the Stone Emporium sells stones")

print(f"\n{'ALL PASS' if not fails else str(fails) + ' FAIL(S)'}")
