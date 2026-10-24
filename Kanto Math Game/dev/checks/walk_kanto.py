
# Kanto side-area walk (areas_08_kanto.patch): the S.S. Anne docked at Vermilion
story.badges = {"KANTO": []}
story.inventory = {}
story.story_flags = {"visited_PALLET_TOWN": True}
story.defeated_trainers = {}
R, S = "KANTO", "PALLET_TOWN"
seen = report("start", S, set())
for b in ["BOULDER", "CASCADE"]:
    badge(R, b)
seen = report("BOULDER + CASCADE", S, seen)
print("   FAIL" if "KANTO_SS_ANNE" in seen else "   OK", "S.S. Anne needs the S.S. Ticket")
story.inventory["SS_TICKET"] = 1
expansion_check("kanto side areas", ["KANTO_SS_ANNE"], S)
print("   OK" if "VERMILLION_CITY" in links("KANTO_SS_ANNE") and "KANTO_SS_ANNE" in links("VERMILLION_CITY") else "   FAIL", "S.S. Anne <-> Vermilion")
pool = PROG["KANTO_SS_ANNE"]["trainer_pool"]
print("   OK" if pool[-1]["name"] == "Rival Blue" and pool[-1].get("is_boss_battle") else "   FAIL", "S.S. Anne ends on the rival")
