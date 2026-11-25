# Shadow forms do everything their species does (Jordan 11-24, kanto_handoff/questions/ORRE.md 14), their stats still
# swapped (Attack <-> Defense, Sp. Atk <-> Sp. Def): every stage of a Shadow line has a Shadow form (dev/builders/
# shadow_lines.py), Shadows breed (a Shadow mother's Egg hatches a Shadow baby with its heart shut), follow you in purple
# (dev/builders/shadow_overworld.py), Mega Evolve (forms.py, swapped stats, purple Mega sprite), learn TMs, keep abilities.
import os
from src.pokemon.data import Pokemon
from src.pokemon import forms, breeding, tms, abilities as ablib
from src.world import shadow as SH
from src.states.overworld.dungeon import follower_names
fails = []


def check(c, m):
    print(("ok   " if c else "FAIL ") + m)
    if not c:
        fails.append(m)


FM = g.loader.area_data.get("FORM_MAP", {})
SHADOW = {int(v["id"]): int(k) for k, v in FM.items() if v.get("form") == "shadow" and int(v["id"]) <= 386}
mk = lambda pid: Pokemon(g.loader.fetch_specific(pid), g.assets, size_mult=2.5)

print("1) Every stage of every Shadow line")
EVOS = g.loader.evolution_map if hasattr(g.loader, "evolution_map") else {}
roots = {int(ablib.species(g, b).get("egg") or b) for b in SHADOW}
check(roots <= set(SHADOW), f"each line's first stage has a Shadow form (an Egg's baby) - missing {sorted(roots - set(SHADOW))[:8]}")
s, n = mk(SHADOW[152]), mk(152)   # (Shadow Chikorita: a first stage made by shadow_lines.py)
b_, s_ = n.base_stats, s.base_stats
check(s.form == "shadow" and s_["ATTACK"] == b_["DEFENSE"] and s_["SPECIAL-ATTACK"] == b_["SPECIAL-DEFENSE"],
      f"a new first stage (Shadow Chikorita {SHADOW[152]}) has the reverse stats")
check(os.path.exists(f"assets/sprites/pokemon/{SHADOW[152]}.png"), "...and its purple battle sprite")

print("2) Breeding: a Shadow mother's Egg hatches a Shadow baby")
mom, dad = mk(SHADOW[296]), mk(297)   # (Shadow Makuhita, Hariyama)
mom.gender, dad.gender = "F", "M"
check(breeding.compatible(g, mom, dad)[0], "a Shadow and its species are compatible")
check(breeding.egg_species(g, mom, dad) == SHADOW[296], f"the Egg is a Shadow Makuhita ({breeding.egg_species(g, mom, dad)})")
mom2 = mk(SHADOW[248])   # (Shadow Tyranitar: the Egg is its line's first stage, Larvitar, Shadow)
mom2.gender = "F"
check(breeding.egg_species(g, mom2, mk(248)) == SHADOW[246], f"Shadow Tyranitar's Egg: Shadow Larvitar ({breeding.egg_species(g, mom2, mk(248))})")
baby = mk(SHADOW[296])
SH.make_shadow(g, baby)
check(SH.is_shadow(g, baby) and baby.shadow["gauge"] > 0 and not SH.is_open(baby), "a hatched Shadow has its heart shut (the hatch gives it a gauge)")

print("3) Following you: a purple sheet of its own")
missing = [d for d in SHADOW if not os.path.exists(f"assets/dungeon/followers/{d}_shadow.png")]
check(not missing, f"every Shadow species has a follower sheet ({len(SHADOW)}; missing {missing[:6]})")
check(follower_names(g, mk(SHADOW[248]))[0] == "248_shadow", f"a Shadow Tyranitar walks as 248_shadow ({follower_names(g, mk(SHADOW[248]))[:2]})")

print("4) Mega Evolution, the stats still swapped")
ty = mk(SHADOW[248])
inv = {"MEGA_RING": 1, "KEY_STONE": 1, "TYRANITARITE": 1}
f = forms.player_form(g.assets, ty, inv, False)
check(f is not None and f["form"] == "mega", f"a Shadow Tyranitar with a Key Stone and Tyranitarite can Mega Evolve ({f and f['name']})")
if f:
    forms.apply_form(g.assets, ty, f)
    st = ty.base_stats
    check(st["ATTACK"] == f["stats"]["DEFENSE"] and st["DEFENSE"] == f["stats"]["ATTACK"]
          and st["SPECIAL-ATTACK"] == f["stats"]["SPECIAL-DEFENSE"], f"Mega Shadow Tyranitar keeps the swap ({st})")
    check(ty.display_name.upper() == "MEGA SHADOW TYRANITAR", f"its name ({ty.display_name})")
    forms.revert_form(ty)
    check(ty.form == "shadow", "after battle it's a Shadow Tyranitar again")
art = [d for d in SHADOW for f_ in (forms.forms_for(g.assets, d) or []) if f_.get("form") != "primal"
       and os.path.exists(f"assets/sprites/pokemon/mega/{f_['sprite']}")   # (a Mega with art at all: the newest have none yet)
       and not os.path.exists(f"assets/sprites/pokemon/mega/{d}_shadow_{f_['form']}.png")]
check(not art, f"every Shadow line's Mega with art has a purple battle sprite (missing {art[:6]})")

print("5) TMs and abilities: as its species")
for d in (248, 296, 6):
    sh_, no = mk(SHADOW[d]), mk(d)
    sh_.ability_slot = no.ability_slot = 0   # (the same slot: a new Pokemon rolls one)
    tm = tms.key_for_move(g, "EARTHQUAKE") or tms.key_for_move(g, "TOXIC")
    check(tms.can_learn(g, sh_, tm) == tms.can_learn(g, no, tm), f"{sh_.display_name}: a TM as its species ({tm})")
    check(ablib.ability(g, sh_) == ablib.ability(g, no), f"{sh_.display_name}: its species' ability ({ablib.ability(g, sh_)})")

print(f"##### {len(fails)} failures")
