"""Route dungeons (the Mystery Dungeon style): a route, forest or cave walked on a grid of tiles.

    core.py   the rules, with no pygame (floors, turns, wild Pokemon that chase you, loot, TM spots),
              so they can be tested on their own and reused by a standalone game.
    recipes   assets/dungeon_routes.json: which areas are dungeons and how each one is built
              (floors, style, size, wild count, its loot table and TM spots).

The game's screen for it is src/states/overworld/dungeon.py (DungeonState, a PlayState).
"""
