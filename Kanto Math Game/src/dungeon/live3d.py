"""Live 3D (11-20, Jordan: Castelia's camera, "Live 3D camera"): a place's own Black 2 models drawn every frame from a
moving camera on the graphics card, as the DS does: the view tilts and swings as you walk (the avenue's rail cameras,
the streets' camera strips). PC only: it needs moderngl (an OpenGL 3.3 card); without it, or headless, the baked
picture stays (available() says which).

Scenes: assets/b2_3d/<zone>.npz (kanto_handoff/unova_map_tools/export3d.py): per texture its picture, its triangles'
corners (x, y up, z, in tiles from the zone's top-left, the walk grid's units) and its kind (0 ground, 1 building,
2 shadow sheet, 4 backdrop past a side street's edges: seen from inside only, never walked on). People are drawn into the same scene as upright sprites (billboards), so buildings hide them.

What the export leaves out, put back on loading (11-21): an atlas's unused space is a key colour (230, 57, 255), drawn
see-through; a light sheet (a lamp's glow, the piers' clouds: one pale colour on a see-through picture) is translucent on
the DS and its glow is a quarter circle mirrored into a whole one (its UVs run 0..2), so it is drawn mirrored, faint, after
everything solid (kind 3).
"""
import math
import os

import pygame

try:   # (numpy and moderngl are only on a PC set up for the live camera: without them, the baked pictures)
    import numpy as np
except ImportError:
    np = None

_CTX = {}
_SCENES = {}
KEY = (230, 57, 255)   # (an atlas's unused space)
LIGHT_ALPHA = 0.42     # (a light sheet: the lamps' glow, the clouds)
GLASS = (118, 146, 176, 190)   # (a tower's window pane: Black 2 leaves it open, an inner model behind; 11-21)
ALLOW_HOLES = False    # (the checks: draw a scene with holes anyway, to try its camera)

VERT = """
#version 330
uniform mat4 mvp;
in vec3 pos;
in vec2 uv;
out vec2 v_uv;
out float v_y;
void main() { gl_Position = mvp * vec4(pos, 1.0); v_uv = uv; v_y = pos.y; }
"""
FRAG = """
#version 330
uniform sampler2D tex;
uniform int kind;
uniform vec3 tint;
uniform float alpha;
uniform int glass;
in vec2 v_uv;
in float v_y;
out vec4 color;
void main() {
    vec4 c = texture(tex, v_uv);
    if (glass == 1) {   // (a tower's window panes, after everything solid: tinted, what's inside still showing)
        if (c.a < 0.05 || c.a > 0.95) discard;
        color = vec4(c.rgb * tint, c.a);
        return;
    }
    if (c.a < (kind < 2 ? 0.95 : 0.5)) discard;
    if (kind == 2) { color = vec4(0.0, 0.0, 0.0, 0.38); return; }   // (a shadow sheet: darkens what's under it)
    color = vec4(c.rgb * tint, alpha);
}
"""


def available(game=None):
    """True when the live camera can draw here (a real window and a card that does OpenGL 3.3)."""
    if np is None:
        return False
    if os.environ.get("SDL_VIDEODRIVER") == "dummy" and not getattr(game, "live3d_headless", False):
        return False
    return _context() is not None


def _context():
    if "ctx" not in _CTX:
        try:
            import moderngl
            try:
                ctx = moderngl.create_standalone_context()
            except Exception:   # (no X display: Linux's EGL)
                ctx = moderngl.create_standalone_context(backend="egl")
            prog = ctx.program(vertex_shader=VERT, fragment_shader=FRAG)
            _CTX["ctx"], _CTX["prog"], _CTX["mgl"] = ctx, prog, moderngl
        except Exception:
            _CTX["ctx"] = None
    return _CTX["ctx"]


def has_scene(game, zone):
    return os.path.exists(os.path.join(game.assets.assets_dir or "assets", "b2_3d", "%d.npz" % int(zone)))


