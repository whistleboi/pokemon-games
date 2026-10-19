# [REF-0070: Math Engine]
"""
One place that makes every math question in the game.

Difficulty levels live in assets/math_levels.json so new regions can add
new kinds of math (fractions, decimals...) without touching game states.

The player picks a level (or AUTO) per save file. AUTO follows the story:
the current region + badges earned in that region choose the level.

This module deliberately has no pygame import so it can be unit-tested.
"""
import json
import random

AUTO = "AUTO"

# Used only if math_levels.json is missing or broken, so the game never crashes.
_FALLBACK_CONFIG = {
    "symbols": {"add": "+", "sub": "-", "mul": "x", "div": "÷"},
    "levels": [
        {
            "id": 2, "name": "GREAT BALL", "desc": "Add & subtract up to 20",
            "ops": {"add": 1, "sub": 1},
            "add": {"max_sum": 20, "min_term": 1},
            "sub": {"max_start": 20, "min_term": 1},
            "formats": {"solve": 3, "missing": 1},
        }
    ],
    "auto": {"DEFAULT": [[0, 2]]},
}


def _weighted_pick(weights):
    """weights: {"key": weight}. Returns a key."""
    keys = [k for k, w in weights.items() if w > 0]
    return random.choices(keys, weights=[weights[k] for k in keys])[0]


