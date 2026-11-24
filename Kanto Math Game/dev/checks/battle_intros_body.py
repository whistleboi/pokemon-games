# Battle intros from each region's own game (Jordan 11-24, region/systems; src/vfx/canon_intros.py): Kanto, Sevii
# and Orange play FireRed's, Hoenn Emerald's, Johto HGSS's, Sinnoh Platinum's, Orre the Essentials ones of
# Pokemon Orre 2.1.1, each picked the way that game picks it; Unova and the menu regions keep the older intros.
# Also: map battles (OVERWORLD style) get one intro, a classic trainer one, and back from the Bag none.
# Pictures mid-effect and a GIF per region in dev/checks/out/battle_intros/.
#   bash dev/checks/run.sh battle_intros
exec(open("dev/checks/dungeon_lib.py", encoding="utf-8").read())
import datetime as _dt
import glob as _glob
import json as _json
import os as _os
from PIL import Image as _Image
from src.vfx import canon_intros as ci
from src.vfx import transitions as tr
from src.states.battle import TrainerBattleState, TrainerIntroState

OUT = _os.path.join(S, "battle_intros")
_os.makedirs(OUT, exist_ok=True)
g.dungeon_routes = True
NOON, MIDNIGHT = _dt.datetime(2026, 11, 24, 12), _dt.datetime(2026, 11, 24, 23)

_SPRITES = {}
for _f in _glob.glob("assets/*_area_data.json"):
    def _walk(o):
        if isinstance(o, dict):
            if o.get("class") and o.get("name") and o.get("sprite"):
                _SPRITES.setdefault(str(o["name"]).lower(), o["sprite"])
            for v in o.values():
                _walk(v)
        elif isinstance(o, list):
            for v in o:
                _walk(v)
    _walk(_json.load(open(_f, encoding="utf-8")))


def tsprite(name):
    f = _SPRITES.get(name.lower()) or next((v for k, v in _SPRITES.items() if name.lower() in k), None)
    return g.assets.get_trainer_image(f) if f else None


def C(**kw):
    return ci.Ctx(**kw)


def sel(key, **kw):
    return ci.select_for(key, C(**kw))[0]


print("1) the region picks the game")
check([ci.game_for(r) for r in ("KANTO", "ORANGE", "HOENN", "JOHTO", "SINNOH", "ORRE")] ==
      ["frlg", "frlg", "emerald", "hgss", "platinum", "orre"], "Kanto/Orange FireRed, Hoenn Emerald, Johto HGSS, Sinnoh Platinum, Orre Essentials")
check(all(ci.game_for(r) is None for r in ("UNOVA", "KALOS", "ALOLA", "GALAR", "PALDEA", "DECOLORE")), "Unova and the menu regions: no profile (today's intros)")
story.current_area_key = "GREEN_PATH"
check(story.get_current_region() == "KANTO" and ci.game_for(story.get_current_region()) == "frlg", "a Sevii area reports Kanto: FireRed's")

print("2) FireRed/LeafGreen (Kanto, Sevii, Orange)")
L, H = dict(foe_levels=[3], my_levels=[10]), dict(foe_levels=[10], my_levels=[10])
check(sel("frlg", **L) == "slice" and sel("frlg", **H) == "white_bars", "wild grass: weaker Slice, equal-or-stronger White Bars")
check(sel("frlg", area="cave", **L) == "clockwise" and sel("frlg", area="cave", **H) == "grid", "wild cave: Clockwise / Grid Squares")
check(sel("frlg", area="cave", dark=True, unlit=True, **L) == "blur" and sel("frlg", area="cave", dark=True, unlit=False, **L) == "clockwise",
      "a dark cave: Blur till Flash lights it, then the cave row")
