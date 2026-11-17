"""The rowdy Pikachu (Pokemon Yellow's partner; Jordan 11-16).

Prof. Oak gives it in his Kanto Lab once the player has beaten Lt. Surge (the Thunder Badge; Jordan 11-16: in time
for a first visit to Route 19's Summer Beach House; a Journal side mission sends you): Lv 5, perfect IVs,
Volt Tackle. It never evolves, it always walks behind the player while it is in the party, and it refuses the PC,
release, the Day Care and trades ("There isn't any response..."). Only the player's Mom will keep it: one locker
shared by every region (kept in story_flags, so it is the same at every region's Mom).
"""

SPECIAL = "rowdy_pikachu"
LOCKER = "mom_locker"          # story_flags key: [the saved record] while Mom has it
GIVEN = "got_rowdy_pikachu"    # story_flags key: Oak has given it
NO_RESPONSE = "There isn't any response..."
PIKACHU = 25
START_MOVES = ["VOLT-TACKLE", "THUNDER-SHOCK", "GROWL"]


def is_rowdy(p):
    return p is not None and getattr(p, "special", None) == SPECIAL


def in_party(story):
    return next((p for p in story.player_team if is_rowdy(p)), None)


def at_mom(story):
    return bool(story.story_flags.get(LOCKER))


def can_get(story):
    """Oak's gift: once Lt. Surge is beaten (the Thunder Badge), and not given yet."""
    return not story.story_flags.get(GIVEN) and story.has_badge("THUNDER")


def make(game):
    """A new rowdy Pikachu: Lv 5, all IVs 31, Volt Tackle."""
    from src.pokemon.data import Pokemon
    from src.pokemon import moves as mv
    mon = Pokemon(game.loader.fetch_specific(PIKACHU), game.assets, size_mult=2.5)
    mon.level, mon.xp = 5, 0
    mon.max_ivs()
    mon.special = SPECIAL
    mon.caught_region = "KANTO"
    mon.caught_level = 5
    known = list(START_MOVES)
    pool = mv.move_pool(game, mon)
    for m in known:
        if m not in pool:
            pool.append(m)
    mon.moves = known[:mv.MAX_MOVES]
    mon.current_hp = mon.get_max_hp()
    return mon


def give(game):
    """Oak hands it over: into the party, or to Mom when the party is full (it never goes in the PC)."""
    story = game.story_manager
    mon = make(game)
    story.story_flags[GIVEN] = True
    game.data.mark_seen(mon.id)
    game.data.add_pokemon(mon)
    if len([p for p in story.player_team if p]) < 6:
        story.player_team.append(mon)
        return "PIKACHU joined your team!"
    story.story_flags[LOCKER] = [story._pokemon_record(mon)]
    return "Your party is full, so PIKACHU was sent home to Mom."


def leave_with_mom(story):
    """Mom keeps it. Returns the message (refused if it is the only Pokemon you have with you)."""
    mon = in_party(story)
    if mon is None:
        return None
    if len([p for p in story.player_team if p and not getattr(p, "is_egg", False)]) <= 1:
        return "Mom: Oh, but then you'd have no Pokemon with you! Keep Pikachu close."
    mon.heal_full()
    story.story_flags[LOCKER] = [story._pokemon_record(mon)]
    story.player_team.remove(mon)
    return "Mom: I'll take good care of Pikachu. Come back for it any time, from anywhere!"


def take_from_mom(game):
    """Pikachu rejoins the party (needs a free slot). Returns the message."""
    story = game.story_manager
    recs = story.story_flags.get(LOCKER) or []
    if not recs:
        return None
    if len([p for p in story.player_team if p]) >= 6:
        return "Mom: Your party is full! Make some room first, then Pikachu can come along."
    mon = story._load_pokemon(recs[0], game.loader)
    mon.special = SPECIAL
    story.player_team.append(mon)
    story.story_flags.pop(LOCKER, None)
    return "Pikachu jumped back to your side! It looks thrilled."


def refuse(p):
    """True (and the reason) when this Pokemon can't be put in the PC, released, left at the Day Care or traded."""
    return NO_RESPONSE if is_rowdy(p) else None


def mood_lines(mon):
    """The Celadon Mansion old lady's reading of how much Pikachu likes you (Yellow; its friendship, 0-255)."""
    f = int(getattr(mon, "friendship", 0) or 0)
    if f >= 250:
        how = "Oh my! Your Pikachu adores you. It would follow you anywhere!"
    elif f >= 200:
        how = "Your Pikachu looks so happy. It really likes you!"
    elif f >= 130:
        how = "Your Pikachu seems to like you. Keep being kind to it!"
    elif f >= 70:
        how = "Hmm... your Pikachu is getting used to you. Give it time."
    else:
        how = "Oh dear. Your Pikachu doesn't trust you yet. Maybe it's still a bit rowdy?"
    return ["Old woman: Let me take a look at that Pikachu of yours...", how]
