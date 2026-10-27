# Assets needed

Art the game still uses a stand-in for. Drop a file in with the name shown, and point the data at it if needed.

## Trainer sprites (`assets/sprites/trainers/`, 80×80 PNG, transparent background)

| File | Character | Used in | Stand-in now | Notes |
|---|---|---|---|---|
| `celosia.png` | Team Flare Scientist Celosia (X/Y) | Kalos: Poké Ball Factory, Lysandre Labs | `scientist.png` | Not on Pokémon Showdown's trainer sprites (checked 2026-10-27). |
| `aliana.png` | Team Flare Scientist Aliana (X/Y) | Kalos: Kalos Power Plant, Lysandre Labs | `scientist.png` | Not on Pokémon Showdown's trainer sprites (checked 2026-10-27). |
| `onare.png` | Glitterati Billy & O'Nare (Scarlet/Violet) | Paldea: Apple Hills (Kitakami) | `gentleman.png` | Not on Pokémon Showdown's trainer sprites (checked 2026-10-27). |
| `honey.png` | Dojo Matron Honey (Sword/Shield, Isle of Armor) | Galar: Isle of Armor (Battle Honey) | `beauty.png` | Not on Pokémon Showdown's trainer sprites (checked 2026-10-27). |

### Orre (Colosseum / XD)

Orre's named trainers all borrow a generic class sprite. Set the new file as the trainer's `sprite` in `assets/orre_area_data.json`.

| File | Character | Used in | Stand-in now |
|---|---|---|---|
| `evice.png` | Cipher Head Evice | Realgam Tower | `gentleman.png` |
| `greevil.png` | Grand Master Greevil | Citadark Isle | `gentleman.png` |
| `exol.png` | Cipher Cmdr Exol | ONBS | `gentleman.png` |
| `dakim.png` | Cipher Admin Dakim | Realgam Tower | `blackbelt.png` |
| `ein.png` | Cipher Admin Ein | Realgam Tower | `scientist.png` |
| `venus.png` | Cipher Admin Venus | The Under | `beauty.png` |
| `gorigan.png` | Cipher Admin Gorigan | Cipher Key Lair | `blackbelt.png` |
| `lovrina.png` | Cipher Admin Lovrina | Cipher Lab | `beauty.png` |
| `mirorb.png` | Miror B. | Pyrite Town | `guitarist.png` |
| `vander.png` | Mt. Battle Master Vander | Mt. Battle | `blackbelt.png` |
| `nascour.png` | Cipher Nascour (Colosseum) | Realgam Tower | `gentleman.png` |
| `snattle.png`, `ardos.png`, `eldes.png` | Cipher Admins Snattle, Ardos and Eldes (XD) | Citadark Isle | `gentleman.png` |
| `gonzap.png` | Snagem Head Gonzap | Desert Trail (Snagem Hideout) | `roughneck.png` |
| `cipherpeon_m.png`, `cipherpeon_f.png` | Cipher Peons (Peon Litnar, Peon Remil and the Phenac Peons) | Phenac City, The Under | `roughneck.png`, `biker.png` |

Orre's other trainers (Thug Brock, Streetler Dax, Scrapper Kit, Outlaw Rusty, Rider Vex, Nomad Ilda, Medium Sora, Civilian Mona, Pree Champion Justy and the Area trainers) use class sprites that fit, so they aren't listed.

**Sources checked:**
- Pokémon Showdown: not checked yet for Orre (the site was down on 2026-10-27).
- MajinCubyan's "Gen II Custom Orre Trainers" (PokéCommunity, 2017): free to use, with credit to MajinCubyan. The sprites are Game Boy Color style (4 colors, 56×56, grey background), so they clash with our DS-era art. It has Miror B., the Cipher Peons (M/F) and Justy, but none of the admins or bosses. Use it only as a last resort.