check(sel("frlg", surfing=True, **L) == "wave" and sel("frlg", surfing=True, **H) == "ripple", "surfing: Wave / Ripple")
check(sel("frlg", fished=True, **L) == "slice", "fishing from the shore: the tile you stand on (land)")
check(sel("frlg", wild=False, **L) == "balls_trail" and sel("frlg", wild=False, **H) == "angled", "trainer: Poke Balls Trail / Angled Wipes")
check(sel("frlg", wild=False, area="cave", **L) == "shuffle" and sel("frlg", wild=False, area="cave", **H) == "big_ball", "trainer in a cave: Shuffle / Big Poke Ball")
check(sel("frlg", wild=False, double=True, foe_levels=[8, 8], my_levels=[10, 5]) == "angled", "a double trainer: the first two levels summed (16 vs 15: stronger)")
check(sel("frlg", wild=False, cls="GYM_LEADER", name="Brock", **L) == "balls_trail", "a Gym Leader: the normal table")
check(sel("frlg", wild=False, cls="ROCKET_LEADER", name="Giovanni", **H) == "angled", "Giovanni: the normal table")
_e = ci.select_for("frlg", C(wild=False, cls="ELITE_FOUR", name="Agatha"))
check(_e[0] == "mugshot" and _e[1]["who"] == "agatha", "Elite Four Agatha: her mugshot (pink)")
check(ci.select_for("frlg", C(wild=False, cls="CHAMPION", name="{rival_name}"))[1]["who"] == "champion", "the Champion: Blue's mugshot")
check(sel("frlg", species=150, **L) == "blur" and sel("frlg", species=243, **L) == "slice", "Mewtwo: Blur; Raikou (a roamer): the wild table")
check(ci.select_for("frlg", C())[2] == ("gen3", 2), "two grey flashes first")

print("3) Emerald (Hoenn)")
check(sel("emerald", area="cave", dark=True, unlit=False, **L) == "blur", "Emerald: a dark cave stays on the Flash row after Flash")
check(sel("emerald", wild=False, cls="TEAM_MAGMA", name="Team Magma Grunt") == "big_ball" and
      ci.select_for("emerald", C(wild=False, cls="ROCKET", name="Aqua Admin Matt"))[1]["art"] == "aqua", "Magma and Aqua: their emblems (any level)")
check(ci.select_for("emerald", C(wild=False, cls="ELITE_FOUR", name="Glacia"))[1]["who"] == "glacia", "Glacia's mugshot")
check(sel("emerald", species=382) == "legend_art" and sel("emerald", species=384) == "rayquaza", "Kyogre's art, Rayquaza's")
check(ci.select_for("emerald", C(species=378))[1]["art"] == "regice" and sel("emerald", species=151) == "grid" and sel("emerald", species=249) == "blur",
      "Regice's braille, Mew's Grid Squares, Lugia's Blur")
check(sel("emerald", wild=False, cls="GYM_LEADER", name="Roxanne", **L) == "balls_trail", "a Gym Leader: the normal table")
check(ci.select_for("emerald", C())[2] == ("gen3", 3), "three grey flashes")

print("4) Platinum (Sinnoh)")
check(sel("platinum", **L) == "pt_grass" and ci.select_for("platinum", C(**L))[1] == {"higher": False}, "wild grass, foe lower")
_p = ci.select_for("platinum", C(foe_levels=[11], my_levels=[10]))
check(_p[1]["higher"] and _p[2][1] == ci.WHITE, "strictly higher: the 'higher' version, white flash")
_p = ci.select_for("platinum", C(**H))
check(not _p[1]["higher"] and _p[2][1] == ci.BLACK, "a tie: the lower version, black flash")
check(sel("platinum", fished=True) == "pt_water" and sel("platinum", area="cave") == "pt_cave", "fishing: water; a cave: the iris")
check(sel("platinum", wild=False) == "tr_grass" and sel("platinum", wild=False, surfing=True) == "tr_water" and sel("platinum", wild=False, area="cave") == "tr_cave",
      "trainers: the six Poke Ball effects by terrain")
check(sel("platinum", wild=False, cls="GYM_LEADER", name="Roark") == "leader_banner" and sel("platinum", wild=False, cls="GYM_LEADER", name="Volkner", double=True) == "ds_double",
      "a Gym Leader's banner; not in a double battle")
