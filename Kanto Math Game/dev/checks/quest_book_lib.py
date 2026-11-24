# Shared helpers for the quest_book suites, split by region 11-23 (each suite reads this with exec).

# The Quest Book (Jordan, 11-22; kanto_handoff/QUEST_BOOK_DESIGN.md): the Journal's STORY tab as arcs and chapters
# (assets/quest_book.json), SIDE errands, FEATS with tiers (assets/quest_feats.json). Kanto is the pilot.
import json, re
import pygame
from src.states.overworld import CityState
from src.states.systems import JournalState
from src.world import quest_book, feats, guide
fails = 0


def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m)
    fails += 0 if c else 1


def tap(st, pos):
    st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos)])


g.data.save = lambda *a, **k: None
prog = g.loader.area_data["STORY_PROGRESSION"]
missions = {m["id"]: m for m in g.loader.area_data["JOURNAL_MISSIONS"]}
book = quest_book.table(g)
ft = feats.table(g)
tmaps = json.load(open("assets/town_maps.json", encoding="utf-8"))
jmissions = {m["id"]: m for m in g.loader.area_data["JOURNAL_MISSIONS"]}

tms = json.load(open("assets/tms.json", encoding="utf-8"))
import copy
from src.pokemon import tutors
from src.pokemon import items as _items
flags = story.story_flags


def now():
    a, c = quest_book.current(g)
    return (a or {}).get("title"), (c or {}).get("title")


def at(area):
    story.current_area_key = area
    flags["visited_" + area] = True


def badge(name, flag=None):
    story.badges["JOHTO"].append(name)
    if flag:
        flags[flag] = True


def item(k, n=1):
    story.inventory[k] = n


def want(arc, chapter, why):
    check(now() == (arc, chapter), f"{why}: {chapter} ({now()})")


def done_(cond):
    if isinstance(cond, list):
        for c in cond:
            done_(c)
    elif cond.startswith("has_item:"):
        item(cond[9:])
    else:
        flags[cond] = True