class Scene:
    """One zone's models on the card."""

    def __init__(self, path):
        ctx, prog, mgl = _context(), _CTX["prog"], _CTX["mgl"]
        data = np.load(path)
        self.parts = []
        solid = []
        lo, hi = np.full(3, 1e9, np.float32), np.full(3, -1e9, np.float32)
        for key in sorted(k for k in data.files if k.startswith("v")):
            i = key[1:]
            verts = data["v" + i].astype("f4")
            lo, hi = np.minimum(lo, verts[:, :3].min(0)), np.maximum(hi, verts[:, :3].max(0))
            kind, rgba, verts = _fix(int(data["k" + i]), data["t" + i], verts)
            if kind in (0, 1):
                solid.append(verts[:, :3].reshape(-1, 3, 3))
            if kind == 0:
                self.__dict__.setdefault("_kind0", []).append(verts[:, :3].reshape(-1, 3, 3))
            elif kind == 1:   # (stairs, pier ramps: walked on where there's no ground of the block's own)
                self.__dict__.setdefault("_kind1", []).append(verts[:, :3].reshape(-1, 3, 3))
            tex = ctx.texture((rgba.shape[1], rgba.shape[0]), 4, np.ascontiguousarray(rgba).tobytes())
            tex.filter = (mgl.NEAREST, mgl.NEAREST)
            tex.repeat_x = tex.repeat_y = True
            vbo = ctx.buffer(verts.tobytes())
            vao = ctx.vertex_array(prog, [(vbo, "3f 2f", "pos", "uv")])
            self.parts.append((kind, tex, vao))
            if kind in (0, 1) and (rgba[..., 3] == GLASS[3]).any():
                self.__dict__.setdefault("_glass", []).append((tex, vao))
        self.parts.sort(key=lambda p: (p[0] == 2) + 2 * (p[0] == 3))   # (shadow sheets after the solid, light sheets last)
        self._flat = np.concatenate(solid)[:, :, [0, 2]] if solid else np.zeros((0, 3, 2), "f4")   # (seen from above: for covers())
        self._covers = {}
        self.lo, self.hi = lo, hi
        self.cam = np.array(data["cam"], "f4") if "cam" in data.files else None   # (export3d.camera: Black 2's camera here)
        self.indoor = bool(int(data["indoor"])) if "indoor" in data.files else False   # (a room: black round it, 11-21)
        self.fbo = None
        self._sprites = {}

    def ground_at(self, x, y, near=None):
        """The scene's ground (kind 0) under tile (x, y)'s middle, in tiles, or None (cached per tile): of the surfaces
        there, the one nearest `near` (the place's own height map: the street, not an awning or a planter over it, 11-21),
        else the highest; with no ground, a building model's lowest surface (stairs, a ramp)."""
        cache = self.__dict__.setdefault("_ground", {})
        key = (x, y, None if near is None else round(near, 1))
        if key not in cache:
            pick = max if near is None else (lambda ys: ys[np.argmin(np.abs(ys - near))])
            cache[key] = self._top(x, y, "_kind0", pick)
            if cache[key] is None:
                cache[key] = self._top(x, y, "_kind1", min)
        return cache[key]

    def _top(self, x, y, which, pick):
        T = self.__dict__.get(which + "_tris")
        if T is None:
            T = np.concatenate(getattr(self, which)) if getattr(self, which, None) else np.zeros((0, 3, 3), "f4")
            self.__dict__[which + "_tris"] = T
        if True:
            p = np.array([x + 0.5, y + 0.5], "f4")
            a, b, c = T[:, 0, [0, 2]], T[:, 1, [0, 2]], T[:, 2, [0, 2]]
            v0, v1, v2 = c - a, b - a, p - a
            d00, d01, d11 = (v0 * v0).sum(1), (v0 * v1).sum(1), (v1 * v1).sum(1)
            d20, d21 = (v2 * v0).sum(1), (v2 * v1).sum(1)
            den = d00 * d11 - d01 * d01
            ok = np.abs(den) > 1e-9
            den = np.where(ok, den, 1.0)
            u, v = (d11 * d20 - d01 * d21) / den, (d00 * d21 - d01 * d20) / den
            hit = ok & (u >= -1e-3) & (v >= -1e-3) & (u + v <= 1 + 1e-3)
            if hit.any():
                ys = T[:, 0, 1] * (1 - u - v) + T[:, 2, 1] * u + T[:, 1, 1] * v
                return float(pick(ys[hit]))
            return None

    def surfaces(self, x, y):
        """Every walkable height under tile (x, y)'s middle, tiles: the ground's (kind 0) not counting the sea under the
        piers, else a building model's lowest (stairs, a ramp); [] with none."""
        out = []
        self._top(x, y, "_kind0", lambda ys: out.extend(float(v) for v in ys) or 0.0)
        cap = 1e9 if getattr(self, "indoor", False) else 8.0   # (outdoors a roof over a hole isn't ground; a room's upper floors are: the Gym's at 10 and 20)
        land = sorted({round(v, 3) for v in out if -1.0 < v < cap}) or sorted({round(v, 3) for v in out if v < cap})   # (not the sea, nor a roof over a hole)
        if not land:
            low = self._top(x, y, "_kind1", min)
            land = [low] if low is not None else []
        return land

    def walk_heights(self, tiles, hint=None):
        """The ground you walk on over a place's open tiles {(x, y): height}, worked out once (11-21): tiles with a single
        surface (or a road and its kerb) first, then outward a tile at a time from the lowest, each taking the surface nearest the neighbour it was reached from,
        so the street runs on under an awning, a planter or a ledge over it, and stairs climb step by step; hint(x, y)
        (the place's own height map) picks between a road and its kerb. Tiles cut off from the rest take their lowest."""
        import heapq
        tiles = set(tiles)
        S = {t: self.surfaces(*t) for t in tiles}
        levels = {hint(*t) for t in tiles} if hint else set()
        if len(levels) == 1 and None not in levels:   # (one height for the whole floor: a level of a stacked room, the Gym's)
            lv = levels.pop()
            return {t: min(ys, key=lambda v: abs(v - lv)) for t, ys in S.items() if ys}
        H, todo = {}, []
        for t, ys in S.items():
            if ys and ys[-1] - ys[0] < 1.0:   # (one surface, or a road and its kerb: settled, the one the place's heights say)
                h = hint(*t) if hint else None
                H[t] = min(ys, key=lambda v: abs(v - h)) if h is not None else ys[-1]
                heapq.heappush(todo, (H[t], t))
        while todo:   # (lowest ground first: the street claims what it reaches before an awning or a planter can)
            _h, (x, y) = heapq.heappop(todo)
            for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if q in S and q not in H:
                    H[q] = min(S[q], key=lambda v: abs(v - H[(x, y)])) if S[q] else H[(x, y)]   # (no ground: a hole, as its neighbour)
                    heapq.heappush(todo, (H[q], q))
        for t, ys in S.items():
            if t not in H and ys:   # (cut off, as a seller boxed in by her stall: the lowest ground, not the awning)
                H[t] = max(v for v in ys if v - ys[0] < 1.0)
        return H

    def covers(self, tiles):
        """True when every tile (x, y) given has the scene's ground (or a building's floor) under its middle: a scene
        exported with holes where you walk would show the sky there and drop you through it (11-21)."""
        if ALLOW_HOLES:
            return True
        key = hash(tuple(sorted(tiles)))
        if key not in self._covers:
            self._covers[key] = not self.holes(tiles)
        return self._covers[key]

    def holes(self, tiles):
        """The tiles given with nothing of the scene under their middles."""
        tris = self._flat
        out = []
        for x, y in tiles:
            p = np.array([x + 0.5, y + 0.5], "f4")
            a, b, c = tris[:, 0], tris[:, 1], tris[:, 2]
            v0, v1, v2 = c - a, b - a, p - a
            d00, d01, d11 = (v0 * v0).sum(1), (v0 * v1).sum(1), (v1 * v1).sum(1)
            d20, d21 = (v2 * v0).sum(1), (v2 * v1).sum(1)
            den = d00 * d11 - d01 * d01
            ok = np.abs(den) > 1e-9
            den = np.where(ok, den, 1.0)
            u, v = (d11 * d20 - d01 * d21) / den, (d00 * d21 - d01 * d20) / den
            if not (ok & (u >= -1e-3) & (v >= -1e-3) & (u + v <= 1 + 1e-3)).any():
                out.append((x, y))
        return out

    def _target(self, size):
        ctx = _context()
        if self.fbo is None or self.fbo.size != size:
            self.fbo = ctx.framebuffer(color_attachments=[ctx.texture(size, 4)], depth_attachment=ctx.depth_renderbuffer(size))
        return self.fbo

    def _sprite(self, surf):
        """A pygame Surface as a texture (cached by the surface itself: the same frame, the same texture)."""
        key = id(surf)
        got = self._sprites.get(key)
        if got is not None and got[0] is surf:
            return got[1]
        ctx, mgl = _context(), _CTX["mgl"]
        raw = pygame.image.tobytes(surf, "RGBA", False)
        tex = ctx.texture(surf.get_size(), 4, raw)
        tex.filter = (mgl.NEAREST, mgl.NEAREST)
        if len(self._sprites) > 400:
            for _k, (_s, t) in list(self._sprites.items())[:200]:
                t.release()
                self._sprites.pop(_k, None)
        self._sprites[key] = (surf, tex)
        return tex

    def render(self, size, cam, sprites=(), sky=(150, 190, 235), shadows=()):
        """The scene from cam (eye, target, fov degrees, up) at size (w, h): a pygame Surface. sprites: [(surface,
        (x, y, z) of its feet in tiles, height in tiles)] stood upright facing the camera; shadows: [(x, y, z)] the oval
        under someone's feet, lying on the ground."""
        ctx, prog = _context(), _CTX["prog"]
        fbo = self._target(size)
        fbo.use()
        ctx.enable(_CTX["mgl"].DEPTH_TEST | _CTX["mgl"].BLEND)
        ctx.blend_func = _CTX["mgl"].SRC_ALPHA, _CTX["mgl"].ONE_MINUS_SRC_ALPHA
        if self.indoor:
            sky = (0, 0, 0)
        fbo.clear(sky[0] / 255, sky[1] / 255, sky[2] / 255, 1.0, depth=1.0)
        mvp = _mvp(size, cam)
        prog["mvp"].write(mvp.T.astype("f4").tobytes())
        prog["tint"].value = (1.0, 1.0, 1.0)
        prog["alpha"].value = 1.0
        prog["glass"].value = 0
        light = []
        for kind, tex, vao in self.parts:
            if kind == 3:
                light.append((tex, vao))
                continue
            if kind == 2:
                ctx.depth_mask = False
            tex.use(0)
            prog["kind"].value = min(kind, 1) if kind == 4 else kind
            if kind == 4:   # (the backdrop past a street's edges: one-sided, seen only from inside, 11-21)
                ctx.enable(_CTX["mgl"].CULL_FACE)
            vao.render()
            if kind == 4:
                ctx.disable(_CTX["mgl"].CULL_FACE)
            ctx.depth_mask = True
        if shadows:
            self._draw_shadows(ctx, prog, shadows)
        if sprites:
            self._draw_sprites(ctx, prog, cam, sprites)
        if getattr(self, "_glass", None):   # (window panes after the solid and the people: they tint what's behind)
            ctx.depth_mask = False
            prog["glass"].value = 1
            for tex, vao in self._glass:
                tex.use(0)
                vao.render()
            prog["glass"].value = 0
            ctx.depth_mask = True
        if light:   # (after people too: a lamp's glow over whoever stands by it)
            ctx.depth_mask = False
            prog["kind"].value, prog["alpha"].value = 3, LIGHT_ALPHA
            for tex, vao in light:
                tex.use(0)
                vao.render()
            ctx.depth_mask = True
            prog["alpha"].value = 1.0
        raw = fbo.read(components=3)
        return pygame.transform.flip(pygame.image.frombuffer(raw, size, "RGB"), False, True)

    def _draw_sprites(self, ctx, prog, cam, sprites):
        eye, target = np.array(cam["eye"], "f4"), np.array(cam["target"], "f4")
        fwd = target - eye
        right = np.cross(fwd, np.array([0, 1, 0], "f4"))
        right /= max(1e-6, np.linalg.norm(right))
        prog["kind"].value = 1
        rows = []
        for surf, (x, y, z), h in sprites:
            if surf is None:
                continue
            w = h * surf.get_width() / max(1, surf.get_height())
            base = np.array([x, y, z], "f4")
            r = right * (w / 2)
            up = np.array([0, h, 0], "f4")
            a, b, c, d = base - r, base + r, base + r + up, base - r + up
            quad = np.array([[*a, 0, 1], [*b, 1, 1], [*c, 1, 0], [*a, 0, 1], [*c, 1, 0], [*d, 0, 0]], "f4")
            rows.append((surf, quad))
        rows.sort(key=lambda t: -float(np.linalg.norm(t[1][0, :3] - eye)))   # (far first)
        buf = ctx.buffer(reserve=6 * 5 * 4)
        vao = ctx.vertex_array(prog, [(buf, "3f 2f", "pos", "uv")])
        for surf, quad in rows:
            self._sprite(surf).use(0)
            buf.write(quad.tobytes())
            vao.render()
        vao.release(); buf.release()

    def _draw_shadows(self, ctx, prog, spots):
        """Each an oval on the ground (B2W2's: about two thirds of a tile across), darkening it as the shadow sheets do."""
        if "shadow" not in _CTX:
            img = pygame.Surface((32, 32), pygame.SRCALPHA)
            pygame.draw.ellipse(img, (0, 0, 0, 255), img.get_rect())
            _CTX["shadow"] = img
        quads = []
        for x, y, z in spots:
            a, b = 0.31, 0.2
            y += 0.03
            quads.append([[x - a, y, z - b, 0, 0], [x + a, y, z - b, 1, 0], [x + a, y, z + b, 1, 1],
                          [x - a, y, z - b, 0, 0], [x + a, y, z + b, 1, 1], [x - a, y, z + b, 0, 1]])
        buf = ctx.buffer(np.array(quads, "f4").tobytes())
        vao = ctx.vertex_array(prog, [(buf, "3f 2f", "pos", "uv")])
        self._sprite(_CTX["shadow"]).use(0)
        prog["kind"].value = 2
        ctx.depth_mask = False
        vao.render()
        ctx.depth_mask = True
        vao.release(); buf.release()

    def pick(self, size, cam, sx, sy, plane_y):
        """The point (tiles) on the level plane y = plane_y under screen point (sx, sy): (x, y, z), or None."""
        inv = np.linalg.inv(_mvp(size, cam))
        nx, ny = 2 * sx / size[0] - 1, 1 - 2 * sy / size[1]
        a = inv @ np.array([nx, ny, -1.0, 1.0]); b = inv @ np.array([nx, ny, 1.0, 1.0])
        a, b = a[:3] / a[3], b[:3] / b[3]
        if abs(b[1] - a[1]) < 1e-9:
            return None
        t = (plane_y - a[1]) / (b[1] - a[1])
        return tuple(a + (b - a) * t) if t >= 0 else None

    def project(self, size, cam, point):
        """Where a point (tiles) lands on the picture, (x, y) px, or None behind the camera."""
        p = _mvp(size, cam) @ np.array([point[0], point[1], point[2], 1.0])
        if p[3] <= 1e-6:
            return None
        return ((p[0] / p[3] + 1) * size[0] / 2, (1 - p[1] / p[3]) * size[1] / 2)


