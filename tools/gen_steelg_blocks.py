"""钢金块 / 钢金砧 / 钢金门 / 钢金打火石：纹理与资源。

纹理都在原版贴图上重染：黑亮钢身 + 整圈金边（打火石只改那个 C 形的金属部分）。
"""

import json
import os
import zipfile

from PIL import Image

JAR = r"D:/GAME/MC1.26.2/1.26.2/.minecraft/libraries/net/neoforged/minecraft-client-patched/26.1.2.78/minecraft-client-patched-26.1.2.78.jar"
RES = r"D:/dshworkshop/copper_iron_alloy/src/main/resources"
MOD = "copper_iron_alloy"
TEX = f"{RES}/assets/{MOD}/textures"

STEEL = [(22, 22, 28), (34, 34, 42), (48, 48, 58), (66, 66, 78), (86, 86, 100),
         (110, 110, 126), (142, 142, 162), (186, 186, 206), (246, 246, 255)]
GOLD = [(150, 100, 20), (198, 140, 32), (232, 178, 56), (250, 214, 96), (255, 244, 190)]


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


def steel_pixel(rgb, t):
    return ramp(STEEL, 0.02 + 0.66 * t)


def steelify(img, border_gold=False, only_bright=False):
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    src, dst = img.load(), out.load()
    w, h = img.size
    vals = [lum(src[x, y][:3]) for y in range(h) for x in range(w) if src[x, y][3] > 0]
    lo, hi = (min(vals), max(vals)) if vals else (0.0, 255.0)
    span = max(1.0, hi - lo)

    for y in range(h):
        for x in range(w):
            r, g, b, a = src[x, y]
            if a == 0:
                continue
            t = (lum((r, g, b)) - lo) / span
            if only_bright and lum((r, g, b)) < 110:
                dst[x, y] = (r, g, b, a)  # keep flint dark
                continue
            if border_gold and (x in (0, w - 1) or y in (0, h - 1)):
                rgb = ramp(GOLD, 0.35 + 0.6 * t)
            else:
                rgb = steel_pixel((r, g, b), t)
            dst[x, y] = (rgb[0], rgb[1], rgb[2], a)
    return out


