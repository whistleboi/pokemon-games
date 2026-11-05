"""The Trainer Card (Jordan, 11-04): ID No., name, money, Pokedex, play time, Champion titles, the
trainer's picture and the region's badges. The save screen shows the game being played; the load
screen shows the file about to be loaded (read from the file, before it is loaded)."""
import pygame
from src.ui import theme
from src.ui.mon_tags import fit_sprite
from src.utils import Utils
from src.config import WHITE


def facts_live(game):
    """The card for the game being played."""
    story = game.story_manager
    area = story.get_current_area_data() or {}
    return {
        "name": str(getattr(game, "player_name", "TRAINER")),
        "char": getattr(game, "player_character", "red"),
        "trainer_id": getattr(story, "trainer_id", 0),
        "money": story.money,
        "dex": _dex_count(game.data.data.get("pokedex", {})),
        "seconds": int(getattr(story, "play_seconds", 0)),
        "titles": _titles(game, story.story_flags),
        "region": story.get_current_region(),
        "earned": list(story.badges.get(story.get_current_region(), [])),
        "party": [(p.id, getattr(p, "form", "normal"), getattr(p, "is_shiny", False))
                  for p in story.player_team[:6] if p is not None],
        "place": area.get("route_name") or (story.current_area_key or "").replace("_", " ").title(),
    }


def facts_from_save(game, data):
    """The card for a save file's data (the dict in game_data_*.json), without loading it."""
    story = data.get("story") or {}
    key = story.get("current_area_key") or ""
    area = game.loader.area_data.get("STORY_PROGRESSION", {}).get(key, {}) or {}
    region = str(area.get("region") or story.get("active_badge_region") or story.get("starting_region")
                 or "KANTO").upper()
    store = (story.get("region_stores") or {}).get(story.get("active_store") or "", {})
    team = store.get("team") or story.get("player_team") or []
    return {
        "name": str(story.get("player_name", "TRAINER")),
        "char": story.get("player_char", "red"),
        "trainer_id": int(story.get("trainer_id") or 0),
        "money": int(story.get("money", 0)),
        "dex": _dex_count(data.get("pokedex", {})),
        "seconds": int(story.get("play_seconds", 0)),
        "titles": _titles(game, story.get("story_flags") or {}),
        "region": region,
        "earned": list((story.get("badges") or {}).get(region, [])),
        "party": [(p.get("id"), p.get("form", "normal"), p.get("shiny", False))
                  for p in team[:6] if isinstance(p, dict) and p.get("id")],
        "place": area.get("route_name") or key.replace("_", " ").title(),
    }


def _dex_count(dex):
    return len({v["id"] for v in dex.values() if isinstance(v, dict) and "id" in v})


def _titles(game, flags):
    starts = game.loader.area_data.get("REGION_START", {})
    sm = game.story_manager
    return sum(1 for r, cfg in starts.items() if not cfg.get("travel_only") and flags.get(sm.champion_flag(r)))


_BADGE_CASE = {}  # one badge case per game: its badge art for every region


def _badge_case(game):
    case = _BADGE_CASE.get(id(game))
    if case is None:
        from src.states.systems.badge_case import BadgeCaseState
        case = _BADGE_CASE[id(game)] = BadgeCaseState(game, None)
    return case


