# [REF-0094: Double battles]
"""Double battles (Jordan 11-18; first one: Luana's Kumquat Gym, Orange 5.7): two Pokemon a side.

A battle is a double one when its trainer data says so: battle options {"double": true} (the trainer's
"battle_options", or "double": true on the trainer). `TrainerBattleState(..., options={"double": True})` hands back
this class (TrainerBattleState.__new__), so Twins, tag battles and the like only need the flag in their data.

How it plays (the games' rules, our math):
- Each of your Pokemon out picks its own action in turn (FIGHT / BAG / POKEMON / RUN). FIGHT: the move, then the
  target when it can hit more than one (either foe, or your partner), then a math question: ONE QUESTION PER
  POKEMON'S ACTION, and that answer decides that Pokemon's move exactly as in a single battle (wrong: weaker,
  quick and right: a bonus). Then the turn plays: both foes act too, everyone by priority and Speed.
- Spread moves (Earthquake, Surf, Rock Slide...: PokeAPI targets "all-opponents" / "all-other-pokemon") hit every
  Pokemon they reach at 0.75x (`spread_mult`); Earthquake and Surf hit your partner too.
- The doubles-only effects written into battle_moves.py now take effect: Helping Hand, Follow Me / Rage Powder,
  After You / Quash (they reorder `turn_actions` through `action_for`), Ally Switch, Coaching, the Pledge
  combinations, Round, Life Dew...
- A fainted Pokemon is replaced at the end of the turn (the trainer's next; yours from the party list). With only one
  Pokemon able to battle, you battle with one (the games' rule), and a side that runs out battles on with one.

Tag battles (11-18): options "partner" {name, class, sprite, team, levels} put a partner's Pokemon in your second slot,
run by the AI (Steven at Mossdeep, Lance at the Rocket base...); "second_trainer" {the same} put a second trainer on the
other side, each with its own slot (Twins-style pairs are one trainer). Each slot refills from its owner's team only;
an owner who runs out leaves that slot empty. You lose when your own Pokemon are out (as in Emerald); only yours earn XP.

The single-battle engine is reused as it is: the battle's "focused pair" (`player_pokemon` / `opponent_pokemon` and
their HP mirrors) is pointed at whoever is acting and its target (`_focus`), and each Pokemon's own `current_hp` is
the truth. The helpers that asked "is this the player's Pokemon?" by `is self.player_pokemon` (side, label, HP,
bench) answer by team instead (overridden below).
"""
import random

import pygame

from src.states.battle import TrainerBattleState
from src.states.battle_doubles import FOE_SPREAD
from src.pokemon import moves as movelib
from src.pokemon import pp as pplib
from src.pokemon import affection
from src.pokemon.mechanics import TypeAdvantage
from src.ui.panels import CommandButton
from src.ui.widgets import Backdrop
from src.ui import theme
from src.utils import Utils
from src.vfx.animations import FaintAnimation, battle_sprite, MAX_HEIGHT
from src.vfx import move_anim as move_anims
from src.vfx.move_anim import tinted

SPREAD = FOE_SPREAD + ("all-other-pokemon",)   # (a move that hits every Pokemon it reaches, 0.75x each)
# Where each slot's Pokemon stands (feet), as shares of the screen; your feet stand on the text box's top edge.
FOE_FEET = ((0.60, 0.43), (0.84, 0.385))
MY_FEET_X = (0.17, 0.42)
SPRITE_K = 0.8          # (two a side: a little smaller than in a single battle, so they don't overlap)
FOE_BOX = (420, 84)
MY_BOX = (440, 98)
BOX_GAP = 8


