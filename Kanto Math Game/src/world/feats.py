# [REF-0141: Feats]
"""Feats: the Quest Book's achievements (Jordan, 11-22; kanto_handoff/QUEST_BOOK_DESIGN.md). Each region has its own list
(assets/quest_feats.json, keyed by region) of feats with tiers, "Fish up 10 / 40 / 100 Pokemon"; each tier pays once:
a TM, an item, money, or a mix, more for the harder tiers.

What a feat counts ("count"):
- worked out from what you own: "dex" (species of the region's own Pokedex), "types" (types among them), "lv50" (Pokemon at
  Lv. 50 or more in the region's party and PC), "math_streak" (the best run of right answers while in the region),
  (dex and types: Pokemon caught in this region only - caught_in(); Jordan 11-24)
  "places" (the region's places you've set foot in whose key has the feat's "match": Orange's islands, "ISLAND";
  or the feat's own "places" list: Sevii's), "unown" (Unown forms caught, of 28),
  "forms" (the region's own forms you own: FORM_MAP entries of the feat's "forms", less its "not_yet", ones that
  can't be got yet: each region's Variants feat, Orange's Pinkan, Valencia and Crystal Pokemon; Jordan 11-23);
  Orre's (11-24): "snagged" (Shadow Pokemon of the region's shadow_pool snagged), "purified" (Shadow lines purified at
  least once, purified_line_<base>), "battle_cds" (XD's Battle CDs cleared);
- counted as you play, per region (StoryManager.feat_counts {region: {kind: n}}), by note(): "trainers", "steps", "fish",
  "finds" (Headbutt, Rock Smash), "evolved", "evo_items", "berries", "safari", "rematches" (VS Seeker or phone rematches
  won: dungeon.py), "swarm" (today's swarm Pokemon caught where it swarms: catching.py), any region's own event kinds.
A tier is [goal, reward] with goal a number or "all" (the most there is: every species of the dex, every type in it);
an optional third part is a flag an older mission paid it under (Kanto's "Catch 30..." missions: kanto_catch_30), so
nobody is paid twice. Payouts go through pay(), called with the catch milestones (every town and catch)."""
import json
import os

_DATA = {}


def table(game):
    key = id(game)
    if key not in _DATA:
        try:
            with open(os.path.join(game.assets.assets_dir, "quest_feats.json"), encoding="utf-8") as f:
                _DATA[key] = json.load(f)
        except (OSError, ValueError, TypeError, AttributeError):
            _DATA[key] = {}
    return _DATA[key]


def feats(game, region):
    return [f for f in table(game).get(str(region).upper(), []) if isinstance(f, dict) and f.get("id")]


def note(story, kind, n=1):
    """Count n more of a kind of thing done in the region you're in (a trainer beaten, a step, a bite)."""
    try:
        region = story.get_current_region()
    except Exception:
        return
    counts = story.__dict__.setdefault("feat_counts", {}).setdefault(region, {})
    counts[kind] = counts.get(kind, 0) + n


def note_best(story, kind, value):
    """Keep the best of a kind (a run of right answers)."""
    try:
        region = story.get_current_region()
    except Exception:
        return
    counts = story.__dict__.setdefault("feat_counts", {}).setdefault(region, {})
    if value > counts.get(kind, 0):
        counts[kind] = value


def _dex_ids(story, region):
    from src.states.systems.pokedex import region_dex
    return set(region_dex(story.get_region_start(region)))


def _owned_ids(story):
    dex = story.game.data.data.get("pokedex", {})
    return {int(v.get("id", 0)) for v in dex.values() if isinstance(v, dict)}


