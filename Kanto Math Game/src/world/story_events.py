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
    "canalave_library": {"lines": ["Canalave Library. One book is called 'Sinnoh's Myth'.",
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
        "lines": ["sinnoh_mars_intro"], "requires": ["has_fen_badge"],
        "fail": ["Team Galactic grunts block the way to the lake."], "flag": "galactic_lake_verity_cleared",
        "battle": {"name": "Commander Mars", "class": "COMMANDER", "sprite": "mars.png", "team": [42, 436, 432], "level": 40,
                   "is_boss_battle": True, "dialogue": {"player_won": ["sinnoh_mars_won"]}}},
    "saturn_lake_valor": {
        "lines": ["The lake has been drained. Galactic grunts are everywhere!", "sinnoh_saturn_intro"],
        "requires": ["has_fen_badge"], "flag": "galactic_lake_valor_cleared",
        "battle": {"name": "Commander Saturn", "class": "COMMANDER", "sprite": "saturn.png", "team": [64, 436, 454],
                   "is_boss_battle": True,
                   "dialogue": {"player_won": ["Saturn: Azelf is already ours. You're too late.",
                                               "Saturn: Go to Lake Acuity if you must. Jupiter is there."]}}},
    "jupiter_lake_acuity": {
        "lines": ["sinnoh_jupiter_intro"], "requires": ["has_mine_badge"], "flag": "galactic_lake_acuity_cleared",
        "battle": {"name": "Commander Jupiter", "class": "COMMANDER", "sprite": "galactic_grunt.png",
                   "team": [42, 436, 435], "is_boss_battle": True, "rewards": {"GALACTIC_KEY": 1},
                   "dialogue": {"player_won": ["Jupiter: Uxie is captured. The lake trio belongs to Cyrus now.",
                                               "Jupiter dropped the GALACTIC KEY as she fled!",
                                               "It opens Team Galactic HQ in Veilstone City."]}}},
    "cyrus_spear_pillar": {
        "lines": ["sinnoh_spear_pillar_event"], "requires": ["galactic_hq_cleared"],
        "fail": ["A strange force blocks the summit. Free the lake guardians at Team Galactic HQ first."],
        "flag": "spear_pillar_resolved",
        "battle": {"name": "Cyrus", "class": "BOSS", "sprite": "cyrus.png", "team": [229, 430, 169, 130, 461],
                   "is_boss_battle": True,
                   "dialogue": {"player_won": ["Cyrus: ...My new world... is gone.",
                                               "Cyrus: Then I will find another way. Alone.",
                                               "The legendary Pokemon still stirs at the top of the Spear Pillar..."]}}},
    "riley_iron_island": {
        "lines": ["sinnoh_riley_intro"], "flag": "riley_iron_island_cleared",
        "battle": _t(GRUNT_G, team=[42, 435], rewards={"POKEMON_447": 1},
                     dialogue={"player_won": ["sinnoh_riley_egg"]})},
    "barry_victory_road": {
        "lines": ["sinnoh_barry_rival_intro"], "flag": "defeated_rival_victory_road",
        "battle": {"name": "{rival_name}", "class": "RIVAL", "sprite": "barry.png", "is_boss_battle": True,
                   "team": [398, 214, 419, 143, 392],
                   "team_choice": {"387": [398, 214, 419, 143, 392], "390": [398, 214, 419, 143, 395],
                                   "393": [398, 214, 419, 143, 389]},
                   "dialogue": {"player_won": ["sinnoh_barry_rival_won"],
                                "player_lost": ["sinnoh_barry_rival_lost"]}}},

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
        "gift_pokemon": {"495": 513, "498": 515, "501": 511, "default": 511}, "flag": "got_elemental_monkey"},
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
    "bianca_castelia": {
        "lines": ["Bianca: {player_name}! Let's see how much we've both grown!"], "flag": "defeated_bianca_castelia",
        "battle": {"name": "Bianca", "class": "PKMN_TRAINER", "sprite": "bianca.png",
                   "team": [507, 517, 502],
                   "team_choice": {"495": [507, 517, 502], "498": [507, 517, 496], "501": [507, 517, 499]},
                   "dialogue": {"player_won": ["unova_bianca_won"]}}},
    "n_nimbasa_ferris_wheel": {
        "lines": ["unova_n_nimbasa_ferris_wheel", "N: I am the king of Team Plasma. Now, let us battle."],
        "flag": "met_n_nimbasa",
        "battle": {"name": "N", "class": "PKMN_TRAINER", "sprite": "n.png", "team": [551, 554, 559, 561],
                   "dialogue": {"player_won": ["N: I'll become the hero, and find Reshiram... or Zekrom."]}}},
    "bianca_nimbasa": {
        "lines": ["unova_bianca_nimbasa"], "flag": "defeated_bianca_nimbasa",
        "battle": {"name": "Bianca", "class": "PKMN_TRAINER", "sprite": "bianca.png",
                   "team": [507, 517, 513, 502],
                   "team_choice": {"495": [507, 517, 513, 502], "498": [507, 517, 511, 496],
                                   "501": [507, 517, 515, 499]},
                   "dialogue": {"player_won": ["unova_bianca_won"]}}},
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
    "bianca_undella": {
        "lines": ["unova_bianca_surf", "Bianca: One more battle before the League, okay?"],
        "flag": "defeated_bianca_undella",
        "battle": {"name": "Bianca", "class": "PKMN_TRAINER", "sprite": "bianca.png",
                   "team": [508, 518, 514, 503],
                   "team_choice": {"495": [508, 518, 514, 503], "498": [508, 518, 512, 497],
                                   "501": [508, 518, 516, 500]},
                   "dialogue": {"player_won": ["unova_bianca_won"]}}},
    "drayden_dragon_stones": {"lines": ["Drayden: The Light Stone and Dark Stone hold the dragons of truth and ideals.",
                                        "N has one. The other must be awakened by someone the dragon accepts.",
                                        "I believe that someone is you."],
                              "flag": "heard_dragon_stones"},
    "cheren_victory_road": {
        "lines": ["unova_cheren_victory_road"], "flag": "defeated_rival_victory_road",
        "battle": {"name": "{rival_name}", "class": "RIVAL", "sprite": "cheren.png", "is_boss_battle": True,
                   "team": [521, 510, 526, 516, 500],
                   "team_choice": {"495": [521, 510, 526, 516, 500], "498": [521, 510, 526, 512, 503],
                                   "501": [521, 510, 526, 514, 497]},
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
    "wally_tutorial": {"lines": ["Wally: I'm going to live with my cousins in Verdanturf. The air is cleaner there.",
                                 "Could you help me catch a Pokemon to keep me company?",
                                 "...We did it! A Ralts! Thank you so much!"],
                       "flag": "helped_wally"},
    "devon_president": {"lines": ["Mr. Stone: You got our Devon Goods back from Team Magma/Aqua? Thank you!",
                                  "Please deliver this letter to my son Steven in Dewford, and these parts to Captain Stern.",
                                  "Take this PokeNav Plus, too."],
                        "gift_item": {"POKE_NAV": 1}, "flag": "met_mr_stone",
                        "done": ["Mr. Stone: Steven is in Granite Cave, in Dewford. Thank you again!"]},
    "slateport_market": {"lines": ["The Slateport Market is busy. Merchants call out their best deals.",
                                   "Use the Shop to buy what you need."]},
    "captain_stern": {"lines": ["Captain Stern: Those are the Devon Parts? Wonderful!",
                                "With these we can finish the submarine and explore the sea floor."],
                      "flag": "delivered_devon_parts"},
    "bike_shop": {"lines": ["Rydel: Welcome to Rydel's Cycles! You came all the way from Littleroot?",
                            "Then take a bike. Ride it everywhere and tell people about my shop!"],
                  "gift_item": {"BICYCLE": 1}, "flag": "got_bike_hoenn",
                  "done": ["Rydel: How's the bike? Treat it well!"]},
    "wally_house": {"lines": ["Wally: I've been training with Ralts every day!",
                              "Someday I'll be strong enough to challenge you. Just watch!"]},
    "professor_cozmo": {"lines": ["Cozmo's wife: My husband went to Meteor Falls with some strange people...",
                                  "They wanted his Meteorite! Please, go help him!"],
                        "flag": "heard_cozmo"},

    # ---------------- Kalos / Alola / Galar ----------------
    "kalos_rival_couriway": {
        "lines": ["{rival_name}: Couriway Town! The waterfalls are amazing, right?",
                  "{rival_name}: Before the Victory Road, I want one more battle."],
        "flag": "defeated_rival_couriway",
        "battle": {"name": "{rival_name}", "class": "RIVAL", "sprite": "serena.png", "is_boss_battle": True,
                   "team": [678, 359, 657],
                   "team_choice": {"650": [678, 359, 654], "653": [678, 359, 657], "656": [678, 359, 651]},
                   "dialogue": {"player_won": ["kalos_rival_won"], "player_lost": ["kalos_rival_lost"]}}},
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


def gift_pokemon(game, pid):
    """Give a Pokemon to the player (party, or the PC when the party is full). Returns the message."""
    from src.pokemon.data import Pokemon
    from src.world import levels
    story = game.story_manager
    mon = Pokemon(game.loader.fetch_specific(int(pid)), game.assets, size_mult=2.5)
    mon.caught_region = story.get_current_region()
    levels.set_wild(game, mon, story.current_area_key)
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
