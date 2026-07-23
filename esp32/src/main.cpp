#include <Arduino.h>
#include <esp_system.h>
#include <Preferences.h>
#include <SPI.h>

#include "RealmboundConfig.h"

#if REALMBOUND_DISPLAY_DRIVER == REALMBOUND_DISPLAY_ST7789
#include <Adafruit_ST7789.h>
Adafruit_ST7789 tft(REALMBOUND_TFT_CS, REALMBOUND_TFT_DC, REALMBOUND_TFT_RST);
#else
#include <Adafruit_ST7735.h>
Adafruit_ST7735 tft(REALMBOUND_TFT_CS, REALMBOUND_TFT_DC, REALMBOUND_TFT_RST);
#endif

Preferences prefs;

constexpr uint16_t COLOR_BG = ST77XX_BLACK;
constexpr uint16_t COLOR_TEXT = ST77XX_WHITE;
constexpr uint16_t COLOR_TITLE = ST77XX_YELLOW;
constexpr uint16_t COLOR_DIM = 0x8410;
constexpr uint16_t COLOR_GOOD = ST77XX_GREEN;
constexpr uint16_t COLOR_BAD = ST77XX_RED;
constexpr uint16_t COLOR_BLUE = ST77XX_CYAN;
constexpr uint32_t SAVE_MAGIC = 0x52424e44; // RBND

enum Button : uint8_t {
  BTN_NONE,
  BTN_UP,
  BTN_DOWN,
  BTN_SELECT,
  BTN_BACK,
};

enum Mode : uint8_t {
  MODE_MENU,
  MODE_TEXT,
};

enum Action : uint8_t {
  ACT_NONE,
  ACT_NEW_GAME,
  ACT_LOAD_GAME,
  ACT_SHOW_TITLE,
  ACT_RESUME,
  ACT_SAVE_GAME,
  ACT_SHOW_STATS,
  ACT_RUN_SCENE,
  ACT_CHOOSE_FROG,
  ACT_CHOOSE_WAND,
  ACT_OPEN_SHOP,
  ACT_SHOP_WEAPON,
  ACT_SHOP_ARMOR,
  ACT_SHOP_MANA,
  ACT_SHOP_POTION,
  ACT_SHOP_EXIT,
  ACT_ATTACK,
  ACT_SPELL,
  ACT_POTION,
  ACT_RUN_AWAY,
  ACT_LONG_ROAD_NEXT,
  ACT_POSTGAME,
};

enum FightKind : uint8_t {
  FIGHT_ADVANCE_SCENE,
  FIGHT_LONG_ROAD,
  FIGHT_FINAL,
};

struct Enemy {
  const char* name;
  uint16_t hp;
  uint8_t damage;
  uint8_t reward;
  const char* attack;
};

struct GameState {
  uint32_t magic = SAVE_MAGIC;
  uint8_t scene = 0;
  uint8_t longRoadIndex = 0;
  uint16_t maxHp = 100;
  uint16_t hp = 100;
  uint16_t maxMana = 60;
  uint16_t mana = 60;
  uint16_t nickels = 40;
  uint8_t weapon = 0;
  uint8_t armor = 0;
  uint8_t potions = 2;
  uint8_t flags = 0;
};

constexpr uint8_t FLAG_FROG = 1 << 0;
constexpr uint8_t FLAG_ROAD_STARTED = 1 << 1;
constexpr uint8_t FLAG_ROAD_SEAL = 1 << 2;
constexpr uint8_t FLAG_DRAGON_SCALE = 1 << 3;
constexpr uint8_t FLAG_FINISHED = 1 << 4;

GameState game;
Mode mode = MODE_MENU;
String screenTitle;
String screenBody;
Action textAction = ACT_NONE;

struct MenuItem {
  String label;
  Action action;
  bool enabled;
};

MenuItem menuItems[6];
uint8_t menuCount = 0;
uint8_t menuIndex = 0;
String menuSubtitle;
Action shopExitAction = ACT_SHOP_EXIT;
bool hasPausedScreen = false;
Mode pausedMode = MODE_MENU;
String pausedTitle;
String pausedBody;
String pausedSubtitle;
Action pausedTextAction = ACT_NONE;
MenuItem pausedMenuItems[6];
uint8_t pausedMenuCount = 0;
uint8_t pausedMenuIndex = 0;

