"""Johto's walkable maps for dev/builders/build_town_maps.py (see its docstring for the characters)."""

MAPS = {
    # New Bark Town: Elm's Lab top left, your house top right, Elm's house (SE) and a neighbour's (SW),
    # two Headbutt trees between the top buildings, the sea on the east (scenery toward Route 27).
    "NEW_BARK_TOWN": {
        "art": [
            "TTTTTTTTTTTTTTTTTTTTTTTTTTT~~~",
            "TTTTTTTTTTTTTTTTTTTTTTTTTT~~~~",
            "TT..LLLLLLLL..T..PPPPP..TTT~~~",
            "TT..LLLLLLLL.....PPPPP...TT~~~",
            "TT..LLLLLLLL..T..PPPPP....T~~~",
            "TT..LLLDLLLL.....PPDPP.....~~~",
            "<......=............=......s~~",
            "<..N...=============.......s~~",
            "<......=..................ss~~",
            "T......=..HHHHH....EEEEE...s~~",
            "T......=..HHHHH....EEEEE..ss~~",
            "T......=..HHDHH....EEDEE..s~~~",
            "T..ff..=====..=======.....s~~~",
            "T........ff..........ff...s~~~",
            "TTTTTTTTTTTTTTTTTTTTTTTTTTT~~~",
        ],
        "exits": {"<": "JOHTO_ROUTE_29"},
        "buildings": {"L": "lab", "P": "home", "H": "house", "E": "house"},
        "people": ["Talk to Nice Lady"],
    },
    # Route 29: Cherrygrove (west) to New Bark (east); the gatehouse north to Route 46; tall grass in
    # patches; the ledges are fences with gaps; sand patches; a Headbutt tree by the top-left fence.
    "JOHTO_ROUTE_29": {
        "art": [
            "TTTTTTTTTTTTTTTTTTTTTTTTTTGGGGGTTTTTTTTTTTTTTTTTTTTTTTTTTTTT",
            "TTTTTTTTTTTTTTTTTTTTTTTTTTGGGGGTTTTTTTTTTTTTTTTTTTTTTTTTTTTT",
            "TTTTTTTTTTTTTTTTTTTTTTTTTTGGDGGTTTTTTTTTTTTTTTTTTTTTTTTTTTTT",
            "T#####..ff.....T.....ff.......ff.....TT..........TT.......TT",
            "<..ss.#...\"\"\"\"..T.#####..##.........\"\"\"\"\"\"\"......\"\"\"\"\".....>",
            "<..ss.#...\"\"\"\".......\"\"\"\"...........\"\"\"\"\"\"\"....##\"\"\"\"\".....>",
            "<.....#...\"\"\"\".......\"\"\"\"....T.......\"\"\"\"\"\"\"......\"\"\"\"\"....>",
            "<..TT.....\"\"\"\"..............................TT.......\"\"\"\"\".>",
            "T........#####..ss........\"\"\"\"\"......ss.......#####........T",
            "T..\"\"\"\"\"\".........ss......\"\"\"\"\"......ss.............ss.....T",
            "T..\"\"\"\"\"\".....T...........\"\"\"\"\".........T...........ss.....T",
            "TT.\"\"\"\"\"\".......##########........\"\"\"\"\"\"\"\"....T............T",
            "TT.......................T........\"\"\"\"\"\"\"\".................T",
            "TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT",
        ],
        "exits": {"<": "CHERRYGROVE_CITY", ">": "NEW_BARK_TOWN", "D": "JOHTO_ROUTE_46"},
        "buildings": {"G": "gate"},
    },
    # Cherrygrove City: the Mart (blue roof) and the Pokemon Center (orange) at the top, the wide sand road
    # left of the Mart north to Route 30, the long road east to Route 29, a north-south road joining the two
    # east-west roads, three houses (the Guide Gent's, the fisherman's with Mystic Water, one locked), the sea
    # and beach west, the pond behind the trees north of the Center (out of reach), the cliffs south.
    "CHERRYGROVE_CITY": {
        "art": [
            "TTTTTTTTTTTTTT^^^TTTTTTTTTTTTTTTTTTT",
            "~~~~~~TTTTTTTT===TTTTT~~~TTTTTTTTTTT",
            "~~~~~ss.......===.MMMM.TTT.CCCCC.TTT",
            "~~~~~ss.......===.MMMM.....CCCCC..TT",
            "~~~~ss........===.MMDM.....CCDCC..fT",
            "~~~~ss........=====================>",
            "~~~~ss........=.......=............>",
            "~~~~ss..AAAA..=..BBBB.=...HHHH....TT",
            "~~~~ss..AAAA..=..BBBB.=...HHHH...fTT",
            "~~~~ss..AADA..=..BBDB.=...HHDH...fTT",
            "~~~~~ss.......=.......===========..T",
            "~~~~~ss...N........................T",
            "~~~~~~sss....rrrrrrrrrrrTTTTTTTTTTTT",
            "~~~~~~~~ssTTTTTTTTTTTTTTTTTTTTTTTTTT",
        ],
        "exits": {"^": "JOHTO_ROUTE_30", ">": "JOHTO_ROUTE_29"},
        "buildings": {"M": "mart", "C": "center", "A": "gent", "B": "fisher", "H": "house"},
        "people": ["Wake Sleeping Man"],
    },
}
