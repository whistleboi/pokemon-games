# Builds "Pokemath Portable": the game plus its own Python, so the folder runs on any 64-bit Windows PC with nothing to
# install, and stays plain editable files (Jordan 11-24: "portable folder", not an .exe).
#   python dev/tools/make_portable.py            (build or refresh; rerun after editing the game)
#   python dev/tools/make_portable.py --saves    (also copy this folder's game_data*.json saves into it)
#
# Layout:   <out>/Play.bat           double-click to play
#           <out>/python/            Windows' embeddable Python (same version as this one) + pygame-ce, numpy, moderngl
#           <out>/game/              the game (no dev/, tests/, saves, caches)
#           <out>/game/mesa/         Mesa's OpenGL, used only when the PC's own driver can't do OpenGL 3.3
#                                    (src/dungeon/live3d.py _mesa: DirectX 12 on the card where it can, else the CPU)
# Inputs (downloaded once, Jordan's OK 11-24) in pokemon-games/sources/portable_downloads:
#   python-<ver>-embed-amd64.zip (python.org), mesa3d-<ver>-release-msvc.7z extracted to mesa/ (github pal1000/mesa-dist-win,
#   unpacked with 7zr.exe from 7-zip.org).
# A refresh never deletes the portable copy's own saves (game_data*.json) and leaves files there that it didn't put.
import argparse
import filecmp
import glob
import os
import shutil
import site
import sys
import zipfile

GAME = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   # (.../Kanto Math Game, holding main.py)
POKEMON_GAMES = os.path.abspath(os.path.join(GAME, "..", ".."))
if os.path.basename(os.path.dirname(GAME)) != "Kanto Math Game":   # (a worktree: .../.claude/worktrees/<name>/Kanto Math Game)
    i = GAME.replace("\\", "/").find("/Kanto Math Game/.claude/")
    POKEMON_GAMES = os.path.dirname(GAME[:i + len("/Kanto Math Game")]) if i >= 0 else POKEMON_GAMES
DOWNLOADS = os.path.join(POKEMON_GAMES, "sources", "portable_downloads")
OUT = os.path.join(POKEMON_GAMES, "Pokemath Portable")
PACKAGES = ("pygame", "pygame_ce-*.dist-info", "numpy", "numpy.libs", "numpy-*.dist-info", "moderngl", "_moderngl.py",
            "moderngl-*.dist-info", "glcontext", "glcontext-*.dist-info")
MESA_FILES = ("opengl32.dll", "libgallium_wgl.dll", "dxil.dll")   # (dxil: Mesa's DirectX 12 path on the graphics card)
SKIP_DIRS = {"dev", "tests", "__pycache__", ".git", ".claude", "mesa"}
SKIP_FILES = ("crash.log",)


def _skip_file(name):
    return name in SKIP_FILES or name.startswith("game_data") or ".bak" in name or name.endswith((".pyc", ".tmp", ".corrupt"))


def _copy(src, dst, counts):
    if os.path.exists(dst) and os.path.getsize(src) == os.path.getsize(dst) and filecmp.cmp(src, dst, shallow=True):
        return
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)
    counts["copied"] += 1


def game_files():
    for root, dirs, files in os.walk(GAME):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not (root == GAME and d.startswith("."))]
        for f in files:
            if not _skip_file(f):
                yield os.path.relpath(os.path.join(root, f), GAME)


def build(saves=False):
    v = sys.version_info
    embed = os.path.join(DOWNLOADS, f"python-{v.major}.{v.minor}.{v.micro}-embed-amd64.zip")
    mesa = os.path.join(DOWNLOADS, "mesa", "x64")
    for need in (embed, *(os.path.join(mesa, f) for f in MESA_FILES)):
        if not os.path.exists(need):
            sys.exit(f"missing {need} (see the top of this file)")
    counts = {"copied": 0, "removed": 0}

    # 1) Python: the embeddable zip, told where the packages and the game are (its ._pth file sets sys.path)
    py = os.path.join(OUT, "python")
    if not os.path.exists(os.path.join(py, "python.exe")):
        with zipfile.ZipFile(embed) as z:
            z.extractall(py)
    pth = os.path.join(py, f"python{v.major}{v.minor}._pth")
    with open(pth, "w", encoding="utf-8") as f:
        f.write(f"python{v.major}{v.minor}.zip\n.\nLib\\site-packages\n..\\game\nimport site\n")
    sp_out = os.path.join(py, "Lib", "site-packages")
    sp_in = [p for p in site.getsitepackages() if p.endswith("site-packages")][0]
    for pat in PACKAGES:
        hits = glob.glob(os.path.join(sp_in, pat))
        if not hits:
            sys.exit(f"this Python has no {pat} in {sp_in}")
        for hit in hits:
            if os.path.isdir(hit):
                for root, dirs, files in os.walk(hit):
                    dirs[:] = [d for d in dirs if d != "__pycache__"]
                    for f in files:
                        s = os.path.join(root, f)
                        _copy(s, os.path.join(sp_out, os.path.relpath(s, sp_in)), counts)
            else:
                _copy(hit, os.path.join(sp_out, os.path.basename(hit)), counts)

    # 2) the game, mirrored: new and changed files in, files the game no longer has out (saves and Mesa kept)
    g = os.path.join(OUT, "game")
    want = set(game_files())
    for rel in want:
        _copy(os.path.join(GAME, rel), os.path.join(g, rel), counts)
    for root, dirs, files in os.walk(g):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            rel = os.path.relpath(os.path.join(root, f), g)
            if rel not in want and not _skip_file(f):
                os.remove(os.path.join(root, f))
                counts["removed"] += 1
    if saves:
        for s in glob.glob(os.path.join(GAME, "game_data*.json")):
            if ".bak" not in s:
                _copy(s, os.path.join(g, os.path.basename(s)), counts)

    # 3) Mesa beside the game (live3d.MESA_DIR)
    for f in MESA_FILES:
        _copy(os.path.join(mesa, f), os.path.join(g, "mesa", f), counts)

    # 4) the launcher: pythonw (no console window), run from the game folder; a crash still lands in game/crash.log
    with open(os.path.join(OUT, "Play.bat"), "w", encoding="ascii", newline="\r\n") as f:
        f.write('@echo off\ncd /d "%~dp0game"\nstart "" "%~dp0python\\pythonw.exe" main.py\n')
    with open(os.path.join(OUT, "README.txt"), "w", encoding="utf-8", newline="\r\n") as f:
        f.write("Pokemath, portable copy for 64-bit Windows.\n\n"
                "Play: double-click Play.bat. Nothing to install; copy this whole folder to another PC to play there.\n"
                "Edit: the game is plain files in game\\ (code in game\\src, maps and data in game\\assets).\n"
                "Saves: game\\game_data*.json (copy them along to keep your progress).\n"
                "3D: if the PC's graphics driver can't do OpenGL 3.3, the game uses game\\mesa instead.\n"
                "Made by dev/tools/make_portable.py in the main game folder; rerun it to refresh this copy.\n")
    print(f"{OUT}: {counts['copied']} files copied, {counts['removed']} removed")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--saves", action="store_true", help="also copy this folder's saves")
    build(ap.parse_args().saves)
