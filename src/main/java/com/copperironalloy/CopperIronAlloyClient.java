package com.copperironalloy;

import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.RegisterMenuScreensEvent;

/** 钢金砧沿用原版铁砧界面。 */
@EventBusSubscriber(modid = CopperIronAlloy.MODID, value = Dist.CLIENT)
public final class CopperIronAlloyClient {
    private CopperIronAlloyClient() {
    }

    @SubscribeEvent
    public static void registerScreens(RegisterMenuScreensEvent event) {
        event.register(CopperIronAlloy.STEEL_GOLD_ANVIL_MENU.get(),
                (net.minecraft.world.inventory.AnvilMenu menu, net.minecraft.world.entity.player.Inventory inventory, net.minecraft.network.chat.Component title) ->
                        new net.minecraft.client.gui.screens.inventory.AnvilScreen(menu, inventory, title));
    }
}
