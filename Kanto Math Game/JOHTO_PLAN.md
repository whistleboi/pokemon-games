# Johto: what it needs

Readers: Jordan, Claude and Grok. This list comes from reviewing the Kanto change log and auditing Johto's data and live game, as of 2026-10-20. The canon reference is HeartGold/SoulSilver (HGSS). Items marked **(verify)** are canon details to confirm on Bulbapedia before building.

## Status (2026-10-20)

Sections 1 to 7 are done (see CHANGELOG, "Johto teams, Silver and Red, League rematches"). Still open: the section 8 run-throughs and the section 9 full playthrough. The Orange Islands are built (see CHANGELOG).

## Kanto review: what Johto should match

Kanto is in good shape: 151/151 caught in Grok's playthrough, and Grok's bugs are fixed. Kanto got the following, so Johto should get the same:

| Kanto has | Johto status |
|---|---|
| Canon story gates (badges, key items, story events) | **Partly.** About 10 gates are missing (section 2). |
| Gym, Elite Four and Champion teams that match the real game | **Partly.** 7 teams differ from HGSS (section 3). |
| Exact real-game levels for the Champion | No. Johto uses calculated levels. |
| Rival teams that follow your starter | **Only the first battle** (section 4). |
| Per-town marts (no Rare Candy everywhere) | No. Every Johto mart sells Rare Candy (section 6). |
| "Kanto stays Kanto" (no later-region Pokémon until played) | The wild pools are clean (Gen 1–2 only). The Goldenrod store sells Gen 4–9 items (section 1). |
| League rules: a loss resets the run; rematches after the title | Indigo only (section 5). |
| Story beats with their own scenes (Fuji, Snorlax, Silph) | Mostly there. Red is missing (section 4). |
| A full playthrough test | Not done for Johto yet (section 9). |