class MathEngine:
    def __init__(self, config_path=None):
        config = None
        if config_path:
            try:
                with open(config_path, "r", encoding="utf-8-sig") as f:
                    config = json.load(f)
            except Exception as e:
                print(f"✗ Could not load math levels ({e}); using fallback.")
        if not config or not config.get("levels"):
            config = _FALLBACK_CONFIG

        self.symbols = {**_FALLBACK_CONFIG["symbols"], **config.get("symbols", {})}
        self.levels = sorted(config["levels"], key=lambda lv: lv["id"])
        self.level_by_id = {lv["id"]: lv for lv in self.levels}
        self.auto_table = config.get("auto", {})

    # ------------------------------------------------------------------
    # Level selection
    # ------------------------------------------------------------------
    @property
    def min_level(self):
        return self.levels[0]["id"]

    @property
    def max_level(self):
        return self.levels[-1]["id"]

    def clamp_level(self, level_id):
        """Snap any number to the nearest real level id."""
        try:
            level_id = int(level_id)
        except (TypeError, ValueError):
            return self.min_level
        if level_id in self.level_by_id:
            return level_id
        return min(self.level_by_id, key=lambda i: abs(i - level_id))

    def auto_level(self, region, badges_in_region):
        table = self.auto_table.get(region) or self.auto_table.get("DEFAULT") or [[0, self.min_level]]
        chosen = table[0][1]
        for min_badges, level_id in sorted(table):
            if badges_in_region >= min_badges:
                chosen = level_id
        return self.clamp_level(chosen)

    def resolve_level(self, setting, region="KANTO", badges_in_region=0):
        """setting is AUTO or a level id. Returns a concrete level id."""
        if setting == AUTO or setting is None:
            return self.auto_level(region, badges_in_region)
        return self.clamp_level(setting)

    def describe(self, setting, region="KANTO", badges_in_region=0):
        """Short label for UI, e.g. 'AUTO (GREAT BALL)'."""
        level = self.level_by_id[self.resolve_level(setting, region, badges_in_region)]
        if setting == AUTO or setting is None:
            return f"AUTO ({level['name']})"
        return level["name"]

    # ------------------------------------------------------------------
    # Question generation
    # ------------------------------------------------------------------
    def generate(self, level_id, num_options=3):
        """
        Returns (problem_str, correct_answer, options).
        Same contract the old generate_math_set() had, so every caller
        (catching, battles, starter pick, PokeMath Infinite) keeps working.
        """
        level = self.level_by_id[self.clamp_level(level_id)]
        op = _weighted_pick(level["ops"])
        a, b, c = self._make_fact(op, level)
        fmt = _weighted_pick(level.get("formats", {"solve": 1}))
        sym = self.symbols[op]

        if fmt == "missing":
            if random.random() < 0.5:
                problem, ans = f"? {sym} {b} = {c}", a
            else:
                problem, ans = f"{a} {sym} ? = {c}", b
            options = self._number_options(ans, num_options, op, (a, b, c))
        elif fmt == "equation":
            problem = f"{c} = ?"
            ans = f"{a} {sym} {b}"
            options = self._equation_options(op, a, b, c, level, num_options)
        else:
            problem, ans = f"{a} {sym} {b} = ?", c
            options = self._number_options(ans, num_options, op, (a, b, c))

        random.shuffle(options)
        return problem, ans, options

    def _make_fact(self, op, level):
        """Returns (a, b, c) where 'a op b = c' is true and all are whole numbers."""
        p = level.get(op, {})
        if op == "add":
            max_sum = max(4, p.get("max_sum", 20))
            lo = p.get("min_term", 1)
            c = random.randint(2 * lo, max_sum)
            a = random.randint(lo, c - lo)
            return a, c - a, c
        if op == "sub":
            max_start = max(4, p.get("max_start", 20))
            lo = p.get("min_term", 1)
            a = random.randint(2 * lo, max_start)
            b = random.randint(lo, a - lo)
            return a, b, a - b
        tables = p.get("tables", [2, 5, 10])
        max_factor = p.get("max_factor", 10)
        min_factor = p.get("min_factor", 2)
        if op == "mul":
            t = random.choice(tables)
            n = random.randint(min_factor, max_factor)
            a, b = (t, n) if random.random() < 0.5 else (n, t)
            return a, b, a * b
        if op == "div":
            divisor = random.choice(tables)
            quotient = random.randint(min_factor, max_factor)
            return divisor * quotient, divisor, quotient
        raise ValueError(f"Unknown op {op}")

    def _number_options(self, ans, num_options, op, fact):
        """Wrong answers that are close enough to make the player think."""
        a, b, c = fact
        candidates = [ans + d for d in (-3, -2, -1, 1, 2, 3)]
        if ans >= 20:
            candidates += [ans - 10, ans + 10]
        if op == "mul" and ans == c:
            # Classic slips: one row off in the times table.
            candidates += [a * (b + 1), a * (b - 1), (a + 1) * b, (a - 1) * b]
        candidates = [x for x in set(candidates) if x >= 1 and x != ans]
        random.shuffle(candidates)
        options = [ans] + candidates[: num_options - 1]
        # Safety net: always return exactly num_options distinct numbers.
        filler = ans + 4
        while len(options) < num_options:
            if filler not in options:
                options.append(filler)
            filler += 1
        return options

    def _equation_options(self, op, a, b, c, level, num_options):
        """Other equations that do NOT equal c (all still whole-number valid)."""
        sym = self.symbols
        correct = f"{a} {sym[op]} {b}"
        options = [correct]
        seen_values = set()
        for _ in range(200):
            if len(options) >= num_options:
                break
            d = random.choice([-2, -1, 1, 2])
            if op in ("add", "sub"):
                kind = random.randint(1, 3)
                x, y, o = a, b, op
                if kind == 1:
                    x += d
                elif kind == 2:
                    y += d
                else:
                    o = "sub" if op == "add" else "add"
                if x < 1 or y < 1 or (o == "sub" and x <= y):
                    continue
                value = x + y if o == "add" else x - y
                text = f"{x} {sym[o]} {y}"
            elif op == "mul":
                x, y = (a + d, b) if random.random() < 0.5 else (a, b + d)
                if x < 1 or y < 1:
                    continue
                value, text = x * y, f"{x} {sym['mul']} {y}"
            else:  # div: keep it divisible, just change the quotient
                q = c + d
                if q < 1:
                    continue
                value, text = q, f"{b * q} {sym['div']} {b}"
            if value == c or text in options or value in seen_values:
                continue
            seen_values.add(value)
            options.append(text)
        # Extremely unlikely, but never return too few buttons.
        k = 1
        while len(options) < num_options:
            text = f"{c + k} {sym['add']} {k}"
            if text not in options:
                options.append(text)
            k += 1
        return options
