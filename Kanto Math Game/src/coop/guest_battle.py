"""A guest's battles (Jordan, 11-08): the game's own, math every turn, on the guest's device with borrowed Pokemon. They only
differ at the end: instead of changing a save or the story, they tell the host how it went. Prizes and progress are the host's
to give."""
import os
import time

from src.config import FPS
from src.pokemon import forms
from src.states.battle import TrainerBattleState, WildBattleState
from src.states.battle_gimmicks import end_battle as gimmick_end_battle
from src.states.coop_watch import snapshot


STUCK_SECONDS = 6
WAITS_FOR_PLAYER = ("MENU", "BATTLE", "MOVE_SELECT", "SWITCH_PROMPT", "CATCH_PROMPT", "CATCH_ANIMATION")


class _GuestFight:
    _sent = None
    _sig, _still = None, 0

    def _watchdog(self):
        """Safety net: a guest's battle that has stopped moving with nothing left to tap must not trap everyone."""
        box = self.dialogue_box
        sig = (self.phase, tuple(box.text_lines or []), box.current_line, box.is_finished, box.visible, self.current_opponent_idx,
               self.opponent_hp, self.player_hp, bool(self._move_seq), self.faint_anim.active, self.trainer_slide_offset)
        if sig != self._sig:
            self._sig, self._still = sig, 0
            return
        if self.phase in WAITS_FOR_PLAYER or not (box.is_finished or not box.visible) or self._move_seq:
            return
        self._still += 1
        if self._still >= STUCK_SECONDS * FPS:
            self._still = 0
            self._note_stuck(sig)
            self._unstick()

    def _note_stuck(self, sig):
        try:
            with open(os.path.join(self.game.assets.base_dir, "crash.log"), "a", encoding="utf-8") as f:
                f.write(f"\n=== {time.ctime()} co-op battle stuck ===\n{type(self).__name__} {sig} team {len(self.opponent_team)}\n")
        except OSError:
            pass

    def _unstick(self):
        if self.phase == "VICTORY_TEXT":
            return self.advance_victory_sequence()
        if self.phase in ("REWARD_TEXT", "OUTRO"):
            return self._finish(self._beat_or("fled") if self.player_won else "lost")
        self.turn_actions.clear()
        self.faint_anim.active = False
        if self.player_hp <= 0:
            if any(p.current_hp > 0 for p in self.game.story_manager.player_team if p is not self.player_pokemon):
                return self.force_switch_menu()
            return self.trigger_outro(win=False)
        if self.opponent_hp <= 0:
            if self.trainer_class == "WILD":
                return self.trigger_outro(win=True)
            self.opponent_pokemon.current_hp = 0
            return self.on_switch_no()  # (the next Pokemon, or the win)
        self.return_to_menu_after_forced_switch()

    def _try_sos_call(self):  # (one wild Pokemon was handed out: no one else joins)
        return False

    def _get_play_state_instance(self):
        return self.map_state

    def _finish(self, outcome):
        if self.reported:
            return
        self.reported = True
        self._settle_xp()
        self.map_state.link.send_intent({"watch": None})
        for p in self.game.story_manager.player_team:
            gimmick_end_battle(p)
            forms.revert_form(p)
            if hasattr(p, "revert_transform"):
                p.revert_transform()
        self.map_state.fight_over(self.eid, outcome, getattr(self, "_thrown_ball", None))

    def _beat_or(self, other):
        return "beaten" if self.opponent_hp <= 0 else other

    def on_flee_complete(self):
        self._finish(self._beat_or("fled"))

    def _on_catch_exit(self):
        self._finish("caught" if self.catch_phase == "CAUGHT" else self._beat_or("fled"))

    def exit_battle(self, lost=False):
        self._finish("lost" if lost else self._beat_or("fled"))

    def perform_battle_black_out(self):
        self._finish("lost")

    def update(self):
        if self.map_state.pump():
            super().update()
            if self.game.current_state is self and not self.reported:
                self._watchdog()
            self._frame = getattr(self, "_frame", 0) + 1
            if self.game.current_state is self and not self.reported and self._frame % 6 == 0:
                feed = snapshot(self)
                if feed != self._sent:
                    self._sent = feed
                    self.map_state.link.send_intent({"watch": feed})


class GuestWildBattle(_GuestFight, WildBattleState):
    def __init__(self, game, pokemon, area, background, map_state, eid):
        self.map_state, self.eid, self.reported = map_state, eid, False
        super().__init__(game, pokemon, area, background_image=background)


class GuestTrainerBattle(_GuestFight, TrainerBattleState):
    def __init__(self, game, team, map_state, eid, **details):
        self.map_state, self.eid, self.reported = map_state, eid, False
        super().__init__(game, team, **details)
