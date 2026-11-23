# Gym Leaders give their own game's TM again (Jordan 11-22: "reinstate the leaders giving their canon rewards"): FireRed's,
# HeartGold / SoulSilver's, Platinum's, Black 2 / White 2's (Black / White's for the Trio, Lenora, Brycen), X / Y's, Sword /
# Shield's, Scarlet / Violet's; Hoenn's (ORAS) were set in its own pass. A Leader who gives their TM gives no random one too.
#   bash dev/checks/run.sh gym_tms
import json
from src.pokemon import tms
from src.states.battle import TrainerBattleState

fails = []


def check(c, m):
    print(("   ok  " if c else "   FAIL ") + m)
    if not c:
        fails.append(m)


CANON = {
    "pokemon": {"PEWTER_CITY": "ROCK-TOMB", "CERULEAN_CITY": "WATER-PULSE", "VERMILLION_CITY": "SHOCK-WAVE", "CELADON_CITY": "GIGA-DRAIN",
                "FUCHSIA_CITY": "TOXIC", "SAFFRON_CITY": "CALM-MIND", "CINNABAR_ISLAND": "FIRE-BLAST", "VIRIDIAN_CITY": "EARTHQUAKE"},
    "johto": {"VIOLET_CITY": "ROOST", "AZALEA_TOWN": "U-TURN", "GOLDENROD_CITY": "ATTRACT", "ECRUTEAK_CITY": "SHADOW-BALL",
              "CIANWOOD_CITY": "FOCUS-PUNCH", "OLIVINE_CITY": "IRON-TAIL", "MAHOGANY_TOWN": "AVALANCHE"},
    "sinnoh": {"OREBURGH_CITY": "STEALTH-ROCK", "ETERNA_CITY": "GRASS-KNOT", "HEARTHOME_CITY": "SHADOW-CLAW", "VEILSTONE_CITY": "DRAIN-PUNCH",
               "PASTORIA_CITY": "BRINE", "CANALAVE_CITY": "FLASH-CANNON", "SNOWPOINT_CITY": "AVALANCHE", "SUNYSHORE_CITY": "CHARGE-BEAM"},
    "unova": {"ASPERTIA_CITY": "WORK-UP", "VIRBANK_CITY": "VENOSHOCK", "STRIATON_CITY": "WORK-UP", "NACRENE_CITY": "RETALIATE",
              "CASTELIA_CITY": "STRUGGLE-BUG", "NIMBASA_CITY": "VOLT-SWITCH", "DRIFTVEIL_CITY": "BULLDOZE", "MISTRALTON_CITY": "ACROBATICS",
              "ICIRRUS_CITY": "FROST-BREATH", "OPELUCID_CITY": "DRAGON-TAIL"},
    "kalos": {"SANTALUNE_CITY": "INFESTATION", "CYLLAGE_CITY": "ROCK-TOMB", "SHALOUR_CITY": "POWER-UP-PUNCH", "COUMARINE_CITY": "GRASS-KNOT",
              "LUMIOSE_CITY": "VOLT-SWITCH", "LAVERRE_CITY": "DAZZLING-GLEAM", "ANISTAR_CITY": "PSYSHOCK", "SNOWBELLE_CITY": "AVALANCHE"},
    "galar": {"TURFFIELD": "MAGICAL-LEAF", "HULBURY": "WHIRLPOOL", "MOTOSTOKE": "WILL-O-WISP", "STOW_ON_SIDE": "REVENGE",
              "BALLONLEA": "DRAINING-KISS", "CIRCHESTER": "ROCK-TOMB", "SPIKEMUTH": "SNARL", "HAMMERLOCKE": "BREAKING-SWIPE"},
    "paldea": {"CORTONDO": "POUNCE", "ARTAZON": "TRAILBLAZE", "LEVINCIA": "VOLT-SWITCH", "CASCARRAFA": "CHILLING-WATER",
               "MEDALI": "FACADE", "MONTENEVERA": "SHADOW-BALL", "ALFORNADA": "PSYCHIC", "GLASEADO": "ICE-SPINNER"},
}

print("1) every Leader's own TM is in their rewards")
for reg, d in CANON.items():
    A = json.load(open(f"assets/{reg}_area_data.json", encoding="utf-8"))["STORY_PROGRESSION"]
    wrong = []
    for area, move in d.items():
        gy = A[area]["gym"]
        L = gy.get("leader") if isinstance(gy.get("leader"), dict) else gy
        if not any(tms.move_of(g, k) == move for k in L.get("rewards", {}) if tms.is_tm(k)):
            wrong.append((area, move))
    check(not wrong, f"{reg}: {len(d)} Leaders, each with their TM {wrong[:4]}")

print("2) a Leader with their own TM gives no random one too; a Leader without one still does")
class _B:
    pass
_inv0 = dict(story.inventory)
for _k in [k for k in story.inventory if tms.is_tm(k)]:
    story.inventory.pop(_k)
for rewards, want_random in (({"balls": 5, "TM268": 1}, False), ({"balls": 5}, True)):
    b = _B(); b.game = g; b.opponent_team = []; b.trainer_class = "GYM_LEADER"; b.is_boss_battle = True; b.player_won = True; b.rewards = rewards
    story.enter_region("JOHTO"); story.current_area_key = "VIOLET_CITY"
    got = TrainerBattleState._tm_reward(b)
    check(bool(got) == want_random, f"rewards {rewards}: random TM {got}")
story.inventory.clear(); story.inventory.update(_inv0)
print(f"##### {len(fails)} failures")
