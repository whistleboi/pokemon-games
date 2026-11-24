"""The P*DA (Orre batch 8d; Jordan 11-21: "all four tabs"): in Orre the Journal is Wes's and Michael's P*DA - its own look
and four tabs: JOURNAL (the missions, as everywhere), MAIL (every e-mail so far), SNAG LIST (each Shadow Pokemon: where,
snagged, purified) and SPOT MONITOR (each Poke Spot's tray and visitor: src/world/poke_snacks.py).
The mail is read from story flags (MAIL below: each arrives when its flag is set), so nothing has to post it."""
import pygame

from src.ui import theme

ACCENT = (52, 120, 196)
TABS = [("journal", "JOURNAL"), ("mail", "MAIL"), ("snag", "SNAG LIST"), ("monitor", "MONITOR")]
# (flag, from, subject, body) in the order they come in the story
MAIL = [
    ("orre_kids_grid", "Megg", "You're in the Kids Grid!", "Megg here. Your P*DA number's in our address book now. We'll send anything we hear."),
    ("orre_part2", "Professor Krane", "Please come", "It's been five years, and I need your help. Please come to the Pokemon HQ Lab at once."),   # (the time skip, story rework S1)
    ("xd_krane_taken", "Lily", "The Professor...", "Cipher took Professor Krane! Come back to the lab as soon as you can."),
    ("xd_nett_rom", "Nett", "Poke Spots", "Duking found places in the desert where wild Pokemon gather. Try the Rock Poke Spot off the Desert Trail."),
    ("xd_spot_oasis", "Duking", "Snacks", "Leave Poke Snacks on a spot's tray and something will come to eat. Your P*DA's Spot Monitor will tell you."),
    ("xd_gorigan_beaten", "Professor Krane", "Thank you", "Cipher's lair is broken, thanks to you. Come by the lab - there is something I must show you."),
    ("xd_greevil_beaten", "Eagun", "Meet me", "{player_name}! Meet me outside the HQ Lab. Bring your best team."),
    ("xd_beluh_mail", "Beluh", "Please come", "Please come to Agate Village. Something is wrong with some of our Pokemon."),
    ("xd_le_vc5", "Megg", "My Shroomish!", "My Shroomish has gone completely quiet since someone gave it a translator. Can you help?"),
    ("col_post_nett", "Nett", "A tip", "A kid in Pyrite says Cail battled someone with a Shadow Pokemon. He hides behind a bookcase."),
    ("col_post_nett2", "Nett", "Gurks", "Gurks on the Junk Shop's balcony knows things about Shadow Pokemon. Ask him."),
    ("col_gonzap_post", "Gonzap", "Deep down", "That D-Disk goes in the floating platform in The Under. Tell me what's down there."),
]


def mail(game):
    flags = game.story_manager.story_flags
    from src.states.overworld.common import _fill_names   # (the player by their own name, Jordan 11-24)
    return [(frm, sub, _fill_names(game, body)) for f, frm, sub, body in MAIL if flags.get(f)]


def snag_list(game):
    """[(name, where, trainer, status)] for every Shadow Pokemon in Orre's lists."""
    ad = game.loader.area_data
    flags = game.story_manager.story_flags
    fm = ad.get("FORM_MAP", {})
    out = []
    for key, area in (ad.get("STORY_PROGRESSION") or {}).items():
        if not isinstance(area, dict) or str(area.get("region")).upper() != "ORRE":
            continue
        for e in area.get("shadow_pool") or []:
            base = (fm.get(str(e.get("id"))) or {}).get("id")
            status = ("PURIFIED" if flags.get(f"purified_line_{base}") else "SNAGGED") if flags.get(e.get("flag")) else "-"
            out.append((e.get("name", "?").replace("Shadow ", ""), area.get("route_name", key), e.get("trainer", ""), status))
    return out


def monitor(game):
    from src.world import poke_snacks
    t = poke_snacks.trays(game.story_manager)
    out = []
    for spot, name in poke_snacks.SPOTS.items():
        v = t[spot]["visitor"]
        state = "Quiet." if not v else f"{poke_snacks.beeps(v)} Something's eating!"
        out.append((name.replace("the ", "").title(), t[spot]["tray"], state))
    return out


def rows(game, tab):
    if tab == "mail":
        return [(f"{frm}: {sub}", body) for frm, sub, body in reversed(mail(game))] or [("No mail yet.", "")]
    if tab == "snag":
        lst = snag_list(game)
        done = sum(1 for r in lst if r[3] != "-")
        return [(f"Snagged {done} of {len(lst)}", "")] + [(f"{n}  -  {s if s != '-' else 'not snagged yet'}", f"{w}: {t}") for n, w, t, s in lst]
    if tab == "monitor":
        return [(f"{n}: {k} snack{'s' if k != 1 else ''} on the tray", st) for n, k, st in monitor(game)]
    return []


def draw(state, screen, rect, scroll):
    """A tab's rows in rect (two lines each), from scroll."""
    f = state.game.assets.fonts
    theme.draw_panel(screen, rect)
    rs = rows(state.game, state.tab)
    y = rect.y + 14
    shown = 0
    for title, body in rs[scroll:]:
        if y + 58 > rect.bottom - 8:
            break
        r = pygame.Rect(rect.x + 12, y, rect.w - 24, 54 if body else 34)
        theme.card(screen, r, accent=ACCENT, radius=10)
        theme.shadow_text(screen, title, f["label"], r.x + 14, r.y + 4)
        if body:
            from src.ui.slot_list import fit
            theme.shadow_text(screen, fit(f["caption"], body, r.w - 28), f["caption"], r.x + 14, r.y + 30, color=(70, 80, 100))
        y = r.bottom + 6
        shown += 1
    return len(rs), shown
