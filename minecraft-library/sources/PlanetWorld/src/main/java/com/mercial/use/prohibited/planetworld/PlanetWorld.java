package com.mercial.use.prohibited.planetworld;

import com.sk89q.worldedit.EditSession;
import com.sk89q.worldedit.LocalConfiguration;
import com.sk89q.worldedit.WorldEdit;
import com.sk89q.worldedit.WorldEditException;
import com.sk89q.worldedit.bukkit.BukkitAdapter;
import com.sk89q.worldedit.bukkit.BukkitWorld;
import com.sk89q.worldedit.bukkit.WorldEditPlugin;
import com.sk89q.worldedit.extent.clipboard.Clipboard;
import com.sk89q.worldedit.extent.clipboard.io.ClipboardFormat;
import com.sk89q.worldedit.extent.clipboard.io.ClipboardFormats;
import com.sk89q.worldedit.extent.clipboard.io.ClipboardReader;
import com.sk89q.worldedit.function.operation.Operation;
import com.sk89q.worldedit.function.operation.Operations;
import com.sk89q.worldedit.math.BlockVector2;
import com.sk89q.worldedit.math.BlockVector3;
import com.sk89q.worldedit.session.ClipboardHolder;
import com.sk89q.worldedit.world.block.BlockTypes;
import com.sk89q.worldguard.WorldGuard;
import com.sk89q.worldguard.bukkit.BukkitPlayer;
import com.sk89q.worldguard.bukkit.WorldGuardPlugin;
import com.sk89q.worldguard.domains.DefaultDomain;
import com.sk89q.worldguard.protection.flags.Flags;
import com.sk89q.worldguard.protection.flags.StateFlag;
import com.sk89q.worldguard.protection.managers.RegionManager;
import com.sk89q.worldguard.protection.regions.ProtectedCuboidRegion;
import com.sk89q.worldguard.protection.regions.ProtectedRegion;
import org.bukkit.Bukkit;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.World;
import org.bukkit.block.Biome;
import org.bukkit.block.Chest;
import org.bukkit.command.Command;
import org.bukkit.command.CommandExecutor;
import org.bukkit.command.CommandSender;
import org.bukkit.configuration.file.FileConfiguration;
import org.bukkit.configuration.file.YamlConfiguration;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.Listener;
import org.bukkit.event.inventory.InventoryAction;
import org.bukkit.event.inventory.InventoryClickEvent;
import org.bukkit.event.inventory.InventoryType;
import org.bukkit.event.player.PlayerJoinEvent;
import org.bukkit.generator.ChunkGenerator;
import org.bukkit.inventory.Inventory;
import org.bukkit.inventory.ItemStack;
import org.bukkit.plugin.java.JavaPlugin;
import org.jetbrains.annotations.NotNull;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.IOException;
import java.lang.reflect.Proxy;
import java.nio.file.Files;
import java.util.Objects;
import java.util.Random;

public final class PlanetWorld extends JavaPlugin implements Listener {
    private static final Logger log = LoggerFactory.getLogger(PlanetWorld.class);
    private PlotGenerator plotGenerator;
    private Random random;
    private Clipboard clipboardSpawn;
    private BlockVector3 vec3SpawnPoint;

    private static class SpaceChunkGenerator extends ChunkGenerator {
        @Override
        public @NotNull ChunkData generateChunkData(@NotNull World world, @NotNull Random random, int x, int z, @NotNull BiomeGrid biome) {
            return super.createChunkData(world);
        }

        @NotNull
        public ChunkData createVanillaChunkData(@NotNull World world, int x, int z) {
            return super.createChunkData(world);
        }

        @Override
        public boolean canSpawn(@NotNull World world, int x, int z) {
            return true;
        }

        @Override
        public @NotNull Location getFixedSpawnLocation(@NotNull World world, @NotNull Random random) {
            return new Location(world, 0, 0, 0);
        }
    }

    public static class PlotGenerator {
        private int nDirectionIndex;
        private int nCurrentSteps;
        private int nStepsMax;
        private int nTurns;
        private int nX;
        private int nZ;

        private final File pathConfiguration;

        public PlotGenerator(File path) {
            pathConfiguration = path;
            FileConfiguration config = YamlConfiguration.loadConfiguration(pathConfiguration);
            nDirectionIndex = config.getInt("nDirectionIndex");
            nCurrentSteps = config.getInt("nCurrentSteps");
            nStepsMax = config.getInt("nStepsMax", 1);
            nTurns = config.getInt("nTurns");
            nX = config.getInt("nX");
            nZ = config.getInt("nZ");
        }

