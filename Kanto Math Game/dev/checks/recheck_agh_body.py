
# The 10-27 Serebii PokéEarth recheck of Alola (USUM + SM), Galar (SwSh + DLC) and Hisui (PLA),
# critical to low (kanto_handoff/SEREBII_RECHECK_ALOLA_GALAR_HISUI_2026-10-27.md), and S.O.S. battles.
import os
import random as _r
from src.states.overworld import CityState, PlayState
from src.states.battle import WildBattleState
from src.pokemon import balance
fails = 0


def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m)
    fails += 0 if c else 1


g.data.save = lambda *a, **k: None
data = g.loader.area_data
prog = data["STORY_PROGRESSION"]
flags = story.story_flags


def enter_events(area):
    ev = prog[area].get("on_enter_event")
    return ev if isinstance(ev, list) else [ev] if ev else []


def opts(area):
    a = prog[area]
    return (a.get("route_menu") or []) + (a.get("explore_options") or []) + (a.get("travel_options") or [])


def links(area):
    return {o.get("target_area") or o.get("target") for o in opts(area) if o.get("action") in (None, "EXIT", "TRAVEL")}


def pool(area):
    return data.get(prog[area].get("wild_pool_percentages") or "", {})


print("1) critical: the Wild Area (two halves), the DLC areas and Hisui's zones have their full pools")
check(len(pool("WILD_AREA")) >= 100 and len(pool("WILD_AREA_NORTH")) >= 150, "Wild Area South / North pools")
check("WILD_AREA_NORTH" in links("WILD_AREA") and "WILD_AREA" in links("WILD_AREA_NORTH")
      and "HAMMERLOCKE" in links("WILD_AREA_NORTH") and "WILD_AREA_NORTH" in links("HAMMERLOCKE"), "the halves connect")
north = next(o for o in prog["WILD_AREA"]["route_menu"] if o.get("target_area") == "WILD_AREA_NORTH")
check("has_fire_badge" in north["condition"], "North opens after Kabu's badge")
hm = next(o for o in prog["WILD_AREA_NORTH"]["route_menu"] if o.get("target_area") == "HAMMERLOCKE")
check("has_fairy_badge" in hm["condition"], "North -> Hammerlocke keeps the Route 6 gate")
for a, n in (("ISLE_OF_ARMOR", 80), ("CROWN_TUNDRA", 80), ("OBSIDIAN_FIELDLANDS", 80), ("CRIMSON_MIRELANDS", 80),
             ("COBALT_COASTLANDS", 80), ("CORONET_HIGHLANDS", 80), ("ALABASTER_ICELANDS", 80)):
    check(len(pool(a)) >= n, f"{a}: {len(pool(a))} species")
check(any(k in pool("COBALT_COASTLANDS") for k in ("2039", "2044")), "Hisuian forms stay in Hisui pools")
check(prog["WILD_AREA"].get("can_fish") and data.get("WILD_AREA_OLD_ROD_PERCENTAGES"), "Wild Area fishing")

print("2) high: Alola story")
hala = prog["IKI_TOWN"]["gym"]["leader"]
check(hala["badge_reward"] == "FIGHTINIUM_Z" and hala["team"] == [66, 296, 739], "Hala's Grand Trial at Iki Town")
check(prog["HEAHEA_CITY"]["gym"]["requirements"]["badges"] == 2 and prog["SEAFOLK_VILLAGE"]["gym"]["requirements"]["badges"] == 4,
      "later Grand Trials count Hala's badge")
check(story.get_region_gym_badges("ALOLA") .count("FIGHTINIUM_Z") == 1, "Fightinium Z is one of Alola's badges")
for area in ("ALOLA_ROUTE_3", "PANIOLA_TOWN", "DIGLETTS_TUNNEL", "MALIE_CITY"):
    t = next((e["trainer"] for e in enter_events(area) if e["trainer"]["name"] == "{rival_name}"), None)
    check(t and set(t["team_choice"]) == {"722", "725", "728"}, f"{area}: Hau, keyed by starter")
t = next(e["trainer"] for e in enter_events("PANIOLA_TOWN") if e["trainer"]["name"] == "{rival_name}")
check(any(p in (725, 726, 727) for p in t["team_choice"]["722"]), "Hau takes the starter strong against yours")
for area in ("ALOLA_ROUTE_5", "AETHER_HOUSE", "MOUNT_LANAKILA"):
    check(any(e["trainer"]["name"] == "{friend_name}" for e in enter_events(area)), f"{area}: Gladion")
for area, who in (("AKALA_OUTSKIRTS", "Plumeria"), ("ALOLA_ROUTE_15", "Plumeria"), ("MALIE_GARDEN", "Guzma"),
                  ("ROYAL_AVENUE", "Kiawe"), ("LUSH_JUNGLE", "Mallow"), ("KONIKONI_CITY", "Lana")):
    check(any(who in e["trainer"]["name"] for e in enter_events(area)), f"{area}: {who}")
