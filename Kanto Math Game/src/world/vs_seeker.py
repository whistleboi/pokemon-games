"""The VS Seeker and trainer rematches (Jordan's answers, 11-18: kanto_handoff/VS_SEEKER.md).

- Every region. You get it at the games' own spot (Kanto / Sevii: Vermilion City; Sinnoh: Route 207; Orange 5.7:
  Kinnow Island), else after your
  2nd badge in that region, the next place you arrive.
- A Bag item, used on a route map: each trainer in view you beat today has a 70% chance (50% in Sinnoh, as Platinum) to want a rematch: they
  come back with a "!" and battle you when you meet them. It recharges after 100 steps on the maps.
- How strong: the games' own rematch team where we have one (a phone trainer's tiers, SoulSilver's), else the trainer's
  usual team levelled up to your badges' level. Rewards grow with the rematch's level.
- Route trainers you beat also come back by themselves the next day, as before (story.trainer_on_map).
Saved in story_flags: "vs_seeker_steps" (charge), "vs_ready" {area: {index: date}}, "vs_wins" {"area|index": n}."""
import random

ITEM = "VS_SEEKER"
CHARGE = 100          # (steps on the maps before it works again: FireRed's)
READY_CHANCE = 0.7    # (each beaten trainer in view, each use: FireRed's 70%, pokefirered vs_seeker.c)
# Regions whose games' own rematch teams are in our data ("rematch" tiers; Johto: the phone's): there, only trainers
# with them want a rematch, as in the games (FireRed shows an "X" for the rest). Elsewhere every route trainer does.
TABLE_REGIONS = {"KANTO", "SEVII", "JOHTO", "HOENN", "SINNOH", "ORANGE"}   # (Hoenn: Emerald's; Sinnoh: Platinum's; Orange: 5.7's; 11-18)
CHANCE = {"SINNOH": 0.5}   # (Platinum's VS Seeker: 50% a trainer, pokeplatinum vs_seeker.c; elsewhere FireRed's 70%)
SEE = 9               # (how far "in view" reaches, in tiles)
GIFT_AT = {"KANTO": "VERMILLION_CITY", "SEVII": "VERMILLION_CITY", "SINNOH": "SINNOH_ROUTE_207",
           "ORANGE": "KINNOW_ISLAND"}   # (Orange 5.7: a trainer in Kinnow's Pokemon Center)


def has(story):
    return story.inventory.get(ITEM, 0) > 0


def charge(story):
    return int(story.story_flags.get("vs_seeker_steps", CHARGE))


def step(story):
    """A step on a map: the battery charges."""
    if has(story) and charge(story) < CHARGE:
        story.story_flags["vs_seeker_steps"] = charge(story) + 1


def _ready(story):
    return story.story_flags.setdefault("vs_ready", {})


def is_ready(story, area, index):
    return (story.story_flags.get("vs_ready") or {}).get(area, {}).get(str(index)) == story._today()


def use(state):
    """Used on a route map (a DungeonState): lines to show. Some beaten trainers in view come back for a rematch."""
    return seek(state)["lines"]


