"""Watching a friend's battle (Jordan, 11-08): the fight as it goes, on the battle's own widgets so it looks the same, and
each turn's question to try for practice. Whether you were right only shows once the player in the fight has answered.
Watching changes nothing in the fight."""
import pygame

from src.pokemon.data import Pokemon
from src.states.base import GameState
from src.ui import theme
from src.ui.dialogue import ClassicDialogueBox
from src.ui.panels import BattleActionMenu, CommandButton
from src.ui.widgets import Backdrop, MathBattleUI, MoveButton
from src.utils import Utils
from src.vfx.renderer import BattleRenderer

GIVE_UP = 20          # frames with nothing to show: the fight is over
FEEDBACK = {True: 16, False: 24}  # as the battle's own
SPECIALS = {"MEGA": theme.MEGA, "PRIMAL": (200, 60, 40), "Z-MOVE": (230, 170, 40), "TERA": (90, 190, 220)}


def _idle():
    pass


def _move_specs(battle):
    """The FIGHT menu's buttons as they are on the battler's screen."""
    out = []
    for b in battle.move_buttons:
        spec = {"rect": list(b.rect), "text": str(b.text)}
        if isinstance(b, MoveButton):
            spec.update(type=b.type_name, color=list(b.type_color), detail=b.detail, effect=b.effect, stab=bool(b.stab))
        out.append(spec)
    return out


def snapshot(battle):
    """A fight as those watching need it. The answer is only in it after the player in the fight has answered."""
    w = battle.__dict__.setdefault("_watch", {"qid": 0, "open": False, "result": None})
    asking = battle.phase == "BATTLE"
    if asking and not w["open"]:
        w.update(qid=w["qid"] + 1, open=True, q=str(battle.problem_str), opts=[str(o) for o in battle.options],
                 ans=str(battle.correct_ans))
    elif w["open"] and battle.phase != "BATTLE":
        w.update(open=False, result={"qid": w["qid"], "ans": w["ans"]})

    def side(p, hp, top):
        return {"id": int(p.id), "form": str(p.form), "shiny": bool(p.is_shiny), "name": str(p.display_name),
                "level": int(p.level), "status": p.status, "hp": max(0, int(hp)), "max": int(top)}
    box = battle.dialogue_box
    lines = box.text_lines or []
    out = {"foe": side(battle.opponent_pokemon, battle.opponent_hp, battle.opp_max_hp),
           "me": side(battle.player_pokemon, battle.player_hp, battle.player_max_hp), "phase": str(battle.phase),
           "say": str(lines[min(box.current_line, len(lines) - 1)]) if box.visible and lines else "",
           "bg": getattr(battle, "coop_bg", None), "result": w["result"],
           "specials": [str(b.text) for b in battle.action_menu.special_buttons]}
    if asking:
        out.update(qid=w["qid"], q=w["q"], opts=w["opts"])
    if battle.phase == "MOVE_SELECT":
        out["moves"] = _move_specs(battle)
    return out


