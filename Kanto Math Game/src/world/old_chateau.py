"""The Old Chateau's ghosts (Sinnoh S3, 11-23). Platinum: now and then the ghost of a little girl appears in the fourth
bedroom from the west, looks at you and drifts off toward the door; a butler's ghost floats through the dining hall. Neither
can be spoken to. The map's scenes (kanto_handoff/sinnoh_map_tools/s_s3_old_chateau.py) play on "world:old_chateau:<percent>":
true that often, rolled afresh every 20 seconds (so a scene's condition, read every frame, gives one answer per visit)."""
import time
import random


def condition(story, arg):
    try:
        pct = int(arg)
    except ValueError:
        return False
    roll = random.Random(int(time.time() // 20) * 7919 + pct).random()
    return roll * 100 < pct
