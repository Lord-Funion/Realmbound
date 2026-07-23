#include <algorithm>
#include <chrono>
#include <cctype>
#include <cstdio>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>
#include <random>
#include <sstream>
#include <stdexcept>
#include <string>
#include <thread>
#include <unordered_map>
#include <utility>
#include <vector>

#ifdef _WIN32
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#else
#include <unistd.h>
#endif

namespace fs = std::filesystem;

constexpr int BASIC_DAMAGE = 4;
constexpr int STATUS_DAMAGE = 5;
constexpr const char* FINISHED_SCENE = "finished";
constexpr const char* SAVE_PATH = "saves/cpp_autosave.cppsave";
constexpr const char* EXIT_LABEL = "Exit Game";

struct GameOver : std::exception {};
struct ExitGame : std::exception {};

namespace term {
constexpr const char* RESET = "\033[0m";
constexpr const char* BOLD = "\033[1m";
constexpr const char* DIM = "\033[2m";
constexpr const char* RED = "\033[31m";
constexpr const char* YELLOW = "\033[33m";
constexpr const char* BLUE = "\033[34m";
constexpr const char* MAGENTA = "\033[35m";
constexpr const char* CYAN = "\033[36m";
constexpr const char* BRIGHT_GREEN = "\033[92m";
constexpr const char* BRIGHT_YELLOW = "\033[93m";
constexpr const char* BRIGHT_CYAN = "\033[96m";
constexpr const char* BRIGHT_MAGENTA = "\033[95m";

bool no_color_requested() {
    return std::getenv("NO_COLOR") != nullptr;
}

bool enable_virtual_terminal() {
    if (no_color_requested()) {
        return false;
    }

#ifdef _WIN32
    HANDLE output = GetStdHandle(STD_OUTPUT_HANDLE);
    if (output == INVALID_HANDLE_VALUE || output == nullptr) {
        return false;
    }

    DWORD mode = 0;
    if (!GetConsoleMode(output, &mode)) {
        return false;
    }

    mode |= ENABLE_VIRTUAL_TERMINAL_PROCESSING;
    if (!SetConsoleMode(output, mode)) {
        return false;
    }
    return true;
#else
    return isatty(fileno(stdout)) != 0;
#endif
}

bool color_enabled() {
    static const bool enabled = enable_virtual_terminal();
    return enabled;
}

std::string paint(const std::string& text, const char* color) {
    if (!color_enabled()) {
        return text;
    }
    return std::string(color) + text + RESET;
}

std::string bold(const std::string& text) { return paint(text, BOLD); }
std::string dim(const std::string& text) { return paint(text, DIM); }
std::string red(const std::string& text) { return paint(text, RED); }
std::string yellow(const std::string& text) { return paint(text, YELLOW); }
std::string blue(const std::string& text) { return paint(text, BLUE); }
std::string magenta(const std::string& text) { return paint(text, MAGENTA); }
std::string cyan(const std::string& text) { return paint(text, CYAN); }
std::string bright_green(const std::string& text) { return paint(text, BRIGHT_GREEN); }
std::string bright_yellow(const std::string& text) { return paint(text, BRIGHT_YELLOW); }
std::string bright_cyan(const std::string& text) { return paint(text, BRIGHT_CYAN); }
std::string bright_magenta(const std::string& text) { return paint(text, BRIGHT_MAGENTA); }
}

struct Spell {
    bool has_damage = false;
    int damage = 0;
    bool has_healing = false;
    int healing = 0;
    int mana_cost = 0;
    int burn = 0;
    int stun = 0;
    std::string description;
};

struct FrogAttack {
    bool has_damage = false;
    int damage = 0;
    bool has_healing = false;
    int healing = 0;
    int energy_cost = 0;
    int burn = 0;
    int stun = 0;
    std::string description;
};

struct Monster {
    int health = 0;
    int damage = 0;
    int reward = 10;
    std::vector<std::string> attacks;
};

struct Player {
    std::string name = "Adventurer";
    int money = 0;
    int health = 100;
    int health_max = 100;
    int mana = 100;
    int mana_max = 100;
    int armor = 0;
    int weapon_damage = 0;
    int extra_damage = 0;
    bool frog_mode = false;
    int frog_power = 0;
    int frog_energy = 0;
    int frog_energy_max = 0;
    int road_progress = 0;
    std::vector<std::string> backpack;
    std::vector<std::string> spells;
    std::vector<std::string> frog_attacks;
};

struct State {
    Player player;
    std::unordered_map<std::string, bool> shop_stock;
    std::string next_scene = "intro";
};

const State* active_autosave_state = nullptr;
bool autosave_running = false;
Player* active_quick_menu_player = nullptr;
bool quick_menu_running = false;

void autosave_tick();
bool handle_quick_menu_request(const std::string& value);
void pause_for_output();

struct AutosaveScope {
    const State* previous = nullptr;

    explicit AutosaveScope(const State& state) : previous(active_autosave_state) {
        active_autosave_state = &state;
    }

    ~AutosaveScope() {
        active_autosave_state = previous;
    }
};

struct QuickMenuScope {
    Player* previous = nullptr;

    explicit QuickMenuScope(Player& player) : previous(active_quick_menu_player) {
        active_quick_menu_player = &player;
    }

    ~QuickMenuScope() {
        active_quick_menu_player = previous;
    }
};

struct MenuOption {
    std::string key;
    std::string label;
    std::string value;
    std::string detail;
    std::vector<std::string> aliases;
    bool enabled = true;
    std::string status;

    MenuOption(
        std::string key_value,
        std::string label_value,
        std::string option_value,
        std::string detail_value = "",
        std::vector<std::string> alias_values = {},
        bool enabled_value = true,
        std::string status_value = ""
    )
        : key(std::move(key_value)),
          label(std::move(label_value)),
          value(std::move(option_value)),
          detail(std::move(detail_value)),
          aliases(std::move(alias_values)),
          enabled(enabled_value),
          status(std::move(status_value)) {}
};

std::mt19937& rng() {
    static std::mt19937 engine(std::random_device{}());
    return engine;
}

int random_int(int min, int max) {
    std::uniform_int_distribution<int> dist(min, max);
    return dist(rng());
}

template <typename T>
const T& random_choice(const std::vector<T>& values) {
    std::uniform_int_distribution<std::size_t> dist(0, values.size() - 1);
    return values[dist(rng())];
}

std::string trim(const std::string& value) {
    std::size_t first = 0;
    while (first < value.size() && std::isspace(static_cast<unsigned char>(value[first]))) {
        ++first;
    }
    std::size_t last = value.size();
    while (last > first && std::isspace(static_cast<unsigned char>(value[last - 1]))) {
        --last;
    }
    return value.substr(first, last - first);
}

std::string normalize_choice(const std::string& value) {
    std::string lowered;
    bool in_space = false;
    for (char ch : trim(value)) {
        if (std::isspace(static_cast<unsigned char>(ch))) {
            if (!in_space && !lowered.empty()) {
                lowered.push_back(' ');
            }
            in_space = true;
        } else {
            lowered.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(ch))));
            in_space = false;
        }
    }
    return trim(lowered);
}

std::string ask(const std::string& prompt) {
    while (true) {
        std::cout << term::bright_cyan(prompt);
        std::string value;
        if (!std::getline(std::cin, value)) {
            throw std::runtime_error("Input stream closed.");
        }
        value = trim(value);
        if (handle_quick_menu_request(value)) {
            continue;
        }
        return value;
    }
}

bool starts_with(const std::string& value, const std::string& prefix) {
    return value.rfind(prefix, 0) == 0;
}

double text_speed_multiplier() {
    const char* raw_speed = std::getenv("TEXT_ADVENTURE_SPEED");
    std::string speed = raw_speed ? normalize_choice(raw_speed) : "normal";
    if (speed == "instant") {
        return 0.0;
    }
    if (speed == "fast") {
        return 0.55;
    }
    if (speed == "slow") {
        return 1.35;
    }
    return 1.0;
}

void pause_for_output() {
    double multiplier = text_speed_multiplier();
    if (multiplier <= 0.0) {
        return;
    }
    auto delay = std::chrono::milliseconds(static_cast<int>(650 * multiplier));
    std::this_thread::sleep_for(delay);
}

std::string colorize_plain_message(const std::string& message) {
    if (message.find("\033[") != std::string::npos) {
        return message;
    }

    std::size_t first = 0;
    while (first < message.size() && std::isspace(static_cast<unsigned char>(message[first]))) {
        ++first;
    }
    std::string leading = message.substr(0, first);
    std::string body = message.substr(first);
    if (body.empty()) {
        return message;
    }

    std::string lowered = normalize_choice(body);
    if (starts_with(body, "===") || lowered.find("the end") != std::string::npos) {
        return leading + term::bright_yellow(body);
    }
    if (lowered.find("game over") != std::string::npos ||
        lowered.find("damage") != std::string::npos ||
        lowered.find("attacks") != std::string::npos) {
        return leading + term::red(body);
    }
    if (lowered.find("good job") != std::string::npos ||
        lowered.find("you learned") != std::string::npos ||
        lowered.find("you bought") != std::string::npos ||
        lowered.find("cloud synced") != std::string::npos) {
        return leading + term::bright_green(body);
    }
    if (lowered.find("credits:") == 0) {
        return leading + term::dim(body);
    }
    if (body.find('"') != std::string::npos) {
        return leading + term::bright_cyan(body);
    }
    return message;
}

void say(const std::string& message) {
    std::cout << colorize_plain_message(message) << "\n";
    pause_for_output();
    autosave_tick();
}

void exit_game() {
    say("\nGoodbye.");
    throw ExitGame();
}

void divider(const std::string& title) {
    std::cout << "\n" << term::bright_yellow("=== " + title + " ===") << "\n";
}

std::string stat_meter(int current, int maximum, int width = 16) {
    if (maximum <= 0) {
        return "[" + std::string(width, '-') + "]";
    }
    int capped = std::max(0, std::min(current, maximum));
    int filled = static_cast<int>((width * capped + maximum / 2) / maximum);
    return "[" + std::string(filled, '#') + std::string(width - filled, '-') + "]";
}

std::string money_text(int amount) {
    return term::bright_yellow(std::to_string(amount) + " " + (amount == 1 ? "Whoop Nickel" : "Whoop Nickels"));
}

std::string health_text(int current, int maximum) {
    return term::red(stat_meter(current, maximum) + " " + std::to_string(current) + "/" + std::to_string(maximum));
}

std::string health_value_text(int current, int maximum) {
    return term::red(std::to_string(current) + "/" + std::to_string(maximum));
}

std::string mana_text(int current, int maximum) {
    return term::blue(stat_meter(current, maximum) + " " + std::to_string(current) + "/" + std::to_string(maximum));
}

std::string mana_value_text(int current, int maximum) {
    return term::blue(std::to_string(current) + "/" + std::to_string(maximum));
}

void clocktower_scene(Player& player, std::unordered_map<std::string, bool>& shop_stock);
void well_scene(Player& player);

const std::vector<std::string>& scene_order() {
    static const std::vector<std::string> order = {
        "intro",
        "wizard",
        "locked_door",
        "first_goblin",
        "village",
        "forest",
        "twin_doors",
        "witch",
        "mountain_pass",
        "moonlit_market",
        "vampire_castle",
        "false_throne",
        "underkeep",
        "clocktower",
        "well",
        "hundred_day_road",
        "dragon_gate",
        "final_battle",
    };
    return order;
}

const std::unordered_map<std::string, std::string>& scene_titles() {
    static const std::unordered_map<std::string, std::string> titles = {
        {"intro", "Chocolate Frog"},
        {"wizard", "Rumblerod"},
        {"locked_door", "Locked Door"},
        {"first_goblin", "First Goblin"},
        {"village", "Village"},
        {"forest", "Forest Trail"},
        {"twin_doors", "Twin Doors"},
        {"witch", "Witch"},
        {"mountain_pass", "Mountain Pass"},
        {"moonlit_market", "Moonlit Market"},
        {"vampire_castle", "Vampire Castle"},
        {"false_throne", "False Throne"},
        {"underkeep", "Underkeep"},
        {"clocktower", "Clocktower"},
        {"well", "Old Well"},
        {"hundred_day_road", "The Hundred-Day Road"},
        {"dragon_gate", "Dragon Gate"},
        {"final_battle", "Final Battle"},
        {FINISHED_SCENE, "Finished Game"},
    };
    return titles;
}

const std::unordered_map<std::string, Spell>& spells() {
    static const std::unordered_map<std::string, Spell> data = {
        {"Fireball", {true, 14, false, 0, 12, 2, 0, "Deals 14 damage and sets the target burning."}},
        {"Arcane Blast", {true, 0, false, 0, 32, 0, 2, "Stuns an enemy for 2 turns."}},
        {"Thunderstorm", {true, 32, false, 0, 45, 0, 0, "Deals 32 damage."}},
        {"Restoration Incantation", {false, 0, true, 24, 35, 0, 0, "Heals 24 health in battle."}},
        {"Frost Nova", {true, 18, false, 0, 38, 0, 1, "Deals 18 damage and freezes the enemy for 1 turn."}},
        {"Solar Beam", {true, 45, false, 0, 65, 0, 0, "Deals 45 damage."}},
        {"Life Bloom", {false, 0, true, 45, 55, 0, 0, "Heals 45 health in battle."}},
        {"Lockio Reducto", {false, 0, false, 0, 0, 0, 0, "Unlocks sealed doors."}},
    };
    return data;
}

