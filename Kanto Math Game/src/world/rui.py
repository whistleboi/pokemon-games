"""Rui walks with you through Orre (Jordan 11-20, Q4: as in Colosseum, from the sack in Phenac to the end). She doesn't
battle; she reads Shadow Pokemon's auras (shadow.aura_visible, the flag "aura_reader"). On every Orre map she walks a
step behind your Pokemon: the route and cave maps through DungeonState._companions, the towns through walk_town's own
trail (rui_from / rui). Story flags: "orre_rui_joined" (she's with you), "orre_rui_away" (a scene has her elsewhere)."""
SHEET = "orre_partner_rui.png"   # (Orre 2.1.1's Partner_Rui)
NAME = "Rui"
CHAT = ["Rui: I can see a dark glow around some Pokémon. Those are Shadow Pokémon. Let's save them all!",
        "Rui: Your Snag Machine can catch them. Then their hearts can open again.",
        "Rui: I'm right behind you. Lead the way!"]


def active(story):
    f = story.story_flags
    try:
        region = story.get_current_region()
    except Exception:
        region = None
    return region == "ORRE" and bool(f.get("orre_rui_joined") or f.get("got_snag_machine")) and not f.get("orre_rui_away")   # (older saves: past Phenac already)


def chat(story):
    """What she says when you talk to her (by the story so far)."""
    n = story.story_flags.get("_rui_chat", 0)
    story.story_flags["_rui_chat"] = n + 1
    return [CHAT[n % len(CHAT)]]
