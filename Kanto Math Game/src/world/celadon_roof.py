"""Celadon Dept. Store's roof, FireRed's (11-23, the Kanto encyclopedia cleanup): the three vending machines sell drinks
(Fresh Water $200, Soda Pop $300, Lemonade $350, FireRed's prices), and the thirsty little girl trades a drink for a TM,
one TM per kind of drink (FireRed's flags 0x294-0x296): Fresh Water -> Light Screen, Soda Pop -> Safeguard,
Lemonade -> Reflect. The roof's map (k_batch12, CELADON_CITY "dept_roof"):
    sign event {"world": "celadon_roof", "drink": "FRESH_WATER"}   a vending machine: pay and get the drink
    person event {"world": "celadon_roof", "girl": true}            give her the first drink she hasn't had yet"""
from src.pokemon import forms

PRICES = {"FRESH_WATER": 200, "SODA_POP": 300, "LEMONADE": 350}
TRADES = [("FRESH_WATER", "TM075", "Light Screen", "got_celadon_roof_tm_water"),
          ("SODA_POP", "TM236", "Safeguard", "got_celadon_roof_tm_soda"),
          ("LEMONADE", "TM074", "Reflect", "got_celadon_roof_tm_lemonade")]


def event(state, ev, lines, show):
    game = state.game
    story = game.story_manager
    me = getattr(game, "player_name", "You")
    head = list(lines or [])
    if ev.get("drink"):
        item = ev["drink"]
        cost = PRICES[item]
        name = forms.item_label(item)
        head.append(f"A vending machine. {name}: ${cost}.")
        if getattr(story, "money", 0) < cost:
            show(head + ["You don't have enough money."])
            return
        story.money -= cost
        story.inventory[item] = story.inventory.get(item, 0) + 1
        show(head + [f"{me} paid ${cost}.", f"A can of {name} popped out!"])
        return
    if ev.get("girl"):
        head = []   # (her own words below)
        left = [t for t in TRADES if not story.story_flags.get(t[3])]
        if not left:
            show(head + ["Little girl: I'm not thirsty any more! Thank you!"])
            return
        have = next((t for t in left if story.inventory.get(t[0], 0) > 0), None)
        if not have:
            show(head + ["Little girl: I'm thirsty! I want something to drink!"])
            return
        item, tm, move, flag = have
        story.inventory[item] -= 1
        story.inventory[tm] = story.inventory.get(tm, 0) + 1
        story.story_flags[flag] = True
        show(head + [f"Little girl: I'm thirsty! Is that {forms.item_label(item)}? Can I have it?",
                     f"{me} gave the {forms.item_label(item)} away.",
                     "Little girl: Yay! Thank you! You can have this from me!",
                     f"{me} received the TM {move}!"])
        return
    show(head)
