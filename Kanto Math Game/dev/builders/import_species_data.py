"""Abilities, genders and egg groups (Jordan, 11-03): from Pokemon Journeys' PBS files (Pokemon
Essentials v18: abilities.txt, pokemon.txt, pokemonforms.txt), with PokeAPI's CSV tables
(github.com/PokeAPI/pokeapi, data/v2/csv) for what Journeys doesn't have: species #891-1025, the
Galarian, Hisuian and Paldean forms, Megas and other forms, and the abilities after Gen 8.

Writes:
  assets/abilities.json     {KEY: {"name", "desc"}}            (KEY like LIGHTNINGROD, as Essentials)
  assets/move_flags.json    {"THUNDER-PUNCH": ["contact", "punch"], ...}  (for abilities: Static on
                            contact, Iron Fist, Strong Jaw...; Journeys' moves.txt, else PokeAPI, else
                            a physical move counts as contact)
  assets/species_data.json  {"25": {"abilities": [...], "hidden": KEY or null,
                                    "gender": female eighths 0-8 or -1 (genderless),
                                    "egg_groups": ["FIELD", "FAIRY"]}}   also keyed by our form ids

Run from the game folder:
    python dev/builders/import_species_data.py [<Journeys PBS folder>] [<PokeAPI CSV folder>]
"""
import csv
import json
import os
import re
import sys

PBS = sys.argv[1] if len(sys.argv) > 1 else os.path.join("..", "..", "Pokemon Journeys V18", "PBS")
CSV = sys.argv[2] if len(sys.argv) > 2 else os.path.join("dev", "builders", "out", "pokeapi_csv")
ENGLISH = 9

GENDER = {"AlwaysMale": 0, "FemaleOneEighth": 1, "Female25Percent": 2, "Female50Percent": 4,
          "Female75Percent": 6, "FemaleSevenEighths": 7, "AlwaysFemale": 8, "Genderless": -1}
# PokeAPI egg group -> Essentials' name
EGG = {"monster": "MONSTER", "water1": "WATER1", "bug": "BUG", "flying": "FLYING", "ground": "FIELD",
       "fairy": "FAIRY", "plant": "GRASS", "humanshape": "HUMANLIKE", "water3": "WATER3", "mineral": "MINERAL",
       "indeterminate": "AMORPHOUS", "water2": "WATER2", "ditto": "DITTO", "dragon": "DRAGON",
       "no-eggs": "UNDISCOVERED"}
# our FORM_MAP form -> PokeAPI's identifier suffix (the rest share it: "therian", "origin"...)
SUFFIX = {"alolan": "alola", "galarian": "galar", "hisuian": "hisui", "paldean": "paldea"}
OWN_REGION_FORMS = ("pinkan", "valencia", "shadow", "crystal", "black_fog", "normal")


def key(text):
    return re.sub(r"[^A-Z0-9]", "", str(text).upper())