class TrainerCard:
    def __init__(self, game, facts):
        self.game, self.facts = game, facts
        assets = game.assets
        img = assets.get_player_image(facts["char"] or "red")
        self.trainer_img = fit_sprite(img, 230, 250) if img else None
        self.party_icons = []
        for pid, form, shiny in facts["party"]:
            try:
                icon = assets.get_pokemon_image(pid, form, shiny)
            except Exception:
                icon = None
            self.party_icons.append(fit_sprite(icon, 58, 58) if icon else None)
        self.badges = []  # (sprite, earned) for each Gym of the region
        self.accent = (70, 92, 150)
        try:
            case = _badge_case(game)
            region = facts["region"]
            self.accent = case.REGION_COLORS.get(region, self.accent)
            badge_map = case.region_maps.get(region, {})
            for i in range(1, max(badge_map.values(), default=0) + 1):
                sprite = case.badge_sprites.get(region, {}).get(i)
                self.badges.append((pygame.transform.smoothscale(sprite, (52, 52)) if sprite else None,
                                    any(badge_map.get(b) == i for b in facts["earned"])))
        except Exception:  # (a region without a badge case page: no badge row)
            pass

    def rows(self):
        f = self.facts
        secs = f["seconds"]
        return [("NAME", f["name"]), ("MONEY", f"${f['money']:,}"), ("POKEDEX", str(f["dex"])),
                ("PLAY TIME", f"{secs // 3600}:{secs // 60 % 60:02d}"), ("CHAMPION TITLES", str(f["titles"]))]

    def draw(self, screen, c):
        """The card in rect c (made for 764 x 448)."""
        f, accent = self.game.assets.fonts, self.accent
        pygame.draw.rect(screen, theme.shade(accent, 0.55), c.move(0, 6), border_radius=22)
        pygame.draw.rect(screen, accent, c, border_radius=22)
        pygame.draw.rect(screen, theme.shade(accent, 1.25), c, 4, border_radius=22)
        Utils.draw_text_outline(screen, "TRAINER CARD", f["button"], WHITE, c.x + 28, c.y + 34, align="left",
                                outline_color=theme.shade(accent, 0.45), thickness=3)
        Utils.draw_text_outline(screen, f"IDNo. {self.facts['trainer_id']:05d}", f["label"], WHITE, c.right - 28,
                                c.y + 34, align="right", outline_color=theme.shade(accent, 0.45), thickness=2)

        inner = pygame.Rect(c.x + 18, c.y + 64, c.w - 36, c.h - 82)
        pygame.draw.rect(screen, (248, 248, 252), inner, border_radius=16)
        # The facts on lined rows, the trainer on the right.
        rows = pygame.Rect(inner.x + 22, inner.y + 16, inner.w - 300, 0)
        for k, (label, value) in enumerate(self.rows()):
            y = rows.y + k * 50
            pygame.draw.line(screen, (214, 218, 232), (rows.x, y + 42), (rows.right, y + 42), 2)
            theme.shadow_text(screen, label, f["label"], rows.x, y + 10, color=(110, 116, 140))
            vf = f["s_med"] if f["s_med"].size(value)[0] <= rows.w - 190 else f["label"]
            theme.shadow_text(screen, value, vf, rows.right, y + 6, align="right")
        spot = pygame.Rect(inner.right - 262, inner.y + 12, 246, 262)
        pygame.draw.rect(screen, theme.shade(accent, 1.6) if sum(accent) < 400 else (236, 238, 246), spot,
                         border_radius=14)
        if self.trainer_img:
            screen.blit(self.trainer_img, self.trainer_img.get_rect(midbottom=(spot.centerx, spot.bottom - 6)))

        # The region's badges along the bottom.
        strip = pygame.Rect(inner.x + 14, inner.bottom - 84, inner.w - 28, 72)
        pygame.draw.rect(screen, theme.shade(accent, 0.5), strip, border_radius=14)
        if not self.badges:
            Utils.draw_text_outline(screen, "No Gym badges in this region", f["label"], WHITE, strip.centerx,
                                    strip.centery, outline_color=theme.shade(accent, 0.3), thickness=2)
            return
        step = strip.w / len(self.badges)
        for i, (sprite, earned) in enumerate(self.badges):
            cx = int(strip.x + step * (i + 0.5))
            pygame.draw.circle(screen, theme.shade(accent, 0.35), (cx, strip.centery), 30)
            if sprite:
                img = sprite.copy()
                if not earned:
                    img.fill((60, 60, 70), special_flags=pygame.BLEND_RGB_MULT)
                    img.set_alpha(90)
                screen.blit(img, img.get_rect(center=(cx, strip.centery)))

    def draw_party(self, screen, x, y, w):
        """The party's icons in a row of six boxes, w wide."""
        cell = w // 6
        for i in range(6):
            r = pygame.Rect(x + i * cell, y, cell - 6, cell - 6)
            pygame.draw.rect(screen, theme.shade(theme.PANEL_BORDER, 0.8), r, border_radius=10)
            icon = self.party_icons[i] if i < len(self.party_icons) else None
            if icon:
                screen.blit(icon, icon.get_rect(center=r.center))