const std::unordered_map<std::string, FrogAttack>& frog_attacks() {
    static const std::unordered_map<std::string, FrogAttack> data = {
        {"Tongue Slap", {true, 8, false, 0, 0, 0, 0, "Free frog attack."}},
        {"Bubble Burp", {true, 16, false, 0, 8, 2, 0, "Deals 16 damage and leaves the enemy bubbling."}},
        {"Royal Croak", {true, 26, false, 0, 14, 0, 1, "Deals 26 damage and startles the enemy."}},
        {"Snack Break", {false, 0, true, 24, 12, 0, 0, "The frog produces snacks and heals 24 health."}},
        {"Moon Leap", {true, 38, false, 0, 22, 0, 0, "A heavy moonlit frog slam."}},
        {"Dragonfly Dive", {true, 50, false, 0, 30, 0, 1, "A late-game dive that deals 50 damage and stuns."}},
    };
    return data;
}

const std::unordered_map<std::string, Monster>& monsters() {
    static const std::unordered_map<std::string, Monster> data = {
        {"goblin", {32, 8, 10, {"punch", "screech", "headbutt"}}},
        {"troll", {52, 12, 10, {"club", "slam", "bite"}}},
        {"skeleton", {36, 15, 10, {"bone club", "bone scare", "bone headbutt"}}},
        {"werewolf", {68, 18, 10, {"claw", "bite", "howl"}}},
        {"ogre", {86, 24, 10, {"big club", "super smash", "stomp"}}},
        {"witch", {64, 16, 10, {"poison", "curse", "hex"}}},
        {"vampire", {82, 21, 10, {"transform into bat", "fangs", "suck blood"}}},
        {"gate rat", {22, 7, 10, {"rusty nibble", "ankle dash", "tiny ambush"}}},
        {"smoke imp", {38, 10, 10, {"soot slap", "ember pinch", "smoke cough"}}},
        {"bramble wolf", {54, 16, 10, {"thorn bite", "vine trip", "bark howl"}}},
        {"treasure mimic", {58, 18, 10, {"lid snap", "coin spit", "hinge bash"}}},
        {"curse candle", {45, 17, 10, {"wax splash", "blue flame", "bad birthday wish"}}},
        {"ice goblin", {72, 20, 10, {"snowball uppercut", "icicle jab", "freezing giggle"}}},
        {"snow bat", {48, 17, 10, {"frost bite", "wing slap", "sleet shriek"}}},
        {"shadow knight", {95, 25, 10, {"gloom slash", "helmet bonk", "midnight shove"}}},
        {"receipt wraith", {62, 19, 10, {"paper cut", "late fee", "ink cloud"}}},
        {"basement bat", {58, 18, 10, {"cape flutter", "fang tap", "ceiling dive"}}},
        {"sugar golem", {105, 27, 10, {"frosting fist", "sprinkle storm", "cookie crumble"}}},
        {"rust rat", {66, 20, 10, {"rust bite", "pipe scramble", "gear squeak"}}},
        {"glass cobra", {88, 28, 10, {"mirror fang", "shatter hiss", "scale flash"}}},
        {"crystal dragon", {145, 32, 10, {"rainbow sneeze", "crystal claw", "tail prism"}}},
        {"crown wraith", {110, 30, 10, {"royal glare", "cold decree", "crown toss"}}},
        {"lord dreadbiscuit", {180, 36, 10, {"crumb storm", "butter curse", "ego blast"}}},
        {"realmbound dragon", {260, 42, 10, {"starfire breath", "crownquake", "eclipse wingstorm", "ancient claw"}}},
        {"ashfall pilgrim", {96, 23, 10, {"ember staff", "cinder prayer", "ash cloak"}}},
        {"lantern jackal", {100, 24, 10, {"lamp bite", "oil slick", "howling flare"}}},
        {"mossbound knight", {108, 25, 10, {"root shield", "green blade", "helmet sprout"}}},
        {"mirror moth", {92, 26, 10, {"glass wing", "reflection flash", "powder dazzle"}}},
        {"ember librarian", {112, 27, 10, {"burning bookmark", "shushing flame", "index curse"}}},
        {"fogbank siren", {116, 28, 10, {"mist song", "harbor pull", "whiteout whisper"}}},
        {"tin crown bandit", {120, 29, 10, {"fake decree", "coin knife", "royal shove"}}},
        {"hollow beekeeper", {124, 30, 10, {"wax veil", "hive rattle", "stinger rain"}}},
        {"moonlit scarecrow", {128, 31, 10, {"straw jab", "moon grin", "field hex"}}},
        {"iron acorn brute", {136, 32, 10, {"oak punch", "iron shell", "squirrel panic"}}},
        {"velvet gargoyle", {132, 33, 10, {"soft stone claw", "curtain dive", "balcony crash"}}},
        {"clockwork eel", {118, 34, 10, {"gear bite", "static coil", "spring lash"}}},
        {"glacier monk", {140, 35, 10, {"frozen palm", "silent avalanche", "ice mantra"}}},
        {"briar drummer", {126, 36, 10, {"thorn rhythm", "snare root", "wild tempo"}}},
        {"marble banshee", {144, 37, 10, {"statue shriek", "grave echo", "cracked aria"}}},
        {"thunder yak", {150, 38, 10, {"storm charge", "horn thunder", "cloud stomp"}}},
        {"paper lantern fiend", {122, 39, 10, {"paper flame", "festival fright", "string snare"}}},
        {"copper wyvern", {156, 40, 10, {"coin-scale rake", "green fire", "roof snatch"}}},
        {"old road revenant", {148, 41, 10, {"mile marker", "dust hand", "forgotten shortcut"}}},
        {"saltwater specter", {152, 42, 10, {"brine wave", "anchor chill", "shipbell howl"}}},
        {"orchard mimic", {160, 43, 10, {"apple snap", "branch disguise", "basket bite"}}},
        {"candlewax duelist", {146, 44, 10, {"wick rapier", "melting feint", "flame salute"}}},
        {"rune-tusk boar", {168, 45, 10, {"glyph gore", "mud ward", "tusk spell"}}},
        {"midnight tax collector", {154, 46, 10, {"late fee", "receipt lash", "audit glare"}}},
        {"feathered basilisk", {162, 47, 10, {"plume stare", "stone chirp", "talon flash"}}},
        {"broken compass spirit", {158, 48, 10, {"northless pull", "needle spin", "lost road"}}},
        {"jewel wasp swarm", {170, 49, 10, {"ruby sting", "buzzing crown", "gem cloud"}}},
        {"singing stump", {166, 50, 10, {"root chorus", "bark note", "splinter solo"}}},
        {"blackglass panther", {176, 51, 10, {"mirror pounce", "shadow claw", "glass growl"}}},
        {"sunken bell knight", {184, 52, 10, {"drowned chime", "rusted lance", "undertow step"}}},
        {"nettle witchling", {172, 53, 10, {"sting charm", "green hex", "thorn wink"}}},
        {"storm cellar troll", {190, 54, 10, {"barrel throw", "basement boom", "storm burp"}}},
        {"silver mask rogue", {178, 55, 10, {"mask flash", "quiet dagger", "vanishing bow"}}},
        {"bonewheel racer", {182, 56, 10, {"wheel crash", "rib spoke", "graveyard lap"}}},
        {"spellbook leech", {188, 57, 10, {"page drain", "ink bite", "borrowed spell"}}},
        {"cloud anvil giant", {208, 58, 10, {"sky hammer", "anvil drop", "forge thunder"}}},
        {"porcelain hydra", {202, 59, 10, {"china fang", "teacup roar", "seven saucers"}}},
        {"scarecrow magistrate", {194, 60, 10, {"field warrant", "straw verdict", "gavel stick"}}},
        {"obsidian choir", {210, 61, 10, {"black hymn", "shard harmony", "echo cut"}}},
        {"frostroot colossus", {224, 62, 10, {"winter branch", "rootquake", "snow crown"}}},
        {"honeycomb horror", {198, 63, 10, {"sticky maw", "hexagon swarm", "golden sting"}}},
        {"brass cathedral rook", {218, 64, 10, {"bell tower dive", "brass wing", "sanctuary slam"}}},
        {"map-eating serpent", {206, 65, 10, {"cartography bite", "folded coil", "legend swallow"}}},
        {"velvet thunderlord", {230, 66, 10, {"royal thunder", "soft lightning", "storm decree"}}},
        {"eclipse ferryman", {220, 67, 10, {"black oar", "river shadow", "fare curse"}}},
        {"crownless lion", {236, 68, 10, {"mane flare", "throne roar", "claw decree"}}},
        {"dream ash phantom", {214, 69, 10, {"sleep cinder", "nightmare veil", "pillow grave"}}},
        {"seven-key jailer", {242, 70, 10, {"keyring crush", "cell door slam", "warden glare"}}},
        {"realmquake titan", {260, 72, 10, {"continent stomp", "fault line", "mountain backhand"}}},
        {"calendar dragon", {280, 74, 10, {"lost month", "deadline flame", "year-end wing"}}},
    };
    return data;
}

const std::vector<std::string>& long_road_enemies() {
    static const std::vector<std::string> enemies = {
        "ashfall pilgrim",
        "lantern jackal",
        "mossbound knight",
        "mirror moth",
        "ember librarian",
        "fogbank siren",
        "tin crown bandit",
        "hollow beekeeper",
        "moonlit scarecrow",
        "iron acorn brute",
        "velvet gargoyle",
        "clockwork eel",
        "glacier monk",
        "briar drummer",
        "marble banshee",
        "thunder yak",
        "paper lantern fiend",
        "copper wyvern",
        "old road revenant",
        "saltwater specter",
        "orchard mimic",
        "candlewax duelist",
        "rune-tusk boar",
        "midnight tax collector",
        "feathered basilisk",
        "broken compass spirit",
        "jewel wasp swarm",
        "singing stump",
        "blackglass panther",
        "sunken bell knight",
        "nettle witchling",
        "storm cellar troll",
        "silver mask rogue",
        "bonewheel racer",
        "spellbook leech",
        "cloud anvil giant",
        "porcelain hydra",
        "scarecrow magistrate",
        "obsidian choir",
        "frostroot colossus",
        "honeycomb horror",
        "brass cathedral rook",
        "map-eating serpent",
        "velvet thunderlord",
        "eclipse ferryman",
        "crownless lion",
        "dream ash phantom",
        "seven-key jailer",
        "realmquake titan",
        "calendar dragon",
    };
    return enemies;
}

const std::vector<std::string>& loot_drops() {
    static const std::vector<std::string> drops = {
        "Suspicious Gold Nugget",
        "Metal Scraps of Mystery",
        "Pointy Monster Tooth",
        "Rotten Flesh",
        "Small Health Potion",
        "Mystery Goop",
        "Strange Liquid",
        "Gnarled Toenail",
        "Moon Cheese",
        "Dragon Scale Chip",
        "Haunted Button",
    };
    return drops;
}

bool is_sellable_loot(const std::string& item) {
    static const std::vector<std::string> sellable = {
        "Suspicious Gold Nugget",
        "Metal Scraps of Mystery",
        "Pointy Monster Tooth",
        "Rotten Flesh",
        "Mystery Goop",
        "Strange Liquid",
        "Gnarled Toenail",
        "Moon Cheese",
        "Dragon Scale Chip",
        "Haunted Button",
    };
    return std::find(sellable.begin(), sellable.end(), item) != sellable.end();
}

std::unordered_map<std::string, bool> create_shop_stock() {
    return {
        {"Arcane Blast", true},
        {"Thunderstorm", true},
        {"Restoration Incantation", true},
        {"Frost Nova", true},
        {"Solar Beam", true},
        {"Life Bloom", true},
        {"Glorious Helmet", true},
        {"Mage Boots", true},
        {"Crystal Sword", true},
        {"Phoenix Feather", true},
        {"Dragon Scale Shield", true},
        {"Star Cloak", true},
        {"Croak Fu Primer", true},
        {"Bubble Burp Codex", true},
        {"Royal Croak Sheet Music", true},
        {"Snack Break Cookbook", true},
        {"Moon Leap Manual", true},
        {"Golden Fly Protein", true},
        {"Dragonfly Tactics", true},
        {"Clockwork Compass", true},
        {"Old Bell Manual", true},
        {"Well Whisper Notes", true},
    };
}

State new_state() {
    State state;
    state.shop_stock = create_shop_stock();
    state.next_scene = scene_order().front();
    return state;
}

std::string scene_title(const std::string& scene_id) {
    auto found = scene_titles().find(scene_id);
    if (found != scene_titles().end()) {
        return found->second;
    }
    std::string title = scene_id;
    std::replace(title.begin(), title.end(), '_', ' ');
    bool capitalize = true;
    for (char& ch : title) {
        if (capitalize) {
            ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
        }
        capitalize = ch == ' ';
    }
    return title;
}

std::string next_scene(const std::string& scene_id) {
    const auto& order = scene_order();
    auto found = std::find(order.begin(), order.end(), scene_id);
    if (found == order.end() || std::next(found) == order.end()) {
        return FINISHED_SCENE;
    }
    return *std::next(found);
}

bool has_item(const Player& player, const std::string& item) {
    return std::find(player.backpack.begin(), player.backpack.end(), item) != player.backpack.end();
}

void remove_item(Player& player, const std::string& item) {
    auto found = std::find(player.backpack.begin(), player.backpack.end(), item);
    if (found != player.backpack.end()) {
        player.backpack.erase(found);
    }
}

void add_spell(Player& player, const std::string& spell_name) {
    if (std::find(player.spells.begin(), player.spells.end(), spell_name) == player.spells.end()) {
        player.spells.push_back(spell_name);
    }
}

void add_frog_attack(Player& player, const std::string& attack_name) {
    if (std::find(player.frog_attacks.begin(), player.frog_attacks.end(), attack_name) == player.frog_attacks.end()) {
        player.frog_attacks.push_back(attack_name);
    }
}

