"""Join Avenue (Black 2 / White 2; batch 3b, 11-21, Jordan: "Black 2's offline rules"): you manage a new shopping street.

As in the game without other players: a few visitors come each day (3 here), each with a dream, one of the shop kinds.
Invite a visitor to open their shop on a free lot (8 lots). Recommend a shop to a visitor: if it's the kind they like,
the shop and the avenue grow more popular; if not, they leave. A shop's rank (1-10) comes from its popularity and opens
more of its goods; the avenue's rank (1-100) from all of it, with rewards on the way. The Nursery can only open after
the Hall of Fame, at avenue rank 15 or more. Everything is kept in the story flag "join_avenue".

Hooks: common._run_story_event hands {"join_avenue": "owner" | "assistant" | "visitor" | "shop", ...} events here.
The map (dev/builders/town_maps/unova.py JOIN_AVENUE) stands 3 visitor spots and 8 shopkeepers (one a lot)."""
import datetime
import random

LOTS = 8
VISITORS_A_DAY = 3
KINDS = {   # kind: (shop name, the dream, goods by shop rank: rank 1 first, each rank adds the next items)
    "market": ("Market", "I'd love to sell things that make Trainers' journeys easier!",
               ["POTION", "ANTIDOTE", "PARALYZE_HEAL", "SUPER_POTION", "FULL_HEAL", "HYPER_POTION", "REVIVE", "MAX_POTION",
                "FULL_RESTORE", "MAX_REVIVE"]),
    "florist": ("Flower Shop", "I want to grow lovely Berries and share them with everyone!",
                ["ORAN_BERRY", "PECHA_BERRY", "CHERI_BERRY", "RAWST_BERRY", "ASPEAR_BERRY", "CHESTO_BERRY", "PERSIM_BERRY",
                 "LUM_BERRY", "SITRUS_BERRY", "LEPPA_BERRY"]),
    "cafe": ("Cafe", "I want to cook delicious meals that make Pokemon happy!",
             ["BERRY_JUICE", "FRESH_WATER", "SODA_POP", "LEMONADE", "MOOMOO_MILK", "LAVA_COOKIE", "CASTELIACONE", "OLD_GATEAU",
              "RAGECANDYBAR", "RARE_CANDY"]),
    "dojo": ("Dojo", "I want to train other people's Pokemon and make them strong!",
             ["HEALTH_WING", "MUSCLE_WING", "RESIST_WING", "GENIUS_WING", "CLEVER_WING", "SWIFT_WING", "PROTEIN", "IRON",
              "CARBOS", "HP_UP"]),
    "antique": ("Antique Shop", "I want to collect rare things and surprise everyone!",
                ["RED_SHARD", "BLUE_SHARD", "YELLOW_SHARD", "GREEN_SHARD", "FIRE_STONE", "WATER_STONE", "THUNDER_STONE",
                 "LEAF_STONE", "MOON_STONE", "SUN_STONE"]),
    "raffle": ("Raffle Shop", "I want to run a raffle where anyone can win something great!",
               ["POKE_BALL", "GREAT_BALL", "NET_BALL", "DUSK_BALL", "QUICK_BALL", "TIMER_BALL", "HEAL_BALL", "ULTRA_BALL",
                "REPEAT_BALL", "LUXURY_BALL"]),
    "salon": ("Beauty Salon", "I want to groom Pokemon until they shine!",
              ["SHOAL_SALT", "SHOAL_SHELL", "HEART_SCALE", "PEARL", "BIG_PEARL", "STARDUST", "STAR_PIECE", "NUGGET",
               "PEARL_STRING", "COMET_SHARD"]),
    "nursery": ("Nursery", "I want to look after Eggs and help them hatch!",
                ["EVERSTONE", "DESTINY_KNOT", "POWER_WEIGHT", "POWER_BRACER", "POWER_BELT", "POWER_LENS", "POWER_BAND",
                 "POWER_ANKLET", "OVAL_CHARM", "SHINY_CHARM"]),
}
NAMES = ["Kirk", "Rosa", "Dean", "Amira", "Lewis", "Pia", "Omar", "Celia", "Hank", "Mina", "Theo", "Lila", "Ravi", "Noor",
         "Bram", "Iris", "Jude", "Vera", "Otto", "Sana"]
REWARDS = {2: "POTION", 3: "GREAT_BALL", 5: "HYPER_POTION", 8: "RARE_CANDY", 10: "NUGGET", 15: "PP_UP", 20: "MASTER_BALL",
           30: "PP_MAX", 50: "BIG_NUGGET", 100: "COMET_SHARD"}


def _today():
    return datetime.date.today()


def data(story):
    d = story.story_flags.get("join_avenue")
    if not isinstance(d, dict):
        d = {"pop": 0, "lots": [None] * LOTS, "day": None, "visitors": [], "rewarded": []}
        story.story_flags["join_avenue"] = d
    return d


