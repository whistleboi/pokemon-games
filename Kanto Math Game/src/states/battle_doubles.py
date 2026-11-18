# [REF-0093: Battle slots (doubles-ready)]
"""Where a second battler per side would plug in (Jordan, 11-17: "Since we don't have double battles, those moves
can still work as intended but would have no effect. This will allow easy integration of double battles when that
time comes.").

Every battle today is a single battle: one Pokemon a side, `player_pokemon` and `opponent_pokemon`. The moves that
only matter with partners (Helping Hand, Ally Switch, Coaching, Aromatic Mist, Dragon Cheer, Follow Me / Rage
Powder / Spotlight, After You, Quash, the Pledge combinations, Pollen Puff's heal, spread moves' 0.75x...) all ask
the questions below instead of assuming "there is no ally", so a doubles battle only has to answer them:

- `battlers(side)`        the Pokemon out on a side ("player" / "opponent"), in slot order. Singles: one each.
- `allies(mon)`           the others on mon's side that are out. Singles: always [].
- `ally_of(mon)`          the one partner (or None). Singles: None.
- `opponents_of(mon)`     the other side's Pokemon that are out. Singles: [the foe].
- `move_targets(user, d, chosen)` who a move hits, from its PokeAPI target ("selected-pokemon", "all-opponents",
                          "all-other-pokemon", "ally", "user-or-ally", "user-and-allies", "all-allies", "all-pokemon"...).
- `spread_mult(targets)`  0.75 when a move hits more than one Pokemon (Gen 5+), else 1. Singles: always 1.
- `redirect_target(user, target, d)` Follow Me / Rage Powder / Spotlight pull single-target moves to the centre of
                          attention. Singles: the foe is the only target anyway, so it returns the target unchanged.
- `turn_order_for(mon)`   After You / Quash / Instruct move a battler in this turn's order (`_order_override`).

Doubles are built (11-18): src/states/battle_double.py (DoubleBattleState) gives each side two slots and answers
these from them; a battle with options {"double": True} is one. Originally: to add doubles, give the battle a second slot per side (e.g. `player_slots = [a, b]`, `opponent_slots = [c, d]`),
make `battlers()` return them, and loop `_use_move` over `move_targets()` with `spread_mult()` in the damage. The
move code in battle_moves.py already calls these hooks; in singles they return the empty answers above, and the
moves say so in a short line where the games would ("But there's no one to help!") or stay quiet where they do.
"""

ALLY_TARGETS = ("ally",)
SELF_OR_ALLY = ("user-or-ally",)
SIDE_TARGETS = ("user-and-allies", "all-allies", "users-field")
FOE_SPREAD = ("all-opponents",)
ALL_SPREAD = ("all-other-pokemon", "all-pokemon")
NO_ALLY = "But there's no one to help!"     # (the games: "But it failed!" with no partner; our own words)


class DoublesSlots:
    is_doubles = False   # (a doubles battle sets True and fills the slots)

    def battlers(self, side):
        mon = self.player_pokemon if side == "player" else self.opponent_pokemon
        return [mon] if mon is not None else []

    def allies(self, mon):
        """The other Pokemon out on mon's side (none in a single battle)."""
        return [m for m in self.battlers(self.side_of(mon)) if m is not mon]

    def ally_of(self, mon):
        a = self.allies(mon)
        return a[0] if a else None

    def opponents_of(self, mon):
        return self.battlers("opponent" if self.side_of(mon) == "player" else "player")

    def move_targets(self, user, d, chosen=None):
        """Who the move hits. `chosen` is the picked target for single-target moves (the foe in singles)."""
        t = d.get("target") or "selected-pokemon"
        if t in ("user", "users-field", "entire-field", "opponents-field"):
            return [user]
        if t in ALLY_TARGETS:
            return self.allies(user)[:1]
        if t in SELF_OR_ALLY:
            return [chosen] if chosen is not None and chosen in self.allies(user) else [user]
        if t in SIDE_TARGETS:
            return [user] + self.allies(user)
        if t in FOE_SPREAD:
            return self.opponents_of(user)
        if t in ALL_SPREAD:
            others = self.opponents_of(user) + self.allies(user)
            return others + ([user] if t == "all-pokemon" else [])
        foes = self.opponents_of(user)
        return [chosen if chosen is not None else (foes[0] if foes else None)]

    @staticmethod
    def spread_mult(targets):
        return 0.75 if len([t for t in targets if t is not None]) > 1 else 1.0

    def redirect_target(self, user, target, d):
        """Follow Me / Rage Powder / Spotlight: in doubles a single-target move goes to the one that called
        attention to itself. With one Pokemon a side the target can't change."""
        if not self.is_doubles or d.get("target") != "selected-pokemon":
            return target
        for mon in self.opponents_of(user):
            if self.vol(mon).get("center_of_attention"):
                return mon
        return target

    def swap_allies(self, a, b):
        """Ally Switch: the two partners trade places (a double battle swaps their slots; singles never get here)."""

    def turn_order_for(self, mon):
        """After You (+1: next), Quash (-1: last) set in this turn's order; None: by Speed as usual."""
        return self.__dict__.get("_order_override", {}).get(id(mon))

    def action_for(self, mon):
        """The queued turn action that makes mon move (singles: player_attack / opponent_attack; a doubles battle
        returns each slot's own action here)."""
        if mon is None:
            return None
        if mon is self.player_pokemon:
            return self.player_attack
        if mon is self.opponent_pokemon:
            return self.opponent_attack
        return None

    def apply_turn_order(self, mon):
        """Move mon's queued action as turn_order_for says: next (After You) or after every other battler's
        (Quash). False if it has no action waiting."""
        order, act = self.turn_order_for(mon), self.action_for(mon)
        if order is None or act is None or act not in self.turn_actions:
            return False
        self.turn_actions.remove(act)
        if order > 0:
            self.turn_actions.insert(0, act)
            return True
        movers = [self.action_for(m) for side in ("player", "opponent") for m in self.battlers(side)]
        last = max([i for i, a in enumerate(self.turn_actions) if a in movers] + [-1])
        self.turn_actions.insert(last + 1, act)
        return True