        public BlockVector2 NextPlot() {
            BlockVector2 vec2Result = BlockVector2.at(nX, nZ);
            switch (nDirectionIndex) {
                case 0:
                    nX += 1;
                    break;
                case 1:
                    nZ += 1;
                    break;
                case 2:
                    nX -= 1;
                    break;
                case 3:
                    nZ -= 1;
                    break;
                default:
                    throw new RuntimeException();
            }
            nCurrentSteps += 1;
            if (nCurrentSteps == nStepsMax) {
                nCurrentSteps = 0;
                nDirectionIndex = (nDirectionIndex + 1) % 4;
                nTurns += 1;

                if (nTurns == 2) {
                    nTurns = 0;
                    nStepsMax += 1;
                }
            }
            {
                FileConfiguration config = new YamlConfiguration();
                config.set("nDirectionIndex", nDirectionIndex);
                config.set("nCurrentSteps", nCurrentSteps);
                config.set("nStepsMax", nStepsMax);
                config.set("nTurns", nTurns);
                config.set("nX", nX);
                config.set("nZ", nZ);
                try {
                    config.save(pathConfiguration);
                } catch (IOException e) {
                    log.error("e: ", e);
                }
            }
            return vec2Result;
        }
    }

    private static Player wrapPlayer(Player player) {
        return (Player) Proxy.newProxyInstance(
                Player.class.getClassLoader(),
                new Class<?>[]{Player.class},
                (proxy, method, args1) -> {
                    if (method.equals(Player.class.getMethod("isOp"))) {
                        return true;
                    } else {
                        return method.invoke(player, args1);
                    }
                }
        );
    }

    public static class CommandSharePlanet implements CommandExecutor {
        @Override
        public boolean onCommand(@NotNull CommandSender sender, @NotNull Command command, @NotNull String label, String[] args) {
            if (sender instanceof Player) {
                sender.getServer().dispatchCommand(
                        wrapPlayer((Player) sender),
                        String.format("rg addmember %s %s", getPlayerPlanetName(sender.getName()), String.join(" ", args))
                );
                return true;
            } else {
                sender.sendMessage("Only players can use this cmd");
                return false;
            }
        }
    }

    public static class CommandTravelToPlanet implements CommandExecutor {
        @Override
        public boolean onCommand(@NotNull CommandSender sender, @NotNull Command command, @NotNull String label, String[] args) {
            if (sender instanceof Player) {
                if (1 < args.length) {
                    return false;
                } else {
                    sender.getServer().dispatchCommand(
                            wrapPlayer((Player) sender),
                            String.format("rg tp %s", getPlayerPlanetName(0 == args.length ? sender.getName() : args[0]))
                    );
                    return true;
                }
            } else {
                sender.sendMessage("Only players can use this cmd");
                return false;
            }
        }
    }

    private static String getPlayerPlanetName(String strPlayerName) {
        return strPlayerName + "Planet";
    }

    @Override
    public ChunkGenerator getDefaultWorldGenerator(@NotNull String worldName, String id) {
        return new SpaceChunkGenerator();
    }

    @Override
    public void onEnable() {
        random = new Random();
        plotGenerator = new PlotGenerator(new File(this.getServer().getWorldContainer(), "PlotState.yml"));
        Bukkit.getPluginManager().registerEvents(this, this);
        Objects.requireNonNull(this.getCommand("share")).setExecutor(new CommandSharePlanet());
        Objects.requireNonNull(this.getCommand("travel")).setExecutor(new CommandTravelToPlanet());
        File file = new File(
                WorldEdit
                        .getInstance()
                        .getWorkingDirectoryPath(WorldEdit.getInstance().getConfiguration().saveDir).toFile(),
                "spawn1.schem"
        );
        ClipboardFormat format = Objects.requireNonNull(ClipboardFormats.findByFile(file));
        try (ClipboardReader reader = format.getReader(Files.newInputStream(file.toPath()))) {
            clipboardSpawn = reader.read();
        } catch (IOException e) {
            throw new RuntimeException(e);
        }

        for (BlockVector3 blockVector3 : clipboardSpawn.getRegion().getBoundingBox()) {
            if (clipboardSpawn.getBlock(blockVector3).getBlockType() == BlockTypes.RED_WOOL) {
                clipboardSpawn.setOrigin(blockVector3);
                vec3SpawnPoint = BlockVector3.UNIT_Y;
            }
        }
    }