void activate_frog_partner(Player& player) {
    player.frog_mode = true;
    player.frog_power = std::max(player.frog_power, 4);
    if (!has_item(player, "Magical Chocolate Frog")) {
        player.backpack.push_back("Magical Chocolate Frog");
    }
    if (player.frog_energy_max <= 0) {
        player.frog_energy_max = 25;
    }
    if (player.frog_energy <= 0) {
        player.frog_energy = player.frog_energy_max;
    }
    add_frog_attack(player, "Tongue Slap");
}

int count_item(const Player& player, const std::string& item) {
    return static_cast<int>(std::count(player.backpack.begin(), player.backpack.end(), item));
}

void print_stats(const Player& player) {
    divider("Player Stats");
    std::cout << "Whoop Nickels: " << money_text(player.money) << "\n";
    std::cout << "Health: " << health_text(player.health, player.health_max) << "\n";
    std::cout << "Mana: " << mana_text(player.mana, player.mana_max) << "\n";
    std::cout << "Armor: " << term::bright_cyan(std::to_string(player.armor)) << "\n";
    std::cout << "Weapon Damage: " << term::bright_yellow("+" + std::to_string(player.weapon_damage)) << "\n";
    std::cout << "Spell Damage: " << term::bright_magenta("+" + std::to_string(player.extra_damage)) << "\n";
    if (player.frog_mode) {
        std::cout << "Frog Energy: "
                  << term::bright_green(stat_meter(player.frog_energy, player.frog_energy_max) + " " +
                                        std::to_string(player.frog_energy) + "/" +
                                        std::to_string(player.frog_energy_max))
                  << "\n";
        std::cout << "Frog Power: " << term::bright_green("+" + std::to_string(player.frog_power)) << "\n";
    }

    std::cout << "Spells: ";
    if (player.spells.empty()) {
        std::cout << term::magenta("None") << "\n";
    } else {
        std::ostringstream spell_list;
        for (std::size_t i = 0; i < player.spells.size(); ++i) {
            if (i) {
                spell_list << ", ";
            }
            spell_list << player.spells[i];
        }
        std::cout << term::magenta(spell_list.str()) << "\n";
    }

    if (player.frog_mode) {
        std::cout << "Frog Attacks: ";
        if (player.frog_attacks.empty()) {
            std::cout << term::bright_green("None") << "\n";
        } else {
            std::ostringstream attack_list;
            for (std::size_t i = 0; i < player.frog_attacks.size(); ++i) {
                if (i) {
                    attack_list << ", ";
                }
                attack_list << player.frog_attacks[i];
            }
            std::cout << term::bright_green(attack_list.str()) << "\n";
        }
    }

    std::cout << "Items: ";
    if (player.backpack.empty()) {
        std::cout << term::bright_green("None") << "\n\n";
        autosave_tick();
        return;
    }

    std::map<std::string, int> counts;
    for (const std::string& item : player.backpack) {
        counts[item] += 1;
    }
    bool first = true;
    std::ostringstream item_list;
    for (const auto& [item, count] : counts) {
        if (!first) {
            item_list << ", ";
        }
        first = false;
        item_list << item;
        if (count > 1) {
            item_list << " x" << count;
        }
    }
    std::cout << term::bright_green(item_list.str()) << "\n\n";
    autosave_tick();
}

std::vector<std::string> option_inputs(const MenuOption& option) {
    std::vector<std::string> inputs = {option.key, option.label};
    inputs.insert(inputs.end(), option.aliases.begin(), option.aliases.end());
    for (std::string& input : inputs) {
        input = normalize_choice(input);
    }
    return inputs;
}

std::string choose_menu(
    const std::string& title,
    const std::vector<MenuOption>& options,
    const std::string& prompt = "Choose: ",
    const std::string& subtitle = "",
    const std::string& invalid = "\nPlease choose one of the listed options."
) {
    while (true) {
        divider(title);
        if (!subtitle.empty()) {
            std::cout << subtitle << "\n";
        }

        for (const MenuOption& option : options) {
            std::ostringstream line;
            line << option.key << ". " << option.label;
            if (!option.detail.empty()) {
                line << " - " << option.detail;
            }
            if (!option.status.empty()) {
                line << " (" << option.status << ")";
            }
            if (!option.enabled) {
                line << " [unavailable]";
            }

            if (option.enabled) {
                std::cout << term::cyan(option.key) << ". " << term::bold(option.label);
                if (!option.detail.empty()) {
                    std::cout << " - " << option.detail;
                }
                if (!option.status.empty()) {
                    std::cout << " (" << term::yellow(option.status) << ")";
                }
                std::cout << "\n";
            } else {
                std::cout << term::dim(line.str()) << "\n";
            }
        }

        autosave_tick();
        std::string choice = normalize_choice(ask(prompt));
        bool matched_disabled = false;
        for (const MenuOption& option : options) {
            std::vector<std::string> inputs = option_inputs(option);
            if (std::find(inputs.begin(), inputs.end(), choice) != inputs.end()) {
                if (option.enabled) {
                    return option.value;
                }
                matched_disabled = true;
                say("\n" + option.label + " is not available right now.");
                break;
            }
        }
        if (!matched_disabled) {
            say(invalid);
        }
    }
}

bool handle_quick_menu_request(const std::string& value) {
    if (normalize_choice(value) != "~") {
        return false;
    }
    if (active_quick_menu_player == nullptr) {
        say("\nNo stats are available right now.");
        return true;
    }
    if (quick_menu_running) {
        say("\nYou are already in the ~ menu.");
        return true;
    }

    quick_menu_running = true;
    std::string choice = choose_menu("~ Menu", {
        {"1", "Player Stats", "stats", "", {"stats", "status"}},
        {"2", "Back", "back", "", {"back", "return", "cancel"}},
    }, "~ menu choice: ", "Opened with ~.");
    if (choice == "stats") {
        print_stats(*active_quick_menu_player);
    }
    quick_menu_running = false;
    return true;
}

std::string ask_choice(
    const std::string& prompt,
    const std::unordered_map<std::string, std::vector<std::string>>& choices,
    const std::string& invalid
) {
    while (true) {
        std::string choice = normalize_choice(ask(prompt));
        for (const auto& [value, aliases] : choices) {
            for (const std::string& alias : aliases) {
                if (choice == normalize_choice(alias)) {
                    return value;
                }
            }
        }
        say(invalid);
    }
}

std::string yes_no(const std::string& prompt) {
    return ask_choice(prompt, {{"yes", {"yes", "y", "1"}}, {"no", {"no", "n", "2"}}}, "\nPlease answer yes or no.");
}

std::string fight_or_run(const std::string& prompt = "\nDo you fight or run? ") {
    return ask_choice(prompt, {{"fight", {"fight", "f", "1"}}, {"run", {"run", "r", "2"}}}, "\nPlease choose fight or run.");
}

std::string choose_left_or_right(const std::string& prompt) {
    return ask_choice(prompt, {{"left", {"left", "l", "1"}}, {"right", {"right", "r", "2"}}}, "\nPlease choose left or right.");
}

int basic_damage(const Player& player) {
    return BASIC_DAMAGE + player.weapon_damage;
}

bool try_combat_revive(Player& player) {
    if (!has_item(player, "Phoenix Feather")) {
        return false;
    }
    remove_item(player, "Phoenix Feather");
    player.health = std::max(1, player.health_max / 2);
    say("\nThe Phoenix Feather bursts into warm sparks and pulls you back to " +
        health_value_text(player.health, player.health_max) + " health!");
    return true;
}

void game_over(const Player& player) {
    say("You have been defeated!");
    std::cout << term::red("GAME OVER") << "\nYou had " << money_text(player.money) << ".\n";
    throw GameOver();
}

std::string spell_detail(const Player& player, const Spell& spell) {
    std::vector<std::string> parts;
    if (spell.has_damage) {
        int damage = spell.damage + player.extra_damage;
        parts.push_back(damage ? std::to_string(damage) + " damage" : "control");
    }
    if (spell.has_healing) {
        parts.push_back("heal " + std::to_string(spell.healing));
    }
    if (spell.burn) {
        parts.push_back("burn");
    }
    if (spell.stun) {
        parts.push_back("stun " + std::to_string(spell.stun) + " turns");
    }
    parts.push_back(std::to_string(spell.mana_cost) + " mana");

    std::ostringstream out;
    for (std::size_t i = 0; i < parts.size(); ++i) {
        if (i) {
            out << ", ";
        }
        out << parts[i];
    }
    return out.str();
}

std::string frog_attack_detail(const Player& player, const FrogAttack& attack) {
    std::vector<std::string> parts;
    if (attack.has_damage) {
        int damage = attack.damage + player.frog_power;
        parts.push_back(damage ? std::to_string(damage) + " damage" : "control");
    }
    if (attack.has_healing) {
        parts.push_back("heal " + std::to_string(attack.healing));
    }
    if (attack.burn) {
        parts.push_back("bubble burn");
    }
    if (attack.stun) {
        parts.push_back("stun " + std::to_string(attack.stun) + " turns");
    }
    parts.push_back(std::to_string(attack.energy_cost) + " frog energy");

    std::ostringstream out;
    for (std::size_t i = 0; i < parts.size(); ++i) {
        if (i) {
            out << ", ";
        }
        out << parts[i];
    }
    return out.str();
}

std::string choose_combat_action(const std::string& monster_name, int monster_health, int monster_max_health, const Player& player) {
    std::ostringstream subtitle;
    int basic_attack_damage = basic_damage(player);
    subtitle << "You: " << health_text(player.health, player.health_max)
             << " | Mana: " << mana_value_text(player.mana, player.mana_max)
             << " | " << scene_title(monster_name) << ": "
             << health_value_text(std::max(monster_health, 0), monster_max_health);

    std::vector<MenuOption> options = {
        {"1", "Basic Attack", "basic", "free, " + std::to_string(basic_attack_damage) + " damage", {"basic", "attack", "hit", "punch"}},
    };

    int next_key = 2;
    for (const std::string& spell_name : player.spells) {
        auto spell_found = spells().find(spell_name);
        if (spell_found == spells().end()) {
            continue;
        }
        const Spell& spell = spell_found->second;
        if (!spell.has_damage && !spell.has_healing) {
            continue;
        }

        bool enabled = player.mana >= spell.mana_cost;
        std::string status;
        if (!enabled) {
            status = "need " + std::to_string(spell.mana_cost - player.mana) + " mana";
        } else if (spell.has_healing && player.health >= player.health_max) {
            enabled = false;
            status = "health full";
        }

        options.push_back({
            std::to_string(next_key++),
            spell_name,
            spell_name,
            spell_detail(player, spell),
            {spell_name},
            enabled,
            status,
        });
    }

    return choose_menu("Combat", options, "Action: ", subtitle.str(), "Choose an action by number or name.");
}

std::string choose_frog_action(const std::string& monster_name, int monster_health, int monster_max_health, const Player& player) {
    std::ostringstream subtitle;
    subtitle << "You: " << health_text(player.health, player.health_max)
             << " | Frog Energy: " << term::bright_green(std::to_string(player.frog_energy) + "/" + std::to_string(player.frog_energy_max))
             << " | " << scene_title(monster_name) << ": "
             << health_value_text(std::max(monster_health, 0), monster_max_health);

    std::vector<MenuOption> options;
    int next_key = 1;
    for (const std::string& attack_name : player.frog_attacks) {
        auto attack_found = frog_attacks().find(attack_name);
        if (attack_found == frog_attacks().end()) {
            continue;
        }
        const FrogAttack& attack = attack_found->second;
        bool enabled = player.frog_energy >= attack.energy_cost;
        std::string status;
        if (!enabled) {
            status = "need " + std::to_string(attack.energy_cost - player.frog_energy) + " energy";
        } else if (attack.has_healing && player.health >= player.health_max) {
            enabled = false;
            status = "health full";
        }

        options.push_back({
            std::to_string(next_key++),
            attack_name,
            attack_name,
            frog_attack_detail(player, attack),
            {attack_name},
            enabled,
            status,
        });
    }

    return choose_menu("Frog Battle", options, "Frog command: ", subtitle.str(), "Choose a frog attack by number or name.");
}

int monster_attack(const std::string& monster_name, const Monster& monster, Player& player) {
    const std::string& attack = random_choice(monster.attacks);
    int damage = std::max(0, monster.damage - player.armor);
    say("The " + monster_name + " attacks with " + attack + "!");
    player.health -= damage;
    if (damage) {
        say("You take " + std::to_string(damage) + " damage. Health: " +
            health_value_text(player.health, player.health_max));
    } else {
        say("Your armor absorbs the hit.");
    }

    if (monster_name == "witch" && attack == "poison") {
        say("The poison slips past your armor.");
        return 3;
    }
    return 0;
}

void win_fight(const std::string& monster_name, Player& player) {
    say("The " + monster_name + " has been defeated!");
    int reward = random_int(4, 9);
    player.money += reward;
    std::string drop = random_choice(loot_drops());
    player.backpack.push_back(drop);
    if (player.frog_mode) {
        player.frog_energy = std::min(player.frog_energy_max, player.frog_energy + 4);
    }
    say("You gained " + money_text(reward) + " and found a " + term::bright_green(drop) + ".");
}

