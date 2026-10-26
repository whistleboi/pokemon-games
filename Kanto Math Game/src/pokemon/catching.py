# [REF-0082: Poke Balls and catching]
"""Catching works like the games (Jordan): the Gen 8/9 formula, real ball bonuses, status and the
low-level bonus, four shake checks and critical captures.

  a = (3*maxHP - 2*HP) * catch_rate * ball / (3*maxHP) * status * low_level
  caught at once if a >= 255; else each shake check passes with b = 65536 / (255/a)^(3/16)
  (four checks; the ball wobbles once per check passed, up to three times). A critical capture
  (more likely the more species you've caught) needs only one check.

Poke Balls are the story's one count (story.balls_left, 'POKE_BALLS'); every other ball is an
item in the Bag. The player picks which ball to throw (story.selected_ball)."""
import datetime
import math
import random

POKE = "POKE_BALLS"
# Ball -> (label, flat bonus). Balls with a condition are worked out in ball_bonus().
BALLS = {
    POKE: ("POKE BALL", 1.0), "GREAT_BALL": ("GREAT BALL", 1.5), "ULTRA_BALL": ("ULTRA BALL", 2.0),
    "MASTER_BALL": ("MASTER BALL", 255.0), "PREMIER_BALL": ("PREMIER BALL", 1.0),
    "LUXURY_BALL": ("LUXURY BALL", 1.0), "HEAL_BALL": ("HEAL BALL", 1.0), "CHERISH_BALL": ("CHERISH BALL", 1.0),
    "FRIEND_BALL": ("FRIEND BALL", 1.0), "LOVE_BALL": ("LOVE BALL", 1.0), "HEAVY_BALL": ("HEAVY BALL", 1.0),
    "NET_BALL": ("NET BALL", 1.0), "DIVE_BALL": ("DIVE BALL", 1.0), "NEST_BALL": ("NEST BALL", 1.0),
    "REPEAT_BALL": ("REPEAT BALL", 1.0), "TIMER_BALL": ("TIMER BALL", 1.0), "QUICK_BALL": ("QUICK BALL", 1.0),
    "DUSK_BALL": ("DUSK BALL", 1.0), "LEVEL_BALL": ("LEVEL BALL", 1.0), "LURE_BALL": ("LURE BALL", 1.0),
    "MOON_BALL": ("MOON BALL", 1.0), "FAST_BALL": ("FAST BALL", 1.0), "DREAM_BALL": ("DREAM BALL", 1.0),
    "BEAST_BALL": ("BEAST BALL", 1.0), "SAFARI_BALL": ("SAFARI BALL", 1.5), "SPORT_BALL": ("SPORT BALL", 1.5),
}
# What each ball does (the Bag and the Mart show it).
BALL_TEXT = {
    POKE: "A ball for catching wild Pokemon.", "GREAT_BALL": "Better than a Poke Ball (x1.5).",
    "ULTRA_BALL": "Better than a Great Ball (x2).", "MASTER_BALL": "Catches any wild Pokemon for sure.",
    "PREMIER_BALL": "A rare ball made to celebrate an event.", "LUXURY_BALL": "Pokemon caught in it grow friendly fast.",
    "HEAL_BALL": "Heals the Pokemon it catches.", "NET_BALL": "Great for Water and Bug types (x3.5).",
    "DIVE_BALL": "Great on the water and underwater (x3.5).", "NEST_BALL": "Better the lower the Pokemon's level.",
    "REPEAT_BALL": "Great for species you've caught before (x3.5).",
    "TIMER_BALL": "Gets better the longer the battle goes (up to x4).",
    "QUICK_BALL": "Great on the first turn of a battle (x5).", "DUSK_BALL": "Great at night and in caves (x3).",
    "LEVEL_BALL": "Better when your Pokemon is a higher level.", "LURE_BALL": "Great for fished-up Pokemon (x4).",
    "MOON_BALL": "Great for Pokemon that evolve with a Moon Stone (x4).", "FAST_BALL": "Great for fast Pokemon (x4).",
    "DREAM_BALL": "Great for sleeping Pokemon (x4).", "FRIEND_BALL": "Pokemon caught in it are friendly at once.",
    "BEAST_BALL": "Made for Ultra Beasts (x5); poor for others.",
    "SAFARI_BALL": "A ball used in the Safari Zone (x1.5).", "SPORT_BALL": "A ball for the Bug-Catching Contest (x1.5).",
    "LOVE_BALL": "A ball Kurt makes from a Pink Apricorn.", "HEAVY_BALL": "A ball Kurt makes from a Black Apricorn.",
    "CHERISH_BALL": "A rare ball for special Pokemon.",
}
MOON_STONE_LINES = {29, 30, 32, 33, 35, 39, 300, 517}  # Nidoran lines, Clefairy, Jigglypuff, Skitty, Munna
ULTRA_BEASTS = {793, 794, 795, 796, 797, 798, 799, 803, 804, 805, 806}
STATUS_BONUS = {"sleep": 2.5, "freeze": 2.5, "paralysis": 1.5, "poison": 1.5, "toxic": 1.5, "burn": 1.5}


