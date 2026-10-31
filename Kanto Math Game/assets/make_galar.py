"""Draw Galar in the style of the simple Paldea town map -> galar_paldea_style.svg"""
import math
import random

random.seed(7)

W, H = 1500, 2920          # output canvas
S = 2.0                     # scale from the 728x1420 reference map
OX, OY = 130, 40             # offset

LAND = "#D4F7BA"
SEA = "#B5E7EF"
LINE = "#1EB4E6"


def roughen(pts, depth=4, amp=0.18, closed=True):
    """Midpoint-displacement so smooth outlines get the wobbly coastline look."""
    pts = [(OX + x * S, OY + y * S) for x, y in pts]
    for _ in range(depth):
        out = []
        n = len(pts) if closed else len(pts) - 1
        for i in range(n):
            (x1, y1), (x2, y2) = pts[i], pts[(i + 1) % len(pts)]
            dx, dy = x2 - x1, y2 - y1
            d = math.hypot(dx, dy)
            off = random.uniform(-amp, amp) * d
            mx, my = (x1 + x2) / 2 - dy / (d or 1) * off, (y1 + y2) / 2 + dx / (d or 1) * off
            out += [(x1, y1), (mx, my)]
        if not closed:
            out.append(pts[-1])
        pts = out
        amp *= 0.7
    return pts


def path(pts, closed=True):
    d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    return d + (" Z" if closed else "")


# --- Main island (Galar + Crown Tundra), traced from the official map ---
mainland = [
    (15, 55), (40, 28), (110, 30), (200, 22), (300, 30), (380, 42), (440, 80), (505, 100),
    (508, 132), (440, 142), (390, 150), (372, 190), (378, 240), (378, 300), (350, 335),
    (372, 380), (385, 430), (385, 495), (360, 515), (330, 520), (315, 560), (345, 600),
    (330, 640), (315, 690), (330, 740), (295, 760), (290, 800), (350, 812), (352, 840),
    (325, 862), (305, 905), (330, 960), (305, 1005), (335, 1050), (345, 1130), (395, 1150),
    (385, 1205), (345, 1225), (335, 1300), (318, 1350), (260, 1392), (160, 1395),
    (105, 1360), (80, 1290), (82, 1200), (72, 1100), (85, 1020), (68, 960), (60, 880),
    (75, 820), (75, 740), (60, 700), (30, 690), (25, 620), (12, 560), (5, 380), (10, 200),
]

isle_of_armor = [
    (470, 420), (520, 400), (560, 410), (595, 405), (612, 440), (605, 500), (612, 545),
    (585, 590), (530, 610), (485, 595), (462, 560), (470, 510), (455, 470),
]

small_islands = [
    [(395, 360), (430, 345), (440, 352), (405, 372)],                # Route 9 islet
    [(18, 900), (35, 880), (42, 930), (30, 965), (16, 950)],          # west islets
    [(100, 1375), (118, 1370), (120, 1390), (102, 1392)],
]

# --- Water features (lakes = filled, rivers = open lines) ---
lakes = [
    [(150, 720), (185, 712), (195, 745), (175, 790), (150, 770)],    # Lake of Outrage
    [(205, 735), (240, 728), (245, 775), (215, 790), (200, 765)],    # Axew's Eye
    [(228, 855), (262, 850), (270, 872), (240, 880)],                # Route 2 lake
    [(255, 1160), (295, 1150), (305, 1185), (270, 1200)],            # Ballimere Lake
    [(160, 1330), (210, 1325), (215, 1355), (165, 1360)],            # Lakeside Cave pond
    [(505, 480), (535, 470), (545, 500), (515, 512)],                # Isle lagoon
]
rivers = [
    [(14, 196), (120, 200), (250, 196), (372, 200)],                  # Wyndon river
    [(12, 520), (110, 515), (190, 505), (290, 500), (385, 498)],      # Hammerlocke / Rt 7 river
    [(180, 520), (175, 600), (185, 700), (180, 800)],                # Wild Area river
    [(320, 430), (335, 450), (360, 470), (385, 470)],                # Route 9 inlet
    [(240, 862), (290, 860), (340, 845)],                            # Route 2 stream
    [(80, 1215), (140, 1222), (200, 1215), (260, 1220), (335, 1230)],# Tundra river
]

# --- Towns: red = major cities (like Mesagoza/Levincia), blue = towns ---
towns = [
    ("Wyndon", 190, 130, "red", "above"),
    ("Circhester", 315, 372, "blue", "above"),
    ("Ballonlea", 75, 340, "blue", "above"),
    ("Stow-on-Side", 92, 448, "blue", "above"),
    ("Hammerlocke", 190, 488, "red", "above"),
    ("Spikemuth", 343, 492, "blue", "above"),
    ("Turffield", 88, 578, "blue", "above"),
    ("Hulbury", 280, 575, "blue", "above"),
    ("Motostoke", 185, 652, "red", "above"),
    ("Wedgehurst", 200, 898, "blue", "above"),
    ("Postwick", 200, 968, "blue", "above"),
    ("Freezington", 115, 1190, "blue", "above"),
    ("Dyna Tree Hill", 205, 1068, "blue", "above"),
    ("Master Dojo", 572, 455, "blue", "above"),
]

out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
       f'<rect width="{W}" height="{H}" fill="{SEA}"/>']
for shape, amp in [(mainland, 0.16), (isle_of_armor, 0.2)] + [(s, 0.25) for s in small_islands]:
    out.append(f'<path d="{path(roughen(shape, 5, amp))}" fill="{LAND}" stroke="{LINE}" stroke-width="3" stroke-linejoin="round"/>')
for lake in lakes:
    out.append(f'<path d="{path(roughen(lake, 4, 0.2))}" fill="{SEA}" stroke="{LINE}" stroke-width="3" stroke-linejoin="round"/>')
for r in rivers:
    out.append(f'<path d="{path(roughen(r, 4, 0.08, closed=False), closed=False)}" fill="none" stroke="{LINE}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>')

font = 'font-family="Verdana, Tahoma, sans-serif" font-weight="bold" font-size="34" text-anchor="middle"'
for name, x, y, color, pos in towns:
    cx, cy = OX + x * S, OY + y * S
    fill = "#FF0000" if color == "red" else "#0000FF"
    out.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="34" fill="{fill}" stroke="#666" stroke-width="5"/>')
    ty = cy - 46 if pos == "above" else cy + 76
    out.append(f'<text x="{cx:.0f}" y="{ty:.0f}" {font}>{name}</text>')

out.append("</svg>")
open("galar_paldea_style.svg", "w", encoding="utf-8").write("\n".join(out))
print("wrote galar_paldea_style.svg")

