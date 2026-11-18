# [REF-0084: Items]
"""Items that work like the games (Jordan): Poke Mart stock and what each item does.

MEDICINE heals HP (Potion 20, Super Potion 60, Hyper Potion 120, Max Potion all), cures conditions
(Antidote, Paralyze Heal, Awakening, Burn Heal, Ice Heal, Full Heal) or both (Full Restore), or
revives (Revive half HP, Max Revive all). BATTLE items raise stats (X Attack... +2, like Gen 7+),
crits (Dire Hit) or guard against stat drops (Guard Spec.). Repels keep wild Pokemon away: here a
route can be left without battling while one lasts (Repel 2 routes, Super 4, Max 5). An Escape Rope
leads out of a cave or building to the last Pokemon Center.

STANDARD_MART: the Poke Mart counter of the games (Gen 4 on), by badges earned in the region.
SPECIALTY_BALLS: the second counter's balls, by badges. DEPARTMENT: what department stores add."""

MEDICINE = {
    "POTION": {"heal": 20, "price": 200, "text": "Restores 20 HP."},
    "SUPER_POTION": {"heal": 60, "price": 700, "text": "Restores 60 HP."},
    "HYPER_POTION": {"heal": 120, "price": 1500, "text": "Restores 120 HP."},
    "MAX_POTION": {"heal": "full", "price": 2500, "text": "Fully restores HP."},
    "FULL_RESTORE": {"heal": "full", "cure": "all", "price": 3000, "text": "Fully restores HP and cures any condition."},
    "FRESH_WATER": {"heal": 30, "price": 200, "text": "Water with lots of minerals. Restores 30 HP."},
    "SODA_POP": {"heal": 50, "price": 300, "text": "A fizzy soda drink. Restores 50 HP."},
    "LEMONADE": {"heal": 70, "price": 400, "text": "A very sweet drink. Restores 70 HP."},
    "MOOMOO_MILK": {"heal": 100, "price": 600, "text": "Rich milk from Miltank. Restores 100 HP."},
    "BERRY_JUICE": {"heal": 20, "price": 100, "text": "A juice made from Berries. Restores 20 HP."},   # (HGSS: Shuckie holds one)
    "ANTIDOTE": {"cure": ["poison", "toxic"], "price": 200, "text": "Cures poison."},
    "PARALYZE_HEAL": {"cure": ["paralysis"], "price": 200, "text": "Cures paralysis."},
    "AWAKENING": {"cure": ["sleep"], "price": 100, "text": "Wakes up a sleeping Pokemon."},
    "BURN_HEAL": {"cure": ["burn"], "price": 200, "text": "Heals a burn."},
    "ICE_HEAL": {"cure": ["freeze"], "price": 200, "text": "Thaws out a frozen Pokemon."},
    "FULL_HEAL": {"cure": "all", "price": 400, "text": "Cures any status condition."},
    # Lavaridge's Herb Shop (ORAS): cheaper than the Mart's, and very bitter
    "ENERGY_POWDER": {"heal": 50, "price": 500, "text": "A very bitter powder. Restores 50 HP."},
    "ENERGY_ROOT": {"heal": 200, "price": 1200, "text": "A very bitter root. Restores 200 HP."},
    "HEAL_POWDER": {"cure": "all", "price": 300, "text": "A very bitter powder. Cures any status condition."},
    "REVIVAL_HERB": {"revive": 1.0, "price": 2800, "text": "A very bitter herb. Revives a fainted Pokemon with all its HP."},
    "LAVA_COOKIE": {"cure": "all", "price": 200, "text": "Mt. Chimney's own treat, baked with volcanic ash. Cures any status condition."},
    "REVIVE": {"revive": 0.5, "price": 2000, "text": "Revives a fainted Pokemon with half its HP."},
    "MAX_REVIVE": {"revive": 1.0, "price": 4000, "text": "Revives a fainted Pokemon with all its HP."},
    "RARE_CANDY": {"price": 10000, "text": "Raises a Pokemon's level by one."},
    # Berries that heal (Hoenn's berry patches, Jordan 11-12): used from the Berries pocket, in or out of battle
    # (no price here: the shops' berry price stands)
    "ORAN_BERRY": {"heal": 10, "berry": True, "text": "A Berry. Restores 10 HP."},
    "SITRUS_BERRY": {"heal": 0.25, "berry": True, "text": "A Berry. Restores a quarter of a Pokemon's HP."},
    "CHERI_BERRY": {"cure": ["paralysis"], "berry": True, "text": "A Berry. Cures paralysis."},
    "CHESTO_BERRY": {"cure": ["sleep"], "berry": True, "text": "A Berry. Wakes up a sleeping Pokemon."},
    "PECHA_BERRY": {"cure": ["poison", "toxic"], "berry": True, "text": "A Berry. Cures poison."},
    "RAWST_BERRY": {"cure": ["burn"], "berry": True, "text": "A Berry. Heals a burn."},
    "ASPEAR_BERRY": {"cure": ["freeze"], "berry": True, "text": "A Berry. Thaws out a frozen Pokemon."},
    "LUM_BERRY": {"cure": "all", "berry": True, "text": "A Berry. Cures any status condition."},
    "PERSIM_BERRY": {"cure_vol": "confused", "berry": True, "text": "A Berry. Held, it snaps its holder out of confusion."},
    # Route 113's Glass Workshop flutes (blown from volcanic ash; sold there): played again and again ("keep")
    "BLUE_FLUTE": {"cure": ["sleep"], "keep": True, "price": 100, "text": "A blue glass flute. Its tune wakes a sleeping Pokemon."},
}
BATTLE = {
    "X_ATTACK": {"stat": "ATTACK", "price": 1000, "text": "Sharply raises Attack in battle."},
    "X_DEFENSE": {"stat": "DEFENSE", "price": 2000, "text": "Sharply raises Defense in battle."},
    "X_SP_ATK": {"stat": "SPATK", "price": 1000, "text": "Sharply raises Sp. Atk in battle."},
    "X_SP_DEF": {"stat": "SPDEF", "price": 2000, "text": "Sharply raises Sp. Def in battle."},
    "X_SPEED": {"stat": "SPEED", "price": 1000, "text": "Sharply raises Speed in battle."},
    "X_ACCURACY": {"stat": "ACCURACY", "price": 1000, "text": "Sharply raises accuracy in battle."},
    "DIRE_HIT": {"focus": 2, "price": 1000, "text": "Makes critical hits much more likely in battle."},
    "GUARD_SPEC": {"mist": 5, "price": 1500, "text": "Stops your team's stats being lowered for five turns."},
    # Run from a wild Pokemon for sure (FireRed's Poke Doll, ORAS's Poke Toy, Gen 3's Fluffy Tail)
    "POKE_TOY": {"flee": True, "price": 1000, "text": "A toy on a stick. Use it in a battle with a wild Pokemon to get away for sure."},
    "POKE_DOLL": {"flee": True, "price": 1000, "text": "A cute doll. Use it against a wild Pokemon to get away for sure. Saffron's Copycat would love one, too."},   # (FireRed: Celadon Dept. Store 4F)
    "FLUFFY_TAIL": {"flee": True, "price": 1000, "text": "A fluffy tail toy. Use it in a battle with a wild Pokemon to get away for sure."},
    "YELLOW_FLUTE": {"cure_vol": "confused", "keep": True, "price": 300, "text": "A yellow glass flute. In battle, its tune snaps a Pokemon out of confusion."},
    "RED_FLUTE": {"cure_vol": "infatuated", "keep": True, "price": 200, "text": "A red glass flute. In battle, its tune snaps a Pokemon out of infatuation."},
}
FIELD = {
    "REPEL": {"repel": 2, "price": 400, "text": "Keeps wild Pokemon away: leave the next 2 routes without battling."},
    "SUPER_REPEL": {"repel": 4, "price": 700, "text": "Keeps wild Pokemon away for the next 4 routes."},
    "MAX_REPEL": {"repel": 5, "price": 900, "text": "Keeps wild Pokemon away for the next 5 routes."},
    "ESCAPE_ROPE": {"escape": True, "price": 1000, "text": "Leads out of a cave or building, to the last Pokemon Center."},
    # Route dungeons (src/states/overworld/dungeon.py): HONEY on the map draws three wild Pokemon to catch.
    "HONEY": {"attract": True, "price": 300, "text": "Sweet honey. Use it out on a route to draw in three wild Pokemon."},
    "BLACK_FLUTE": {"repel": 1, "keep": True, "price": 400, "text": "A black glass flute. Its tune keeps wild Pokemon away for the next route."},
    "WHITE_FLUTE": {"attract": True, "keep": True, "price": 500, "text": "A white glass flute. Play it out on a route to draw in three wild Pokemon."},
}
BALL_PRICES = {"POKE_BALLS": 1000, "GREAT_BALL": 600, "ULTRA_BALL": 800, "PREMIER_BALL": 20, "NET_BALL": 1000,
               "DIVE_BALL": 1000, "NEST_BALL": 1000, "REPEAT_BALL": 1000, "TIMER_BALL": 1000, "QUICK_BALL": 1000,
               "DUSK_BALL": 1000, "HEAL_BALL": 300, "LUXURY_BALL": 3000}

