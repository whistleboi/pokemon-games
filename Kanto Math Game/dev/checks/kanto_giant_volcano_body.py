# The Giant Volcano easter egg (Jordan, 11-16: src/world/mystery_dungeon.py), played the way a player meets it: the
# Cinnabar Lab's scientist after Blaine, his walk to the volcano, the fall, ten floors as a Charmander with a Vulpix,
# the shiny Moltres at the top, waking up in the Lab (won or fainted), and a save made inside. Glue after harness_head.py:
#   bash dev/checks/run.sh kanto_giant_volcano
import json
import random
from src.states.overworld import PlayState, CityState, AreaTransitionState
from src.states.overworld.walk_town import WalkTownState as _WTS
from src.states.overworld.mystery_dungeon import MysteryDungeonState as _MDS, PMDView, SUMMIT
from src.states.battle import WildBattleState
from src.dungeon import core, pmd
from src.world import mystery_dungeon as md

fails = []


def check(c, m):
    print(("   ok  " if c else "   FAIL ") + m)
    if not c:
        fails.append(m)


g.dungeon_routes = True; g.walk_towns = True; g.player_character = "red"
said = []


def _note(st):
    box = getattr(st, "npc_dialogue", None) if getattr(st, "npc_active", False) else getattr(st, "dialogue_box", None)
    if box is not None and getattr(box, "visible", True):
        for line in getattr(box, "text_lines", []) or []:
            if not said or said[-1] != line:
                said.append(line)


def frames(n):
    for _ in range(n):
        g.current_state.update(); g.current_state.draw()


def play(until, n=3000):
    """Run the game, tapping through whatever is said, till until() (or n frames)."""
    for _ in range(n):
        if until():
            return True
        st = g.current_state
        if getattr(st, "npc_active", False):
            _note(st)
            st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
        elif getattr(st, "dialogue_box", None) is not None and getattr(st.dialogue_box, "visible", False):
            _note(st)
            st.dialogue_box.advance()
        st.update(); st.draw()
    return until()


def open_town(room=None):
    story.current_area_key, story.last_area_key = "CINNABAR_ISLAND", "KANTO_ROUTE_21"
    g.walk_town_pos = None
    st = CityState(g)
    g.change_state(st)
    frames(2)
    if room:
        st._go(room, "")
        frames(2)
    return st


def person(st, text):
    for spot, opt in st.people.items():
        opts = opt.get("any") or [opt]
        if any(o.get("text") == text for o in opts):
            return spot, opt
    return None, None


# the real party going in (to see it come back)
story.player_team = [mk(25), mk(1)]
for p in story.player_team:
    p.level = 30
real_ids = [p.id for p in story.player_team]
story.battle_style = "TRADITIONAL"
for f in (md.MOLTRES_FLAG, md.BEATEN_FLAG, md.CLEARS_FLAG, md.WALK_FLAG):
    story.story_flags.pop(f, None)
_badges = story.badges.get("KANTO")

# ---- the Lab's Testing Room: the scientist by the machines
story.badges["KANTO"] = [b for b in (story.badges.get("KANTO") or []) if b != "VOLCANO"]
lab = open_town("lab_test")
spot, opt = person(lab, "Pokemon Lab")   # (FireRed's fossil scientist by the machines, since Kanto batch 23; 11-24)
check(spot == (12, 3) and isinstance(opt, dict) and "any" in opt, f"Testing Room: the scientist by the machines ({spot})")
shown = [o.get("text") for o in opt.get("any", []) if lab._shown(o)]
check(shown == ["Pokemon Lab"], f"...before Blaine he only revives fossils ({shown})")
story.badges.setdefault("KANTO", []).append("VOLCANO")
lab = open_town("lab_test")
spot, opt = person(lab, "Pokemon Lab")
shown = [o.get("text") for o in opt.get("any", []) if lab._shown(o)]
check(shown == ["Volcano experiment", "Pokemon Lab"], f"...with the Volcano Badge he offers the experiment ({shown})")

# talk to him and pick the experiment: out of the Lab, he walks you to the volcano, you fall in
said.clear()
exp = next(o for o in opt["any"] if o.get("text") == "Volcano experiment")
lab._get_callback_for_option(exp)()
play(lambda: isinstance(g.current_state, _WTS) and g.current_state.room is None, 300)
out = g.current_state
check(isinstance(out, _WTS) and out.room is None and story.story_flags.get(md.WALK_FLAG), f"...out of the Lab together ({getattr(out, 'room', '?')}, {getattr(out, 'player', '?')})")
check(any("Blaine" in s for s in said), "...after his offer")
said.clear()
play(lambda: story.current_area_key == md.AREA and isinstance(g.current_state, _MDS), 4000)
check(any("This way" in s for s in said) and any("tumble into the volcano" in s for s in said),
      f"...he leads you up to the volcano's mouth and you fall in ({said[:8]})")
gv = g.current_state
check(isinstance(gv, _MDS) and story.current_area_key == "GIANT_VOLCANO", f"...into the Giant Volcano ({type(gv).__name__})")
team = [p for p in story.player_team if p]
check([p.id for p in team] == [4, 37] and all(p.level == md.LEVEL and p.everstone for p in team),
      f"...you're a Charmander, a Vulpix with you ({[(p.id, p.level) for p in team]})")
