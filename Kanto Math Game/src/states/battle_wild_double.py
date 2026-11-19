"""Wild double battles (Jordan 11-18, with Platinum's walking partners): two wild Pokemon at once, you and your partner
against them (src/world/walk_partners.py). The double battle engine (battle_double.py) plays it; what's wild about it:

- No trainer: "Wild X and wild Y appeared!", no prize-Ball reward, RUN works as in any wild battle.
- A Poke Ball can be thrown only when one wild Pokemon is left standing (the games: "It's no good! It's impossible to aim
  when there are two Pokemon!"). The throw is your Pokemon's action that turn; the catch is the games' formula
  (catching.throw), kept as in any wild battle (complete_catch: the party, else the PC).
- A knocked-out wild Pokemon can't be caught (as in the games' doubles): no catch window.
- After every battle (won, caught, or run from) your partner heals your team, as Platinum's partners do.
"""
import pygame

from src.states.battle_double import DoubleBattleState
from src.pokemon import catching


class WildDoubleBattleState(DoubleBattleState):
    def __init__(self, game, wild_pair, area_name, partner=None, background_image=None):
        opts = {"double": True, "heal_after": True}
        if partner:
            opts["partner"] = dict(partner)
        super().__init__(game, [p for p in wild_pair if p is not None], trainer_class="WILD", battle_type="field",
                         area_name=area_name, background_image=background_image, options=opts)
        self.rewards = {"balls": 0}
        self.trainer_name = None
        names = " and ".join(f"wild {p.display_name.upper()}" for p in wild_pair if p is not None)
        self._opening = [f"{names[0].upper() + names[1:]} appeared!"]
        if self.partner_team:
            self._opening.append(f"{self.partner_name}: I'll help! Let's take them on together!")

    def start(self):
        super().start()
        if getattr(self, "_opening", None) and self.phase == "MENU":
            lines, self._opening = self._opening, None
            self.show_message(lines, callback=self.return_to_menu)

    # ---- catching
    def throw_from_bag(self):
        story = self.game.story_manager
        standing = self.battlers("opponent")
        if len(standing) != 1:
            self.show_message(["It's no good! You can't aim a ball when there are two wild Pokemon!"],
                              callback=self.return_to_menu)
            return
        foe = standing[0]
        ball = catching.selected(story)
        catching.use(story, ball)
        terrain = self.game.loader.area_data.get("STORY_PROGRESSION", {}).get(story.current_area_key, {}).get("battle_type", "")
        success, shakes, critical = catching.throw(self.game, foe, ball, hp=max(1, foe.current_hp), max_hp=foe.get_max_hp(),
                                                   turn=max(1, self.turn_count), terrain=terrain)
        lines = [f"{self.game.player_name} threw a {catching.label(ball)}!"]
        if not success:
            self.show_message(lines + [self.BREAK_FREE[min(shakes, 3)]], callback=self.on_item_used)   # (the turn goes on)
            return
        if critical:
            lines.append("A critical capture!")
        lines.append(f"Gotcha! {foe.display_name.upper()} was caught!")
        catching.after_catch(self.game, foe, ball)
        self._caught = foe
        self.o_slots = [None if p is foe else p for p in self.o_slots]
        self.opponent_team = [p for p in self.opponent_team if p is not foe]
        play = self.game.states.get("play")
        if play is not None and hasattr(play, "complete_catch"):
            play.p_data = [None, foe, None]
            play.complete_catch(1)
        else:
            story.player_team.append(foe) if len(story.player_team) < 6 else None
        self.show_message(lines, callback=lambda: self._wild_end(won=True, caught=True))

    BREAK_FREE = ("Oh no! The Pokemon broke free!", "Aww! It appeared to be caught!",
                  "Aargh! Almost had it!", "Gah! It was so close, too!")

    # ---- the end
    def trigger_outro(self, win):
        if not win:
            return super().trigger_outro(False)
        self._wild_end(won=True)

    def _wild_end(self, won=True, caught=False):
        self.player_won = True
        if not caught:
            self.game.music.victory()
        lines = [] if caught else ["The wild Pokemon were defeated!"]
        lines += self._partner_heal_lines()
        self.action_menu.set_visibility(False)
        if self.math_ui:
            self.math_ui.set_visibility(False)
        if not lines:
            return self.on_flee_complete()
        self.phase = "MESSAGE"
        self.show_message(lines, callback=self.on_flee_complete)

    def _partner_heal_lines(self):
        """Your partner patches your team up after the battle (Platinum's partners do, every time)."""
        from src.states.overworld.area_transition import heal_team
        heal_team(self.game)
        if self.partner_team:
            return [f"{self.partner_name} healed your Pokemon."]
        return []

    def handle_run(self):
        if self.run_blocked():   # (Shadow Tag, Arena Trap: as in any wild battle)
            return super().handle_run()

        def after():   # (your partner heals you after running away too)
            self._partner_heal_lines()
            self.on_flee_complete()
        self.show_message(["Got away safely!"], callback=after)
