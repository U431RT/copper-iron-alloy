"""Generates the 铁铜合金 building block set from the vanilla copper blocks.

No weathering, no waxed variants: every vanilla copper building block is cloned once,
renamed to our namespace, and all of its blockstate / model / item / loot / recipe /
tag references are rewritten. Textures are recoloured with the alloy palette.
"""

import json
import os
import zipfile
from PIL import Image

JAR = r"D:/GAME/MC1.26.2/1.26.2/.minecraft/libraries/net/neoforged/minecraft-client-patched/26.1.2.78/minecraft-client-patched-26.1.2.78.jar"
RES = r"D:/dshworkshop/copper_iron_alloy/src/main/resources"
MOD = "copper_iron_alloy"
TEX_OUT = f"{RES}/assets/{MOD}/textures"

# vanilla id -> our id (also used for name rewriting)
BLOCKS = {
    "copper_block": "iron_copper_alloy_block",
    "cut_copper": "cut_iron_copper_alloy_block",
    "cut_copper_stairs": "cut_iron_copper_alloy_stairs",
    "cut_copper_slab": "cut_iron_copper_alloy_slab",
    "chiseled_copper": "chiseled_iron_copper_alloy_block",
    "copper_grate": "iron_copper_alloy_grate",
    "copper_bars": "iron_copper_alloy_bars",
    "copper_door": "iron_copper_alloy_door",
    "copper_trapdoor": "iron_copper_alloy_trapdoor",
    "copper_bulb": "iron_copper_alloy_bulb",
    "copper_chain": "iron_copper_alloy_chain",
    "lightning_rod": "iron_copper_alloy_lightning_rod",
}

# extra ingredient remapping for recipes
INGREDIENTS = {
    "copper_ingot": "iron_copper_alloy_ingot",
}

# texture renaming: vanilla texture file -> our texture file
TEXTURES = [
    ("block/copper_block", "block/iron_copper_alloy_block"),
    ("block/cut_copper", "block/cut_iron_copper_alloy_block"),
    ("block/chiseled_copper", "block/chiseled_iron_copper_alloy_block"),
    ("block/copper_grate", "block/iron_copper_alloy_grate"),
    ("block/copper_bars", "block/iron_copper_alloy_bars"),
    ("block/copper_door_top", "block/iron_copper_alloy_door_top"),
    ("block/copper_door_bottom", "block/iron_copper_alloy_door_bottom"),
    ("block/copper_trapdoor", "block/iron_copper_alloy_trapdoor"),
    ("block/copper_bulb", "block/iron_copper_alloy_bulb"),
    ("block/copper_bulb_lit", "block/iron_copper_alloy_bulb_lit"),
    ("block/copper_bulb_powered", "block/iron_copper_alloy_bulb_powered"),
    ("block/copper_bulb_lit_powered", "block/iron_copper_alloy_bulb_lit_powered"),
    ("block/copper_chain", "block/iron_copper_alloy_chain"),
    ("block/lightning_rod", "block/iron_copper_alloy_lightning_rod"),
    ("block/lightning_rod_on", "block/iron_copper_alloy_lightning_rod_on"),
    ("item/copper_door", "item/iron_copper_alloy_door"),
    ("item/copper_chain", "item/iron_copper_alloy_chain"),
]


def rename_name(name):
    for old, new in sorted(BLOCKS.items(), key=lambda kv: -len(kv[0])):
        if name == old:
            return new
        if name.startswith(old + "_"):
            return new + name[len(old):]
    for old, new in INGREDIENTS.items():
        if name == old:
            return new
    return name


def rewrite(obj):
    if isinstance(obj, str):
        return rewrite_str(obj)
    if isinstance(obj, list):
        return [rewrite(v) for v in obj]
    if isinstance(obj, dict):
        return {k: rewrite(v) for k, v in obj.items()}
    return obj


def rewrite_str(s):
    if not s.startswith("minecraft:"):
        return s
    rest = s[len("minecraft:"):]
    parts = rest.split("/")
    new = rename_name(parts[-1])
    if new == parts[-1]:
        return s
    parts[-1] = new
    return MOD + ":" + "/".join(parts)