# Badges in the region -> what the Poke Mart counter adds (Gen 4 on).
STANDARD_MART = [
    (0, ["POKE_BALLS", "POTION", "ANTIDOTE", "PARALYZE_HEAL", "ESCAPE_ROPE"]),
    (1, ["GREAT_BALL", "SUPER_POTION", "AWAKENING", "BURN_HEAL", "ICE_HEAL", "REPEL"]),
    (3, ["HYPER_POTION", "SUPER_REPEL", "REVIVE"]),
    (5, ["ULTRA_BALL", "FULL_HEAL", "MAX_REPEL"]),
    (7, ["MAX_POTION"]),
    (8, ["FULL_RESTORE"]),
]
SPECIALTY_BALLS = [(2, ["NET_BALL", "NEST_BALL"]), (3, ["QUICK_BALL", "DUSK_BALL", "HEAL_BALL"]),
                   (4, ["DIVE_BALL", "REPEAT_BALL", "TIMER_BALL"]), (5, ["LUXURY_BALL"])]
DEPARTMENT = ["X_ATTACK", "X_DEFENSE", "X_SP_ATK", "X_SP_DEF", "X_SPEED", "X_ACCURACY", "DIRE_HIT", "GUARD_SPEC",
              "FRESH_WATER", "SODA_POP", "LEMONADE"]


# Held items that power up one type's moves (Jordan, 11-06: Cherrygrove's fisherman's Mystic Water)
HELD_BOOSTS = {"SILK_SCARF": "NORMAL", "METAL_COAT": "STEEL", "SPELL_TAG": "GHOST", "SILVER_POWDER": "BUG", "PIXIE_PLATE": "FAIRY",
               "ROCK_INCENSE": "ROCK", "ROSE_INCENSE": "GRASS", "ODD_INCENSE": "PSYCHIC", "MYSTIC_WATER": "WATER", "CHARCOAL": "FIRE", "SEA_INCENSE": "WATER", "WAVE_INCENSE": "WATER", "NEVER_MELT_ICE": "ICE", "BLACK_GLASSES": "DARK",
               "MIRACLE_SEED": "GRASS", "POISON_BARB": "POISON", "TWISTED_SPOON": "PSYCHIC", "HARD_STONE": "ROCK", "MAGNET": "ELECTRIC", "SHARP_BEAK": "FLYING", "BLACK_BELT": "FIGHTING", "SOFT_SAND": "GROUND", "DRAGON_FANG": "DRAGON",
               "FLAME_PLATE": "FIRE", "SPLASH_PLATE": "WATER", "ZAP_PLATE": "ELECTRIC", "MEADOW_PLATE": "GRASS", "ICICLE_PLATE": "ICE", "FIST_PLATE": "FIGHTING", "TOXIC_PLATE": "POISON", "EARTH_PLATE": "GROUND", "SKY_PLATE": "FLYING", "MIND_PLATE": "PSYCHIC", "INSECT_PLATE": "BUG", "STONE_PLATE": "ROCK", "SPOOKY_PLATE": "GHOST", "DRACO_PLATE": "DRAGON", "DREAD_PLATE": "DARK", "IRON_PLATE": "STEEL"}   # (the Plates: HGSS's S.S. Aqua captain, 11-16)   # (HGSS gifts: Route 32's old man, Frieda, Tuscany; 11-15)  # (Charcoal: Lavaridge's Herb Shop; Sea Incense: Mt. Pyre, 11-12)
