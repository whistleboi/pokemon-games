
# The music library (Jordan, 11-15): tracks by generation, then A-Z, wherever music is picked
# (the Options jukebox). A made-up library first (so it runs without the 1 GB build), then the real one.
import json, shutil, tempfile
from src.core import music_library as lib
from src.states.systems.options import OptionsState

fails = 0


def check(ok, what):
    global fails
    if not ok:
        fails += 1
    print(("ok   " if ok else "FAIL ") + what)


print("1) the order: generation, then name")
fake = tempfile.mkdtemp()
tracks = [("gen3/orre/b.ogg", "Battle! (Elite Four)", 3, "bgm"), ("gen1/journeys/p.mp3", "Pallet Town", 1, "bgm"),
          ("gen0/journeys/t.mid", "Triple Triad", 0, "bgm"), ("gen1/journeys/a.mp3", "a Route", 1, "bgm"),
          ("gen1/journeys/h.mp3", "The Hall of Fame", 1, "bgm"), ("gen9/x/s.ogg", "Sound", 9, "sound"),
          ("gen2/x/missing.ogg", "Not built", 2, "bgm"), ("gen10/x/z.ogg", "Zed", 10, "me")]
os.makedirs(os.path.join(fake, "music", "library"))
for f, *_ in tracks:
    if "missing" not in f:
        os.makedirs(os.path.join(fake, "music", "library", os.path.dirname(f)), exist_ok=True)
        open(os.path.join(fake, "music", "library", f), "wb").close()
with open(os.path.join(fake, lib.MANIFEST), "w") as fh:
    json.dump({"sources": {"orre": {"title": "Pokemon Orre 2.1.1"}},
               "tracks": [{"file": f, "name": n, "gen": gen, "kind": k, "source": f.split("/")[1]} for f, n, gen, k in tracks]}, fh)
got = [t["name"] for t in lib.ordered(fake)]
check(got == ["a Route", "The Hall of Fame", "Pallet Town", "Battle! (Elite Four)", "Triple Triad"],
      f"Gen 1 A-Z (case and 'The' ignored), Gen 3, Other last; fanfares, sounds and unbuilt files left out: {got}")
check([t["name"] for t in lib.ordered(fake, kinds=("bgm", "me"))][-2:] == ["Zed", "Triple Triad"], "Gen 10 sorts before Other")
check(lib.generations(lib.ordered(fake)) == [1, 3, 0], "generations cycle Gen 1 up, Other last")
check([t["name"] for t in lib.ordered(fake, gen=1)] == ["a Route", "The Hall of Fame", "Pallet Town"], "one generation's tracks")
check(lib.ordered(os.path.join(fake, "nowhere")) == [], "no library: no tracks (and no crash)")

print("2) the Options jukebox")
real_dir = g.assets.assets_dir
g.assets.assets_dir = fake
played = []
g.music.listen = lambda path: played.append(path)
op = OptionsState(g, g.current_state, lambda: None)
op.tab = op.tabs.index("SOUND")
names = [r[0] for r in op.rows()]
check(names[-2:] == ["Jukebox generation", "Jukebox"], f"SOUND has the jukebox rows: {names}")
jb = op.rows()[-1]
check([l for _v, l in jb[1]] == ["Off", "a Route", "The Hall of Fame", "Pallet Town", "Battle! (Elite Four)", "Triple Triad"],
      "the jukebox steps through every generation's songs in order (no fanfares or sounds)")
op._step(jb, 1)
check(played and played[-1].endswith("a.mp3") and op.jb_track == played[-1], "a step plays the first track")
op._step(op.rows()[-1], -1)
check(played[-1] is None, "back to Off stops it")
op._step(op.rows()[-1], -1)
check(played[-1].endswith("t.mid"), "stepping back from Off wraps to the last track (Other)")
op._step(op.rows()[-2], 1)   # generation: Gen 1
check(op.jb_gen == 1 and [l for _v, l in op.rows()[-1][1]][1:] == ["a Route", "The Hall of Fame", "Pallet Town"],
      "a generation keeps its tracks A-Z")
check(played[-1] is None, "changing generation stops a track from another one")
op._step(op.rows()[-1], 1)
check("Gen 1" in op.rows()[-1][4], f"the bar says the track's generation and source: {op.rows()[-1][4]}")
op.draw()
op.close()
check(played[-1] is None, "leaving Options brings the usual music back")
del g.music.listen
g.assets.assets_dir = os.path.join(os.path.dirname(fake), "nowhere")
op2 = OptionsState(g, g.current_state, lambda: None)
op2.tab = op2.tabs.index("SOUND")
check([r[0] for r in op2.rows()] == ["Music volume", "Sound effects"], "no library: SOUND is as it was")
g.assets.assets_dir = real_dir
shutil.rmtree(fake, ignore_errors=True)

print("3) listen() and the music manager")
if pygame.mixer.get_init():
    m = g.music
    m.kind, m.path = "town", None
    calls = []
    real_play = m.play
    m.play = lambda kind, force=False: calls.append((kind, force))
    some = lib.ordered(real_dir)
    if some:
        m.listen(some[0]["path"])
        check(m.listening and m.path == some[0]["path"], "the jukebox track plays")
    else:
        m.listening = True
    m.listen(None)
    check(not m.listening and calls == [("town", True)], f"Off: the music for the screen comes back {calls}")
    m.play = real_play
else:
    print("(no mixer here: skipped)")

print("4) the real library")
man = lib.manifest(real_dir)
real = lib.ordered(real_dir)
if not man.get("tracks"):
    print("(not built on this PC: python -I dev/builders/build_music_library.py)")
else:
    check(len(real) == len([t for t in man["tracks"] if t["kind"] in lib.MUSIC_KINDS]), f"every listed track is built ({len(real)})")
    check(real == sorted(real, key=lib.sort_key), "the library comes in order")
    # (game files name their own fanfares; a fan game's file under 20 seconds counts as one)
    short = [t["name"] for t in real if t.get("seconds", 999) < 20
             and man["sources"].get(t["source"], {}).get("kind") == "fan game"]
    check(not short and all(t["kind"] == "bgm" for t in real), f"the jukebox has songs only, no fanfares: {short[:5]}")
    fan = [t["name"] for t in real if any(w in t["name"] for w in ("Level Up", "Badge Get", "Item Get", "Healed"))]
    check(not fan, f"no well-known fanfare is in the jukebox: {fan[:5]}")
    check(all(t.get("gen") in range(0, 10) and t.get("source") in man["sources"] for t in man["tracks"]),
          "every track has a generation and a credited source")
    shas = [t["sha1"] for t in man["tracks"] + man.get("sounds", [])]
    check(len(shas) == len(set(shas)), "no file is in twice")
    gens = lib.generations(real)
    check(gens[0] == 1 and gens[-1] == 0, f"generations: {gens}")
    for t in real[:3] + real[-3:]:
        try:
            pygame.mixer.music.load(t["path"]) if pygame.mixer.get_init() else None
        except pygame.error as e:
            check(False, f"{t['file']} plays: {e}")

print(f"##### {fails} fails")
