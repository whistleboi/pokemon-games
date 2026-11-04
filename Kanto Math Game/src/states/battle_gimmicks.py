# [REF-0096: Z-Moves and Terastal in battle]
"""The Z-MOVE and TERA buttons (Jordan, 11-03): a mixin for TrainerBattleState. The rules are in
src/pokemon/zpower.py. Each works once per battle, like Mega Evolution.

- Z-MOVE: the Pokemon holds a Z-Crystal; its next damaging move of that type becomes its Z-Move.
- TERA (in Paldea only, for now): the Pokemon becomes its Tera Type until the battle ends.
- Foes: Alola's Kahunas and Captains use a Z-Move; Paldea's Leaders, Elite Four and Champion
  Terastallize their last Pokemon into their Gym's type."""
from src.pokemon import zpower, moves as movelib

LEADERS = ("GYM_LEADER", "ELITE_FOUR", "CHAMPION")


class GimmickEffects:
    def _gimmicks(self):
        return self.__dict__.setdefault("_gimmick_state", {"z_used": {}, "tera_used": {}, "z_armed": set()})

    # ------------------------------------------------------------------ Z-Moves
    def _z_moves_for(self, mon):
        """The moves this Pokemon could turn into Z-Moves now (the type of the Z-Crystal it holds)."""
        held = zpower.held_crystal_type(mon)
        return [m for m in movelib.ensure_moves(self.game, mon)
                if held and (movelib.info(self.game, m).get("power") or 0) > 0
                and movelib.info(self.game, m).get("type") == held]

    def z_option(self):
        """True if the Z-MOVE button should show."""
        story = self.game.story_manager
        mon = self.player_pokemon
        if getattr(self, "starter_battle", False) or not mon or not story.inventory.get(zpower.Z_RING):
            return False
        if self._gimmicks()["z_used"].get("player") or id(mon) in self._gimmicks()["z_armed"]:
            return False
        return bool(self._z_moves_for(mon))

    def activate_z(self):
        """Z-MOVE: the next damaging move with a Z-Crystal becomes its Z-Move."""
        if not self.z_option() or self.phase != "MENU":
            return
        self._gimmicks()["z_armed"].add(id(self.player_pokemon))
        self.setup_action_menu()
        self.show_message([f"{self.player_pokemon.display_name.upper()} is surrounded by Z-Power!",
                           "Choose a move: a matching one becomes a Z-Move!"], callback=self.return_to_menu)

    def z_convert(self, attacker, name, d):
        """(d, lines): the Z-Move version of the move, if this Pokemon's Z-Power is armed."""
        g = self._gimmicks()
        if id(attacker) not in g["z_armed"] or not (d.get("power") or 0):
            return d, []
        story_side = attacker is self.player_pokemon
        if story_side and zpower.held_crystal_type(attacker) != d.get("type"):
            return d, []  # (it holds another type's crystal: the move stays as it is)
        g["z_armed"].discard(id(attacker))
        g["z_used"]["player" if story_side else "opponent"] = True
        zname = zpower.Z_MOVE.get(d.get("type"), "Z-Move")
        zd = dict(d, power=zpower.z_power(d.get("power")), accuracy=None, ailment_chance=0, flinch=0, stat_chance=0,
                  stat_changes=[], drain=0, max_hits=None, min_hits=None, _z_name=zname)
        label = self._label(attacker)
        return zd, [f"{label} surrounded itself with its Z-Power!", f"{label} unleashes its full-force Z-Move!",
                    f"{zname.upper()}!"]

    def foe_arms_z(self, foe):
        """Alola's Kahunas and Captains use a Z-Move once, with their last Pokemon."""
        if self.game.story_manager.get_current_region() != "ALOLA":
            return
        who = f"{self.trainer_class} {getattr(self, 'trainer_name', '')}"
        if self.trainer_class not in LEADERS and "Kahuna" not in who and "Captain" not in who:
            return
        team = [p for p in (self.opponent_team or []) if p]
        g = self._gimmicks()
        if g["z_used"].get("opponent") or not team or foe is not team[-1]:
            return
        g["z_armed"].add(id(foe))

    # ------------------------------------------------------------------ Terastal
    def tera_option(self):
        story = self.game.story_manager
        mon = self.player_pokemon
        return bool(mon and not getattr(self, "starter_battle", False) and story.inventory.get(zpower.TERA_ORB)
                    and story.get_current_region() == "PALDEA"  # (Paldea only, for now: Jordan 11-03)
                    and not self._gimmicks()["tera_used"].get("player") and not getattr(mon, "_tera_types", None)
                    and not getattr(mon, "_form_state", None))

    def terastallize(self, mon):
        """Turn into its Tera Type for the rest of the battle. Returns the lines."""
        t = zpower.tera_type(mon)
        mon._tera_types = list(mon.types or [])
        mon.types = [t]
        self._gimmicks()["tera_used"][self.side_of(mon)] = True
        return [f"{self._label(mon)} terastallized!", f"It became the {t.title()} type!"]

    def activate_tera(self):
        if not self.tera_option() or self.phase != "MENU":
            return
        lines = self.terastallize(self.player_pokemon)
        self.setup_action_menu()
        self.show_message(lines, callback=self.return_to_menu)

    def foe_tera_on_entry(self, foe):
        """Paldea's Leaders, Elite Four and Champion: their last Pokemon in their Gym's type."""
        if self.game.story_manager.get_current_region() != "PALDEA" or self.trainer_class not in LEADERS:
            return []
        if self._gimmicks()["tera_used"].get("opponent") or getattr(foe, "_tera_types", None):
            return []
        team = [p for p in (self.opponent_team or []) if p]
        if not team or foe is not team[-1]:
            return []
        count = {}
        for p in team:
            for t in p.types or []:
                count[t] = count.get(t, 0) + 1
        foe.tera_type = max(count, key=lambda t: (count[t], t != "NORMAL")) if count else zpower.tera_type(foe)
        return self.terastallize(foe)

    def stab_mult(self, attacker, move_type):
        """1, 1.5 or 2: STAB, counting a Terastallized Pokemon's old types, and 2 when its Tera Type is one
        of them."""
        types = attacker.types or []
        old = getattr(attacker, "_tera_types", None)
        if old:
            if move_type in types and move_type in old:
                return 2.0
            return 1.5 if move_type in types or move_type in old else 1.0
        return 1.5 if move_type in types else 1.0


def end_battle(mon):
    """After the battle: back to its own types."""
    old = getattr(mon, "_tera_types", None)
    if old is not None:
        mon.types = old
        del mon._tera_types
