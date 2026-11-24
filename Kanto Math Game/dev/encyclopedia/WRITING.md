# Writing a walkthrough part (region/encyclopedia)

The game's own walkthrough, in the layout of Bulbapedia's FireRed/LeafGreen walkthrough. Tables and battle boxes come
from the game's data (`facts.py`); the words between them are written by hand, one file per part:
`dev/encyclopedia/<region>/partNN.html`. `build.py` puts them together into one page.

## The rules (Jordan's)

- **Every fact comes from the game's own data or code.** Read the place's fact sheet (`facts.py` writes
  `sheets/<AREA>.txt`), and where a sheet isn't enough, the code (see "Where things live"). **Anything you can't confirm
  is left out.** Never fill a gap from memory of FireRed, Bulbapedia or anywhere else.
- **All text in our own words.** Don't copy Bulbapedia's wording (its saved pages in `pokemon-games/sources/FRLG`,
  "Walkthrough_..._Part N", show the layout and the order of places only). Don't paste NPC lines either: say what
  they tell you, briefly (the sample: "A boy near the ledges points out that hopping down them is the quickest way back").
  Journal text is the one exception: it goes in its box with `{{journal:ID}}`, word for word, by the builder.
- **"Ours"**: mark anything FireRed doesn't have with `<span class="ours">ours</span>` (the tables do this themselves
  for Headbutt trees and later regions' Pokémon). Examples: Headbutt, the Shiny Charm from Oak, move tutors that sell
  TMs, HGSS / Yellow extras. Only tag it when you're sure FireRed lacks it; otherwise leave the tag off.
- Plain, friendly English for a young player; short paragraphs. "You", present tense. Pokémon with the accent.
  The rival is "your rival" (his name is the player's choice); he's Professor Oak's grandson.

## The layout of a part (copy part01.html's style)

```
<!--title: Route 6 and Vermilion City-->
<h2 data-place="KANTO_ROUTE_6">Route 6</h2>
<p>Intro: what the place is, where it leads, what's new here.</p>
{{tables:KANTO_ROUTE_6}}          Available Pokémon + Items, side by side
<p class="small">a short note under the tables if needed (Headbutt needs the Rocky Helmet, etc.)</p>
{{trainers:KANTO_ROUTE_6}}        the trainers on the map, as a table
<h3>A building or a scene</h3>
<p>...</p>
{{trainers:VERMILLION_CITY:Vermilion Gym}}   one room's trainers (the room title as in the sheet's "## ROOM x: Title")
{{battle:VERMILLION_CITY:Lt. Surge}}          a story battle box (Leader, rival, Rocket boss), found by name
{{journal:m6}}                                 the Journal mission's own text, in its box
```

- One `<h2 data-place="KEY">` per place (KEY = the area key, e.g. `CERULEAN_CITY`). When a place comes back in a later
  part (a second visit), use a plain `<h2>` with words like "Cerulean City (again)" and no data-place, or the same
  data-place: the first one in the page becomes the link target.
- `<h3>` per building or scene, `<h4>` per floor. The contents box is made from the h2/h3 headings.
- Place names in `<p>` text are linked to their sections by the builder: just write the name.
- Boxes you can write by hand: `<div class="note"><b>Title.</b> text</div>`.
- Markers: `{{tables:KEY}}`, `{{wild:KEY}}`, `{{items:KEY}}`, `{{items:KEY:Room title}}`, `{{trainers:KEY}}`,
  `{{trainers:KEY:Room title}}`, `{{battle:KEY:Name}}`, `{{battle:KEY:Name|a short line under it}}`, `{{journal:ID}}`.
  `{{tables:KEY}}` lists every item of the place (rooms included), so use it once per place.
- The Items table's "When" column: the builder words a few conditions itself. To say when for an item it can't, add a line
  to `<region>/when_partNN.json`: `{"AREA:ITEM_KEY:where": "After the Thunder Badge"}` (where = the room title as in the
  sheet, or `outside`).

## Building and checking

```
python dev/encyclopedia/facts.py ALL <scratch dir>          # fact sheets: <scratch dir>/sheets/<AREA>.txt
python dev/encyclopedia/build.py kanto <scratch>/test.html 5 6   # only parts 5 and 6 (part 1 always comes too)
```

The build stops on a marker it can't fill (a misspelt key, a battle name it can't find): fix and rebuild. Match the
files' LF line endings; check the file has no NUL bytes after writing.

## Where things live (when the sheet isn't enough)

- `assets/pokemon_area_data.json` (Kanto) / `assets/sevii_area_data.json`: `STORY_PROGRESSION[AREA]` (trainer_pool,
  gym, route_menu, explore_options, on_enter_event, area_boss), `GAME_CONFIG.JOURNAL_MISSIONS`, `GAME_TEXT` (what
  people with `"action": "NPC"` say).
- `assets/town_maps.json[AREA]`: people, signs, scenes, rooms, hidden items, barred tiles (what blocks the way, and until when).
- Story code: `src/world/story.py`, `src/world/story_events.py`, `src/world/kanto_lab.py`, `src/world/kanto_safari.py`,
  `src/states/overworld/town_story.py`, `src/states/overworld/common.py`; HMs and badges `src/world/hms.py`.
- Levels: `src/world/levels.py` (wild = area level -2..+1); fishing `src/states/overworld/route_actions.py`.
- `pokemon-games/kanto_handoff/KANTO_INVENTORY.md`: a record of what Kanto got. Useful to know what exists, but check
  each fact against the data before writing it.