def seek(state):
    """The VS Seeker used on a route map, as FireRed plays it (11-19, Jordan: "build Vs Seeker screens and animations"):
    {"charged": False, "lines"} when the battery is low; else {"charged": True, "lines", "rematch": [movers back for a
    rematch: their "!!"], "seen": [(mover, "!" for a trainer you haven't beaten yet, "X" for one beaten who won't battle
    again yet)]}. The map plays the pose and the bubbles (dungeon.use_vs_seeker), then the lines."""
    story = state.game.story_manager
    left = CHARGE - charge(story)
    if left > 0:
        return {"charged": False, "lines": [f"The VS Seeker's battery needs charging. Walk {left} more step{'s' if left != 1 else ''}."]}
    story.story_flags["vs_seeker_steps"] = 0
    from src.dungeon import core
    run, area = state.run, state.area_key
    floor, (px, py) = run.floor, run.player
    pool = state.area_data.get("trainer_pool", [])
    taken = {(m.x, m.y) for m in floor.movers} | {run.player}
    back, movers = [], []
    for idx, info in enumerate(pool):
        if not isinstance(info, dict) or not story.beaten_today(area, idx) or is_ready(story, area, idx):
            continue
        if not _route_trainer(story, info) or not _has_rematch(story, area, info):
            continue
        spot = next((floor.spots.get(f"trainer:{n}") for n in (info.get("spot_name"), info.get("name")) if n and floor.spots.get(f"trainer:{n}")), None)
        if spot is None or tuple(spot) in taken or abs(spot[0] - px) + abs(spot[1] - py) > SEE:
            continue
        if random.random() >= CHANCE.get(str(story.area_region(area)).upper(), READY_CHANCE):
            continue
        _ready(story).setdefault(area, {})[str(idx)] = story._today()
        facing = (0, 1) if spot[1] < py else (0, -1) if spot[1] > py else ((1, 0) if spot[0] < px else (-1, 0))
        m = core.Mover("trainer", spot[0], spot[1], (idx, info), facing)
        floor.movers.append(m)
        taken.add(tuple(spot))
        back.append(info.get("name", "A trainer"))
        movers.append(m)
    seen = []   # (the others in view react too, as in FireRed: "!" not beaten yet, "X" beaten and not ready)
    for m in floor.movers:
        if m.kind != "trainer" or m in movers or not isinstance(m.payload, tuple) or abs(m.x - px) + abs(m.y - py) > SEE:
            continue
        if hasattr(run, "visible") and not run.visible(m.x, m.y):
            continue
        i = m.payload[0]
        if is_ready(story, area, i):
            continue
        seen.append((m, "X" if story.is_trainer_defeated(area, i) else "!"))
    if not back:
        lines = ["You used the VS Seeker...", "Nobody around wants a rematch right now."]
    else:
        lines = ["You used the VS Seeker!"] + [f"{n} wants a rematch!" for n in back]
    return {"charged": True, "lines": lines, "rematch": movers, "seen": seen}


# ---- in a town (Jordan 11-18: "Vs seeker in towns for just those 2"): a trainer battle written into a town that has
# the games' rematch stages (only Seven Island's Psychics Dario and Rodette, FireRed's): used in that town, they may want
# a rematch; talk to them for it. Keyed "town:<their battle's flag>".
def use_menu(state):
    """Used on a route played from its menu (the regions without route maps yet: Unova, Kalos, Alola, Galar,
    Paldea): every trainer beaten there is in view; each that rematches has the usual chance. Lines to show."""
    story = state.game.story_manager
    left = CHARGE - charge(story)
    if left > 0:
        return [f"The VS Seeker's battery needs charging. Walk {left} more step{'s' if left != 1 else ''}."]
    story.story_flags["vs_seeker_steps"] = 0
    area = story.current_area_key
    pool = (state.game.loader.area_data.get("STORY_PROGRESSION", {}).get(area) or {}).get("trainer_pool") or []
    back = []
    for idx, info in enumerate(pool):
        if (not isinstance(info, dict) or not story.is_trainer_defeated(area, idx) or is_ready(story, area, idx)
                or not _route_trainer(story, info) or not _has_rematch(story, area, info)):
            continue
        if random.random() >= CHANCE.get(str(story.area_region(area)).upper(), READY_CHANCE):
            continue
        _ready(story).setdefault(area, {})[str(idx)] = story._today()
        back.append(info.get("name", "A trainer"))
    if not back:
        return ["You used the VS Seeker...", "Nobody around wants a rematch right now."]
    return ["You used the VS Seeker!"] + [f"{n} wants a rematch!" for n in back] + ["(Battle trainers on this route to meet them.)"]