Enemy activeEnemy;
int16_t enemyHp = 0;
FightKind fightKind = FIGHT_ADVANCE_SCENE;
String statusLine;

constexpr Enemy STORY_ENEMIES[] = {
  {"gate rat", 28, 8, 8, "rusty nibble"},
  {"shadow knight", 95, 25, 18, "gloom slash"},
  {"crystal dragon", 145, 32, 28, "tail prism"},
};

constexpr Enemy LONG_ROAD_ENEMIES[] = {
  {"ashfall pilgrim", 96, 23, 12, "ember staff"},
  {"lantern jackal", 100, 24, 12, "lamp bite"},
  {"mossbound knight", 108, 25, 13, "root shield"},
  {"mirror moth", 92, 26, 13, "reflection flash"},
  {"ember librarian", 112, 27, 14, "burning bookmark"},
  {"fogbank siren", 116, 28, 14, "mist song"},
  {"tin crown bandit", 120, 29, 15, "fake decree"},
  {"hollow beekeeper", 124, 30, 15, "hive rattle"},
  {"moonlit scarecrow", 128, 31, 16, "moon grin"},
  {"iron acorn brute", 136, 32, 16, "oak punch"},
  {"velvet gargoyle", 132, 33, 17, "balcony crash"},
  {"clockwork eel", 118, 34, 17, "gear bite"},
  {"glacier monk", 140, 35, 18, "frozen palm"},
  {"briar drummer", 126, 36, 18, "thorn rhythm"},
  {"marble banshee", 144, 37, 19, "statue shriek"},
  {"thunder yak", 150, 38, 19, "storm charge"},
  {"paper lantern fiend", 122, 39, 20, "paper flame"},
  {"copper wyvern", 156, 40, 20, "green fire"},
  {"old road revenant", 148, 41, 21, "dust hand"},
  {"saltwater specter", 152, 42, 21, "brine wave"},
  {"orchard mimic", 160, 43, 22, "apple snap"},
  {"candlewax duelist", 146, 44, 22, "wick rapier"},
  {"rune-tusk boar", 168, 45, 23, "glyph gore"},
  {"midnight tax collector", 154, 46, 23, "late fee"},
  {"feathered basilisk", 162, 47, 24, "plume stare"},
  {"broken compass spirit", 158, 48, 24, "northless pull"},
  {"jewel wasp swarm", 170, 49, 25, "ruby sting"},
  {"singing stump", 166, 50, 25, "root chorus"},
  {"blackglass panther", 176, 51, 26, "mirror pounce"},
  {"sunken bell knight", 184, 52, 26, "drowned chime"},
  {"nettle witchling", 172, 53, 27, "green hex"},
  {"storm cellar troll", 190, 54, 27, "barrel throw"},
  {"silver mask rogue", 178, 55, 28, "quiet dagger"},
  {"bonewheel racer", 182, 56, 28, "wheel crash"},
  {"spellbook leech", 188, 57, 29, "page drain"},
  {"cloud anvil giant", 208, 58, 29, "sky hammer"},
  {"porcelain hydra", 202, 59, 30, "china fang"},
  {"scarecrow magistrate", 194, 60, 30, "field warrant"},
  {"obsidian choir", 210, 61, 31, "black hymn"},
  {"frostroot colossus", 224, 62, 31, "rootquake"},
  {"honeycomb horror", 198, 63, 32, "sticky maw"},
  {"brass cathedral rook", 218, 64, 32, "bell tower dive"},
  {"map-eating serpent", 206, 65, 33, "legend swallow"},
  {"velvet thunderlord", 230, 66, 33, "royal thunder"},
  {"eclipse ferryman", 220, 67, 34, "black oar"},
  {"crownless lion", 236, 68, 34, "throne roar"},
  {"dream ash phantom", 214, 69, 35, "sleep cinder"},
  {"seven-key jailer", 242, 70, 35, "keyring crush"},
  {"realmquake titan", 260, 72, 36, "continent stomp"},
  {"calendar dragon", 280, 74, 38, "deadline flame"},
};

static_assert(sizeof(LONG_ROAD_ENEMIES) / sizeof(LONG_ROAD_ENEMIES[0]) == 50, "Long road must have exactly 50 enemies.");

