#Pydroid run pygame
# (That line, and importing pygame right here, are how Pydroid 3 knows to open this as a graphical app. Without them
# it runs the game in its text terminal, where SDL can't start: "did you include SDL_main.h".)
import pygame  # noqa: F401
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
