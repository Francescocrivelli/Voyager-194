async function mineOneLapisOre(bot) {
  // Equip the diamond pickaxe
  const diamondPickaxe = bot.inventory.findInventoryItem(mcData.itemsByName.diamond_pickaxe.id);
  await bot.equip(diamondPickaxe, "hand");

  // Find a lapis_lazuli_ore block
  const lapisOre = await exploreUntil(bot, new Vec3(1, -1, 1), 60, () => {
    const lapisOre = bot.findBlock({
      matching: block => block.name === "lapis_ore",
      maxDistance: 32
    });
    return lapisOre;
  });
  if (!lapisOre) {
    bot.chat("Could not find a lapis lazuli ore.");
    return;
  }

  // Mine the lapis_lazuli_ore block
  await mineBlock(bot, "lapis_ore", 1);
  bot.chat("1 lapis lazuli ore mined.");
}