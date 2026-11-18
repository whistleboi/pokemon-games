"""Following-Pokemon sheets for the game's other forms (Jordan, 11-17: every form gets its own overworld sprite),
copied from art already in ~/Downloads, Essentials-named (NAME_<form number>.png, shiny in their own folder):
  * Pokemon Everlasting X / Devastating Y (Beta v1.5, kalos/...): Graphics/Characters/Followers and Followers shiny
    (the set import_followers.py took the species from): Deoxys, Rotom, Giratina, Shaymin, the Therians, Kyurem,
    Keldeo, Meloetta, Genesect, Zygarde 10%, Vivillon, Necrozma, Lycanroc, Zacian, Zamazenta, Urshifu, Calyrex,
    Darmanitan's Zen Mode and Unown's letters;
  * the ZA Megas pack (import_follower_packs.py left Mega Raichu X and Y out): RAICHU_3 / RAICHU_4.
-> assets/dungeon/followers/<dex>_<form>.png and shiny/, the form named as the game's FORM_MAP names it
(386_attack, 479_heat, 201_b...), the name DungeonState._follower_img tries first. Form numbers are Essentials'
(PBS/pokemon_forms.txt).

    python -I dev/builders/import_essentials_form_followers.py [<Downloads folder>]
"""
import os
import shutil
import sys

SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/Downloads")
EVERLASTING = os.path.join(SRC, "kalos", "(Beta v1.5) Pokemon Everlasting X Devastating Y",
                           "(Beta v1.5) Pokemon Everlasting X Devastating Y", "Graphics", "Characters")
ZA_MEGAS = os.path.join(SRC, "ZA Megas-20261107T054444Z-1-001", "ZA Megas")
OUT = os.path.join("assets", "dungeon", "followers")

# Essentials file stem -> our <dex>_<form>
FORMS = {
    "DEOXYS_1": "386_attack", "DEOXYS_2": "386_defense", "DEOXYS_3": "386_speed",
    "ROTOM_1": "479_heat", "ROTOM_2": "479_wash", "ROTOM_3": "479_frost", "ROTOM_4": "479_fan", "ROTOM_5": "479_mow",
    "GIRATINA_1": "487_origin", "SHAYMIN_1": "492_sky",
    "DARMANITAN_1": "555_zen",
    "TORNADUS_1": "641_therian", "THUNDURUS_1": "642_therian", "LANDORUS_1": "645_therian",
    "KYUREM_1": "646_white", "KYUREM_2": "646_black",
    "KELDEO_1": "647_resolute", "MELOETTA_1": "648_pirouette", "GENESECT_2": "649_burn",
    "VIVILLON_18": "666_fancy", "VIVILLON_19": "666_poke_ball",
    "ZYGARDE_1": "718_ten_percent",
    "LYCANROC_2": "745_dusk",
    "NECROZMA_1": "800_dusk_mane", "NECROZMA_2": "800_dawn_wings",
    "ZACIAN_1": "888_crowned", "ZAMAZENTA_1": "889_crowned",
    "URSHIFU_1": "892_rapid",
    "CALYREX_1": "898_ice_rider", "CALYREX_2": "898_shadow_rider",
}
# Unown: 1-25 = B-Z, then Everlasting X's 26 = ! and 27 = ? (the other way round from Essentials' PBS; checked by eye)
for _n in range(1, 26):
    FORMS[f"UNOWN_{_n}"] = f"201_{chr(ord('a') + _n)}"
FORMS["UNOWN_26"], FORMS["UNOWN_27"] = "201_exclamation", "201_question"
MEGAS = {"RAICHU_3": "26_mega_x", "RAICHU_4": "26_mega_y"}


def copy_set(folders, table):
    done, missing = 0, []
    for folder, sub in folders:
        for stem, dst in table.items():
            src = os.path.join(folder, stem + ".png")
            if not os.path.isfile(src):
                missing.append(f"{sub or 'normal'}/{stem}")
                continue
            out = os.path.join(OUT, sub, dst + ".png")
            os.makedirs(os.path.dirname(out), exist_ok=True)
            shutil.copyfile(src, out)
            done += 1
    return done, missing


def main():
    a, miss_a = copy_set([(os.path.join(EVERLASTING, "Followers"), ""),
                          (os.path.join(EVERLASTING, "Followers shiny"), "shiny")], FORMS)
    b, miss_b = copy_set([(ZA_MEGAS, ""), (os.path.join(ZA_MEGAS, "Shiny"), "shiny")], MEGAS)
    print(a + b, "sheets; not in the sources:", miss_a + miss_b)


if __name__ == "__main__":
    main()
