# Johto's events PLAYED on their maps (J3, 11-23; AUDIT_GUIDE 8, as kanto_events): walk up to whoever it is, talk (walk into
# them), tap through what's said, pick what a player would, fight the battles; then look at what you got. The data side is
# checked in johto_canon (which already plays the Apricorns, Kurt, the phone, Primo, the radio, the Contest, the Frontier, the
# Safari Zone, the Odd Egg, the tutors and the Dragon Shrine's Dratini); this plays the rest.
#   bash dev/checks/run.sh -v johto_events
_src = open("dev/checks/kanto_events_body.py", encoding="utf-8").read()
exec(_src[:_src.index("_flags0, _inv0, _team0, _money0 = ")])
import datetime as _dt

story.starting_region = "JOHTO"
g.player_character = "ethan"
BADGES8 = ["ZEPHYR", "HIVE", "PLAIN", "FOG", "STORMBADGE", "MINERAL", "GLACIER", "RISING"]
_real_date = _dt.date


def on_day(name):
    """Make the game's clock read this weekday ("mon" ... "sun"): the Week Siblings, Friday's Lapras."""
    days = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    base = _real_date(2026, 11, 23)   # (a Monday)

    class _Day(_real_date):
        @classmethod
        def today(cls):
            return base + _dt.timedelta(days=days.index(name))
    _dt.date = _Day


def johto(badges=8, flags=(), items=()):
    """A Johto save part-way: badges, flags, key items."""
    story.badges["JOHTO"] = BADGES8[:badges]
    for f in flags:
        story.story_flags[f] = True
    for i in items:
        story.inventory[i] = story.inventory.get(i, 0) + 1


def fight_trainer(st, name, n=8000):
    """Walk into a route's trainer called name (on whichever floor he stands) and fight it out."""
    said.clear()
    hit = lambda fl: next((m for m in fl.movers if m.kind == "trainer" and isinstance(m.payload, tuple) and (m.payload[1] or {}).get("name") == name), None)
    if hit(st.run.floor) is None:
        for i in range(st.run.n_floors):
            if hit(st.run.made(i)) is not None:
                st.run.enter_floor(i); frames(2)
                break
    f = st.run.floor
    f.movers = [m for m in f.movers if m.kind != "wild"]
    m = hit(f)
    if m is None:
        return None
    for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        b = (m.x + dx, m.y + dy)
        if f.walkable(*b) and f.mover_at(*b) is None and b not in f.exits:
            st.run.player = b; st.anim = 0
            st.step(-dx, -dy)
            break
    else:
        return None
    play((), n)
    return list(said)


def won(flag):
    return bool(story.story_flags.get(flag))


story.balls_left = 20
story.story_flags.update({"received_starter_johto": True, "starter_johto": 155})

print("1) In-game trades: walk up with the Pokemon they want, get theirs with its nickname and held item (HGSS)")
for area, came, who, want, give, nick, item, flag in (
        ("VIOLET_CITY", "JOHTO_ROUTE_31", "Kyle", 69, 95, "Rocky", "PERSIM_BERRY", "violet_onix_trade"),
        ("GOLDENROD_CITY", "JOHTO_ROUTE_34", "Trader", None, None, None, None, "goldenrod_machop_trade"),
        ("OLIVINE_CITY", "JOHTO_ROUTE_39", "Trader", None, None, None, None, "olivine_krabby_trade"),
        ("BLACKTHORN_CITY", "JOHTO_ROUTE_45", "Trader", None, None, None, None, "blackthorn_dodrio_trade")):
    opt = next(o for o in g.loader.area_data["STORY_PROGRESSION"][area]["explore_options"]
               if o.get("text") == who and (o.get("event") or {}).get("trade"))
    tr = opt["event"]["trade"]
    want, give, nick, item = tr["want"], tr["give"], tr.get("nickname"), tr.get("item")
    story.story_flags.pop(flag, None)
    johto()
    team(want, level=20)
    t = town(area, came)
    w = meet(t, who, picks=[True, True, True])
    got = next((p for p in story.player_team if p.id == give), None)
    check(w is not None and got is not None and won(flag) and (not nick or nick in str(getattr(got, "nickname", "") or getattr(got, "name", "")))
          and (not item or getattr(got, "held_item", None) == item),
          f"{area}: {who} takes #{want}, gives #{give} {nick!r} holding {item} (got {got and (got.id, getattr(got, 'nickname', None), getattr(got, 'held_item', None))}; {w and w[:1]})")