check(story.battle_style == "OVERWORLD" and not story.story_flags.get(md.WALK_FLAG), "...every battle on the map now")
saved = story.serialize()
check([r.get("id") for r in saved["player_team"]] == real_ids and saved["current_area_key"] == "CINNABAR_ISLAND"
      and saved["battle_style"] == "TRADITIONAL", f"a save made inside keeps your real party, on Cinnabar ({[r.get('id') for r in saved['player_team']]}, {saved['current_area_key']})")
check([p.id for p in story.player_team] == [4, 37], "...and you're still the Charmander after it")

# ---- the dungeon itself
play(lambda: gv._ready(), 300)
check(any("Charmander" in s for s in said) and any("Vulpix" in s for s in said), "...Vulpix meets you on the first floor")
check(gv.run.n_floors == 10 and gv._tiles is not None, f"ten floors, Explorers of Sky's own tiles ({gv.run.n_floors})")
frames(2)
check(gv._floor_surf is not None and gv._floor_surf.get_size() == (gv.run.floor.w * 56, gv.run.floor.h * 56), "...the floor drawn from them")
check(len(gv._glow) > 0, f"...lava pools that glow ({len(gv._glow)} glowing tiles)")
check(all(v != core.STAIRS_UP for v in gv.run.floor.exits.values()) and core.STAIRS in gv.run.floor.exits.values(),
      f"...stairs up, no way back out ({sorted(set(map(str, gv.run.floor.exits.values())))})")
wild = [m for m in gv.run.floor.movers if m.kind == "wild"]
ok_ids = {pid for pid, _w, _l in md.wild_on(1)}
check(wild and all(m.payload.id in ok_ids for m in wild), f"...Giant Volcano's own Pokemon ({sorted({m.payload.id for m in wild})})")
_lv = {pid: l for pid, _w, l in md.wild_on(1)}
check(all(_lv[m.payload.id][0] <= m.payload.level <= _lv[m.payload.id][1] for m in wild), "...at their own levels")
check(gv.lead() is team[1], "...Vulpix walks a step behind you")
img = gv._player_img()
check(img is not None and img.get_height() > 20, f"...you drawn as the PMD Charmander ({img and img.get_size()})")
# PMD sprites, shiny ones in their own colours
n = mk(146); s = mk(146); s.is_shiny = True
a, b = gv._follower_img(n, (0, 1)), gv._follower_img(s, (0, 1))
check(a is not None and b is not None and pygame.image.tostring(a, "RGBA") != pygame.image.tostring(b, "RGBA"),
      "...a shiny Pokemon in its shiny PMD colours (Moltres)")
for pid in [p for p, *_ in md.WILD] + [md.HERO, md.PARTNER, 146]:
    if not (pmd.has(g, pid) and pmd.anims(g, pid, True).get("Walk") and "shiny" in pmd.anims(g, pid, True)["Walk"][0]):
        check(False, f"...PMD sprite and shiny sprite for #{pid}")
        break
else:
    check(True, "...every species here has its PMD sprite and its shiny one")

# a wild one: bumped into, fought on the map, can't be caught
m = wild[0]
gv.walk_goal = None
gv._meet_wild(m)
bt = g.current_state
check(isinstance(bt, WildBattleState) and isinstance(getattr(bt, "overworld", None), PMDView) and bt.no_catch,
      f"bump a wild one: a battle right on the map, no catching ({type(bt).__name__})")
frames(30)
bt.trigger_outro(True)
play(lambda: g.current_state is gv, 1500)
check(g.current_state is gv and m not in gv.run.floor.movers, f"...won, back on the floor, it's gone ({type(g.current_state).__name__}, {m in gv.run.floor.movers})")

# HP comes back as you walk
team[0].current_hp = team[0].get_max_hp() // 2
was = team[0].current_hp
for _ in range(30):
    for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        if gv._ready() and gv.run.floor.walkable(gv.run.player[0] + d[0], gv.run.player[1] + d[1]) and not gv.run.floor.mover_at(gv.run.player[0] + d[0], gv.run.player[1] + d[1]) and (gv.run.player[0] + d[0], gv.run.player[1] + d[1]) not in gv.run.floor.exits:
            gv.step(*d); play(lambda: gv.anim == 0 and gv._ready() or g.current_state is not gv, 60)
            break
    if g.current_state is not gv:
        break
check(g.current_state is not gv or team[0].current_hp > was, f"...HP comes back as you walk ({was} -> {team[0].current_hp})")
if g.current_state is not gv:   # (walked into a fight: win it)
    g.current_state.trigger_outro(True)
    play(lambda: g.current_state is gv, 1500)

# up the stairs, floor by floor, to the top
for i in range(1, 10):
    gv._descend()
    frames(1)
