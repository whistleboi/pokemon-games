# A person's scene with its own words and then a story event that has words too (src/dungeon/npc.py Scenes): the event
# starts on the next frame, not from inside the closing of the scene's words, so its own words close and the scene ends
# (Sinnoh 11-25: Rowan's TM27 locked you in place; any region's scene could).
#   bash dev/checks/run.sh scene_event
from src.dungeon import npc as _npc

fails = 0


def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m)
    fails += 0 if c else 1


class Host:
    """A stand-in map: one message box at a time, as the game's (a new message opened while one closes is lost)."""
    def __init__(self):
        self.box, self.closing, self.lost, self.locked, self.events = None, False, 0, False, []

    def npc_say(self, lines, cb):
        if self.closing:   # (opened inside the closing of the last one: the game drops its callback)
            self.lost += 1
            return
        self.box = (list(lines), cb)

    def close(self):
        if self.box:
            _, cb = self.box
            self.box, self.closing = None, True
            try:
                cb() if cb else None
            finally:
                self.closing = False

    def npc_event(self, key, done):
        self.events.append(key)
        self.npc_say(["You got a TM!"], done)   # (an event with words of its own: a gift)

    def npc_lock(self, on): self.locked = on
    def npc_player(self): return (5, 5)
    def npc_face_player(self, pos): pass
    def npc_passable(self, t, m): return True
    def npc_flag(self, f): pass
    def npc_flagged(self, f): return False
    def npc_shown(self, s): return True
    def npc_open(self, t): return True
    def npc_person(self, who): return self.m


h = Host()
h.m = _npc.Motion((5, 4), {"m": "still"})
scene = {"who": "rowan", "trigger": "talk", "lines": ["Take this."], "then": "event:give_tm27", "after": "stay"}
sc = _npc.Scenes([scene], h)
check(sc.on_talk("rowan"), "talking to him starts his scene")
for _ in range(60):
    if not sc.busy():
        break
    sc.tick()
    h.close()
check(h.events == ["give_tm27"] and h.lost == 0, f"the gift's own words open after his, none lost ({h.events}, lost {h.lost})")
check(not sc.busy() and not h.locked, "the scene ends and you can move again")
print(f"##### {fails} failures")