def owned(story, ball):
    if ball == POKE:
        return max(0, int(getattr(story, "balls_left", 0)))
    return max(0, int(story.inventory.get(ball, 0)))


def total_balls(story):
    """Every ball you can throw (Poke Balls and the rest)."""
    return sum(owned(story, b) for b in BALLS)


def balls_owned(story):
    return [b for b in BALLS if owned(story, b) > 0]


def selected(story):
    """The ball you'll throw: the one you picked, while you still have it, else the first you own."""
    pick = getattr(story, "selected_ball", None) or POKE
    if owned(story, pick) > 0:
        return pick
    have = balls_owned(story)
    return have[0] if have else POKE


def cycle(story):
    """Pick the next ball you own (the BALL button)."""
    have = balls_owned(story)
    if not have:
        return POKE
    cur = selected(story)
    story.selected_ball = have[(have.index(cur) + 1) % len(have)] if cur in have else have[0]
    return story.selected_ball


def use(story, ball):
    if ball == POKE:
        story.balls_left = max(0, story.balls_left - 1)
    else:
        story.inventory[ball] = max(0, story.inventory.get(ball, 0) - 1)
        if story.inventory[ball] <= 0:
            story.inventory.pop(ball, None)


def label(ball):
    return BALLS.get(ball, (ball.replace("_", " "), 1.0))[0]


def ball_bonus(ball, game, target, turn=1, fishing=False, terrain=""):
    """The ball's multiplier for this throw (Gen 8/9 values)."""
    bonus = BALLS.get(ball, (None, 1.0))[1]
    types = set(getattr(target, "types", None) or [])
    level = int(getattr(target, "level", 5) or 5)
    story = game.story_manager
    if ball == "NET_BALL" and types & {"WATER", "BUG"}:
        return 3.5
    if ball == "DIVE_BALL" and terrain in ("ocean", "water", "surf", "underwater", "dive"):
        return 3.5
    if ball == "NEST_BALL":
        return max(1.0, (41 - level) / 10)
    if ball == "REPEAT_BALL" and _caught_before(game, target.id):
        return 3.5
    if ball == "TIMER_BALL":
        return min(4.0, 1 + turn * 1229 / 4096)
    if ball == "QUICK_BALL" and turn <= 1:
        return 5.0
    if ball == "DUSK_BALL" and (terrain in ("cave", "dungeon") or not 6 <= datetime.datetime.now().hour < 20):
        return 3.0
    if ball == "LEVEL_BALL":
        mine = max((int(p.level) for p in story.player_team if p), default=1)
        return 8.0 if mine >= 4 * level else 4.0 if mine >= 2 * level else 2.0 if mine > level else 1.0
    if ball == "LURE_BALL" and fishing:
        return 4.0
    if ball == "MOON_BALL" and target.id in MOON_STONE_LINES:
        return 4.0
    if ball == "FAST_BALL":
        speed = (game.assets.movesets.get(str(target.id), {}).get("stats") or {}).get("SPEED", 0)
        return 4.0 if speed >= 100 else 1.0
    if ball == "DREAM_BALL" and getattr(target, "status", None) == "sleep":
        return 4.0
    if ball == "BEAST_BALL":
        return 5.0 if target.id in ULTRA_BEASTS else 0.1
    return bonus


def _caught_before(game, pid):
    return any(isinstance(v, dict) and v.get("id") == pid for v in game.data.data.get("pokedex", {}).values())


