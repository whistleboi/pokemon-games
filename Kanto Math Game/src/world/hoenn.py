# [REF-0076: Hoenn - Omega Ruby / Alpha Sapphire]
"""
Hoenn follows Omega Ruby or Alpha Sapphire, chosen the first time the player arrives
(story flag `hoenn_version`).

The Hoenn data is written once for both versions:
- text uses tokens such as {team}, {leader}, {legend} and {orb};
- villain trainers carry a `villain` role (grunt, admin_a, admin_b, leader).

`apply_version` fills those in from a pristine copy of the data, so the chosen team
(Magma or Aqua), its admins, Pokemon and sprites, and the box legendary (Groudon or
Kyogre) appear everywhere. Before a choice is made the text stays neutral.
"""
import copy

VERSIONS = {
    "OMEGA_RUBY": {
        "title": "OMEGA RUBY", "team": "Team Magma", "team_short": "Magma", "leader": "Maxie",
        "leader_sprite": "maxie.png", "grunt_sprite": "magma_grunt.png", "grunt_class": "TEAM_MAGMA",
        "admin_a": ("Tabitha", "tabitha.png"), "admin_b": ("Courtney", "courtney.png"),
        "legend": "Groudon", "legend_id": 383, "orb": "Red Orb", "orb_item": "RED_ORB",
        "other_legend": "Kyogre", "other_legend_id": 382, "other_orb": "Blue Orb", "other_orb_item": "BLUE_ORB",
        "eon": "Latios", "eon_id": 381, "eon_stone": "LATIOSITE", "other_eon": "Latias", "other_eon_id": 380,
        "leader_mega": 323,
        "crisis_weather": "SUN", "goal": "expand the land", "color": (200, 40, 40),
        # Team Pokemon swap to the version's team (Numel/Camerupt for Magma).
        "swap": {318: 322, 319: 323},
    },
    "ALPHA_SAPPHIRE": {
        "title": "ALPHA SAPPHIRE", "team": "Team Aqua", "team_short": "Aqua", "leader": "Archie",
        "leader_sprite": "archie.png", "grunt_sprite": "aqua_grunt.png", "grunt_class": "TEAM_AQUA",
        "admin_a": ("Matt", "matt.png"), "admin_b": ("Shelly", "shelly.png"),
        "legend": "Kyogre", "legend_id": 382, "orb": "Blue Orb", "orb_item": "BLUE_ORB",
        "other_legend": "Groudon", "other_legend_id": 383, "other_orb": "Red Orb", "other_orb_item": "RED_ORB",
        "eon": "Latias", "eon_id": 380, "eon_stone": "LATIASITE", "other_eon": "Latios", "other_eon_id": 381,
        "leader_mega": 319,
        "crisis_weather": "RAIN", "goal": "expand the sea", "color": (40, 90, 210),
        "swap": {322: 318, 323: 319},
    },
}
NEUTRAL = {"team": "Team Magma/Aqua", "team_short": "Magma/Aqua", "leader": "Maxie/Archie",
           "legend": "Groudon/Kyogre", "other_legend": "Kyogre/Groudon", "orb": "Red/Blue Orb",
           "other_orb": "Blue/Red Orb", "eon": "Latios/Latias", "goal": "change the world"}
TOKENS = ("team", "team_short", "leader", "legend", "other_legend", "orb", "other_orb", "eon", "goal")

# The Hoenn starter each Mega Stone belongs to (Steven's gift on Route 120).
STARTER_STONES = {252: "SCEPTILITE", 255: "BLAZIKENITE", 258: "SWAMPERTITE"}
STARTER_LINES = {252: (252, 253, 254), 255: (255, 256, 257), 258: (258, 259, 260)}
# Sold by the stone collector on Route 114 once the Primal crisis is over.
HOENN_MEGA_STONES = ["SCEPTILITE", "BLAZIKENITE", "SWAMPERTITE", "GARDEVOIRITE", "GALLADITE", "SABLENITE",
                     "MAWILITE", "AGGRONITE", "MEDICHAMITE", "MANECTITE", "SHARPEDONITE", "CAMERUPTITE",
                     "ALTARIANITE", "BANETTITE", "ABSOLITE", "GLALITITE", "SALAMENCITE", "METAGROSSITE",
                     "LATIASITE", "LATIOSITE", "AUDINITE", "LOPUNNITE"]

_PRISTINE = {}


def version(story):
    return story.story_flags.get("hoenn_version")


def info(story):
    return VERSIONS.get(version(story))


def is_hoenn_area(key, area):
    return str(area.get("region") or "").upper() == "HOENN" or key.startswith("HOENN_")