class CoopWatchState(GameState):
    uses_keyboard = True

    def __init__(self, game, back, source, who, pump=None):
        super().__init__(game)
        self.back, self.source, self.who, self.pump = back, source, who, pump
        self.renderer = BattleRenderer(game)
        self.mons, self.background, self.bg_name = {}, None, ""
        self.feed, self.gone = source(), 0
        self.qid, self.picked, self.math, self.judged = None, None, None, None
        self.menu, self.menu_key, self.moves, self.moves_key, self.said = None, None, None, None, None
        f = game.assets.fonts
        self.font = f["label"]
        self.bar = Utils.get_full_dialogue_rect(game)
        self.box = ClassicDialogueBox(self.bar, [""], f["med"])
        self.box.visible = False
        self.btn_stop = CommandButton((game.width - 216, 14, 200, 56), "STOP", f["label"], self.stop, bg_color=theme.BACK, autosize=False)

    def stop(self):
        self.game.change_state(self.back)

    def _mon(self, info):
        key = (info["id"], info["form"], info["shiny"])
        if key not in self.mons:
            loader = self.game.loader
            form = "normal" if info["form"] == "gmax" else info["form"]
            self.mons[key] = Pokemon(loader.fetch_specific(info["id"], form=form, is_shiny=info["shiny"]), self.game.assets, size_mult=3.125)
        p = self.mons[key]
        p.display_name, p.level, p.status, p.current_hp = info["name"], info["level"], info["status"], info["hp"]
        return p

    def _pick(self, index):
        if self.picked is None and self.feed and "opts" in self.feed:
            self.picked = self.feed["opts"][index]

    def handle_events(self, events):
        for e in events:
            if self.btn_stop.handle_event(e):
                return
            if self.math is not None and self.picked is None:
                self.math.handle_event(e)

    def _judge(self):
        """Once the player in the fight has answered: the answer shows as it does in a battle."""
        res = self.feed.get("result")
        if self.math is None or not res or res["qid"] != self.qid or self.judged == self.qid:
            return
        self.judged = self.qid
        opts = self.feed.get("opts") or self.math.options
        right = opts.index(res["ans"]) if res["ans"] in opts else 0
        correct = self.picked == res["ans"]
        text = "You got it!" if correct else f"Nice try! It was {res['ans']}." if self.picked is not None else f"It was {res['ans']}."
        self.math.feedback = {"index": opts.index(self.picked) if self.picked in opts else len(opts), "right": right, "correct": correct,
                              "text": text, "frames": FEEDBACK[correct], "total": FEEDBACK[correct]}

    def update(self):
        if self.pump is not None and not self.pump():
            return
        now = self.source()
        if now is None:
            self.gone += 1
            if self.gone >= GIVE_UP:
                self.stop()
            return
        self.gone, self.feed = 0, now
        if "qid" in now and now["qid"] != self.qid:
            self.qid, self.picked = now["qid"], None
            self.math = MathBattleUI(self.game, now["q"], now["opts"], self._pick)
        self._judge()
        if self.math is not None and self.math.feedback:
            self.math.feedback["frames"] -= 1
            if self.math.feedback["frames"] <= 0:
                self.math = None
        if now.get("say") != self.said:
            self.said = now.get("say")
            if self.said:
                self.box.reset(self.said)
            else:
                self.box.visible = False
        if self.box.visible:
            self.box.update()

    def _bg(self):
        name = self.feed.get("bg") or ""
        if self.background is None or name != self.bg_name:
            assets = self.game.assets
            raw = (assets.get_background(name, from_overworld=False) if name else None) or assets.get_random_battle_background("field", "")
            self.background = pygame.transform.scale(raw, (self.game.width, self.bar.top)) if raw else None
            self.bg_name = name
        return self.background

    def _action_menu(self):
        key = (self.feed["me"]["name"], tuple(self.feed.get("specials", [])))
        if key != self.menu_key:
            specials = key[1]
            lead = specials[0] if specials and specials[0] in ("MEGA", "PRIMAL") else None
            extra = [(s, _idle, SPECIALS.get(s, theme.MEGA)) for s in specials if s != lead]
            self.menu = BattleActionMenu(self.game, key[0], _idle, _idle, _idle, _idle, on_mega=_idle if lead else None,
                                         mega_label=lead or "MEGA", extra=extra)
            self.menu.set_visibility(True)
            self.menu_key = key
        return self.menu

    def _move_menu(self):
        key = repr(self.feed["moves"])
        if key != self.moves_key:
            f = self.game.assets.fonts
            self.moves = [Backdrop(self.bar)]
            for s in self.feed["moves"]:
                if "type" in s:
                    self.moves.append(MoveButton(tuple(s["rect"]), s["text"], f["button"], f["label"], _idle, s["type"],
                                                 tuple(s["color"]), s["detail"], s["effect"], stab=s["stab"]))
                else:
                    self.moves.append(CommandButton(tuple(s["rect"]), s["text"], f["button"], _idle, bg_color=(120, 124, 144), autosize=False))
            self.moves_key = key
        return self.moves

    def draw(self):
        screen = self.game.screen
        feed = self.feed
        if not feed:
            screen.fill((28, 36, 62))
            return
        foe, me = feed["foe"], feed["me"]
        self.renderer.draw(screen, self._mon(foe), self._mon(me), foe["hp"], me["hp"], foe["max"], me["max"], background=self._bg(), show_fainted=True)
        theme.shadow_text(screen, f"Watching {self.who}", self.font, self.game.width // 2, 20, color=(255, 255, 255), shadow=(16, 20, 36), align="center")
        self.btn_stop.draw(screen)
        if self.math is not None:
            self.math.draw(screen)
            if self.picked in self.math.options and not self.math.feedback:  # (your try, till the answer shows)
                pygame.draw.rect(screen, (240, 190, 40), self.math.answer_grid.button_rects[self.math.options.index(self.picked)], 5, border_radius=10)
        elif feed.get("moves"):
            for widget in self._move_menu():
                widget.draw(screen)
        elif feed.get("phase") == "MENU":
            self._action_menu().draw(screen)
        elif self.box.visible:
            self.box.draw(screen)
        else:
            theme.draw_textbox(screen, self.bar)
