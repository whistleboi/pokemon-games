"""Move helper functions that several suites copy word for word into one shared <name>_lib.py (Checks C5, 11-24).

    python dev/checks/share_helpers.py <lib name> <function,function,...> <suite> <suite> ... [--dry]

For each function, the version most of the suites share is written to dev/checks/<lib name>_lib.py (with the comment
lines just above it). In each suite, a copy identical to that version (same code, by Python's own parse) is taken out
with the comment lines just above it; where the first one stood goes
    exec(open("dev/checks/<lib name>_lib.py", encoding="utf-8").read())
A suite whose own different version of one of the functions comes before that line, that assigns one of the names, or
whose shared functions' default values need names, is stopped and named (nothing written for it). Tests are never
touched; afterwards re-run each suite: 0 fails and the same checks made as baseline.tsv."""
import ast
import collections
import os
import sys

CHECKS = os.path.dirname(os.path.abspath(__file__))


def read(path):
    b = open(path, "rb").read()
    crlf = b"\r\n" in b
    return b.decode("utf-8").replace("\r\n", "\n"), crlf


def top_defs(src):
    """{name: [(node, start line incl. its comments and decorators, end line, dump)]} (1-based, inclusive)."""
    tree = ast.parse(src)
    lines = src.split("\n")
    out = collections.defaultdict(list)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            start = min([node.lineno] + [d.lineno for d in node.decorator_list])
            while start > 1 and lines[start - 2].lstrip().startswith("#") and not lines[start - 2].startswith(" "):
                start -= 1   # (the comment lines just above it belong to it)
            out[node.name].append((node, start, node.end_lineno, ast.dump(node, include_attributes=False)))
    return tree, out


def main(argv):
    dry = "--dry" in argv
    argv = [a for a in argv if a != "--dry"]
    lib, funcs, suites = argv[0], argv[1].split(","), argv[2:]
    texts, defs, trees = {}, {}, {}
    for s in suites:
        texts[s] = read(os.path.join(CHECKS, f"{s}_body.py"))
        trees[s], defs[s] = top_defs(texts[s][0])
    # each function's shared version: the one most suites have
    canon = {}
    for f in funcs:
        c = collections.Counter(d[3] for s in suites for d in defs[s].get(f, []))
        if not c:
            sys.exit(f"no suite defines {f}")
        dump, n = c.most_common(1)[0]
        src_suite = next(s for s in suites if any(d[3] == dump for d in defs[s].get(f, [])))
        node, a, b, _ = next(d for d in defs[src_suite][f] if d[3] == dump)
        lines = texts[src_suite][0].split("\n")
        canon[f] = (dump, "\n".join(lines[a - 1:b]), n, src_suite, node)
        needs = {x.id for x in ast.walk(ast.Module(body=node.args.defaults + node.args.kw_defaults + node.decorator_list,
                                                   type_ignores=[])) if isinstance(x, ast.Name)} if (
            node.args.defaults or node.decorator_list) else set()
        if needs - {"None", "True", "False"}:
            print(f"   note: {f}'s default values / decorators use {sorted(needs)}: must exist before the exec line")
        canon[f] = canon[f] + (needs,)
    report, done = [], 0
    plans = {}
    for s in suites:
        src, crlf = texts[s]
        lines = src.split("\n")
        take = []   # (start, end) spans to take out
        for f in funcs:
            for node, a, b, dump in defs[s].get(f, []):
                if dump == canon[f][0]:
                    take.append((a, b, f))
        if not take:
            report.append(f"{s}: none of them identical, left alone")
            continue
        first = min(a for a, _, _ in take)
        # Safe when nothing else binds a name before the copy taken out: the shared one then comes in earlier (at the
        # exec line) but every later def or assignment still wins after it, as before. Anything binding it before the
        # copy (its own other version, a variable) would now be overwritten by the exec line, or win over it: stop.
        taken_at = {f: min(a for a, _, g in take if g == f) for f in {g for _, _, g in take}}
        bad = []
        for f in taken_at:
            for node, a, b, dump in defs[s].get(f, []):
                if (a, b, f) not in take and a < taken_at[f]:
                    bad.append(f"its own {f} (line {a}) comes before the copy")
        for f in funcs:   # (one it keeps its own version of, bound before the exec line, would be overwritten by it)
            if f not in taken_at:
                for node, a, b, dump in defs[s].get(f, []):
                    if a < first:
                        bad.append(f"its own {f} (line {a}) comes before the exec line")
                for node in trees[s].body:
                    for x in ast.walk(node):
                        if isinstance(x, ast.Name) and isinstance(x.ctx, ast.Store) and x.id == f and x.lineno < first:
                            bad.append(f"sets {f} (line {x.lineno}) before the exec line")
        for node in trees[s].body:
            for x in ast.walk(node):
                if isinstance(x, ast.Name) and isinstance(x.ctx, ast.Store) and x.id in taken_at \
                        and x.lineno < taken_at[x.id]:
                    bad.append(f"sets {x.id} (line {x.lineno}) before the copy")
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                for al in node.names:
                    nm = (al.asname or al.name).split(".")[0]
                    if nm in taken_at and node.lineno < taken_at[nm]:
                        bad.append(f"imports {nm} (line {node.lineno}) before the copy")
        if bad:
            report.append(f"{s}: STOPPED - " + "; ".join(bad))
            continue
        keep = set()
        for a, b, _ in take:
            keep.update(range(a, b + 1))
        names = sorted({f for _, _, f in take}, key=funcs.index)
        new = []
        for i, line in enumerate(lines, 1):
            if i == first:
                new.append(f'exec(open("dev/checks/{lib}_lib.py", encoding="utf-8").read())   '
                           f'# ({", ".join(names)}: shared, Checks C5)')
            if i in keep:
                continue
            new.append(line)
        out, blank = [], 0   # (no more than two blank lines in a row where copies came out)
        for line in new:
            blank = blank + 1 if not line.strip() else 0
            if blank <= 2:
                out.append(line)
        plans[s] = (out, crlf)
        report.append(f"{s}: {len(take)} taken out ({', '.join(names)}), {len(lines) - len(out)} lines fewer")
        done += 1
    head = [f"# Helpers that {', '.join(s for s in suites if s in plans)} shared word for word (Checks C5, 11-24;",
            f"# made by dev/checks/share_helpers.py). Each suite runs: exec(open(\"dev/checks/{lib}_lib.py\", "
            f"encoding=\"utf-8\").read())",
            "# They use the suite's own globals (g, story, fails, check...). Change one here and every suite gets it.", ""]
    body = []
    for f in funcs:
        body += [canon[f][1], "", ""]
    for r in report:
        print("  ", r)
    print(f"   {lib}_lib.py: {len(funcs)} functions, {sum(len(canon[f][1].split(chr(10))) for f in funcs)} lines")
    if dry:
        return
    if os.path.exists(os.path.join(CHECKS, f"{lib}_lib.py")):
        sys.exit(f"{lib}_lib.py exists already: add to it by hand")
    open(os.path.join(CHECKS, f"{lib}_lib.py"), "w", encoding="utf-8", newline="\n").write(
        "\n".join(head + body).rstrip("\n") + "\n")
    for s, (out, crlf) in plans.items():
        open(os.path.join(CHECKS, f"{s}_body.py"), "wb").write(("\r\n" if crlf else "\n").join(out).encode("utf-8"))


if __name__ == "__main__":
    main(sys.argv[1:])
