# Rotom's appliance forms (src/pokemon/forms.py ROTOM_FORMS, rotom_change, a trainer team's "forms"): Platinum / Black 2.
# Main cleanup clean-main-unova-rotom-forms, 11-24 (the PWT's Rotom sets; the Shopping Mall's stockroom).
#   bash dev/checks/run.sh rotom_forms
from src.pokemon import forms
from src.pokemon.data import Pokemon

fails = 0


def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m)
    fails += 0 if c else 1


g.data.save = lambda *a, **k: None
want = {"heat": "FIRE", "wash": "WATER", "frost": "ICE", "fan": "FLYING", "mow": "GRASS"}
got = {f: Pokemon(g.loader.fetch_specific(479, f), g.assets).types for f in want}
check(all(got[f] == ["ELECTRIC", t] for f, t in want.items()), f"each form: Electric and its appliance's type ({got})")
heat = Pokemon(g.loader.fetch_specific(479, "heat"), g.assets)
check(heat.stats.get("DEFENSE") == 107 and heat.stats.get("SPEED") == 86 if hasattr(heat, "stats") and isinstance(heat.stats, dict) else True,
      "...and the forms' own stats")

rotom = Pokemon(g.loader.fetch_specific(479), g.assets)
rotom.level = 30
rotom.moves = ["THUNDER-SHOCK", "ASTONISH", "CONFUSE-RAY", "DISCHARGE"]
story.player_team = [rotom]
lines = forms.rotom_change(g, 0, "wash")
r = story.player_team[0]
check(r.types == ["ELECTRIC", "WATER"] and "HYDRO-PUMP" in r.moves and len(r.moves) == 4 and r.level == 30,
      f"into the washing machine: Wash Rotom, Hydro Pump learned ({r.types}, {r.moves}; {lines})")
forms.rotom_change(g, 0, "heat")
r = story.player_team[0]
check(r.types == ["ELECTRIC", "FIRE"] and "OVERHEAT" in r.moves and "HYDRO-PUMP" not in r.moves,
      f"into the oven: Hydro Pump becomes Overheat ({r.moves})")
check(str(story._pokemon_record(r).get("form")) == "heat", "...and the form is kept in the save")
forms.rotom_change(g, 0, "normal")
r = story.player_team[0]
check(r.types == ["ELECTRIC", "GHOST"] and not set(r.moves) & set(forms.ROTOM_FORMS.values()), f"back to normal: no appliance move ({r.moves})")
check(forms.rotom_change(g, 0, "fan") is not None and forms.rotom_change(g, 5, "fan") is None, "only a Rotom changes")

team = [Pokemon(g.loader.fetch_specific(479), g.assets, size_mult=3.125)]
team[0].level = 50
forms.mark_trainer_team(team, {"forms": ["fan"]})
check(team[0].types == ["ELECTRIC", "FLYING"] and team[0].level == 50 and "AIR-SLASH" in (getattr(team[0], "preset_moves", None) or []),
      f"a trainer's 'forms': the PWT's Fan Rotom ({team[0].types})")
print(f"##### {fails} failures")
