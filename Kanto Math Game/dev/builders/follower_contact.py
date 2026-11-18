"""A contact sheet of form followers for Jordan to look over: each row is the species' own sheet (a frame per
facing) beside the form's, normal on the left and shiny on the right, labelled.

    python dev/builders/follower_contact.py <out.png> <dex>_<form> [<dex>_<form> ...]
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame

OUT = os.path.join("assets", "dungeon", "followers")
CELL = 64


def frames(path):
    if not os.path.isfile(path):
        return None
    img = pygame.image.load(path).convert_alpha()
    cw, ch = img.get_width() // 4, img.get_height() // 4
    return [pygame.transform.scale(img.subsurface((0, r * ch, cw, ch)), (CELL, CELL)) for r in range(4)]


def contact(path, stems):
    font = pygame.font.SysFont("arial", 14)
    label_w = 140
    half = 8 * CELL + 16
    pic = pygame.Surface((label_w + 2 * half, len(stems) * (CELL + 4) + 4))
    pic.fill((214, 214, 222))
    for i, stem in enumerate(stems):
        y = 4 + i * (CELL + 4)
        pic.blit(font.render(stem, True, (20, 20, 30)), (6, y + CELL // 2 - 8))
        dex = stem.split("_")[0]
        for h, sub in enumerate(("", "shiny")):
            x = label_w + h * half
            for name in (dex, stem):
                fr = frames(os.path.join(OUT, sub, name + ".png"))
                for k in range(4):
                    if fr:
                        pic.blit(fr[k], (x, y))
                    else:
                        pygame.draw.line(pic, (200, 40, 40), (x + 4, y + 4), (x + CELL - 4, y + CELL - 4), 2)
                    x += CELL
                x += 6
    os.makedirs(os.path.dirname(path), exist_ok=True)
    pygame.image.save(pic, path)
    return path


def main():
    pygame.init()
    pygame.display.set_mode((8, 8))
    print(contact(sys.argv[1], sys.argv[2:]))


if __name__ == "__main__":
    main()