def caught_in(story, region):
    """Species caught in this region (Jordan 11-24: a region's Pokedex and Type Feats count only Pokemon caught there).
    Each Pokemon's caught_region says where (shown as "Met in" on its Summary); one without (a starter, an older save)
    is tagged with the region whose storage it's in now. Kept in story_flags["region_caught"], so a Pokemon released or
    traded away still counts where it was caught. Forms count as their species."""
    log = story.story_flags.setdefault("region_caught", {})
    fm = story.game.loader.area_data.get("FORM_MAP", {}) if getattr(story.game, "loader", None) else {}
    linked = getattr(story, "LINKED", "LINKED")
    active = getattr(story, "active_store", "KANTO")
    stores = [(active, {"team": story.player_team, "pc": story.pc_pokemon})] + [   # (the storage in use first: an old region's
        (k, st) for k, st in (getattr(story, "region_stores", {}) or {}).items() if k != active]   #  store can share its lists once linked)
    seen = set()
    for key, st in stores:
        home = story.get_current_region() if key == linked else str(key).upper()
        for p in list(st.get("team") or []) + list(st.get("pc") or []):
            if not p or getattr(p, "is_egg", False) or id(p) in seen:
                continue
            seen.add(id(p))
            if not getattr(p, "caught_region", None):
                p.caught_region = home
            pid = int(getattr(p, "id", 0) or 0)
            base = int((fm.get(str(pid)) or {}).get("id", pid) or pid)
            got = log.setdefault(str(p.caught_region).upper(), [])
            for i in {pid, base}:
                if i and i not in got:
                    got.append(i)
    return set(log.get(str(region).upper(), []))


def _types_of(story, ids):
    sets = story.game.assets.movesets
    return {t for i in ids for t in (sets.get(str(i), {}) or {}).get("types", []) or []}


def _places(story, feat, region):
    """The region's places a "places" feat counts (keys with its "match" in them)."""
    prog = story.game.loader.area_data.get("STORY_PROGRESSION", {})
    if feat.get("places"):
        return [k for k in feat["places"] if k in prog]
    match = str(feat.get("match") or "")
    return [k for k, a in prog.items() if isinstance(a, dict) and str(a.get("region", "KANTO")).upper() == region
            and match in k]


def _form_ids(story, feat):
    """The forms a "forms" feat counts (by their own numbers: 9134 Pinkan Rhyhorn)."""
    fm = story.game.loader.area_data.get("FORM_MAP", {})
    want = set(feat.get("forms") or [])
    return {int(s) for s, m in fm.items() if isinstance(m, dict) and m.get("form") in want} - set(feat.get("not_yet") or [])


def _shadow_pool(story, region):
    """The region's Shadow Pokemon: {snag flag: species id} from its places' shadow_pool (Orre)."""
    prog = story.game.loader.area_data.get("STORY_PROGRESSION", {})
    return {s["flag"]: s.get("id") for a in prog.values() if isinstance(a, dict)
            and str(a.get("region", "KANTO")).upper() == region for s in a.get("shadow_pool") or [] if s.get("flag")}


def _shadow_lines(story, region):
    """The base species of the region's Shadow Pokemon (a line counts as purified once any of it was: story.py)."""
    fm = story.game.loader.area_data.get("FORM_MAP", {})
    return {int((fm.get(str(i)) or {}).get("id", 0) or 0) for i in _shadow_pool(story, region).values()} - {0}


def _battle_cds(story):
    from src.world import battle_cd
    return list(battle_cd.data(story.game))


def value(story, feat, region):
    """How far along a feat is."""
    kind = feat.get("count")
    if kind == "dex":
        return len(_dex_ids(story, region) & caught_in(story, region))
    if kind == "types":
        return len(_types_of(story, _dex_ids(story, region) & caught_in(story, region)))
    if kind == "forms":
        return len(_form_ids(story, feat) & _owned_ids(story))
    if kind == "unown":
        return story.unown_forms_caught()
    if kind == "snagged":
        return sum(1 for f in _shadow_pool(story, region) if story.story_flags.get(f))
    if kind == "purified":
        return sum(1 for b in _shadow_lines(story, region) if story.story_flags.get(f"purified_line_{b}"))
    if kind == "battle_cds":
        return sum(1 for k in _battle_cds(story) if story.story_flags.get(f"battle_cd_{k}_cleared"))
    if kind == "places":
        return sum(1 for k in _places(story, feat, region) if story.story_flags.get("visited_" + k))
    if kind == "lv50":
        if story.get_current_region() == region:
            mons = list(story.player_team) + list(story.pc_pokemon)
        else:
            st = (getattr(story, "region_stores", {}) or {}).get(story.store_key(region)) or {}
            mons = list(st.get("team") or []) + list(st.get("pc") or [])
        return sum(1 for p in mons if p and (getattr(p, "level", 0) or 0) >= int(feat.get("level", 50)))
    return int(((getattr(story, "feat_counts", {}) or {}).get(region) or {}).get(kind, 0))


