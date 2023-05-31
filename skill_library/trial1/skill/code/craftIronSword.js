async function craftIronSword(bot) {
  // Check if there are enough iron ingots and sticks in the inventory
  const ironIngotsCount = bot.inventory.count(mcData.itemsByName.iron_ingot.id);
  const sticksCount = bot.inventory.count(mcData.itemsByName.stick.id);

  // If not enough iron ingots or sticks, collect the required items
  if (ironIngotsCount < 2) {
    await mineBlock(bot, "iron_ore", 2 - ironIngotsCount);
    bot.chat("Collected iron ores.");
    await smeltItem(bot, "iron_ore", "coal", 2 - ironIngotsCount);
    bot.chat("Smelted iron ores into iron ingots.");
  }
  if (sticksCount < 1) {
    await craftItem(bot, "stick", 1);
    bot.chat("Crafted sticks.");
  }

  // Place the crafting table near the bot
  const craftingTablePosition = bot.entity.position.offset(1, 0, 0);
  await placeItem(bot, "crafting_table", craftingTablePosition);

  // Craft an iron sword using the crafting table
  await craftItem(bot, "iron_sword", 1);
  bot.chat("Crafted an iron sword.");
}