check(sel("platinum", wild=False, cls="CHAMPION", name="Cynthia") == "e4_vs", "Cynthia: the E4/Champion VS")
check(sel("platinum", wild=False, cls="GALACTIC", name="Galactic Grunt") == "logo_rain" and sel("platinum", wild=False, cls="GALACTIC", name="Commander Mars", double=True) == "galactic_boss",
      "Galactic: Grunts' G logos; Mars (even in a double) the boss effect")
check(sel("platinum", wild=False, cls="RIVAL", name="Barry") == "tr_grass", "Barry: the ordinary trainer effect")
check(sel("platinum", species=487) == "mythical" and sel("platinum", species=483) == "legendary" and sel("platinum", species=481) == "pt_grass",
      "Giratina mythical, Dialga legendary, Mesprit (roaming) the local one")

print("5) HeartGold/SoulSilver (Johto): the time of day, not the levels")
_d, _n = ci.select_for("hgss", C(night=False, **H)), ci.select_for("hgss", C(night=True, **L))
check(_d[0] == "hg_grass" and not _d[1]["night"] and _d[2][1] == ci.WHITE, "day: grass grid, white flash")
check(_n[0] == "hg_grass" and _n[1]["night"] and _n[2][1] == ci.BLACK, "night: grass grid from the other corner, black flash")
check(sel("hgss", area="cave") == "hg_cave" and sel("hgss", surfing=True) == "hg_water", "cave diagonals; the water wave")
check(ci.select_for("hgss", C(wild=False, night=False))[1]["higher"] and not ci.select_for("hgss", C(wild=False, night=True))[1]["higher"],
      "trainers: Platinum's six, day = its 'higher', night = 'lower'")
check(sel("hgss", wild=False, cls="GYM_LEADER", name="Falkner") == "leader_banner" and sel("hgss", wild=False, cls="RIVAL", name="Silver") == "leader_banner",
      "Gym Leaders and Silver: the portrait banner")
check(sel("hgss", wild=False, cls="ROCKET", name="Rocket Grunt") == "logo_rain" and sel("hgss", wild=False, cls="ROCKET", name="Executive Ariana") == "rocket_admin",
      "Rocket: grunts' R, executives' name banner")
check(sel("hgss", wild=False, cls="KIMONO_GIRL", name="Kimono Girl Zuki") == "kimono" and sel("hgss", wild=False, cls="PKMN_TRAINER", name="Red") == "red_tiles",
      "the Kimono Girls' and Red's own")
check(sel("hgss", wild=False, cls="ELITE_FOUR", name="Will") == "e4_vs" and sel("hgss", species=250) == "legendary" and sel("hgss", species=150) == "mythical",
      "Will's VS; Ho-Oh legendary; Mewtwo 'ancient'")
check(sel("hgss", species=245, night=True) == "hg_grass", "Suicune (a roamer): the local one")

print("6) Orre (Essentials v21.1)")
check(sel("orre", night=False) == "or_snake" and sel("orre", wild=False, night=False) == "or_two_ball" and sel("orre", wild=False, night=True) == "or_spin_split",
      "outside: wild Snake Squares; trainer Two Ball Pass by day, Spin Ball Split at night")
check(ci.select_for("orre", C(area="inside"))[1]["origin"] == 0 and ci.select_for("orre", C(in_room=True, night=True))[1]["origin"] == 3,
      "inside: Diagonal Bubble from the top left by day, bottom right at night")
check(sel("orre", area="cave", wild=False) == "or_ball_down" and ci.select_for("orre", C(area="cave"))[2][1] == ci.BLACK, "a cave: Ball Down, black flashes")
check(sel("orre", fished=True) == "or_splash" and sel("orre", wild=False, surfing=True) == "or_wavy_three_ball", "water: Rising Splash / Wavy Three Ball Up")
check(sel("orre", wild=False, double=True) == "or_four_ball", "a double trainer: Four Ball Burst")
check(sel("orre", wild=False, cls="CIPHER_ADMIN", name="Cipher Admin Miror B.") == "or_vs_trainer" and sel("orre", wild=False, cls="CHAMPION", name="Cipher Head Evice") == "or_vs_trainer"
      and sel("orre", wild=False, cls="MT_BATTLE_MASTER", name="Mt. Battle Master Vander") == "or_vs_trainer", "Miror B., Evice, the Mt. Battle master: VS cards")
