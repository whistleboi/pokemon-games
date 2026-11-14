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
    if not hidden or (story.inventory or {}).get("ITEMFINDER", 0) <= 0:
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
    return f"The Itemfinder is beeping! Something's hidden to the {_way(best[1], best[2])}."
