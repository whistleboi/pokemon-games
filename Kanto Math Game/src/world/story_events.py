"""Story NPC buttons in towns and routes: dialogue, an optional battle, gifts and the story flag.

Each entry is keyed by the button's "target". Fields (all optional):
  lines     GAME_TEXT key(s) or literal lines shown first
  requires  menu conditions that must all hold (flags, "has_<x>_badge", ...)
  fail      lines shown when a requirement is missing
  done      lines shown once the event's flag is already set
  flag      story flag set when the event finishes (the battle's victory flag)
  battle    trainer: name, class, sprite, team, team_choice (by the region starter),
            dialogue {player_won, player_lost}, rewards {item: qty, "POKEMON_<id>": 1},
            level (the ace's level; otherwise from the area)
  gift_item {item: qty} given straight away ("balls" adds Poke Balls)
  gift_pokemon  species id, or {starter id: species id}
  gift_level    the gift's level (default: the area's wild level)
"""

GRUNT_G = {"name": "Galactic Grunt", "class": "GRUNT", "sprite": "galactic_grunt.png"}
GRUNT_P = {"name": "Plasma Grunt", "class": "GRUNT", "sprite": "plasma_grunt.png"}


def _t(base, **kw):
    out = dict(base)
    out.update(kw)
    return out