check(sel("orre", wild=False, cls="CHAMPION", name="Colosseum Champion") == "or_vs_e4" and ci.select_for("orre", C(wild=False, cls="CHAMPION", name="X"))[2] is None,
      "the Champion card, no flashes first")
check(sel("orre", wild=False, cls="CIPHER_ADMIN", name="Cipher Admin Dakim") == "or_two_ball", "other admins: the default table")

print("7) read from the real battle and place: terrain, levels, the clock")
story.player_team = [mk(4)]
story.player_team[0].level = 20
story.current_area_key = "DARK_CAVE"
_w = mk(41); _w.level = 30
_wb = WildBattleState(g, _w, "DARK_CAVE")
_pl = ci.pick(g, _wb, now=NOON)
check(_pl.game_key == "hgss" and _pl.effect == "hg_cave" and _pl.ctx.area == "cave", f"Johto's Dark Cave: HGSS's cave grid ({_pl})")
check(ci.pick(g, _wb, now=MIDNIGHT).params["night"], "...the night one at 23:00")
story.current_area_key = "MT_MOON" if "MT_MOON" in g.loader.area_data["STORY_PROGRESSION"] else "KANTO_MT_MOON"
_pl = ci.pick(g, _wb)
check(_pl.game_key == "frlg" and _pl.effect == "grid", f"Mt. Moon, the foe stronger: FireRed's Grid Squares ({_pl})")
_w.level = 5
check(ci.pick(g, WildBattleState(g, _w, story.current_area_key)).effect == "clockwise", "...weaker: Clockwise Wipe")
story.current_area_key = "SINNOH_ROUTE_201"
check(ci.pick(g, WildBattleState(g, _w, "SINNOH_ROUTE_201")).effect == "pt_grass", "Sinnoh Route 201: Platinum's strips")
story.current_area_key = "TANGELO_JUNGLE"
check(ci.pick(g, WildBattleState(g, _w, "TANGELO_JUNGLE")).game_key == "frlg", "the Orange Islands: FireRed's")
story.current_area_key = "HOENN_ROUTE_101"
_tb = TrainerBattleState(g, [mk(1)], trainer_sprite=tsprite("Sidney"), trainer_class="ELITE_FOUR", trainer_name="Sidney")
_pl = ci.pick(g, TrainerIntroState(g, _tb.trainer_sprite, ["Hi"], _tb))
check(_pl.effect == "mugshot" and _pl.params["who"] == "sidney", "a trainer's intro reads its battle: Sidney's mugshot")

print("8) every effect runs to the end and the battle starts (classic battles, intros on)")
g.battle_transitions = True
_ps = PlayState(g, classic=True)


def run(target, region_area):
    story.current_area_key = region_area
    g.current_state = _ps
    g.screen.fill((60, 120, 60))
    g.change_state(target)
    st = g.current_state
    if not isinstance(st, tr.BattleTransitionState):
        return None, False
    for _ in range(st.length + 10):
        if g.current_state is not st:
            break
        st.draw()
        st.update()
    return st, g.current_state is target


_cases = [("KANTO_ROUTE_1", "wild"), ("HOENN_ROUTE_101", "wild"), ("JOHTO_ROUTE_29", "wild"), ("SINNOH_ROUTE_201", "wild"),
          ("ORRE_DESERT", "wild"), ("JOHTO_ROUTE_29", ("GYM_LEADER", "Falkner")), ("SINNOH_ROUTE_201", ("GALACTIC", "Galactic Grunt")),
          ("ORRE_DESERT", ("CIPHER_ADMIN", "Cipher Admin Miror B.")), ("UNOVA_ROUTE_1" if "UNOVA_ROUTE_1" in g.loader.area_data["STORY_PROGRESSION"] else "KALOS_ROUTE_2", "wild")]
