"""The Odd Egg (Jordan, 11-16): Route 34's Day-Care Man gives an Odd Egg seven times, a different baby each time. The next one is
ready one calendar day after the last one hatched; a Journal side mission ("The Odd Egg") starts by itself on that day.

Story flags: odd_eggs_given (list of species given), odd_egg_pending (an Odd Egg not hatched yet), odd_egg_hatched_day
(ISO date of the last hatch), odd_egg_ready (refreshed by refresh(): the mission's condition)."""
import datetime
import random

# HGSS's Odd Egg babies, with Happiny instead of Tyrogue (Karate King Kiyo already gives a Tyrogue) so Blissey is in Johto's run.
SPECIES = [172, 173, 174, 238, 239, 240, 440]   # Pichu, Cleffa, Igglybuff, Smoochum, Elekid, Magby, Happiny
COUNT = len(SPECIES)


def today():
    return datetime.date.today().isoformat()


def refresh(story):
    """Set odd_egg_ready: an egg is waiting (none given yet, or the last one hatched before today)."""
    f = story.story_flags
    given = list(f.get("odd_eggs_given") or [])
    ready = (len(given) < COUNT and not f.get("odd_egg_pending")
             and (not given or (f.get("odd_egg_hatched_day") and f.get("odd_egg_hatched_day") != today())))
    if ready:
        f["odd_egg_ready"] = True
    else:
        f.pop("odd_egg_ready", None)
    return ready


def next_species(story):
    given = set(story.story_flags.get("odd_eggs_given") or [])
    left = [s for s in SPECIES if s not in given]
    return random.choice(left) if left else None


def talk(game, lines):
    """The Day-Care Man. Returns the species to give as an Egg now, or None (lines say why)."""
    story = game.story_manager
    f = story.story_flags
    given = list(f.get("odd_eggs_given") or [])
    if len(given) >= COUNT:
        lines += ["Day-Care Man: That was the last of the odd Eggs. Every one of them hatched into something special!"]
        return None
    if f.get("odd_egg_pending"):
        lines += ["Day-Care Man: Is that odd Egg still with you? Keep it close and it'll hatch soon enough."]
        return None
    if not refresh(story):
        lines += ["Day-Care Man: Nothing new yet. Come back tomorrow - another odd Egg might turn up."]
        return None
    if len([p for p in story.player_team if p]) >= 6:
        lines += ["Day-Care Man: I found an odd Egg, but your party's full. Make some room and come back."]
        return None
    sp = next_species(story)
    lines += (["Day-Care Man: Oh, it's you! We found an Egg here and nobody knows whose it is.", "Will you take care of it?"]
              if not given else ["Day-Care Man: Another odd Egg turned up! I'd like you to have this one too."])
    f["odd_eggs_given"] = given + [sp]
    f["odd_egg_pending"] = True
    f.pop("odd_egg_ready", None)
    return sp


def hatched(story, species_id):
    """An Egg hatched: if it was the Odd Egg, start the wait for the next one."""
    f = story.story_flags
    if f.get("odd_egg_pending") and int(species_id) in SPECIES and int(species_id) in (f.get("odd_eggs_given") or []):
        f.pop("odd_egg_pending", None)
        f["odd_egg_hatched_day"] = today()
        refresh(story)
