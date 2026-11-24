"""Check every link in a built encyclopedia site (region/encyclopedia, 11-24), without a browser.

    python dev/encyclopedia/build_site.py <SITE>
    python dev/encyclopedia/check_links.py <SITE>

Reads the site's data files, works out every page that exists (the same routes site.html's route() knows), then checks
every href="#..." in every page's HTML. An href that also carries data-scroll is a contents-box jump inside its own
page and is skipped. Also reports leftover [[PL: link placeholders and {{markers}}. Exit code 1 when anything is broken."""
import json
import os
import re
import sys

LISTS = {"walkthrough", "places", "pokemon", "items", "trainers", "buildings", "mechanics", "moves", "tms"}


def slug(s):
    return re.sub(r"^-|-$", "", re.sub(r"[^a-z0-9]+", "-", str(s).lower()))


def load(site, name):
    p = os.path.join(site, "data", name)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}


def main(site):
    page = open(os.path.join(site, "index.html"), encoding="utf-8").read()
    live = json.loads(re.search(r"const SITE = (\{.*?\});", page).group(1))["live"]
    sp = load(site, "species.json")
    mech = load(site, "mechanics.json")
    jour = load(site, "journal.json")
    ok = {"home", "journal"} | {f"list-{k}" for k in LISTS}
    ok |= {f"pokemon-{i}" for i in sp.get("species", {})}
    ok |= {f"move-{slug(k)}" for k in sp.get("mv", {})}
    ok |= {f"map-{r.lower()}" for r in sp.get("maps", [])}
    ok |= {f"mechanic-{k}" for k in mech} | {f"journal-{k}" for k in jour}
    texts = [(f"mechanic-{k}", m.get("html", "")) for k, m in mech.items()] + [(f"journal-{k}", j.get("html", "")) for k, j in jour.items()]
    for r in live:
        d = load(site, f"{r['key']}.json")
        ok |= {f"part-{r['key']}-{p['n']}" for p in d.get("parts", [])}
        ok |= {f"place-{slug(k)}" for k in d.get("places", {})}
        ok |= {f"item-{k}" for k in d.get("items", {})} | {f"trainer-{k}" for k in d.get("trainers", {})}
        ok |= {f"building-{k}" for k, b in d.get("buildings", {}).items() if b.get("html")}
        ok |= {f"places-{b['slug']}" for b in d.get("nav", [])}
        if d.get("dex"):
            ok.add(f"dex-{r['key']}")
        texts += [(f"part-{r['key']}-{p['n']}", p.get("html", "") + p.get("toc", "")) for p in d.get("parts", [])]
        texts += [(f"place-{slug(k)}", p.get("html", "")) for k, p in d.get("places", {}).items()]
        texts += [(f"building-{k}", b.get("html", "")) for k, b in d.get("buildings", {}).items()]
        texts += [(f"trainer-{k}", "".join(x.get("html", "") for x in t.get("battles", []))) for k, t in d.get("trainers", {}).items()]
    broken, leftovers = [], []
    for where, html in texts:
        for m in re.finditer(r'<a\b[^>]*href="#([^"]*)"[^>]*>', html):
            if "data-scroll" in m.group(0) or m.group(1) == "":
                continue
            if m.group(1) not in ok:
                broken.append((where, m.group(1)))
        for bad in ("[[PL:", "{{"):
            if bad in html:
                leftovers.append((where, bad))
    print(f"{len(texts)} pages read, {len(ok)} pages exist")
    for where, target in sorted(set(broken))[:200]:
        print(f"  broken: {where} -> #{target}")
    for where, bad in sorted(set(leftovers))[:50]:
        print(f"  leftover {bad} in {where}")
    print("OK" if not broken and not leftovers else f"{len(set(broken))} broken links, {len(set(leftovers))} leftovers")
    return 1 if broken or leftovers else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