EVENTS = {
    # ---------------- Sinnoh (Brilliant Diamond / Shining Pearl) ----------------
    "professor_rowan": {
        "lines": ["Professor Rowan: Hm. So you're the one who met me at Lake Verity.",
                  "Your Pokemon looks happy with you. Then take this Pokedex.",
                  "Record every Pokemon you meet. Sinnoh is wider than you think."],
        "flag": "received_pokedex_sinnoh",
        "done": ["Professor Rowan: Fill that Pokedex! Every page is a lesson."]},
    "rowan_assistant": {
        "lines": ["Dawn: The Professor asked me to show you how to catch Pokemon.",
                  "Weaken it first, then throw a Poke Ball. The more it's hurt, the easier!",
                  "Here, take these to get started."],
        "gift_item": {"balls": 5}, "flag": "rowan_assistant_balls",
        "done": ["Dawn: Catch lots of Pokemon, okay? The Professor will be thrilled!"]},
    "poketch_company": {
        "lines": ["Pokétch Company President: You found all three of our clowns? No? Ah, never mind!",
                  "Here, take a Pokétch. It's a watch, a calculator, and so much more!"],
        "flag": "got_poketch",
        "done": ["President: How's the Pokétch? We'll have new apps soon!"]},
    "looker": {"lines": ["sinnoh_looker_intro"], "flag": "met_looker"},
    "looker_veilstone": {"lines": ["sinnoh_looker_galactic_tip"]},
    "gts_building": {"lines": ["The Global Trade Station is buzzing with trainers from far away.",
                               "Trades will open up once the link is finished. Come back later!"]},
    "galactic_jubilife": {
        "lines": ["sinnoh_galactic_jubilife"], "flag": "galactic_jubilife_cleared",
        "battle": _t(GRUNT_G, team=[41, 431],
                     dialogue={"player_won": ["Galactic Grunt: Ugh! Retreat! Back to Eterna!"]})},
    "galactic_windworks_grunt": {
        "lines": ["Galactic Grunt: The Valley Windworks belongs to Team Galactic now!",
                  "You want in? You'll need this key... if you can take it!"],
        "flag": "got_works_key",
        "done": ["The grunts ran off to the Valley Windworks on Route 205. Stop them there!"],
        "battle": _t(GRUNT_G, team=[434, 41], rewards={"WORKS_KEY": 1},
                     dialogue={"player_won": ["Galactic Grunt: Fine! Take the Works Key and see if we care!"]})},
    "galactic_eterna": {
        "lines": ["The Team Galactic Eterna Building. Grunts stand guard at the door...",
                  "Commander Jupiter: You came all the way up here? How adorable."],
        "flag": "galactic_eterna_cleared",
        "battle": {"name": "Commander Jupiter", "class": "COMMANDER", "sprite": "galactic_grunt.png",
                   "team": [41, 435], "is_boss_battle": True,
                   "dialogue": {"player_won": ["Jupiter: ...We're leaving. We have what we came for.",
                                               "The stolen Clefairy was rescued from the building!"]}}},
    "rad_rickshaw": {
        "lines": ["Rad Rickshaw: Thanks for chasing off Team Galactic!",
                  "Take this Bicycle. Ride it with pride!"],
        "gift_item": {"BICYCLE": 1}, "flag": "got_bicycle_sinnoh",
        "done": ["Rad Rickshaw: How's that Bicycle treating you?"]},
    "amity_square": {"lines": ["Amity Square: small Pokemon can walk alongside their trainers here.",
                               "Your partner sniffs around happily. It found nothing... this time."]},
    "cynthia_hm": {"lines": ["sinnoh_cynthia_hm"], "flag": "received_hm_cut"},
    "day_care": {"lines": ["Day Care Lady: We raise Pokemon for trainers on the go.",
                           "Come back when you have a Pokemon you'd like us to look after!"]},
    "solaceon_reporter": {"lines": ["Reporter: There are strange ruins just north of town.",
                                    "They say the Unown inside spell out words... spooky, right?"]},
    "celestic_ruins": {"lines": ["sinnoh_cynthia_celestic"]},
    "celestic_elder": {"lines": ["sinnoh_celestic_elder"]},
    "old_charm_delivery": {"lines": ["sinnoh_old_charm_deliver"], "flag": "delivered_old_charm"},
    # BDSP: after the Mine Badge, Rowan meets you and your rival here; then Lake Valor explodes.
    "canalave_library": {
        "stages": [{"requires": ["has_mine_badge"], "flag": "canalave_library_meeting",
                    "lines": ["Professor Rowan is waiting on the library's top floor with {rival_name}.",
                              "Professor Rowan: Sinnoh's myths speak of three lake Pokémon: Uxie, Mesprit and Azelf.",
                              "Professor Rowan: Team Galactic is after them. We must each watch a lake.",
                              "BOOM! The whole library shakes!",
                              "A sailor runs in: 'An explosion! Over at Lake Valor!'",
                              "Professor Rowan: {player_name}, go to Lake Valor at once!"]}],
        "done": ["Canalave Library. One book is called 'Sinnoh's Myth'.",
                 "'Three Pokemon were born from the Original One: two of time and space, one of antimatter.'",
                 "'Then three more were born to give the world spirit: knowledge, emotion and willpower.'"]},
    "sunyshore_lighthouse": {"lines": ["Vista Lighthouse. From the top you can see the Pokemon League across the sea.",
                                       "Volkner sometimes comes up here when the Gym gets boring."]},
    "roark_mine": {
        "lines": ["A man in a hard hat is breaking boulders deep in the mine.",
                  "Roark: Hm? A new face! I'm Roark, the Oreburgh Gym Leader.",
                  "My Pokemon and I dig up fossils here between challenges.",
                  "If you want a Gym battle, meet me back at the Gym. I'll be waiting!"],
        "flag": "met_roark"},
    "galactic_lake_verity": {
        "lines": ["sinnoh_mars_intro"], "requires": ["galactic_lake_valor_cleared"],
        "fail": ["Team Galactic grunts block the way to the lake."], "flag": "galactic_lake_verity_cleared",
        "battle": {"name": "Commander Mars", "class": "COMMANDER", "sprite": "mars.png", "team": [42, 436, 432],
                   "levels": [37, 37, 39],
                   "is_boss_battle": True, "dialogue": {"player_won": ["sinnoh_mars_won"]}}},
    # BDSP (Serebii's lake pages): Saturn has already taken Azelf but battles you in Valor Cavern;
    # Jupiter has taken Uxie and beaten your rival, and doesn't battle. The Galactic Key is in the
    # Veilstone warehouse underpass.
    "saturn_lake_valor": {
        "lines": ["Lake Valor has been drained. Only a muddy crater is left.",
                  "Deep in Valor Cavern, Commander Saturn turns around.",
                  "Saturn: You're too late. Azelf is already ours. But since you came all this way..."],
        "requires": ["canalave_library_meeting"], "flag": "galactic_lake_valor_cleared",
        "battle": {"name": "Commander Saturn", "class": "COMMANDER", "sprite": "saturn.png", "team": [64, 436, 454],
                   "levels": [35, 35, 37], "is_boss_battle": True,
                   "dialogue": {"player_won": ["Saturn: Well fought. But Azelf is already ours.",
                                               "Saturn: Mars went to Lake Verity. Hurry, if you think it matters."]}}},
    "jupiter_lake_acuity": {
        "lines": ["{rival_name} is slumped by the shore of Lake Acuity.",
                  "{rival_name}: Sorry... Commander Jupiter took Uxie. I couldn't stop her.",
                  "{rival_name}: She said they're taking all three lake Pokémon to their HQ in Veilstone City!",
                  "Team Galactic has the lake trio. Head to Veilstone City."],
        "requires": ["has_icicle_badge"], "flag": "galactic_lake_acuity_cleared"},
    "spear_pillar_commanders": {
        "lines": ["Mars and Jupiter block the way to the summit.",
                  "Jupiter: Cyrus is about to make his new world. You won't interrupt him!"],
        "requires": ["galactic_hq_cleared"], "flag": "spear_pillar_commanders",
        "battle": {"name": "Commanders Mars and Jupiter", "class": "COMMANDER", "sprite": "mars.png",
                   "team": [436, 42, 432, 435], "levels": [41, 42, 45, 46], "is_boss_battle": True,
                   "dialogue": {"player_won": ["Mars: Ugh... Go, then. Cyrus will finish you himself."]}}},
    "cyrus_spear_pillar": {
        "lines": ["sinnoh_spear_pillar_event"], "requires": ["galactic_hq_cleared", "spear_pillar_commanders"],
        "fail": ["A strange force blocks the summit. Free the lake guardians at Team Galactic HQ first."],
        "flag": "spear_pillar_resolved",
        "battle": {"name": "Cyrus", "class": "BOSS", "sprite": "cyrus.png", "team": [430, 169, 130, 461],
                   "levels": [45, 46, 45, 48],
                   "is_boss_battle": True,
                   "dialogue": {"player_won": ["Cyrus: ...My new world... is gone.",
                                               "Cyrus: Then I will find another way. Alone.",
                                               "The legendary Pokemon still stirs at the top of the Spear Pillar..."]}}},
    "riley_iron_island": {
        "lines": ["sinnoh_riley_intro"], "flag": "riley_iron_island_cleared",
        "battle": _t(GRUNT_G, team=[42, 435], rewards={"POKEMON_447": 1},
                     dialogue={"player_won": ["sinnoh_riley_egg"]})},

    # ---------------- Unova (Black / White) ----------------
    "n_accumula_speech": {"lines": ["unova_ghetsis_accumula", "unova_n_accumula_speech"],
                          "flag": "heard_n_accumula"},
    "looker_intro": {"lines": ["unova_looker_intro"], "flag": "met_looker"},
    "alder_route2": {"lines": ["unova_alder_route2"], "flag": "met_alder"},
    "n_route2_battle": {
        "lines": ["unova_n_route2_battle"], "flag": "defeated_n_route2",
        "battle": {"name": "N", "class": "PKMN_TRAINER", "sprite": "n.png", "team": [509],
                   "dialogue": {"player_won": ["unova_n_route2_won"], "player_lost": ["unova_n_route2_lost"]}}},
    "dreamyard_monkey": {
        "lines": ["A girl named Fennel is studying the Dreamyard.",
                  "Fennel: This Pokemon is perfect against the Striaton Gym Leaders. Please take it!"],
        "gift_pokemon": {"495": 515, "498": 511, "501": 513, "default": 511}, "flag": "got_elemental_monkey"},
    "plasma_nacrene": {
        "lines": ["unova_museum_plasma"], "flag": "plasma_nacrene_cleared",
        "battle": _t(GRUNT_P, team=[509], dialogue={"player_won": ["unova_plasma_nacrene_won"],
                                                    "player_lost": ["unova_plasma_grunt_lost"]})},
    "plasma_pinwheel": {
        "lines": ["Team Plasma grunts are running through Pinwheel Forest with the Dragon Skull!",
                  "Burgh: I'll cover the other path. Go!"],
        "flag": "plasma_pinwheel_cleared",
        "battle": _t(GRUNT_P, team=[504, 509], dialogue={"player_won": ["unova_plasma_grunt_lost"]})},
    "burgh_sewers": {
        "lines": ["unova_castelia_sewers"], "flag": "plasma_castelia_cleared",
        "battle": _t(GRUNT_P, team=[509, 504], dialogue={"player_won": ["unova_plasma_grunt_lost"]})},
    "n_nimbasa_ferris_wheel": {
        "lines": ["unova_n_nimbasa_ferris_wheel", "N: I am the king of Team Plasma. Now, let us battle."],
        "flag": "met_n_nimbasa",
        "battle": {"name": "N", "class": "PKMN_TRAINER", "sprite": "n.png", "team": [551, 554, 559, 561],
                   "dialogue": {"player_won": ["N: I'll become the hero, and find Reshiram... or Zekrom."]}}},
    "plasma_relic_castle": {
        "lines": ["Sand pours through Relic Castle. Team Plasma is digging for something!"],
        "flag": "plasma_relic_castle_cleared",
        "battle": _t(GRUNT_P, team=[510, 505], dialogue={"player_won": [
            "Plasma Grunt: Too late! Lord N already has what he needs..."]})},
    "plasma_dragonspiral": {
        "lines": ["Team Plasma has stormed Dragonspiral Tower!",
                  "At the top, N calls out to the legendary dragon..."],
        "flag": "plasma_dragonspiral_cleared",
        "battle": _t(GRUNT_P, team=[510, 505, 521], dialogue={"player_won": [
            "A blinding light fills the tower. N flies away on the legendary dragon!",
            "N: Find the other dragon stone, {player_name}. Then we'll see whose truth is stronger."]})},
    "lacunosa_elder": {"lines": ["Elder: Long ago, a monster fell from the sky in a meteorite at Giant Chasm.",
                                 "On cold nights it comes to town and takes people away. So we stay inside at night.",
                                 "That monster... some say it is the empty shell of the original dragon. Kyurem."],
                       "flag": "heard_kyurem_legend"},
    "drayden_dragon_stones": {"lines": ["Drayden: The Light Stone and Dark Stone hold the dragons of truth and ideals.",
                                        "N has one. The other must be awakened by someone the dragon accepts.",
                                        "I believe that someone is you."],
                              "flag": "heard_dragon_stones"},
    # Cheren's B2W2 battle (Serebii PokeEarth): tied to Cheren, whichever role he holds in this save.
    "cheren_victory_road": {
        "lines": ["unova_cheren_victory_road"], "flag": "defeated_rival_victory_road",
        "battle": {"who": "cheren", "class": "RIVAL", "is_boss_battle": True,
                   "team": [510, 512, 521, 526, 612, 500], "levels": [65, 65, 65, 65, 65, 67],
                   "team_choice": {"495": [510, 512, 521, 526, 612, 500], "498": [510, 514, 521, 526, 612, 503],
                                   "501": [510, 516, 521, 526, 612, 497]},
                   "dialogue": {"player_won": ["unova_cheren_rival_won"],
                                "player_lost": ["unova_cheren_rival_lost"]}}},
    "n_chargestone": {
        "lines": ["unova_n_chargestone"], "flag": "defeated_n_chargestone",
        "battle": {"name": "N", "class": "PKMN_TRAINER", "sprite": "n.png", "team": [525, 595, 597, 599],
                   "dialogue": {"player_won": ["N: I'll go to Dragonspiral Tower. The legendary dragon is waiting."]}}},

    # ---------------- Johto (HeartGold / SoulSilver) ----------------
    "giovanni": {
        "lines": ["A man in a dark suit stands behind the waterfall...",
                  "Giovanni: So, the one who keeps getting in Team Rocket's way.",
                  "I have returned to rebuild. Let me see if you are worth my time."],
        "requires": ["has_8_johto_badges"], "flag": "defeated_giovanni_johto",
        "done": ["The cave behind the waterfall is quiet now."],
        "battle": {"name": "Giovanni", "class": "BOSS", "sprite": "leader_giovanni.png", "is_boss_battle": True,
                   "team": [51, 31, 34, 112], "level": 45,
                   "dialogue": {"player_won": ["Giovanni: ...Team Rocket is finished. For now.",
                                               "Giovanni vanished into the mist of the falls."]}}},
    "dragon_elder": {"lines": ["dragon_elder_pass"], "requires": ["has_rising_badge"],
                     "fail": ["dragon_elder_intro"]},
    "bug_catching_contest": {"lines": ["Officer: The Bug-Catching Contest is held in the National Park!",
                                       "It runs on Tuesdays, Thursdays and Saturdays. Bring your best Bug Pokemon!"]},

    # ---------------- Hoenn (Omega Ruby / Alpha Sapphire) ----------------
    # The opening (dev/builders/build_hoenn_story.py): Birch isn't at his lab until he's been saved
    # on Route 101; the rival waits on Route 103; the Pokedex and Poke Balls come after that battle.
    "hoenn_neighbor": {"lines": ["Mrs. Birch: Oh, you must be our new neighbor! Welcome to Littleroot!",
                                 "Mrs. Birch: My husband is out doing fieldwork again, and {rival_name} went off to study Pokemon.",
                                 "Mrs. Birch: Why not go and look for them? Route 101 is just north of town."],
                       "flag": "hoenn_met_neighbor",
                       "done": ["Mrs. Birch: Make yourself at home in Littleroot! Drop by anytime."]},
    "hoenn_birch_lab": {
        "stages": [
            {"lines": ["hoenn_birch_lab"], "requires": ["not:hoenn_birch_rescued"]},
            {"lines": ["Professor Birch: Thanks again for saving me out there!",
                       "Professor Birch: You and that Pokemon worked so well together. Please, keep it!",
                       "Professor Birch: My kid, {rival_name}, is on Route 103, north of Oldale Town. Go and say hello!"],
             "requires": ["hoenn_birch_rescued"], "flag": "hoenn_birch_thanked"},
            {"lines": ["Professor Birch: {rival_name} is on Route 103, north of Oldale Town."],
             "requires": ["hoenn_birch_thanked", "not:hoenn_rival_103"]},
            {"lines": ["Professor Birch: You battled {rival_name}? And you won? Then you'll need this!",
                       "{player_name} received a POKEDEX!",
                       "Professor Birch: It records every Pokemon you meet. Fill it up for me!",
                       "{rival_name}: Here, take these too. You can't catch anything without Poke Balls!"],
             "requires": ["hoenn_rival_103"], "flag": "received_pokedex_hoenn", "gift_item": {"balls": 10}},
        ],
        "done": ["Professor Birch: Fill that Pokedex! Your dad is in Petalburg City, west past Route 102."]},
    "oldale_clerk": {"lines": ["Poke Mart Clerk: Hi there! We're giving away free samples today.",
                               "Poke Mart Clerk: Potions heal your Pokemon in a pinch. Take some!"],
                     "gift_item": {"POTION": 10}, "flag": "oldale_free_potions",
                     "done": ["Poke Mart Clerk: Come shop with us anytime!"]},
    "oldale_sketch_boy": {"lines": ["A boy is drawing footprints right in the middle of the path to Route 102.",
                                    "Boy: Don't step on my sketch! Come back after you've seen Professor Birch."]},
    "norman_wally": {
        "lines": ["Your dad, Norman, is the Gym Leader here in Petalburg City!",
                  "Norman: {player_name}! You made it! And you have a Pokemon of your own now.",
                  "A thin boy walks into the Gym. Wally: Excuse me... I'm Wally.",
                  "Wally: I'm moving to Verdanturf Town, where the air is cleaner. I'd like a Pokemon to keep me company...",
                  "Wally: But I've never caught one before.",
                  "Norman: Then borrow my Zigzagoon and this Poke Ball. {player_name}, go with Wally to Route 102!"],
        "scene": "wally_catch", "flag": "helped_wally",
        "after": ["Wally: Thank you, {player_name}! Ralts and I are going to be best friends.",
                  "Norman: Well done, both of you. {player_name}, I'm a Gym Leader. Earn four badges, then challenge me!",
                  "Norman: Start with Roxanne in Rustboro City. Go through Route 104 and Petalburg Woods."]},
    "norman_petalburg": {"lines": ["Norman: Earn four badges, then come back and challenge me!",
                                   "Norman: Wally moved to Verdanturf with his Ralts. He's training hard, I hear."]},
    "wally_mauville": {
        "lines": ["Wally is standing at the door of the Mauville Gym with his uncle.",
                  "Wally: {player_name}! Ralts and I have been training every day.",
                  "Wally: Before I challenge the Gym... will you battle me? I want to see how strong we've gotten!"],
        "flag": "defeated_wally_mauville",
        "battle": {"name": "Wally", "class": "PKMN_TRAINER", "sprite": "wally.png", "team": [280], "levels": [17],
                   "rewards": {"balls": 5, "HM_ROCK_SMASH": 1},
                   "dialogue": {"player_won": ["Wally: ...You're amazing. I'll keep getting stronger, you'll see!",
                                               "Wally's uncle: Thank you for looking out for Wally. Take this HM Rock Smash!",
                                               "Wally went home to Verdanturf. The Mauville Gym is open now."],
                                "player_lost": ["Wally: We won? Ralts, we really won!"]}}},
    "granite_steven": {
        "lines": ["Deep in Granite Cave, a man is studying the old cave walls.",
                  "Steven: A letter from my father? Thank you for coming all this way.",
                  "Steven: I'm Steven. I'm fond of rare stones. Mr. Briney can take you on to Slateport. Good luck!"],
        "requires": ["met_mr_stone"], "fail": ["A man is studying the cave walls. He seems busy."],
        "take_item": {"LETTER": 1}, "flag": "met_steven",
        "done": ["Steven: Mr. Briney can take you on to Slateport. Good luck!"]},
    "rival_route112": {
        "lines": ["{rival_name}: Hey, {player_name}! Heading for Lavaridge Town?",
                  "{rival_name}: The way through is the Fiery Path, but boulders block it. Take this!"],
        "gift_item": {"HM_STRENGTH": 1}, "flag": "got_strength_hoenn",
        "done": ["{rival_name}: Use Strength to move the boulders in the Fiery Path!"]},
    "weather_scientists": {
        "lines": ["Scientist: You saved the Weather Institute! Thank you!",
                  "Scientist: We've been studying this Pokemon. It changes form with the weather.",
                  "Scientist: Please, take it with you!"],
        "gift_pokemon": 351, "flag": "got_castform",
        "done": ["Scientist: How is Castform doing? Try it in the rain and in the sun!"]},
    "devon_president": {"lines": ["Mr. Stone: You got our Devon Parts back? Thank you!",
                                  "Please deliver this letter to my son Steven in Dewford, and these parts to Captain Stern.",
                                  "Mr. Briney's boat can take you. Take this PokeNav Plus, too."],
                        "requires": ["rusturf_rescued"], "fail": ["hoenn_devon_parts_stolen"],
                        "gift_item": {"POKE_NAV": 1, "LETTER": 1, "DEVON_PARTS": 1}, "flag": "met_mr_stone",
                        "done": ["Mr. Stone: Steven is in Granite Cave, in Dewford. Thank you again!"]},
    "slateport_market": {"lines": ["The Slateport Market is busy. Merchants call out their best deals.",
                                   "Use the Shop to buy what you need."]},
    "captain_stern": {"lines": ["Captain Stern: Those are the Devon Parts? Wonderful!",
                                "With these we can finish the submarine and explore the sea floor."],
                      "requires": ["oceanic_museum_cleared"], "fail": ["hoenn_museum_stern"],
                      "take_item": {"DEVON_PARTS": 1}, "flag": "delivered_devon_parts"},
    "bike_shop": {"lines": ["Rydel: Welcome to Rydel's Cycles! You came all the way from Littleroot?",
                            "Then take a bike. Ride it everywhere and tell people about my shop!"],
                  "gift_item": {"BICYCLE": 1}, "flag": "got_bike_hoenn",
                  "done": ["Rydel: How's the bike? Treat it well!"]},
    "wally_house": {"lines": ["Wally: I've been training with Ralts every day!",
                              "Someday I'll be strong enough to challenge you. Just watch!"]},
    "professor_cozmo": {"stages": [
        {"lines": ["Cozmo's wife: My husband went to Meteor Falls with some strange people...",
                   "They wanted his Meteorite! Please, go help him!"], "flag": "heard_cozmo",
         "requires": ["not:meteor_falls_cleared"]},
        {"lines": ["Cozmo's wife: Please hurry! Meteor Falls is along Route 114, east of town."],
         "requires": ["heard_cozmo", "not:meteor_falls_cleared"]},
        {"lines": ["Professor Cozmo: Thank you for saving me at Meteor Falls!",
                   "Professor Cozmo: They took my Meteorite up Mt. Chimney. Please stop them!",
                   "Professor Cozmo: The Cable Car on Route 112 goes to the top."],
         "requires": ["meteor_falls_cleared"], "flag": "cozmo_thanked"}],
        "done": ["Professor Cozmo: I'll keep studying meteorites. Come by anytime!"]},

    # ---------------- Kalos / Alola / Galar ----------------
    "alola_looker": {"lines": ["Looker: I am Looker of the International Police.",
                               "Creatures called Ultra Beasts have been sighted in Alola.",
                               "If you see anything strange, let me know."],
                     "flag": "met_alola_looker"},
    "galar_magnolia_intro": {"lines": ["Professor Magnolia: Welcome to Wedgehurst. I study Dynamax.",
                                       "Pokemon grow giant in Galar thanks to a strange energy underground.",
                                       "Sonia will help you with anything else. Off you go!"],
                             "flag": "met_magnolia"},
    "galar_sonia_murals": {"lines": ["Sonia: The mural in Stow-on-Side... it shows two heroes, and two Pokemon!",
                                     "The history books only talk about the heroes. That isn't the whole story."],
                           "flag": "saw_stow_murals"},
    "galar_sonia_bath": {"lines": ["Sonia: The Hero's Bath! Look at the statues. Two Pokemon with a sword and a shield.",
                                   "The Darkest Day wasn't stopped by people alone. I'm sure of it now."],
                         "flag": "saw_circhester_monument"},
    "galar_marnie_spikemuth": {
        "lines": ["Marnie: Spikemuth's my home. Team Yell was only tryin' to help me.",
                  "Marnie: But this is my battle now. Let's go."],
        "flag": "defeated_marnie_spikemuth",
        "battle": {"name": "Marnie", "class": "PKMN_TRAINER", "sprite": "marnie.png", "is_boss_battle": True,
                   "team": [510, 454, 560, 877, 861],
                   "dialogue": {"player_won": ["Marnie: You're strong. Go on, the Finals are waitin'."]}}},
}

