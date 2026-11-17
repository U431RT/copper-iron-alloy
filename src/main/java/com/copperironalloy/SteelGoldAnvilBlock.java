package com.copperironalloy;

import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.stats.Stats;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.SimpleMenuProvider;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.ContainerLevelAccess;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.AnvilBlock;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;

/** 钢金砧：和铁砧一样用，但永远不会裂开。 */
public class SteelGoldAnvilBlock extends AnvilBlock {
    public SteelGoldAnvilBlock(BlockBehaviour.Properties properties) {
        super(properties);
    }

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hitResult) {
        if (level.isClientSide()) {
            return InteractionResult.SUCCESS;
        }
        player.openMenu(new SimpleMenuProvider(
                (containerId, inventory, p) -> new SteelGoldAnvilMenu(containerId, inventory, ContainerLevelAccess.create(level, pos)),
                Component.translatable("container.copper_iron_alloy.steel_gold_anvil")));
        player.awardStat(Stats.INTERACT_WITH_ANVIL);
        return InteractionResult.CONSUME;
    }
}