names = [x["name"] for x in prog["AETHER_PARADISE"]["trainer_pool"]]
check(names[-1] == "Lusamine" and any("Faba" in n for n in names) and any("Guzma" in n for n in names), "Aether: Faba, Guzma, then Lusamine")
check(any(o.get("text") == "Title Defense: {rival_name}" for o in opts("ALOLA_POKEMON_LEAGUE")), "Hau's title defense")
check(any(t["name"] == "Acerola" for t in prog["ALOLA_POKEMON_LEAGUE"]["gym"]["trainers"]), "Acerola in the Elite Four")
check(prog["MEGALO_TOWER"]["area_boss"]["id"] == 7003 and "MEGALO_TOWER" in links("ALTAR_SUNNE_MOONE"), "Ultra Necrozma at Megalo Tower")

print("3) high: Galar and Hisui story")
for area in ("GALAR_ROUTE_2", "MOTOSTOKE", "GALAR_ROUTE_5", "GALAR_MINE_NO_2", "STOW_ON_SIDE", "GALAR_ROUTE_7", "CIRCHESTER"):
    t = next((e["trainer"] for e in enter_events(area) if e["trainer"]["name"] == "{rival_name}"), None)
    check(t and set(t["team_choice"]) == {"810", "813", "816"}, f"{area}: Hop, keyed by starter")
for area in ("GALAR_MINE", "GALAR_MINE_NO_2", "STOW_ON_SIDE"):
    check(any(e["trainer"]["name"] == "Bede" for e in enter_events(area)), f"{area}: Bede")
check(any(e["trainer"]["name"] == "Marnie" for e in enter_events("MOTOSTOKE"))
      and any(e["trainer"]["name"] == "Marnie" for e in enter_events("GALAR_ROUTE_9")), "Marnie at Motostoke and Route 9")
cup = [t["name"] for t in prog["WYNDON"]["gym"]["trainers"]]
check(all(any(n in c for c in cup) for n in ("Nessa", "Bea", "Raihan")), f"Champion Cup finals: {cup}")
check(sum(1 for e in enter_events("WEDGEHURST") if e["trainer"]["name"] in ("Sordward", "Shielbert")) == 2, "Sordward and Shielbert")
for area, text in (("WYNDON", "Battle Tower: Leon"), ("BALLONLEA", "Gym Leader Bede"), ("ISLE_OF_ARMOR", "MUSTARD'S FINAL TRIAL"),
                   ("CROWN_TUNDRA", "Battle Peony"), ("CORONET_HIGHLANDS", "Temple of Sinnoh: Volo"),
                   ("JUBILIFE_VILLAGE", "Battle Warden Ingo")):
    check(any(o.get("text") == text for o in opts(area)), f"{area}: {text}")
for area, who in (("JUBILIFE_VILLAGE", "Volo"), ("JUBILIFE_VILLAGE", "Akari"), ("JUBILIFE_VILLAGE", "Adaman")):
    check(any(who in e["trainer"]["name"] for e in enter_events(area)), f"{area}: {who}")
check(sum(1 for x in prog["CORONET_HIGHLANDS"]["trainer_pool"] if "Warden" in x["name"]) >= 3, "Coronet's wardens")

print("4) medium: legendaries boss-only, places, Totems, Hisui legendaries")
wild_legends = [(k, p) for k, v in data.items() if k.endswith("PERCENTAGES") and isinstance(v, dict) and "ULTRA" not in k
                and any(k.startswith(x) for x in ("ALOLA", "GALAR", "OBSIDIAN", "CRIMSON", "COBALT", "CORONET", "ALABASTER", "SLUMBERING", "WILD", "ISLE", "CROWN"))
                for p in v if p.isdigit() and (balance.is_legendary(int(p)) or int(p) in (772, 773, 789, 790))]
check(not wild_legends, f"no legendaries / Type: Null / Cosmog in these wild pools {wild_legends[:4]}")
check(any(o.get("event", {}).get("gift_pokemon") == 772 for o in opts("AETHER_PARADISE")), "Type: Null from Gladion")
check(any(o.get("event", {}).get("gift_pokemon") == 789 for o in opts("LAKE_OF_THE_SUNNE_MOONE")), "a Cosmog at the lake")
for key, boss in (("RUINS_OF_CONFLICT", 785), ("RUINS_OF_ABUNDANCE", 787), ("RUINS_OF_HOPE", 788)):
    check(prog[key]["area_boss"]["id"] == boss and any(key in links(k) for k in prog if isinstance(prog[k], dict)), f"{key}")
check(not prog["MOUNT_LANAKILA"].get("area_boss"), "Tapu Koko moved off Mount Lanakila")
for area, boss in (("BROOKLET_HILL", 752), ("MOUNT_HOKULANI", 777), ("VAST_PONI_CANYON", 784)):
    check(prog[area]["area_boss"]["id"] == boss, f"{area}: USUM Totem {boss}")