for area, kind in _cases:
    story.current_area_key = area
    if kind == "wild":
        tgt = WildBattleState(g, mk(16), area)
    else:
        b = TrainerBattleState(g, [mk(16)], trainer_sprite=tsprite(kind[1]), trainer_class=kind[0], trainer_name=kind[1])
        tgt = TrainerIntroState(g, b.trainer_sprite, ["Hi"], b)
    st, ok = run(tgt, area)
    canon = st is not None and st.canon is not None
    want = ci.game_for(story.get_current_region()) is not None
    check(st is not None and ok and canon == want, f"{area} {kind}: {st.style if st else None} ({st.canon.plan.effect if canon else 'old intro'}) -> the battle")
# every effect on its own, start to end (each game's effects, the parameters it uses)
_snap = g.screen.copy()
_ctx = C(name="Lance", cls="ELITE_FOUR", foe_sprite=tsprite("Lance"), foe_image=mk(382).image, region="JOHTO")
_variants = {"big_ball": [{"em": True}, {"em": False, "art": "magma", "hold": 60}, {"em": True, "art": "registeel"}],
             "hg_grass": [{"night": False}, {"night": True}], "hg_cave": [{"night": False}, {"night": True}],
             "or_diagonal": [{"origin": 0}, {"origin": 3}], "legendary": [{"push": 2350}, {"push": 660}],
             "logo_rain": [{"logo": "galactic"}, {"logo": "rocket"}], "mugshot": [{"em": False, "who": "lance"}, {"em": True, "who": "champion"}]}
_bad = []
for name in ci.EFFECTS:
    for prm in _variants.get(name, [{"em": True, "higher": True}, {"em": False, "higher": False}]):
        try:
            it = ci.Intro(g, _snap, ci.Plan("x", name, prm, ("ds", ci.WHITE, 2), _ctx))
            for t in range(it.length):
                it.draw(g.screen, t)
            end = g.screen.get_at((640, 360))[:3]
            if end != it.fx.END:
                _bad.append(f"{name} {prm} ends {end}")
        except Exception as ex:
            _bad.append(f"{name} {prm}: {ex!r}")
check(not _bad, f"all {len(ci.EFFECTS)} effects draw start to end and end on their colour {_bad[:4]}")

print("9) map battles (OVERWORLD style): one intro, then the battle on the map; back from the Bag, none")
_made = []
_orig_init = tr.BattleTransitionState.__init__


def _count(self, *a, **k):
    _made.append(a[1] if len(a) > 1 else k.get("target"))
    _orig_init(self, *a, **k)


tr.BattleTransitionState.__init__ = _count


def finish_intro(n=200):
    for _ in range(n):
        st = g.current_state
        if not isinstance(st, tr.BattleTransitionState):
            return
        st.draw()
        st.update()


story.battle_style = "OVERWORLD"
p = kanto("KANTO_ROUTE_3", came="PEWTER_CITY")
story.player_team[0].level = 50
trm = next((m for f in p.run.floors for m in f.movers if m.kind == "trainer"), None)
p._battle_trainer(trm)
for _ in range(400):
    if g.current_state is not p:
        break
    if p.dialogue_box.visible:
        p.dialogue_box.advance()
    p.update()
