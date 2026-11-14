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
    # Lavaridge's Herb Shop (ORAS): cheaper than the Mart's, and very bitter
    "ENERGY_POWDER": {"heal": 50, "price": 500, "text": "A very bitter powder. Restores 50 HP."},
    "ENERGY_ROOT": {"heal": 200, "price": 1200, "text": "A very bitter root. Restores 200 HP."},
    "HEAL_POWDER": {"cure": "all", "price": 300, "text": "A very bitter powder. Cures any status condition."},
    "REVIVAL_HERB": {"revive": 1.0, "price": 2800, "text": "A very bitter herb. Revives a fainted Pokemon with all its HP."},
    "LAVA_COOKIE": {"cure": "all", "price": 200, "text": "Mt. Chimney's own treat, baked with volcanic ash. Cures any status condition."},
    "REVIVE": {"revive": 0.5, "price": 2000, "text": "Revives a fainted Pokemon with half its HP."},
    "MAX_REVIVE": {"revive": 1.0, "price": 4000, "text": "Revives a fainted Pokemon with all its HP."},
    "RARE_CANDY": {"price": 10000, "text": "Raises a Pokemon's level by one."},
    # Berries that heal (Hoenn's berry patches, Jordan 11-12): used from the Berries pocket, in or out of battle
    # (no price here: the shops' berry price stands)
    "ORAN_BERRY": {"heal": 10, "berry": True, "text": "A Berry. Restores 10 HP."},
    "SITRUS_BERRY": {"heal": 30, "berry": True, "text": "A Berry. Restores 30 HP."},
    "CHERI_BERRY": {"cure": ["paralysis"], "berry": True, "text": "A Berry. Cures paralysis."},
    "CHESTO_BERRY": {"cure": ["sleep"], "berry": True, "text": "A Berry. Wakes up a sleeping Pokemon."},
    "PECHA_BERRY": {"cure": ["poison", "toxic"], "berry": True, "text": "A Berry. Cures poison."},
    "RAWST_BERRY": {"cure": ["burn"], "berry": True, "text": "A Berry. Heals a burn."},
    "ASPEAR_BERRY": {"cure": ["freeze"], "berry": True, "text": "A Berry. Thaws out a frozen Pokemon."},
    "LUM_BERRY": {"cure": "all", "berry": True, "text": "A Berry. Cures any status condition."},
    # Route 113's Glass Workshop flutes (blown from volcanic ash; sold there): played again and again ("keep")
    "BLUE_FLUTE": {"cure": ["sleep"], "keep": True, "price": 100, "text": "A blue glass flute. Its tune wakes a sleeping Pokemon."},
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
    "YELLOW_FLUTE": {"cure_vol": "confused", "keep": True, "price": 300, "text": "A yellow glass flute. In battle, its tune snaps a Pokemon out of confusion."},
    "RED_FLUTE": {"cure_vol": "infatuated", "keep": True, "price": 200, "text": "A red glass flute. In battle, its tune snaps a Pokemon out of infatuation."},
}
FIELD = {
    "REPEL": {"repel": 2, "price": 400, "text": "Keeps wild Pokemon away: leave the next 2 routes without battling."},
    "SUPER_REPEL": {"repel": 4, "price": 700, "text": "Keeps wild Pokemon away for the next 4 routes."},
    "MAX_REPEL": {"repel": 5, "price": 900, "text": "Keeps wild Pokemon away for the next 5 routes."},
    "ESCAPE_ROPE": {"escape": True, "price": 1000, "text": "Leads out of a cave or building, to the last Pokemon Center."},
    # Route dungeons (src/states/overworld/dungeon.py): HONEY on the map draws three wild Pokemon to catch.
    "HONEY": {"attract": True, "price": 300, "text": "Sweet honey. Use it out on a route to draw in three wild Pokemon."},
    "BLACK_FLUTE": {"repel": 1, "keep": True, "price": 400, "text": "A black glass flute. Its tune keeps wild Pokemon away for the next route."},
    "WHITE_FLUTE": {"attract": True, "keep": True, "price": 500, "text": "A white glass flute. Play it out on a route to draw in three wild Pokemon."},
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


# Held items that power up one type's moves (Jordan, 11-06: Cherrygrove's fisherman's Mystic Water)
HELD_BOOSTS = {"MYSTIC_WATER": "WATER", "CHARCOAL": "FIRE", "SEA_INCENSE": "WATER", "NEVER_MELT_ICE": "ICE"}  # (Charcoal: Lavaridge's Herb Shop; Sea Incense: Mt. Pyre, 11-12)
FEWER_WILD = {"CLEANSE_TAG"}
DEFENCE_HELD = {"EVIOLITE"}  # (held by a Pokemon that can still evolve: its defences up by half. Route 123, 11-12)  # (held by your lead: fewer wild Pokemon on a map. Mt. Pyre's old woman, 11-12)
HELD_BOOST = 1.2
HELD = {"MYSTIC_WATER": {"price": 1000, "text": "Give it to a Pokemon to hold: its Water-type moves hit harder."},
        "CHARCOAL": {"price": 1000, "text": "Give it to a Pokemon to hold: its Fire-type moves hit harder."},
        "SEA_INCENSE": {"price": 1000, "text": "Give it to a Pokemon to hold: its Water-type moves hit harder."},
        "CLEANSE_TAG": {"price": 1000, "text": "Give it to your lead Pokemon to hold: fewer wild Pokemon come near."},
        "EVIOLITE": {"price": 3000, "text": "Give it to a Pokemon that can still evolve: it takes less damage."},
        "MENTAL_HERB": {"price": 1000, "text": "Held: used up to free its holder from love, Taunt, Encore and Disable."},
        "SHELL_BELL": {"price": 4000, "text": "Held: its holder gets back an eighth of the damage it deals."},
        "FOCUS_BAND": {"price": 3000, "text": "Held: now and then its holder hangs on at 1 HP instead of fainting."},
        "NEVER_MELT_ICE": {"price": 1000, "text": "Give it to a Pokemon to hold: its Ice-type moves hit harder."},
        "LEFTOVERS": {"price": 4000, "text": "Held: its holder gets back a little HP at the end of every turn."}}   # (the S.S. Tidal's hidden one, Emerald)


def held_boost(pokemon, move_type):
    """How much a held item powers up a move of this type (1.0: not at all)."""
    t = HELD_BOOSTS.get(getattr(pokemon, "held_item", None))
    return HELD_BOOST if t and t == str(move_type).upper() else 1.0


# Vitamins (the games, Gen 3 on: Lilycove's 3F): each adds 10 effort points to one stat, up to 100 from vitamins
# (and 510 in all). A stat gains a point for every 4 effort points at Lv 100 (data.Pokemon.stat_value).
VITAMIN_EV, VITAMIN_CAP, EV_TOTAL = 10, 100, 510
VITAMINS = {"HP_UP": {"stat": "HP", "price": 9800, "text": "Raises a Pokemon's HP a little, for good."},
            "PROTEIN": {"stat": "ATTACK", "price": 9800, "text": "Raises a Pokemon's Attack a little, for good."},
            "IRON": {"stat": "DEFENSE", "price": 9800, "text": "Raises a Pokemon's Defense a little, for good."},
            "CALCIUM": {"stat": "SPATK", "price": 9800, "text": "Raises a Pokemon's Sp. Atk a little, for good."},
            "ZINC": {"stat": "SPDEF", "price": 9800, "text": "Raises a Pokemon's Sp. Def a little, for good."},
            "CARBOS": {"stat": "SPEED", "price": 9800, "text": "Raises a Pokemon's Speed a little, for good."}}
# Valuables: only to sell (half their price), as in the games
VALUABLES = {"NUGGET": {"price": 10000, "text": "A nugget of pure gold. Sell it for a good price."},
             "BIG_PEARL": {"price": 7500, "text": "A big, shining pearl. Sell it for a good price."},
             "PEARL": {"price": 1400, "text": "A small, pretty pearl. Sell it for a little money."},
             "STARDUST": {"price": 2000, "text": "Lovely red sand. Sell it for a little money."},
             "STAR_PIECE": {"price": 9800, "text": "A shard of a pretty gem. Sell it for a good price."}}


def use_vitamin(pokemon, item):
    """(raised, line): add the vitamin's effort points to its stat, if it can take more."""
    stat = VITAMINS[item]["stat"]
    evs = pokemon.__dict__.setdefault("evs", {})
    have, total = evs.get(stat, 0), sum(evs.values())
    if have >= VITAMIN_CAP or total >= EV_TOTAL:
        return False, "It won't have any effect."
    gain = min(VITAMIN_EV, VITAMIN_CAP - have, EV_TOTAL - total)
    before = pokemon.get_max_hp()
    evs[stat] = have + gain
    if stat == "HP":
        pokemon.current_hp = min(pokemon.get_max_hp(), pokemon.current_hp + pokemon.get_max_hp() - before)
    label = {"HP": "HP", "ATTACK": "Attack", "DEFENSE": "Defense", "SPATK": "Sp. Atk", "SPDEF": "Sp. Def", "SPEED": "Speed"}[stat]
    return True, f"{pokemon.display_name}'s {label} rose!"


def info(item):
    return MEDICINE.get(item) or BATTLE.get(item) or FIELD.get(item) or HELD.get(item) or VITAMINS.get(item) or VALUABLES.get(item) or {}


def price(item):
    if item in BALL_PRICES:
        return BALL_PRICES[item]
    return info(item).get("price")


def describe(item):
    from src.pokemon import catching, tms
    from src.ui import theme
    if tms.is_tm(item) and theme.GAME is not None:  # what the TM teaches
        from src.pokemon import moves as movelib
        move = tms.move_of(theme.GAME, item) or ""
        d = movelib.info(theme.GAME, move)
        power = f", power {d['power']}" if d.get("power") else ""
        return (f"Teaches {move.replace('-', ' ').title()} ({str(d.get('type', '')).title()}{power}). "
                f"{d.get('effect') or ''} It can be used again and again.")
    if str(item).startswith("HM_"):
        return "A Hidden Machine: it opens the way wherever it's needed."
    from src.pokemon import zpower
    if item in zpower.ITEM_TEXT:
        return zpower.ITEM_TEXT[item]
    return info(item).get("text") or catching.BALL_TEXT.get(item, "")


def standard_stock(badges):
    """The Poke Mart counter for this many badges (in the region)."""
    out = []
    for need, items in STANDARD_MART + SPECIALTY_BALLS:
        if badges >= need:
            out += items
    return out


# Route trainers' prizes (Jordan, 11-06): healing items in place of Poke Balls, more and stronger as the
# region's story goes on (by its badges: Potions, then Super Potions and Revives, then Hyper Potions).
# Max Revives are never prizes: they're found lying on the walked maps, late on (dungeon.MAX_REVIVE_BADGES).
TRAINER_PRIZES = [(0, {"POTION": 2}), (2, {"POTION": 1, "SUPER_POTION": 1}),
                  (4, {"SUPER_POTION": 2, "REVIVE": 1}), (6, {"HYPER_POTION": 2, "REVIVE": 1})]


def trainer_prize(badges):
    return dict(next(prize for need, prize in reversed(TRAINER_PRIZES) if badges >= need))


def route_rewards(badges, rewards):
    """A route trainer's rewards: its own (a story item) without the Poke Balls, and the healing prize."""
    out = {k: v for k, v in (rewards or {}).items() if k != "balls"}
    for k, v in trainer_prize(badges).items():
        out[k] = out.get(k, 0) + v
    out["balls"] = 0  # (a battle gives 3 when it isn't said)
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
