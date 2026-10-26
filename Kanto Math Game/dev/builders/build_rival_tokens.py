"""Regional rivals the player names (Jordan): each region's rival and second friend in the data use
{rival_name} / {rival_character} and {friend_name} / {friend_character} instead of the canon name
and sprite, so the names typed on the rival screen show everywhere (StoryManager.RIVAL_CHOICES).

  Kanto Blue, Johto Silver, Sinnoh Barry, Unova Cheren (friend Bianca), Kalos Serena (friend Shauna),
  Alola Hau (friend Gladion), Galar Hop, Paldea Nemona. (Hoenn already used the tokens.)

Only the story areas and the GAME_TEXT dialogue are changed (not journal missions or place names
like Hau'oli). Run from the game folder:  python dev/builders/build_rival_tokens.py
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from textjson import TextJSON  # noqa: E402

B = "\\b"  # a regex word boundary


def rival(name):
    """The region's rival: their name (not "Hau'oli") and sprite file become tokens."""
    return [(B + name + B + "(?!')", "{rival_name}"), (B + name.lower() + "\\.png" + B, "{rival_character}")]


def friend(name):
    return [(B + name + B + "(?!')", "{friend_name}"), (B + name.lower() + "\\.png" + B, "{friend_character}")]


RULES = {
    "assets/pokemon_area_data.json": [('"name": "Rival Blue"', '"name": "{rival_name}"')],
    "assets/johto_area_data.json": [('"name": "Silver"', '"name": "{rival_name}"')],  # (art stays silver.png)
    "assets/sinnoh_area_data.json": rival("Barry"),
    "assets/unova_area_data.json": rival("Cheren") + friend("Bianca"),
    "assets/kalos_area_data.json": rival("Serena") + friend("Shauna"),
    "assets/alola_area_data.json": rival("Hau") + friend("Gladion"),
    "assets/galar_area_data.json": rival("Hop"),
    "assets/paldea_area_data.json": rival("Nemona"),
}


def apply(text, rules):
    n = 0
    for pat, tok in rules:
        text, k = re.subn(pat, tok, text)
        n += k
    return text, n


total = 0
for path, rules in RULES.items():
    tj = TextJSON(path)
    for section in ("GAME_TEXT", "STORY_PROGRESSION"):
        if f'"{section}"' not in tj.s:
            continue
        st, en = tj.area_span(section)
        body, n = apply(tj.s[st:en], rules)
        tj.s = tj.s[:st] + body + tj.s[en:]
        total += n
        print(f"{path} {section}: {n}")
    tj.save()

# Story NPC events written in code (Barry, Cheren, Bianca, Serena's sprite).
P = "src/world/story_events.py"
s = open(P, encoding="utf-8").read()
s, n = apply(s, rival("Barry") + rival("Cheren") + friend("Bianca") + [(B + "serena\\.png" + B, "{rival_character}")])
open(P, "w", encoding="utf-8", newline="").write(s)
print(f"{P}: {n}")
print("total", total + n)
