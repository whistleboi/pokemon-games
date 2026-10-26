# [REF-0080: Evolution rules]
"""
When a Pokemon evolves, from assets/pokemon_levels.json ("pairs", keyed "fromId>toId").
Rules come from the real games, with stand-ins where the real trigger can't happen here:

    level          reaches this level (Charmander -> Charmeleon at 16)
    item           use the item from the Bag (stones; trade items; Linking Cord for plain trades)
    time           only by day (6:00-20:00) or by night
    friendship     5 wild Pokemon caught while it's in the party (or use a Soothe Bell)
    move/move_type has learned that move (or a move of that type) by its level
    party_species/party_type   that Pokemon / a Pokemon of that type is also in the party
    weather        it's raining where you are
    beauty         Feebas: Beauty from Pokeblocks (contests)
    counter        battle feats: crits (they add up over battles), damage taken in a battle or in total,
                   attacks used, battles won, Bisharp defeated, catches made together
    money          you have at least this much money (Gimmighoul's coins)
    shed           Nincada: Shedinja also appears if there's room in the party

Rules with an item only happen from the Bag; everything else is checked after battles,
catches and Rare Candies.
"""
import datetime

FRIENDSHIP_CATCHES = 5
NINCADA, NINJASK, SHEDINJA = 290, 291, 292


def _data(game):
    return getattr(game.loader, "level_data", {}) or {}


def is_night(now=None):
    hour = (now or datetime.datetime.now()).hour
    return hour < 6 or hour >= 20


def base_id(poke):
    """Species id for rules and learnsets (regional forms use their base species)."""
    return int(getattr(poke, "meta_id", None) or poke.id) if int(poke.id) >= 2000 else int(poke.id)


def learnset(game, pid):
    return _data(game).get("learnsets", {}).get(str(pid), [])


def move_species(game, poke):
    """Whose learnset a Pokemon uses: its own form's (Crystal Onix) when it has one, else its species'."""
    sets = _data(game).get("learnsets", {})
    if str(poke.id) in sets and int(poke.id) >= 2000:
        return int(poke.id)
    form = getattr(poke, "form", "normal")
    if form and form != "normal":  # an evolved form keeps the base id (Onix + crystal): find the form's id
        for sid, m in game.loader.area_data.get("FORM_MAP", {}).items():
            if m.get("id") == base_id(poke) and m.get("form") == form and sid in sets:
                return int(sid)
    return base_id(poke)


def known_moves(game, poke, level=None):
    """Moves it has learned by level-up at its level (names as in the movesets, e.g. IRON-TAIL)."""
    lv = poke.level if level is None else level
    return {m for l, m in learnset(game, move_species(game, poke)) if max(1, l) <= lv}


def _move_types(game):
    cache = getattr(game, "_move_type_cache", None)
    if cache is None:
        cache = {}
        for data in game.assets.movesets.values():
            for m in data.get("moves", []):
                cache.setdefault(m.get("name", "").upper(), m.get("type"))
        game._move_type_cache = cache
    return cache


def default_level(game, pid):
    """The lowest level a species shows up at: its evolution level, or Lv 5."""
    return max(5, int(_data(game).get("min_level", {}).get(str(pid), 5)))


def suited_to_level(game, pid, level):
    """The species, or its earlier form, that can be found at this level: a hooked
    Dragonair below Dragonair's evolution level comes up as a Dratini."""
    pid = int(pid)
    pairs = _data(game).get("pairs", {})
    for _ in range(3):
        if pid >= 2000 or default_level(game, pid) <= level:
            break
        pre = next((int(k.split(">")[0]) for k in pairs if int(k.split(">")[1]) == pid), None)
        if pre is None:
            break
        pid = pre
    return pid


def _regional_only_targets(game):
    """Species ids that only a regional form evolves into (per the region data's evolution map)."""
    cache = getattr(game, "_regional_evo_cache", None)
    if cache is None:
        evo_map = game.loader.evolution_map
        by_form, by_plain = set(), set()
        for key, entries in evo_map.items():
            if not isinstance(entries, list) or key in ("ITEM_LOCKS",):
                continue
            bucket = by_form if "_" in key else by_plain
            for entry in entries:
                tid = game.name_to_id.get(entry.split("_")[0].upper())
                if tid:
                    bucket.add(tid)
        cache = game._regional_evo_cache = by_form - by_plain
    return cache


def native_region(game, pid):
    """The region whose Pokedex range (REGION_START dex_range, = PokeAPI generation) holds pid."""
    for region, cfg in game.loader.area_data.get("REGION_START", {}).items():
        lo, hi = cfg.get("dex_range", [0, -1])
        if lo <= int(pid) <= hi:
            return region.upper()
    return None


