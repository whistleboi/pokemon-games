"""A guest's wild battle (Jordan, 11-08): the game's own battle, math every turn, on the guest's device with borrowed
Pokemon. It only differs at the end: instead of changing a save or the story, it tells the host how it went."""
from src.pokemon import forms
from src.states.battle import WildBattleState
from src.states.battle_gimmicks import end_battle as gimmick_end_battle
from src.states.coop_watch import snapshot


class GuestWildBattle(WildBattleState):
    _sent = None

    def __init__(self, game, pokemon, area, background, map_state, eid):
        self.map_state, self.eid, self.reported = map_state, eid, False
        super().__init__(game, pokemon, area, background_image=background)

    def _try_sos_call(self):  # (one wild Pokemon was handed out: no one else joins)
        return False

    def _get_play_state_instance(self):
        return self.map_state

    def _finish(self, outcome):
        if self.reported:
            return
        self.reported = True
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
            self._frame = getattr(self, "_frame", 0) + 1
            if self.game.current_state is self and not self.reported and self._frame % 6 == 0:
                feed = snapshot(self)
                if feed != self._sent:
                    self._sent = feed
                    self.map_state.link.send_intent({"watch": feed})
