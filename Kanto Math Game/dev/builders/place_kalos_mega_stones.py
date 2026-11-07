"""Kalos's Mega Stones (Jordan, 11-06), one place each: where X / Y put them (Kalos is X / Y's region), and
the stones X / Y doesn't have where Legends: Z-A puts them in Lumiose (its districts, the Quasartico Inc. and
Vernal Avenue shops, the Battle Club's prizes; Jaune District, Centrico Plaza and the side missions, which
aren't places here, are Lumiose City itself). The Kanto starters' stones are the Stone Emporium's, as in X / Y
(its other way, Sycamore's gift, would make two). On a walked map a stone lies on the floor; in a town it's a
button (got_<stone>, once); a shop sells it. Hyperspace no longer gives stones (its prizes: Rare Candy and star
berries). Adds to assets/kalos_area_data.json and assets/dungeon_sprites.json as text. Run once.

    python dev/builders/place_kalos_mega_stones.py
"""
import json

MAP = [  # area, stone, who (None: it lies on the ground)
    ("FROST_CAVERN", "ABOMASITE", None), ("FROST_CAVERN", "SCIZORITE", None),
    ("REFLECTION_CAVE", "ALAKAZITE", None), ("AZURE_BAY", "AMPHAROSITE", "AN OLD MAN"),
    ("CHAMBER_OF_EMPTINESS", "BANETTITE", None), ("VICTORY_ROAD_KALOS", "GARCHOMPITE", None),
    ("SANTALUNE_FOREST", "HERACRONITE", None), ("SANTALUNE_FOREST", "PINSIRITE", None),
    ("KALOS_ROUTE_16", "HOUNDOOMINITE", None), ("KALOS_ROUTE_16", "MANECTITE", None),
    ("GLITTERING_CAVE", "KANGASKHANITE", None), ("TOWER_OF_MASTERY", "LUCARIONITE", "KORRINA"),
    ("KALOS_ROUTE_7", "MAWILITE", None), ("POKEMON_VILLAGE", "MEWTWONITE_X", None),
    ("POKEMON_VILLAGE", "MEWTWONITE_Y", None),
]
LINES = {"AMPHAROSITE": "Old man: My Ampharos would want you to have this.",
         "LUCARIONITE": "Korrina: You beat me fair and square! This Mega Stone is yours."}
TOWN = [  # area, stone, button, line
    ("KILOUDE_CITY", "ABSOLITE", "Your Rival", "Your rival: You're the real deal. Take this Absolite!"),
    ("AMBRETTE_TOWN", "AERODACTYLITE", "Fossil Lab Scientist", "Scientist: We dug this up with a fossil. It's a Mega Stone!"),
    ("CYLLAGE_CITY", "AGGRONITE", "Gym Wall: Aggronite", None),
    ("CYLLAGE_CITY", "TYRANITARITE", "Gym Wall: Tyranitarite", None),
    ("LUMIOSE_CITY", "GARDEVOIRITE", "Diantha at Cafe Soleil", "Diantha: A Ralts' best friend is this stone. Take good care of it!"),
    ("LAVERRE_CITY", "GENGARITE", "A Black-Haired Woman", "Woman: This stone gives me shivers. You take it!"),
    ("LAVERRE_CITY", "MEDICHAMITE", "By the Well", None),
    ("COURIWAY_TOWN", "GYARADOSITE", "Waterfall: Gyaradosite", None),
    # Legends: Z-A's
    ("LUMIOSE_VERT_DISTRICT", "BEEDRILLITE", "Vert Sector 5", None),
    ("LUMIOSE_VERT_DISTRICT", "DRAGONINITE", "Vert Sector 3", None),
    ("LUMIOSE_BLEU_DISTRICT", "BARBARACITE", "Bleu Sector 5", None),
    ("LUMIOSE_BLEU_DISTRICT", "FROSLASSITE", "Aymlis Park: Froslassite", None),
    ("LUMIOSE_BLEU_DISTRICT", "SLOWBRONITE", "Aymlis Park: Slowbronite", None),
    ("LUMIOSE_BLEU_DISTRICT", "STARMINITE", "Bleu Sector 9", None),
    ("LUMIOSE_MAGENTA_DISTRICT", "ALTARIANITE", "Magenta Sector 4", None),
    ("LUMIOSE_MAGENTA_DISTRICT", "HAWLUCHANITE", "Magenta Sector 3", None),
    ("LUMIOSE_MAGENTA_DISTRICT", "VICTREEBELITE", "Magenta Sector 9", None),
    ("LUMIOSE_CITY", "CAMERUPTITE", "Jaune Sector 3", None),
    ("LUMIOSE_CITY", "ZYGARDITE", "Centrico Plaza", None),
    ("LUMIOSE_CITY", "LATIASITE", "Siblings of the Sky", "A girl: Two stones fell from the sky! Take one... no, take both!"),
    ("LUMIOSE_CITY", "LATIOSITE", "Siblings of the Sky (2)", "A girl: And here's the other one!"),
]
BATTLE_CLUB = ["SCEPTILITE", "BLAZIKENITE", "SWAMPERTITE", "CHESNAUGHTITE", "DELPHOXITE", "GRENINJITE"]
SHOPS = [  # Lumiose City: button, stock
    ("Stone Emporium", ["VENUSAURITE", "CHARIZARDITE_X", "CHARIZARDITE_Y", "BLASTOISINITE"]),
    ("Quasartico Inc.", ["CLEFABLITE", "CHANDELURITE", "DRAGALGITE", "DRAMPANITE", "EELEKTROSSITE", "EXCADRITE",
                         "FALINKSITE", "MALAMARITE", "PYROARITE", "SCOLIPITE", "SCRAFTINITE", "SKARMORITE", "FLOETTITE",
                         "PIDGEOTITE", "GLALITITE", "SABLENITE", "SHARPEDONITE", "SALAMENCITE", "METAGROSSITE",
                         "LOPUNNITE", "GALLADITE", "AUDINITE", "DIANCITE"]),
    ("Vernal Avenue Shop", ["EMBOARITE", "FERALIGITE", "MEGANIUMITE", "STEELIXITE"]),
]


