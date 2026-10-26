# [REF-0084: Items]
"""Items that work like the games (Jordan): Poke Mart stock and what each item does.

MEDICINE heals HP (Potion 20, Super Potion 60, Hyper Potion 120, Max Potion all), cures conditions
(Antidote, Paralyze Heal, Awakening, Burn Heal, Ice Heal, Full Heal) or both (Full Restore), or
revives (Revive half HP, Max Revive all). BATTLE items raise stats (X Attack... +2, like Gen 7+),
crits (Dire Hit) or guard against stat drops (Guard Spec.). Repels keep wild Pokemon away: here a
route can be left without battling while one lasts (Repel 2 routes, Super 4, Max 5). An Escape Rope
leads out of a cave or building to the last Pokemon Center.

STANDARD_MART: the Poke Mart counter of the games (Gen 4 on), by badges earned in the region.
SPECIALTY_BALLS: the second counter's balls, by badges. DEPARTMENT: what department stores add."""

MEDICINE = {
    "POTION": {"heal": 20, "price": 200, "text": "Restores 20 HP."},
    "SUPER_POTION": {"heal": 60, "price": 700, "text": "Restores 60 HP."},
    "HYPER_POTION": {"heal": 120, "price": 1500, "text": "Restores 120 HP."},
    "MAX_POTION": {"heal": "full", "price": 2500, "text": "Fully restores HP."},
    "FULL_RESTORE": {"heal": "full", "cure": "all", "price": 3000, "text": "Fully restores HP and cures any condition."},
    "FRESH_WATER": {"heal": 30, "price": 200, "text": "Water with lots of minerals. Restores 30 HP."},
    "SODA_POP": {"heal": 50, "price": 300, "text": "A fizzy soda drink. Restores 50 HP."},
    "LEMONADE": {"heal": 70, "price": 400, "text": "A very sweet drink. Restores 70 HP."},
    "MOOMOO_MILK": {"heal": 100, "price": 600, "text": "Rich milk from Miltank. Restores 100 HP."},
    "ANTIDOTE": {"cure": ["poison", "toxic"], "price": 200, "text": "Cures poison."},
    "PARALYZE_HEAL": {"cure": ["paralysis"], "price": 200, "text": "Cures paralysis."},
    "AWAKENING": {"cure": ["sleep"], "price": 100, "text": "Wakes up a sleeping Pokemon."},
    "BURN_HEAL": {"cure": ["burn"], "price": 200, "text": "Heals a burn."},
    "ICE_HEAL": {"cure": ["freeze"], "price": 200, "text": "Thaws out a frozen Pokemon."},
    "FULL_HEAL": {"cure": "all", "price": 400, "text": "Cures any status condition."},
    "REVIVE": {"revive": 0.5, "price": 2000, "text": "Revives a fainted Pokemon with half its HP."},
    "MAX_REVIVE": {"revive": 1.0, "price": 4000, "text": "Revives a fainted Pokemon with all its HP."},
    "RARE_CANDY": {"price": 10000, "text": "Raises a Pokemon's level by one."},
}
BATTLE = {
    "X_ATTACK": {"stat": "ATTACK", "price": 1000, "text": "Sharply raises Attack in battle."},
    "X_DEFENSE": {"stat": "DEFENSE", "price": 2000, "text": "Sharply raises Defense in battle."},
    "X_SP_ATK": {"stat": "SPATK", "price": 1000, "text": "Sharply raises Sp. Atk in battle."},
    "X_SP_DEF": {"stat": "SPDEF", "price": 2000, "text": "Sharply raises Sp. Def in battle."},
    "X_SPEED": {"stat": "SPEED", "price": 1000, "text": "Sharply raises Speed in battle."},
    "X_ACCURACY": {"stat": "ACCURACY", "price": 1000, "text": "Sharply raises accuracy in battle."},
    "DIRE_HIT": {"focus": 2, "price": 1000, "text": "Makes critical hits much more likely in battle."},
    "GUARD_SPEC": {"mist": 5, "price": 1500, "text": "Stops your team's stats being lowered for five turns."},
}
FIELD = {
    "REPEL": {"repel": 2, "price": 400, "text": "Keeps wild Pokemon away: leave the next 2 routes without battling."},
    "SUPER_REPEL": {"repel": 4, "price": 700, "text": "Keeps wild Pokemon away for the next 4 routes."},
    "MAX_REPEL": {"repel": 5, "price": 900, "text": "Keeps wild Pokemon away for the next 5 routes."},
    "ESCAPE_ROPE": {"escape": True, "price": 1000, "text": "Leads out of a cave or building, to the last Pokemon Center."},
}
BALL_PRICES = {"POKE_BALLS": 1000, "GREAT_BALL": 600, "ULTRA_BALL": 800, "PREMIER_BALL": 20, "NET_BALL": 1000,
               "DIVE_BALL": 1000, "NEST_BALL": 1000, "REPEAT_BALL": 1000, "TIMER_BALL": 1000, "QUICK_BALL": 1000,
               "DUSK_BALL": 1000, "HEAL_BALL": 300, "LUXURY_BALL": 3000}