def write_json(rel, obj):
    path = os.path.join(RES, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.write("\n")


# ----------------------------------------------------------------- textures
def recolor_image(img):
    out = img.convert("RGBA").copy()
    px = out.load()
    for y in range(out.size[1]):
        for x in range(out.size[0]):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            lum = 0.299 * r + 0.587 * g + 0.114 * b
            t = max(0.0, min(1.0, lum / 255.0))
            # alloy ramp
            ramp = [(92, 48, 30), (124, 68, 44), (152, 88, 58), (178, 108, 74),
                    (202, 128, 92), (222, 146, 104), (236, 164, 122), (246, 182, 142),
                    (252, 198, 160)]
            pos = (0.05 + 0.78 * t) * (len(ramp) - 1)
            i = int(pos)
            if i >= len(ramp) - 1:
                rgb = ramp[-1]
            else:
                f = pos - i
                rgb = tuple(int(round(ramp[i][k] + (ramp[i + 1][k] - ramp[i][k]) * f)) for k in range(3))
            px[x, y] = (rgb[0], rgb[1], rgb[2], a)
    return out


def gen_textures(z):
    for src, dst in TEXTURES:
        with z.open(f"assets/minecraft/textures/{src}.png") as f:
            img = Image.open(f)
            data = img.convert("RGBA")
        out = recolor_image(data)
        path = f"{TEX_OUT}/{dst}.png"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        out.save(path)
        print("texture", dst)


# ----------------------------------------------------------------- assets/data
def gen_block_assets(z):
    names = z.namelist()
    for vanilla, ours in BLOCKS.items():
        # blockstate
        bs = f"assets/minecraft/blockstates/{vanilla}.json"
        if bs in names:
            write_json(f"assets/{MOD}/blockstates/{ours}.json", rewrite(json.loads(z.read(bs))))
        # block models (all prefixed variants)
        for n in names:
            if not n.startswith(f"assets/minecraft/models/block/{vanilla}"):
                continue
            if not n.endswith(".json"):
                continue
            model = n[len("assets/minecraft/models/block/"):-5]
            new_model = rename_name(model)
            write_json(f"assets/{MOD}/models/block/{new_model}.json", rewrite(json.loads(z.read(n))))
        # item model
        im = f"assets/minecraft/models/item/{vanilla}.json"
        if im in names:
            write_json(f"assets/{MOD}/models/item/{ours}.json", rewrite(json.loads(z.read(im))))
        # item definition
        it = f"assets/minecraft/items/{vanilla}.json"
        if it in names:
            write_json(f"assets/{MOD}/items/{ours}.json", rewrite(json.loads(z.read(it))))
        # loot table
        lt = f"data/minecraft/loot_table/blocks/{vanilla}.json"
        if lt in names:
            write_json(f"data/{MOD}/loot_table/blocks/{ours}.json", rewrite(json.loads(z.read(lt))))
        # recipes producing this block
        for n in names:
            if not n.startswith("data/minecraft/recipe/") or not n.endswith(".json"):
                continue
            rec = json.loads(z.read(n))
            rid = rec.get("result")
            if not isinstance(rid, dict) or "id" not in rid:
                continue
            if rid["id"] != f"minecraft:{vanilla}":
                continue
            new_rec = rewrite(rec)
            out_name = new_rec["result"]["id"].split(":")[1]
            write_json(f"data/{MOD}/recipe/{out_name}.json", new_rec)


def gen_block_tags(z):
    names = [n for n in z.namelist() if n.startswith("data/minecraft/tags/block/") and n.endswith(".json")]
    vanilla_ids = {f"minecraft:{v}" for v in BLOCKS}
    for n in names:
        tag = json.loads(z.read(n))
        values = tag.get("values", [])
        if not any(v in vanilla_ids for v in values):
            continue
        ours = [rewrite_str(v) for v in values if v in vanilla_ids]
        tag_name = n[len("data/minecraft/tags/block/"):]
        write_json(f"data/minecraft/tags/block/{tag_name}", {"values": ours})

    names = [n for n in z.namelist() if n.startswith("data/minecraft/tags/item/") and n.endswith(".json")]
    for n in names:
        tag = json.loads(z.read(n))
        values = tag.get("values", [])
        if not any(v in vanilla_ids for v in values):
            continue
        ours = [rewrite_str(v) for v in values if v in vanilla_ids]
        tag_name = n[len("data/minecraft/tags/item/"):]
        write_json(f"data/minecraft/tags/item/{tag_name}", {"values": ours})


def substitution_recipes(z):
    """Optional ('alloy as copper') variants: vanilla copper results, alloy ingredients."""
    conditions = [{"type": "copper_iron_alloy:config_enabled", "option": "alloy_as_copper"}]
    targets = {f"minecraft:{v}" for v in BLOCKS}
    count = 0

    def sub(obj):
        if isinstance(obj, str):
            if obj.startswith("minecraft:"):
                name = obj[len("minecraft:"):]
                if name in BLOCKS:
                    return f"{MOD}:{BLOCKS[name]}"
                if name == "copper_ingot":
                    return f"{MOD}:iron_copper_alloy_ingot"
            return obj
        if isinstance(obj, list):
            return [sub(v) for v in obj]
        if isinstance(obj, dict):
            return {k: sub(v) for k, v in obj.items()}
        return obj

    for n in z.namelist():
        if not n.startswith("data/minecraft/recipe/") or not n.endswith(".json"):
            continue
        rec = json.loads(z.read(n))
        res = rec.get("result")
        if not isinstance(res, dict) or res.get("id") not in targets:
            continue
        new = {k: (v if k == "result" else sub(v)) for k, v in rec.items()}
        if json.dumps(new, sort_keys=True) == json.dumps(rec, sort_keys=True):
            continue
        new["neoforge:conditions"] = conditions
        write_json(f"data/{MOD}/recipe/sub_{res['id'].split(':')[1]}.json", new)
        count += 1
    print("substitution recipes:", count)


ITEM_BLOCK_MODEL = {
    "iron_copper_alloy_block": "iron_copper_alloy_block",
    "cut_iron_copper_alloy_block": "cut_iron_copper_alloy_block",
    "cut_iron_copper_alloy_stairs": "cut_iron_copper_alloy_stairs",
    "cut_iron_copper_alloy_slab": "cut_iron_copper_alloy_slab",
    "chiseled_iron_copper_alloy_block": "chiseled_iron_copper_alloy_block",
    "iron_copper_alloy_grate": "iron_copper_alloy_grate",
    "iron_copper_alloy_bars": "iron_copper_alloy_bars_post",
    "iron_copper_alloy_trapdoor": "iron_copper_alloy_trapdoor_bottom",
    "iron_copper_alloy_bulb": "iron_copper_alloy_bulb",
    "iron_copper_alloy_chain": "iron_copper_alloy_chain",
    "iron_copper_alloy_lightning_rod": "iron_copper_alloy_lightning_rod",
    # doors keep the flat item texture
}


def gen_block_item_models():
    for item, block_model in ITEM_BLOCK_MODEL.items():
        write_json(f"assets/{MOD}/models/item/{item}.json", {"parent": f"{MOD}:block/{block_model}"})
        write_json(f"assets/{MOD}/items/{item}.json",
                   {"model": {"type": "minecraft:model", "model": f"{MOD}:block/{block_model}"}})


def gen_lang():
    zh = {
        "iron_copper_alloy_block": "铁铜合金块",
        "cut_iron_copper_alloy_block": "切制铁铜合金块",
        "cut_iron_copper_alloy_stairs": "切制铁铜合金楼梯",
        "cut_iron_copper_alloy_slab": "切制铁铜合金台阶",
        "chiseled_iron_copper_alloy_block": "錾制铁铜合金块",
        "iron_copper_alloy_grate": "铁铜合金格栅",
        "iron_copper_alloy_bars": "铁铜合金栏杆",
        "iron_copper_alloy_door": "铁铜合金门",
        "iron_copper_alloy_trapdoor": "铁铜合金活板门",
        "iron_copper_alloy_bulb": "铁铜合金灯",
        "iron_copper_alloy_chain": "铁铜合金链",
        "iron_copper_alloy_lightning_rod": "铁铜合金避雷针",
    }
    en = {
        "iron_copper_alloy_block": "Block of Iron-Copper Alloy",
        "cut_iron_copper_alloy_block": "Cut Iron-Copper Alloy",
        "cut_iron_copper_alloy_stairs": "Cut Iron-Copper Alloy Stairs",
        "cut_iron_copper_alloy_slab": "Cut Iron-Copper Alloy Slab",
        "chiseled_iron_copper_alloy_block": "Chiseled Iron-Copper Alloy",
        "iron_copper_alloy_grate": "Iron-Copper Alloy Grate",
        "iron_copper_alloy_bars": "Iron-Copper Alloy Bars",
        "iron_copper_alloy_door": "Iron-Copper Alloy Door",
        "iron_copper_alloy_trapdoor": "Iron-Copper Alloy Trapdoor",
        "iron_copper_alloy_bulb": "Iron-Copper Alloy Bulb",
        "iron_copper_alloy_chain": "Iron-Copper Alloy Chain",
        "iron_copper_alloy_lightning_rod": "Iron-Copper Alloy Lightning Rod",
    }
    for lang, table in (("zh_cn", zh), ("en_us", en)):
        path = f"{RES}/assets/{MOD}/lang/{lang}.json"
        data = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
        for k, v in table.items():
            data[f"block.{MOD}.{k}"] = v
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")


if __name__ == "__main__":
    with zipfile.ZipFile(JAR) as z:
        gen_textures(z)
        gen_block_assets(z)
        gen_block_tags(z)
        gen_block_item_models()
        substitution_recipes(z)
    gen_lang()
    print("blocks written")
