"""Generates the Copper-Iron Alloy textures from the vanilla 26.1.2 art.

Rules from the design brief:
  * 铁铜合金 (ingot / tools / armour) - copper art, slightly transparent, faded / whitened
  * 粗铁铜混合物                      - raw copper + raw iron crushed into powder, mixed
  * 铁铜合金剪刀 / 水桶 / 岩浆桶       - copper-coloured metal, fluid colours untouched
  * 岩浆桶 3 stages                   - chipped like an anvil before it shatters
"""

import colorsys
import random

from PIL import Image

VANILLA = "D:/dshworkshop/_cia/tex/assets/minecraft/textures"
OUT = "D:/dshworkshop/copper_iron_alloy/src/main/resources/assets/copper_iron_alloy/textures"

COPPER_RAMP = [
    (66, 28, 17), (95, 44, 28), (128, 57, 33), (156, 78, 49), (193, 90, 54),
    (214, 109, 72), (231, 124, 86), (252, 153, 130), (253, 212, 203),
]
IRON_RAMP = [
    (24, 24, 24), (53, 53, 53), (94, 94, 94), (130, 130, 130), (168, 168, 168),
    (200, 200, 200), (224, 224, 224), (244, 244, 244), (255, 255, 255),
]
ALLOY_RAMP = [
    (92, 48, 30), (124, 68, 44), (152, 88, 58), (178, 108, 74), (202, 128, 92),
    (222, 146, 104), (236, 164, 122), (246, 182, 142), (252, 198, 160),
]
RAW_IRON_RAMP = [
    (59, 52, 41), (87, 77, 57), (136, 116, 85), (175, 142, 119),
    (216, 175, 147), (233, 200, 177), (254, 222, 200), (254, 244, 237),
]

CRACK_DARK = (58, 32, 22, 255)
CRACK_LIGHT = (120, 64, 40, 255)

# 1px crack lines, stage 1 then the extra stage 2 pixels
CRACKS = [
    [(5, 7), (6, 8), (6, 9)],
    [(9, 5), (9, 6), (10, 7), (4, 11), (5, 11)],
]


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def ramp_lookup(ramp, t):
    t = max(0.0, min(1.0, t))
    pos = t * (len(ramp) - 1)
    i = int(pos)
    if i >= len(ramp) - 1:
        return ramp[-1]
    return lerp(ramp[i], ramp[i + 1], pos - i)


def lum(rgb):
    return 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]


def hsv(rgb):
    r, g, b = (c / 255.0 for c in rgb)
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    return h * 360.0, s, v


def is_metal(rgb):
    h, s, v = hsv(rgb)
    if s < 0.18:
        return True
    return h < 32.0 and s > 0.35


def is_grey(rgb):
    _, s, _ = hsv(rgb)
    return s < 0.18


def load(path):
    return Image.open(path).convert("RGBA")


def pixel_map(img, fn):
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    src, dst = img.load(), out.load()
    for y in range(img.size[1]):
        for x in range(img.size[0]):
            c = src[x, y]
            res = fn(x, y, c)
            dst[x, y] = c if res is None else res
    return out


def recolor(img, ramp=ALLOY_RAMP, alpha=255, only_greys=False):
    """Recolour metal pixels along a ramp; leaves wooden handles / fluids alone."""
    checker = is_grey if only_greys else is_metal
    vals = []
    for y in range(img.size[1]):
        for x in range(img.size[0]):
            r, g, b, a = img.getpixel((x, y))
            if a > 0 and checker((r, g, b)):
                vals.append(lum((r, g, b)))
    lo, hi = (min(vals), max(vals)) if vals else (0.0, 255.0)
    rng = max(1.0, hi - lo)

    def fn(x, y, c):
        r, g, b, a = c
        if a == 0 or not checker((r, g, b)):
            return None
        t = (lum((r, g, b)) - lo) / rng
        rgb = ramp_lookup(ramp, 0.05 + 0.78 * t)
        return (rgb[0], rgb[1], rgb[2], int(a * alpha / 255))

    return pixel_map(img, fn)


