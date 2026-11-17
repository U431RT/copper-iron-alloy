package com.copperironalloy;

import java.util.Map;

import com.mojang.serialization.MapCodec;

import net.minecraft.core.cauldron.CauldronInteractions;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.tags.BlockTags;
import net.minecraft.tags.TagKey;
import net.minecraft.world.item.AxeItem;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.HoeItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.FlintAndSteelItem;
import net.minecraft.world.item.ShearsItem;
import net.minecraft.world.item.ShovelItem;
import net.minecraft.world.entity.EquipmentSlotGroup;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.item.StandingAndWallBlockItem;
import net.minecraft.world.item.ToolMaterial;
import net.minecraft.world.item.component.Consumables;
import net.minecraft.world.item.equipment.ArmorMaterial;
import net.minecraft.world.item.equipment.ArmorType;
import net.minecraft.world.item.equipment.EquipmentAsset;
import net.minecraft.world.item.equipment.EquipmentAssets;
import net.minecraft.core.Direction;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.ChainBlock;
import net.minecraft.world.level.block.CopperBulbBlock;
import net.minecraft.world.level.block.DoorBlock;
import net.minecraft.world.level.block.IronBarsBlock;
import net.minecraft.world.level.block.LightningRodBlock;
import net.minecraft.world.level.block.SlabBlock;
import net.minecraft.world.level.block.TorchBlock;
import net.minecraft.world.level.block.WallTorchBlock;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.world.level.block.state.properties.NoteBlockInstrument;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.StairBlock;
import net.minecraft.world.level.block.TrapDoorBlock;
import net.minecraft.world.level.block.WaterloggedTransparentBlock;
import net.minecraft.world.inventory.MenuType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.properties.BlockSetType;
import net.minecraft.world.level.material.MapColor;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.event.ItemAttributeModifierEvent;
import net.neoforged.neoforge.event.entity.player.PlayerEvent;
import net.neoforged.neoforge.event.entity.living.LivingDropsEvent;
import net.neoforged.neoforge.event.level.BlockDropsEvent;
import net.neoforged.fml.ModContainer;
import net.neoforged.fml.common.Mod;
import net.neoforged.fml.config.ModConfig;
import net.neoforged.fml.event.lifecycle.FMLCommonSetupEvent;
import net.neoforged.neoforge.common.conditions.ICondition;
import net.neoforged.neoforge.event.BuildCreativeModeTabContentsEvent;
import net.neoforged.neoforge.registries.DeferredBlock;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredItem;
import net.neoforged.neoforge.registries.DeferredRegister;
import net.neoforged.neoforge.common.extensions.IMenuTypeExtension;
import net.neoforged.neoforge.registries.NeoForgeRegistries;

/**
 * 铜铁合金 / Copper-Iron Alloy.
 *
 * <p>Everything the mod adds lives in its own creative tab: materials, tools, armour,
 * the hard coded buckets, the alloy building block family and the milk bucket.</p>
 */
@Mod(CopperIronAlloy.MODID)
public class CopperIronAlloy {
    public static final String MODID = "copper_iron_alloy";

    public static final DeferredRegister.Blocks BLOCKS = DeferredRegister.createBlocks(MODID);
    public static final DeferredRegister.Items ITEMS = DeferredRegister.createItems(MODID);
    public static final DeferredRegister<CreativeModeTab> TABS = DeferredRegister.create(Registries.CREATIVE_MODE_TAB, MODID);
    public static final DeferredRegister<MapCodec<? extends ICondition>> CONDITIONS =
            DeferredRegister.create(NeoForgeRegistries.Keys.CONDITION_CODECS, MODID);
    public static final DeferredRegister<MenuType<?>> MENUS = DeferredRegister.create(Registries.MENU, MODID);

    public static final DeferredHolder<MenuType<?>, MenuType<net.minecraft.world.inventory.AnvilMenu>> STEEL_GOLD_ANVIL_MENU =
            MENUS.register("steel_gold_anvil", () -> IMenuTypeExtension.create(
                    (containerId, inventory, data) -> (net.minecraft.world.inventory.AnvilMenu) new SteelGoldAnvilMenu(
                            containerId, inventory, net.minecraft.world.inventory.ContainerLevelAccess.NULL)));

    public static final DeferredHolder<MapCodec<? extends ICondition>, MapCodec<? extends ICondition>> CONFIG_CONDITION =
            CONDITIONS.register("config_enabled", () -> CopperIronAlloyConfig.ConfigEnabledCondition.CODEC);

    private static TagKey<Item> itemTag(String path) {
        return TagKey.create(Registries.ITEM, Identifier.fromNamespaceAndPath(MODID, path));
    }

    public static final TagKey<Item> ALLOY_TOOL_MATERIALS = itemTag("iron_copper_alloy_tool_materials");
    public static final TagKey<Item> ALLOY_REPAIR_MATERIALS = itemTag("iron_copper_alloy_repair_materials");

    // ------------------------------------------------------------------
    // Materials
    // ------------------------------------------------------------------
    public static final ToolMaterial ALLOY_TOOL = new ToolMaterial(
            BlockTags.INCORRECT_FOR_IRON_TOOL,
            220,
            5.5F,
            1.5F,
            14,
            ALLOY_REPAIR_MATERIALS);

