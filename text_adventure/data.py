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
}


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
