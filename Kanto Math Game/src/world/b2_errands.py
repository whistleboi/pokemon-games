"""Black 2 / White 2's little room errands (batch 3b, 11-21; Route 4's houses, both versions).

stat_check: a person particular about one stat names a number each day; show them a Pokemon whose stat matches it
  exactly and they give five of a wing, higher and they give one (Route 4: Speed -> Health Wings in Black 2, Attack ->
  Swift Wings in White 2). Once a day. Event {"stat_check": {"stat": "SPEED", "item": "HEALTH_WING", "key": "..."}}.
cry_quiz: a Maid imitates the cry of one of your party; pick which. The first right answer wins a Poke Toy; after that
  she just plays. Event {"cry_quiz": {"item": "POKE_TOY", "flag": "..."}}.
common._run_story_event hands both here.
maid_food (batch 4a, 11-23; through main's region hook, {"world": "b2_errands", "maid_food": True}): Route 5's hungry Maid,
  Black 2's "gourmet maniac": she buys food from your Bag at her own prices (Bulbapedia's Item maniac page: GOURMET).
berry_bunch ({"world": "b2_errands", "berry_bunch": {...}}): Route 5's Berry seller: one bunch of five a day for $200,
  today's kind one of Pomeg, Kelpsy, Qualot, Hondew, Grepa."""
import datetime
import random

STAT_NAMES = {"HP": "HP", "ATTACK": "Attack", "DEFENSE": "Defense", "SPATK": "Sp. Atk", "SPDEF": "Sp. Def", "SPEED": "Speed"}


def _today():
    return datetime.date.today().isoformat()