    public static final ResourceKey<EquipmentAsset> ALLOY_EQUIPMENT_ASSET = ResourceKey.create(
            EquipmentAssets.ROOT_ID,
            Identifier.fromNamespaceAndPath(MODID, "iron_copper_alloy"));

    public static final ArmorMaterial ALLOY_ARMOR = new ArmorMaterial(
            13,
            Map.of(
                    ArmorType.HELMET, 2,
                    ArmorType.CHESTPLATE, 5,
                    ArmorType.LEGGINGS, 4,
                    ArmorType.BOOTS, 2,
                    ArmorType.BODY, 5),
            9,
            SoundEvents.ARMOR_EQUIP_COPPER,
            0.0F,
            0.0F,
            ALLOY_REPAIR_MATERIALS,
            ALLOY_EQUIPMENT_ASSET);

    // ------------------------------------------------------------------
    // 钢金 / Steel-Gold
    // ------------------------------------------------------------------
    //   iron    -> durability 250, speed 6.0, +2.0, enchant 14, iron tier
    //   diamond -> durability 1561, speed 8.0, +3.0, enchant 10, diamond tier
    // 900 / 7.0 / 2.5 sit in between; the tier is diamond and the speed already carries
    // the hidden half level of Efficiency (1 + 0.5^2 = 1.25x).
    public static final TagKey<Item> STEEL_GOLD_REPAIR_MATERIALS = itemTag("steel_gold_repair_materials");

    public static final float EFFICIENCY_HALF = 1.25F;

    public static final ToolMaterial STEEL_GOLD_TOOL = new ToolMaterial(
            BlockTags.INCORRECT_FOR_DIAMOND_TOOL,
            900,
            7.0F * EFFICIENCY_HALF,
            2.5F,
            12,
            STEEL_GOLD_REPAIR_MATERIALS);

    public static final ResourceKey<EquipmentAsset> STEEL_GOLD_EQUIPMENT_ASSET = ResourceKey.create(
            EquipmentAssets.ROOT_ID,
            Identifier.fromNamespaceAndPath(MODID, "steel_gold"));

    public static final ArmorMaterial STEEL_GOLD_ARMOR = new ArmorMaterial(
            24,
            Map.of(
                    ArmorType.HELMET, 3,
                    ArmorType.CHESTPLATE, 7,
                    ArmorType.LEGGINGS, 6,
                    ArmorType.BOOTS, 3,
                    ArmorType.BODY, 6),
            10,
            SoundEvents.ARMOR_EQUIP_DIAMOND,
            1.0F,
            0.0F,
            STEEL_GOLD_REPAIR_MATERIALS,
            STEEL_GOLD_EQUIPMENT_ASSET);

    private static BlockBehaviour.Properties gemBlockProps() {
        return BlockBehaviour.Properties.of()
                .mapColor(MapColor.SNOW)
                .strength(5.0F, 6.0F)
                .sound(SoundType.METAL)
                .requiresCorrectToolForDrops();
    }

    private static BlockBehaviour.Properties torchProps() {
        return BlockBehaviour.Properties.of()
                .noCollision()
                .noOcclusion()
                .instabreak()
                .lightLevel(state -> 15)
                .sound(SoundType.WOOD)
                .pushReaction(net.minecraft.world.level.material.PushReaction.DESTROY);
    }

    // ------------------------------------------------------------------
    // 改性白钻 / Modified White Diamond
    // ------------------------------------------------------------------
    //   diamond   -> 1561 / 8.0 / +3.0 / enchant 10 / toughness 2.0 / kb 0
    //   netherite -> 2031 / 9.0 / +4.0 / enchant 15 / toughness 3.0 / kb 0.1
    public static final TagKey<Item> WHITE_DIAMOND_REPAIR_MATERIALS = itemTag("white_diamond_repair_materials");

    public static final ToolMaterial WHITE_DIAMOND_TOOL = new ToolMaterial(
            BlockTags.INCORRECT_FOR_DIAMOND_TOOL,
            1800,
            8.5F,
            3.5F,
            12,
            WHITE_DIAMOND_REPAIR_MATERIALS);

    public static final ResourceKey<EquipmentAsset> WHITE_DIAMOND_EQUIPMENT_ASSET = ResourceKey.create(
            EquipmentAssets.ROOT_ID,
            Identifier.fromNamespaceAndPath(MODID, "white_diamond"));

    /** 宝石很轻：不加击退抗性。 */
    public static final ArmorMaterial WHITE_DIAMOND_ARMOR = new ArmorMaterial(
            35,
            Map.of(
                    ArmorType.HELMET, 3,
                    ArmorType.CHESTPLATE, 8,
                    ArmorType.LEGGINGS, 6,
                    ArmorType.BOOTS, 3,
                    ArmorType.BODY, 8),
            12,
            SoundEvents.ARMOR_EQUIP_DIAMOND,
            2.5F,
            0.0F,
            WHITE_DIAMOND_REPAIR_MATERIALS,
            WHITE_DIAMOND_EQUIPMENT_ASSET);

    // ------------------------------------------------------------------
    // Building blocks (no weathering, no waxed variants)
    // ------------------------------------------------------------------
    private static BlockBehaviour.Properties copperProps() {
        return BlockBehaviour.Properties.of()
                .mapColor(MapColor.COLOR_ORANGE)
                .strength(3.0F, 6.0F)
                .sound(SoundType.COPPER)
                .requiresCorrectToolForDrops();
    }