constexpr Enemy FINAL_DRAGON = {
  "Realmbound Dragon",
  320,
  78,
  100,
  "starfire breath",
};

void showTitle();
void showPause();
void restorePausedScreen();
void runScene();
void openShop(Action exitAction = ACT_SHOP_EXIT);
void runLongRoad();
void render();
void handleAction(Action action);

String moneyText(uint16_t amount) {
  return String(amount) + (amount == 1 ? " Whoop Nickel" : " Whoop Nickels");
}

int minInt(int left, int right) {
  return left < right ? left : right;
}

int maxInt(int left, int right) {
  return left > right ? left : right;
}

String statLine() {
  return String("HP ") + String(game.hp) + "/" + String(game.maxHp) +
         " MP " + String(game.mana) + "/" + String(game.maxMana) +
         " WN " + String(game.nickels);
}

bool flagSet(uint8_t flag) {
  return (game.flags & flag) != 0;
}

void setFlag(uint8_t flag, bool value = true) {
  if (value) {
    game.flags |= flag;
  } else {
    game.flags &= ~flag;
  }
}

void saveGame() {
  prefs.begin("realmbound", false);
  prefs.putBytes("state", &game, sizeof(game));
  prefs.end();
}

bool loadGame() {
  GameState loaded;
  prefs.begin("realmbound", true);
  size_t read = prefs.getBytes("state", &loaded, sizeof(loaded));
  prefs.end();
  if (read != sizeof(loaded) || loaded.magic != SAVE_MAGIC) {
    return false;
  }
  game = loaded;
  return true;
}

void newGame() {
  game = GameState();
  statusLine = "";
}

void configurePins() {
  pinMode(REALMBOUND_BUTTON_UP, INPUT_PULLUP);
  pinMode(REALMBOUND_BUTTON_DOWN, INPUT_PULLUP);
  pinMode(REALMBOUND_BUTTON_SELECT, INPUT_PULLUP);
  pinMode(REALMBOUND_BUTTON_BACK, INPUT_PULLUP);
#if REALMBOUND_TFT_BL >= 0
  pinMode(REALMBOUND_TFT_BL, OUTPUT);
  digitalWrite(REALMBOUND_TFT_BL, HIGH);
#endif
}

void initDisplay() {
  SPI.begin(REALMBOUND_TFT_SCLK, -1, REALMBOUND_TFT_MOSI, REALMBOUND_TFT_CS);
#if REALMBOUND_DISPLAY_DRIVER == REALMBOUND_DISPLAY_ST7789
  tft.init(REALMBOUND_TFT_WIDTH, REALMBOUND_TFT_HEIGHT);
#else
  tft.initR(REALMBOUND_TFT_TAB);
#endif
  tft.setRotation(REALMBOUND_TFT_ROTATION);
  tft.setTextWrap(false);
  tft.fillScreen(COLOR_BG);
}

Button readButton() {
  static uint32_t lastPressMs = 0;
  if (millis() - lastPressMs < 140) {
    return BTN_NONE;
  }

  Button button = BTN_NONE;
  if (digitalRead(REALMBOUND_BUTTON_UP) == LOW) {
    button = BTN_UP;
  } else if (digitalRead(REALMBOUND_BUTTON_DOWN) == LOW) {
    button = BTN_DOWN;
  } else if (digitalRead(REALMBOUND_BUTTON_SELECT) == LOW) {
    button = BTN_SELECT;
  } else if (digitalRead(REALMBOUND_BUTTON_BACK) == LOW) {
    button = BTN_BACK;
  } else if (Serial.available()) {
    char value = static_cast<char>(Serial.read());
    if (value == 'w' || value == 'W') button = BTN_UP;
    if (value == 's' || value == 'S') button = BTN_DOWN;
    if (value == 'e' || value == 'E' || value == '\n' || value == '\r') button = BTN_SELECT;
    if (value == 'b' || value == 'B') button = BTN_BACK;
  }

  if (button != BTN_NONE) {
    lastPressMs = millis();
  }
  return button;
}

