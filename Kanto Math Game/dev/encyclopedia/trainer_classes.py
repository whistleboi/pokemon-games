"""Trainer class pages (region/encyclopedia, 11-24): one page per kind of trainer (Bug Catcher, Hiker, Team Rocket Grunt...)
from every written region's trainers (build.all_trainers on each place's facts): their portrait from the game's own
trainer sprites, where they stand, and the teams they use. Built during build_site's region pass (collect), written into
the mechanics pages (group "Trainer classes"); the portraits go to data/trainers-maps.json (loaded like map pictures)."""
import base64
import os
import re
from io import BytesIO

import build as B
import facts as F

ROWS = []          # (region title, place key, trainer dict)
PICS = {}          # "tc/<sprite>" -> data URI


def collect(region_title, key, f):
    for t in B.all_trainers(f):
        if t.get("team"):
            ROWS.append((region_title, key, t))


def _pic(sprite):
    if not sprite:
        return None
    path = os.path.join(F.A, "sprites", "trainers", sprite)
    if not os.path.exists(path):
        return None
    name = f"tc/{sprite}"
    if name not in PICS:
        from PIL import Image
        im = Image.open(path).convert("RGBA")
        box = im.getbbox()
        if box:
            im = im.crop(box)
        h = 96
        if im.height > h:
            im = im.resize((max(1, im.width * h // im.height), h), Image.NEAREST)
        buf = BytesIO()
        im.save(buf, "WEBP", lossless=True, method=6)
        PICS[name] = "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()
    return name


def _slug(s):
    return re.sub(r"[^a-z0-9]+", "-", str(s).lower()).strip("-")


def pages(_unused=None):
    """{slug: page} for the mechanics dict: "class-<class>" pages, group "Trainer classes"."""
    by = {}
    for region, key, t in ROWS:
        cls = B.class_word(t.get("class")) if t.get("class") else "Trainer"
        if t.get("villain"):
            cls = "Team Magma/Aqua"
        by.setdefault(cls, []).append((region, key, t))
    out = {}
    for cls, rows in sorted(by.items()):
        sprites = []
        for _r, _k, t in rows:
            if t.get("sprite") and t["sprite"] not in sprites:
                sprites.append(t["sprite"])
        pics = [p for p in (_pic(s) for s in sprites[:6]) if p]
        head = ('<div class="tcpics">' + "".join(f'<img data-region="trainers" data-map="{p}" alt="{B.esc(cls)}" loading="lazy">'
                                                 for p in pics) + "</div>") if pics else ""
        regions = {}
        for region, key, t in rows:
            regions.setdefault(region, []).append((key, t))
        body = [head, f"<p>{len(rows)} {B.esc(cls)} battle{'s' if len(rows) != 1 else ''} in the regions written so far, "
                      f"in {len(regions)} region{'s' if len(regions) != 1 else ''}.</p>"]
        for region, lst in regions.items():
            trs = []
            seen = set()
            for key, t in lst:
                sig = (B.trainer_name(t), key, tuple(m["id"] for m in t["team"]))
                if sig in seen:
                    continue
                seen.add(sig)
                nm = (F.PLACES.get(key) or {}).get("route_name") or key.replace("_", " ").title()
                where = f'<a href="#place-{_slug(key)}">{B.esc(F.fix(nm))}</a>' + (f' <span class="small">({B.esc(t["where"])})</span>'
                                                                                    if t.get("where") not in (None, "outside", "on the map") else "")
                trs.append(f"<tr><td>{B.esc(B.trainer_name(t))}</td><td>{where}</td><td>{B.team_html(t['team'])}</td></tr>")
            body.append(f'<h2>{B.esc(region)}</h2><div class="frame"><table><thead><tr><th>Trainer</th><th>Where</th>'
                        f'<th>Team</th></tr></thead><tbody>{"".join(trs)}</tbody></table></div>')
        out[f"class-{_slug(cls)}"] = {"title": cls, "group": "Trainer classes",
                                      "blurb": f"{len(rows)} battles", "html": "".join(body), "toc": ""}
    return out
