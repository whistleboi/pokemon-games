"""Donuts (Jordan, 11-06): the way into Hyperspace Lumiose. Kept simple for kids: a donut is 3 berries.

- Plain berries (free from the Donut Shop's basket): Cheri spicy, Pecha sweet, Aspear sour, Chesto dry,
  Rawst bitter.
- Star berries (found only in Hyperspace, in the Bag): Pinap spicy, Watmel sweet, Belue sour, Nanab dry,
  Durin bitter. Each one adds a star.
- The donut's taste (the one most of its berries have) picks the zone; its stars say how deep you can go
  (each zone needs some: Verdant and Ember none, Tidal 1, Frost 2, Voltage 3).
- Recipes: three of one taste is a PERFECT donut (one more star); three different tastes a RAINBOW donut
  (30 more seconds on each floor's clock).

The donut you bake is kept (story flag "hyperspace_donut") until you go in with it."""

PLAIN = {"CHERI_BERRY": "SPICY", "PECHA_BERRY": "SWEET", "ASPEAR_BERRY": "SOUR", "CHESTO_BERRY": "DRY",
         "RAWST_BERRY": "BITTER"}
STAR = {"PINAP_BERRY": "SPICY", "WATMEL_BERRY": "SWEET", "BELUE_BERRY": "SOUR", "NANAB_BERRY": "DRY",
        "DURIN_BERRY": "BITTER"}
TASTES = ("SWEET", "SPICY", "SOUR", "DRY", "BITTER")
TASTE_COLOR = {"SWEET": (246, 140, 190), "SPICY": (236, 84, 60), "SOUR": (246, 214, 70), "DRY": (110, 150, 236),
               "BITTER": (110, 190, 90)}
FLAG = "hyperspace_donut"
RAINBOW_SECONDS = 30


def taste(berry):
    return PLAIN.get(berry) or STAR.get(berry)


def bake(berries, burnt=False):
    """The donut 3 berries make: {"taste", "stars", "recipe", "name", "bonus_seconds"}. burnt (a wrong
    answer while baking): it still works, without a recipe's bonus."""
    tastes = [taste(b) for b in berries]
    counts = {t: tastes.count(t) for t in tastes}
    main = max(counts, key=lambda t: (counts[t], -tastes.index(t)))  # most, then the first added
    stars = sum(1 for b in berries if b in STAR)
    recipe = "plain"
    if not burnt and len(counts) == 1:
        recipe, stars = "perfect", stars + 1
    elif not burnt and len(counts) == len(berries) == 3:
        recipe = "rainbow"
    stars = min(3, stars)
    word = main.title()
    name = {"perfect": f"Perfect {word} Donut", "rainbow": "Rainbow Donut"}.get(recipe, f"{word} Donut")
    if burnt:
        name = f"Toasty {word} Donut"
    return {"taste": main, "stars": stars, "recipe": recipe, "name": name,
            "bonus_seconds": RAINBOW_SECONDS if recipe == "rainbow" else 0, "berries": list(berries)}


def zone_for(game, donut):
    """The Hyperspace zone a donut opens: its taste's, if it has the stars that zone needs; else None."""
    prog = game.loader.area_data.get("STORY_PROGRESSION", {})
    for key, area in prog.items():
        hs = area.get("hyperspace") if isinstance(area, dict) else None
        if hs and hs.get("taste") == donut.get("taste"):
            return key if donut.get("stars", 0) >= hs.get("stars", 0) else None
    return None


def zones(game):
    """[(area key, area)] of the Hyperspace zones, easiest first."""
    prog = game.loader.area_data.get("STORY_PROGRESSION", {})
    out = [(k, a) for k, a in prog.items() if isinstance(a, dict) and a.get("hyperspace")]
    return sorted(out, key=lambda kv: (kv[1]["hyperspace"].get("stars", 0), kv[1].get("level", 0)))
