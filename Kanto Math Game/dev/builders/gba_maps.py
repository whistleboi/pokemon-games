"""Read the maps of a FireRed- or Emerald-based GBA ROM hack (Jordan, 11-04) and draw them.

The ROM is only read as data (nothing in it is run). The formats are the ones the pokefirered and
pokeemerald decompilations document: map groups -> map headers -> layouts (size, block data, two
tilesets) -> metatiles (2 x 2 tiles, two layers) -> 4bpp tiles and 16-colour palettes.

    rom = Rom(path); maps = MapReader(rom)
    maps.groups()          -> [[header offset, ...], ...]
    maps.name(section)     -> "Nuvema Town" (the region map's name for a map's section)
    maps.render(header)    -> a pygame Surface, 16 px per metatile (scale=2: 32 px, like Journeys)
    maps.grass(header)     -> rows of True where a metatile is tall grass
"""
import struct

import pygame

# game code -> where the pointer to the map groups is stored, the primary tileset's tile/metatile
# count, its palette count, where the pointer to the map names is stored (FireRed: a list of name
# pointers; Emerald: the region map's entries, 8 bytes each, the name pointer last), the first named
# section, the tileset's metatile attribute field and size
ENGINES = {
    "BPRE": {"groups": 0x5524C, "prim": 640, "prim_pals": 7, "names": 0xC0C94, "name_step": 4, "name_at": 0,
             "first_section": 0x58, "attrs": 0x14, "attr_size": 4, "behavior": 0x1FF},
    "BPEE": {"groups": 0x84AA4, "prim": 512, "prim_pals": 6, "names": 0x123B44, "name_step": 8, "name_at": 4,
             "first_section": 0, "attrs": 0x10, "attr_size": 2, "behavior": 0xFF},
}
TALL_GRASS = (0x02, 0x03)  # metatile behaviours: tall grass, long grass

# The games' text encoding (enough for map names).
CHARS = {0: " ", 0xAB: "!", 0xAC: "?", 0xAD: ".", 0xAE: "-", 0xB4: "'", 0xB8: ",", 0xBA: "/", 0x1B: "e"}
CHARS.update({0xA1 + i: str(i) for i in range(10)})
CHARS.update({0xBB + i: chr(65 + i) for i in range(26)})
CHARS.update({0xD5 + i: chr(97 + i) for i in range(26)})


class Rom:
    def __init__(self, path, engine=None):
        with open(path, "rb") as f:
            self.data = f.read()
        self.code = self.data[0xAC:0xB0].decode("latin1")
        self.engine = engine or self.code  # a hack with its own game code: say which engine it uses

    def u8(self, o):
        return self.data[o]

    def u16(self, o):
        return struct.unpack_from("<H", self.data, o)[0]

    def u32(self, o):
        return struct.unpack_from("<I", self.data, o)[0]

    def s32(self, o):
        return struct.unpack_from("<i", self.data, o)[0]

    def ptr(self, o):
        """A ROM pointer as an offset in the file, or None if it isn't one."""
        if o is None or not 0 <= o <= len(self.data) - 4:
            return None
        v = self.u32(o)
        return v - 0x08000000 if 0x08000000 <= v < 0x08000000 + len(self.data) else None

    def text(self, o, limit=40):
        out = ""
        for b in self.data[o:o + limit]:
            if b == 0xFF:
                return out
            if b not in CHARS:
                return None
            out += CHARS[b]
        return None

    def lz77(self, o):
        """GBA BIOS LZ77 (type 0x10) data, unpacked."""
        d = self.data
        if d[o] != 0x10:
            raise ValueError("not LZ77 data")
        size = d[o + 1] | d[o + 2] << 8 | d[o + 3] << 16
        out = bytearray()
        i = o + 4
        while len(out) < size:
            flags = d[i]
            i += 1
            for bit in range(8):
                if len(out) >= size:
                    break
                if flags & (0x80 >> bit):
                    n = (d[i] >> 4) + 3
                    disp = ((d[i] & 0xF) << 8 | d[i + 1]) + 1
                    i += 2
                    for _ in range(n):
                        out.append(out[-disp])
                else:
                    out.append(d[i])
                    i += 1
        return bytes(out[:size])