    public static final DeferredBlock<Block> ALLOY_BLOCK =
            BLOCKS.registerSimpleBlock("iron_copper_alloy_block", CopperIronAlloy::copperProps);
    public static final DeferredBlock<Block> CUT_ALLOY_BLOCK =
            BLOCKS.registerSimpleBlock("cut_iron_copper_alloy_block", CopperIronAlloy::copperProps);
    public static final DeferredBlock<StairBlock> CUT_ALLOY_STAIRS = BLOCKS.registerBlock(
            "cut_iron_copper_alloy_stairs",
            p -> new StairBlock(CUT_ALLOY_BLOCK.get().defaultBlockState(), p),
            CopperIronAlloy::copperProps);
    public static final DeferredBlock<SlabBlock> CUT_ALLOY_SLAB =
            BLOCKS.registerBlock("cut_iron_copper_alloy_slab", SlabBlock::new, CopperIronAlloy::copperProps);
    public static final DeferredBlock<Block> CHISELED_ALLOY_BLOCK =
            BLOCKS.registerSimpleBlock("chiseled_iron_copper_alloy_block", CopperIronAlloy::copperProps);
    public static final DeferredBlock<WaterloggedTransparentBlock> ALLOY_GRATE = BLOCKS.registerBlock(
            "iron_copper_alloy_grate", WaterloggedTransparentBlock::new,
            () -> copperProps().noOcclusion().isViewBlocking((state, level, pos) -> false));
    public static final DeferredBlock<IronBarsBlock> ALLOY_BARS = BLOCKS.registerBlock(
            "iron_copper_alloy_bars", IronBarsBlock::new,
            () -> copperProps().noOcclusion().isViewBlocking((state, level, pos) -> false));
    public static final DeferredBlock<DoorBlock> ALLOY_DOOR = BLOCKS.registerBlock(
            "iron_copper_alloy_door", p -> new DoorBlock(BlockSetType.COPPER, p),
            () -> copperProps().noOcclusion());
    public static final DeferredBlock<TrapDoorBlock> ALLOY_TRAPDOOR = BLOCKS.registerBlock(
            "iron_copper_alloy_trapdoor", p -> new TrapDoorBlock(BlockSetType.COPPER, p),
            () -> copperProps().noOcclusion());
    public static final DeferredBlock<CopperBulbBlock> ALLOY_BULB = BLOCKS.registerBlock(
            "iron_copper_alloy_bulb", CopperBulbBlock::new,
            () -> copperProps().lightLevel(state -> state.getValue(CopperBulbBlock.LIT) ? 15 : 0));
    public static final DeferredBlock<ChainBlock> ALLOY_CHAIN = BLOCKS.registerBlock(
            "iron_copper_alloy_chain", ChainBlock::new,
            () -> copperProps().noOcclusion().isViewBlocking((state, level, pos) -> false));
    public static final DeferredBlock<LightningRodBlock> ALLOY_LIGHTNING_ROD = BLOCKS.registerBlock(
            "iron_copper_alloy_lightning_rod", LightningRodBlock::new,
            () -> copperProps().noOcclusion().isViewBlocking((state, level, pos) -> false));

    public static final DeferredItem<net.minecraft.world.item.BlockItem> ALLOY_BLOCK_ITEM = ITEMS.registerSimpleBlockItem(ALLOY_BLOCK);
    public static final DeferredItem<net.minecraft.world.item.BlockItem> CUT_ALLOY_BLOCK_ITEM = ITEMS.registerSimpleBlockItem(CUT_ALLOY_BLOCK);
    public static final DeferredItem<net.minecraft.world.item.BlockItem> CUT_ALLOY_STAIRS_ITEM = ITEMS.registerSimpleBlockItem(CUT_ALLOY_STAIRS);
    public static final DeferredItem<net.minecraft.world.item.BlockItem> CUT_ALLOY_SLAB_ITEM = ITEMS.registerSimpleBlockItem(CUT_ALLOY_SLAB);
    public static final DeferredItem<net.minecraft.world.item.BlockItem> CHISELED_ALLOY_BLOCK_ITEM = ITEMS.registerSimpleBlockItem(CHISELED_ALLOY_BLOCK);
    public static final DeferredItem<net.minecraft.world.item.BlockItem> ALLOY_GRATE_ITEM = ITEMS.registerSimpleBlockItem(ALLOY_GRATE);
    public static final DeferredItem<net.minecraft.world.item.BlockItem> ALLOY_BARS_ITEM = ITEMS.registerSimpleBlockItem(ALLOY_BARS);
    public static final DeferredItem<net.minecraft.world.item.BlockItem> ALLOY_DOOR_ITEM = ITEMS.registerSimpleBlockItem(ALLOY_DOOR);
    public static final DeferredItem<net.minecraft.world.item.BlockItem> ALLOY_TRAPDOOR_ITEM = ITEMS.registerSimpleBlockItem(ALLOY_TRAPDOOR);
    public static final DeferredItem<net.minecraft.world.item.BlockItem> ALLOY_BULB_ITEM = ITEMS.registerSimpleBlockItem(ALLOY_BULB);
    public static final DeferredItem<net.minecraft.world.item.BlockItem> ALLOY_CHAIN_ITEM = ITEMS.registerSimpleBlockItem(ALLOY_CHAIN);
    public static final DeferredItem<net.minecraft.world.item.BlockItem> ALLOY_LIGHTNING_ROD_ITEM = ITEMS.registerSimpleBlockItem(ALLOY_LIGHTNING_ROD);

