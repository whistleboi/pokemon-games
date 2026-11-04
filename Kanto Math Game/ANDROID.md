# Playing on Android (Pydroid 3)

The game runs on an Android phone or tablet with **Pydroid 3**, a free Python app. It's the same game as on the PC: same screens, same saves.

## 1. Set up Pydroid 3 (once)
1. Install **Pydroid 3** from the Play Store.
2. Open it, tap the menu (☰), then **Pip**.
3. Type `pygame`, then tap **Install**. If Pydroid asks you to install its "repository plugin", say yes, then install pygame again.
4. When Pydroid asks to use your storage, allow it.

## 2. Copy the game to the phone
1. On the PC, in the game folder, run:
   - `python dev/tools/make_android_copy.py` to make `KantoMathGame_Android.zip` next to the game folder (about 500 MB).
   - Add `--saves` to bring your save files along.
2. Copy the zip to the phone (USB cable, Google Drive, and so on).
3. Unzip it on the phone, for example into **Download**. You'll get a `KantoMathGame_Android` folder.

## 3. Play
1. In Pydroid 3, tap the folder icon, then **Open**.
2. Find `KantoMathGame_Android/main.py` and open it.
3. Tap the yellow **▶** button.

The game fills the screen sideways. The first start takes a little while.

## On a phone
- **Tapping** works like clicking.
- **Typing a name:** tap the name box and the keyboard opens. Tap anywhere else, or press Enter, to close it.
- The phone's **Back** button works like Esc: it presses BACK, EXIT or NO on the screen.
- Switching to another app pauses the music. If AUTOSAVE is on, it also saves when you're in a town or on a route.
- Read-aloud (the speaker button) only works on a Windows PC.

## Saves
Saves are the `game_data_*.json` files in the game's folder on the phone. To carry on playing on the PC, copy them back into the PC's game folder (and the other way round).

## If something goes wrong
- **Errors:** the game writes `crash.log` in its folder. Send that file over.
- **No music:** this phone's pygame may not play the Kanto music files (.mp3). Everything else still works. Say so, and they can be converted.
