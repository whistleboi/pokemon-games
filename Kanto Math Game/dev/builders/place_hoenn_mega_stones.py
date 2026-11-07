"""Hoenn's Mega Stones where Omega Ruby / Alpha Sapphire put them (Jordan, 11-06: all of them before the
League). Locations from PokeBase's ORAS Mega Stone list (pokemondb.net/pokebase/221773); a stone ORAS only
gives after the League (Galladite, Metagrossite, Mewtwonite Y) or in the Delta Episode (Sharpedonite,
Cameruptite) is at the same place, there from the start. Each one is an EVENT: on a walked map it lies on
the floor (its picture, dungeon_sprites.json figures), in a town it's a button; it's given once (got_<stone>).
Writes assets/hoenn_area_data.json and assets/dungeon_sprites.json as text (their own layout kept).
Run once: a second run changes nothing.

    python dev/builders/place_hoenn_mega_stones.py
"""
import json

# area, stone, what's said (route/cave: it lies on the ground; town: who gives it)
MAP = [
    ("HOENN_SEA_MAUVILLE", "BEEDRILLITE", None), ("HOENN_GRANITE_CAVE", "STEELIXITE", None),
    ("HOENN_SHOAL_CAVE", "GLALITITE", None), ("HOENN_SHOAL_CAVE", "SLOWBRONITE", None),
    ("HOENN_METEOR_FALLS", "AERODACTYLITE", None), ("HOENN_FIERY_PATH", "CHARIZARDITE_X", None),
    ("HOENN_SCORCHED_SLAB", "CHARIZARDITE_Y", None), ("HOENN_ROUTE_119", "VENUSAURITE", None),
    ("HOENN_SS_TIDAL", "BLASTOISINITE", None), ("HOENN_ROUTE_124", "PINSIRITE", None),
    ("HOENN_ROUTE_123", "GYARADOSITE", None), ("HOENN_ROUTE_123", "ABOMASITE", None),
    ("HOENN_NEW_MAUVILLE", "AMPHAROSITE", None), ("HOENN_PETALBURG_WOODS", "SCIZORITE", None),
    ("HOENN_ROUTE_127", "HERACRONITE", None), ("HOENN_JAGGED_PASS", "TYRANITARITE", None),
    ("HOENN_RUSTURF_TUNNEL", "AGGRONITE", None), ("HOENN_MT_PYRE", "MEDICHAMITE", None),
    ("HOENN_MT_PYRE", "BANETTITE", None), ("HOENN_ROUTE_110", "MANECTITE", None),
    ("HOENN_SAFARI_ZONE", "ABSOLITE", None), ("HOENN_TEAM_HIDEOUT", "SHARPEDONITE", None),
    ("HOENN_MAGMA_HIDEOUT", "CAMERUPTITE", None),
    ("HOENN_METEOR_FALLS", "SALAMENCITE", "An old woman: My granddaughter loves this stone. I think you should have it."),
]
TOWN = [
    ("RUSTBORO_CITY", "PIDGEOTITE", "Mr. Stone", "Mr. Stone: An intriguing stone! Here, a special Mega Stone in return."),
    ("SOOTOPOLIS_CITY", "SABLENITE", "A Glinting Stone", None),
    ("LILYCOVE_CITY", "ALTARIANITE", "The Collector", "Collector: A lovely Altaria! Take this, it suits a Pokemon like that."),
    ("MAUVILLE_CITY", "LOPUNNITE", "Man in a Suit", "Man in a suit: A Mega Stone for a Trainer with style. Take it!"),
    ("SLATEPORT_CITY", "ALAKAZITE", "Market Stall", "Merchant: This odd stone has been on my stall for ages. It's yours!"),
    ("PACIFIDLOG_TOWN", "KANGASKHANITE", "A Glinting Stone", None),
    ("LAVARIDGE_TOWN", "HOUNDOOMINITE", "A Glinting Stone", None),
    ("VERDANTURF_TOWN", "GARDEVOIRITE", "Wanda", "Wanda: You helped us so much. Please take this stone!"),
    ("VERDANTURF_TOWN", "MAWILITE", "A Glinting Stone", None),
    ("LITTLEROOT_TOWN", "LATIASITE", "Mom", "Mom: A stone came in the mail for you. Two of them, in fact!"),
    ("LITTLEROOT_TOWN", "LATIOSITE", "Mom's Second Stone", "Mom: And here's the other one!"),
    ("LITTLEROOT_TOWN", "MEWTWONITE_X", "A Glinting Stone", None),
    ("FALLARBOR_TOWN", "GALLADITE", "Professor Cozmo", "Professor Cozmo: A strange stone, not a meteorite at all. You should have it."),
    ("MOSSDEEP_CITY", "METAGROSSITE", "Steven's House", "Steven left a stone on his table, with a note: \"For you, my friend.\""),
    ("EVER_GRANDE_CITY", "MEWTWONITE_Y", "A Glinting Stone", None),
]


