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
READY_CHANCE = 1 / 3  # (each beaten trainer in view, each use)
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
        if not _route_trainer(story, info):
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
    before = sum(old) / len(old) if old else 0
    after = sum(out["levels"]) / max(1, len(out["levels"]))
    k = max(1.5, after / before) if before else 1.5   # (bigger than the first win: grows with the rematch's level)
    out["rewards"] = {key: (max(1, int(round(v * k))) if isinstance(v, (int, float)) else v)
                      for key, v in (info.get("rewards") or {"balls": 3}).items()}
    return out


def won(story, area, index):
    """A rematch won: it goes back to waiting (the next use of the VS Seeker, or tomorrow)."""
    _ready(story).get(area, {}).pop(str(index), None)
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
