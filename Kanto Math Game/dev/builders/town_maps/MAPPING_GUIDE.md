# Mapping guide: making our walkable maps from the original pictures

This guide is for anyone, human or AI, who builds or redoes one of the game's walkable maps. Read it all before you start. The worked example is **Saffron City** (`saffron_city()` in `kanto.py`).

## The goal

Every town, route and cave is drawn in **our own style**. `src/dungeon/art.py` draws a grid of characters with simple shapes. Jordan chose this style on purpose, so every region looks the same even where we have no good pictures.

**The layout must match the original as exactly as possible.** Same size, and the same position for every building, road, path, fence, ledge, pond, tree line and way out. "Close enough" or "compacted" is not acceptable. Jordan reviews these hypercritically.

- **One tile = one tile of the original.** At 1x scale that's 16 px in FireRed/LeafGreen, HeartGold/SoulSilver and the Pokémon Journeys maps.
  - Saffron's picture is 1092 × 835 px, so Saffron is 69 × 53 tiles.
  - Don't shrink a map to make it "fit". Don't widen one either.
- **Sources, in order of preference:**
  1. Jordan's whole-town pictures in `assets/backgrounds/<region>/*.png`. The `routes/` and `towns/` subfolders are our own crops, not sources.
  2. Pictures Jordan gives you (for example `Downloads/Cinnabar_Island_FRLG.png`).
  3. The Pokémon Journeys V18 maps (render them with `dev/builders/render_journeys_backgrounds.py`'s `Journeys(...).render(map_id)`).
- **Ask Jordan before building** whenever something in the picture is unclear (which house is whose, what a structure is). Describe the layout and get an OK first.

## Files

| File | What it is |
|---|---|
| `dev/builders/town_maps/<region>.py` | One function per map, returning its rows (`def saffron_city(): ... return g.rows()`), plus the region's `MAPS` dict entry for each map. |
| `dev/builders/town_maps/draw.py` | `Grid(w, h, fill)`: `.rect(x, y, w, h, ch)`, `.put(x, y, text)`, `.building(x, y, w, h, letter, door_x=None)`, `.rows()`. |
| `dev/builders/build_town_maps.py` | Builds `assets/town_maps.json` and checks every map. Writes previews to `dev/builders/out/maps/<KEY>.png`. Run it after every change: `python dev/builders/build_town_maps.py` |
| `dev/tools/map_grid.py` | Measures a source picture (see Step 2). |
| `dev/tools/journeys_render.py` | Renders a Pokémon Journeys map at 32 px a tile, with labelled crops. |
| `dev/tools/tile_classify.py` | Sorts a picture's tiles into map characters by the share of each kind's exact colours (`?` where unsure). |
| `src/dungeon/art.py` | Draws the characters. Add a new ground type or prop here if the original needs one, and keep it in our style. |
| `assets/<region>_area_data.json` (Kanto: `pokemon_area_data.json`) | The area's options. A door opens the option whose `"door"` field matches the building's kind. |
| `src/states/overworld/walk_town.py` `LABELS` | The name shown over a door ("COPYCAT'S HOUSE"). |

## The characters

| Char | Meaning | Walkable? |
|---|---|---|
| `.` | grass ground (lawn) | yes |
| `d` | walking path of pale grass (FireRed/LeafGreen towns) | yes |
| `=` | sand path | yes |
| `s` | beach | yes |
| `"` | tall grass (wild Pokémon) | yes |
| `f` | flowers | yes |
| `a` | city road (gray) | yes |
| `p` | city sidewalk (brick; a curb is drawn where it meets `a`) | yes |
| `e` | pale stone pavement (plazas) | yes |
| `o` | open sea you Surf across (route maps) | with HM Surf |
| `T` | tree | no |
| `r` | rock (a grave in the `tower` theme) | no |
| `~` | water you can't cross | no |
| `#` | wooden fence (a ledge in the original becomes a fence with gaps) | no |
| `k` | white picket fence | no |
| `i` | blue iron railing | no |
| `c` | cliff, or a cave/building wall in themed maps | no |
| `q` | rock in the sea | no |
| `l` | lamp post | no |
| `m` | machine / console (desks, lockers, generators, counters) | no |
| `g` | stone gate wall with pillars (Route 23's badge gates) | no |
| `j` | white stone post | no |
| `y` | sofa | no |
| `z` | potted plant | no |
| `h` | fire hydrant | no |
| `!` | sign (its lines come from `"signs"`, in reading order) | no |
| `b` | boulder (Strength plus the slide puzzle moves it; route maps) | no, until moved |
| `< > ^ v` | way out (`"exits"` says where) | yes |
| `w`, `u` | water ways out (by Surf) | yes |
| `+`, `-` | ladder down, ladder up (maps with floors) | yes |
| `N` | someone standing (`"people"`, in reading order) | no |
| `X` | a trainer's own spot (`"trainer_spots"`, in reading order) | no |
| capital letter | a building: one rectangle per letter | no |
| `D` | a door, always in its building's bottom row (made by `g.building`) | no |

Reserved capitals: `T`, `D`, `N`, `X`. A big town can run out of free capitals. Saffron has 44 buildings, so its closed apartments use Greek and Cyrillic capitals written as escapes (`"Α"`). Any character where Python's `str.isupper()` is true works.

### Map entry keys (`MAPS["KEY"]`)

- `art`: the rows.
- `exits`: `{char or building letter: area key}`. A building letter's door leads out (a gatehouse).
- `buildings`: `{letter: kind}`, with kinds such as `center`, `mart`, `gym`, `house` (closed), `gate`, `cave`, or a `"door"` name from the area data.
- `roofs`: `{letter: [r, g, b]}`.
- `people`: a town option's text, or (route maps) a route option's text.
- `signs`: a list of line lists.
- `trainer_spots`.
- `locked`: `{kind: message}`.
- `theme`: `cave`, `ice`, `tunnel`, `ship` or `tower`.
- `floors`: a list of `{art, exits, signs, people}`, plus `floor_names` and `descend`.
  - **Ladders pair up in reading order.** The n-th `+` on a floor arrives at the n-th `-` on the next floor (and back), falling back to the first. Order the floors so this matches the original; Cerulean Cave is `[2F, 1F, B1F]`, and you start on the floor that holds the entrance.
  - A floor that is deliberately in separate parts, each reached by its own ladder (Cerulean Cave 2F), gets `"parts": True`, so the builder checks reachability from every ladder.
- `zone_rects`, `fog`, `dark`.

## The method, step by step (worked on Saffron)

### 1. Get the source and check its scale

Open the picture and confirm the tile size. Small things (a sign, a hydrant, a lamp) are 1 tile; a Pokémon Center is 5 tiles wide. Saffron: 16 px per tile, 1:1.

### 2. Measure it with the tool

```
python dev/tools/map_grid.py assets/backgrounds/kanto/saffron_city.png OUT --sample road=11,30
```

- `info.txt` gives the map size (69 × 53) and the grid phase. If the auto phase looks off, pass `--phase X,Y` (Saffron: `--phase 7,4`).
- `grid_q*.png` are zoomed crops with `i,j` labels every 4 tiles. **Read every position from these.**
- `mask.txt` marks every tile whose colour matches a sample tile (here the road at tile 11,30). That gives the road network exactly: copy it rather than eyeballing roads.

Check that the grid lines fall on building edges. If they don't, fix the phase before reading anything.

### 2b. Pokémon Journeys maps

```
python dev/tools/journeys_layout.py MAP_ID OUT
```

This reads the map's own data (passages, terrain tags, events) and writes `layout.txt`, `events.txt` and `map.png` (32 px a tile). Be careful with it:

- Some Journeys tilesets have **empty passage and terrain tables**; everything reads as walkable. Route 23, Victory Road and Cerulean Cave all use "Inside Cave". When `layout.txt` comes out all `.`, use the colour pass below instead.
- **Events can be unfinished.** Cerulean Cave's ladders warp to placeholder towns, and Victory Road has no events at all. Use the events for *positions* only, and link floors the way FireRed/LeafGreen does.

The colour pass works on the rendered `map.png`:
1. Sample a tile of each kind (floor, wall, water, sand, rock).
2. Classify every tile by its share of pixels near each sample's colour, and by its share of dark pixels (boulders and ledge edges are dark-outlined).
3. Print the result and overlay it on the picture (red squares on the tiles you call blocked). Check the overlay by eye before trusting it.

Small round things are easier found by brightness than by eye: Route 23's white posts were found by counting near-white pixels per tile.

Ledges in caves are dark lines. Make them walls, then open a one-tile gap where the original lets you hop down.

### 3. Read the layout, feature by feature

Write down, for every feature, its tile rectangle `(x, y, w, h)`:

- The edge: tree lines, cliffs, railings.
- Ground types: roads from the mask, sidewalks, paths, sand, grass, water. **Walking paths matter most.** They guide players, so trace them tile by tile with a colour mask. FireRed/LeafGreen towns draw their paths as pale grass (`d`) with darker lawn (`.`) around the houses; Pallet Town is the example.
- Every building, separately (adjacent apartments are separate buildings), and where its door is.
- Ways out: gatehouses, path ends, water.
- Props: signs, lamps, hydrants, fences/ledges, rocks, flowers.

**Rounding rule:** a feature spanning pixel tiles 18.6 to 22.6 occupies tiles `round(18.6)` to `round(22.6) - 1`, so 19..22. Be consistent.

Saffron's readings, for example:
- The Magnet Train station is x 10..18, y 7..14, with its door at x 16.
- Silph Co. is x 30..39, y 19..30, with its door at x 35.
- The main road is rows 17–18.
- The plaza in front of Silph is x 30..39, rows 33..35.
- The left railing is column 8 and the right railing column 61, each with a gap at rows 37..41 for the west and east gates.

### 4. Write the map function

Start from the fill (`Grid(69, 53, "T")`), then paint in this order:
1. Ground (sidewalk everywhere in the city).
2. Roads.
3. Railings and fences.
4. Buildings.
5. Props.

Comment each block with what it is. See `saffron_city()`.

- **Doors:** `g.building()` puts a `D` in the bottom row (`door_x` picks the column). A building whose front faces a wall or railing, like Saffron's bottom row of apartments, gets `g.rect(...)` with no door.
- **Gatehouse at the top edge:** a building with its door at the bottom (`exits: {"A": "KANTO_ROUTE_5"}`).
- **Gatehouse at the bottom or sides:** a doorless block, with the way-out characters in front of it.

### 5. Wire it up

- Give every building letter a kind, and a roof colour if it needs one.
- For a building that opens something (Copycat, the Dojo, the Magnet Train):
  - add `"door": "<kind>"` to that option in the area's data;
  - add the kind to `LABELS` in `walk_town.py`.
- Story people go in `people` (town: an explore option's text, or an option of its own as a dict; route maps: a `route_menu` option's text).
- Signs go in reading order (top to bottom, then left to right).

### 6. Build and fix

```
python dev/builders/build_town_maps.py
```

The builder stops on:
- rows of different widths;
- a building that isn't a rectangle;
- a building with no kind;
- `N` / `!` / `X` counts that don't match `people` / `signs` / `trainer_spots`;
- a way out, door, sign or person you can't reach.

"Out of reach" is usually a prop or a hydrant in front of a door, or a gap that's one tile too narrow. Fix the map; don't weaken the check.

### 7. Compare side by side

```
python dev/tools/map_compare.py PICTURE MAP_KEY OUT.png --tile 16 --phase X,Y
```

Use `--tile 32 --phase 32,32` for a Journeys `map.png`.


Put the original and `dev/builders/out/maps/<KEY>.png` next to each other at the same scale. The preview is 28 px a tile, so scale it to the source's 16 px. Check:
- every building;
- every road edge;
- every way out;
- every prop.

Then fix what's off and compare again. Only then show Jordan.

### 8. Play it

Walk it headless (see `dev/checks/dungeon_body.py`'s walked-town section). Check that:
- you arrive at the right spot from each neighbour;
- every door opens the right thing;
- every way out leads to the right place.

Then run the checks that touch it:
```
bash dev/checks/run_all.sh
```
Or for just the maps:
```
cat dev/checks/harness_head.py dev/checks/dungeon_body.py > dev/checks/out/check_dungeon.py
python dev/checks/out/check_dungeon.py dev/checks/out
```
It should end with `##### 0 failures`.

## Pitfalls we've hit

- **Line endings:** match each file's. Many are CRLF. Patch them with a Python script that keeps CRLF, never `sed` (Git Bash's `sed` strips it).
- **Escapes and quoting:** Bash heredocs mangle backslash escapes (`Α`) and quotes. Write patch scripts to a file and run them.
- **JSON data files:** they're hand-formatted. Insert text; never re-serialize the whole file.
- **Doors and props:** a door's tile must be reachable from the front. Don't put a hydrant, lamp or sign right in front of one.
- **Route maps (not towns):** `people` must be the exact text of a `route_menu` option. That option's conditions decide when the person shows.
- **Floors:** each floor of a cave or building is its own `art`. Ladders: `+` goes down, `-` goes up. Keep `descend` and `floor_names` right.
- **Nothing walled in:** don't leave walkable pockets that can't be reached (items can land there). The builder checks ways out and doors, not every tile.
- **No `TRAVEL` button:** boats and trains open from a door (a travel option with a `"door"` field).

## Handing work back

- Deliver the changed `<region>.py` (and any data or `LABELS` edits) as a patch.
- Include the side-by-side image, the builder's output, and a short list of anything you weren't sure about.
- Claude reviews each map against its source before it's merged. Jordan approves layouts.


## The map maker (dev/tools/map_maker.py)

A window for drawing a map by hand in this same format (Jordan, 11-14), made first for the regions that only exist in 3D:
lay the 3D area's top-down picture underneath (Reference) and design the 2D map over it.

- `python dev/tools/map_maker.py [KEY | layout.json] [--ref=picture.png] [--size=WxH]`. Open and Load (and the park builder's Load...) pop up a file window at the saved maps folder, `dev/builders/town_maps/made`; a key typed in the Open box opens with Enter.
- Paint, Box and Fill with any character from the drop lists (each shows its picture as the game draws it). Right-click picks up what's under the mouse.
- Buildings: pre-made at the game's usual sizes. Pick one to change its kind, name, size, door position or roof colour. A tile-sheet house's custom roof is saved as `{"roof": [r, g, b], "tint": true}`, and `art.py` tints the house picture for it.
- Pick a way out to fill in "Leads to". Right-click a person or a sign to say who they are or what it says.
- Height levels (L0-L3) are the map maker's own guide. "Cliffs from levels" lays real cliffs where the ground steps down
  (dev/tools/cliff_tiers.py): a higher level's south edge gets its whole face (lip, face, base: 3 rows of that level),
  its west and east edges a column of rock side, its north edge the lip; ends round off, corners join, inside corners turn,
  tiers stand on one another, and a path crossing a cliff becomes stairs. The rock tiles become c (in the way) and the
  tiles to draw go in the map's roofs "_cliffs" (tile set rock_bp, Banished Platinum's). Trees, buildings and water keep
  their tile: a cliff runs on hidden under the woods, so paint the woods at the level of the ground beside them. Change
  the levels and press it again: the last cliffs are cleared first.
- The park builder (its button, or P) swaps the panel for pictures of everything in tabs (Buildings, Scenery, Ground, Height, Ways out), each sorted into groups (Centers & Marts, Houses, Trees & plants, Statues, Signs & lamps...) and by the tile set it came from: the group chips, a search box, and lists of tile set (artist), theme (Town, Tropical, Forest, Desert, Snow...) and generation narrow the pictures together. Scenery's Stairs group gathers every staircase (assets/tiles/stairs: the cliff builder's stone stairs as cliff crossings and flights, SoulSilver's cave stairs, Platinum's indoor stairs); stairs are walked on, not in the way, and may be placed across a cliff to cut a way through. Its Paths & ground group holds ready-made patches of sand, paving, dirt, grass, snow and water from the tile artists' sheets: they lie under everything else and are walked on (water patches are in the way). The Mounds group holds rock mounds, 2 to 6 tiles wide, in the cliff builder's own rock (in the way, like a boulder). The Stairs group has stone flights and cliff crossings 2 or 3 tiles wide. The Ground tab paints ground that draws its own edges: sand, dirt, gravel, brick and white stone paths, light and tall grass, the sea (a sand, wooden or earth shore), a beach in the sea, and lava. Each painted tile picks its corner, edge or middle from its eight neighbours (RPG Maker autotiles, `assets/tiles/autotiles`, drawn by art.py from the map's roofs "_paint"). Painted ground walks as its own character (sand path =, sea o, tall grass ", ...) and runs on under pieces placed on it. Its brush is 1, 3 or 5 tiles wide, or Box (drag out a rectangle) or Fill (paint the whole stretch of like ground joined to the tile you click). Plain grass rubs paint out. The Ledges group's ledge is dragged along: a run across the map hops south; a run up or down hops toward the lower ground (by the levels), else dragged down hops east and dragged up hops west; an L-shaped run turns its corner; F flips the last one. The park builder offers only the games' and tile artists' pictures (the map maker's own drawn buildings, scenery and ground stay in the classic panel). Right-click a picture to hide it (dev/builders/pieces/hidden.json); the Hidden button shows hidden ones, right-click again to bring one back. A piece's group, theme and generation come from its spec, else are guessed from its name. The roof colours show only for a chosen building and the source picture's controls fold away under Picture. Pieces from the Pokemon Ultimate Tileset Collection are cut by kanto_handoff/tileset_catalog/auto_import.py into dev/builders/pieces/tc_<artist>.json sets. The games' own buildings (FireRed / LeafGreen, HeartGold / SoulSilver, Diamond / Pearl / Platinum, Black 2 / White 2) come from kanto_handoff/tileset_catalog/game_sets.py as assets/tiles/game_<game> and are listed first in the tile set list; the map maker's own drawn pieces are "Our own art". Click a picture or drag it onto the map: a see-through copy follows the mouse, green where it fits, red where it doesn't; click again for another, right-click or Esc to empty your hand. Drag anything placed to move it; right-click takes it away. Ground and height are 1/3/5-tile brushes; raising or lowering the ground rebuilds the cliffs when you let go. The Height tab also has Box (drag a rectangle) and Fill (the whole stretch at one level joined to the tile you click). Draw a terrace edge at its level, then fill inside it to raise the whole terrace. Stairs only where a path runs across a cliff; a path running along under one is covered by the rock. A source picture (the layout to follow) goes with the map: Load..., or drop the picture file on the window; it lies at its actual size (32 px a tile, as the pieces are drawn); the Size button steps through 32 px a tile, 16 px a tile (GBA screenshots) and stretched over the map; Remove takes it off the map (Ctrl+Z puts it back; a save then leaves it out); Fit map sizes the map to it (16 px a tile, again for 32), Move / size frames it against the map (drag it; the wheel sizes it, Ctrl only wider, Shift only taller; arrows nudge, Shift+arrows a whole tile; Keep shape puts its own proportions back, Reset stretches it over the map again), its mode button cycles On top, Underneath (the map see-through over it) and Tracing layer (only what you've put down drawn over the picture; plain lawn stays clear); Strength fades it. It's saved with the map (`_maker` ref).
- Saves to `dev/builders/town_maps/made/<KEY>.json`. The build takes it in as region `made` (last, so it replaces a region's map with the same key) and checks it like any other.
