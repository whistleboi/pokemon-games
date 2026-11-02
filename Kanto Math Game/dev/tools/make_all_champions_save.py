"""A save that has won every region's League once, in story order, ending with Paldea (Jordan, 11-01).
No post-game: nothing after any title is done, and no post-game Pokemon caught.

Each region's story is played as flags: open what can be opened, take the story battles and
events there, repeat; then the League and the title. Items behind a Champion are skipped, and a
legendary battle only counts where a gate needs it (the story ones). Each region gets its own
team of six, led by its first partner, a little above its Champion's level. Written to the first
empty save slot as ALL CHAMPIONS; no other file is touched.

    python dev/tools/make_all_champions_save.py
"""
import os
import re
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
from src.pokemon.balance import is_legendary  # noqa: E402
from src.world import levels, league_redo  # noqa: E402

NAME = "ALL CHAMPIONS"
# Story steps the game sets in its own code (not in the area data), by region.
CODE_FLAGS = {
    "KANTO": ["received_pokedex_kanto", "kanto_parcel_era", "tower_ghost_defeated", "met_mr_fuji", "silph_co_cleared",
              "received_silph_reward",
              "game_corner_cleared", "nugget_bridge_moved", "caught_snorlax", "defeated_rival_kanto", "beat_elite_four"],
    "JOHTO": ["johto_rival_met_in_lab", "met_mr_pokemon", "elm_received_egg", "elm_silver_report", "ampharos_cured",
              "defeated_rival_johto", "met_bill_johto"],
    "HOENN": ["got_mega_bracelet", "got_starter_mega_stone", "got_mt_pyre_orb", "got_stolen_orb"],
}
# Key items the story gives in code.
CODE_ITEMS = {"KANTO": ["SILPH_SCOPE", "POKE_FLUTE"]}
# Optional legendary battles a gate somewhere mentions, but the story doesn't need (no post-game, no extras).
SKIP_FLAGS = {"UNOVA_ROUTE_22_boss_defeated", "MISTRALTON_CAVE_boss_defeated", "VICTORY_ROAD_UNOVA_boss_defeated"}
HOENN_VERSION = "OMEGA_RUBY"



def is_champ_cond(c):
    c = str(c)
    return bool(re.search(r"beat_(\w+_)?champion", c)) and not c.startswith(("not:", "not "))


def conds(x):
    if not x:
        return []
    return x if isinstance(x, list) else [x]


def gate_refs(game):
    """Flags some gate needs set (positive references in conditions)."""
    refs = set()

    def walk(o, key=None):
        if isinstance(o, dict):
            for k, v in o.items():
                if k in ("condition", "flag", "flags", "flag_condition", "requires", "required_flag"):
                    for c in conds(v):
                        if isinstance(c, str) and not c.startswith(("not:", "not ")):
                            refs.add(c.split(":")[-1] if c.startswith("flag:") else c)
                walk(v, k)
        elif isinstance(o, list):
            for v in o:
                walk(v, key)
    walk(game.loader.area_data.get("STORY_PROGRESSION", {}))
    for m in game.loader.area_data.get("JOURNAL_MISSIONS", []):
        if str(m.get("type", "")).upper() == "MAIN":
            walk(m)
    return refs


NO_ITEMS = {"RAINBOW_PASS", "TRI_PASS", "MYSTICTICKET", "AURORATICKET", "OLD_SEA_MAP", "EON_TICKET"}


def _ok(story, c):
    from src.world import guide
    if guide._ok(story, c):
        return True
    return isinstance(c, str) and c.startswith("has_8_") and story.check_requirements(c)


def _trainers(o, top=True):
    """Trainers anywhere in an area, but not its gym (the gym is taken badge by badge) or the
    things only the Champion opens."""
    if isinstance(o, dict):
        if not top and isinstance(o.get("team"), list) and o.get("name"):
            yield o
        for k, v in o.items():
            if k in ("gym", "post_champion_events", "area_boss", "boss"):
                continue
            yield from _trainers(v, False)
    elif isinstance(o, list):
        for v in o:
            yield from _trainers(v, False)


