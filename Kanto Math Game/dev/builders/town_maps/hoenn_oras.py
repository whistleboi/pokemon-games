"""Omega Ruby / Alpha Sapphire's New Mauville story, fitted to our Emerald-built Mauville (Jordan, 11-14: "insert the
storyline of new mauville into mauville, it can be compacted and altered to match what we have"). ORAS's Mauville is a
city under one roof, many levels; ours is Emerald's open town, so its Mauville Hills is one building, its spare house
by the Mart: one hall standing in for the flats.

The story (Bulbapedia's ORAS walkthrough, part 18), in our words:
- After the eighth badge, Wattson waits in the square: the Square Tower's light means trouble in New Mauville. He asks
  you up to his flat in Mauville Hills (scene in MAUVILLE_CITY).
- In the flat he scans your eyes for the security system and asks you to run the check on New Mauville's computer.
- In New Mauville, the computer (where Wattson used to stand to battle) runs the check.
- Back in the flat, Wattson thanks you with TM126 Thunderbolt (Hoenn's own, HTM24).
Mauville Hills also has the frightened Collector and the balcony's TM060 U-turn. The loan shark's Lopunnite is already the
Man in a Suit's, outside.

These are applied over Emerald's maps (emerald.py is written by hgen.py; this file adds to it).
"""

HILLS_ROOM = {
    "art": [
        "cccccccccccccccc",
        "c..N...cc....N.c",
        "c......cc......c",
        "cyy....cc....zzc",
        "c..............c",
        "c.N............c",
        "c..............c",
        "cccccccnnccccccc",
    ],
    "exits": {"n": "OUT:19,14"},
    "buildings": {},
    "people": [
        {"any": [
            {"text": "Wattson", "action": "EVENT", "condition": ["has_badge:RAIN", "not:wattson_new_mauville_asked"],
             "event": {"lines": ["Wattson: Wahahaha! You came! Come in, come in.",
                                 "Wattson: New Mauville is an old power plant under Route 110. Nobody uses it now.",
                                 "Wattson: But the tower lit up, so something may be wrong down there.",
                                 "Wattson: Hold still... Click! That's your eyes scanned. The doors will open for you now.",
                                 "Wattson: Run the check on the computer in New Mauville's back room, then come tell me!"],
                       "flag": "wattson_new_mauville_asked"}},
            {"text": "Wattson", "action": "EVENT", "condition": ["new_mauville_checked", "not:new_mauville_cleared"],
             "event": {"lines": ["Wattson: All clear, you say? Wahahaha! Splendid!",
                                 "Wattson: Here, this is for you. Thunderbolt suits a Trainer with spark!"],
                       "gift_item": {"TM126": 1}, "flag": "new_mauville_cleared"}},
            {"text": "Wattson", "action": "EVENT", "condition": "wattson_new_mauville_asked",
             "event": {"lines": ["Wattson: The computer is in New Mauville's back room. Its door is at the east end of town!"]}},
            {"text": "Wattson", "action": "EVENT",
             "event": {"lines": ["Wattson: Wahahaha! Mauville Hills is a fine place to live. You can see the whole city!"]}},
        ]},
        {"text": "TM060 U-TURN", "action": "EVENT", "found": True, "flag_condition": "not got_tm89_hills",
         "event": {"lines": ["Something was left out on the balcony... It's TM060 U-turn!"], "gift_item": {"TM060": 1},
                   "flag": "got_tm89_hills"}},
        {"text": "Collector", "action": "EVENT",
         "event": {"lines": ["Collector: Eek! Oh, it's only you.",
                             "Collector: A scary man in a suit keeps asking about my rent. I spent it all on my collection!"]}},
    ],
    "theme": "room",
    "title": "Mauville Hills",
}

WATTSON_SCENE = {
    "trigger": "enter", "condition": "has_badge:RAIN", "flag": "wattson_square_talk",
    "cast": [{"sheet": "em_127.png", "from": [19, 9], "to": "player", "leave": "back",
              "lines": ["Wattson: Wahahaha! There you are! See the tower in the square? Its light is on.",
                        "Wattson: That means something's up in New Mauville. Come up to my flat in Mauville Hills!",
                        "Wattson: It's the building by the Mart. I'll explain there."]}],
}


def apply(maps):
    m = maps["MAUVILLE_CITY"]
    m["inside"] = dict(m.get("inside") or {}, **{"19,14": "hills"})
    m["rooms"] = dict(m.get("rooms") or {}, hills=HILLS_ROOM)
    m["scenes"] = list(m.get("scenes") or []) + [WATTSON_SCENE]
    from . import oras_new_mauville   # (New Mauville: ORAS's layout, Emerald's tiles; the computer where Wattson stood)
    oras_new_mauville.new_mauville(maps)
