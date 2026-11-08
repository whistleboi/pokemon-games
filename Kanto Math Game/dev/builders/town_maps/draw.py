"""Little helpers for laying out a map grid with rectangles (the bigger maps), then reading it out as rows."""


class Grid:
    def __init__(self, w, h, fill="."):
        self.w, self.h = w, h
        self.cells = [[fill] * w for _ in range(h)]

    def rect(self, x, y, w, h, ch):
        """Fill a rectangle (clipped to the map)."""
        for yy in range(max(0, y), min(self.h, y + h)):
            for xx in range(max(0, x), min(self.w, x + w)):
                self.cells[yy][xx] = ch
        return self

    def put(self, x, y, text):
        """Write characters left to right from (x, y)."""
        for i, ch in enumerate(text):
            if 0 <= x + i < self.w and 0 <= y < self.h:
                self.cells[y][x + i] = ch
        return self

    def building(self, x, y, w, h, letter, door_x=None):
        """A building's rectangle with its door in the bottom row (door_x: across from x, default the middle)."""
        self.rect(x, y, w, h, letter)
        dx = x + (w // 2 if door_x is None else door_x)
        self.cells[y + h - 1][dx] = "D"
        return self

    def rows(self):
        return ["".join(r) for r in self.cells]
