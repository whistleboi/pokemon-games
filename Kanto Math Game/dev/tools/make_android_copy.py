"""Make the copy of the game to put on an Android phone or tablet (Pydroid 3). See ANDROID.md.

Run from the game folder:
    python dev/tools/make_android_copy.py            -> ../KantoMathGame_Android.zip
    python dev/tools/make_android_copy.py --saves    -> the same, with your save files
    python dev/tools/make_android_copy.py --folder   -> a folder instead of a zip

It takes only what the game needs: main.py, src/, assets/, CREDITS.md and ANDROID.md (no dev tools,
tests, backups or crash logs). Pictures and sounds are stored as they are (they're compressed already).
"""
import argparse
import os
import shutil
import sys
import zipfile

GAME = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NAME = "KantoMathGame_Android"
KEEP_FILES = ("main.py", "CREDITS.md", "ANDROID.md")
KEEP_DIRS = ("src", "assets")
SKIP_DIRS = {"__pycache__", ".git", ".vscode"}
SKIP_EXT = {".pyc", ".bak", ".tmp", ".corrupt", ".log", ".webp"}  # (the .webp pictures aren't used)
STORED_EXT = {".png", ".ogg", ".mp3", ".jpg", ".ttf", ".wav"}  # already compressed


def game_files(with_saves):
    for name in KEEP_FILES:
        if os.path.exists(os.path.join(GAME, name)):
            yield name
    if with_saves:
        for name in sorted(os.listdir(GAME)):
            if name.startswith("game_data") and name.endswith(".json"):
                yield name
    for top in KEEP_DIRS:
        for root, dirs, files in os.walk(os.path.join(GAME, top)):
            dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
            for f in sorted(files):
                if os.path.splitext(f)[1].lower() in SKIP_EXT or ".bak" in f:
                    continue
                yield os.path.relpath(os.path.join(root, f), GAME)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--saves", action="store_true", help="include your save files (game_data*.json)")
    ap.add_argument("--folder", action="store_true", help="make a folder instead of a zip")
    ap.add_argument("--out", default=os.path.dirname(GAME), help="where to put it (default: next to the game folder)")
    args = ap.parse_args()
    files = list(game_files(args.saves))
    total = sum(os.path.getsize(os.path.join(GAME, f)) for f in files)
    if args.folder:
        dest = os.path.join(args.out, NAME)
        if os.path.exists(dest):
            sys.exit(f"{dest} is already there: move it or delete it first.")
        for f in files:
            os.makedirs(os.path.dirname(os.path.join(dest, f)) or dest, exist_ok=True)
            shutil.copy2(os.path.join(GAME, f), os.path.join(dest, f))
    else:
        dest = os.path.join(args.out, NAME + ".zip")
        with zipfile.ZipFile(dest, "w") as z:
            for f in files:
                kind = zipfile.ZIP_STORED if os.path.splitext(f)[1].lower() in STORED_EXT else zipfile.ZIP_DEFLATED
                z.write(os.path.join(GAME, f), os.path.join(NAME, f).replace(os.sep, "/"), compress_type=kind)
    print(f"{len(files)} files ({total / 1e6:.0f} MB) -> {dest}")
    print("Next: copy it to the phone and follow ANDROID.md.")


if __name__ == "__main__":
    main()