FEWER_WILD = {"CLEANSE_TAG", "PURE_INCENSE"}
DEFENCE_HELD = {"EVIOLITE"}  # (held by a Pokemon that can still evolve: its defences up by half. Route 123, 11-12)  # (held by your lead: fewer wild Pokemon on a map. Mt. Pyre's old woman, 11-12)
HELD_BOOST = 1.2
HELD = {"MYSTIC_WATER": {"price": 1000, "text": "Give it to a Pokemon to hold: its Water-type moves hit harder."},
        "CHARCOAL": {"price": 1000, "text": "Give it to a Pokemon to hold: its Fire-type moves hit harder."},
        "BLACK_GLASSES": {"price": 1000, "text": "Give it to a Pokemon to hold: its Dark-type moves hit harder."},   # (FireRed: the Rocket Hideout, 11-14)
        "LEFTOVERS": {"price": 4000, "text": "Held: its holder gets back a little HP at the end of every turn."},   # (FireRed: hidden under Route 12's Snorlax, 11-14)
        "QUICK_CLAW": {"price": 4000, "text": "Held: now and then its holder gets to move first."},   # (FireRed: the Safari Zone, 11-14)
        "SEA_INCENSE": {"price": 1000, "text": "Give it to a Pokemon to hold: its Water-type moves hit harder."},
        "CLEANSE_TAG": {"price": 1000, "text": "Give it to your lead Pokemon to hold: fewer wild Pokemon come near."},
        "EVIOLITE": {"price": 3000, "text": "Give it to a Pokemon that can still evolve: it takes less damage."},
        "MENTAL_HERB": {"price": 1000, "text": "Held: used up to free its holder from love, Taunt, Encore and Disable."},
        "SHELL_BELL": {"price": 4000, "text": "Held: its holder gets back an eighth of the damage it deals."},
        "FOCUS_BAND": {"price": 3000, "text": "Held: now and then its holder hangs on at 1 HP instead of fainting."},
        "NEVER_MELT_ICE": {"price": 1000, "text": "Give it to a Pokemon to hold: its Ice-type moves hit harder."},
        "POWER_HERB": {"price": 100, "text": "Held: a move that needs a turn to charge goes at once. Used up."},   # (Route 34's Kate, HGSS; effect not built yet)
        "MIRACLE_SEED": {"price": 1000, "text": "Give it to a Pokemon to hold: its Grass-type moves hit harder."},
        "HARD_STONE": {"price": 1000, "text": "Give it to a Pokemon to hold: its Rock-type moves hit harder."},
        "POISON_BARB": {"price": 1000, "text": "Give it to a Pokemon to hold: its Poison-type moves hit harder."},
        "TWISTED_SPOON": {"price": 1000, "text": "Give it to a Pokemon to hold: its Psychic-type moves hit harder."},
        "WAVE_INCENSE": {"price": 9600, "text": "Give it to a Pokemon to hold: its Water-type moves hit harder."},   # (HGSS: Route 47)
        "LAGGING_TAIL": {"price": 200, "text": "Held: its holder always moves last."},   # (HGSS: Route 47; effect not built yet)
        "IRON_BALL": {"price": 200, "text": "Held: its holder's Speed is halved, and Ground moves can hit it even if it flies."},   # (HGSS: Mt. Mortar; effect not built yet)
        "FULL_INCENSE": {"price": 9600, "text": "Held: its holder always moves last."},   # (HGSS: Mt. Mortar; effect not built yet)
        "PURE_INCENSE": {"price": 9600, "text": "Give it to your lead Pokemon to hold: fewer wild Pokemon come near."},   # (HGSS: Mt. Silver, N16)
        "EXPERT_BELT": {"price": 4000, "text": "Held: its holder's super-effective moves hit harder."},   # (HGSS: Mt. Silver; effect not built yet)
        "DESTINY_KNOT": {"price": 200, "text": "Held: if its holder falls in love, the foe does too. At the Day Care, it passes on more of a parent's strengths."},   # (HGSS: Route 26; effect not built yet)
        "BLACK_BELT": {"price": 1000, "text": "Give it to a Pokemon to hold: its Fighting-type moves hit harder."},   # (HGSS: Wesley, Lake of Rage)
        "CHOICE_SPECS": {"price": 4000, "text": "Held: Sp. Atk goes up by half, but its holder can only use the first move it picks."},   # (HGSS: Lake of Rage; effect not built yet)
        "DRAGON_FANG": {"price": 1000, "text": "Give it to a Pokemon to hold: its Dragon-type moves hit harder."},   # (HGSS: Route 45 / Dragon's Den)
        "FLAME_PLATE": {"price": 1000, "text": "A stone tablet. Give it to a Pokemon to hold: its Fire-type moves hit harder."},
        "SPLASH_PLATE": {"price": 1000, "text": "A stone tablet. Give it to a Pokemon to hold: its Water-type moves hit harder."},
        "ZAP_PLATE": {"price": 1000, "text": "A stone tablet. Give it to a Pokemon to hold: its Electric-type moves hit harder."},
        "MEADOW_PLATE": {"price": 1000, "text": "A stone tablet. Give it to a Pokemon to hold: its Grass-type moves hit harder."},
        "ICICLE_PLATE": {"price": 1000, "text": "A stone tablet. Give it to a Pokemon to hold: its Ice-type moves hit harder."},
        "FIST_PLATE": {"price": 1000, "text": "A stone tablet. Give it to a Pokemon to hold: its Fighting-type moves hit harder."},
        "TOXIC_PLATE": {"price": 1000, "text": "A stone tablet. Give it to a Pokemon to hold: its Poison-type moves hit harder."},
        "EARTH_PLATE": {"price": 1000, "text": "A stone tablet. Give it to a Pokemon to hold: its Ground-type moves hit harder."},
        "SKY_PLATE": {"price": 1000, "text": "A stone tablet. Give it to a Pokemon to hold: its Flying-type moves hit harder."},
        "MIND_PLATE": {"price": 1000, "text": "A stone tablet. Give it to a Pokemon to hold: its Psychic-type moves hit harder."},
        "INSECT_PLATE": {"price": 1000, "text": "A stone tablet. Give it to a Pokemon to hold: its Bug-type moves hit harder."},
        "STONE_PLATE": {"price": 1000, "text": "A stone tablet. Give it to a Pokemon to hold: its Rock-type moves hit harder."},
        "SPOOKY_PLATE": {"price": 1000, "text": "A stone tablet. Give it to a Pokemon to hold: its Ghost-type moves hit harder."},
        "DRACO_PLATE": {"price": 1000, "text": "A stone tablet. Give it to a Pokemon to hold: its Dragon-type moves hit harder."},
        "DREAD_PLATE": {"price": 1000, "text": "A stone tablet. Give it to a Pokemon to hold: its Dark-type moves hit harder."},
        "IRON_PLATE": {"price": 1000, "text": "A stone tablet. Give it to a Pokemon to hold: its Steel-type moves hit harder."},   # (HGSS: the S.S. Aqua's captain, a Plate a day after all 16 Badges)
        "SOFT_SAND": {"price": 1000, "text": "Give it to a Pokemon to hold: its Ground-type moves hit harder."},   # (HGSS: Santos, Blackthorn)
        "SMOKE_BALL": {"price": 200, "text": "Held: its holder can always get away from a wild Pokemon."},   # (HGSS: Doris the Dodrio; effect not built yet)
        "SHARP_BEAK": {"price": 1000, "text": "Give it to a Pokemon to hold: its Flying-type moves hit harder."},   # (HGSS: Monica, Route 40)
        "MAGNET": {"price": 1000, "text": "Give it to a Pokemon to hold: its Electric-type moves hit harder."},   # (HGSS: Sunny, Route 37)
        "SOOTHE_BELL": {"price": 100, "text": "Held: its holder grows friendly with you faster."},   # (HGSS: the National Park, 11-15)
        "LEFTOVERS": {"price": 4000, "text": "Held: its holder gets back a little HP at the end of every turn."},   # (the S.S. Tidal's hidden one, Emerald)
        # (11-16: the rest of the held items the regions hand out, each with its games' effect: src/states/battle_items.py)
        "SILK_SCARF": {"price": 1000, "text": "Give it to a Pokemon to hold: its Normal-type moves hit harder."},
        "SPELL_TAG": {"price": 1000, "text": "Give it to a Pokemon to hold: its Ghost-type moves hit harder."},
        "SILVER_POWDER": {"price": 1000, "text": "Give it to a Pokemon to hold: its Bug-type moves hit harder."},
        "PIXIE_PLATE": {"price": 1000, "text": "A stone tablet. Give it to a Pokemon to hold: its Fairy-type moves hit harder."},
        "ROCK_INCENSE": {"price": 2000, "text": "Give it to a Pokemon to hold: its Rock-type moves hit harder."},
        "ROSE_INCENSE": {"price": 2000, "text": "Give it to a Pokemon to hold: its Grass-type moves hit harder."},
        "ODD_INCENSE": {"price": 2000, "text": "Give it to a Pokemon to hold: its Psychic-type moves hit harder."},
        "LAX_INCENSE": {"price": 5000, "text": "Held: foes' moves miss its holder a little more often."},
        "BRIGHT_POWDER": {"price": 4000, "text": "Held: foes' moves miss its holder a little more often."},
        "WIDE_LENS": {"price": 4000, "text": "Held: its holder's moves hit a little more often."},
        "SCOPE_LENS": {"price": 4000, "text": "Held: its holder's moves land critical hits more often."},
        "KINGS_ROCK": {"price": 5000, "text": "Held: its holder's attacks may make the foe flinch. (A Poliwhirl or Slowpoke may also evolve with it.)"},
        "RAZOR_FANG": {"price": 5000, "text": "Held: its holder's attacks may make the foe flinch."},
        "METAL_COAT": {"price": 2000, "text": "Held: its holder's Steel-type moves hit harder. (Onix and Scyther may also evolve with it.)"},
        "LIGHT_BALL": {"price": 1000, "text": "Held by Pikachu: its Attack and Sp. Atk are doubled."},
        "THICK_CLUB": {"price": 1000, "text": "Held by Cubone or Marowak: its Attack is doubled."},
        "DEEP_SEA_TOOTH": {"price": 2000, "text": "Held by Clamperl: its Sp. Atk is doubled. (Clamperl may also evolve with it.)"},
        "DEEP_SEA_SCALE": {"price": 2000, "text": "Held by Clamperl: its Sp. Def is doubled. (Clamperl may also evolve with it.)"},
        "METAL_POWDER": {"price": 1000, "text": "Held by Ditto: its Defense is doubled."},
        "QUICK_POWDER": {"price": 1000, "text": "Held by Ditto: its Speed is doubled."},
        "CHOICE_BAND": {"price": 4000, "text": "Held: Attack goes up by half, but its holder can only use the first move it picks."},
        "CHOICE_SCARF": {"price": 4000, "text": "Held: Speed goes up by half, but its holder can only use the first move it picks."},
        "MACHO_BRACE": {"price": 3000, "text": "Held: its holder earns twice the effort points from battles, but its Speed is halved."},
        "LUCKY_EGG": {"price": 200, "text": "Held: its holder earns half again as much XP from battles."},   # (Kanto: Route 15's aide, for fifty kinds caught; 11-17)
        "LUCKY_PUNCH": {"price": 10, "text": "Held by Chansey: a pair of gloves. Its moves land critical hits far more often."},   # (FireRed: Sevault Canyon's Chansey house; 11-17)
        "STICK": {"price": 200, "text": "Held by Farfetch'd: a leek stalk. Its moves land critical hits far more often."},   # (FireRed: Vermilion's traded Farfetch'd holds it; 11-17)
        "METRONOME": {"price": 4000, "text": "Held: using the same move again and again makes it stronger."},
        "BIG_ROOT": {"price": 4000, "text": "Held: moves that drain HP give its holder more back."},
        "SAFETY_GOGGLES": {"price": 4000, "text": "Held: its holder takes no sandstorm damage, and powder moves don't affect it."},
        "ROCKY_HELMET": {"price": 4000, "text": "Held: a foe that touches its holder with a move gets hurt. (Lets your Pokemon Headbutt trees, too.)"},
        "WHITE_HERB": {"price": 4000, "text": "Held: if its holder's stats are lowered, it puts them back. Used up."},
        "FLOAT_STONE": {"price": 1000, "text": "Held: its holder weighs half as much."},
        "HEAT_ROCK": {"price": 4000, "text": "Held: sunshine its holder calls lasts eight turns. Use it in battle to call sunshine."},
        "DAMP_ROCK": {"price": 4000, "text": "Held: rain its holder calls lasts eight turns. Use it in battle to call rain."},
        "SMOOTH_ROCK": {"price": 4000, "text": "Held: a sandstorm its holder calls lasts eight turns. Use it in battle to call one."},
        "ICY_ROCK": {"price": 4000, "text": "Held: snow its holder calls lasts eight turns. Use it in battle to call snow."},
        "RED_SCARF": {"price": 100, "text": "Held in a Contest: its holder's Cool condition counts for more."},
        "BLUE_SCARF": {"price": 100, "text": "Held in a Contest: its holder's Beauty condition counts for more."},
        "PINK_SCARF": {"price": 100, "text": "Held in a Contest: its holder's Cute condition counts for more."},
        "GREEN_SCARF": {"price": 100, "text": "Held in a Contest: its holder's Clever condition counts for more."},
        "YELLOW_SCARF": {"price": 100, "text": "Held in a Contest: its holder's Tough condition counts for more."},
        # (11-17: for Fling, Trick and Psycho Shift, as in the games. Where to get them: Reversal Mountain (B2W2),
        # Ula'ula Meadow / Resolution Cave (USUM), Wyndon Stadium (SwSh), Levincia's shop (SV, 15,000))
        "FLAME_ORB": {"price": 15000, "text": "Held: it burns its holder at the end of a turn. Flung, it burns the foe."},
        "TOXIC_ORB": {"price": 15000, "text": "Held: it badly poisons its holder at the end of a turn. Flung, it poisons the foe."}}
