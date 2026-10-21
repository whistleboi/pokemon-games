"""Read-aloud with the computer's built-in voices (no downloads, nothing stored).

- A speaker button reads the math question or the text box.
- Character lines ("Professor Oak: ...", "Mom: ...") are read out automatically, each character
  with their own voice: male or female, pitch and speed (a deep, slow Oak; a quick rival).

On Windows this uses System.Speech through PowerShell, in the background so the game never waits.
The text reaches PowerShell through environment variables and is XML-escaped there, so nothing in
a line can run as a command. Where there's no voice (or no audio, as in tests) it stays quiet.
"""
import os
import re
import subprocess
import sys
import threading

import pygame

_proc = None
_lock = threading.Lock()

_PS = ("Add-Type -AssemblyName System.Speech; "
       "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
       "try { $s.SelectVoiceByHints([System.Speech.Synthesis.VoiceGender]::$env:POKEMATH_GENDER) } catch {}; "
       "$t = [System.Security.SecurityElement]::Escape($env:POKEMATH_SAY); "
       "$x = \"<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='en-US'>"
       "<prosody pitch='$env:POKEMATH_PITCH' rate='$env:POKEMATH_RATE'>$t</prosody></speak>\"; "
       "$s.SpeakSsml($x)")

NUMBER_WORDS = {"+": " plus ", "-": " minus ", "−": " minus ", "×": " times ", "x": " times ",
                "*": " times ", "÷": " divided by ", "/": " divided by ", "=": " equals ",
                "?": " what", "<": " is less than ", ">": " is more than "}

# Voices: (gender, pitch, rate). Pitch is an SSML word; rate a percentage.
NARRATOR = ("Female", "medium", "-5%")
DEFAULT = ("Male", "medium", "+0%")
PROFESSOR = ("Male", "low", "-15%")
VILLAIN = ("Male", "x-low", "-10%")
KID = ("Male", "high", "+15%")

FEMALE = {
    "MOM", "NURSE", "NURSE JOY", "BIANCA", "OLIVIA", "MARNIE", "DIANTHA", "LENORA", "PENNY", "OLEANA",
    "NEMONA", "MALVA", "LUSAMINE", "KORRINA", "ZINNIA", "VIOLA", "VALERIE", "SONIA", "SKYLA",
    "SHAUNTAL", "MISTY", "ERIKA", "SABRINA", "LORELEI", "AGATHA", "WHITNEY", "JASMINE", "CLAIR",
    "KAREN", "ROXANNE", "FLANNERY", "WINONA", "PHOEBE", "GLACIA", "GARDENIA", "FANTINA", "CANDICE",
    "CYNTHIA", "ELESA", "IRIS", "CAITLIN", "MALLOW", "LANA", "LILLIE", "ACEROLA", "PLUMERIA",
    "NESSA", "BEA", "OPAL", "MELONY", "RIKA", "POPPY", "IONO", "TULIP", "KATY", "GEETA", "MELA",
    "ERI", "KAHILI", "DAWN", "MAY", "LYRA", "HILDA", "ROSA", "SERENA", "SELENE", "GLORIA", "JULIANA",
    "JESSIE", "MARS", "JUPITER", "COURTNEY", "SHELLY", "SHAUNA", "PROFESSOR JUNIPER", "JUNIPER",
    "PROFESSOR MAGNOLIA", "MAGNOLIA", "PROFESSOR SADA", "SADA", "LASS", "BEAUTY", "PICNICKER",
}
PROFESSORS = {"PROFESSOR OAK", "PROF. OAK", "OAK", "PROFESSOR ELM", "ELM", "PROFESSOR BIRCH", "BIRCH",
              "PROFESSOR ROWAN", "ROWAN", "PROFESSOR SYCAMORE", "SYCAMORE", "PROFESSOR KUKUI", "KUKUI",
              "PROFESSOR TURO", "TURO", "MR. FUJI", "ELDER", "DIRECTOR CLAVELL", "BILL", "KURT"}