def run(game, region, extra_flags=()):
    from src.world import guide, story_events, hms
    story = game.story_manager
    prog = game.loader.area_data["STORY_PROGRESSION"]
    refs = gate_refs(game)
    start = story.get_region_start(region).get("start_area")
    for f in extra_flags:
        story.story_flags[f] = True
    for item in CODE_ITEMS.get(region, []):
        story.inventory[item] = max(1, story.inventory.get(item, 0))
    # key items the story hands over in code (Bicycle, S.S. Ticket...): any a gate here asks for
    for key, area in prog.items():
        if story.area_region(key) != region:
            continue
        for o in (area.get("travel_options") or []) + (area.get("route_menu") or []) + (area.get("explore_options") or []):
            cs = conds(o.get("condition"))
            if any(is_champ_cond(c) for c in cs):
                continue
            for c in cs:
                if isinstance(c, str) and c.startswith("has_item:") and not c[9:].startswith("HM_") and c[9:] not in NO_ITEMS:
                    story.inventory[c[9:]] = max(1, story.inventory.get(c[9:], 0))

    def ok_item(item):
        cs = conds(item.get("condition"))
        if any(is_champ_cond(c) for c in cs):
            return False
        if not all(_ok(story, c) for c in cs if isinstance(c, str) and not c.startswith("can_") and c not in
                   ("boss_not_defeated", "boss_defeated", "has_trainers", "no_trainers", "dungeon_cleared")):
            return False
        fc = item.get("flag_condition")
        if fc:
            p = fc.split()
            if p[0] == "not" and len(p) == 2:
                return True  # it's there until done: take it
            if is_champ_cond(p[0]) or not story.story_flags.get(p[0]):
                return False
        return True

    def take(flag):
        if flag and flag not in SKIP_FLAGS and not story.story_flags.get(flag):
            story.story_flags[flag] = True
            return True
        return False

    changed, rounds = True, 0
    seen = set()
    league_done = False
    while (changed or not league_done) and rounds < 80:
        if not changed:  # stuck: the League now (Unova's story goes on after Alder)
            league_done = True
            for key in seen:
                gym = (prog.get(key) or {}).get("gym") or {}
                from src.states.overworld import is_league
                if gym and is_league(gym):
                    for t in gym.get("trainers", []) + [gym.get("leader") or {}]:
                        f = t.get("victory_flag")
                        if f and not is_champ_cond(f):
                            take(f)
        changed, rounds = False, rounds + 1
        # the Journal's main story steps that only code sets (Hoenn's Cozmo, Meteor Falls...)
        for m in story.get_active_missions():
            if str(m.get("type", "")).upper() == "MAIN" and m.get("completed_flag") and not is_champ_cond(m["completed_flag"]):
                if m.get("target") in seen or not m.get("target"):
                    changed |= take(m["completed_flag"])
        eight = f"has_8_{region.lower()}_badges"  # (guide's check reads it as a flag; dropped at the end)
        if len(story.badges.get(region, [])) >= 8:
            story.story_flags[eight] = True
        # reachable areas of this region
        reach, todo = {start}, [start]
        while todo:
            a = todo.pop()
            for n in guide.neighbours(game, a, True):
                if n in prog and n not in reach and story.area_region(n) == region:
                    reach.add(n)
                    todo.append(n)
        seen |= reach
        for key in reach:
            area = prog.get(key) or {}
            changed |= take(f"visited_{key}")
            if area.get("post_champion_events"):
                pass
            for t in _trainers(area):  # every trainer in here, nested ones too (Rocket HQ's executives)
                if not any(is_champ_cond(c) for c in conds(t.get("condition"))) and not is_champ_cond(t.get("victory_flag")):
                    changed |= take(t.get("victory_flag"))
            evs = area.get("on_enter_event")
            for ev in conds(evs):
                if isinstance(ev, dict) and ok_item(ev):
                    changed |= take(ev.get("flag_check") or (ev.get("trainer") or {}).get("victory_flag"))
                    for f in guide._event_flags(ev):
                        changed |= take(f)
            items = (area.get("route_menu") or []) + (area.get("explore_options") or [])
            for it in items:
                if not ok_item(it):
                    continue
                act = it.get("action")
                fc = it.get("flag_condition") or ""
                if act == "GALACTIC_GAUNTLET" and fc.startswith("not "):
                    changed |= take(fc.split()[1])
                if act == "TRAINER" and fc.startswith("not "):
                    changed |= take(fc.split()[1])
                if act in ("NPC", "EVENT", "HOENN_EVENT"):
                    changed |= take(it.get("victory_flag"))
                    ev = it.get("event") if isinstance(it.get("event"), dict) else {}
                    for f in guide._event_flags(ev) | guide._event_flags(story_events.get(it.get("target"))):
                        changed |= take(f)
                    for item_key in (ev.get("gift_item") or {}):
                        if story.inventory.get(item_key, 0) <= 0:
                            story.inventory[item_key] = 1
                            changed = True
                    if fc.startswith("not "):
                        changed |= take(fc.split()[1])
                if act == "BOSS":
                    boss = it.get("boss") or area.get("area_boss") or {}
                    flag = boss.get("victory_flag", f"{key}_boss_defeated")
                    if flag in refs:
                        changed |= take(flag)
            gym = area.get("gym")
            if gym:
                reqs = gym.get("requirements") or {}
                need = len(story.badges.get(region, [])) >= reqs.get("badges", 0) and all(
                    story.story_flags.get(f) for f in conds(reqs.get("flags")) + conds(reqs.get("flag")))
                pre = gym.get("pre_battle_event") or {}
                if pre.get("flag_check") and not pre.get("invert_flag"):
                    pass
                elif pre.get("flag_check"):
                    changed |= take(pre["flag_check"])
                if need:
                    from src.states.overworld import is_league
                    leader = gym.get("leader") or {}
                    if is_league(gym):
                        continue  # the League last
                    for t in gym.get("trainers", []):
                        changed |= take(t.get("victory_flag"))
                    b = leader.get("badge_reward")
                    if b and b not in story.badges.setdefault(region, []):
                        story.badges[region].append(b)
                        story.story_flags[f"badge_{hms._norm(b).lower()}_earned"] = True
                        hms.give_for_badges(story)
                        changed = True
                    changed |= take(leader.get("victory_flag"))
    story.story_flags.pop(f"has_8_{region.lower()}_badges", None)
    return seen