void drawWrapped(const String& text, int16_t x, int16_t y, int16_t width, uint8_t maxLines, uint16_t color) {
  tft.setTextColor(color, COLOR_BG);
  tft.setTextSize(1);

  const uint8_t calculatedChars = width / 6;
  const uint8_t maxChars = calculatedChars < 8 ? 8 : calculatedChars;
  String line;
  String word;
  uint8_t lines = 0;

  auto flushLine = [&]() {
    if (lines >= maxLines) return;
    tft.setCursor(x, y + lines * 10);
    tft.print(line);
    line = "";
    lines++;
  };

  for (uint16_t i = 0; i <= text.length(); ++i) {
    char c = i < text.length() ? text[i] : ' ';
    if (c == '\n') {
      if (word.length()) {
        if (line.length() + word.length() + 1 > maxChars) flushLine();
        if (line.length()) line += ' ';
        line += word;
        word = "";
      }
      flushLine();
      continue;
    }
    if (c == ' ' || i == text.length()) {
      if (word.length()) {
        if (line.length() + word.length() + (line.length() ? 1 : 0) > maxChars) {
          flushLine();
        }
        if (line.length()) line += ' ';
        line += word;
        word = "";
      }
    } else {
      word += c;
    }
  }
  if (line.length() && lines < maxLines) {
    flushLine();
  }
}

void setTextScreen(const String& title, const String& body, Action nextAction) {
  mode = MODE_TEXT;
  screenTitle = title;
  screenBody = body;
  textAction = nextAction;
  render();
}

void setMenu(const String& title, const String& subtitle, const MenuItem* items, uint8_t count) {
  mode = MODE_MENU;
  screenTitle = title;
  menuSubtitle = subtitle;
  menuCount = count > 6 ? 6 : count;
  menuIndex = 0;
  for (uint8_t i = 0; i < menuCount; ++i) {
    menuItems[i] = items[i];
  }
  render();
}

void renderMenu() {
  tft.fillScreen(COLOR_BG);
  tft.setTextSize(1);
  tft.setTextColor(COLOR_TITLE, COLOR_BG);
  tft.setCursor(2, 2);
  tft.print(screenTitle);
  drawWrapped(menuSubtitle, 2, 14, tft.width() - 4, 3, COLOR_DIM);

  int16_t y = 46;
  for (uint8_t i = 0; i < menuCount; ++i) {
    tft.setCursor(4, y + i * 14);
    bool selected = i == menuIndex;
    uint16_t color = menuItems[i].enabled ? COLOR_TEXT : COLOR_DIM;
    if (selected) {
      tft.fillRect(0, y + i * 14 - 2, tft.width(), 12, ST77XX_BLUE);
      color = ST77XX_WHITE;
    }
    tft.setTextColor(color, selected ? ST77XX_BLUE : COLOR_BG);
    tft.print(selected ? "> " : "  ");
    tft.print(menuItems[i].label);
  }

  tft.setTextColor(COLOR_DIM, COLOR_BG);
  tft.setCursor(2, tft.height() - 10);
  tft.print("UP/DN move  SEL choose");
}

void renderText() {
  tft.fillScreen(COLOR_BG);
  tft.setTextSize(1);
  tft.setTextColor(COLOR_TITLE, COLOR_BG);
  tft.setCursor(2, 2);
  tft.print(screenTitle);
  uint8_t availableLines = (tft.height() - 32) / 10;
  if (availableLines < 8) {
    availableLines = 8;
  }
  drawWrapped(screenBody, 2, 16, tft.width() - 4, availableLines, COLOR_TEXT);
  tft.setTextColor(COLOR_DIM, COLOR_BG);
  tft.setCursor(2, tft.height() - 10);
  tft.print("SEL continue  BACK menu");
}

void render() {
  if (mode == MODE_MENU) {
    renderMenu();
  } else {
    renderText();
  }
}

void showTitle() {
  MenuItem items[] = {
    {"New Game", ACT_NEW_GAME, true},
    {"Continue", ACT_LOAD_GAME, true},
  };
  setMenu("Realmbound", String("ESP32 TFT edition\n") + statLine(), items, 2);
}

void showPause() {
  if (screenTitle != "Pause") {
    hasPausedScreen = true;
    pausedMode = mode;
    pausedTitle = screenTitle;
    pausedBody = screenBody;
    pausedSubtitle = menuSubtitle;
    pausedTextAction = textAction;
    pausedMenuCount = menuCount;
    pausedMenuIndex = menuIndex;
    for (uint8_t i = 0; i < menuCount; ++i) {
      pausedMenuItems[i] = menuItems[i];
    }
  }

  MenuItem items[] = {
    {"Resume", ACT_RESUME, true},
    {"Stats", ACT_SHOW_STATS, true},
    {"Save Game", ACT_SAVE_GAME, true},
    {"Title", ACT_SHOW_TITLE, true},
  };
  setMenu("Pause", statLine(), items, 4);
}