def _panes(rgba, reach=12):
    """A tall building's picture with its open window panes glazed (11-21): Black 2 cuts them out and sets an inner model
    behind, made for its fixed camera; ours swings round and looked through them to the street. A pane is a see-through
    texel (not the atlas's key colour) with the picture's own frame within `reach` texels on all four sides, so a
    railing's gaps, a tree's edge and unused space stay open."""
    a = rgba[..., 3] > 0
    hole = ~a & ~np.all(rgba[..., :3] == KEY, axis=-1)
    if not hole.any():
        return rgba
    h, w = a.shape
    near = []
    P = np.pad(a, reach)   # (frame looked for within reach; past the picture's edge counts as none, 11-21: a 7-wide picture)
    for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        hit = np.zeros_like(a)
        for k in range(1, reach + 1):
            hit |= P[reach + dy * k:reach + dy * k + h, reach + dx * k:reach + dx * k + w]
        near.append(hit)
    pane = hole & near[0] & near[1] & near[2] & near[3]
    if not pane.any():
        return rgba
    rgba = rgba.copy()
    rgba[pane] = GLASS
    return rgba


def _fix(kind, rgba, verts):
    """(kind, picture, corners) with what the export left out put back (see the top)."""
    rgba = np.array(rgba, dtype=np.uint8)
    rgba[np.all(rgba[..., :3] == KEY, axis=-1), 3] = 0
    if kind == 2:
        return kind, rgba, verts
    if kind in (0, 1) and len(verts) and float(verts[:, 1].max()) > 6.0:
        rgba = _panes(rgba)
    a = rgba[..., 3]
    seen = rgba[a > 0][:, :3]
    if not len(seen) or not (a == 0).any() or seen.min() < 190 or len(np.unique(seen, axis=0)) > 2:
        return kind, rgba, verts
    verts = verts.copy()
    for axis, col in ((1, 3), (0, 4)):   # (u: across the picture's width; v: down its height)
        lo_, hi_ = verts[:, col].min(), verts[:, col].max()
        if lo_ > -0.05 and 1.5 < hi_ < 2.1:   # (a quarter circle, mirrored into a whole one)
            rgba = np.concatenate([rgba, np.flip(rgba, axis=axis)], axis=axis)
            verts[:, col] /= 2
    return 3, np.ascontiguousarray(rgba), verts