def label(stone):
    return stone.replace("_", " ").title().replace("Charizardite X", "Charizardite X")


def event(stone, line):
    flag = f"got_{stone.lower()}"
    lines = [line] if line else [f"Something glints on the ground... It's a Mega Stone!"]
    lines.append(f"You found the {label(stone).upper()}!")
    return {"text": "A GLINTING STONE" if not line else "MEGA STONE", "action": "EVENT", "color": "GOLD",
            "flag_condition": f"not {flag}", "event": {"lines": lines, "gift_item": {stone: 1}, "flag": flag}}


def main():
    p = "assets/hoenn_area_data.json"
    text = open(p, encoding="utf-8", newline="").read()
    if "got_beedrillite" in text:
        print("already there")
        return
    data = json.loads(text)
    sp = data["STORY_PROGRESSION"]
    sprites = {}
    for area, stone, line in MAP:
        opt = event(stone, line)
        opt["text"] = f"{label(stone).upper()}" if not line else "AN OLD WOMAN"
        sp[area].setdefault("route_menu", []).insert(0, opt)
        sprites[f"{area}:{opt['text']}"] = {"item": stone} if not line else {"sheet": "NPC 11.png"}
    for area, stone, who, line in TOWN:
        opt = event(stone, line)
        opt["text"] = who if line else f"{who}: {label(stone)}"
        sp[area].setdefault("explore_options", []).append(opt)
    # (each option added as one line, into the area's own list: the file keeps its layout)
    out = text
    added = {}
    for area, stone, line in MAP:
        added.setdefault((area, "route_menu"), []).append(next(o for o in sp[area]["route_menu"] if o["event"]["flag"] == f"got_{stone.lower()}"
                                                                if o.get("event")))
    for area, stone, who, line in TOWN:
        added.setdefault((area, "explore_options"), []).append(next(o for o in sp[area]["explore_options"]
                                                                     if (o.get("event") or {}).get("flag") == f"got_{stone.lower()}"))
    for (area, key), opts in added.items():
        start = out.index(f'"{area}": {{')
        k = out.index(f'"{key}": [', start)
        k += len(f'"{key}": [')
        out = out[:k] + "".join(json.dumps(o, ensure_ascii=False) + ", " for o in opts) + out[k:]
    json.loads(out)
    open(p, "w", encoding="utf-8", newline="").write(out)

    p = "assets/dungeon_sprites.json"
    text = open(p, encoding="utf-8", newline="").read()
    nl = "\r\n" if "\r\n" in text else "\n"
    anchor = '"figures": {'
    i = text.index(anchor) + len(anchor)
    add = "".join(f'{nl}    {json.dumps(k)}: {json.dumps(v)},' for k, v in sprites.items())
    text = text[:i] + add + text[i:]
    json.loads(text)
    open(p, "w", encoding="utf-8", newline="").write(text)
    print(len(MAP), "on the maps,", len(TOWN), "in towns")


if __name__ == "__main__":
    main()
