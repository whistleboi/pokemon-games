"""Watching a friend's battle (Jordan, 11-08): the fight as it goes, on the battle's own widgets so it looks the same, and
each turn's question to try for practice. Whether you were right only shows once the player in the fight has answered.
Watching changes nothing in the fight."""
import types

import pygame

from src.coop import world
from src.pokemon.data import Pokemon
from src.states.base import GameState
from src.states.overworld.overworld_battle import OverworldView
from src.ui import theme
from src.ui.dialogue import ClassicDialogueBox
from src.ui.panels import BattleActionMenu, CommandButton
from src.ui.widgets import Backdrop, MathBattleUI, MoveButton
from src.utils import Utils
from src.vfx import move_anim as move_anims
from src.vfx.animations import AnimationController, battle_spot
from src.vfx.renderer import BattleRenderer

GIVE_UP = 20          # frames with nothing to show: the fight is over
FEEDBACK = {True: 16, False: 24}  # as the battle's own
SPECIALS = {"MEGA": theme.MEGA, "PRIMAL": (200, 60, 40), "Z-MOVE": (230, 170, 40), "TERA": (90, 190, 220)}


def _idle():
    pass


def _map_info(battle):
    """Where a fight on the map is, for someone watching on the same map."""
    view, play = battle.overworld, battle.overworld.play
    index = getattr(play.run, "index", None)
    return {"area": play.area_key, "floor": play.floor if index is None else index, "spot": list(view.spot), "mine": list(view.mine),
            "focus": list(view.focus), "stander": getattr(play, "ow_stander", None)}


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
    from src.coop import raid
    if raid.is_raid(battle):
        out["raid"] = raid.info(battle)
    anim, ctrl = getattr(battle, "move_anim", None), getattr(battle, "anim_ctrl", None)
    if anim is not None and anim is not w.get("anim"):  # (numbered, so a watcher never misses one or plays it twice)
        w.update(anim=anim, anim_n=w.get("anim_n", 0) + 1)
        w["anim_info"] = {"n": w["anim_n"], "name": battle.move_anim_name, "side": battle.move_anim_side}
    out["anim"] = w.get("anim_info")
    out["lunge"] = getattr(anim, "user_side", None) if anim is not None else (ctrl.lunge_side if ctrl is not None and ctrl.is_lunging else None)
    if getattr(battle, "overworld", None) is not None:
        out["map"] = _map_info(battle)
        out.update(fainting=battle.fainting_side, hide=bool(getattr(battle, "_ow_hide", False)), ko=bool(getattr(battle, "_ow_ko", False)),
                   ball=[int(v) for v in battle.ball_pos] if battle.phase == "CATCH_ANIMATION" else None)
    if asking:
        out.update(qid=w["qid"], q=w["q"], opts=w["opts"])
    if battle.phase == "MOVE_SELECT":
        out["moves"] = _move_specs(battle)
    return out


