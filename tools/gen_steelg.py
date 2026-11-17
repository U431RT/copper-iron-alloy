"""钢金 / Steel-Gold: textures + resources.

  * 粗钢金混合物   - sugar-shaped pile of gold / steel / charcoal dust
  * 钢金锭         - dark glossy steel ingot with a gold rim
  * tools / armour - same dark steel, same gold rim
  * worn armour    - plain dark steel, no gold
"""

import json
import os
import random
import zipfile

from PIL import Image

JAR = r"D:/GAME/MC1.26.2/1.26.2/.minecraft/libraries/net/neoforged/minecraft-client-patched/26.1.2.78/minecraft-client-patched-26.1.2.78.jar"
RES = r"D:/dshworkshop/copper_iron_alloy/src/main/resources"
MOD = "copper_iron_alloy"
TEX = f"{RES}/assets/{MOD}/textures"

STEEL = [(22, 22, 28), (34, 34, 42), (48, 48, 58), (66, 66, 78), (86, 86, 100),
         (110, 110, 126), (142, 142, 162), (186, 186, 206), (246, 246, 255)]
GOLD = [(150, 100, 20), (198, 140, 32), (232, 178, 56), (250, 214, 96), (255, 244, 190)]
GOLD_DUST = [(178, 124, 30), (214, 158, 44), (244, 196, 70), (255, 232, 140)]
STEEL_DUST = [(56, 56, 64), (88, 88, 98), (128, 128, 140), (172, 172, 184)]
CHARCOAL = [(26, 24, 24), (44, 42, 42), (66, 62, 62), (92, 88, 86)]

TOOLS = ["sword", "pickaxe", "axe", "shovel", "hoe"]
ARMOR = ["helmet", "chestplate", "leggings", "boots"]


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def ramp(colors, t):
    t = max(0.0, min(1.0, t))
    pos = t * (len(colors) - 1)
    i = int(pos)
    if i >= len(colors) - 1:
        return colors[-1]
    return lerp(colors[i], colors[i + 1], pos - i)


def is_metal(rgb):
    import colorsys
    r, g, b = (c / 255.0 for c in rgb)
    h, sa, v = colorsys.rgb_to_hsv(r, g, b)
    h *= 360.0
    if sa < 0.18:
        return True
    return h < 32.0 and sa > 0.35


def lum(rgb):
    return 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]


def load_from_jar(z, path):
    with z.open(path) as f:
        return Image.open(f).convert("RGBA")


def silhouette_edges(img):
    """Pixels that touch transparency -> the rim we paint gold."""
    w, h = img.size
    edge = set()
    px = img.load()
    for y in range(h):
        for x in range(w):
            if px[x, y][3] == 0:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if not (0 <= nx < w and 0 <= ny < h) or px[nx, ny][3] == 0:
                    edge.add((x, y))
                    break
    return edge


def steelify(img, alpha=255, gold_rim=True, gold_chance=0.85, seed=7):
    rnd = random.Random(seed)
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    src, dst = img.load(), out.load()
    vals = [lum(src[x, y][:3]) for y in range(img.size[1]) for x in range(img.size[0]) if src[x, y][3] > 0]
    lo, hi = (min(vals), max(vals)) if vals else (0.0, 255.0)
    span = max(1.0, hi - lo)
    edge = silhouette_edges(img) if gold_rim else set()
    edge = {(x, y) for (x, y) in edge if is_metal(src[x, y][:3])}

    for y in range(img.size[1]):
        for x in range(img.size[0]):
            r, g, b, a = src[x, y]
            if a == 0:
                continue
            if not is_metal((r, g, b)):
                dst[x, y] = (r, g, b, int(a * alpha / 255))
                continue
            t = (lum((r, g, b)) - lo) / span
            rgba = ramp(STEEL, 0.02 + 0.66 * t)
            if gold_rim and (x, y) in edge and rnd.random() < gold_chance:
                rgba = ramp(GOLD, 0.25 + 0.7 * t)
            dst[x, y] = (rgba[0], rgba[1], rgba[2], int(a * alpha / 255))
    return out


