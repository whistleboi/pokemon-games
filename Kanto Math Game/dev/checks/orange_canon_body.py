# The Orange canon check (11-17; SWEEP_RULES Part 3 item 7): every Orange area built on Orange Islands Beta 5.7's maps
# against 5.7's own content (kanto_handoff/orange_rom_tools/ocanon.py: trainers and their teams at fixed levels, item
# balls, hidden items, people, gifts, wild tables). Each gap is a FAIL line; agreed differences are in ocanon_decisions.json.
#   bash dev/checks/run.sh orange_canon
import importlib.util as _u, io as _io, contextlib as _cl
_tools = os.path.normpath(os.path.join(os.getcwd(), "..", "..", "kanto_handoff", "orange_rom_tools"))
_spec = _u.spec_from_file_location("ocanon", os.path.join(_tools, "ocanon.py"))
_buf = _io.StringIO()
_keep = sys.argv
sys.argv = ["ocanon.py"]
with _cl.redirect_stdout(_buf):
    _oc = _u.module_from_spec(_spec); _spec.loader.exec_module(_oc)
    _rc = _oc.main(["--md", os.path.join(_tools, "..", "orange_check", "CANON.md")])
sys.argv = _keep
fails = 0
for line in _buf.getvalue().splitlines():
    if line.startswith("- ["):
        print("   FAIL " + line[2:]); fails += 1
    else:
        print("   " + line)
print(f"##### {fails} failures")
