# [REF-0141: Feats]
"""Feats: the Quest Book's achievements (Jordan, 11-22; kanto_handoff/QUEST_BOOK_DESIGN.md). Each region has its own list
(assets/quest_feats.json, keyed by region) of feats with tiers, "Fish up 10 / 40 / 100 Pokemon"; each tier pays once:
a TM, an item, money, or a mix, more for the harder tiers.

What a feat counts ("count"):
- worked out from what you own: "dex" (species of the region's own Pokedex), "types" (types among them), "lv50" (Pokemon at
  Lv. 50 or more in the region's party and PC), "math_streak" (the best run of right answers while in the region);
- counted as you play, per region (StoryManager.feat_counts {region: {kind: n}}), by note(): "trainers", "steps", "fish",
  "finds" (Headbutt, Rock Smash), "evolved", "evo_items", "berries", "safari", any region's own event kinds.
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


def _types_of(story, ids):
    sets = story.game.assets.movesets
    return {t for i in ids for t in (sets.get(str(i), {}) or {}).get("types", []) or []}


def value(story, feat, region):
    """How far along a feat is."""
    kind = feat.get("count")
    if kind == "dex":
        return len(_dex_ids(story, region) & _owned_ids(story))
    if kind == "types":
        return len(_types_of(story, _dex_ids(story, region) & _owned_ids(story)))
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
