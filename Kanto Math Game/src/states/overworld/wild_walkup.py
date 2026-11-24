"""Wild Pokemon that come to you on a walked map (Jordan 11-23, branch region/systems).

Honey, Sweet Scent and the White Flute: the three Pokemon picked for the catch screen pop out of the grass nearby (out of
the water, when you surf), walk up to stand round you, and only then does the catch screen open - see-through, over the
live map (dungeon.py's _draw_catch_layer). Afterwards the one you caught is gone and the others run off.

Swarms (src/world/swarms.py): on today's swarm place, a wild Pokemon of the swarm's species met in its grass (or on its
water, for a Surf swarm) now and then calls its friends (SWARM_CALL): two more walk up the same way, and a short battle is
fought right on the map (no see-through layer): three math problems. A right answer knocks one out (half Exp. each for
the first two); the third right answer leaves the last one - the highest level of the three - to CATCH (a sure catch with
your selected ball) or FAINT, either for full Exp. A wrong answer, or the time running out, and one of them hits your lead
Pokemon; if it faints, the swarm runs off.

Map movers of kind "walkup" are these Pokemon: drawn like wild ones (their overworld sprite), moved here by an npc.Motion,
never by the map's own wild Pokemon turns (core.Run.others_act skips them).
Check: dev/checks/walkup_body.py (bash dev/checks/run.sh walkup)."""
import math
import random
from collections import deque

import pygame

from src.config import FPS
from src.dungeon import core, npc
from src.pokemon import catching
from src.ui import theme

WALKUP = "walkup"
SWARM_CALL = 0.6          # (how often a swarm Pokemon met on its own place calls its friends: about 1 meeting in 4 there)
HOP = int(FPS * 0.35)     # (frames it takes to pop out of the grass)
WALK_LIMIT = FPS * 6      # (frames before anyone still on the way is simply put on its spot)
SETTLE = int(FPS * 0.35)  # (a breath once they're all there, before the screen opens)
LEAVE_FRAMES = FPS * 3    # (frames to run off; then gone, seen or not)
FADE = int(FPS * 0.4)
ORB = int(FPS * 0.4)      # (an attack flying across)
FAINT = int(FPS * 0.6)
THROW = int(FPS * 0.9)


