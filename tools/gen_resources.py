"""Emits every JSON resource for 铜铁合金 / Copper-Iron Alloy (Minecraft 26.1.2)."""

import json
import os

MOD = "copper_iron_alloy"
RES = "D:/dshworkshop/copper_iron_alloy/src/main/resources"

TOOLS = ["sword", "pickaxe", "axe", "shovel", "hoe"]
ARMOR = ["helmet", "chestplate", "leggings", "boots"]

ZH = {
    "raw_iron_copper_mixture": "粗铁铜混合物",
    "iron_copper_alloy_ingot": "铁铜合金",
    "iron_copper_alloy_sword": "铁铜合金剑",
    "iron_copper_alloy_pickaxe": "铁铜合金镐",
    "iron_copper_alloy_axe": "铁铜合金斧",
    "iron_copper_alloy_shovel": "铁铜合金锹",
    "iron_copper_alloy_hoe": "铁铜合金锄",
    "iron_copper_alloy_shears": "铁铜合金剪刀",
    "iron_copper_alloy_bucket": "铁铜合金桶",
    "iron_copper_alloy_water_bucket": "铁铜合金水桶",
    "iron_copper_alloy_lava_bucket": "铁铜合金岩浆桶",
    "iron_copper_alloy_powder_snow_bucket": "铁铜合金细雪桶",
    "iron_copper_alloy_milk_bucket": "铁铜奶桶",
    "iron_copper_alloy_helmet": "铁铜合金头盔",
    "iron_copper_alloy_chestplate": "铁铜合金胸甲",
    "iron_copper_alloy_leggings": "铁铜合金护腿",
    "iron_copper_alloy_boots": "铁铜合金靴子",
}
EN = {
    "raw_iron_copper_mixture": "Raw Iron-Copper Mixture",
    "iron_copper_alloy_ingot": "Iron-Copper Alloy Ingot",
    "iron_copper_alloy_sword": "Iron-Copper Alloy Sword",
    "iron_copper_alloy_pickaxe": "Iron-Copper Alloy Pickaxe",
    "iron_copper_alloy_axe": "Iron-Copper Alloy Axe",
    "iron_copper_alloy_shovel": "Iron-Copper Alloy Shovel",
    "iron_copper_alloy_hoe": "Iron-Copper Alloy Hoe",
    "iron_copper_alloy_shears": "Iron-Copper Alloy Shears",
    "iron_copper_alloy_bucket": "Iron-Copper Alloy Bucket",
    "iron_copper_alloy_water_bucket": "Iron-Copper Alloy Water Bucket",
    "iron_copper_alloy_lava_bucket": "Iron-Copper Alloy Lava Bucket",
    "iron_copper_alloy_powder_snow_bucket": "Iron-Copper Alloy Powder Snow Bucket",
    "iron_copper_alloy_milk_bucket": "Iron-Copper Milk Bucket",
    "iron_copper_alloy_helmet": "Iron-Copper Alloy Helmet",
    "iron_copper_alloy_chestplate": "Iron-Copper Alloy Chestplate",
    "iron_copper_alloy_leggings": "Iron-Copper Alloy Leggings",
    "iron_copper_alloy_boots": "Iron-Copper Alloy Boots",
}

ADV_ZH = {
    "no_such_alloy": ("根本没有这种合金！", "三份粗铜掺一份粗铁，磨碎了混在一起。根本没有这种合金！"),
    "youre_just_scared": ("你只是怕了", "把它丢进炉子里烧成锭，假装它真的是一种合金。你只是怕了。"),
    "who_isnt_scared": ("这谁不怕！", "真的拿这种东西去打了一把工具、搓了一套盔甲——这谁不怕！"),
}
ADV_EN = {
    "no_such_alloy": ("There Is No Such Alloy!", "Ground three raw copper together with one raw iron. There is no such alloy at all!"),
    "youre_just_scared": ("You're Just Scared", "Smelt the mixture into an ingot and pretend it is a real alloy. You're just scared."),
    "who_isnt_scared": ("Who Wouldn't Be Scared!", "Actually forged a tool or a piece of armour out of it. Who wouldn't be scared!"),
}