def label(stone):
    return stone.replace("_", " ").title()


def ev(stone, line, text):
    flag = f"got_{stone.lower()}"
    lines = [line] if line else ["Something glints... It's a Mega Stone!"]
    return {"text": text, "action": "EVENT", "color": "GOLD", "flag_condition": f"not {flag}",
            "event": {"lines": lines + [f"You found the {label(stone).upper()}!"], "gift_item": {stone: 1}, "flag": flag}}


def insert(text, area, key, opts):
    start = text.index(f'"{area}": {{')
    k = text.index(f'"{key}": [', start) + len(f'"{key}": [')
    return text[:k] + "".join(json.dumps(o, ensure_ascii=False) + ", " for o in opts) + text[k:]


def main():
    p = "assets/kalos_area_data.json"
    text = open(p, encoding="utf-8", newline="").read()
    if "got_abomasite" in text:
        print("already there")
        return
    sprites, add = {}, {}
    for area, stone, who in MAP:
        o = ev(stone, LINES.get(stone), who or label(stone).upper())
        add.setdefault((area, "route_menu"), []).append(o)
        sprites[f"{area}:{o['text']}"] = {"item": stone} if not who else {"sheet": "NPC 11.png"}
    for area, stone, button, line in TOWN:
        add.setdefault((area, "explore_options"), []).append(ev(stone, line, button))
    club = {"text": "Z-A Battle Club", "action": "EVENT", "color": "GOLD", "flag_condition": "not got_battle_club_stones",
            "condition": "has_voltage_badge",
            "event": {"lines": ["Battle Club host: You've climbed our ranks! Our prize stones are yours."]
                      + [f"You received the {label(s).upper()}!" for s in BATTLE_CLUB],
                      "gift_item": {s: 1 for s in BATTLE_CLUB}, "flag": "got_battle_club_stones"}}
    add.setdefault(("LUMIOSE_CITY", "explore_options"), []).append(club)
    for button, stock in SHOPS:
        add[("LUMIOSE_CITY", "explore_options")].append({"text": button, "action": "SHOP", "stock": stock})
    for (area, key), opts in add.items():
        text = insert(text, area, key, opts)
    # Hyperspace: no stones any more (its prizes are Rare Candy and star berries)
    import re
    text, n = re.subn(r', "stones": \[[^\]]*\]', "", text)
    data = json.loads(text)
    open(p, "w", encoding="utf-8", newline="").write(text)

    p = "assets/dungeon_sprites.json"
    t = open(p, encoding="utf-8", newline="").read()
    nl = "\r\n" if "\r\n" in t else "\n"
    i = t.index('"figures": {') + len('"figures": {')
    t = t[:i] + "".join(f'{nl}    {json.dumps(k)}: {json.dumps(v)},' for k, v in sprites.items()) + t[i:]
    json.loads(t)
    open(p, "w", encoding="utf-8", newline="").write(t)
    print(len(MAP), "on maps,", len(TOWN) + 1, "town buttons,", sum(len(s) for _b, s in SHOPS), "in shops;",
          n, "Hyperspace zones' stones taken off")


if __name__ == "__main__":
    main()