def catch_rate(game, target):
    """The species' catch rate (forms such as Shadow or Pinkan Pokemon use their species')."""
    from src.pokemon.evolution import base_id
    sets = game.assets.movesets
    rate = (sets.get(str(target.id)) or {}).get("capture_rate")
    if rate is None:
        rate = (sets.get(str(base_id(target))) or {}).get("capture_rate", 45)
    return max(1, int(rate))


def crit_multiplier(game):
    """Critical captures get likelier the more species you've caught (Gen 8)."""
    caught = len({v.get("id") for v in game.data.data.get("pokedex", {}).values() if isinstance(v, dict)})
    return 2.5 if caught > 600 else 2.0 if caught > 450 else 1.5 if caught > 300 else 1.0 if caught > 150 \
        else 0.5 if caught > 30 else 0.0


def throw(game, target, ball, hp=None, max_hp=None, turn=1, fishing=False, terrain="", bonus=1.0):
    """One throw. Returns (caught, shakes 0-3, critical). hp/max_hp: how weak the target is (a
    knocked-out Pokemon counts as 1 HP); bonus: extra multiplier (a quick right answer)."""
    if ball == "MASTER_BALL":
        return True, 3, False
    max_hp = max(1, int(max_hp or target.get_max_hp()))
    hp = max(1, min(max_hp, int(hp if hp is not None else target.current_hp)))
    level = int(getattr(target, "level", 5) or 5)
    a = ((3 * max_hp - 2 * hp) * catch_rate(game, target) * ball_bonus(ball, game, target, turn, fishing, terrain)
         / (3 * max_hp))
    a *= STATUS_BONUS.get(getattr(target, "status", None), 1.0)
    if level < 13:  # the games' low-level bonus (Gen 8)
        a *= (36 - 2 * level) / 10
    a *= bonus
    if a >= 255:
        return True, 3, False
    a = max(1.0, a)
    b = 65536 / math.pow(255 / a, 0.1875)
    crit_chance = min(1.0, a * crit_multiplier(game) / 6 / 256)
    if random.random() < crit_chance:  # critical capture: one check
        ok = random.randrange(65536) < b
        return ok, 1, True
    shakes = 0
    for _ in range(4):
        if random.randrange(65536) >= b:
            return False, min(shakes, 3), False
        shakes += 1
    return True, 3, False


def window_throw(game, target, ball, guaranteed=False, **kw):
    """A throw at the catch window (after the battle, or a route's right answer), Jordan's rules:
    legendaries, mythicals and bosses are a sure catch (like SwSh's Dynamax Adventures), and
    everything else keeps the ball's odds with half the chance to break free."""
    if guaranteed:
        return True, 3, False
    result = throw(game, target, ball, **kw)
    if not result[0] and random.random() < 0.5:  # half the fails become catches
        return True, 3, False
    return result


def chance(game, target, ball, hp=None, max_hp=None, turn=1, fishing=False, terrain="", bonus=1.0):
    """Roughly how likely this throw is to work (0-1), for tests and hints."""
    if ball == "MASTER_BALL":
        return 1.0
    max_hp = max(1, int(max_hp or target.get_max_hp()))
    hp = max(1, min(max_hp, int(hp if hp is not None else target.current_hp)))
    level = int(getattr(target, "level", 5) or 5)
    a = ((3 * max_hp - 2 * hp) * catch_rate(game, target) * ball_bonus(ball, game, target, turn, fishing, terrain)
         / (3 * max_hp)) * STATUS_BONUS.get(getattr(target, "status", None), 1.0) * bonus
    if level < 13:
        a *= (36 - 2 * level) / 10
    if a >= 255:
        return 1.0
    b = 65536 / math.pow(255 / max(1.0, a), 0.1875)
    return (b / 65536) ** 4


def after_catch(game, pokemon, ball):
    """What the ball does to the Pokemon it caught: a Heal Ball heals it, a Friend Ball makes it
    friendly at once, a Luxury Ball starts it a little friendlier (it also grows friendlier faster
    in the games)."""
    if not pokemon or not ball:
        return
    pokemon.caught_ball = ball
    if ball == "HEAL_BALL":
        pokemon.current_hp = pokemon.get_max_hp()
        if getattr(pokemon, "status", None):
            pokemon.cure_status()
    if ball == "FRIEND_BALL":
        pokemon.friendship = max(getattr(pokemon, "friendship", 0), 200)
    if ball == "LUXURY_BALL":
        pokemon.friendship = getattr(pokemon, "friendship", 0) + 50