    @EventHandler
    public void onInventoryClick(InventoryClickEvent event) {
        if (event.getWhoClicked() instanceof Player) {
            Inventory topInventory = event.getView().getTopInventory();
            if (topInventory.getType() == InventoryType.CHEST) {
                if (event.getRawSlot() < topInventory.getSize()) {
                    InventoryAction action = event.getAction();
                    if (action == InventoryAction.PICKUP_ALL ||
                            action == InventoryAction.PICKUP_HALF ||
                            action == InventoryAction.PICKUP_ONE ||
                            action == InventoryAction.PICKUP_SOME ||
                            action == InventoryAction.MOVE_TO_OTHER_INVENTORY ||
                            action == InventoryAction.HOTBAR_SWAP ||
                            action == InventoryAction.HOTBAR_MOVE_AND_READD) {
                        event.setCancelled(true);
                    }
                }
            }
        }
    }

    @EventHandler
    public void onPlayerJoin(PlayerJoinEvent event) {
        Player player = event.getPlayer();
        World world = player.getWorld();
        if (player.getBedSpawnLocation() == null) {
            try {
                ItemStack[] items = {
                        new ItemStack(Material.WRITABLE_BOOK),
                        new ItemStack(Material.WRITABLE_BOOK),
                        new ItemStack(Material.WRITABLE_BOOK),
                        new ItemStack(Material.WRITABLE_BOOK),
                        new ItemStack(Material.WRITABLE_BOOK)
                };
                player.getInventory().addItem(items);
                BukkitWorld weWorld = new BukkitWorld(world);

                BlockVector2 vec2Size = clipboardSpawn.getDimensions().toBlockVector2();
                BlockVector3 vec3Position;
                try (EditSession editSession = WorldEdit.getInstance().newEditSession(weWorld)) {
                    BlockVector2 vec2Center = plotGenerator.NextPlot();
                    vec3Position = BlockVector3.at(
                            vec2Center.getX() * vec2Size.getBlockX(),
                            100,
                            vec2Center.getZ() * vec2Size.getBlockZ()
                    );
                    Operation operation = new ClipboardHolder(clipboardSpawn)
                            .createPaste(editSession)
                            .to(vec3Position)
                            .build();
                    Operations.complete(operation);
                } catch (WorldEditException e) {
                    throw new RuntimeException(e);
                }
                Location locationSpawn = new Location(
                        world,
                        vec3Position.getX() + vec3SpawnPoint.getX(),
                        vec3Position.getY() + vec3SpawnPoint.getY(),
                        vec3Position.getZ() + vec3SpawnPoint.getZ()
                );
                RegionManager regionManager = Objects.requireNonNull(
                        WorldGuard
                                .getInstance()
                                .getPlatform()
                                .getRegionContainer()
                                .get(BukkitAdapter.adapt(world))
                );
                ProtectedRegion region = new ProtectedCuboidRegion(
                        getPlayerPlanetName(player.getName()),
                        vec3Position.add(clipboardSpawn.getMinimumPoint().subtract(clipboardSpawn.getOrigin())).withY(0),
                        vec3Position.add(clipboardSpawn.getMaximumPoint().subtract(clipboardSpawn.getOrigin())).withY(255)
                );
                {
                    DefaultDomain defaultDomain = new DefaultDomain();
                    defaultDomain.addPlayer(new BukkitPlayer(WorldGuardPlugin.inst(), player));
                    region.setOwners(defaultDomain);
                    region.setFlag(Flags.PVP, StateFlag.State.DENY);
                    region.setFlag(Flags.BUILD, StateFlag.State.DENY);
                    region.setFlag(Flags.CHEST_ACCESS, StateFlag.State.ALLOW);
                    region.setFlag(Flags.TELE_LOC, new com.sk89q.worldedit.util.Location(weWorld, locationSpawn.getX(), locationSpawn.getY(), locationSpawn.getZ(), 0, 0));
                    regionManager.addRegion(region);
                }

                world.getChunkAt(locationSpawn).load();
                player.setBedSpawnLocation(locationSpawn, true);
                player.teleport(locationSpawn);
            } catch (Exception exception) {
                player.sendMessage(exception.toString());
            }
        }
    }
}
