package com.copperironalloy;

import java.util.function.Supplier;

import net.minecraft.core.BlockPos;
import net.minecraft.core.cauldron.CauldronInteraction;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.context.UseOnContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.AbstractCauldronBlock;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.BucketPickup;
import net.minecraft.world.level.block.LayeredCauldronBlock;
import net.minecraft.world.level.block.LiquidBlockContainer;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.gameevent.GameEvent;
import net.minecraft.world.level.material.Fluid;
import net.minecraft.world.level.material.FluidState;
import net.minecraft.world.level.material.Fluids;

/**
 * A deliberately dumb bucket: no fluid registry lookups and no BucketLib, just the
 * handful of vanilla behaviours written out by hand.
 *
 * <p>It scoops from water / lava / powder snow blocks (including waterlogged blocks, via
 * the vanilla {@link BucketPickup} interface), pours back into the world, waterlogs
 * blocks that accept water, and takes part in all four cauldron interaction tables.
 * Filling a bucket with lava chips it, and the third pour shatters it, anvil style.</p>
 */
public class AlloyBucketItem extends Item {
    public static final int MAX_USES = 3;

    public enum Kind {
        EMPTY,
        WATER,
        LAVA,
        POWDER_SNOW
    }

    private final Kind kind;

    public AlloyBucketItem(Kind kind, Item.Properties properties) {
        super(properties);
        this.kind = kind;
    }

    public Kind kind() {
        return this.kind;
    }

    // ------------------------------------------------------------------
    // milking: any mammal, not just cows
    // ------------------------------------------------------------------
    private static final java.util.Set<String> NON_MILKERS = java.util.Set.of(
            "Chicken", "Parrot", "Frog", "Turtle", "Axolotl", "Bee", "Sniffer", "Bat",
            "Squid", "GlowSquid", "Cod", "Salmon", "TropicalFish", "Pufferfish", "Allay");

    @Override
    public InteractionResult interactLivingEntity(ItemStack stack, Player player, net.minecraft.world.entity.LivingEntity entity,
            InteractionHand hand) {
        if (this.kind != Kind.EMPTY || !(entity instanceof net.minecraft.world.entity.animal.Animal)) {
            return InteractionResult.PASS;
        }
        if (NON_MILKERS.contains(entity.getClass().getSimpleName())) {
            return InteractionResult.PASS;
        }
        if (!player.level().isClientSide()) {
            player.setItemInHand(hand, new ItemStack(CopperIronAlloy.MILK_BUCKET.get()));
            player.playSound(SoundEvents.COW_MILK, 1.0F, 1.0F);
        }
        return InteractionResult.SUCCESS;
    }

    // ------------------------------------------------------------------
    // block interaction
    // ------------------------------------------------------------------
    @Override
    public InteractionResult useOn(UseOnContext context) {
        Player player = context.getPlayer();
        if (player == null) {
            return InteractionResult.PASS;
        }
        Level level = context.getLevel();
        BlockPos pos = context.getClickedPos();
        BlockState state = level.getBlockState(pos);

        // cauldrons are handled by the cauldron interaction tables
        if (state.getBlock() instanceof AbstractCauldronBlock) {
            return InteractionResult.PASS;
        }

        return this.kind == Kind.EMPTY
                ? this.scoop(context, level, player, pos, state)
                : this.pour(context, level, player, pos, state);
    }

    private static Kind kindOf(BlockState state) {
        FluidState fluid = state.getFluidState();
        if (fluid.is(Fluids.WATER)) {
            return Kind.WATER;
        }
        if (fluid.is(Fluids.LAVA)) {
            return Kind.LAVA;
        }
        if (state.is(Blocks.POWDER_SNOW)) {
            return Kind.POWDER_SNOW;
        }
        return null;
    }

    private InteractionResult scoop(UseOnContext context, Level level, Player player, BlockPos pos, BlockState state) {
        if (!(state.getBlock() instanceof BucketPickup pickup)) {
            return InteractionResult.PASS;
        }
        Kind scooped = kindOf(state);
        if (scooped == null) {
            return InteractionResult.PASS;
        }

        ItemStack taken = pickup.pickupBlock(player, level, pos, state);
        if (taken.isEmpty()) {
            return InteractionResult.PASS;
        }

        pickup.getPickupSound().ifPresent(sound -> player.playSound(sound, 1.0F, 1.0F));
        level.gameEvent(player, GameEvent.FLUID_PICKUP, pos);

        if (player.getAbilities().instabuild) {
            return InteractionResult.SUCCESS;
        }
        ItemStack result = new ItemStack(itemFor(scooped));
        result.setDamageValue(context.getItemInHand().getDamageValue());
        return InteractionResult.SUCCESS.heldItemTransformedTo(result);
    }