# every gear item that should pop the third advancement
GEAR = [
    "iron_copper_alloy_sword", "iron_copper_alloy_pickaxe", "iron_copper_alloy_axe",
    "iron_copper_alloy_shovel", "iron_copper_alloy_hoe",
    "iron_copper_alloy_helmet", "iron_copper_alloy_chestplate",
    "iron_copper_alloy_leggings", "iron_copper_alloy_boots",
]

# items whose model switches on damage (anvil style cracking)
CRACKED = {
    "iron_copper_alloy_bucket": [1, 2],
    "iron_copper_alloy_lava_bucket": [1, 2],
}


def write_tag(rel, values):
    """merge with an existing tag file so generators can each add their own entries"""
    path = os.path.join(RES, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    existing = []
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            existing = json.load(f).get("values", [])
    merged = list(dict.fromkeys(existing + values))
    write(rel, {"values": merged})


def write(rel, obj):
    path = os.path.join(RES, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.write("\n")


def model_ref(name):
    return {"type": "minecraft:model", "model": f"{MOD}:item/{name}"}


def gen_assets():
    handheld = {f"iron_copper_alloy_{t}" for t in TOOLS}

    for item in ZH:
        parent = "minecraft:item/handheld" if item in handheld else "minecraft:item/generated"

        # plain model file (also used as the "undamaged" variant)
        write(f"assets/{MOD}/models/item/{item}.json",
              {"parent": parent, "textures": {"layer0": f"{MOD}:item/{item}"}})

        if item in CRACKED:
            for stage in CRACKED[item]:
                write(f"assets/{MOD}/models/item/{item}_{stage}.json",
                      {"parent": parent, "textures": {"layer0": f"{MOD}:item/{item}_{stage}"}})
            entries = [{"threshold": stage, "model": model_ref(f"{item}_{stage}")} for stage in CRACKED[item]]
            write(f"assets/{MOD}/items/{item}.json", {
                "model": {
                    "type": "minecraft:range_dispatch",
                    "property": "minecraft:damage",
                    "normalize": False,
                    "entries": entries,
                    "fallback": model_ref(item),
                }
            })
        else:
            write(f"assets/{MOD}/items/{item}.json",
                  {"model": {"type": "minecraft:model", "model": f"{MOD}:item/{item}"}})

    # worn armour layers
    write(f"assets/{MOD}/equipment/iron_copper_alloy.json", {
        "layers": {
            "humanoid": [{"texture": f"{MOD}:iron_copper_alloy"}],
            "humanoid_baby": [{"texture": f"{MOD}:iron_copper_alloy"}],
            "humanoid_leggings": [{"texture": f"{MOD}:iron_copper_alloy"}],
        }
    })

    for lang, table, adv in (("zh_cn", ZH, ADV_ZH), ("en_us", EN, ADV_EN)):
        lang_path = os.path.join(RES, f"assets/{MOD}/lang/{lang}.json")
        data = {}
        if os.path.exists(lang_path):
            with open(lang_path, encoding="utf-8") as f:
                data = json.load(f)
        data.update({f"item.{MOD}.{k}": v for k, v in table.items()})
        for key, (title, desc) in adv.items():
            data[f"advancements.{MOD}.{key}.title"] = title
            data[f"advancements.{MOD}.{key}.description"] = desc
        data[f"itemGroup.{MOD}"] = "铜铁合金" if lang == "zh_cn" else "Copper-Iron Alloy"
        write(f"assets/{MOD}/lang/{lang}.json", data)


def gen_recipes():
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

    # 3 raw copper + 1 raw iron -> 4 raw mixture
    write(f"data/{MOD}/recipe/raw_iron_copper_mixture.json", {
        "type": "minecraft:crafting_shapeless",
        "category": "misc",
        "ingredients": ["minecraft:raw_copper", "minecraft:raw_copper", "minecraft:raw_copper", "minecraft:raw_iron"],
        "result": {"id": f"{MOD}:raw_iron_copper_mixture", "count": 4},
    })

    # smelt / blast the mixture
    for kind, time in (("smelting", 200), ("blasting", 100)):
        write(f"data/{MOD}/recipe/iron_copper_alloy_ingot_from_{kind}.json", {
            "type": f"minecraft:{kind}",
            "category": "misc",
            "cookingtime": time,
            "experience": 0.7,
            "group": "iron_copper_alloy_ingot",
            "ingredient": f"{MOD}:raw_iron_copper_mixture",
            "result": {"id": f"{MOD}:iron_copper_alloy_ingot"},
        })

    # 1 copper ingot + 1 iron ingot -> 1 alloy ingot
    write(f"data/{MOD}/recipe/iron_copper_alloy_ingot.json", {
        "type": "minecraft:crafting_shapeless",
        "category": "misc",
        "ingredients": ["minecraft:copper_ingot", "minecraft:iron_ingot"],
        "result": {"id": f"{MOD}:iron_copper_alloy_ingot"},
    })

    # tools
    for tool, pattern in patterns.items():
        write(f"data/{MOD}/recipe/iron_copper_alloy_{tool}.json", {
            "type": "minecraft:crafting_shaped",
            "category": "equipment",
            "key": {"#": "minecraft:stick", "X": f"#{MOD}:iron_copper_alloy_tool_materials"},
            "pattern": pattern,
            "result": {"id": f"{MOD}:iron_copper_alloy_{tool}"},
        })

    # shears + bucket
    write(f"data/{MOD}/recipe/iron_copper_alloy_shears.json", {
        "type": "minecraft:crafting_shaped",
        "category": "equipment",
        "key": {"#": f"{MOD}:iron_copper_alloy_ingot"},
        "pattern": [" #", "# "],
        "result": {"id": f"{MOD}:iron_copper_alloy_shears"},
    })
    write(f"data/{MOD}/recipe/iron_copper_alloy_bucket.json", {
        "type": "minecraft:crafting_shaped",
        "category": "misc",
        "key": {"#": f"{MOD}:iron_copper_alloy_ingot"},
        "pattern": ["# #", " # "],
        "result": {"id": f"{MOD}:iron_copper_alloy_bucket"},
    })

    # armour
    for piece, pattern in armor_patterns.items():
        write(f"data/{MOD}/recipe/iron_copper_alloy_{piece}.json", {
            "type": "minecraft:crafting_shaped",
            "category": "equipment",
            "key": {"X": f"{MOD}:iron_copper_alloy_ingot"},
            "pattern": pattern,
            "result": {"id": f"{MOD}:iron_copper_alloy_{piece}"},
        })


def gen_tags():
    write(f"data/{MOD}/tags/item/iron_copper_alloy_tool_materials.json",
          {"values": [f"{MOD}:iron_copper_alloy_ingot"]})
    write(f"data/{MOD}/tags/item/iron_copper_alloy_repair_materials.json",
          {"values": [f"{MOD}:iron_copper_alloy_ingot", "minecraft:copper_ingot", "minecraft:iron_ingot"]})

    vanilla = {
        "swords": [f"{MOD}:iron_copper_alloy_sword"],
        "pickaxes": [f"{MOD}:iron_copper_alloy_pickaxe"],
        "axes": [f"{MOD}:iron_copper_alloy_axe"],
        "shovels": [f"{MOD}:iron_copper_alloy_shovel"],
        "hoes": [f"{MOD}:iron_copper_alloy_hoe"],
        "head_armor": [f"{MOD}:iron_copper_alloy_helmet"],
        "chest_armor": [f"{MOD}:iron_copper_alloy_chestplate"],
        "leg_armor": [f"{MOD}:iron_copper_alloy_leggings"],
        "foot_armor": [f"{MOD}:iron_copper_alloy_boots"],
        "enchantable/mining": [f"{MOD}:iron_copper_alloy_shears"],
        "enchantable/durability": [f"{MOD}:iron_copper_alloy_shears"],
    }
    for tag, values in vanilla.items():
        write_tag(f"data/minecraft/tags/item/{tag}.json", values)


def gen_advancements():
    def crit(item):
        return {"conditions": {"items": [{"items": f"{MOD}:{item}"}]}, "trigger": "minecraft:inventory_changed"}

    write(f"data/{MOD}/advancement/no_such_alloy.json", {
        "display": {
            "icon": {"id": f"{MOD}:raw_iron_copper_mixture"},
            "title": {"translate": f"advancements.{MOD}.no_such_alloy.title"},
            "description": {"translate": f"advancements.{MOD}.no_such_alloy.description"},
            "background": "minecraft:textures/block/copper_block.png",
            "frame": "task",
            "show_toast": True,
            "announce_to_chat": True,
        },
        "criteria": {"mixture": crit("raw_iron_copper_mixture")},
        "requirements": [["mixture"]],
        "sends_telemetry_event": False,
    })

    write(f"data/{MOD}/advancement/youre_just_scared.json", {
        "parent": f"{MOD}:no_such_alloy",
        "display": {
            "icon": {"id": f"{MOD}:iron_copper_alloy_ingot"},
            "title": {"translate": f"advancements.{MOD}.youre_just_scared.title"},
            "description": {"translate": f"advancements.{MOD}.youre_just_scared.description"},
            "frame": "task",
            "show_toast": True,
            "announce_to_chat": True,
        },
        "criteria": {"got": crit("iron_copper_alloy_ingot")},
        "requirements": [["got"]],
        "sends_telemetry_event": False,
    })

    # third advancement: pop it when a tool or armour piece is actually made
    write(f"data/{MOD}/advancement/who_isnt_scared.json", {
        "parent": f"{MOD}:no_such_alloy",
        "display": {
            "icon": {"id": f"{MOD}:iron_copper_alloy_sword"},
            "title": {"translate": f"advancements.{MOD}.who_isnt_scared.title"},
            "description": {"translate": f"advancements.{MOD}.who_isnt_scared.description"},
            "frame": "goal",
            "show_toast": True,
            "announce_to_chat": True,
        },
        "criteria": {"gear": {
            "trigger": "minecraft:inventory_changed",
            "conditions": {"items": [{"items": f"{MOD}:{item}"} for item in GEAR]},
        }},
        "requirements": [["gear"]],
        "sends_telemetry_event": False,
    })


def gen_dairy_compat():
    """Make the milk bucket usable anywhere milk is: conventional tags + a cake variant."""
    milk = f"{MOD}:iron_copper_alloy_milk_bucket"
    write("data/c/tags/item/buckets/milk.json", {"values": [milk]})
    write("data/c/tags/item/drink_containing/bucket.json", {"values": [milk]})
    write("data/c/tags/item/drinks/milk.json", {"values": [milk]})
    write(f"data/{MOD}/recipe/cake_from_alloy_milk.json", {
        "type": "minecraft:crafting_shaped",
        "category": "misc",
        "key": {
            "A": milk,
            "B": "minecraft:sugar",
            "C": "minecraft:wheat",
            "E": "#minecraft:eggs",
        },
        "pattern": ["AAA", "BEB", "CCC"],
        "result": {"id": "minecraft:cake"},
    })


if __name__ == "__main__":
    gen_assets()
    gen_recipes()
    gen_tags()
    gen_advancements()
    gen_dairy_compat()
    print("resources written")