# Items that are used up when their effect happens (berries too): the holder's copy leaves the Bag.
CONSUMED = {"POWER_HERB", "WHITE_HERB", "MENTAL_HERB"}
# Held berries (Gen 4 on): eaten in battle when their moment comes.
PINCH_BERRIES = {"LIECHI_BERRY": "ATTACK", "GANLON_BERRY": "DEFENSE", "SALAC_BERRY": "SPEED", "PETAYA_BERRY": "SPATK",
                 "APICOT_BERRY": "SPDEF", "LANSAT_BERRY": "focus", "STARF_BERRY": "random"}
RESIST_BERRIES = {"OCCA_BERRY": "FIRE", "PASSHO_BERRY": "WATER", "WACAN_BERRY": "ELECTRIC", "RINDO_BERRY": "GRASS",
                  "YACHE_BERRY": "ICE", "CHOPLE_BERRY": "FIGHTING", "KEBIA_BERRY": "POISON", "SHUCA_BERRY": "GROUND",
                  "COBA_BERRY": "FLYING", "PAYAPA_BERRY": "PSYCHIC", "TANGA_BERRY": "BUG", "CHARTI_BERRY": "ROCK",
                  "KASIB_BERRY": "GHOST", "HABAN_BERRY": "DRAGON", "COLBUR_BERRY": "DARK", "BABIRI_BERRY": "STEEL",
                  "ROSELI_BERRY": "FAIRY", "CHILAN_BERRY": "NORMAL"}