class MapReader:
    MAX_SIDE = 400  # a layout bigger than this isn't a real map (a pointer read past a table's end)

    def __init__(self, rom):
        self.rom = rom
        self.cfg = ENGINES[rom.engine]
        self.groups_at = rom.ptr(self.cfg["groups"])
        self._tilesets = {}

    def groups(self):
        """[[map header offset, ...], ...]: each group's maps, up to the first one that isn't. A
        group's list ends where the next group's starts (the ROM keeps no counts; they sit in a row)."""
        rom, out, starts = self.rom, [], []
        while len(starts) < 64:
            gp = rom.ptr(self.groups_at + 4 * len(starts))
            if gp is None:
                break
            starts.append(gp)
        for k, gp in enumerate(starts):
            later = [s for s in starts if s > gp]
            limit = min(400, (min(later) - gp) // 4) if later else 400
            maps = []
            while len(maps) < limit:
                hp = rom.ptr(gp + 4 * len(maps))
                if hp is None or not self.valid(hp):
                    break
                maps.append(hp)
            if not maps:
                break
            out.append(maps)
        return out

    def valid(self, header):
        try:
            lay = self.layout(header)
        except (struct.error, TypeError, IndexError):
            return False
        return (0 < lay["w"] <= self.MAX_SIDE and 0 < lay["h"] <= self.MAX_SIDE
                and None not in (lay["blocks"], lay["prim"], lay["sec"]))

    def layout(self, header):
        rom = self.rom
        lo = rom.ptr(header)
        return {"w": rom.s32(lo), "h": rom.s32(lo + 4), "blocks": rom.ptr(lo + 12), "prim": rom.ptr(lo + 16),
                "sec": rom.ptr(lo + 20), "section": rom.u8(header + 0x14), "type": rom.u8(header + 0x17)}

    def name(self, section):
        """The region map's name for a map section ("Nuvema Town"), or None."""
        at = self.cfg["names"]
        table = self.rom.ptr(at) if at is not None else None
        i = section - self.cfg["first_section"]
        if table is None or not 0 <= i < 256:
            return None
        p = self.rom.ptr(table + self.cfg["name_step"] * i + self.cfg["name_at"])
        return self.rom.text(p) if p is not None else None

    def tileset(self, off):
        if off not in self._tilesets:
            rom, cfg = self.rom, self.cfg
            tiles_p, pals_p = rom.ptr(off + 4), rom.ptr(off + 8)
            tiles = rom.lz77(tiles_p) if rom.u8(off) else rom.data[tiles_p:tiles_p + 0x8000]
            pals = [[_color(rom.u16(pals_p + 32 * p + 2 * c)) for c in range(16)] for p in range(16)]
            self._tilesets[off] = {"tiles": tiles, "pals": pals, "metas": rom.ptr(off + 12),
                                   "attrs": rom.ptr(off + cfg["attrs"])}
        return self._tilesets[off]

    def _metatile_source(self, lay, m):
        """(tileset, index in it) of metatile m of this layout."""
        n = self.cfg["prim"]
        return (self.tileset(lay["prim"]), m) if m < n else (self.tileset(lay["sec"]), m - n)

    def behavior(self, lay, m):
        ts, i = self._metatile_source(lay, m)
        if ts["attrs"] is None:
            return 0
        size = self.cfg["attr_size"]
        o = ts["attrs"] + i * size
        raw = self.rom.u32(o) if size == 4 else self.rom.u16(o)
        return raw & self.cfg["behavior"]

    def blocks(self, header):
        lay = self.layout(header)
        w, h = lay["w"], lay["h"]
        return lay, [[self.rom.u16(lay["blocks"] + 2 * (y * w + x)) & 0x3FF for x in range(w)] for y in range(h)]

    def grass(self, header):
        lay, rows = self.blocks(header)
        seen = {}
        return [[seen.setdefault(m, self.behavior(lay, m) in TALL_GRASS) for m in row] for row in rows]

    def render(self, header, scale=1):
        lay, rows = self.blocks(header)
        prim, sec = self.tileset(lay["prim"]), self.tileset(lay["sec"])
        np = self.cfg["prim_pals"]
        pals = prim["pals"][:np] + sec["pals"][np:13] + [[(0, 0, 0)] * 16] * 3
        tiles, metas = {}, {}

        def tile(idx, pal, hf, vf):
            key = (idx, pal, hf, vf)
            if key not in tiles:
                src, i = (prim["tiles"], idx) if idx < self.cfg["prim"] else (sec["tiles"], idx - self.cfg["prim"])
                surf = pygame.Surface((8, 8), pygame.SRCALPHA)
                raw = src[i * 32:(i + 1) * 32]
                if len(raw) == 32:
                    colors = pals[pal]
                    for y in range(8):
                        for x in range(8):
                            b = raw[y * 4 + x // 2]
                            c = (b >> 4) if x & 1 else (b & 0xF)
                            if c:
                                surf.set_at((x, y), colors[c])
                tiles[key] = pygame.transform.flip(surf, hf, vf) if (hf or vf) else surf
            return tiles[key]

        def metatile(m):
            if m not in metas:
                ts, mi = self._metatile_source(lay, m)
                surf = pygame.Surface((16, 16))
                surf.fill(pals[0][0])
                for layer in range(2):
                    for q in range(4):
                        v = self.rom.u16(ts["metas"] + mi * 16 + (layer * 4 + q) * 2)
                        surf.blit(tile(v & 0x3FF, (v >> 12) & 0xF, bool(v & 0x400), bool(v & 0x800)),
                                  ((q % 2) * 8, (q // 2) * 8))
                metas[m] = surf
            return metas[m]

        img = pygame.Surface((lay["w"] * 16, lay["h"] * 16))
        for y, row in enumerate(rows):
            for x, m in enumerate(row):
                img.blit(metatile(m), (x * 16, y * 16))
        return img if scale == 1 else pygame.transform.scale(img, (img.get_width() * scale, img.get_height() * scale))


def _color(v):
    """A GBA BGR555 colour as RGB."""
    return ((v & 31) * 255 // 31, (v >> 5 & 31) * 255 // 31, (v >> 10 & 31) * 255 // 31)