def scene(game, zone):
    key = int(zone)
    if key not in _SCENES:
        _SCENES[key] = Scene(os.path.join(game.assets.assets_dir or "assets", "b2_3d", "%d.npz" % key)) if has_scene(game, key) else None
    return _SCENES[key]


def _mvp(size, cam):
    w, h = size
    fov = math.radians(cam.get("fov", 30.0))
    f = 1 / math.tan(fov / 2)
    near, far = 0.3, 400.0
    proj = np.array([[f * h / w, 0, 0, 0], [0, f, 0, 0], [0, 0, (far + near) / (near - far), 2 * far * near / (near - far)], [0, 0, -1, 0]], "f8")
    eye, target = np.array(cam["eye"], "f8"), np.array(cam["target"], "f8")
    up = np.array(cam.get("up", (0, 1, 0)), "f8")
    zax = eye - target; zax /= np.linalg.norm(zax)
    xax = np.cross(up, zax); xax /= max(1e-9, np.linalg.norm(xax))
    yax = np.cross(zax, xax)
    view = np.array([[*xax, -xax @ eye], [*yax, -yax @ eye], [*zax, -zax @ eye], [0, 0, 0, 1]], "f8")
    return proj @ view


def follow(px, py, pz, pitch_deg, dist, yaw_deg=0.0, fov=30.0):
    """A camera behind and above a point (tiles): looking down at pitch, from dist away, turned by yaw (0: from the
    south, looking north as the DS camera does)."""
    p, yw = math.radians(pitch_deg), math.radians(yaw_deg)
    back = (math.sin(yw) * math.cos(p), math.sin(p), math.cos(yw) * math.cos(p))
    eye = (px + back[0] * dist, py + back[1] * dist, pz + back[2] * dist)
    return {"eye": eye, "target": (px, py, pz), "fov": fov}