    // ------------------------------------------------------------------
    // Items
    // ------------------------------------------------------------------
    public static final DeferredItem<Item> RAW_MIXTURE = ITEMS.registerSimpleItem("raw_iron_copper_mixture");
    public static final DeferredItem<Item> ALLOY_INGOT = ITEMS.registerSimpleItem("iron_copper_alloy_ingot");

    public static final DeferredItem<Item> ALLOY_SWORD = ITEMS.registerSimpleItem("iron_copper_alloy_sword",
            p -> p.sword(ALLOY_TOOL, 3.0F, -2.4F));
    public static final DeferredItem<Item> ALLOY_PICKAXE = ITEMS.registerSimpleItem("iron_copper_alloy_pickaxe",
            p -> p.pickaxe(ALLOY_TOOL, 1.0F, -2.8F));
    public static final DeferredItem<AxeItem> ALLOY_AXE = ITEMS.registerItem("iron_copper_alloy_axe",
            p -> new AxeItem(ALLOY_TOOL, 6.5F, -3.15F, p));
    public static final DeferredItem<ShovelItem> ALLOY_SHOVEL = ITEMS.registerItem("iron_copper_alloy_shovel",
            p -> new ShovelItem(ALLOY_TOOL, 1.5F, -3.0F, p));
    public static final DeferredItem<HoeItem> ALLOY_HOE = ITEMS.registerItem("iron_copper_alloy_hoe",
            p -> new HoeItem(ALLOY_TOOL, -1.5F, -1.5F, p));

    public static final DeferredItem<ShearsItem> ALLOY_SHEARS = ITEMS.registerItem("iron_copper_alloy_shears",
            p -> new ShearsItem(p.durability(220).component(DataComponents.TOOL, ShearsItem.createToolProperties())));

    public static final DeferredItem<AlloyBucketItem> BUCKET = ITEMS.registerItem("iron_copper_alloy_bucket",
            p -> new AlloyBucketItem(AlloyBucketItem.Kind.EMPTY, p.stacksTo(1).durability(AlloyBucketItem.MAX_USES)));
    public static final DeferredItem<AlloyBucketItem> WATER_BUCKET = ITEMS.registerItem("iron_copper_alloy_water_bucket",
            p -> new AlloyBucketItem(AlloyBucketItem.Kind.WATER, p.stacksTo(1).durability(AlloyBucketItem.MAX_USES)));
    public static final DeferredItem<AlloyBucketItem> LAVA_BUCKET = ITEMS.registerItem("iron_copper_alloy_lava_bucket",
            p -> new AlloyBucketItem(AlloyBucketItem.Kind.LAVA, p.stacksTo(1).durability(AlloyBucketItem.MAX_USES)));
    public static final DeferredItem<AlloyBucketItem> POWDER_SNOW_BUCKET = ITEMS.registerItem("iron_copper_alloy_powder_snow_bucket",
            p -> new AlloyBucketItem(AlloyBucketItem.Kind.POWDER_SNOW, p.stacksTo(1).durability(AlloyBucketItem.MAX_USES)));

    /** 铁铜奶桶 - milk any mammal, and usable wherever milk is. */
    public static final DeferredItem<Item> MILK_BUCKET = ITEMS.registerItem("iron_copper_alloy_milk_bucket",
            p -> new Item(p.stacksTo(1)
                    .craftRemainder(BUCKET.get())
                    .component(DataComponents.CONSUMABLE, Consumables.MILK_BUCKET)
                    .usingConvertsTo(BUCKET.get())));

    public static final DeferredItem<Item> ALLOY_HELMET = ITEMS.registerSimpleItem("iron_copper_alloy_helmet",
            p -> p.humanoidArmor(ALLOY_ARMOR, ArmorType.HELMET));
    public static final DeferredItem<Item> ALLOY_CHESTPLATE = ITEMS.registerSimpleItem("iron_copper_alloy_chestplate",
            p -> p.humanoidArmor(ALLOY_ARMOR, ArmorType.CHESTPLATE));
    public static final DeferredItem<Item> ALLOY_LEGGINGS = ITEMS.registerSimpleItem("iron_copper_alloy_leggings",
            p -> p.humanoidArmor(ALLOY_ARMOR, ArmorType.LEGGINGS));
    public static final DeferredItem<Item> ALLOY_BOOTS = ITEMS.registerSimpleItem("iron_copper_alloy_boots",
            p -> p.humanoidArmor(ALLOY_ARMOR, ArmorType.BOOTS));

    // ---- 钢金 ----
    public static final DeferredItem<Item> RAW_STEEL_GOLD = ITEMS.registerSimpleItem("raw_steel_gold_mixture");
    public static final DeferredItem<Item> STEEL_GOLD_INGOT = ITEMS.registerSimpleItem("steel_gold_ingot");

