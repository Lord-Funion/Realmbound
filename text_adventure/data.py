"""Shared game data.

Keeping spells, monsters, and item names here makes the story files easier to
read and avoids magic strings scattered through combat and shops.
"""


SPELLS = {
    "Fireball": {
        "damage": 14,
        "manaCost": 12,
        "effects": {"burn": 2},
        "description": "Deals 14 damage and sets the target burning.",
    },
    "Arcane Blast": {
        "damage": 0,
        "manaCost": 32,
        "effects": {"stun": 2},
        "description": "Stuns an enemy for 2 turns.",
    },
    "Thunderstorm": {
        "damage": 32,
        "manaCost": 45,
        "description": "Deals 32 damage.",
    },
    "Restoration Incantation": {
        "healing": 24,
        "manaCost": 35,
        "description": "Heals 24 health in battle.",
    },
    "Frost Nova": {
        "damage": 18,
        "manaCost": 38,
        "effects": {"stun": 1},
        "description": "Deals 18 damage and freezes the enemy for 1 turn.",
    },
    "Solar Beam": {
        "damage": 45,
        "manaCost": 65,
        "description": "Deals 45 damage.",
    },
    "Life Bloom": {
        "healing": 45,
        "manaCost": 55,
        "description": "Heals 45 health in battle.",
    },
    "Lockio Reducto": {
        "description": "Unlocks sealed doors.",
    },
}


FROG_ATTACKS = {
    "Tongue Slap": {
        "damage": 8,
        "energyCost": 0,
        "description": "Free frog attack.",
    },
    "Bubble Burp": {
        "damage": 16,
        "energyCost": 8,
        "effects": {"burn": 2},
        "description": "Deals 16 damage and leaves the enemy bubbling.",
    },
    "Royal Croak": {
        "damage": 26,
        "energyCost": 14,
        "effects": {"stun": 1},
        "description": "Deals 26 damage and startles the enemy.",
    },
    "Snack Break": {
        "healing": 24,
        "energyCost": 12,
        "description": "The frog produces snacks and heals 24 health.",
    },
    "Moon Leap": {
        "damage": 38,
        "energyCost": 22,
        "description": "A heavy moonlit frog slam.",
    },
    "Dragonfly Dive": {
        "damage": 50,
        "energyCost": 30,
        "effects": {"stun": 1},
        "description": "A late-game dive that deals 50 damage and stuns.",
    },
}


