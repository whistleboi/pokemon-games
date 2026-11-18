"""The Orange Islands' walkable maps (Jordan 11-17: Orange becomes a walkable region; "5.7 for everything"): all of them
come from Orange Islands Beta 5.7 (Kalarie's FireRed hack) by the Hoenn method (oi57.py, written by
kanto_handoff/orange_rom_tools/ogen.py from the batches o_batchN.py: change a map there and rerun it, not here)."""
from .oi57 import ORANGE as _OI57

MAPS = dict(_OI57)
