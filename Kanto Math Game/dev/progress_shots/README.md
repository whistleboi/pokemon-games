# Menu progress shots

Screenshots of the game's menus at eight commits, rendered headless at the fixed 1280x720 canvas.
Each menu has two images:

- `<menu>_timeline.png`: all eight commits, oldest to newest
- `<menu>_before_after.png`: the oldest commit (daffb82) next to the newest (b964151)

## Commits used

| Date | Commit | What it was |
|---|---|---|
| 2026-03-23 | daffb82 | Building out Kanto, started Johto (first commit of this engine) |
| 2026-04-12 | b10a887 | Last spring build (Hoenn started) |
| 2026-10-18 | ac5e891 | Any-region starts, playable Gen 3-9 regions |
| 2026-10-20 | 9134172 | Options, art, music, Mart rework |
| 2026-10-23 | 373f7ad | Stable playtest build synced into the repo |
| 2026-10-25 | b33a308 | UI redesign, Journeys art and music |
| 2026-10-26 | fc8d731 | UI redesign pass |
| 2026-10-27 | b964151 | Current HEAD (Orre, Orange Islands) |

Every menu rendered at every commit. The playtest copies weren't needed.

## What changed in each menu

**Main menu**: a black screen titled "KANTO MATH" with two blue buttons became "POKEMATH ADVENTURES" in April.
On 10-20 a red QUIT button was added, and LOAD GAME greys out when there's no save. The 10-25 redesign
added the POKéMATH logo, a map backdrop, a featured legendary (Zacian, then Solgaleo, now Mewtwo),
stacked green and grey buttons, and the tagline "Learn math, catch them all!".

**Character select**: a black screen with one trainer, "<" and ">" arrows, and a small name box, until 10-23.
The 10-25 redesign split it into a "Step 1 of 4" flow: a large trainer card on a green platform,
a Name panel with help text, and a NEXT button.

**Mart greeting**: the same Viridian Mart art throughout. The gold pixel-font text box became the
white rounded dialogue box on 10-25.

**Mart shop** (`src/states/systems.py`): in March the stock was evolution stones bought with Poké Balls,
in a pop-up list over the Mart art. In April and 10-18, a row of small blue item buttons ran along a
gold bar. On 10-20 the shop became a full-screen list with BUY/SELL tabs, item icons, the bag count,
and prices in Poké Dollars. On 10-25 it gained a blue header bar (EXIT, POKé MART, BUY, SELL, money),
white item cards in two columns, and a "What would you like?" box.

**Pokémon Center**: the same center art throughout. The nurse sprite was added on 10-20. The text box
changed with the 10-25 redesign, like the Mart's.

**Party**: blue name bars in a 2x3 grid with tiny icons, and a gold "Choose a PKMN." bar,
until 10-23. The 10-25 redesign added a green "POKéMON" header and white cards with large sprites,
names, levels, HP bars and HP numbers.

**Bag**: paged black screens ("EVOLUTION ITEMS" in March, "USEABLE ITEMS" from April, "ITEMS" by 10-23)
with blue item bars and "<"/">" arrows. The 10-25 redesign added an orange BAG header and six pocket tabs
(Items, Medicine, Poké Balls, Berries, TMs & HMs, Key Items). Potions now sit in the Medicine pocket,
so the Items pocket in the newer shots shows only Great Balls.

**Battle**: gold boxes and a gold "What will CHARIZARD do?" bar with MATH/PKDEX/PKMN/RUN. By April
PKDEX became BAG. Levels and HP numbers appeared on 10-20 and 10-23. The 10-25 redesign added slanted
white HP panels with an EXP bar and colored FIGHT/BAG/POKéMON/RUN buttons. The battle backdrop
changes between shots because of day/night and weather, not because of a code change.

## Notes

- The shots use a test save: player JORDAN in Viridian City (Kanto); party Charizard, Pikachu, Blastoise,
  Snorlax, Gyarados and Alakazam; ₽12,345; a few items; and a wild Pidgey.
- The town-themed Sinnoh/Unova Center and Mart backgrounds, and the shop change in
  `src/states/systems.py`, were uncommitted when these were taken, so the HEAD shots don't show them.
- The very first commit (ee6e082, 2026-02-13) holds two earlier, separate programs (Pokémath v1.3 and
  Pokemath Adventures v0.1, single-file scripts) that don't have this engine's menus, so it was left out.
- To retake: `tools/shoot.py <exported game dir> <out dir>` renders one commit,
  and `tools/compose.py` builds the sheets. Both scripts are in this folder.
