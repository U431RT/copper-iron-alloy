package com.copperironalloy;

import net.minecraft.world.entity.Entity;
import net.minecraft.world.level.block.DoorBlock;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.properties.BlockSetType;

/**
 * 钢金门：防爆、防僵尸破门，但可以手开。
 *
 * <p>僵尸破门只针对 {@code DoorBlock.isWoodenDoor}（即 {@code type().canOpenByHand()}）的门，
 * 所以这里用 IRON 门的声音/交互集（canOpenByHand = false）来免疫僵尸，再自己实现右键开关。</p>
 */
public class SteelGoldDoorBlock extends DoorBlock {
    public SteelGoldDoorBlock(BlockBehaviour.Properties properties) {
        super(BlockSetType.IRON, properties);
    }

    @Override
    protected net.minecraft.world.InteractionResult useWithoutItem(net.minecraft.world.level.block.state.BlockState state,
            net.minecraft.world.level.Level level, net.minecraft.core.BlockPos pos,
            net.minecraft.world.entity.player.Player player, net.minecraft.world.phys.BlockHitResult hitResult) {
        state = state.cycle(OPEN);
        level.setBlock(pos, state, 10);
        boolean open = state.getValue(OPEN);
        level.playSound(null, pos, open ? this.type().doorOpen() : this.type().doorClose(),
                net.minecraft.sounds.SoundSource.BLOCKS, 1.0F, 1.0F);
        level.gameEvent(player, open ? net.minecraft.world.level.gameevent.GameEvent.BLOCK_OPEN
                : net.minecraft.world.level.gameevent.GameEvent.BLOCK_CLOSE, pos);
        return net.minecraft.world.InteractionResult.SUCCESS;
    }

    @Override
    public boolean isOpen(net.minecraft.world.level.block.state.BlockState state) {
        return state.getValue(OPEN);
    }
}
