# [REF-0091: Abilities in battle]
"""Abilities in battle (Jordan, 11-03): a mixin for TrainerBattleState, like battle_effects.py.

About 120 of the most common abilities work, as in the games (Gen 8 rules); the rest show their text
on the Summary and do nothing here yet (IMPLEMENTED lists the ones that work). Where they act:
- switching in: Intimidate, the weather setters, Download, Intrepid Sword, Dauntless Shield, Trace,
  Pressure / Mold Breaker / Unnerve messages;
- a move aimed at it: the absorbing abilities (Volt / Water Absorb, Flash Fire, Lightning Rod,
  Storm Drain, Motor Drive, Sap Sipper, Dry Skin, Earth Eater, Well-Baked Body), Levitate,
  Soundproof, Bulletproof, Overcoat, Good as Gold, Wonder Guard, Sturdy, Disguise;
- the damage: attack boosts (Huge Power, Guts, Hustle, Solar Power, the pinch abilities Blaze /
  Torrent / Overgrow / Swarm...), move boosts (Technician, Iron Fist, Strong Jaw, Tough Claws, Mega
  Launcher, Reckless, Sheer Force, Sand Force, the -ate abilities...), defences (Thick Fat, Heatproof,
  Filter, Multiscale, Fur Coat, Fluffy, Ice Scales...), Adaptability, Tinted Lens, Sniper, Scrappy;
- crits, accuracy and Speed: Battle Armor, Super Luck, Compound Eyes, No Guard, Sand Veil, Swift Swim,
  Chlorophyll, Sand Rush, Slush Rush, Quick Feet; priority: Prankster, Gale Wings, Triage;
- statuses and stat changes: Limber, Insomnia, Immunity, Water Veil, Magma Armor, Own Tempo,
  Oblivious, Inner Focus, Clear Body, Hyper Cutter, Keen Eye, Big Pecks, Simple, Contrary, Defiant,
  Competitive, Unaware;
- after a hit: Static, Flame Body, Poison Point, Effect Spore, Cute Charm, Rough Skin, Iron Barbs,
  Gooey, Weak Armor, Stamina, Justified, Rattled, Water Compaction, Anger Point, Poison Touch, Moxie,
  Beast Boost, Aftermath, Stench, Serene Grace, Shield Dust, Rock Head, Skill Link;
- end of turn: Speed Boost, Moody, Rain Dish, Ice Body, Dry Skin, Solar Power, Poison Heal, Shed Skin,
  Hydration, Bad Dreams; Magic Guard (no indirect damage); Truant;
- leaving: Natural Cure, Regenerator; running: Run Away, Shadow Tag / Arena Trap.
"""
import random

from src.pokemon import abilities as ablib

MOLD_BREAKERS = {"MOLDBREAKER", "TERAVOLT", "TURBOBLAZE"}
WEATHER_SETTERS = {"DRIZZLE": "RAIN", "DROUGHT": "SUN", "SANDSTREAM": "SAND", "SNOWWARNING": "SNOW"}
PINCH = {"BLAZE": "FIRE", "TORRENT": "WATER", "OVERGROW": "GRASS", "SWARM": "BUG"}
ATE = {"AERILATE": "FLYING", "PIXILATE": "FAIRY", "REFRIGERATE": "ICE", "GALVANIZE": "ELECTRIC"}
TYPE_BOOST = {"STEELWORKER": ("STEEL", 1.5), "TRANSISTOR": ("ELECTRIC", 1.3), "DRAGONSMAW": ("DRAGON", 1.5),
              "ROCKYPAYLOAD": ("ROCK", 1.5), "WATERBUBBLE": ("WATER", 2.0)}
# absorbing / immune abilities: type -> (ability, what happens)
ABSORB = {"VOLTABSORB": ("ELECTRIC", "heal"), "WATERABSORB": ("WATER", "heal"), "DRYSKIN": ("WATER", "heal"),
          "EARTHEATER": ("GROUND", "heal"), "FLASHFIRE": ("FIRE", "flash"), "LIGHTNINGROD": ("ELECTRIC", "SPATK"),
          "STORMDRAIN": ("WATER", "SPATK"), "MOTORDRIVE": ("ELECTRIC", "SPEED"), "SAPSIPPER": ("GRASS", "ATTACK"),
          "WELLBAKEDBODY": ("FIRE", "DEFENSE2")}
