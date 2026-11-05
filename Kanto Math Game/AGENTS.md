# AGENTS.md

Notes for AI coding agents working on this game.

## What it is
A Pygame Pokémon game where battles are won by answering math problems. Nine regions (Kanto to Paldea) plus side regions (Sevii, Orange Islands, Orre, and others).

## Run and check
- Run the game: `python main.py`
- Run all checks: `bash dev/checks/run_all.sh`. It should end with `##### 0 failures`. The `ValueError: test` from batch5 is deliberate.
- Headless checks use `SDL_VIDEODRIVER=dummy` and `SDL_AUDIODRIVER=dummy`.

## Layout
- `src/core`: the game loop, asset loading, music.
- `src/states`: screens (overworld, battle, menus, Bag/PC/Pokédex, and so on).
- `src/pokemon`: species, moves, abilities, TMs, breeding, evolution.
- `src/world`: story flags and saves (`story.py`), levels, HMs.
- `src/ui`: buttons, panels, dialogue, theme.
- `src/dungeon` + `src/states/overworld/dungeon.py`: route dungeons (areas in `assets/dungeon_routes.json` are walked on a map). `PlayState(game)` hands back a `DungeonState` there (`PlayState.__new__`); `PlayState(game, classic=True)` is always the old route screen. Headless, dungeons stay off unless `game.dungeon_routes = True` (see `dev/checks/dungeon_body.py`).
- `assets/*_area_data.json`: each region's areas, buttons, trainers and wild Pokémon (`pokemon_area_data.json` is Kanto).
- `dev/builders`: scripts that made the data. Some are out of date (Sevii's), so check before re-running one.
- `dev/checks`: the check suite. `dev/tools`: one-off tools. `dev/reference`: reference pictures the game doesn't load.
- Android (Pydroid 3): `ANDROID.md`, `src/core/android.py`, and `dev/tools/make_android_copy.py`. Keep the code Python 3.11 compatible (the suite compiles it with 3.11) and avoid pygame-ce-only functions.

## Rules
- Commit and push only when asked.
- Local saves (`game_data*.json`) and their backups stay out of git.
- Match the file's line endings: some files are CRLF and some are LF.
- Game text is short, in our own words.
- Credit asset and data sources in `CREDITS.md`.