def on_defeated(story, area, index):
    """A trainer beaten (story.mark_trainer_defeated: maps and menus alike): a VS Seeker rematch won counts."""
    if not is_ready(story, area, index):
        return
    pool = (story.game.loader.area_data.get("STORY_PROGRESSION", {}).get(area) or {}).get("trainer_pool") or []
    info = pool[index] if 0 <= index < len(pool) and isinstance(pool[index], dict) else {}
    won(story, area, index, stage_for(story, area, index, info))


def town_key(ev):
    return f"town:{ev.get('flag')}"


def _town_battles(state):
    """[(tile, event)] of the town's people with a battle that has rematch stages, already beaten."""
    story = state.game.story_manager
    out = []
    for t, opt in state._people().items():
        for o in (opt.get("any") or [opt]) if isinstance(opt, dict) else []:
            ev = o.get("event") if isinstance(o, dict) else None
            if isinstance(ev, dict) and (ev.get("battle") or {}).get("rematch") and ev.get("flag") and story.story_flags.get(ev["flag"]):
                out.append((tuple(t), ev))
    return out


def settle_town(story, area):
    """A town rematch won (its battle set "vs_won|area|key"): that stage is beaten, the trainer waits again."""
    for k in [k for k in story.story_flags if k.startswith(f"vs_won|{area}|")]:
        story.story_flags.pop(k)
        key = k.split("|", 2)[2]
        stage = (story.story_flags.get("vs_stage_pending") or {}).pop(f"{area}|{key}", None)
        won(story, area, key, stage)


def use_town(state):
    """Used in a walked town: lines to show. Only battles with the games' rematch stages answer (Dario and Rodette)."""
    story = state.game.story_manager
    left = CHARGE - charge(story)
    if left > 0:
        return [f"The VS Seeker's battery needs charging. Walk {left} more step{'s' if left != 1 else ''}."]
    story.story_flags["vs_seeker_steps"] = 0
    settle_town(story, state.area_key)
    px, py = state.player
    back = []
    for t, ev in _town_battles(state):
        if abs(t[0] - px) + abs(t[1] - py) > SEE or is_ready(story, state.area_key, town_key(ev)):
            continue
        if random.random() >= READY_CHANCE:
            continue
        _ready(story).setdefault(state.area_key, {})[town_key(ev)] = story._today()
        back.append(ev["battle"].get("name", "A trainer"))
    if not back:
        return ["You used the VS Seeker...", "Nobody around wants a rematch right now."]
    return ["You used the VS Seeker!"] + [f"{n} wants a rematch!" for n in back]


def town_rematch(game, area, ev):
    """Talking to a town trainer the VS Seeker called: (battle info, its win flag) for the rematch, else None."""
    story = game.story_manager
    settle_town(story, area)
    key = town_key(ev)
    if not is_ready(story, area, key):
        return None
    info = rematch(game, area, key, dict(ev["battle"]))
    story.story_flags.setdefault("vs_stage_pending", {})[f"{area}|{key}"] = info.get("_vs_stage")
    return info, f"vs_won|{area}|{key}"


def _has_rematch(story, area, info):
    """Would this trainer rematch at all? In a region with the games' tables: only those with a team there."""
    region = str(story.area_region(area)).upper()
    need = (info.get("rematch") or {}).get("needs") or {}
    if need.get("badges") and len(story.badges.get(region, [])) < int(need["badges"]):
        return False   # (Emerald: rematches only once you have 5 badges, as its Match Call)
    if region not in TABLE_REGIONS:
        return True
    return bool((info.get("rematch") or {}).get("tiers") or (info.get("phone") or {}).get("tiers"))


