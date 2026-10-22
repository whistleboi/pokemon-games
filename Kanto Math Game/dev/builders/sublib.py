"""Builder for sub-region data files (Sevii, Decolore, Sinjoh, Orre)."""
import json


class Sub:
    def __init__(self, region, subregion, prefix, hubs, ship_word="ferry", ship_line=""):
        """hubs: {area_key: (name, condition or None)} reachable from each other by ship."""
        self.region, self.subregion, self.prefix = region, subregion, prefix
        self.hubs, self.ship_word, self.ship_line = hubs, ship_word, ship_line
        self.areas, self.pools, self.missions = {}, {}, []

    def _base(self, key, name, level, area_type):
        a = {"area_type": area_type, "route_name": name, "region": self.region, "level": level}
        if self.subregion:
            a["subregion"] = self.subregion
        self.areas[key] = a
        return a

    def ships(self, here):
        out = []
        for key, (name, cond) in self.hubs.items():
            if key == here:
                continue
            opt = {"text": f"{self.ship_word.title()} to {name}", "target_area": key,
                   "message": f"{self.ship_line} Next stop: {name}!".strip()}
            if cond:
                opt["condition"] = cond
            out.append(opt)
        return out

    def town(self, key, name, level, explore, local=(), gym=None, extra_travel=(), center=True, shop=True,
             ships=True, **more):
        a = self._base(key, name, level, "town")
        a["has_gym"] = bool(gym)
        a["explore_options"] = (([{"text": "Pokemon Center", "action": "HEAL"}] if center else [])
                                + ([{"text": "Poke Mart", "action": "SHOP"}] if shop else []) + list(explore))
        a["travel_options"] = ([{"text": t, "target_area": k, **({"condition": c} if c else {})} for t, k, c in local]
                               + list(extra_travel) + (self.ships(key) if ships else []))
        if local:
            a["next_area"] = local[0][1]
        if gym:
            a["gym"] = gym
        a.update(more)
        return a

    def wild(self, key, name, level, battle_type, pool, exits, trainers=(), extra=(), catch_cond="has_balls",
             area_type=None, **more):
        a = self._base(key, name, level, area_type or ("dungeon" if battle_type in ("cave", "indoor") else "wild_route"))
        menu = []
        if pool:
            pk = f"{self.prefix}_{key}_PERCENTAGES"
            self.pools[f"{self.prefix}_{key}"] = [int(i) for i in pool]
            self.pools[pk] = {str(i): w for i, w in pool.items()}
            a["wild_pool_percentages"] = pk
            menu += [{"text": "CATCH WILD PKMN", "action": "CATCH", "condition": catch_cond, "color": "BLUE"},
                     {"text": "BATTLE WILD PKMN", "action": "BATTLE", "condition": "can_battle", "color": "GREEN"}]
        if trainers:
            menu.append({"text": "BATTLE TRAINER", "action": "TRAINER", "condition": "has_trainers", "color": "GREEN"})
        menu += list(extra)
        for text, target, *cond in exits:
            menu.append({"text": text, "action": "EXIT", "target_area": target,
                         "condition": cond[0] if cond else "can_exit", "color": "RED"})
        a.update({"battle_type": battle_type, "min_rounds": 2 if pool else 0, "trainer_pool": list(trainers),
                  "route_menu": menu, "next_area": exits[0][1]})
        a.update(more)
        return a

    def mission(self, mid, kind, title, desc, cond, reward):
        cond = dict(cond, required_region=self.region)
        self.missions.append({"id": mid, "type": kind, "title": title, "description": desc,
                              "condition": cond, "reward": reward, "region": self.region})

    def save(self, path, extra=None):
        data = {"STORY_PROGRESSION": self.areas, "JOURNAL_MISSIONS": self.missions}
        data.update(self.pools)
        data.update(extra or {})
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(path, "areas:", len(self.areas), "pools:", len(self.pools) // 2)


def event(text, ev, **extra):
    o = {"text": text, "action": "EVENT", "color": "GOLD", "event": ev}
    o.update(extra)
    return o


def trainer(name, cls, sprite, team, balls=4, **extra):
    t = {"name": name, "class": cls, "sprite": sprite, "team": team, "rewards": {"balls": balls}}
    t.update(extra)
    return t


def battle(name, cls, sprite, team, levels, won, balls=10, **extra):
    b = {"name": name, "class": cls, "sprite": sprite, "team": team, "levels": levels,
         "rewards": {"balls": balls}, "dialogue": {"player_won": won}}
    b.update(extra)
    return b


def boss(text, pid, name, level, flag, lines, won, cond, rewards=None, no_catch=True, color="GOLD"):
    return {"text": text, "action": "BOSS", "color": color, "condition": cond, "flag_condition": f"not {flag}",
            "boss": {"id": pid, "name": name, "level": level, "no_catch": no_catch, "victory_flag": flag,
                     "lines": lines, "won": won, "rewards": rewards or {"balls": 5}}}
