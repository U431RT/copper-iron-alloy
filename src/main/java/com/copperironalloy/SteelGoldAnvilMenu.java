package com.copperironalloy;

import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.inventory.AnvilMenu;
import net.minecraft.world.inventory.ContainerLevelAccess;
import net.minecraft.world.level.block.state.BlockState;

/**
 * 钢金砧的菜单：经验消耗减半，单纯改名免费。
 *
 * <p>原版 {@code AnvilMenu.createResult()} 是 final，但真正算钱的 {@link AnvilMenu#createResultInternal()}
 * 可以覆写；覆写后把 cost 改掉即可。</p>
 */
public class SteelGoldAnvilMenu extends AnvilMenu {
    /** 修理时额外恢复的最大耐久比例（不是加耐久上限）。 */
    private static final float EXTRA_REPAIR_RESTORE = 0.10F;

    /** AnvilMenu.cost is a private final DataSlot; drive it directly. */
    private static final java.lang.reflect.Field COST_FIELD = findCostField();

    private static java.lang.reflect.Field findCostField() {
        try {
            java.lang.reflect.Field field = AnvilMenu.class.getDeclaredField("cost");
            field.setAccessible(true);
            return field;
        } catch (ReflectiveOperationException e) {
            throw new IllegalStateException("AnvilMenu.cost not found", e);
        }
    }

    public SteelGoldAnvilMenu(int containerId, Inventory inventory, ContainerLevelAccess access) {
        super(containerId, inventory, access);
    }

    @Override
    protected void createResultInternal() {
        super.createResultInternal();

        // 先补那 10%，这样即使后面 cost 为 0 也不会被跳过
        applyExtraRepair();

        int cost = this.getCost();
        if (cost <= 0) {
            return;
        }

        // rename only (vanilla charges 1 level) -> free, otherwise half price
        int adjusted = (this.repairItemCountCost == 0 && cost <= 1)
                ? 0
                : Math.max(1, (cost + 1) / 2);
        try {
            ((net.minecraft.world.inventory.DataSlot) COST_FIELD.get(this)).set(adjusted);
        } catch (ReflectiveOperationException e) {
            throw new IllegalStateException(e);
        }
    }

    /** 在钢金砧上修东西：除了原版修好的部分，额外再补 10% 耐久（上限不变）。 */
    private void applyExtraRepair() {
        net.minecraft.world.item.ItemStack input = this.inputSlots.getItem(0);
        net.minecraft.world.item.ItemStack result = this.resultSlots.getItem(0);
        if (input.isEmpty() || result.isEmpty() || !result.isDamageableItem()) {
            return;
        }
        boolean repaired = result.getDamageValue() < input.getDamageValue() || this.repairItemCountCost > 0;
        if (!repaired) {
            return;
        }
        int extra = Math.max(1, Math.round(result.getMaxDamage() * EXTRA_REPAIR_RESTORE));
        result.setDamageValue(Math.max(0, result.getDamageValue() - extra));
    }

    /**
     * 原版 {@code mayPickup} 额外要求 {@code cost > 0}，所以 cost 设成 0 时结果根本拿不下来
     * （测试时“改名拿不下来”就是这个原因）。这里去掉那条限制，只要结果槽有东西就能拿。
     */
    @Override
    protected boolean mayPickup(net.minecraft.world.entity.player.Player player, boolean hasItem) {
        return (player.getAbilities().instabuild || player.experienceLevel >= this.getCost()) && hasItem;
    }

    @Override
    protected boolean isValidBlock(BlockState state) {
        return state.is(CopperIronAlloy.STEEL_GOLD_ANVIL.get());
    }
}