Kanto leftovers, for the record:
- Levels: DONE. Real growth curves, with XP x3 for fast leveling (Jordan's call).
- Route 2 after Viridian Forest: keep as is (Jordan's call).

## 1. Decisions for Jordan (DONE)

1. **"Johto stays Johto"?** The wild pools already have no Pokémon past Gen 2. The Goldenrod Department Store does sell later-generation evolution items (Dawn Stone, Electirizer, Auspicious Armor…). Lock those until their regions are played, like Kanto's Up-Grade rule?
2. **Kanto after Johto:** in HGSS, Kanto opens after the Johto Champion, with 8 more Gyms. Here Kanto is already its own region. Is the plan "beat Johto, then the post-credits region select", or a direct HGSS-style trip through Route 27?
3. **Rival battle order:** the game's first Silver battle is an ambush in New Bark. In HGSS it's in Cherrygrove after Mr. Pokémon. Keep New Bark, or move it?

Answers: (1) yes, Johto stays Johto. (2) Kanto and Johto are linked by travel: after either title, a message says the road is open, and the S.S. Aqua and Magnet Train connect them. Picking the other one in Mom's region picker says to travel there instead. (3) Moved to Cherrygrove.

## 2. Canon gates that are missing (DONE, with HMs; see CHANGELOG)

| Gate | Now | HGSS |
|---|---|---|
| Azalea → Ilex Forest | Open | Needs Cut (**Hive Badge**) |
| Morty's Gym | Open | After the Burned Tower scene (rival battle + the three beasts flee) |
| Olivine → Route 40 (to Cianwood) | Open | Needs Surf (**Fog Badge**) |
| Jasmine's Gym | Open | After taking the SecretPotion from Cianwood to Amphy in the Lighthouse |
| Ecruteak → Route 42 → Mahogany | Open | Needs Surf (**Fog Badge**) |
| Pryce's Gym | Open | After the Rocket Hideout **(verify)** |
| Red Gyarados | Needs the Rocket HQ cleared (backwards) | Gyarados first, then Lance, then the Rocket HQ |
| Goldenrod Radio Tower takeover | Any time | After the 7th badge (Glacier) |
| Mahogany → Route 44 / Ice Path | Open | After the Radio Tower **(verify)** |
| New Bark → Route 27 (to Kanto) | `has_8_badges` counts **any** region's badges | 8 **Johto** badges (and the Johto Champion, for Kanto) |
| Mt. Silver | Open from the Mt. Silver hub | After the Johto Champion **and** 16 badges |

## 3. Teams that don't match HGSS (DONE: HGSS teams, levels scaled so Lance's ace is 63 like Kanto's Champion, plus HGSS rematch teams)

| Trainer | Now | HGSS |
|---|---|---|
| Falkner | Pidgey, Hoothoot, Pidgeotto | Pidgey, Pidgeotto |
| Morty | Gastly, Haunter, Gengar | Gastly, Haunter, Haunter, Gengar |
| Jasmine | Magnemite, **Magneton**, Steelix | Magnemite, Magnemite, Steelix |
| Clair | Dragonair, Dragonair, Kingdra | Gyarados, Dragonair, Dragonair, Kingdra |
| Will | Xatu, Jynx, Exeggutor, **Jynx**, Xatu | Xatu, Jynx, Exeggutor, **Slowbro**, Xatu |
| Karen | Umbreon, Murkrow, Gengar, **Kangaskhan**, Houndoom | Umbreon, **Vileplume**, Gengar, Murkrow, Houndoom |
| Lance | Gyarados, Aerodactyl ×2, Dragonite ×3 | Gyarados, Dragonite, **Charizard**, Aerodactyl, Dragonite, Dragonite |

Bugsy, Whitney, Chuck, Pryce, Koga and Bruno already match HGSS.
- **Exact levels:** set the HGSS levels on the leaders, Elite Four and Lance, as Kanto's Champion has.
- **Rematches:** add the HGSS rematch teams for the Elite Four and Lance after the title, as Kanto has its FireRed/LeafGreen rematch teams.

## 4. Rival (Silver) and Red (DONE)

- **Starter-based teams:** only the New Bark battle picks Silver's team from your starter. Azalea, Goldenrod Underground and Mt. Silver always use the Cyndaquil line. Add `team_choice` to each, as Sinnoh's Barry has.
- **Missing battles:** Burned Tower (Ecruteak) and Victory Road (before the League).
- **Mt. Silver:** Silver is there with a Tyranitar team, which isn't canon. Move that fight to Victory Road. Optionally add HGSS's post-game Mt. Moon rematches.
- **Red is missing.** "CHALLENGE RED" on Mt. Silver starts a wild **Tyranitar** boss. Make it a trainer battle against Red with his HGSS team: Pikachu 88, Lapras 80, Snorlax 82, Venusaur 84, Charizard 84, Blastoise 84. It should need 16 badges and the Johto title. (verified)

## 5. The Silver League (DONE, for every region's league)

- The Elite Four battle levels are right (42–47), but the League doesn't behave like Indigo:
  - A loss doesn't reset the run to Will.
  - There's no "Title Defense" or rematch mode after you win.
  - The gauntlet code only special-cases `INDIGO_PLATEAU`. Make it work for any region's league, which helps the other regions too.
- Check that beating Lance sets the Johto Champion flag and leads into the post-credits region select, as Kanto does.

## 6. Marts (DONE, normalized for every region)

- **Per-town stock:** give Johto marts HGSS-style per-town stock, as Kanto has. Rare Candy shouldn't be sold everywhere, and Revive should come later.
- **Goldenrod Department Store:** use HGSS's floors. Apply the section 1 decision about later-generation items.

## 7. Bugs found in the audit (DONE)

- **Dead buttons:** National Park's "Catch PKMN" and "Battle Trainers" do nothing, because town menus don't handle CATCH or BATTLE.
- **Odd area levels:**
  - Cliff Edge Gate is Lv 40, but the Safari Zone behind it is Lv 17.
  - Route 46 is Lv 3, but it leads into Dark Cave at Lv 17.
- **Two "CHALLENGE HO-OH" buttons on the Bell Tower:** one checks `has_rainbow_wing`, the other `has_RAINBOW_WING`. Keep one.
- **Blackthorn's travel buttons** use `can_exit`, a route-only condition, on a town.

## 8. Story beats to check end to end

Most of these exist in some form. Each needs a run-through to confirm it works and gates the right things:
1. Elm → Mr. Pokémon → Mystery Egg → Togepi.
2. Sprout Tower (Elder Li).
3. Slowpoke Well.
4. Kurt's Apricorn Balls.
5. Ilex Forest (the Farfetch'd chase is optional).
6. Sudowoodo and the SquirtBottle.
7. Burned Tower, and the roaming Raikou and Entei after it.
8. Kimono Girls → Clear Bell or Tidal Bell, and the Rainbow and Silver Wings.
9. Lighthouse and SecretPotion.
10. Lake of Rage → Lance → Rocket Hideout.
11. Radio Tower → Card Key / Director.
12. Ice Path.
13. Dragon's Den → Rising Badge.
14. Bug-Catching Contest.
15. Union Cave Lapras.
16. Ruins of Alph / Unown.
17. Day Care.
18. Celebi.

## 9. Testing

- **Full playthrough:** run a Grok-style Johto playthrough with the `dexplay/` harness from the Kanto run. Use visible buttons only, real catches, and both the Johto dex and the League. It found two crashes and a soft-lock in Kanto, so it's the best way to find Johto's.
- **Art:** the generic stand-in art covers Johto, so nothing shows blank. `ASSETS_NEEDED.md` lists Johto's own art still to make.

## Suggested order

1. Make the section 1 decisions.
2. Section 7 bugs, then section 2 gates. These are small data edits plus a little code.
3. Sections 3 and 4: teams, rival and Red (mostly data).
4. Section 5 League flow (code that helps every region).
5. Section 6 marts.
6. Section 8 run-throughs, then the section 9 full playthrough.