void frog_fight(const std::string& monster_name, Player& player) {
    if (player.frog_attacks.empty()) {
        add_frog_attack(player, "Tongue Slap");
    }

    const Monster& monster = monsters().at(monster_name);
    int monster_health = monster.health;
    int monster_max_health = monster.health;
    int burn_turns = 0;
    int stun_turns = 0;
    int poison_ticks = 0;

    say("\nA frog battle starts between you and the " + monster_name + "!");
    say("The " + monster_name + " has " + term::red(std::to_string(monster_health)) + " health.");
    say("It does " + term::bright_cyan(std::to_string(monster.damage)) + " damage.");

    while (monster_health > 0 && player.health > 0) {
        if (poison_ticks > 0) {
            player.health -= STATUS_DAMAGE;
            poison_ticks -= 1;
            say("The poison burns you for " + std::to_string(STATUS_DAMAGE) + " damage. Health: " +
                health_value_text(player.health, player.health_max));
            if (player.health <= 0 && !try_combat_revive(player)) {
                game_over(player);
            }
        }

        if (burn_turns > 0) {
            monster_health -= STATUS_DAMAGE;
            burn_turns -= 1;
            say("The " + monster_name + " fizzes for " + std::to_string(STATUS_DAMAGE) + " damage. Health: " +
                health_value_text(std::max(monster_health, 0), monster_max_health));
            if (monster_health <= 0) {
                win_fight(monster_name, player);
                return;
            }
        }

        std::string action = choose_frog_action(monster_name, monster_health, monster_max_health, player);
        const FrogAttack& attack = frog_attacks().at(action);
        player.frog_energy -= attack.energy_cost;
        say("You shout, \"" + action + "!\" The magical frog hops forward.");

        if (attack.has_damage) {
            int damage = attack.damage + player.frog_power;
            monster_health -= damage;
            if (damage) {
                say("The frog deals " + std::to_string(damage) + " damage.");
            }
            if (attack.burn) {
                burn_turns = std::max(burn_turns, attack.burn);
                say("The target fizzes for " + std::to_string(burn_turns) + " turns.");
            }
            if (attack.stun) {
                stun_turns = std::max(stun_turns, attack.stun);
                say("The " + monster_name + " is stunned for " + std::to_string(stun_turns) + " turns.");
            }
        } else {
            int heal_amount = std::max(0, std::min(player.health_max - player.health, attack.healing));
            player.health += heal_amount;
            say("The frog shares snacks and heals " + std::to_string(heal_amount) + " health.");
        }

        if (monster_health <= 0) {
            win_fight(monster_name, player);
            return;
        }

        if (stun_turns > 0) {
            stun_turns -= 1;
            say("The " + monster_name + " is stunned and skips its turn.");
        } else {
            poison_ticks = std::max(poison_ticks, monster_attack(monster_name, monster, player));
        }

        if (player.health <= 0 && !try_combat_revive(player)) {
            game_over(player);
        }

        say("The " + monster_name + " has " +
            health_value_text(std::max(monster_health, 0), monster_max_health) + " health remaining.");
    }
}

void spell_fight(const std::string& monster_name, Player& player) {
    if (player.frog_mode) {
        frog_fight(monster_name, player);
        return;
    }

    const Monster& monster = monsters().at(monster_name);
    int monster_health = monster.health;
    int monster_max_health = monster.health;
    int burn_turns = 0;
    int stun_turns = 0;
    int poison_ticks = 0;

    say("\nA fight starts between you and the " + monster_name + "!");
    say("The " + monster_name + " has " + term::red(std::to_string(monster_health)) + " health.");
    say("It does " + term::bright_cyan(std::to_string(monster.damage)) + " damage.");

    while (monster_health > 0 && player.health > 0) {
        if (poison_ticks > 0) {
            player.health -= STATUS_DAMAGE;
            poison_ticks -= 1;
            say("The poison burns you for " + std::to_string(STATUS_DAMAGE) + " damage. Health: " +
                health_value_text(player.health, player.health_max));
            if (player.health <= 0 && !try_combat_revive(player)) {
                game_over(player);
            }
        }

        if (burn_turns > 0) {
            monster_health -= STATUS_DAMAGE;
            burn_turns -= 1;
            say("The " + monster_name + " burns for " + std::to_string(STATUS_DAMAGE) + " damage. Health: " +
                health_value_text(std::max(monster_health, 0), monster_max_health));
            if (monster_health <= 0) {
                win_fight(monster_name, player);
                return;
            }
        }

        std::string action = choose_combat_action(monster_name, monster_health, monster_max_health, player);
        if (action == "basic") {
            int damage = basic_damage(player);
            monster_health -= damage;
            say("You strike for " + std::to_string(damage) + " damage.");
            if (player.mana < player.mana_max) {
                int recovered = std::min(3, player.mana_max - player.mana);
                player.mana += recovered;
                say("You steady your breathing and recover " + std::to_string(recovered) + " mana.");
            }
        } else {
            const Spell& spell = spells().at(action);
            player.mana -= spell.mana_cost;
            say("You cast " + action + ".");

            if (spell.has_damage) {
                int damage = spell.damage + player.extra_damage;
                monster_health -= damage;
                if (damage) {
                    say("You deal " + std::to_string(damage) + " damage.");
                }
                if (spell.burn) {
                    burn_turns = std::max(burn_turns, spell.burn);
                    say("The target burns for " + std::to_string(burn_turns) + " turns.");
                }
                if (spell.stun) {
                    stun_turns = std::max(stun_turns, spell.stun);
                    say("The " + monster_name + " is stunned for " + std::to_string(stun_turns) + " turns.");
                }
            } else {
                int heal_amount = std::max(0, std::min(player.health_max - player.health, spell.healing));
                player.health += heal_amount;
                say("You heal " + std::to_string(heal_amount) + " health.");
            }
        }

        if (monster_health <= 0) {
            win_fight(monster_name, player);
            return;
        }

        if (stun_turns > 0) {
            stun_turns -= 1;
            say("The " + monster_name + " is stunned and skips its turn.");
        } else {
            poison_ticks = std::max(poison_ticks, monster_attack(monster_name, monster, player));
        }

        if (player.health <= 0 && !try_combat_revive(player)) {
            game_over(player);
        }

        say("The " + monster_name + " has " +
            health_value_text(std::max(monster_health, 0), monster_max_health) + " health remaining.");
    }
}

bool sell_scraps(Player& player) {
    bool sold_anything = false;
    std::vector<std::string> remaining;
    for (const std::string& item : player.backpack) {
        if (is_sellable_loot(item)) {
            int worth = random_int(5, 10);
            player.money += worth;
            sold_anything = true;
            say("\nYou sold a(n) " + term::bright_green(item) + " for " + money_text(worth) + ".");
        } else {
            remaining.push_back(item);
        }
    }
    player.backpack = remaining;
    return sold_anything;
}

bool offer_potions(Player& player) {
    while (true) {
        int big_count = count_item(player, "Big Health Potion");
        int small_count = count_item(player, "Small Health Potion");

        if (player.health >= player.health_max) {
            if (big_count || small_count) {
                say("\nYour health is full, so you save your potions.");
            }
            return false;
        }

        if (!big_count && !small_count) {
            say("\nNo health potions available.");
            return false;
        }

        std::ostringstream subtitle;
        subtitle << "Health: " << health_text(player.health, player.health_max);
        std::string choice = choose_menu("Potion Menu", {
            {"1", "Drink Big Health Potion", "big", "restore to full", {"big", "big potion", "full"}, big_count > 0, big_count ? "x" + std::to_string(big_count) : "none"},
            {"2", "Drink Small Health Potion", "small", "+15 health", {"small", "small potion"}, small_count > 0, small_count ? "x" + std::to_string(small_count) : "none"},
            {"3", "Save potions", "exit", "", {"exit", "leave", "back", "no", "n", "q"}},
        }, "Potion choice: ", subtitle.str());

        if (choice == "big") {
            player.health = player.health_max;
            remove_item(player, "Big Health Potion");
            say("\nYour health is restored to " + std::to_string(player.health) + ".");
            break;
        }
        if (choice == "small") {
            player.health = std::min(player.health_max, player.health + 15);
            remove_item(player, "Small Health Potion");
            say("\nYour health is now " + std::to_string(player.health) + ".");
            break;
        }
        if (choice == "exit") {
            say("\nYou save your potions for later.");
            return false;
        }
    }

    return true;
}

std::string price_status(const Player& player, int price, bool unavailable = false, const std::string& unavailable_label = "owned") {
    if (unavailable) {
        return unavailable_label;
    }
    if (player.money < price) {
        return "need " + money_text(price - player.money) + " more";
    }
    return "";
}

void buy_spell(Player& player, std::unordered_map<std::string, bool>& stock, const std::string& spell_name, int price) {
    if (!stock[spell_name]) {
        say("\nThat spell is out of stock.");
        return;
    }
    if (player.money < price) {
        say("\nYou don't have enough Whoop Nickels.");
        return;
    }
    player.money -= price;
    add_spell(player, spell_name);
    stock[spell_name] = false;
    say("\nYou learned " + term::magenta(spell_name) + ".");
    say("You have " + money_text(player.money) + " left.");
}

void buy_item(Player& player, const std::string& item_name, int price) {
    if (player.money < price) {
        say("\nYou don't have enough Whoop Nickels.");
        return;
    }
    player.money -= price;
    player.backpack.push_back(item_name);
    say("\nYou bought a " + term::bright_green(item_name) + ".");
    say("You have " + money_text(player.money) + " left.");
}

void buy_mana_flask(Player& player) {
    constexpr int price = 60;
    if (player.money < price) {
        say("\nYou don't have enough Whoop Nickels.");
        return;
    }
    player.money -= price;
    player.mana = std::min(player.mana_max, player.mana + 35);
    say("\nYou drink a Mana Flask and recover to " + mana_value_text(player.mana, player.mana_max) + " mana.");
    say("You have " + money_text(player.money) + " left.");
}

void buy_stocked_item(Player& player, std::unordered_map<std::string, bool>& stock, const std::string& item_name, int price) {
    if (!stock[item_name]) {
        say("\nThat item is out of stock.");
        return;
    }
    if (player.money < price) {
        say("\nYou don't have enough Whoop Nickels.");
        return;
    }
    player.money -= price;
    player.backpack.push_back(item_name);
    stock[item_name] = false;
    say("\nYou bought a " + term::bright_green(item_name) + ".");
    say("You have " + money_text(player.money) + " left.");
}

void buy_equipment(Player& player, std::unordered_map<std::string, bool>& stock, const std::string& item_name, int price, const std::string& stat_name, int amount) {
    if (!stock[item_name]) {
        say("\nThat equipment is out of stock.");
        return;
    }
    if (player.money < price) {
        say("\nYou don't have enough Whoop Nickels.");
        return;
    }
    player.money -= price;
    if (stat_name == "armor") {
        player.armor += amount;
    } else if (stat_name == "extraDamage") {
        player.extra_damage += amount;
    } else if (stat_name == "weaponDamage") {
        player.weapon_damage += amount;
    }
    player.backpack.push_back(item_name);
    stock[item_name] = false;
    say("\nYou bought " + term::bright_green(item_name) + ".");
    say("You have " + money_text(player.money) + " left.");
}

void buy_mana(Player& player) {
    while (true) {
        constexpr int price_each = 4;
        std::string amount_text = normalize_choice(ask("\nMax mana to buy (" + money_text(price_each) + " each, 'all' for max, or 'back'): "));
        int amount = 0;
        if (amount_text == "back" || amount_text == "b" || amount_text == "cancel" || amount_text == "leave" || amount_text == "q") {
            say("\nYou decide not to buy mana.");
            return;
        }
        if (amount_text == "all" || amount_text == "max") {
            if (player.money <= 0) {
                say("\nYou don't have enough Whoop Nickels.");
                return;
            }
            amount = player.money / price_each;
        } else {
            try {
                std::size_t parsed = 0;
                amount = std::stoi(amount_text, &parsed);
                if (parsed != amount_text.size()) {
                    throw std::invalid_argument("bad number");
                }
            } catch (const std::exception&) {
                say("\nPlease enter a number, 'all', or 'back'.");
                continue;
            }
        }

        if (amount <= 0) {
            say("\nPlease enter a positive number.");
            continue;
        }
        int cost = amount * price_each;
        if (player.money < cost) {
            say("\nYou don't have enough Whoop Nickels.");
            return;
        }
        player.money -= cost;
        player.mana += amount;
        player.mana_max += amount;
        say("\nYou bought " + term::blue(std::to_string(amount)) + " max mana.");
        say("You have " + money_text(player.money) + " left.");
        return;
    }
}

void buy_frog_attack(Player& player, std::unordered_map<std::string, bool>& stock, const std::string& item_name, int price, const std::string& attack_name) {
    if (!stock[item_name]) {
        say("\nThat training book is out of stock.");
        return;
    }
    if (player.money < price) {
        say("\nYou don't have enough Whoop Nickels.");
        return;
    }
    player.money -= price;
    add_frog_attack(player, attack_name);
    player.backpack.push_back(item_name);
    stock[item_name] = false;
    say("\nThe frog studies " + term::bright_green(item_name) + " and learns " + term::bright_green(attack_name) + ".");
    say("You have " + money_text(player.money) + " left.");
}

void buy_frog_training(Player& player, std::unordered_map<std::string, bool>& stock, const std::string& item_name, int price, int power = 0, int energy = 0) {
    if (!stock[item_name]) {
        say("\nThat training book is out of stock.");
        return;
    }
    if (player.money < price) {
        say("\nYou don't have enough Whoop Nickels.");
        return;
    }
    player.money -= price;
    player.frog_power += power;
    player.frog_energy_max += energy;
    player.frog_energy = std::min(player.frog_energy_max, player.frog_energy + energy);
    player.backpack.push_back(item_name);
    stock[item_name] = false;
    say("\nThe frog trains with " + term::bright_green(item_name) + ".");
    if (power) {
        say("Frog Power increased by " + std::to_string(power) + ".");
    }
    if (energy) {
        say("Max Frog Energy increased by " + std::to_string(energy) + ".");
    }
    say("You have " + money_text(player.money) + " left.");
}