    public static final DeferredItem<Item> STEEL_GOLD_SWORD = ITEMS.registerSimpleItem("steel_gold_sword",
            p -> p.sword(STEEL_GOLD_TOOL, 3.0F, -2.4F));
    public static final DeferredItem<Item> STEEL_GOLD_PICKAXE = ITEMS.registerSimpleItem("steel_gold_pickaxe",
            p -> p.pickaxe(STEEL_GOLD_TOOL, 1.0F, -2.8F));
    public static final DeferredItem<AxeItem> STEEL_GOLD_AXE = ITEMS.registerItem("steel_gold_axe",
            p -> new AxeItem(STEEL_GOLD_TOOL, 6.0F, -3.0F, p));
    public static final DeferredItem<ShovelItem> STEEL_GOLD_SHOVEL = ITEMS.registerItem("steel_gold_shovel",
            p -> new ShovelItem(STEEL_GOLD_TOOL, 1.5F, -3.0F, p));
    public static final DeferredItem<HoeItem> STEEL_GOLD_HOE = ITEMS.registerItem("steel_gold_hoe",
            p -> new HoeItem(STEEL_GOLD_TOOL, -2.5F, -0.5F, p));

    public static final DeferredItem<SteelGoldArmorItem> STEEL_GOLD_HELMET = ITEMS.registerItem("steel_gold_helmet",
            p -> new SteelGoldArmorItem(p.humanoidArmor(STEEL_GOLD_ARMOR, ArmorType.HELMET)));
    public static final DeferredItem<SteelGoldArmorItem> STEEL_GOLD_CHESTPLATE = ITEMS.registerItem("steel_gold_chestplate",
            p -> new SteelGoldArmorItem(p.humanoidArmor(STEEL_GOLD_ARMOR, ArmorType.CHESTPLATE)));
    public static final DeferredItem<SteelGoldArmorItem> STEEL_GOLD_LEGGINGS = ITEMS.registerItem("steel_gold_leggings",
            p -> new SteelGoldArmorItem(p.humanoidArmor(STEEL_GOLD_ARMOR, ArmorType.LEGGINGS)));
    public static final DeferredItem<SteelGoldArmorItem> STEEL_GOLD_BOOTS = ITEMS.registerItem("steel_gold_boots",
            p -> new SteelGoldArmorItem(p.humanoidArmor(STEEL_GOLD_ARMOR, ArmorType.BOOTS)));

    /** 钢金打火石：没有耐久，永远用不坏。 */
    public static final DeferredItem<FlintAndSteelItem> STEEL_GOLD_FLINT_AND_STEEL = ITEMS.registerItem(
            "steel_gold_flint_and_steel", p -> new FlintAndSteelItem(p.stacksTo(1)));

    // ---- 钢金方块 / 砧 / 门 ----
    public static final DeferredBlock<Block> STEEL_GOLD_BLOCK = BLOCKS.registerSimpleBlock(
            "steel_gold_block",
            () -> BlockBehaviour.Properties.of()
                    .mapColor(MapColor.COLOR_BLACK)
                    .strength(5.0F, 1200.0F)
                    .sound(SoundType.METAL)
                    .requiresCorrectToolForDrops());

    public static final DeferredBlock<SteelGoldAnvilBlock> STEEL_GOLD_ANVIL = BLOCKS.registerBlock(
            "steel_gold_anvil", SteelGoldAnvilBlock::new,
            () -> BlockBehaviour.Properties.of()
                    .mapColor(MapColor.COLOR_BLACK)
                    .strength(5.0F, 1200.0F)
                    .sound(SoundType.ANVIL)
                    .requiresCorrectToolForDrops());

    /** 钢金灯：长得像铜灯，但永远是亮的，光 15。 */
    public static final DeferredBlock<Block> STEEL_GOLD_LAMP = BLOCKS.registerSimpleBlock(
            "steel_gold_lamp",
            () -> BlockBehaviour.Properties.of()
                    .mapColor(MapColor.COLOR_BLACK)
                    .strength(3.0F, 6.0F)
                    .sound(SoundType.COPPER)
                    .lightLevel(state -> 15));

    public static final DeferredBlock<SteelGoldDoorBlock> STEEL_GOLD_DOOR = BLOCKS.registerBlock(
            "steel_gold_door", SteelGoldDoorBlock::new,
            () -> BlockBehaviour.Properties.of()
                    .mapColor(MapColor.COLOR_BLACK)
                    .strength(5.0F, 1200.0F)
                    .sound(SoundType.IRON)
                    .noOcclusion());

    public static final DeferredItem<net.minecraft.world.item.BlockItem> STEEL_GOLD_BLOCK_ITEM = ITEMS.registerSimpleBlockItem(STEEL_GOLD_BLOCK);
    public static final DeferredItem<net.minecraft.world.item.BlockItem> STEEL_GOLD_ANVIL_ITEM = ITEMS.registerSimpleBlockItem(STEEL_GOLD_ANVIL);
    public static final DeferredItem<net.minecraft.world.item.BlockItem> STEEL_GOLD_DOOR_ITEM = ITEMS.registerSimpleBlockItem(STEEL_GOLD_DOOR);
    public static final DeferredItem<net.minecraft.world.item.BlockItem> STEEL_GOLD_LAMP_ITEM = ITEMS.registerSimpleBlockItem(STEEL_GOLD_LAMP);