check(isinstance(g.current_state, tr.BattleTransitionState) and g.current_state.canon is not None, f"a map trainer battle opens with FireRed's intro ({type(g.current_state).__name__})")
_shot = g.current_state
for _ in range(_shot.length // 2):
    _shot.update()
_shot.draw()
pygame.image.save(g.screen, _os.path.join(OUT, "map_trainer_kanto.png"))
finish_intro()
b = g.current_state
check(isinstance(b, TrainerBattleState) and getattr(b, "overworld", None) is not None and len(_made) == 1, f"...then the battle on the map, after one intro ({len(_made)})")
from src.states.systems.bag import BagState
g.change_state(BagState(g, b, context="battle"))
g.change_state(b)
check(g.current_state is b and len(_made) == 1, "back from the Bag: straight into the battle, no second intro")
_made.clear()
p = kanto("KANTO_ROUTE_1")
w, _ = beside(p, "wild")
p._meet_wild(w)
p._pick(1)
for _ in range(400):
    if g.current_state is not p:
        break
    p.update()
check(isinstance(g.current_state, tr.BattleTransitionState) and len(_made) == 1, f"a map wild battle: one intro ({type(g.current_state).__name__}, {len(_made)})")
finish_intro()
check(isinstance(g.current_state, WildBattleState) and getattr(g.current_state, "overworld", None) is not None and len(_made) == 1, "...then the wild battle on the map")
story.battle_style = "TRADITIONAL"
_made.clear()
p = kanto("KANTO_ROUTE_3", came="PEWTER_CITY")
trm = next((m for f in p.run.floors for m in f.movers if m.kind == "trainer"), None)
p._battle_trainer(trm)
finish_intro()
_ti = g.current_state
check(isinstance(_ti, TrainerIntroState) and len(_made) == 1, f"a classic trainer battle: one intro before the trainer's lines ({type(_ti).__name__})")
g.change_state(_ti.next_state)
check(isinstance(g.current_state, TrainerBattleState) and len(_made) == 1, "...and none between the lines and the battle")
tr.BattleTransitionState.__init__ = _orig_init

print("10) pictures mid-effect and a GIF per region (dev/checks/out/battle_intros)")


def backdrop(area):
    """The region's own map to start from (its route drawn as you'd see it), else the last screen."""
    story.current_area_key = area
    try:
        st = PlayState(g)
        g.change_state(st)
        for _ in range(3):
            st.update()
        st.draw()
    except Exception:
        pass
    return g.screen.copy()


REGIONS = {
    "kanto": ("KANTO_ROUTE_1", "frlg", [("wild weaker", C(**L)), ("wild stronger", C(**H)), ("cave weaker", C(area="cave", **L)),
                                       ("surfing stronger", C(surfing=True, **H)), ("trainer weaker", C(wild=False, **L)),
                                       ("trainer stronger", C(wild=False, **H)), ("trainer cave stronger", C(wild=False, area="cave", **H)),
                                       ("Elite Four Lance", C(wild=False, cls="ELITE_FOUR", name="Lance", foe_sprite=tsprite("Lance"))),
                                       ("Mewtwo", C(species=150))]),
    "hoenn": ("HOENN_ROUTE_101", "emerald", [("wild stronger", C(**H)), ("dark cave", C(area="cave", dark=True, **L)),
                                            ("trainer weaker", C(wild=False, **L)), ("Team Magma", C(wild=False, cls="TEAM_MAGMA", name="Team Magma Grunt")),
                                            ("Team Aqua", C(wild=False, cls="TEAM_AQUA", name="Team Aqua Grunt")),
                                            ("Elite Four Drake", C(wild=False, cls="ELITE_FOUR", name="Drake", foe_sprite=tsprite("Drake"))),
                                            ("Regirock", C(species=377)), ("Kyogre", C(species=382, foe_image=mk(382).image)),
                                            ("Rayquaza", C(species=384, foe_image=mk(384).image))]),
    "johto": ("JOHTO_ROUTE_29", "hgss", [("wild day", C(night=False)), ("wild night", C(night=True)), ("cave day", C(area="cave")),
                                        ("water", C(surfing=True)), ("trainer day", C(wild=False)), ("trainer night", C(wild=False, night=True)),
                                        ("Falkner", C(wild=False, cls="GYM_LEADER", name="Falkner", foe_sprite=tsprite("Falkner"))),
                                        ("Silver", C(wild=False, cls="RIVAL", name="Silver", foe_sprite=tsprite("{rival_name}"))),
                                        ("Rocket Grunt", C(wild=False, cls="ROCKET", name="Rocket Grunt")),
                                        ("Executive Archer", C(wild=False, cls="ROCKET", name="Executive Archer", foe_sprite=tsprite("Executive Archer"))),
                                        ("Kimono Girl", C(wild=False, cls="KIMONO_GIRL", name="Kimono Girl Zuki")),
                                        ("Red", C(wild=False, cls="PKMN_TRAINER", name="Red")), ("Will", C(wild=False, cls="ELITE_FOUR", name="Will", foe_sprite=tsprite("Will"))),
                                        ("Ho-Oh", C(species=250))]),
    "sinnoh": ("SINNOH_ROUTE_201", "platinum", [("wild lower", C(**L)), ("wild higher", C(foe_levels=[11], my_levels=[10])),
                                               ("water", C(surfing=True)), ("cave", C(area="cave")), ("trainer lower", C(wild=False, **L)),
                                               ("trainer higher", C(wild=False, foe_levels=[11], my_levels=[10])),
                                               ("trainer water higher", C(wild=False, surfing=True, foe_levels=[11], my_levels=[10])),
                                               ("trainer cave higher", C(wild=False, area="cave", foe_levels=[11], my_levels=[10])),
                                               ("double", C(wild=False, double=True)), ("Galactic Grunt", C(wild=False, cls="GALACTIC", name="Galactic Grunt")),
                                               ("Cyrus", C(wild=False, cls="GALACTIC", name="Cyrus")),
                                               ("Roark", C(wild=False, cls="GYM_LEADER", name="Roark", foe_sprite=tsprite("Roark"))),
                                               ("Cynthia", C(wild=False, cls="CHAMPION", name="Cynthia", foe_sprite=tsprite("Cynthia"))),
                                               ("Giratina", C(species=487)), ("Dialga", C(species=483))]),
    "orre": ("ORRE_DESERT", "orre", [("wild outside", C()), ("wild inside", C(area="inside")), ("wild cave", C(area="cave")),
                                    ("wild water", C(fished=True)), ("trainer day", C(wild=False)), ("trainer night", C(wild=False, night=True)),
                                    ("trainer inside", C(wild=False, area="inside")), ("trainer cave", C(wild=False, area="cave")),
                                    ("trainer water", C(wild=False, surfing=True)), ("trainer water night", C(wild=False, surfing=True, night=True)),
                                    ("double", C(wild=False, double=True)),
                                    ("Miror B.", C(wild=False, cls="CIPHER_ADMIN", name="Cipher Admin Miror B.", foe_sprite=tsprite("Cipher Admin Miror B."))),
                                    ("Champion", C(wild=False, cls="CHAMPION", name="Champion", foe_sprite=tsprite("Cipher Head Evice")))]),
}
for region, (area, key, cases) in REGIONS.items():
    snap = backdrop(area)
    frames, picked = [], []
    for label, c in cases:
        if c.foe_sprite is None and not c.wild:
            c.foe_sprite = tsprite("Brock")
        if c.foe_image is None:
            c.foe_image = mk(25).image
        effect, prm, flash = ci.select_for(key, c)
        picked.append(effect)
        it = ci.Intro(g, snap, ci.Plan(key, effect, prm, flash, c))
        mid = it.length * 2 // 3
        for t in range(it.length):
            it.draw(g.screen, t)
            _ci_font = ci._font(28)
            tag = _ci_font.render(f"{region.upper()}: {label} ({effect})", True, (255, 255, 120))
            if t == mid:
                pygame.image.save(g.screen, _os.path.join(OUT, f"{region}_{label.replace(' ', '_').replace('.', '')}.png"))
            small = pygame.transform.smoothscale(g.screen, (480, 270))
            small.blit(pygame.transform.smoothscale(tag, (tag.get_width() * 2 // 3, tag.get_height() * 2 // 3)), (6, 4))
            frames.append(_Image.frombytes("RGB", (480, 270), pygame.image.tostring(small, "RGB")))
        frames += frames[-1:] * 6
    path = _os.path.join(OUT, f"{region}.gif")
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=40, loop=0)
    check(_os.path.getsize(path) > 10000 and len(frames) > 50, f"{region}: GIF of {len(cases)} intros ({len(frames)} frames; {', '.join(picked)})")
g.battle_transitions = False
print(f"##### {fails} failures")