void buy_frog_energy(Player& player) {
    while (true) {
        constexpr int price_each = 4;
        std::string amount_text = normalize_choice(ask("\nFrog energy to buy (" + money_text(price_each) + " each, 'all' for max, or 'back'): "));
        int amount = 0;
        if (amount_text == "back" || amount_text == "b" || amount_text == "cancel" || amount_text == "leave" || amount_text == "q") {
            say("\nYou decide not to buy frog energy.");
            return;
        }
        if (amount_text == "all" || amount_text == "max") {
            if (player.money <= 0) {
                say("\nYou don't have enough Whoop Nickels.");
                return;
            }
            amount = player.money / price_each;
        } else {
            try {
                std::size_t parsed = 0;
                amount = std::stoi(amount_text, &parsed);
                if (parsed != amount_text.size()) {
                    throw std::invalid_argument("bad number");
                }
            } catch (const std::exception&) {
                say("\nPlease enter a number, 'all', or 'back'.");
                continue;
            }
        }

        if (amount <= 0) {
            say("\nPlease enter a positive number.");
            continue;
        }
        int cost = amount * price_each;
        if (player.money < cost) {
            say("\nYou don't have enough Whoop Nickels.");
            return;
        }
        player.money -= cost;
        player.frog_energy += amount;
        player.frog_energy_max += amount;
        say("\nYou bought " + term::bright_green(std::to_string(amount)) + " frog energy.");
        say("You have " + money_text(player.money) + " left.");
        return;
    }
}

void run_frog_shop(Player& player, std::unordered_map<std::string, bool>& stock, bool advanced = false, bool legendary = false) {
    while (true) {
        std::vector<MenuOption> options = {
            {"1", "Small Health Potion", "small_potion", money_text(28) + " - heals 15 health", {"small", "small potion", "health potion", "potion"}, true, price_status(player, 28)},
            {"2", "Croak Fu Primer", "croak_fu", money_text(85) + " - +3 frog power, +10 max frog energy", {"croak", "croak fu", "primer", "training"}, stock["Croak Fu Primer"], price_status(player, 85, !stock["Croak Fu Primer"], "read")},
            {"3", "Bubble Burp Codex", "bubble_burp", money_text(70) + " - " + frog_attacks().at("Bubble Burp").description, {"bubble", "bubble burp", "codex"}, stock["Bubble Burp Codex"], price_status(player, 70, !stock["Bubble Burp Codex"], "read")},
            {"4", "Add Frog Energy", "frog_energy", money_text(4) + " = +1 max frog energy", {"energy", "frog energy", "add energy"}, true, player.money ? "spend any amount" : "no money"},
        };

        if (advanced) {
            options.push_back({"5", "Big Health Potion", "big_potion", money_text(95) + " - restores full health", {"big", "big potion", "full potion"}, true, price_status(player, 95)});
            options.push_back({"6", "Royal Croak Sheet Music", "royal_croak", money_text(125) + " - " + frog_attacks().at("Royal Croak").description, {"royal", "royal croak", "sheet music"}, stock["Royal Croak Sheet Music"], price_status(player, 125, !stock["Royal Croak Sheet Music"], "read")});
            options.push_back({"7", "Snack Break Cookbook", "snack_break", money_text(110) + " - " + frog_attacks().at("Snack Break").description, {"snack", "snack break", "cookbook"}, stock["Snack Break Cookbook"], price_status(player, 110, !stock["Snack Break Cookbook"], "read")});
            options.push_back({"8", "Moon Leap Manual", "moon_leap", money_text(165) + " - " + frog_attacks().at("Moon Leap").description, {"moon", "moon leap", "manual"}, stock["Moon Leap Manual"], price_status(player, 165, !stock["Moon Leap Manual"], "read")});
            options.push_back({"9", "Golden Fly Protein", "golden_fly", money_text(180) + " - +5 frog power, +5 max frog energy", {"golden", "fly", "protein"}, stock["Golden Fly Protein"], price_status(player, 180, !stock["Golden Fly Protein"], "used")});
            if (legendary) {
                options.push_back({"10", "Dragonfly Tactics", "dragonfly_dive", money_text(240) + " - " + frog_attacks().at("Dragonfly Dive").description, {"dragonfly", "dragonfly dive", "tactics"}, stock["Dragonfly Tactics"], price_status(player, 240, !stock["Dragonfly Tactics"], "read")});
                options.push_back({"11", "Phoenix Feather", "phoenix_feather", money_text(180) + " - revives you once in combat", {"phoenix", "feather", "revive"}, stock["Phoenix Feather"], price_status(player, 180, !stock["Phoenix Feather"], "owned")});
                options.push_back({"12", "Dragon Scale Shield", "dragon_shield", money_text(220) + " - +8 armor", {"shield", "dragon shield", "dragon scale"}, stock["Dragon Scale Shield"], price_status(player, 220, !stock["Dragon Scale Shield"], "owned")});
                options.push_back({"13", "Leave store", "leave", "", {"leave", "exit", "back", "q"}});
            } else {
                options.push_back({"10", "Leave store", "leave", "", {"leave", "exit", "back", "q"}});
            }
        } else {
            options.push_back({"5", "Leave store", "leave", "", {"leave", "exit", "back", "q"}});
        }

        std::ostringstream subtitle;
        subtitle << "Whoop Nickels: " << money_text(player.money)
                 << " | Health: " << health_text(player.health, player.health_max)
                 << " | Frog Energy: " << term::bright_green(stat_meter(player.frog_energy, player.frog_energy_max) + " " + std::to_string(player.frog_energy) + "/" + std::to_string(player.frog_energy_max));
        std::string choice = choose_menu("Frog Training Shop", options, "Shop choice: ", subtitle.str());

        if (choice == "small_potion") {
            buy_item(player, "Small Health Potion", 28);
        } else if (choice == "croak_fu") {
            buy_frog_training(player, stock, "Croak Fu Primer", 85, 3, 10);
        } else if (choice == "bubble_burp") {
            buy_frog_attack(player, stock, "Bubble Burp Codex", 70, "Bubble Burp");
        } else if (choice == "frog_energy") {
            buy_frog_energy(player);
        } else if (choice == "big_potion") {
            buy_item(player, "Big Health Potion", 95);
        } else if (choice == "royal_croak") {
            buy_frog_attack(player, stock, "Royal Croak Sheet Music", 125, "Royal Croak");
        } else if (choice == "snack_break") {
            buy_frog_attack(player, stock, "Snack Break Cookbook", 110, "Snack Break");
        } else if (choice == "moon_leap") {
            buy_frog_attack(player, stock, "Moon Leap Manual", 165, "Moon Leap");
        } else if (choice == "golden_fly") {
            buy_frog_training(player, stock, "Golden Fly Protein", 180, 5, 5);
        } else if (choice == "dragonfly_dive") {
            buy_frog_attack(player, stock, "Dragonfly Tactics", 240, "Dragonfly Dive");
        } else if (choice == "phoenix_feather") {
            buy_stocked_item(player, stock, "Phoenix Feather", 180);
        } else if (choice == "dragon_shield") {
            buy_equipment(player, stock, "Dragon Scale Shield", 220, "armor", 8);
        } else if (choice == "leave") {
            say("\nYou leave the store.");
            return;
        }
    }
}

void run_shop(Player& player, std::unordered_map<std::string, bool>& stock, bool advanced = false, bool legendary = false) {
    sell_scraps(player);
    if (player.frog_mode) {
        run_frog_shop(player, stock, advanced, legendary);
        return;
    }

    while (true) {
        std::vector<MenuOption> options = {
            {"1", "Arcane Blast", "arcane", money_text(45) + " - " + spells().at("Arcane Blast").description, {"arcane", "arcane blast", "spell 1"}, stock["Arcane Blast"], price_status(player, 45, !stock["Arcane Blast"], "learned")},
            {"2", "Small Health Potion", "small_potion", money_text(28) + " - heals 15 health", {"small", "small potion", "health potion", "potion"}, true, price_status(player, 28)},
            {"3", "Thunderstorm", "thunderstorm", money_text(90) + " - " + spells().at("Thunderstorm").description, {"thunder", "thunderstorm", "spell 3"}, stock["Thunderstorm"], price_status(player, 90, !stock["Thunderstorm"], "learned")},
            {"4", "Restoration Incantation", "restoration", money_text(75) + " - " + spells().at("Restoration Incantation").description, {"restore", "restoration", "heal spell", "spell 4"}, stock["Restoration Incantation"], price_status(player, 75, !stock["Restoration Incantation"], "learned")},
            {"5", "Add Mana", "mana", money_text(4) + " = +1 max mana", {"mana", "add mana", "buy mana"}, true, player.money ? "spend any amount" : "no money"},
            {"6", "Mana Flask", "mana_flask", money_text(60) + " - recover 35 mana now", {"flask", "mana flask", "refill"}, true, price_status(player, 60)},
        };

        if (advanced) {
            options.push_back({"7", "Big Health Potion", "big_potion", money_text(95) + " - restores full health", {"big", "big potion", "full potion"}, true, price_status(player, 95)});
            options.push_back({"8", "Glorious Helmet", "helmet", money_text(140) + " - +5 armor", {"helmet", "armor"}, stock["Glorious Helmet"], price_status(player, 140, !stock["Glorious Helmet"], "owned")});
            options.push_back({"9", "Mage Boots", "boots", money_text(130) + " - +3 spell damage", {"boots", "mage boots", "damage"}, stock["Mage Boots"], price_status(player, 130, !stock["Mage Boots"], "owned")});
            options.push_back({"10", "Frost Nova", "frost_nova", money_text(120) + " - " + spells().at("Frost Nova").description, {"frost", "frost nova", "spell 9"}, stock["Frost Nova"], price_status(player, 120, !stock["Frost Nova"], "learned")});
            options.push_back({"11", "Crystal Sword", "crystal_sword", money_text(160) + " - +8 basic attack damage", {"sword", "crystal sword", "weapon"}, stock["Crystal Sword"], price_status(player, 160, !stock["Crystal Sword"], "owned")});
            options.push_back({"12", "Phoenix Feather", "phoenix_feather", money_text(180) + " - revives you once in combat", {"phoenix", "feather", "revive"}, stock["Phoenix Feather"], price_status(player, 180, !stock["Phoenix Feather"], "owned")});
            if (legendary) {
                options.push_back({"13", "Solar Beam", "solar_beam", money_text(240) + " - " + spells().at("Solar Beam").description, {"solar", "solar beam", "spell 12"}, stock["Solar Beam"], price_status(player, 240, !stock["Solar Beam"], "learned")});
                options.push_back({"14", "Life Bloom", "life_bloom", money_text(210) + " - " + spells().at("Life Bloom").description, {"life", "life bloom", "heal spell"}, stock["Life Bloom"], price_status(player, 210, !stock["Life Bloom"], "learned")});
                options.push_back({"15", "Dragon Scale Shield", "dragon_shield", money_text(220) + " - +8 armor", {"shield", "dragon shield", "dragon scale"}, stock["Dragon Scale Shield"], price_status(player, 220, !stock["Dragon Scale Shield"], "owned")});
                options.push_back({"16", "Star Cloak", "star_cloak", money_text(230) + " - +5 spell damage", {"cloak", "star cloak"}, stock["Star Cloak"], price_status(player, 230, !stock["Star Cloak"], "owned")});
                options.push_back({"17", "Leave store", "leave", "", {"leave", "exit", "back", "q"}});
            } else {
                options.push_back({"13", "Leave store", "leave", "", {"leave", "exit", "back", "q"}});
            }
        } else {
            options.push_back({"7", "Leave store", "leave", "", {"leave", "exit", "back", "q"}});
        }

        std::ostringstream subtitle;
        subtitle << "Whoop Nickels: " << money_text(player.money)
                 << " | Health: " << health_text(player.health, player.health_max)
                 << " | Mana: " << mana_text(player.mana, player.mana_max);
        std::string choice = choose_menu("Shop Menu", options, "Shop choice: ", subtitle.str());

        if (choice == "arcane") {
            buy_spell(player, stock, "Arcane Blast", 45);
        } else if (choice == "small_potion") {
            buy_item(player, "Small Health Potion", 28);
        } else if (choice == "thunderstorm") {
            buy_spell(player, stock, "Thunderstorm", 90);
        } else if (choice == "restoration") {
            buy_spell(player, stock, "Restoration Incantation", 75);
        } else if (choice == "mana") {
            buy_mana(player);
        } else if (choice == "mana_flask") {
            buy_mana_flask(player);
        } else if (choice == "big_potion") {
            buy_item(player, "Big Health Potion", 95);
        } else if (choice == "helmet") {
            buy_equipment(player, stock, "Glorious Helmet", 140, "armor", 5);
        } else if (choice == "boots") {
            buy_equipment(player, stock, "Mage Boots", 130, "extraDamage", 3);
        } else if (choice == "frost_nova") {
            buy_spell(player, stock, "Frost Nova", 120);
        } else if (choice == "crystal_sword") {
            buy_equipment(player, stock, "Crystal Sword", 160, "weaponDamage", 8);
        } else if (choice == "phoenix_feather") {
            buy_stocked_item(player, stock, "Phoenix Feather", 180);
        } else if (choice == "solar_beam") {
            buy_spell(player, stock, "Solar Beam", 240);
        } else if (choice == "life_bloom") {
            buy_spell(player, stock, "Life Bloom", 210);
        } else if (choice == "dragon_shield") {
            buy_equipment(player, stock, "Dragon Scale Shield", 220, "armor", 8);
        } else if (choice == "star_cloak") {
            buy_equipment(player, stock, "Star Cloak", 230, "extraDamage", 5);
        } else if (choice == "leave") {
            say("\nYou leave the store.");
            return;
        }
    }
}

void write_vector(std::ofstream& out, const std::vector<std::string>& values) {
    out << values.size() << "\n";
    for (const std::string& value : values) {
        out << value << "\n";
    }
}

std::vector<std::string> read_vector(std::ifstream& in) {
    std::string line;
    std::getline(in, line);
    int count = std::stoi(line);
    std::vector<std::string> values;
    for (int i = 0; i < count; ++i) {
        std::getline(in, line);
        values.push_back(line);
    }
    return values;
}

