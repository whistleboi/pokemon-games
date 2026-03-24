import sys
import os
from src.core.game import Game

# Allow imports from the src folder
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

if __name__ == "__main__":
    Game().run()