print("2) Kenya: the Goldenrod gate guard's Spearow carries a letter to the sleepy man on Route 31; HP Up back (HGSS)")
for f in ("got_kenya", "kenya_delivered", "got_hp_up_kenya_guard"):
    story.story_flags.pop(f, None)
johto(badges=2)
team(158, level=20)
story.inventory.pop("HP_UP", None)
t = town("GOLDENROD_CITY", "JOHTO_ROUTE_35")
meet(t, "Gate guard", picks=[True, True])
check(won("got_kenya") and any(p.id == 21 for p in story.player_team), f"the guard lends you Kenya (Spearow) {[p.id for p in story.player_team]}")
r = route("JOHTO_ROUTE_31", "VIOLET_CITY")
w = meet(r, "Sleepy man")
check(won("kenya_delivered") and story.inventory.get("TM085", 0) >= 1, f"Route 31's sleepy man reads the letter: TM Rest ({w and w[:1]})")
t = town("GOLDENROD_CITY", "JOHTO_ROUTE_35")
meet(t, "Gate guard", picks=[True, True])
check(won("got_hp_up_kenya_guard") and story.inventory.get("HP_UP", 0) >= 1, "back at the gate: an HP Up")

print("3) Kirk's Shuckie (Cianwood): a Shuckle holding Berry Juice")
story.story_flags.pop("got_shuckie", None)
johto(badges=4)
team(158, level=30)
t = town("CIANWOOD_CITY", "JOHTO_ROUTE_41")
meet(t, "Kirk", picks=[True, True])
sh = next((p for p in story.player_team if p.id == 213), None)
check(won("got_shuckie") and sh is not None and getattr(sh, "held_item", None) == "BERRY_JUICE", f"Shuckie joins, holding Berry Juice ({sh and sh.held_item})")

print("4) The Week Siblings: each on their own day, an item once (HGSS; no ribbons, agreed 11-15)")
for day, area, came, who in (("mon", "JOHTO_ROUTE_40", "OLIVINE_CITY", "Monica"), ("tue", "JOHTO_ROUTE_29", "NEW_BARK_TOWN", "Tuscany"),
                             ("wed", "LAKE_OF_RAGE", "JOHTO_ROUTE_43", "Wesley"), ("thu", "JOHTO_ROUTE_36", "VIOLET_CITY", "Arthur"),
                             ("fri", "JOHTO_ROUTE_32", "VIOLET_CITY", "Frieda"), ("sat", "BLACKTHORN_CITY", "JOHTO_ROUTE_45", "Santos"),
                             ("sun", "JOHTO_ROUTE_37", "ECRUTEAK_CITY", "Sunny")):
    johto(badges=8)
    other = "tue" if day != "tue" else "wed"
    on_day(other)
    st = place(area, came)
    absent = meet(st, who) is None
    on_day(day)
    inv0 = dict(story.inventory)
    st = place(area, came)
    w = meet(st, who, picks=[True])
    gained = {k: v - inv0.get(k, 0) for k, v in story.inventory.items() if v > inv0.get(k, 0)}
    inv1 = dict(story.inventory)
    meet(place(area, came), who, picks=[True])
    again = {k: v - inv1.get(k, 0) for k, v in story.inventory.items() if v > inv1.get(k, 0)}
    check(absent and w is not None and gained and not again, f"{who} ({day}): not there on other days; an item ({gained}), once ({again or 'nothing more'})")
_dt.date = _real_date

print("5) Mr. Pokemon trades vitamins for the Red Scale (ours: the Exp. Share retired, 11-16)")
johto(badges=7, flags=("defeated_red_gyarados",), items=("RED_SCALE",))
story.story_flags.pop("traded_red_scale", None)
r = place("MR_POKEMONS_HOUSE", "JOHTO_ROUTE_30")
w = meet(r, "Show the Red Scale", picks=[True])
check(won("traded_red_scale") and not story.inventory.get("RED_SCALE") and story.inventory.get("CARBOS", 0) >= 1, f"the scale for six vitamins ({w and w[:1]})")

print("6) Mt. Mortar's Karate King: beat him, a Tyrogue (HGSS)")
johto(badges=6)
ace()
r = route("MT_MORTAR", "JOHTO_ROUTE_42")
w = fight_trainer(r, "Karate King Kiyo")
check(any(p.id == 236 for p in story.player_team) or any(p.id == 236 for p in (story.pc_boxes[0] if getattr(story, "pc_boxes", None) else [])),
      f"Kiyo beaten: a Tyrogue joins ({[p.id for p in story.player_team]}; {w and w[-1:]})")

