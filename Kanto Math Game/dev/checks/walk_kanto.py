
# Kanto side-area walk (areas_08_kanto.patch): the S.S. Anne docked at Vermilion
story.badges = {"KANTO": []}
story.inventory = {}
story.story_flags = {"visited_PALLET_TOWN": True, "received_starter_kanto": True,  # past Oak's lab and Parcel
                     "received_pokedex_kanto": True}
story.defeated_trainers = {}
R, S = "KANTO", "PALLET_TOWN"
seen = report("start", S, set())
for b in ["BOULDER", "CASCADE"]:
    badge(R, b)
seen = report("BOULDER + CASCADE", S, seen)
print("   FAIL" if "KANTO_SS_ANNE" in seen else "   OK", "S.S. Anne needs the S.S. Ticket")
story.inventory["SS_TICKET"] = 1
story.story_flags["visited_LAVENDER_TOWN"] = True  # (the Underground Path to Vermilion opens after Lavender: Jordan, 11-08)
# (11-17: the walked S.S. Anne has no menu gauntlet or gauntlet flag any more; kanto_maps and kanto_playthrough walk its story)
print("   OK" if "VERMILLION_CITY" in links("KANTO_SS_ANNE") and "KANTO_SS_ANNE" in links("VERMILLION_CITY") else "   FAIL", "S.S. Anne <-> Vermilion")
# (the rival on the ship is a scene on the walked map now, not the last of a trainer list: kanto_maps plays it)
