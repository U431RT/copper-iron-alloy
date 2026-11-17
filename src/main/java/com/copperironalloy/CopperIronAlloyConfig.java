package com.copperironalloy;

import com.mojang.serialization.Codec;
import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;

import net.neoforged.neoforge.common.ModConfigSpec;
import net.neoforged.neoforge.common.conditions.ICondition;

/**
 * Config plus the matching data-pack condition, so that recipe files can be shipped and
 * only load when the player turns the option on.
 */
public final class CopperIronAlloyConfig {
    public static final ModConfigSpec SPEC;
    public static final ModConfigSpec.BooleanValue ALLOY_AS_COPPER;
    public static final ModConfigSpec.BooleanValue STEEL_GOLD_AS_IRON;
    public static final ModConfigSpec.BooleanValue WHITE_DIAMOND_AS_DIAMOND;

    static {
        ModConfigSpec.Builder builder = new ModConfigSpec.Builder();
        builder.comment("Recipe behaviour").push("recipes");
        ALLOY_AS_COPPER = builder
                .comment("Let 铁铜合金 stand in for copper in copper recipes.",
                        "Off by default: the alloy only crafts its own blocks and items.")
                .define("alloy_as_copper", false);
        STEEL_GOLD_AS_IRON = builder
                .comment("Let 钢金 stand in for iron in iron recipes.",
                        "Off by default.")
                .define("steel_gold_as_iron", false);
        WHITE_DIAMOND_AS_DIAMOND = builder
                .comment("Let 改性白钻 stand in for diamond in diamond recipes.",
                        "Off by default.")
                .define("white_diamond_as_diamond", false);
        builder.pop();
        SPEC = builder.build();
    }

    private CopperIronAlloyConfig() {
    }

    /** {@code {"type": "copper_iron_alloy:config_enabled", "option": "alloy_as_copper"}} */
    public record ConfigEnabledCondition(String option) implements ICondition {
        public static final MapCodec<ConfigEnabledCondition> CODEC = RecordCodecBuilder.mapCodec(instance -> instance.group(
                Codec.STRING.fieldOf("option").forGetter(ConfigEnabledCondition::option)
        ).apply(instance, ConfigEnabledCondition::new));

        @Override
        public boolean test(ICondition.IContext context) {
            return switch (this.option) {
                case "alloy_as_copper" -> ALLOY_AS_COPPER.get();
                case "steel_gold_as_iron" -> STEEL_GOLD_AS_IRON.get();
                case "white_diamond_as_diamond" -> WHITE_DIAMOND_AS_DIAMOND.get();
                default -> false;
            };
        }

        @Override
        public MapCodec<? extends ICondition> codec() {
            return CODEC;
        }
    }
}
