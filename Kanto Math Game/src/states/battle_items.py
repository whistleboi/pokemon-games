# [REF-0086: Held items in battle]
"""What held items do in battle, as in the games (Gen 4 on). The battle (src/states/battle.py) and its
effect mixins call these hooks:

  power / attack / defence / final damage: type boosters and Plates, Choice Band / Specs, Light Ball,
      Thick Club, Deep Sea Tooth / Scale, Metal Powder, Eviolite, Expert Belt, Metronome
  accuracy: Wide Lens (holder's moves), Bright Powder / Lax Incense (foe's moves at the holder)
  critical hits: the Stick (Farfetch'd: two stages)
  speed and order: Choice Scarf, Iron Ball, Macho Brace, Quick Powder, Quick Claw, Lagging Tail, Full Incense
  moves: Choice items lock the first move picked; Power Herb skips a charge turn; King's Rock / Razor Fang flinch
  after hits: Rocky Helmet, Shell Bell, Big Root (more back from draining)
  stats / conditions: White Herb, Mental Herb, Destiny Knot, Safety Goggles, Iron Ball (grounded), Smoke Ball
  end of turn: Leftovers
  berries: HP (Oran, Sitrus), conditions (Cheri, Chesto, Pecha, Rawst, Aspear, Persim, Lum), Leppa (PP),
      pinch berries (Liechi... Lansat, Starf) and the resist berries (Occa, Passho, Wacan...)

A Klutz holder's item does nothing. Used-up items (berries, herbs) leave the holder, and a player's
Pokemon's leave the Bag too (holding an item keeps the Bag's copy: src/states/systems/bag.py)."""
import random

from src.pokemon import items as itemlib

CHOICE = {"CHOICE_BAND": "ATTACK", "CHOICE_SPECS": "SPATK", "CHOICE_SCARF": "SPEED"}
SPECIES_ITEMS = {  # held item -> (species ids, stat, multiplier)
    "LIGHT_BALL": ({25}, ("ATTACK", "SPATK"), 2.0),
    "THICK_CLUB": ({104, 105}, ("ATTACK",), 2.0),
    "DEEP_SEA_TOOTH": ({366}, ("SPATK",), 2.0),
    "DEEP_SEA_SCALE": ({366}, ("SPDEF",), 2.0),
    "METAL_POWDER": ({132}, ("DEFENSE",), 2.0),
    "QUICK_POWDER": ({132}, ("SPEED",), 2.0),
}
CRIT_ITEMS = {"STICK": ({83, 865}, 2), "LUCKY_PUNCH": ({113}, 2), "SCOPE_LENS": (None, 1)}  # (11-18: the Scope Lens, any holder: Orange's Hamlin gift)   # (11-17: the Lucky Punch, Chansey's, FireRed's Sevault Canyon)   # held item -> (species ids, critical-hit stages): the Stick, Farfetch'd's (and Sirfetch'd's) own
SLOW_ITEMS = {"IRON_BALL", "MACHO_BRACE"}
LAST_ITEMS = {"LAGGING_TAIL", "FULL_INCENSE"}
FLINCH_ITEMS = {"KINGS_ROCK", "RAZOR_FANG"}
HP_BERRIES = {"ORAN_BERRY": 10, "SITRUS_BERRY": 0.25, "BERRY_JUICE": 20}
STATUS_BERRIES = {"CHERI_BERRY": ("paralysis",), "CHESTO_BERRY": ("sleep",), "PECHA_BERRY": ("poison", "toxic"),
                  "RAWST_BERRY": ("burn",), "ASPEAR_BERRY": ("freeze",)}
STAT_WORD = {"ATTACK": "Attack", "DEFENSE": "Defense", "SPATK": "Sp. Atk", "SPDEF": "Sp. Def", "SPEED": "Speed"}