def target(story, key, team):
    """Today's number: near your party's own (so it can be met some days), the same all day."""
    rng = random.Random(f"{key}@{_today()}")
    lv = max([p.level for p in team if p] or [5])
    lo = max(8, int(lv * 1.1))
    return rng.randint(lo, lo + max(6, lv // 2))


def event(state, ev, lines, show):
    game, story = state.game, state.game.story_manager
    from src.states.overworld.common import _say_then
    team = [p for p in story.player_team if p and not getattr(p, "is_egg", False)]
    if ev.get("stat_check"):
        sc = ev["stat_check"]
        stat, item, key = sc["stat"], sc["item"], sc.get("key", "stat_check")
        name = STAT_NAMES.get(stat, stat.title())
        want = target(story, key, team)
        if story.story_flags.get(key) == _today():
            show([f"I've seen all the {name} I need for today! Come back tomorrow, OK?"])
            return
        best = max(team, key=lambda p: (p.stat_value(stat) == want, p.stat_value(stat)), default=None)
        head = [f"I'm very particular about a Pokemon's {name}!",
                f"Today I'd love to see a Pokemon with a {name} of {want} or more!"]
        if best is None or best.stat_value(stat) < want:
            show(head + [f"Hmm... none of yours today. There's more to a Pokemon than {name}, though! Try again tomorrow."])
            return
        exact = best.stat_value(stat) == want
        count = 5 if exact else 1
        story.story_flags[key] = _today()
        story.add_item(item, count)
        label = item.replace("_", " ").title()
        show(head + [f"Your {best.display_name}'s {name} is {best.stat_value(stat)}!" + (" Exactly what I wanted!" if exact else " Wonderful!"),
                     f"{getattr(game, 'player_name', 'You')} received {count} {label}{'s' if count > 1 else ''}!"])
        return
    if ev.get("cry_quiz"):
        cq = ev["cry_quiz"]
        if len(team) < 2:
            show(["Hi! I imitate Pokemon cries!", "...You have too few Pokemon with you for a guessing game. Come back with more!"])
            return
        pick = random.choice(team)
        try:
            pick.cry.play()
        except Exception:
            pass
        from src.states.systems.pick_list import PickListState

        def answer(p):
            game.change_state(state)
            if p is None:
                show(["Aww, no guess? Maybe next time!"])
                return
            if p is not pick:
                show([f"Close! Too bad... That was {pick.display_name}!"])
                return
            if not story.story_flags.get(cq.get("flag", "")):
                story.story_flags[cq.get("flag", "cry_quiz_won")] = True
                story.add_item(cq["item"])
                show(["Correct! You know the voices you hear every day.",
                      f"Thank you for playing with me! {getattr(game, 'player_name', 'You')} received a {cq['item'].replace('_', ' ').title()}!"])
            else:
                show(["Correct! Of course you know your partners' voices!"])
        _say_then(state, ["Hi! I'll imitate the cry of one of your Pokemon! Listen...", f"{pick.cry_text() if hasattr(pick, 'cry_text') else '...!'}",
                          "Which Pokemon was it?"],
                  lambda: game.change_state(PickListState(game, state, "WHOSE CRY?", [(p.display_name, p) for p in team], answer)))
        return
    show(lines or ["..."])


RARE_BERRIES = {"LANSAT_BERRY", "STARF_BERRY", "ENIGMA_BERRY", "MICLE_BERRY", "CUSTAP_BERRY", "JABOCA_BERRY", "ROWAP_BERRY"}
UNCOMMON_BERRIES = {k + "_BERRY" for k in ("RAZZ", "BLUK", "MAGOST", "NANAB", "WEPEAR", "PINAP", "CORNN", "RABUTA", "NOMEL",
                                            "SPELON", "PAMTRE", "WATMEL", "DURIN", "BELUE")}
GOURMET = {"SWEET_HEART": 100, "STICK": 200, "FRESH_WATER": 200, "LEFTOVERS": 200, "LUCKY_EGG": 200, "SODA_POP": 300,
           "LEMONADE": 350, "TINY_MUSHROOM": 500, "HONEY": 500, "MOOMOO_MILK": 500, "BERRY_JUICE": 1500, "CASTELIACONE": 2000,
           "LAVA_COOKIE": 4000, "OLD_GATEAU": 4000, "BIG_MUSHROOM": 5000, "RAGECANDYBAR": 6000, "SHOAL_SALT": 7000,
           "RARE_CANDY": 10000, "BALM_MUSHROOM": 25000}
BUNCH = ("POMEG_BERRY", "KELPSY_BERRY", "QUALOT_BERRY", "HONDEW_BERRY", "GREPA_BERRY")


def gourmet_price(item):
    """What Route 5's Maid pays for one (None: not food to her)."""
    if item in GOURMET:
        return GOURMET[item]
    if item.endswith("_BERRY"):
        return 30000 if item in RARE_BERRIES else 500 if item in UNCOMMON_BERRIES else 20
    return None


def _maid(state, show):
    game, story = state.game, state.game.story_manager
    from src.states.systems.pick_list import PickListState
    from src.states.overworld.common import _say_then
    foods = [(k, n, gourmet_price(k)) for k, n in sorted((story.inventory or {}).items()) if n > 0 and gourmet_price(k)]
    if not foods:
        show(["I'm cooking, but I'm short of ingredients... *sniff sniff* Nothing tasty in your Bag, I'm afraid."])
        return

    def picked(k):
        game.change_state(state)
        if k is None:
            show(["Oh... Maybe another time, then."])
            return
        price = gourmet_price(k)
        story.inventory[k] = story.inventory.get(k, 0) - 1
        if story.inventory[k] <= 0:
            story.inventory.pop(k, None)
        story.money = getattr(story, "money", 0) + price
        name = k.replace("_", " ").title()
        show([f"A {name}! Just what my recipe needs!", f"Here's ${price:,} for it. Thank you!"])
    choices = [(f"{k.replace('_', ' ').title()} x{n}  (${p:,})", k) for k, n, p in foods]
    _say_then(state, ["*sniff sniff* Something in your Bag smells delicious! Would you sell me one?"],
              lambda: game.change_state(PickListState(game, state, "SELL TO THE MAID", choices, picked)))


def _berry_bunch(state, ev, show):
    game, story = state.game, state.game.story_manager
    key = (ev.get("berry_bunch") or {}).get("key", "b2_r5_berry_bunch")
    kind = BUNCH[random.Random(f"{key}@{_today()}").randrange(len(BUNCH))]
    name = kind.replace("_", " ").title()
    if story.story_flags.get(key) == _today():
        show(["That's all I've got today! Come back tomorrow for a fresh bunch."])
        return
    if getattr(story, "money", 0) < 200:
        show([f"Today's bunch: five {name}s for $200! ...Oh, you're a bit short. Come back later!"])
        return
    story.money -= 200
    story.add_item(kind, 5)
    story.story_flags[key] = _today()
    show([f"Today's bunch: five {name}s for $200! Thank you!", f"{getattr(game, 'player_name', 'You')} received 5 {name}s!"])


_event_before = event


def event(state, ev, lines, show):   # noqa: F811  (the region hook's entry: the Route 5 errands, then the earlier ones)
    if ev.get("maid_food"):
        _maid(state, show)
        return
    if ev.get("berry_bunch"):
        _berry_bunch(state, ev, show)
        return
    _event_before(state, ev, lines, show)
