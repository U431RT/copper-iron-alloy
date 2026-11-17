"""Contact sheet: vanilla source on the left, generated texture on the right."""

import os

from PIL import Image, ImageDraw

VAN = "D:/dshworkshop/_cia/tex/assets/minecraft/textures/item"
GEN = "D:/dshworkshop/copper_iron_alloy/src/main/resources/assets/copper_iron_alloy/textures/item"

PAIRS = [
    ("copper_ingot", "iron_copper_alloy_ingot"),
    ("copper_ingot", "copper_clad_iron_ingot"),
    ("raw_copper", "raw_iron_copper_mixture"),
    ("copper_sword", "iron_copper_alloy_sword"),
    ("copper_sword", "copper_clad_iron_sword"),
    ("copper_pickaxe", "iron_copper_alloy_pickaxe"),
    ("copper_pickaxe", "copper_clad_iron_pickaxe"),
    ("copper_axe", "iron_copper_alloy_axe"),
    ("copper_axe", "copper_clad_iron_axe"),
    ("copper_shovel", "iron_copper_alloy_shovel"),
    ("copper_shovel", "copper_clad_iron_shovel"),
    ("copper_hoe", "iron_copper_alloy_hoe"),
    ("copper_hoe", "copper_clad_iron_hoe"),
    ("copper_helmet", "iron_copper_alloy_helmet"),
    ("copper_chestplate", "iron_copper_alloy_chestplate"),
    ("copper_leggings", "iron_copper_alloy_leggings"),
    ("copper_boots", "iron_copper_alloy_boots"),
]

S = 5
CELL = 16 * S
PAIR_W = CELL * 2 + 8
COLS = 4
ROWS = (len(PAIRS) + COLS - 1) // COLS

sheet = Image.new("RGBA", (COLS * (PAIR_W + 12), ROWS * (CELL + 20)), (46, 46, 56, 255))
d = ImageDraw.Draw(sheet)

for i, (src_name, gen_name) in enumerate(PAIRS):
    x0 = (i % COLS) * (PAIR_W + 12)
    y0 = (i // COLS) * (CELL + 20)
    for j, path in enumerate(
        (os.path.join(VAN, src_name + ".png"), os.path.join(GEN, gen_name + ".png"))
    ):
        im = Image.open(path).convert("RGBA")
        bg = Image.new("RGBA", im.size, (120, 120, 132, 255))
        bg.alpha_composite(im)
        sheet.paste(bg.resize((CELL, CELL), Image.NEAREST), (x0 + j * (CELL + 8), y0))
    d.text((x0 + 2, y0 + CELL + 3), gen_name, fill=(255, 255, 255, 255))

sheet.save("D:/dshworkshop/copper_iron_alloy/tools/preview.png")
print("ok", sheet.size)