STATUS_IMMUNE = {"LIMBER": {"paralysis"}, "INSOMNIA": {"sleep"}, "VITALSPIRIT": {"sleep"}, "SWEETVEIL": {"sleep"},
                 "IMMUNITY": {"poison", "toxic"}, "PASTELVEIL": {"poison", "toxic"}, "WATERVEIL": {"burn"},
                 "WATERBUBBLE": {"burn"}, "THERMALEXCHANGE": {"burn"}, "MAGMAARMOR": {"freeze"},
                 "COMATOSE": {"paralysis", "sleep", "poison", "toxic", "burn", "freeze"},
                 "PURIFYINGSALT": {"paralysis", "sleep", "poison", "toxic", "burn", "freeze"}}
VOLATILE_IMMUNE = {"OWNTEMPO": "confusion", "OBLIVIOUS": "infatuation"}
CONTACT_STATUS = {"STATIC": "paralysis", "FLAMEBODY": "burn", "POISONPOINT": "poison"}
STAT_GUARD = {"CLEARBODY": None, "WHITESMOKE": None, "FULLMETALBODY": None, "HYPERCUTTER": "ATTACK",
              "KEENEYE": "ACCURACY", "BIGPECKS": "DEFENSE"}
SAND_PROOF = {"SANDVEIL", "SANDRUSH", "SANDFORCE", "OVERCOAT", "MAGICGUARD"}
INTIMIDATE_PROOF = {"INNERFOCUS", "OBLIVIOUS", "OWNTEMPO", "SCRAPPY"} | set(STAT_GUARD) - {"KEENEYE", "BIGPECKS"}
ANNOUNCE = {"PRESSURE": "{n} is exerting its pressure!", "MOLDBREAKER": "{n} breaks the mold!",
            "UNNERVE": "{n} is too nervous to eat Berries!", "TERAVOLT": "{n} is radiating a bursting aura!",
            "TURBOBLAZE": "{n} is radiating a blazing aura!", "AIRLOCK": "The effects of the weather disappeared.",
            "CLOUDNINE": "The effects of the weather disappeared.", "COMATOSE": "{n} is drowsing!"}

SURGE = {"ELECTRICSURGE": "electric", "GRASSYSURGE": "grassy", "MISTYSURGE": "misty", "PSYCHICSURGE": "psychic"}

IMPLEMENTED = (set(SURGE) | set(WEATHER_SETTERS) | set(PINCH) | set(ATE) | set(TYPE_BOOST) | set(ABSORB) | set(STATUS_IMMUNE)
               | set(VOLATILE_IMMUNE) | set(CONTACT_STATUS) | set(STAT_GUARD) | set(ANNOUNCE) | SAND_PROOF | {
    "INTIMIDATE", "DOWNLOAD", "INTREPIDSWORD", "DAUNTLESSSHIELD", "TRACE", "LEVITATE", "SOUNDPROOF",
    "BULLETPROOF", "GOODASGOLD", "WONDERGUARD", "STURDY", "DISGUISE", "HUGEPOWER", "PUREPOWER", "GUTS",
    "HUSTLE", "SOLARPOWER", "GORILLATACTICS", "DEFEATIST", "TECHNICIAN", "IRONFIST", "STRONGJAW",
    "TOUGHCLAWS", "MEGALAUNCHER", "RECKLESS", "SHEERFORCE", "SANDFORCE", "PUNKROCK", "TOXICBOOST",
    "FLAREBOOST", "THICKFAT", "HEATPROOF", "FILTER", "SOLIDROCK", "PRISMARMOR", "MULTISCALE",
    "SHADOWSHIELD", "FURCOAT", "MARVELSCALE", "FLUFFY", "ICESCALES", "PURIFYINGSALT", "ADAPTABILITY",
    "TINTEDLENS", "SNIPER", "SCRAPPY", "NORMALIZE", "BATTLEARMOR", "SHELLARMOR", "SUPERLUCK", "MERCILESS",
    "COMPOUNDEYES", "NOGUARD", "VICTORYSTAR", "SNOWCLOAK", "TANGLEDFEET", "SWIFTSWIM", "CHLOROPHYLL",
    "SLUSHRUSH", "QUICKFEET", "PRANKSTER", "GALEWINGS", "TRIAGE", "LEAFGUARD", "INNERFOCUS", "STEADFAST",
    "SIMPLE", "CONTRARY", "DEFIANT", "COMPETITIVE", "UNAWARE", "EFFECTSPORE", "CUTECHARM", "ROUGHSKIN",
    "IRONBARBS", "GOOEY", "TANGLINGHAIR", "WEAKARMOR", "STAMINA", "JUSTIFIED", "RATTLED", "WATERCOMPACTION",
    "STEAMENGINE", "ANGERPOINT", "BERSERK", "POISONTOUCH", "MOXIE", "CHILLINGNEIGH", "GRIMNEIGH",
    "BEASTBOOST", "AFTERMATH", "STENCH", "SERENEGRACE", "SHIELDDUST", "ROCKHEAD", "SKILLLINK", "SPEEDBOOST",
    "MOODY", "RAINDISH", "ICEBODY", "POISONHEAL", "SHEDSKIN", "HYDRATION", "BADDREAMS", "TRUANT",
    "NATURALCURE", "REGENERATOR", "RUNAWAY", "SHADOWTAG", "ARENATRAP", "MOLDBREAKER", "SYNCHRONIZE"})


