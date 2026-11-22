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
    # (where the save IS: Kanto's areas name no region, and the last region a badge was won in may be another: a League Redo)
    region = str(area.get("region") or ("KANTO" if area else story.get("active_badge_region") or story.get("starting_region") or "KANTO")).upper()
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
        """The card in rect c (made for 764 x 448): Solar Eclipse's glossy card in the region's colour,
        a faint ring watermark and a light streak, the facts on dark rows, the trainer on the right."""
        f, accent = self.game.assets.fonts, tuple(self.accent)[:3]
        cut = 18
        theme.alpha_poly(screen, (0, 0, 0), theme.chamfer(c.move(6, 8), cut), 120)
        pygame.draw.polygon(screen, theme.shade(accent, 0.45), theme.chamfer(c, cut))
        body = c.inflate(-8, -8)
        pygame.draw.polygon(screen, accent, theme.chamfer(body, cut - 3))
        # the gloss: a lighter top half, a light diagonal streak, a faint ring
        top = pygame.Surface(body.size, pygame.SRCALPHA)
        pygame.draw.polygon(top, (255, 255, 255, 34), [(0, 0), (body.w, 0), (body.w, body.h // 3), (0, body.h // 2)])
        pygame.draw.polygon(top, (255, 255, 255, 40), [(body.w * 0.62, 0), (body.w * 0.7, 0), (body.w * 0.48, body.h),
                                                       (body.w * 0.40, body.h)])
        pygame.draw.circle(top, (255, 255, 255, 22), (body.w // 2, body.h // 2 + 10), body.h // 3, 18)
        screen.blit(top, body.topleft)
        pygame.draw.polygon(screen, theme.mix(accent, (255, 255, 255), 0.5), theme.chamfer(body, cut - 3), 2)
        theme.slashes(screen, c.x + 24, c.y + 22, 22, (255, 255, 255))
        Utils.draw_text_outline(screen, "TRAINER CARD", f["button"], WHITE, c.x + 74, c.y + 34, align="left",
                                outline_color=theme.shade(accent, 0.4), thickness=3)
        Utils.draw_text_outline(screen, f"IDNo. {self.facts['trainer_id']:05d}", f["label"], WHITE, c.right - 28,
                                c.y + 34, align="right", outline_color=theme.shade(accent, 0.4), thickness=2)

        inner = pygame.Rect(c.x + 18, c.y + 64, c.w - 36, c.h - 82)
        # The facts on dark rows, the trainer on the right.
        rows = pygame.Rect(inner.x + 4, inner.y + 8, inner.w - 286, 0)
        for k, (label, value) in enumerate(self.rows()):
            y = rows.y + k * 50
            row = pygame.Rect(rows.x, y, rows.w, 44)
            theme.alpha_poly(screen, (10, 10, 16), theme.chamfer(row, 8, tl=False, br=True, tr=False, bl=False), 150)
            pygame.draw.rect(screen, (255, 255, 255), (row.x, row.y, 5, row.h))
            theme.shadow_text(screen, label, f["label"], row.x + 18, y + 22 - f["label"].get_height() // 2,
                              color=theme.mix(accent, (255, 255, 255), 0.7))
            vf = f["s_med"] if f["s_med"].size(value)[0] <= rows.w - 200 else f["label"]
            theme.shadow_text(screen, value, vf, row.right - 14, y + 22 - vf.get_height() // 2, align="right")
        spot = pygame.Rect(inner.right - 262, inner.y + 8, 258, 262)
        theme.alpha_poly(screen, (10, 10, 16), theme.chamfer(spot, 14, tl=False), 120)
        pygame.draw.polygon(screen, theme.mix(accent, (255, 255, 255), 0.4), theme.chamfer(spot, 14, tl=False), 2)
        if self.trainer_img:
            screen.blit(self.trainer_img, self.trainer_img.get_rect(midbottom=(spot.centerx, spot.bottom - 6)))

        # The region's badges along the bottom.
        strip = pygame.Rect(inner.x + 4, inner.bottom - 84, inner.w - 8, 76)
        pygame.draw.polygon(screen, (24, 24, 30), theme.chamfer(strip, 12))
        pygame.draw.polygon(screen, theme.shade(accent, 0.6), theme.chamfer(strip, 12), 2)
        if not self.badges:
            Utils.draw_text_outline(screen, "No Gym badges in this region", f["label"], WHITE, strip.centerx,
                                    strip.centery, outline_color=(10, 10, 14), thickness=2)
            return
        step = strip.w / len(self.badges)
        for i, (sprite, earned) in enumerate(self.badges):
            cx = int(strip.x + step * (i + 0.5))
            pygame.draw.circle(screen, (40, 40, 48), (cx, strip.centery), 30)
            pygame.draw.circle(screen, theme.mix(accent, (255, 255, 255), 0.3) if earned else (60, 60, 70),
                               (cx, strip.centery), 30, 2)
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
            pygame.draw.polygon(screen, (24, 24, 30), theme.chamfer(r, 8))
            pygame.draw.polygon(screen, theme.PANEL_EDGE, theme.chamfer(r, 8), 1)
            icon = self.party_icons[i] if i < len(self.party_icons) else None
            if icon:
                screen.blit(icon, icon.get_rect(center=r.center))