class DoubleBattleState(TrainerBattleState):
    is_doubles = True
    NO_AUTO_TEXT = TrainerBattleState.NO_AUTO_TEXT + ("TARGET_SELECT", "D_PICK")

    def __init__(self, game, opponent_data, *args, **kwargs):
        super().__init__(game, opponent_data, *args, **kwargs)
        story = game.story_manager
        self._tag_teams()
        able = [p for p in story.player_team if p is not None and p.current_hp > 0]
        if self.partner_team:   # (a tag battle: your first Pokemon and your partner's)
            self.p_slots = [able[0] if able else self.player_pokemon, self.partner_team[0]]
        else:
            self.p_slots = [able[0] if able else self.player_pokemon, able[1] if len(able) > 1 else None]
        for p in self.opponent_team:   # (a trainer's Pokemon start at full HP, as each foe does in a single battle)
            if p is not None:
                p.current_hp = p.get_max_hp()
        foes = [p for p in self.opponent_team if p is not None]
        if self.foe_teams:   # (two trainers: each sends out its first)
            self.o_slots = [next(iter(t), None) for t in self.foe_teams]
        else:
            self.o_slots = [foes[0] if foes else None, foes[1] if len(foes) > 1 else None]
        self.current_opponent_idx = min(1, len(foes) - 1)
        self._plans, self._act_of = {}, {}
        self._d_down, self._d_faint_queue = set(), []
        self._d_fanim, self._d_fainting = FaintAnimation(), None
        self._d_actor, self._d_hit = None, []
        self._spread_k = 1.0
        self._slot_turn = 0
        self._target_buttons, self._pending_target = [], None
        self._sprite_cache = {}
        self._focus(self.p_slots[0], self.o_slots[0])
        self._check_forms()   # (the second Pokemon of each side coming out: Intimidate, hazards...)
        self.setup_action_menu()
        if self.phase == "MENU":
            self._slot_turn = self._next_input_slot(-1) or 0
            self._focus(self.p_slots[self._slot_turn], self._first_foe())

    # ================================================================== tag battles: whose Pokemon is whose
    def _tag_teams(self):
        """The partner's team and the second trainer's, from the battle options (their data, as a trainer's)."""
        opts = self.battle_options
        self.partner_team, self.foe_teams = [], []
        self.partner_name = self.foe2_name = None
        self.partner_sprite = self.foe2_sprite = self.partner_back = None
        if not (opts.get("partner") or opts.get("second_trainer")):
            return
        from src.states.overworld.common import _story_team, _trainer_sprite, _fill_names
        area = getattr(self, "area_name", None) or self.game.story_manager.current_area_key
        info = opts.get("partner")
        if info:
            self.partner_team = [p for p in _story_team(self.game, area, dict(info)) if p is not None]
            for p in self.partner_team:
                p.current_hp = p.get_max_hp()
            self.partner_name = _fill_names(self.game, info.get("name") or "Partner")
            self.partner_sprite = _trainer_sprite(self.game, info.get("sprite"))
            self.partner_back = self._back_sprite(info.get("sprite"))
        info = opts.get("second_trainer")
        if info and info.get("villain"):   # (a villain dressed as this Hoenn version's team: Tabitha or Matt)
            from src.world import hoenn as _h
            v = _h.VERSIONS.get(_h.version(self.game.story_manager))
            if v:
                info = _h._villain(dict(info), v)
        if info:
            first = [p for p in self.opponent_team if p is not None]
            second = [p for p in _story_team(self.game, area, dict(info)) if p is not None]
            self.foe_teams = [first, second]
            self.opponent_team = first + second
            self.foe2_name = _fill_names(self.game, info.get("name") or info.get("class") or "Trainer")
            self.foe2_sprite = _trainer_sprite(self.game, info.get("sprite"))
            for k, v in (info.get("rewards") or {"balls": 3}).items():   # (both trainers pay out)
                if isinstance(v, (int, float)):
                    self.rewards[k] = self.rewards.get(k, 0) + v

    def _back_sprite(self, sprite):
        """A partner seen from behind, beside you: assets/sprites/trainers/back/<its sprite> if it's there (Jordan's
        list: kanto_handoff/PARTNER_BACK_SPRITES.md), else None (the front picture stands in)."""
        import os
        if not sprite:
            return None
        for role in ("rival", "friend"):   # (the region's rival as partner: Barry at Spear Pillar is "{rival_character}")
            if f"{{{role}_character}}" in str(sprite):
                sprite = f"{str(getattr(self.game, role + '_character', '') or '').lower()}.png"
        path = os.path.join(self.game.assets.trainers_dir, "back", os.path.basename(str(sprite)))
        if not os.path.exists(path):
            return None
        try:
            return pygame.image.load(path).convert_alpha()
        except pygame.error:
            return None

    def is_partner(self, mon):
        return mon is not None and self._has(self.__dict__.get("partner_team") or [], mon)

    def _owner(self, mon):
        """Which slot's owner a Pokemon belongs to: 1 for the partner's and the second trainer's, else 0."""
        if self.is_partner(mon):
            return 1
        teams = self.__dict__.get("foe_teams") or []
        return 1 if len(teams) > 1 and self._has(teams[1], mon) else 0

    def _slot_team(self, side, k):
        """The team that fills slot k: the partner's / that trainer's in a tag battle, else the side's whole team."""
        if side == "player":
            return self.partner_team if (self.partner_team and k == 1) else self.game.story_manager.player_team
        return self.foe_teams[k] if self.foe_teams else self.opponent_team

    def _slot_bench(self, side, k):
        """(team, indices into it) of who can come into slot k."""
        team = self._slot_team(side, k)
        out = self.p_slots + self.o_slots
        return team, [i for i, p in enumerate(team) if p is not None and p.current_hp > 0 and not self._has(out, p)]

    def owner_name(self, side, k):
        if side == "opponent" and k == 1 and self.foe2_name:
            return self.foe2_name
        if side == "player" and k == 1 and self.partner_name:
            return self.partner_name
        return self._trainer_word() if side == "opponent" else None

    # ================================================================== who's out
    @staticmethod
    def _has(seq, mon):
        return any(m is mon for m in seq if m is not None)

    def _slots(self, side):
        return self.p_slots if side == "player" else self.o_slots

    def _alive(self, mon):
        return mon is not None and self._hp(mon) > 0

    def battlers(self, side):
        if "p_slots" not in self.__dict__:
            return super().battlers(side)
        return [m for m in self._slots(side) if self._alive(m)]

    def _first_foe(self, side="opponent"):
        out = self.battlers(side)
        if out:
            return out[0]
        return next((m for m in self._slots(side) if m is not None), None)

    def _focus(self, mine=None, foe=None):
        """Point the single-battle engine at these two (each one's own current_hp is the truth)."""
        if mine is not None:
            self.player_pokemon = mine
            self.player_max_hp = mine.get_max_hp()
            self.player_hp = max(0, mine.current_hp)
        if foe is not None:
            self.opponent_pokemon = foe
            self.opp_hp_mult = 1
            self.opp_max_hp = foe.get_max_hp()
            self.opponent_hp = max(0, foe.current_hp)

    def _focus_pair(self, a, b):
        """a acts on b: a on its side of the focus, b on the other (an ally target leaves the other side as it was)."""
        if self.side_of(a) == "player":
            foe = b if b is not None and self.side_of(b) == "opponent" else (
                self.opponent_pokemon if self._alive(self.opponent_pokemon) else self._first_foe("opponent"))
            self._focus(a, foe)
        else:
            mine = b if b is not None and self.side_of(b) == "player" else (
                self.player_pokemon if self._alive(self.player_pokemon) else self._first_foe("player"))
            self._focus(mine, a)

    # ---- the helpers that asked "is this the focused Pokemon?" answer by team in a double battle
    def side_of(self, mon):
        if "p_slots" not in self.__dict__:
            return super().side_of(mon)
        return "player" if (self._has(self.game.story_manager.player_team, mon) or self.is_partner(mon)) else "opponent"

    def _label(self, mon):
        return mon.display_name.upper() if self.side_of(mon) == "player" else f"Foe {mon.display_name.upper()}"

    def _foe_of(self, mon):
        if "p_slots" not in self.__dict__:
            return super()._foe_of(mon)
        other = "opponent" if self.side_of(mon) == "player" else "player"
        focused = self.opponent_pokemon if other == "opponent" else self.player_pokemon
        return focused if self._alive(focused) else self._first_foe(other)

    def _hp(self, mon):
        if mon is self.player_pokemon and "player_hp" in self.__dict__:
            return self.player_hp
        if mon is self.opponent_pokemon and "opponent_hp" in self.__dict__:
            return self.opponent_hp
        return mon.current_hp

    def _max_hp(self, mon):
        return mon.get_max_hp()

    def _adjust_hp(self, mon, delta, floor=0):
        if mon is self.player_pokemon or mon is self.opponent_pokemon:
            return super()._adjust_hp(mon, delta, floor)
        if delta > 0 and self.vol(mon).get("heal_block"):
            return
        mon.current_hp = max(min(floor, mon.current_hp), min(mon.get_max_hp(), mon.current_hp + delta))

    def _hurt(self, mon, dmg):
        mon.current_hp = max(0, mon.current_hp - int(dmg))
        if mon is self.player_pokemon:
            self.player_hp = mon.current_hp
        if mon is self.opponent_pokemon:
            self.opponent_hp = mon.current_hp

    def forget_switched_out(self):
        if "p_slots" not in self.__dict__:
            return super().forget_switched_out()
        active = {id(m) for m in self.p_slots + self.o_slots if m is not None}
        self.mv_left_field(active)
        for table in (self._fx()["stages"], self._fx()["vol"]):
            for k in [k for k in table if k not in active]:
                table.pop(k)

    def _check_forms(self):
        """Switch-in effects for every Pokemon that came out (not just the focused pair)."""
        if "p_slots" not in self.__dict__:
            return super()._check_forms()
        self.forget_switched_out()
        seen = self.__dict__.setdefault("_on_field", set())
        keep = (self.player_pokemon, self.opponent_pokemon)
        for mon in [m for m in self.p_slots + self.o_slots if m is not None and m.current_hp > 0]:
            if id(mon) in seen:
                continue
            seen.add(id(mon))
            self._focus_pair(mon, None)
            self._form_msgs.extend(self.mv_mask_form(mon))
            self._form_msgs.extend(self.mv_on_entry(mon))
            self._form_msgs.extend(self.entry_hazards(mon))
            self._form_msgs.extend(self.ability_on_entry(mon))
        seen.intersection_update({id(m) for m in self.p_slots + self.o_slots if m is not None})
        self._focus(*keep)

    def _bench(self, mon):
        if "p_slots" not in self.__dict__:
            return super()._bench(mon)
        side = self.side_of(mon)
        if side == "opponent" and self.foe_teams:   # (indices into the whole opponent_team, as the engine reads them)
            mine = self.foe_teams[self._owner(mon)]
            return [j for j, p in enumerate(self.opponent_team) if p is not None and p.current_hp > 0
                    and self._has(mine, p) and not self._has(self.o_slots, p)]
        return self._slot_bench(side, self._owner(mon))[1]

    def action_for(self, mon):
        return self._act_of.get(id(mon)) if mon is not None else None

    def swap_allies(self, a, b):
        """Ally Switch: the two trade places."""
        slots = self._slots(self.side_of(a))
        ia = next((i for i, m in enumerate(slots) if m is a), None)
        ib = next((i for i, m in enumerate(slots) if m is b), None)
        if ia is not None and ib is not None:
            slots[ia], slots[ib] = slots[ib], slots[ia]

    def _note_first_turns(self):
        seen = self.__dict__.setdefault("_out_since", {})
        for mon in self.p_slots + self.o_slots:
            if mon is not None and seen.get(id(mon), (None,))[0] is not mon:
                seen[id(mon)] = (mon, self.turn_count)

    def _calculate_damage(self, *args, **kwargs):
        dmg = super()._calculate_damage(*args, **kwargs)
        if dmg and self._spread_k != 1:
            dmg = max(1, int(dmg * self._spread_k))
        return dmg

    def _after_entry_lines(self):
        lines = self._collect_faints()
        if lines or self._d_faint_queue:
            self.phase = "D_RESOLVE"
            self.turn_actions.clear()
            self._turn_end_done = True
            if lines:
                self.dialogue_box.reset(lines)
                self.dialogue_box.set_visibility(True)
            return
        self.return_to_menu()

    # ================================================================== choosing, one Pokemon at a time
    def _next_input_slot(self, after):
        for k in range(after + 1, 2):
            if self._alive(self.p_slots[k]) and not self.is_partner(self.p_slots[k]):
                return k
        return None

    def _new_question(self):
        play = self.game.states.get("play")
        if play is not None:
            self.problem_str, self.correct_ans, self.options = play.generate_math_set(play.total_caught, num_options=4)
        self.setup_math_ui()

    def _prompt_slot(self, k):
        """Slot k's Pokemon picks its action: its own FIGHT / BAG / POKEMON / RUN, and its own math question."""
        self._slot_turn = k
        self.chosen_move, self._pending_target, self.form_armed = None, None, None
        self._focus(self.p_slots[k], self._first_foe())
        self._ready_attacks()
        self.setup_action_menu()
        self._new_question()
        self.return_to_menu()

    def _begin_input(self):
        self._plans = {}
        k = self._next_input_slot(-1)
        if k is None:   # (nobody of yours can act: the battle is over; _end_check says so)
            return
        self._prompt_slot(k)

    def _plan_done(self):
        """This Pokemon's choice is in: the partner's turn to choose, or the turn plays."""
        nxt = self._next_input_slot(self._slot_turn)
        if nxt is not None:
            self._prompt_slot(nxt)
        else:
            self._start_turn()

    def _move_target_kind(self, name):
        d = movelib.info(self.game, self.mv_alias(self.player_pokemon, name))
        return d.get("target") or "selected-pokemon"

    def choose_move(self, name):
        self._clear_move_buttons()
        self.chosen_move = name
        mon = self.player_pokemon
        options = []
        if self._move_target_kind(name) == "selected-pokemon" and not self._forced_move(mon):
            options = self.battlers("opponent") + [a for a in self.allies(mon) if self._alive(a)]
        if len(options) > 1:
            self._open_target_select(options)
            return
        self._pending_target = options[0] if options else None
        self.phase = "MENU"
        self.start_math_phase()

    def _open_target_select(self, options):
        """Which one? Each foe (and your partner) as a button, BACK to the moves."""
        self.phase = "TARGET_SELECT"
        self.action_menu.set_visibility(False)
        self.dialogue_box.set_visibility(False)
        box = Utils.get_full_dialogue_rect(self.game)
        pad, gap, back_w = 16, 10, 170
        n = len(options)
        bw = (box.width - pad * 2 - back_w - gap * n) // n
        bh = box.height - pad * 2 - 4
        self._clear_target_buttons()
        self._target_backdrop = Backdrop(box)
        self.game.ui_manager.add_element(self._target_backdrop)
        for i, mon in enumerate(options):
            foe = self.side_of(mon) == "opponent"
            text = mon.display_name.upper()   # (a foe red, your partner green)
            btn = CommandButton((box.x + pad + i * (bw + gap), box.y + pad, bw, bh), text,
                                self.game.assets.fonts["button"], lambda m=mon: self._pick_target(m),
                                bg_color=theme.FIGHT if foe else theme.POKEMON, autosize=False)
            self._target_buttons.append(btn)
        back = CommandButton((box.right - pad - back_w, box.y + pad, back_w, bh), "BACK",
                             self.game.assets.fonts["button"], self._target_back, bg_color=(120, 124, 144),
                             autosize=False)
        self._target_buttons.append(back)
        for btn in self._target_buttons:
            self.game.ui_manager.add_element(btn)

    def _clear_target_buttons(self):
        for btn in self._target_buttons + [getattr(self, "_target_backdrop", None)]:
            if btn is not None and btn in self.game.ui_manager.elements:
                self.game.ui_manager.elements.remove(btn)
        self._target_buttons, self._target_backdrop = [], None

    def _pick_target(self, mon):
        self._clear_target_buttons()
        self._pending_target = mon
        self.phase = "MENU"
        self.start_math_phase()

    def _target_back(self):
        self._clear_target_buttons()
        self.phase = "MENU"
        self.open_move_menu()

    def resolve_turn(self, player_was_correct):
        """The answer is in: it's this Pokemon's plan (its move, target and how well the answer went)."""
        if self.math_ui:
            self.math_ui.set_visibility(False)
        mode = getattr(self, "_answer_mode", None)
        if not player_was_correct and mode is None:
            mode = "weak"
        mon = self.player_pokemon
        self._plans[id(mon)] = {"kind": "move", "mon": mon, "move": self.chosen_move,
                                "target": self._pending_target, "mode": mode, "form": self.form_armed}
        self.form_armed, self._answer_mode = None, None
        self.phase = "D_WAIT"
        self._plan_done()

    def on_item_used(self):
        """An item from the Bag takes this Pokemon's action."""
        mon = self.player_pokemon
        self._plans[id(mon)] = {"kind": "item", "mon": mon}
        self.game.change_state(self)
        self._plan_done()

    def open_party_menu(self):
        if self.no_switch:
            return self.show_message([self.no_switch_text()], callback=self.return_to_menu)
        k, team = self._slot_turn, self.game.story_manager.player_team
        taken = [p["new"] for p in self._plans.values() if p.get("kind") == "switch"]

        def chosen(idx):
            p = team[idx] if 0 <= idx < len(team) else None
            if p is None or p.current_hp <= 0:
                self.game.show_dialogue([f"{p.display_name.upper() if p else 'It'} has no energy left!"])
                return
            if self._has(self.p_slots, p) or self._has(taken, p):
                self.game.show_dialogue([f"{p.display_name.upper()} is already in battle!"])
                return
            mon = self.p_slots[k]
            self._plans[id(mon)] = {"kind": "switch", "mon": mon, "slot": k, "new": p}
            self.game.change_state(self)
            self._plan_done()

        def cancel():
            self.game.change_state(self)
            self.return_to_menu()

        from src.states.systems import PokemonPartyMenuState
        self.game.change_state(PokemonPartyMenuState(self.game, previous_state=self, context="battle_switch",
                                                     on_select=chosen, on_cancel=cancel))

    # ================================================================== the turn
    def _ai_plan(self, foe):
        """A trainer's Pokemon (or your partner's) picks its move and its target: the strongest hit it has on either
        of the other side's."""
        chart = TypeAdvantage(self.game.loader.area_data.get("TYPE_CHART", {}))
        best = None
        other = "opponent" if self.side_of(foe) == "player" else "player"
        for t in self.battlers(other):
            self._focus_pair(foe, t)
            name = self._forced_move(foe) or self._ai_choose(foe, t)
            d = movelib.info(self.game, name)
            score = (d.get("power") or 40) * (chart.get_multiplier(d.get("type"), t.types or []) if d.get("type") else 1)
            if d.get("target") == "all-other-pokemon":   # (an Earthquake hits its own partner too: less keen)
                if any(chart.get_multiplier(d.get("type"), a.types or []) > 0 for a in self.allies(foe)):
                    score *= 0.5
            score *= random.uniform(0.85, 1.15)
            if best is None or score > best[0]:
                best = (score, name, t)
        if best is None:
            return None
        return {"kind": "move", "mon": foe, "move": best[1], "target": best[2], "mode": None}

    def _order_key(self, plan):
        mon = plan["mon"]
        if plan["kind"] in ("switch", "item"):
            return (-7, 0, 0, random.random())   # (switching and items before any move)
        self._focus_pair(mon, None)
        d = movelib.info(self.game, self._forced_move(mon) or plan.get("move") or movelib.STRUGGLE)
        pri = d.get("priority", 0) + self.ability_priority(mon, d) + self.mv_priority(mon, d)
        return (-pri, -self.held_order(mon), -self._speed(mon), random.random())

    def _start_turn(self):
        self.phase = "D_RESOLVE"
        self.turn_actions.clear()
        self.turn_count += 1
        self._turn_end_done = False
        self._flinched = set()
        self._acts_second = None
        self.__dict__.pop("_order_override", None)
        self._note_first_turns()
        for foe in self.battlers("opponent") + [m for m in self.battlers("player") if self.is_partner(m)]:
            plan = self._ai_plan(foe)
            if plan:
                self._plans[id(foe)] = plan
        for plan in [p for p in self._plans.values() if p.get("form")]:   # (Mega Evolution first, as in singles)
            self._focus_pair(plan["mon"], None)
            self.form_armed = plan["form"]
            self._apply_transforms()
        picks = {k: p["move"] for k, p in self._plans.items() if p["kind"] == "move" and p.get("move")}
        self._form_msgs.extend(self.mv_turn_start(picks))
        plans = sorted(self._plans.values(), key=self._order_key)
        self._act_of = {id(p["mon"]): (lambda m=p["mon"]: self._act(m)) for p in plans}
        self.turn_actions = [self._act_of[id(p["mon"])] for p in plans]
        if self.math_ui:
            self.math_ui.set_visibility(False)
        self.action_menu.set_visibility(False)

    def _act(self, mon):
        """One Pokemon's turn: a switch, an item (already used), or its move on its target(s)."""
        plan = self._plans.get(id(mon))
        if plan is None or not self._alive(mon) or not (self._has(self.p_slots, mon) or self._has(self.o_slots, mon)):
            return
        if plan["kind"] == "switch":
            if self._pursued_first(mon):   # (a foe's Pursuit aimed at it strikes first, at double power; then it goes)
                return
            return self._switch_in("player", plan["slot"], plan["new"], called_back=True)
        if plan["kind"] != "move":
            return
        side = self.side_of(mon)
        other = "opponent" if side == "player" else "player"
        if not self.battlers(other):
            return
        chosen = plan.get("target")
        if chosen is not None and not (self._alive(chosen) and (self._has(self.p_slots, chosen) or self._has(self.o_slots, chosen))):
            chosen = None   # (the one it aimed at has fainted: the other foe, as in the games)
        if chosen is None or chosen is mon:
            chosen = self.battlers(other)[0]
        self._focus_pair(mon, chosen)
        label = self._label(mon)
        mine = side == "player" and not self.is_partner(mon)
        if side == "player" and not mine:
            self.chosen_move, self._answer_mode = plan["move"], None
        if mine:
            self.chosen_move, self._answer_mode = plan["move"], plan.get("mode")
            cap, lv = self._obey_level(), self._level(mon)
            if lv > cap and random.random() < (lv - cap) / (lv + cap):
                return self._say([random.choice(self.DISOBEY_LINES).format(n=label),
                                  f"(Win more badges here to earn the trust of Pokemon above Lv {cap}.)"])
        stopped, pre = self._status_stops(mon, label)
        if not stopped:
            stopped, more = self.before_move(mon)
            pre = pre + more
        if stopped:
            return self._say(pre + self._collect_faints())
        picked = plan.get("move")
        if side == "opponent" and picked and picked != movelib.STRUGGLE and pplib.left(self.game, mon, picked) <= 0:
            picked = None
        name, pp_lines = self._move_for_turn(mon, picked or self._ai_choose(mon, chosen))
        if side == "opponent":
            self.foe_arms_z(mon)
        d = movelib.info(self.game, name)
        kind = d.get("target") or "selected-pokemon"
        chosen = self.redirect_target(mon, chosen, d)   # (Follow Me / Rage Powder / Spotlight)
        if kind in SPREAD:
            targets = [t for t in self.move_targets(mon, d, chosen) if t is not None and t is not mon and self._alive(t)]
        elif kind == "random-opponent":
            targets = [random.choice(self.battlers(other))]
        else:
            targets = [chosen]
        self._spread_k = self.spread_mult(targets)
        messages, hit, first, foe_dmg = list(pre), [], True, 0
        self._blast_after = [] if name in movelib.EXPLODE else None  # (Explosion hits every target, then the user faints)
        for t in targets:
            if self.side_of(t) != side:
                self._focus_pair(mon, t)
            act = self._act_of.get(id(t))
            self._acts_second = id(t) if act is not None and act in self.turn_actions else None
            self._answer_used = None
            hp = self._hp(t)
            dmg, lines, _ = self._use_move(mon, t, name, label, self._label(t), self._max_hp(t), hp)
            if not first:   # (one "X used Y!" for a move that hits two)
                i = self._used_line(lines)
                lines = lines[i + 1:] if i is not None else lines
            if len(targets) > 1:
                lines = [self._for_target(line, t) for line in lines]
            if dmg and t is not mon:
                if self.side_of(t) == "player" and dmg >= self._hp(t) > 1 and affection.endures(t):
                    dmg = self._hp(t) - 1
                    lines.append(affection.ENDURE_TEXT.format(n=t.display_name.upper()))
                self._hurt(t, dmg)
                lines += self.mv_note_hit(mon, t, dmg)
                hit.append(t)
                if self.side_of(t) == "player":
                    self._battle_damage[id(t)] = self._battle_damage.get(id(t), 0) + dmg
                    t.counters["damage_total"] = t.counters.get("damage_total", 0) + dmg
                elif side == "player":
                    foe_dmg = dmg
                    mon.counters["attacks"] = mon.counters.get("attacks", 0) + 1
                    if self._last_was_crit:
                        self._battle_crits[id(mon)] = self._battle_crits.get(id(mon), 0) + 1
                        mon.counters["crits"] = mon.counters.get("crits", 0) + 1
            messages += lines
            first = False
            if not self._alive(mon):
                break
        for m in (self._blast_after or [])[:1]:
            if self._alive(m):
                self._adjust_hp(m, -self._hp(m))
        self._blast_after = None
        self._spread_k = 1.0
        messages += pp_lines
        if mine:
            messages += self._answer_notes(label, foe_dmg)
        messages += self.end_rampage_turn(mon)
        self._answer_mode = None
        for m in self.battlers("player") + self.battlers("opponent"):   # (held berries: everyone out)
            messages += self.held_berry_check(m)
        self._d_actor, self._d_hit = mon, hit
        lunge = side if not self._start_move_anim(mon, name, side, messages, targets) and hit else None
        messages += self._collect_faints()
        self._d_pending_switches()
        self._show_move_text(messages, lunge)
        self.feedback_timer = 30

    def _pursued_first(self, mon):
        """You switch mon out: a foe that picked Pursuit at it (and hasn't moved) hits it first, at double power, as in
        the games (Gen 4 on; 11-18: in a double battle the switch always went first). True if it struck: the switch
        comes after it (if mon is still standing)."""
        for foe in self.battlers("opponent"):
            fp = self._plans.get(id(foe)) or {}
            act = self._act_of.get(id(foe))
            if fp.get("kind") != "move" or fp.get("move") != "PURSUIT" or act not in self.turn_actions:
                continue
            if fp.get("target") is not None and fp.get("target") is not mon:
                continue
            fp["target"] = mon
            self.turn_actions.remove(act)
            self.turn_actions.insert(0, lambda m=mon: self._act(m))   # (then the switch, unless it fainted)
            self._mv_call_boost = 2.0
            act()
            self.__dict__.pop("_mv_call_boost", None)
            return True
        return False

    @staticmethod
    def _for_target(line, t):
        lab = t.display_name.upper()
        return {"It's super effective!": f"It's super effective on {lab}!",
                "It's not very effective...": f"It's not very effective on {lab}...",
                "Critical hit!": f"A critical hit on {lab}!"}.get(line, line)

    def _say(self, lines):
        self.dialogue_box.reset(lines or [""])
        self.dialogue_box.set_visibility(True)
        self.feedback_timer = 30

    def _d_pending_switches(self):
        """U-turn, Baton Pass, Roar...: the Pokemon leaves now (yours: you pick who comes in)."""
        pending = self._mv()["pending"]
        while pending:
            kind, mon, baton = pending.pop(0)
            side = self.side_of(mon)
            slots = self._slots(side)
            k = next((i for i, m in enumerate(slots) if m is mon), None)
            bench = self._bench(mon)
            if k is None or not bench or not self._alive(mon):
                continue
            if side == "opponent":
                j = random.choice(bench) if kind == "force" else self._ai_switch_pick(bench, self._first_foe("player"))
                new = self.opponent_team[j]
            else:
                team = self._slot_team(side, self._owner(mon))
                new = team[random.choice(bench) if kind == "force" else bench[0]]
            self.turn_actions.insert(0, lambda s=side, k=k, n=new, b=baton, f=kind == "force":
                                     self._switch_in(s, k, n, called_back=True, baton=b, dragged=f))

    def _switch_in(self, side, k, new, called_back=False, baton=None, dragged=False):
        """new takes slot k (a switch, a replacement after a faint, or a pivot move). Shows the lines."""
        slots = self._slots(side)
        old = slots[k]
        who = self.owner_name(side, k) or self._trainer_word()
        theirs = side == "opponent" or self.is_partner(new) or self.is_partner(old)
        lines = []
        if old is not None and old.current_hp > 0 and called_back:
            self.ability_on_switch_out(old)
            self.mv_switched_out(old)
            lines.append(f"{who} withdrew {old.display_name.upper()}!" if theirs
                         else f"Come back, {old.display_name.upper()}!")
        if old is not None:
            self.__dict__.get("_out_since", {}).pop(id(old), None)
        slots[k] = new
        self._d_down.discard(id(new))
        if dragged:
            lines = [f"{self._label(new)} was dragged out!"]
        else:
            lines.append(f"{who} sent out {new.display_name.upper()}!" if theirs
                         else f"Go! {new.display_name.upper()}!")
        self._focus_pair(new, None)
        self._check_forms()
        if baton:
            self.mv_apply_baton(new, baton)
        lines += self._form_msgs
        self._form_msgs = []
        lines += self._collect_faints()   # (entry hazards can knock it out)
        if side == "player":
            self._xp_participants = [m for m in self.battlers("player") if not self.is_partner(m)]
        self._say(lines)

    def _trainer_word(self):
        who = self.trainer_name or self.trainer_class
        return getattr(self.game, "rival_name", who) if self.trainer_class == "RIVAL" else who

    # ================================================================== faints and the end of the turn
    def _collect_faints(self):
        """Every Pokemon out that has just hit 0 HP: its line (and the XP for a foe); it sinks after the text."""
        lines = []
        for side in ("opponent", "player"):
            for mon in self._slots(side):
                if mon is None or mon.current_hp > 0 or id(mon) in self._d_down:
                    continue
                self._d_down.add(id(mon))
                self._d_faint_queue.append(mon)
                self._mv()["fainted_turn"][side] = self.turn_count
                lines.append(f"{self._label(mon)} fainted!")
                act = self._act_of.get(id(mon))
                if act in self.turn_actions:
                    self.turn_actions.remove(act)
                if side == "opponent":
                    mine = [m for m in self.battlers("player") if not self.is_partner(m)]   # (the partner's earn nothing)
                    if mine:
                        keep = (self.player_pokemon, self.opponent_pokemon)
                        self._focus(mine[0], mon)
                        self._xp_participants = list(mine)
                        lines += self._award_battle_xp()
                        self._focus(*keep)
        return lines

    def _end_check(self):
        """Out of Pokemon on either side: the battle's over (True)."""
        if not any(p is not None and p.current_hp > 0 for p in self.game.story_manager.player_team):
            self.trigger_outro(win=False)
            return True
        if not any(p is not None and p.current_hp > 0 for p in self.opponent_team):
            self.show_trainer, self.trainer_slide_offset = True, 0
            self.trigger_outro(win=True)
            return True
        return False

    def _end_of_turn(self):
        """Weather, status damage, Leech Seed, the field's timers...: the single battle's end of turn for the first
        Pokemon of each side, then (with the field's timers held still) for the second ones."""
        pa, oa = self._first_foe("player"), self._first_foe("opponent")
        rest_p = [m for m in self.battlers("player") if m is not pa]
        rest_o = [m for m in self.battlers("opponent") if m is not oa]
        extra = []
        if rest_p or rest_o:
            fx, mv = self._fx(), self._mv()
            side0 = {k: dict(v) for k, v in fx["side"].items()}
            field0, future0 = dict(fx["field"]), mv["future"]
            weather0 = (self.weather, self.weather_turns, self.weather_primal)
            for s in fx["side"].values():
                s.pop("wish", None)
            mv["future"] = {}
            self._focus(rest_p[0] if rest_p else pa, rest_o[0] if rest_o else oa)
            if not rest_p:
                self.player_hp = 0   # (only the mirror: this side's first one was done in the first pass)
            if not rest_o:
                self.opponent_hp = 0
            extra = self._weather_end_of_turn() + self.effects_end_of_turn()
            fx["side"].clear()
            fx["side"].update(side0)
            fx["field"].clear()
            fx["field"].update(field0)
            mv["future"] = future0
            self.weather, self.weather_turns, self.weather_primal = weather0
        self._focus(pa, oa)
        lines = self._weather_end_of_turn() + self.effects_end_of_turn()
        lines += [ln for ln in extra if ln not in lines]
        for m in self.battlers("player") + self.battlers("opponent"):
            self.vol(m).pop("helping_hand", None)
            self.vol(m).pop("center_of_attention", None)
        return lines + self._collect_faints()

    def _replace_fainted(self):
        """At the end of the turn, an empty spot is filled: the trainer's next Pokemon, then yours (you pick).
        True while one is being sent out."""
        for k, mon in enumerate(self.o_slots):
            if mon is None or mon.current_hp <= 0:
                team, bench = self._slot_bench("opponent", k)
                if bench:
                    self._switch_in("opponent", k, team[bench[0]])
                    return True
        for k, mon in enumerate(self.p_slots):
            if mon is None or mon.current_hp <= 0:
                team, bench = self._slot_bench("player", k)
                if not bench:
                    continue
                if team is self.partner_team:   # (your partner sends out its next)
                    self._switch_in("player", k, team[bench[0]])
                else:
                    self._pick_replacement(k)
                return True
        return False

    def _pick_replacement(self, k):
        team = self.game.story_manager.player_team
        self.phase = "D_PICK"

        def chosen(idx):
            p = team[idx] if 0 <= idx < len(team) else None
            if p is None or p.current_hp <= 0:
                self.game.show_dialogue([f"{p.display_name.upper() if p else 'It'} has no energy left!"])
                return
            if self._has(self.p_slots, p):
                self.game.show_dialogue([f"{p.display_name.upper()} is already in battle!"])
                return
            self.game.change_state(self)
            self.phase = "D_RESOLVE"
            self._switch_in("player", k, p)

        def cancel():
            chosen(self._slot_bench("player", k)[1][0])

        from src.states.systems import PokemonPartyMenuState
        self.game.change_state(PokemonPartyMenuState(self.game, previous_state=self, context="forced_switch",
                                                     on_select=chosen, on_cancel=cancel))

    def _step(self):
        """The turn plays out, one beat at a time (each waits for its text, animation and HP bars)."""
        if self.dialogue_box.visible and not self.dialogue_box.is_finished:
            return
        if self.renderer.hp_animating() or self.anim_ctrl.is_lunging or self.feedback_timer > 0:
            return
        self.dialogue_box.visible = False
        self._d_actor, self._d_hit = None, []
        if self._d_faint_queue:
            mon = self._d_faint_queue.pop(0)
            img, rect = self._sprite_at(mon)
            if img is not None:
                self._d_fainting = mon
                self._d_fanim.start(img, rect.topleft)
                self.phase = "D_FAINT"
            return
        if self._end_check():
            return
        if self._form_msgs:
            msgs, self._form_msgs = self._form_msgs, []
            return self._say(msgs + self._collect_faints())
        if self.turn_actions:
            self.turn_actions.pop(0)()
            return
        if not self._turn_end_done:
            self._turn_end_done = True
            lines = self._end_of_turn()
            if lines:
                self._say(lines)
            return
        if self._replace_fainted():
            return
        self._begin_input()

    def update(self):
        if self.phase == "D_FAINT":
            self._auto_text()
            self.anim_ctrl.update()
            self.renderer.tick()
            if self._d_fanim.update() or not self._d_fanim.active:
                self._d_fainting = None
                self.phase = "D_RESOLVE"
            return
        super().update()
        if self.phase == "D_RESOLVE" and not self._move_seq:
            self._step()

    # ================================================================== drawing
    def _sprite(self, mon, side):
        img = battle_sprite(mon, side)
        if img is None:
            return None
        key = (id(mon), id(img))
        if key not in self._sprite_cache:
            self._sprite_cache[key] = pygame.transform.smoothscale(
                img, (max(1, int(img.get_width() * SPRITE_K)), max(1, int(img.get_height() * SPRITE_K))))
        return self._sprite_cache[key]

    def _feet(self, side, k):
        w, h = self.game.width, self.game.height
        if side == "opponent":
            return w * FOE_FEET[k][0], h * FOE_FEET[k][1]
        return w * MY_FEET_X[k], Utils.get_full_dialogue_rect(self.game).top + 10

    def _slot_of(self, mon):
        for side in ("player", "opponent"):
            for k, m in enumerate(self._slots(side)):
                if m is mon:
                    return side, k
        return None, None

    def _sprite_at(self, mon):
        side, k = self._slot_of(mon)
        if side is None:
            return None, None
        img = self._sprite(mon, side)
        if img is None:
            return None, None
        fx, fy = self._feet(side, k)
        pad = img.get_height() - img.get_bounding_rect().bottom
        return img, img.get_rect(midbottom=(int(fx), int(fy + pad)))

    def _spot(self, mon):
        img, rect = self._sprite_at(mon)
        if rect is None:
            side, k = self._slot_of(mon)
            return self._feet(side or "player", k or 0)
        return rect.center

    def _start_move_anim(self, user, name, side, messages, targets=None):
        used = self.game.assets.get_text("used_move", name="", move="").strip(" !")
        if not any(used and used in m for m in messages) or any(f in m for m in messages for f in self.MOVE_FAILED) \
                or self.__dict__.get("_charging", {}).get(id(user)) == name:
            return False
        anim, swapped = move_anims.find(self.game.assets.assets_dir, name, side)
        from src.core import settings
        if not anim or not settings.get(self.game.story_manager, "move_anims"):
            return False
        target = next((t for t in (targets or []) if t is not user), None) or self._foe_of(user)
        self.move_anim_name, self.move_anim_side = name, side
        self.move_anim = move_anims.MoveAnimation(self.game, anim, self._spot(user), self._spot(target),
                                                  Utils.get_full_dialogue_rect(self.game).top, swapped, side)
        self._d_hit = [target] + [t for t in self._d_hit if t is not target]
        return True

    def _shown(self, mon):
        """Drawn: standing, or just hit 0 and not yet sunk (its faint comes after the text)."""
        if mon is None or mon is self._d_fainting:
            return False
        return mon.current_hp > 0 or self._has(self._d_faint_queue, mon) or (
            self._move_seq is not None and (mon is self._d_actor or self._has(self._d_hit, mon)))

    def _draw_mon(self, screen, mon):
        img, rect = self._sprite_at(mon)
        if img is None:
            return
        side = self.side_of(mon)
        ctrl, anim = self.anim_ctrl, self.move_anim
        dx = dy = 0
        if mon is self._d_actor and ctrl.is_lunging and ctrl.lunge_side == side:
            reach = ctrl.lunge_amount()
            dx, dy = (70 * reach, -30 * reach) if side == "player" else (-70 * reach, 30 * reach)
        hit = self._has(self._d_hit, mon) and mon is not self._d_actor
        if hit:
            if not ctrl.hit_visible(side):
                return
            push = ctrl.knockback(side)
            dx += -push if side == "player" else push
        if anim is not None and (mon is self._d_actor or hit):
            mdx, mdy, shown, opacity, tint = anim.battler(side)
            if not shown:
                return
            dx, dy = dx + mdx, dy + mdy
            img = tinted(img, tint, opacity)
        r = rect.move(int(dx), int(dy))
        screen.blit(img, r)
        self.renderer._shadow_fog(screen, mon, r)

    def _box_rect(self, side, k, dx=0):
        if side == "opponent":
            bw, bh = FOE_BOX
            return pygame.Rect(self.renderer.MARGIN + int(dx), 16 + k * (bh + BOX_GAP), bw, bh)
        bw, bh = MY_BOX
        top = Utils.get_full_dialogue_rect(self.game).top - 14 - 2 * bh - BOX_GAP
        return pygame.Rect(self.game.width - self.renderer.MARGIN - bw + int(dx), top + k * (bh + BOX_GAP), bw, bh)

    def _draw_box(self, screen, mon, side, k, dx=0):
        r = self.renderer
        box = self._box_rect(side, k, dx)
        mine = side == "player"
        r._box(screen, box, "left" if mine else "right")
        x0 = box.x + (48 if mine else 20)
        right = box.right - (20 if mine else 44)
        r._name_line(screen, mon, x0, box.y + 8, right)
        tag_w = r._status_tag(screen, mon, x0, box.y + 44)
        bar = r._hp_bar(screen, ("player" if mine else "opp", id(mon)), x0 + tag_w, box.y + 47,
                        right - x0 - tag_w, max(0, mon.current_hp), mon.get_max_hp())
        if mine:
            theme.shadow_text(screen, f"{max(0, int(mon.current_hp))}/{mon.get_max_hp()}", self.game.assets.fonts["label"],
                              bar.right, bar.bottom + 4, align="right")
        choosing = self.phase in ("MENU", "MOVE_SELECT", "TARGET_SELECT", "BATTLE", "ANSWER_FEEDBACK") \
            and mine and k == self._slot_turn and self.game.current_state is self
        if choosing:   # (the Pokemon whose action you're picking)
            pygame.draw.rect(screen, (250, 205, 60), box.inflate(8, 8), 4, border_radius=10)

    def draw_side(self, screen, side, dx=0, sprites=True):
        """One side's Pokemon and boxes (the trainer intro draws each side as it comes out)."""
        for k, mon in enumerate(self._slots(side)):
            if sprites and self._shown(mon):
                self._draw_mon(screen, mon)
        for k, mon in enumerate(self._slots(side)):
            if mon is not None and (mon.current_hp > 0 or self._has(self._d_faint_queue, mon)):
                self._draw_box(screen, mon, side, k, dx)

    def draw(self):
        screen = self.game.screen
        if getattr(self, "overworld", None) is not None:
            self.overworld.draw(screen, self)
            self.game.ui_manager.draw(screen)
            return
        screen.fill((0, 0, 0))
        if self.background:
            screen.blit(self.background, (0, 0))
        else:
            screen.fill((95, 145, 185))
        if self.move_anim:
            self.move_anim.draw_back(screen)
        for side in ("opponent", "player"):
            for mon in self._slots(side):
                if self._shown(mon):
                    self._draw_mon(screen, mon)
        if self.trainer_sprite is not None and self.show_trainer:
            w, h = self.game.width, self.game.height
            two = self.foe2_sprite is not None
            screen.blit(self.trainer_sprite, self.trainer_sprite.get_rect(
                center=(w * (0.70 if two else 0.78) + self.trainer_slide_offset, h * 0.26)))
            if two:
                screen.blit(self.foe2_sprite, self.foe2_sprite.get_rect(center=(w * 0.88 + self.trainer_slide_offset, h * 0.26)))
        if self.move_anim:
            self.move_anim.draw(screen)
        self._draw_weather(screen)
        for side in ("opponent", "player"):
            for k, mon in enumerate(self._slots(side)):
                if mon is not None and (mon.current_hp > 0 or self._has(self._d_faint_queue, mon)
                                        or mon is self._d_fainting):
                    self._draw_box(screen, mon, side, k)
        if self.phase == "D_FAINT" and self._d_fanim.active:
            self._d_fanim.draw(screen)
        self.game.ui_manager.draw(screen)


def battle_options(t_info):
    """A trainer's battle options from its data: "battle_options": {...}, or "double" / "no_switch" on the trainer."""
    opts = dict((t_info or {}).get("battle_options") or {})
    for key in ("double", "no_switch"):
        if (t_info or {}).get(key):
            opts.setdefault(key, t_info[key])
    return opts