check(gv.run.index == 9 and gv._floor_name(9) == "10F", f"up to the top floor ({gv._floor_name(gv.run.index)})")
boss = [mv for mv in gv.run.floor.movers if mv.kind == "figure" and mv.payload.get("action") == "BOSS"]
check(len(boss) == 1 and SUMMIT not in gv.run.floor.exits.values(), "...the Moltres waits at the summit (no way out round it)")
_ticks = pygame.time.get_ticks; pygame.time.get_ticks = lambda: 1000   # (the same frame of each)
fig = gv._figure_img(boss[0].payload) if boss else None
_same = fig is not None and pygame.image.tostring(fig, "RGBA") == pygame.image.tostring(gv._follower_img(s, (0, 1)), "RGBA")
pygame.time.get_ticks = _ticks
check(_same,
      "...the shiny Moltres, in its PMD shiny colours")
said.clear()
gv._use_figure(boss[0])
play(lambda: isinstance(g.current_state, WildBattleState), 300)
bt = g.current_state
check(isinstance(bt, WildBattleState) and isinstance(getattr(bt, "overworld", None), PMDView) and bt.no_catch
      and bt.opponent_pokemon.id == 146 and bt.opponent_pokemon.is_shiny and bt.opponent_pokemon.level == 44,
      f"...its battle, on the map: shiny Lv 44 ({getattr(bt.opponent_pokemon, 'level', '?')})")
check(any("glowing gold" in s for s in said), "...after its own words")
frames(30)
bt.trigger_outro(True)
said.clear()
play(lambda: isinstance(g.current_state, _WTS), 3000)
home = g.current_state
check(isinstance(home, _WTS) and home.room == "lab_test" and tuple(home.player) == md.LAB_SPOT,
      f"beaten: you wake up in the Lab ({type(home).__name__}, {getattr(home, 'room', '?')}, {getattr(home, 'player', '?')}, {said[-4:]})")
check(any("save the volcano" in s for s in said) and any("see each other again soon" in s for s in said),
      "...after Vulpix thanks you and hopes to see you again")
play(lambda: not getattr(home, "npc_active", False), 300)
ids = [p.id for p in story.player_team]
check(ids[:2] == real_ids and story.battle_style == "TRADITIONAL" and not md.active(story), f"...yourself again, your own party ({ids})")
mol = [p for p in list(story.player_team) + [p for p in story.pc_pokemon if p] if p.id == 146]
check(len(mol) == 1 and mol[0].is_shiny and story.story_flags.get(md.MOLTRES_FLAG), "...and the shiny Moltres came with you")
check(any("followed you back" in s for s in said), "...the scientist sees it")
fol = gv._follower_img(mol[0], (0, 1)) if mol else None
check(fol is not None, "...the shiny Moltres follows you on the maps")
import os as _os
from src.states.overworld.dungeon import DungeonState as _DS
check(_os.path.isfile("assets/dungeon/followers/shiny/146.png"), "...with its shiny walking sheet")

# ---- again: Moltres has joined you, so the summit's way out is there instead
lab = open_town("lab_test")
md.become(g)
story.current_area_key = md.AREA
g.change_state(AreaTransitionState(g, md.AREA)) if False else None
st = PlayState(g); g.change_state(st); frames(2)
gv = g.current_state
play(lambda: gv._ready(), 300)
check(isinstance(gv, _MDS) and any("again" in s for s in said[-3:]), "a second climb: Vulpix welcomes you back")
for i in range(1, 10):
    gv._descend()
check(not [mv for mv in gv.run.floor.movers if mv.kind == "figure"] and SUMMIT in gv.run.floor.exits.values(),
      "...no Moltres at the top now, the summit's way out instead")
said.clear()
gv._try_exit(SUMMIT)
play(lambda: isinstance(g.current_state, _WTS), 2000)
check(isinstance(g.current_state, _WTS) and g.current_state.room == "lab_test" and [p.id for p in story.player_team][:2] == real_ids,
      "...the summit: back in the Lab as yourself")
check(len([p for p in list(story.player_team) + [p for p in story.pc_pokemon if p] if p.id == 146]) == 1, "...no second Moltres")

# ---- fainted inside: you wake in the Lab, nothing lost
md.become(g)
story.current_area_key = md.AREA
st = PlayState(g); g.change_state(st); frames(2)
said.clear()
from src.states.overworld import white_out
white_out(g)
play(lambda: isinstance(g.current_state, _WTS) and not getattr(g.current_state, "npc_active", False), 600)
check(isinstance(g.current_state, _WTS) and g.current_state.room == "lab_test" and [p.id for p in story.player_team][:2] == real_ids
      and any("You're awake" in s for s in said), f"both fainted: you wake in the Lab as yourself ({said[-2:]})")
check(not md.active(story) and story.battle_style == "TRADITIONAL", "...your battle style back too")

# ---- out some other way (an Escape Rope, Fly): yourself again
md.become(g)
story.current_area_key = md.AREA
st = PlayState(g); g.change_state(st); frames(2)
AreaTransitionState(g, "CINNABAR_ISLAND")
check(not md.active(story) and [p.id for p in story.player_team][:2] == real_ids, "out by an Escape Rope or Fly: yourself again")

if _badges is not None:
    story.badges["KANTO"] = _badges
print(f"##### {len(fails)} failures")
