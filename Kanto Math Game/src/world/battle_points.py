"""Battle Points (BP): won in battle facilities, spent at their Exchange Service Corners (Jordan 11-22: "add battle points ...
implement them for all walkable regions"; the facilities' own special rules are NOT built).

Earning (our streaks are shorter than the games', 5 / 10 wins, so a win pays as the games' sets do over seven):
  - each win in a Battle Frontier streak (Hoenn's seven + the Battle Maison, Johto's five): WIN_BP
  - beating a Frontier Brain: BRAIN_BP (Silver) / BRAIN_GOLD_BP (Gold), as the games' bonus for a Brain
  - each win on the Battle Subway (Black 2 / White 2): WIN_BP
Spending: SHOPS, each region's own counter, item for item and price for price from its game (Bulbapedia, 11-22):
  Emerald's Exchange Service Corner, HeartGold / SoulSilver's two stalls in the Frontier's plaza, Black 2 / White 2's Gear
  Station counters. Decorations, dolls and the items whose battle effect isn't built (Red Card, Eject Button, Binding Band,
  Absorb Bulb, Cell Battery; Air Balloon, retired here) are left out. TMs by their move (one TM list in every region).
Kept as a story flag, like the Game Corner's coins."""
BP_FLAG = "battle_points"
MAX_BP = 9999
WIN_BP = 1
BRAIN_BP, BRAIN_GOLD_BP = 10, 20

VITAMINS = [("PROTEIN", 1), ("CALCIUM", 1), ("IRON", 1), ("ZINC", 1), ("CARBOS", 1), ("HP_UP", 1)]
POWERS = [("POWER_BRACER", 16), ("POWER_BELT", 16), ("POWER_LENS", 16), ("POWER_BAND", 16), ("POWER_ANKLET", 16), ("POWER_WEIGHT", 16)]

