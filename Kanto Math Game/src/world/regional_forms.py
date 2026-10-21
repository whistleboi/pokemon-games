# [REF-0081: Regional forms everywhere]
"""
Regional forms (Alolan, Galarian, Hisuian, Paldean) live in their home region. Once the
player has caught every form from one region, those forms start turning up everywhere
else too: wherever the ordinary counterpart can be found, the regional form joins the
pool at about 1% (like Kanto and Johto's hand-placed 1% regional forms).

Hisuian forms are only found in Hisui (a Sinnoh sub-region, `"subregion": "HISUI"`) until then.
"""
FORM_REGIONS = {"alolan": "Alolan", "galarian": "Galarian", "hisuian": "Hisuian", "paldean": "Paldean"}
SPAWN_SHARE = 0.01
HISUI_ONLY_EVOLUTIONS = {899, 900, 901, 902}  # Wyrdeer, Kleavor, Ursaluna, Basculegion


def form_sets(game):
    """{form: {smart_id: base_id}} from FORM_MAP."""
    cache = getattr(game, "_form_sets", None)
    if cache is None:
        cache = {f: {} for f in FORM_REGIONS}
        for sid, m in game.loader.area_data.get("FORM_MAP", {}).items():
            if m.get("form") in cache and m.get("id"):
                cache[m["form"]][int(sid)] = int(m["id"])
        game._form_sets = cache
    return cache


def caught_ids(game):
    return {int(v["id"]) for v in game.data.data.get("pokedex", {}).values()
            if isinstance(v, dict) and str(v.get("id", "")).isdigit()}


def complete(game, form):
    forms = form_sets(game).get(form, {})
    return bool(forms) and set(forms) <= caught_ids(game)


def unlocked(game):
    flags = game.story_manager.story_flags
    return [f for f in FORM_REGIONS if flags.get(f"forms_complete_{f}")]


# Home region of each regional form (Hisui is reached from Sinnoh).
FORM_HOME = {"alolan": "ALOLA", "galarian": "GALAR", "hisuian": "SINNOH", "paldean": "PALDEA"}


# Kanto and Johto stay Gen 1-2 until the player has played later regions ("Kanto stays Kanto",
# "Johto stays Johto"), and so do the Orange Islands; the later regions keep their mixed pools.
CLASSIC_REGIONS = ("KANTO", "JOHTO", "ORANGE")


def _in_kanto(game):
    """True in Kanto, Johto or the Orange Islands (the regions that keep later regions' Pokemon out)."""
    return game.story_manager.get_current_region() in CLASSIC_REGIONS


def form_allowed(game, form):
    """Kanto and Johto only show another region's forms once the player has been there."""
    home = FORM_HOME.get(str(form).lower())
    if not home or not _in_kanto(game):
        return True
    return home in game.story_manager.visited_regions()


# Sub-regions that open a later region's Pokemon early (the Sevii Islands: Johto's, as in FireRed).
SUBREGION_OPENS = {"SEVII": {"JOHTO"}}


def species_allowed(game, pid):
    """In Kanto and Johto, a wild Pokemon from a later region (or another region's form) only
    shows up once the player has played that region. Other regions keep their mixed pools."""
    if not _in_kanto(game):
        return True
    pid = int(pid)
    opens = SUBREGION_OPENS.get(game.story_manager.get_current_area_data().get("subregion"), set())
    mapping = game.loader.area_data.get("FORM_MAP", {}).get(str(pid))
    if mapping:
        return form_allowed(game, mapping.get("form")) and species_allowed(game, mapping.get("id", pid))
    from src.pokemon import evolution
    return evolution.evolution_allowed(game, pid) or evolution.native_region(game, pid) in opens


def restrict(game, pool):
    """Drop Pokemon the player can't meet here yet (see species_allowed)."""
    if not pool or not _in_kanto(game):
        return pool
    out = {k: v for k, v in pool.items() if species_allowed(game, k)}
    return out or pool


def extend_pool(game, pool):
    """Add unlocked regional forms (about 1%) wherever their counterpart is in the pool,
    then keep Kanto free of Pokemon from regions not played yet."""
    forms = unlocked(game)
    if not pool or not forms:
        return restrict(game, pool)
    total = sum(pool.values()) or 1
    out = dict(pool)
    for form in forms:
        for sid, base in form_sets(game)[form].items():
            if str(base) in pool and str(sid) not in out:
                out[str(sid)] = max(total * SPAWN_SHARE, 0.5)
    return restrict(game, out)


def check_completion(game):
    """After a catch: unlock any region whose forms are now all caught. Returns message lines."""
    flags = game.story_manager.story_flags
    lines = []
    for form, label in FORM_REGIONS.items():
        if not flags.get(f"forms_complete_{form}") and complete(game, form):
            flags[f"forms_complete_{form}"] = True
            lines += [f"You've caught every {label} form!",
                      f"{label} Pokemon may now appear anywhere their usual forms live."]
    return lines


def in_hisui(game):
    return game.story_manager.get_current_area_data().get("subregion") == "HISUI"


def hisuian_entry(game, target_id):
    """'NAME_HISUIAN' if the target has a Hisuian form (evolving inside Hisui), else None."""
    for sid, base in form_sets(game)["hisuian"].items():
        if base == target_id:
            name = game.assets.pokemon_names.get(str(target_id), "").upper()
            return f"{name}_HISUIAN" if name else None
    return None