# Route buttons that already have their own handler in PlayState.
ROUTE_METHODS = {"sage_li": "visit_sage_li", "director_radio": "visit_director_radio"}


def get(key):
    return EVENTS.get(key)


def gift_for_starter(gift, starter_id):
    """A gift species, or the one matching the player's region starter."""
    if isinstance(gift, dict):
        return gift.get(str(starter_id)) or gift.get("default")
    return gift


def gift_pokemon(game, pid, level=None):
    """Give a Pokemon to the player (party, or the PC when the party is full), at the area's wild
    level or at `level` (the Sinjoh Ruins' Lv 1 dragons). Returns the message."""
    from src.pokemon.data import Pokemon
    from src.world import levels
    story = game.story_manager
    mon = Pokemon(game.loader.fetch_specific(int(pid)), game.assets, size_mult=2.5)
    mon.caught_region = story.get_current_region()
    levels.set_wild(game, mon, story.current_area_key)
    if level:
        mon.level = int(level)
        mon.current_hp = mon.get_max_hp()
    if len(story.player_team) < 6:
        story.player_team.append(mon)
        where = "joined your team"
    else:
        slot = next((i for i, p in enumerate(story.pc_pokemon) if p is None), None)
        if slot is None:
            story.pc_pokemon.append(mon)
        else:
            story.pc_pokemon[slot] = mon
        where = "was sent to the PC"
    game.data.mark_seen(mon.id)
    game.data.add_pokemon(mon)
    return f"{mon.name.upper()} {where}!"