void restorePausedScreen() {
  if (!hasPausedScreen) {
    showTitle();
    return;
  }
  mode = pausedMode;
  screenTitle = pausedTitle;
  screenBody = pausedBody;
  menuSubtitle = pausedSubtitle;
  textAction = pausedTextAction;
  menuCount = pausedMenuCount;
  menuIndex = pausedMenuIndex;
  for (uint8_t i = 0; i < pausedMenuCount; ++i) {
    menuItems[i] = pausedMenuItems[i];
  }
  hasPausedScreen = false;
  render();
}

void showStats() {
  String body = statLine();
  body += String("\nWeapon +") + String(game.weapon);
  body += String(" Armor +") + String(game.armor);
  body += String("\nPotions ") + String(game.potions);
  body += flagSet(FLAG_FROG) ? "\nRoute: frog partner" : "\nRoute: wand";
  body += String("\nRoad ") + String(game.longRoadIndex) + "/50";
  setTextScreen("Stats", body, ACT_RESUME);
}

void openShop(Action exitAction) {
  shopExitAction = exitAction;
  MenuItem items[] = {
    {"Weapon +4 35WN", ACT_SHOP_WEAPON, game.nickels >= 35},
    {"Armor +3 35WN", ACT_SHOP_ARMOR, game.nickels >= 35},
    {"Mana +15 25WN", ACT_SHOP_MANA, game.nickels >= 25},
    {"Potion 12WN", ACT_SHOP_POTION, game.nickels >= 12},
    {"Leave Shop", shopExitAction, true},
  };
  String subtitle = String("Gnome Depot travel stall\n") + statLine();
  if (statusLine.length()) {
    subtitle += String("\n") + statusLine;
  }
  setMenu("Shop", subtitle, items, 5);
}

void showCombatMenu() {
  MenuItem items[] = {
    {"Attack", ACT_ATTACK, true},
    {"Spell 10MP", ACT_SPELL, game.mana >= 10},
    {"Potion", ACT_POTION, game.potions > 0},
    {"Run", ACT_RUN_AWAY, true},
  };
  setMenu(String(activeEnemy.name), statusLine + "\n" + statLine() + "\nEnemy HP " + String(enemyHp), items, 4);
}

void startFight(const Enemy& enemy, FightKind kind) {
  activeEnemy = enemy;
  enemyHp = enemy.hp;
  fightKind = kind;
  statusLine = String("A ") + String(activeEnemy.name) + " attacks.";
  showCombatMenu();
}

void enemyTurn() {
  int damage = maxInt(1, activeEnemy.damage - game.armor);
  if (damage >= game.hp) {
    game.hp = 0;
  } else {
    game.hp -= damage;
  }
  statusLine += String("\n") + String(activeEnemy.attack) + " hits for " + String(damage) + ".";
}

void afterVictory() {
  game.nickels += activeEnemy.reward;
  if (random(0, 4) == 0) {
    game.potions++;
    statusLine += "\nFound a potion.";
  }
  saveGame();

  if (fightKind == FIGHT_FINAL) {
    setFlag(FLAG_FINISHED);
    game.scene = 7;
    saveGame();
    setTextScreen(
      "Realm Saved",
      "The Realmbound Dragon falls. The storm breaks into silver sparks. Good job, adventurer, you completed the game.",
      ACT_POSTGAME
    );
    return;
  }

  statusLine = String("The ") + String(activeEnemy.name) + " is defeated.\n" + statusLine;

  if (fightKind == FIGHT_LONG_ROAD) {
    game.longRoadIndex++;
    if (game.longRoadIndex % 5 == 0) {
      game.hp = minInt(game.maxHp, game.hp + 30);
      game.mana = minInt(game.maxMana, game.mana + 20);
      statusLine += "\nA shrine restores 30HP and 20MP.";
    }
    saveGame();

    if (game.longRoadIndex >= 50) {
      setFlag(FLAG_ROAD_SEAL);
      game.nickels += 150;
      game.scene = 5;
      saveGame();
      setTextScreen(
        "Road Complete",
        "The fiftieth milepost cracks open. You gain the Hundred-Day Road Seal and 150 Whoop Nickels.",
        ACT_RUN_SCENE
      );
      return;
    }

    setTextScreen(
      "Victory",
      statusLine + "\nCheckpoint saved. Road " + String(game.longRoadIndex) + "/50 complete.",
      ACT_LONG_ROAD_NEXT
    );
    return;
  }

  game.scene++;
  saveGame();
  setTextScreen("Victory", statusLine + "\nYou gained " + moneyText(activeEnemy.reward) + ".", ACT_RUN_SCENE);
}

