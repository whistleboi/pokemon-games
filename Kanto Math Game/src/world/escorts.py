"""People (or Pokemon) who go everywhere with someone on the map (Jordan 11-19: "adding extra characters may be the right
move, since we could want to retain the ability to have the meowth do actions on its own at some point, or if it lands on
a tile that is not reachable normally"). Jessie & James's Meowth, for one.

Who has escorts (assets/dungeon_sprites.json):
  "escorts": {"<battle sprite>": {"names": [...], "escorts": [{"sheet", "name"}, ...]}}   - trainers drawn with that battle
             sprite whose name has one of "names" ("jessie_james.png", "Jessie"/"James": not Orange's Grunts, who borrow it)
  "figures": {"AREA:TEXT": {"sheet", "escorts": [...]}}        - one story figure (Mt. Ember's Jessie and James)
An escort's "sheet" is an overworld sheet (assets/dungeon/characters), or "mon:<species>" for a Pokemon's follower sprite.

On the map each escort is its own Mover (kind "escort", payload {"sheet", "name", "leader"}): it stands on an open tile
beside its leader that you could walk to (found by walking out from the leader), blocks the way like anyone, follows its
leader's steps, and leaves when its leader does (beaten, gone with the story). Talking to it is talking to its leader.
Its own payload is where a later scene can give it lines or moves of its own."""
from src.dungeon import core


def _specs(ds, m):
    from src.states.overworld.dungeon import sprite_map
    sm = sprite_map(ds.game)
    if m.kind == "trainer" and isinstance(m.payload, tuple) and isinstance(m.payload[1], dict):
        spec = (sm.get("escorts") or {}).get(m.payload[1].get("sprite") or "") or []
        if isinstance(spec, dict):   # ({"names": [...], "escorts": [...]}: only for trainers so named - Orange's Grunts borrow the pair's picture)
            name = str(m.payload[1].get("name") or "")
            spec = (spec.get("escorts") or []) if any(n in name for n in spec.get("names") or []) else []
        return spec
    if m.kind == "figure" and isinstance(m.payload, dict):
        return ((sm.get("figures") or {}).get(f"{ds.area_key}:{m.payload.get('text')}") or {}).get("escorts") or []
    return []


def _spots(f, start, n, avoid):
    """n open tiles near start that you can walk to from it (beside it first: left and right, then the rest)."""
    out, seen, todo = [], {start}, [start]
    while todo and len(out) < n:
        nxt = []
        for t in todo:
            for dx, dy in ((-1, 0), (1, 0), (0, 1), (0, -1)):
                u = (t[0] + dx, t[1] + dy)
                if u in seen or not f.walkable(*u) or u in f.exits:
                    continue
                seen.add(u)
                if f.mover_at(*u) is None and u not in avoid and u not in f.items:
                    out.append(u)
                nxt.append(u)
        todo = nxt
    return out[:n]


def sync(ds):
    """Every frame on the map: escorts made for whoever has them, following their leader, gone with them."""
    if not hasattr(ds, "run"):
        return
    f = ds.run.floor
    player = tuple(ds.run.player)
    for m in [m for m in f.movers if m.kind == "escort"]:   # (its leader is gone: so is it)
        if m.payload.get("leader") not in f.movers:
            f.movers.remove(m)
    for lead in [m for m in f.movers if m.kind in ("trainer", "figure")]:
        if not getattr(lead, "_escorted", False):
            specs = _specs(ds, lead)
            lead._escorted = True
            if not specs:
                continue
            spots = _spots(f, (lead.x, lead.y), len(specs), {player})
            lead._escorts = []
            for spec, t in zip(specs, spots):
                e = core.Mover("escort", t[0], t[1], {"sheet": spec.get("sheet"), "name": spec.get("name"), "leader": lead},
                               facing=getattr(lead, "facing", (0, 1)))
                f.movers.append(e)
                lead._escorts.append(e)
            lead._trail = (lead.x, lead.y)
            continue
        chain = [e for e in getattr(lead, "_escorts", []) if e in f.movers]
        if not chain:
            continue
        here = (lead.x, lead.y)
        if here != lead._trail:   # (the leader stepped: each escort steps into the place of the one ahead)
            prev = lead._trail
            for e in chain:
                if prev == player or (f.mover_at(*prev) not in (None, e)):
                    break
                e.x, e.y, prev = prev[0], prev[1], (e.x, e.y)
            lead._trail = here
        for e in chain:
            e.facing = getattr(lead, "facing", e.facing)


def leader_of(m):
    return (m.payload or {}).get("leader") if m is not None and m.kind == "escort" else None


def image(ds, m, frame=0):
    sheet = str((m.payload or {}).get("sheet") or "")
    if sheet.startswith("mon:"):
        class _Mon:   # (just what the follower sprite needs)
            id, form, is_shiny, gender = int(sheet[4:]), "normal", False, None
        return ds._follower_img(_Mon(), tuple(m.facing or (0, 1)))
    return ds._sheet_frame(sheet, tuple(m.facing or (0, 1)), frame=frame) if sheet else None
