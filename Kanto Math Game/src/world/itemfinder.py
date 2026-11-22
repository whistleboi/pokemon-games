"""The Itemfinder (FireRed's, from Oak's aide on Route 11): with it in the Bag, a hidden item left on screen makes it
beep once, and it says which way the item lies. Hidden items are still found by stepping on (or walking into) them."""

# (FireRed's Itemfinder reads the screen: 7 tiles either side, 5 up and down)
REACH_X, REACH_Y = 7, 5


def _way(dx, dy):
    ns = "north" if dy < 0 else "south" if dy > 0 else ""
    ew = "west" if dx < 0 else "east" if dx > 0 else ""
    if ns and ew and abs(dx) > 2 * abs(dy):
        ns = ""
    elif ns and ew and abs(dy) > 2 * abs(dx):
        ew = ""
    return "-".join(w for w in (ns, ew) if w) or "here"


def beep(story, hidden, here, flag_of, heard):
    """The line to show when the Itemfinder picks up an item in `hidden` {"x,y": item} near `here`, else None.
    `flag_of(x, y)` is the item's found flag; `heard` a set of spots it has already beeped for (this visit)."""
    inv = story.inventory or {}
    dowse = inv.get("DOWSING_MACHINE", 0) > 0   # (Unova's own: Bianca's gift at the Castelia Gate, B2W2; 11-21)
    if not hidden or (inv.get("ITEMFINDER", 0) <= 0 and not dowse):
        return None
    best = None
    for key in hidden:
        try:
            x, y = (int(v) for v in key.split(","))
        except ValueError:
            continue
        dx, dy = x - here[0], y - here[1]
        if abs(dx) > REACH_X or abs(dy) > REACH_Y or (dx, dy) == (0, 0) or key in heard or story.story_flags.get(flag_of(x, y)):
            continue
        if best is None or abs(dx) + abs(dy) < abs(best[1]) + abs(best[2]):
            best = (key, dx, dy)
    if best is None:
        return None
    heard.add(best[0])
    if dowse and inv.get("ITEMFINDER", 0) <= 0:
        return f"The Dowsing MCHN is reacting! Something's buried {abs(best[1]) + abs(best[2])} steps to the {_way(best[1], best[2])}."
    return f"The Itemfinder is beeping! Something's hidden to the {_way(best[1], best[2])}."


# ---- the Dowsing MCHN's own screen (11-21, Jordan: "Black 2's dowsing screen"): switched on from the Bag; while on, a
# panel on the map shows its two rods swinging toward the nearest buried item within reach, glowing brighter as you near it
DOWSE_REACH = 9


def dowsing_on(story):
    return bool((story.story_flags or {}).get("dowsing_on")) and (story.inventory or {}).get("DOWSING_MACHINE", 0) > 0


def dowse(story, hidden, here, flag_of):
    """(dx, dy) to the nearest unfound hidden item within DOWSE_REACH tiles, or None."""
    best = None
    for key in hidden or {}:
        try:
            x, y = (int(v) for v in key.split(","))
        except ValueError:
            continue
        dx, dy = x - here[0], y - here[1]
        if abs(dx) + abs(dy) > DOWSE_REACH or story.story_flags.get(flag_of(x, y)):
            continue
        if best is None or abs(dx) + abs(dy) < abs(best[0]) + abs(best[1]):
            best = (dx, dy)
    return best


def draw_dowsing(screen, rect, found, fonts=None):
    """The panel: two rods from the bottom corners; with an item in reach they swing toward it (screen up = north) and
    their tips glow, brighter the nearer it is; with none they hang still."""
    import math
    import pygame
    pygame.draw.rect(screen, (24, 30, 48), rect, border_radius=12)
    pygame.draw.rect(screen, (120, 200, 255), rect, 2, border_radius=12)
    t = pygame.time.get_ticks() / 1000.0
    if found is None:
        ang, glow = -math.pi / 2, 0.0
        sway = math.sin(t * 2) * 0.08
    else:
        dx, dy = found
        ang = math.atan2(dy, dx) if (dx, dy) != (0, 0) else -math.pi / 2
        d = abs(dx) + abs(dy)
        glow = max(0.15, 1.0 - d / (DOWSE_REACH + 1))
        sway = math.sin(t * (4 + 8 * glow)) * 0.05
    clip = screen.get_clip()
    screen.set_clip(rect.inflate(-4, -4))
    for side in (-1, 1):
        base = (rect.centerx + side * rect.w // 4, rect.bottom - 10)
        a = ang + sway * side
        tip = (int(base[0] + math.cos(a) * rect.h * 0.5), int(base[1] + math.sin(a) * rect.h * 0.5))
        pygame.draw.line(screen, (200, 210, 230), base, tip, 5)
        if glow > 0:
            c = (int(80 + 175 * glow), int(200 + 55 * glow), 255)
            pygame.draw.circle(screen, c, tip, int(5 + 7 * glow))
    screen.set_clip(clip)
    if fonts is not None:
        label = fonts["small"].render("DOWSING", True, (180, 220, 255))
        screen.blit(label, (rect.x + 8, rect.y + 4))
