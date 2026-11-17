"""Kanto's walkable maps for dev/builders/build_town_maps.py: every one rebuilt from the FireRed file by the Hoenn method
(firered.py, written by kanto_handoff/kanto_rom_tools/kgen.py: change a map there and rerun it, not here). The hand-drawn
maps that were here and frlg.py's first FireRed pass were all replaced by those, and deleted 11-16 (git history has them)."""
from .firered import KANTO as _FIRERED

MAPS = dict(_FIRERED)