# Berries that lower one stat's effort points by 10 and make a Pokemon friendlier (Gen 4 on; ORAS's -10)
EV_BERRIES = {"POMEG_BERRY": "HP", "KELPSY_BERRY": "ATTACK", "QUALOT_BERRY": "DEFENSE", "HONDEW_BERRY": "SPATK",
              "GREPA_BERRY": "SPDEF", "TAMATO_BERRY": "SPEED"}
BERRY_TEXT = {**{k: f"A Berry. Held, it's eaten when its holder is in a pinch: it raises its {s.replace('SPATK', 'Sp. Atk').replace('SPDEF', 'Sp. Def').title()}."
                 for k, s in PINCH_BERRIES.items() if s not in ("focus", "random")},
              "LANSAT_BERRY": "A Berry. Held, it's eaten when its holder is in a pinch: critical hits get more likely.",
              "STARF_BERRY": "A Berry. Held, it's eaten when its holder is in a pinch: one stat sharply rises.",
              **{k: f"A Berry. Held, it halves one super-effective {t.title()}-type hit." for k, t in RESIST_BERRIES.items() if t != "NORMAL"},
              "CHILAN_BERRY": "A Berry. Held, it halves one Normal-type hit.",
              **{k: f"A Berry. Makes a Pokemon friendlier, but lowers its base {s.replace('SPATK', 'Sp. Atk').replace('SPDEF', 'Sp. Def').title() if s != 'HP' else 'HP'}."
                 for k, s in EV_BERRIES.items()}}


def holdable(item):
    """Can a Pokemon be given this to hold? (held items, and the Berries that do something held)"""
    return item in HELD or item in BERRY_TEXT and item not in EV_BERRIES or item in MEDICINE and MEDICINE[item].get("berry") \
        or item in ("LEPPA_BERRY", "BERRY_JUICE")


def consumed(item):
    """Used up when it does its job (a berry is eaten)."""
    return item in CONSUMED or str(item).endswith("_BERRY") or item == "BERRY_JUICE"


def use_ev_berry(pokemon, item):
    """(used, line): a Pomeg / Kelpsy... Berry: 10 fewer effort points in its stat, and friendlier."""
    stat = EV_BERRIES[item]
    evs = pokemon.__dict__.setdefault("evs", {})
    have = int(evs.get(stat, 0))
    friend = int(getattr(pokemon, "friendship", 70) or 70)
    if have <= 0 and friend >= 255:
        return False, "It won't have any effect."
    before = pokemon.get_max_hp()
    evs[stat] = max(0, have - 10)
    if stat == "HP":
        pokemon.current_hp = max(1 if pokemon.current_hp > 0 else 0, min(pokemon.get_max_hp(), pokemon.current_hp - (before - pokemon.get_max_hp())))
    friend_gain(pokemon, 10 if friend < 100 else 5 if friend < 200 else 2)
    label = {"HP": "HP", "ATTACK": "Attack", "DEFENSE": "Defense", "SPATK": "Sp. Atk", "SPDEF": "Sp. Def", "SPEED": "Speed"}[stat]
    if have > 0:
        return True, f"{pokemon.display_name} became friendly. Its base {label} fell!"
    return True, f"{pokemon.display_name} adores you! Its base {label} can't fall any more."


def held_boost(pokemon, move_type):
    """How much a held item powers up a move of this type (1.0: not at all)."""
    t = HELD_BOOSTS.get(getattr(pokemon, "held_item", None))
    return HELD_BOOST if t and t == str(move_type).upper() else 1.0


XP_HELD = {"LUCKY_EGG": 1.5}   # (held: the holder's battle XP is multiplied, as in the games)


def xp_held_mult(pokemon):
    """How much a held item multiplies its holder's battle XP (1.0: not at all)."""
    return XP_HELD.get(getattr(pokemon, "held_item", None), 1.0)