void normalize_player(Player& player) {
    player.name = trim(player.name).empty() ? "Adventurer" : trim(player.name);
    if (!has_item(player, "Magic Wand") && has_item(player, "Magical Chocolate Frog")) {
        activate_frog_partner(player);
    }
    if (player.frog_mode) {
        if (player.frog_energy_max <= 0) {
            player.frog_energy_max = 25;
        }
        if (player.frog_energy <= 0) {
            player.frog_energy = player.frog_energy_max;
        }
        player.frog_power = std::max(player.frog_power, 4);
        if (player.frog_attacks.empty()) {
            add_frog_attack(player, "Tongue Slap");
        }
    } else {
        player.frog_energy = std::max(0, player.frog_energy);
        player.frog_energy_max = std::max(0, player.frog_energy_max);
    }
    player.road_progress = std::clamp(
        player.road_progress,
        0,
        static_cast<int>(long_road_enemies().size())
    );
}

void save_state(const State& state, const std::string& path = SAVE_PATH) {
    fs::create_directories(fs::path(path).parent_path());
    std::ofstream out(path);
    if (!out) {
        throw std::runtime_error("Could not write save file.");
    }
    const Player& p = state.player;
    out << "AdventureGameCppSaveV4\n";
    out << state.next_scene << "\n";
    out << p.name << "\n";
    out << p.money << "\n" << p.health << "\n" << p.health_max << "\n" << p.mana << "\n"
        << p.mana_max << "\n" << p.armor << "\n" << p.weapon_damage << "\n" << p.extra_damage << "\n";
    out << (p.frog_mode ? 1 : 0) << "\n" << p.frog_power << "\n" << p.frog_energy << "\n" << p.frog_energy_max << "\n";
    out << p.road_progress << "\n";
    write_vector(out, p.backpack);
    write_vector(out, p.spells);
    write_vector(out, p.frog_attacks);
    out << state.shop_stock.size() << "\n";
    for (const auto& [item, stocked] : state.shop_stock) {
        out << item << "\n" << (stocked ? 1 : 0) << "\n";
    }
}

State load_state(const std::string& path = SAVE_PATH) {
    std::ifstream in(path);
    if (!in) {
        throw std::runtime_error("No C++ autosave found.");
    }
    std::string line;
    std::getline(in, line);
    bool version_2 = line == "AdventureGameCppSaveV2";
    bool version_3 = line == "AdventureGameCppSaveV3";
    bool version_4 = line == "AdventureGameCppSaveV4";
    bool version_3_or_newer = version_3 || version_4;
    if (line != "AdventureGameCppSaveV1" && !version_2 && !version_3_or_newer) {
        throw std::runtime_error("Save file is not a C++ port save.");
    }

    State state;
    state.shop_stock = create_shop_stock();
    std::getline(in, state.next_scene);
    Player& p = state.player;
    if (version_3_or_newer) {
        std::getline(in, p.name);
    }
    std::getline(in, line); p.money = std::stoi(line);
    std::getline(in, line); p.health = std::stoi(line);
    std::getline(in, line); p.health_max = std::stoi(line);
    std::getline(in, line); p.mana = std::stoi(line);
    std::getline(in, line); p.mana_max = std::stoi(line);
    std::getline(in, line); p.armor = std::stoi(line);
    if (version_2 || version_3_or_newer) {
        std::getline(in, line); p.weapon_damage = std::stoi(line);
    }
    std::getline(in, line); p.extra_damage = std::stoi(line);
    if (version_3_or_newer) {
        std::getline(in, line); p.frog_mode = std::stoi(line) != 0;
        std::getline(in, line); p.frog_power = std::stoi(line);
        std::getline(in, line); p.frog_energy = std::stoi(line);
        std::getline(in, line); p.frog_energy_max = std::stoi(line);
    }
    if (version_4) {
        std::getline(in, line); p.road_progress = std::stoi(line);
    }
    p.backpack = read_vector(in);
    p.spells = read_vector(in);
    if (version_3_or_newer) {
        p.frog_attacks = read_vector(in);
    }

    std::getline(in, line);
    int stock_count = std::stoi(line);
    for (int i = 0; i < stock_count; ++i) {
        std::string item;
        std::string stocked;
        std::getline(in, item);
        std::getline(in, stocked);
        state.shop_stock[item] = stocked == "1";
    }
    normalize_player(state.player);
    return state;
}

bool autosave_state(const State& state) {
    try {
        save_state(state);
    } catch (const std::exception&) {
        return false;
    }
    return true;
}

void autosave_tick() {
    if (!active_autosave_state || autosave_running) {
        return;
    }
    autosave_running = true;
    try {
        save_state(*active_autosave_state);
    } catch (const std::exception&) {
    }
    autosave_running = false;
}

State load_state_interactive() {
    while (true) {
        std::string choice = choose_menu("Load Game", {
            {"1", "Load C++ Autosave", "autosave", SAVE_PATH, {"load", "autosave", "continue"}},
            {"2", "Back", "back", "", {"back", "cancel"}},
            {"3", EXIT_LABEL, "exit", "", {"exit", "quit", "q"}},
        }, "Load choice: ", "C++ port saves are stored separately from Python/web saves.");

        if (choice == "back") {
            throw std::runtime_error("back");
        }
        if (choice == "exit") {
            exit_game();
        }
        try {
            State state = load_state();
            say("\nLoaded C++ autosave.");
            return state;
        } catch (const std::exception& exc) {
            say(std::string("\nLoad failed: ") + exc.what());
        }
    }
}

void extra_fight(Player& player, const std::string& monster_name, const std::string& intro, const std::string& run_text) {
    say("\n" + intro);
    if (fight_or_run() == "run") {
        say("\n" + run_text);
        game_over(player);
    }
    spell_fight(monster_name, player);
    offer_potions(player);
}

void intro_scene(Player& player) {
    player.name = ask("\nWhat is your adventurer name? ");
    if (trim(player.name).empty()) {
        player.name = "Adventurer";
    }
    say("\nYou are out on a casual stroll when a magical chocolate frog hops around your feet.");
    std::string choice = yes_no("\nDo you pick it up? (yes/no): ");
    if (choice == "yes") {
        say("\nYou pick up the frog and store it in your backpack.");
    } else {
        say("\nYou start to walk away. RIBBIT.");
        say("The frog hops into your backpack anyway.");
    }
    player.backpack.push_back("Magical Chocolate Frog");
}

void wizard_scene(Player& player) {
    say("\nYou bump into an old man with a long white beard.");
    say("\"Was that the croak of a chocolate frog?\" he asks.");
    if (yes_no("\nWhat do you say? (yes/no): ") == "no") {
        say("\nHis old hearing must be failing him. He wanders off.");
        activate_frog_partner(player);
        say("The frog gives you a tiny nod. It looks ready to fight for itself.");
        return;
    }

    say("\nHe smiles. \"I am Rumblerod The Great, the only remaining wizard in the North.\"");
    if (yes_no("\nTrade the frog for his spare magic wand? (yes/no): ") == "no") {
        say("\nRumblerod shrugs and continues down the path.");
        activate_frog_partner(player);
        say("The frog hops onto your shoulder and learns Tongue Slap out of spite.");
        return;
    }

    remove_item(player, "Magical Chocolate Frog");
    player.backpack.push_back("Magic Wand");
    add_spell(player, "Lockio Reducto");
    say("\nYou receive a Magic Wand.");
    say("Rumblerod says, \"Lockio Reducto can unlock any door.\"");
}

void locked_door_scene(Player& player) {
    say("\nYou continue your journey and come to a fork in the path.");
    if (choose_left_or_right("\nDo you go left or right? ") == "right") {
        say("\nYou notice a locked door on the left and decide not to miss it.");
    }

    int amount = random_int(20, 30);
    std::string choice = player.frog_mode
        ? yes_no("\nYou find a locked door. Send the frog through the keyhole? (yes/no): ")
        : yes_no("\nYou find a locked door. Use the wand and say the words? (yes/no): ");
    if (choice == "no") {
        say("\nA goblin sneaks up behind you and stabs you.");
        game_over(player);
    }

    player.money += amount;
    if (player.frog_mode) {
        say("\nThe frog squeezes under the door, unlocks it, and looks smug. You find " + money_text(amount) + ".");
    } else {
        say("\nYou say Lockio Reducto. The door opens and you find " + money_text(amount) + ".");
    }
    extra_fight(
        player,
        "gate rat",
        "The noise wakes a gate rat with opinions about trespassing.",
        "The gate rat follows your shoelaces and wins."
    );
}

void first_goblin_scene(Player& player) {
    say("\nYou turn to exit, but a goblin blocks your path.");
    if (fight_or_run() == "run") {
        say("\nThe goblin is faster than you.");
        game_over(player);
    }

    std::string attack = choose_menu("Quick Fight", {
        {"1", "Uppercut", "uppercut", "", {"uppercut", "punch"}},
        {"2", "Kick", "kick", "", {"kick"}},
        {"3", "Dirt Throw", "dirt", "", {"dirt", "throw dirt"}},
    }, "Move: ");

    if (attack == "dirt") {
        say("\nThe dirt blinds the goblin long enough for you to knock it out.");
    } else {
        say("\nYour " + attack + " knocks out the goblin.");
    }
    if (player.frog_mode) {
        add_frog_attack(player, "Bubble Burp");
        say("It drops a page from a frog-training book.");
        say("The frog eats half the page and learns Bubble Burp.");
    } else {
        add_spell(player, "Fireball");
        say("It drops a page from a spell book.");
        say("You learned Fireball.");
    }
}

void village_scene(Player& player, std::unordered_map<std::string, bool>& shop_stock) {
    say("\nYou see a village nearby.");
    say("A troll is attacking the villagers.");
    if (fight_or_run() == "run") {
        say("\nThe troll catches you before you can escape.");
        game_over(player);
    }
    spell_fight("troll", player);
    extra_fight(
        player,
        "smoke imp",
        "A smoke imp crawls out of the village chimney and starts throwing sparks.",
        "You run through the smoke and smack directly into a fence."
    );

    say("\nA villager says, \"Thank you for saving our village.\"");
    say("\"Take this Big Health Potion. It will restore your health.\"");
    player.backpack.push_back("Big Health Potion");
    offer_potions(player);

    if (yes_no("\nYou see Gnome Depot, Harold Sellsalot's shop. Go inside? (yes/no): ") == "no") {
        say("\nA skeleton archer outside the village shoots you.");
        game_over(player);
    }

    say("\nHarold welcomes you into Gnome Depot.");
    run_shop(player, shop_stock);

    say("\nYou leave the store and encounter a skeleton.");
    if (fight_or_run() == "run") {
        say("\nThe skeleton catches you near the village gate.");
        game_over(player);
    }
    spell_fight("skeleton", player);
    offer_potions(player);
    extra_fight(
        player,
        "curse candle",
        "The village shrine candle grows teeth and blocks the road.",
        "The candle waddles after you. Slowly. Somehow still fast enough."
    );
    std::string whisper = normalize_choice(ask("\nBefore you leave, the cobblestones seem to whisper. Type what you heard or press Enter: "));
    if (whisper == "listen") {
        say("\nA loose brick slides aside and reveals a narrow ladder.");
        clocktower_scene(player, shop_stock);
    } else if (whisper == "well") {
        well_scene(player);
    }
}

void forest_scene(Player& player, std::unordered_map<std::string, bool>& shop_stock) {
    say("\nYou follow a forest trail.");
    say("A werewolf howls at you from the trees.");
    if (fight_or_run() == "run") {
        say("\nThe werewolf catches you in the brush.");
        game_over(player);
    }
    spell_fight("werewolf", player);
    offer_potions(player);
    extra_fight(
        player,
        "bramble wolf",
        "The bushes shake, then become a second wolf made mostly of thorns.",
        "You sprint into the brambles and immediately regret the shortcut."
    );

    say("\nFarther down the trail, a goblin jumps into the path.");
    if (fight_or_run() == "run") {
        say("\nThe goblin is faster than you.");
        game_over(player);
    }
    spell_fight("goblin", player);
    offer_potions(player);
    extra_fight(
        player,
        "treasure mimic",
        "A treasure chest sits in the road. It smiles before you can.",
        "The chest runs faster than a chest should legally run."
    );

    say("\nAt the forest edge, Miss Costalot waves you over to her traveling cart.");
    run_shop(player, shop_stock, true);
    if (normalize_choice(ask("\nA mossy sign points off the road. Type 'detour' to ignore it, or press Enter: ")) == "detour") {
        say("\nYou push through nettles and find a forgotten well.");
        well_scene(player);
    }
}

void twin_doors_scene(Player& player) {
    say("\nYou find two locked doors at the end of the road.");
    std::string door = player.frog_mode
        ? choose_left_or_right("\nDo you send the frog to the left or the right door? ")
        : choose_left_or_right("\nDo you use the wand on the left or the right door? ");
    if (player.frog_mode) {
        say("\nThe frog shoulder-checks the lock until the door gives up.");
    } else {
        say("\nYou say Lockio Reducto and the door opens.");
    }

    if (door == "left") {
        say("\nThe left door leads to a dead end guarded by an ogre.");
        if (fight_or_run() == "fight") {
            spell_fight("ogre", player);
            offer_potions(player);
            say("\nAfter defeating the ogre, you realize this path leads nowhere.");
        } else {
            say("\nYou escape back to the corridor.");
        }
        say("The right door is now your only option.");
    }

    say("\nYou go through the right door and find a chest.");
    say("Before you can open it, an ogre attacks.");
    if (fight_or_run() == "run") {
        say("\nYou slide between the ogre's legs and escape.");
        return;
    }

    spell_fight("ogre", player);
    int amount = random_int(15, 25);
    player.money += amount;
    say("\nYou find " + money_text(amount) + " in the chest.");
    offer_potions(player);
}