def make_mixture(img):
    """Raw copper and raw iron knocked into coarse powder, then shovelled together."""
    rnd = random.Random(20261116)
    src = img.copy()
    px = src.load()
    w, h = src.size

    vals = [lum(px[x, y][:3]) for y in range(h) for x in range(w) if px[x, y][3] > 0]
    lo, hi = (min(vals), max(vals)) if vals else (0.0, 255.0)
    rng = max(1.0, hi - lo)

    out = Image.new("RGBA", src.size, (0, 0, 0, 0))
    dst = out.load()
    cells = {}

    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            t = (lum((r, g, b)) - lo) / rng
            if t < 0.16:
                dst[x, y] = (74, 60, 48, a)
                continue
            cell = (x // 2, y // 2)
            cells.setdefault(cell, rnd.random())
            tg = max(0.0, min(1.0, t + rnd.uniform(-0.13, 0.13)))
            is_copper = cells[cell] >= 0.62 or rnd.random() < 0.24
            if is_copper:
                rgb = ramp_lookup(COPPER_RAMP, 0.25 + 0.62 * tg)
            elif rnd.random() < 0.4:
                rgb = ramp_lookup(IRON_RAMP, 0.28 + 0.58 * tg)
            else:
                rgb = ramp_lookup(RAW_IRON_RAMP, 0.22 + 0.70 * tg)
            dst[x, y] = (rgb[0], rgb[1], rgb[2], a)

    grains = 0
    while grains < 22:
        x, y = rnd.randrange(w), rnd.randrange(h)
        if dst[x, y][3] == 0 or lum(dst[x, y][:3]) < 90:
            continue
        dst[x, y] = (232, 148, 118, 255) if grains % 3 else (226, 206, 186, 255)
        grains += 1
    spilled = 0
    while spilled < 6:
        x, y = rnd.randrange(1, w - 1), rnd.randrange(1, h - 1)
        if dst[x, y][3] != 0:
            continue
        if not any(dst[x + dx, y + dy][3] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            continue
        dst[x, y] = (198, 124, 96, 210) if spilled % 3 == 0 else (204, 186, 168, 210)
        spilled += 1
    return out


def bucket_with_content(name, alpha=255):
    """Recolour the bucket frame only; keep whatever the vanilla texture puts inside.

    Comparing against the vanilla empty bucket gives an exact "content" mask, so milk /
    powder snow / water / lava keep their original colours.
    """
    empty_src = load(f"{VANILLA}/item/bucket.png")
    filled = load(f"{VANILLA}/item/{name}.png")
    result = recolor(empty_src, alpha=alpha, only_greys=True)
    for y in range(result.size[1]):
        for x in range(result.size[0]):
            fc = filled.getpixel((x, y))
            ec = empty_src.getpixel((x, y))
            if fc == ec or fc[3] == 0:
                continue
            result.putpixel((x, y), fc)
    return result


def add_cracks(img, stage):
    """Draw anvil-style cracks; stage 1 = chipped, stage 2 = badly damaged."""
    out = img.copy()
    px = out.load()
    for line in CRACKS[:stage]:
        for i, (x, y) in enumerate(line):
            if px[x, y][3] == 0:
                continue
            px[x, y] = CRACK_DARK if i % 2 == 0 else CRACK_LIGHT
    return out


def save(img, rel):
    import os

    path = f"{OUT}/{rel}"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)
    print("wrote", rel, img.size)


def main():
    item = f"{VANILLA}/item"
    equip = f"{VANILLA}/entity/equipment"

    # --- ingot + mixture -------------------------------------------
    copper_ingot = load(f"{item}/copper_ingot.png")
    save(recolor(copper_ingot, alpha=225), "item/iron_copper_alloy_ingot.png")
    save(make_mixture(load(f"{item}/raw_copper.png")), "item/raw_iron_copper_mixture.png")

    # --- tools ------------------------------------------------------
    for tool in ("sword", "pickaxe", "axe", "shovel", "hoe"):
        src = load(f"{item}/copper_{tool}.png")
        save(recolor(src, alpha=225), f"item/iron_copper_alloy_{tool}.png")

    # --- armour icons ----------------------------------------------
    for piece in ("helmet", "chestplate", "leggings", "boots"):
        src = load(f"{item}/copper_{piece}.png")
        save(recolor(src, alpha=225), f"item/iron_copper_alloy_{piece}.png")

    # --- worn armour layers ----------------------------------------
    save(recolor(load(f"{equip}/humanoid/copper.png")),
         "entity/equipment/humanoid/iron_copper_alloy.png")
    save(recolor(load(f"{equip}/humanoid_leggings/copper.png")),
         "entity/equipment/humanoid_leggings/iron_copper_alloy.png")

    # --- shears -----------------------------------------------------
    save(recolor(load(f"{item}/shears.png"), alpha=225), "item/iron_copper_alloy_shears.png")

    # --- buckets ----------------------------------------------------
    empty = recolor(load(f"{item}/bucket.png"), only_greys=True)
    save(empty, "item/iron_copper_alloy_bucket.png")
    save(add_cracks(empty, 1), "item/iron_copper_alloy_bucket_1.png")
    save(add_cracks(empty, 2), "item/iron_copper_alloy_bucket_2.png")

    save(bucket_with_content("water_bucket"), "item/iron_copper_alloy_water_bucket.png")
    save(bucket_with_content("powder_snow_bucket"), "item/iron_copper_alloy_powder_snow_bucket.png")
    save(bucket_with_content("milk_bucket"), "item/iron_copper_alloy_milk_bucket.png")

    lava = bucket_with_content("lava_bucket")
    save(lava, "item/iron_copper_alloy_lava_bucket.png")
    save(add_cracks(lava, 1), "item/iron_copper_alloy_lava_bucket_1.png")
    save(add_cracks(lava, 2), "item/iron_copper_alloy_lava_bucket_2.png")


if __name__ == "__main__":
    main()