class HeldItemEffects:
    # ------------------------------------------------------------------ the item
    def held(self, mon):
        """The item a battler holds that works now (None: nothing, a Klutz holder, or a used-up item it no longer has)."""
        item = getattr(mon, "held_item", None)
        if not item or self.ab(mon) == "KLUTZ" or self.vol(mon).get("embargo") or self.field().get("magic_room"):
            return None
        if itemlib.consumed(item) and self._player_owns(mon) and self.vol(mon).get("borrowed") != item:
            story = self.game.story_manager
            if story.inventory.get(item, 0) <= 0:  # (its copy was used from the Bag since)
                return None
        return item

    def _player_owns(self, mon):
        team = getattr(self.game.story_manager, "player_team", None) or []
        return any(p is mon for p in team)

    def consume_held(self, mon):
        """A used-up held item (a berry, an herb): gone from the holder (and, for yours, from the Bag)."""
        item = getattr(mon, "held_item", None)
        mon.held_item = None
        if item and hasattr(self, "_consumed"):
            self._consumed(mon, item)  # (Recycle can find it again; Belch counts a berry)
        if item and self._player_owns(mon) and self.vol(mon).pop("borrowed", None) != item:
            inv = self.game.story_manager.inventory
            inv[item] = inv.get(item, 0) - 1
            if inv[item] <= 0:
                inv.pop(item, None)
        return item

    def _item_name(self, item):
        from src.pokemon import forms
        return forms.item_label(item)

    # ------------------------------------------------------------------ damage
    def held_power_mult(self, attacker, defender, name, d):
        item, mult = self.held(attacker), 1.0
        t = d.get("type")
        if item in itemlib.HELD_BOOSTS and itemlib.HELD_BOOSTS[item] == str(t).upper():
            mult *= itemlib.HELD_BOOST
        if item and str(item).endswith("_GEM") and str(item)[:-4] == str(t).upper() and (d.get("power") or 0) > 0:   # (a Gem: once, then used up; 1.5x, as in Black 2 / White 2)
            mult *= 1.5
            self.consume_held(attacker)
        orb = itemlib.ORB_BOOSTS.get(item)
        if orb and int(getattr(attacker, "id", 0) or 0) == orb[0] and t in orb[1]:
            mult *= 1.2  # (Adamant, Lustrous, Griseous Orb)
        if item in itemlib.OGERPON_MASKS and int(getattr(attacker, "id", 0) or 0) == 1017:
            mult *= itemlib.MASK_BOOST  # (Ogerpon's masks: every move)
        if item == "METRONOME":  # the same move again and again: +20% a time, up to double
            chain = self.vol(attacker).get("metronome_chain")
            if chain and chain[0] == name:
                mult *= min(2.0, 1.0 + 0.2 * chain[1])
        return mult

    def held_attack_mult(self, attacker, special):
        item, mult = self.held(attacker), 1.0
        if item == ("CHOICE_SPECS" if special else "CHOICE_BAND"):
            mult *= 1.5
        mult *= self._species_item(attacker, "SPATK" if special else "ATTACK")
        return mult

    def held_defense_mult(self, defender, special):
        item, mult = self.held(defender), 1.0
        if item == "EVIOLITE":  # (held by one that can still evolve: both defences up by half)
            from src.pokemon.evolution import _descendants
            if _descendants(self.game, getattr(defender, "id", 0)):
                mult *= 1.5
        mult *= self._species_item(defender, "SPDEF" if special else "DEFENSE")
        return mult

    def _species_item(self, mon, stat):
        hit = SPECIES_ITEMS.get(self.held(mon))
        if hit and int(getattr(mon, "id", 0) or 0) in hit[0] and stat in hit[1]:
            if hit[0] == {132} and self.vol(mon).get("transformed"):
                return 1.0  # (Ditto's powders stop working once it transforms)
            return hit[2]
        return 1.0

    def held_final_mult(self, attacker, defender, eff):
        return 1.2 if eff > 1 and self.held(attacker) == "EXPERT_BELT" else 1.0

    def held_resist_berry(self, attacker, defender, d, eff):
        """A resist berry halves one hit: (True, lines) if it's eaten now."""
        item = self.held(defender)
        t = itemlib.RESIST_BERRIES.get(item)
        if not t or t != d.get("type") or attacker is defender or self._unnerved(defender):
            return False, []
        if t != "NORMAL" and eff <= 1:
            return False, []
        self.consume_held(defender)
        return True, [f"{self._label(defender)} ate its {self._item_name(item)}! It weakened the hit."]

    def held_move_type(self, attacker, name, d):
        """Judgment takes its Plate's type, Techno Blast its Drive's (as in the games)."""
        item = self.held(attacker)
        if name == "JUDGMENT" and item in itemlib.PLATE_TYPES:
            return dict(d, type=itemlib.PLATE_TYPES[item])
        if name == "TECHNO-BLAST" and item in itemlib.DRIVES:
            return dict(d, type=itemlib.DRIVES[item])
        return d

    def held_crit(self, attacker):
        """Critical-hit stages from the holder's item (the Stick: +2, only for Farfetch'd and Sirfetch'd)."""
        from src.pokemon.evolution import base_id
        ids, stages = CRIT_ITEMS.get(self.held(attacker), ((), 0))
        return stages if stages and (ids is None or getattr(attacker, "id", None) in ids or base_id(attacker) in ids) else 0

    def held_acc_mult(self, attacker, defender):
        mult = 1.1 if self.held(attacker) == "WIDE_LENS" else 1.0
        if self.held(defender) in ("BRIGHT_POWDER", "LAX_INCENSE"):
            mult *= 0.9
        return mult

    # ------------------------------------------------------------------ speed and order
    def held_speed_mult(self, mon):
        item, mult = self.held(mon), 1.0
        if item == "CHOICE_SCARF":
            mult *= 1.5
        if item in SLOW_ITEMS:
            mult *= 0.5
        return mult * self._species_item(mon, "SPEED")

    def held_order(self, mon):
        """+1: a Quick Claw lets it go first in its priority bracket this turn; -1: it goes last; 0: Speed decides."""
        item = self.held(mon)
        if item == "QUICK_CLAW" and random.random() < 0.2:
            return 1
        return -1 if item in LAST_ITEMS else 0

    # ------------------------------------------------------------------ moves
    def held_choice_lock(self, mon):
        """The move a Choice item has locked it into (None: free to pick)."""
        if self.held(mon) not in CHOICE:
            return None
        return self.vol(mon).get("choice_lock")

    def held_after_pick(self, mon, name):
        """After a move is picked: the Choice lock and the Metronome count."""
        from src.pokemon import moves as movelib
        if name == movelib.STRUGGLE:
            return
        v = self.vol(mon)
        if self.held(mon) in CHOICE and not v.get("choice_lock"):
            v["choice_lock"] = name
        chain = v.get("metronome_chain")
        v["metronome_chain"] = (name, chain[1] + 1) if chain and chain[0] == name else (name, 0)

    def held_skips_charge(self, mon):
        """A Power Herb: the two-turn move goes at once (used up). Returns lines, or None."""
        if self.held(mon) != "POWER_HERB":
            return None
        self.consume_held(mon)
        return [f"{self._label(mon)} became fully charged due to its Power Herb!"]

    def held_flinch(self, attacker, chance):
        """King's Rock / Razor Fang: a 10% flinch for attacks that can't already make the foe flinch."""
        if not chance and self.held(attacker) in FLINCH_ITEMS:
            return 10
        return chance

    # ------------------------------------------------------------------ after a hit
    def held_after_hit(self, attacker, defender, name, damage, defender_hp):
        """Rocky Helmet and Shell Bell. Returns lines."""
        lines = []
        if not damage or attacker is defender:
            return lines
        if self.held(defender) == "ROCKY_HELMET" and "contact" in self._flags(name) and self._hp(attacker) > 0 \
                and self.ab(attacker) != "MAGICGUARD":
            self._adjust_hp(attacker, -max(1, self._max_hp(attacker) // 6))
            lines.append(f"{self._label(attacker)} was hurt by the Rocky Helmet!")
        if self.held(defender) == "STICKY_BARB" and "contact" in self._flags(name) and self._hp(attacker) > 0                 and not getattr(attacker, "held_item", None) and hasattr(self, "_get_item"):   # (it clings to whoever touches it;
            self._lose_item(defender)                                                         #  B2W2: Route 20's autumn Barb, 11-20)
            self._get_item(attacker, "STICKY_BARB")
            lines.append(f"The Sticky Barb stuck to {self._label(attacker)}!")
        if self.held(attacker) == "SHELL_BELL" and self._hp(attacker) > 0:  # (an eighth of the damage back)
            self._adjust_hp(attacker, max(1, min(damage, defender_hp) // 8))
            lines.append(f"{self._label(attacker)} restored a little HP using its Shell Bell!")
        return lines

    def held_drain_mult(self, mon):
        return 1.3 if self.held(mon) == "BIG_ROOT" else 1.0

    def held_endures(self, defender):
        """A Focus Band: now and then it hangs on at 1 HP."""
        return self.held(defender) == "FOCUS_BAND" and random.random() < 0.1

    # ------------------------------------------------------------------ conditions and stats
    def held_grounded(self, mon):
        return self.held(mon) == "IRON_BALL"

    def held_powder_proof(self, mon):
        return self.held(mon) == "SAFETY_GOGGLES"

    def held_weather_proof(self, mon):
        return self.held(mon) == "SAFETY_GOGGLES"

    def held_after_stat_drop(self, mon):
        """A White Herb puts lowered stats back (used up). Returns lines."""
        if self.held(mon) != "WHITE_HERB":
            return []
        st = self.stages(mon)
        low = [k for k, n in st.items() if n < 0]
        if not low:
            return []
        for k in low:
            st[k] = 0
        self.consume_held(mon)
        return [f"{self._label(mon)} returned its stats to normal using its White Herb!"]

    def held_mental_herb(self, mon):
        """A Mental Herb frees its holder from love, Taunt, Encore and Disable (used up). Returns lines."""
        v = self.vol(mon)
        mind = [k for k in ("infatuated", "taunt", "encore", "disabled") if v.get(k)]
        if not mind or self.held(mon) != "MENTAL_HERB":
            return []
        for k in mind:
            v.pop(k, None)
        self.consume_held(mon)
        return [f"{self._label(mon)} used its Mental Herb to snap out of it!"]

    def held_destiny_knot(self, holder, source):
        """The holder fell in love: with a Destiny Knot, the one it loves does too. Returns lines."""
        if self.held(holder) != "DESTINY_KNOT" or source is None or source is holder:
            return []
        sv = self.vol(source)
        if sv.get("infatuated") or self.ability_status_immune(source, "infatuation"):
            return []
        sv["infatuated"] = True
        return [f"{self._label(source)} fell in love from the Destiny Knot!"]

    def held_escape(self, mon):
        return self.held(mon) == "SMOKE_BALL"

    # ------------------------------------------------------------------ berries and PP
    def _unnerved(self, mon):
        foe = self._foe_of(mon)
        return foe is not None and self.ab(foe) in ("UNNERVE", "ASONEGLASTRIER", "ASONESPECTRIER")

    def held_pp_empty(self, mon, move):
        """A held Leppa Berry: a move that runs out of PP gets 10 back. Returns lines."""
        if self.held(mon) != "LEPPA_BERRY" or self._unnerved(mon):
            return []
        from src.pokemon import pp as pplib
        pplib.restore(self.game, mon, move, 10)
        self.consume_held(mon)
        return [f"{self._label(mon)} restored {move.replace('-', ' ')}'s PP using its Leppa Berry!"]

    def held_berry_check(self, mon):
        """A held berry whose moment has come is eaten: HP, a condition, confusion, a pinch. Returns lines."""
        item = self.held(mon)
        if not item or not str(item).endswith(("_BERRY", "_JUICE")) or mon is None or self._hp(mon) <= 0 \
                or self._unnerved(mon):
            return []
        label, hp, mx = self._label(mon), self._hp(mon), self._max_hp(mon)
        name = self._item_name(item)
        gluttony = self.ab(mon) == "GLUTTONY"
        if item in HP_BERRIES and hp * 2 <= mx:
            amt = HP_BERRIES[item]
            gain = max(1, int(mx * amt)) if isinstance(amt, float) else amt
            self._adjust_hp(mon, gain)
            self.consume_held(mon)
            return [f"{label} restored its health using its {name}!"]
        status = getattr(mon, "status", None)
        cures = STATUS_BERRIES.get(item, ())
        if status and (status in cures or item == "LUM_BERRY"):
            mon.cure_status()
            self.consume_held(mon)
            return [f"{label}'s {name} cured its {itemlib._status_word(status)}!"]
        v = self.vol(mon)
        if v.get("confused") and item in ("PERSIM_BERRY", "LUM_BERRY"):
            v.pop("confused", None)
            self.consume_held(mon)
            return [f"{label}'s {name} snapped it out of its confusion!"]
        pinch = itemlib.PINCH_BERRIES.get(item)
        if pinch and hp * (2 if gluttony else 4) <= mx:
            self.consume_held(mon)
            if pinch == "focus":
                v["focus"] = max(v.get("focus", 0), 2)
                return [f"{label} used its {name} to get pumped!"]
            if pinch == "random":
                options = [s for s in STAT_WORD if self.stages(mon).get(s, 0) < 6]
                if not options:
                    return [f"{label} ate its {name}!"]
                return [f"{label} ate its {name}!"] + self.change_stages(mon, [[random.choice(options), 2]])
            return [f"{label} ate its {name}!"] + self.change_stages(mon, [[pinch, 1]])
        return []

    def held_after_action(self):
        """After every move (and the end of the turn): both battlers' berries. Returns lines."""
        lines = []
        for mon in (getattr(self, "player_pokemon", None), getattr(self, "opponent_pokemon", None)):
            if mon is not None:
                lines += self.held_berry_check(mon)
        return lines

    def held_end_of_turn(self, mon):
        """Leftovers: a sixteenth of its HP back, while it's standing and hurt. A Flame Orb / Toxic Orb burns /
        badly poisons its holder. Returns lines."""
        orb = {"FLAME_ORB": "burn", "TOXIC_ORB": "toxic"}.get(self.held(mon))
        if orb and self._hp(mon) > 0 and self._can_inflict(orb, mon):
            return [self._inflict(orb, mon, self._label(mon))]
        if self.held(mon) == "STICKY_BARB" and self._hp(mon) > 0 and self.ab(mon) != "MAGICGUARD":   # (an eighth a turn)
            self._adjust_hp(mon, -max(1, self._max_hp(mon) // 8))
            return [f"{self._label(mon)} was hurt by its Sticky Barb!"]
        if self.held(mon) == "BLACK_SLUDGE" and self._hp(mon) > 0:   # (a Poison type heals as with Leftovers; any other loses an eighth)
            if "POISON" in [str(x).upper() for x in (mon.types or [])]:
                if self._hp(mon) >= self._max_hp(mon):
                    return []
                self._adjust_hp(mon, max(1, self._max_hp(mon) // 16))
                return [f"{self._label(mon)} restored a little HP using its Black Sludge!"]
            if self.ab(mon) == "MAGICGUARD":
                return []
            self._adjust_hp(mon, -max(1, self._max_hp(mon) // 8))
            return [f"{self._label(mon)} was hurt by its Black Sludge!"]
        if self.held(mon) != "LEFTOVERS":
            return []
        hp, mx = self._hp(mon), self._max_hp(mon)
        if hp <= 0 or hp >= mx:
            return []
        self._adjust_hp(mon, max(1, mx // 16))
        return [f"{self._label(mon)} restored a little HP using its Leftovers!"]