class _MapView(OverworldView):
    """The map view of a fight, from what's sent to those watching (it never touches a real battle)."""

    def __init__(self, play, info):
        self.play, self.info = play, info
        self.spot, self.mine, self.focus = tuple(info["spot"]), tuple(info["mine"]), tuple(info["focus"])
        self.fx, self.shots, self.last, self.anim_seen = [], [], {}, None

    def _draw_map(self, screen):
        play, stander = self.play, self.info.get("stander")
        is_guest = hasattr(play, "ow_stander")  # (a guest's map; the host's is the game's own)
        if is_guest:
            play.ow_stander = stander
            play._ow_foe = types.SimpleNamespace(x=self.spot[0], y=self.spot[1])
        else:
            play._ow_foe = next((m for m in play.run.floor.movers if (m.x, m.y) == self.spot and m.kind == "wild"), None)
        super()._draw_map(screen)
        play._ow_foe = None
        if is_guest:
            play.ow_stander = None
            return
        play._backdrop = True  # (the same camera as the map just drawn)
        cx, cy = play._camera()
        play._backdrop = False
        game = play.game
        ox, oy = int(game.width / 2 - cx), int(game.height / 2 - cy)
        world.draw_guests(game, ox, oy, self.info["area"], self.info["floor"])
        if stander:  # (a guest's trainer is off the host's map while they fight)
            img = play._trainer_img({"sprite": stander.get("sprite")}, tuple(stander.get("f") or (0, 1)))
            if img is not None:
                screen.blit(img, img.get_rect(midbottom=(ox + stander["x"] * world.TILE + world.TILE // 2, oy + (stander["y"] + 1) * world.TILE)))


class CoopWatchState(GameState):
    uses_keyboard = True

    def __init__(self, game, back, source, who, pump=None):
        super().__init__(game)
        self.back, self.source, self.who, self.pump = back, source, who, pump
        self.renderer = BattleRenderer(game)
        self.mons, self.background, self.bg_name = {}, None, ""
        self.feed, self.gone = source(), 0
        self.qid, self.picked, self.math, self.judged = None, None, None, None
        self.view, self.view_key = None, None
        self.anim_ctrl, self.move_anim, self.lunge_seen = AnimationController(), None, None
        self.anim_seen = ((self.feed or {}).get("anim") or {}).get("n")  # (joined part way: not a move from before)
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
        self._play_attacks(now)
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

    def _play_attacks(self, feed):
        """The move's own animation if it has one, else the attacker's lunge, and the HP bars sliding."""
        self.renderer.tick()
        self.anim_ctrl.update()
        anim = feed.get("anim")
        if anim and anim["n"] != self.anim_seen:
            self.anim_seen = anim["n"]
            self.move_anim = self._start_anim(anim, feed)
        if self.move_anim is not None:
            self.move_anim.update()
            if self.move_anim.done:
                self.move_anim = None
        lunge = feed.get("lunge")
        if lunge and lunge != self.lunge_seen and self.move_anim is None:
            self.anim_ctrl.start_lunge(lunge)
        self.lunge_seen = lunge

    def _start_anim(self, info, feed):
        found, swapped = move_anims.find(self.game.assets.assets_dir, info["name"], info["side"])
        if not found:
            return None
        game, side = self.game, info["side"]
        mons = {"player": self._mon(feed["me"]), "opponent": self._mon(feed["foe"])}
        other = "opponent" if side == "player" else "player"
        return move_anims.MoveAnimation(game, found, battle_spot(game, mons[side], side), battle_spot(game, mons[other], other),
                                        self.bar.top, swapped, side)

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

    def _map_view(self):
        """The map view, if this fight is on the map you're on."""
        info, play = self.feed.get("map"), self.back
        if not info or not hasattr(play, "draw_backdrop") or getattr(play, "area_key", None) != info["area"]:
            return None
        here = play.floor if hasattr(play, "surf") else getattr(getattr(play, "run", None), "index", None)
        if here != info["floor"] or (hasattr(play, "surf") and not play.surf):
            return None
        key = repr((info["spot"], info["mine"], info["focus"]))
        if key != self.view_key:
            self.view, self.view_key = _MapView(play, info), key
        self.view.info = info
        return self.view

    def _draw_on_map(self, screen, view, foe, me):
        feed = self.feed
        lunge = feed.get("lunge")
        self.move_anim = None  # (a fight on the map shows its attacks as orbs, as it does for the player in it)
        fight = types.SimpleNamespace(opponent_pokemon=self._mon(foe), player_pokemon=self._mon(me), opponent_hp=foe["hp"], player_hp=me["hp"],
                                      opp_max_hp=foe["max"], player_max_hp=me["max"], phase=feed["phase"], fainting_side=feed.get("fainting"),
                                      _ow_hide=feed.get("hide", False), _ow_ko=feed.get("ko", False), move_anim=None,
                                      anim_ctrl=types.SimpleNamespace(is_lunging=bool(lunge), lunge_side=lunge))
        view.draw(screen, fight)
        if feed.get("ball"):
            ball = pygame.transform.smoothscale(self.game.assets.ball_imgs[0], (56, 56))
            screen.blit(ball, ball.get_rect(center=tuple(feed["ball"])))

    def draw(self):
        screen = self.game.screen
        feed = self.feed
        if not feed:
            screen.fill((28, 36, 62))
            return
        foe, me = feed["foe"], feed["me"]
        view = self._map_view()
        if view is not None:
            self._draw_on_map(screen, view, foe, me)
        else:
            self.renderer.draw(screen, self._mon(foe), self._mon(me), foe["hp"], me["hp"], foe["max"], me["max"], background=self._bg(), show_fainted=True,
                                 anim_ctrl=self.anim_ctrl, move_anim=self.move_anim, keep_battlers=bool(self.move_anim))
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
