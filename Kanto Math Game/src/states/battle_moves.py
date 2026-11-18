# [REF-0094: Every move's own mechanics]
"""The moves whose effect is more than "power, type, an added effect" (Jordan, 11-17: "Make all moves work").

A mixin for TrainerBattleState (src/states/battle.py), beside MoveEffects (battle_effects.py: stat stages,
conditions, screens, hazards, the plain status moves). `_use_move` in battle.py calls these hooks in order:

  mv_prepare      the move as it is used now: variable power (Gyro Ball, Reversal, Return, Stored Power, Hex,
                  Facade, Knock Off...), its type (Weather Ball, Hidden Power, Natural Gift, Tera Blast...),
                  per-hit powers (Triple Axel), fixed damage (Counter, Endeavor, Psywave, Bide, Final Gambit)
  mv_blocked      Torment, Heal Block, Throat Chop, Gravity, Gigaton Hammer twice, Belch, Last Resort...
  mv_charge       charge-turn effects (Skull Bash, Meteor Beam, Electro Shot, Sky Drop's lift)
  mv_fails        "But it failed!" cases (Sucker Punch, Dream Eater, Poltergeist, Focus Punch, Upper Hand...) and
                  the moves that act later (Future Sight, Bide's storing)
  mv_protect      Protect and its kin (King's Shield, Spiky Shield, Baneful Bunker, Obstruct, Silk Trap, Burning
                  Bulwark), the guards (Quick / Wide Guard, Crafty Shield), moves that go through (Feint...)
  mv_sure_hit     Lock-On, Telekinesis, Glaive Rush, Minimize, Thunder / Hurricane in rain, Blizzard in snow...
  mv_status       the status moves with a mechanic of their own (Baton Pass, Trick, Sleep Talk, Transform...)
  mv_before_hit / mv_hit_mult / mv_after_damage   screens broken, final multipliers, item theft, switching...
  mv_end_move     what the battle remembers (last move, a failure for Stomping Tantrum, Rollout's chain...)
  mv_note_hit     damage taken (Counter, Revenge, Assurance, Rage, Destiny Bond, Bide, Rage Fist...)
  mv_end_of_turn  Future Sight landing, Nightmare, Salt Cure, Syrup Bomb, Octolock, the timers
  mv_battle_end   types, items and Transform back as they were; Pay Day's coins

Doubles-only parts go through battle_doubles.py (allies, targets): with one Pokemon a side they have no effect.
Switching in the middle of a turn (U-turn, Baton Pass, Roar in a trainer battle) is in battle.py
(_run_pending_switch). _queue_pending_switch runs after each side's action: Shell Trap jumping ahead when hit,
Revival Blessing's choice list, a foe's Pursuit catching a Pokemon that leaves by its own move, and a U-turn
user switching after a KO (`_pivot_after_ko`, picked up where battle.py ends a faint)."""
import math
import random

from src.pokemon import items as itemlib
from src.pokemon import moves as movelib
from src.states.battle_doubles import NO_ALLY

FAIL = "But it failed!"
STELLAR = "STELLAR"   # (Terapagos's Tera type: not in the type chart, so neutral on every type)
TERAPAGOS, OGERPON, TAUROS = 1024, 1017, 128
PIVOT_HIT = {"U-TURN", "VOLT-SWITCH", "FLIP-TURN"}
FORCE_HIT = {"DRAGON-TAIL", "CIRCLE-THROW"}
CRASH = {"HIGH-JUMP-KICK", "JUMP-KICK", "AXE-KICK", "SUPERCELL-SLAM"}
HALF_HP_COST = {"STEEL-BEAM", "MIND-BLOWN", "CHLOROBLAST"}
SCREEN_BREAK = {"BRICK-BREAK", "PSYCHIC-FANGS", "RAGING-BULL"}
PROTECT_BYPASS = {"FEINT", "HYPER-DRILL", "MIGHTY-CLEAVE", "PHANTOM-FORCE", "SHADOW-FORCE", "HYPERSPACE-HOLE",
                  "HYPERSPACE-FURY"}
PROTECT_BREAK = {"FEINT", "PHANTOM-FORCE", "SHADOW-FORCE", "HYPERSPACE-HOLE", "HYPERSPACE-FURY"}
SLEEP_MOVES = {"SNORE", "SLEEP-TALK"}
IGNORE_DEF_STAGES = {"CHIP-AWAY", "SACRED-SWORD", "DARKEST-LARIAT"}
TARGET_DEFENSE = {"PSYSHOCK", "PSYSTRIKE", "SECRET-SWORD"}
NO_REPEAT = {"GIGATON-HAMMER", "BLOOD-MOON"}
GRAVITY_BANNED = {"FLY", "BOUNCE", "SKY-DROP", "HIGH-JUMP-KICK", "JUMP-KICK", "SPLASH", "MAGNET-RISE", "TELEKINESIS",
                  "FLYING-PRESS", "FLOATY-FALL"}
MINIMIZE_PUNISH = {"STOMP", "BODY-SLAM", "DRAGON-RUSH", "HEAT-CRASH", "HEAVY-SLAM", "FLYING-PRESS", "STEAMROLLER",
                   "PHANTOM-FORCE", "SHADOW-FORCE", "MALICIOUS-MOONSAULT", "SUPERCELL-SLAM", "DOUBLE-IRON-BASH"}
STORM_RAIN = {"THUNDER", "HURRICANE", "BLEAKWIND-STORM", "WILDBOLT-STORM", "SANDSEAR-STORM", "SPRINGTIDE-STORM"}
RAMPAGE_EXTRA = {"RAGING-FURY"}
PLEDGES = {"FIRE-PLEDGE", "WATER-PLEDGE", "GRASS-PLEDGE"}
# Moves Sleep Talk, Metronome, Copycat, Assist and the other move-callers can't call (as in the games).
NOT_CALLED = {"SLEEP-TALK", "ASSIST", "COPYCAT", "METRONOME", "MIRROR-MOVE", "ME-FIRST", "NATURE-POWER", "MIMIC",
              "SKETCH", "SNATCH", "INSTRUCT", "BIDE", "FOCUS-PUNCH", "UPROAR", "BEAK-BLAST", "SHELL-TRAP", "STRUGGLE",
              "TRANSFORM", "COUNTER", "MIRROR-COAT", "METAL-BURST", "COMEUPPANCE", "PROTECT", "DETECT", "ENDURE",
              "KINGS-SHIELD", "SPIKY-SHIELD", "BANEFUL-BUNKER", "OBSTRUCT", "SILK-TRAP", "BURNING-BULWARK",
              "DESTINY-BOND", "FOLLOW-ME", "RAGE-POWDER", "SPOTLIGHT", "HELPING-HAND", "FEINT", "THIEF", "COVET",
              "TRICK", "SWITCHEROO", "CHATTER", "SKY-DROP", "DYNAMAX-CANNON", "CELEBRATE", "HOLD-HANDS"}
SLEEP_TALK_SKIPS = NOT_CALLED | set(movelib.TWO_TURN) | {"SOLAR-BEAM", "SOLAR-BLADE"}
# Status moves Snatch steals and Magic Coat bounces back.
NOT_SNATCHED = {"PSYCH-UP", "ACUPRESSURE", "SNATCH", "BATON-PASS", "SHED-TAIL", "TELEPORT", "TRANSFORM", "REST",
                "SUBSTITUTE", "METRONOME", "SLEEP-TALK", "SPLASH", "CELEBRATE", "STOCKPILE", "SWALLOW", "COPYCAT"}
NOT_BOUNCED = {"TRANSFORM", "SKETCH", "PSYCH-UP", "CURSE", "PERISH-SONG", "ROLE-PLAY", "IMPRISON", "MIMIC", "SPITE",
               "INSTRUCT", "QUASH", "AFTER-YOU", "ME-FIRST", "SNATCH", "PAIN-SPLIT", "HEAL-PULSE", "FLORAL-HEALING",
               "PURIFY", "DECORATE", "DOODLE", "ACUPRESSURE", "HELPING-HAND", "COACHING", "AROMATIC-MIST"}
BATON_VOL = ("substitute", "confused", "focus", "seeded", "cursed", "ingrain", "aqua_ring", "no_escape", "perish",
             "magnet_rise", "embargo", "heal_block", "telekinesis", "lock_on", "stat_over", "ability_lost")
EXTRA_SOUND = {"ALLURING-VOICE", "PSYCHIC-NOISE", "TORCH-SONG", "CLANGOROUS-SOUL", "CLANGING-SCALES", "OVERDRIVE",
               "SPARKLING-ARIA", "EERIE-SPELL", "BOOMBURST", "RELIC-SONG", "DISARMING-VOICE"}
HP_TYPES = ("FIGHTING", "FLYING", "POISON", "GROUND", "ROCK", "BUG", "GHOST", "STEEL", "FIRE", "WATER", "GRASS",
            "ELECTRIC", "PSYCHIC", "ICE", "DRAGON", "DARK")
# Natural Gift: each berry's type and power (Gen 6 on).
_NG = {80: {"CHERI": "FIRE", "CHESTO": "WATER", "PECHA": "ELECTRIC", "RAWST": "GRASS", "ASPEAR": "ICE",
            "LEPPA": "FIGHTING", "ORAN": "POISON", "PERSIM": "GROUND", "LUM": "FLYING", "SITRUS": "PSYCHIC",
            "FIGY": "BUG", "WIKI": "ROCK", "MAGO": "GHOST", "AGUAV": "DRAGON", "IAPAPA": "DARK", "RAZZ": "STEEL",
            "OCCA": "FIRE", "PASSHO": "WATER", "WACAN": "ELECTRIC", "RINDO": "GRASS", "YACHE": "ICE",
            "CHOPLE": "FIGHTING", "KEBIA": "POISON", "SHUCA": "GROUND", "COBA": "FLYING", "PAYAPA": "PSYCHIC",
            "TANGA": "BUG", "CHARTI": "ROCK", "KASIB": "GHOST", "HABAN": "DRAGON", "COLBUR": "DARK", "BABIRI": "STEEL",
            "CHILAN": "NORMAL", "ROSELI": "FAIRY", "BLUK": "FIRE", "NANAB": "WATER", "WEPEAR": "ELECTRIC",
            "PINAP": "GRASS"},
       90: {"POMEG": "ICE", "KELPSY": "FIGHTING", "QUALOT": "POISON", "HONDEW": "GROUND", "GREPA": "FLYING",
            "TAMATO": "PSYCHIC", "CORNN": "BUG", "MAGOST": "ROCK", "RABUTA": "GHOST", "NOMEL": "DRAGON",
            "SPELON": "DARK", "PAMTRE": "STEEL", "WATMEL": "FIRE", "DURIN": "WATER", "BELUE": "ELECTRIC"},
       100: {"LIECHI": "GRASS", "GANLON": "ICE", "SALAC": "FIGHTING", "PETAYA": "POISON", "APICOT": "GROUND",
             "LANSAT": "FLYING", "STARF": "PSYCHIC", "ENIGMA": "BUG", "MICLE": "ROCK", "CUSTAP": "GHOST",
             "JABOCA": "DRAGON", "ROWAP": "DARK", "KEE": "FAIRY", "MARANGA": "DARK"}}
NATURAL_GIFT = {f"{b}_BERRY": (t, p) for p, berries in _NG.items() for b, t in berries.items()}
# Fling: power by item (the games' table; an item not listed flies at 30, a berry at 10). Some do more on landing.
FLING_POWER = {"IRON_BALL": 130, "HARD_STONE": 100, "DEEP_SEA_TOOTH": 90, "THICK_CLUB": 90, "QUICK_CLAW": 80,
               "SAFETY_GOGGLES": 80, "POISON_BARB": 70, "DRAGON_FANG": 70, "ROCKY_HELMET": 60, "STICK": 60,
               "MACHO_BRACE": 60, "HEAT_ROCK": 60, "DAMP_ROCK": 60, "SMOOTH_ROCK": 60, "SHARP_BEAK": 50,
               "ICY_ROCK": 40, "EVIOLITE": 40, "LUCKY_PUNCH": 40, "CHOICE_BAND": 10, "CHOICE_SCARF": 10,
               "CHOICE_SPECS": 10, "LEFTOVERS": 10, "BIG_ROOT": 10, "EXPERT_BELT": 10, "FOCUS_BAND": 10,
               "LAGGING_TAIL": 10, "SILK_SCARF": 10, "SILVER_POWDER": 10, "SOFT_SAND": 10, "WIDE_LENS": 10,
               "WHITE_HERB": 10, "MENTAL_HERB": 10, "POWER_HERB": 10, "BRIGHT_POWDER": 10, "SOOTHE_BELL": 10,
               "DESTINY_KNOT": 10, "METAL_POWDER": 10, "QUICK_POWDER": 10, "FULL_INCENSE": 10, "LAX_INCENSE": 10,
               "ODD_INCENSE": 10, "PURE_INCENSE": 10, "ROCK_INCENSE": 10, "ROSE_INCENSE": 10, "SEA_INCENSE": 10,
               "WAVE_INCENSE": 10, "FLOAT_STONE": 30, "FLAME_ORB": 30, "TOXIC_ORB": 30, "KINGS_ROCK": 30,
               "RAZOR_FANG": 30, "LIGHT_BALL": 30}
FLING_EFFECT = {"FLAME_ORB": "burn", "TOXIC_ORB": "toxic", "LIGHT_BALL": "paralysis", "POISON_BARB": "poison",
                "KINGS_ROCK": "flinch", "RAZOR_FANG": "flinch"}
# Nature Power: the move it becomes, by terrain, else by where you battle (Gen 7 on; Tri Attack anywhere else).
NATURE_TERRAIN = {"electric": "THUNDERBOLT", "grassy": "ENERGY-BALL", "misty": "MOONBLAST", "psychic": "PSYCHIC"}
NATURE_PLACE = {"grass": "ENERGY-BALL", "forest": "ENERGY-BALL", "route": "ENERGY-BALL", "water": "HYDRO-PUMP",
                "sea": "HYDRO-PUMP", "ocean": "HYDRO-PUMP", "beach": "EARTH-POWER", "sand": "EARTH-POWER",
                "desert": "EARTH-POWER", "cave": "POWER-GEM", "rock": "POWER-GEM", "snow": "ICE-BEAM",
                "ice": "ICE-BEAM", "volcano": "FLAMETHROWER", "swamp": "MUD-BOMB", "space": "DRACO-METEOR"}
PRESENT_ROLLS = ((0.4, 40), (0.3, 80), (0.1, 120))   # (the other 20%: it heals the foe a quarter)
MAGNITUDE = ((5, 4, 10), (10, 5, 30), (20, 6, 50), (30, 7, 70), (20, 8, 90), (10, 9, 110), (5, 10, 150))
NO_TRANSFORM_ITEM_MOVES = {"FLING", "NATURAL-GIFT"}
LOCKED_TYPES = {493, 773}   # (Arceus, Silvally: types can't be changed by Soak and the like)


def _nice(name):
    return str(name).replace("-", " ")