    private InteractionResult pour(UseOnContext context, Level level, Player player, BlockPos pos, BlockState state) {
        if (this.kind == Kind.POWDER_SNOW) {
            return this.pourPowderSnow(context, level, player, pos, state);
        }

        Fluid fluid = this.kind == Kind.WATER ? Fluids.WATER : Fluids.LAVA;
        BlockPos target = state.getBlock() instanceof LiquidBlockContainer container
                && container.canPlaceLiquid(player, level, pos, state, fluid)
                ? pos
                : pos.relative(context.getClickedFace());
        BlockState at = level.getBlockState(target);

        boolean placed;
        if (at.getBlock() instanceof LiquidBlockContainer container && container.canPlaceLiquid(player, level, target, at, fluid)) {
            // waterlogging a stair / slab, or filling a cauldron
            if (!level.isClientSide()) {
                container.placeLiquid(level, target, at, fluid.defaultFluidState());
            }
            placed = true;
        } else if (at.canBeReplaced(fluid)) {
            if (!level.isClientSide()) {
                level.setBlock(target, fluid.defaultFluidState().createLegacyBlock(), 11);
            }
            placed = true;
        } else {
            placed = false;
        }

        if (!placed) {
            return InteractionResult.PASS;
        }

        if (!level.isClientSide()) {
            level.playSound(null, target,
                    this.kind == Kind.WATER ? SoundEvents.BUCKET_EMPTY : SoundEvents.BUCKET_EMPTY_LAVA,
                    SoundSource.BLOCKS, 1.0F, 1.0F);
            level.gameEvent(null, GameEvent.FLUID_PLACE, target);
        }
        return finishPour(context, level, player);
    }

    private InteractionResult pourPowderSnow(UseOnContext context, Level level, Player player, BlockPos pos, BlockState state) {
        BlockPos target = state.canBeReplaced() ? pos : pos.relative(context.getClickedFace());
        if (!level.getBlockState(target).canBeReplaced()) {
            return InteractionResult.PASS;
        }
        if (!level.isClientSide()) {
            level.setBlock(target, Blocks.POWDER_SNOW.defaultBlockState(), 3);
            level.playSound(null, target, SoundEvents.BUCKET_EMPTY_POWDER_SNOW, SoundSource.BLOCKS, 1.0F, 1.0F);
            level.gameEvent(null, GameEvent.FLUID_PLACE, target);
        }
        return finishPour(context, level, player);
    }

    private InteractionResult finishPour(UseOnContext context, Level level, Player player) {
        if (player.getAbilities().instabuild) {
            return InteractionResult.SUCCESS;
        }
        return InteractionResult.SUCCESS.heldItemTransformedTo(afterPour(context.getItemInHand(), player, level));
    }

    /**
     * Turns the bucket that was just emptied into an empty bucket, chipping it if the
     * content was lava. Returns {@link ItemStack#EMPTY} once the bucket shatters.
     */
    public static ItemStack afterPour(ItemStack used, Player player, Level level) {
        int damage = used.getDamageValue();
        if (used.is(CopperIronAlloy.LAVA_BUCKET.get())) {
            damage++;
            if (damage >= MAX_USES) {
                if (!level.isClientSide()) {
                    level.playSound(null, player.getX(), player.getY(), player.getZ(),
                            SoundEvents.ITEM_BREAK, SoundSource.PLAYERS, 1.0F, 1.0F);
                }
                return ItemStack.EMPTY;
            }
        }
        ItemStack empty = new ItemStack(CopperIronAlloy.BUCKET.get());
        empty.setDamageValue(damage);
        return empty;
    }

    private static Item itemFor(Kind kind) {
        return switch (kind) {
            case WATER -> CopperIronAlloy.WATER_BUCKET.get();
            case LAVA -> CopperIronAlloy.LAVA_BUCKET.get();
            case POWDER_SNOW -> CopperIronAlloy.POWDER_SNOW_BUCKET.get();
            case EMPTY -> CopperIronAlloy.BUCKET.get();
        };
    }

    // ------------------------------------------------------------------
    // cauldron interactions (filled in during common setup)
    // ------------------------------------------------------------------

    /** empty bucket -> filled bucket; water cauldrons must be full, lava / powder snow any level. */
    public static CauldronInteraction scoopFromCauldron(Supplier<Item> filled, SoundEvent sound, boolean requireFull) {
        return (state, level, pos, player, hand, stack) -> {
            if (requireFull && state.getValue(LayeredCauldronBlock.LEVEL) < LayeredCauldronBlock.MAX_FILL_LEVEL) {
                return InteractionResult.TRY_WITH_EMPTY_HAND;
            }
            if (!level.isClientSide()) {
                ItemStack result = new ItemStack(filled.get());
                result.setDamageValue(stack.getDamageValue());
                player.setItemInHand(hand, result);
                level.setBlockAndUpdate(pos, Blocks.CAULDRON.defaultBlockState());
                level.playSound(null, pos, sound, SoundSource.BLOCKS, 1.0F, 1.0F);
                level.gameEvent(null, GameEvent.FLUID_PICKUP, pos);
            }
            return InteractionResult.SUCCESS;
        };
    }

    /** filled bucket -> empty cauldron becomes a full one. */
    public static CauldronInteraction fillCauldron(BlockState filled, SoundEvent sound) {
        return (state, level, pos, player, hand, stack) -> {
            if (!level.isClientSide()) {
                player.setItemInHand(hand, afterPour(stack, player, level));
                level.setBlockAndUpdate(pos, filled);
                level.playSound(null, pos, sound, SoundSource.BLOCKS, 1.0F, 1.0F);
                level.gameEvent(null, GameEvent.FLUID_PLACE, pos);
            }
            return InteractionResult.SUCCESS;
        };
    }

    static BlockState fullWaterCauldron() {
        return Blocks.WATER_CAULDRON.defaultBlockState().setValue(LayeredCauldronBlock.LEVEL, LayeredCauldronBlock.MAX_FILL_LEVEL);
    }

    static BlockState fullPowderSnowCauldron() {
        return Blocks.POWDER_SNOW_CAULDRON.defaultBlockState().setValue(LayeredCauldronBlock.LEVEL, LayeredCauldronBlock.MAX_FILL_LEVEL);
    }
}