void witch_scene(Player& player) {
    say("\nYou continue down the corridor.");
    if (fight_or_run("\nYou see a witch. Do you fight or run? ") == "run") {
        say("\nYou run into the ogre's dad, who is very angry with you.");
        game_over(player);
    }
    spell_fight("witch", player);
    offer_potions(player);
    extra_fight(
        player,
        "curse candle",
        "The witch's last candle hops down from a shelf and tries to finish the curse.",
        "The candle stamps out your escape plan with tiny wax feet."
    );
}

void mountain_pass_scene(Player& player) {
    say("\nPast the witch's corridor, the road climbs into a mountain pass.");
    say("A sign reads: FINAL CASTLE THIS WAY. Under it, someone wrote: probably.");
    if (fight_or_run("\nAn ice goblin rolls down the hill at you. Do you fight or run? ") == "run") {
        say("\nYou try to run downhill, which works until the hill runs out.");
        game_over(player);
    }

    spell_fight("ice goblin", player);
    extra_fight(
        player,
        "snow bat",
        "A snow bat drops from the pass marker and shakes frost from its wings.",
        "You run downhill; the snow bat takes the express route."
    );
    int reward = random_int(35, 50);
    player.money += reward;
    player.backpack.push_back("Moon Cheese");
    say("\nThe ice goblin's lunchbox pops open. You find " + money_text(reward) + " and some Moon Cheese.");
    offer_potions(player);
}

void moonlit_market_scene(Player& player, std::unordered_map<std::string, bool>& shop_stock) {
    say("\nAt the top of the pass, paper lanterns glow over the Moonlit Market.");
    say("A merchant named Madam Probably says, \"Everything here is almost safe.\"");
    run_shop(player, shop_stock, true);

    say("\nBehind the last stall, a shadow knight blocks the castle road.");
    if (fight_or_run() == "run") {
        say("\nThe knight sighs, walks faster than you, and bonks you with the flat of a gloomy sword.");
        game_over(player);
    }
    spell_fight("shadow knight", player);
    extra_fight(
        player,
        "receipt wraith",
        "The knight's dropped receipt unfolds into a very angry wraith.",
        "The receipt wraith charges a late fee on your escape."
    );
    player.money += 30;
    say("\nThe shadow knight drops " + money_text(30) + " and a note that says: please stop Lord Dreadbiscuit.");
    offer_potions(player);
    if (normalize_choice(ask("\nA vendor drops a receipt. Type the first word printed in tiny ink, or press Enter: ")) == "clock") {
        say("\nThe receipt opens a seam in the market wall.");
        clocktower_scene(player, shop_stock);
    }
}

void vampire_castle_scene(Player& player) {
    say("\nYou reach a castle shaped like a fancy tooth.");
    say("Inside, a vampire is practicing scary faces in a mirror that refuses to help.");
    if (fight_or_run("\nThe vampire notices you. Do you fight or run? ") == "run") {
        say("\nYou run into a closet full of capes. The capes win.");
        game_over(player);
    }

    spell_fight("vampire", player);
    extra_fight(
        player,
        "basement bat",
        "The castle basement answers the noise with an even smaller, meaner bat.",
        "You trip over a cape rack. The bat accepts the assist."
    );
    player.backpack.push_back("Silver Key of Mild Concern");
    player.money += 40;
    say("\nThe vampire turns into a bat and drops the Silver Key of Mild Concern plus " + money_text(40) + ".");
    say("The key is real, but the real castle keeps moving farther away.");
    offer_potions(player);
}

void false_throne_scene(Player& player, std::unordered_map<std::string, bool>& shop_stock) {
    say("\nThe Silver Key opens a hall with a throne made of polished cookies.");
    say("A herald in a paper crown announces that the final castle is 'just ahead' again.");
    if (fight_or_run("\nA mirrored knight steps out of the throne room. Fight or run? ") == "run") {
        say("\nYou run, but the hallway keeps becoming longer behind you.");
        game_over(player);
    }

    spell_fight("shadow knight", player);
    extra_fight(
        player,
        "sugar golem",
        "The cookie throne melts into a sugar golem with fists like bakery bricks.",
        "The hallway becomes syrup under your boots."
    );
    int reward = random_int(20, 35);
    player.money += reward;
    say("\nBehind the false throne, you find " + money_text(reward) + " and a stairway that goes down.");
    offer_potions(player);
    run_shop(player, shop_stock, true);
}

void clocktower_scene(Player& player, std::unordered_map<std::string, bool>& shop_stock) {
    say("\nA narrow stair climbs into a clocktower nobody mentioned.");
    say("Each floor is quieter than the last, as if the tower is trying not to be found.");
    if (fight_or_run("\nA brass sentinel blocks the gears. Fight or run? ") == "run") {
        say("\nYou run, but the tower ticks its way into your path again.");
        game_over(player);
    }
    spell_fight("shadow knight", player);
    extra_fight(
        player,
        "rust rat",
        "A gear hatch opens and another rust rat skitters across the clock face.",
        "The tower ticks your escape route closed."
    );
    player.money += 20;
    player.backpack.push_back("Clockwork Cog");
    say("\nThe sentinel drops a Clockwork Cog and the tower keeps turning anyway.");
    offer_potions(player);
    run_shop(player, shop_stock, true);
}

void well_scene(Player& player) {
    say("\nYou find an old well behind a fence that should not be easy to notice.");
    say("Something from below taps back twice, waits, then once more.");
    if (yes_no("\nLean over and listen again? (yes/no): ") == "no") {
        say("\nThe well stays quiet, which is somehow worse.");
        return;
    }
    player.backpack.push_back("Well Water");
    player.money += 7;
    say("\nA bucket rises with " + money_text(7) + " and a bottle of cold well water.");
}

void underkeep_scene(Player& player) {
    say("\nThe stairway leads under the castle into a damp underkeep.");
    say("A sleepy archivist says the princess is not here, then stamps your map with 'TRY AGAIN'.");
    if (fight_or_run("\nA chained ogre blocks the only tunnel. Fight or run? ") == "run") {
        say("\nYou run into a wall of old bricks and lose the argument.");
        game_over(player);
    }

    spell_fight("ogre", player);
    extra_fight(
        player,
        "rust rat",
        "A rust rat drops from the pipes and starts chewing the map.",
        "You run into a pipe maze and the rust rat knows every pipe."
    );
    player.backpack.push_back("Ancient Map Fragment");
    player.money += 25;
    say("\nThe ogre drops an Ancient Map Fragment and a small pouch of Whoop Nickels.");
    say("The fragment points deeper underground, because of course it does.");
    offer_potions(player);
    if (normalize_choice(ask("\nThe tunnel breathes once. Type 'deeper' to keep going, or press Enter: ")) == "deeper") {
        say("\nYou slip into a maintenance passage that should not exist.");
        well_scene(player);
    }
}

void hundred_day_road_scene(Player& player, std::unordered_map<std::string, bool>& shop_stock) {
    static const std::vector<std::string> chapter_names = {
        "Ash Month",
        "Lantern Month",
        "Mirror Month",
        "Storm Month",
        "Crownless Month",
    };

    const auto& enemies = long_road_enemies();
    int road_progress = std::clamp(player.road_progress, 0, static_cast<int>(enemies.size()));
    if (road_progress >= static_cast<int>(enemies.size())) {
        say("\nRoad checkpoint loaded: all 50 battles complete.");
    } else if (road_progress > 0) {
        say("\nRoad checkpoint loaded: " + std::to_string(road_progress) + "/50 battles complete.");
        say("The road unfolds again at milepost " + std::to_string(road_progress + 1) + ".");
    } else {
        say("\nThe Ancient Map Fragment unfolds into a road that is much longer than the paper should allow.");
        say("Mileposts rise out of the dirt one after another, each carved with a different warning.");
        say("Rumblerod squints at the first marker and says, 'This is the Hundred-Day Road. Bring snacks.'");
        say("The Dragon Gate waits at the far end, but the road refuses to be skipped.");
        run_shop(player, shop_stock, true, true);
    }

    for (std::size_t offset = static_cast<std::size_t>(road_progress); offset < enemies.size(); ++offset) {
        int index = static_cast<int>(offset) + 1;
        const std::string& enemy = enemies[offset];

        if (offset % 10 == 0) {
            say("\n=== " + chapter_names[offset / 10] + " ===");
            say("The milepost reads " + std::to_string(index) + "/50. The road insists another month has begun.");
            if (index > 1) {
                offer_potions(player);
                run_shop(player, shop_stock, true, true);
            }
        }

        if (fight_or_run("\nEnemy " + std::to_string(index) + "/50: A " + scene_title(enemy) + " blocks the road. Fight or run? ") == "run") {
            say("\nYou turn back. The road folds behind you like a map in a bad mood.");
            game_over(player);
        }

        spell_fight(enemy, player);
        player.road_progress = index;
        if (index % 5 == 0) {
            say("\nRoad checkpoint saved: " + std::to_string(index) + "/50 battles complete.");
        } else {
            say("\nRoad progress saved: " + std::to_string(index) + "/50.");
        }

        if (index % 5 == 0) {
            int health_gain = std::min(30, player.health_max - player.health);
            int mana_gain = std::min(20, player.mana_max - player.mana);
            player.health += health_gain;
            player.mana += mana_gain;
            say("\nA roadside shrine gives you just enough rest to keep going. Health +" +
                std::to_string(health_gain) + ", mana +" + std::to_string(mana_gain) + ".");
            offer_potions(player);
        }
    }

    if (!has_item(player, "Hundred-Day Road Seal")) {
        player.backpack.push_back("Hundred-Day Road Seal");
        player.money += 150;
        say("\nThe fiftieth milepost cracks open and reveals the Hundred-Day Road Seal.");
        say("You also pry " + money_text(150) + " from a stone donation box labeled 'hero maintenance'.");
    } else {
        say("\nYour Hundred-Day Road Seal still glows. This road has already been conquered.");
    }
    say("Behind you, the road is full of footprints. Ahead, the Dragon Gate finally stops pretending to be close.");
    run_shop(player, shop_stock, true, true);
}

void dragon_gate_scene(Player& player, std::unordered_map<std::string, bool>& shop_stock) {
    say("\nThe Silver Key fits a gate made of old dragon scales.");
    say("Next to it, two blacksmiths argue over whether anvils count as musical instruments.");
    say("They call their shop The Dragon Forge and offer one last chance to gear up.");
    run_shop(player, shop_stock, true, true);

    extra_fight(
        player,
        "glass cobra",
        "A glass cobra uncoils from the gate hinges and reflects your worst angle.",
        "The cobra turns the gate into a mirror maze."
    );
    say("\nWhen you unlock the gate, a crystal dragon wakes up and sneezes rainbows everywhere.");
    if (fight_or_run("\nDo you fight the crystal dragon or run? ") == "run") {
        say("\nYou run. The dragon thinks this is fetch.");
        game_over(player);
    }

    spell_fight("crystal dragon", player);
    extra_fight(
        player,
        "crown wraith",
        "The dragon's roar shakes a crown-shaped wraith out of the ceiling.",
        "The wraith declares your retreat illegal."
    );
    player.backpack.push_back("Dragon Scale Chip");
    player.money += 60;
    say("\nThe dragon bows, gives you a Dragon Scale Chip, and pushes " + money_text(60) + " into your hands.");
    say("You are sure this must be the last thing. It is not the last thing.");
    offer_potions(player);
}

void final_battle_scene(Player& player) {
    say("\nBeyond the gate stands Lord Dreadbiscuit, wearing a crown far too small for his ego.");
    say("\"At last,\" he says, \"someone has come to challenge my mildly inconvenient darkness.\"");
    say("Then the crown cracks like thunder and the whole castle tilts toward the sky.");
    say("A dragon larger than the tower unfolds from the storm clouds, each scale glowing like a sealed doorway.");
    say("Lord Dreadbiscuit points up and whispers, \"Technically, I was only renting the throne.\"");

    if (has_item(player, "Dragon Scale Chip")) {
        player.health = std::min(player.health_max, player.health + 40);
        player.mana = std::min(player.mana_max, player.mana + 35);
        say("\nThe Dragon Scale Chip burns white-hot and shields you in old realmfire. Health: " +
            std::to_string(player.health) + "/" + std::to_string(player.health_max) +
            " Mana: " + std::to_string(player.mana) + "/" + std::to_string(player.mana_max) + ".");
    }

    say("\nThe Realmbound Dragon lands on the ruined throne and blocks out every star.");
    if (fight_or_run("\nDo you fight the Realmbound Dragon or run? ") == "run") {
        say("\nYou run. The dragon inhales once, and the road behind you becomes a memory.");
        game_over(player);
    }

    spell_fight("realmbound dragon", player);
    say("\nThe Realmbound Dragon crashes across the throne mountain and folds its wings around the broken castle.");
    say("Its final roar turns into sunrise. Every locked road in the realm opens at once.");
    say("Lord Dreadbiscuit crawls from under a biscuit-shaped shield and immediately retires from evil.");
    say("Rumblerod appears from behind a curtain and insists he was helping invisibly the whole time.");
}

bool postgame_add_once(Player& player, const std::string& item) {
    if (has_item(player, item)) {
        return false;
    }
    player.backpack.push_back(item);
    return true;
}

bool postgame_spend(Player& player, int amount) {
    if (player.money < amount) {
        say("\nYou need " + money_text(amount - player.money) + " more.");
        return false;
    }
    player.money -= amount;
    return true;
}