class WildWalkUps:
    # ---------------------------------------------------------------- where they come from and stand
    def _wu_water(self):
        return self.run.floor.tile(*self.run.player) == core.SURF

    def _wu_free(self, t, m=None, water=False, claimed=()):
        """Can a walking-up Pokemon step onto t: the same kind of ground as you (land, or the sea you surf), nothing on it."""
        f = self.run.floor
        x, y = t
        if not (0 <= x < f.w and 0 <= y < f.h) or not f.walkable(x, y) or (f.tile(x, y) == core.SURF) != water:
            return False
        if t in f.exits or t in f.items or t in f.tm_spots or t in (getattr(f, "decor", None) or {}) or t in claimed:
            return False
        if t == tuple(self.run.player) or (getattr(self, "anim", 0) > 0 and t == tuple(getattr(self, "anim_from", ()))):
            return False
        for o in f.movers:
            if o is m:
                continue
            mo = getattr(o, "motion", None)
            if t == (o.x, o.y) or (mo is not None and mo.moving() and t == mo.frm):
                return False
        return True

    def _wu_spots(self, n, water, claimed=()):
        """Up to n tiles round you to stand on: in front, to either side, behind, then the corners (not your Pokemon's)."""
        px, py = self.run.player
        fx, fy = getattr(self, "facing", (0, 1)) or (0, 1)
        ring = [(fx, fy), (fy, fx), (-fy, -fx), (-fx, -fy), (fx + fy, fy + fx), (fx - fy, fy - fx),
                (-fx + fy, -fy + fx), (-fx - fy, -fy - fx)]
        partner = tuple(getattr(self, "partner", (px, py)) or (px, py))
        out, taken = [], set(claimed)
        for dx, dy in ring:
            t = (px + dx, py + dy)
            if t != partner and t not in out and self._wu_free(t, water=water, claimed=taken):
                out.append(t)
                taken.add(t)
            if len(out) >= n:
                break
        return out

    def _wu_reach(self, water, depth=7):
        """{tile: steps from you} over the ground they can walk on, out to depth."""
        start = tuple(self.run.player)
        seen, todo = {start: 0}, deque([start])
        while todo:
            cur = todo.popleft()
            if seen[cur] >= depth:
                continue
            for dx, dy in core.DIRS:
                t = (cur[0] + dx, cur[1] + dy)
                if t not in seen and self._wu_free(t, water=water):
                    seen[t] = seen[cur] + 1
                    todo.append(t)
        return seen

    def _wu_sources(self, n, water, rng):
        """n tiles 3 to 6 steps off where they pop out (tall grass first, then anywhere in view), spread apart."""
        f = self.run.floor
        reach = self._wu_reach(water)
        far = [t for t, d in reach.items() if 3 <= d <= 6]
        if len(far) < n:
            far = [t for t, d in reach.items() if d >= 1]
        rng.shuffle(far)
        far.sort(key=lambda t: (0 if water or f.tile(*t) == core.GRASS else 1, 0 if self.run.visible(*t) else 1))
        picked = []
        for t in far:
            if all(abs(t[0] - o[0]) + abs(t[1] - o[1]) >= 2 for o in picked):
                picked.append(t)
            if len(picked) >= n:
                break
        return picked

    # ---------------------------------------------------------------- walking up
    def walkup_start(self, mons, then, keep=()):
        """Bring mons to you (new map Pokemon, popping out nearby); keep: wild ones already beside you that join them (a
        swarm's caller). Then then() - the catch screen, the swarm's battle. Returns the movers."""
        f = self.run.floor
        rng = random.Random()
        water = self._wu_water()
        for k in keep:   # (already here: it stays where it is, turned to you)
            k.kind, k.alert = WALKUP, False
            k.motion = npc.Motion((k.x, k.y), seed=f"wu{id(k)}", facing=tuple(k.facing or (0, 1)))
            k._wu_age = HOP
        spots = self._wu_spots(len(mons), water, claimed={(k.x, k.y) for k in keep})
        sources = self._wu_sources(len(mons), water, rng)
        movers = list(keep)
        for i, mon in enumerate(mons):
            if i >= len(spots):   # (no room round you: it is in the catch, just not on the map)
                break
            goal = spots[i]
            src = min(sources, key=lambda s: abs(s[0] - goal[0]) + abs(s[1] - goal[1])) if sources else goal
            if src in sources:
                sources.remove(src)
            m = core.Mover(WALKUP, src[0], src[1], payload=mon)
            m.motion = npc.Motion(src, seed=f"wu{i}:{rng.random()}")
            m.motion.emote = int(FPS * 0.9)
            m._wu_goal, m._wu_age = goal, 0
            if src != goal:
                m.motion.walk(goal, lambda t, m=m: self._wu_free(t, m, water), beside=False)
            f.movers.append(m)
            movers.append(m)
        self._wu = {"movers": movers, "then": then, "t": 0, "water": water, "settle": 0}
        self._wu_hud(False)
        self.walk_goal = None
        self.mode = "WALKUP"
        first = movers[0].payload if movers else None
        if first is not None and getattr(first, "cry", None):
            first.cry.play()
        return movers

    def _wu_tick(self):
        wu = getattr(self, "_wu", None)
        if not wu:
            self.mode = "MAP"
            return
        wu["t"] += 1
        here = True
        for m in wu["movers"]:
            m._wu_age = getattr(m, "_wu_age", HOP) + 1
            if m._wu_age < HOP:   # (still popping out of the grass)
                here = False
                continue
            mo = m.motion
            mo.tick(lambda t, m=m: self._wu_free(t, m, wu["water"]))
            m.x, m.y = mo.pos
            m.facing = mo.facing
            if not mo.idle():
                here = False
        if not here and wu["t"] > WALK_LIMIT:   # (someone stuck on the way: on its spot now)
            for m in wu["movers"]:
                goal = getattr(m, "_wu_goal", None)
                if goal and (m.x, m.y) != goal and self._wu_free(goal, m, wu["water"]):
                    m.motion.pos = m.motion.frm = goal
                m.motion.path, m.motion.t = [], 1.0
                m.x, m.y = m.motion.pos
            here = True
        if not here:
            return
        if wu["settle"] == 0:   # (all here: they look at you, you look at the middle one)
            for m in wu["movers"]:
                m.motion.face(self.run.player)
                m.facing = m.motion.facing
            mid = wu["movers"][len(wu["movers"]) // 2] if wu["movers"] else None
            if mid is not None:
                self._wu_face(mid)
        wu["settle"] += 1
        if wu["settle"] >= SETTLE:
            then = wu.pop("then", None)
            self.mode = "MAP"
            if then:
                then()

    def _wu_hud(self, shown):
        """The map's MENU button: hidden while they walk up and while the swarm battles you (taps go nowhere else)."""
        for b in getattr(self, "hud_buttons", None) or []:
            b.set_visibility(shown)

    def _wu_face(self, m):
        px, py = self.run.player
        dx, dy = m.x - px, m.y - py
        if dx or dy:
            self.facing = ((1 if dx > 0 else -1), 0) if abs(dx) > abs(dy) else (0, (1 if dy > 0 else -1))

    def _wu_lift(self, m):
        """How far up it's drawn: a hop out of the grass, a fainting sink (negative)."""
        age = getattr(m, "_wu_age", HOP)
        if age < HOP:
            return int(math.sin(math.pi * age / HOP) * 22)
        return -int(getattr(m, "_wu_sink", 0))

    # ---------------------------------------------------------------- running off
    def walkup_leave(self, movers=None, gone=()):
        """The group breaks up: each of movers (default: the whole group) runs off out of sight; gone ones vanish now."""
        wu = getattr(self, "_wu", None) or {}
        movers = list(wu.get("movers", ()) if movers is None else movers)
        water = wu.get("water", False)
        self._wu = None
        leaving = getattr(self, "_wu_leavers", None) or []
        px, py = self.run.player
        reach = self._wu_reach(water, depth=9)
        for m in movers:
            if any(m is g for g in gone) or m.payload is None:
                self._wu_drop(m)
                continue
            far = [t for t in reach if (t[0] - px) * (m.x - px) + (t[1] - py) * (m.y - py) > 0] or list(reach)
            goal = max(far, key=lambda t: abs(t[0] - px) + abs(t[1] - py)) if far else (m.x, m.y)
            mo = getattr(m, "motion", None) or npc.Motion((m.x, m.y))
            m.motion, mo.emote = mo, 0
            mo.walk(goal, lambda t, m=m: self._wu_free(t, m, water), beside=False)
            m._wu_leave, m._wu_water = 0, water
            leaving.append(m)
        self._wu_leavers = leaving

    def _wu_drop(self, m):
        for fl in getattr(self.run, "floors", [self.run.floor]):
            if m in fl.movers:
                fl.movers.remove(m)

    def _wu_leavers_tick(self):
        leaving = getattr(self, "_wu_leavers", None)
        if not leaving:
            return
        keep = []
        for m in leaving:
            if m not in self.run.floor.movers:   # (another floor now: gone)
                self._wu_drop(m)
                continue
            m._wu_leave += 1
            mo = m.motion
            for _ in range(2):   # (running: twice the walking pace)
                mo.tick(lambda t, m=m: self._wu_free(t, m, m._wu_water))
            m.x, m.y = mo.pos
            m.facing = mo.facing
            left = LEAVE_FRAMES - m._wu_leave
            if mo.idle() or not self.run.visible(m.x, m.y):
                left = min(left, FADE)
                m._wu_leave = max(m._wu_leave, LEAVE_FRAMES - FADE)
            m._wu_alpha = max(0, min(255, int(255 * left / FADE)))
            if left <= 0:
                self._wu_drop(m)
                continue
            keep.append(m)
        self._wu_leavers = keep

    # ---------------------------------------------------------------- Honey's catch screen
    def complete_catch(self, idx):
        self._wu_caught = self.p_data[idx] if 0 <= idx < len(self.p_data) else None
        return super().complete_catch(idx)

    def walkup_catch_over(self):
        """The catch screen is done: the one you caught is gone, the rest run off."""
        wu = getattr(self, "_wu", None)
        if not wu or wu.get("kind") != "catch":
            return
        got = getattr(self, "_wu_caught", None)
        self._wu_caught = None
        self.walkup_leave(gone=[m for m in wu["movers"] if got is not None and m.payload is got])

    # ---------------------------------------------------------------- a swarm on the map
    def _swarm_today(self):
        """(species, "grass" | "surf") of today's swarm when it is here, else None."""
        from src.world import swarms
        story = self.game.story_manager
        region = story.area_region(self.area_key) if hasattr(story, "area_region") else story.get_current_region()
        sw = swarms.today(story, region)
        if not sw or sw[0] != self.area_key:
            return None
        kind = swarms.kind_today(story, region)
        from src.world import regional_forms
        if not regional_forms.species_allowed(self.game, int(sw[1])):   # (Kanto's lock, as swarms.adjust: none of a region not played yet)
            return None
        return (int(sw[1]), kind) if kind in ("grass", "surf") else None

    def swarm_call(self, mover, rng=None):
        """A wild Pokemon met on today's swarm place: now and then it is one of the swarm and calls two friends over
        (they walk up, then the swarm's battle). True when it did."""
        rng = rng or random.Random()
        p = getattr(mover, "payload", None)
        sw = self._swarm_today()
        if (sw is None or p is None or mover.kind != "wild" or int(p.id) != sw[0] or getattr(self, "contest", None)
                or getattr(self, "safari", None) or getattr(p, "snack_visitor", None)):
            return False
        water = self.run.floor.tile(mover.x, mover.y) == core.SURF
        if water != (sw[1] == "surf") or water != self._wu_water():
            return False
        lead = self.lead()
        if lead is None or lead.current_hp <= 0 or rng.random() >= SWARM_CALL:
            return False
        friends = [f for f in (self._swarm_mon(sw[0]) for _ in range(2)) if f is not None]
        if len(friends) < 2 or len(self._wu_spots(2, water, claimed={(mover.x, mover.y)})) < 2:
            return False
        self.walk_goal = None
        for q in [p] + friends:
            self.game.data.mark_seen(q.id)
        if getattr(p, "cry", None):
            p.cry.play()
        name = p.display_name.upper()

        def come():
            group = self.walkup_start(friends, lambda: self._sw_begin(group), keep=[mover])
            self._wu["kind"] = "swarm"
        self.say([f"The wild {name} called its friends!"], then=come)
        return True

    def _swarm_mon(self, pid):
        from src.pokemon.data import Pokemon
        from src.world import levels
        raw = self.game.loader._fetch_raw(id_pool=[pid], area_data=self.area_data)
        if not raw or raw.get("id", 0) == 0:
            return None
        mon = Pokemon(raw, self.game.assets, size_mult=3.125)
        levels.set_wild(self.game, mon, self.area_key)
        return mon

    def _sw_begin(self, movers):
        order = sorted(movers, key=lambda m: m.payload.level)   # (the last one standing: the highest level of the three)
        for m in order:
            m._wu_hp = 1.0
        self._sw = {"order": order, "k": 0, "phase": "TALK", "t": 0, "fx": []}
        self.mode = "SWARM"
        name = order[0].payload.display_name.upper()
        self.say([f"A swarm of {name} surrounds you!", "Answer right to knock them out, one at a time!"], then=self._sw_ask)

    def _sw_target(self):
        sw = self._sw
        return sw["order"][min(sw["k"], len(sw["order"]) - 1)]

    def _sw_ask(self):
        sw = self._sw
        self._wu_face(self._sw_target())
        self.problem_str, self.correct_ans, self.options = self.generate_math_set(self.total_caught, num_options=3)
        self.math_timer = self.math_full = self.game.story_manager.timer_frames(self._math_seconds())
        sw["phase"], sw["t"] = "ASK", 0

    def _math_seconds(self):
        from src.states.overworld import dungeon
        return dungeon.MATH_SECONDS

    def _sw_answer(self, idx):
        sw = getattr(self, "_sw", None)
        if not sw or sw["phase"] != "ASK" or idx >= len(self.options):
            return
        right = self.options[idx] == self.correct_ans
        quick = (self.math_full - self.math_timer) < FPS * 5
        self.game.story_manager.note_answer(self.problem_str, right, quick)
        self._sw_shot(right)

    def _sw_shot(self, right):
        sw = self._sw
        if right:
            sw["phase"], sw["t"] = "HIT", 0
        else:
            standing = [m for m in sw["order"][sw["k"]:]]
            sw["attacker"] = random.choice(standing)
            sw["phase"], sw["t"] = "HURT", 0
            lead = sw["victim"] = self.lead()   # (the one hit: kept, so a faint mid-hit doesn't pass the hit on)
            sw["dmg"] = self._sw_damage(sw["attacker"].payload, lead)
            sw["hp_from"] = lead.current_hp

    @staticmethod
    def _sw_damage(foe, lead):
        """One plain hit (power 40), the games' way: ((2 x Lv / 5 + 2) x 40 x Atk / Def) / 50 + 2, a little random."""
        atk, dfn = max(1, foe.stat_value("ATTACK")), max(1, lead.stat_value("DEFENSE"))
        return max(1, int(((2 * foe.level / 5 + 2) * 40 * atk / dfn / 50 + 2) * random.uniform(0.85, 1.0)))

    def _sw_tick(self):
        sw = getattr(self, "_sw", None)
        if not sw:
            self.mode = "MAP"
            return
        if self.dialogue_box.visible:
            return
        sw["t"] += 1
        ph, t = sw["phase"], sw["t"]
        tgt = self._sw_target()
        if ph == "ASK":
            self.math_timer -= 1
            if self.math_timer <= 0:
                self.game.story_manager.note_answer(self.problem_str, False)
                self._sw_shot(False)
        elif ph == "HIT":
            tgt._wu_hp = max(0.0, 1.0 - t / ORB) if sw["k"] < 2 else max(0.15, 1.0 - t / ORB)
            if t >= ORB:
                if sw["k"] >= len(sw["order"]) - 1:   # (the last one: catch it, or knock it out)
                    sw["phase"], sw["t"], sw["pick"] = "PICK", 0, 0 if self._sw_can_catch() else 1
                else:
                    sw["phase"], sw["t"] = "FAINT", 0
                    if getattr(tgt.payload, "cry", None):
                        tgt.payload.cry.play()
        elif ph == "FAINT":
            tgt._wu_sink = int(28 * t / FAINT)
            tgt._wu_alpha = max(0, int(255 * (1 - t / FAINT)))
            if t >= FAINT:
                self._wu_drop(tgt)
                last = sw["k"] >= len(sw["order"]) - 1
                lines = [f"The wild {tgt.payload.display_name.upper()} fainted!"] + \
                    self._sw_exp(tgt.payload, 1.0 if last else 0.5)
                sw["k"] += 1
                sw["phase"] = "TALK"
                self.say(lines, then=self._sw_end if last else self._sw_ask)
        elif ph == "HURT":
            lead = sw["victim"]
            k = min(1.0, t / ORB)
            lead.current_hp = max(0, int(round(sw["hp_from"] - sw["dmg"] * k)))
            if t >= ORB:
                name = sw["attacker"].payload.display_name.upper()
                lines = [f"The wild {name} attacked! {lead.display_name.upper()} took {sw['dmg']} damage!"]
                sw["phase"] = "TALK"
                if lead.current_hp <= 0:
                    lines.append(f"{lead.display_name.upper()} fainted!")
                    team_left = any(p and p.current_hp > 0 for p in self.game.story_manager.player_team)
                    if not team_left:
                        self.say(lines + ["Your team is exhausted!", f"{self.game.player_name} whited out!"],
                                 then=self._sw_whiteout)
                        return
                    self.say(lines + ["The swarm ran off!"], then=self._sw_run_off)
                    return
                self.say(lines, then=self._sw_ask)
        elif ph == "THROW":
            if t >= THROW:
                self._sw_caught(tgt)

    def _sw_can_catch(self):
        return self._can_catch() and catching.total_balls(self.game.story_manager) > 0

    def _sw_pick(self, which):
        sw = getattr(self, "_sw", None)
        if not sw or sw["phase"] != "PICK":
            return
        tgt = self._sw_target()
        if which == 0:
            if not self._sw_can_catch():
                self.flash("You can't catch it: no Poke Balls!" if self.game.story_manager.catch_unlocked()
                           else "You can't catch Pokemon yet!")
                return
            story = self.game.story_manager
            ball = catching.selected(story)
            catching.use(story, ball)
            sw["ball"] = ball
            sw["phase"] = "TALK"
            lines = self._sw_exp(tgt.payload, 1.0)
            go = lambda: sw.update(phase="THROW", t=0)
            if lines:
                self.say(lines, then=go)
            else:
                go()
        else:
            sw["phase"], sw["t"] = "FAINT", 0
            if getattr(tgt.payload, "cry", None):
                tgt.payload.cry.play()

    def _sw_caught(self, tgt):
        """The ball lands: caught (the route's own catch: party or PC, Pokedex, streak, save)."""
        self._wu_hud(True)
        sw = self._sw
        self._sw = None
        self.encounter = tgt
        self.throw_result, self._thrown_ball, self.was_shiny_override = "caught", sw.get("ball"), False
        self._wu = None
        self._resolve_throw()

    def _sw_end(self):
        self._wu_hud(True)
        self._sw = None
        self._wu = None
        self.mode = "MAP"
        self.check_for_evolution()

    def _sw_run_off(self):
        self._wu_hud(True)
        sw = self._sw
        self._sw = None
        self.mode = "MAP"
        self._wu = {"movers": [m for m in sw["order"][sw["k"]:]], "water": self._wu_water()}
        self.walkup_leave()

    def _sw_whiteout(self):
        self._wu_hud(True)
        self._sw = None
        self._wu = None
        self.mode = "MAP"
        self.perform_black_out()

    def _sw_exp(self, foe, share):
        """Exp. for a swarm Pokemon knocked out or caught: the battle's own formula (src/states/battle.py
        _award_battle_xp) at share (half for the two extras); the rest of the team half again with EXP SHARE on."""
        from src.pokemon import affection, growth
        from src.pokemon import moves as movelib
        from src.pokemon.evolution import base_id
        from src.pokemon.items import gain_battle_evs, xp_held_mult
        from src.world import levels
        story = self.game.story_manager
        lead = self.lead()
        if lead is None or lead.current_hp <= 0:
            return []
        lead.counters["wins"] = lead.counters.get("wins", 0) + 1
        team = [p for p in story.player_team if p and p.current_hp > 0 and not getattr(p, "is_egg", False)]
        shares = [(lead, 1.0)] + ([(p, 0.5) for p in team if p is not lead] if getattr(story, "exp_share", True) else [])
        base_yield = self.game.assets.movesets.get(str(base_id(foe)), {}).get("base_xp") or 100
        cap = levels.xp_cap(story)
        lines = []
        for p, k in shares:
            gain_battle_evs(self.game, p, base_id(foe))
            gained = max(1, int(growth.battle_xp(base_yield, foe.level, p.level) * affection.xp_mult(p)
                                * xp_held_mult(p) * k * share))
            if p.level >= cap:
                if p is lead and p.level < 100:
                    lines.append(f"{p.display_name.upper()} can't grow past Lv {cap} until you beat the next Gym!")
                continue
            old = p.level
            grew = p.gain_xp(gained, cap)
            if p is lead:
                lines.append(f"{p.display_name.upper()} gained {gained} XP!")
            if grew:
                lines.append(f"{p.display_name.upper()} grew to Lv {p.level}!")
                lines.extend(movelib.learn_new_moves(self.game, p, old))
        if len(shares) > 1:
            lines.insert(1 if lines else 0, "The rest of your team gained XP too!")
        return lines

    # ---------------------------------------------------------------- the swarm's battle: keys, taps, drawing
    def _sw_answer_rects(self):
        W, H = self.game.width, self.game.height
        bw, gap = 190, 18
        x0 = W // 2 - 120
        return [pygame.Rect(x0 + i * (bw + gap), H - 150, bw, 96) for i in range(3)]

    def _sw_question_rect(self):
        W, H = self.game.width, self.game.height
        return pygame.Rect(W // 2 - 470, H - 150, 330, 96)

    def _sw_pick_rects(self):
        W, H = self.game.width, self.game.height
        return [pygame.Rect(W // 2 - 320, H - 160, 300, 110), pygame.Rect(W // 2 + 20, H - 160, 300, 110)]

    def _sw_event(self, e):
        sw = getattr(self, "_sw", None)
        if not sw:
            return
        if sw["phase"] == "ASK":
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                for i, r in enumerate(self._sw_answer_rects()):
                    if r.collidepoint(e.pos):
                        self._sw_answer(i)
                        return
            elif e.type == pygame.KEYDOWN:
                keys = {pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2, pygame.K_KP1: 0, pygame.K_KP2: 1, pygame.K_KP3: 2}
                if e.key in keys:
                    self._sw_answer(keys[e.key])
        elif sw["phase"] == "PICK":
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                for i, r in enumerate(self._sw_pick_rects()):
                    if r.collidepoint(e.pos):
                        self._sw_pick(i)
                        return
            elif e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d):
                    sw["pick"] = 1 - sw.get("pick", 0)
                elif e.key in (pygame.K_1, pygame.K_KP1):
                    self._sw_pick(0)
                elif e.key in (pygame.K_2, pygame.K_KP2):
                    self._sw_pick(1)
                elif e.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
                    self._sw_pick(sw.get("pick", 0))

    def _sw_bar(self, screen, r, k, label, mine=False):
        fonts = self.game.assets.fonts
        bar = pygame.Rect(0, 0, 70, 9)
        bar.midbottom = (r.centerx, r.top - 18)
        if mine:
            bar.midtop = (r.centerx, r.bottom + 8)
        pygame.draw.rect(screen, (20, 20, 30), bar.inflate(4, 4), border_radius=4)
        col = (90, 220, 110) if k > 0.5 else (240, 200, 60) if k > 0.2 else (230, 70, 60)
        pygame.draw.rect(screen, col, (bar.x, bar.y, int(bar.w * max(0.0, k)), bar.h), border_radius=3)
        if mine:
            pygame.draw.rect(screen, (120, 200, 255), bar.inflate(4, 4), 2, border_radius=4)
        tag = fonts["caption"].render(label, True, (255, 255, 255))
        box = tag.get_rect(midtop=(bar.centerx, bar.bottom + 2)) if mine else tag.get_rect(midbottom=(bar.centerx, bar.y - 2))
        shade = pygame.Surface(box.inflate(10, 4).size, pygame.SRCALPHA)
        shade.fill((10, 14, 24, 150))
        screen.blit(shade, box.inflate(10, 4))
        screen.blit(tag, box)

    def _sw_orb(self, screen, a, b, k, color):
        for j in range(4):
            kk = max(0.0, k - j * 0.06)
            pygame.draw.circle(screen, color, (int(a[0] + (b[0] - a[0]) * kk), int(a[1] + (b[1] - a[1]) * kk)), 10 - j * 2)
        if k > 0.75:
            pygame.draw.circle(screen, color, (int(b[0]), int(b[1])), int(10 + (k - 0.75) * 120), 3)

    def _draw_swarm(self, screen, at):
        """The swarm's battle, over the clear map: HP bars over them and your lead, the attacks, the question or the
        CATCH / FAINT choice along the bottom."""
        from src.states.overworld.overworld_battle import TYPE_COLOR
        sw = getattr(self, "_sw", None)
        if not sw:
            return
        fonts = self.game.assets.fonts
        W, H = self.game.width, self.game.height
        lead = sw.get("victim") if sw["phase"] == "HURT" else (self.lead() or (self.game.story_manager.player_team or [None])[0])
        me_tile = tuple(self.partner) if tuple(getattr(self, "partner", self.run.player)) != tuple(self.run.player) else tuple(self.run.player)
        mr = at(*me_tile)
        for m in sw["order"][sw["k"]:]:   # (just the level over each: they stand side by side, the species is in the heading)
            if m in self.run.floor.movers and getattr(m, "_wu_alpha", 255) > 0:
                r = at(m.x, m.y)
                self._sw_bar(screen, r, getattr(m, "_wu_hp", 1.0), f"Lv{m.payload.level}")
        if lead is not None:
            self._sw_bar(screen, mr, lead.current_hp / max(1, lead.get_max_hp()),
                         f"{lead.display_name.upper()} {max(0, lead.current_hp)}/{lead.get_max_hp()}", mine=True)
        tgt = self._sw_target()
        tr = at(tgt.x, tgt.y)
        if sw["phase"] == "HIT" and lead is not None:
            kind = str((getattr(lead, "types", None) or ["NORMAL"])[0]).upper()
            self._sw_orb(screen, mr.center, tr.center, min(1.0, sw["t"] / ORB), TYPE_COLOR.get(kind, (255, 255, 255)))
        elif sw["phase"] == "HURT":
            foe = sw["attacker"]
            kind = str((getattr(foe.payload, "types", None) or ["NORMAL"])[0]).upper()
            self._sw_orb(screen, at(foe.x, foe.y).center, mr.center, min(1.0, sw["t"] / ORB), TYPE_COLOR.get(kind, (255, 255, 255)))
            k = min(1.0, sw["t"] / ORB)
            if k > 0.5:
                theme.shadow_text(screen, f"-{sw['dmg']}", fonts["label"], mr.right + 30, mr.top - int(k * 30),
                                  color=(255, 140, 130), shadow=(20, 20, 30), align="center")
        elif sw["phase"] == "THROW":
            k = min(1.0, sw["t"] / THROW)
            a, b = at(*self.run.player).center, tr.center
            x = a[0] + (b[0] - a[0]) * min(1.0, k * 1.6)
            y = a[1] + (b[1] - a[1]) * min(1.0, k * 1.6) - math.sin(math.pi * min(1.0, k * 1.6)) * 60
            if k > 0.62:   # (in the ball, shaking: the Pokemon is in it)
                x += math.sin(k * 40) * 5
                tgt._wu_alpha = 0
            ball = self._ball_img(30)
            screen.blit(ball, ball.get_rect(center=(int(x), int(y))))
        left = len(sw["order"]) - sw["k"]
        kind = sw["order"][-1].payload.display_name.upper()
        head = f"{kind} SWARM!  {left} left" if sw["phase"] != "PICK" else "The last one is worn out!"
        tag = fonts["label"].render(head, True, (255, 255, 255))
        hr = tag.get_rect(midtop=(self._view().centerx, 70)).inflate(24, 10)
        pygame.draw.rect(screen, (30, 36, 58), hr, border_radius=10)
        pygame.draw.rect(screen, theme.FIGHT, hr, 2, border_radius=10)
        screen.blit(tag, tag.get_rect(center=hr.center))
        if self.dialogue_box.visible:
            return
        mouse = pygame.mouse.get_pos()
        if sw["phase"] == "ASK":
            q = self._sw_question_rect()
            theme.draw_textbox(screen, q)
            theme.math_text(screen, self.problem_str, fonts["big"], q.centerx, q.centery)
            for i, r in enumerate(self._sw_answer_rects()):
                theme.card(screen, r, hover=r.collidepoint(mouse), accent=theme.FIGHT)
                theme.answer_text(screen, self.options[i], fonts["num"], r.centerx, r.centery)
            k = max(0.0, self.math_timer / max(1, self.math_full))
            track = pygame.Rect(q.x, q.bottom + 10, self._sw_answer_rects()[-1].right - q.x, 10)
            pygame.draw.rect(screen, (60, 64, 80), track, border_radius=5)
            pygame.draw.rect(screen, theme.POKEMON if k > 0.33 else theme.FIGHT,
                             (track.x, track.y, max(6, int(track.w * k)), track.h), border_radius=5)
        elif sw["phase"] == "PICK":
            can = self._sw_can_catch()
            ball = catching.label(catching.selected(self.game.story_manager)).title()
            labels = [("CATCH", f"Sure catch: 1 {ball}" if can else "No balls / no Pokedex", theme.RUN if can else theme.BACK),
                      ("FAINT", "Knock it out for Exp.", theme.FIGHT)]
            for i, (r, (label, small, color)) in enumerate(zip(self._sw_pick_rects(), labels)):
                theme.command_button(screen, r, label, fonts["button"], color,
                                     hover=r.collidepoint(mouse) or sw.get("pick") == i, small=fonts["caption"], sub=small)