def _fill(value, words):
    if isinstance(value, str):
        for t in TOKENS:
            value = value.replace("{" + t + "}", words[t])
        return value
    if isinstance(value, list):
        return [_fill(v, words) for v in value]
    if isinstance(value, dict):
        return {k: _fill(v, words) for k, v in value.items()}
    return value


def _villain(trainer, v):
    """Dress a villain trainer in the chosen team's colours."""
    role = trainer.get("villain")
    if not role or not v:
        return trainer
    if role == "grunt":
        trainer["name"] = f"{v['team']} Grunt"
        trainer["sprite"] = v["grunt_sprite"]
        trainer["class"] = v["grunt_class"]
    elif role in ("admin_a", "admin_b"):
        name, sprite = v[role]
        trainer["name"] = f"{v['team_short']} Admin {name}"
        trainer["sprite"] = sprite
        trainer["class"] = v["grunt_class"]
    elif role == "leader":
        trainer["name"] = f"{v['team_short']} Leader {v['leader']}"
        trainer["sprite"] = v["leader_sprite"]
        trainer["class"] = "ROCKET_LEADER"
        if trainer.get("leader_mega", True):
            trainer["mega"] = v["leader_mega"]
    if isinstance(trainer.get("team"), list):
        trainer["team"] = [v["swap"].get(p, p) if isinstance(p, int) else p for p in trainer["team"]]
    return trainer


def _version_area(key, area, v):
    for t in area.get("trainer_pool", []):
        _villain(t, v)
    events = area.get("on_enter_event")
    for ev in (events if isinstance(events, list) else [events] if events else []):
        if ev.get("trainer"):
            _villain(ev["trainer"], v)
    boss = area.get("area_boss") or {}
    if v and boss.get("legend") == "main":
        boss["id"], boss["name"] = v["legend_id"], v["legend"]
    for item in area.get("route_menu", []):
        b = item.get("boss") or {}
        if v and b.get("legend") == "other":
            b["id"], b["name"] = v["other_legend_id"], v["other_legend"]
        if v and b.get("legend") == "other_eon":
            b["id"], b["name"] = v["other_eon_id"], v["other_eon"]
    if v and area.get("crisis_weather_area"):
        area["weather"] = v["crisis_weather"]
    return area


def apply_version(game):
    """Rewrite the in-memory Hoenn data for the chosen version (idempotent)."""
    data = game.loader.area_data
    story = game.story_manager
    chosen = version(story)
    if data.get("_hoenn_applied") == (chosen or "NEUTRAL"):
        return
    key = id(data)
    if key not in _PRISTINE:
        sp = data.get("STORY_PROGRESSION", {})
        _PRISTINE[key] = {
            "areas": {k: copy.deepcopy(a) for k, a in sp.items() if is_hoenn_area(k, a)},
            "missions": [(i, copy.deepcopy(m)) for i, m in enumerate(data.get("JOURNAL_MISSIONS", []))
                         if str(m.get("id", "")).startswith("hoenn")],
            "text": {k: copy.deepcopy(t) for k, t in data.get("GAME_TEXT", {}).items() if k.startswith("hoenn")},
        }
    pristine = _PRISTINE[key]
    v = VERSIONS.get(chosen)
    words = {t: (v[t] if v else NEUTRAL[t]) for t in TOKENS}
    sp = data["STORY_PROGRESSION"]
    for k, area in pristine["areas"].items():
        sp[k] = _fill(_version_area(k, copy.deepcopy(area), v), words)
    for i, m in pristine["missions"]:
        data["JOURNAL_MISSIONS"][i] = _fill(copy.deepcopy(m), words)
    for k, t in pristine["text"].items():
        data["GAME_TEXT"][k] = _fill(copy.deepcopy(t), words)
    texts = getattr(game.assets, "game_text", None)
    if isinstance(texts, dict):
        for k, t in pristine["text"].items():
            texts[k] = data["GAME_TEXT"][k]
    data["_hoenn_applied"] = chosen or "NEUTRAL"


def needs_choice(story):
    return story.get_current_region() == "HOENN" and not version(story)


def primal_crisis(story):
    """Between Seafloor Cavern and the Cave of Origin the box legend's weather covers Hoenn."""
    f = story.story_flags
    return bool(f.get("seafloor_cavern_cleared") and not f.get("cave_of_origin_cleared"))


def starter_stone(game):
    """The Mega Stone for the player's Hoenn starter line (Sceptile, Blaziken or Swampert)."""
    story = game.story_manager
    owned = {p.id for p in story.player_team if p} | {p.id for p in story.pc_pokemon if p}
    for base, line in STARTER_LINES.items():
        if owned & set(line):
            return STARTER_STONES[base]
    return STARTER_STONES[252]

