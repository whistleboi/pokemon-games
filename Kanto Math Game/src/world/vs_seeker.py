"""The VS Seeker and trainer rematches (Jordan's answers, 11-18: kanto_handoff/VS_SEEKER.md).

- Every region. You get it at the games' own spot (Kanto / Sevii: Vermilion City; Sinnoh: Route 207; Orange 5.7:
  Kinnow Island), else after your
  2nd badge in that region, the next place you arrive.
- A Bag item, used on a route map: each trainer in view you beat today has about a 1 in 3 chance to want a rematch: they
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
TABLE_REGIONS = {"KANTO", "SEVII", "JOHTO", "HOENN"}   # (Hoenn: Emerald's table, 11-18)
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
    story = state.game.story_manager
    left = CHARGE - charge(story)
    if left > 0:
        return [f"The VS Seeker's battery needs charging. Walk {left} more step{'s' if left != 1 else ''}."]
    story.story_flags["vs_seeker_steps"] = 0
    from src.dungeon import core
    run, area = state.run, state.area_key
    floor, (px, py) = run.floor, run.player
    pool = state.area_data.get("trainer_pool", [])
    taken = {(m.x, m.y) for m in floor.movers} | {run.player}
    back = []
    for idx, info in enumerate(pool):
        if not isinstance(info, dict) or not story.beaten_today(area, idx) or is_ready(story, area, idx):
            continue
        if not _route_trainer(story, info) or not _has_rematch(story, area, info):
            continue
        spot = next((floor.spots.get(f"trainer:{n}") for n in (info.get("spot_name"), info.get("name")) if n and floor.spots.get(f"trainer:{n}")), None)
        if spot is None or tuple(spot) in taken or abs(spot[0] - px) + abs(spot[1] - py) > SEE:
            continue
        if random.random() >= READY_CHANCE:
            continue
        _ready(story).setdefault(area, {})[str(idx)] = story._today()
        facing = (0, 1) if spot[1] < py else (0, -1) if spot[1] > py else ((1, 0) if spot[0] < px else (-1, 0))
        m = core.Mover("trainer", spot[0], spot[1], (idx, info), facing)
        floor.movers.append(m)
        taken.add(tuple(spot))
        back.append(info.get("name", "A trainer"))
    if not back:
        return ["You used the VS Seeker...", "Nobody around wants a rematch right now."]
    return ["You used the VS Seeker!"] + [f"{n} wants a rematch!" for n in back]


# ---- in a town (Jordan 11-18: "Vs seeker in towns for just those 2"): a trainer battle written into a town that has
# the games' rematch stages (only Seven Island's Psychics Dario and Rodette, FireRed's): used in that town, they may want
# a rematch; talk to them for it. Keyed "town:<their battle's flag>".
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


def stage_for(story, area, index, info):
    """The rematch stage (index into "rematch" tiers) a trainer uses now, as FireRed picks it: the next stage you
    haven't beaten; if that stage waits for a story point not reached ("unlock"), the one before it. -1: its first team."""
    tiers = (info.get("rematch") or {}).get("tiers") or []
    done = int((story.story_flags.get("vs_stage") or {}).get(f"{area}|{index}", -1))
    nxt = next((j for j in range(done + 1, len(tiers)) if tiers[j]), None)
    if nxt is None:   # (every stage beaten: the last one again)
        return max((j for j, t in enumerate(tiers) if t), default=-1)
    gate = tiers[nxt].get("unlock")
    if gate and not story.story_flags.get(gate):
        return max((j for j in range(nxt) if tiers[j]), default=-1)
    return nxt


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
        top = max(1, min(100, levels.story_level_cap(story) - 2))
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
