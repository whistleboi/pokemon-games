# The playthroughs keep one engine (Checks C6, 11-24): kanto_playthrough_body.py is the engine; each region's
# kanto_handoff/<region>/make_*playthrough.py writes its own <region>_playthrough_body.py from it. This suite runs every
# generator into a scratch folder and compares what it writes with the committed body, so a hand edit to a generated
# body (lost the next time the generator runs) or a body not written again after the engine changed shows up.
#   bash dev/checks/run.sh playthrough_sync
# A FAIL: either put the hand edit into the region's generator and run it, or just run the generator (the engine changed).
import difflib, shutil, subprocess, tempfile

fails = []


def check(c, m):
    print(("   ok  " if c else "   FAIL ") + m)
    if not c:
        fails.append(m)


def _handoff():
    d = os.path.abspath(os.getcwd())
    for _ in range(8):
        if os.path.isdir(os.path.join(d, "kanto_handoff")):
            return os.path.join(d, "kanto_handoff")
        d = os.path.dirname(d)
    return None


GEN = {   # region: its generator (in kanto_handoff)
    "johto": "johto_check/make_jplaythrough.py",
    "orange": "orange_rom_tools/make_oplaythrough.py",
    "orre": "orre_check/make_rplaythrough.py",
    "hoenn": "hoenn_check/make_hplaythrough.py",
    "sinnoh": "sinnoh_check/make_splaythrough.py",
    "unova": "unova_check/make_uplaythrough.py",
}
H = _handoff()
check(H is not None, "kanto_handoff found beside the game folder (the generators live there)")
if H:
    tmp = tempfile.mkdtemp(prefix="pt_sync_")
    os.makedirs(os.path.join(tmp, "dev", "checks"))
    shutil.copy("dev/checks/kanto_playthrough_body.py", os.path.join(tmp, "dev", "checks"))
    for region, gen in GEN.items():
        path = os.path.join(H, gen)
        if not os.path.exists(path):
            check(False, f"{region}: its generator {gen} is there")
            continue
        r = subprocess.run([sys.executable, "-I", path, tmp], env=dict(os.environ, GAME=tmp, KANTO_REPO=tmp),
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
        made = os.path.join(tmp, "dev", "checks", f"{region}_playthrough_body.py")
        if r.returncode != 0 or not os.path.exists(made):
            check(False, f"{region}: {gen} runs ({(r.stderr or r.stdout).strip().splitlines()[-1:]})")
            continue
        want = open(made, encoding="utf-8").read().replace("\r\n", "\n").splitlines()
        have = open(f"dev/checks/{region}_playthrough_body.py", encoding="utf-8").read().replace("\r\n", "\n").splitlines()
        diff = [l for l in difflib.unified_diff(have, want, "committed", "generated", n=0, lineterm="")
                if l[:1] in "+-" and not l.startswith(("+++", "---"))]
        only_here = sum(1 for l in diff if l.startswith("-"))
        only_gen = sum(1 for l in diff if l.startswith("+"))
        check(not diff, f"{region}_playthrough_body.py is what {gen} writes" + (
            "" if not diff else f" ({only_here} lines only in the committed body - hand edits the generator would drop; "
                                f"{only_gen} only in the generator's - engine changes not written in yet; first: "
                                f"{diff[0][:110]!r})"))
    shutil.rmtree(tmp, ignore_errors=True)

print(f"##### {len(fails)} failures")