def goal(story, feat, tier, region):
    g = tier[0]
    if g == "all":
        if feat.get("count") == "dex":
            return len(_dex_ids(story, region))
        if feat.get("count") == "types":
            return len(_types_of(story, _dex_ids(story, region)))
        if feat.get("count") == "places":
            return len(_places(story, feat, region))
        if feat.get("count") == "forms":
            return len(_form_ids(story, feat))
        if feat.get("count") == "unown":
            return len(story.UNOWN_FORMS)
        if feat.get("count") == "snagged":
            return len(_shadow_pool(story, region))
        if feat.get("count") == "purified":
            return len(_shadow_lines(story, region))
        if feat.get("count") == "battle_cds":
            return len(_battle_cds(story))
    return int(g)


def tier_flag(region, feat, i):
    tier = feat["tiers"][i]
    return tier[2] if len(tier) > 2 and tier[2] else f"feat_{str(region).lower()}_{feat['id']}_{i + 1}"


TIER_NAMES = ("Bronze", "Silver", "Gold", "Platinum", "Master")


def reward_words(game, reward):
    """'TM080 Thunder Wave, a Rare Candy, $3,000'"""
    from src.pokemon import tms
    from src.pokemon.forms import item_label as display_name
    out = []
    for tm in ([reward["tm"]] if isinstance(reward.get("tm"), str) else reward.get("tm") or []):
        out.append(tms.label(game, tm) if tms.is_tm(tm) else str(tm))
    for item, qty in (reward.get("items") or {}).items():
        out.append(f"{qty} x {display_name(item)}" if qty > 1 else display_name(item))
    if reward.get("money"):
        out.append(f"${int(reward['money']):,}")
    return ", ".join(out) or "None"


def give(story, reward):
    """Hand a tier's reward over. Returns the lines to show. (A TM you already have: its price instead.)"""
    from src.pokemon import tms
    from src.pokemon.forms import item_label as display_name
    game = story.game
    lines = []
    for tm in ([reward["tm"]] if isinstance(reward.get("tm"), str) else reward.get("tm") or []):
        if story.inventory.get(tm, 0) > 0:
            cash = int(tms.price(game, tm) or 3000)
            story.money += cash
            lines.append(f"You already have {tms.label(game, tm)}: ${cash:,} instead!")
        else:
            story.add_item(tm, 1)
            lines.append(f"You received {tms.label(game, tm)}!")
    for item, qty in (reward.get("items") or {}).items():
        story.add_item(item, int(qty))
        lines.append(f"You received {display_name(item)}" + (f" x{qty}!" if qty > 1 else "!"))
    if reward.get("money"):
        story.money += int(reward["money"])
        lines.append(f"You received ${int(reward['money']):,}!")
    return lines


def rows(story, region=None):
    """The FEATS tab: [{feat, value, tiers: [(goal, reward, paid)], next}] for a region."""
    region = (region or story.get_current_region()).upper()
    out = []
    for f in feats(story.game, region):
        v = value(story, f, region)
        tiers = [(goal(story, f, t, region), t[1] if len(t) > 1 else {}, bool(story.story_flags.get(tier_flag(region, f, i))))
                 for i, t in enumerate(f.get("tiers") or [])]
        nxt = next((i for i, t in enumerate(tiers) if not t[2]), None)
        out.append({"feat": f, "value": v, "tiers": tiers, "next": nxt})
    return out


def pay(story):
    """Pay every tier reached and not paid yet, in the region you're in. Returns the lines to show."""
    if not getattr(story, "game", None):
        return []
    region = story.get_current_region()
    lines = []
    for f in feats(story.game, region):
        v = None
        for i, t in enumerate(f.get("tiers") or []):
            flag = tier_flag(region, f, i)
            if story.story_flags.get(flag):
                continue
            if v is None:
                v = value(story, f, region)
            if v < goal(story, f, t, region):
                break
            story.story_flags[flag] = True
            lines.append(f"Feat: {f.get('name', f['id'])} ({TIER_NAMES[min(i, len(TIER_NAMES) - 1)]})!")
            lines += give(story, t[1] if len(t) > 1 else {})
    return lines