void postgame_status(const Player& player) {
    static const std::vector<std::string> milestones = {
        "Postgame House",
        "Second Floor",
        "Family Hearth",
        "Garden Patch",
        "Hero Shop Ledger",
        "Town Charter",
        "Fishing Rod",
        "River Boat",
        "Apprentice Badge",
        "Festival Banner",
        "Hero Statue",
    };
    std::vector<std::string> unlocked;
    for (const std::string& item : milestones) {
        if (has_item(player, item)) {
            unlocked.push_back(item);
        }
    }
    say("\nWhoop Nickels: " + money_text(player.money));
    if (unlocked.empty()) {
        say("Settlement: nothing built yet");
    } else {
        std::ostringstream out;
        for (std::size_t i = 0; i < unlocked.size(); ++i) {
            if (i > 0) {
                out << ", ";
            }
            out << unlocked[i];
        }
        say("Settlement: " + out.str());
    }
}

void postgame_menu(Player& player) {
    while (true) {
        std::string choice = choose_menu("Postgame", {
            {"1", "Build or Upgrade Home", "house", "", {"house", "build", "upgrade"}},
            {"2", "Family and Home", "family", "", {"family", "home"}},
            {"3", "Garden and Craft", "garden", "", {"garden", "farm", "craft"}},
            {"4", "Run Your Shop", "shop", "", {"shop", "store"}},
            {"5", "Rebuild the Realm", "town", "", {"town", "help", "realm"}},
            {"6", "Jobs Board", "quest", "", {"quest", "job", "jobs"}},
            {"7", "Hold a Festival", "festival", "", {"festival", "party"}},
            {"8", "Fish and Sail", "river", "", {"fish", "river", "sail"}},
            {"9", "Train an Apprentice", "apprentice", "", {"train", "apprentice"}},
            {"10", "Settlement Status", "status", "", {"status", "settlement"}},
            {"11", EXIT_LABEL, "exit", "", {"exit", "quit", "q"}},
        }, "Postgame choice: ", "The realm is safe enough to live in now.");

        if (choice == "house") {
            if (!has_item(player, "Postgame House")) {
                if (postgame_spend(player, 25)) {
                    postgame_add_once(player, "Postgame House");
                    say("\nYou buy land near the road and build a small house with a sturdy roof.");
                    say("You hang a lantern by the door and finally have a place to come back to.");
                }
            } else if (!has_item(player, "Second Floor")) {
                if (postgame_spend(player, 60)) {
                    postgame_add_once(player, "Second Floor");
                    say("\nYou add a second floor, a guest room, and a balcony facing the hills.");
                }
            } else {
                say("\nYou patch the roof, oil the hinges, and make the house a little nicer.");
            }
        } else if (choice == "family") {
            if (!has_item(player, "Postgame House")) {
                say("\nYou should build a home first.");
            } else if (postgame_add_once(player, "Family Hearth")) {
                say("\nYou meet someone kind, and over time you start a family in the quiet part of the valley.");
                say("The house gets louder, warmer, and a lot more lived in.");
            } else {
                say("\nYou spend the day at home cooking, telling stories, and fixing a mysteriously broken chair.");
            }
        } else if (choice == "garden") {
            postgame_add_once(player, "Garden Patch");
            player.backpack.push_back("Potion Herbs");
            say("\nYou tend the garden and harvest Potion Herbs.");
            say("The frog supervises the garden like it owns the property.");
        } else if (choice == "shop") {
            if (postgame_add_once(player, "Hero Shop Ledger")) {
                say("\nYou open a tiny shop and sell repair kits, jam, and honest advice.");
            }
            int earnings = random_int(8, 22);
            player.money += earnings;
            say("Travelers buy supplies and leave " + money_text(earnings) + " on the counter.");
        } else if (choice == "town") {
            if (postgame_add_once(player, "Town Charter")) {
                say("\nYou help repair roads, roofs, and the old bridge over the river.");
                say("The village starts looking like a place people can grow old in.");
            } else if (postgame_add_once(player, "Hero Statue")) {
                say("\nThe town builds a small statue of you. It looks almost, but not quite, like you.");
            } else {
                say("\nYou spend the afternoon settling disputes, moving lumber, and signing very official papers.");
            }
        } else if (choice == "quest") {
            int reward = random_int(10, 30);
            player.money += reward;
            static const std::vector<std::string> outcomes = {
                "A farmer hires you to find three missing sheep. You return with four, because one tagged along.",
                "The blacksmith asks for rare ore. You spend the afternoon in the hills and come back with a strange blue stone.",
                "A child asks for a hero story. You make one up, then realize it is almost true.",
                "A courier needs help crossing the old road. You escort them past three suspicious puddles.",
            };
            say("\n" + outcomes[random_int(0, static_cast<int>(outcomes.size()) - 1)]);
            say("You earn " + money_text(reward) + ".");
        } else if (choice == "festival") {
            postgame_add_once(player, "Festival Banner");
            say("\nYou help organize a town festival with lanterns, music, and too many pies.");
            say("By nightfall the whole valley feels warmer.");
        } else if (choice == "river") {
            if (postgame_add_once(player, "Fishing Rod")) {
                say("\nYou carve a fishing rod and learn that hero work did not teach patience.");
            } else if (postgame_add_once(player, "River Boat")) {
                say("\nYou build a small river boat and map the bends beyond town.");
            } else {
                static const std::vector<std::string> catches = {
                    "Silver Minnow",
                    "Boot With Teeth Marks",
                    "Tiny Treasure Chest",
                };
                std::string caught = random_choice(catches);
                player.backpack.push_back(caught);
                say("\nYou fish until sunset and catch a " + caught + ".");
            }
        } else if (choice == "apprentice") {
            if (postgame_add_once(player, "Apprentice Badge")) {
                say("\nA young adventurer asks to train with you. You give them an Apprentice Badge.");
            } else {
                say("\nYou teach your apprentice how to pack snacks, read maps, and run only when running helps.");
            }
        } else if (choice == "adventure") {
            static const std::vector<std::string> finds = {
                "Starlit Pebble",
                "Old Road Coin",
                "Map to Nowhere",
            };
            std::string found = random_choice(finds);
            player.backpack.push_back(found);
            say("\nYou take one more walk into the hills and return with a " + found + ".");
        } else if (choice == "status") {
            postgame_status(player);
        } else if (choice == "exit") {
            return;
        }
    }
}

void run_scene(const std::string& scene_id, Player& player, std::unordered_map<std::string, bool>& shop_stock) {
    if (scene_id == "intro") {
        intro_scene(player);
    } else if (scene_id == "wizard") {
        wizard_scene(player);
    } else if (scene_id == "locked_door") {
        locked_door_scene(player);
    } else if (scene_id == "first_goblin") {
        first_goblin_scene(player);
    } else if (scene_id == "village") {
        village_scene(player, shop_stock);
    } else if (scene_id == "forest") {
        forest_scene(player, shop_stock);
    } else if (scene_id == "twin_doors") {
        twin_doors_scene(player);
    } else if (scene_id == "witch") {
        witch_scene(player);
    } else if (scene_id == "mountain_pass") {
        mountain_pass_scene(player);
    } else if (scene_id == "moonlit_market") {
        moonlit_market_scene(player, shop_stock);
    } else if (scene_id == "vampire_castle") {
        vampire_castle_scene(player);
    } else if (scene_id == "false_throne") {
        false_throne_scene(player, shop_stock);
    } else if (scene_id == "underkeep") {
        underkeep_scene(player);
    } else if (scene_id == "clocktower") {
        clocktower_scene(player, shop_stock);
    } else if (scene_id == "well") {
        well_scene(player);
    } else if (scene_id == "hundred_day_road") {
        hundred_day_road_scene(player, shop_stock);
    } else if (scene_id == "dragon_gate") {
        dragon_gate_scene(player, shop_stock);
    } else if (scene_id == "final_battle") {
        final_battle_scene(player);
    } else {
        throw std::runtime_error("Unknown story checkpoint.");
    }
}

void finish_game(const Player& player) {
    say("\nThe Realmbound Dragon's storm breaks apart into silver sparks above the saved realm.");
    say("\nGood job, " + player.name + ", you have completed the game.");
    say("\nCredits: Realmbound by Thunderstruck7 and Lord Funion.");
    std::cout << "\n" << term::bright_yellow("THE END") << "\nYou finished with " << money_text(player.money) << ".\n";
    autosave_tick();
}

bool checkpoint_menu(State& state) {
    while (true) {
        std::string subtitle = "Next: " + scene_title(state.next_scene) + " | Autosave: " + SAVE_PATH;
        std::string choice = choose_menu("Checkpoint", {
            {"1", "Continue", "continue", "", {"continue", "c", "next"}},
            {"2", "Save Game", "save", "", {"save", "s"}},
            {"3", "Load Game", "load", "", {"load", "l"}},
            {"4", "Cloud Saves", "cloud", "", {"cloud", "online", "sync"}},
            {"5", EXIT_LABEL, "exit", "", {"exit", "quit", "q"}},
        }, "Checkpoint choice: ", subtitle);

        if (choice == "continue") {
            return true;
        }
        if (choice == "save") {
            try {
                save_state(state);
                say("\nSaved C++ checkpoint to " + std::string(SAVE_PATH) + ".");
            } catch (const std::exception& exc) {
                say(std::string("\nSave failed: ") + exc.what());
            }
        } else if (choice == "load") {
            try {
                state = load_state();
                say("\nLoaded C++ autosave.");
                return true;
            } catch (const std::exception& exc) {
                say(std::string("\nLoad failed: ") + exc.what());
            }
        } else if (choice == "cloud") {
            say("\nCloud saves are not available in the C++ port.");
        } else if (choice == "exit") {
            exit_game();
        }
    }
}

void run_story(State state) {
    AutosaveScope autosave_scope(state);
    QuickMenuScope quick_menu_scope(state.player);
    while (true) {
        std::string scene_id = state.next_scene;
        if (scene_id == FINISHED_SCENE) {
            finish_game(state.player);
            postgame_menu(state.player);
            return;
        }

        run_scene(scene_id, state.player, state.shop_stock);

        state.next_scene = next_scene(scene_id);
        if (state.next_scene == FINISHED_SCENE) {
            finish_game(state.player);
            postgame_menu(state.player);
            return;
        }

        if (autosave_state(state)) {
            say("\nAutosaved.");
        }
    }
}

std::string restart_menu() {
    return choose_menu("Game Over", {
        {"1", "Restart", "restart", "", {"restart", "r", "new game", "new"}},
        {"2", "Main Menu", "main", "", {"main", "menu", "m"}},
        {"3", EXIT_LABEL, "exit", "", {"exit", "quit", "q"}},
    }, "Game over choice: ");
}

State main_menu_state() {
    while (true) {
        std::string choice = choose_menu("Realmbound", {
            {"1", "New Game", "new", "", {"new", "start"}},
            {"2", "Load Game", "load", "", {"load", "continue"}},
            {"3", "Cloud Saves", "cloud", "", {"cloud", "online", "sync"}},
            {"4", EXIT_LABEL, "exit", "", {"exit", "quit", "q"}},
        }, "Main menu choice: ");

        if (choice == "new") {
            return new_state();
        }
        if (choice == "load") {
            try {
                return load_state_interactive();
            } catch (const std::runtime_error& exc) {
                if (std::string(exc.what()) == "back") {
                    continue;
                }
                throw;
            }
        }
        if (choice == "cloud") {
            say("\nCloud saves are not available in the C++ port.");
        }
        if (choice == "exit") {
            exit_game();
        }
    }
}

fs::path executable_directory() {
#ifdef _WIN32
    std::vector<char> buffer(MAX_PATH);
    while (true) {
        DWORD length = GetModuleFileNameA(nullptr, buffer.data(), static_cast<DWORD>(buffer.size()));
        if (length == 0) {
            return {};
        }
        if (length < buffer.size() - 1) {
            return fs::path(std::string(buffer.data(), length)).parent_path();
        }
        buffer.resize(buffer.size() * 2);
    }
#elif defined(__linux__)
    std::vector<char> buffer(1024);
    while (true) {
        ssize_t length = readlink("/proc/self/exe", buffer.data(), buffer.size());
        if (length < 0) {
            return {};
        }
        if (static_cast<std::size_t>(length) < buffer.size()) {
            return fs::path(std::string(buffer.data(), static_cast<std::size_t>(length))).parent_path();
        }
        buffer.resize(buffer.size() * 2);
    }
#else
    return {};
#endif
}

void use_executable_directory() {
    fs::path directory = executable_directory();
    if (!directory.empty()) {
        fs::current_path(directory);
    }
}

void show_logo() {
    const std::string logo =
        " ____            _           _                           _\n"
        "|  _ \\ ___  __ _| |_ __ ___ | |__   ___  _   _ _ __   __| |\n"
        "| |_) / _ \\/ _` | | '_ ` _ \\| '_ \\ / _ \\| | | | '_ \\ / _` |\n"
        "|  _ <  __/ (_| | | | | | | | |_) | (_) | |_| | | | | (_| |\n"
        "|_| \\_\\___|\\__,_|_|_| |_| |_|_.__/ \\___/ \\__,_|_| |_|\\__,_|\n\n";
    std::cout << term::bright_yellow(logo);
}

void run_game() {
    show_logo();
    std::string mode = "menu";
    while (true) {
        try {
            if (mode == "restart") {
                run_story(new_state());
            } else {
                run_story(main_menu_state());
            }
            return;
        } catch (const GameOver&) {
            std::string choice = restart_menu();
            if (choice == "restart") {
                show_logo();
                mode = "restart";
            } else if (choice == "main") {
                show_logo();
                mode = "menu";
            } else if (choice == "exit") {
                exit_game();
            }
        }
    }
}

int main() {
    try {
        use_executable_directory();
        run_game();
    } catch (const ExitGame&) {
        return 0;
    } catch (const std::exception& exc) {
        std::cerr << "\nAdventure Game C++ port error: " << exc.what() << "\n";
        return 1;
    }
    return 0;
}