# Badges in the region -> what the Poke Mart counter adds (Gen 4 on).
STANDARD_MART = [
    (0, ["POKE_BALLS", "POTION", "ANTIDOTE", "PARALYZE_HEAL", "ESCAPE_ROPE"]),
    (1, ["GREAT_BALL", "SUPER_POTION", "AWAKENING", "BURN_HEAL", "ICE_HEAL", "REPEL"]),
    (3, ["HYPER_POTION", "SUPER_REPEL", "REVIVE"]),
    (5, ["ULTRA_BALL", "FULL_HEAL", "MAX_REPEL"]),
    (7, ["MAX_POTION"]),
    (8, ["FULL_RESTORE"]),
]
SPECIALTY_BALLS = [(2, ["NET_BALL", "NEST_BALL"]), (3, ["QUICK_BALL", "DUSK_BALL", "HEAL_BALL"]),
                   (4, ["DIVE_BALL", "REPEAT_BALL", "TIMER_BALL"]), (5, ["LUXURY_BALL"])]
DEPARTMENT = ["X_ATTACK", "X_DEFENSE", "X_SP_ATK", "X_SP_DEF", "X_SPEED", "X_ACCURACY", "DIRE_HIT", "GUARD_SPEC",
              "FRESH_WATER", "SODA_POP", "LEMONADE"]


def info(item):
    return MEDICINE.get(item) or BATTLE.get(item) or FIELD.get(item) or {}


def price(item):
    if item in BALL_PRICES:
        return BALL_PRICES[item]
    return info(item).get("price")


def describe(item):
    from src.pokemon import catching
    return info(item).get("text") or catching.BALL_TEXT.get(item, "")


def standard_stock(badges):
    """The Poke Mart counter for this many badges (in the region)."""
    out = []
    for need, items in STANDARD_MART + SPECIALTY_BALLS:
        if badges >= need:
            out += items
    return out


def medicine_effect(item, pokemon):
    """Use a medicine on a Pokemon (outside or inside battle). Returns (used, lines). The caller
    takes the item from the Bag when used."""
    data = MEDICINE.get(item, {})
    name = pokemon.display_name
    mx = pokemon.get_max_hp()
    fainted = pokemon.current_hp <= 0
    label = item.replace("_", " ").title()
    if "revive" in data:
        if not fainted:
            return False, [f"{name} isn't fainted! The {label} won't have any effect."]
        pokemon.current_hp = max(1, int(mx * data["revive"]))
        if getattr(pokemon, "status", None):
            pokemon.cure_status()
        return True, [f"{name} was revived!", f"{name} has {pokemon.current_hp} HP."]
    if fainted:
        return False, [f"The {label} won't have any effect on a fainted {name}."]
    lines, did = [], False
    cure = data.get("cure")
    status = getattr(pokemon, "status", None)
    if cure and status and (cure == "all" or status in cure):
        pokemon.cure_status()
        lines.append(f"{name} was cured of its {_status_word(status)}!")
        did = True
    heal = data.get("heal")
    if heal and pokemon.current_hp < mx:
        amount = mx - pokemon.current_hp if heal == "full" else min(int(heal), mx - pokemon.current_hp)
        pokemon.current_hp += amount
        lines.append(f"{name}'s HP was restored by {amount} points.")
        did = True
    if not did:
        if heal and not cure:
            return False, [f"{name}'s HP is already full!"]
        return False, [f"It won't have any effect on {name}."]
    return True, lines


def _status_word(status):
    return {"poison": "poison", "toxic": "poison", "paralysis": "paralysis", "sleep": "sleep",
            "burn": "burn", "freeze": "freeze"}.get(status, "condition")
