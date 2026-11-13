"""People who move on the maps (Jordan, 11-12: "walking animations and story event triggers for NPCs; they should react in
the overworld if the story says"). Used by the town maps (walk_town.py) and the route and cave maps (dungeon.py).

How someone moves: a map's "moves" {"x,y" of their spot (an N or X tile): spec}. spec is a dict:
    "m":  "still"   stands as placed (the default: anyone not listed)
          "face"    stands looking one way ("d": that way)
          "look"    turns now and then to one of "d" (letters u d l r)
          "wander"  takes a step now and then, in "d", no further than "r" [x, y] tiles from their spot
          "march"   walks on the spot, looking "d" (a jogger, a guard pacing)
          "copy"    copies your steps: each step you take, they take one ("v": "same", "opposite", "ccw" turned left,
                    "cw" turned right; "g": only onto tall grass): Route 119's Mimic Circle, Emerald's copy-the-player
    "s":  how far a trainer sees (tiles), else the game's usual
The Hoenn maps take these from Emerald's own people (kanto_handoff/hoenn_rom_tools/hgen.py, MOVES).

Story scenes: a map's "scenes" [scene, ...]. A scene plays once its conditions are met (the same keys as an option's:
"condition", "flag_condition", ...) and its "flag" is not yet set (it is set when the scene ends):
    "who":      the person it is about: an option's text (a town's person, a route's figure), or "trainer:<name>"
    "trigger":  "enter" (as you arrive), {"zone": [x0, y0, x1, y1]} (you step into that box), or "sight" (you walk into
                their line of sight, as a trainer sees you)
    "approach": true: they walk up to you (else they turn to you where they stand)
    "lines":    what they say when they reach you
    "then":     "talk" (their own option runs, as if you had walked up and talked to them: a battle, a gift), or nothing
    "after":    "home" (they walk back to their spot), "stay" (where they stopped), or "leave" (they walk off the
                nearest edge of the map and are gone for this visit)
    "push":     [dx, dy]: you take a step that way afterwards (someone who stops you going on)
    "every":    true: it plays every time it triggers (someone who keeps stopping you), and "flag" is not set
    "lead":     [[x, y, [lines]], ...]: they show you round: they walk to each spot in turn with you following one step
                behind, and say that spot's lines there (Oldale's Mart clerk). Usually with "trigger": "talk" (it plays
                when you talk to them, instead of their option; "then": "talk" runs the option at the end)
Hosts also give: host.npc_follow(tile) (you step onto that tile, the one they just left)"""
import random
from collections import deque

DIRS = {"u": (0, -1), "d": (0, 1), "l": (-1, 0), "r": (1, 0)}
STEP = 9          # frames a person's step takes (a little slower than yours)


