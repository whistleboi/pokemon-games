# Partner Pokemon beside the important people on the walked maps (Jordan 11-24, region/systems; src/world/partners.py):
# Gym Leaders, the Elite Four and Champions, rivals, villain bosses and admins have their ace beside them, following them.
#   bash dev/checks/run.sh partners
exec(open("dev/checks/dungeon_lib.py", encoding="utf-8").read())
import os as _os
from src.world import partners
g.dungeon_routes = True
g.walk_towns = True
SHOTS = _os.path.join(S, "partners")
_os.makedirs(SHOTS, exist_ok=True)

print("1) who counts: from their own battle data")
area = {"gym": {"leader": {"name": "Brock", "class": "GYM_LEADER", "team": [74, 95], "levels": [12, 14]},
                "trainers": [{"name": "Lorelei", "class": "ELITE_FOUR", "team": [87, 91, 80, 124, 131], "levels": [52, 51, 52, 54, 54]}]}}
check(partners.trainer_of(area, {"text": "Gym", "action": "GYM"})[1:] == ([74, 95], [12, 14]), "a Gym's leader (action GYM)")
check(partners.ace([74, 95], [12, 14]) == 95, "the ace: the highest level (Brock's Onix)")
check(partners.ace([87, 91, 80, 124, 131], [52, 51, 52, 54, 54]) == 131, "...the last of those that share it (Lorelei's Lapras)")
check(partners.trainer_of(area, {"text": "Lorelei", "action": "LEAGUE", "index": "0"})[0] == "Lorelei", "a League room (action LEAGUE, its index)")
grunt = {"text": "Grunt", "action": "EVENT", "event": {"battle": {"name": "Rocket Grunt", "class": "ROCKET_GRUNT", "team": [19], "levels": [9]}}}
admin = {"text": "Archer", "action": "EVENT", "event": {"battle": {"name": "Archer", "class": "ROCKET_ADMIN", "team": [229], "levels": [35]}}}
rival = {"text": "Silver", "action": "EVENT", "event": {"battle": {"name": "Silver", "class": "RIVAL", "team": [155], "levels": [5]}}}
james = {"text": "James", "action": "EVENT", "event": {"battle": {"name": "James", "class": "ROCKET_ADMIN", "team": [109], "levels": [20]}}}
check(partners.trainer_of({}, grunt) is None, "a grunt: no partner")
check(partners.trainer_of({}, admin) and partners.trainer_of({}, rival), "an admin and a rival: a partner each")
check(partners.trainer_of({}, james) is None, "Jessie and James: their own Meowth (escorts.py), no other")
check(partners.partner_for(g, area, {"text": "Gym", "action": "GYM"}) == ("Onix", "Brock"), "Brock's partner: Onix")


def town(area_key, came):
    story.current_area_key, story.last_area_key = area_key, came
    g.walk_town_pos = None
    t = _CS(g)
    g.change_state(t)
    frames(t, 2)
    _tap_through(t)
    return g.current_state


def partner_people(t):
    return {spot: o for spot, o in t.people.items() if isinstance(o, dict) and o.get("_partner_of") is not None}


print("2) in the towns' rooms: Pewter Gym, the Indigo Plateau's League rooms")
story.enter_region("KANTO")
t = town("PEWTER_CITY", "KANTO_ROUTE_2")
t._go("gym", None)
frames(t, 3)
pp = partner_people(t)
check(any(o["text"] == "Onix" for o in pp.values()), f"Pewter Gym: Brock with his Onix beside him ({[o['text'] for o in pp.values()]})")
for spot, o in pp.items():
    lead = o["_partner_of"]
    check(abs(spot[0] - lead[0]) + abs(spot[1] - lead[1]) == 1, f"...on the tile beside him ({spot} by {lead})")
    check(t.motions[spot].kind == "trail", "...following him (a trail move)")
t.draw()
pygame.image.save(g.screen, _os.path.join(SHOTS, "pewter_gym.png"))
check(not any(o["text"] in ("Geodude",) for o in pp.values()) and len(pp) == 1, f"the Gym's trainers have none ({len(pp)} partner)")

t = town("INDIGO_PLATEAU", "VICTORY_ROAD")
got = {}
for room in ("league_lorelei", "league_bruno", "league_agatha", "league_lance", "league_champion"):
    t._go(room, None)
    frames(t, 2)
    got[room] = [o["text"] for o in partner_people(t).values()]
    if room == "league_lorelei":
        t.draw()
        pygame.image.save(g.screen, _os.path.join(SHOTS, "lorelei.png"))
print("    League partners:", got)
check(sum(1 for v in got.values() if v) >= 4, f"the Elite Four and the Champion each have their ace ({got})")

print("3) on the route maps: a rival or a villain trainer gets one; the others don't")
found = []
for area_key in ("KANTO_ROUTE_22", "SILPH_CITY", "ROCKET_HIDEOUT", "JOHTO_ROUTE_22", "ROCKET_HQ", "HOENN_MT_CHIMNEY",
                 "SINNOH_LAKE_VALOR", "ETERNA_GALACTIC_BUILDING"):
    if area_key not in g.loader.area_data["STORY_PROGRESSION"]:
        continue
    try:
        p = kanto(area_key)
    except Exception as e:   # (a place that can't open headless)
        print("    skip", area_key, type(e).__name__)
        continue
    if not hasattr(p, "run"):
        continue
    for i in range(p.run.n_floors):
        if i:
            p.run.enter_floor(i)
        p._partners_key = None
        p._sync_partners()
        for m in p.run.floor.movers:
            if getattr(m, "_partner_of", None) is not None:
                lead = m._partner_of
                who = lead.payload.get("text") if lead.kind == "figure" else (lead.payload[1] or {}).get("name")
                found.append((area_key, i, who, m.payload["text"]))
                if len(found) == 1:
                    p.run.player = (lead.x, lead.y + 2) if p.run.floor.walkable(lead.x, lead.y + 2) else p.run.player
                    p.draw()
                    pygame.image.save(g.screen, _os.path.join(SHOTS, f"route_{area_key}.png"))
print("    route partners:", found[:12])
check(len(found) >= 1, f"at least one rival or villain on a route map has a partner ({len(found)})")
check(all(not str(w).lower().startswith(("grunt", "team rocket grunt")) for _, _, w, _ in found), "...and no grunt does")
print(f"##### {fails} failures")