def friend_gain(pokemon, n):
    """Raise a Pokemon's friendship by n (half again with a Soothe Bell, as in the games), up to 255."""
    if getattr(pokemon, "held_item", None) == "SOOTHE_BELL":
        n = max(n + 1, n * 3 // 2)
    pokemon.friendship = min(255, int(getattr(pokemon, "friendship", 70) or 70) + n)


# Vitamins (the games, Gen 3 on: Lilycove's 3F): each adds 10 effort points to one stat, up to 100 from vitamins
# (and 510 in all). A stat gains a point for every 4 effort points at Lv 100 (data.Pokemon.stat_value).
VITAMIN_EV, VITAMIN_CAP, EV_TOTAL = 10, 100, 510
VITAMINS = {"HP_UP": {"stat": "HP", "price": 9800, "text": "Raises a Pokemon's HP a little, for good."},
            "PROTEIN": {"stat": "ATTACK", "price": 9800, "text": "Raises a Pokemon's Attack a little, for good."},
            "IRON": {"stat": "DEFENSE", "price": 9800, "text": "Raises a Pokemon's Defense a little, for good."},
            "CALCIUM": {"stat": "SPATK", "price": 9800, "text": "Raises a Pokemon's Sp. Atk a little, for good."},
            "ZINC": {"stat": "SPDEF", "price": 9800, "text": "Raises a Pokemon's Sp. Def a little, for good."},
            "CARBOS": {"stat": "SPEED", "price": 9800, "text": "Raises a Pokemon's Speed a little, for good."}}
# Apricorns (HGSS, Jordan 11-15, simplified): picked once a day from the trees with the Apricorn Box; Kurt makes each into his ball on the spot.
APRICORN_BALL = {"RED_APRICORN": "LEVEL_BALL", "BLU_APRICORN": "LURE_BALL", "YLW_APRICORN": "MOON_BALL", "GRN_APRICORN": "FRIEND_BALL",
                 "PNK_APRICORN": "LOVE_BALL", "WHT_APRICORN": "FAST_BALL", "BLK_APRICORN": "HEAVY_BALL"}
APRICORNS = {k: {"price": 40, "text": f"A {k.split('_')[0].title().replace('Blu', 'Blue').replace('Ylw', 'Yellow').replace('Grn', 'Green').replace('Pnk', 'Pink').replace('Wht', 'White').replace('Blk', 'Black')} Apricorn. Kurt in Azalea Town makes it into a {APRICORN_BALL[k].replace('_', ' ').title()}."}
             for k in APRICORN_BALL}
APRICORNS["RADIO_CARD"] = {"text": "A card for the Pokegear: it lets you listen to the radio. Won in Goldenrod's Radio Tower quiz."}
APRICORNS["POKEGEAR"] = {"text": "Mom's gift: a phone (and, with its cards, a Town Map and a radio). Open it from the MENU."}
APRICORNS["MAP_CARD"] = {"text": "A card for the Pokegear: it loads the Town Map. A gift from Cherrygrove's Guide Gent."}
APRICORNS["BASEMENT_KEY"] = {"text": "A key to the locked door in Goldenrod's Tunnel. Taken from a Team Rocket Executive."}
APRICORNS["CARD_KEY"] = {"text": "A card that opens locked doors: Silph Co. in Saffron, or the Radio Tower's 3F in Goldenrod."}
APRICORNS["APRICORN_BOX"] = {"text": "A box for carrying Apricorns. With it, you can pick them from the Apricorn trees once a day."}
# Valuables: only to sell (half their price), as in the games
VALUABLES = {"NUGGET": {"price": 10000, "text": "A nugget of pure gold. Sell it for a good price."},
             "BIG_PEARL": {"price": 7500, "text": "A big, shining pearl. Sell it for a good price."},
             "PEARL": {"price": 1400, "text": "A small, pretty pearl. Sell it for a little money."},
             "STARDUST": {"price": 2000, "text": "Lovely red sand. Sell it for a little money."},
             "STAR_PIECE": {"price": 9800, "text": "A shard of a pretty gem. Sell it for a good price."},
             "TINY_MUSHROOM": {"price": 500, "text": "A small, rare mushroom collectors love. Sell it for a little money."},
             "BIG_MUSHROOM": {"price": 5000, "text": "A big, rare mushroom collectors love. Sell it for a good price."},
             "HEART_SCALE": {"price": 100, "text": "A pretty, heart-shaped scale that shines like a rainbow."},
             "BIG_NUGGET": {"price": 40000, "text": "A big nugget of pure gold. Sell it for a lot of money."},
             "COMET_SHARD": {"price": 60000, "text": "A shard that fell with a comet. Sell it for a lot of money."},
             "BALM_MUSHROOM": {"price": 50000, "text": "A rare mushroom with a lovely smell. Sell it for a lot of money."},
             "RARE_BONE": {"price": 10000, "text": "A rare bone, prized by collectors. Sell it for a good price."},
             "PEARL_STRING": {"price": 30000, "text": "Big pearls on a string. Sell it for a lot of money."},
             "RELIC_GOLD": {"price": 20000, "text": "An old gold coin. Sell it for a lot of money."},
             "SHOAL_SALT": {"price": 20, "text": "Salt from deep in Shoal Cave. The old man there makes Shell Bells from it and Shoal Shells."},
             "SHOAL_SHELL": {"price": 20, "text": "A shell from deep in Shoal Cave. The old man there makes Shell Bells from it and Shoal Salt."},
             "RED_SHARD": {"price": 2000, "text": "A small red shard. The Treasure Hunter on Route 124 trades a Fire Stone for one."},
             "BLUE_SHARD": {"price": 2000, "text": "A small blue shard. The Treasure Hunter on Route 124 trades a Water Stone for one."},
             "YELLOW_SHARD": {"price": 2000, "text": "A small yellow shard. The Treasure Hunter on Route 124 trades a Thunder Stone for one."},
             "GREEN_SHARD": {"price": 2000, "text": "A small green shard. The Treasure Hunter on Route 124 trades a Leaf Stone for one."}}


# Effort points from battle (Gen 6 on): each Pokemon that earns XP from a knockout gets the foe's yield
# (assets/ev_yields.json, from Pokemon Essentials' PBS), doubled by a held Macho Brace; up to 252 a stat, 510 in all.
EV_STAT_CAP = 252


def ev_yield(game, species_id):
    table = getattr(game, "_ev_yields", None)
    if table is None:
        import json, os
        try:
            with open(os.path.join(game.assets.assets_dir, "ev_yields.json"), encoding="utf-8") as f:
                table = json.load(f)
        except OSError:
            table = {}
        game._ev_yields = table
    return dict(table.get(str(int(species_id)), {}))


def gain_battle_evs(game, pokemon, species_id):
    """Add a knocked-out foe's effort points to a Pokemon. Returns {stat: gained}."""
    got = {}
    mult = 2 if getattr(pokemon, "held_item", None) == "MACHO_BRACE" else 1
    evs = pokemon.__dict__.setdefault("evs", {})
    for stat, n in ev_yield(game, species_id).items():
        room = min(EV_STAT_CAP - int(evs.get(stat, 0)), EV_TOTAL - sum(evs.values()))
        add = max(0, min(n * mult, room))
        if not add:
            continue
        before = pokemon.get_max_hp()
        evs[stat] = int(evs.get(stat, 0)) + add
        if stat == "HP" and pokemon.current_hp > 0:  # (the new HP comes filled in)
            pokemon.current_hp = min(pokemon.get_max_hp(), pokemon.current_hp + pokemon.get_max_hp() - before)
        got[stat] = add
    return got


def use_vitamin(pokemon, item):
    """(raised, line): add the vitamin's effort points to its stat, if it can take more."""
    stat = VITAMINS[item]["stat"]
    evs = pokemon.__dict__.setdefault("evs", {})
    have, total = evs.get(stat, 0), sum(evs.values())
    if have >= VITAMIN_CAP or total >= EV_TOTAL:
        return False, "It won't have any effect."
    gain = min(VITAMIN_EV, VITAMIN_CAP - have, EV_TOTAL - total)
    before = pokemon.get_max_hp()
    evs[stat] = have + gain
    if stat == "HP":
        pokemon.current_hp = min(pokemon.get_max_hp(), pokemon.current_hp + pokemon.get_max_hp() - before)
    label = {"HP": "HP", "ATTACK": "Attack", "DEFENSE": "Defense", "SPATK": "Sp. Atk", "SPDEF": "Sp. Def", "SPEED": "Speed"}[stat]
    return True, f"{pokemon.display_name}'s {label} rose!"


def info(item):
    from src.pokemon.pp import PP_ITEMS
    return (MEDICINE.get(item) or BATTLE.get(item) or FIELD.get(item) or HELD.get(item) or VITAMINS.get(item) or VALUABLES.get(item)
            or APRICORNS.get(item) or PP_ITEMS.get(item) or ({"text": BERRY_TEXT[item]} if item in BERRY_TEXT else None)
            or ({"text": STORY_TEXT[item]} if item in STORY_TEXT else None) or {})


def price(item):
    if item in BALL_PRICES:
        return BALL_PRICES[item]
    return info(item).get("price")


def describe(item):
    from src.pokemon import catching, tms
    from src.ui import theme
    if tms.is_tm(item) and theme.GAME is not None:  # what the TM teaches
        from src.pokemon import moves as movelib
        move = tms.move_of(theme.GAME, item) or ""
        d = movelib.info(theme.GAME, move)
        power = f", power {d['power']}" if d.get("power") else ""
        return (f"Teaches {move.replace('-', ' ').title()} ({str(d.get('type', '')).title()}{power}). "
                f"{d.get('effect') or ''} It can be used again and again.")
    if str(item).startswith("HM_"):
        return "A Hidden Machine: it opens the way wherever it's needed."
    from src.pokemon import zpower
    if item in zpower.ITEM_TEXT:
        return zpower.ITEM_TEXT[item]
    if item == "EON_FLUTE":  # (Soaring in the Sky: src/world/soaring3d.py)
        from src.world import soaring3d
        return soaring3d.FLUTE_TEXT
    return info(item).get("text") or catching.BALL_TEXT.get(item, "") or describe_extra(theme.GAME, item)


def standard_stock(badges):
    """The Poke Mart counter for this many badges (in the region)."""
    out = []
    for need, items in STANDARD_MART + SPECIALTY_BALLS:
        if badges >= need:
            out += items
    return out


# Route trainers' prizes (Jordan, 11-06): healing items in place of Poke Balls, more and stronger as the
# region's story goes on (by its badges: Potions, then Super Potions and Revives, then Hyper Potions).
# Max Revives are never prizes: they're found lying on the walked maps, late on (dungeon.MAX_REVIVE_BADGES).
TRAINER_PRIZES = [(0, {"POTION": 2}), (2, {"POTION": 1, "SUPER_POTION": 1}),
                  (4, {"SUPER_POTION": 2, "REVIVE": 1}), (6, {"HYPER_POTION": 2, "REVIVE": 1})]


def trainer_prize(badges):
    return dict(next(prize for need, prize in reversed(TRAINER_PRIZES) if badges >= need))


def route_rewards(badges, rewards):
    """A route trainer's rewards: its own (a story item) without the Poke Balls, and the healing prize."""
    out = {k: v for k, v in (rewards or {}).items() if k != "balls"}
    for k, v in trainer_prize(badges).items():
        out[k] = out.get(k, 0) + v
    out["balls"] = 0  # (a battle gives 3 when it isn't said)
    return out


def medicine_effect(item, pokemon):
    """Use a medicine on a Pokemon (outside or inside battle). Returns (used, lines). The caller
    takes the item from the Bag when used."""
    data = MEDICINE.get(item, {})
    name = pokemon.display_name
    mx = pokemon.get_max_hp()
    fainted = pokemon.current_hp <= 0
    label = item.replace("_", " ").title()
    if "revive" in data:
        if not fainted:
            return False, [f"{name} isn't fainted! The {label} won't have any effect."]
        pokemon.current_hp = max(1, int(mx * data["revive"]))
        if getattr(pokemon, "status", None):
            pokemon.cure_status()
        return True, [f"{name} was revived!", f"{name} has {pokemon.current_hp} HP."]
    if fainted:
        return False, [f"The {label} won't have any effect on a fainted {name}."]
    lines, did = [], False
    cure = data.get("cure")
    status = getattr(pokemon, "status", None)
    if cure and status and (cure == "all" or status in cure):
        pokemon.cure_status()
        lines.append(f"{name} was cured of its {_status_word(status)}!")
        did = True
    heal = data.get("heal")
    if heal and pokemon.current_hp < mx:
        if isinstance(heal, float):  # (a share of its HP: the Sitrus Berry's quarter)
            heal = max(1, int(mx * heal))
        amount = mx - pokemon.current_hp if heal == "full" else min(int(heal), mx - pokemon.current_hp)
        pokemon.current_hp += amount
        lines.append(f"{name}'s HP was restored by {amount} points.")
        did = True
    if not did:
        if heal and not cure:
            return False, [f"{name}'s HP is already full!"]
        return False, [f"It won't have any effect on {name}."]
    return True, lines


def _status_word(status):
    return {"poison": "poison", "toxic": "poison", "paralysis": "paralysis", "sleep": "sleep",
            "burn": "burn", "freeze": "freeze"}.get(status, "condition")


# Legendary held items (Gen 4 on): their owner's own two types hit harder; Drives set Techno Blast's type.
ORB_BOOSTS = {"ADAMANT_ORB": (483, ("DRAGON", "STEEL"), "Dialga"), "LUSTROUS_ORB": (484, ("WATER", "DRAGON"), "Palkia"),
              "GRISEOUS_ORB": (487, ("GHOST", "DRAGON"), "Giratina")}
DRIVES = {"BURN_DRIVE": "FIRE", "CHILL_DRIVE": "ICE", "DOUSE_DRIVE": "WATER", "SHOCK_DRIVE": "ELECTRIC"}
for _k, (_id, _t, _who) in ORB_BOOSTS.items():
    HELD[_k] = {"price": 10000, "text": f"Held by {_who}: its {_t[0].title()}- and {_t[1].title()}-type moves hit harder."}
for _k, _t in DRIVES.items():
    HELD[_k] = {"price": 1000, "text": f"Held by Genesect: its Techno Blast becomes {_t.title()} type."}
PLATE_TYPES = {k: t for k, t in HELD_BOOSTS.items() if k.endswith("_PLATE")}  # (and Judgment takes the Plate's type)
# Ogerpon's masks (Scarlet / Violet's Teal Mask DLC; 11-17): held by Ogerpon, it takes that mask's form (Grass and the
# mask's type, the mask's Ability), its moves hit 1.2x harder and Ivy Cudgel takes the mask's type. No mask: the
# Teal Mask form (Grass, Defiant). Ogerpon's mask can't be knocked off or stolen (battle_moves._removable).
OGERPON_MASKS = {"WELLSPRING_MASK": "WATER", "HEARTHFLAME_MASK": "FIRE", "CORNERSTONE_MASK": "ROCK"}
MASK_ABILITY = {"WATER": "WATERABSORB", "FIRE": "MOLDBREAKER", "ROCK": "STURDY"}
MASK_ART = {"WATER": "1017_water_mask.png", "FIRE": "1017_fire_mask.png", "ROCK": "1017_rock_mask.png"}   # (sprites/pokemon/altform)
MASK_BOOST = 1.2
for _k, _t in OGERPON_MASKS.items():
    HELD[_k] = {"price": 0, "text": f"Held by Ogerpon: it wears this mask, turns {_t.title()} type too and its moves hit harder."}

# Story and key items: what each is for (the Bag shows it). Kept short, in our own words.
STORY_TEXT = {
    "AMULET_COIN": "While you have it, battles pay out twice the prize money.",
    "SHINY_CHARM": "A shining charm: shiny Pokemon turn up more often while you have it.",
    "EVERSTONE": "Give it to a Pokemon to hold: it won't evolve while it does.",
    "GRACIDEA": "A flower for Shaymin: in the daytime it changes Shaymin to its Sky Forme (use it again to change back).",
    "GOLD_TEETH": "The Safari Zone Warden's lost false teeth. He'll be glad to have them back.",
    "INTRIGUING_STONE": "An odd stone someone in town is keen to see.",
    "HERBA_MYSTICA": "A rare, powerful herb from Paldea's Titan Pokemon.",
    "EXPLORER_KIT": "A bag of tools for digging in the Underground.",
    "ADVENTURE_MAP": "A map from the Survival Area: it points the way to new places.",
    "GALACTIC_KEY": "A key that opens the doors in Team Galactic's building.",
    "MAGMA_EMBLEM": "Team Magma's emblem. It gets you past their guards.",
    "GO_GOGGLES": "Goggles that keep sand out of your eyes in a sandstorm.",
    "MEGA_RING": "A ring with a Key Stone: a Pokemon holding the right Mega Stone can Mega Evolve.",
    "METEORITE": "A strange rock that fell from space.",
    "NATIONAL_DEX": "The National Pokedex: it now lists Pokemon from every region.",
    "BICYCLE": "A folding bike: get around faster.",
    "BIKE_VOUCHER": "Trade it in at the bike shop for a free Bicycle.",
    "COIN_CASE": "A case for Game Corner coins.",
    "CONTEST_PASS": "Lets you enter Pokemon Contests.",
    "DEVON_SCOPE": "A scope that shows Pokemon you can't see.",
    "SILPH_SCOPE": "A scope that shows ghosts for what they really are.",
    "DIPLOMA": "Proof that you completed the Pokedex.",
    "DIVE_GEAR": "Gear for diving under deep water.",
    "AQUA_SUIT": "A Team Aqua uniform: it gets you past their guards.",
    "MAGMA_SUIT": "A Team Magma uniform: it gets you past their guards.",
    "AURORA_TICKET": "A ticket for a ship to a faraway island.",
    "EON_TICKET": "A ticket for a ship to the Southern Island.",
    "MYSTIC_TICKET": "A ticket for a ship to Navel Rock.",
    "OLD_SEA_MAP": "An old map of the sea, showing a lonely island.",
    "SS_TICKET": "A ticket for the ship.",
    "PASS": "A pass for the Magnet Train.",
    "RAINBOW_PASS": "A pass for the ferry between the islands.",
    "TRI_PASS": "A pass for the ferry to the first three islands.",
    "VOLCANO_PASS": "A pass to the volcano.",
    "PINKAN_PERMIT": "Lets you onto Pinkan Island.",
    "OLD_ROD": "An old fishing rod. Fish where there's water.",
    "GOOD_ROD": "A good fishing rod. Fish where there's water.",
    "SUPER_ROD": "The best fishing rod. Fish where there's water.",
    "ITEMFINDER": "It beeps near hidden items.",
    "POKE_FLUTE": "Its tune wakes sleeping Pokemon, even big ones blocking the road.",
    "SQUIRT_BOTTLE": "A watering can that wakes a strange tree.",
    "POKE_NAV": "Hoenn's handy gadget: a map and a phone in one.",
    "TOWN_MAP": "A map of the region. Use it to see where you are.",
    "JOHTO_MAP": "A map of Johto. Use it to see where you are.",
    "CERULEAN_CAVE_MAP": "A map of the cave near Cerulean City.",
    "MT_SILVER_MAP": "A map of Mt. Silver.",
    "UNOWN_REPORT": "Notes on the Unown you've caught.",
    "POKEBLOCK_KIT": "Make Pokeblocks from Berries.",
    "POKEBLOCK_CASE": "A case for Pokeblocks.",
    "BERRY_POUCH": "A pouch that holds every Berry you have.",
    "WAILMER_DOLL": "A big, cuddly Wailmer doll.",
    "GLASS_ORNAMENT": "A pretty glass ornament.",
    "GS_BALL": "A mysterious Poke Ball. Kurt in Azalea Town wants to see it.",
    "RED_SCALE": "A red scale from the Lake of Rage's Gyarados.",
    "SECRET_POTION": "A medicine that cures a sick Pokemon. The lighthouse's Ampharos needs it.",
    "TEA": "A cup of tea for the thirsty guards.",
    "LIFT_KEY": "A key for the lift.",
    "CLIMB_KIT": "A climber's kit for scaling rocky walls. Danny's mountain on Navel Island needs it.",   # (Orange 5.7, 11-17)
    "PICKAXE": "A digger's pickaxe. It breaks small rocks, and maybe a fossil inside.",   # (Orange 5.7: Fukuhara's Nurse Joy, 11-17)
    "SHOWBOAT_PASS": "A pass for the Pokemon Showboat, docked at Kinnow. Board as often as you like.",   # (Orange 5.7, 11-17)
    "SCUBA_GEAR": "Diving gear from Nurse Joy. Where the sea is deep, you can go underwater.",   # (Orange 5.7: Route 58, 11-17)
    "WHIRLPULLER": "A gadget that pulls a whirlpool apart, so you can cross it. A gift on Trovita Island.",   # (Orange 5.7, 11-17)
    "SECRET_KEY": "A key for the locked Gym door.",
    "STORAGE_KEY": "A key to the ship's storage room.",
    "RM_1_KEY": "A key to cabin 1.", "RM_2_KEY": "A key to cabin 2.", "RM_4_KEY": "A key to cabin 4.", "RM_6_KEY": "A key to cabin 6.",
    "MACHINE_PART": "A part stolen from the Power Plant.",
    "SCANNER": "A scanner lost in the Abandoned Ship.",
    "LOST_ITEM": "Something a girl lost. She'll be glad to get it back.",
    "OAKS_PARCEL": "A parcel for Professor Oak.",
    "MYSTERY_EGG": "An Egg. Keep it with you and it'll hatch.",
    "ICE_MELTER": "Melts thick ice in your way.",
    "ROCK_SMASHER": "Breaks rocks in your way.",
    "SNAG_MACHINE": "Lets you snatch Shadow Pokemon from other trainers.",
    "TIDAL_BELL": "A bell that rings like the tide.",
    "RUBY": "A gem as red as fire.", "SAPPHIRE": "A gem as blue as the sea.",
    "FIRE_TREASURE": "The Fire Island's sacred treasure.",
    "ICE_TREASURE": "The Ice Island's sacred treasure.",
    "LIGHTNING_TREASURE": "The Lightning Island's sacred treasure.",
    "EON_FLUTE": "Play it to soar through the sky on Latios or Latias.",
}


def describe_extra(game, item):
    """Text for the items no table above covers: Mega Stones, evolution items, fossils."""
    if game is None:
        return ""
    from src.pokemon import forms
    for pid, entries in (getattr(game.assets, "mega_forms", None) or _mega_forms(game)).items():
        for e in entries:
            if e.get("item") == item:
                return f"A Mega Stone. With a Key Stone, {str(e.get('name', '')).title().replace('Mega ', '')} can Mega Evolve in battle."
    evo = game.loader.evolution_map.get("EVOLUTION_ITEMS", {}).get(item)
    if evo:
        names = sorted({str(k).split("_")[0].title() for k in evo})
        return "Makes some Pokemon evolve: " + ", ".join(names[:5]) + ("..." if len(names) > 5 else ".")
    if str(item).endswith("_FOSSIL") or str(item).startswith("FOSSILIZED_") or item == "OLD_AMBER":
        return "A fossil. A lab can bring back the Pokemon inside it."
    from src.pokemon import poffin, contest
    if item in contest.POKEBLOCKS:
        return f"A Pokeblock: feed it to a Pokemon to raise its {str(contest.POKEBLOCKS[item]).title()} condition for Contests."
    if item in poffin.BERRIES:
        return f"A Berry ({poffin.berry_label(item)}). Plant it, or make it into Pokeblocks and Poffins."
    return ""


def _mega_forms(game):
    cache = getattr(game, "_mega_forms_cache", None)
    if cache is None:
        import json, os
        try:
            with open(os.path.join(game.assets.assets_dir, "mega_forms.json"), encoding="utf-8") as f:
                cache = json.load(f)
        except OSError:
            cache = {}
        game._mega_forms_cache = cache
    return cache