# ---- made-up stronger teams (Jordan 11-18: the regions whose games have no rematch teams, and Orange, whose 5.7 table
# only repeats the first team). Ours, built when the battle starts, the same every time for a trainer:
# 5 stages: 1-4 at a quarter, half, three-quarters and all of the region's badges, 5 after its Champion. The levels
# (Jordan 11-23, main step M5: "establish a rebattle rule for regions that don't canonically have one"): each Pokemon is
# the trainer's own level plus the average boost the canon rematch tables give at that stage (canon_boosts: Kanto /
# Sevii's FireRed, Johto's SoulSilver phone, Hoenn's Emerald, Sinnoh's Platinum, each region weighted the same; about +9
# a stage); each evolves as far as its level allows (the region's own rules); every other stage adds one from the
# route's wild Pokemon, up to six.
MADE_REGIONS = {"ORANGE", "UNOVA", "KALOS", "ALOLA", "GALAR", "PALDEA", "ORRE"}
MADE_STAGES = 5
CANON_REMATCH_REGIONS = ("KANTO", "SEVII", "JOHTO", "HOENN", "SINNOH")
_BOOSTS = {}


def canon_boosts(game):
    """[levels] x MADE_STAGES: the average level boost of the canon rematch tables at each rematch stage. Stage k is a
    trainer's k-th rematch team stronger than its first (a same-level repeat or an empty slot doesn't count); the boost
    is that team's ace minus the first team's ace. Each region's average counts once (so one big table doesn't decide
    it); a stage only one region's table reaches isn't used. Past the last such stage each stage adds the average step
    so far. Measured once from the loaded data, so it follows the tables."""
    if "b" in _BOOSTS:
        return _BOOSTS["b"]
    sp = game.loader.area_data.get("STORY_PROGRESSION", {}) or {}
    story = game.story_manager
    per = {}   # stage -> region -> [boosts]
    for area, a in sp.items():
        if not isinstance(a, dict):
            continue
        reg = str(story.area_region(area)).upper()
        if reg not in CANON_REMATCH_REGIONS:
            continue
        for t in a.get("trainer_pool") or []:
            if not isinstance(t, dict):
                continue
            rm = t.get("rematch") if isinstance(t.get("rematch"), dict) else {}
            tiers = list(rm.get("tiers") or (t.get("phone") or {}).get("tiers") or [])
            if t.get("levels"):
                base = max(int(x) for x in t["levels"])
            elif tiers and tiers[0] and tiers[0].get("levels"):   # (a phone trainer whose first team is its first tier)
                base, tiers = max(int(x) for x in tiers[0]["levels"]), tiers[1:]
            else:
                continue
            k = 0
            for tr in tiers:
                if not tr or not tr.get("levels"):
                    continue
                b = max(int(x) for x in tr["levels"]) - base
                if b > 0:
                    per.setdefault(k, {}).setdefault(reg, []).append(b)
                    k += 1
    out = []
    for k in sorted(per):
        regs = per[k]
        if len(regs) < 2:
            break
        avg = sum(sum(v) / len(v) for v in regs.values()) / len(regs)
        out.append(max(avg, (out[-1] + 1) if out else 1))
    if not out:
        out = [9.0]   # (no tables loaded: the 11-23 measure)
    step = out[-1] / len(out)
    while len(out) < MADE_STAGES:
        out.append(out[-1] + step)
    _BOOSTS["b"] = [int(round(x)) for x in out[:MADE_STAGES]]
    return _BOOSTS["b"]


def _made(story, area, info):
    region = str(story.area_region(area)).upper()
    src = (info.get("rematch") or {}).get("source")
    return region in MADE_REGIONS and (not (info.get("rematch") or {}).get("tiers") or src == "Orange 5.7")


def _made_unlocked(story, region):
    """[bool] x 5: which made-up stages are open now."""
    import math
    from src.world import levels
    n = len(story.get_region_gym_badges(region) or []) or len(levels.gym_aces(region)) or 8
    have = len(story.badges.get(region, []))
    out = [have >= math.ceil(n * (k + 1) / 4) for k in range(4)]
    out.append(bool(story.is_region_champion(region)))
    return out