def steel_with_gold_outline(img, brightness=110, lift=0.0):
    """Only the bright metal part is recoloured; its outer outline becomes gold."""
    src = img.load()
    w, h = img.size
    mask = set()
    for y in range(h):
        for x in range(w):
            r, g, b, a = src[x, y]
            if a > 0 and lum((r, g, b)) >= brightness:
                mask.add((x, y))
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    dst = out.load()
    for y in range(h):
        for x in range(w):
            r, g, b, a = src[x, y]
            if a == 0:
                continue
            if (x, y) not in mask:
                dst[x, y] = (r, g, b, a)
                continue
            t = lum((r, g, b)) / 255.0
            on_rim = any(
                (not (0 <= x + dx < w and 0 <= y + dy < h))           # outside the image
                or src[x + dx, y + dy][3] == 0                         # transparent neighbour
                or ((x + dx, y + dy) not in mask)                      # neighbour that is not metal (flint)
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            rgb = ramp(GOLD, 0.35 + 0.6 * t) if on_rim else steel_pixel((r, g, b), min(1.0, t + lift))
            dst[x, y] = (rgb[0], rgb[1], rgb[2], a)
    return out


def frame_gold(img):
    """1px gold frame around a fully opaque panel (door faces)."""
    out = img.copy()
    px = out.load()
    w, h = out.size
    for y in range(h):
        for x in range(w):
            if px[x, y][3] == 0:
                continue
            if x in (0, w - 1) or y in (0, h - 1):
                t = lum(px[x, y][:3]) / 255.0
                rgb = ramp(GOLD, 0.35 + 0.6 * t)
                px[x, y] = (rgb[0], rgb[1], rgb[2], 255)
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


def rewrite(obj, mapping):
    if isinstance(obj, str):
        return mapping.get(obj, obj)
    if isinstance(obj, list):
        return [rewrite(v, mapping) for v in obj]
    if isinstance(obj, dict):
        return {k: rewrite(v, mapping) for k, v in obj.items()}
    return obj


def main():
    with zipfile.ZipFile(JAR) as z:
        def load(path):
            with z.open(path) as f:
                return Image.open(f).convert("RGBA")

        iron_block = load("assets/minecraft/textures/block/iron_block.png")
        anvil = load("assets/minecraft/textures/block/anvil.png")

        # in-world models: plain black steel, no gold
        save(steelify(iron_block), "block/steel_gold_block")
        save(steelify(anvil), "block/steel_gold_anvil")
        save(steelify(load("assets/minecraft/textures/block/anvil_top.png")), "block/steel_gold_anvil_top")

        # inventory icons: gold rim kept
        save(frame_gold(steelify(iron_block)), "item/steel_gold_block")
        save(frame_gold(steelify(anvil)), "item/steel_gold_anvil")

        # lamp: bright steel core (always lit look), no gold in world
        bulb = load("assets/minecraft/textures/block/copper_bulb_lit.png")
        lamp = steelify(bulb)
        save(lamp, "block/steel_gold_lamp")
        save(frame_gold(lamp), "item/steel_gold_lamp")
        save(steelify(load("assets/minecraft/textures/block/copper_door_top.png")), "block/steel_gold_door_top")
        save(steelify(load("assets/minecraft/textures/block/copper_door_bottom.png")), "block/steel_gold_door_bottom")
        save(steel_with_gold_outline(load("assets/minecraft/textures/item/copper_door.png"), brightness=0, lift=0.3),
             "item/steel_gold_door")
        save(steel_with_gold_outline(load("assets/minecraft/textures/item/flint_and_steel.png")),
             "item/steel_gold_flint_and_steel")

        # ---- block: simple cube ----
        write_json(f"assets/{MOD}/blockstates/steel_gold_block.json",
                   {"variants": {"": {"model": f"{MOD}:block/steel_gold_block"}}})
        write_json(f"assets/{MOD}/models/block/steel_gold_block.json",
                   {"parent": "minecraft:block/cube_all",
                    "textures": {"all": f"{MOD}:block/steel_gold_block"}})
        write_json(f"assets/{MOD}/models/item/steel_gold_block.json",
                   {"parent": f"{MOD}:block/steel_gold_block"})
        write_json(f"assets/{MOD}/items/steel_gold_block.json",
                   {"model": {"type": "minecraft:model", "model": f"{MOD}:block/steel_gold_block"}})

        # ---- steel-gold lamp: always lit ----
        write_json(f"assets/{MOD}/blockstates/steel_gold_lamp.json",
                   {"variants": {"": {"model": f"{MOD}:block/steel_gold_lamp"}}})
        write_json(f"assets/{MOD}/models/block/steel_gold_lamp.json",
                   {"parent": "minecraft:block/cube_all",
                    "textures": {"all": f"{MOD}:block/steel_gold_lamp"}})
        write_json(f"assets/{MOD}/models/item/steel_gold_lamp.json",
                   {"parent": f"{MOD}:block/steel_gold_lamp"})
        write_json(f"assets/{MOD}/items/steel_gold_lamp.json",
                   {"model": {"type": "minecraft:model", "model": f"{MOD}:block/steel_gold_lamp"}})

        # ---- anvil: reuse the vanilla anvil models, our textures ----
        anvil_model = json.loads(z.read("assets/minecraft/models/block/anvil.json"))
        anvil_model["textures"] = {"body": f"{MOD}:block/steel_gold_anvil", "top": f"{MOD}:block/steel_gold_anvil_top"}
        write_json(f"assets/{MOD}/models/block/steel_gold_anvil.json", anvil_model)

        anvil_states = json.loads(z.read("assets/minecraft/blockstates/anvil.json"))
        for key, variant in anvil_states["variants"].items():
            variant["model"] = f"{MOD}:block/steel_gold_anvil"
        write_json(f"assets/{MOD}/blockstates/steel_gold_anvil.json", anvil_states)
        # anvil keeps the 3D block model in the inventory (no gold rim, as requested)
        write_json(f"assets/{MOD}/models/item/steel_gold_anvil.json",
                   {"parent": f"{MOD}:block/steel_gold_anvil"})
        write_json(f"assets/{MOD}/items/steel_gold_anvil.json",
                   {"model": {"type": "minecraft:model", "model": f"{MOD}:block/steel_gold_anvil"}})

        # ---- door: clone the copper door blockstate + models ----
        rename = {
            "minecraft:block/copper_door": f"{MOD}:block/steel_gold_door",
            "minecraft:block/copper_door_top": f"{MOD}:block/steel_gold_door_top",
            "minecraft:block/copper_door_bottom": f"{MOD}:block/steel_gold_door_bottom",
            "minecraft:item/copper_door": f"{MOD}:item/steel_gold_door",
        }
        door_states = json.loads(z.read("assets/minecraft/blockstates/copper_door.json"))
        for key, variant in door_states["variants"].items():
            if "model" in variant:
                variant["model"] = variant["model"].replace("minecraft:block/copper_door",
                                                            f"{MOD}:block/steel_gold_door")
        write_json(f"assets/{MOD}/blockstates/steel_gold_door.json", door_states)
        for n in z.namelist():
            if not n.startswith("assets/minecraft/models/block/copper_door"):
                continue
            model = json.loads(z.read(n))
            name = n[len("assets/minecraft/models/block/"):-5].replace("copper_door", "steel_gold_door")
            write_json(f"assets/{MOD}/models/block/{name}.json", rewrite(model, rename))
        write_json(f"assets/{MOD}/models/item/steel_gold_door.json",
                   {"parent": "minecraft:item/generated",
                    "textures": {"layer0": f"{MOD}:item/steel_gold_door"}})
        write_json(f"assets/{MOD}/items/steel_gold_door.json",
                   {"model": {"type": "minecraft:model", "model": f"{MOD}:item/steel_gold_door"}})

        # ---- flint and steel ----
        write_json(f"assets/{MOD}/models/item/steel_gold_flint_and_steel.json",
                   {"parent": "minecraft:item/generated",
                    "textures": {"layer0": f"{MOD}:item/steel_gold_flint_and_steel"}})
        write_json(f"assets/{MOD}/items/steel_gold_flint_and_steel.json",
                   {"model": {"type": "minecraft:model", "model": f"{MOD}:item/steel_gold_flint_and_steel"}})

        # ---- loot tables (copy + rename from vanilla) ----
        for vanilla, ours in (("copper_block", "steel_gold_block"),
                              ("anvil", "steel_gold_anvil"),
                              ("copper_door", "steel_gold_door")):
            n = f"data/minecraft/loot_table/blocks/{vanilla}.json"
            if n not in z.namelist():
                continue
            loot = json.loads(z.read(n))
            text = json.dumps(loot)
            text = text.replace(f"minecraft:{vanilla}", f"{MOD}:{ours}")
            write_json(f"data/{MOD}/loot_table/blocks/{ours}.json", json.loads(text))

        # ---- recipes ----
        write_json(f"data/{MOD}/recipe/steel_gold_block.json", {
            "type": "minecraft:crafting_shaped", "category": "building",
            "key": {"#": f"{MOD}:steel_gold_ingot"},
            "pattern": ["###", "###", "###"],
            "result": {"id": f"{MOD}:steel_gold_block"},
        })
        write_json(f"data/{MOD}/recipe/steel_gold_ingot_from_block.json", {
            "type": "minecraft:crafting_shapeless", "category": "misc",
            "ingredients": [f"{MOD}:steel_gold_block"],
            "result": {"id": f"{MOD}:steel_gold_ingot", "count": 9},
        })
        write_json(f"data/{MOD}/recipe/steel_gold_anvil.json", {
            "type": "minecraft:crafting_shaped", "category": "misc",
            "key": {"A": f"{MOD}:steel_gold_block", "B": f"{MOD}:steel_gold_ingot"},
            "pattern": ["AAA", " B ", "BBB"],
            "result": {"id": f"{MOD}:steel_gold_anvil"},
        })
        write_json(f"data/{MOD}/recipe/steel_gold_door.json", {
            "type": "minecraft:crafting_shaped", "category": "redstone",
            "key": {"#": f"{MOD}:steel_gold_ingot"},
            "pattern": ["##", "##", "##"],
            "result": {"id": f"{MOD}:steel_gold_door", "count": 3},
        })
        write_json(f"data/{MOD}/recipe/steel_gold_lamp.json", {
            "type": "minecraft:crafting_shaped", "category": "building",
            "key": {"B": f"{MOD}:steel_gold_block", "D": f"{MOD}:white_diamond"},
            "pattern": [" B ", "BDB", " B "],
            "result": {"id": f"{MOD}:steel_gold_lamp", "count": 8},
        })
        write_json(f"data/{MOD}/recipe/steel_gold_flint_and_steel.json", {
            "type": "minecraft:crafting_shapeless", "category": "equipment",
            "ingredients": [f"{MOD}:steel_gold_ingot", "minecraft:flint"],
            "result": {"id": f"{MOD}:steel_gold_flint_and_steel"},
        })

        # ---- tags ----
        for tag in ("mineable/pickaxe", "needs_stone_tool"):
            write_tag(f"data/minecraft/tags/block/{tag}.json",
                      [f"{MOD}:steel_gold_block", f"{MOD}:steel_gold_anvil", f"{MOD}:steel_gold_door"])
        write_tag("data/minecraft/tags/block/doors.json", [f"{MOD}:steel_gold_door"])
        write_tag("data/minecraft/tags/item/doors.json", [f"{MOD}:steel_gold_door"])

        # ---- optional: steel-gold stands in for iron ----
        conditions = [{"type": f"{MOD}:config_enabled", "option": "steel_gold_as_iron"}]
        iron_map = {"minecraft:iron_ingot": f"{MOD}:steel_gold_ingot",
                    "minecraft:iron_block": f"{MOD}:steel_gold_block"}
        count = 0
        for n in z.namelist():
            if not n.startswith("data/minecraft/recipe/") or not n.endswith(".json"):
                continue
            rec = json.loads(z.read(n))
            text = json.dumps(rec)
            if not any(k in text for k in iron_map):
                continue
            res = rec.get("result")
            if isinstance(res, dict) and str(res.get("id", "")).startswith(f"{MOD}:"):
                continue
            new = {k: (v if k == "result" else rewrite(v, iron_map)) for k, v in rec.items()}
            if json.dumps(new, sort_keys=True) == json.dumps(rec, sort_keys=True):
                continue
            new["neoforge:conditions"] = conditions
            out = f"iron_sub_{n.rsplit('/', 1)[-1][:-5]}"
            write_json(f"data/{MOD}/recipe/{out}.json", new)
            count += 1
        print("iron substitution recipes:", count)

    # ---- lang ----
    zh = {
        f"block.{MOD}.steel_gold_lamp": "钢金灯",
        f"block.{MOD}.steel_gold_block": "钢金块",
        f"block.{MOD}.steel_gold_anvil": "钢金砧",
        f"block.{MOD}.steel_gold_door": "钢金门",
        f"item.{MOD}.steel_gold_flint_and_steel": "钢金打火石",
        f"container.{MOD}.steel_gold_anvil": "钢金砧",
    }
    en = {
        f"block.{MOD}.steel_gold_lamp": "Steel-Gold Lamp",
        f"block.{MOD}.steel_gold_block": "Block of Steel-Gold",
        f"block.{MOD}.steel_gold_anvil": "Steel-Gold Anvil",
        f"block.{MOD}.steel_gold_door": "Steel-Gold Door",
        f"item.{MOD}.steel_gold_flint_and_steel": "Steel-Gold Flint and Steel",
        f"container.{MOD}.steel_gold_anvil": "Steel-Gold Anvil",
    }
    for lang, table in (("zh_cn", zh), ("en_us", en)):
        path = f"{RES}/assets/{MOD}/lang/{lang}.json"
        data = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
        data.update(table)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")

    print("steel-gold blocks written")


if __name__ == "__main__":
    main()
