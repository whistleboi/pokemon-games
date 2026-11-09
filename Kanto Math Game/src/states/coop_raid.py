"""A guest in the host's Max Raid (Jordan, 11-08): the battle's own screen and buttons, your own Pokemon, your own move and
math question each turn. The fight itself runs on the host's game."""
import pygame

from src.pokemon import moves as movelib
from src.pokemon.mechanics import TypeAdvantage
from src.states.battle import TrainerBattleState
from src.states.coop_watch import CoopWatchState
from src.ui import theme
from src.ui.widgets import Backdrop, MathBattleUI, MoveButton

FEEDBACK = {True: 16, False: 24}


class CoopRaidState(CoopWatchState):
    _draw_raid_allies = TrainerBattleState._draw_raid_allies
    TYPE_COLORS = TrainerBattleState.TYPE_COLORS

    def __init__(self, game, back, source, who, pump, my_pid):
        super().__init__(game, back, source, who, pump)
        self.my_pid, self.turn, self.stage, self.buttons, self.chosen = my_pid, None, "wait", [], None
        self.raid_allies, self.my_answer = [], None
        self.btn_stop.text = "LEAVE RAID"

    def stop(self):  # (LEAVE RAID)
        self.back.left_raid()

    def _me(self):
        raid = (self.feed or {}).get("raid") or {}
        return next((h for h in raid.get("humans", []) if h["pid"] == self.my_pid), None)

    def _build_moves(self, me):
        box, f = self.bar, self.game.assets.fonts
        pad, gap = 16, 10
        bw, bh = (box.width - pad * 2 - gap) // 2, (box.height - pad * 2 - gap - 4) // 2
        chart = TypeAdvantage(self.game.loader.area_data.get("TYPE_CHART", {}))
        foe_types, own = self._mon(self.feed["foe"]).types, {t.upper() for t in self._mon(me).types}
        self.buttons = [Backdrop(box)]
        for i, name in enumerate(me["moves"][:4]):
            d = movelib.info(self.game, name)
            power, mtype = d.get("power") or 0, d.get("type")
            eff = chart.get_multiplier(mtype, foe_types) if mtype and power else 1
            effect = "super" if eff > 1 else "weak" if 0 < eff < 1 else "none" if eff == 0 else None
            self.buttons.append(MoveButton((box.x + pad + (i % 2) * (bw + gap), box.y + pad + (i // 2) * (bh + gap), bw, bh), name.replace("-", " "),
                                           f["button"], f["label"], (lambda n=name: self._pick_move(n)), mtype or "???",
                                           self.TYPE_COLORS.get(mtype, (120, 120, 120)), f"Pow {power}" if power else "Status", effect,
                                           stab=bool(power and mtype) and mtype.upper() in own))

    def _pick_move(self, name):
        self.chosen, self.stage = name, "math"
        problem, self.my_answer, options = self.game.math.generate(self.game.story_manager.get_math_level(), num_options=4)
        self.math = MathBattleUI(self.game, problem, options, self._answered)

    def _answered(self, index):
        options, right = self.math.options, self.math.options[index] == self.my_answer
        self.back.link.send_intent({"raid_turn": {"turn": self.turn, "move": self.chosen, "right": right}})
        at = options.index(self.my_answer) if self.my_answer in options else index
        self.math.feedback = {"index": index, "right": at, "correct": right, "text": "You got it!" if right else f"Nice try! It was {self.my_answer}.",
                              "frames": FEEDBACK[right], "total": FEEDBACK[right]}
        self.stage = "answered"

    def handle_events(self, events):
        for e in events:
            if self.btn_stop.handle_event(e):
                return
            if self.stage == "pick":
                for b in self.buttons[1:]:
                    if b.handle_event(e):
                        return
            elif self.stage == "math" and self.math is not None:
                self.math.handle_event(e)

    def update(self):
        if not self.pump():
            return
        now = self.source()
        if now is None:  # (the host is in a menu for a moment: the raid goes on)
            return
        self.feed = now
        self._play_attacks(now)
        raid, me = now.get("raid"), self._me()
        if raid and me and raid["turn"] != self.turn and me["hp"] > 0:
            self.turn, self.stage, self.math = raid["turn"], "pick", None
            self._build_moves(me)
        elif me and me["hp"] <= 0:
            self.stage, self.math = "out", None
        if self.math is not None and self.math.feedback:
            self.math.feedback["frames"] -= 1
            if self.math.feedback["frames"] <= 0:
                self.math, self.stage = None, "wait"
        if now.get("say") != self.said:
            self.said = now.get("say")
            if self.said:
                self.box.reset(self.said)
            else:
                self.box.visible = False
        if self.box.visible:
            self.box.update()

    def draw(self):
        screen, feed, me = self.game.screen, self.feed, self._me()
        if not feed or not me:
            screen.fill((28, 36, 62))
            return
        foe = feed["foe"]
        self.renderer.draw(screen, self._mon(foe), self._mon(me), foe["hp"], me["hp"], foe["max"], me["max"], background=self._bg(), show_fainted=True,
                           anim_ctrl=self.anim_ctrl, move_anim=self.move_anim, keep_battlers=bool(self.move_anim))
        team = [(self.who, None, self._mon(feed["me"]))]
        team += [(h["who"], None, self._mon(h)) for h in feed["raid"]["humans"] if h["pid"] != self.my_pid]
        self.raid_allies = team
        self._draw_raid_allies(screen)
        theme.shadow_text(screen, "Max Raid", self.font, self.game.width // 2, 20, color=(255, 255, 255), shadow=(16, 20, 36), align="center")
        self.btn_stop.draw(screen)
        if self.math is not None:
            self.math.draw(screen)
        elif self.stage == "pick":
            for b in self.buttons:
                b.draw(screen)
        elif self.box.visible:
            self.box.draw(screen)
        else:
            theme.draw_textbox(screen, self.bar)
            words = "Your team is out. Cheer them on!" if self.stage == "out" else "Waiting for the others..."
            theme.shadow_text(screen, words, self.font, self.bar.x + 30, self.bar.centery - 12, color=theme.TEXT, shadow=(220, 224, 232))
