# [REF-0083: Move effects]
"""Moves' secondary effects in battle (Jordan: every move with its effects, as pokemondb.net/move/all
lists them; the data is in assets/moves.json, see dev/builders/build_move_effects.py).

A mixin for TrainerBattleState:
- stat stages (-6..+6) for Attack, Defense, Sp. Atk, Sp. Def, Speed, accuracy and evasion, with the
  games' multipliers and messages ("rose sharply!", "won't go any lower!"); they reset when a
  Pokemon leaves the field;
- volatile conditions: confusion, infatuation, trapping (Wrap, Fire Spin...), Leech Seed, Curse,
  Ingrain, Aqua Ring, Yawn, Perish Song, Taunt, Disable, Substitute, Protect / Endure, Focus Energy,
  rampaging moves (Thrash, Outrage), can't-escape (Mean Look);
- each side's field: Reflect, Light Screen, Aurora Veil, Safeguard, Mist, Tailwind, entry hazards
  (Spikes, Toxic Spikes, Stealth Rock, Sticky Web); the whole field: Trick Room, Mud / Water Sport;
- status moves of every kind (stat moves, confusion, healing, swagger, field moves, a set of unique
  moves) and the added effects of damaging moves (stat changes, confusion, trapping, rampage).

usable_status(d) says which status moves the game can use (src/pokemon/moves.py learns only those)."""
import random

STAGE_STATS = ("ATTACK", "DEFENSE", "SPATK", "SPDEF", "SPEED", "ACCURACY", "EVASION")
STAT_NAME = {"ATTACK": "Attack", "DEFENSE": "Defense", "SPATK": "Sp. Atk", "SPDEF": "Sp. Def",
             "SPEED": "Speed", "ACCURACY": "accuracy", "EVASION": "evasiveness"}
RISE = {1: "rose!", 2: "rose sharply!", 3: "rose drastically!"}
FALL = {1: "fell!", 2: "harshly fell!", 3: "severely fell!"}

PROTECT = {"PROTECT", "DETECT", "KINGS-SHIELD", "SPIKY-SHIELD", "BANEFUL-BUNKER", "OBSTRUCT", "SILK-TRAP",
           "BURNING-BULWARK", "MAX-GUARD"}
RAMPAGE = {"THRASH", "OUTRAGE", "PETAL-DANCE", "RAGING-FURY"}
CANT_ESCAPE = {"MEAN-LOOK", "BLOCK", "SPIDER-WEB"}
HAZARDS = {"SPIKES": "spikes", "TOXIC-SPIKES": "toxic_spikes", "STEALTH-ROCK": "stealth_rock", "STICKY-WEB": "sticky_web"}
SCREENS = {"REFLECT": ("reflect", 5, "Reflect"), "LIGHT-SCREEN": ("light_screen", 5, "Light Screen"),
           "AURORA-VEIL": ("aurora_veil", 5, "Aurora Veil"), "SAFEGUARD": ("safeguard", 5, "Safeguard"),
           "MIST": ("mist", 5, "the mist"), "TAILWIND": ("tailwind", 4, "the tailwind"),
           "LUCKY-CHANT": ("lucky_chant", 5, "Lucky Chant")}
WEATHER_HEAL = {"MOONLIGHT", "MORNING-SUN", "SYNTHESIS"}
# Unique status moves this game runs (everything else that does nothing here isn't learned).
UNIQUE = {"SPLASH", "CELEBRATE", "HOLD-HANDS", "TELEPORT", "FOCUS-ENERGY", "BELLY-DRUM", "ENDURE", "REST",
          "SUBSTITUTE", "PAIN-SPLIT", "METRONOME", "CURSE", "AQUA-RING", "WISH", "HEAL-BELL", "AROMATHERAPY",
          "REFRESH", "PSYCH-UP", "TAUNT", "DISABLE", "STRENGTH-SAP", "STOCKPILE", "HAZE", "TRICK-ROOM",
          "MUD-SPORT", "WATER-SPORT", "ROAR", "WHIRLWIND", "LASER-FOCUS", "JUNGLE-HEALING", "LUNAR-BLESSING",
          "TAKE-HEART", "TIDY-UP", "SHELL-SMASH", "FILLET-AWAY", "CLANGOROUS-SOUL", "NO-RETREAT",
          "VICTORY-DANCE"} | PROTECT | CANT_ESCAPE | set(HAZARDS) | set(SCREENS) | WEATHER_HEAL