class Motion:
    """One person: where they stand (pos: the tile they are on, or stepping onto), the tile they came from, which way
    they look, how far through a step they are (t, 1 = standing), and what they do when left alone."""

    def __init__(self, home, spec=None, seed=0, facing=(0, 1)):
        spec = spec or {}
        self.home = tuple(home)
        self.pos = self.frm = tuple(home)
        self.kind = spec.get("m", "still")
        self.dirs = [DIRS[c] for c in (spec.get("d") or "udlr") if c in DIRS] or [(0, 1)]
        self.range = tuple(spec.get("r") or (1, 1))
        self.sight = spec.get("s")
        self.copy_way = spec.get("v", "same")   # (a "copy" person: how they turn your step)
        self.grass = bool(spec.get("g"))
        self.facing = self.dirs[0] if self.kind in ("face", "march") else (DIRS.get(spec.get("f", ""), facing))
        self.t = 1.0
        self.steps = 0
        self.path = []
        self.wait = 0           # frames stuck behind someone on a path
        self.hold = 0           # frames they stay put (just talked to you)
        self.rng = random.Random(f"{seed}:{home}")
        self.timer = self.rng.randint(40, 200)
        self.emote = 0          # frames a "!" shows over their head
        self.gone = False       # walked off the map (a scene's "leave")

    # ------------------------------------------------------------ what is drawn
    def moving(self):
        return self.t < 1.0

    def at(self):
        """Where they are drawn, in tiles (mid-step: between the two)."""
        k = self.t
        return (self.frm[0] + (self.pos[0] - self.frm[0]) * k, self.frm[1] + (self.pos[1] - self.frm[1]) * k)

    def frame(self):
        """The sheet column: standing (0), or the step (1 and 3 by turns)."""
        if self.kind == "march" and not self.path:
            return (1, 0, 3, 0)[(self.timer // 8) % 4]
        if not self.moving():
            return 0
        return 1 if self.steps % 2 else 3

    # ------------------------------------------------------------ moving
    def step_to(self, t):
        self.facing = (max(-1, min(1, t[0] - self.pos[0])), max(-1, min(1, t[1] - self.pos[1])))
        self.frm, self.pos, self.t = self.pos, tuple(t), 0.0
        self.steps += 1

    def face(self, t):
        dx, dy = t[0] - self.pos[0], t[1] - self.pos[1]
        if dx or dy:
            self.facing = ((1 if dx > 0 else -1), 0) if abs(dx) > abs(dy) else (0, (1 if dy > 0 else -1))

    def tick(self, free):
        """One frame. free(tile): can they step there now. Returns True when they turned to look a new way (a trainer
        who turns may see you)."""
        if self.gone:
            return False
        if self.emote > 0:
            self.emote -= 1
        if self.moving():
            self.t = min(1.0, self.t + 1.0 / STEP)
            return False
        if self.path:
            nxt = self.path[0]
            if free(nxt):
                self.path.pop(0)
                self.wait = 0
                self.step_to(nxt)
            else:
                self.wait += 1
                if self.wait > 90:   # (someone's in the way for good: give up)
                    self.path, self.wait = [], 0
            return False
        if self.hold > 0:
            self.hold -= 1
            return False
        self.timer -= 1
        if self.kind == "march":
            return False
        if self.timer > 0:
            return False
        self.timer = self.rng.randint(60, 220)
        if self.kind == "look":
            new = self.rng.choice(self.dirs)
            turned = new != self.facing
            self.facing = new
            return turned
        if self.kind == "wander":
            d = self.rng.choice(self.dirs)
            self.facing = d
            t = (self.pos[0] + d[0], self.pos[1] + d[1])
            if abs(t[0] - self.home[0]) <= self.range[0] and abs(t[1] - self.home[1]) <= self.range[1] and free(t):
                self.step_to(t)
            return True
        return False

    def copy(self, dx, dy, free):
        """You stepped (dx, dy): a "copy" person takes their own step, turned their way, if free(tile) lets them.
        They turn to it even when they can't go."""
        d = {"same": (dx, dy), "opposite": (-dx, -dy), "ccw": (dy, -dx), "cw": (-dy, dx)}.get(self.copy_way, (dx, dy))
        if not (d[0] or d[1]) or self.moving() or self.path:
            return False
        self.facing = d
        t = (self.pos[0] + d[0], self.pos[1] + d[1])
        if free(t):
            self.step_to(t)
        return True

    def walk(self, goal, passable, beside=True, limit=4000):
        """Set off for goal (beside it, if beside) by the shortest way over passable tiles. False if there is none."""
        goal = tuple(goal)
        if beside and abs(goal[0] - self.pos[0]) + abs(goal[1] - self.pos[1]) == 1:
            self.path = []
            return True
        prev, todo = {self.pos: None}, deque([self.pos])
        end = None
        best, best_d = self.pos, abs(goal[0] - self.pos[0]) + abs(goal[1] - self.pos[1])
        while todo and len(prev) < limit:
            cur = todo.popleft()
            d = abs(goal[0] - cur[0]) + abs(goal[1] - cur[1])
            if d < best_d:
                best, best_d = cur, d
            if (beside and abs(cur[0] - goal[0]) + abs(cur[1] - goal[1]) == 1) or (not beside and cur == goal):
                end = cur
                break
            for d in DIRS.values():
                n = (cur[0] + d[0], cur[1] + d[1])
                if n not in prev and n != goal and passable(n):
                    prev[n] = cur
                    todo.append(n)
                elif n not in prev and n == goal and not beside:
                    prev[n] = cur
                    todo.append(n)
        if end is None:   # (no way all the way there: as near as they can get)
            if best == self.pos:
                return False
            end = best
        out = []
        while end != self.pos:
            out.append(end)
            end = prev[end]
        self.path = out[::-1]
        return True

    def idle(self):
        return not self.moving() and not self.path


def sees(motion, target, open_tile, reach=4):
    """Does motion look straight at target within reach tiles, over open ground (the way a trainer spots you)?"""
    if not motion.idle():
        return False
    dx, dy = motion.facing
    x, y = motion.pos
    for _ in range(reach):
        x, y = x + dx, y + dy
        if (x, y) == tuple(target):
            return True
        if not open_tile((x, y)):
            return False
    return False


def spec_at(moves, spot):
    return (moves or {}).get("%d,%d" % tuple(spot))


class Scenes:
    """A map's story scenes, run against a host (the town map or the route map). The host gives:
        host.npc_person(who)         -> Motion or None (the person the scene is about, if standing here now)
        host.npc_player()            -> your tile
        host.npc_passable(tile, m)   -> may m walk there (open ground, nobody there)
        host.npc_shown(scene)        -> its conditions met
        host.npc_flag(name)          -> set a story flag
        host.npc_flagged(name)       -> is it set
        host.npc_say(lines, then)    -> show lines, then call then()
        host.npc_run(who)            -> run that person's own option (as if talked to)
        host.npc_event(key, then)    -> play a story event (story_events.py) by its key, then call then()
        host.npc_heal()              -> heal your team
        host.npc_sheet(token)        -> a walking sheet's file: "em_100.png", or "@rival" (this save's rival),
                                        "@grunt" / "@grunt_f" (this version's villain team)
        host.npc_push(dx, dy)        -> you take a step
        host.npc_follow(tile)        -> you step onto that tile (following someone)
        host.npc_lock(on)            -> stop / let you walk
        host.npc_open(tile)          -> can you see across that tile (for "sight")
        host.npc_edge(m)             -> the nearest tile at the map's edge they can walk off by, or None
        host.npc_face_player(tile)   -> you turn to face that tile
    and draws self.actors (each {"m": Motion, "sheet": file}): the scene's cast while on the map.

    A scene with a "cast" needs no "who": [{"sheet": token, "from": [x, y] (where they appear: a door, the map's edge),
    "to": "player" (beside you) or [x, y], "lines": [...], "then": "event:<key>" (a story event: a gift, a battle),
    "heal": true, "leave": [x, y] or "back" (where they walk off to and are gone; else they vanish where they stand),
    "concurrent": true (sets off together with the one before: a chase)}]. Each walks in, turns to you, speaks,
    and walks off, in turn. Then the scene's own "then": "event:<key>" plays, if any.
    For a "who" scene: "then": "talk" (their own option) or "event:<key>"; "after_lines" said once that is over (after
    a battle: the rival's last words); "heal": true heals your team there; "instead_of": the key of the town's own
    arrival event this scene plays in place of (towns)."""

    def __init__(self, scenes, host):
        self.list = [s for s in (scenes or []) if isinstance(s, dict)]
        self.host = host
        self.playing = None     # [scene, stage, motion, state]
        self.done_here = set()  # (played on this visit: an "every" scene waits till you leave its zone)
        self.entered = False
        self.actors = []        # the cast on the map now: {"m": Motion, "sheet": file}

    def busy(self):
        return self.playing is not None

    def pending(self, s):
        h = self.host
        return not (s.get("flag") and h.npc_flagged(s["flag"]) and not s.get("every")) and h.npc_shown(s)

    def on_talk(self, who):
        """You talk to someone: a "talk" scene of theirs plays instead, if its time has come. True if one started."""
        if self.playing:
            return False   # (a scene already playing: its own "then": "talk" is this)
        h = self.host
        for s in self.list:
            if s.get("trigger") != "talk" or s.get("who") != who or not self.pending(s):
                continue
            m = h.npc_person(who)
            if m is not None and not m.gone:
                self.start(s, m)
                return True
        return False

    def check(self):
        """Call when you stand still on the map with nothing else going on: starts a scene whose time has come."""
        if self.playing:
            return
        h = self.host
        me = h.npc_player()
        for i, s in enumerate(self.list):
            if not self.pending(s):
                continue
            m = h.npc_person(s.get("who")) if s.get("who") else None
            if s.get("who") and (m is None or m.gone):
                continue
            trig = s.get("trigger", "enter")
            hit = False
            if trig == "talk":
                continue
            if trig == "enter":
                hit = not self.entered and i not in self.done_here
            elif trig == "sight":
                hit = m is not None and sees(m, me, h.npc_open, reach=int(s.get("reach") or m.sight or 4))
            elif isinstance(trig, dict) and trig.get("zone"):
                x0, y0, x1, y1 = trig["zone"]
                inside = x0 <= me[0] <= x1 and y0 <= me[1] <= y1
                if not inside:
                    self.done_here.discard(i)
                hit = inside and i not in self.done_here
            if hit:
                self.done_here.add(i)
                self.start(s, m)
                break
        self.entered = True

    def start(self, s, m):
        h = self.host
        h.npc_lock(True)
        st = {"i": 0, "going": False, "steps": 0, "ci": 0, "phase": "spawn", "spawned": set(), "by": {}}
        if m is not None:
            m.path = []
            m.face(h.npc_player())
            m.emote = 0 if s.get("trigger") == "talk" else 40
            st["steps"] = m.steps
        self.playing = [s, "cast" if s.get("cast") else "notice", m, st]

    # ------------------------------------------------------------ the cast
    def _spawn(self, spec, seed):
        m = Motion(tuple(spec["from"]), {"m": "still"}, seed=seed)
        a = {"m": m, "sheet": self.host.npc_sheet(spec.get("sheet", "")), "spec": spec, "goal": None}
        self.actors.append(a)
        return a

    def _cast_tick(self, s, st):
        """One frame of the cast. True when the last of them has gone."""
        h = self.host
        me = h.npc_player()
        cast = s["cast"]
        for a in list(self.actors):   # (everyone on the move keeps moving)
            a["m"].tick(lambda t, a=a: h.npc_passable(t, a["m"]) or t == a["goal"])
        if st["ci"] >= len(cast):
            return True
        spec = cast[st["ci"]]
        ph = st["phase"]
        if ph == "spawn":
            group = [st["ci"]] + [j for j in range(st["ci"] + 1, len(cast)) if all(cast[k].get("concurrent") for k in range(st["ci"] + 1, j + 1))]
            for j in group:
                if j in st["spawned"]:
                    continue
                st["spawned"].add(j)
                a = self._spawn(cast[j], f"cast{j}")
                st["by"][j] = a
                to = cast[j].get("to", "player")
                a["goal"] = tuple(me) if to == "player" else tuple(to)
                a["m"].walk(a["goal"], lambda t, a=a: h.npc_passable(t, a["m"]) or t == a["goal"], beside=(to == "player"))
                if to == "player":
                    a["goal"] = None
            st["phase"] = "in"
            return False
        a = st["by"][st["ci"]]
        m = a["m"]
        if ph == "in":
            if not m.idle():
                return False
            if spec.get("to", "player") == "player" or spec.get("lines"):
                m.face(me)
                h.npc_face_player(m.pos)
            st["phase"] = "talk"

            def said():
                if spec.get("heal"):
                    h.npc_heal()
                ev = spec.get("event") if isinstance(spec.get("event"), dict) else str(spec.get("then") or "")
                if isinstance(ev, dict) or ev.startswith("event:"):   # (a story event: a key, or one written out: a gift)
                    st["phase"], st["ev"] = "event", ev   # (on the next frame: not from inside the closing of the lines just said)
                else:
                    st["phase"] = "out"
            if spec.get("lines"):
                h.npc_say(list(spec["lines"]), said)
            else:
                said()
            return False
        if ph == "event":
            ev = st.pop("ev")
            st["phase"] = "wait"
            h.npc_event(ev if isinstance(ev, dict) else ev[6:], lambda: st.__setitem__("phase", "out"))
            return False
        if ph in ("talk", "wait"):
            return False
        if ph == "out":
            leave = spec.get("leave")
            if leave:
                goal = tuple(spec["from"]) if leave == "back" else tuple(leave)
                a["goal"] = goal
                m.walk(goal, lambda t: h.npc_passable(t, m) or t == goal, beside=False)
            st["phase"] = "leaving"
            return False
        if ph == "leaving":
            if not m.idle():
                return False
            if a in self.actors:
                self.actors.remove(a)
            st["ci"] += 1
            st["phase"] = "spawn" if st["ci"] < len(cast) and st["ci"] not in st["spawned"] else "in"
            return st["ci"] >= len(cast)
        return False

    # ------------------------------------------------------------ one frame
    def _resume(self, stage):
        if self.playing:
            self.playing[1] = stage

    def tick(self):
        """Each frame while a scene plays."""
        if not self.playing:
            return
        s, stage, m, st = self.playing
        h = self.host
        me = h.npc_player()
        if stage == "cast":
            if self._cast_tick(s, st):
                ev = str(s.get("then") or "")
                if ev.startswith("event:"):
                    self.playing[1] = "pause"
                    h.npc_event(ev[6:], lambda: self._resume("after"))
                else:
                    self.playing[1] = "after"
            return
        if stage == "notice":
            if m.emote > 0:
                return
            if s.get("lead"):
                self.playing[1] = "lead"
                return
            if s.get("approach"):
                m.walk(me, lambda t: h.npc_passable(t, m))
            self.playing[1] = "walk"
        elif stage == "lead":  # (showing you round: you follow a step behind)
            if m.steps != st["steps"]:
                st["steps"] = m.steps
                h.npc_follow(m.frm)
            if not m.idle():
                return
            stops = s["lead"]
            if st["i"] >= len(stops):
                self.playing[1] = "walk"
                return
            x, y, lines = stops[st["i"]]
            if not st["going"] and m.pos != (x, y):
                st["going"] = True
                if not m.walk((x, y), lambda t: h.npc_passable(t, m), beside=False):
                    st["going"], st["i"] = False, st["i"] + 1
                return
            st["going"] = False
            st["i"] += 1
            m.face(me)
            if lines:
                self.playing[1] = "pause"
                h.npc_say(list(lines), lambda: self._resume("lead"))
        elif stage == "pause":
            return
        elif stage == "walk":
            if not m.idle():
                return
            m.face(me)
            h.npc_face_player(m.pos)
            self.playing[1] = "talk"

            def then():
                self.playing[1] = "after"
                ev = s.get("event") if isinstance(s.get("event"), dict) else str(s.get("then") or "")
                if ev == "talk":
                    h.npc_run(s.get("who"))
                elif isinstance(ev, dict) or ev.startswith("event:"):   # (a story event: a key, or written out: a battle, a gift)
                    self.playing[1] = "pause"
                    h.npc_event(ev if isinstance(ev, dict) else ev[6:], lambda: self._resume("after"))
            if s.get("lines"):
                h.npc_say(list(s["lines"]), then)
            else:
                then()
        elif stage == "after":
            if (s.get("after_lines") or s.get("heal")) and not st.get("said_after"):
                st["said_after"] = True
                if m is not None:
                    m.face(me)
                if s.get("heal"):
                    h.npc_heal()
                if s.get("after_lines"):
                    self.playing[1] = "pause"
                    h.npc_say(list(s["after_lines"]), lambda: self._resume("after"))
                    return
            if s.get("push"):
                h.npc_push(*s["push"])
            after = s.get("after", "home") if m is not None else "stay"
            if after == "home":
                m.walk(m.home, lambda t: h.npc_passable(t, m), beside=False)
            elif after == "leave":
                edge = h.npc_edge(m)
                if edge:
                    m.walk(edge, lambda t: h.npc_passable(t, m) or t == edge, beside=False)
                self.playing[1] = "leaving"
                if s.get("flag") and not s.get("every"):
                    h.npc_flag(s["flag"])
                return
            if s.get("flag") and not s.get("every"):
                h.npc_flag(s["flag"])
            h.npc_lock(False)
            self.playing = None
        elif stage == "leaving":
            if m.idle():
                m.gone = True
                h.npc_lock(False)
                self.playing = None
