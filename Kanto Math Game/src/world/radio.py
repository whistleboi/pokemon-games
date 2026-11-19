"""The Pokegear radio (HGSS; Jordan 11-15: "do the radio and give the cannon channels"). Needs the RADIO_CARD (Goldenrod
Radio Tower's quiz). Channels, as HGSS has them (our words):
  Pokemon Talk       Professor Oak and Mary name a Pokemon and where it lives
  Pokemon Music      Pokemon March (more wild Pokemon around you) or Pokemon Lullaby (fewer), by the day as in HGSS:
                     March on Sun/Tue/Thu/Sat, Lullaby on Mon/Wed/Fri; tuned in, it stays on till you change it
  Buena's Password   today's password, for Buena on the Radio Tower's 2F
  Variety Channel    a story or a song (flavour)
  Hoenn Sound /      after the National Pokedex: two Hoenn or Sinnoh Pokemon join an area's wild Pokemon while it plays
  Sinnoh Sound       (HGSS's own radio species for each place: the area's "radio_sounds", from the game file)
  Poke Flute         in Kanto: the Poke Flute's tune (it wakes a sleeping Pokemon in the games)
  ?????              in the Ruins of Alph: the Unown's strange signal
  Team Rocket        during the Radio Tower takeover: their broadcast
The lottery (Lucky Channel) is left out (Jordan 11-15). The tuned station: story_flags["radio_station"]."""
import datetime
import random

PASSWORDS = ["CYNDAQUIL", "TOTODILE", "CHIKORITA", "FRESH WATER", "LEMONADE", "SODA POP", "POTION", "ANTIDOTE", "PARLYZ HEAL",
             "SUPER POTION", "HYPER POTION", "FULL HEAL", "BICYCLE", "ULTRA BALL", "GREAT BALL", "POKE BALL", "ESCAPE ROPE", "REPEL"]
VARIETY = [["Variety Channel: ...and so the little Pidgey flew home at last, with the moon to light its way. The end!"],
           ["Variety Channel: Today's song is for everyone out on the road with their Pokemon. Keep walking, keep smiling!"],
           ["Variety Channel: A listener writes: 'My Marill and I splash in the river every morning.' How lovely!"]]


def has_radio(story):
    return story.inventory.get("RADIO_CARD", 0) > 0 and story.inventory.get("POKEGEAR", 0) > 0


def music_today():
    return "march" if datetime.date.today().weekday() in (6, 1, 3, 5) else "lullaby"


def password_today():
    return PASSWORDS[datetime.date.today().toordinal() % len(PASSWORDS)]


def channels(game):
    """[(key, name)] you can tune in to here, now."""
    story = game.story_manager
    region = str(story.get_current_region()).upper()
    area = story.current_area_key
    out = [("talk", "POKEMON TALK"), ("music", "POKEMON MUSIC"), ("buena", "BUENA'S PASSWORD"), ("variety", "VARIETY CHANNEL")]
    if story.story_flags.get("unlocked_national_dex"):
        out += [("hoenn", "HOENN SOUND"), ("sinnoh", "SINNOH SOUND")]
    if region == "KANTO":
        out.append(("flute", "POKE FLUTE"))
    if area == "RUINS_OF_ALPH":
        out.append(("unown", "?????"))
    if story.special_condition("radio_takeover"):
        out.append(("rocket", "TEAM ROCKET"))
    return out


def tune(game, key):
    """Tune in: the broadcast's lines; the station stays on (its effect) till you change it."""
    story = game.story_manager
    story.story_flags["radio_station"] = key
    if key == "talk":
        return _talk(game)
    if key == "music":
        m = music_today()
        story.story_flags["radio_station"] = m
        return (["Pokemon Music: Today it's the Pokemon March! A rousing tune... wild Pokemon come out to listen."] if m == "march" else
                ["Pokemon Music: Today it's the Pokemon Lullaby. Sweet and soft... wild Pokemon doze off and stay hidden."])
    if key == "buena":
        story.story_flags["buena_heard"] = datetime.date.today().isoformat()
        return ["Buena: Hiya, it's Buena's Password! Today's password is...", f"Buena: {password_today()}!",
                "Buena: Come and tell me at the Radio Tower in Goldenrod. See you there!"]
    if key == "variety":
        return list(random.choice(VARIETY))
    if key in ("hoenn", "sinnoh"):
        return [f"{'Hoenn' if key == 'hoenn' else 'Sinnoh'} Sound: a melody from far away... Pokemon from {'Hoenn' if key == 'hoenn' else 'Sinnoh'} may answer its call nearby!"]
    if key == "flute":
        return ["Poke Flute: A lilting tune plays... Even the soundest sleeper would wake up to this!"]
    if key == "unown":
        return ["...?????... ... ...", "A strange signal... It sounds like the Unown are calling out."]
    if key == "rocket":
        return ["...This is Team Rocket! Giovanni, if you can hear us... we're back! We've taken the Radio Tower!"]
    return ["Static..."]


def _talk(game):
    """Professor Oak's Pokemon Talk: a Pokemon of this region and a place it lives."""
    story = game.story_manager
    region = str(story.get_current_region()).upper()
    ad = game.loader.area_data
    places = []
    for key, a in ad.get("STORY_PROGRESSION", {}).items():
        if not isinstance(a, dict) or str(a.get("region", "")).upper() != region:
            continue
        pool = ad.get(a.get("wild_pool_percentages") or "", {}) or {}
        for sp in pool:
            if str(sp).isdigit() and int(sp) < 1000:
                places.append((int(sp), a.get("route_name") or key.replace("_", " ").title()))
    from src.world import swarms as _swarms   # (HGSS: Pokemon Talk tells of today's swarm, after the National Pokedex - 11-19)
    sw = _swarms.today(story, region)
    if sw:
        name = str((game.loader.fetch_specific(int(sw[1])) or {}).get("name", "a Pokemon")).replace("-", " ").title()
        how = {"surf": ", out on the water", "good_rod": ", on the end of a fishing line", "super_rod": ", deep in the water - bring a Super Rod"}.get(_swarms.kind_today(story, region), "")
        return ["Mary: It's Pokemon Talk with Professor Oak!",
                f"Prof. Oak: Big news! There's a swarm of {name} at {_swarms.place_name(sw[0])} today{how}!",
                "Mary: Hurry, everyone! See you next time!"]
    if not places:
        return ["Pokemon Talk: ...the signal's too weak here."]
    sp, where = random.choice(places)
    name = str((game.loader.fetch_specific(sp) or {}).get("name", "a Pokemon")).title()
    return ["Mary: It's Pokemon Talk with Professor Oak!", f"Prof. Oak: Today's Pokemon is {name}. You can find it on {where}!",
            "Mary: Thanks, Professor! See you next time!"]


def encounter_effect(story):
    """"more" (the March), "fewer" (the Lullaby), or None."""
    st = story.story_flags.get("radio_station")
    return "more" if st == "march" else "fewer" if st == "lullaby" else None


def sound_species(story, area_data):
    """Hoenn Sound / Sinnoh Sound: this area's radio Pokemon while it plays ([] otherwise)."""
    st = story.story_flags.get("radio_station")
    if st not in ("hoenn", "sinnoh"):
        return []
    return list((area_data.get("radio_sounds") or {}).get(st) or [])