def rank(d):
    return max(1, min(100, 1 + int(d.get("pop", 0)) // 20))


def shop_rank(lot):
    return max(1, min(10, 1 + int(lot.get("pop", 0)) // 30))


def kinds_open(story, d):
    """The shop kinds a visitor may dream of now (the Nursery: after the Hall of Fame, at rank 15)."""
    ks = [k for k in KINDS if k != "nursery"]
    if story.story_flags.get("beat_unova_champion") and rank(d) >= 15:
        ks.append("nursery")
    return ks


def visitors(story):
    """Today's visitors [{name, dream, likes, done}], rolled once a day."""
    d = data(story)
    today = _today().isoformat()
    if d.get("day") != today:
        rng = random.Random("join_avenue@" + today)
        ks = kinds_open(story, d)
        d["day"] = today
        d["visitors"] = [{"name": rng.choice(NAMES), "dream": rng.choice(ks), "likes": rng.choice(ks), "done": False}
                         for _ in range(VISITORS_A_DAY)]
    return d["visitors"]


def _grow(story, d, lot, amount):
    """Popularity for a shop and the avenue; the avenue's rank rewards as it climbs. Returns the reward lines."""
    before = rank(d)
    if lot is not None:
        lot["pop"] = int(lot.get("pop", 0)) + amount
    d["pop"] = int(d.get("pop", 0)) + amount
    out = []
    if rank(d) > before:
        out.append(f"Join Avenue's rank went up to {rank(d)}!")
        for r, item in sorted(REWARDS.items()):
            if before < r <= rank(d) and r not in d["rewarded"]:
                d["rewarded"].append(r)
                story.add_item(item)
                out.append(f"Jacci: A reward for the avenue's rank {r}: a {item.replace('_', ' ').title()}!")
    return out


def event(state, ev, lines, show):
    game, story = state.game, state.game.story_manager
    from src.states.overworld.common import _say_then
    from src.states.systems.pick_list import PickListState
    d = data(story)
    kind = ev.get("join_avenue")
    name = getattr(game, "player_name", "You")
    if kind == "owner":
        if story.story_flags.get("b2_join_manager"):
            show(["Owner: The avenue's in your hands now. I'm counting on you!"])
            return
        story.story_flags["b2_join_manager"] = True
        show(["Owner: Welcome to Join Avenue! It's brand new, and no shops have opened yet.",
              "Owner: I run several avenues, and I'm far too busy for this one. Would you be its manager?",
              f"Owner: You will? Wonderful! From today, {name} manages Join Avenue!",
              "Owner: Visitors come every day. Hear their dreams, invite them to open shops, and recommend shops to them.",
              "Owner: My assistants Jacci and Future will help you. Good luck, manager!"])
        return
    if not story.story_flags.get("b2_join_manager"):
        show(["The avenue's still waiting for a manager. Try the office at the south end."])
        return
    if kind == "assistant":
        open_ = [l for l in d["lots"] if l]
        show([f"Jacci: Join Avenue is rank {rank(d)}, manager! {len(open_)} of {LOTS} lots have shops.",
              "Future: Visitors come every day. Invite them to open shops, and recommend the kind of shop they like!"]
             + ([f"Jacci: Next reward at rank {min(r for r in REWARDS if r > rank(d))}."] if any(r > rank(d) for r in REWARDS) else []))
        return
    if kind == "visitor":
        vs = visitors(story)
        i = int(ev.get("slot", 0))
        if i >= len(vs) or vs[i].get("done"):
            show(["They've gone on their way. More visitors will come tomorrow!"])
            return
        v = vs[i]
        dream = KINDS[v["dream"]][1]
        free = [n for n, l in enumerate(d["lots"]) if not l]
        shops = [(n, l) for n, l in enumerate(d["lots"]) if l]
        choices = []
        if free and v["dream"] in kinds_open(story, d):
            choices.append((f"Invite: open a {KINDS[v['dream']][0]}", ("invite", free[0])))
        for n, l in shops:
            choices.append((f"Recommend the {KINDS[l['kind']][0]} ({l['owner']})", ("recommend", n)))
        if not choices:
            show([f"{v['name']}: {dream}"])
            return

        def picked(c):
            game.change_state(state)
            if c is None:
                show([f"{v['name']}: Maybe another time, then."])
                return
            act, n = c
            v["done"] = True
            if act == "invite":
                d["lots"][n] = {"kind": v["dream"], "owner": v["name"], "pop": 0}
                story.story_flags[f"ja_lot_{n}"] = True
                show([f"{v['name']}: Really? I can open my {KINDS[v['dream']][0]} here? Thank you, manager!"] + _grow(story, d, d["lots"][n], 10))
                return
            lot = d["lots"][n]
            if lot["kind"] == v["likes"]:
                show([f"{v['name']}: The {KINDS[lot['kind']][0]}? That's just what I wanted! I'll go right now!",
                      f"The {KINDS[lot['kind']][0]} became more popular!"] + _grow(story, d, lot, 15))
            else:
                show([f"{v['name']}: Hmm, a {KINDS[lot['kind']][0]}... not really my thing. I'll be going.",
                      f"(They seemed to want a {KINDS[v['likes']][0]}.)"] + _grow(story, d, None, 2))
        _say_then(state, [f"Visitor {v['name']}: Hello! Is this Join Avenue? {dream}"],
                  lambda: game.change_state(PickListState(game, state, "MANAGER", choices, picked)))
        return
    if kind == "shop":
        n = int(ev.get("lot", 0))
        lot = d["lots"][n] if n < len(d["lots"]) else None
        if not lot:
            show(["An empty lot. A visitor's dream could open a shop here."])
            return
        r = shop_rank(lot)
        goods = KINDS[lot["kind"]][2][:r]
        from src.pokemon import items as _items
        goods = [g for g in goods if _items.info(g) or _items.price(g)]

        def go():
            from src.states.systems import PokeMartState
            game.change_state(PokeMartState(game, state, stock=goods))
        _say_then(state, [f"{lot['owner']}: Welcome to my {KINDS[lot['kind']][0]}! (Shop rank {r})"], go)
        return
    show(lines or ["..."])