def pbs_sections(path):
    """[header, {field: value}] of a PBS file in sections ([25], [RATTATA,1])."""
    out, cur = [], None
    for line in open(path, encoding="utf-8-sig"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("["):
            cur = {}
            out.append((line[1:-1], cur))
        elif cur is not None and "=" in line:
            k, v = line.split("=", 1)
            cur[k.strip()] = v.strip()
    return out


def rows(name):
    with open(os.path.join(CSV, name + ".csv"), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    # ---- abilities: Journeys' names and texts, PokeAPI's for the newer ones
    abilities = {}
    for line in open(os.path.join(PBS, "abilities.txt"), encoding="utf-8-sig"):
        m = re.match(r'(\d+),(\w+),([^,]+),"(.*)"', line.strip())
        if m:
            abilities[m.group(2)] = {"name": m.group(3), "desc": m.group(4)}
    api_name = {}
    for r in rows("ability_names"):
        if int(r["local_language_id"]) == ENGLISH:
            api_name[int(r["ability_id"])] = r["name"]
    api_text = {}
    for r in rows("ability_flavor_text"):  # the newest English text
        if int(r["language_id"]) == ENGLISH:
            prev = api_text.get(int(r["ability_id"]))
            if not prev or int(r["version_group_id"]) >= prev[0]:
                api_text[int(r["ability_id"])] = (int(r["version_group_id"]), " ".join(r["flavor_text"].split()))
    api_key = {}
    for r in rows("abilities"):
        aid = int(r["id"])
        if aid > 10000 or r["is_main_series"] != "1":
            continue
        k = key(api_name.get(aid, r["identifier"]))
        api_key[aid] = k
        if k not in abilities:
            abilities[k] = {"name": api_name.get(aid, r["identifier"].replace("-", " ").title()),
                            "desc": api_text.get(aid, (0, ""))[1]}

    # ---- PokeAPI: every Pokemon (species and forms)
    api_poke = {r["identifier"]: int(r["id"]) for r in rows("pokemon")}
    poke_species = {int(r["id"]): int(r["species_id"]) for r in rows("pokemon")}
    api_abil = {}
    for r in rows("pokemon_abilities"):
        pid, aid = int(r["pokemon_id"]), int(r["ability_id"])
        if aid not in api_key:
            continue
        entry = api_abil.setdefault(pid, {"abilities": [], "hidden": None})
        if r["is_hidden"] == "1":
            entry["hidden"] = api_key[aid]
        else:
            entry["abilities"].append(api_key[aid])
    species = {int(r["id"]): r for r in rows("pokemon_species")}
    egg_names = {int(r["id"]): r["identifier"] for r in rows("egg_groups")}
    api_eggs = {}
    for r in rows("pokemon_egg_groups"):
        api_eggs.setdefault(int(r["species_id"]), []).append(EGG[egg_names[int(r["egg_group_id"])]])

    def api_entry(pid, species_id):
        a = api_abil.get(pid) or api_abil.get(species_id) or {"abilities": [], "hidden": None}
        sp = species[species_id]
        return {"abilities": list(dict.fromkeys(a["abilities"])), "hidden": a["hidden"],
                "gender": int(sp["gender_rate"]), "egg_groups": api_eggs.get(species_id, ["UNDISCOVERED"])}

    # ---- Journeys: species #1-890 and its Alolan forms
    data = {}
    for head, f in pbs_sections(os.path.join(PBS, "pokemon.txt")):
        if not head.isdigit():
            continue
        sid = int(head)
        hidden = [h for h in f.get("HiddenAbility", "").split(",") if h]
        data[str(sid)] = {"abilities": [a for a in f.get("Abilities", "").split(",") if a],
                          "hidden": hidden[0] if hidden else None,
                          "gender": GENDER.get(f.get("GenderRate"), 4),
                          "egg_groups": [e.upper() for e in f.get("Compatibility", "Undiscovered").split(",") if e]}
    names = {r["identifier"]: int(r["id"]) for r in rows("pokemon_species")}
    by_name = {v["identifier"].upper().replace("-", ""): k for k, v in species.items()}
    pbs_forms = {}
    for head, f in pbs_sections(os.path.join(PBS, "pokemonforms.txt")):
        name, _, num = head.partition(",")
        pbs_forms[(name, int(num or 0))] = f
    for sid in range(1, 1026):  # Journeys' gaps (and anything past #890) from PokeAPI
        if str(sid) not in data:
            data[str(sid)] = api_entry(sid, sid)
        elif not data[str(sid)]["abilities"]:
            data[str(sid)]["abilities"] = api_entry(sid, sid)["abilities"]

    # ---- the species an egg hatches into: the bottom of the line (Raichu's eggs are Pichu), but not the
    # babies that need an incense in the games (Azurill, Wynaut, Munchlax...): those lines hatch the next one.
    INCENSE_BABIES = {298, 360, 406, 433, 438, 439, 440, 446, 458}
    parent = {sid: int(r["evolves_from_species_id"]) for sid, r in species.items() if r["evolves_from_species_id"]}
    for sid in range(1, 1026):
        root = sid
        while root in parent and parent[root] not in INCENSE_BABIES:
            root = parent[root]
        if root in INCENSE_BABIES and root != sid:
            root = next((c for c, p_ in parent.items() if p_ == root), root)
        data[str(sid)]["egg"] = root

    # ---- our forms (FORM_MAP ids): regional forms, Megas and the rest
    form_map = {}  # every region file's FORM_MAP (Orange's Pinkan forms, Alola's Zygarde...)
    for name in sorted(os.listdir("assets")):
        if name.endswith("_area_data.json"):
            form_map.update(json.load(open(os.path.join("assets", name), encoding="utf-8")).get("FORM_MAP", {}))
    for fid, m in form_map.items():
        base, form = int(m["id"]), str(m.get("form", "normal")).lower()
        base_key = str(base)
        if form in OWN_REGION_FORMS or base > 1025:
            data[fid] = dict(data.get(base_key) or {}, form_of=base)
            continue
        ident = species[base]["identifier"]
        suffix = SUFFIX.get(form, form.replace("_", "-"))
        # Paldean Tauros breeds, Zen Darmanitan...: the most specific match by the form's name
        extra = re.sub(r"[^a-z]+", "-", str(m.get("name", "")).lower()).strip("-")
        tries = [f"{ident}-{suffix}"]
        for word in ("aqua", "blaze", "combat", "zen", "x", "y"):
            if re.search(rf"\b{word}\b", extra):
                tries.insert(0, f"{ident}-{suffix}-{word}-breed" if form == "paldean" else f"{ident}-{suffix}-{word}")
                tries.insert(1, f"{ident}-{suffix}-{word}")
        pid = next((api_poke[t] for t in tries if t in api_poke), None)
        jour = None
        if form == "alolan":
            for (name, num), f in pbs_forms.items():
                if name == key(ident) and f.get("FormName", "").startswith("Alolan"):
                    jour = f
        if jour and jour.get("Abilities"):
            hidden = [h for h in jour.get("HiddenAbility", "").split(",") if h]
            entry = dict(data[base_key], abilities=jour["Abilities"].split(","), hidden=hidden[0] if hidden else None)
        elif pid:
            entry = dict(data[base_key], **{k: v for k, v in api_entry(pid, base).items()
                                             if k in ("abilities", "hidden")})
        else:
            entry = dict(data[base_key])
        entry["form_of"] = base
        data[fid] = entry

    missing = sorted({a for e in data.values() for a in e["abilities"] + [e["hidden"] or ""] if a and a not in abilities})
    json.dump(dict(sorted(abilities.items())), open(os.path.join("assets", "abilities.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    json.dump(data, open(os.path.join("assets", "species_data.json"), "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    print(f"{len(abilities)} abilities, {len(data)} species/forms; abilities without a text: {missing}")


# Pokemon Essentials v18's move flag letters (moves.txt), the ones the abilities use
FLAG_LETTERS = {"a": "contact", "i": "bite", "j": "punch", "k": "sound", "l": "powder", "m": "pulse",
                "n": "bomb", "o": "dance"}
API_FLAGS = {"contact": "contact", "punch": "punch", "sound": "sound", "bite": "bite", "pulse": "pulse",
             "ballistics": "bomb", "powder": "powder", "dance": "dance"}


def move_flags():
    ours = json.load(open(os.path.join("assets", "moves.json"), encoding="utf-8"))
    jour = {}
    for line in open(os.path.join(PBS, "moves.txt"), encoding="utf-8-sig"):
        parts = line.strip().split(",")
        if len(parts) > 12 and parts[0].isdigit():
            jour[parts[1]] = sorted({FLAG_LETTERS[c] for c in parts[12] if c in FLAG_LETTERS})
    api_id = {r["identifier"]: int(r["id"]) for r in rows("moves")}
    flag_name = {int(r["id"]): r["identifier"] for r in rows("move_flags")}
    api = {}
    for r in rows("move_flag_map"):
        f = API_FLAGS.get(flag_name[int(r["move_flag_id"])])
        if f:
            api.setdefault(int(r["move_id"]), set()).add(f)
    out, guessed = {}, 0
    for name, d in ours.items():
        k = key(name)
        if k in jour:
            flags = jour[k]
        elif api_id.get(name.lower()) in api:
            flags = sorted(api[api_id[name.lower()]])
        else:
            flags = ["contact"] if d.get("category") == "PHYSICAL" else []
            guessed += 1
        if flags:
            out[name] = flags
    json.dump(out, open(os.path.join("assets", "move_flags.json"), "w", encoding="utf-8"), separators=(",", ":"))
    print(f"move flags for {len(out)} moves ({guessed} guessed from the category)")


if __name__ == "__main__":
    main()
    move_flags()
