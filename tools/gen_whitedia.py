"""改性白钻 / Modified White Diamond: textures + resources.

  * 催化剂     - sugar-shaped pile of redstone / lapis / emerald / amethyst dust
  * 待激发宝石 - brilliant-cut gem, deep blue
  * 改性白钻   - same brilliant cut, whiter and brighter than a diamond but not milk white
  * tools/armour - diamond art recoloured to the white-diamond palette
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

TOOLS = ["sword", "pickaxe", "axe", "shovel", "hoe"]
ARMOR = ["helmet", "chestplate", "leggings", "boots"]

# brilliant cut: (y, x0, x1) inclusive
GEM_ROWS = [
    (3, 5, 10),
    (4, 3, 12),
    (5, 2, 13),
    (6, 2, 13),
    (7, 2, 13),
    (8, 3, 12),
    (9, 4, 11),
    (10, 5, 10),
    (11, 6, 9),
    (12, 7, 8),
]

WHITE_RAMP = [(98, 108, 126), (146, 158, 176), (190, 202, 218), (226, 236, 246), (250, 254, 255)]
GEAR_RAMP = [(72, 104, 148), (108, 146, 190), (150, 190, 226), (196, 226, 248), (238, 250, 255)]
BLUE_RAMP = [(8, 14, 44), (16, 26, 72), (26, 42, 108), (40, 64, 150), (64, 96, 194)]

DUST = {
    "redstone": [(120, 20, 20), (170, 34, 34), (210, 60, 60), (240, 110, 110)],
    "lapis": [(18, 40, 96), (30, 62, 140), (52, 92, 178), (96, 138, 214)],
    "emerald": [(10, 78, 46), (18, 120, 70), (40, 168, 100), (110, 214, 150)],
    "amethyst": [(70, 40, 110), (108, 66, 156), (148, 100, 196), (196, 158, 232)],
}


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def ramp(colors, t):
    t = max(0.0, min(1.0, t))
    pos = t * (len(colors) - 1)
    i = int(pos)
    if i >= len(colors) - 1:
        return colors[-1]
    return lerp(colors[i], colors[i + 1], pos - i)


def lum(rgb):
    return 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]


def is_metal(rgb):
    import colorsys
    r, g, b = (c / 255.0 for c in rgb)
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    h *= 360.0
    if s < 0.20:
        return True
    return 140.0 <= h <= 230.0  # diamond cyan / blue


def gem(colors, seed=11, translucent=True):
    """Glass-like brilliant cut: crisp dark rim, see-through body, bright facets."""
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    px = img.load()
    mid = 7.5
    top = GEM_ROWS[0][0]

    for (y, x0, x1) in GEM_ROWS:
        for x in range(x0, x1 + 1):
            edge = min(x - x0, x1 - x)
            left = x < mid
            dy = y - top

            if dy <= 1:                     # table
                base = 0.97
            elif dy <= 3:                   # crown: left facet bright
                base = 0.70 + (0.20 if left else 0.0)
            elif dy <= 5:                   # girdle band: right facet bright
                base = 0.60 + (0.20 if not left else 0.0)
            else:                           # pavilion
                base = 0.58 - 0.06 * (dy - 6) + (0.16 if left else 0.0)

            alpha = 198                     # body: clearly see-through
            if edge == 0:
                base -= 0.66                # crisp dark rim
                alpha = 255
            elif edge == 1:
                base -= 0.22                # inner refraction line
                alpha = 236

            base = min(1.0, max(0.0, base))
            rgb = ramp(colors, base)
            px[x, y] = (rgb[0], rgb[1], rgb[2], alpha)

    # sparkles (opaque) so it reads as a cut stone rather than flat glass
    for (gx, gy) in ((4, 5), (5, 4), (10, 7), (9, 8), (7, 10)):
        if px[gx, gy][3] > 0:
            px[gx, gy] = (252, 254, 255, 255)
    return img


def make_catalyst(sugar):
    rnd = random.Random(777)
    out = Image.new("RGBA", sugar.size, (0, 0, 0, 0))
    px, sp = out.load(), sugar.load()
    keys = list(DUST)
    for y in range(sugar.size[1]):
        for x in range(sugar.size[0]):
            if sp[x, y][3] == 0:
                continue
            rgb = ramp(DUST[rnd.choice(keys)], rnd.random())
            px[x, y] = (rgb[0], rgb[1], rgb[2], 255)
    return out


def recolor(src, alpha=255, colors=None):
    out = Image.new("RGBA", src.size, (0, 0, 0, 0))
    px, dst = src.load(), out.load()
    vals = [lum(px[x, y][:3]) for y in range(src.size[1]) for x in range(src.size[0])
            if px[x, y][3] > 0 and is_metal(px[x, y][:3])]
    lo, hi = (min(vals), max(vals)) if vals else (0.0, 255.0)
    span = max(1.0, hi - lo)
    for y in range(src.size[1]):
        for x in range(src.size[0]):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            if not is_metal((r, g, b)):
                dst[x, y] = (r, g, b, a)
                continue
            t = (lum((r, g, b)) - lo) / span
            rgb = ramp(WHITE_RAMP, 0.22 + 0.74 * t)
            dst[x, y] = (rgb[0], rgb[1], rgb[2], int(a * alpha / 255))
    return out


def torch_texture(src):
    """Recolour the flame to a white-blue glow, keep the wooden stick."""
    out = src.copy()
    px = out.load()
    for y in range(out.size[1]):
        for x in range(out.size[0]):
            r, g, b, a = px[x, y]
            if a == 0 or lum((r, g, b)) < 150:
                continue
            t = (lum((r, g, b)) - 150) / 105.0
            rgb = ramp([(176, 214, 240), (214, 238, 252), (244, 252, 255)], 0.2 + 0.8 * min(1.0, t))
            px[x, y] = (rgb[0], rgb[1], rgb[2], a)
    return out


def save(img, rel):
    path = f"{TEX}/{rel}.png"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)
    print("texture", rel)


def write_json(rel, obj):
    path = os.path.join(RES, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.write("\n")


def write_tag(rel, values):
    path = os.path.join(RES, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    existing = []
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            existing = json.load(f).get("values", [])
    write_json(rel, {"values": list(dict.fromkeys(existing + values))})


NAMES_ZH = {
    "diamond_catalyst": "催化剂",
    "charged_gem": "待激发宝石",
    "white_diamond": "改性白钻",
    "white_diamond_sword": "改性白钻剑",
    "white_diamond_pickaxe": "改性白钻镐",
    "white_diamond_axe": "改性白钻斧",
    "white_diamond_shovel": "改性白钻锹",
    "white_diamond_hoe": "改性白钻锄",
    "white_diamond_helmet": "改性白钻头盔",
    "white_diamond_chestplate": "改性白钻胸甲",
    "white_diamond_leggings": "改性白钻护腿",
    "white_diamond_boots": "改性白钻靴子",
    "white_diamond_block": "白钻块",
    "white_torch": "白火把",
}
NAMES_EN = {
    "diamond_catalyst": "Diamond Catalyst",
    "charged_gem": "Charged Gem",
    "white_diamond": "Modified White Diamond",
    "white_diamond_sword": "White Diamond Sword",
    "white_diamond_pickaxe": "White Diamond Pickaxe",
    "white_diamond_axe": "White Diamond Axe",
    "white_diamond_shovel": "White Diamond Shovel",
    "white_diamond_hoe": "White Diamond Hoe",
    "white_diamond_helmet": "White Diamond Helmet",
    "white_diamond_chestplate": "White Diamond Chestplate",
    "white_diamond_leggings": "White Diamond Leggings",
    "white_diamond_boots": "White Diamond Boots",
    "white_diamond_block": "Block of White Diamond",
    "white_torch": "White Torch",
}

PATTERNS = {
    "sword": ["X", "X", "#"],
    "pickaxe": ["XXX", " # ", " # "],
    "axe": ["XX", "X#", " #"],
    "shovel": ["X", "#", "#"],
    "hoe": ["XX", " #", " #"],
}
ARMOR_PATTERNS = {
    "helmet": ["XXX", "X X"],
    "chestplate": ["X X", "XXX", "XXX"],
    "leggings": ["XXX", "X X", "X X"],
    "boots": ["X X", "X X"],
}


def gen_resources():
    handheld = {f"white_diamond_{t}" for t in TOOLS}
    block_items = {"white_diamond_block", "white_torch"}   # their models are built by hand below
    for item in NAMES_ZH:
        if item in block_items:
            continue
        parent = "minecraft:item/handheld" if item in handheld else "minecraft:item/generated"
        write_json(f"assets/{MOD}/items/{item}.json",
                   {"model": {"type": "minecraft:model", "model": f"{MOD}:item/{item}"}})
        write_json(f"assets/{MOD}/models/item/{item}.json",
                   {"parent": parent, "textures": {"layer0": f"{MOD}:item/{item}"}})

    write_json(f"assets/{MOD}/equipment/white_diamond.json", {
        "layers": {
            "humanoid": [{"texture": f"{MOD}:white_diamond"}],
            "humanoid_baby": [{"texture": f"{MOD}:white_diamond"}],
            "humanoid_leggings": [{"texture": f"{MOD}:white_diamond"}],
        }
    })

    # white diamond block + white torch
    write_json(f"assets/{MOD}/blockstates/white_diamond_block.json",
               {"variants": {"": {"model": f"{MOD}:block/white_diamond_block"}}})
    write_json(f"assets/{MOD}/models/block/white_diamond_block.json",
               {"parent": "minecraft:block/cube_all",
                "textures": {"all": f"{MOD}:block/white_diamond_block"}})
    write_json(f"assets/{MOD}/models/item/white_diamond_block.json",
               {"parent": f"{MOD}:block/white_diamond_block"})
    write_json(f"assets/{MOD}/items/white_diamond_block.json",
               {"model": {"type": "minecraft:model", "model": f"{MOD}:block/white_diamond_block"}})

    write_json(f"data/{MOD}/recipe/white_diamond_block.json", {
        "type": "minecraft:crafting_shaped", "category": "building",
        "key": {"#": f"{MOD}:white_diamond"},
        "pattern": ["###", "###", "###"],
        "result": {"id": f"{MOD}:white_diamond_block"},
    })
    write_json(f"data/{MOD}/recipe/white_diamond_from_block.json", {
        "type": "minecraft:crafting_shapeless", "category": "misc",
        "ingredients": [f"{MOD}:white_diamond_block"],
        "result": {"id": f"{MOD}:white_diamond", "count": 9},
    })
    # same column as the vanilla copper torch, but copper -> white diamond, 16 per craft
    write_json(f"data/{MOD}/recipe/white_torch.json", {
        "type": "minecraft:crafting_shaped", "category": "misc",
        "key": {
            "#": "minecraft:stick",
            "C": f"{MOD}:white_diamond",
            "X": ["minecraft:coal", "minecraft:charcoal"],
        },
        "pattern": ["C", "X", "#"],
        "result": {"id": f"{MOD}:white_torch", "count": 16},
    })
    write_tag("data/minecraft/tags/block/mineable/pickaxe.json", [f"{MOD}:white_diamond_block"])

    # 1 redstone + 1 lapis + 1 emerald + 1 amethyst -> 8 catalyst
    write_json(f"data/{MOD}/recipe/diamond_catalyst.json", {
        "type": "minecraft:crafting_shapeless", "category": "misc",
        "ingredients": ["minecraft:redstone", "minecraft:lapis_lazuli", "minecraft:emerald",
                        "minecraft:amethyst_shard"],
        "result": {"id": f"{MOD}:diamond_catalyst", "count": 8},
    })
    # diamond + 4 catalyst in a cross -> charged gem
    write_json(f"data/{MOD}/recipe/charged_gem.json", {
        "type": "minecraft:crafting_shaped", "category": "misc",
        "key": {"C": f"{MOD}:diamond_catalyst", "D": "minecraft:diamond", "Q": "minecraft:quartz"},
        "pattern": ["QCQ", "CDC", "QCQ"],
        "result": {"id": f"{MOD}:charged_gem", "count": 2},
    })
    # blast furnace only
    write_json(f"data/{MOD}/recipe/white_diamond_from_blasting.json", {
        "type": "minecraft:blasting", "category": "misc",
        "cookingtime": 200, "experience": 1.0, "group": "white_diamond",
        "ingredient": f"{MOD}:charged_gem",
        "result": {"id": f"{MOD}:white_diamond"},
    })

    for tool, pattern in PATTERNS.items():
        write_json(f"data/{MOD}/recipe/white_diamond_{tool}.json", {
            "type": "minecraft:crafting_shaped", "category": "equipment",
            "key": {"#": "minecraft:stick", "X": f"{MOD}:white_diamond"},
            "pattern": pattern,
            "result": {"id": f"{MOD}:white_diamond_{tool}"},
        })
    for piece, pattern in ARMOR_PATTERNS.items():
        write_json(f"data/{MOD}/recipe/white_diamond_{piece}.json", {
            "type": "minecraft:crafting_shaped", "category": "equipment",
            "key": {"X": f"{MOD}:white_diamond"},
            "pattern": pattern,
            "result": {"id": f"{MOD}:white_diamond_{piece}"},
        })

    write_tag(f"data/{MOD}/tags/item/white_diamond_repair_materials.json", [f"{MOD}:white_diamond"])
    write_tag("data/minecraft/tags/item/swords.json", [f"{MOD}:white_diamond_sword"])
    write_tag("data/minecraft/tags/item/pickaxes.json", [f"{MOD}:white_diamond_pickaxe"])
    write_tag("data/minecraft/tags/item/axes.json", [f"{MOD}:white_diamond_axe"])
    write_tag("data/minecraft/tags/item/shovels.json", [f"{MOD}:white_diamond_shovel"])
    write_tag("data/minecraft/tags/item/hoes.json", [f"{MOD}:white_diamond_hoe"])
    write_tag("data/minecraft/tags/item/head_armor.json", [f"{MOD}:white_diamond_helmet"])
    write_tag("data/minecraft/tags/item/chest_armor.json", [f"{MOD}:white_diamond_chestplate"])
    write_tag("data/minecraft/tags/item/leg_armor.json", [f"{MOD}:white_diamond_leggings"])
    write_tag("data/minecraft/tags/item/foot_armor.json", [f"{MOD}:white_diamond_boots"])

    for lang, table in (("zh_cn", NAMES_ZH), ("en_us", NAMES_EN)):
        path = f"{RES}/assets/{MOD}/lang/{lang}.json"
        data = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
        for k, v in table.items():
            if k in ("white_diamond_block", "white_torch"):
                data[f"block.{MOD}.{k}"] = v
            data[f"item.{MOD}.{k}"] = v
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")


def gen_torch_assets(z):
    rename = {"minecraft:block/torch": f"{MOD}:block/white_torch",
              "minecraft:block/wall_torch": f"{MOD}:block/white_wall_torch",
              "minecraft:item/torch": f"{MOD}:item/white_torch"}
    for name in ("torch", "wall_torch"):
        bs = json.loads(z.read(f"assets/minecraft/blockstates/{name}.json"))
        for variant in bs.get("variants", {}).values():
            if "model" in variant:
                variant["model"] = rename.get(variant["model"], variant["model"])
        write_json(f"assets/{MOD}/blockstates/white_{name}.json", bs)
    for name in ("torch", "wall_torch"):
        raw = z.read(f"assets/minecraft/models/block/{name}.json").decode("utf-8")
        for old, new in rename.items():
            raw = raw.replace(old, new)
        write_json(f"assets/{MOD}/models/block/white_{name}.json", json.loads(raw))
    # torch item also shows the 3D block model
    write_json(f"assets/{MOD}/models/item/white_torch.json",
               {"parent": f"{MOD}:block/white_torch"})
    write_json(f"assets/{MOD}/items/white_torch.json",
               {"model": {"type": "minecraft:model", "model": f"{MOD}:block/white_torch"}})


def gen_diamond_substitutions():
    """Optional: white diamond stands in for diamond."""
    conditions = [{"type": f"{MOD}:config_enabled", "option": "white_diamond_as_diamond"}]
    count = 0
    with zipfile.ZipFile(JAR) as z:
        for n in z.namelist():
            if not n.startswith("data/minecraft/recipe/") or not n.endswith(".json"):
                continue
            rec = json.loads(z.read(n))
            text = json.dumps(rec)
            if "minecraft:diamond" not in text:
                continue
            res = rec.get("result")
            if isinstance(res, dict) and str(res.get("id", "")).startswith(f"{MOD}:"):
                continue
            new = {k: (v if k == "result" else _sub_diamond(v)) for k, v in rec.items()}
            if json.dumps(new, sort_keys=True) == json.dumps(rec, sort_keys=True):
                continue
            new["neoforge:conditions"] = conditions
            out = f"diamond_sub_{n.rsplit('/', 1)[-1][:-5]}"
            write_json(f"data/{MOD}/recipe/{out}.json", new)
            count += 1
    print("diamond substitution recipes:", count)


def _sub_diamond(obj):
    if isinstance(obj, str):
        return f"{MOD}:white_diamond" if obj == "minecraft:diamond" else obj
    if isinstance(obj, list):
        return [_sub_diamond(v) for v in obj]
    if isinstance(obj, dict):
        return {k: _sub_diamond(v) for k, v in obj.items()}
    return obj


def main():
    with zipfile.ZipFile(JAR) as z:
        def load(path):
            with z.open(path) as f:
                return Image.open(f).convert("RGBA")

        save(make_catalyst(load("assets/minecraft/textures/item/sugar.png")), "item/diamond_catalyst")
        save(recolor(load("assets/minecraft/textures/block/diamond_block.png")), "block/white_diamond_block")
        save(torch_texture(load("assets/minecraft/textures/block/torch.png")), "block/white_torch")
        gen_torch_assets(z)
        save(gem(BLUE_RAMP), "item/charged_gem")
        save(gem(WHITE_RAMP), "item/white_diamond")

        for tool in TOOLS:
            save(recolor(load(f"assets/minecraft/textures/item/diamond_{tool}.png"), colors=GEAR_RAMP), f"item/white_diamond_{tool}")
        for piece in ARMOR:
            save(recolor(load(f"assets/minecraft/textures/item/diamond_{piece}.png"), colors=GEAR_RAMP), f"item/white_diamond_{piece}")

        for layer, path in (("humanoid", "assets/minecraft/textures/entity/equipment/humanoid/diamond.png"),
                            ("humanoid_leggings", "assets/minecraft/textures/entity/equipment/humanoid_leggings/diamond.png")):
            save(recolor(load(path), colors=GEAR_RAMP), f"entity/equipment/{layer}/white_diamond")

    gen_resources()
    gen_diamond_substitutions()
    print("white diamond written")


if __name__ == "__main__":
    main()
