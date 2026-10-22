"""Shared helpers for building assets/orange_area_data.json."""

AREAS = {}
POOLS = {}

ISLANDS = {  # island hub -> (name, condition to sail there, arrival line)
    "VALENCIA_ISLAND": ("Valencia Island", None, "Palm trees line the docks of Valencia Island."),
    "MIKAN_ISLAND": ("Mikan Island", None, "Mikan Island's lighthouse comes into view."),
    "PINKAN_ISLAND": ("Pinkan Island", "has_coral_eye_badge", "Pink berry trees cover Pinkan Island."),
    "NAVEL_ISLAND": ("Navel Island", "has_coral_eye_badge", "A snowy volcano rises over Navel Island."),
    "SUNBURST_ISLAND": ("Sunburst Island", "has_sea_ruby_badge", "Glass sparkles on every street of Sunburst Island."),
    "TROVITA_ISLAND": ("Trovita Island", "has_sea_ruby_badge", "Trovita Island's beaches shine in the sun."),
    "SHAMOUTI_ISLAND": ("Shamouti Island", "has_spike_shell_badge", "Drums from a festival echo across Shamouti Island."),
    "KUMQUAT_ISLAND": ("Kumquat Island", "has_spike_shell_badge", "Resort hotels line the shore of Kumquat Island."),
    "PUMMELO_ISLAND": ("Pummelo Island", "has_jade_star_badge", "Pummelo Stadium towers over the harbor."),
}


def ships(here):
    """Ship links from one island to every other island it has unlocked."""
    out = []
    for key, (name, cond, arrive) in ISLANDS.items():
        if key == here:
            continue
        opt = {"text": f"Ship to {name}", "target_area": key,
               "message": f"You board the ferry. The ship sails across the Orange Archipelago... {arrive}"}
        if cond:
            opt["condition"] = cond
        out.append(opt)
    return out


def trainer(name, cls, sprite, team, balls=4, **extra):
    t = {"name": name, "class": cls, "sprite": sprite, "team": team, "rewards": {"balls": balls}}
    t.update(extra)
    return t


def wild_menu(exits, trainers=True, extra=None, catch_cond="has_balls"):
    m = [{"text": "CATCH WILD PKMN", "action": "CATCH", "condition": catch_cond, "color": "BLUE"},
         {"text": "BATTLE WILD PKMN", "action": "BATTLE", "condition": "can_battle", "color": "GREEN"}]
    if trainers:
        m.append({"text": "BATTLE TRAINER", "action": "TRAINER", "condition": "has_trainers", "color": "GREEN"})
    m += extra or []
    for text, target in exits:
        m.append({"text": text, "action": "EXIT", "target_area": target, "condition": "can_exit", "color": "RED"})
    return m


def wild(key, name, level, battle_type, pool, exits, trainers=(), extra=None, catch_cond="has_balls", **more):
    pk = f"ORANGE_{key}_PERCENTAGES"
    POOLS[f"ORANGE_{key}"] = [int(i) for i in pool]
    POOLS[pk] = {str(i): w for i, w in pool.items()}
    a = {"area_type": "wild_route" if battle_type != "cave" else "dungeon", "route_name": name,
         "region": "ORANGE", "level": level, "battle_type": battle_type, "wild_pool_percentages": pk,
         "min_rounds": 2, "trainer_pool": list(trainers),
         "route_menu": wild_menu(exits, bool(trainers), extra, catch_cond), "next_area": exits[0][1]}
    a.update(more)
    AREAS[key] = a
    return a


def event(text, ev, **extra):
    o = {"text": text, "action": "EVENT", "color": "GOLD", "event": ev}
    o.update(extra)
    return o


def town(key, level, explore, local=(), gym=None, extra_travel=()):
    a = {"area_type": "town", "route_name": ISLANDS[key][0], "region": "ORANGE", "level": level,
         "has_gym": bool(gym),
         "explore_options": [{"text": "Pokemon Center", "action": "HEAL"},
                             {"text": "Poke Mart", "action": "SHOP"}] + list(explore),
         "travel_options": [{"text": t, "target_area": k, **({"condition": c} if c else {})}
                            for t, k, c in local] + list(extra_travel) + ships(key)}
    if local:
        a["next_area"] = local[0][1]
    if gym:
        a["gym"] = gym
    AREAS[key] = a
    return a


def leader(name, sprite, team, levels, badge, intro, won, lost, cls="GYM_LEADER", **extra):
    d = {"name": name, "class": cls, "sprite": sprite, "is_boss_battle": True, "team": team,
         "levels": levels, "badge_reward": badge, "rewards": {"balls": 10},
         "dialogue": {"intro": intro, "player_won": won, "player_lost": lost}}
    d.update(extra)
    return d


def gym_trainer(name, cls, sprite, team, levels, line):
    return {"name": name, "class": cls, "sprite": sprite, "team": team, "levels": levels,
            "rewards": {"balls": 5}, "dialogue": {"intro": [line]}}