SUPPORTED_AILMENTS = {"paralysis", "sleep", "freeze", "burn", "poison", "confusion", "infatuation", "trap",
                      "leech-seed", "yawn", "perish-song", "ingrain", "disable"}


def usable_status(d):
    """A status move this game can run: stat moves, a status condition it knows, healing,
    Swagger/Flatter, field moves and the unique moves above."""
    name = d.get("name")
    meta = d.get("category_meta")
    if name in UNIQUE:
        return True
    if meta in ("net-good-stats", "heal", "swagger"):
        return True
    if meta == "ailment" and d.get("ailment") in SUPPORTED_AILMENTS:
        return True
    return bool(d.get("stat_changes")) and meta not in ("whole-field-effect", "field-effect")


def stage_mult(s):
    return (2 + s) / 2 if s >= 0 else 2 / (2 - s)


def acc_stage_mult(s):
    return (3 + s) / 3 if s >= 0 else 3 / (3 - s)


class MoveEffects:
    # ------------------------------------------------------------------ state
    def _fx(self):
        return self.__dict__.setdefault("_fx_state", {"stages": {}, "vol": {}, "side": {"player": {}, "opponent": {}},
                                                      "field": {}})

    def stages(self, mon):
        return self._fx()["stages"].setdefault(id(mon), dict.fromkeys(STAGE_STATS, 0))

    def vol(self, mon):
        return self._fx()["vol"].setdefault(id(mon), {})

    def side_of(self, mon):
        return "player" if mon is self.player_pokemon else "opponent"

    def side(self, mon):
        return self._fx()["side"][self.side_of(mon)]

    def field(self):
        return self._fx()["field"]

    def _label(self, mon):
        return mon.display_name.upper() if mon is self.player_pokemon else f"Foe {mon.display_name.upper()}"

    def _foe_of(self, mon):
        return self.opponent_pokemon if mon is self.player_pokemon else self.player_pokemon

    def _hp(self, mon):  # (the Pokemon's own HP until the battle has set up its bars)
        return getattr(self, "player_hp" if mon is self.player_pokemon else "opponent_hp", mon.current_hp)

    def _max_hp(self, mon):
        return getattr(self, "player_max_hp" if mon is self.player_pokemon else "opp_max_hp", None) or mon.get_max_hp()

    def forget_switched_out(self):
        """Stat stages and volatile conditions end when a Pokemon leaves the field (the field
        conditions of each side stay)."""
        active = {id(self.player_pokemon), id(self.opponent_pokemon)}
        for table in (self._fx()["stages"], self._fx()["vol"]):
            for k in [k for k in table if k not in active]:
                table.pop(k)

    # ------------------------------------------------------------------ stat stages
    def stat_mult(self, mon, stat, crit=False, attacking=True):
        s = self.stages(mon)[stat]
        if crit:  # a critical hit ignores the attacker's drops and the defender's boosts
            s = max(0, s) if attacking else min(0, s)
        return stage_mult(s)

    def acc_mult(self, attacker, defender):
        s = max(-6, min(6, self.stages(attacker)["ACCURACY"] - self.stages(defender)["EVASION"]))
        return acc_stage_mult(s)

    def speed_mult(self, mon):
        mult = stage_mult(self.stages(mon)["SPEED"])
        if self.side(mon).get("tailwind"):
            mult *= 2
        return mult

    def change_stages(self, mon, changes, by_foe=False):
        """Apply [[STAT, n], ...] to mon. Returns the game's messages."""
        lines = []
        label = self._label(mon)
        if by_foe and any(n < 0 for _, n in changes):
            if self.side(mon).get("mist"):
                return [f"{label} is protected by the mist!"]
            if self.vol(mon).get("substitute"):
                return [f"But it failed!"]
        st = self.stages(mon)
        for stat, n in changes:
            if stat not in st:
                continue
            new = max(-6, min(6, st[stat] + n))
            name = STAT_NAME[stat]
            if new == st[stat]:
                lines.append(f"{label}'s {name} won't go any {'higher' if n > 0 else 'lower'}!")
                continue
            st[stat] = new
            lines.append(f"{label}'s {name} {(RISE if n > 0 else FALL)[min(3, abs(n))]}")
        return lines

    # ------------------------------------------------------------------ before moving
    def before_move(self, mon):
        """Confusion and infatuation can stop a move. Returns (stopped, lines)."""
        v, label, lines = self.vol(mon), self._label(mon), []
        if v.get("confused"):
            v["confused"] -= 1
            if v["confused"] <= 0:
                v.pop("confused")
                lines.append(f"{label} snapped out of its confusion!")
            else:
                lines.append(f"{label} is confused!")
                if random.random() < 1 / 3:
                    atk = mon.stat_value("ATTACK") * self.stat_mult(mon, "ATTACK")
                    dfn = mon.stat_value("DEFENSE") * self.stat_mult(mon, "DEFENSE")
                    lvl = self._level(mon)
                    dmg = max(1, int(((2 * lvl / 5 + 2) * 40 * atk / max(1, dfn)) / 50 + 2))
                    self._adjust_hp(mon, -dmg)
                    return True, lines + ["It hurt itself in its confusion!"]
        if v.get("infatuated") and random.random() < 0.5:
            return True, lines + [f"{label} is in love with the foe!", f"{label} is immobilized by love!"]
        return False, lines

    def forced_effect_move(self, mon):
        """A rampage keeps going (Thrash, Outrage) whatever was picked."""
        r = self.vol(mon).get("rampage")
        return r[0] if r else None

    def move_blocked(self, mon, name, d):
        """Taunt and Disable stop some moves. Returns the message, or None."""
        v = self.vol(mon)
        if v.get("taunt") and not (d.get("power") or 0):
            return f"{self._label(mon)} can't use {name.replace('-', ' ')} after the taunt!"
        dis = v.get("disabled")
        if dis and dis[0] == name:
            return f"{self._label(mon)}'s {name.replace('-', ' ')} is disabled!"
        return None

    def protected(self, attacker, defender, d):
        """Protect / Detect: moves aimed at the protected Pokemon fail this turn."""
        if attacker is defender or not self.vol(defender).get("protected"):
            return False
        return d.get("target") not in ("user", "users-field", "user-and-allies", "entire-field", "opponents-field")

    # ------------------------------------------------------------------ status moves
    def status_effect(self, name, d, attacker, defender, att_label, def_label):
        """Run a status move (power 0). Returns its lines, or None if this game doesn't know it."""
        meta, target = d.get("category_meta"), d.get("target")
        v, fv = self.vol(attacker), self.vol(defender)
        self_target = target in ("user", "users-field", "user-and-allies", "all-allies", "user-or-ally")
        fail = ["But it failed!"]
        if name in PROTECT:
            streak = v.get("protect_streak", 0)
            if getattr(self, "_acts_second", None) == id(attacker) or random.random() >= (1 / 3) ** streak:
                v["protect_streak"] = 0
                return fail
            v["protected"], v["protect_streak"] = True, streak + 1
            return [f"{att_label} protected itself!"]
        v["protect_streak"] = 0
        if name == "ENDURE":
            v["endure"] = True
            return [f"{att_label} braced itself!"]
        if name in ("SPLASH", "CELEBRATE", "HOLD-HANDS"):
            return ["But nothing happened!"]
        if name == "TELEPORT" or name in ("ROAR", "WHIRLWIND"):
            if self.trainer_class == "WILD":
                self._flee_by_move = attacker
                return ([f"{att_label} teleported away!"] if name == "TELEPORT"
                        else [f"{def_label} was blown away!"])
            return fail
        if name in CANT_ESCAPE:
            fv["no_escape"] = True
            return [f"{def_label} can no longer escape!"]
        if name in HAZARDS:
            key = HAZARDS[name]
            foe_side = self.side(defender)
            layers = foe_side.get(key, 0)
            cap = {"spikes": 3, "toxic_spikes": 2}.get(key, 1)
            if layers >= cap:
                return fail
            foe_side[key] = layers + 1
            return {"spikes": ["Spikes were scattered around the foe's feet!"],
                    "toxic_spikes": ["Poison spikes were scattered around the foe's feet!"],
                    "stealth_rock": ["Pointed stones float in the air around the foe!"],
                    "sticky_web": ["A sticky web spreads out on the ground around the foe!"]}[key]
        if name in SCREENS:
            key, turns, label = SCREENS[name]
            my_side = self.side(attacker)
            if my_side.get(key) or (name == "AURORA-VEIL" and getattr(self, "weather", None) != "SNOW"):
                return fail
            my_side[key] = turns
            team = "Your team" if attacker is self.player_pokemon else "The foe's team"
            return [f"{team} is covered by {label}!" if key != "tailwind" else f"The tailwind blew from behind {team.lower()}!"]
        if name == "TRICK-ROOM":
            f = self.field()
            if f.get("trick_room"):
                f.pop("trick_room")
                return ["The twisted dimensions returned to normal!"]
            f["trick_room"] = 5
            return [f"{att_label} twisted the dimensions!"]
        if name in ("MUD-SPORT", "WATER-SPORT"):
            self.field()[name.lower().replace("-", "_")] = 5
            return ["Electricity's power was weakened!" if name == "MUD-SPORT" else "Fire's power was weakened!"]
        if name == "HAZE":
            for mon in (self.player_pokemon, self.opponent_pokemon):
                self.stages(mon).update(dict.fromkeys(STAGE_STATS, 0))
            return ["All stat changes were eliminated!"]
        if name == "FOCUS-ENERGY":
            if v.get("focus"):
                return fail
            v["focus"] = 2
            return [f"{att_label} is getting pumped!"]
        if name == "LASER-FOCUS":
            v["laser_focus"] = 2
            return [f"{att_label} concentrated intensely!"]
        if name == "BELLY-DRUM":
            hp, mx = self._hp(attacker), self._max_hp(attacker)
            if hp <= mx // 2 or self.stages(attacker)["ATTACK"] >= 6:
                return fail
            self._adjust_hp(attacker, -(mx // 2))
            self.stages(attacker)["ATTACK"] = 6
            return [f"{att_label} cut its own HP and maximized its Attack!"]
        if name == "REST":
            mx = self._max_hp(attacker)
            if self._hp(attacker) >= mx:
                return fail
            self._adjust_hp(attacker, mx)
            attacker.status, attacker.sleep_turns = "sleep", 2
            return [f"{att_label} slept and became healthy!"]
        if name == "SUBSTITUTE":
            mx = self._max_hp(attacker)
            if v.get("substitute") or self._hp(attacker) <= mx // 4:
                return [f"{att_label} doesn't have enough HP left to make a substitute!"] if not v.get("substitute") \
                    else [f"{att_label} already has a substitute!"]
            self._adjust_hp(attacker, -(mx // 4))
            v["substitute"] = mx // 4
            return [f"{att_label} put in a substitute!"]
        if name == "PAIN-SPLIT":
            avg = (self._hp(attacker) + self._hp(defender)) // 2
            self._adjust_hp(attacker, avg - self._hp(attacker))
            self._adjust_hp(defender, avg - self._hp(defender))
            return ["The battlers shared their pain!"]
        if name == "METRONOME":
            from src.pokemon import moves as movelib
            pool = [k for k, m in movelib.table(self.game).items()
                    if (m.get("power") or 0) > 0 and k not in movelib.SELF_KO and m.get("category_meta") != "ohko"
                    and k not in movelib.TWO_TURN]
            pick = random.choice(pool) if pool else movelib.FALLBACK
            self._metronome = pick
            return [f"Waggling a finger let it use {pick.replace('-', ' ')}!"]
        if name == "CURSE":
            if "GHOST" in (attacker.types or []):
                if fv.get("cursed"):
                    return fail
                self._adjust_hp(attacker, -(self._max_hp(attacker) // 2))
                fv["cursed"] = True
                return [f"{att_label} cut its own HP and put a curse on {def_label}!"]
            return self.change_stages(attacker, [["SPEED", -1], ["ATTACK", 1], ["DEFENSE", 1]])
        if name == "AQUA-RING":
            v["aqua_ring"] = True
            return [f"{att_label} surrounded itself with a veil of water!"]
        if name == "WISH":
            if self.side(attacker).get("wish"):
                return fail
            self.side(attacker)["wish"] = (2, max(1, self._max_hp(attacker) // 2), att_label)
            return [f"{att_label} made a wish!"]
        if name in ("HEAL-BELL", "AROMATHERAPY"):
            team = self.game.story_manager.player_team if attacker is self.player_pokemon else self.opponent_team
            for p in team:
                if p and getattr(p, "status", None):
                    p.cure_status()
            return ["A bell chimed!" if name == "HEAL-BELL" else "A soothing aroma wafted through the area!"]
        if name in ("REFRESH", "TAKE-HEART", "JUNGLE-HEALING", "LUNAR-BLESSING"):
            lines = []
            if name in ("JUNGLE-HEALING", "LUNAR-BLESSING"):
                self._adjust_hp(attacker, max(1, self._max_hp(attacker) // 4))
                lines.append(f"{att_label}'s HP was restored.")
            if getattr(attacker, "status", None) and (name != "REFRESH" or attacker.status in ("burn", "poison", "toxic", "paralysis")):
                attacker.cure_status()
                lines.append(f"{att_label}'s status returned to normal!")
            if name == "TAKE-HEART":
                lines += self.change_stages(attacker, [["SPATK", 1], ["SPDEF", 1]])
            return lines or fail
        if name == "PSYCH-UP":
            self.stages(attacker).update(self.stages(defender))
            return [f"{att_label} copied {def_label}'s stat changes!"]
        if name == "TAUNT":
            if fv.get("taunt"):
                return fail
            fv["taunt"] = 3
            return [f"{def_label} fell for the taunt!"]
        if name == "DISABLE":
            last = fv.get("last_move")
            if not last or fv.get("disabled"):
                return fail
            fv["disabled"] = (last, 4)
            return [f"{def_label}'s {last.replace('-', ' ')} was disabled!"]
        if name == "STRENGTH-SAP":
            if self.stages(defender)["ATTACK"] <= -6:
                return fail
            heal = int(defender.stat_value("ATTACK") * self.stat_mult(defender, "ATTACK"))
            self._adjust_hp(attacker, heal)
            return [f"{att_label} drained {def_label}'s strength!"] + self.change_stages(defender, [["ATTACK", -1]], by_foe=True)
        if name == "STOCKPILE":
            n = v.get("stockpile", 0)
            if n >= 3:
                return fail
            v["stockpile"] = n + 1
            return [f"{att_label} stockpiled {n + 1}!"] + self.change_stages(attacker, [["DEFENSE", 1], ["SPDEF", 1]])
        if meta == "heal" or name in WEATHER_HEAL:
            mx = self._max_hp(attacker)
            if self._hp(attacker) >= mx:
                return [f"{att_label}'s HP is full!"]
            pct = d.get("healing") or 50
            if name in WEATHER_HEAL:
                w = getattr(self, "weather", None)
                pct = 66 if w in ("SUN", "HARSH_SUN") else 25 if w else 50
            self._adjust_hp(attacker, max(1, mx * pct // 100))
            return [f"{att_label} regained health!"]
        if meta == "swagger":
            if fv.get("substitute"):
                return fail
            lines = self.change_stages(defender, d.get("stat_changes") or [], by_foe=False)
            if not fv.get("confused") and not self.side(defender).get("safeguard"):
                fv["confused"] = random.randint(2, 5)
                lines.append(f"{def_label} became confused!")
            return lines
        if meta == "ailment":
            return self.ailment_effect(d.get("ailment"), name, attacker, defender, att_label, def_label)
        if d.get("stat_changes"):  # stat moves (Growl, Swords Dance, Shell Smash...)
            if self_target or meta == "net-good-stats" and all(n > 0 for _, n in d["stat_changes"]) \
                    and target not in ("selected-pokemon", "all-opponents", "random-opponent"):
                lines = self.change_stages(attacker, d["stat_changes"])
                if name in ("FILLET-AWAY", "CLANGOROUS-SOUL"):
                    self._adjust_hp(attacker, -(self._max_hp(attacker) // (2 if name == "FILLET-AWAY" else 3)))
                return lines
            if fv.get("substitute"):
                return fail
            return self.change_stages(defender, d["stat_changes"], by_foe=True)
        return None

    def ailment_effect(self, ailment, name, attacker, defender, att_label, def_label, chance=False):
        """Confusion, infatuation, trapping, Leech Seed, Yawn... (the main statuses are the battle's)."""
        fv = self.vol(defender)
        fail = [] if chance else ["But it failed!"]
        if fv.get("substitute") and not chance and attacker is not defender:
            return fail
        if ailment == "confusion":
            if fv.get("confused") or self.side(defender).get("safeguard"):
                return [] if chance else [f"{def_label} is already confused!"]
            fv["confused"] = random.randint(2, 5)
            return [f"{def_label} became confused!"]
        if ailment == "infatuation":
            if fv.get("infatuated"):
                return fail
            fv["infatuated"] = True
            return [f"{def_label} fell in love!"]
        if ailment == "trap":
            if fv.get("trapped"):
                return []
            fv["trapped"] = (random.randint(4, 5), name.replace("-", " "))
            return [f"{def_label} was trapped by {name.replace('-', ' ').title()}!"]
        if ailment == "leech-seed":
            if "GRASS" in (defender.types or []) or fv.get("seeded"):
                return [f"It doesn't affect {def_label}..."] if not chance else []
            fv["seeded"] = True
            return [f"{def_label} was seeded!"]
        if ailment == "yawn":
            if getattr(defender, "status", None) or fv.get("drowsy"):
                return fail
            fv["drowsy"] = 2
            return [f"{att_label} made {def_label} drowsy!"]
        if ailment == "perish-song":
            for mon in (self.player_pokemon, self.opponent_pokemon):
                self.vol(mon).setdefault("perish", 4)
            return ["All Pokemon that hear the song will faint in three turns!"]
        if ailment == "ingrain":
            self.vol(attacker)["ingrain"] = True
            self.vol(attacker)["no_escape"] = True
            return [f"{att_label} planted its roots!"]
        if ailment == "disable":
            return self.status_effect("DISABLE", {}, attacker, defender, att_label, def_label)
        return None

    # ------------------------------------------------------------------ after a hit
    def after_hit(self, name, d, attacker, defender, att_label, def_label, damage, defender_survives):
        """Added effects of a damaging move. Returns lines."""
        lines = []
        meta = d.get("category_meta")
        changes = d.get("stat_changes") or []
        chance = d.get("stat_chance") or (100 if meta in ("damage-raise", "damage-lower") else 0)
        if changes and damage and random.uniform(0, 100) < chance:
            if meta == "damage-raise" or d.get("target") == "user":
                lines += self.change_stages(attacker, changes)
            elif defender_survives:
                lines += self.change_stages(defender, changes, by_foe=True)
        ail = d.get("ailment")
        if (damage and defender_survives and ail in ("confusion", "trap", "infatuation", "leech-seed")
                and random.uniform(0, 100) < (d.get("ailment_chance") or 100)):
            lines += self.ailment_effect(ail, name, attacker, defender, att_label, def_label, chance=True) or []
        if name in RAMPAGE and damage:
            v = self.vol(attacker)
            if not v.get("rampage"):
                v["rampage"] = [name, random.randint(2, 3)]
        if name == "RAPID-SPIN" and damage:
            v = self.vol(attacker)
            v.pop("trapped", None)
            v.pop("seeded", None)
            for key in HAZARDS.values():
                self.side(attacker).pop(key, None)
        return lines

    def end_rampage_turn(self, mon):
        """A rampage counts down after each use; when it ends the user becomes confused."""
        v = self.vol(mon)
        r = v.get("rampage")
        if not r:
            return []
        r[1] -= 1
        if r[1] > 0:
            return []
        v.pop("rampage")
        if v.get("confused"):
            return []
        v["confused"] = random.randint(2, 5)
        return [f"{self._label(mon)} became confused due to fatigue!"]

    def absorb_with_substitute(self, defender, damage, def_label):
        """A substitute takes the hit. Returns (damage to the Pokemon, lines)."""
        v = self.vol(defender)
        sub = v.get("substitute")
        if not sub or damage <= 0:
            return damage, []
        if damage >= sub:
            v.pop("substitute")
            return 0, [f"The substitute took damage for {def_label}!", f"{def_label}'s substitute faded!"]
        v["substitute"] = sub - damage
        return 0, [f"The substitute took damage for {def_label}!"]

    # ------------------------------------------------------------------ switch-in
    def entry_hazards(self, mon):
        """Spikes, Toxic Spikes, Stealth Rock and Sticky Web hurt / slow a Pokemon switching in."""
        s, label, lines = self.side(mon), self._label(mon), []
        if not any(s.get(k) for k in HAZARDS.values()):
            return lines  # (also: the battle's HP isn't set up yet when the first Pokemon come out)
        flying = "FLYING" in (mon.types or [])
        mx = self._max_hp(mon)
        if s.get("stealth_rock"):  # 1/8 of max HP, times Rock's effectiveness on it
            from src.pokemon.mechanics import TypeAdvantage
            chart = TypeAdvantage(self.game.loader.area_data.get("TYPE_CHART", {}))
            dmg = max(1, int(mx * chart.get_multiplier("ROCK", mon.types) / 8))
            self._adjust_hp(mon, -dmg)
            lines.append(f"Pointed stones dug into {label}!")
        if s.get("spikes") and not flying:  # 1/8, 1/6, 1/4 for 1-3 layers
            dmg = max(1, mx // {1: 8, 2: 6, 3: 4}[s["spikes"]])
            self._adjust_hp(mon, -dmg)
            lines.append(f"{label} is hurt by the spikes!")
        if s.get("toxic_spikes") and not flying:
            if "POISON" in (mon.types or []):
                s.pop("toxic_spikes")
                lines.append("The poison spikes disappeared from the ground!")
            elif not getattr(mon, "status", None) and "STEEL" not in (mon.types or []):
                mon.status = "toxic" if s["toxic_spikes"] >= 2 else "poison"
                lines.append(f"{label} was {'badly ' if s['toxic_spikes'] >= 2 else ''}poisoned!")
        if s.get("sticky_web") and not flying:
            lines += [f"{label} was caught in a sticky web!"] + self.change_stages(mon, [["SPEED", -1]])
        return lines

    # ------------------------------------------------------------------ end of turn
    def effects_end_of_turn(self):
        """Leech Seed, trapping, Curse, Ingrain / Aqua Ring, Yawn, Wish, Perish Song, and the field
        timers. Returns lines."""
        lines = []
        for mon in (self.player_pokemon, self.opponent_pokemon):
            if not mon or self._hp(mon) <= 0:
                continue
            v, label, mx = self.vol(mon), self._label(mon), self._max_hp(mon)
            v.pop("protected", None)
            v.pop("endure", None)
            if v.get("aqua_ring") and self._hp(mon) < mx:
                self._adjust_hp(mon, max(1, mx // 16))
                lines.append(f"A veil of water restored {label}'s HP!")
            if v.get("ingrain") and self._hp(mon) < mx:
                self._adjust_hp(mon, max(1, mx // 16))
                lines.append(f"{label} absorbed nutrients with its roots!")
            if v.get("seeded"):
                sap = min(self._hp(mon), max(1, mx // 8))
                self._adjust_hp(mon, -sap)
                other = self._foe_of(mon)
                if other and self._hp(other) > 0:
                    self._adjust_hp(other, sap)
                lines.append(f"{label}'s health is sapped by Leech Seed!")
            if v.get("trapped"):
                turns, move = v["trapped"]
                self._adjust_hp(mon, -max(1, mx // 8))
                lines.append(f"{label} is hurt by {move.title()}!")
                if turns <= 1:
                    v.pop("trapped")
                    lines.append(f"{label} was freed from {move.title()}!")
                else:
                    v["trapped"] = (turns - 1, move)
            if v.get("cursed"):
                self._adjust_hp(mon, -max(1, mx // 4))
                lines.append(f"{label} is afflicted by the curse!")
            if v.get("drowsy"):
                v["drowsy"] -= 1
                if v["drowsy"] <= 0:
                    v.pop("drowsy")
                    if not getattr(mon, "status", None):
                        mon.status, mon.sleep_turns = "sleep", random.randint(1, 3)
                        lines.append(f"{label} fell asleep!")
            if v.get("perish"):
                v["perish"] -= 1
                lines.append(f"{label}'s perish count fell to {v['perish']}!")
                if v["perish"] <= 0:
                    self._adjust_hp(mon, -self._hp(mon))
            for key in ("taunt",):
                if v.get(key):
                    v[key] -= 1
                    if v[key] <= 0:
                        v.pop(key)
                        lines.append(f"{label} shook off the taunt!")
            if v.get("disabled"):
                move, turns = v["disabled"]
                if turns <= 1:
                    v.pop("disabled")
                    lines.append(f"{label}'s {move.replace('-', ' ')} is no longer disabled!")
                else:
                    v["disabled"] = (move, turns - 1)
            if v.get("laser_focus"):
                v["laser_focus"] -= 1
                if v["laser_focus"] <= 0:
                    v.pop("laser_focus")
        for side_name in ("player", "opponent"):
            s = self._fx()["side"][side_name]
            team = "Your team's" if side_name == "player" else "The foe's"
            wish = s.get("wish")
            if wish:
                turns, heal, who = wish
                if turns <= 1:
                    s.pop("wish")
                    mon = self.player_pokemon if side_name == "player" else self.opponent_pokemon
                    if mon and self._hp(mon) > 0:
                        self._adjust_hp(mon, heal)
                        lines.append(f"{who}'s wish came true!")
                else:
                    s["wish"] = (turns - 1, heal, who)
            for key, (_k, _t, label) in {SCREENS[n][0]: SCREENS[n] for n in SCREENS}.items():
                if s.get(key):
                    s[key] -= 1
                    if s[key] <= 0:
                        s.pop(key)
                        lines.append(f"{team} {label} wore off!" if key != "tailwind" else f"{team} tailwind petered out!")
        f = self.field()
        for key, text in (("trick_room", "The twisted dimensions returned to normal!"),
                          ("mud_sport", "The effects of Mud Sport have faded."),
                          ("water_sport", "The effects of Water Sport have faded.")):
            if f.get(key):
                f[key] -= 1
                if f[key] <= 0:
                    f.pop(key)
                    lines.append(text)
        return lines