void playerAttack(bool spell) {
  if (spell && game.mana < 10) {
    statusLine = "Not enough mana.";
    showCombatMenu();
    return;
  }
  int damage = spell ? 24 + game.weapon : 10 + game.weapon;
  if (flagSet(FLAG_FROG) && !spell) {
    damage += 4;
  }
  if (spell) {
    game.mana -= 10;
  }

  enemyHp -= damage;
  statusLine = String(spell ? "Spell" : "Attack") + " hits for " + String(damage) + ".";
  if (enemyHp <= 0) {
    afterVictory();
    return;
  }

  enemyTurn();
  if (game.hp <= 0) {
    setTextScreen("Game Over", "You were defeated on the road. The save is still there if you want to try again.", ACT_SHOW_TITLE);
    return;
  }
  showCombatMenu();
}

void runScene() {
  if (game.scene == 0) {
    MenuItem items[] = {
      {"Keep Frog", ACT_CHOOSE_FROG, true},
      {"Trade For Wand", ACT_CHOOSE_WAND, true},
    };
    setMenu("Chocolate Frog", "Rumblerod offers a wand for the frog. The choice changes your fighting style.", items, 2);
    return;
  }

  if (game.scene == 1) {
    setTextScreen("Locked Door", "A gate rat guards the first sealed door. Time to prove this tiny port can still fight.", ACT_ATTACK);
    startFight(STORY_ENEMIES[0], FIGHT_ADVANCE_SCENE);
    return;
  }

  if (game.scene == 2) {
    statusLine = "";
    openShop();
    return;
  }

  if (game.scene == 3) {
    setTextScreen("Underkeep", "A shadow knight blocks the map chamber under the castle.", ACT_ATTACK);
    startFight(STORY_ENEMIES[1], FIGHT_ADVANCE_SCENE);
    return;
  }

  if (game.scene == 4) {
    runLongRoad();
    return;
  }

  if (game.scene == 5) {
    setTextScreen("Dragon Gate", "The Dragon Gate opens. A crystal dragon sneezes rainbows and refuses to move.", ACT_ATTACK);
    setFlag(FLAG_DRAGON_SCALE);
    startFight(STORY_ENEMIES[2], FIGHT_ADVANCE_SCENE);
    return;
  }

  if (game.scene == 6) {
    if (flagSet(FLAG_DRAGON_SCALE)) {
      game.hp = minInt(game.maxHp, game.hp + 40);
      game.mana = minInt(game.maxMana, game.mana + 35);
    }
    startFight(FINAL_DRAGON, FIGHT_FINAL);
    return;
  }

  setTextScreen("Postgame", "The realm is saved. Build a house, start a family, and keep adventuring in your imagination.", ACT_POSTGAME);
}

void runLongRoad() {
  if (!flagSet(FLAG_ROAD_STARTED)) {
    setFlag(FLAG_ROAD_STARTED);
    saveGame();
    setTextScreen(
      "Hundred-Day Road",
      "The map unfolds into a road longer than the paper. Fifty enemies stand between you and the Dragon Gate.",
      ACT_LONG_ROAD_NEXT
    );
    return;
  }

  if (game.longRoadIndex >= 50) {
    game.scene = 5;
    runScene();
    return;
  }

  if (game.longRoadIndex % 10 == 0) {
    statusLine = String("A new month begins. Road ") + String(game.longRoadIndex + 1) + "/50.";
    if (game.longRoadIndex > 0) {
      openShop(ACT_LONG_ROAD_NEXT);
      return;
    }
  }
  startFight(LONG_ROAD_ENEMIES[game.longRoadIndex], FIGHT_LONG_ROAD);
}