class MoveMechanics:
    # ================================================================== records
    def _mv(self):
        return self.__dict__.setdefault("_mv_state", {
            "took": {}, "moved": set(), "picked": {}, "future": {}, "fainted_turn": {"player": -9, "opponent": -9},
            "types0": {}, "items0": {}, "transform": {}, "hits_taken": {}, "money": 0, "echo": [-9, 0],
            "last_any": None, "been_out": set(), "pending": [], "ate_berry": set(), "lost_item": {},
            "rage_fist": {}, "order": {}})

    def mv_turn_start(self, picks):
        """A new turn: forget last turn's hits and one-turn guards; note what each side picked. Returns lines
        (Focus Punch tightening, Beak Blast heating up, Shell Trap set)."""
        m = self._mv()
        m["took"], m["moved"], m["picked"] = {}, set(), dict(picks)
        m["pending"].clear()   # (a switch the last turn never got to: its Pokemon fainted first)
        for k in ("_order_override", "_pivot_after_ko", "_revive_pick", "_pivot_then_next_foe"):
            self.__dict__.pop(k, None)
        self.field().pop("ion_deluge", None)
        lines = []
        for mon in (self.player_pokemon, self.opponent_pokemon):
            if mon is None:
                continue
            v = self.vol(mon)
            for k in ("magic_coat", "snatch", "center_of_attention", "helping_hand", "electrified", "beak_blast",
                      "shell_trap", "focus_punch", "raised_turn", "lowered_turn"):
                v.pop(k, None)
            for k in ("quick_guard", "wide_guard", "crafty_shield"):
                self.side(mon).pop(k, None)
            pick = picks.get(id(mon))
            if pick == "FOCUS-PUNCH":
                v["focus_punch"] = True
                lines.append(f"{self._label(mon)} is tightening its focus!")
            elif pick == "BEAK-BLAST":
                v["beak_blast"] = True
                lines.append(f"{self._label(mon)} started heating up its beak!")
            elif pick == "SHELL-TRAP":
                v["shell_trap"] = True
                lines.append(f"{self._label(mon)} set a shell trap!")
            if v.get("roost_types"):   # (Roost: its Flying type comes back after the turn it landed)
                self._restore_types(mon)
                v.pop("roost_types", None)
        return lines

    def mv_priority(self, mon, d):
        """Priority changes from the situation: Grassy Glide in Grassy Terrain."""
        if d.get("name") == "GRASSY-GLIDE" and self.terrain() == "grassy" and self.grounded(mon):
            return 1
        return 0

    # ================================================================== types, items, stats for the battle
    def _set_types(self, mon, types):
        t0 = self._mv()["types0"]
        if id(mon) not in t0:
            t0[id(mon)] = (mon, list(mon.types or []))
        mon.types = list(types)

    def _restore_types(self, mon):
        rec = self._mv()["types0"].pop(id(mon), None)
        if rec:
            mon.types = rec[1]

    def _bstat(self, mon, stat):
        """A stat for the damage formula: Power Trick / Power Split / Guard Split's numbers, else its own."""
        over = self.vol(mon).get("stat_over") or {}
        return over.get(stat) or mon.stat_value(stat)

    def _note_item(self, mon):
        """Remember a battler's item before a move changes it (it comes back after the battle: Knock Off, Thief,
        Trick in a trainer battle; as in the games from Gen 5 on)."""
        i0 = self._mv()["items0"]
        if id(mon) not in i0:
            i0[id(mon)] = (mon, getattr(mon, "held_item", None))

    def _item_of(self, mon):
        """The item it holds (even one that does nothing now, as Knock Off sees it)."""
        return getattr(mon, "held_item", None)

    def _lose_item(self, mon):
        """It no longer holds its item for this battle (Knock Off, Incinerate, stolen). Returns the item."""
        item = self._item_of(mon)
        if item:
            self._note_item(mon)
            mon.held_item = None
            self.vol(mon).pop("borrowed", None)
        return item

    def _get_item(self, mon, item, keep=False):
        """mon now holds item. keep: for good (a wild Pokemon's item taken by your Pokemon goes in the Bag)."""
        self._note_item(mon)
        mon.held_item = item
        if self._player_owns(mon):
            if keep:
                inv = self.game.story_manager.inventory
                inv[item] = inv.get(item, 0) + 1
                self._mv()["items0"].pop(id(mon), None)   # (it stays held after the battle)
            else:
                self.vol(mon)["borrowed"] = item

    def _consumed(self, mon, item):
        """mon used up item (eaten, flung): Recycle can bring it back; Belch counts a berry."""
        self._mv()["lost_item"][id(mon)] = item
        if str(item).endswith("_BERRY"):
            self._mv()["ate_berry"].add(id(mon))

    def _eat_berry_now(self, mon, berry):
        """mon eats a berry at once, whatever its HP (Bug Bite, Pluck, Teatime, Stuff Cheeks, a flung berry).
        Returns lines."""
        from src.states.battle_items import HP_BERRIES, STATUS_BERRIES
        from src.pokemon import items as itemlib
        label, mx, lines = self._label(mon), self._max_hp(mon), []
        self._mv()["ate_berry"].add(id(mon))
        if berry in HP_BERRIES:
            amt = HP_BERRIES[berry]
            if self._hp(mon) < mx:
                self._adjust_hp(mon, max(1, int(mx * amt)) if isinstance(amt, float) else amt)
                lines.append(f"{label} restored its health!")
        status = getattr(mon, "status", None)
        if status and (status in STATUS_BERRIES.get(berry, ()) or berry == "LUM_BERRY"):
            mon.cure_status()
            lines.append(f"{label}'s status returned to normal!")
        if berry in ("PERSIM_BERRY", "LUM_BERRY") and self.vol(mon).pop("confused", None):
            lines.append(f"{label} snapped out of its confusion!")
        pinch = itemlib.PINCH_BERRIES.get(berry)
        if pinch == "focus":
            self.vol(mon)["focus"] = 2
            lines.append(f"{label} is getting pumped!")
        elif pinch == "random":
            stats = [s for s in ("ATTACK", "DEFENSE", "SPATK", "SPDEF", "SPEED") if self.stages(mon)[s] < 6]
            if stats:
                lines += self.change_stages(mon, [[random.choice(stats), 2]])
        elif pinch:
            lines += self.change_stages(mon, [[pinch, 1]])
        if berry == "LEPPA_BERRY":
            from src.pokemon import pp as pplib
            low = [m for m in (getattr(mon, "moves", None) or []) if pplib.left(self.game, mon, m) < pplib.max_pp(self.game, mon, m)]
            if low:
                pplib.restore(self.game, mon, min(low, key=lambda m: pplib.left(self.game, mon, m)), 10)
                lines.append(f"{label} restored PP using its berry!")
        return lines

    # ================================================================== the move as used now
    def _friendship(self, mon):
        if not self._player_owns(mon):
            return 255   # (trainers' and wild Pokemon: Return at full power, as their moves were set)
        return max(0, min(255, int(getattr(mon, "friendship", 0) or 0)))

    def _positive_stages(self, mon):
        return sum(n for k, n in self.stages(mon).items() if n > 0)

    def _hidden_power_type(self, mon):
        bits = [mon.iv(s) % 2 for s in ("HP", "ATTACK", "DEFENSE", "SPEED", "SPATK", "SPDEF")]
        return HP_TYPES[sum(b << i for i, b in enumerate(bits)) * 15 // 63]

    def _took_from(self, mon, other=None, category=None):
        """Damage mon took this turn (from `other`, of a category), most recent last."""
        out = []
        for dmg, cat, who in self._mv()["took"].get(id(mon), []):
            if (other is None or who == id(other)) and (category is None or cat == category):
                out.append(dmg)
        return out

    def _moved(self, mon):
        return id(mon) in self._mv()["moved"]

    def _party(self, mon):
        if self._player_owns(mon) or mon is self.player_pokemon:
            return [p for p in self.game.story_manager.player_team if p]
        return [p for p in (self.opponent_team or []) if p]

    def mv_prepare(self, attacker, defender, name, d, preview=False):
        """The move as it's used now (a copy of d). preview: for the FIGHT menu and the foe's choice (no dice, no
        side effects)."""
        d = dict(d)
        v, fv = self.vol(attacker), self.vol(defender) if defender is not None else {}
        hp, mx = self._hp(attacker), max(1, self._max_hp(attacker))
        power = d.get("power") or 0
        t = d.get("type")
        boost = self.__dict__.pop("_mv_call_boost", None) if not preview else None
        # ---- type
        if name == "WEATHER-BALL":
            w = self.weather_now()
            wt = {"RAIN": "WATER", "HEAVY_RAIN": "WATER", "SUN": "FIRE", "HARSH_SUN": "FIRE", "SAND": "ROCK",
                  "SNOW": "ICE"}.get(w)
            if wt:
                t, power = wt, 100
        elif name == "TERRAIN-PULSE" and self.terrain() and self.grounded(attacker):
            t, power = {"electric": "ELECTRIC", "grassy": "GRASS", "misty": "FAIRY", "psychic": "PSYCHIC"}[self.terrain()], 100
        elif name == "HIDDEN-POWER":
            t = self._hidden_power_type(attacker)
        elif name == "REVELATION-DANCE":
            t = (attacker.types or ["NORMAL"])[0]
        elif name in ("TERA-BLAST", "TERA-STARSTORM") and getattr(attacker, "_tera_types", None):
            # (Terastallized Terapagos is Stellar: Stellar type, neutral on everything, double on a
            # Terastallized target; Tera Starstorm then hits every foe)
            t = STELLAR if getattr(attacker, "_stellar", False) else (attacker.types or ["NORMAL"])[0]
            if self._bstat(attacker, "ATTACK") * self.stat_mult(attacker, "ATTACK") > \
                    self._bstat(attacker, "SPATK") * self.stat_mult(attacker, "SPATK"):
                d["category"] = "PHYSICAL"
        elif name == "SHELL-SIDE-ARM" and defender is not None:
            phys = self._bstat(attacker, "ATTACK") / max(1, self._bstat(defender, "DEFENSE"))
            spec = self._bstat(attacker, "SPATK") / max(1, self._bstat(defender, "SPDEF"))
            if phys > spec:
                d["category"] = "PHYSICAL"
        elif name == "IVY-CUDGEL":   # (the mask's type; the Teal Mask, no item here, keeps it Grass)
            t = itemlib.OGERPON_MASKS.get(self.held(attacker), t)
        elif name == "RAGING-BULL":
            t = self._paldean_breed_type(attacker) or t
        elif name == "AURA-WHEEL" and v.get("hangry"):
            t = "DARK"
        elif name == "NATURAL-GIFT":
            berry = self.held(attacker)
            if berry in NATURAL_GIFT:
                t, power = NATURAL_GIFT[berry]
        if name == "TERA-STARSTORM" and t != STELLAR:   # (one target unless it's Stellar Terapagos's)
            d["target"] = "selected-pokemon"
        if t == "NORMAL" and self.field().get("ion_deluge"):
            t = "ELECTRIC"
        if v.get("electrified"):
            t = "ELECTRIC"
        d["type"] = t
        # ---- power
        if name in ("RETURN", "FRUSTRATION"):
            f = self._friendship(attacker)
            power = max(1, (f if name == "RETURN" else 255 - f) * 10 // 25)
        elif name == "GYRO-BALL" and defender is not None:
            power = min(150, int(25 * abs(self._speed(defender)) / max(1, abs(self._speed(attacker)))) + 1)
        elif name == "ELECTRO-BALL" and defender is not None:
            r = abs(self._speed(attacker)) / max(1, abs(self._speed(defender)))
            power = 150 if r >= 4 else 120 if r >= 3 else 80 if r >= 2 else 60 if r >= 1 else 40
        elif name in ("REVERSAL", "FLAIL"):
            p = 48 * hp // mx
            power = 200 if p <= 1 else 150 if p <= 4 else 100 if p <= 9 else 80 if p <= 16 else 40 if p <= 32 else 20
        elif name in ("ERUPTION", "WATER-SPOUT", "DRAGON-ENERGY"):
            power = max(1, 150 * hp // mx)
        elif name in ("CRUSH-GRIP", "WRING-OUT", "HARD-PRESS") and defender is not None:
            top = 100 if name == "HARD-PRESS" else 120
            power = max(1, top * self._hp(defender) // max(1, self._max_hp(defender)))
        elif name in ("STORED-POWER", "POWER-TRIP"):
            power = 20 + 20 * self._positive_stages(attacker)
        elif name == "PUNISHMENT" and defender is not None:
            power = min(200, 60 + 20 * self._positive_stages(defender))
        elif name == "TRUMP-CARD":
            from src.pokemon import pp as pplib
            left = pplib.left(self.game, attacker, name)
            power = {0: 200, 1: 80, 2: 60, 3: 50}.get(left, 40)
        elif name == "BEAT-UP":
            team = [p for p in self._party(attacker) if p.current_hp > 0 and not getattr(p, "status", None)] or [attacker]
            if attacker not in team and attacker.current_hp > 0:
                team = [attacker] + team
            d["_powers"] = [5 + int(p.base_stats.get("ATTACK", 50)) // 10 for p in team]
            power = d["_powers"][0]
        elif name in ("TRIPLE-AXEL", "TRIPLE-KICK"):
            step = 20 if name == "TRIPLE-AXEL" else 10
            d["_powers"], d["_each_acc"] = [step, step * 2, step * 3], True
        elif name == "POPULATION-BOMB":
            d["_powers"] = [power] * 10
            d["_each_acc"] = self.ab(attacker) != "SKILLLINK"
        elif name in ("ROLLOUT", "ICE-BALL"):
            chain = v.get("rollout", 0)
            power = 30 * (2 ** min(chain, 4)) * (2 if v.get("curled") else 1)
        elif name == "FURY-CUTTER":
            power = min(160, 40 * (2 ** v.get("fury_cutter", 0)))
        elif name == "ECHOED-VOICE":
            turn, n = self._mv()["echo"]
            n = n if turn >= self.turn_count - 1 else 0
            power = min(200, 40 * (1 + n))
        elif name == "SPIT-UP":
            power = 100 * v.get("stockpile", 0)
        elif name == "MAGNITUDE" and not preview:
            roll, acc = random.randint(1, 100), 0
            for chance, level, pw in MAGNITUDE:
                acc += chance
                if roll <= acc:
                    d["_magnitude"], power = level, pw
                    break
        elif name == "MAGNITUDE":
            power = 70
        elif name == "PRESENT":
            if preview:
                power = 60
            else:
                r, acc = random.random(), 0.0
                power = 0
                for chance, pw in PRESENT_ROLLS:
                    acc += chance
                    if r < acc:
                        power = pw
                        break
                if not power:
                    d["_present_heal"] = True
                    power = 1
        elif name == "FLING":
            item = self.held(attacker)
            if item and not self.field().get("magic_room"):
                power = FLING_POWER.get(item, 10 if str(item).endswith("_BERRY") else 30)
                d["_fling"] = item
            else:
                power = 0
        elif name == "LAST-RESPECTS":
            fainted = sum(1 for p in self._party(attacker) if p.current_hp <= 0)
            power = min(5050, 50 + 50 * fainted)
        elif name == "RAGE-FIST":
            power = min(350, 50 + 50 * self._mv()["rage_fist"].get(id(attacker), 0))
        # doubling by the situation
        double = False
        if defender is not None:
            fstatus = getattr(defender, "status", None)
            if name == "ACROBATICS" and not self.held(attacker):
                double = True
            elif name == "FACADE" and getattr(attacker, "status", None) in ("burn", "paralysis", "poison", "toxic"):
                double = True
            elif name in ("HEX", "INFERNAL-PARADE") and (fstatus or self.ab(defender) == "COMATOSE"):
                double = True
            elif name in ("VENOSHOCK", "BARB-BARRAGE") and fstatus in ("poison", "toxic"):
                double = True
            elif name == "BRINE" and self._hp(defender) * 2 <= self._max_hp(defender):
                double = True
            elif name in ("AVALANCHE", "REVENGE") and self._took_from(attacker, defender):
                double = True
            elif name == "PAYBACK" and self._moved(defender):
                double = True
            elif name in ("BOLT-BEAK", "FISHIOUS-REND") and not self._moved(defender):
                double = True
            elif name == "ASSURANCE" and self._mv()["took"].get(id(defender)):
                double = True
            elif name in ("STOMPING-TANTRUM", "TEMPER-FLARE") and v.get("last_failed"):
                double = True
            elif name == "LASH-OUT" and v.get("lowered_turn") == self.turn_count:
                double = True
            elif name == "RETALIATE" and self._mv()["fainted_turn"][self.side_of(attacker)] == self.turn_count - 1:
                double = True
            elif name in ("WAKE-UP-SLAP", "SMELLING-SALTS") and fstatus == ("sleep" if name == "WAKE-UP-SLAP" else "paralysis"):
                double = True
            elif name == "ROUND" and any(self._mv()["picked"].get(id(a)) == "ROUND" and self._moved(a)
                                         for a in self.allies(attacker)):
                double = True   # (doubles: right after an ally's Round)
            elif name == "FICKLE-BEAM" and not preview and random.random() < 0.3:
                double, d["_fickle"] = True, True
        if double:
            power *= 2
        if name == "KNOCK-OFF" and defender is not None and self._item_of(defender) and self._removable(defender):
            power = power * 3 // 2
        if name == "EXPANDING-FORCE" and self.terrain() == "psychic" and self.grounded(attacker):
            power = power * 3 // 2
        if name == "RISING-VOLTAGE" and self.terrain() == "electric" and defender is not None and self.grounded(defender):
            power *= 2
        if name == "MISTY-EXPLOSION" and self.terrain() == "misty" and self.grounded(attacker):
            power = power * 3 // 2
        if name == "PSYBLADE" and self.terrain() == "electric":
            power = power * 3 // 2
        if name == "GRAV-APPLE" and self.field().get("gravity"):
            power = power * 3 // 2
        if name in ("SOLAR-BEAM", "SOLAR-BLADE") and self.weather_now() in ("RAIN", "HEAVY_RAIN", "SAND", "SNOW"):
            power //= 2
        combo = self._pledge_combo(attacker, name) if name in PLEDGES else None
        if combo:   # (doubles: right after a partner's other Pledge, one 150-power attack and a field effect)
            power, d["type"], d["_pledge"] = 150, combo[0], combo[1]
        if v.get("charged") and d["type"] == "ELECTRIC" and power:
            power *= 2
        if self.vol(attacker).get("helping_hand") and power:
            power = power * 3 // 2
        if boost:
            power = int(power * boost)
        if power != (d.get("power") or 0):
            d["power"] = power
        # ---- fixed damage
        if not preview and defender is not None:
            fixed = self._fixed_damage(attacker, defender, name, d)
            if fixed is not None:
                d["_fixed"] = fixed
        return d

    PLEDGE_COMBOS = {frozenset(("FIRE-PLEDGE", "GRASS-PLEDGE")): ("FIRE", "sea_of_fire"),
                     frozenset(("WATER-PLEDGE", "FIRE-PLEDGE")): ("WATER", "rainbow"),
                     frozenset(("GRASS-PLEDGE", "WATER-PLEDGE")): ("GRASS", "swamp")}

    def _pledge_combo(self, attacker, name):
        """(type, field effect) when a partner used another Pledge just before this one this turn (doubles only:
        with no partner, None)."""
        for ally in self.allies(attacker):
            other = self._mv()["picked"].get(id(ally))
            if other in PLEDGES and other != name and self._moved(ally):
                return self.PLEDGE_COMBOS[frozenset((name, other))]
        return None

    def _fixed_damage(self, attacker, defender, name, d):
        if name == "PSYWAVE":
            return max(1, self._level(attacker) * random.randint(50, 150) // 100)
        if name == "ENDEAVOR":
            return max(0, self._hp(defender) - self._hp(attacker))
        if name == "FINAL-GAMBIT":
            return self._hp(attacker)
        if name in ("COUNTER", "MIRROR-COAT"):
            got = self._took_from(attacker, defender, "PHYSICAL" if name == "COUNTER" else "SPECIAL")
            return 2 * got[-1] if got else 0
        if name in ("METAL-BURST", "COMEUPPANCE"):
            got = self._took_from(attacker, defender)
            return max(1, got[-1] * 3 // 2) if got else 0
        if name == "BIDE":
            b = self.vol(attacker).get("bide")
            return 2 * b[1] if b and b[0] <= 0 else None
        return None

    def mv_fixed_like(self, name):
        return name in ("PSYWAVE", "ENDEAVOR", "FINAL-GAMBIT", "COUNTER", "MIRROR-COAT", "METAL-BURST",
                        "COMEUPPANCE", "BIDE")

    def _removable(self, mon):
        """Can its item be knocked off / stolen? (not a Mega Stone, Z-Crystal or Plate on Arceus)"""
        item = str(self._item_of(mon) or "")
        if not item or self.ab(mon) == "STICKYHOLD":
            return False
        if item.endswith(("ITE", "ITE_X", "ITE_Y")) or item.endswith("_Z") or "Z_CRYSTAL" in item:
            return False
        if item.endswith("_PLATE") and int(getattr(mon, "id", 0) or 0) == 493:
            return False
        if item.endswith("_MASK") and int(getattr(mon, "id", 0) or 0) == 1017:
            return False
        return True

    # ================================================================== can it be used at all
    def _is_sound(self, name):
        return "sound" in self._flags(name) or name in EXTRA_SOUND

    def mv_blocked(self, mon, name, d):
        """A reason the move can't be used now (the battle says it), or None."""
        v, label = self.vol(mon), self._label(mon)
        if v.get("tormented") and name == v.get("last_move") and name != movelib.STRUGGLE:
            return f"{label} can't use the same move twice in a row due to the torment!"
        if v.get("heal_block") and (d.get("category_meta") == "heal" or name in (
                "REST", "WISH", "HEAL-PULSE", "FLORAL-HEALING", "LIFE-DEW", "JUNGLE-HEALING", "LUNAR-BLESSING",
                "PURIFY", "STRENGTH-SAP", "SHORE-UP", "SWALLOW", "PAIN-SPLIT")):
            return f"{label} can't use {_nice(name)} because of the Heal Block!"
        if v.get("throat_chop") and self._is_sound(name):
            return f"{label} can't use {_nice(name)} because of the Throat Chop!"
        if self.field().get("gravity") and name in GRAVITY_BANNED:
            return f"{label} can't use {_nice(name)} because of the gravity!"
        if name in NO_REPEAT and v.get("last_move") == name and v.get("last_turn") == self.turn_count - 1:
            return f"{label} can't use {_nice(name)} twice in a row!"
        if name == "BELCH" and id(mon) not in self._mv()["ate_berry"]:
            return f"{label} hasn't eaten a Berry, so it can't use Belch!"
        if name == "STUFF-CHEEKS" and not str(self.held(mon) or "").endswith("_BERRY"):
            return f"{label} has no Berry to eat!"
        if name == "LAST-RESORT":
            others = [m for m in (getattr(mon, "moves", None) or []) if m != name]
            if not others or not set(others) <= set(v.get("used_moves") or ()):
                return f"{label} has to use its other moves first!"
        return None

    # ================================================================== two-turn moves
    def mv_skips_charge(self, attacker, name):
        w = self.weather_now()
        return (name in ("SOLAR-BEAM", "SOLAR-BLADE") and w in ("SUN", "HARSH_SUN")) or (
            name == "ELECTRO-SHOT" and w in ("RAIN", "HEAVY_RAIN"))

    def mv_charge(self, attacker, defender, name):
        """The charge turn's extra: (fail lines or None, lines). Skull Bash, Meteor Beam and Electro Shot raise a
        stat; Sky Drop lifts the foe (not one over 200 kg, or behind a substitute)."""
        if name == "SKY-DROP":
            from src.pokemon.catching import weight
            if self.vol(defender).get("substitute") or weight(self.game, defender) >= 200 or self.field().get("gravity"):
                return [FAIL], []
            self.vol(defender)["sky_dropped"] = self.turn_count
            self.__dict__.setdefault("_semi", {})[id(defender)] = ("SKY-DROP", self.turn_count)
            return None, []
        return None, self.mv_charge_boost(attacker, name)

    def mv_charge_boost(self, attacker, name):
        if name == "SKULL-BASH":
            return self.change_stages(attacker, [["DEFENSE", 1]])
        if name in ("METEOR-BEAM", "ELECTRO-SHOT"):
            return self.change_stages(attacker, [["SPATK", 1]])
        return []

    # ================================================================== fails
    def mv_fails(self, attacker, defender, name, d, att_label, def_label):
        """Lines that end the move here (a failure, or a move that does its work later), else None."""
        v, fv, m = self.vol(attacker), self.vol(defender), self._mv()
        picked = m["picked"].get(id(defender))
        pd = movelib.info(self.game, picked) if picked else {}
        if name in ("SUCKER-PUNCH", "THUNDERCLAP"):
            if self._moved(defender) or not picked or pd.get("category") == "STATUS" or not (pd.get("power") or 0) \
                    and picked not in movelib.FIXED_DAMAGE and not self.mv_fixed_like(picked):
                return [FAIL]
        if name == "UPPER-HAND":
            pri = (pd.get("priority") or 0) + (self.ability_priority(defender, pd) if pd else 0)
            if self._moved(defender) or not picked or pri <= 0 or pd.get("category") == "STATUS":
                return [FAIL]
        if name == "DREAM-EATER" and getattr(defender, "status", None) != "sleep" and self.ab(defender) != "COMATOSE":
            return [f"It doesn't affect {def_label}..."]
        if name in SLEEP_MOVES and getattr(attacker, "status", None) != "sleep" and self.ab(attacker) != "COMATOSE":
            return [FAIL]
        if name == "POLTERGEIST":
            item = self._item_of(defender)
            if not item:
                return [FAIL]
        if name == "STEEL-ROLLER" and not self.terrain():
            return [FAIL]
        if name in ("BURN-UP", "DOUBLE-SHOCK"):
            need = "FIRE" if name == "BURN-UP" else "ELECTRIC"
            if need not in (attacker.types or []):
                return [FAIL]
        if name == "FOCUS-PUNCH" and self._took_from(attacker):
            return [f"{att_label} lost its focus and couldn't move!"]
        if name == "SHELL-TRAP" and not self._took_from(attacker, category="PHYSICAL"):
            return [f"{att_label}'s shell trap didn't work!"]
        if name == "FLING":
            if not d.get("_fling") or self.vol(attacker).get("embargo") or self.ab(attacker) == "KLUTZ":
                return [FAIL]
        if name == "NATURAL-GIFT" and (self.held(attacker) not in NATURAL_GIFT or self._unnerved(attacker)):
            return [FAIL]
        if name == "SPIT-UP" and not v.get("stockpile"):
            return [FAIL]
        if self.mv_fixed_like(name) and name != "BIDE" and not d.get("_fixed"):
            return [FAIL]
        if name == "BIDE":
            b = v.get("bide")
            if not b:
                v["bide"] = [2, 0]
                return [f"{att_label} is storing energy!"]
            if b[0] > 0:
                return [f"{att_label} is storing energy!"]
            v.pop("bide", None)
            if not b[1]:
                return [f"{att_label} unleashed its energy!", FAIL]
        if name in ("FUTURE-SIGHT", "DOOM-DESIRE"):
            side = self.side_of(defender)
            if side in m["future"]:
                return [FAIL]
            m["future"][side] = {"turns": 2, "user": attacker, "name": name, "d": d, "label": att_label}
            return [f"{att_label} foresaw an attack!" if name == "FUTURE-SIGHT" else f"{att_label} chose Doom Desire as its destiny!"]
        if (d.get("type") == "GROUND" and (d.get("power") or 0) and self._airborne(defender)
                and name != "THOUSAND-ARROWS"):
            return [f"It doesn't affect {def_label}..."]
        if name == "SKY-DROP" and "FLYING" in (defender.types or []):
            self.vol(defender).pop("sky_dropped", None)
            self.__dict__.get("_semi", {}).pop(id(defender), None)
            return [f"It doesn't affect {def_label}..."]
        return None

    def _airborne(self, mon):
        """Magnet Rise or Telekinesis lift it above Ground moves (not under Gravity, Smack Down or an Iron Ball)."""
        v = self.vol(mon)
        return bool((v.get("magnet_rise") or v.get("telekinesis")) and not self.forced_grounded(mon))

    def forced_grounded(self, mon):
        """Pulled down: an Iron Ball, Smack Down / Thousand Arrows, Gravity, Ingrain."""
        v = self.vol(mon)
        return bool(self.held_grounded(mon) or v.get("smacked_down") or self.field().get("gravity") or v.get("ingrain"))

    # ================================================================== Protect and its kin
    def mv_protect(self, attacker, defender, name, d, att_label, def_label):
        """(blocked, lines): Protect / Detect and the shields with their contact penalties, the side guards; Feint
        and others go through (and some break it)."""
        if attacker is defender:
            return False, []
        fv, fs = self.vol(defender), self.side(defender)
        target = d.get("target")
        lines = []
        aimed = target not in ("user", "users-field", "user-and-allies", "entire-field", "all-allies", "ally",
                               "user-or-ally")
        if aimed and fs.get("quick_guard") and (d.get("priority") or 0) + self.ability_priority(attacker, d) > 0:
            return True, [f"Quick Guard protected {def_label}!"]
        if aimed and fs.get("wide_guard") and target in ("all-opponents", "all-other-pokemon", "all-pokemon"):
            return True, [f"Wide Guard protected {def_label}!"]
        if aimed and fs.get("crafty_shield") and d.get("category") == "STATUS" and target != "opponents-field":
            return True, [f"Crafty Shield protected {def_label}!"]
        kind = fv.get("protected")
        if not kind or not self.protected(attacker, defender, d):
            return False, []
        if name in PROTECT_BYPASS:
            if name in PROTECT_BREAK:
                fv.pop("protected", None)
                lines.append(f"It broke through {def_label}'s protection!")
            return False, lines
        lines.append(f"{def_label} protected itself!")
        contact = "contact" in self._flags(name) and self.ab(attacker) != "LONGREACH"
        shield = kind if isinstance(kind, str) else "PROTECT"
        if contact and d.get("category") != "STATUS" or (contact and shield == "SPIKY-SHIELD"):
            if shield == "KINGS-SHIELD" and d.get("category") != "STATUS":
                lines += self.change_stages(attacker, [["ATTACK", -1]], by_foe=True)
            elif shield == "SPIKY-SHIELD" and self.ab(attacker) != "MAGICGUARD":
                self._adjust_hp(attacker, -max(1, self._max_hp(attacker) // 8))
                lines.append(f"{att_label} was hurt by the spiky shield!")
            elif shield == "BANEFUL-BUNKER" and self._can_inflict("poison", attacker):
                lines.append(self._inflict("poison", attacker, att_label))
            elif shield == "BURNING-BULWARK" and self._can_inflict("burn", attacker):
                lines.append(self._inflict("burn", attacker, att_label))
            elif shield == "OBSTRUCT":
                lines += self.change_stages(attacker, [["DEFENSE", -2]], by_foe=True)
            elif shield == "SILK-TRAP":
                lines += self.change_stages(attacker, [["SPEED", -1]], by_foe=True)
        return True, lines

    # ================================================================== accuracy
    def mv_sure_hit(self, attacker, defender, name, d):
        if attacker is defender:
            return True
        v, fv = self.vol(attacker), self.vol(defender)
        lock = v.get("lock_on")
        if lock and lock[0] == id(defender) and lock[1] >= self.turn_count - 1:
            return True
        if fv.get("telekinesis") or fv.get("glaive_rush") == self.turn_count - 1 or fv.get("glaive_rush") == self.turn_count:
            return True
        if fv.get("minimized") and name in MINIMIZE_PUNISH:
            return True
        w = self.weather_now()
        if name in STORM_RAIN and w in ("RAIN", "HEAVY_RAIN"):
            return True
        if name == "BLIZZARD" and w == "SNOW":
            return True
        if name == "TOXIC" and "POISON" in (attacker.types or []):
            return True
        return False

    def mv_acc_mult(self, attacker, defender, name, d):
        mult = 5 / 3 if self.field().get("gravity") else 1.0
        if name in ("THUNDER", "HURRICANE") and self.weather_now() in ("SUN", "HARSH_SUN"):
            mult *= 50 / max(1, d.get("accuracy") or 70)   # (50% in harsh sunlight)
        return mult

    # ================================================================== effectiveness, final multipliers
    def mv_effectiveness(self, attacker, defender, name, d, eff, chart):
        types = defender.types or []
        t = d.get("type")
        if name == "FREEZE-DRY" and "WATER" in types:   # (Water: super effective instead of resisted)
            eff = 2.0
            for x in types:
                eff *= 1.0 if x == "WATER" else chart.get_multiplier(t, [x])
        if name == "FLYING-PRESS" and eff:
            eff *= chart.get_multiplier("FLYING", types)
        if eff == 0 and t == "GROUND" and (name == "THOUSAND-ARROWS" or self.forced_grounded(defender)):
            eff = chart.get_multiplier("GROUND", [x for x in types if x != "FLYING"] or ["NORMAL"])
        if eff == 0 and self.vol(defender).get("identified") and "GHOST" in types and t in ("NORMAL", "FIGHTING"):
            eff = chart.get_multiplier(t, [x for x in types if x != "GHOST"] or ["NORMAL"])
        if eff == 0 and self.vol(defender).get("miracle_eye") and "DARK" in types and t == "PSYCHIC":
            eff = chart.get_multiplier(t, [x for x in types if x != "DARK"] or ["NORMAL"])
        if t == "FIRE" and self.vol(defender).get("tar_shot"):
            eff *= 2
        return eff

    def mv_hit_mult(self, attacker, defender, name, d, eff):
        mult = 1.0
        if name in ("COLLISION-COURSE", "ELECTRO-DRIFT") and eff > 1:
            mult *= 5461 / 4096
        if self.vol(defender).get("minimized") and name in MINIMIZE_PUNISH:
            mult *= 2
        g = self.vol(defender).get("glaive_rush")
        if g is not None and g >= self.turn_count - 1:
            mult *= 2
        if name == "HYDRO-STEAM" and self.weather_now() in ("SUN", "HARSH_SUN"):
            mult *= 3   # (its sun penalty, 0.5, becomes a boost, 1.5)
        if d.get("type") == STELLAR and getattr(defender, "_tera_types", None):
            mult *= 2   # (a Stellar move is super effective on a Terastallized Pokemon)
        return mult

    def mv_weather_mult(self, name, mult):
        """Hydro Steam isn't put out by harsh sunlight."""
        if name == "HYDRO-STEAM" and mult == 0:
            return 1.5
        return mult

    def mv_damage_cap(self, attacker, defender, name, damage, hp):
        if name in ("FALSE-SWIPE", "HOLD-BACK") and damage >= hp:
            return max(0, hp - 1)
        return damage

    def mv_before_hit(self, attacker, defender, name, d, att_label, def_label):
        """Just before the damage: screens broken, stat boosts stolen. Returns lines."""
        lines = []
        if name in SCREEN_BREAK:
            s = self.side(defender)
            gone = [k for k in ("reflect", "light_screen", "aurora_veil") if s.pop(k, None)]
            if gone:
                lines.append("It shattered the barrier!")
        if name == "SPECTRAL-THIEF":
            st, mine = self.stages(defender), self.stages(attacker)
            up = [[k, n] for k, n in st.items() if n > 0]
            if up:
                for k, n in up:
                    st[k] = 0
                lines.append(f"{att_label} stole the target's boosted stats!")
                lines += self.change_stages(attacker, up)
        if name == "POLTERGEIST":
            lines.append(f"{def_label} is about to be attacked by its {self._item_name(self._item_of(defender))}!")
        if d.get("_fickle"):
            lines.append(f"{att_label} is going all out for this attack!")
        if d.get("_magnitude"):
            lines.append(f"Magnitude {d['_magnitude']}!")
        return lines

    # ================================================================== after the damage
    def mv_after_damage(self, name, d, attacker, defender, att_label, def_label, damage, defender_hp):
        """The move's own effect once it has hit (or done nothing). Returns lines."""
        lines, v, fv = [], self.vol(attacker), self.vol(defender)
        survives = damage < defender_hp
        hit = bool(damage) or d.get("_present_heal")
        if not hit:
            return lines
        if d.get("_present_heal"):
            return lines
        if name == "KNOCK-OFF" and self._item_of(defender) and self._removable(defender) and self._hp(attacker) > 0:
            item = self._lose_item(defender)
            lines.append(f"{att_label} knocked off {def_label}'s {self._item_name(item)}!")
        if name in ("THIEF", "COVET") and not self._item_of(attacker) and self._item_of(defender) \
                and self._removable(defender) and self._hp(attacker) > 0:
            item = self._lose_item(defender)
            keep = self.trainer_class == "WILD" and self._player_owns(attacker)
            self._get_item(attacker, item, keep=keep)
            lines.append(f"{att_label} stole {def_label}'s {self._item_name(item)}!")
        if name in ("BUG-BITE", "PLUCK") and str(self._item_of(defender) or "").endswith("_BERRY") and self._hp(attacker) > 0:
            berry = self._item_of(defender)
            self.consume_held(defender) if self._player_owns(defender) else self._lose_item(defender)
            lines.append(f"{att_label} stole and ate its target's {self._item_name(berry)}!")
            lines += self._eat_berry_now(attacker, berry)
        if name == "INCINERATE" and str(self._item_of(defender) or "").endswith(("_BERRY", "_GEM")):
            item = self._item_of(defender)
            self.consume_held(defender) if self._player_owns(defender) else self._lose_item(defender)
            lines.append(f"{def_label}'s {self._item_name(item)} was burned up!")
        semi = self.__dict__.get("_semi", {}).get(id(defender))
        if name in ("SMACK-DOWN", "THOUSAND-ARROWS") and survives and (
                not self.grounded(defender) or self._airborne(defender) or (semi and semi[0] in ("FLY", "BOUNCE"))):
            fv["smacked_down"] = True
            fv.pop("magnet_rise", None)
            fv.pop("telekinesis", None)
            if semi and semi[0] in ("FLY", "BOUNCE"):
                self.__dict__["_semi"].pop(id(defender), None)
                self.__dict__.get("_charging", {}).pop(id(defender), None)
            lines.append(f"{def_label} fell straight down!")
        if name in ("THOUSAND-WAVES", "ANCHOR-SHOT", "SPIRIT-SHACKLE") and survives and "GHOST" not in (defender.types or []):
            if not fv.get("no_escape"):
                fv["no_escape"] = True
                lines.append(f"{def_label} can no longer escape!")
        if name == "JAW-LOCK" and survives:
            fv["no_escape"] = v["no_escape"] = True
            lines.append("Neither Pokemon can run away!")
        if name == "SPARKLING-ARIA" and survives and getattr(defender, "status", None) == "burn":
            defender.cure_status()
            lines.append(f"{def_label}'s burn was healed!")
        if name in ("WAKE-UP-SLAP", "SMELLING-SALTS") and survives and getattr(defender, "status", None) == (
                "sleep" if name == "WAKE-UP-SLAP" else "paralysis"):
            defender.cure_status()
            lines.append(f"{def_label} woke up!" if name == "WAKE-UP-SLAP" else f"{def_label} was cured of paralysis!")
        if name == "FELL-STINGER" and not survives:
            lines += self.change_stages(attacker, [["ATTACK", 3]])
        if name == "CLEAR-SMOG" and survives:
            self.stages(defender).update({k: 0 for k in self.stages(defender)})
            lines.append(f"{def_label}'s stat changes were removed!")
        if name in ("BURN-UP", "DOUBLE-SHOCK"):
            gone = "FIRE" if name == "BURN-UP" else "ELECTRIC"
            self._set_types(attacker, [x for x in attacker.types if x != gone] or ["???"])
            lines.append(f"{att_label} burned itself out!" if name == "BURN-UP" else f"{att_label} used up all its electricity!")
        if name == "CORE-ENFORCER" and survives and self._moved(defender):
            fv["ability"] = "NONE"
            lines.append(f"{def_label}'s Ability was suppressed!")
        if name == "THROAT-CHOP" and survives:
            fv["throat_chop"] = 2
        if name == "PSYCHIC-NOISE" and survives and not fv.get("heal_block"):
            fv["heal_block"] = 2
            lines.append(f"{def_label} was prevented from healing!")
        if name == "SALT-CURE" and survives and not fv.get("salt_cure"):
            fv["salt_cure"] = True
            lines.append(f"{def_label} is being salt cured!")
        if name == "SYRUP-BOMB" and survives and not fv.get("syrup"):
            fv["syrup"] = (3, id(attacker))
            lines.append(f"{def_label} got covered in sticky candy syrup!")
        if name in ("TRI-ATTACK", "DIRE-CLAW") and survives:
            chance = self.ability_effect_chance(attacker, defender, 20 if name == "TRI-ATTACK" else 50)
            if random.uniform(0, 100) < chance:
                ail = random.choice(("burn", "freeze", "paralysis") if name == "TRI-ATTACK" else ("poison", "paralysis", "sleep"))
                if self._can_inflict(ail, defender) and not self.side(defender).get("safeguard"):
                    lines.append(self._inflict(ail, defender, def_label))
        if name in ("BURNING-JEALOUSY", "ALLURING-VOICE") and survives and fv.get("raised_turn") == self.turn_count:
            if random.uniform(0, 100) < self.ability_effect_chance(attacker, defender, 100):
                if name == "BURNING-JEALOUSY" and self._can_inflict("burn", defender):
                    lines.append(self._inflict("burn", defender, def_label))
                elif name == "ALLURING-VOICE":
                    lines += self.ailment_effect("confusion", name, attacker, defender, att_label, def_label, chance=True) or []
        if name in ("STONE-AXE", "CEASELESS-EDGE"):
            key = "stealth_rock" if name == "STONE-AXE" else "spikes"
            from src.states.battle_effects import HAZARD_CAP
            if self.side(defender).get(key, 0) < HAZARD_CAP[key]:
                lines += self.lay_hazard(key, defender)
        if name == "SCALE-SHOT" and self._hp(attacker) > 0:
            lines += self.change_stages(attacker, [["DEFENSE", -1], ["SPEED", 1]])
        if name in ("PAY-DAY", "MAKE-IT-RAIN") and self._player_owns(attacker):
            self._mv()["money"] += 5 * self._level(attacker)
            lines.append("Coins were scattered everywhere!")
        if name == "PLASMA-FISTS":
            self.field()["ion_deluge"] = True
            lines.append("A deluge of ions showers the battlefield!")
        if name == "UPROAR" and not v.get("uproar"):
            v["uproar"] = 3
            self.field()["uproar"] = True
            lines.append(f"{att_label} caused an uproar!")
            for mon in (attacker, defender):
                if getattr(mon, "status", None) == "sleep":
                    mon.cure_status()
                    lines.append(f"The uproar woke {self._label(mon)}!")
        if name == "GLAIVE-RUSH":
            v["glaive_rush"] = self.turn_count
        if name in ("ICE-SPINNER", "STEEL-ROLLER") and self.terrain() and self._hp(attacker) > 0:
            self.field().pop("terrain", None)
            lines.append("The terrain faded away!")
        if name == "MATCHA-GOTCHA" and getattr(attacker, "status", None) == "freeze":
            attacker.cure_status()
        if name == "FLING" and d.get("_fling"):
            lines += self._fling_lands(attacker, defender, d["_fling"], att_label, def_label, survives)
        if name == "NATURAL-GIFT":
            berry = self.held(attacker)
            if berry:
                self.consume_held(attacker)
                self._consumed(attacker, berry)
        if name == "SPIT-UP":
            lines += self._stockpile_spent(attacker)
        if d.get("_pledge"):   # (a Pledge combination: a sea of fire / swamp on the foes' side, a rainbow on yours)
            key = d["_pledge"]
            side = self.side(attacker) if key == "rainbow" else self.side(defender)
            if not side.get(key):
                side[key] = 4
                lines.append({"sea_of_fire": "A sea of fire enveloped the foe's team!",
                              "swamp": "A swamp enveloped the foe's team!",
                              "rainbow": "A rainbow appeared in the sky!"}[key])
        if name in PIVOT_HIT and self._hp(attacker) > 0:
            self._queue_switch("pivot", attacker)
        if name in FORCE_HIT and survives and self._hp(attacker) > 0:
            lines += self._force_out(attacker, defender, def_label)
        return lines

    def _fling_lands(self, attacker, defender, item, att_label, def_label, survives):
        lines = [f"{att_label} flung its {self._item_name(item)}!"]
        self.consume_held(attacker)
        self._consumed(attacker, item)
        if not survives:
            return lines
        eff = FLING_EFFECT.get(item)
        if eff == "flinch":
            if getattr(self, "_acts_second", None) == id(defender):
                self.__dict__.setdefault("_flinched", set()).add(id(defender))
        elif eff and self._can_inflict(eff, defender):
            lines.append(self._inflict(eff, defender, def_label))
        elif str(item).endswith("_BERRY"):
            lines += self._eat_berry_now(defender, item)
        elif item == "WHITE_HERB":
            low = [k for k, n in self.stages(defender).items() if n < 0]
            for k in low:
                self.stages(defender)[k] = 0
        elif item == "MENTAL_HERB":
            for k in ("infatuated", "taunt", "encore", "disabled", "tormented", "heal_block"):
                self.vol(defender).pop(k, None)
        return lines

    def _stockpile_spent(self, mon):
        n = self.vol(mon).pop("stockpile", 0)
        if not n:
            return []
        st = self.stages(mon)
        st["DEFENSE"], st["SPDEF"] = max(-6, st["DEFENSE"] - n), max(-6, st["SPDEF"] - n)
        return [f"{self._label(mon)}'s stockpiled effect wore off!"]

    # ================================================================== switching moves
    def _bench(self, mon):
        """Who could come in for mon (healthy, not out)."""
        if self.side_of(mon) == "player":
            return [i for i, p in enumerate(self.game.story_manager.player_team) if p and p.current_hp > 0
                    and p is not self.player_pokemon]
        if self.trainer_class == "WILD":
            return []
        i = self.current_opponent_idx
        return [j for j in range(i + 1, len(self.opponent_team)) if self.opponent_team[j]
                and self.opponent_team[j].current_hp > 0]

    def _queue_switch(self, kind, mon, baton=None):
        """After this move's text: mon switches out (kind "pivot": its trainer picks; "force": at random)."""
        if not self._bench(mon):
            return False
        self._mv()["pending"].append((kind, mon, baton))
        return True

    def _force_out(self, attacker, defender, def_label, status=False):
        """Roar, Whirlwind, Dragon Tail, Circle Throw: a wild battle ends; a trainer's Pokemon (or yours) is
        dragged out and another comes in at random. Returns lines."""
        from src.pokemon import forms
        if forms.is_dynamax(defender) or getattr(self, "raid_allies", None) or self.vol(defender).get("ingrain"):
            return [FAIL] if status else []
        if self.trainer_class == "WILD" and not getattr(self, "is_boss_battle", False):
            self._flee_by_move = attacker
            return [f"{def_label} was blown away!"] if self.side_of(defender) == "opponent" else [
                f"{def_label} was dragged away!"]
        if self.trainer_class == "WILD":
            return []
        return [] if self._queue_switch("force", defender) or not status else [FAIL]

    def _queue_pending_switch(self):
        """After an action (called at the end of each side's attack): a Shell Trap that was hit goes next; a Revival
        Blessing's choice opens; the switch a move set going (U-turn, Baton Pass, Roar...) runs next in the turn,
        a foe's Pursuit striking first. If a Pokemon fainted, a U-turn user that's still up switches after the
        faint (`_pivot_after_ko`, picked up in battle.py's faint handling)."""
        for mon in (self.player_pokemon, self.opponent_pokemon):
            if mon is not None:
                self._shell_trap_jump(mon)
        pick = self.__dict__.pop("_revive_pick", None)
        if pick:
            self.turn_actions.insert(0, lambda: self._open_revive_pick(pick))
        pending = self._mv()["pending"]
        if not pending:
            return
        if getattr(self, "_flee_by_move", None) is not None:
            pending.clear()
            return
        if self.player_hp <= 0 or self.opponent_hp <= 0:
            self._note_pivot_after_ko(pending)
            pending.clear()
            return
        self.turn_actions.insert(0, self._run_pending_switch)
        self._pursuit_before_pivot(pending[0])

    def _note_pivot_after_ko(self, pending):
        """U-turn / Volt Switch / Flip Turn knocked the foe out: the user still switches out (as in the games),
        once the faint is over, then the trainer sends in its next one. A wild battle just ends."""
        if self.trainer_class == "WILD":
            return
        for kind, mon, baton in pending:
            if kind == "pivot" and self._hp(mon) > 0 and mon in (self.player_pokemon, self.opponent_pokemon) \
                    and self._bench(mon):
                self._pivot_after_ko = (mon, baton)
                return

    def _pursuit_before_pivot(self, entry):
        """A foe that picked Pursuit and hasn't moved yet hits a Pokemon leaving by its own move (U-turn, Volt
        Switch, Baton Pass, Parting Shot, Teleport...) just before it goes, at double power (Gen 4 on). Not one
        dragged out (Roar, Dragon Tail)."""
        kind, mon, _baton = entry
        if kind != "pivot":
            return
        for pursuer in self.opponents_of(mon):
            act = self.action_for(pursuer)
            if act is None or act not in self.turn_actions or self._moved(pursuer) or self._hp(pursuer) <= 0:
                continue
            if self._mv()["picked"].get(id(pursuer)) != "PURSUIT":
                continue
            self.turn_actions.remove(act)

            def strike(act=act):
                self._mv_call_boost = 2.0
                act()
                self.__dict__.pop("_mv_call_boost", None)   # (it didn't get to move: the boost isn't kept)
            self.turn_actions.insert(0, strike)
            return

    def mv_ai_pursuit_mult(self, attacker, defender):
        """How much more a foe wants Pursuit: a Psychic or Ghost type (weak to it, likely to be pulled out) or one
        that left by its own move before is worth chasing (the games' AI likes Pursuit on those)."""
        if "PSYCHIC" in (defender.types or []) or "GHOST" in (defender.types or []):
            return 1.5
        if self.vol(defender).get("last_move") in PIVOT_HIT | {"BATON-PASS", "PARTING-SHOT", "TELEPORT"}:
            return 1.5
        return 1.0

    def _run_pending_switch(self):
        pending = self._mv()["pending"]
        if not pending:
            return
        kind, mon, baton = pending.pop(0)
        if self._hp(mon) <= 0 or mon not in (self.player_pokemon, self.opponent_pokemon):
            return
        bench = self._bench(mon)
        if not bench:
            return
        if self.side_of(mon) == "opponent":
            j = random.choice(bench) if kind == "force" else self._ai_switch_pick(bench, self.player_pokemon)
            self._switch_foe_now(j, baton, dragged=kind == "force")
            return
        if kind == "force":
            self._switch_player_now(random.choice(bench), None, dragged=True)
            return
        self._pick_pivot(bench, baton)

    def _ai_switch_pick(self, bench, against):
        """The trainer's choice when its Pokemon switches out by its own move: the one whose moves hit `against`
        hardest and that takes its types best (team order breaks a tie; with nothing to face, the next in line)."""
        if against is None or self._hp(against) <= 0 or len(bench) < 2:
            return bench[0]
        from src.pokemon.mechanics import TypeAdvantage
        chart = TypeAdvantage(self.game.loader.area_data.get("TYPE_CHART", {}))

        def score(j):
            p = self.opponent_team[j]
            hit = max([chart.get_multiplier(movelib.info(self.game, mv).get("type"), against.types or [])
                       for mv in (getattr(p, "moves", None) or []) if (movelib.info(self.game, mv).get("power") or 0)]
                      or [1.0])
            took = max(chart.get_multiplier(t, p.types or []) for t in (against.types or ["NORMAL"]))
            return hit - 0.5 * took
        return max(bench, key=lambda j: (score(j), -j))

    def _pick_pivot(self, bench, baton):
        """Your Pokemon switches out: you pick who comes in (the party list; backing out sends the first one)."""
        from src.states.systems import PokemonPartyMenuState

        def chosen(slot):
            team = self.game.story_manager.player_team
            if slot not in bench or team[slot].current_hp <= 0:
                slot = bench[0]
            self.game.change_state(self)
            self._switch_player_now(slot, baton)

        self.phase = "PIVOT_PICK"
        self.game.change_state(PokemonPartyMenuState(self.game, self, context="battle_switch", on_select=chosen,
                                                     on_cancel=lambda: chosen(bench[0])))

    def _switch_player_now(self, slot, baton=None, dragged=False):
        self._mid_turn_switch = True
        self._baton = baton
        self.perform_switch(slot, is_forced=False)
        if dragged:
            new = self.game.story_manager.player_team[slot]
            self.dialogue_box.reset([f"{new.display_name.upper()} was dragged out!"])

    def _switch_foe_now(self, j, baton=None, dragged=False):
        """The trainer's Pokemon goes back and team[j] comes out (it takes the other's place in the team order, so
        the one that left comes out again later)."""
        team, i = self.opponent_team, self.current_opponent_idx
        old = team[i]
        old.current_hp = self.opponent_hp
        self.ability_on_switch_out(old)
        self.mv_switched_out(old)
        team[i], team[j] = team[j], team[i]
        new = team[i]
        fresh = id(new) not in self._mv()["been_out"]
        self.opponent_pokemon = new
        self.setup_battle_matchup(reset_opponent_hp=fresh)
        if not fresh:
            self.opponent_hp = new.current_hp
        self.mv_apply_baton(new, baton)
        who = self.trainer_name or self.trainer_class
        if self.trainer_class == "RIVAL":
            who = getattr(self.game, "rival_name", who)
        lines = ([f"Foe {new.display_name.upper()} was dragged out!"] if dragged
                 else [f"{who} withdrew {old.display_name.upper()}!", f"{who} sent out {new.display_name.upper()}!"])
        self.dialogue_box.reset(lines)
        self.dialogue_box.set_visibility(True)
        self.feedback_timer = 30

    def _pursuit_lines(self, is_forced):
        """You chose to switch: a foe that picked Pursuit hits the one going out first, at double power."""
        if is_forced or getattr(self, "_mid_turn_switch", False) or self.phase not in ("MENU", "MOVE_SELECT", "BATTLE"):
            return []
        foe, mon = self.opponent_pokemon, self.player_pokemon
        if foe is None or mon is None or self.player_hp <= 0 or self.opponent_hp <= 0:
            return []
        if self._ai_choose(foe, mon) != "PURSUIT":
            return []
        self._mv()["picked"] = {id(foe): "PURSUIT"}
        self._mv_call_boost = 2.0
        label = f"Foe {foe.display_name.upper()}"
        dmg, lines, _ = self._use_move(foe, mon, "PURSUIT", label, mon.display_name.upper(), self.player_max_hp,
                                       self.player_hp)
        self.player_hp = max(0, self.player_hp - dmg)
        mon.current_hp = self.player_hp
        self._pursued = True
        return lines

    def mv_alias(self, mon, name):
        """The move a slot really is now: Mimic's slot holds the move it copied."""
        if name == "MIMIC" and mon is not None:
            return self.vol(mon).get("mimic") or name
        return name

    def mv_sure_hit_semi(self, attacker, defender):
        """No Guard and Lock-On reach a Pokemon up in the air or underground."""
        lock = self.vol(attacker).get("lock_on")
        return self.ability_hits_always(attacker, defender) or bool(lock and lock[0] == id(defender))

    def mv_baton_state(self, mon):
        v = self.vol(mon)
        return {"stages": dict(self.stages(mon)), "vol": {k: v[k] for k in BATON_VOL if k in v}}

    def mv_apply_baton(self, mon, baton):
        if not baton:
            return
        if baton.get("stages"):
            self.stages(mon).update(baton["stages"])
        self.vol(mon).update(baton.get("vol") or {})

    # ================================================================== status moves of their own
    def _called(self, pick):
        """Run another move now (Sleep Talk, Copycat, Nature Power...): the battle picks it up as Metronome's."""
        self._metronome = pick
        return []

    def _usable_call(self, name):
        return name and name not in NOT_CALLED and name in movelib.table(self.game)

    def mv_status(self, name, d, attacker, defender, att_label, def_label):
        """A status move with a mechanic of its own: its lines, or None if it isn't one of these."""
        v, fv, m = self.vol(attacker), self.vol(defender), self._mv()
        team_word = "Your team" if attacker is self.player_pokemon else "The foe's team"
        # ---- moves that call another
        if name == "SLEEP-TALK":
            options = [x for x in (getattr(attacker, "moves", None) or []) if x not in SLEEP_TALK_SKIPS and x != name]
            if not options:
                return [FAIL]
            return self._called(random.choice(options))
        if name == "COPYCAT":
            last = m.get("last_any")
            return self._called(last) if self._usable_call(last) else [FAIL]
        if name == "MIRROR-MOVE":
            last = fv.get("last_move")
            return self._called(last) if self._usable_call(last) else [FAIL]
        if name == "ASSIST":
            pool = [x for p in self._party(attacker) if p is not attacker for x in (getattr(p, "moves", None) or [])
                    if self._usable_call(x)]
            return self._called(random.choice(pool)) if pool else [FAIL]
        if name == "NATURE-POWER":
            pick = NATURE_TERRAIN.get(self.terrain())
            if not pick:
                where = str((self.game.story_manager.get_current_area_data() or {}).get("battle_type") or "").lower()
                pick = next((mv for k, mv in NATURE_PLACE.items() if k in where), "TRI-ATTACK")
            return [f"Nature Power turned into {_nice(pick)}!"] + self._called(pick)
        if name == "ME-FIRST":
            picked = m["picked"].get(id(defender))
            pd = movelib.info(self.game, picked) if picked else {}
            if self._moved(defender) or not picked or not (pd.get("power") or 0) or not self._usable_call(picked):
                return [FAIL]
            self._mv_call_boost = 1.5
            return self._called(picked)
        if name == "INSTRUCT":
            last = fv.get("last_move")
            if not self._usable_call(last) or last in movelib.TWO_TURN or fv.get("rampage") or \
                    last not in (getattr(defender, "moves", None) or []):
                return [FAIL]
            lines = [f"{def_label} followed {att_label}'s instructions!"]
            mx_hp = self._max_hp(attacker)
            dmg, more, _ = self._use_move(defender, attacker, last, def_label, att_label, mx_hp, self._hp(attacker))
            if dmg:
                self._adjust_hp(attacker, -dmg)
                self.mv_note_hit(defender, attacker, dmg)
            return lines + more
        # ---- copying
        if name == "MIMIC":
            last = fv.get("last_move")
            if not last or last in ("MIMIC", "SKETCH", "TRANSFORM", "STRUGGLE", "METRONOME") or \
                    last in (getattr(attacker, "moves", None) or []):
                return [FAIL]
            v["mimic"] = last
            return [f"{att_label} learned {_nice(last)}!"]
        if name == "SKETCH":
            last = fv.get("last_move")
            moves = getattr(attacker, "moves", None) or []
            if not last or last in ("SKETCH", "STRUGGLE", "CHATTER") or last in moves or name not in moves:
                return [FAIL]
            moves[moves.index(name)] = last
            pool = getattr(attacker, "move_pool", None)
            if isinstance(pool, list) and last not in pool:
                pool.append(last)
            return [f"{att_label} sketched {_nice(last)}!"]
        if name == "TRANSFORM":
            return self._transform(attacker, defender, att_label, def_label)
        if name == "PSYCH-UP":
            return None
        # ---- switching
        if name in ("BATON-PASS", "TELEPORT", "SHED-TAIL", "PARTING-SHOT", "CHILLY-RECEPTION"):
            return self._switch_status(name, d, attacker, defender, att_label, def_label)
        if name in ("ROAR", "WHIRLWIND"):
            return self._force_out(attacker, defender, def_label, status=True) or [
                f"{def_label} was dragged out!" if self.side_of(defender) == "player" else f"{def_label} was blown away!"]
        if name in ("HEALING-WISH", "LUNAR-DANCE"):
            if not self._bench(attacker):
                return [FAIL]
            self.side(attacker)["healing_wish"] = name
            self._adjust_hp(attacker, -self._hp(attacker))
            return [f"{att_label} fainted to heal its teammate!"]
        if name == "MEMENTO":
            lines = [] if fv.get("substitute") else self.change_stages(defender, [["ATTACK", -2], ["SPATK", -2]], by_foe=True)
            self._adjust_hp(attacker, -self._hp(attacker))
            return lines or [FAIL]
        if name == "REVIVAL-BLESSING":
            return self._revive(attacker, att_label)
        # ---- doubles-only (one Pokemon a side: no one to help)
        if name in ("HELPING-HAND", "ALLY-SWITCH", "COACHING", "AROMATIC-MIST", "DRAGON-CHEER"):
            ally = self.ally_of(attacker)
            if ally is None:
                return [NO_ALLY]
            av = self.vol(ally)
            if name == "HELPING-HAND":
                av["helping_hand"] = True
                return [f"{att_label} is ready to help {self._label(ally)}!"]
            if name == "COACHING":
                return self.change_stages(ally, [["ATTACK", 1], ["DEFENSE", 1]])
            if name == "AROMATIC-MIST":
                return self.change_stages(ally, [["SPDEF", 1]])
            if name == "DRAGON-CHEER":
                av["focus"] = max(av.get("focus", 0), 2 if "DRAGON" in (ally.types or []) else 1)
                return [f"{self._label(ally)} is getting pumped!"]
            self.swap_allies(attacker, ally)   # (Ally Switch: battle_doubles.py; a double battle trades their spots)
            return [f"{att_label} and {self._label(ally)} switched places!"]
        if name in ("FOLLOW-ME", "RAGE-POWDER", "SPOTLIGHT"):
            (fv if name == "SPOTLIGHT" else v)["center_of_attention"] = True
            return [f"{def_label if name == 'SPOTLIGHT' else att_label} became the center of attention!"]
        if name in ("AFTER-YOU", "QUASH"):
            # The turn order changes through the doubles hooks (turn_order_for / apply_turn_order). In a single
            # battle both fail, as in the games (Gen 8 on), and so does one aimed at a Pokemon that has moved.
            if not self.is_doubles or self._moved(defender) or defender is attacker:
                return [FAIL]
            self.__dict__.setdefault("_order_override", {})[id(defender)] = 1 if name == "AFTER-YOU" else -1
            if not self.apply_turn_order(defender):
                return [FAIL]
            return [f"{def_label} took the kind offer!" if name == "AFTER-YOU" else f"{def_label}'s move was postponed!"]
        if name in ("GEAR-UP", "MAGNETIC-FLUX"):
            who = [x for x in [attacker] + self.allies(attacker) if self.ab(x) in ("PLUS", "MINUS")]
            if not who:
                return [FAIL]
            stats = [["ATTACK", 1], ["SPATK", 1]] if name == "GEAR-UP" else [["DEFENSE", 1], ["SPDEF", 1]]
            return [ln for x in who for ln in self.change_stages(x, stats)]
        if name in ("ROTOTILLER", "FLOWER-SHIELD"):
            who = [x for x in (attacker, defender) if "GRASS" in (x.types or []) and (name == "FLOWER-SHIELD" or self.grounded(x))]
            if not who:
                return [FAIL]
            stats = [["ATTACK", 1], ["SPATK", 1]] if name == "ROTOTILLER" else [["DEFENSE", 1]]
            return [ln for x in who for ln in self.change_stages(x, stats, by_foe=x is not attacker)]
        if name == "LIFE-DEW":
            lines = []
            for x in [attacker] + self.allies(attacker):
                if self._hp(x) < self._max_hp(x):
                    self._adjust_hp(x, max(1, self._max_hp(x) // 4))
                    lines.append(f"{self._label(x)}'s HP was restored.")
            return lines or [FAIL]
        # ---- healing others
        if name in ("HEAL-PULSE", "FLORAL-HEALING"):
            if fv.get("substitute") or self._hp(defender) >= self._max_hp(defender) or fv.get("heal_block"):
                return [FAIL]
            pct = 67 if name == "FLORAL-HEALING" and self.terrain() == "grassy" else 50
            self._adjust_hp(defender, max(1, self._max_hp(defender) * pct // 100))
            return [f"{def_label}'s HP was restored."]
        if name == "PURIFY":
            if not getattr(defender, "status", None):
                return [FAIL]
            defender.cure_status()
            lines = [f"{def_label}'s status returned to normal!"]
            if self._hp(attacker) < self._max_hp(attacker):
                self._adjust_hp(attacker, max(1, self._max_hp(attacker) // 2))
                lines.append(f"{att_label} regained health!")
            return lines
        if name == "SWALLOW":
            n = v.get("stockpile", 0)
            if not n:
                return [FAIL]
            self._adjust_hp(attacker, max(1, self._max_hp(attacker) * {1: 25, 2: 50, 3: 100}[n] // 100))
            return [f"{att_label} regained health!"] + self._stockpile_spent(attacker)
        if name == "SHORE-UP":
            if self._hp(attacker) >= self._max_hp(attacker):
                return [f"{att_label}'s HP is full!"]
            pct = 67 if self.weather_now() == "SAND" else 50
            self._adjust_hp(attacker, max(1, self._max_hp(attacker) * pct // 100))
            return [f"{att_label} regained health!"]
        if name == "ROOST":
            if self._hp(attacker) >= self._max_hp(attacker):
                return [f"{att_label}'s HP is full!"]
            self._adjust_hp(attacker, max(1, self._max_hp(attacker) // 2))
            if "FLYING" in (attacker.types or []) and not getattr(attacker, "_tera_types", None):
                self._set_types(attacker, [x for x in attacker.types if x != "FLYING"] or ["NORMAL"])
                v["roost_types"] = True
            return [f"{att_label} regained health!"]
        # ---- items
        if name in ("TRICK", "SWITCHEROO"):
            a_item, d_item = self._item_of(attacker), self._item_of(defender)
            if (not a_item and not d_item) or fv.get("substitute") or (a_item and not self._removable(attacker)) \
                    or (d_item and not self._removable(defender)):
                return [FAIL]
            keep = self.trainer_class == "WILD"
            self._lose_item(attacker)
            self._lose_item(defender)
            if d_item:
                self._get_item(attacker, d_item, keep=keep and self._player_owns(attacker))
            if a_item:
                if keep and self._player_owns(attacker):   # (given to a wild Pokemon for good: it leaves the Bag)
                    inv = self.game.story_manager.inventory
                    inv[a_item] = inv.get(a_item, 0) - 1
                    if inv[a_item] <= 0:
                        inv.pop(a_item, None)
                    self._mv()["items0"].pop(id(attacker), None)
                self._get_item(defender, a_item)
            out = [f"{att_label} switched items with its target!"]
            if d_item:
                out.append(f"{att_label} obtained {self._item_name(d_item)}.")
            if a_item:
                out.append(f"{def_label} obtained {self._item_name(a_item)}.")
            return out
        if name == "BESTOW":
            item = self._item_of(attacker)
            if not item or self._item_of(defender) or not self._removable(attacker):
                return [FAIL]
            self._lose_item(attacker)
            self._get_item(defender, item)
            return [f"{def_label} received {self._item_name(item)} from {att_label}!"]
        if name == "RECYCLE":
            item = m["lost_item"].get(id(attacker))
            if not item or self._item_of(attacker):
                return [FAIL]
            m["lost_item"].pop(id(attacker))
            attacker.held_item = item
            if self._player_owns(attacker):
                inv = self.game.story_manager.inventory
                inv[item] = inv.get(item, 0) + 1
            return [f"{att_label} found one {self._item_name(item)}!"]
        if name == "EMBARGO":
            if fv.get("embargo"):
                return [FAIL]
            fv["embargo"] = 5
            return [f"{def_label} can't use items anymore!"]
        if name == "TEATIME":
            lines = []
            for x in (attacker, defender):
                berry = self.held(x)
                if str(berry or "").endswith("_BERRY"):
                    self.consume_held(x)
                    self._consumed(x, berry)
                    lines += [f"{self._label(x)} ate its {self._item_name(berry)}!"] + self._eat_berry_now(x, berry)
            return lines or [FAIL]
        if name == "STUFF-CHEEKS":
            berry = self.held(attacker)
            self.consume_held(attacker)
            self._consumed(attacker, berry)
            return [f"{att_label} ate its {self._item_name(berry)}!"] + self._eat_berry_now(attacker, berry) \
                + self.change_stages(attacker, [["DEFENSE", 2]])
        # ---- conditions on the foe
        if name == "SPITE":
            last = fv.get("last_move")
            from src.pokemon import pp as pplib
            if not last or last not in (getattr(defender, "moves", None) or []) or pplib.left(self.game, defender, last) <= 0:
                return [FAIL]
            pplib.spend(self.game, defender, last, 4)
            return [f"It reduced the PP of {def_label}'s {_nice(last)}!"]
        if name == "TORMENT":
            if fv.get("tormented") or fv.get("substitute"):
                return [FAIL]
            fv["tormented"] = True
            return [f"{def_label} was subjected to torment!"]
        if name == "HEAL-BLOCK":
            if fv.get("heal_block"):
                return [FAIL]
            fv["heal_block"] = 5
            return [f"{def_label} was prevented from healing!"]
        if name == "NIGHTMARE":
            if getattr(defender, "status", None) != "sleep" or fv.get("nightmare") or fv.get("substitute"):
                return [FAIL]
            fv["nightmare"] = True
            return [f"{def_label} began having a nightmare!"]
        if name == "TELEKINESIS":
            if fv.get("telekinesis") or fv.get("ingrain") or fv.get("smacked_down") or self.field().get("gravity") \
                    or int(getattr(defender, "id", 0) or 0) in (50, 51, 769, 770):
                return [FAIL]
            fv["telekinesis"] = 3
            return [f"{def_label} was hurled into the air!"]
        if name in ("FORESIGHT", "ODOR-SLEUTH", "MIRACLE-EYE"):
            fv["identified" if name != "MIRACLE-EYE" else "miracle_eye"] = True
            st = self.stages(defender)
            if st["EVASION"] > 0:
                st["EVASION"] = 0
            return [f"{def_label} was identified!"]
        if name in ("LOCK-ON", "MIND-READER"):
            v["lock_on"] = (id(defender), self.turn_count)
            return [f"{att_label} took aim at {def_label}!"]
        if name == "OCTOLOCK":
            if fv.get("octolock") or fv.get("substitute"):
                return [FAIL]
            fv["octolock"] = id(attacker)
            fv["no_escape"] = True
            return [f"{def_label} can no longer escape because of Octolock!"]
        if name == "ELECTRIFY":
            if self._moved(defender):
                return [FAIL]
            fv["electrified"] = True
            return [f"{def_label}'s moves have been electrified!"]
        if name == "ION-DELUGE":
            self.field()["ion_deluge"] = True
            return ["A deluge of ions showers the battlefield!"]
        if name == "PSYCHO-SHIFT":
            st = getattr(attacker, "status", None)
            if not st or not self._can_inflict(st, defender) or self.side(defender).get("safeguard"):
                return [FAIL]
            line = self._inflict(st, defender, def_label)
            attacker.cure_status()
            return [line, f"{att_label}'s status returned to normal!"]
        if name in ("TAR-SHOT", "TOXIC-THREAD"):
            if fv.get("substitute"):
                return [FAIL]
            lines = self.change_stages(defender, [["SPEED", -1]], by_foe=True)
            if name == "TAR-SHOT" and not fv.get("tar_shot"):
                fv["tar_shot"] = True
                lines.append(f"{def_label} became weaker to fire!")
            if name == "TOXIC-THREAD" and self._can_inflict("poison", defender) and not self.side(defender).get("safeguard"):
                lines.append(self._inflict("poison", defender, def_label))
            return lines
        if name == "CAPTIVATE":
            from src.pokemon import breeding
            ga, gd = breeding.gender_of(self.game, attacker), breeding.gender_of(self.game, defender)
            if ga is None or gd is None or ga == gd or fv.get("substitute"):
                return [FAIL]
            return self.change_stages(defender, [["SPATK", -2]], by_foe=True)
        if name == "VENOM-DRENCH":
            if getattr(defender, "status", None) not in ("poison", "toxic"):
                return [FAIL]
            return self.change_stages(defender, [["ATTACK", -1], ["SPATK", -1], ["SPEED", -1]], by_foe=True)
        if name == "SPICY-EXTRACT":
            if fv.get("substitute"):
                return [FAIL]
            return self.change_stages(defender, [["ATTACK", 2], ["DEFENSE", -2]], by_foe=True)
        if name == "TOPSY-TURVY":
            st = self.stages(defender)
            if not any(st.values()):
                return [FAIL]
            for k in st:
                st[k] = -st[k]
            return [f"All stat changes on {def_label} were inverted!"]
        if name == "HEART-SWAP":
            a, b = self.stages(attacker), self.stages(defender)
            a_copy = dict(a)
            a.update(b)
            b.update(a_copy)
            return [f"{att_label} switched stat changes with its target!"]
        if name in ("POWER-SPLIT", "GUARD-SPLIT"):
            stats = ("ATTACK", "SPATK") if name == "POWER-SPLIT" else ("DEFENSE", "SPDEF")
            for s in stats:
                avg = (self._bstat(attacker, s) + self._bstat(defender, s)) // 2
                v.setdefault("stat_over", {})[s] = avg
                fv.setdefault("stat_over", {})[s] = avg
            return [f"{att_label} shared its {'power' if name == 'POWER-SPLIT' else 'guard'} with the target!"]
        if name == "POWER-TRICK":
            over = v.setdefault("stat_over", {})
            a, dfn = self._bstat(attacker, "ATTACK"), self._bstat(attacker, "DEFENSE")
            over["ATTACK"], over["DEFENSE"] = dfn, a
            return [f"{att_label} switched its Attack and Defense!"]
        if name == "ACUPRESSURE":
            options = [s for s in ("ATTACK", "DEFENSE", "SPATK", "SPDEF", "SPEED", "ACCURACY", "EVASION")
                       if self.stages(attacker)[s] < 6]
            if not options:
                return [FAIL]
            return self.change_stages(attacker, [[random.choice(options), 2]])
        if name == "AUTOTOMIZE":
            lines = self.change_stages(attacker, [["SPEED", 2]])
            attacker._autotomized = getattr(attacker, "_autotomized", 0) + 1
            return lines + [f"{att_label} became nimble!"]
        if name == "CHARGE":
            v["charged"] = True
            return [f"{att_label} began charging power!"] + self.change_stages(attacker, [["SPDEF", 1]])
        if name in ("DEFENSE-CURL", "MINIMIZE"):
            v["curled" if name == "DEFENSE-CURL" else "minimized"] = True
            return None   # (its stat change as usual)
        if name == "NO-RETREAT":
            if v.get("no_retreat"):
                return [FAIL]
            v["no_retreat"] = v["no_escape"] = True
            return self.change_stages(attacker, [[s, 1] for s in ("ATTACK", "DEFENSE", "SPATK", "SPDEF", "SPEED")])
        if name == "CLANGOROUS-SOUL" and self._hp(attacker) <= self._max_hp(attacker) // 3:
            return [FAIL]
        if name == "FILLET-AWAY" and self._hp(attacker) <= self._max_hp(attacker) // 2:
            return [FAIL]
        if name == "DESTINY-BOND":
            if v.get("destiny_bond_turn") == self.turn_count - 1:
                return [FAIL]
            v["destiny_bond"] = True
            v["destiny_bond_turn"] = self.turn_count
            return [f"{att_label} is hoping to take its attacker down with it!"]
        if name == "GRUDGE":
            v["grudge"] = True
            return [f"{att_label} wants its target to bear a grudge!"]
        if name == "MAGIC-COAT":
            v["magic_coat"] = True
            return [f"{att_label} shrouded itself with Magic Coat!"]
        if name == "SNATCH":
            v["snatch"] = True
            return [f"{att_label} waits for a target to make a move!"]
        if name in ("QUICK-GUARD", "WIDE-GUARD", "CRAFTY-SHIELD", "MAT-BLOCK"):
            key = name.lower().replace("-", "_")
            if name == "MAT-BLOCK":
                if not self._first_turn(attacker):
                    return [FAIL]
                key = "wide_guard"
            self.side(attacker)[key] = True
            return [{"quick_guard": f"Quick Guard protected {team_word.lower()}!",
                     "wide_guard": f"Wide Guard protected {team_word.lower()}!",
                     "crafty_shield": f"Crafty Shield protected {team_word.lower()}!"}[key]]
        if name == "MAGNET-RISE":
            if v.get("magnet_rise") or self.forced_grounded(attacker):
                return [FAIL]
            v["magnet_rise"] = 5
            return [f"{att_label} levitated with electromagnetism!"]
        if name == "GRAVITY":
            f = self.field()
            if f.get("gravity"):
                return [FAIL]
            f["gravity"] = 5
            lines = ["Gravity intensified!"]
            for x in (attacker, defender):
                xv = self.vol(x)
                if xv.pop("magnet_rise", None) or xv.pop("telekinesis", None):
                    lines.append(f"{self._label(x)} couldn't stay airborne because of gravity!")
                semi = self.__dict__.get("_semi", {}).get(id(x))
                if semi and semi[0] in ("FLY", "BOUNCE", "SKY-DROP"):
                    self.__dict__["_semi"].pop(id(x), None)
                    self.__dict__.get("_charging", {}).pop(id(x), None)
                    lines.append(f"{self._label(x)} fell from the sky due to the gravity!")
            return lines
        if name == "FAIRY-LOCK":
            if self.field().get("fairy_lock"):
                return [FAIL]
            self.field()["fairy_lock"] = 2
            return ["No one will be able to run away during the next turn!"]
        # ---- types and abilities
        if name in ("SOAK", "MAGIC-POWDER"):
            want = "WATER" if name == "SOAK" else "PSYCHIC"
            if fv.get("substitute") or defender.types == [want] or int(getattr(defender, "id", 0) or 0) in LOCKED_TYPES \
                    or getattr(defender, "_tera_types", None):
                return [FAIL]
            self._set_types(defender, [want])
            return [f"{def_label} transformed into the {want.title()} type!"]
        if name in ("FORESTS-CURSE", "TRICK-OR-TREAT"):
            add = "GRASS" if name == "FORESTS-CURSE" else "GHOST"
            if add in (defender.types or []) or getattr(defender, "_tera_types", None):
                return [FAIL]
            self._set_types(defender, [x for x in defender.types if x not in ("GRASS", "GHOST") or x != add][:2] + [add])
            return [f"{add.title()} type was added to {def_label}!"]
        if name == "REFLECT-TYPE":
            if getattr(attacker, "_tera_types", None) or not defender.types:
                return [FAIL]
            self._set_types(attacker, list(defender.types))
            return [f"{att_label}'s type became the same as {def_label}'s type!"]
        if name == "CONVERSION":
            moves = getattr(attacker, "moves", None) or []
            t = movelib.info(self.game, moves[0]).get("type") if moves else None
            if not t or attacker.types == [t] or getattr(attacker, "_tera_types", None):
                return [FAIL]
            self._set_types(attacker, [t])
            return [f"{att_label} transformed into the {t.title()} type!"]
        if name == "CONVERSION-2":
            last = fv.get("last_move")
            lt = movelib.info(self.game, last).get("type") if last else None
            if not lt:
                return [FAIL]
            from src.pokemon.mechanics import TypeAdvantage
            chart = TypeAdvantage(self.game.loader.area_data.get("TYPE_CHART", {}))
            options = [t for t in HP_TYPES + ("NORMAL", "FAIRY") if chart.get_multiplier(lt, [t]) < 1
                       and t not in (attacker.types or [])]
            if not options:
                return [FAIL]
            t = random.choice(options)
            self._set_types(attacker, [t])
            return [f"{att_label} transformed into the {t.title()} type!"]
        if name in ("SKILL-SWAP", "ROLE-PLAY", "ENTRAINMENT", "SIMPLE-BEAM", "WORRY-SEED", "GASTRO-ACID", "DOODLE"):
            return self._ability_move(name, attacker, defender, att_label, def_label)
        return None

    def _ability_move(self, name, attacker, defender, att_label, def_label):
        fixed = {"MULTITYPE", "STANCECHANGE", "SCHOOLING", "COMATOSE", "SHIELDSDOWN", "DISGUISE", "RKSSYSTEM",
                 "BATTLEBOND", "POWERCONSTRUCT", "ICEFACE", "ZEROTOHERO", "COMMANDER", "TERASHIFT", "ASONEGLASTRIER",
                 "ASONESPECTRIER", "GULPMISSILE", "ZENMODE"}
        a, b = self.ab(attacker), self.ab(defender)
        v, fv = self.vol(attacker), self.vol(defender)
        if name == "SKILL-SWAP":
            if not a or not b or a in fixed or b in fixed or a in ("WONDERGUARD",) or b in ("WONDERGUARD",):
                return [FAIL]
            v["ability"], fv["ability"] = b, a
            return [f"{att_label} swapped Abilities with its target!"]
        if name in ("ROLE-PLAY", "DOODLE"):
            if not b or b in fixed or b in ("TRACE", "WONDERGUARD", "RECEIVER", "POWEROFALCHEMY") or a == b:
                return [FAIL]
            v["ability"] = b
            return [f"{att_label} copied {def_label}'s {self.ab_name(defender)}!"]
        if name == "ENTRAINMENT":
            if not a or a in fixed or b in fixed or b == "TRUANT" or a == b:
                return [FAIL]
            fv["ability"] = a
            return [f"{def_label} acquired {self.ab_name(defender)}!"]
        if name in ("SIMPLE-BEAM", "WORRY-SEED"):
            new = "SIMPLE" if name == "SIMPLE-BEAM" else "INSOMNIA"
            if b in fixed or b == new or b == "TRUANT":
                return [FAIL]
            fv["ability"] = new
            lines = [f"{def_label} acquired {self.ab_name(defender)}!"]
            if new == "INSOMNIA" and getattr(defender, "status", None) == "sleep":
                defender.cure_status()
                lines.append(f"{def_label} woke up!")
            return lines
        if name == "GASTRO-ACID":
            if b in fixed or fv.get("ability") == "NONE":
                return [FAIL]
            fv["ability"] = "NONE"
            return [f"{def_label}'s Ability was suppressed!"]
        return [FAIL]

    def _transform(self, attacker, defender, att_label, def_label):
        """Transform (the move): for this battle, the user takes the target's types, stats (not HP), moves, stat
        changes and Ability."""
        rec = self._mv()["transform"]
        if id(attacker) in rec or hasattr(attacker, "transformed_state") or self.vol(defender).get("substitute") \
                or id(defender) in rec:
            return [FAIL]
        hp_base = attacker.base_stats.get("HP")
        rec[id(attacker)] = (attacker, attacker.base_stats, list(attacker.moves or []), dict(attacker.pp or {}))
        self._set_types(attacker, list(defender.types or []))
        stats = dict(defender.base_stats)
        if hp_base is not None:
            stats["HP"] = hp_base
        attacker.base_stats = stats
        attacker.moves = list(defender.moves or [])[:4] or ["TACKLE"]
        self.mv_copied_pp(attacker)
        self.stages(attacker).update(self.stages(defender))
        if self.ab(defender):
            self.vol(attacker)["ability"] = self.ab(defender)
        return [f"{att_label} transformed into {defender.display_name.upper()}!"]

    def mv_copied_pp(self, mon):
        """Transformed: each copied move has 5 PP, and 5 is its most (fewer if the move has fewer), as in the
        games. Its own moves and PP come back when it switches out or the battle ends."""
        from src.pokemon import pp as pplib
        mon._pp_cap = {mv: min(5, pplib.base_pp(self.game, mv)) for mv in (mon.moves or [])}
        mon.pp = dict(mon._pp_cap)

    def mv_undo_transform(self, mon):
        rec = self._mv()["transform"].pop(id(mon), None)
        if rec:
            _m, stats, moves, pp = rec
            mon.base_stats, mon.moves, mon.pp = stats, moves, pp
            mon.__dict__.pop("_pp_cap", None)

    def _switch_status(self, name, d, attacker, defender, att_label, def_label):
        lines = []
        if name == "TELEPORT" and self.trainer_class == "WILD":
            if self.side_of(attacker) == "opponent" or not getattr(self, "is_boss_battle", False):
                self._flee_by_move = attacker
                return [f"{att_label} teleported away!" if self.side_of(attacker) == "opponent" else "Got away safely!"]
            return [FAIL]
        if name == "SHED-TAIL":
            mx = self._max_hp(attacker)
            if self._hp(attacker) <= mx // 2 or self.vol(attacker).get("substitute") or not self._bench(attacker):
                return [FAIL]
            self._adjust_hp(attacker, -((mx + 1) // 2))
            self._queue_switch("pivot", attacker, {"vol": {"substitute": mx // 4}})
            return [f"{att_label} shed its tail to create a decoy!"]
        if name == "PARTING-SHOT":
            if self.vol(defender).get("substitute"):
                return [FAIL]
            lines = self.change_stages(defender, [["ATTACK", -1], ["SPATK", -1]], by_foe=True)
            if not any("fell" in ln for ln in lines):
                return lines
        if name == "CHILLY-RECEPTION":
            lines = [f"{att_label} is preparing to tell a chillingly bad joke!"]
            if not self.weather_primal:
                self.set_weather("SNOW")
                self._weather_announced = True
                lines.append(self.WEATHER_TEXT["SNOW"][0])
        baton = self.mv_baton_state(attacker) if name == "BATON-PASS" else None
        if not self._queue_switch("pivot", attacker, baton):
            return lines or [FAIL] if name in ("BATON-PASS", "TELEPORT") else lines
        return lines

    def _revive(self, attacker, att_label):
        """Revival Blessing: a fainted party member back with half its HP. You choose which (a list after the
        move's text, unless only one is down); a trainer revives its strongest."""
        team = self._party(attacker)
        down = [p for p in team if p.current_hp <= 0 and p is not attacker]
        if not down:
            return [FAIL]
        if self.side_of(attacker) == "player":
            if len(down) > 1:
                self._revive_pick = [i for i, p in enumerate(team) if p in down]
                return []
            return self._revive_one(down[0])
        mon = max(down, key=lambda p: (getattr(p, "level", 0), sum((getattr(p, "base_stats", None) or {}).values())))
        lines = self._revive_one(mon)
        t = self.opponent_team   # (it comes out again later, next in team order)
        t.remove(mon)
        t.insert(self.current_opponent_idx + 1, mon)
        return lines

    def _revive_one(self, mon):
        mon.current_hp = max(1, mon.get_max_hp() // 2)
        return [f"{mon.display_name.upper()} was revived and is ready to fight again!"]

    def _open_revive_pick(self, slots):
        """The list of your fainted Pokemon for Revival Blessing (it has to be one of them: backing out asks again)."""
        from src.states.systems.pick_list import PickListState
        team = self.game.story_manager.player_team
        slots = [i for i in slots if i < len(team) and team[i] is not None and team[i].current_hp <= 0]
        if not slots:
            return

        def done(i):
            if i is None:
                self.game.change_state(PickListState(self.game, self, "REVIVE WHICH?", rows, done))
                return
            self.dialogue_box.reset(self._revive_one(team[i]))
            self.dialogue_box.set_visibility(True)
            self.phase = "RESOLVE_TURN"
            self.feedback_timer = 30

        rows = [(f"{team[i].display_name.upper()} Lv{getattr(team[i], 'level', '')}", i) for i in slots]
        self.game.change_state(PickListState(self.game, self, "REVIVE WHICH?", rows, done))

    def _shell_trap_jump(self, mon):
        """Shell Trap goes off right after its user is hit by a physical move (in its turn order's place
        otherwise it fails at its own turn)."""
        if not self.vol(mon).get("shell_trap") or self._moved(mon) or self._hp(mon) <= 0:
            return
        if not self._took_from(mon, category="PHYSICAL"):
            return
        act = self.action_for(mon)
        if act in self.turn_actions and self.turn_actions.index(act) > 0:
            self.turn_actions.remove(act)
            self.turn_actions.insert(0, act)

    def _paldean_breed_type(self, mon):
        """Raging Bull's type from Paldean Tauros's breed, by its form data (FORM_MAP: Combat = Fighting,
        Blaze = Fire, Aqua = Water); None for any other Pokemon (Normal, as Kanto's Tauros)."""
        fm = self.game.loader.area_data.get("FORM_MAP", {}).get(str(getattr(mon, "id", "")))
        if fm and fm.get("id") == TAUROS and fm.get("form") == "paldean" and fm.get("types"):
            return fm["types"][0]
        return None

    def mv_mask_form(self, mon):
        """Ogerpon holding a mask (Wellspring, Hearthflame, Cornerstone) is in that mask's form in battle: Grass and
        the mask's type, the mask's Ability, its picture. No mask: the Teal Mask form (Grass, Defiant)."""
        mask = itemlib.OGERPON_MASKS.get(getattr(mon, "held_item", None))
        if int(getattr(mon, "id", 0) or 0) != OGERPON or not mask:
            return []
        self._set_types(mon, ["GRASS", mask])
        self.vol(mon)["ability"] = itemlib.MASK_ABILITY[mask]
        art = self._mv().setdefault("mask_art", {})
        if id(mon) not in art:
            art[id(mon)] = (mon, mon.image, mon.sidebar_image)
            assets = self.game.assets
            fname = assets.alt_sprite_map.get(itemlib.MASK_ART[mask])
            if fname:
                import os
                import pygame
                try:
                    img = pygame.image.load(os.path.join(assets.alt_sprites_dir, fname)).convert_alpha()
                except pygame.error:
                    img = None
                for attr in ("image", "sidebar_image"):
                    cur = getattr(mon, attr, None)
                    if img is not None and cur is not None:
                        setattr(mon, attr, pygame.transform.scale(img, cur.get_size()))
        return []

    def mv_redirect(self, attacker, defender, name, d):
        """Snatch and Magic Coat: (user, target, lines) the status move really runs with."""
        target = d.get("target")
        if d.get("category") != "STATUS":
            return attacker, defender, []
        if target in ("user", "users-field", "user-and-allies", "all-allies") and name not in NOT_SNATCHED:
            foe = self._foe_of(attacker)
            if foe is not None and self.vol(foe).get("snatch") and self._hp(foe) > 0:
                self.vol(foe).pop("snatch", None)
                return foe, attacker, [f"{self._label(foe)} snatched {self._label(attacker)}'s move!"]
        if target in ("selected-pokemon", "all-opponents", "opponents-field") and name not in NOT_BOUNCED \
                and defender is not None and attacker is not defender:
            if self.vol(defender).get("magic_coat") or self.def_ab(attacker, defender) == "MAGICBOUNCE":
                self.vol(defender).pop("magic_coat", None)
                return defender, attacker, [f"{self._label(defender)} bounced the {_nice(name)} back!"]
        return attacker, defender, []

    # ================================================================== bookkeeping after a move
    def mv_end_move(self, attacker, defender, name, d, damage, lines):
        """What the battle remembers once a move is done."""
        m, v = self._mv(), self.vol(attacker)
        m["moved"].add(id(attacker))
        failed = not damage and any(f in str(ln) for ln in lines for f in (
            "But it failed", "missed", "avoided the attack", "doesn't affect", "protected itself", "protected",
            "can't use", "lost its focus", "didn't work", "has nothing", "no Berry", "has to use"))
        v["last_failed"] = failed
        v["last_turn"] = self.turn_count
        v.setdefault("used_moves", set()).add(name)
        if name not in ("STRUGGLE",) and name not in NOT_CALLED:
            m["last_any"] = name
        # chains
        if name in ("ROLLOUT", "ICE-BALL"):
            if failed:
                v.pop("rollout", None)
                v.pop("rollout_lock", None)
            else:
                v["rollout"] = v.get("rollout", 0) + 1
                if v["rollout"] >= 5:
                    v.pop("rollout", None)
                    v.pop("rollout_lock", None)
                else:
                    v["rollout_lock"] = name
        else:
            v.pop("rollout", None)
            v.pop("rollout_lock", None)
        if name == "FURY-CUTTER" and not failed:
            v["fury_cutter"] = min(2, v.get("fury_cutter", 0) + 1)
        else:
            v.pop("fury_cutter", None)
        if name == "ECHOED-VOICE" and not failed:
            turn, n = m["echo"]
            if turn != self.turn_count:
                m["echo"] = [self.turn_count, (n + 1) if turn >= self.turn_count - 1 else 1]
        if name == "RAGE" and not failed:
            v["rage"] = True
        elif name != "RAGE":
            v.pop("rage", None)
        if name == "BEAK-BLAST":   # (its heat ends once it strikes)
            v.pop("beak_blast", None)
        if name != "DESTINY-BOND":
            v.pop("destiny_bond", None)
        if name != "GRUDGE":
            v.pop("grudge", None)
        if d.get("type") == "ELECTRIC" and (d.get("power") or 0) and name != "CHARGE":
            v.pop("charged", None)
        if name in HALF_HP_COST and self._hp(attacker) > 0 and not any("can't use" in str(ln) or "Damp" in str(ln) for ln in lines) \
                and self.ab(attacker) != "MAGICGUARD":
            self._adjust_hp(attacker, -((self._max_hp(attacker) + 1) // 2))
        if name in ("MEMENTO", "FINAL-GAMBIT") and damage and self._hp(attacker) > 0:
            self._adjust_hp(attacker, -self._hp(attacker))

    def mv_missed(self, attacker, defender, name, d, att_label):
        """A crash: High Jump Kick and the like hurt the user when they miss or are blocked. Returns lines."""
        if name in CRASH and self.ab(attacker) != "MAGICGUARD" and self._hp(attacker) > 0:
            self._adjust_hp(attacker, -max(1, self._max_hp(attacker) // 2))
            return [f"{att_label} kept going and crashed!"]
        return []

    def mv_note_hit(self, attacker, defender, damage, name=None):
        """defender lost `damage` HP to attacker's move. Returns lines (Rage, Destiny Bond, Grudge, Beak Blast)."""
        m = self._mv()
        last = getattr(self, "_mv_last_hit", None) or (name, "PHYSICAL")
        cat = last[1]
        lines = []
        if not damage or attacker is defender:
            return lines
        m["took"].setdefault(id(defender), []).append((damage, cat, id(attacker)))
        m["rage_fist"][id(defender)] = m["rage_fist"].get(id(defender), 0) + 1
        fv = self.vol(defender)
        b = fv.get("bide")
        if b:
            b[1] += damage
        if fv.get("rage") and self._hp(defender) > 0:
            lines += [f"{self._label(defender)}'s rage is building!"] + self.change_stages(defender, [["ATTACK", 1]])
        contact = "contact" in self._flags(last[0] or "")
        if fv.get("beak_blast") and contact and self._can_inflict("burn", attacker):
            lines.append(self._inflict("burn", attacker, self._label(attacker)))
        if self._hp(defender) <= 0:
            m["fainted_turn"][self.side_of(defender)] = self.turn_count
            if fv.get("destiny_bond") and self._hp(attacker) > 0:
                self._adjust_hp(attacker, -self._hp(attacker))
                lines.append(f"{self._label(defender)} took its attacker down with it!")
            if fv.get("grudge") and last[0] and last[0] in (getattr(attacker, "moves", None) or []):
                from src.pokemon import pp as pplib
                pplib.spend(self.game, attacker, last[0], 99)
                lines.append(f"{self._label(attacker)}'s {_nice(last[0])} lost all its PP due to the grudge!")
        return lines

    # ================================================================== switching in
    def mv_on_entry(self, mon):
        """A Pokemon coming out: Healing Wish / Lunar Dance waiting for it. Returns lines."""
        s = self.side(mon)
        wish = s.pop("healing_wish", None)
        if wish and self._hp(mon) > 0:
            self._adjust_hp(mon, self._max_hp(mon))
            mon.cure_status()
            if wish == "LUNAR-DANCE":
                mon.pp = {}
            return [f"{self._label(mon)} became cloaked in mystical light!" if wish == "LUNAR-DANCE"
                    else f"The healing wish came true for {self._label(mon)}!"]
        return []

    def mv_left_field(self, active):
        """Called as the field's stat stages and conditions are cleared: whoever isn't out now gets its own
        types and moves back (Soak, Roost, Transform...) and counts as having been out (a trainer's Pokemon that
        comes back keeps its HP)."""
        m = self._mv()
        for key, (mon, _t) in list(m["types0"].items()):
            if key not in active:
                self._restore_types(mon)
        for key in list(m["transform"]):
            if key not in active:
                self.mv_undo_transform(m["transform"][key][0])
        m["been_out"].update(k for k in self._fx()["vol"] if k not in active)

    def mv_switched_out(self, mon):
        """Leaving the field ends what was only for its time out (types, Transform, Autotomize)."""
        self._restore_types(mon)
        self.mv_undo_transform(mon)
        if hasattr(mon, "transformed_state") and hasattr(mon, "undo_transform"):   # (Ditto's own transforming)
            mon.undo_transform()
        if hasattr(mon, "_autotomized"):
            del mon._autotomized
        self._mv()["been_out"].add(id(mon))

    # ================================================================== the end of the turn
    def mv_end_of_turn(self):
        lines, m = [], self._mv()
        for side, pending in list(m["future"].items()):
            pending["turns"] -= 1
            if pending["turns"] > 0:
                continue
            m["future"].pop(side)
            target = self.player_pokemon if side == "player" else self.opponent_pokemon
            if target is None or self._hp(target) <= 0:
                continue
            lines.append(f"{self._label(target)} took the {_nice(pending['name']).title()} attack!")
            from src.pokemon.mechanics import TypeAdvantage
            chart = TypeAdvantage(self.game.loader.area_data.get("TYPE_CHART", {}))
            d = pending["d"]
            eff = chart.get_multiplier(d.get("type"), target.types or [])
            if eff == 0:
                lines.append(f"It doesn't affect {self._label(target)}...")
                continue
            dmg = self._calculate_damage(pending["user"], target, d.get("power") or 120, eff, 1.0,
                                         category="SPECIAL", move_type=d.get("type"))
            dmg = min(dmg, self._hp(target))
            self._adjust_hp(target, -dmg)
            self._mv_last_hit = (pending["name"], "SPECIAL")
            lines += self.mv_note_hit(pending["user"], target, dmg)
            if eff > 1:
                lines.append("It's super effective!")
        for mon in (self.player_pokemon, self.opponent_pokemon):
            if mon is None or self._hp(mon) <= 0:
                continue
            v, label, mx = self.vol(mon), self._label(mon), self._max_hp(mon)
            if v.get("nightmare"):
                if getattr(mon, "status", None) != "sleep":
                    v.pop("nightmare")
                elif self.ab(mon) != "MAGICGUARD":
                    self._adjust_hp(mon, -max(1, mx // 4))
                    lines.append(f"{label} is locked in a nightmare!")
            if v.get("salt_cure") and self._hp(mon) > 0 and self.ab(mon) != "MAGICGUARD":
                hard = {"WATER", "STEEL"} & set(mon.types or [])
                self._adjust_hp(mon, -max(1, mx // (4 if hard else 8)))
                lines.append(f"{label} is hurt by Salt Cure!")
            syrup = v.get("syrup")
            if syrup:
                turns, src = syrup
                if src in (id(self.player_pokemon), id(self.opponent_pokemon)) and self._hp(mon) > 0:
                    lines += self.change_stages(mon, [["SPEED", -1]], by_foe=True)
                v["syrup"] = (turns - 1, src) if turns > 1 else None
                if not v["syrup"]:
                    v.pop("syrup")
            if v.get("octolock"):
                if v["octolock"] in (id(self.player_pokemon), id(self.opponent_pokemon)):
                    lines += self.change_stages(mon, [["DEFENSE", -1], ["SPDEF", -1]], by_foe=True)
                else:
                    v.pop("octolock")
            for key, text in (("heal_block", "{n}'s Heal Block wore off!"), ("embargo", "{n} can use items again!"),
                              ("throat_chop", None), ("telekinesis", "{n} was freed from the telekinesis!"),
                              ("magnet_rise", "{n}'s electromagnetism wore off!")):
                if v.get(key):
                    v[key] -= 1
                    if v[key] <= 0:
                        v.pop(key)
                        if text:
                            lines.append(text.format(n=label))
            if v.get("uproar"):
                v["uproar"] -= 1
                if v["uproar"] <= 0:
                    v.pop("uproar")
                    lines.append(f"{label} calmed down.")
            if v.get("bide"):
                v["bide"][0] -= 1
            if v.get("lock_on") and v["lock_on"][1] < self.turn_count:
                v.pop("lock_on")
        if not any(self.vol(x).get("uproar") for x in (self.player_pokemon, self.opponent_pokemon) if x):
            self.field().pop("uproar", None)
        f = self.field()
        for key, text in (("gravity", "Gravity returned to normal!"), ("fairy_lock", None)):
            if f.get(key):
                f[key] -= 1
                if f[key] <= 0:
                    f.pop(key)
                    if text:
                        lines.append(text)
        for side_name in ("player", "opponent"):
            s = self._fx()["side"][side_name]
            mon = self.player_pokemon if side_name == "player" else self.opponent_pokemon
            for key, text in (("sea_of_fire", None), ("swamp", None), ("rainbow", None)):
                if s.get(key):
                    if key == "sea_of_fire" and mon and self._hp(mon) > 0 and "FIRE" not in (mon.types or []):
                        self._adjust_hp(mon, -max(1, self._max_hp(mon) // 8))
                        lines.append(f"{self._label(mon)} is hurt by the sea of fire!")
                    s[key] -= 1
                    if s[key] <= 0:
                        s.pop(key)
        return lines

    # ================================================================== the end of the battle
    def mv_battle_end(self):
        """Types, items and Transform back as they were; the uproar and the like end. Returns Pay Day's money."""
        m = self._mv()
        for mon, _types in list(m["types0"].values()):
            self._restore_types(mon)
        for key in list(m["transform"]):
            mon = m["transform"][key][0]
            self.mv_undo_transform(mon)
        for mon, image, side in list(m.pop("mask_art", {}).values()):   # (Ogerpon's mask picture: back to its own)
            mon.image, mon.sidebar_image = image, side
        for mon, item in list(m["items0"].values()):
            if self._player_owns(mon):
                gone = itemlib_consumed(item) and self.game.story_manager.inventory.get(item, 0) <= 0
                mon.held_item = None if gone else item
        for p in self.game.story_manager.player_team:
            if p is not None and hasattr(p, "_autotomized"):
                del p._autotomized
        money, m["money"] = m["money"], 0
        return money

    # ================================================================== the foe's choices and the menu
    def mv_would_fail(self, attacker, defender, name, d):
        """A quick look (no side effects) at whether the move would do nothing now. For the foe's choice."""
        v, fv = self.vol(attacker), self.vol(defender)
        if name in SLEEP_MOVES:
            return getattr(attacker, "status", None) != "sleep"
        if name == "DREAM-EATER" or name == "NIGHTMARE":
            return getattr(defender, "status", None) != "sleep"
        if name in ("HELPING-HAND", "ALLY-SWITCH", "COACHING", "AROMATIC-MIST", "DRAGON-CHEER", "FOLLOW-ME",
                    "RAGE-POWDER", "SPOTLIGHT", "AFTER-YOU", "QUASH", "INSTRUCT"):
            return self.ally_of(attacker) is None
        if name in ("FLING",):
            return not self.held(attacker)
        if name == "NATURAL-GIFT":
            return self.held(attacker) not in NATURAL_GIFT
        if name == "POLTERGEIST":
            return not self._item_of(defender)
        if name in ("SPIT-UP", "SWALLOW"):
            return not v.get("stockpile")
        if name == "STEEL-ROLLER":
            return not self.terrain()
        if name in ("COUNTER", "MIRROR-COAT", "METAL-BURST", "COMEUPPANCE", "BIDE", "SHELL-TRAP",
                    "UPPER-HAND", "ME-FIRST", "SNATCH", "MAGIC-COAT",
                    "COPYCAT", "MIRROR-MOVE", "MIMIC", "SKETCH", "TRANSFORM", "ASSIST", "LAST-RESORT", "BELCH",
                    "ELECTRIFY", "ION-DELUGE", "TEATIME", "STUFF-CHEEKS", "RECYCLE", "BESTOW", "PSYCHO-SHIFT",
                    "REVIVAL-BLESSING", "HEALING-WISH", "LUNAR-DANCE", "MEMENTO", "FINAL-GAMBIT", "GRUDGE",
                    "DESTINY-BOND", "CAPTIVATE", "VENOM-DRENCH", "GEAR-UP", "MAGNETIC-FLUX", "ROTOTILLER",
                    "FLOWER-SHIELD", "HEAL-PULSE", "FLORAL-HEALING", "PURIFY", "FAIRY-LOCK", "TELEPORT",
                    "BATON-PASS", "SHED-TAIL", "CHILLY-RECEPTION", "SPICY-EXTRACT", "DECORATE", "LIFE-DEW",
                    "QUICK-GUARD", "WIDE-GUARD", "CRAFTY-SHIELD", "MAT-BLOCK", "SPLASH", "CELEBRATE", "HOLD-HANDS"):
            return True   # (situational: the foe doesn't pick these on its own)
        if name in ("TORMENT", "HEAL-BLOCK", "EMBARGO", "TELEKINESIS", "OCTOLOCK", "TAR-SHOT"):
            key = {"TORMENT": "tormented", "HEAL-BLOCK": "heal_block", "EMBARGO": "embargo", "TELEKINESIS": "telekinesis",
                   "OCTOLOCK": "octolock", "TAR-SHOT": "tar_shot"}[name]
            return bool(fv.get(key))
        if name in ("TRICK", "SWITCHEROO"):
            return not (self._item_of(attacker) or self._item_of(defender))
        if name == "GRAVITY":
            return bool(self.field().get("gravity"))
        if name == "MAGNET-RISE":
            return bool(v.get("magnet_rise"))
        return False

    def mv_power_preview(self, attacker, defender, name, d):
        """The power to show and to choose by (0 if it can't do damage now)."""
        if name in movelib.WEIGHT_MOVES or defender is None:
            return d.get("power") or 0
        return self.mv_prepare(attacker, defender, name, d, preview=True).get("power") or 0


def itemlib_consumed(item):
    from src.pokemon import items as itemlib
    return itemlib.consumed(item)