    // ---- 改性白钻 ----
    public static final DeferredItem<Item> DIAMOND_CATALYST = ITEMS.registerSimpleItem("diamond_catalyst");
    public static final DeferredItem<Item> CHARGED_GEM = ITEMS.registerSimpleItem("charged_gem");
    public static final DeferredItem<Item> WHITE_DIAMOND = ITEMS.registerSimpleItem("white_diamond");

    public static final DeferredItem<Item> WHITE_DIAMOND_SWORD = ITEMS.registerSimpleItem("white_diamond_sword",
            p -> p.sword(WHITE_DIAMOND_TOOL, 3.0F, -2.4F));
    public static final DeferredItem<Item> WHITE_DIAMOND_PICKAXE = ITEMS.registerSimpleItem("white_diamond_pickaxe",
            p -> p.pickaxe(WHITE_DIAMOND_TOOL, 1.0F, -2.8F));
    public static final DeferredItem<AxeItem> WHITE_DIAMOND_AXE = ITEMS.registerItem("white_diamond_axe",
            p -> new AxeItem(WHITE_DIAMOND_TOOL, 5.0F, -3.0F, p));
    public static final DeferredItem<ShovelItem> WHITE_DIAMOND_SHOVEL = ITEMS.registerItem("white_diamond_shovel",
            p -> new ShovelItem(WHITE_DIAMOND_TOOL, 1.5F, -3.0F, p));
    public static final DeferredItem<HoeItem> WHITE_DIAMOND_HOE = ITEMS.registerItem("white_diamond_hoe",
            p -> new HoeItem(WHITE_DIAMOND_TOOL, -3.0F, 0.0F, p));

    public static final DeferredItem<Item> WHITE_DIAMOND_HELMET = ITEMS.registerSimpleItem("white_diamond_helmet",
            p -> p.humanoidArmor(WHITE_DIAMOND_ARMOR, ArmorType.HELMET));
    public static final DeferredItem<Item> WHITE_DIAMOND_CHESTPLATE = ITEMS.registerSimpleItem("white_diamond_chestplate",
            p -> p.humanoidArmor(WHITE_DIAMOND_ARMOR, ArmorType.CHESTPLATE));
    public static final DeferredItem<Item> WHITE_DIAMOND_LEGGINGS = ITEMS.registerSimpleItem("white_diamond_leggings",
            p -> p.humanoidArmor(WHITE_DIAMOND_ARMOR, ArmorType.LEGGINGS));
    public static final DeferredItem<Item> WHITE_DIAMOND_BOOTS = ITEMS.registerSimpleItem("white_diamond_boots",
            p -> p.humanoidArmor(WHITE_DIAMOND_ARMOR, ArmorType.BOOTS));

    // ---- 白钻块 / 白火把 ----
    public static final DeferredBlock<Block> WHITE_DIAMOND_BLOCK = BLOCKS.registerSimpleBlock(
            "white_diamond_block", CopperIronAlloy::gemBlockProps);

    public static final DeferredBlock<TorchBlock> WHITE_TORCH = BLOCKS.registerBlock(
            "white_torch", p -> new TorchBlock(ParticleTypes.END_ROD, p), CopperIronAlloy::torchProps);
    public static final DeferredBlock<WallTorchBlock> WHITE_WALL_TORCH = BLOCKS.registerBlock(
            "white_wall_torch", p -> new WallTorchBlock(ParticleTypes.END_ROD, p), CopperIronAlloy::torchProps);

    public static final DeferredItem<net.minecraft.world.item.BlockItem> WHITE_DIAMOND_BLOCK_ITEM =
            ITEMS.registerSimpleBlockItem(WHITE_DIAMOND_BLOCK);
    /** 火把物品要同时认识立式与墙式两种方块，否则插不到墙上。 */
    public static final DeferredItem<StandingAndWallBlockItem> WHITE_TORCH_ITEM = ITEMS.registerItem(
            "white_torch",
            p -> new StandingAndWallBlockItem(WHITE_TORCH.get(), WHITE_WALL_TORCH.get(), Direction.DOWN, p));