def make_mixture(sugar):
    rnd = random.Random(4242)
    out = Image.new("RGBA", sugar.size, (0, 0, 0, 0))
    px, sp = out.load(), sugar.load()
    for y in range(sugar.size[1]):
        for x in range(sugar.size[0]):
            _, _, _, a = sp[x, y]
            if a == 0:
                continue
            bucket = rnd.random()
            if bucket < 0.30:
                rgba = ramp(GOLD_DUST, rnd.random())
            elif bucket < 0.70:
                rgba = ramp(STEEL_DUST, rnd.random())
            else:
                rgba = ramp(CHARCOAL, rnd.random())
            px[x, y] = (rgba[0], rgba[1], rgba[2], a)
    # a few bright grains
    spots = 0
    while spots < 8:
        x, y = rnd.randrange(16), rnd.randrange(16)
        if px[x, y][3] == 0:
            continue
        c = rnd.choice([(255, 236, 150), (232, 232, 244)])
        px[x, y] = (c[0], c[1], c[2], 255)
        spots += 1
    return out


def save(img, rel):
    path = f"{TEX}/{rel}.png"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)
    print("texture", rel)


def write_tag(rel, values):
    path = os.path.join(RES, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    existing = []
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            existing = json.load(f).get("values", [])
    merged = list(dict.fromkeys(existing + values))
    write_json(rel, {"values": merged})


def write_json(rel, obj):
    path = os.path.join(RES, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.write("\n")


NAMES_ZH = {
    "raw_steel_gold_mixture": "粗钢金混合物",
    "steel_gold_ingot": "钢金锭",
    "steel_gold_sword": "钢金剑",
    "steel_gold_pickaxe": "钢金镐",
    "steel_gold_axe": "钢金斧",
    "steel_gold_shovel": "钢金锹",
    "steel_gold_hoe": "钢金锄",
    "steel_gold_helmet": "钢金头盔",
    "steel_gold_chestplate": "钢金胸甲",
    "steel_gold_leggings": "钢金护腿",
    "steel_gold_boots": "钢金靴子",
}
NAMES_EN = {
    "raw_steel_gold_mixture": "Raw Steel-Gold Mixture",
    "steel_gold_ingot": "Steel-Gold Ingot",
    "steel_gold_sword": "Steel-Gold Sword",
    "steel_gold_pickaxe": "Steel-Gold Pickaxe",
    "steel_gold_axe": "Steel-Gold Axe",
    "steel_gold_shovel": "Steel-Gold Shovel",
    "steel_gold_hoe": "Steel-Gold Hoe",
    "steel_gold_helmet": "Steel-Gold Helmet",
    "steel_gold_chestplate": "Steel-Gold Chestplate",
    "steel_gold_leggings": "Steel-Gold Leggings",
    "steel_gold_boots": "Steel-Gold Boots",
}


def gen_resources():
    handheld = {f"steel_gold_{t}" for t in TOOLS}
    for item in NAMES_ZH:
        parent = "minecraft:item/handheld" if item in handheld else "minecraft:item/generated"
        write_json(f"assets/{MOD}/items/{item}.json",
                   {"model": {"type": "minecraft:model", "model": f"{MOD}:item/{item}"}})
        write_json(f"assets/{MOD}/models/item/{item}.json",
                   {"parent": parent, "textures": {"layer0": f"{MOD}:item/{item}"}})

    write_json(f"assets/{MOD}/equipment/steel_gold.json", {
        "layers": {
            "humanoid": [{"texture": f"{MOD}:steel_gold"}],
            "humanoid_baby": [{"texture": f"{MOD}:steel_gold"}],
            "humanoid_leggings": [{"texture": f"{MOD}:steel_gold"}],
        }
    })

    # recipes
    write_json(f"data/{MOD}/recipe/raw_steel_gold_mixture.json", {
        "type": "minecraft:crafting_shaped",
        "category": "misc",
        "key": {"G": "minecraft:gold_ingot", "#": "minecraft:charcoal", "I": "minecraft:iron_ingot"},
        "pattern": ["G#G", "#I#", "G#G"],
        "result": {"id": f"{MOD}:raw_steel_gold_mixture", "count": 3},
    })
    write_json(f"data/{MOD}/recipe/steel_gold_ingot_from_blasting.json", {
        "type": "minecraft:blasting",
        "category": "misc",
        "cookingtime": 100,
        "experience": 0.7,
        "group": "steel_gold_ingot",
        "ingredient": f"{MOD}:raw_steel_gold_mixture",
        "result": {"id": f"{MOD}:steel_gold_ingot"},
    })

    patterns = {
        "sword": ["X", "X", "#"],
        "pickaxe": ["XXX", " # ", " # "],
        "axe": ["XX", "X#", " #"],
        "shovel": ["X", "#", "#"],
        "hoe": ["XX", " #", " #"],
    }
    armor_patterns = {
        "helmet": ["XXX", "X X"],
        "chestplate": ["X X", "XXX", "XXX"],
        "leggings": ["XXX", "X X", "X X"],
        "boots": ["X X", "X X"],
    }
    for tool, pattern in patterns.items():
        write_json(f"data/{MOD}/recipe/steel_gold_{tool}.json", {
            "type": "minecraft:crafting_shaped",
            "category": "equipment",
            "key": {"#": "minecraft:stick", "X": f"{MOD}:steel_gold_ingot"},
            "pattern": pattern,
            "result": {"id": f"{MOD}:steel_gold_{tool}"},
        })
    for piece, pattern in armor_patterns.items():
        write_json(f"data/{MOD}/recipe/steel_gold_{piece}.json", {
            "type": "minecraft:crafting_shaped",
            "category": "equipment",
            "key": {"X": f"{MOD}:steel_gold_ingot"},
            "pattern": pattern,
            "result": {"id": f"{MOD}:steel_gold_{piece}"},
        })

    # tags: piglin-safe armour is handled in code, but gear tags are needed for enchanting
    write_json(f"data/{MOD}/tags/item/steel_gold_repair_materials.json",
               {"values": [f"{MOD}:steel_gold_ingot"]})
    write_tag("data/minecraft/tags/item/swords.json", [f"{MOD}:steel_gold_sword"])
    write_tag("data/minecraft/tags/item/pickaxes.json", [f"{MOD}:steel_gold_pickaxe"])
    write_tag("data/minecraft/tags/item/axes.json", [f"{MOD}:steel_gold_axe"])
    write_tag("data/minecraft/tags/item/shovels.json", [f"{MOD}:steel_gold_shovel"])
    write_tag("data/minecraft/tags/item/hoes.json", [f"{MOD}:steel_gold_hoe"])
    write_tag("data/minecraft/tags/item/head_armor.json", [f"{MOD}:steel_gold_helmet"])
    write_tag("data/minecraft/tags/item/chest_armor.json", [f"{MOD}:steel_gold_chestplate"])
    write_tag("data/minecraft/tags/item/leg_armor.json", [f"{MOD}:steel_gold_leggings"])
    write_tag("data/minecraft/tags/item/foot_armor.json", [f"{MOD}:steel_gold_boots"])

    # lang (merge)
    for lang, table in (("zh_cn", NAMES_ZH), ("en_us", NAMES_EN)):
        path = f"{RES}/assets/{MOD}/lang/{lang}.json"
        data = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
        for k, v in table.items():
            data[f"item.{MOD}.{k}"] = v
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")


def main():
    with zipfile.ZipFile(JAR) as z:
        sugar = load_from_jar(z, "assets/minecraft/textures/item/sugar.png")
        save(make_mixture(sugar), "item/raw_steel_gold_mixture")

        ingot = load_from_jar(z, "assets/minecraft/textures/item/iron_ingot.png")
        save(steelify(ingot, gold_rim=True, gold_chance=0.95), "item/steel_gold_ingot")

        for tool in TOOLS:
            src = load_from_jar(z, f"assets/minecraft/textures/item/iron_{tool}.png")
            save(steelify(src, gold_rim=True, gold_chance=1.0), f"item/steel_gold_{tool}")
        for piece in ARMOR:
            src = load_from_jar(z, f"assets/minecraft/textures/item/iron_{piece}.png")
            save(steelify(src, gold_rim=True, gold_chance=1.0), f"item/steel_gold_{piece}")

        # worn armour: dark steel only, no gold
        for layer, path in (("humanoid", "assets/minecraft/textures/entity/equipment/humanoid/iron.png"),
                            ("humanoid_leggings", "assets/minecraft/textures/entity/equipment/humanoid_leggings/iron.png")):
            src = load_from_jar(z, path)
            save(steelify(src, gold_rim=False), f"entity/equipment/{layer}/steel_gold")

    gen_resources()
    print("steel-gold written")


if __name__ == "__main__":
    main()