def _made_stage(story, area, index):
    region = str(story.area_region(area)).upper()
    open_ = _made_unlocked(story, region)
    done = int((story.story_flags.get("vs_stage") or {}).get(f"{area}|{index}", -1))
    nxt = min(done + 1, MADE_STAGES - 1)
    if open_[nxt]:
        return nxt
    return max((j for j in range(nxt) if open_[j]), default=-1)


def _evolve_up(game, pid, level, rng):
    """The species evolved as far as this level allows (a branch picked the same way every time: Eevee)."""
    from src.pokemon import evolution
    data = evolution._data(game)
    pairs, mins = data.get("pairs", {}), data.get("min_level", {})
    for _ in range(3):
        nxt = sorted(int(k.split(">")[1]) for k in pairs if k.split(">")[0] == str(pid)
                     and int(mins.get(k.split(">")[1], 999)) <= level and evolution.evolution_allowed(game, int(k.split(">")[1])))
        if not nxt:
            break
        pid = rng.choice(nxt)
    return pid


def made_team(game, area, index, info, k):
    """(team, levels) of made-up stage k for this trainer."""
    rng = random.Random(f"{area}|{index}|{info.get('name')}|{k}")
    base = [int(x) for x in (info.get("team") or []) if isinstance(x, int) or str(x).isdigit()]
    base_lv = list(info.get("levels") or [])
    boost = canon_boosts(game)[max(0, min(k, MADE_STAGES - 1))]   # (the canon tables' average at this stage: M5)
    size = min(6, len(base) + (k + 1) // 2)
    team = list(base)
    pool = (game.loader.area_data.get("STORY_PROGRESSION", {}).get(area) or {}).get("wild_pool_percentages")
    wild = [int(x) for x in (game.loader.area_data.get(pool) or {}) if str(x).isdigit() and int(x) < 2000] if pool else []
    while len(team) < size:
        team.append(rng.choice(wild) if wild else rng.choice(base or [19]))
    lv = []
    for i in range(len(team)):   # (an added Pokemon: the trainer's top level)
        own = int(base_lv[i]) if i < len(base_lv) else (max(int(x) for x in base_lv) if base_lv else 10)
        lv.append(own + boost)
    team = [_evolve_up(game, p, l, rng) for p, l in zip(team, lv)]
    return team, [min(100, x) for x in lv]


def stage_for(story, area, index, info):
    """The rematch stage (index into "rematch" tiers) a trainer uses now, as FireRed picks it: the next stage you
    haven't beaten; if that stage waits for a story point not reached ("unlock"), the one before it. -1: its first team."""
    if _made(story, area, info):
        return _made_stage(story, area, index)
    tiers = (info.get("rematch") or {}).get("tiers") or []
    done = int((story.story_flags.get("vs_stage") or {}).get(f"{area}|{index}", -1))
    nxt = next((j for j in range(done + 1, len(tiers)) if tiers[j]), None)
    if nxt is None:   # (every stage beaten: the last one again)
        return max((j for j, t in enumerate(tiers) if t), default=-1)
    gate = tiers[nxt].get("unlock")
    if gate and not _unlocked(story, gate):
        return max((j for j in range(nxt) if tiers[j]), default=-1)
    return nxt


def _unlocked(story, gate):
    """A stage's story point reached: a flag, "badge:NAME", or a list of them (any one: Platinum's level 2 opens with
    Fantina's badge or on reaching Celestic Town)."""
    for g in (gate if isinstance(gate, list) else [gate]):
        if str(g).startswith("badge:") and story.has_badge(g[6:]):
            return True
        if not str(g).startswith("badge:") and story.story_flags.get(g):
            return True
    return False


def _route_trainer(story, info):
    cls = str(info.get("class", "")).upper()
    return not (info.get("is_boss_battle") or info.get("victory_flag") or info.get("villain")
                or any(w in cls for w in story.NOT_ROUTE_TRAINERS))


def rematch(game, area, index, info):
    """A trainer the VS Seeker called back: the games' rematch team (a phone trainer's best ready tier), else its own
    team levelled to your badges' level; rewards grown with the levels. Else info as it was."""
    story = game.story_manager
    if not is_ready(story, area, index):
        return info
    out = dict(info, _vs_rematch=True)
    if _made(story, area, info):   # (our own stronger teams: Orange, and the regions whose games have none)
        j = _made_stage(story, area, index)
        out["_vs_stage"] = j
        if j >= 0:
            team, lv = made_team(game, area, index, info, j)
            out.update(team=team, levels=lv)
            out.pop("movesets", None)
            out.pop("team_moves", None)
        return _bigger_reward(info, out)
    if (info.get("rematch") or {}).get("tiers"):   # (the games' own stages: FireRed's)
        j = stage_for(story, area, index, info)
        out["_vs_stage"] = j
        if j >= 0:
            tier = info["rematch"]["tiers"][j]
            out.update(team=list(tier["team"]), levels=list(tier["levels"]))
            out.pop("movesets", None)
            out.pop("team_moves", None)
            if tier.get("team_moves"):
                out["team_moves"] = [list(m) for m in tier["team_moves"]]
        return _bigger_reward(info, out)
    tiers = (info.get("phone") or {}).get("tiers") or []
    if tiers:
        from src.world import phone
        t = phone.tier_ready(game, info)
        if t is not None:
            out.update(team=list(tiers[t]["team"]), levels=list(tiers[t]["levels"]))
    old = list(info.get("levels") or [])
    if out.get("levels") == old or not out.get("levels"):
        from src.world import levels
        top = max(1, min(100, levels.story_ace(story) - 2))
        n = len(out.get("team") or [])
        out["levels"] = [max(old[i] if i < len(old) else 1, top - (n - 1 - i)) for i in range(n)]
    return _bigger_reward(info, out)


def _bigger_reward(info, out):
    """Rewards bigger than the first win, growing with the rematch's levels (Jordan's answer)."""
    old = list(info.get("levels") or [])
    before = sum(old) / len(old) if old else 0
    after = sum(out.get("levels") or old or [0]) / max(1, len(out.get("levels") or old or [0]))
    k = max(1.5, after / before) if before else 1.5   # (bigger than the first win: grows with the rematch's level)
    out["rewards"] = {key: (max(1, int(round(v * k))) if isinstance(v, (int, float)) else v)
                      for key, v in (info.get("rewards") or {"balls": 3}).items()}
    return out


def won(story, area, index, stage=None):
    """A rematch won: it goes back to waiting (the next use of the VS Seeker, or tomorrow); the stage it used is
    beaten (FireRed: the next rematch is the next stage)."""
    _ready(story).get(area, {}).pop(str(index), None)
    if stage is not None and stage >= 0:
        st = story.story_flags.setdefault("vs_stage", {})
        st[f"{area}|{index}"] = max(int(st.get(f"{area}|{index}", -1)), stage)
    wins = story.story_flags.setdefault("vs_wins", {})
    wins[f"{area}|{index}"] = wins.get(f"{area}|{index}", 0) + 1


def gift(game, area):
    """Arriving somewhere: the VS Seeker, at the games' spot (Vermilion, Route 207), else after the 2nd badge in this
    region. Lines to show (else [])."""
    story = game.story_manager
    if has(story):
        return []
    region = str(story.area_region(area)).upper()   # (the place you've arrived in)
    spot = GIFT_AT.get(region)
    if spot:
        if area != spot:
            return []
    elif len(story.badges.get(region, [])) < 2:
        return []
    story.inventory[ITEM] = 1
    story.story_flags["vs_seeker_steps"] = CHARGE
    return ["Hello! You battle a lot, don't you? Take this VS Seeker.",
            "Use it out on a route: trainers you've beaten may want a rematch!",
            "You received the VS SEEKER!"]
