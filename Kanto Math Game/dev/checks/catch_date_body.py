# A catch date on every Pokemon (11-25, for Unova's Hip Waders: "caught today"): src/pokemon/data.py caught_date /
# caught_today(), saved by story._pokemon_record; Pokemon from saves made before it have none.
#   bash dev/checks/run.sh catch_date
import datetime as _dt
from src.pokemon.data import Pokemon as _P
fails = []


def check(c, m):
    print(("   ok  " if c else "   FAIL ") + m)
    if not c:
        fails.append(m)


today = _dt.date.today().isoformat()
story = g.story_manager
print("1) a new Pokemon is today's")
p = _P(g.loader.fetch_specific(129), g.assets, size_mult=2.5)
check(p.caught_date == today and p.caught_today(), f"a new Magikarp: caught {p.caught_date}")
print("2) the save keeps it; an older save's Pokemon has none")
rec = story._pokemon_record(p)
check(rec.get("caught_date") == today, "saved with its date")
back = story._load_pokemon(dict(rec, caught_date="2026-01-02"), g.loader)
check(back.caught_date == "2026-01-02" and not back.caught_today(), "loaded: its own day, not today")
old = dict(rec); old.pop("caught_date")
back = story._load_pokemon(old, g.loader)
check(back.caught_date is None and not back.caught_today(), "an older save's Pokemon: no date, never 'caught today'")
print("3) it stays the same Pokemon's date through a change of species")
back.caught_date = "2026-03-04"
new = story.change_species(back, 130)
check(new.caught_date == "2026-03-04", "Magikarp to Gyarados keeps the day it was caught")
print(f"##### {len(fails)} failures")