check(any((o.get("boss") or {}).get("id") == 743 for o in opts("PONI_MEADOW")), "Mina's Totem Ribombee at Poni Meadow")
for z, ids in (("OBSIDIAN_FIELDLANDS", {481, 492, 645}), ("CRIMSON_MIRELANDS", {482}), ("COBALT_COASTLANDS", {485, 489, 490, 642, 4001}),
               ("CORONET_HIGHLANDS", {483, 484, 488, 491, 493}), ("ALABASTER_ICELANDS", {480, 486, 641})):
    have = {(o.get("boss") or {}).get("id") for o in opts(z)}
    check(ids <= have, f"{z}: Hisui legendaries {sorted(ids - have) or 'all'}")
lair = prog["MAX_LAIR"]["max_raid_den"]["5"]
check("150" in lair and not any(int(p) in range(793, 800) for p in lair), "Max Lair: legendaries, no Ultra Beasts")
for area in ("TEN_CARAT_HILL", "MELEMELE_SEA", "PIKACHU_VALLEY", "LAKE_OF_THE_SUNNE_MOONE", "MEGALO_TOWER", "MAX_LAIR",
             "WILD_AREA_NORTH", "RUINS_OF_CONFLICT"):
    try:
        story.current_area_key = area
        st = CityState(g) if prog[area].get("area_type") == "town" else PlayState(g)
        g.change_state(st)
        st.draw()
        ok = True
    except Exception as e:
        ok = False
        print("     ", type(e).__name__, e)
    check(ok, f"{area} opens")
sprites = os.path.join(g.assets.assets_dir, "sprites", "trainers")
for s in ("plumeria", "faba", "kiawe", "mallow", "lana", "mina", "bede", "sordward", "shielbert", "mustard", "peony", "volo",
          "akari", "adaman", "irida", "kamado", "zisu", "ingo_hisui", "melli", "sabi", "gaeric", "lian", "coin", "charm", "clover"):
    check(os.path.isfile(os.path.join(sprites, s + ".png")), f"sprite {s}.png")

print("5) low: route trainers, S.O.S. tables, exits")
check(len(prog["ALOLA_ROUTE_1"]["trainer_pool"]) >= 5 and len(prog["GALAR_ROUTE_3"]["trainer_pool"]) >= 5, "route trainers")
sos = [k for k, a in prog.items() if isinstance(a, dict) and a.get("sos_pool")]
check(len(sos) >= 40 and all(data.get(prog[k]["sos_pool"]) for k in sos), f"{len(sos)} Alola areas have S.O.S. tables")
check("ALOLA_ROUTE_16" in links("ALOLA_ROUTE_15") and "GALAR_ROUTE_3" in links("MOTOSTOKE"), "exits")

print("6) S.O.S. battles")
story.current_area_key = "ALOLA_ROUTE_1"
mon = mk(731)
mon.level = 20
mon.current_hp = mon.get_max_hp()
story.player_team = [mon]
foe = mk(734)
foe.level = 5
foe.current_hp = foe.get_max_hp()
b = WildBattleState(g, foe, "ALOLA_ROUTE_1")
g.change_state(b)
b.opponent_hp = b.opp_max_hp  # full HP: never calls
check(b._try_sos_call() is None, "a healthy wild Pokemon doesn't call")
b.opponent_hp = 1
_r.seed(3)
lines, tries = None, 0
while tries < 200 and not (lines and b.sos_ally is not None):
    b.sos_ally = None
    lines = b._try_sos_call()
    tries += 1
check(lines and "called for help" in lines[0] and b.sos_ally is not None, f"a weak one calls and an ally answers ({lines})")
ally = b.sos_ally
check(str(ally.id) in data[prog["ALOLA_ROUTE_1"]["sos_pool"]] or ally.id == 734, f"the ally is the caller's species or from the table ({ally.name})")
b.opponent_hp = 0
b.catch_no()
check(b.opponent_pokemon is ally and b.phase == "ENEMY_SUMMON" and b.opponent_hp == b.opp_max_hp, "the ally steps in after the KO")
check(b.sos_chain == 1 and b.sos_ally is None, "the chain counts on")
boss = WildBattleState(g, mk(785), "ALOLA_ROUTE_1", is_boss_battle=True)
boss.opponent_hp = 1
check(all(boss._try_sos_call() is None for _ in range(50)), "bosses and legendaries never call")
story.current_area_key = "KANTO_ROUTE_1"
k = WildBattleState(g, mk(16), "KANTO_ROUTE_1")
k.opponent_hp = 1
check(all(k._try_sos_call() is None for _ in range(50)), "areas without an S.O.S. table: nobody answers")

print(f"\n{'ALL PASS' if not fails else str(fails) + ' FAIL(S)'}")
