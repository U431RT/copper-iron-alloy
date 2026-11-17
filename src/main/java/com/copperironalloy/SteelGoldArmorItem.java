package com.copperironalloy;

import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;

/** 钢金盔甲：和原版金装一样能让猪灵中立。 */
public class SteelGoldArmorItem extends Item {
    public SteelGoldArmorItem(Item.Properties properties) {
        super(properties);
    }

    @Override
    public boolean makesPiglinsNeutral(ItemStack stack, LivingEntity wearer) {
        return true;
    }
}
