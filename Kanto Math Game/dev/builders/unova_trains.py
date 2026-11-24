"""The Battle Subway's trains, cut from Black 2's own art (Unova batch 4b's close-out, 11-23).

    python dev/builders/unova_trains.py

Black 2 draws its trains as 3D models; the one picture of them laid flat is Anville Town's ground (assets/tiles/b2_ground/
418.png: two cars at the station). From it:
- assets/tiles/unova_rides/: the ride scenes' pictures, half size (the ride screen shows ten 16-pixel tiles): Anville with its
  track bare (anville.png), Gear Station's Brown Line platform (platform.png), the train standing up (train_v.png) and
  lying down (train_h.png). The ride scenes themselves are RIDE_SCENES in unova_area_data.json (b2_brown_out / b2_brown_back).
- assets/dungeon/characters/b2_train/: the train lying on a platform's track, cut into 32-pixel tiles (r<row>_c<col>.png),
  stood on each platform's track as "img:" pieces (unova.py PLATFORM_TRAIN)."""
import os
from PIL import Image

GAME = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
A = os.path.join(GAME, "assets")
TRAIN = (740, 1485, 860, 2048)        # (the two cars at Anville's station, in its ground picture)
TRACK = (740, 1000, 860, 1160)        # (a stretch of bare track just north of the bridge, to lay where the cars stood)
ROWS, COL0, COLS = (8, 12), 13, 18    # (a platform's track: rows 8-11, from column 13: Gear Station's platforms, zones 67-74)


def main():
    out = os.path.join(A, "tiles", "unova_rides")
    pieces = os.path.join(A, "dungeon", "characters", "b2_train")
    os.makedirs(out, exist_ok=True)
    os.makedirs(pieces, exist_ok=True)
    anv = Image.open(os.path.join(A, "tiles", "b2_ground", "418.png")).convert("RGBA")
    train = anv.crop(TRAIN)
    bare = anv.copy()
    strip = anv.crop(TRACK)
    for y in range(TRAIN[1], TRAIN[3], strip.height):
        bare.paste(strip.crop((0, 0, strip.width, min(strip.height, TRAIN[3] - y))), (TRAIN[0], y))
    half = lambda im: im.resize((im.width // 2, im.height // 2), Image.NEAREST)
    half(bare).save(os.path.join(out, "anville.png"))
    # (the train as a sprite: the cars only, the track and grass beside them cleared)
    t = train.copy()
    px = t.load()
    for y in range(t.height):
        for x in range(t.width):
            r, g, b, a = px[x, y]
            if x < 6 or x >= t.width - 6:   # (the ballast either side of the cars)
                px[x, y] = (0, 0, 0, 0)
    half(t).save(os.path.join(out, "train_v.png"))
    th = t.rotate(90, expand=True)
    half(th).save(os.path.join(out, "train_h.png"))
    plat = Image.open(os.path.join(A, "tiles", "b2_ground", "74.png")).convert("RGBA")
    half(plat).save(os.path.join(out, "platform.png"))
    # the waiting train, in tiles, on a platform's track (lying down, its front at the track's west end)
    band = Image.new("RGBA", (COLS * 32, (ROWS[1] - ROWS[0]) * 32))
    band.paste(th.crop((0, 0, min(th.width, band.width), th.height)), (0, (band.height - th.height) // 2))
    for r in range(ROWS[1] - ROWS[0]):
        for c in range(COLS):
            tile = band.crop((c * 32, r * 32, c * 32 + 32, r * 32 + 32))
            if tile.getbbox():
                tile.save(os.path.join(pieces, "r%d_c%d.png" % (r, c)))
    print("rides:", sorted(os.listdir(out)), "train pieces:", len(os.listdir(pieces)), "train", th.size)


if __name__ == "__main__":
    main()