print("7) The legends, met where they wait (agreed: Ho-Oh / Lugia Lv 60, their wings and bell)")
for area, came, who, flags_, items_, day, flag in (
        ("UNION_CAVE", "JOHTO_ROUTE_33", "CHALLENGE LAPRAS", (), (), "fri", None),
        ("ILEX_FOREST", "AZALEA_TOWN", "CHALLENGE CELEBI", ("kurt_examined_gs_ball",), ("GS_BALL",), None, None),
        ("BELL_TOWER", "BELLCHIME_TRAIL", "CHALLENGE HO-OH", ("got_rainbow_wing",), ("RAINBOW_WING",), None, None),
        ("WHIRL_ISLANDS", "JOHTO_ROUTE_41", "CHALLENGE LUGIA", ("got_silver_wing", "got_tidal_bell"), ("SILVER_WING", "TIDAL_BELL"), None, None),
        ("MT_SILVER", "MT_SILVER_CITY", "SEEK MOLTRES", ("beat_johto_champion",), (), None, "mt_silver_moltres_defeated"),
        ("BURNED_TOWER", "ECRUTEAK_CITY", "ENCOUNTER SUICUNE", ("johto_beasts_fled",), (), None, None)):
    johto(badges=8, flags=flags_, items=items_)
    if day:
        on_day(day)
    ace()
    story.story_flags.pop(f"{area}_boss_defeated", None)
    if flag:
        story.story_flags.pop(flag, None)
    r = route(area, came)
    f0 = set(k for k, v in story.story_flags.items() if v)
    w = meet(r, who, n=8000)
    caught = [k for k, v in story.story_flags.items() if v and k.startswith("caught_") and k not in f0]
    done = won(f"{area}_boss_defeated") or (flag and won(flag)) or bool(caught)
    check(w is not None and done, f"{area}: walk up to it ({who}) and battle it ({'beaten or caught ' + str(caught) if done else 'not won'}; {w and w[:1]})")
    _dt.date = _real_date

print("8) Elm's aide's Egg (a story step since 11-23): Violet's Center, after the Zephyr Badge")
story.story_flags.pop("got_togepi_egg", None)
johto(badges=1, flags=("elm_received_egg",))
team(158, level=12)
t = town("VIOLET_CITY", "JOHTO_ROUTE_31")
meet(t, "Elm's aide", picks=[True])
check(won("got_togepi_egg") and any(getattr(p, "is_egg", False) or p.id == 175 for p in story.player_team), f"the Egg joins your party ({[p.id for p in story.player_team]})")

print("9) The Name Rater (Goldenrod): pick a Pokemon you caught, type a name, it's renamed")
johto(badges=3)
story.story_flags.pop("beat_johto_champion", None)   # (after the title the town asks "where next?" first)
team(158, level=20)
t = town("GOLDENROD_CITY", "JOHTO_ROUTE_34")
said.clear()
_spot = None
for room in (t.town_map.get("rooms") or {}):
    t._go(room, ""); frames(2)
    _spot = next((sp for sp, o in t._people().items() if o.get("text") == "Name Rater"), None)
    if _spot:
        break
for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
    b = (_spot[0] + dx, _spot[1] + dy) if _spot else None
    if b and t._open(b) and b not in t.exits:
        t.player = t.anim_from = b; t.anim = 0; t.step(-dx, -dy)
        break
for _ in range(300):   # (his words, then the party list)
    st = g.current_state
    if type(st).__name__ == "PokemonPartyMenuState":
        break
    if getattr(st, "npc_active", False):
        st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
    st.update(); st.draw()
menu = g.current_state
check(type(menu).__name__ == "PokemonPartyMenuState", f"his words, then the party list ({type(menu).__name__})")
if type(menu).__name__ == "PokemonPartyMenuState":
    menu.on_select(0)
    box = g.current_state
    check(type(box).__name__ == "NameRaterState", f"a Pokemon picked: the name box ({type(box).__name__})")
    if type(box).__name__ == "NameRaterState":
        box.text = "Blaze"; box.confirm()
        check(story.player_team[0].nickname == "Blaze", f"renamed: {story.player_team[0].nickname}")

print(f"\n##### {fails} fails")
