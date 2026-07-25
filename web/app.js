(() => {
  "use strict";

  const SAVE_STORAGE_KEY = "adventureGame.webSaves.v1";
  const CLOUD_STORAGE_KEY = "adventureGame.cloudSession.v1";
  const SAVE_SUFFIX = ".tasave";
  const SAVE_FORMAT_VERSION = 1;
  const DEFAULT_API_URL = "https://lordfunion.dev/adventure-api";
  const BASIC_DAMAGE = 8;
  const STATUS_DAMAGE = 4;
  const OUTPUT_DELAY_MS = 280;
  const FINISHED_SCENE = "finished";
  let ENCOUNTER_DATA = null;
  async function loadEncounterData() { const r=await fetch("story/encounters.json",{cache:"no-store"}); if(!r.ok) throw new Error(`Encounter data ${r.status}`); ENCOUNTER_DATA=await r.json(); }
  const SCENE_ORDER = [
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
  ];
  const SCENE_TITLES = {
    intro: "Chocolate Frog",
    wizard: "Rumblerod",
    locked_door: "Locked Door",
    first_goblin: "First Goblin",
    village: "Village",
    forest: "Forest Trail",
    twin_doors: "Twin Doors",
    witch: "Witch",
    mountain_pass: "Mountain Pass",
    moonlit_market: "Moonlit Market",
    vampire_castle: "Vampire Castle",
    false_throne: "False Throne",
    underkeep: "Underkeep",
    clocktower: "Clocktower",
    well: "Old Well",
    hundred_day_road: "The Hundred-Day Road",
    dragon_gate: "Dragon Gate",
    final_battle: "Final Battle",
    [FINISHED_SCENE]: "Finished Game",
  };

  const SPELLS = {
    Fireball: {
      damage: 18,
      manaCost: 10,
      effects: { burn: 2 },
      description: "Deals 14 damage and sets the target burning.",
    },
    "Arcane Blast": {
      damage: 0,
      manaCost: 24,
      effects: { stun: 2 },
      description: "Stuns an enemy for 2 turns.",
    },
    Thunderstorm: {
      damage: 38,
      manaCost: 32,
      description: "Deals 32 damage.",
    },
    "Restoration Incantation": {
      healing: 35,
      manaCost: 25,
      description: "Heals 24 health in battle.",
    },
    "Frost Nova": {
      damage: 24,
      manaCost: 28,
      effects: { stun: 1 },
      description: "Deals 18 damage and chills an enemy still for 1 turn.",
    },
    "Solar Beam": {
      damage: 55,
      manaCost: 45,
      description: "Deals 45 damage.",
    },
    "Life Bloom": {
      healing: 55,
      manaCost: 40,
      description: "Heals 45 health in battle.",
    },
    "Lockio Reducto": {
      description: "Unlocks sealed doors.",
    },
  };

  const FROG_ATTACKS = {
    "Tongue Slap": {
      damage: 10,
      energyCost: 0,
      description: "A free snapping smack from a very serious frog.",
    },
    "Bubble Burp": {
      damage: 16,
      energyCost: 8,
      effects: { burn: 2 },
      description: "Deals 16 damage and leaves the target covered in fizzy bubbles.",
    },
    "Royal Croak": {
      damage: 26,
      energyCost: 14,
      effects: { stun: 1 },
      description: "Deals 26 damage and startles the enemy.",
    },
    "Snack Break": {
      healing: 24,
      energyCost: 12,
      description: "The frog shares emergency snacks and heals 24 health.",
    },
    "Moon Leap": {
      damage: 38,
      energyCost: 22,
      description: "A heavy moonlit frog slam.",
    },
    "Dragonfly Dive": {
      damage: 50,
      energyCost: 30,
      effects: { stun: 1 },
      description: "A late-game dive that deals 50 damage and stuns.",
    },
  };

  const MONSTERS = {
    goblin: {
      health: 32,
      damage: 8,
      attacks: ["punch", "screech", "headbutt"],
    },
    troll: {
      health: 52,
      damage: 12,
      attacks: ["club", "slam", "bite"],
    },
    skeleton: {
      health: 36,
      damage: 15,
      attacks: ["bone club", "bone scare", "bone headbutt"],
    },
    werewolf: {
      health: 68,
      damage: 18,
      attacks: ["claw", "bite", "howl"],
    },
    ogre: {
      health: 86,
      damage: 24,
      attacks: ["big club", "super smash", "stomp"],
    },
    witch: {
      health: 64,
      damage: 16,
      attacks: ["poison", "curse", "hex"],
    },
    vampire: {
      health: 82,
      damage: 21,
      attacks: ["transform into bat", "fangs", "suck blood"],
    },
    "gate rat": {
      health: 22,
      damage: 7,
      attacks: ["rusty nibble", "ankle dash", "tiny ambush"],
    },
    "smoke imp": {
      health: 38,
      damage: 10,
      attacks: ["soot slap", "ember pinch", "smoke cough"],
    },
    "bramble wolf": {
      health: 54,
      damage: 16,
      attacks: ["thorn bite", "vine trip", "bark howl"],
    },
    "treasure mimic": {
      health: 58,
      damage: 18,
      attacks: ["lid snap", "coin spit", "hinge bash"],
    },
    "curse candle": {
      health: 45,
      damage: 17,
      attacks: ["wax splash", "blue flame", "bad birthday wish"],
    },
    "ice goblin": {
      health: 72,
      damage: 20,
      attacks: ["snowball uppercut", "icicle jab", "freezing giggle"],
    },
    "snow bat": {
      health: 48,
      damage: 17,
      attacks: ["frost bite", "wing slap", "sleet shriek"],
    },
    "shadow knight": {
      health: 95,
      damage: 25,
      attacks: ["gloom slash", "helmet bonk", "midnight shove"],
    },
    "receipt wraith": {
      health: 62,
      damage: 19,
      attacks: ["paper cut", "late fee", "ink cloud"],
    },
    "basement bat": {
      health: 58,
      damage: 18,
      attacks: ["cape flutter", "fang tap", "ceiling dive"],
    },
    "sugar golem": {
      health: 105,
      damage: 27,
      attacks: ["frosting fist", "sprinkle storm", "cookie crumble"],
    },
    "rust rat": {
      health: 66,
      damage: 20,
      attacks: ["rust bite", "pipe scramble", "gear squeak"],
    },
    "glass cobra": {
      health: 88,
      damage: 28,
      attacks: ["mirror fang", "shatter hiss", "scale flash"],
    },
    "crystal dragon": {
      health: 145,
      damage: 32,
      attacks: ["rainbow sneeze", "crystal claw", "tail prism"],
    },
    "crown wraith": {
      health: 110,
      damage: 30,
      attacks: ["royal glare", "cold decree", "crown toss"],
    },
    "lord dreadbiscuit": {
      health: 180,
      damage: 36,
      attacks: ["crumb storm", "butter curse", "ego blast"],
    },
    "realmbound dragon": {
      health: 260,
      damage: 42,
      attacks: ["starfire breath", "crownquake", "eclipse wingstorm", "ancient claw"],
    },
    "ashfall pilgrim": {
      health: 96,
      damage: 23,
      attacks: ["ember staff", "cinder prayer", "ash cloak"],
    },
    "lantern jackal": {
      health: 100,
      damage: 24,
      attacks: ["lamp bite", "oil slick", "howling flare"],
    },
    "mossbound knight": {
      health: 108,
      damage: 25,
      attacks: ["root shield", "green blade", "helmet sprout"],
    },
    "mirror moth": {
      health: 92,
      damage: 26,
      attacks: ["glass wing", "reflection flash", "powder dazzle"],
    },
    "ember librarian": {
      health: 112,
      damage: 27,
      attacks: ["burning bookmark", "shushing flame", "index curse"],
    },
    "fogbank siren": {
      health: 116,
      damage: 28,
      attacks: ["mist song", "harbor pull", "whiteout whisper"],
    },
    "tin crown bandit": {
      health: 120,
      damage: 29,
      attacks: ["fake decree", "coin knife", "royal shove"],
    },
    "hollow beekeeper": {
      health: 124,
      damage: 30,
      attacks: ["wax veil", "hive rattle", "stinger rain"],
    },
    "moonlit scarecrow": {
      health: 128,
      damage: 31,
      attacks: ["straw jab", "moon grin", "field hex"],
    },
    "iron acorn brute": {
      health: 136,
      damage: 32,
      attacks: ["oak punch", "iron shell", "squirrel panic"],
    },
    "velvet gargoyle": {
      health: 132,
      damage: 33,
      attacks: ["soft stone claw", "curtain dive", "balcony crash"],
    },
    "clockwork eel": {
      health: 118,
      damage: 34,
      attacks: ["gear bite", "static coil", "spring lash"],
    },
    "glacier monk": {
      health: 140,
      damage: 35,
      attacks: ["frozen palm", "silent avalanche", "ice mantra"],
    },
    "briar drummer": {
      health: 126,
      damage: 36,
      attacks: ["thorn rhythm", "snare root", "wild tempo"],
    },
    "marble banshee": {
      health: 144,
      damage: 37,
      attacks: ["statue shriek", "grave echo", "cracked aria"],
    },
    "thunder yak": {
      health: 150,
      damage: 38,
      attacks: ["storm charge", "horn thunder", "cloud stomp"],
    },
    "paper lantern fiend": {
      health: 122,
      damage: 39,
      attacks: ["paper flame", "festival fright", "string snare"],
    },
    "copper wyvern": {
      health: 156,
      damage: 40,
      attacks: ["coin-scale rake", "green fire", "roof snatch"],
    },
    "old road revenant": {
      health: 148,
      damage: 41,
      attacks: ["mile marker", "dust hand", "forgotten shortcut"],
    },
    "saltwater specter": {
      health: 152,
      damage: 42,
      attacks: ["brine wave", "anchor chill", "shipbell howl"],
    },
    "orchard mimic": {
      health: 160,
      damage: 43,
      attacks: ["apple snap", "branch disguise", "basket bite"],
    },
    "candlewax duelist": {
      health: 146,
      damage: 44,
      attacks: ["wick rapier", "melting feint", "flame salute"],
    },
    "rune-tusk boar": {
      health: 168,
      damage: 45,
      attacks: ["glyph gore", "mud ward", "tusk spell"],
    },
    "midnight tax collector": {
      health: 154,
      damage: 46,
      attacks: ["late fee", "receipt lash", "audit glare"],
    },
    "feathered basilisk": {
      health: 162,
      damage: 47,
      attacks: ["plume stare", "stone chirp", "talon flash"],
    },
    "broken compass spirit": {
      health: 158,
      damage: 48,
      attacks: ["northless pull", "needle spin", "lost road"],
    },
    "jewel wasp swarm": {
      health: 170,
      damage: 49,
      attacks: ["ruby sting", "buzzing crown", "gem cloud"],
    },
    "singing stump": {
      health: 166,
      damage: 50,
      attacks: ["root chorus", "bark note", "splinter solo"],
    },
    "blackglass panther": {
      health: 176,
      damage: 51,
      attacks: ["mirror pounce", "shadow claw", "glass growl"],
    },
    "sunken bell knight": {
      health: 184,
      damage: 52,
      attacks: ["drowned chime", "rusted lance", "undertow step"],
    },
    "nettle witchling": {
      health: 172,
      damage: 53,
      attacks: ["sting charm", "green hex", "thorn wink"],
    },
    "storm cellar troll": {
      health: 190,
      damage: 54,
      attacks: ["barrel throw", "basement boom", "storm burp"],
    },
    "silver mask rogue": {
      health: 178,
      damage: 55,
      attacks: ["mask flash", "quiet dagger", "vanishing bow"],
    },
    "bonewheel racer": {
      health: 182,
      damage: 56,
      attacks: ["wheel crash", "rib spoke", "graveyard lap"],
    },
    "spellbook leech": {
      health: 188,
      damage: 57,
      attacks: ["page drain", "ink bite", "borrowed spell"],
    },
    "cloud anvil giant": {
      health: 208,
      damage: 58,
      attacks: ["sky hammer", "anvil drop", "forge thunder"],
    },
    "porcelain hydra": {
      health: 202,
      damage: 59,
      attacks: ["china fang", "teacup roar", "seven saucers"],
    },
    "scarecrow magistrate": {
      health: 194,
      damage: 60,
      attacks: ["field warrant", "straw verdict", "gavel stick"],
    },
    "obsidian choir": {
      health: 210,
      damage: 61,
      attacks: ["black hymn", "shard harmony", "echo cut"],
    },
    "frostroot colossus": {
      health: 224,
      damage: 62,
      attacks: ["winter branch", "rootquake", "snow crown"],
    },
    "honeycomb horror": {
      health: 198,
      damage: 63,
      attacks: ["sticky maw", "hexagon swarm", "golden sting"],
    },
    "brass cathedral rook": {
      health: 218,
      damage: 64,
      attacks: ["bell tower dive", "brass wing", "sanctuary slam"],
    },
    "map-eating serpent": {
      health: 206,
      damage: 65,
      attacks: ["cartography bite", "folded coil", "legend swallow"],
    },
    "velvet thunderlord": {
      health: 230,
      damage: 66,
      attacks: ["royal thunder", "soft lightning", "storm decree"],
    },
    "eclipse ferryman": {
      health: 220,
      damage: 67,
      attacks: ["black oar", "river shadow", "fare curse"],
    },
    "crownless lion": {
      health: 236,
      damage: 68,
      attacks: ["mane flare", "throne roar", "claw decree"],
    },
    "dream ash phantom": {
      health: 214,
      damage: 69,
      attacks: ["sleep cinder", "nightmare veil", "pillow grave"],
    },
    "seven-key jailer": {
      health: 242,
      damage: 70,
      attacks: ["keyring crush", "cell door slam", "warden glare"],
    },
    "realmquake titan": {
      health: 260,
      damage: 72,
      attacks: ["continent stomp", "fault line", "mountain backhand"],
    },
    "calendar dragon": {
      health: 280,
      damage: 74,
      attacks: ["lost month", "deadline flame", "year-end wing"],
    },
    "realmbound dragon": {
      health: 150,
      damage: 31,
      reward: 90,
      attacks: ["starfire breath", "crownquake", "eclipse wingstorm", "ancient claw"],
    },
  };

  const LONG_ROAD_ENEMIES = [
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
  ];

  const STORY_BALANCE_OVERRIDES = {
      "gate rat": {
          "health": 22,
          "damage": 5,
          "reward": 8
      },
      "goblin": {
          "health": 30,
          "damage": 6,
          "reward": 9
      },
      "troll": {
          "health": 46,
          "damage": 8,
          "reward": 12
      },
      "smoke imp": {
          "health": 32,
          "damage": 7,
          "reward": 10
      },
      "skeleton": {
          "health": 34,
          "damage": 8,
          "reward": 10
      },
      "bramble wolf": {
          "health": 44,
          "damage": 8,
          "reward": 11
      },
      "werewolf": {
          "health": 54,
          "damage": 9,
          "reward": 13
      },
      "treasure mimic": {
          "health": 48,
          "damage": 9,
          "reward": 14
      },
      "ogre": {
          "health": 68,
          "damage": 11,
          "reward": 16
      },
      "witch": {
          "health": 58,
          "damage": 10,
          "reward": 15
      },
      "curse candle": {
          "health": 40,
          "damage": 8,
          "reward": 11
      },
      "ice goblin": {
          "health": 60,
          "damage": 10,
          "reward": 15
      },
      "snow bat": {
          "health": 42,
          "damage": 8,
          "reward": 11
      },
      "shadow knight": {
          "health": 76,
          "damage": 12,
          "reward": 18
      },
      "receipt wraith": {
          "health": 52,
          "damage": 9,
          "reward": 13
      },
      "vampire": {
          "health": 70,
          "damage": 12,
          "reward": 18
      },
      "basement bat": {
          "health": 48,
          "damage": 9,
          "reward": 12
      },
      "sugar golem": {
          "health": 86,
          "damage": 13,
          "reward": 20
      },
      "rust rat": {
          "health": 54,
          "damage": 9,
          "reward": 13
      },
      "glass cobra": {
          "health": 72,
          "damage": 12,
          "reward": 18
      },
      "crystal dragon": {
          "health": 108,
          "damage": 14,
          "reward": 30
      },
      "crown wraith": {
          "health": 88,
          "damage": 13,
          "reward": 24
      },
      "lord dreadbiscuit": {
          "health": 120,
          "damage": 16,
          "reward": 35
      },
      "realmbound dragon": {
          "health": 150,
          "damage": 18,
          "reward": 60
      }
  };
  for (const [name, stats] of Object.entries(STORY_BALANCE_OVERRIDES)) {
    Object.assign(MONSTERS[name], stats);
  }
  LONG_ROAD_ENEMIES.forEach((name, zeroIndex) => {
    const index = zeroIndex + 1;
    Object.assign(MONSTERS[name], {
      health: 48 + Math.round(index * 1.1),
      damage: 6 + Math.floor((index - 1) / 12),
      reward: 10 + Math.floor((index - 1) / 5),
    });
  });
  for (const monster of Object.values(MONSTERS)) {
    if (monster.reward === undefined) monster.reward = Math.max(8, Math.min(30, Math.round(monster.health / 7)));
  }

  const LOOT_DROPS = [
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
  ];

  const SELLABLE_LOOT = new Set([
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
  ]);

  class GameOver extends Error {}

  function clone(value) {
    return JSON.parse(JSON.stringify(value));
  }

  function randomInt(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
  }

  function randomChoice(values) {
    return values[Math.floor(Math.random() * values.length)];
  }

  function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  function normalizeChoice(value) {
    return value.trim().toLowerCase().split(/\s+/).filter(Boolean).join(" ");
  }

  function cleanInput(value) {
    return value.trim().split(/\s+/).filter(Boolean).join(" ");
  }

  function statMeter(current, maximum, width = 16) {
    if (maximum <= 0) {
      return `[${"-".repeat(width)}]`;
    }
    const capped = Math.max(0, Math.min(current, maximum));
    const filled = Math.round((width * capped) / maximum);
    return `[${"#".repeat(filled)}${"-".repeat(width - filled)}]`;
  }

  function sanitizeSlotName(value) {
    const cleaned = value.replace(/[^A-Za-z0-9_. -]+/g, "").trim().replace(/^[. ]+|[. ]+$/g, "");
    return cleaned || "adventure-save";
  }

  function stripSaveSuffix(value) {
    return value.endsWith(SAVE_SUFFIX) ? value.slice(0, -SAVE_SUFFIX.length) : value;
  }

  function defaultSaveStem(prefix = "adventure") {
    const now = new Date();
    const stamp = now.toISOString().replace(/[-:]/g, "").replace(/\..+/, "").replace("T", "_");
    return `${prefix}_${stamp}`;
  }

  function pathFromPlayerInput(value, fallbackStem = null) {
    const cleaned = value.trim();
    if (!cleaned) {
      return fallbackStem || defaultSaveStem();
    }
    const lastPart = cleaned.split(/[\\/]/).pop() || cleaned;
    return stripSaveSuffix(sanitizeSlotName(lastPart));
  }

  function formatSavedAt(value) {
    return value || "unknown time";
  }

  function safeJsonParse(value, fallback) {
    try {
      return JSON.parse(value);
    } catch {
      return fallback;
    }
  }

  class Terminal {
    constructor(root, output) {
      this.root = root;
      this.output = output;
      this.activePrompt = null;
    }

    scrollToBottom() {
      this.root.scrollTop = this.root.scrollHeight;
    }

    colorClassForText(text) {
      const lowered = text.toLowerCase();
      if (text.startsWith("$") || lowered.includes("whoop nickel")) return "yellow";
      if (lowered.includes("game over") || lowered.includes("damage") || lowered.includes("attacks")) return "red";
      if (/^\d+\/\d+$/.test(text) || lowered.includes("health")) return "red";
      if (lowered.includes("the end") || text.startsWith("===")) return "yellow";
      if (lowered.includes("good job") || lowered.includes("you learned") || lowered.includes("you bought") || lowered.includes("cloud synced")) return "green";
      if (lowered.startsWith("credits:")) return "dim";
      if (text.startsWith('"') && text.endsWith('"')) return "cyan";
      return "";
    }

    colorizeText(value) {
      const text = String(value);
      const pattern = /(\$-?\d+|\b\d+\s+Whoop Nickels?\b|\b\d+\/\d+\b|\b\d+\s+(?:damage|health)\b|GAME OVER|THE END|=== [^=\n]+ ===|Credits:[^\n]*|Good job,[^\n]*|You learned[^\n]*|You bought[^\n]*|Cloud synced|".*?")/g;
      const parts = [];
      let lastIndex = 0;
      for (const match of text.matchAll(pattern)) {
        if (match.index > lastIndex) {
          parts.push(text.slice(lastIndex, match.index));
        }
        const token = match[0];
        const className = this.colorClassForText(token);
        parts.push(className ? { text: token, className } : token);
        lastIndex = match.index + token.length;
      }
      if (lastIndex < text.length) {
        parts.push(text.slice(lastIndex));
      }
      return parts.length ? parts : text;
    }

    appendLine(parts = "") {
      const line = document.createElement("div");
      line.className = "terminal-line";
      this.appendParts(line, Array.isArray(parts) ? parts : this.colorizeText(parts));
      this.output.append(line);
      this.scrollToBottom();
      return line;
    }

    appendLogo() {
      const wrapper = document.createElement("pre");
      wrapper.className = "terminal-logo";
      wrapper.setAttribute("aria-label", "Realmbound ASCII logo");
      wrapper.textContent = [
        " ____            _           _                           _",
        "|  _ \\ ___  __ _| |_ __ ___ | |__   ___  _   _ _ __   __| |",
        "| |_) / _ \\/ _` | | '_ ` _ \\| '_ \\ / _ \\| | | | '_ \\ / _` |",
        "|  _ <  __/ (_| | | | | | | | |_) | (_) | |_| | | | | (_| |",
        "|_| \\_\\___|\\__,_|_|_| |_| |_|_.__/ \\___/ \\__,_|_| |_|\\__,_|",
        "",
      ].join("\n");
      this.output.append(wrapper);
      this.scrollToBottom();
      return wrapper;
    }

    appendClickableLine(parts, submitValue, disabled = false) {
      const line = this.appendLine(parts);
      if (disabled) {
        line.classList.add("terminal-choice-disabled");
        line.setAttribute("aria-disabled", "true");
        return line;
      }

      line.classList.add("terminal-choice");
      line.setAttribute("role", "button");
      line.setAttribute("tabindex", "0");
      line.addEventListener("click", () => this.submitActivePrompt(submitValue));
      line.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          this.submitActivePrompt(submitValue);
        }
      });
      return line;
    }

    appendParts(parent, parts) {
      if (!Array.isArray(parts)) {
        parent.append(document.createTextNode(String(parts)));
        return;
      }

      for (const part of parts) {
        if (typeof part === "string") {
          parent.append(document.createTextNode(part));
          continue;
        }
        const span = document.createElement("span");
        span.textContent = part.text;
        if (part.className) {
          span.className = part.className;
        }
        parent.append(span);
      }
    }

    appendPromptClickChoices(parent, choices) {
      if (!choices || !choices.length) {
        return;
      }

      const choicesWrap = document.createElement("span");
      choicesWrap.className = "terminal-inline-choices";
      for (const choice of choices) {
        const button = document.createElement("span");
        button.className = "terminal-inline-choice";
        button.textContent = choice.label;
        button.setAttribute("role", "button");
        button.setAttribute("tabindex", "0");
        button.addEventListener("click", () => this.submitActivePrompt(choice.value));
        button.addEventListener("keydown", (event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            this.submitActivePrompt(choice.value);
          }
        });
        choicesWrap.append(document.createTextNode(" ["));
        choicesWrap.append(button);
        choicesWrap.append(document.createTextNode("]"));
      }
      choicesWrap.append(document.createTextNode(" "));
      parent.append(choicesWrap);
    }

    ask(prompt, options = {}) {
      return new Promise((resolve) => {
        const wrapper = document.createElement("div");
        wrapper.className = "terminal-input-line";

        const promptSpan = document.createElement("span");
        promptSpan.className = "terminal-prompt";
        promptSpan.textContent = prompt;
        wrapper.append(promptSpan);
        this.appendPromptClickChoices(wrapper, options.clickChoices);

        const form = document.createElement("form");
        form.className = "terminal-input-form";

        const input = document.createElement("input");
        input.className = "terminal-input";
        input.type = options.password ? "password" : "text";
        input.autocomplete = "off";
        input.autocapitalize = "none";
        input.spellcheck = false;
        form.append(input);
        wrapper.append(form);

        this.output.append(wrapper);
        this.scrollToBottom();
        input.focus();
        this.activePrompt = { input, form };

        form.addEventListener("submit", (event) => {
          event.preventDefault();
          const raw = input.value;
          this.activePrompt = null;
          const finalLine = document.createElement("div");
          finalLine.className = "terminal-line";
          finalLine.append(document.createTextNode(prompt));
          finalLine.append(document.createTextNode(options.password && raw ? "********" : raw));
          wrapper.replaceWith(finalLine);
          this.scrollToBottom();
          resolve(cleanInput(raw));
        });
      });
    }

    submitActivePrompt(value) {
      if (!this.activePrompt) {
        return;
      }
      this.activePrompt.input.value = value;
      this.activePrompt.form.requestSubmit();
    }

    clear() {
      this.output.replaceChildren();
      this.activePrompt = null;
      this.scrollToBottom();
    }
  }

  class AdventureGame {
    constructor(terminal) {
      this.terminal = terminal;
      this.activeState = null;
      this.autosaveRunning = false;
      this.outputQueue = Promise.resolve();
      this.quickMenuRunning = false;
      document.addEventListener("keydown", (event) => {
        if (event.key !== "~" || !this.activeState || this.quickMenuRunning) {
          return;
        }
        if (!this.terminal.activePrompt) {
          return;
        }
        event.preventDefault();
        this.terminal.submitActivePrompt("~");
      });
    }

    async start() {
      this.terminal.appendLogo();
      let mode = "menu";

      while (true) {
        try {
          if (mode === "restart") {
            await this.runStory(this.newState());
          } else {
            await this.mainMenu();
          }
          return;
        } catch (error) {
          if (!(error instanceof GameOver)) {
            this.say(`\nUnexpected web-port error: ${error.message || error}`, "quick");
            throw error;
          }

          const choice = await this.restartMenu();
          if (choice === "restart") {
            this.terminal.clear();
            this.terminal.appendLogo();
            mode = "restart";
            continue;
          }
          if (choice === "main") {
            this.terminal.clear();
            this.terminal.appendLogo();
            mode = "menu";
            continue;
          }
        }
      }
    }

    say(message) {
      this.queueOutput(() => this.terminal.appendLine(message));
    }

    sayParts(parts) {
      this.queueOutput(() => this.terminal.appendLine(parts));
    }

    sayClickableParts(parts, submitValue, disabled = false) {
      this.queueOutput(() => this.terminal.appendClickableLine(parts, submitValue, disabled));
    }

    async ask(prompt, options = {}) {
      while (true) {
        await this.flushOutput();
        const value = await this.terminal.ask(prompt, options);
        if (normalizeChoice(value) === "~") {
          await this.quickMenu();
          continue;
        }
        return value;
      }
    }

    queueOutput(writeLine) {
      this.outputQueue = this.outputQueue.then(async () => {
        writeLine();
        this.autosaveAfterOutput();
        await sleep(OUTPUT_DELAY_MS);
      });
      return this.outputQueue;
    }

    async flushOutput() {
      await this.outputQueue;
    }

    async quickMenu() {
      if (!this.activeState) {
        this.say("\nNo stats are available right now.");
        await this.flushOutput();
        return;
      }
      if (this.quickMenuRunning) {
        this.say("\nYou are already in the ~ menu.");
        await this.flushOutput();
        return;
      }
      this.quickMenuRunning = true;
      try {
        const choice = await this.chooseMenu("~ Menu", [
          { key: "1", label: "Player Stats", value: "stats", aliases: ["stats", "status"] },
          { key: "2", label: "Back", value: "back", aliases: ["back", "return", "cancel"] },
        ], {
          prompt: "~ menu choice: ",
          subtitle: "Opened with ~.",
        });
        if (choice === "stats") {
          this.printStats(this.activeState.player);
        }
      } finally {
        this.quickMenuRunning = false;
      }
    }

    divider(title) {
      this.sayParts(["\n", { text: `=== ${title} ===`, className: "yellow" }]);
    }

    moneyParts(amount) {
      const label = amount === 1 ? "Whoop Nickel" : "Whoop Nickels";
      return [{ text: `${amount} ${label}`, className: "yellow" }];
    }

    createPlayer() {
      return {
        name: "Adventurer",
        money: 20,
        health: 120,
        healthMax: 120,
        mana: 120,
        manaMax: 120,
        armor: 0,
        weaponDamage: 0,
        extraDamage: 0,
        frogMode: false,
        frogPower: 0,
        frogEnergy: 0,
        frogEnergyMax: 0,
        roadProgress: 0,
        backpack: ["Small Health Potion"],
        spells: [],
        frogAttacks: [],
      };
    }

    addSpell(player, spellName) {
      if (!player.spells.includes(spellName)) {
        player.spells.push(spellName);
      }
    }

    addFrogAttack(player, attackName) {
      if (!player.frogAttacks.includes(attackName)) {
        player.frogAttacks.push(attackName);
      }
    }

    activateFrogPartner(player) {
      player.frogMode = true;
      player.frogPower = Math.max(player.frogPower || 0, 4);
      player.frogEnergyMax = Math.max(player.frogEnergyMax || 0, 25);
      player.frogEnergy = Math.max(player.frogEnergy || 0, player.frogEnergyMax);
      if (!player.backpack.includes("Magical Chocolate Frog")) {
        player.backpack.push("Magical Chocolate Frog");
      }
      this.addFrogAttack(player, "Tongue Slap");
    }

    createShopStock() {
      return {
        "Arcane Blast": true,
        Thunderstorm: true,
        "Restoration Incantation": true,
        "Frost Nova": true,
        "Solar Beam": true,
        "Life Bloom": true,
        "Glorious Helmet": true,
        "Mage Boots": true,
        "Crystal Sword": true,
        "Phoenix Feather": true,
        "Dragon Scale Shield": true,
        "Star Cloak": true,
        "Croak Fu Primer": true,
        "Bubble Burp Codex": true,
        "Royal Croak Sheet Music": true,
        "Snack Break Cookbook": true,
        "Moon Leap Manual": true,
        "Golden Fly Protein": true,
      "Dragonfly Tactics": true,
      "Clockwork Compass": true,
      "Old Bell Manual": true,
      "Well Whisper Notes": true,
    };
    }

    newState() {
      return {
        player: this.createPlayer(),
        shop_stock: this.createShopStock(),
        next_scene: SCENE_ORDER[0],
      };
    }

    sceneTitle(sceneId) {
      return SCENE_TITLES[sceneId] || sceneId.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
    }

    nextScene(sceneId) {
      const index = SCENE_ORDER.indexOf(sceneId);
      return index + 1 >= SCENE_ORDER.length ? FINISHED_SCENE : SCENE_ORDER[index + 1];
    }

    printStats(player) {
      this.divider("Player Stats");
      this.sayParts(["Whoop Nickels: ", ...this.moneyParts(player.money)]);
      this.sayParts([
        "Health: ",
        { text: `${statMeter(player.health, player.healthMax)} ${player.health}/${player.healthMax}`, className: "red" },
      ]);
      this.sayParts([
        "Mana: ",
        { text: `${statMeter(player.mana, player.manaMax)} ${player.mana}/${player.manaMax}`, className: "blue" },
      ]);
      this.sayParts(["Armor: ", { text: String(player.armor), className: "cyan" }]);
      this.sayParts(["Weapon Damage: ", { text: `+${player.weaponDamage || 0}`, className: "yellow" }]);
      this.sayParts(["Spell Damage: ", { text: `+${player.extraDamage}`, className: "magenta" }]);
      if (player.frogMode) {
        this.sayParts([
          "Frog Energy: ",
          {
            text: `${statMeter(player.frogEnergy, player.frogEnergyMax)} ${player.frogEnergy}/${player.frogEnergyMax}`,
            className: "green",
          },
        ]);
        this.sayParts(["Frog Power: ", { text: `+${player.frogPower || 0}`, className: "green" }]);
      }

      const spells = player.spells.length ? player.spells.join(", ") : "None";
      this.sayParts(["Spells: ", { text: spells, className: "magenta" }]);
      if (player.frogMode) {
        const frogAttacks = player.frogAttacks.length ? player.frogAttacks.join(", ") : "None";
        this.sayParts(["Frog Attacks: ", { text: frogAttacks, className: "green" }]);
      }

      if (player.backpack.length) {
        const counts = new Map();
        for (const item of player.backpack) {
          counts.set(item, (counts.get(item) || 0) + 1);
        }
        const items = [...counts.entries()]
          .sort(([left], [right]) => left.localeCompare(right))
          .map(([item, count]) => (count > 1 ? `${item} x${count}` : item));
        this.sayParts(["Items: ", { text: `${items.join(", ")}\n`, className: "green" }]);
      } else {
        this.sayParts(["Items: ", { text: "None\n", className: "green" }]);
      }
    }

    optionInputs(option) {
      const inputs = [option.key, option.label, ...(option.aliases || [])];
      return new Set(inputs.filter(Boolean).map(normalizeChoice));
    }

    async chooseMenu(title, options, config = {}) {
      const prompt = config.prompt || "Choose: ";
      const invalid = config.invalid || "\nPlease choose one of the listed options.";

      while (true) {
        this.divider(title);
        if (config.subtitle) {
          Array.isArray(config.subtitle) ? this.sayParts(config.subtitle) : this.say(config.subtitle);
        }

        for (const option of options) {
          const parts = [
            { text: option.key, className: option.enabled === false ? "dim" : "cyan" },
            ". ",
            { text: option.label, className: option.enabled === false ? "dim" : "green" },
          ];
          if (option.detail) {
            parts.push({ text: " - ", className: "dim" });
            if (Array.isArray(option.detail)) {
              parts.push(...option.detail);
            } else {
              parts.push({ text: option.detail, className: "white" });
            }
          }
          if (option.status) {
            parts.push(" (", { text: option.status, className: "yellow" }, ")");
          }
          this.sayClickableParts(parts, option.key, option.enabled === false);
        }

        const choice = normalizeChoice(await this.ask(prompt));
        for (const option of options) {
          if (this.optionInputs(option).has(choice)) {
            if (option.enabled !== false) {
              return option.value;
            }
            this.say(`\n${option.label} is not available right now.`);
            break;
          }
        }
        if (!options.some((option) => this.optionInputs(option).has(choice))) {
          this.say(invalid);
        }
      }
    }

    async askChoice(prompt, choices, invalid) {
      const normalizedChoices = Object.entries(choices).map(([value, aliases]) => [
        value,
        new Set(aliases.map(normalizeChoice)),
      ]);
      const clickChoices = Object.entries(choices).map(([value]) => ({
        label: value,
        value,
      }));

      while (true) {
        const choice = normalizeChoice(await this.ask(prompt, { clickChoices }));
        for (const [value, aliases] of normalizedChoices) {
          if (aliases.has(choice)) {
            return value;
          }
        }
        this.say(invalid);
      }
    }

    yesNo(prompt) {
      return this.askChoice(prompt, {
        yes: ["yes", "y", "1"],
        no: ["no", "n", "2"],
      }, "\nPlease answer yes or no.");
    }

    fightOrRun(prompt = "\nDo you fight or run? ") {
      return this.askChoice(prompt, {
        fight: ["fight", "f", "1"],
        run: ["run", "r", "2"],
      }, "\nPlease choose fight or run.");
    }

    chooseLeftOrRight(prompt) {
      return this.askChoice(prompt, {
        left: ["left", "l", "1"],
        right: ["right", "r", "2"],
      }, "\nPlease choose left or right.");
    }

    restartMenu() {
      return this.chooseMenu("Game Over", [
        { key: "1", label: "Restart", value: "restart", aliases: ["restart", "r", "new game", "new"] },
        { key: "2", label: "Main Menu", value: "main", aliases: ["main", "menu", "m"] },
      ], {
        prompt: "Game over choice: ",
      });
    }

    normalizeState(rawState) {
      if (!rawState || typeof rawState !== "object") {
        throw new Error("The save does not contain game state.");
      }
      const rawPlayer = rawState.player;
      if (!rawPlayer || typeof rawPlayer !== "object") {
        throw new Error("The save does not contain a valid player.");
      }

      const player = this.createPlayer();
      const rawName = rawPlayer.name ?? player.name;
      if (typeof rawName !== "string") {
        throw new Error("Save field 'name' is not valid text.");
      }
      player.name = cleanInput(rawName) || "Adventurer";

      for (const key of [
        "money",
        "health",
        "healthMax",
        "mana",
        "manaMax",
        "armor",
        "weaponDamage",
        "extraDamage",
        "frogPower",
        "frogEnergy",
        "frogEnergyMax",
        "roadProgress",
      ]) {
        const value = rawPlayer[key] ?? player[key];
        if (!Number.isInteger(value)) {
          throw new Error(`Save field '${key}' is not a valid number.`);
        }
        player[key] = value;
      }
      player.roadProgress = Math.max(0, Math.min(player.roadProgress, LONG_ROAD_ENEMIES.length));
      const frogMode = rawPlayer.frogMode ?? player.frogMode;
      if (typeof frogMode !== "boolean") {
        throw new Error("Save field 'frogMode' is not a valid true/false value.");
      }
      player.frogMode = frogMode;

      for (const key of ["backpack", "spells", "frogAttacks"]) {
        const value = rawPlayer[key] ?? [];
        if (!Array.isArray(value) || value.some((item) => typeof item !== "string")) {
          throw new Error(`Save field '${key}' is not a valid list.`);
        }
        player[key] = [...value];
      }
      if (!player.backpack.includes("Magic Wand") && player.backpack.includes("Magical Chocolate Frog")) {
        this.activateFrogPartner(player);
      }
      if (player.frogMode && !player.frogAttacks.length) {
        this.addFrogAttack(player, "Tongue Slap");
      }

      const shopStock = this.createShopStock();
      const rawStock = rawState.shop_stock || {};
      if (typeof rawStock !== "object" || Array.isArray(rawStock)) {
        throw new Error("The save does not contain valid shop stock.");
      }
      for (const itemName of Object.keys(shopStock)) {
        const value = rawStock[itemName] ?? shopStock[itemName];
        if (typeof value !== "boolean") {
          throw new Error(`Save field '${itemName}' is not valid shop stock.`);
        }
        shopStock[itemName] = value;
      }

      const nextScene = rawState.next_scene;
      if (!SCENE_ORDER.includes(nextScene) && nextScene !== FINISHED_SCENE) {
        throw new Error("The save points to an unknown story checkpoint.");
      }

      return { player, shop_stock: shopStock, next_scene: nextScene };
    }

    loadStateFromPayload(payload) {
      if (!payload || typeof payload !== "object") {
        throw new Error("The save payload is not valid.");
      }
      if (payload.game !== "Adventure Game") {
        throw new Error("This save belongs to a different game.");
      }
      return this.normalizeState(payload.state);
    }

    makeSavePayload(state) {
      return {
        game: "Adventure Game",
        format_version: SAVE_FORMAT_VERSION,
        saved_at: new Date().toISOString().replace(/\.\d{3}Z$/, "+00:00"),
        state: clone(state),
      };
    }

    makeSaveText(state) {
      return JSON.stringify(this.makeSavePayload(state));
    }

    readSaveSlots() {
      const parsed = safeJsonParse(localStorage.getItem(SAVE_STORAGE_KEY), {});
      return parsed && typeof parsed === "object" && !Array.isArray(parsed) ? parsed : {};
    }

    writeSaveSlots(slots) {
      localStorage.setItem(SAVE_STORAGE_KEY, JSON.stringify(slots));
    }

    writeSaveText(saveText, stem) {
      const payload = this.loadStateFromPayload(JSON.parse(saveText));
      const slots = this.readSaveSlots();
      const safeStem = sanitizeSlotName(stem);
      slots[safeStem] = {
        save_data: saveText,
        saved_at: payload.saved_at,
        updated_at: Date.now(),
      };
      this.writeSaveSlots(slots);
      return `saves/${safeStem}${SAVE_SUFFIX}`;
    }

    loadSaveText(stem) {
      const slots = this.readSaveSlots();
      const slot = slots[sanitizeSlotName(stem)];
      if (!slot || typeof slot.save_data !== "string") {
        throw new Error(`No browser save exists at saves/${sanitizeSlotName(stem)}${SAVE_SUFFIX}.`);
      }
      return slot.save_data;
    }

    listSaveFiles() {
      const slots = this.readSaveSlots();
      return Object.entries(slots)
        .filter(([, slot]) => slot && typeof slot.save_data === "string")
        .sort(([, left], [, right]) => (right.updated_at || 0) - (left.updated_at || 0))
        .map(([stem, slot]) => ({ stem, name: `${stem}${SAVE_SUFFIX}`, slot }));
    }

    saveDetail(stem, slot) {
      try {
        const payload = JSON.parse(slot.save_data);
        const state = this.loadStateFromPayload(payload);
        const label = state.player.money === 1 ? "Whoop Nickel" : "Whoop Nickels";
        return `${this.sceneTitle(state.next_scene)}, ${state.player.money} ${label}, saved ${formatSavedAt(payload.saved_at)}`;
      } catch {
        return "unreadable or tampered";
      }
    }

    async saveStateInteractive(state) {
      const suggestedStem = defaultSaveStem();
      const typedPath = await this.ask(`\nSave name or path [${suggestedStem}${SAVE_SUFFIX}]: `);
      const stem = typedPath ? pathFromPlayerInput(typedPath) : suggestedStem;
      const saveText = this.makeSaveText(state);

      try {
        const finalPath = this.writeSaveText(saveText, stem);
        this.say(`\nSaved encrypted checkpoint to ${finalPath}.`);
      } catch (error) {
        this.say(`\nSave failed: ${error.message || error}`);
        return;
      }

      if (this.isSignedIn()) {
        try {
          await this.uploadSave(stem, saveText);
          this.say(`\nSynced cloud save slot '${stem}'.`);
        } catch (error) {
          this.say(`\nCloud sync failed: ${error.message || error}`);
        }
      }
    }

    async loadStateInteractive() {
      while (true) {
        const saveFiles = this.listSaveFiles();
        const options = [];
        saveFiles.slice(0, 9).forEach((saveFile, index) => {
          options.push({
            key: String(index + 1),
            label: saveFile.name,
            value: saveFile.stem,
            detail: this.saveDetail(saveFile.stem, saveFile.slot),
            aliases: [saveFile.stem, saveFile.name],
          });
        });

        const customKey = String(options.length + 1);
        options.push({
          key: customKey,
          label: "Load other file",
          value: "custom",
          detail: "type a .tasave path",
          aliases: ["custom", "other", "file", "path"],
        });
        options.push({
          key: String(options.length + 1),
          label: "Back",
          value: "back",
          aliases: ["back", "cancel"],
        });

        const choice = await this.chooseMenu("Load Game", options, {
          prompt: "Load choice: ",
          subtitle: "Encrypted save files end in .tasave.",
        });

        if (choice === "back") {
          return null;
        }

        let stem = choice;
        if (choice === "custom") {
          const typedPath = await this.ask("\nSave file path: ");
          if (!typedPath) {
            this.say("\nNo file selected.");
            continue;
          }
          stem = pathFromPlayerInput(typedPath);
        }

        try {
          const saveText = this.loadSaveText(stem);
          const state = this.loadStateFromPayload(JSON.parse(saveText));
          this.say(`\nLoaded save from saves/${sanitizeSlotName(stem)}${SAVE_SUFFIX}.`);
          return state;
        } catch (error) {
          this.say(`\nLoad failed: ${error.message || error}`);
        }
      }
    }

    autosaveAfterOutput() {
      if (!this.activeState || this.autosaveRunning) {
        return;
      }
      this.autosaveRunning = true;
      try {
        this.writeSaveText(this.makeSaveText(this.activeState), "autosave");
      } catch {
        // Silent autosave should never interrupt gameplay.
      } finally {
        this.autosaveRunning = false;
      }
    }

    async autosaveState(state, syncCloud = true) {
      const saveText = this.makeSaveText(state);
      try {
        this.writeSaveText(saveText, "autosave");
      } catch {
        return [false, false];
      }

      let cloudSynced = false;
      if (syncCloud && this.isSignedIn()) {
        try {
          await this.uploadSave("autosave", saveText, 2000);
          cloudSynced = true;
        } catch {
          cloudSynced = false;
        }
      }
      return [true, cloudSynced];
    }

    loadCloudSettings() {
      const parsed = safeJsonParse(localStorage.getItem(CLOUD_STORAGE_KEY), {});
      return parsed && typeof parsed === "object" && !Array.isArray(parsed) ? parsed : {};
    }

    saveCloudSettings(settings) {
      localStorage.setItem(CLOUD_STORAGE_KEY, JSON.stringify(settings));
    }

    normalizeApiUrl(apiUrl) {
      let cleaned = apiUrl.trim().split(/\s+/).join(" ");
      if (!cleaned) {
        throw new Error("Cloud save API URL cannot be empty.");
      }
      if (!cleaned.includes("://")) {
        cleaned = `https://${cleaned}`;
      }
      const parsed = new URL(cleaned);
      if (!["http:", "https:"].includes(parsed.protocol) || !parsed.host) {
        throw new Error("Cloud save API URL must look like https://example.com/adventure-api.");
      }
      return cleaned.replace(/\/+$/, "");
    }

    currentApiUrl() {
      return DEFAULT_API_URL;
    }

    currentUsername() {
      return (this.loadCloudSettings().username || "").trim();
    }

    isSignedIn() {
      const settings = this.loadCloudSettings();
      return Boolean(settings.token && settings.username);
    }

    signOut() {
      const settings = this.loadCloudSettings();
      delete settings.token;
      delete settings.username;
      this.saveCloudSettings(settings);
    }

    normalizeSlotName(value) {
      return sanitizeSlotName(value).slice(0, 64).trim() || "autosave";
    }

    endpoint(apiUrl, action) {
      const url = new URL(apiUrl);
      if (!url.pathname.endsWith(".php")) {
        url.pathname = `${url.pathname.replace(/\/+$/, "")}/index.php`;
      }
      url.searchParams.set("action", action);
      return url.toString();
    }

    async requestCloud(action, data = {}, token = null, timeout = 6000) {
      const apiUrl = this.normalizeApiUrl(this.currentApiUrl());
      const payload = { ...data, action };
      const headers = {
        "Content-Type": "application/json",
        Accept: "application/json",
      };
      if (token) {
        headers.Authorization = `Bearer ${token}`;
        payload.token = token;
      }

      const controller = new AbortController();
      const timeoutId = window.setTimeout(() => controller.abort(), timeout);
      try {
        const response = await fetch(this.endpoint(apiUrl, action), {
          method: "POST",
          headers,
          body: JSON.stringify(payload),
          signal: controller.signal,
        });
        const body = await response.text();
        let result;
        try {
          result = JSON.parse(body);
        } catch {
          throw new Error("Cloud save server returned a response the game could not read.");
        }
        if (!response.ok || !result.ok) {
          throw new Error(result.error || result.message || `Cloud save server returned HTTP ${response.status}.`);
        }
        return result;
      } catch (error) {
        if (error.name === "AbortError") {
          throw new Error("Cloud save server is unavailable. Local saves still work.");
        }
        throw new Error(error.message || "Cloud save server is unavailable. Local saves still work.");
      } finally {
        window.clearTimeout(timeoutId);
      }
    }

    sessionToken() {
      const token = (this.loadCloudSettings().token || "").trim();
      if (!token) {
        throw new Error("You are not signed in to cloud saves.");
      }
      return token;
    }

    saveSession(username, token) {
      this.saveCloudSettings({ ...this.loadCloudSettings(), username, token });
    }

    async register(username, password) {
      const response = await this.requestCloud("register", { username, password });
      this.saveSession(response.username, response.token);
      return response;
    }

    async login(username, password) {
      const response = await this.requestCloud("login", { username, password });
      this.saveSession(response.username, response.token);
      return response;
    }

    async listSaves() {
      const response = await this.requestCloud("list", {}, this.sessionToken());
      return response.saves || [];
    }

    async uploadSave(slotName, saveText, timeout = 6000) {
      return this.requestCloud(
        "upload",
        { slot_name: this.normalizeSlotName(slotName), save_data: saveText },
        this.sessionToken(),
        timeout,
      );
    }

    async downloadSave(slotName) {
      const response = await this.requestCloud(
        "download",
        { slot_name: this.normalizeSlotName(slotName) },
        this.sessionToken(),
      );
      if (typeof response.save_data !== "string" || !response.save_data) {
        throw new Error("Cloud save server did not return save data.");
      }
      return response;
    }

    cloudStatus() {
      let apiPart;
      try {
        apiPart = `API: ${this.currentApiUrl()}`;
      } catch (error) {
        apiPart = `API URL problem: ${error.message || error}`;
      }

      const accountPart = this.isSignedIn() ? `Signed in: ${this.currentUsername()}` : "Not signed in";
      return `${apiPart} | ${accountPart}`;
    }

    async cloudRegister() {
      const username = await this.ask("\nChoose cloud username: ");
      if (!username) {
        this.say("\nNo username entered.");
        return;
      }
      const password = await this.ask("Choose cloud password: ", { password: true });
      const confirm = await this.ask("Confirm cloud password: ", { password: true });
      if (password !== confirm) {
        this.say("\nPasswords did not match.");
        return;
      }

      try {
        await this.register(username, password);
        this.say(`\nSigned in to cloud saves as ${this.currentUsername()}.`);
      } catch (error) {
        this.say(`\nCloud registration failed: ${error.message || error}`);
      }
    }

    async cloudLogin() {
      const username = await this.ask("\nCloud username: ");
      if (!username) {
        this.say("\nNo username entered.");
        return;
      }
      const password = await this.ask("Cloud password: ", { password: true });
      try {
        await this.login(username, password);
        this.say(`\nSigned in to cloud saves as ${this.currentUsername()}.`);
      } catch (error) {
        this.say(`\nCloud sign-in failed: ${error.message || error}`);
      }
    }

    async cloudUploadCurrent(state) {
      if (state === null) {
        this.say("\nStart or load a game before uploading a cloud save.");
        return;
      }
      if (!this.isSignedIn()) {
        this.say("\nSign in before uploading cloud saves.");
        return;
      }

      const typedSlot = await this.ask("\nCloud save slot [autosave]: ");
      const slotName = this.normalizeSlotName(typedSlot || "autosave");
      const saveText = this.makeSaveText(state);
      try {
        await this.uploadSave(slotName, saveText);
        this.say(`\nUploaded cloud save slot '${slotName}'.`);
      } catch (error) {
        this.say(`\nCloud upload failed: ${error.message || error}`);
      }
    }

    async cloudLoadInteractive() {
      if (!this.isSignedIn()) {
        this.say("\nSign in before loading cloud saves.");
        return null;
      }

      let cloudSlots;
      try {
        cloudSlots = await this.listSaves();
      } catch (error) {
        this.say(`\nCloud saves are unavailable: ${error.message || error}`);
        return null;
      }

      const options = [];
      cloudSlots.slice(0, 9).forEach((cloudSlot, index) => {
        const slotName = cloudSlot.slot_name || "";
        if (!slotName) {
          return;
        }
        options.push({
          key: String(index + 1),
          label: slotName,
          value: slotName,
          detail: `updated ${cloudSlot.updated_at || "unknown time"}`,
          aliases: [slotName],
        });
      });

      if (!options.length) {
        this.say("\nNo cloud saves found for this account.");
        return null;
      }

      options.push({
        key: String(options.length + 1),
        label: "Back",
        value: "back",
        aliases: ["back", "cancel"],
      });

      const slotName = await this.chooseMenu("Load Cloud Save", options, {
        prompt: "Cloud save choice: ",
        subtitle: "Downloaded cloud saves are also copied into saves/ for offline loading.",
      });
      if (slotName === "back") {
        return null;
      }

      try {
        const response = await this.downloadSave(slotName);
        const state = this.loadStateFromPayload(JSON.parse(response.save_data));
        const localStem = `cloud_${this.normalizeSlotName(slotName)}`;
        this.writeSaveText(response.save_data, localStem);
        this.say(`\nDownloaded cloud save to saves/${localStem}${SAVE_SUFFIX}.`);
        this.say(`\nLoaded cloud save slot '${slotName}'.`);
        return state;
      } catch (error) {
        this.say(`\nCloud load failed: ${error.message || error}`);
        return null;
      }
    }

    async cloudMenu(currentState = null) {
      while (true) {
        let options = [];
        if (this.isSignedIn()) {
          let nextKey = 1;
          if (currentState !== null) {
            options.push({
              key: String(nextKey),
              label: "Upload Current Save",
              value: "upload",
              aliases: ["upload", "sync", "save"],
            });
            nextKey += 1;
          }
          options = options.concat([
            {
              key: String(nextKey),
              label: "Load Cloud Save",
              value: "load",
              aliases: ["load", "download"],
            },
            {
              key: String(nextKey + 1),
              label: "Sign Out",
              value: "logout",
              aliases: ["logout", "sign out"],
            },
            {
              key: String(nextKey + 2),
              label: "Back",
              value: "back",
              aliases: ["back", "cancel"],
            },
          ]);
        } else {
          options = [
            { key: "1", label: "Create Account", value: "register", aliases: ["register", "create"] },
            { key: "2", label: "Sign In", value: "login", aliases: ["login", "sign in"] },
            { key: "3", label: "Back", value: "back", aliases: ["back", "cancel"] },
          ];
        }

        const choice = await this.chooseMenu("Cloud Saves", options, {
          prompt: "Cloud choice: ",
          subtitle: this.cloudStatus(),
        });

        if (choice === "register") {
          await this.cloudRegister();
        } else if (choice === "login") {
          await this.cloudLogin();
        } else if (choice === "upload") {
          await this.cloudUploadCurrent(currentState);
        } else if (choice === "load") {
          const loadedState = await this.cloudLoadInteractive();
          if (loadedState !== null) {
            return loadedState;
          }
        } else if (choice === "logout") {
          this.signOut();
          this.say("\nSigned out of cloud saves on this device.");
        } else if (choice === "back") {
          return null;
        }
      }
    }

    async checkpointMenu(state) {
      while (true) {
        let subtitle = `Next: ${this.sceneTitle(state.next_scene)} | Autosave: saves/autosave.tasave`;
        if (this.isSignedIn()) {
          subtitle += ` | Cloud: ${this.currentUsername()}`;
        }

        const choice = await this.chooseMenu("Checkpoint", [
          { key: "1", label: "Continue", value: "continue", aliases: ["continue", "c", "next"] },
          { key: "2", label: "Save Game", value: "save", aliases: ["save", "s"] },
          { key: "3", label: "Load Game", value: "load", aliases: ["load", "l"] },
          { key: "4", label: "Cloud Saves", value: "cloud", aliases: ["cloud", "online", "sync"] },
        ], {
          prompt: "Checkpoint choice: ",
          subtitle,
        });

        if (choice === "continue") {
          return state;
        }
        if (choice === "save") {
          await this.saveStateInteractive(state);
        } else if (choice === "load") {
          const loadedState = await this.loadStateInteractive();
          if (loadedState !== null) {
            return loadedState;
          }
        } else if (choice === "cloud") {
          const loadedState = await this.cloudMenu(state);
          if (loadedState !== null) {
            return loadedState;
          }
        }
      }
    }

    async mainMenu() {
      while (true) {
        const choice = await this.chooseMenu("Realmbound", [
          { key: "1", label: "New Game", value: "new", aliases: ["new", "start"] },
          { key: "2", label: "Load Game", value: "load", aliases: ["load", "continue"] },
          { key: "3", label: "Cloud Saves", value: "cloud", aliases: ["cloud", "online", "sync"] },
        ], { prompt: "Main menu choice: " });

        if (choice === "new") {
          await this.runStory(this.newState());
          return;
        }
        if (choice === "load") {
          const state = await this.loadStateInteractive();
          if (state !== null) {
            await this.runStory(state);
            return;
          }
        }
        if (choice === "cloud") {
          const state = await this.cloudMenu();
          if (state !== null) {
            await this.runStory(state);
            return;
          }
        }
      }
    }

    async runStory(state) {
      this.activeState = state;
      try {
        while (true) {
          const sceneId = state.next_scene;
          if (sceneId === FINISHED_SCENE) {
            await this.finishGame(state.player);
            return;
          }

          await this.runScene(sceneId, state.player, state.shop_stock);

          state.next_scene = this.nextScene(sceneId);
          if (state.next_scene === FINISHED_SCENE) {
            await this.finishGame(state.player);
            return;
          }

          const [autosaved, cloudSynced] = await this.autosaveState(state, true);
          if (autosaved) {
            let message = "\nAutosaved.";
            if (cloudSynced) {
              message += " Cloud synced.";
            }
            this.say(message);
          }
        }
      } finally {
        this.activeState = null;
      }
    }

    async runScene(sceneId, player, shopStock) {
      if (sceneId === "intro") {
        await this.introScene(player);
      } else if (sceneId === "wizard") {
        await this.wizardScene(player);
      } else if (sceneId === "locked_door") {
        await this.lockedDoorScene(player);
      } else if (sceneId === "first_goblin") {
        await this.firstGoblinScene(player);
      } else if (sceneId === "village") {
        await this.villageScene(player, shopStock);
      } else if (sceneId === "forest") {
        await this.forestScene(player, shopStock);
      } else if (sceneId === "twin_doors") {
        await this.twinDoorsScene(player);
      } else if (sceneId === "witch") {
        await this.witchScene(player);
      } else if (sceneId === "mountain_pass") {
        await this.mountainPassScene(player);
      } else if (sceneId === "moonlit_market") {
        await this.moonlitMarketScene(player, shopStock);
      } else if (sceneId === "vampire_castle") {
        await this.vampireCastleScene(player);
      } else if (sceneId === "false_throne") {
        await this.falseThroneScene(player, shopStock);
      } else if (sceneId === "underkeep") {
        await this.underkeepScene(player);
      } else if (sceneId === "clocktower") {
        await this.clocktowerScene(player, shopStock);
      } else if (sceneId === "well") {
        await this.wellScene(player);
      } else if (sceneId === "hundred_day_road") {
        await this.hundredDayRoadScene(player, shopStock);
      } else if (sceneId === "dragon_gate") {
        await this.dragonGateScene(player, shopStock);
      } else if (sceneId === "final_battle") {
        await this.finalBattleScene(player);
      } else {
        throw new Error("Unknown story checkpoint.");
      }

      await this.runSceneAdditions(sceneId, player, shopStock);
    }

    jsonLines(value) {
      if (value === undefined || value === null) return [];
      return Array.isArray(value) ? value.map(String) : [String(value)];
    }

    showJsonText(value) {
      for (const line of this.jsonLines(value)) {
        if (line) this.say(`\n${line}`);
      }
    }

    jsonMoney(value) {
      if (value && typeof value === "object") return randomInt(Number(value.min || 0), Number(value.max || 0));
      return Number(value || 0);
    }

    applyJsonRewards(rewards, player) {
      for (const reward of rewards || []) {
        if (!reward || typeof reward !== "object") continue;
        if (reward.item) player.backpack.push(String(reward.item));
        if (reward.money !== undefined) {
          const amount = this.jsonMoney(reward.money);
          player.money += amount;
          this.sayParts(["\nYou receive ", ...this.moneyParts(amount), "."]);
        }
        if (reward.health !== undefined) {
          const gained = Math.max(0, Math.min(Number(reward.health), player.healthMax - player.health));
          player.health += gained;
          this.say(`\nHealth +${gained}.`);
        }
        if (reward.mana !== undefined) {
          const gained = Math.max(0, Math.min(Number(reward.mana), player.manaMax - player.mana));
          player.mana += gained;
          this.say(`\nMana +${gained}.`);
        }
      }
    }

    restoreJsonPlayer(player, restore) {
      const config = restore && typeof restore === "object" ? restore : { health: "full", mana: "full" };
      const gains = { health: 0, mana: 0 };
      for (const [stat, maximum] of [["health", "healthMax"], ["mana", "manaMax"]]) {
        if (config[stat] === undefined || config[stat] === null) continue;
        const before = player[stat];
        player[stat] = config[stat] === "full"
          ? player[maximum]
          : Math.min(player[maximum], player[stat] + Math.max(0, Number(config[stat])));
        gains[stat] = player[stat] - before;
      }
      return gains;
    }

    async runJsonStep(step, player, shopStock) {
      if (!step || typeof step !== "object") throw new Error("A custom encounter step must be an object.");
      const type = step.type || "text";

      if (type === "sequence") {
        this.showJsonText(step.intro);
        await this.runJsonSteps(step.steps || [], player, shopStock);
        return;
      }
      if (type === "text") {
        this.showJsonText(step.text !== undefined ? step.text : step.lines);
        return;
      }
      if (type === "choice") {
        this.showJsonText(step.intro);
        const answer = await this.yesNo(step.prompt || "\nDo you continue? (yes/no): ");
        await this.runJsonSteps(step[answer] || [], player, shopStock);
        return;
      }
      if (type === "battle") {
        this.showJsonText(step.intro);
        if (step.choice === "fight_or_run" && await this.fightOrRun(step.prompt || "\nDo you fight or run? ") === "run") {
          const result = step.run || {};
          this.showJsonText(result.text);
          if (result.game_over) this.gameOver(player);
          return;
        }
        await this.spellFight(step.enemy, player);
        const victory = step.victory || {};
        this.applyJsonRewards(victory.rewards || [], player);
        this.showJsonText(victory.text);
        if (victory.offer_potions) await this.offerPotions(player);
        return;
      }
      if (type === "shop") {
        this.showJsonText(step.intro);
        const optional = step.optional !== undefined ? Boolean(step.optional) : step.prompt !== undefined;
        if (optional && await this.yesNo(step.prompt || "\nVisit the shop? (yes/no): ") === "no") {
          this.showJsonText(step.decline_text);
          return;
        }
        this.showJsonText(step.enter_text);
        await this.runShop(player, shopStock, Boolean(step.advanced), Boolean(step.legendary), {
          title: step.name || "Shop Menu",
          leaveText: step.leave_text || "You leave the store.",
        });
        return;
      }
      if (type === "church" || type === "rest") {
        this.showJsonText(step.intro);
        const optional = step.optional !== undefined ? Boolean(step.optional) : true;
        const prompt = step.prompt || `\nEnter ${step.name || "the church"}? (yes/no): `;
        if (optional && await this.yesNo(prompt) === "no") {
          this.showJsonText(step.decline_text || "You continue down the road.");
          return;
        }
        this.showJsonText(step.enter_text);
        const gains = this.restoreJsonPlayer(player, step.restore);
        this.showJsonText(step.rest_text || `You rest safely. Health +${gains.health}, mana +${gains.mana}.`);
        return;
      }
      if (type === "reward") {
        this.showJsonText(step.intro);
        this.applyJsonRewards(step.rewards || [], player);
        this.showJsonText(step.text);
        return;
      }
      throw new Error(`Unsupported custom encounter type: ${type}`);
    }

    async runJsonSteps(steps, player, shopStock) {
      for (const step of steps || []) await this.runJsonStep(step, player, shopStock);
    }

    async runJsonEncounter(encounterId, player, shopStock) {
      const entry = ENCOUNTER_DATA.data_encounters[encounterId];
      if (!entry) throw new Error(`Unknown encounter: ${encounterId}`);
      await this.runJsonStep(entry, player, shopStock);
    }

    async runSceneAdditions(sceneId, player, shopStock) {
      for (const id of (ENCOUNTER_DATA.scenes[sceneId].after_scene || [])) {
        await this.runJsonEncounter(id, player, shopStock);
      }
    }

    async extraFight(player, monsterName, intro, runText) {
      this.say(`\n${intro}`);
      if (await this.fightOrRun() === "run") {
        this.say(`\n${runText}`);
        this.gameOver(player);
      }
      await this.spellFight(monsterName, player);
      await this.offerPotions(player);
    }

    finishGame(player) {
      this.say("\nThe Realmbound Dragon's storm breaks apart into silver sparks above the saved realm.");
      this.say(`\nGood job, ${player.name || "Adventurer"}, you have completed the game.`);
      this.say("\nCredits: Realmbound by Thunderstruck7 and Lord Funion.");
      this.sayParts(["\nTHE END\nYou finished with ", ...this.moneyParts(player.money), "."]);
      return this.postgameMenu(player);
    }

    postgameHas(player, item) {
      return player.backpack.includes(item);
    }

    postgameAddOnce(player, item) {
      if (!this.postgameHas(player, item)) {
        player.backpack.push(item);
        return true;
      }
      return false;
    }

    postgameSpend(player, amount) {
      if (player.money < amount) {
        this.sayParts(["\nYou need ", ...this.moneyParts(amount - player.money), " more."]);
        return false;
      }
      player.money -= amount;
      return true;
    }

    postgameStatus(player) {
      const milestones = [
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
      ];
      const unlocked = milestones.filter((item) => this.postgameHas(player, item));
      this.sayParts(["\nWhoop Nickels: ", ...this.moneyParts(player.money)]);
      this.say(`Settlement: ${unlocked.length ? unlocked.join(", ") : "nothing built yet"}`);
    }

    async postgameMenu(player) {
      while (true) {
        const choice = await this.chooseMenu("Postgame", [
          { key: "1", label: "Build or Upgrade Home", value: "house", aliases: ["house", "build", "upgrade"] },
          { key: "2", label: "Family and Home", value: "family", aliases: ["family", "home"] },
          { key: "3", label: "Garden and Craft", value: "garden", aliases: ["garden", "farm", "craft"] },
          { key: "4", label: "Run Your Shop", value: "shop", aliases: ["shop", "store"] },
          { key: "5", label: "Rebuild the Realm", value: "town", aliases: ["town", "help", "realm"] },
          { key: "6", label: "Jobs Board", value: "quest", aliases: ["quest", "job", "jobs"] },
          { key: "7", label: "Hold a Festival", value: "festival", aliases: ["festival", "party"] },
          { key: "8", label: "Fish and Sail", value: "river", aliases: ["fish", "river", "sail"] },
          { key: "9", label: "Train an Apprentice", value: "apprentice", aliases: ["train", "apprentice"] },
          { key: "10", label: "Settlement Status", value: "status", aliases: ["status", "settlement"] },
          { key: "11", label: "Exit Game", value: "exit", aliases: ["exit", "quit", "q"] },
        ], {
          prompt: "Postgame choice: ",
          subtitle: "The realm is safe enough to live in now.",
        });
        if (choice === "house") {
          if (!this.postgameHas(player, "Postgame House")) {
            if (this.postgameSpend(player, 25)) {
              this.postgameAddOnce(player, "Postgame House");
              this.say("\nYou buy land near the road and build a small house with a sturdy roof.");
              this.say("You hang a lantern by the door and finally have a place to come back to.");
            }
          } else if (!this.postgameHas(player, "Second Floor")) {
            if (this.postgameSpend(player, 60)) {
              this.postgameAddOnce(player, "Second Floor");
              this.say("\nYou add a second floor, a guest room, and a balcony facing the hills.");
            }
          } else {
            this.say("\nYou patch the roof, oil the hinges, and make the house a little nicer.");
          }
        } else if (choice === "family") {
          if (!this.postgameHas(player, "Postgame House")) {
            this.say("\nYou should build a home first.");
          } else if (this.postgameAddOnce(player, "Family Hearth")) {
            this.say("\nYou meet someone kind, and over time you start a family in the quiet part of the valley.");
            this.say("The house gets louder, warmer, and a lot more lived in.");
          } else {
            this.say("\nYou spend the day at home cooking, telling stories, and fixing a mysteriously broken chair.");
          }
        } else if (choice === "garden") {
          this.postgameAddOnce(player, "Garden Patch");
          player.backpack.push("Potion Herbs");
          this.say("\nYou tend the garden and harvest Potion Herbs.");
          this.say("The frog supervises the garden like it owns the property.");
        } else if (choice === "shop") {
          if (this.postgameAddOnce(player, "Hero Shop Ledger")) {
            this.say("\nYou open a tiny shop and sell repair kits, jam, and honest advice.");
          }
          const earnings = randomInt(8, 22);
          player.money += earnings;
          this.sayParts(["Travelers buy supplies and leave ", ...this.moneyParts(earnings), " on the counter."]);
        } else if (choice === "town") {
          if (this.postgameAddOnce(player, "Town Charter")) {
            this.say("\nYou help repair roads, roofs, and the old bridge over the river.");
            this.say("The village starts looking like a place people can grow old in.");
          } else if (this.postgameAddOnce(player, "Hero Statue")) {
            this.say("\nThe town builds a small statue of you. It looks almost, but not quite, like you.");
          } else {
            this.say("\nYou spend the afternoon settling disputes, moving lumber, and signing very official papers.");
          }
        } else if (choice === "quest") {
          const reward = randomInt(10, 30);
          player.money += reward;
          const outcomes = [
            "A farmer hires you to find three missing sheep. You return with four, because one tagged along.",
            "The blacksmith asks for rare ore. You spend the afternoon in the hills and come back with a strange blue stone.",
            "A child asks for a hero story. You make one up, then realize it is almost true.",
            "A courier needs help crossing the old road. You escort them past three suspicious puddles.",
          ];
          this.say(`\n${outcomes[Math.floor(Math.random() * outcomes.length)]}`);
          this.sayParts(["You earn ", ...this.moneyParts(reward), "."]);
        } else if (choice === "festival") {
          this.postgameAddOnce(player, "Festival Banner");
          this.say("\nYou help organize a town festival with lanterns, music, and too many pies.");
          this.say("By nightfall the whole valley feels warmer.");
        } else if (choice === "river") {
          if (this.postgameAddOnce(player, "Fishing Rod")) {
            this.say("\nYou carve a fishing rod and learn that hero work did not teach patience.");
          } else if (this.postgameAddOnce(player, "River Boat")) {
            this.say("\nYou build a small river boat and map the bends beyond town.");
          } else {
            const catches = ["Silver Minnow", "Boot With Teeth Marks", "Tiny Treasure Chest"];
            const caught = catches[Math.floor(Math.random() * catches.length)];
            player.backpack.push(caught);
            this.say(`\nYou fish until sunset and catch a ${caught}.`);
          }
        } else if (choice === "apprentice") {
          if (this.postgameAddOnce(player, "Apprentice Badge")) {
            this.say("\nA young adventurer asks to train with you. You give them an Apprentice Badge.");
          } else {
            this.say("\nYou teach your apprentice how to pack snacks, read maps, and run only when running helps.");
          }
        } else if (choice === "adventure") {
          const finds = ["Starlit Pebble", "Old Road Coin", "Map to Nowhere"];
          const find = finds[Math.floor(Math.random() * finds.length)];
          player.backpack.push(find);
          this.say(`\nYou take one more walk into the hills and return with a ${find}.`);
        } else if (choice === "status") {
          this.postgameStatus(player);
        } else if (choice === "exit") {
          return;
        }
      }
    }

    async introScene(player) {
      player.name = cleanInput(await this.ask("\nWhat is your adventurer name? ")) || "Adventurer";
      this.say("\nYou are out on a casual stroll when a magical chocolate frog hops around your feet.");

      const choice = await this.yesNo("\nDo you pick it up? (yes/no): ");
      if (choice === "yes") {
        this.say("\nYou pick up the frog and store it in your backpack.");
      } else {
        this.say("\nYou start to walk away. RIBBIT.");
        this.say("The frog hops into your backpack anyway.");
      }

      player.backpack.push("Magical Chocolate Frog");
    }

    async wizardScene(player) {
      this.say("\nYou bump into an old man with a long white beard.");
      this.say('"Was that the croak of a chocolate frog?" he asks.');

      const choice = await this.yesNo("\nWhat do you say? (yes/no): ");
      if (choice === "no") {
        this.say("\nHis old hearing must be failing him. He wanders off.");
        this.activateFrogPartner(player);
        this.say("The frog gives you a tiny nod. It looks ready to fight for itself.");
        return;
      }

      this.say('\nHe smiles. "I am Rumblerod The Great, the only remaining wizard in the North."');
      const trade = await this.yesNo("\nTrade the frog for his spare magic wand? (yes/no): ");
      if (trade === "no") {
        this.say("\nRumblerod shrugs and continues down the path.");
        this.activateFrogPartner(player);
        this.say("The frog hops onto your shoulder and learns Tongue Slap out of spite.");
        return;
      }

      const frogIndex = player.backpack.indexOf("Magical Chocolate Frog");
      if (frogIndex >= 0) {
        player.backpack.splice(frogIndex, 1);
      }
      player.backpack.push("Magic Wand");
      this.addSpell(player, "Lockio Reducto");
      this.say("\nYou receive a Magic Wand.");
      this.say('Rumblerod says, "Lockio Reducto can unlock any door."');
    }

    async lockedDoorScene(player) {
      this.say("\nYou continue your journey and come to a fork in the path.");
      const pathChoice = await this.chooseLeftOrRight("\nDo you go left or right? ");
      if (pathChoice === "right") {
        this.say("\nYou notice a locked door on the left and decide not to miss it.");
      }

      const amount = randomInt(20, 30);
      const choice = player.frogMode
        ? await this.yesNo("\nYou find a locked door. Send the frog through the keyhole? (yes/no): ")
        : await this.yesNo("\nYou find a locked door. Use the wand and say the words? (yes/no): ");
      if (choice === "no") {
        this.say("\nA goblin sneaks up behind you and stabs you.");
        this.gameOver(player);
      }

      player.money += amount;
      if (player.frogMode) {
        this.sayParts([
          "\nThe frog squeezes under the door, unlocks it, and looks smug. You find ",
          ...this.moneyParts(amount),
          ".",
        ]);
      } else {
        this.sayParts(["\nYou say Lockio Reducto. The door opens and you find ", ...this.moneyParts(amount), "."]);
      }
    }

    async firstGoblinScene(player) {
      this.say("\nYou turn to exit, but a goblin blocks your path.");
      if (await this.fightOrRun() === "run") {
        this.say("\nThe goblin is faster than you.");
        this.gameOver(player);
      }

      const attack = await this.chooseMenu("Quick Fight", [
        { key: "1", label: "Uppercut", value: "uppercut", aliases: ["uppercut", "punch"] },
        { key: "2", label: "Kick", value: "kick", aliases: ["kick"] },
        { key: "3", label: "Dirt Throw", value: "dirt", aliases: ["dirt", "throw dirt"] },
      ], { prompt: "Move: " });

      if (attack === "dirt") {
        this.say("\nThe dirt blinds the goblin long enough for you to knock it out.");
      } else {
        this.say(`\nYour ${attack} knocks out the goblin.`);
      }
      if (player.frogMode) {
        this.addFrogAttack(player, "Bubble Burp");
        this.say("It drops a page from a frog-training book.");
        this.say("The frog eats half the page and learns Bubble Burp.");
      } else {
        this.addSpell(player, "Fireball");
        this.say("It drops a page from a spell book.");
        this.say("You learned Fireball.");
      }
      await this.extraFight(
        player,
        "gate rat",
        "The noise wakes a gate rat with opinions about trespassing.",
        "The gate rat follows your shoelaces and wins.",
      );
    }

    async villageScene(player, shopStock) {
      this.say("\nYou see a village nearby.");
      this.say("A troll is attacking the villagers.");
      if (await this.fightOrRun() === "run") {
        this.say("\nThe troll catches you before you can escape.");
        this.gameOver(player);
      }
      await this.spellFight("troll", player);
      await this.extraFight(
        player,
        "smoke imp",
        "A smoke imp crawls out of the village chimney and starts throwing sparks.",
        "You run through the smoke and smack directly into a fence.",
      );

      this.say('\nA villager says, "Thank you for saving our village."');
      this.say('"Take this Big Health Potion. It will restore your health."');
      player.backpack.push("Big Health Potion");
      await this.offerPotions(player);

      const enterStore = await this.yesNo("\nYou see Gnome Depot, Harold Sellsalot's shop. Go inside? (yes/no): ");
      if (enterStore === "no") {
        this.say("\nA skeleton archer outside the village shoots you.");
        this.gameOver(player);
      }

      this.say("\nHarold welcomes you into Gnome Depot.");
      await this.runShop(player, shopStock);

      this.say("\nYou leave the store and encounter a skeleton.");
      if (await this.fightOrRun() === "run") {
        this.say("\nThe skeleton catches you near the village gate.");
        this.gameOver(player);
      }
      await this.spellFight("skeleton", player);
      await this.offerPotions(player);
      await this.extraFight(
        player,
        "curse candle",
        "The village shrine candle grows teeth and blocks the road.",
        "The candle waddles after you. Slowly. Somehow still fast enough.",
      );
      const whisper = (await this.ask("\nBefore you leave, the cobblestones seem to whisper. Type what you heard or press Enter: ")).trim().toLowerCase();
      if (whisper === "listen") {
        this.say("\nA loose brick slides aside and reveals a narrow ladder.");
        await this.clocktowerScene(player, shopStock);
      } else if (whisper === "well") {
        await this.wellScene(player);
      }
    }

    async forestScene(player, shopStock) {
      this.say("\nYou follow a forest trail.");
      this.say("A werewolf howls at you from the trees.");
      if (await this.fightOrRun() === "run") {
        this.say("\nThe werewolf catches you in the brush.");
        this.gameOver(player);
      }
      await this.spellFight("werewolf", player);
      await this.offerPotions(player);
      await this.extraFight(
        player,
        "bramble wolf",
        "The bushes shake, then become a second wolf made mostly of thorns.",
        "You sprint into the brambles and immediately regret the shortcut.",
      );

      this.say("\nFarther down the trail, a goblin jumps into the path.");
      if (await this.fightOrRun() === "run") {
        this.say("\nThe goblin is faster than you.");
        this.gameOver(player);
      }
      await this.spellFight("goblin", player);
      await this.offerPotions(player);
      await this.extraFight(
        player,
        "treasure mimic",
        "A treasure chest sits in the road. It smiles before you can.",
        "The chest runs faster than a chest should legally run.",
      );

      this.say("\nAt the forest edge, Miss Costalot waves you over to her traveling cart.");
      await this.runShop(player, shopStock, true);
      if ((await this.ask("\nA mossy sign points off the road. Type 'detour' to ignore it, or press Enter: ")).trim().toLowerCase() === "detour") {
        this.say("\nYou push through nettles and find a forgotten well.");
        await this.wellScene(player);
      }
    }

    async twinDoorsScene(player) {
      this.say("\nYou find two locked doors at the end of the road.");
      const door = player.frogMode
        ? await this.chooseLeftOrRight("\nDo you send the frog to the left or the right door? ")
        : await this.chooseLeftOrRight("\nDo you use the wand on the left or the right door? ");
      if (player.frogMode) {
        this.say("\nThe frog shoulder-checks the lock until the door gives up.");
      } else {
        this.say("\nYou say Lockio Reducto and the door opens.");
      }

      if (door === "left") {
        this.say("\nThe left door leads to a dead end guarded by an ogre.");
        if (await this.fightOrRun() === "fight") {
          await this.spellFight("ogre", player);
          await this.offerPotions(player);
          this.say("\nAfter defeating the ogre, you realize this path leads nowhere.");
        } else {
          this.say("\nYou escape back to the corridor.");
        }
        this.say("The right door is now your only option.");
      }

      this.say("\nYou go through the right door and find a chest.");
      this.say("Before you can open it, an ogre attacks.");
      if (await this.fightOrRun() === "run") {
        this.say("\nYou slide between the ogre's legs and escape.");
        return;
      }

      await this.spellFight("ogre", player);
      const amount = randomInt(15, 25);
      player.money += amount;
      this.sayParts(["\nYou find ", ...this.moneyParts(amount), " in the chest."]);
      await this.offerPotions(player);
    }

    async witchScene(player) {
      this.say("\nYou continue down the corridor.");
      if (await this.fightOrRun("\nYou see a witch. Do you fight or run? ") === "run") {
        this.say("\nYou run into the ogre's dad, who is very angry with you.");
        this.gameOver(player);
      }

      await this.spellFight("witch", player);
      await this.offerPotions(player);
      await this.extraFight(
        player,
        "curse candle",
        "The witch's last candle hops down from a shelf and tries to finish the curse.",
        "The candle stamps out your escape plan with tiny wax feet.",
      );
    }

    async mountainPassScene(player) {
      this.say("\nPast the witch's corridor, the road climbs into a mountain pass.");
      this.say("A sign reads: FINAL CASTLE THIS WAY. Under it, someone wrote: probably.");
      if (await this.fightOrRun("\nAn ice goblin rolls down the hill at you. Do you fight or run? ") === "run") {
        this.say("\nYou try to run downhill, which works until the hill runs out.");
        this.gameOver(player);
      }

      await this.spellFight("ice goblin", player);
      await this.extraFight(
        player,
        "snow bat",
        "A snow bat drops from the pass marker and shakes frost from its wings.",
        "You run downhill; the snow bat takes the express route.",
      );
      const reward = randomInt(35, 50);
      player.money += reward;
      player.backpack.push("Moon Cheese");
      this.sayParts(["\nThe ice goblin's lunchbox pops open. You find ", ...this.moneyParts(reward), " and some Moon Cheese."]);
      await this.offerPotions(player);
    }

    async moonlitMarketScene(player, shopStock) {
      this.say("\nAt the top of the pass, paper lanterns glow over the Moonlit Market.");
      this.say('A merchant named Madam Probably says, "Everything here is almost safe."');
      await this.runShop(player, shopStock, true);

      this.say("\nBehind the last stall, a shadow knight blocks the castle road.");
      if (await this.fightOrRun() === "run") {
        this.say("\nThe knight sighs, walks faster than you, and bonks you with the flat of a gloomy sword.");
        this.gameOver(player);
      }
      await this.spellFight("shadow knight", player);
      await this.extraFight(
        player,
        "receipt wraith",
        "The knight's dropped receipt unfolds into a very angry wraith.",
        "The receipt wraith charges a late fee on your escape.",
      );
      player.money += 30;
      this.sayParts(["\nThe shadow knight drops ", ...this.moneyParts(30), " and a note that says: please stop Lord Dreadbiscuit."]);
      await this.offerPotions(player);
      if ((await this.ask("\nA vendor drops a receipt. Type the first word printed in tiny ink, or press Enter: ")).trim().toLowerCase() === "clock") {
        this.say("\nThe receipt opens a seam in the market wall.");
        await this.clocktowerScene(player, shopStock);
      }
    }

    async vampireCastleScene(player) {
      this.say("\nYou reach a castle shaped like a fancy tooth.");
      this.say("Inside, a vampire is practicing scary faces in a mirror that refuses to help.");
      if (await this.fightOrRun("\nThe vampire notices you. Do you fight or run? ") === "run") {
        this.say("\nYou run into a closet full of capes. The capes win.");
        this.gameOver(player);
      }

      await this.spellFight("vampire", player);
      await this.extraFight(
        player,
        "basement bat",
        "The castle basement answers the noise with an even smaller, meaner bat.",
        "You trip over a cape rack. The bat accepts the assist.",
      );
      player.backpack.push("Silver Key of Mild Concern");
      player.money += 40;
      this.sayParts(["\nThe vampire turns into a bat and drops the Silver Key of Mild Concern plus ", ...this.moneyParts(40), "."]);
      this.say("The key is real, but the real castle keeps moving farther away.");
      await this.offerPotions(player);
    }

    async falseThroneScene(player, shopStock) {
      this.say("\nThe Silver Key opens a hall with a throne made of polished cookies.");
      this.say("A herald in a paper crown announces that the final castle is 'just ahead' again.");
      if (await this.fightOrRun("\nA mirrored knight steps out of the throne room. Fight or run? ") === "run") {
        this.say("\nYou run, but the hallway keeps becoming longer behind you.");
        this.gameOver(player);
      }

      await this.spellFight("shadow knight", player);
      await this.extraFight(
        player,
        "sugar golem",
        "The cookie throne melts into a sugar golem with fists like bakery bricks.",
        "The hallway becomes syrup under your boots.",
      );
      const reward = randomInt(20, 35);
      player.money += reward;
      this.sayParts(["\nBehind the false throne, you find ", ...this.moneyParts(reward), " and a stairway that goes down."]);
      await this.offerPotions(player);
      await this.runShop(player, shopStock, true);
    }

    async clocktowerScene(player, shopStock) {
      this.say("\nA narrow stair climbs into a clocktower nobody mentioned.");
      this.say("Each floor is quieter than the last, as if the tower is trying not to be found.");
      if (await this.fightOrRun("\nA brass sentinel blocks the gears. Fight or run? ") === "run") {
        this.say("\nYou run, but the tower ticks its way into your path again.");
        this.gameOver(player);
      }
      await this.spellFight("shadow knight", player);
      await this.extraFight(
        player,
        "rust rat",
        "A gear hatch opens and another rust rat skitters across the clock face.",
        "The tower ticks your escape route closed.",
      );
      player.money += 20;
      player.backpack.push("Clockwork Cog");
      this.say("\nThe sentinel drops a Clockwork Cog and the tower keeps turning anyway.");
      await this.offerPotions(player);
      await this.runShop(player, shopStock, true);
    }

    async wellScene(player) {
      this.say("\nYou find an old well behind a fence that should not be easy to notice.");
      this.say("Something from below taps back twice, waits, then once more.");
      const choice = await this.yesNo("\nLean over and listen again? (yes/no): ");
      if (choice === "no") {
        this.say("\nThe well stays quiet, which is somehow worse.");
        return;
      }
      player.backpack.push("Well Water");
      player.money += 7;
      this.sayParts(["\nA bucket rises with ", ...this.moneyParts(7), " and a bottle of cold well water."]);
    }

    async underkeepScene(player) {
      this.say("\nThe stairway leads under the castle into a damp underkeep.");
      this.say("A sleepy archivist says the princess is not here, then stamps your map with 'TRY AGAIN'.");
      if (await this.fightOrRun("\nA chained ogre blocks the only tunnel. Fight or run? ") === "run") {
        this.say("\nYou run into a wall of old bricks and lose the argument.");
        this.gameOver(player);
      }

      await this.spellFight("ogre", player);
      await this.extraFight(
        player,
        "rust rat",
        "A rust rat drops from the pipes and starts chewing the map.",
        "You run into a pipe maze and the rust rat knows every pipe.",
      );
      player.backpack.push("Ancient Map Fragment");
      player.money += 25;
      this.say("\nThe ogre drops an Ancient Map Fragment and a small pouch of Whoop Nickels.");
      this.say("The fragment points deeper underground, because of course it does.");
      await this.offerPotions(player);
      const deeper = (await this.ask("\nThe tunnel breathes once. Type 'deeper' to keep going, or press Enter: ")).trim().toLowerCase();
      if (deeper === "deeper") {
        this.say("\nYou slip into a maintenance passage that should not exist.");
        await this.wellScene(player);
      }
    }

    async hundredDayRoadScene(player, shopStock) {
      const chapterNames = [
        "Ash Month",
        "Lantern Month",
        "Mirror Month",
        "Storm Month",
        "Crownless Month",
      ];

      const roadProgress = Math.max(0, Math.min(player.roadProgress || 0, LONG_ROAD_ENEMIES.length));
      if (roadProgress >= LONG_ROAD_ENEMIES.length) {
        this.say("\nRoad checkpoint loaded: all 50 battles complete.");
      } else if (roadProgress > 0) {
        this.say(`\nRoad checkpoint loaded: ${roadProgress}/50 battles complete.`);
        this.say(`The road unfolds again at milepost ${roadProgress + 1}.`);
      } else {
        this.say("\nThe Ancient Map Fragment unfolds into a road that is much longer than the paper should allow.");
        this.say("Mileposts rise out of the dirt one after another, each carved with a different warning.");
        this.say("Rumblerod squints at the first marker and says, 'This is the Hundred-Day Road. Bring snacks.'");
        this.say("The Dragon Gate waits at the far end, but the road refuses to be skipped.");
        await this.runShop(player, shopStock, true, true);
      }

      for (const [offset, enemy] of LONG_ROAD_ENEMIES.entries()) {
        if (offset < roadProgress) {
          continue;
        }
        const index = offset + 1;
        if (offset % 10 === 0) {
          const chapter = chapterNames[Math.floor(offset / 10)];
          this.say(`\n=== ${chapter} ===`);
          this.say(`The milepost reads ${index}/50. The road insists another month has begun.`);
          if (index > 1) {
            await this.offerPotions(player);
            await this.runShop(player, shopStock, true, true);
          }
        }

        const enemyTitle = enemy.replace(/\b\w/g, (letter) => letter.toUpperCase());
        if (await this.fightOrRun(`\nEnemy ${index}/50: A ${enemyTitle} blocks the road. Fight or run? `) === "run") {
          this.say("\nYou turn back. The road folds behind you like a map in a bad mood.");
          this.gameOver(player);
        }

        await this.spellFight(enemy, player);
        player.roadProgress = index;
        if (index % 5 === 0) {
          this.say(`\nRoad checkpoint saved: ${index}/50 battles complete.`);
        } else {
          this.say(`\nRoad progress saved: ${index}/50.`);
        }

        if (index % 5 === 0) {
          const healthGain = Math.min(30, player.healthMax - player.health);
          const manaGain = Math.min(20, player.manaMax - player.mana);
          player.health += healthGain;
          player.mana += manaGain;
          this.say(`\nA roadside shrine gives you just enough rest to keep going. Health +${healthGain}, mana +${manaGain}.`);
          await this.offerPotions(player);
        }
      }

      if (!player.backpack.includes("Hundred-Day Road Seal")) {
        player.backpack.push("Hundred-Day Road Seal");
        player.money += 150;
        this.say("\nThe fiftieth milepost cracks open and reveals the Hundred-Day Road Seal.");
        this.sayParts(["You also pry ", ...this.moneyParts(150), " from a stone donation box labeled 'hero maintenance'."]);
      } else {
        this.say("\nYour Hundred-Day Road Seal still glows. This road has already been conquered.");
      }
      this.say("Behind you, the road is full of footprints. Ahead, the Dragon Gate finally stops pretending to be close.");
      await this.runShop(player, shopStock, true, true);
    }

    async dragonGateScene(player, shopStock) {
      this.say("\nThe Silver Key fits a gate made of old dragon scales.");
      this.say("Next to it, two blacksmiths argue over whether anvils count as musical instruments.");
      this.say("They call their shop The Dragon Forge and offer one last chance to gear up.");
      await this.runShop(player, shopStock, true, true);

      await this.extraFight(
        player,
        "glass cobra",
        "A glass cobra uncoils from the gate hinges and reflects your worst angle.",
        "The cobra turns the gate into a mirror maze.",
      );
      this.say("\nWhen you unlock the gate, a crystal dragon wakes up and sneezes rainbows everywhere.");
      if (await this.fightOrRun("\nDo you fight the crystal dragon or run? ") === "run") {
        this.say("\nYou run. The dragon thinks this is fetch.");
        this.gameOver(player);
      }

      await this.spellFight("crystal dragon", player);
      await this.extraFight(
        player,
        "crown wraith",
        "The dragon's roar shakes a crown-shaped wraith out of the ceiling.",
        "The wraith declares your retreat illegal.",
      );
      player.backpack.push("Dragon Scale Chip");
      player.money += 60;
      this.sayParts(["\nThe dragon bows, gives you a Dragon Scale Chip, and pushes ", ...this.moneyParts(60), " into your hands."]);
      this.say("You are sure this must be the last thing. It is not the last thing.");
      await this.offerPotions(player);
    }

    async finalBattleScene(player) {
      this.say("\nBeyond the gate stands Lord Dreadbiscuit, wearing a crown far too small for his ego.");
      this.say('"At last," he says, "someone has come to challenge my mildly inconvenient darkness."');
      this.say("Then the crown cracks like thunder and the whole castle tilts toward the sky.");
      this.say("A dragon larger than the tower unfolds from the storm clouds, each scale glowing like a sealed doorway.");
      this.say('Lord Dreadbiscuit points up and whispers, "Technically, I was only renting the throne."');

      if (player.backpack.includes("Dragon Scale Chip")) {
        player.health = Math.min(player.healthMax, player.health + 40);
        player.mana = Math.min(player.manaMax, player.mana + 35);
        this.say(`\nThe Dragon Scale Chip burns white-hot and shields you in old realmfire. Health: ${player.health}/${player.healthMax} Mana: ${player.mana}/${player.manaMax}.`);
      }

      this.say("\nThe Realmbound Dragon lands on the ruined throne and blocks out every star.");
      if (await this.fightOrRun("\nDo you fight the Realmbound Dragon or run? ") === "run") {
        this.say("\nYou run. The dragon inhales once, and the road behind you becomes a memory.");
        this.gameOver(player);
      }

      await this.spellFight("realmbound dragon", player);
      this.say("\nThe Realmbound Dragon crashes across the throne mountain and folds its wings around the broken castle.");
      this.say("Its final roar turns into sunrise. Every locked road in the realm opens at once.");
      this.say("Lord Dreadbiscuit crawls from under a biscuit-shaped shield and immediately retires from evil.");
      this.say("Rumblerod appears from behind a curtain and insists he was helping invisibly the whole time.");
    }

    sellScraps(player) {
      let soldAnything = false;
      for (const item of [...player.backpack]) {
        if (SELLABLE_LOOT.has(item)) {
          const worth = randomInt(8, 14);
          player.backpack.splice(player.backpack.indexOf(item), 1);
          player.money += worth;
          soldAnything = true;
          this.sayParts([`\nYou sold a(n) ${item} for `, ...this.moneyParts(worth), "."]);
        }
      }
      return soldAnything;
    }

    async offerPotions(player) {
      while (true) {
        const maxHealth = player.healthMax;
        const bigCount = player.backpack.filter((item) => item === "Big Health Potion").length;
        const smallCount = player.backpack.filter((item) => item === "Small Health Potion").length;

        if (player.health >= maxHealth) {
          if (bigCount || smallCount) {
            this.say("\nYour health is full, so you save your potions.");
          }
          return false;
        }

        if (!bigCount && !smallCount) {
          this.say("\nNo health potions available.");
          return false;
        }

        const subtitle = [
          "Health: ",
          { text: `${statMeter(player.health, maxHealth)} ${player.health}/${maxHealth}`, className: "red" },
        ];
        const choice = await this.chooseMenu("Potion Menu", [
          {
            key: "1",
            label: "Drink Big Health Potion",
            value: "big",
            detail: "restore to full",
            aliases: ["big", "big potion", "full"],
            enabled: bigCount > 0,
            status: bigCount ? `x${bigCount}` : "none",
          },
          {
            key: "2",
            label: "Drink Small Health Potion",
            value: "small",
            detail: "+15 health",
            aliases: ["small", "small potion"],
            enabled: smallCount > 0,
            status: smallCount ? `x${smallCount}` : "none",
          },
          {
            key: "3",
            label: "Save potions",
            value: "exit",
            aliases: ["exit", "leave", "back", "no", "n", "q"],
          },
        ], {
          prompt: "Potion choice: ",
          subtitle,
        });

        if (choice === "big") {
          player.health = maxHealth;
          player.backpack.splice(player.backpack.indexOf("Big Health Potion"), 1);
          this.say(`\nYour health is restored to ${player.health}.`);
          break;
        }
        if (choice === "small") {
          player.health = Math.min(maxHealth, player.health + 30);
          player.backpack.splice(player.backpack.indexOf("Small Health Potion"), 1);
          this.say(`\nYour health is now ${player.health}.`);
          break;
        }
        if (choice === "exit") {
          this.say("\nYou save your potions for later.");
          return false;
        }
      }

      return true;
    }

    spellDetail(player, spell) {
      const manaCost = spell.manaCost || 0;
      const parts = [];
      if (Object.prototype.hasOwnProperty.call(spell, "damage")) {
        const damage = spell.damage + (player.extraDamage || 0);
        parts.push(damage ? `${damage} damage` : "control");
      }
      if (Object.prototype.hasOwnProperty.call(spell, "healing")) {
        parts.push(`heal ${spell.healing}`);
      }
      if (spell.effects?.burn) {
        parts.push("burn");
      }
      if (spell.effects?.stun) {
        parts.push(`stun ${spell.effects.stun} turns`);
      }
      parts.push(`${manaCost} mana`);
      return parts.join(", ");
    }

    frogAttackDetail(player, attack) {
      const energyCost = attack.energyCost || 0;
      const parts = [];
      if (Object.prototype.hasOwnProperty.call(attack, "damage")) {
        const damage = attack.damage + (player.frogPower || 0);
        parts.push(damage ? `${damage} damage` : "control");
      }
      if (Object.prototype.hasOwnProperty.call(attack, "healing")) {
        parts.push(`heal ${attack.healing}`);
      }
      if (attack.effects?.burn) {
        parts.push("bubble burn");
      }
      if (attack.effects?.stun) {
        parts.push(`stun ${attack.effects.stun} turns`);
      }
      parts.push(`${energyCost} frog energy`);
      return parts.join(", ");
    }

    basicDamage(player) {
      return BASIC_DAMAGE + (player.weaponDamage || 0) + Math.floor((player.roadProgress || 0) / 5);
    }

    tryCombatRevive(player) {
      const featherIndex = player.backpack.indexOf("Phoenix Feather");
      if (featherIndex < 0) {
        return false;
      }
      player.backpack.splice(featherIndex, 1);
      player.health = Math.max(1, Math.floor(player.healthMax / 2));
      this.say(`\nThe Phoenix Feather bursts into warm sparks and pulls you back to ${player.health}/${player.healthMax} health!`);
      return true;
    }

    async chooseCombatAction(monsterName, monsterHealth, monsterMaxHealth, player) {
      const basicDamage = this.basicDamage(player);
      const subtitle = [
        "You: ",
        { text: statMeter(player.health, player.healthMax), className: "red" },
        ` ${player.health}/${player.healthMax} | Mana: `,
        { text: `${player.mana}/${player.manaMax}`, className: "blue" },
        ` | ${monsterName[0].toUpperCase()}${monsterName.slice(1)}: `,
        { text: `${Math.max(monsterHealth, 0)}/${monsterMaxHealth}`, className: "red" },
      ];

      const options = [{
        key: "1",
        label: "Basic Attack",
        value: "basic",
        detail: `free, ${basicDamage} damage`,
        aliases: ["basic", "attack", "hit", "punch"],
      }];

      let nextKey = 2;
      for (const spellName of player.spells) {
        const spell = SPELLS[spellName] || {};
        if (!Object.prototype.hasOwnProperty.call(spell, "damage") && !Object.prototype.hasOwnProperty.call(spell, "healing")) {
          continue;
        }

        const manaCost = spell.manaCost || 0;
        let enabled = player.mana >= manaCost;
        let status = "";
        if (!enabled) {
          status = `need ${manaCost - player.mana} mana`;
        } else if (Object.prototype.hasOwnProperty.call(spell, "healing") && player.health >= player.healthMax) {
          enabled = false;
          status = "health full";
        }

        options.push({
          key: String(nextKey),
          label: spellName,
          value: spellName,
          detail: this.spellDetail(player, spell),
          aliases: [spellName],
          enabled,
          status,
        });
        nextKey += 1;
      }

      return this.chooseMenu("Combat", options, {
        prompt: "Action: ",
        subtitle,
        invalid: "Choose an action by number or name.",
      });
    }

    async chooseFrogAction(monsterName, monsterHealth, monsterMaxHealth, player) {
      const subtitle = [
        "You: ",
        { text: statMeter(player.health, player.healthMax), className: "red" },
        ` ${player.health}/${player.healthMax} | Frog Energy: `,
        { text: `${player.frogEnergy}/${player.frogEnergyMax}`, className: "green" },
        ` | ${monsterName[0].toUpperCase()}${monsterName.slice(1)}: `,
        { text: `${Math.max(monsterHealth, 0)}/${monsterMaxHealth}`, className: "red" },
      ];

      const options = [];
      for (const [index, attackName] of player.frogAttacks.entries()) {
        const attack = FROG_ATTACKS[attackName];
        if (!attack) {
          continue;
        }
        const energyCost = attack.energyCost || 0;
        let enabled = player.frogEnergy >= energyCost;
        let status = enabled ? "" : `need ${energyCost - player.frogEnergy} energy`;
        if (enabled && Object.prototype.hasOwnProperty.call(attack, "healing") && player.health >= player.healthMax) {
          enabled = false;
          status = "health full";
        }
        options.push({
          key: String(index + 1),
          label: attackName,
          value: attackName,
          detail: this.frogAttackDetail(player, attack),
          aliases: [attackName],
          enabled,
          status,
        });
      }

      return this.chooseMenu("Frog Battle", options, {
        prompt: "Frog command: ",
        subtitle,
        invalid: "Choose a frog attack by number or name.",
      });
    }

    monsterAttack(monsterName, monster, player) {
      const attack = randomChoice(monster.attacks);
      const damage = Math.max(0, monster.damage - (player.armor || 0));
      this.say(`The ${monsterName} attacks with ${attack}!`);
      player.health -= damage;
      if (damage) {
        this.sayParts([
          `You take ${damage} damage. Health: `,
          { text: `${player.health}/${player.healthMax}`, className: "red" },
        ]);
      } else {
        this.say("Your armor absorbs the hit.");
      }

      if (monsterName === "witch" && attack === "poison") {
        this.say("The poison slips past your armor.");
        return 3;
      }
      return 0;
    }

    async spellFight(monsterName, player) {
      if (player.frogMode) {
        await this.frogFight(monsterName, player);
        return;
      }

      const monster = MONSTERS[monsterName];
      let monsterHealth = monster.health;
      const monsterMaxHealth = monster.health;
      let burnTurns = 0;
      let stunTurns = 0;
      let poisonTicks = 0;

      this.say(`\nA fight starts between you and the ${monsterName}!`);
      this.sayParts([`The ${monsterName} has `, { text: String(monsterHealth), className: "red" }, " health."]);
      this.sayParts(["It does ", { text: String(monster.damage), className: "cyan" }, " damage."]);

      while (monsterHealth > 0 && player.health > 0) {
        if (poisonTicks > 0) {
          player.health -= STATUS_DAMAGE;
          poisonTicks -= 1;
          this.say(`The poison burns you for ${STATUS_DAMAGE} damage. Health: ${player.health}/${player.healthMax}`);
          if (player.health <= 0 && !this.tryCombatRevive(player)) {
            this.gameOver(player);
          }
        }

        if (burnTurns > 0) {
          monsterHealth -= STATUS_DAMAGE;
          burnTurns -= 1;
          this.say(`The ${monsterName} burns for ${STATUS_DAMAGE} damage. Health: ${Math.max(monsterHealth, 0)}/${monsterMaxHealth}`);
          if (monsterHealth <= 0) {
            this.winFight(monsterName, player);
            return;
          }
        }

        const action = await this.chooseCombatAction(monsterName, monsterHealth, monsterMaxHealth, player);

        if (action === "basic") {
          const basicDamage = this.basicDamage(player);
          monsterHealth -= basicDamage;
          this.say(`You strike for ${basicDamage} damage.`);
          if (player.mana < player.manaMax) {
            const recovered = Math.min(3, player.manaMax - player.mana);
            player.mana += recovered;
            this.say(`You steady your breathing and recover ${recovered} mana.`);
          }
        } else {
          const spellName = action;
          const spell = SPELLS[spellName];
          const manaCost = spell.manaCost || 0;
          player.mana -= manaCost;
          this.say(`You cast ${spellName}.`);

          if (Object.prototype.hasOwnProperty.call(spell, "damage")) {
            const damage = spell.damage + (player.extraDamage || 0);
            monsterHealth -= damage;
            if (damage) {
              this.say(`You deal ${damage} damage.`);
            }

            const effects = spell.effects || {};
            if (Object.prototype.hasOwnProperty.call(effects, "burn")) {
              burnTurns = Math.max(burnTurns, effects.burn);
              this.say(`The target burns for ${burnTurns} turns.`);
            }
            if (Object.prototype.hasOwnProperty.call(effects, "stun")) {
              stunTurns = Math.max(stunTurns, effects.stun);
              this.say(`The ${monsterName} is stunned for ${stunTurns} turns.`);
            }
          } else {
            const healAmount = Math.max(0, Math.min(player.healthMax - player.health, spell.healing));
            player.health += healAmount;
            this.say(`You heal ${healAmount} health.`);
          }
        }

        if (monsterHealth <= 0) {
          this.winFight(monsterName, player);
          return;
        }

        if (stunTurns > 0) {
          stunTurns -= 1;
          this.say(`The ${monsterName} is stunned and skips its turn.`);
        } else {
          poisonTicks = Math.max(poisonTicks, this.monsterAttack(monsterName, monster, player));
        }

        if (player.health <= 0 && !this.tryCombatRevive(player)) {
          this.gameOver(player);
        }

        this.sayParts([
          `The ${monsterName} has `,
          { text: `${Math.max(monsterHealth, 0)}/${monsterMaxHealth}`, className: "red" },
          " health remaining.",
        ]);
      }
    }

    async frogFight(monsterName, player) {
      if (!player.frogAttacks.length) {
        this.addFrogAttack(player, "Tongue Slap");
      }

      const monster = MONSTERS[monsterName];
      let monsterHealth = monster.health;
      const monsterMaxHealth = monster.health;
      let burnTurns = 0;
      let stunTurns = 0;
      let poisonTicks = 0;

      this.say(`\nA frog battle starts between you and the ${monsterName}!`);
      this.sayParts([`The ${monsterName} has `, { text: String(monsterHealth), className: "red" }, " health."]);
      this.sayParts(["It does ", { text: String(monster.damage), className: "cyan" }, " damage."]);

      while (monsterHealth > 0 && player.health > 0) {
        if (poisonTicks > 0) {
          player.health -= STATUS_DAMAGE;
          poisonTicks -= 1;
          this.say(`The poison burns you for ${STATUS_DAMAGE} damage. Health: ${player.health}/${player.healthMax}`);
          if (player.health <= 0 && !this.tryCombatRevive(player)) {
            this.gameOver(player);
          }
        }

        if (burnTurns > 0) {
          monsterHealth -= STATUS_DAMAGE;
          burnTurns -= 1;
          this.say(`The ${monsterName} fizzes for ${STATUS_DAMAGE} damage. Health: ${Math.max(monsterHealth, 0)}/${monsterMaxHealth}`);
          if (monsterHealth <= 0) {
            this.winFight(monsterName, player);
            return;
          }
        }

        const attackName = await this.chooseFrogAction(monsterName, monsterHealth, monsterMaxHealth, player);
        const attack = FROG_ATTACKS[attackName];
        player.frogEnergy -= attack.energyCost || 0;
        this.say(`You shout, "${attackName}!" The magical frog hops forward.`);

        if (Object.prototype.hasOwnProperty.call(attack, "damage")) {
          const damage = attack.damage + (player.frogPower || 0);
          monsterHealth -= damage;
          if (damage) {
            this.say(`The frog deals ${damage} damage.`);
          }

          const effects = attack.effects || {};
          if (Object.prototype.hasOwnProperty.call(effects, "burn")) {
            burnTurns = Math.max(burnTurns, effects.burn);
            this.say(`The target fizzes for ${burnTurns} turns.`);
          }
          if (Object.prototype.hasOwnProperty.call(effects, "stun")) {
            stunTurns = Math.max(stunTurns, effects.stun);
            this.say(`The ${monsterName} is stunned for ${stunTurns} turns.`);
          }
        } else {
          const healAmount = Math.max(0, Math.min(player.healthMax - player.health, attack.healing));
          player.health += healAmount;
          this.say(`The frog shares snacks and heals ${healAmount} health.`);
        }

        if (monsterHealth <= 0) {
          this.winFight(monsterName, player);
          return;
        }

        if (stunTurns > 0) {
          stunTurns -= 1;
          this.say(`The ${monsterName} is stunned and skips its turn.`);
        } else {
          poisonTicks = Math.max(poisonTicks, this.monsterAttack(monsterName, monster, player));
        }

        if (player.health <= 0 && !this.tryCombatRevive(player)) {
          this.gameOver(player);
        }

        this.sayParts([
          `The ${monsterName} has `,
          { text: `${Math.max(monsterHealth, 0)}/${monsterMaxHealth}`, className: "red" },
          " health remaining.",
        ]);
      }
    }

    winFight(monsterName, player) {
      this.say(`The ${monsterName} has been defeated!`);
      const monster = MONSTERS[monsterName];
      const reward = Number(monster.reward || 10);
      player.money += reward;
      const drop = randomChoice(LOOT_DROPS);
      player.backpack.push(drop);
      const healthGain = Math.max(0, Math.min(Math.max(18, Math.floor(player.healthMax / 6)), player.healthMax - player.health));
      const manaGain = Math.max(0, Math.min(Math.max(15, Math.floor(player.manaMax / 8)), player.manaMax - player.mana));
      player.health += healthGain;
      player.mana += manaGain;
      if (player.frogMode) player.frogEnergy = Math.min(player.frogEnergyMax, player.frogEnergy + 8);
      this.sayParts(["You gained ", ...this.moneyParts(reward), ` and found a ${drop}.`]);
      if (healthGain || manaGain) this.say(`You catch your breath: health +${healthGain}, mana +${manaGain}.`);
    }

    gameOver(player) {
      this.say("You have been defeated!");
      this.sayParts(["GAME OVER\nYou had ", ...this.moneyParts(player.money), "."]);
      throw new GameOver();
    }

    buySpell(player, stock, spellName, price) {
      if (!stock[spellName]) {
        this.say("\nThat spell is out of stock.");
        return;
      }
      if (player.money < price) {
        this.say("\nYou don't have enough Whoop Nickels.");
        return;
      }

      player.money -= price;
      this.addSpell(player, spellName);
      stock[spellName] = false;
      this.say(`\nYou learned ${spellName}.`);
      this.sayParts(["You have ", ...this.moneyParts(player.money), " left."]);
    }

    buyItem(player, itemName, price) {
      if (player.money < price) {
        this.say("\nYou don't have enough Whoop Nickels.");
        return;
      }

      player.money -= price;
      player.backpack.push(itemName);
      this.say(`\nYou bought a ${itemName}.`);
      this.sayParts(["You have ", ...this.moneyParts(player.money), " left."]);
    }

    buyStockedItem(player, stock, itemName, price) {
      if (!stock[itemName]) {
        this.say("\nThat item is out of stock.");
        return;
      }
      if (player.money < price) {
        this.say("\nYou don't have enough Whoop Nickels.");
        return;
      }

      player.money -= price;
      player.backpack.push(itemName);
      stock[itemName] = false;
      this.say(`\nYou bought a ${itemName}.`);
      this.sayParts(["You have ", ...this.moneyParts(player.money), " left."]);
    }

    buyManaFlask(player) {
      const price = 60;
      if (player.money < price) {
        this.say("\nYou don't have enough Whoop Nickels.");
        return;
      }

      player.money -= price;
      player.mana = Math.min(player.manaMax, player.mana + 35);
      this.say(`\nYou drink a Mana Flask and recover to ${player.mana}/${player.manaMax} mana.`);
      this.sayParts(["You have ", ...this.moneyParts(player.money), " left."]);
    }

    async buyMana(player) {
      const priceEach = 4;
      while (true) {
        const priceLabel = `${priceEach} Whoop Nickels`;
        const amountText = normalizeChoice(await this.ask(`\nMax mana to buy (${priceLabel} each, 'all' for max, or 'back'): `));
        let amount;
        if (["back", "b", "cancel", "leave", "q"].includes(amountText)) {
          this.say("\nYou decide not to buy mana.");
          return;
        }
        if (["all", "max"].includes(amountText)) {
          if (player.money <= 0) {
            this.say("\nYou don't have enough Whoop Nickels.");
            return;
          }
          amount = Math.floor(player.money / priceEach);
        } else if (/^\d+$/.test(amountText)) {
          amount = Number.parseInt(amountText, 10);
        } else {
          this.say("\nPlease enter a number, 'all', or 'back'.");
          continue;
        }

        if (amount <= 0) {
          this.say("\nPlease enter a positive number.");
          continue;
        }
        const cost = amount * priceEach;
        if (player.money < cost) {
          this.say("\nYou don't have enough Whoop Nickels.");
          return;
        }

        player.money -= cost;
        player.mana += amount;
        player.manaMax += amount;
        this.say(`\nYou bought ${amount} max mana.`);
        this.sayParts(["You have ", ...this.moneyParts(player.money), " left."]);
        return;
      }
    }

    priceStatus(player, price, unavailable = false, unavailableLabel = "owned") {
      if (unavailable) {
        return unavailableLabel;
      }
      if (player.money < price) {
        const amount = price - player.money;
        const label = amount === 1 ? "Whoop Nickel" : "Whoop Nickels";
        return `need ${amount} ${label} more`;
      }
      return "";
    }

    buyEquipment(player, stock, itemName, price, statName, amount) {
      if (!stock[itemName]) {
        this.say("\nThat equipment is out of stock.");
        return;
      }
      if (player.money < price) {
        this.say("\nYou don't have enough Whoop Nickels.");
        return;
      }

      player.money -= price;
      player[statName] += amount;
      player.backpack.push(itemName);
      stock[itemName] = false;
      this.say(`\nYou bought ${itemName}.`);
      this.sayParts(["You have ", ...this.moneyParts(player.money), " left."]);
    }

    buyFrogAttack(player, stock, itemName, price, attackName) {
      if (!stock[itemName]) {
        this.say("\nThat training book is out of stock.");
        return;
      }
      if (player.money < price) {
        this.say("\nYou don't have enough Whoop Nickels.");
        return;
      }

      player.money -= price;
      this.addFrogAttack(player, attackName);
      player.backpack.push(itemName);
      stock[itemName] = false;
      this.say(`\nThe frog studies ${itemName} and learns ${attackName}.`);
      this.sayParts(["You have ", ...this.moneyParts(player.money), " left."]);
    }

    buyFrogTraining(player, stock, itemName, price, config = {}) {
      if (!stock[itemName]) {
        this.say("\nThat training book is out of stock.");
        return;
      }
      if (player.money < price) {
        this.say("\nYou don't have enough Whoop Nickels.");
        return;
      }

      const power = config.power || 0;
      const energy = config.energy || 0;
      player.money -= price;
      player.frogPower += power;
      player.frogEnergyMax += energy;
      player.frogEnergy = Math.min(player.frogEnergyMax, player.frogEnergy + energy);
      player.backpack.push(itemName);
      stock[itemName] = false;
      this.say(`\nThe frog trains with ${itemName}.`);
      if (power) {
        this.say(`Frog Power increased by ${power}.`);
      }
      if (energy) {
        this.say(`Max Frog Energy increased by ${energy}.`);
      }
      this.sayParts(["You have ", ...this.moneyParts(player.money), " left."]);
    }

    async buyFrogEnergy(player) {
      const priceEach = 4;
      while (true) {
        const amountText = normalizeChoice(await this.ask(`\nFrog energy to buy (${priceEach} Whoop Nickels each, 'all' for max, or 'back'): `));
        let amount;
        if (["back", "b", "cancel", "leave", "q"].includes(amountText)) {
          this.say("\nYou decide not to buy frog energy.");
          return;
        }
        if (["all", "max"].includes(amountText)) {
          if (player.money <= 0) {
            this.say("\nYou don't have enough Whoop Nickels.");
            return;
          }
          amount = Math.floor(player.money / priceEach);
        } else if (/^\d+$/.test(amountText)) {
          amount = Number.parseInt(amountText, 10);
        } else {
          this.say("\nPlease enter a number, 'all', or 'back'.");
          continue;
        }

        if (amount <= 0) {
          this.say("\nPlease enter a positive number.");
          continue;
        }
        const cost = amount * priceEach;
        if (player.money < cost) {
          this.say("\nYou don't have enough Whoop Nickels.");
          return;
        }

        player.money -= cost;
        player.frogEnergy += amount;
        player.frogEnergyMax += amount;
        this.say(`\nYou bought ${amount} frog energy.`);
        this.sayParts(["You have ", ...this.moneyParts(player.money), " left."]);
        return;
      }
    }

    async runFrogShop(player, stock, advanced = false, legendary = false, config = {}) {
      while (true) {
        const options = [
          {
            key: "1",
            label: "Small Health Potion",
            value: "small_potion",
            detail: [...this.moneyParts(28), " - heals 30 health"],
            aliases: ["small", "small potion", "health potion", "potion"],
            status: this.priceStatus(player, 28),
          },
          {
            key: "2",
            label: "Croak Fu Primer",
            value: "croak_fu",
            detail: [...this.moneyParts(85), " - +3 frog power, +10 max frog energy"],
            aliases: ["croak", "croak fu", "primer", "training"],
            enabled: stock["Croak Fu Primer"],
            status: this.priceStatus(player, 85, !stock["Croak Fu Primer"], "read"),
          },
          {
            key: "3",
            label: "Bubble Burp Codex",
            value: "bubble_burp",
            detail: [...this.moneyParts(70), ` - ${FROG_ATTACKS["Bubble Burp"].description}`],
            aliases: ["bubble", "bubble burp", "codex"],
            enabled: stock["Bubble Burp Codex"],
            status: this.priceStatus(player, 70, !stock["Bubble Burp Codex"], "read"),
          },
          {
            key: "4",
            label: "Add Frog Energy",
            value: "frog_energy",
            detail: [...this.moneyParts(4), " = +1 max frog energy"],
            aliases: ["energy", "frog energy", "add energy"],
            status: player.money ? "spend any amount" : "no money",
          },
        ];

        if (advanced) {
          options.push(
            {
              key: "5",
              label: "Big Health Potion",
              value: "big_potion",
              detail: [...this.moneyParts(95), " - restores full health"],
              aliases: ["big", "big potion", "full potion"],
              status: this.priceStatus(player, 95),
            },
            {
              key: "6",
              label: "Royal Croak Sheet Music",
              value: "royal_croak",
              detail: [...this.moneyParts(125), ` - ${FROG_ATTACKS["Royal Croak"].description}`],
              aliases: ["royal", "royal croak", "sheet music"],
              enabled: stock["Royal Croak Sheet Music"],
              status: this.priceStatus(player, 125, !stock["Royal Croak Sheet Music"], "read"),
            },
            {
              key: "7",
              label: "Snack Break Cookbook",
              value: "snack_break",
              detail: [...this.moneyParts(110), ` - ${FROG_ATTACKS["Snack Break"].description}`],
              aliases: ["snack", "snack break", "cookbook"],
              enabled: stock["Snack Break Cookbook"],
              status: this.priceStatus(player, 110, !stock["Snack Break Cookbook"], "read"),
            },
            {
              key: "8",
              label: "Moon Leap Manual",
              value: "moon_leap",
              detail: [...this.moneyParts(165), ` - ${FROG_ATTACKS["Moon Leap"].description}`],
              aliases: ["moon", "moon leap", "manual"],
              enabled: stock["Moon Leap Manual"],
              status: this.priceStatus(player, 165, !stock["Moon Leap Manual"], "read"),
            },
            {
              key: "9",
              label: "Golden Fly Protein",
              value: "golden_fly",
              detail: [...this.moneyParts(180), " - +5 frog power, +5 max frog energy"],
              aliases: ["golden", "fly", "protein"],
              enabled: stock["Golden Fly Protein"],
              status: this.priceStatus(player, 180, !stock["Golden Fly Protein"], "used"),
            },
          );
          if (legendary) {
            options.push(
              {
                key: "10",
                label: "Dragonfly Tactics",
                value: "dragonfly_dive",
                detail: [...this.moneyParts(240), ` - ${FROG_ATTACKS["Dragonfly Dive"].description}`],
                aliases: ["dragonfly", "dragonfly dive", "tactics"],
                enabled: stock["Dragonfly Tactics"],
                status: this.priceStatus(player, 240, !stock["Dragonfly Tactics"], "read"),
              },
              {
                key: "11",
                label: "Phoenix Feather",
                value: "phoenix_feather",
                detail: [...this.moneyParts(180), " - revives you once in combat"],
                aliases: ["phoenix", "feather", "revive"],
                enabled: stock["Phoenix Feather"],
                status: this.priceStatus(player, 180, !stock["Phoenix Feather"], "owned"),
              },
              {
                key: "12",
                label: "Dragon Scale Shield",
                value: "dragon_shield",
                detail: [...this.moneyParts(220), " - +8 armor"],
                aliases: ["shield", "dragon shield", "dragon scale"],
                enabled: stock["Dragon Scale Shield"],
                status: this.priceStatus(player, 220, !stock["Dragon Scale Shield"], "owned"),
              },
              {
                key: "13",
                label: "Leave store",
                value: "leave",
                aliases: ["leave", "exit", "back", "q"],
              },
            );
          } else {
            options.push({
              key: "10",
              label: "Leave store",
              value: "leave",
              aliases: ["leave", "exit", "back", "q"],
            });
          }
        } else {
          options.push({
            key: "5",
            label: "Leave store",
            value: "leave",
            aliases: ["leave", "exit", "back", "q"],
          });
        }

        const subtitle = [
          "Whoop Nickels: ",
          ...this.moneyParts(player.money),
          ` | Health: ${statMeter(player.health, player.healthMax)} ${player.health}/${player.healthMax} | Frog Energy: ${statMeter(player.frogEnergy, player.frogEnergyMax)} ${player.frogEnergy}/${player.frogEnergyMax}`,
        ];

        const choice = await this.chooseMenu(config.title || "Frog Training Shop", options, {
          prompt: "Shop choice: ",
          subtitle,
        });

        if (choice === "small_potion") {
          this.buyItem(player, "Small Health Potion", 28);
        } else if (choice === "croak_fu") {
          this.buyFrogTraining(player, stock, "Croak Fu Primer", 85, { power: 3, energy: 10 });
        } else if (choice === "bubble_burp") {
          this.buyFrogAttack(player, stock, "Bubble Burp Codex", 70, "Bubble Burp");
        } else if (choice === "frog_energy") {
          await this.buyFrogEnergy(player);
        } else if (choice === "big_potion") {
          this.buyItem(player, "Big Health Potion", 95);
        } else if (choice === "royal_croak") {
          this.buyFrogAttack(player, stock, "Royal Croak Sheet Music", 125, "Royal Croak");
        } else if (choice === "snack_break") {
          this.buyFrogAttack(player, stock, "Snack Break Cookbook", 110, "Snack Break");
        } else if (choice === "moon_leap") {
          this.buyFrogAttack(player, stock, "Moon Leap Manual", 165, "Moon Leap");
        } else if (choice === "golden_fly") {
          this.buyFrogTraining(player, stock, "Golden Fly Protein", 180, { power: 5, energy: 5 });
        } else if (choice === "dragonfly_dive") {
          this.buyFrogAttack(player, stock, "Dragonfly Tactics", 240, "Dragonfly Dive");
        } else if (choice === "phoenix_feather") {
          this.buyStockedItem(player, stock, "Phoenix Feather", 180);
        } else if (choice === "dragon_shield") {
          this.buyEquipment(player, stock, "Dragon Scale Shield", 220, "armor", 8);
        } else if (choice === "leave") {
          this.say(`\n${config.leaveText || "You leave the store."}`);
          return;
        }
      }
    }

    async runShop(player, stock, advanced = false, legendary = false, config = {}) {
      this.sellScraps(player);
      if (player.frogMode) {
        await this.runFrogShop(player, stock, advanced, legendary, config);
        return;
      }

      while (true) {
        const options = [
          {
            key: "1",
            label: "Arcane Blast",
            value: "arcane",
            detail: [...this.moneyParts(45), ` - ${SPELLS["Arcane Blast"].description}`],
            aliases: ["arcane", "arcane blast", "spell 1"],
            enabled: stock["Arcane Blast"],
            status: this.priceStatus(player, 45, !stock["Arcane Blast"], "learned"),
          },
          {
            key: "2",
            label: "Small Health Potion",
            value: "small_potion",
            detail: [...this.moneyParts(28), " - heals 30 health"],
            aliases: ["small", "small potion", "health potion", "potion"],
            status: this.priceStatus(player, 28),
          },
          {
            key: "3",
            label: "Thunderstorm",
            value: "thunderstorm",
            detail: [...this.moneyParts(90), ` - ${SPELLS.Thunderstorm.description}`],
            aliases: ["thunder", "thunderstorm", "spell 3"],
            enabled: stock.Thunderstorm,
            status: this.priceStatus(player, 90, !stock.Thunderstorm, "learned"),
          },
          {
            key: "4",
            label: "Restoration Incantation",
            value: "restoration",
            detail: [...this.moneyParts(75), ` - ${SPELLS["Restoration Incantation"].description}`],
            aliases: ["restore", "restoration", "heal spell", "spell 4"],
            enabled: stock["Restoration Incantation"],
            status: this.priceStatus(player, 75, !stock["Restoration Incantation"], "learned"),
          },
          {
            key: "5",
            label: "Add Mana",
            value: "mana",
            detail: [...this.moneyParts(4), " = +1 max mana"],
            aliases: ["mana", "add mana", "buy mana"],
            status: player.money ? "spend any amount" : "no money",
          },
          {
            key: "6",
            label: "Mana Flask",
            value: "mana_flask",
            detail: [...this.moneyParts(60), " - recover 35 mana now"],
            aliases: ["flask", "mana flask", "refill"],
            status: this.priceStatus(player, 60),
          },
        ];

        if (advanced) {
          options.push(
            {
              key: "7",
              label: "Big Health Potion",
              value: "big_potion",
              detail: [...this.moneyParts(95), " - restores full health"],
              aliases: ["big", "big potion", "full potion"],
              status: this.priceStatus(player, 95),
            },
            {
              key: "8",
              label: "Glorious Helmet",
              value: "helmet",
              detail: [...this.moneyParts(140), " - +5 armor"],
              aliases: ["helmet", "armor"],
              enabled: stock["Glorious Helmet"],
              status: this.priceStatus(player, 140, !stock["Glorious Helmet"], "owned"),
            },
            {
              key: "9",
              label: "Mage Boots",
              value: "boots",
              detail: [...this.moneyParts(130), " - +3 spell damage"],
              aliases: ["boots", "mage boots", "damage"],
              enabled: stock["Mage Boots"],
              status: this.priceStatus(player, 130, !stock["Mage Boots"], "owned"),
            },
            {
              key: "10",
              label: "Frost Nova",
              value: "frost_nova",
              detail: [...this.moneyParts(120), ` - ${SPELLS["Frost Nova"].description}`],
              aliases: ["frost", "frost nova", "spell 9"],
              enabled: stock["Frost Nova"],
              status: this.priceStatus(player, 120, !stock["Frost Nova"], "learned"),
            },
            {
              key: "11",
              label: "Crystal Sword",
              value: "crystal_sword",
              detail: [...this.moneyParts(160), " - +8 basic attack damage"],
              aliases: ["sword", "crystal sword", "weapon"],
              enabled: stock["Crystal Sword"],
              status: this.priceStatus(player, 160, !stock["Crystal Sword"], "owned"),
            },
            {
              key: "12",
              label: "Phoenix Feather",
              value: "phoenix_feather",
              detail: [...this.moneyParts(180), " - revives you once in combat"],
              aliases: ["phoenix", "feather", "revive"],
              enabled: stock["Phoenix Feather"],
              status: this.priceStatus(player, 180, !stock["Phoenix Feather"], "owned"),
            },
          );
          if (legendary) {
            options.push(
              {
                key: "13",
                label: "Solar Beam",
                value: "solar_beam",
                detail: [...this.moneyParts(240), ` - ${SPELLS["Solar Beam"].description}`],
                aliases: ["solar", "solar beam", "spell 12"],
                enabled: stock["Solar Beam"],
                status: this.priceStatus(player, 240, !stock["Solar Beam"], "learned"),
              },
              {
                key: "14",
                label: "Life Bloom",
                value: "life_bloom",
                detail: [...this.moneyParts(210), ` - ${SPELLS["Life Bloom"].description}`],
                aliases: ["life", "life bloom", "heal spell"],
                enabled: stock["Life Bloom"],
                status: this.priceStatus(player, 210, !stock["Life Bloom"], "learned"),
              },
              {
                key: "15",
                label: "Dragon Scale Shield",
                value: "dragon_shield",
                detail: [...this.moneyParts(220), " - +8 armor"],
                aliases: ["shield", "dragon shield", "dragon scale"],
                enabled: stock["Dragon Scale Shield"],
                status: this.priceStatus(player, 220, !stock["Dragon Scale Shield"], "owned"),
              },
              {
                key: "16",
                label: "Star Cloak",
                value: "star_cloak",
                detail: [...this.moneyParts(230), " - +5 spell damage"],
                aliases: ["cloak", "star cloak"],
                enabled: stock["Star Cloak"],
                status: this.priceStatus(player, 230, !stock["Star Cloak"], "owned"),
              },
              {
                key: "17",
                label: "Leave store",
                value: "leave",
                aliases: ["leave", "exit", "back", "q"],
              },
            );
          } else {
            options.push({
              key: "13",
              label: "Leave store",
              value: "leave",
              aliases: ["leave", "exit", "back", "q"],
            });
          }
        } else {
          options.push({
            key: "7",
            label: "Leave store",
            value: "leave",
            aliases: ["leave", "exit", "back", "q"],
          });
        }

        const subtitle = [
          "Whoop Nickels: ",
          ...this.moneyParts(player.money),
          ` | Health: ${statMeter(player.health, player.healthMax)} ${player.health}/${player.healthMax} | Mana: ${statMeter(player.mana, player.manaMax)} ${player.mana}/${player.manaMax}`,
        ];

        const choice = await this.chooseMenu(config.title || "Shop Menu", options, {
          prompt: "Shop choice: ",
          subtitle,
        });

        if (choice === "arcane") {
          this.buySpell(player, stock, "Arcane Blast", 45);
        } else if (choice === "small_potion") {
          this.buyItem(player, "Small Health Potion", 28);
        } else if (choice === "thunderstorm") {
          this.buySpell(player, stock, "Thunderstorm", 90);
        } else if (choice === "restoration") {
          this.buySpell(player, stock, "Restoration Incantation", 75);
        } else if (choice === "mana") {
          await this.buyMana(player);
        } else if (choice === "mana_flask") {
          this.buyManaFlask(player);
        } else if (choice === "big_potion") {
          this.buyItem(player, "Big Health Potion", 95);
        } else if (choice === "helmet") {
          this.buyEquipment(player, stock, "Glorious Helmet", 140, "armor", 5);
        } else if (choice === "boots") {
          this.buyEquipment(player, stock, "Mage Boots", 130, "extraDamage", 3);
        } else if (choice === "frost_nova") {
          this.buySpell(player, stock, "Frost Nova", 120);
        } else if (choice === "crystal_sword") {
          this.buyEquipment(player, stock, "Crystal Sword", 160, "weaponDamage", 8);
        } else if (choice === "phoenix_feather") {
          this.buyStockedItem(player, stock, "Phoenix Feather", 180);
        } else if (choice === "solar_beam") {
          this.buySpell(player, stock, "Solar Beam", 240);
        } else if (choice === "life_bloom") {
          this.buySpell(player, stock, "Life Bloom", 210);
        } else if (choice === "dragon_shield") {
          this.buyEquipment(player, stock, "Dragon Scale Shield", 220, "armor", 8);
        } else if (choice === "star_cloak") {
          this.buyEquipment(player, stock, "Star Cloak", 230, "extraDamage", 5);
        } else if (choice === "leave") {
          this.say(`\n${config.leaveText || "You leave the store."}`);
          return;
        }
      }
    }
  }

  window.addEventListener("DOMContentLoaded", async () => {
    const terminal = new Terminal(
      document.getElementById("terminal"),
      document.getElementById("terminal-output"),
    );
    await loadEncounterData();
    const game = new AdventureGame(terminal);
    await game.start();
  });
})();
