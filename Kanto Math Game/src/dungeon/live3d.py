"""Live 3D (11-20, Jordan: Castelia's camera, "Live 3D camera"): a place's own Black 2 models drawn every frame from a
moving camera on the graphics card, as the DS does: the view tilts and swings as you walk (the avenue's rail cameras,
the streets' camera strips). PC only: it needs moderngl (an OpenGL 3.3 card); without it, or headless, the baked
picture stays (available() says which).

Scenes: assets/b2_3d/<zone>.npz (kanto_handoff/unova_map_tools/export3d.py): per texture its picture, its triangles'
corners (x, y up, z, in tiles from the zone's top-left, the walk grid's units) and its kind (0 ground, 1 building,
2 shadow sheet). People are drawn into the same scene as upright sprites (billboards), so buildings hide them.

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
in vec2 v_uv;
in float v_y;
out vec4 color;
void main() {
    vec4 c = texture(tex, v_uv);
    if (c.a < 0.5) discard;
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
            tex = ctx.texture((rgba.shape[1], rgba.shape[0]), 4, np.ascontiguousarray(rgba).tobytes())
            tex.filter = (mgl.NEAREST, mgl.NEAREST)
            tex.repeat_x = tex.repeat_y = True
            vbo = ctx.buffer(verts.tobytes())
            vao = ctx.vertex_array(prog, [(vbo, "3f 2f", "pos", "uv")])
            self.parts.append((kind, tex, vao))
        self.parts.sort(key=lambda p: (p[0] == 2) + 2 * (p[0] == 3))   # (shadow sheets after the solid, light sheets last)
        self._flat = np.concatenate(solid)[:, :, [0, 2]] if solid else np.zeros((0, 3, 2), "f4")   # (seen from above: for covers())
        self._covers = {}
        self.lo, self.hi = lo, hi
        self.cam = np.array(data["cam"], "f4") if "cam" in data.files else None   # (export3d.camera: Black 2's camera here)
        self.fbo = None
        self._sprites = {}

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
        fbo.clear(sky[0] / 255, sky[1] / 255, sky[2] / 255, 1.0, depth=1.0)
        mvp = _mvp(size, cam)
        prog["mvp"].write(mvp.T.astype("f4").tobytes())
        prog["tint"].value = (1.0, 1.0, 1.0)
        prog["alpha"].value = 1.0
        light = []
        for kind, tex, vao in self.parts:
            if kind == 3:
                light.append((tex, vao))
                continue
            if kind == 2:
                ctx.depth_mask = False
            tex.use(0)
            prog["kind"].value = kind
            vao.render()
            ctx.depth_mask = True
        if shadows:
            self._draw_shadows(ctx, prog, shadows)
        if sprites:
            self._draw_sprites(ctx, prog, cam, sprites)
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


def _fix(kind, rgba, verts):
    """(kind, picture, corners) with what the export left out put back (see the top)."""
    rgba = np.array(rgba, dtype=np.uint8)
    rgba[np.all(rgba[..., :3] == KEY, axis=-1), 3] = 0
    if kind == 2:
        return kind, rgba, verts
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