void handleAction(Action action) {
  switch (action) {
    case ACT_NEW_GAME:
      newGame();
      runScene();
      break;
    case ACT_LOAD_GAME:
      if (loadGame()) {
        setTextScreen("Loaded", "Save loaded from ESP32 flash.", ACT_RUN_SCENE);
      } else {
        setTextScreen("No Save", "No valid save was found. Start a new game from the title screen.", ACT_SHOW_TITLE);
      }
      break;
    case ACT_SHOW_TITLE:
      showTitle();
      break;
    case ACT_RESUME:
      restorePausedScreen();
      break;
    case ACT_RUN_SCENE:
      runScene();
      break;
    case ACT_SAVE_GAME:
      saveGame();
      setTextScreen("Saved", "Progress saved to ESP32 flash.", ACT_RESUME);
      break;
    case ACT_SHOW_STATS:
      showStats();
      break;
    case ACT_CHOOSE_FROG:
      setFlag(FLAG_FROG);
      game.scene = 1;
      saveGame();
      setTextScreen("Frog Route", "The frog joins you and adds bite to basic attacks.", ACT_RUN_SCENE);
      break;
    case ACT_CHOOSE_WAND:
      setFlag(FLAG_FROG, false);
      game.weapon += 2;
      game.scene = 1;
      saveGame();
      setTextScreen("Wand Route", "You trade the frog for a wand. Weapon damage rises by 2.", ACT_RUN_SCENE);
      break;
    case ACT_OPEN_SHOP:
      openShop();
      break;
    case ACT_SHOP_WEAPON:
      game.nickels -= 35;
      game.weapon += 4;
      statusLine = "Weapon upgraded.";
      saveGame();
      openShop(shopExitAction);
      break;
    case ACT_SHOP_ARMOR:
      game.nickels -= 35;
      game.armor += 3;
      statusLine = "Armor upgraded.";
      saveGame();
      openShop(shopExitAction);
      break;
    case ACT_SHOP_MANA:
      game.nickels -= 25;
      game.maxMana += 15;
      game.mana = game.maxMana;
      statusLine = "Mana upgraded.";
      saveGame();
      openShop(shopExitAction);
      break;
    case ACT_SHOP_POTION:
      game.nickels -= 12;
      game.potions++;
      statusLine = "Potion bought.";
      saveGame();
      openShop(shopExitAction);
      break;
    case ACT_SHOP_EXIT:
      game.scene++;
      saveGame();
      runScene();
      break;
    case ACT_ATTACK:
      playerAttack(false);
      break;
    case ACT_SPELL:
      playerAttack(true);
      break;
    case ACT_POTION:
      if (game.potions > 0) {
        game.potions--;
        game.hp = minInt(game.maxHp, game.hp + 35);
        statusLine = "Potion used.";
      } else {
        statusLine = "No potions.";
      }
      showCombatMenu();
      break;
    case ACT_RUN_AWAY:
      setTextScreen("Game Over", "You ran. The realm remembers.", ACT_SHOW_TITLE);
      break;
    case ACT_LONG_ROAD_NEXT:
      runLongRoad();
      break;
    case ACT_POSTGAME:
      showTitle();
      break;
    default:
      break;
  }
}

void handleButton(Button button) {
  if (button == BTN_BACK) {
    showPause();
    return;
  }

  if (mode == MODE_TEXT) {
    if (button == BTN_SELECT) {
      handleAction(textAction);
    }
    return;
  }

  if (mode == MODE_MENU) {
    if (button == BTN_UP && menuCount) {
      menuIndex = menuIndex == 0 ? menuCount - 1 : menuIndex - 1;
      render();
    } else if (button == BTN_DOWN && menuCount) {
      menuIndex = (menuIndex + 1) % menuCount;
      render();
    } else if (button == BTN_SELECT && menuCount) {
      if (menuItems[menuIndex].enabled) {
        handleAction(menuItems[menuIndex].action);
      }
    }
  }
}

void setup() {
  Serial.begin(115200);
  configurePins();
  initDisplay();
  randomSeed(esp_random());
  showTitle();
}

void loop() {
  Button button = readButton();
  if (button != BTN_NONE) {
    handleButton(button);
  }
}
