import sys
import os
from src.core import android
for _stream in (sys.stdout, sys.stderr):  # a console that can't show "✓" or "→" must not stop the game
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(errors="replace")
android.prepare()  # Android (Pydroid 3): the Back button and landscape, before pygame starts
from src.core.game import Game  # noqa: E402

# Allow imports from the src folder
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

if __name__ == "__main__":
    Game().run()