    // ------------------------------------------------------------------
    // Creative tab
    // ------------------------------------------------------------------
    public static final DeferredHolder<CreativeModeTab, CreativeModeTab> TAB = TABS.register("copper_iron_alloy",
            () -> CreativeModeTab.builder()
                    .title(Component.translatable("itemGroup." + MODID))
                    .icon(() -> new ItemStack(ALLOY_INGOT.get()))
                    .displayItems((parameters, output) -> {
                        output.accept(RAW_MIXTURE.get());
                        output.accept(ALLOY_INGOT.get());
                        output.accept(ALLOY_SWORD.get());
                        output.accept(ALLOY_PICKAXE.get());
                        output.accept(ALLOY_AXE.get());
                        output.accept(ALLOY_SHOVEL.get());
                        output.accept(ALLOY_HOE.get());
                        output.accept(ALLOY_SHEARS.get());
                        output.accept(ALLOY_HELMET.get());
                        output.accept(ALLOY_CHESTPLATE.get());
                        output.accept(ALLOY_LEGGINGS.get());
                        output.accept(ALLOY_BOOTS.get());
                        output.accept(BUCKET.get());
                        output.accept(WATER_BUCKET.get());
                        output.accept(LAVA_BUCKET.get());
                        output.accept(POWDER_SNOW_BUCKET.get());
                        output.accept(MILK_BUCKET.get());
                        output.accept(ALLOY_BLOCK_ITEM.get());
                        output.accept(CUT_ALLOY_BLOCK_ITEM.get());
                        output.accept(CUT_ALLOY_STAIRS_ITEM.get());
                        output.accept(CUT_ALLOY_SLAB_ITEM.get());
                        output.accept(CHISELED_ALLOY_BLOCK_ITEM.get());
                        output.accept(ALLOY_GRATE_ITEM.get());
                        output.accept(ALLOY_BARS_ITEM.get());
                        output.accept(ALLOY_DOOR_ITEM.get());
                        output.accept(ALLOY_TRAPDOOR_ITEM.get());
                        output.accept(ALLOY_BULB_ITEM.get());
                        output.accept(ALLOY_CHAIN_ITEM.get());
                        output.accept(ALLOY_LIGHTNING_ROD_ITEM.get());
                        output.accept(RAW_STEEL_GOLD.get());
                        output.accept(STEEL_GOLD_INGOT.get());
                        output.accept(STEEL_GOLD_SWORD.get());
                        output.accept(STEEL_GOLD_PICKAXE.get());
                        output.accept(STEEL_GOLD_AXE.get());
                        output.accept(STEEL_GOLD_SHOVEL.get());
                        output.accept(STEEL_GOLD_HOE.get());
                        output.accept(STEEL_GOLD_HELMET.get());
                        output.accept(STEEL_GOLD_CHESTPLATE.get());
                        output.accept(STEEL_GOLD_LEGGINGS.get());
                        output.accept(STEEL_GOLD_BOOTS.get());
                        output.accept(STEEL_GOLD_FLINT_AND_STEEL.get());
                        output.accept(STEEL_GOLD_BLOCK_ITEM.get());
                        output.accept(STEEL_GOLD_ANVIL_ITEM.get());
                        output.accept(STEEL_GOLD_DOOR_ITEM.get());
                        output.accept(STEEL_GOLD_LAMP_ITEM.get());
                        output.accept(DIAMOND_CATALYST.get());
                        output.accept(CHARGED_GEM.get());
                        output.accept(WHITE_DIAMOND.get());
                        output.accept(WHITE_DIAMOND_SWORD.get());
                        output.accept(WHITE_DIAMOND_PICKAXE.get());
                        output.accept(WHITE_DIAMOND_AXE.get());
                        output.accept(WHITE_DIAMOND_SHOVEL.get());
                        output.accept(WHITE_DIAMOND_HOE.get());
                        output.accept(WHITE_DIAMOND_HELMET.get());
                        output.accept(WHITE_DIAMOND_CHESTPLATE.get());
                        output.accept(WHITE_DIAMOND_LEGGINGS.get());
                        output.accept(WHITE_DIAMOND_BOOTS.get());
                        output.accept(WHITE_DIAMOND_BLOCK_ITEM.get());
                        output.accept(WHITE_TORCH_ITEM.get());
                    })
                    .build());

    public CopperIronAlloy(IEventBus modEventBus, ModContainer modContainer) {
        BLOCKS.register(modEventBus);
        ITEMS.register(modEventBus);
        TABS.register(modEventBus);
        CONDITIONS.register(modEventBus);
        MENUS.register(modEventBus);

        modContainer.registerConfig(ModConfig.Type.COMMON, CopperIronAlloyConfig.SPEC);
        modEventBus.addListener(this::commonSetup);

        // hidden half levels of Fortune / Looting
        NeoForge.EVENT_BUS.addListener(this::onBlockDrops);
        NeoForge.EVENT_BUS.addListener(this::onLivingDrops);
        NeoForge.EVENT_BUS.addListener(this::onItemAttributes);
        NeoForge.EVENT_BUS.addListener(this::onItemCrafted);
    }

    /**
     * 改性白钻盔甲的额外属性：
     *   头盔 +0.5 方块交互距离 / +0.5 实体交互距离
     *   胸甲 +10 最大生命
     *   护腿 +10% 潜行速度
     *   靴子 +10% 移动速度
     */
    private void onItemAttributes(ItemAttributeModifierEvent event) {
        ItemStack stack = event.getItemStack();
        if (stack.is(WHITE_DIAMOND_HELMET.get())) {
            event.addModifier(Attributes.BLOCK_INTERACTION_RANGE, modifier("white_diamond_helmet_reach", 0.5),
                    EquipmentSlotGroup.HEAD);
            event.addModifier(Attributes.ENTITY_INTERACTION_RANGE, modifier("white_diamond_helmet_reach_entity", 0.5),
                    EquipmentSlotGroup.HEAD);
        } else if (stack.is(WHITE_DIAMOND_CHESTPLATE.get())) {
            event.addModifier(Attributes.MAX_HEALTH, modifier("white_diamond_chestplate_health", 10.0),
                    EquipmentSlotGroup.CHEST);
        } else if (stack.is(WHITE_DIAMOND_LEGGINGS.get())) {
            event.addModifier(Attributes.SNEAKING_SPEED,
                    new AttributeModifier(Identifier.fromNamespaceAndPath(MODID, "white_diamond_leggings_sneak"),
                            0.10, AttributeModifier.Operation.ADD_MULTIPLIED_TOTAL),
                    EquipmentSlotGroup.LEGS);
        } else if (stack.is(WHITE_DIAMOND_BOOTS.get())) {
            event.addModifier(Attributes.MOVEMENT_SPEED,
                    new AttributeModifier(Identifier.fromNamespaceAndPath(MODID, "white_diamond_boots_speed"),
                            0.10, AttributeModifier.Operation.ADD_MULTIPLIED_TOTAL),
                    EquipmentSlotGroup.FEET);
        }
    }

