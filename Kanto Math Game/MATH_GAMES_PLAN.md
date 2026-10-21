# Math mini-games for gym battles: options and how to add them

Readers: Jordan, Claude and Grok. This is a plan only: nothing here is built yet. Written 2026-10-21.

## The idea

Every battle turn asks the same kind of question: a sum, four answer buttons. Gym battles could ask in different ways instead: pop bubbles, catch falling comets, flip memory cards. The math stays K–3 and the battle rules stay the same. A right answer lands the move, a quick one earns a bonus, and a wrong one is a weak hit.

## What's out there (inspiration only)

| Project | What it does | Licence / notes |
|---|---|---|
| [TuxMath (Tux, of Math Command)](https://en.wikipedia.org/wiki/Tux,_of_Math_Command) | Missile Command style: solve the sum on a falling comet before it lands. Also *Factoroids* (factors and fractions). | Free/open source (C/SDL, rewritten in JavaScript in 2022). |
| GCompris ([overview](https://www.linuxjournal.com/index%2Ephp/node/1008912)) | Big suite for ages 2–10: counting, guess the number, dot-to-dot, money, +/−/× fact quizzes, arithmetic memory cards, grid patterns. | Free/open source (Qt). |
| [BubbleMath](https://github.com/rlv-dan/BubbleMath/blob/master/README.md) | Pygame: shoot bubbles whose numbers add up to a target. | Python 2; licence not stated. |
| pySioGame ([article](https://ubuntuhandbook.org/index.php/tag/pysiogame/)) | Pygame activity pack for ages 3+: mostly maths, plus letters, colours and memory. | Old; check the licence. |
| [Math Runner](https://takitechgames.itch.io/math-runner) | Run and jump into the cube with the right answer. | Not confirmed open source. |

**Rule: take mechanics, not code or art.** Game mechanics are free to reuse, but the code and assets of these projects are under licences like the GPL, or no stated licence at all. Copying them would put this game under those terms. Each mini-game here should be written fresh in our own style, like `src/states/gym_puzzles.py`.

## Candidate games

Effort key:
- **S:** works with today's four-button answer panel; only the question changes.
- **M:** needs its own small panel.
- **L:** needs animation or timing.

| # | Game | Inspired by | How a turn plays | Math | Fits | Effort |
|---|---|---|---|---|---|---|
| 1 | **Missing Number** | GCompris quizzes | `7 + ? = 12`: pick the missing number. | Addition/subtraction facts, inverse ops | Any gym; good default | S |
| 2 | **Bigger or Smaller** | GCompris | Two cards (`6 + 5` vs `12`): tap the bigger one. | Comparing | Ice/Water (Pryce, Misty) | S |
| 3 | **Count the Pokémon** | GCompris counting | 3–12 small sprites on screen: how many? | Counting, subitising | Bug/early gyms (Bugsy, Brock) | S |
| 4 | **Number Patterns** | Tanoby puzzle | `2, 4, 6, ?` | Skip counting | Dragon (Clair, Drake) | S |
| 5 | **Make 10** | ten-frame drills | Pick the number that makes 10 with 7. | Number bonds | Fighting (Chuck, Bruno) | S |
| 6 | **What Time Is It?** | GCompris clock | A drawn clock face; pick the time. | Telling time (hours, half hours) | Psychic (Sabrina, Will) | S/M |
| 7 | **Poké Mart Change** | GCompris money | Pay exactly ₽8 with coins; tap coins until it's right. | Money, adding small values | Normal (Whitney, Lenora) | M |
| 8 | **Bubble Target** | BubbleMath | Pop bubbles until they add up to the target. | Multi-addend sums | Water (Misty, Cissy) | M |
| 9 | **Memory Match** | GCompris memory | Flip cards to pair `3 + 4` with `7`. One pair per turn. | Fact fluency, memory | Ghost (Morty, Agatha) | M |
| 10 | **Number Line Hop** | classroom number lines | A Pokémon hops along a 0–20 line; land on the answer. | Number line, +/− as moves | Ground (Giovanni, Clay) | M |
| 11 | **Shape Sides** | GCompris geometry | Pick the shape with 5 sides, or count corners. | Shapes | Rock/Steel (Brock, Jasmine) | M |
| 12 | **Comet Command** | TuxMath | Sums fall from the sky; tap the answer before they land. More speed means a better bonus. | Speed with facts | Flying/Electric (Falkner, Surge) | L |
| 13 | **Answer Runner** | Math Runner | The Pokémon runs; jump into the lane with the right answer. | Speed with facts | Electric (Surge, Elesa) | L |
| 14 | **Berry Fractions** | Factoroids | Cut a berry into halves or quarters; pick the picture showing ½. | Simple fractions (Grade 2–3) | Grass (Erika) | M |
| 15 | **Times Tables Blast** | TuxMath / Factoroids | Like Comet Command with × facts, for higher math levels. | Multiplication | Fire (Blaine) | L |

The gym puzzles already in the game (Surge's cans, Koga's footprints, the Orange Crew challenges, Sevii braille...) can serve as models for 2, 3, 4 and 5.

## How to build it cleanly

### 1. One small interface, one folder

`src/math_games/` with one file per game and a registry. Each game is pure logic: no drawing, a seeded `rng`, and testable headless, the same way `gym_puzzles.make_step` is.

```python
class MathGame:
    key = "missing_number"
    title = "Missing Number"
    panel = "choices"          # "choices" = today's 4-button panel; or the game's own panel class

    def make_round(self, rng, level):
        """-> Round(prompt, picture, options, answer); level comes from math_levels.json."""

    def check(self, round, picked):
        """-> True/False (Bubble Target and Poké Mart Change take several taps before checking)."""
```

`REGISTRY = {g.key: g for g in (MissingNumber(), BiggerSmaller(), ...)}`.

### 2. One hook in the battle

Battles already get their question in one place (`generate_math_set` → `game.math.generate(level)`) and score it in one place (`TrainerBattleState._answer_feedback`). The hook:

- When a battle has a `math_game`, ask that game for the round instead of `game.math.generate`.
- For **S** games, the round is still `(problem, answer, options)`, so `MathBattleUI` shows it unchanged.
- **M/L** games supply their own panel (a `UIElement`, like `MathBattleUI`). It calls the same callback with right/wrong.
- `_answer_feedback` would take a correct/wrong result instead of a button index. That's a small refactor, after which every game shares the existing rules: the weak roll on a wrong answer, the quick-answer bonus, the "Nice try!" feedback and the read-aloud button.

The battle rules don't change, only how the question is asked.

### 3. Choosing which game

- **Themed:** a gym's data names its game, for example `"gym": {"math_game": "memory_match", ...}`, so Morty is always Memory Match. Leaders could also mix 2–3 games across their team.
- **Random:** wild and route-trainer battles pick from a pool, weighted toward the S games so turns stay quick.
- **Options:** a "Battle games" setting, saved like the level-cap mode: Classic (today), Themed (gyms only) or Mixed (everywhere).
- Difficulty keeps coming from `story.get_math_level()`; each game maps the level to its own ranges (bigger sums, half hours vs hours, more bubbles).

### 4. Accessibility and feel

- Each game needs a read-aloud line (`speech.math_words`) and must work with the keyboard (arrows and Enter), like today's panel.
- No timers on **S/M** games. **L** games use gentle speeds that slow down after a wrong answer, and they can be turned off in Options.
- A one-screen "How to play" card the first time a game appears. Pictures over words for the youngest players.

### 5. Tests

Each game gets a headless test, like `check_ui`:
- 200 seeded rounds per level.
- The right answer is always among the options, and the options are unique.
- No impossible rounds (negative answers, a target bubbles can't reach).
- `check()` agrees with the answer.

A battle test plays one turn of each game through the hook.

## Suggested order

1. Refactor `_answer_feedback` to take a correct/wrong result, and add the registry plus the battle hook with Classic as the default. Nothing changes for players yet.
2. The five **S** games (Missing Number, Bigger or Smaller, Count the Pokémon, Number Patterns, Make 10), themed for the gyms in the table.
3. Options setting (Classic / Themed / Mixed).
4. **M** games: Memory Match, Bubble Target, Poké Mart Change, Number Line Hop, What Time Is It?
5. **L** games: Comet Command, Answer Runner, then Times Tables Blast for the highest math levels.