def _descendants(game, pid, seen=None):
    seen = set() if seen is None else seen
    for pair in _data(game).get("pairs", {}):
        a, b = pair.split(">")
        if int(a) == int(pid) and int(b) not in seen:
            seen.add(int(b))
            _descendants(game, int(b), seen)
    name = str(getattr(game.assets, "pokemon_names", {}).get(str(pid), "")).upper()
    for entry in game.loader.evolution_map.get(name, []) if name else []:
        tid = game.name_to_id.get(str(entry).split("_")[0].upper())
        if tid and tid not in seen:
            seen.add(tid)
            _descendants(game, tid, seen)
    return seen


def evolution_allowed(game, target_id):
    """Cross-generation gating: evolving INTO a species introduced in a later region (Crobat,
    Blissey, Porygon2, Magmortar...) needs that region visited, unless the species is older than
    a visited region (start in Sinnoh: Chansey -> Blissey is fine, Sinnoh's dex has it). If any species further down the
    line is native to a visited region, the steps leading to it are allowed too (start in Sinnoh:
    Porygon -> Porygon2 -> Porygon-Z)."""
    story = getattr(game, "story_manager", None)
    if story is None or not hasattr(story, "visited_regions"):
        return True
    visited = story.visited_regions()
    native = native_region(game, target_id)
    if native is None or native in visited:
        return True
    starts = game.loader.area_data.get("REGION_START", {})
    # A region's own listed exceptions (Hoenn's Gallade and Froslass...) are always fine there.
    if int(target_id) in starts.get(story.get_current_region(), {}).get("dex_extra", []):
        return True
    order = lambda r: starts.get(r, {}).get("order", 99)
    if any(order(native) < order(v) for v in visited):
        return True  # only LATER regions' evolutions are locked (Johto/Sinnoh already have Vaporeon)
    return any(native_region(game, d) in visited for d in _descendants(game, target_id))


# Evolutions that become the Alolan form when they happen in Alola (Raichu, Exeggutor, Marowak).
ALOLA_EVOLVES = {26, 103, 105}


def _form_item_rules(game):
    """{(source key, target entry): item} for item evolutions from or into a form in EVOLUTION_ITEMS
    (Galarian Slowpoke + Galarica Cuff; Onix + Crystal Stone -> Crystal Onix)."""
    cache = getattr(game, "_form_item_rules", None)
    if cache is None:
        cache = {}
        for item, pairs in game.loader.evolution_map.get("EVOLUTION_ITEMS", {}).items():
            for src_key, target in (pairs.items() if isinstance(pairs, dict) else pairs):
                if "_" in str(src_key) or "_" in str(target):
                    cache.setdefault((str(src_key).upper(), str(target).upper()), item)
        game._form_item_rules = cache
    return cache


def evolution_options(game, poke):
    """[(entry_name, target_id, rule)] for everything this Pokemon can evolve into."""
    evo_map = game.loader.evolution_map
    key = poke.name.upper()
    if poke.form and poke.form != "normal":
        key += f"_{poke.form.upper()}"
    entries = list(evo_map.get(key) or evo_map.get(key.title()) or [])
    src = base_id(poke)
    pairs = _data(game).get("pairs", {})
    names = getattr(game.assets, "pokemon_names", {})
    known_ids = set()
    for entry in entries:
        tid = game.name_to_id.get(entry.split("_")[0].upper())
        if tid:
            known_ids.add(tid)
    # Evolutions the real games have that the old evolution map was missing (but never the
    # ones only a regional form can reach, like Galarian Farfetch'd -> Sirfetch'd).
    from src.world import regional_forms
    hisui = regional_forms.in_hisui(game)
    if key == poke.name.upper():
        regional = _regional_only_targets(game)
        if hisui:
            regional = regional - regional_forms.HISUI_ONLY_EVOLUTIONS  # Wyrdeer, Kleavor... evolve in Hisui
        for pair in pairs:
            a, b = pair.split(">")
            if int(a) == src and int(b) not in known_ids and names.get(b) and int(b) not in regional:
                entries.append(names[b].upper())
                known_ids.add(int(b))
    out = []
    for entry in entries:
        tid = game.name_to_id.get(entry.split("_")[0].upper())
        if not tid:
            continue
        if not evolution_allowed(game, tid):
            continue  # a later region's evolution: not until the player has been there
        if src == NINCADA and tid == SHEDINJA:
            continue  # Shedinja is the extra Pokemon Nincada -> Ninjask leaves behind, never an evolution
        rule = pairs.get(f"{src}>{tid}") or {"level": default_level(game, tid)}
        if (key, entry) in _form_item_rules(game):
            # A regional form's own item evolution (Galarian Slowpoke: Galarica Cuff -> Slowbro,
            # Galarica Wreath -> Slowking), not the base species' rule (level 37 / King's Rock).
            rule = {"item": _form_item_rules(game)[(key, entry)]}
        if hisui and "_" not in entry:
            # Like Legends: Arceus, evolving in Hisui gives the Hisuian form when there is one.
            entry = regional_forms.hisuian_entry(game, tid) or entry
        elif tid in ALOLA_EVOLVES and key == poke.name.upper():
            # Sun/Moon: Pikachu, Exeggcute and Cubone evolve into the Alolan forms in Alola, and only
            # there (Alolan forms belong to Alola).
            in_alola = game.story_manager.get_current_region() == "ALOLA"
            if entry.endswith("_ALOLAN") and not in_alola:
                continue
            if in_alola and "_" not in entry:
                entry = f"{entry}_ALOLAN"
        if any(o[0] == entry for o in out):
            continue
        out.append((entry, tid, rule))
    return out


