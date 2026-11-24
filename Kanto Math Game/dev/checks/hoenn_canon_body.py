# Hoenn's content against its source games (11-23, ROADMAP_HOENN H3; AUDIT_GUIDE section 4): the story, teams and levels
# follow Omega Ruby / Alpha Sapphire, the maps come from Emerald. Every ORAS trainer with ORAS's team and levels (Emerald's
# where ORAS has none for a place), ORAS's double battles as doubles, item balls, hidden items, Berries in soft soil, gifts,
# ORAS's wild tables of both versions (grass, hordes, DexNav, Surf, the three rods, Rock Smash, seaweed), Emerald's people,
# trades and tutors. The checker is kanto_handoff/hoenn_rom_tools/hcanon.py (agreed differences: hcanon_decisions.json;
# the report: kanto_handoff/hoenn_check/CANON.md, rewritten by this suite, its hand-written summary kept). This suite runs
# it and prints each gap as a FAIL line ([call] waits for Jordan's answer, [bug] looks like a plain mistake of ours).
# It only reads the game's data. Glue after harness_head.py:
#   bash dev/checks/run_par.sh hoenn_canon
import importlib.util as _u, io as _io, contextlib as _cl

fails = []


def check(c, m):
    print(("   ok  " if c else "   FAIL ") + m)
    if not c:
        fails.append(m)


def _handoff():
    """kanto_handoff sits beside the game's folders: found by walking up from here (the main folder or a worktree)."""
    d = os.getcwd()
    for _ in range(8):
        cand = os.path.join(d, "kanto_handoff")
        if os.path.isdir(cand):
            return cand
        d = os.path.dirname(d)
    return os.path.join(os.getcwd(), "..", "..", "kanto_handoff")


_tools = os.path.join(_handoff(), "hoenn_rom_tools")
check(os.path.exists(os.path.join(_tools, "hcanon.py")) and os.path.exists(os.path.join(_tools, "canon", "oras_walk.json")),
      f"the checker and the canon content are in the handoff folder ({_tools}; make canon/ with hcanon_rom.py)")
_spec = _u.spec_from_file_location("hcanon", os.path.join(_tools, "hcanon.py"))
_buf = _io.StringIO()
with _cl.redirect_stdout(_buf):
    K = _u.module_from_spec(_spec); _spec.loader.exec_module(K)
    res = K.run()
    K.write_md(res, os.path.join(_handoff(), "hoenn_check", "CANON.md"))

# ---- hcanon lays the ORAS overlay over the area data itself: it must see what the game loaded
_area = g.loader.area_data["STORY_PROGRESSION"]
_same = [k for k in K.ORDER if len(K.A[k].get("trainer_pool") or []) != len(_area.get(k, {}).get("trainer_pool") or [])]
check(not _same, f"hcanon's Hoenn data (area data + hoenn_oras.json) has the game's trainers in every area {_same}")

# ---- the gaps, area by area, group by group (decisions applied)
for r in res:
    for group, kinds in K.GROUPS:
        gaps = [x for x in r["gaps"] if x[0] in kinds]
        if not gaps:
            continue
        for kind, what, call in gaps:
            tag = ("  [bug]" if call.startswith("BUG") else "  [call]") if call else ""
            check(False, f"{r['key']}: [{kind}] {what}{tag}")
    if not r["gaps"]:
        print(f"   ok  {r['key']}: as ORAS / Emerald" + (f" ({len(r['decided'])} agreed differences)" if r["decided"] else ""))
_tot = sum(len(r["gaps"]) for r in res)
print(f"   ..  hcanon: {_tot} gaps in {sum(1 for r in res if r['gaps'])} of {len(res)} areas; "
      f"{sum(len(r['decided']) for r in res)} agreed differences; "
      f"{sum(1 for r in res for x in r['gaps'] if x[2] and not x[2].startswith('BUG'))} wait for Jordan's call; "
      f"{sum(1 for r in res for x in r['gaps'] if x[2] and x[2].startswith('BUG'))} look like plain bugs")

print(f"##### {len(fails)} failures")