def team_for(game, region, starter, starters=()):
    """The first partner (fully evolved), then the region's strongest of five other types (not
    the other first partners)."""
    story = game.story_manager
    _by_name, data = league_redo._species(game)
    cap = league_redo.GEN_CAP.get(region, 1025)
    allowed = {p for p in data if p <= cap and p not in league_redo.PARADOX}
    dex = [p for p in league_redo._region_dex(story, region) if p in allowed]
    team = [league_redo.fully_evolved(game, starter, allowed | {starter})]
    skip = {league_redo.fully_evolved(game, s, allowed | {s}) for s in starters}
    types = set((data.get(team[0], {}).get("types") or [])[:1])
    bst = lambda p: sum((data[p].get("stats") or {}).values())
    for p in sorted(set(dex), key=lambda p: (-bst(p), p)):
        if len(team) >= 6:
            break
        t = (data[p].get("types") or ["?"])[0]
        if p in team or p in skip or is_legendary(p) or league_redo._next_stages(game, p, allowed) or t in types:
            continue
        team.append(p)
        types.add(t)
    return team


def main():
    g = gm.Game()
    slot = save_slots.first_empty(save_slots.folder(g))
    g.data.save_file = save_slots.slot_path(save_slots.folder(g), slot)  # before anything can write
    g.start_new_game()
    g.player_name, g.player_character = "CHAMP", "red"
    story = g.story_manager
    prog = g.loader.area_data["STORY_PROGRESSION"]
    from src.states.overworld import is_league
    order = [r for r, _c in story.get_region_starts()]
    story.starting_region = order[0]
    story.story_flags["hoenn_version"] = HOENN_VERSION
    report = []
    for region in order:
        cfg = story.get_region_start(region)
        story.current_area_key = cfg.get("start_area")  # first: each region keeps its own team, PC and Bag
        story.use_region_store(region)
        story.enter_region(region)
        rival = story.assign_region_rival(region)  # the canon rival, already met (no rival screen)
        story.record_region_rival(region, rival["name"], rival["character"], chosen=True)
        r = region.lower()
        starters = cfg.get("starters") or [1]
        for f in (f"received_starter_{r}", f"has_{r}_starter"):
            story.story_flags[f] = True
        story.story_flags[f"starter_{r}"] = starters[0]
        if region != order[0] and not cfg.get("travel_only"):
            story.story_flags[f"moved_to_{r}"] = True
        seen = run(g, region, CODE_FLAGS.get(region, []))
        # the League, then the title
        _gyms, league = league_redo.gyms(story, region)
        gym = (prog.get(league) or {}).get("gym") or {}
        for t in gym.get("trainers", []) + [gym.get("leader") or {}]:
            if t.get("victory_flag"):
                story.story_flags[t["victory_flag"]] = True
        story.story_flags[story.champion_flag(region)] = True
        story.story_flags[f"move_offer_{r}"] = True  # the title's offers are past
        for key in prog:
            if story.area_region(key) == region:
                story.story_flags[f"gym_progress_{key}"] = 0 if (prog[key].get("gym") and is_league(prog[key]["gym"]))                     else story.story_flags.get(f"gym_progress_{key}", 0)
        if story.storage_region(region) != region:  # a trip (Orange, Orre): the home region's team goes along
            report.append((region, len(story.badges.get(region, [])), len(seen), "(travels with the home team)"))
            continue
        # the team: a little above the Champion's ace
        top = max(levels.gym_team_levels(region, league, 6, "champion")) if league else 50
        ids = team_for(g, region, starters[0], starters)
        if cfg.get("partners_join"):
            ids = list(dict.fromkeys(list(starters) + ids))[:6]
        team = []
        for pid in ids:
            p = Pokemon(g.loader.fetch_specific(pid), g.assets, size_mult=2.5)
            p.level = min(100, top + 2)
            p.current_hp = p.get_max_hp()
            team.append(p)
            g.data.add_pokemon(p)
        story.player_team = team
        story.balls_left = max(story.balls_left, 30)
        report.append((region, len(story.badges.get(region, [])), len(seen), [(p.display_name, p.level) for p in team]))
    story.link_champion_regions()
    last = order[-1]
    story.current_area_key = story.get_region_start(last).get("start_area")
    story.use_region_store(last)
    story.active_badge_region = last
    g.update_save_data()
    g.data.data["save_name"] = NAME
    g.data.data["save_area"] = prog[story.current_area_key].get("route_name", story.current_area_key.title())
    g.data.save()
    blank = g.data.save_file + ".bak"  # (the blank new game the first save wrote: not a real backup)
    if os.path.exists(blank) and os.path.getsize(blank) < 1000:
        os.remove(blank)
    for region, badges, areas, team in report:
        print(f"{region:8} {badges} badges, {areas} areas  {team}")
    print(f"slot {slot + 1} ({os.path.basename(g.data.save_file)}): {NAME}, {g.data.data['save_area']}")


if __name__ == "__main__":
    main()