def rule_met(game, poke, rule, party=None, area_key=None):
    """True if every non-item condition of the rule holds right now."""
    if "item" in rule:
        return False
    story = game.story_manager
    party = party if party is not None else story.player_team
    if rule.get("level") and poke.level < rule["level"]:
        return False
    caught_at = getattr(poke, "caught_level", None)
    if rule.get("level") and caught_at is not None and poke.level <= caught_at:
        return False  # caught past its evolution level: it evolves at its next level up
    if rule.get("time") == "day" and is_night():
        return False
    if rule.get("time") == "night" and not is_night():
        return False
    if rule.get("friendship") and poke.friendship < FRIENDSHIP_CATCHES:
        return False
    if rule.get("move") and rule["move"] not in known_moves(game, poke):
        return False
    if rule.get("move_type"):
        types = _move_types(game)
        if not any(types.get(m) == rule["move_type"] for m in known_moves(game, poke)):
            return False
    others = [p for p in party if p is not poke]
    if rule.get("party_species"):
        want = game.name_to_id.get(rule["party_species"].upper())
        if not any(p.id == want for p in others):
            return False
    if rule.get("party_type") and not any(rule["party_type"] in (p.types or []) for p in others):
        return False
    if rule.get("weather"):
        from src.world import seasons
        if seasons.area_weather(game, area_key or story.current_area_key) != rule["weather"]:
            return False
    if rule.get("beauty"):
        from src.pokemon.contest import feebas_ready
        if not feebas_ready(poke):
            return False
    for counter, need in (rule.get("counter") or {}).items():
        if poke.counters.get(counter, 0) < need:
            return False
    if rule.get("money") and story.money < rule["money"]:
        return False
    if not any(k in rule for k in ("level", "friendship", "move", "move_type", "counter", "money", "beauty",
                                   "party_species", "party_type", "weather")):
        return False
    return True


def ready_evolutions(game, poke, party=None):
    """Entry names this Pokemon can evolve into right now (without items)."""
    if getattr(poke, "everstone", False):
        return []  # holding an Everstone: it stays as it is
    return [entry for entry, tid, rule in evolution_options(game, poke) if rule_met(game, poke, rule, party)]


def item_evolution(game, poke, item):
    """(entry, target_id) if using `item` on this Pokemon evolves it now, else None."""
    for entry, tid, rule in evolution_options(game, poke):
        if rule.get("item") != item:
            continue
        if rule.get("time") == "day" and is_night() or rule.get("time") == "night" and not is_night():
            continue
        return entry, tid
    return None


def condition_hint(rule):
    """A short line telling the player how a Pokemon evolves (for the summary page)."""
    if "item" in rule:
        text = f"use a {rule['item'].replace('_', ' ').title()}"
    elif rule.get("friendship"):
        text = f"catch {FRIENDSHIP_CATCHES} Pokemon with it in your party"
    elif rule.get("move"):
        text = f"level up knowing {rule['move'].replace('-', ' ').title()}"
    elif rule.get("move_type"):
        text = f"level up knowing a {rule['move_type'].title()} move"
    elif rule.get("counter"):
        (name, need), = rule["counter"].items()
        text = {"crits": f"land {need} critical hits in battle (they add up)",
                "damage_battle": f"win a battle after losing {need}+ HP",
                "damage_total": f"take {need} damage in total",
                "attacks": f"attack {need} times", "wins": f"win {need} battles",
                "bisharp": f"defeat {need} Bisharp", "catches": f"catch {need} Pokemon with it in your party"}[name]
    elif rule.get("money"):
        text = f"have ${rule['money']:,}"
    elif rule.get("beauty"):
        text = "raise its Beauty with Pokeblocks"
    elif rule.get("level"):
        text = f"reach Lv {rule['level']}"
    else:
        text = "?"
    if rule.get("level") and "item" not in rule and not text.startswith("reach"):
        text = f"reach Lv {rule['level']} and {text}"
    if rule.get("time"):  # real clock, so say when (Gliscor, Weavile, Umbreon...)
        text += {"night": " at night (8 PM-6 AM)", "day": " during the day (6 AM-8 PM)"}.get(
            rule["time"], f" ({rule['time']})")
    if rule.get("weather"):
        text += " while it's raining"
    if rule.get("party_species"):
        text += f" with {rule['party_species'].title()} in the party"
    if rule.get("party_type"):
        text += f" with a {rule['party_type'].title()}-type in the party"
    return text[0].upper() + text[1:]