class AbilityEffects:
    # ------------------------------------------------------------------ lookups
    def ab(self, mon):
        """The ability working now (Trace's copy for this battle, else its own)."""
        if not mon:
            return None
        return self.vol(mon).get("ability") or ablib.ability(self.game, mon)

    def def_ab(self, attacker, defender):
        """The defender's ability, unless the attacker's Mold Breaker ignores it."""
        if attacker is not defender and self.ab(attacker) in MOLD_BREAKERS:
            return None
        return self.ab(defender)

    def ab_name(self, mon):
        return ablib.name(self.game, self.ab(mon))

    def weather_now(self):
        """The weather, unless Cloud Nine / Air Lock is out."""
        if any(self.ab(m) in ("CLOUDNINE", "AIRLOCK") for m in (self.player_pokemon, self.opponent_pokemon) if m):
            return None
        return self.weather

    def _flags(self, name):
        return ablib.move_flags(self.game, name)

    # ------------------------------------------------------------------ switching in
    def ability_on_entry(self, mon):
        a, label, lines = self.ab(mon), self._label(mon), []
        foe = self._foe_of(mon)
        if not a:
            return lines
        if a in WEATHER_SETTERS and not self.weather_primal and self.weather != WEATHER_SETTERS[a]:
            self.set_weather(WEATHER_SETTERS[a])
            self._weather_announced = True
            lines.append(f"{label}'s {self.ab_name(mon)}!")
            lines.append(self.WEATHER_TEXT[self.weather][0])
        elif a == "INTIMIDATE" and foe:
            lines.append(f"{label}'s Intimidate!")
            fa = self.ab(foe)
            if fa in INTIMIDATE_PROOF:
                lines.append(f"{self._label(foe)}'s {self.ab_name(foe)} kept its Attack from falling!")
            else:
                lines += self.change_stages(foe, [["ATTACK", -1]], by_foe=True)
            if fa == "RATTLED":
                lines += self.change_stages(foe, [["SPEED", 1]])
        elif a == "DOWNLOAD" and foe:
            dfn = foe.stat_value("DEFENSE") * self.stat_mult(foe, "DEFENSE")
            sdf = foe.stat_value("SPDEF") * self.stat_mult(foe, "SPDEF")
            lines += [f"{label}'s Download!"] + self.change_stages(mon, [["SPATK" if sdf > dfn else "ATTACK", 1]])
        elif a == "INTREPIDSWORD":
            lines += [f"{label}'s Intrepid Sword!"] + self.change_stages(mon, [["ATTACK", 1]])
        elif a == "DAUNTLESSSHIELD":
            lines += [f"{label}'s Dauntless Shield!"] + self.change_stages(mon, [["DEFENSE", 1]])
        elif a == "TRACE" and foe:
            copy = self.ab(foe)
            if copy and copy not in ("TRACE", "MULTITYPE", "STANCECHANGE", "DISGUISE", "ZENMODE", "IMPOSTER"):
                self.vol(mon)["ability"] = copy
                lines.append(f"{label} traced {self._label(foe)}'s {ablib.name(self.game, copy)}!")
                lines += self.ability_on_entry(mon)
        elif a in SURGE:
            lines += [f"{label}'s {self.ab_name(mon)}!"] + self.set_terrain(SURGE[a])
        elif a in ANNOUNCE:
            lines.append(ANNOUNCE[a].format(n=label))
        return lines

    def ability_on_switch_out(self, mon):
        """Natural Cure and Regenerator, as it goes back."""
        a = self.ab(mon)
        if a == "NATURALCURE" and getattr(mon, "status", None):
            mon.cure_status()
        if a == "REGENERATOR" and mon.current_hp > 0:
            mon.current_hp = min(mon.get_max_hp(), mon.current_hp + mon.get_max_hp() // 3)

    def run_blocked(self):
        """Run Away always gets away; the foe's Shadow Tag / Arena Trap stop it."""
        me, foe = self.player_pokemon, self.opponent_pokemon
        if self.ab(me) == "RUNAWAY":
            return None
        fa = self.ab(foe)
        if fa == "SHADOWTAG" and self.ab(me) != "SHADOWTAG" or (
                fa == "ARENATRAP" and "FLYING" not in (me.types or []) and self.ab(me) != "LEVITATE"):
            return f"{self._label(foe)}'s {self.ab_name(foe)} prevents escape!"
        return None

    # ------------------------------------------------------------------ before the move lands
    def ability_move_type(self, attacker, d):
        """The -ate abilities and Normalize change the move's type (and power it up a little)."""
        a = self.ab(attacker)
        if not d.get("power"):
            return d
        if a in ATE and d.get("type") == "NORMAL":
            return dict(d, type=ATE[a], _ate=True)
        if a == "NORMALIZE":
            return dict(d, type="NORMAL", _ate=True)
        return d

    def ability_priority(self, mon, d):
        a = self.ab(mon)
        if a == "PRANKSTER" and d.get("category") == "STATUS":
            return 1
        if a == "GALEWINGS" and d.get("type") == "FLYING" and self._hp(mon) >= self._max_hp(mon):
            return 1
        if a == "TRIAGE" and ((d.get("drain") or 0) > 0 or d.get("category_meta") == "heal"):
            return 3
        return 0

    def ability_hits_always(self, attacker, defender):
        return "NOGUARD" in (self.ab(attacker), self.ab(defender))

    def ability_acc_mult(self, attacker, defender, d):
        a, fa, mult = self.ab(attacker), self.def_ab(attacker, defender), 1.0
        if a == "COMPOUNDEYES":
            mult *= 1.3
        if a == "VICTORYSTAR":
            mult *= 1.1
        if a == "HUSTLE" and d.get("category") == "PHYSICAL":
            mult *= 0.8
        w = self.weather_now()
        if (fa == "SANDVEIL" and w == "SAND") or (fa == "SNOWCLOAK" and w == "SNOW"):
            mult *= 0.8
        if fa == "TANGLEDFEET" and self.vol(defender).get("confused"):
            mult *= 0.5
        return mult

    def ability_immunity(self, attacker, defender, d):
        """The ability that stops this move outright (no side effects), or None."""
        if attacker is defender or d.get("target") in ("user", "users-field", "entire-field", "opponents-field"):
            return None
        fa = self.def_ab(attacker, defender)
        if not fa:
            return None
        t, name = d.get("type"), d.get("name")
        if fa in ABSORB and ABSORB[fa][0] == t:
            return fa
        if fa == "LEVITATE" and t == "GROUND" and (d.get("power") or 0):
            return fa
        flags = self._flags(name)
        if (fa == "SOUNDPROOF" and "sound" in flags) or (fa == "BULLETPROOF" and "bomb" in flags):
            return fa
        if fa == "OVERCOAT" and "powder" in flags:
            return fa
        if fa == "GOODASGOLD" and d.get("category") == "STATUS":
            return fa
        if fa == "STURDY" and d.get("category_meta") == "ohko":
            return fa
        return None

    def ability_absorb(self, attacker, defender, d):
        """Lines if the defender's ability takes the move (healing or a boost), else None."""
        fa = self.ability_immunity(attacker, defender, d)
        if not fa:
            return None
        label = self._label(defender)
        lines = [f"{label}'s {ablib.name(self.game, fa)}!"]
        kind = ABSORB.get(fa, (None, None))[1]
        mx = self._max_hp(defender)
        if kind == "heal":
            if self._hp(defender) < mx:
                self._adjust_hp(defender, max(1, mx // 4))
                return lines + [f"{label}'s HP was restored."]
            return lines + [f"It doesn't affect {label}..."]
        if kind == "flash":
            self.vol(defender)["flash_fire"] = True
            return lines + [f"The power of {label}'s Fire-type moves rose!"]
        if kind in ("SPATK", "SPEED", "ATTACK"):
            return lines + self.change_stages(defender, [[kind, 1]])
        if kind == "DEFENSE2":
            return lines + self.change_stages(defender, [["DEFENSE", 2]])
        return lines + [f"It doesn't affect {label}..."]

    def ability_effectiveness(self, attacker, defender, d, eff):
        """Scrappy: Normal and Fighting moves hit Ghosts."""
        if eff == 0 and self.ab(attacker) == "SCRAPPY" and d.get("type") in ("NORMAL", "FIGHTING") \
                and "GHOST" in (defender.types or []):
            from src.pokemon.mechanics import TypeAdvantage
            chart = TypeAdvantage(self.game.loader.area_data.get("TYPE_CHART", {}))
            others = [t for t in defender.types if t != "GHOST"]
            return chart.get_multiplier(d["type"], others) if others else 1.0
        return eff

    def ability_wonder_guard(self, attacker, defender, eff):
        return self.def_ab(attacker, defender) == "WONDERGUARD" and eff <= 1.0

    # ------------------------------------------------------------------ damage
    def ability_power_mult(self, attacker, defender, name, d):
        a, mult = self.ab(attacker), 1.0
        power, t, flags = d.get("power") or 0, d.get("type"), self._flags(name)
        if d.get("_ate"):
            mult *= 1.2
        if a in PINCH and PINCH[a] == t and self._hp(attacker) * 3 <= self._max_hp(attacker):
            mult *= 1.5
        if a == "TECHNICIAN" and power <= 60:
            mult *= 1.5
        if a == "IRONFIST" and "punch" in flags:
            mult *= 1.2
        if a == "STRONGJAW" and "bite" in flags:
            mult *= 1.5
        if a == "TOUGHCLAWS" and "contact" in flags:
            mult *= 1.3
        if a == "MEGALAUNCHER" and "pulse" in flags:
            mult *= 1.5
        if a == "PUNKROCK" and "sound" in flags:
            mult *= 1.3
        if a == "RECKLESS" and (d.get("drain") or 0) < 0:
            mult *= 1.2
        if a == "SHEERFORCE" and self._has_added_effect(d):
            mult *= 1.3
        if a == "SANDFORCE" and self.weather_now() == "SAND" and t in ("ROCK", "GROUND", "STEEL"):
            mult *= 1.3
        if a in TYPE_BOOST and TYPE_BOOST[a][0] == t:
            mult *= TYPE_BOOST[a][1]
        if self.vol(attacker).get("flash_fire") and t == "FIRE":
            mult *= 1.5
        status = getattr(attacker, "status", None)
        if a == "TOXICBOOST" and status in ("poison", "toxic") and d.get("category") == "PHYSICAL":
            mult *= 1.5
        if a == "FLAREBOOST" and status == "burn" and d.get("category") == "SPECIAL":
            mult *= 1.5
        return mult

    def ability_attack_mult(self, attacker, special):
        a, mult = self.ab(attacker), 1.0
        if not special and a in ("HUGEPOWER", "PUREPOWER"):
            mult *= 2
        if not special and a == "GUTS" and getattr(attacker, "status", None):
            mult *= 1.5
        if not special and a in ("HUSTLE", "GORILLATACTICS"):
            mult *= 1.5
        if special and a == "SOLARPOWER" and self.weather_now() in ("SUN", "HARSH_SUN"):
            mult *= 1.5
        if a == "DEFEATIST" and self._hp(attacker) * 2 <= self._max_hp(attacker):
            mult *= 0.5
        return mult

    def ability_defense_mult(self, attacker, defender, special):
        fa, mult = self.def_ab(attacker, defender), 1.0
        if not special and fa == "FURCOAT":
            mult *= 2
        if not special and fa == "MARVELSCALE" and getattr(defender, "status", None):
            mult *= 1.5
        return mult

    def ability_final_mult(self, attacker, defender, name, d, eff, crit, stab):
        a, fa, mult = self.ab(attacker), self.def_ab(attacker, defender), 1.0
        t, special, flags = d.get("type"), d.get("category") == "SPECIAL", self._flags(name)
        if a == "ADAPTABILITY" and stab:
            mult *= 2.0 / 1.5
        if a == "TINTEDLENS" and 0 < eff < 1:
            mult *= 2
        if a == "SNIPER" and crit:
            mult *= 1.5
        if fa == "THICKFAT" and t in ("FIRE", "ICE"):
            mult *= 0.5
        if fa in ("HEATPROOF", "WATERBUBBLE") and t == "FIRE":
            mult *= 0.5
        if fa in ("FILTER", "SOLIDROCK", "PRISMARMOR") and eff > 1:
            mult *= 0.75
        if fa in ("MULTISCALE", "SHADOWSHIELD") and self._hp(defender) >= self._max_hp(defender):
            mult *= 0.5
        if fa == "FLUFFY":
            mult *= (0.5 if "contact" in flags else 1) * (2 if t == "FIRE" else 1)
        if fa == "ICESCALES" and special:
            mult *= 0.5
        if fa == "PUNKROCK" and "sound" in flags:
            mult *= 0.5
        if fa == "DRYSKIN" and t == "FIRE":
            mult *= 1.25
        if fa == "PURIFYINGSALT" and t == "GHOST":
            mult *= 0.5
        return mult

    def ability_crit(self, attacker, defender, stage):
        """(stage, blocked): Super Luck +1; Battle Armor / Shell Armor stop crits; Merciless always."""
        if self.def_ab(attacker, defender) in ("BATTLEARMOR", "SHELLARMOR"):
            return stage, True
        a = self.ab(attacker)
        if a == "SUPERLUCK":
            stage += 1
        if a == "MERCILESS" and getattr(defender, "status", None) in ("poison", "toxic"):
            stage += 3
        return stage, False

    def ability_ignores_stages(self, mon, other):
        """Unaware: mon ignores other's stat stages."""
        return self.ab(mon) == "UNAWARE"

    def ability_survives(self, attacker, defender, damage, hp):
        """Sturdy and Disguise. Returns (damage, lines)."""
        fa = self.def_ab(attacker, defender)
        label = self._label(defender)
        if fa == "DISGUISE" and damage > 0 and not getattr(defender, "_disguise_busted", False):
            defender._disguise_busted = True
            return min(hp - 1, max(1, self._max_hp(defender) // 8)), [f"{label}'s disguise was busted!"]
        if fa == "STURDY" and damage >= hp and hp >= self._max_hp(defender):
            return hp - 1, [f"{label} endured the hit!", f"({label}'s Sturdy)"]
        return damage, []

    # ------------------------------------------------------------------ added effects
    @staticmethod
    def _has_added_effect(d):
        return bool((d.get("ailment_chance") or 0) or (d.get("flinch") or 0)
                    or (d.get("stat_chance") and d.get("category_meta") in ("damage-lower", "damage-raise")))

    def ability_effect_chance(self, attacker, defender, chance):
        """An added effect's chance: Serene Grace doubles it; Sheer Force and Shield Dust stop it."""
        if self.ab(attacker) == "SHEERFORCE" or self.def_ab(attacker, defender) == "SHIELDDUST":
            return 0
        return chance * 2 if self.ab(attacker) == "SERENEGRACE" else chance

    def ability_recoil_blocked(self, mon):
        return self.ab(mon) in ("ROCKHEAD", "MAGICGUARD")

    def ability_flinch(self, attacker, defender, chance):
        """Stench adds a 10% flinch; Inner Focus stops flinching."""
        if self.def_ab(attacker, defender) == "INNERFOCUS":
            return 0
        if not chance and self.ab(attacker) == "STENCH":
            chance = 10
        return self.ability_effect_chance(attacker, defender, chance)

    def ability_status_immune(self, target, ailment):
        a = self.ab(target)
        if ailment in STATUS_IMMUNE.get(a, ()):
            return True
        if a == "LEAFGUARD" and self.weather_now() in ("SUN", "HARSH_SUN") and ailment in movelib_statuses():
            return True
        return VOLATILE_IMMUNE.get(a) == ailment

    def ability_synchronize(self, target, ailment, source):
        """Synchronize passes a burn, paralysis or poison back to the one who caused it."""
        if self.ab(target) != "SYNCHRONIZE" or not source or source is target or ailment not in (
                "burn", "paralysis", "poison", "toxic") or getattr(source, "status", None) \
                or self.ability_status_immune(source, ailment):
            return []
        source.status = "poison" if ailment == "toxic" else ailment
        return [f"{self._label(target)}'s Synchronize!",
                self.STATUS_TEXT[source.status].format(n=self._label(source))]

    # ------------------------------------------------------------------ stat changes
    def ability_stage_filter(self, mon, changes, by_foe):
        """(changes, lines): Simple doubles, Contrary flips, Clear Body / Hyper Cutter / Keen Eye /
        Big Pecks stop the foe's drops."""
        a, label, lines = self.ab(mon), self._label(mon), []
        if a == "SIMPLE":
            changes = [[s, n * 2] for s, n in changes]
        if a == "CONTRARY":
            changes = [[s, -n] for s, n in changes]
        if by_foe and a in STAT_GUARD:
            guarded = STAT_GUARD[a]
            kept = [[s, n] for s, n in changes if n > 0 or (guarded and s != guarded)]
            if len(kept) != len(changes):
                lines.append(f"{label}'s {self.ab_name(mon)} prevents its stats from being lowered!")
            changes = kept
        return changes, lines

    def ability_after_drop(self, mon, by_foe, dropped):
        """Defiant / Competitive: a stat lowered by the foe sharply raises Attack / Sp. Atk."""
        a = self.ab(mon)
        if not (by_foe and dropped) or a not in ("DEFIANT", "COMPETITIVE"):
            return []
        stat = "ATTACK" if a == "DEFIANT" else "SPATK"
        st = self.stages(mon)
        st[stat] = min(6, st[stat] + 2)
        return [f"{self._label(mon)}'s {self.ab_name(mon)}!", f"{self._label(mon)}'s "
                f"{'Attack' if stat == 'ATTACK' else 'Sp. Atk'} rose sharply!"]

    # ------------------------------------------------------------------ after a hit
    def ability_after_hit(self, attacker, defender, name, d, damage, knocked_out):
        """Contact abilities, Moxie, the stat-on-hit abilities... Returns lines."""
        if not damage or attacker is defender:
            return []
        lines = []
        a, fa = self.ab(attacker), self.ab(defender)
        al, dl = self._label(attacker), self._label(defender)
        contact = "contact" in self._flags(name)
        t = d.get("type")
        # the defender's abilities
        if contact and self._hp(attacker) > 0:
            if fa in CONTACT_STATUS and random.random() < 0.3 and self._can_inflict(CONTACT_STATUS[fa], attacker):
                lines += [f"{dl}'s {self.ab_name(defender)}!", self._inflict(CONTACT_STATUS[fa], attacker, al)]
            elif fa == "EFFECTSPORE" and "GRASS" not in (attacker.types or []) and random.random() < 0.3:
                ail = random.choice(("poison", "paralysis", "sleep"))
                if self._can_inflict(ail, attacker):
                    lines += [f"{dl}'s Effect Spore!", self._inflict(ail, attacker, al)]
            elif fa == "CUTECHARM" and random.random() < 0.3:
                lines += self.ailment_effect("infatuation", name, defender, attacker, dl, al, chance=True) or []
            if fa in ("ROUGHSKIN", "IRONBARBS") and self.ab(attacker) != "MAGICGUARD":
                self._adjust_hp(attacker, -max(1, self._max_hp(attacker) // 8))
                lines.append(f"{al} was hurt by {dl}'s {self.ab_name(defender)}!")
            if fa in ("GOOEY", "TANGLINGHAIR"):
                lines += [f"{dl}'s {self.ab_name(defender)}!"] + self.change_stages(attacker, [["SPEED", -1]], by_foe=True)
            if fa == "AFTERMATH" and knocked_out and self.ab(attacker) != "MAGICGUARD":
                self._adjust_hp(attacker, -max(1, self._max_hp(attacker) // 4))
                lines.append(f"{al} was caught in the aftermath!")
        if not knocked_out:
            if fa == "WEAKARMOR" and d.get("category") == "PHYSICAL":
                lines += [f"{dl}'s Weak Armor!"] + self.change_stages(defender, [["DEFENSE", -1], ["SPEED", 2]])
            if fa == "STAMINA":
                lines += [f"{dl}'s Stamina!"] + self.change_stages(defender, [["DEFENSE", 1]])
            if fa == "JUSTIFIED" and t == "DARK":
                lines += [f"{dl}'s Justified!"] + self.change_stages(defender, [["ATTACK", 1]])
            if fa == "RATTLED" and t in ("BUG", "GHOST", "DARK"):
                lines += [f"{dl}'s Rattled!"] + self.change_stages(defender, [["SPEED", 1]])
            if fa == "WATERCOMPACTION" and t == "WATER":
                lines += [f"{dl}'s Water Compaction!"] + self.change_stages(defender, [["DEFENSE", 2]])
            if fa == "STEAMENGINE" and t in ("FIRE", "WATER"):
                lines += [f"{dl}'s Steam Engine!"] + self.change_stages(defender, [["SPEED", 6]])
            if fa == "ANGERPOINT" and getattr(self, "_last_was_crit", False):
                self.stages(defender)["ATTACK"] = 6
                lines.append(f"{dl}'s Anger Point maxed its Attack!")
            if fa == "BERSERK" and self._hp(defender) * 2 < self._max_hp(defender) \
                    and (self._hp(defender) + damage) * 2 >= self._max_hp(defender):
                lines += [f"{dl}'s Berserk!"] + self.change_stages(defender, [["SPATK", 1]])
            # the attacker's
            if a == "POISONTOUCH" and contact and random.random() < 0.3 and self._can_inflict("poison", defender):
                lines += [f"{al}'s Poison Touch!", self._inflict("poison", defender, dl)]
        elif self._hp(attacker) > 0:
            if a in ("MOXIE", "CHILLINGNEIGH"):
                lines += [f"{al}'s {self.ab_name(attacker)}!"] + self.change_stages(attacker, [["ATTACK", 1]])
            elif a == "GRIMNEIGH":
                lines += [f"{al}'s Grim Neigh!"] + self.change_stages(attacker, [["SPATK", 1]])
            elif a == "BEASTBOOST":
                best = max(("ATTACK", "DEFENSE", "SPATK", "SPDEF", "SPEED"), key=attacker.stat_value)
                lines += [f"{al}'s Beast Boost!"] + self.change_stages(attacker, [[best, 1]])
        return lines

    # ------------------------------------------------------------------ before moving
    def ability_loafs(self, mon):
        """Truant: every other turn it loafs around. Returns the line, or None."""
        if self.ab(mon) != "TRUANT":
            return None
        v = self.vol(mon)
        v["truant"] = not v.get("truant", False)
        return None if v["truant"] else f"{self._label(mon)} is loafing around!"

    # ------------------------------------------------------------------ the end of the turn
    def ability_status_chip(self, mon, status, chip):
        """(chip, line): Poison Heal heals instead; Magic Guard takes nothing."""
        a = self.ab(mon)
        if a == "POISONHEAL" and status in ("poison", "toxic"):
            mx = self._max_hp(mon)
            if self._hp(mon) < mx:
                self._adjust_hp(mon, max(1, mx // 8))
                return 0, f"{self._label(mon)}'s Poison Heal restored its HP!"
            return 0, None
        if a == "MAGICGUARD":
            return 0, None
        return chip, None

    def ability_sand_proof(self, mon):
        return self.ab(mon) in SAND_PROOF

    def ability_end_of_turn(self):
        lines = []
        w = self.weather_now()
        for mon in (self.player_pokemon, self.opponent_pokemon):
            if not mon or self._hp(mon) <= 0:
                continue
            a, label, mx = self.ab(mon), self._label(mon), self._max_hp(mon)
            heal = 0
            if a == "SPEEDBOOST" and self.stages(mon)["SPEED"] < 6:
                lines += [f"{label}'s Speed Boost!"] + self.change_stages(mon, [["SPEED", 1]])
            elif a == "MOODY":
                stats = ["ATTACK", "DEFENSE", "SPATK", "SPDEF", "SPEED"]
                up = random.choice([s for s in stats if self.stages(mon)[s] < 6] or stats)
                down = random.choice([s for s in stats if s != up])
                lines += [f"{label}'s Moody!"] + self.change_stages(mon, [[up, 2], [down, -1]])
            elif a == "RAINDISH" and w in ("RAIN", "HEAVY_RAIN"):
                heal = mx // 16
            elif a == "ICEBODY" and w == "SNOW":
                heal = mx // 16
            elif a == "DRYSKIN" and w in ("RAIN", "HEAVY_RAIN"):
                heal = mx // 8
            elif a in ("DRYSKIN", "SOLARPOWER") and w in ("SUN", "HARSH_SUN"):
                self._adjust_hp(mon, -max(1, mx // 8))
                lines.append(f"{label} is hurt by the sunlight! ({self.ab_name(mon)})")
            elif a in ("SHEDSKIN", "HYDRATION") and getattr(mon, "status", None) and (
                    (a == "SHEDSKIN" and random.random() < 1 / 3) or (a == "HYDRATION" and w in ("RAIN", "HEAVY_RAIN"))):
                mon.cure_status()
                lines.append(f"{label}'s {self.ab_name(mon)} cured its status!")
            elif a == "BADDREAMS":
                foe = self._foe_of(mon)
                if foe and self._hp(foe) > 0 and getattr(foe, "status", None) == "sleep" \
                        and self.ab(foe) != "MAGICGUARD":
                    self._adjust_hp(foe, -max(1, self._max_hp(foe) // 8))
                    lines.append(f"{self._label(foe)} is tormented by Bad Dreams!")
            if heal and self._hp(mon) < mx:
                self._adjust_hp(mon, max(1, heal))
                lines.append(f"{label}'s {self.ab_name(mon)} restored its HP.")
        return lines


def movelib_statuses():
    from src.pokemon import moves as movelib
    return movelib.STATUSES