VILLAINS = {"GIOVANNI", "CYRUS", "GHETSIS", "LYSANDRE", "ROSE", "MAXIE", "ARCHIE", "GUZMA", "LUSAMINE"}
KIDS = {"HOP", "HAU", "BARRY", "ARVEN", "WALLY", "YOUNGSTER", "BUG CATCHER", "BLUE", "GARY",
        "SILVER", "CHEREN", "N", "TIERNO", "TREVOR"}

SPEAKER = re.compile(r"^\s*([A-Z][A-Za-z.'\- ]{0,28}):\s+(.+)$")


def available():
    """A voice to speak with (Windows), and real sound (tests run with a dummy audio driver)."""
    return sys.platform == "win32" and os.environ.get("SDL_AUDIODRIVER") != "dummy"


def math_words(problem):
    """'7 + 3 = ?' -> '7 plus 3 equals what?'"""
    out = [NUMBER_WORDS.get(tok, tok).strip() for tok in str(problem).split()]
    text = " ".join(t for t in out if t)
    return text + ("?" if text.endswith("what") else "")


def clean(text):
    """Drop symbols a voice reads badly."""
    text = re.sub(r"[▼►◄★♪]", " ", str(text))
    return text.replace("PKMN", "Pokémon").replace("POKé", "Poké")


def voice_for(name):
    """(gender, pitch, rate) for a character's name."""
    n = name.strip().upper()
    last = n.split()[-1] if n.split() else n
    if n in PROFESSORS or last in PROFESSORS and n.startswith("PROF"):
        return ("Female", "medium", "-10%") if n in FEMALE else PROFESSOR
    if n in VILLAINS:
        return ("Female", "low", "-5%") if n in FEMALE else VILLAIN
    if n in FEMALE or last in FEMALE:
        return ("Female", "high", "+5%") if n in {"NURSE", "NURSE JOY", "MOM"} else ("Female", "medium", "+5%")
    if n in KIDS or last in KIDS:
        return KID
    return DEFAULT


def split_speaker(line):
    """'Mom: Hello!' -> ('Mom', 'Hello!'); a plain line -> (None, line)."""
    m = SPEAKER.match(str(line))
    return (m.group(1), m.group(2)) if m else (None, str(line))


def say(text, voice=NARRATOR):
    """Speak in the background, cutting off anything still being read."""
    if not available() or not text:
        return
    text = clean(text)[:600]
    gender, pitch, rate = voice

    def run():
        global _proc
        with _lock:
            if _proc and _proc.poll() is None:
                _proc.kill()
            env = dict(os.environ, POKEMATH_SAY=text, POKEMATH_GENDER=gender,
                       POKEMATH_PITCH=pitch, POKEMATH_RATE=rate)
            try:
                _proc = subprocess.Popen(
                    ["powershell", "-NoProfile", "-NonInteractive", "-Command", _PS],
                    env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            except OSError:
                _proc = None

    threading.Thread(target=run, daemon=True).start()


def say_line(line, auto=False):
    """Read a dialogue line in its speaker's voice. With auto=True only character lines are read
    (narration stays silent unless the player taps the speaker)."""
    name, words = split_speaker(line)
    if name:
        say(words, voice_for(name))
    elif not auto:
        say(words, NARRATOR)


def draw_speaker(surface, rect, color=(255, 255, 255), ink=(30, 30, 40)):
    """A round speaker button."""
    r = pygame.Rect(rect)
    pygame.draw.circle(surface, ink, r.center, r.w // 2 + 2)
    pygame.draw.circle(surface, (70, 110, 220), r.center, r.w // 2)
    cx, cy = r.center
    u = max(2, r.w // 12)
    pygame.draw.rect(surface, color, (cx - 4 * u, cy - 2 * u, 2 * u, 4 * u))
    pygame.draw.polygon(surface, color, [(cx - 2 * u, cy - 2 * u), (cx + u, cy - 5 * u),
                                         (cx + u, cy + 5 * u), (cx - 2 * u, cy + 2 * u)])
    for k in (1, 2):
        arc = pygame.Rect(0, 0, (3 + 2 * k) * u, (5 + 3 * k) * u)
        arc.center = (cx + 2 * u, cy)
        pygame.draw.arc(surface, color, arc, -0.9, 0.9, max(2, u))
