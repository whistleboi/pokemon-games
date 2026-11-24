"""The number garden: a walked room's floor puzzle (Orre's Agate Gym, Jordan 11-24: "our own puzzle" in place of the fan
game's mirrors and light - questions/ORRE.md 6).

A room's "gardens": {"flag": set once every garden blooms, "gardens": [{"target": n, "beds": {"x,y": number}, "label": [x, y]}],
"done": [lines when all have bloomed]}. Walk onto a garden's beds: each bed you step on blooms and its number is added. Make
the garden's target exactly and it stays in bloom (flag "<flag>_<i>"); go over and the vines grow back over it - its beds
close and you start that garden again. Walking back over a bloomed bed adds nothing. Every garden in bloom: the room's flag
(its barriers - the vines on the way on - open, as a Mauville switch's would). walk_town.py calls step() after each step
and draw() with the room's floor."""
import os

import pygame

_IMG = {}


def _gardens(state):
    return getattr(state, "gardens", None) or None


def _flags(state):
    return state.game.story_manager.story_flags


def _bloomed(state):
    """{garden index: the beds bloomed on this try} (kept while you're in the room)."""
    return state.__dict__.setdefault("_garden_bloom", {})


def step(state, t):
    g = _gardens(state)
    if not g:
        return
    key = "%d,%d" % tuple(t)
    flags = _flags(state)
    for i, gd in enumerate(g["gardens"]):
        if key not in gd["beds"]:
            continue
        if flags.get(f"{g['flag']}_{i}"):
            return
        got = _bloomed(state).setdefault(i, set())
        if key in got:
            return
        got.add(key)
        total = sum(gd["beds"][k] for k in got)
        target = gd["target"]
        if total == target:
            flags[f"{g['flag']}_{i}"] = True
            _bloomed(state).pop(i, None)
            if all(flags.get(f"{g['flag']}_{j}") for j in range(len(g["gardens"]))):
                flags[g["flag"]] = True
                keep = (state.player, state.facing)
                state._from_art(state.town_map["rooms"][state.room] if state.room else state.town_map)
                state.player, state.facing = keep
                state.show_message(list(g.get("done") or ["Every garden is in bloom!"]))
            else:
                state.flash(f"{' + '.join(str(gd['beds'][k]) for k in sorted(got, key=lambda k: gd['beds'][k]))} = {target}! The garden is in full bloom!", 150)
        elif total > target:
            _bloomed(state).pop(i, None)
            state.flash(f"{total} is more than {target}! The vines grow back over the garden...", 150)
        else:
            state.flash(f"Bloom! {total} so far - this garden wants {target}.", 120)
        return


def _img(state, name, size):
    k = (name, size)
    if k not in _IMG:
        try:
            _IMG[k] = pygame.transform.scale(pygame.image.load(os.path.join(
                state.game.assets.assets_dir, "dungeon", "characters", "orre_garden", name)).convert_alpha(), (size, size))
        except (pygame.error, FileNotFoundError):
            _IMG[k] = None
    return _IMG[k]


def draw(state, screen, at, fonts):
    g = _gardens(state)
    if not g:
        return
    from src.ui import theme
    flags = _flags(state)
    font = fonts.get("label") or fonts.get("small")
    for i, gd in enumerate(g["gardens"]):
        done = flags.get(f"{g['flag']}_{i}")
        got = _bloomed(state).get(i, set())
        for k, n in gd["beds"].items():
            r = at(tuple(int(v) for v in k.split(",")))
            if done or k in got:
                img = _img(state, "bloom.png", r.w)
                if img is not None:
                    screen.blit(img, r)
            else:
                bed = r.inflate(-r.w // 6, -r.h // 6)
                pygame.draw.rect(screen, (120, 82, 50), bed, border_radius=max(2, r.w // 8))
                pygame.draw.rect(screen, (86, 56, 34), bed, 2, border_radius=max(2, r.w // 8))
            if font is not None and not done:
                theme.shadow_text(screen, str(n), font, r.centerx, r.centery, align="center")
        if font is not None and gd.get("label"):
            r = at(tuple(gd["label"]))
            text = "In bloom!" if done else f"Make {gd['target']}"
            theme.shadow_text(screen, text, font, r.centerx + r.w // 2, r.centery, color=(255, 236, 150), align="center")