MONSTERS = {
    "goblin": {
        "health": 32,
        "damage": 8,
        "attacks": ["punch", "screech", "headbutt"],
    },
    "troll": {
        "health": 52,
        "damage": 12,
        "attacks": ["club", "slam", "bite"],
    },
    "skeleton": {
        "health": 36,
        "damage": 15,
        "attacks": ["bone club", "bone scare", "bone headbutt"],
    },
    "werewolf": {
        "health": 68,
        "damage": 18,
        "attacks": ["claw", "bite", "howl"],
    },
    "ogre": {
        "health": 86,
        "damage": 24,
        "attacks": ["big club", "super smash", "stomp"],
    },
    "witch": {
        "health": 64,
        "damage": 16,
        "attacks": ["poison", "curse", "hex"],
    },
    "vampire": {
        "health": 82,
        "damage": 21,
        "attacks": ["transform into bat", "fangs", "suck blood"],
    },
    "gate rat": {
        "health": 22,
        "damage": 7,
        "attacks": ["rusty nibble", "ankle dash", "tiny ambush"],
    },
    "smoke imp": {
        "health": 38,
        "damage": 10,
        "attacks": ["soot slap", "ember pinch", "smoke cough"],
    },
    "bramble wolf": {
        "health": 54,
        "damage": 16,
        "attacks": ["thorn bite", "vine trip", "bark howl"],
    },
    "treasure mimic": {
        "health": 58,
        "damage": 18,
        "attacks": ["lid snap", "coin spit", "hinge bash"],
    },
    "curse candle": {
        "health": 45,
        "damage": 17,
        "attacks": ["wax splash", "blue flame", "bad birthday wish"],
    },
    "ice goblin": {
        "health": 72,
        "damage": 20,
        "attacks": ["snowball uppercut", "icicle jab", "freezing giggle"],
    },
    "snow bat": {
        "health": 48,
        "damage": 17,
        "attacks": ["frost bite", "wing slap", "sleet shriek"],
    },
    "shadow knight": {
        "health": 95,
        "damage": 25,
        "attacks": ["gloom slash", "helmet bonk", "midnight shove"],
    },
    "receipt wraith": {
        "health": 62,
        "damage": 19,
        "attacks": ["paper cut", "late fee", "ink cloud"],
    },
    "basement bat": {
        "health": 58,
        "damage": 18,
        "attacks": ["cape flutter", "fang tap", "ceiling dive"],
    },
    "sugar golem": {
        "health": 105,
        "damage": 27,
        "attacks": ["frosting fist", "sprinkle storm", "cookie crumble"],
    },
    "rust rat": {
        "health": 66,
        "damage": 20,
        "attacks": ["rust bite", "pipe scramble", "gear squeak"],
    },
    "glass cobra": {
        "health": 88,
        "damage": 28,
        "attacks": ["mirror fang", "shatter hiss", "scale flash"],
    },
    "crystal dragon": {
        "health": 145,
        "damage": 32,
        "attacks": ["rainbow sneeze", "crystal claw", "tail prism"],
    },
    "crown wraith": {
        "health": 110,
        "damage": 30,
        "attacks": ["royal glare", "cold decree", "crown toss"],
    },
    "lord dreadbiscuit": {
        "health": 180,
        "damage": 36,
        "attacks": ["crumb storm", "butter curse", "ego blast"],
    },
    "realmbound dragon": {
        "health": 260,
        "damage": 42,
        "attacks": ["starfire breath", "crownquake", "eclipse wingstorm", "ancient claw"],
    },
    "ashfall pilgrim": {
        "health": 96,
        "damage": 23,
        "attacks": ["ember staff", "cinder prayer", "ash cloak"],
    },
    "lantern jackal": {
        "health": 100,
        "damage": 24,
        "attacks": ["lamp bite", "oil slick", "howling flare"],
    },
    "mossbound knight": {
        "health": 108,
        "damage": 25,
        "attacks": ["root shield", "green blade", "helmet sprout"],
    },
    "mirror moth": {
        "health": 92,
        "damage": 26,
        "attacks": ["glass wing", "reflection flash", "powder dazzle"],
    },
    "ember librarian": {
        "health": 112,
        "damage": 27,
        "attacks": ["burning bookmark", "shushing flame", "index curse"],
    },
    "fogbank siren": {
        "health": 116,
        "damage": 28,
        "attacks": ["mist song", "harbor pull", "whiteout whisper"],
    },
    "tin crown bandit": {
        "health": 120,
        "damage": 29,
        "attacks": ["fake decree", "coin knife", "royal shove"],
    },
    "hollow beekeeper": {
        "health": 124,
        "damage": 30,
        "attacks": ["wax veil", "hive rattle", "stinger rain"],
    },
    "moonlit scarecrow": {
        "health": 128,
        "damage": 31,
        "attacks": ["straw jab", "moon grin", "field hex"],
    },
    "iron acorn brute": {
        "health": 136,
        "damage": 32,
        "attacks": ["oak punch", "iron shell", "squirrel panic"],
    },
    "velvet gargoyle": {
        "health": 132,
        "damage": 33,
        "attacks": ["soft stone claw", "curtain dive", "balcony crash"],
    },
    "clockwork eel": {
        "health": 118,
        "damage": 34,
        "attacks": ["gear bite", "static coil", "spring lash"],
    },
    "glacier monk": {
        "health": 140,
        "damage": 35,
        "attacks": ["frozen palm", "silent avalanche", "ice mantra"],
    },
    "briar drummer": {
        "health": 126,
        "damage": 36,
        "attacks": ["thorn rhythm", "snare root", "wild tempo"],
    },
    "marble banshee": {
        "health": 144,
        "damage": 37,
        "attacks": ["statue shriek", "grave echo", "cracked aria"],
    },
    "thunder yak": {
        "health": 150,
        "damage": 38,
        "attacks": ["storm charge", "horn thunder", "cloud stomp"],
    },
    "paper lantern fiend": {
        "health": 122,
        "damage": 39,
        "attacks": ["paper flame", "festival fright", "string snare"],
    },
    "copper wyvern": {
        "health": 156,
        "damage": 40,
        "attacks": ["coin-scale rake", "green fire", "roof snatch"],
    },
    "old road revenant": {
        "health": 148,
        "damage": 41,
        "attacks": ["mile marker", "dust hand", "forgotten shortcut"],
    },
    "saltwater specter": {
        "health": 152,
        "damage": 42,
        "attacks": ["brine wave", "anchor chill", "shipbell howl"],
    },
    "orchard mimic": {
        "health": 160,
        "damage": 43,
        "attacks": ["apple snap", "branch disguise", "basket bite"],
    },
    "candlewax duelist": {
        "health": 146,
        "damage": 44,
        "attacks": ["wick rapier", "melting feint", "flame salute"],
    },
    "rune-tusk boar": {
        "health": 168,
        "damage": 45,
        "attacks": ["glyph gore", "mud ward", "tusk spell"],
    },
    "midnight tax collector": {
        "health": 154,
        "damage": 46,
        "attacks": ["late fee", "receipt lash", "audit glare"],
    },
    "feathered basilisk": {
        "health": 162,
        "damage": 47,
        "attacks": ["plume stare", "stone chirp", "talon flash"],
    },
    "broken compass spirit": {
        "health": 158,
        "damage": 48,
        "attacks": ["northless pull", "needle spin", "lost road"],
    },
    "jewel wasp swarm": {
        "health": 170,
        "damage": 49,
        "attacks": ["ruby sting", "buzzing crown", "gem cloud"],
    },
    "singing stump": {
        "health": 166,
        "damage": 50,
        "attacks": ["root chorus", "bark note", "splinter solo"],
    },
    "blackglass panther": {
        "health": 176,
        "damage": 51,
        "attacks": ["mirror pounce", "shadow claw", "glass growl"],
    },
    "sunken bell knight": {
        "health": 184,
        "damage": 52,
        "attacks": ["drowned chime", "rusted lance", "undertow step"],
    },
    "nettle witchling": {
        "health": 172,
        "damage": 53,
        "attacks": ["sting charm", "green hex", "thorn wink"],
    },
    "storm cellar troll": {
        "health": 190,
        "damage": 54,
        "attacks": ["barrel throw", "basement boom", "storm burp"],
    },
    "silver mask rogue": {
        "health": 178,
        "damage": 55,
        "attacks": ["mask flash", "quiet dagger", "vanishing bow"],
    },
    "bonewheel racer": {
        "health": 182,
        "damage": 56,
        "attacks": ["wheel crash", "rib spoke", "graveyard lap"],
    },
    "spellbook leech": {
        "health": 188,
        "damage": 57,
        "attacks": ["page drain", "ink bite", "borrowed spell"],
    },
    "cloud anvil giant": {
        "health": 208,
        "damage": 58,
        "attacks": ["sky hammer", "anvil drop", "forge thunder"],
    },
    "porcelain hydra": {
        "health": 202,
        "damage": 59,
        "attacks": ["china fang", "teacup roar", "seven saucers"],
    },
    "scarecrow magistrate": {
        "health": 194,
        "damage": 60,
        "attacks": ["field warrant", "straw verdict", "gavel stick"],
    },
    "obsidian choir": {
        "health": 210,
        "damage": 61,
        "attacks": ["black hymn", "shard harmony", "echo cut"],
    },
    "frostroot colossus": {
        "health": 224,
        "damage": 62,
        "attacks": ["winter branch", "rootquake", "snow crown"],
    },
    "honeycomb horror": {
        "health": 198,
        "damage": 63,
        "attacks": ["sticky maw", "hexagon swarm", "golden sting"],
    },
    "brass cathedral rook": {
        "health": 218,
        "damage": 64,
        "attacks": ["bell tower dive", "brass wing", "sanctuary slam"],
    },
    "map-eating serpent": {
        "health": 206,
        "damage": 65,
        "attacks": ["cartography bite", "folded coil", "legend swallow"],
    },
    "velvet thunderlord": {
        "health": 230,
        "damage": 66,
        "attacks": ["royal thunder", "soft lightning", "storm decree"],
    },
    "eclipse ferryman": {
        "health": 220,
        "damage": 67,
        "attacks": ["black oar", "river shadow", "fare curse"],
    },
    "crownless lion": {
        "health": 236,
        "damage": 68,
        "attacks": ["mane flare", "throne roar", "claw decree"],
    },
    "dream ash phantom": {
        "health": 214,
        "damage": 69,
        "attacks": ["sleep cinder", "nightmare veil", "pillow grave"],
    },
    "seven-key jailer": {
        "health": 242,
        "damage": 70,
        "attacks": ["keyring crush", "cell door slam", "warden glare"],
    },
    "realmquake titan": {
        "health": 260,
        "damage": 72,
        "attacks": ["continent stomp", "fault line", "mountain backhand"],
    },
    "calendar dragon": {
        "health": 280,
        "damage": 74,
        "attacks": ["lost month", "deadline flame", "year-end wing"],
    },
}


LONG_ROAD_ENEMIES = (
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
)


LOOT_DROPS = [
    "Suspicious Gold Nugget",
    "Metal Scraps of Mystery",
    "Pointy Monster Tooth",
    "Rotten Flesh",
    "Small Health Potion",
    "Mystery Goop",
    "Strange Liquid",
    "Gnarled Toenail",
]


SELLABLE_LOOT = {
    "Suspicious Gold Nugget",
    "Metal Scraps of Mystery",
    "Pointy Monster Tooth",
    "Rotten Flesh",
    "Mystery Goop",
    "Strange Liquid",
    "Gnarled Toenail",
}