    /**
     * 白钻工具一出炉就带附魔（直接写在成品上）：
     *   镐 时运 I / 斧 锋利 I / 剑 抢夺 I / 锹 精准采集 I / 锄 耐久 I
     */
    private void onItemCrafted(PlayerEvent.ItemCraftedEvent event) {
        if (!(event.getEntity() instanceof net.minecraft.world.entity.player.Player player) || player.level().isClientSide()) {
            return;
        }
        ItemStack stack = event.getCrafting();
        net.minecraft.core.HolderLookup.RegistryLookup<net.minecraft.world.item.enchantment.Enchantment> enchantments =
                player.level().registryAccess().lookupOrThrow(Registries.ENCHANTMENT);

        if (stack.is(WHITE_DIAMOND_PICKAXE.get())) {
            stack.enchant(enchantments.getOrThrow(net.minecraft.world.item.enchantment.Enchantments.FORTUNE), 1);
        } else if (stack.is(WHITE_DIAMOND_AXE.get())) {
            stack.enchant(enchantments.getOrThrow(net.minecraft.world.item.enchantment.Enchantments.SHARPNESS), 1);
        } else if (stack.is(WHITE_DIAMOND_SWORD.get())) {
            stack.enchant(enchantments.getOrThrow(net.minecraft.world.item.enchantment.Enchantments.LOOTING), 1);
        } else if (stack.is(WHITE_DIAMOND_SHOVEL.get())) {
            stack.enchant(enchantments.getOrThrow(net.minecraft.world.item.enchantment.Enchantments.SILK_TOUCH), 1);
        } else if (stack.is(WHITE_DIAMOND_HOE.get())) {
            stack.enchant(enchantments.getOrThrow(net.minecraft.world.item.enchantment.Enchantments.UNBREAKING), 1);
        }
    }

    private static AttributeModifier modifier(String id, double amount) {
        return new AttributeModifier(Identifier.fromNamespaceAndPath(MODID, id), amount,
                AttributeModifier.Operation.ADD_VALUE);
    }

    /**
     * Hidden half level of Fortune: half the time, one extra item drops.
     * Nothing is shown on the tooltip.
     */
    private void onBlockDrops(BlockDropsEvent event) {
        if (!event.getTool().is(STEEL_GOLD_PICKAXE.get()) || event.getDrops().isEmpty()) {
            return;
        }
        if (event.getLevel().getRandom().nextFloat() >= 0.5F) {
            return;
        }
        net.minecraft.world.entity.item.ItemEntity pick = event.getDrops()
                .get(event.getLevel().getRandom().nextInt(event.getDrops().size()));
        pick.getItem().grow(1);
    }

    /** Hidden half level of Looting, same idea. */
    private void onLivingDrops(LivingDropsEvent event) {
        net.minecraft.world.entity.Entity attacker = event.getSource().getEntity();
        if (!(attacker instanceof net.minecraft.world.entity.player.Player player)) {
            return;
        }
        if (!player.getMainHandItem().is(STEEL_GOLD_SWORD.get()) || event.getDrops().isEmpty()) {
            return;
        }
        if (player.getRandom().nextFloat() >= 0.5F) {
            return;
        }
        java.util.List<net.minecraft.world.entity.item.ItemEntity> drops = new java.util.ArrayList<>(event.getDrops());
        drops.get(player.getRandom().nextInt(drops.size())).getItem().grow(1);
    }

    private void commonSetup(FMLCommonSetupEvent event) {
        event.enqueueWork(() -> {
            CauldronInteractions.EMPTY.put(WATER_BUCKET.get(),
                    AlloyBucketItem.fillCauldron(AlloyBucketItem.fullWaterCauldron(), SoundEvents.BUCKET_EMPTY));
            CauldronInteractions.EMPTY.put(LAVA_BUCKET.get(),
                    AlloyBucketItem.fillCauldron(net.minecraft.world.level.block.Blocks.LAVA_CAULDRON.defaultBlockState(), SoundEvents.BUCKET_EMPTY_LAVA));
            CauldronInteractions.EMPTY.put(POWDER_SNOW_BUCKET.get(),
                    AlloyBucketItem.fillCauldron(AlloyBucketItem.fullPowderSnowCauldron(), SoundEvents.BUCKET_EMPTY_POWDER_SNOW));

            CauldronInteractions.WATER.put(BUCKET.get(),
                    AlloyBucketItem.scoopFromCauldron(WATER_BUCKET::get, SoundEvents.BUCKET_FILL, true));
            CauldronInteractions.LAVA.put(BUCKET.get(),
                    AlloyBucketItem.scoopFromCauldron(LAVA_BUCKET::get, SoundEvents.BUCKET_FILL_LAVA, false));
            CauldronInteractions.POWDER_SNOW.put(BUCKET.get(),
                    AlloyBucketItem.scoopFromCauldron(POWDER_SNOW_BUCKET::get, SoundEvents.BUCKET_FILL_POWDER_SNOW, false));
        });
    }
}