# counter -> (its name, [(item key or "TM:<MOVE>", BP)])
SHOPS = {
    "emerald": ("Exchange Service Corner", VITAMINS + [
        ("LEFTOVERS", 48), ("WHITE_HERB", 48), ("QUICK_CLAW", 48), ("MENTAL_HERB", 48),
        ("BRIGHT_POWDER", 64), ("CHOICE_BAND", 64), ("KINGS_ROCK", 64), ("FOCUS_BAND", 64), ("SCOPE_LENS", 64),
        ("RAZOR_CLAW", 48)]),   # (11-23, Jordan: the Razor Claw for Weavile, at ORAS's Battle Maison price; the Maison lives in Hoenn's Frontier)
    "hgss_items": ("Exchange Service Corner", VITAMINS + [("RARE_CANDY", 48)] + POWERS + [
        ("TOXIC_ORB", 16), ("FLAME_ORB", 16), ("WHITE_HERB", 32), ("POWER_HERB", 32),
        ("BRIGHT_POWDER", 48), ("FOCUS_BAND", 48), ("FOCUS_SASH", 48), ("CHOICE_BAND", 48), ("CHOICE_SCARF", 48),
        ("SCOPE_LENS", 48), ("MUSCLE_BAND", 48), ("RAZOR_CLAW", 48), ("RAZOR_FANG", 48)]),
    "hgss_tms": ("Exchange Service Corner (TMs)", [
        ("TM:AERIAL-ACE", 40), ("TM:BRICK-BREAK", 40), ("TM:U-TURN", 40), ("TM:X-SCISSOR", 64), ("TM:STONE-EDGE", 80),
        ("TM:EARTHQUAKE", 80), ("TM:SHADOW-BALL", 64), ("TM:ENERGY-BALL", 64), ("TM:SLUDGE-BOMB", 80), ("TM:DRAGON-PULSE", 80),
        ("TM:TOXIC", 32), ("TM:THUNDER-WAVE", 32), ("TM:WILL-O-WISP", 32), ("TM:ATTRACT", 32), ("TM:BULK-UP", 48),
        ("TM:CALM-MIND", 48)]),
    # Platinum's corners: HGSS's lists without the U-turn TM (Bulbapedia's Gen IV Battle Frontier, read 11-22)
    "plat_items": ("Exchange Service Corner", None),
    "plat_tms": ("Exchange Service Corner (TMs)", None),
    "b2w2_items": ("Exchange Service Corner", VITAMINS + [
        ("FIRE_STONE", 3), ("THUNDER_STONE", 3), ("WATER_STONE", 3), ("LEAF_STONE", 3),
        ("SCOPE_LENS", 8), ("WIDE_LENS", 8), ("MUSCLE_BAND", 8), ("WISE_GLASSES", 8), ("RAZOR_CLAW", 8), ("RAZOR_FANG", 8),
        ("BRIGHT_POWDER", 12), ("FOCUS_BAND", 12), ("ZOOM_LENS", 12), ("IRON_BALL", 12)] + POWERS + [
        ("TOXIC_ORB", 16), ("FLAME_ORB", 16), ("WHITE_HERB", 16), ("POWER_HERB", 16),
        ("CHOICE_BAND", 24), ("CHOICE_SPECS", 24), ("CHOICE_SCARF", 24), ("FOCUS_SASH", 24), ("LIFE_ORB", 24), ("RARE_CANDY", 24)]),
    # Orre's Battle Tower (S6c, 11-24): the fan game's tutor teaches any move for BP; here he sells the TMs (rule: tutors
    # sell TMs), Gen 3's strong ones; its item counter is Emerald's ("emerald")
    "orre_tms": ("Move Tutor's TMs", [
        ("TM:TOXIC", 32), ("TM:PROTECT", 32), ("TM:REST", 32), ("TM:RETURN", 32), ("TM:AERIAL-ACE", 40), ("TM:BRICK-BREAK", 40),
        ("TM:CALM-MIND", 48), ("TM:BULK-UP", 48), ("TM:DRAGON-CLAW", 48), ("TM:SHADOW-BALL", 64), ("TM:ICE-BEAM", 64),
        ("TM:THUNDERBOLT", 64), ("TM:FLAMETHROWER", 64), ("TM:PSYCHIC", 64), ("TM:EARTHQUAKE", 80)]),
    "b2w2_tms": ("Exchange Service Corner (TMs)", [
        ("TM:PROTECT", 6), ("TM:SAFEGUARD", 6), ("TM:DOUBLE-TEAM", 6), ("TM:INCINERATE", 6), ("TM:BRICK-BREAK", 12),
        ("TM:FROST-BREATH", 12), ("TM:U-TURN", 12), ("TM:HIDDEN-POWER", 18), ("TM:SMACK-DOWN", 18), ("TM:ROUND", 18),
        ("TM:SWORDS-DANCE", 18), ("TM:SWAGGER", 18), ("TM:PLUCK", 18), ("TM:SLUDGE-WAVE", 24), ("TM:ALLY-SWITCH", 24),
        ("TM:QUASH", 24), ("TM:EXPLOSION", 24), ("TM:PSYCH-UP", 24)]),
}


def bp(story):
    return int(story.story_flags.get(BP_FLAG, 0) or 0)


def add_bp(story, n):
    """Win (or spend, n < 0) Battle Points. Returns how many were added."""
    before = bp(story)
    story.story_flags[BP_FLAG] = max(0, min(MAX_BP, before + int(n)))
    return bp(story) - before


def stock(game, shop):
    """[(item key, BP)] of a counter, its TMs turned into our TM keys (a TM we don't have is left out)."""
    from src.pokemon import tms
    out = []
    for what, cost in SHOPS[shop][1]:
        if what.startswith("TM:"):
            what = tms.key_for_move(game, what[3:])
            if not what:
                continue
        out.append((what, cost))
    return out


def buy(game, item, cost):
    """Spend BP on one item. Returns a line to show."""
    from src.pokemon import tms
    story = game.story_manager
    name = tms.label(game, item) if tms.is_tm(item) else str(item).replace("_", " ").title()
    if tms.is_tm(item) and story.inventory.get(item, 0) > 0:
        return f"You already have {name}."
    if bp(story) < cost:
        return f"You need {cost} BP for {name}. You have {bp(story)}."
    if not story.add_item(item, 1):
        return f"Your Bag can't hold any more {name}."
    add_bp(story, -cost)
    return f"You got {name} for {cost} BP! You have {bp(story)} BP left."


SHOPS["plat_items"] = ("Exchange Service Corner", list(SHOPS["hgss_items"][1]))
SHOPS["plat_tms"] = ("Exchange Service Corner (TMs)", [t for t in SHOPS["hgss_tms"][1] if t[0] != "TM:U-TURN"])
