"""The Sevii Islands' walkable maps (Jordan, 11-11): laid out from FireRed's own map data, tile for tile (frlg.py, written by
kanto_handoff/frlg_map_tools; change a map there). See MAPPING_GUIDE.md. In story order."""
from .frlg import SEVII

MAPS = dict(SEVII)

# Rebuilt from the FireRed file by the Hoenn method (firered.py, written by kanto_handoff/kanto_rom_tools/kgen.py, 11-14): each
# Sevii map rebuilt there replaces the one above of the same name.
from .firered import KANTO as _FIRERED  # noqa: E402

MAPS.update({k: v for k, v in _FIRERED.items() if k in MAPS})
