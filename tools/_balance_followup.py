from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def update(path: str, old: str, new: str, count: int = 1) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    if old not in text:
        raise RuntimeError(f"Missing expected text in {path}: {old[:80]!r}")
    target.write_text(text.replace(old, new, count), encoding="utf-8")


update(
    "text_adventure/combat.py",
    'health_gain = min(max(18, player["healthMax"] // 6), player["healthMax"] - player["health"])',
    'health_gain = min(max(40, player["healthMax"] // 3), player["healthMax"] - player["health"])',
)
update(
    "web/app.js",
    "Math.max(18, Math.floor(player.healthMax / 6))",
    "Math.max(40, Math.floor(player.healthMax / 3))",
)
update(
    "text_adventure/data.py",
    '"realmbound dragon": {"health": 150, "damage": 18, "reward": 60}',
    '"realmbound dragon": {"health": 135, "damage": 14, "reward": 60}',
)
update(
    "web/app.js",
    '"realmbound dragon": {\n          "health": 150,\n          "damage": 18,\n          "reward": 60\n      }',
    '"realmbound dragon": {\n          "health": 135,\n          "damage": 14,\n          "reward": 60\n      }',
)
update(
    "text_adventure/player.py",
    "The player starts like a regular adventurer: no Whoop Nickels, no spells, basic\n    health, and enough mana to matter after learning magic.",
    "The player starts with a small safety fund, one potion, sturdier health, and\n    enough mana to experiment after learning magic.",
)
update(
    "story/encounter-guide.html",
    '<tr><td><code>enemy</code></td><td class="required">Required</td><td>The exact lowercase name of an enemy that already exists in the game\'s combat data.</td></tr>',
    '<tr><td><code>enemy</code></td><td class="optional">Battle only</td><td>The exact lowercase name of an enemy that already exists in the game\'s combat data.</td></tr>',
)
update(
    "story/encounter-guide.html",
    '<tr><td><code>intro</code></td><td class="optional">Optional</td><td>An array of text lines shown before the battle.</td></tr>',
    '<tr><td><code>intro</code></td><td class="optional">Optional</td><td>An array of text lines shown before any encounter or nested step.</td></tr>',
)

check = '''#!/usr/bin/env python3
"""Static fairness checks for Realmbound's required combat path."""
from __future__ import annotations

import math

from text_adventure.combat import BASE_BASIC_DAMAGE
from text_adventure.data import LONG_ROAD_ENEMIES, MONSTERS
from text_adventure.encounter_data import load
from text_adventure.player import create_player

player = create_player()
assert player["healthMax"] >= 120
assert player["manaMax"] >= 120
assert player["money"] >= 20
assert "Small Health Potion" in player["backpack"]

# Simulate the entire mandatory road with only basic attacks. Health carries
# between fights, normal victory recovery applies, and the existing roadside
# shrine restores up to 30 health after every fifth fight.
road_health = player["healthMax"]
for index, name in enumerate(LONG_ROAD_ENEMIES, start=1):
    monster = MONSTERS[name]
    basic = BASE_BASIC_DAMAGE + (index - 1) // 5
    enemy_turns = max(0, math.ceil(monster["health"] / basic) - 1)
    incoming = enemy_turns * monster["damage"]
    road_health -= incoming
    assert road_health > 0, ("road death", index, name, monster, basic, incoming)
    recovery = max(40, player["healthMax"] // 3)
    road_health = min(player["healthMax"], road_health + recovery)
    if index % 5 == 0:
        road_health = min(player["healthMax"], road_health + 30)
    assert monster["damage"] <= 10

# A fully progressed player can also survive the final boss with basic attacks.
dragon = MONSTERS["realmbound dragon"]
final_basic = BASE_BASIC_DAMAGE + len(LONG_ROAD_ENEMIES) // 5
dragon_turns = max(0, math.ceil(dragon["health"] / final_basic) - 1)
assert dragon_turns * dragon["damage"] < player["healthMax"]
assert dragon["damage"] <= 14
assert dragon["health"] <= 135
assert min(monster["reward"] for monster in MONSTERS.values()) >= 8

story = load()
assert story["schema_version"] >= 2
for encounter_id, expected_type in (
    ("mossy_lantern_church", "church"),
    ("last_chance_caravan", "shop"),
):
    assert story["data_encounters"][encounter_id]["type"] == expected_type
    scene_id = story["data_encounters"][encounter_id]["scene"]
    assert encounter_id in story["scenes"][scene_id]["after_scene"]

print("Cumulative road, final boss, and data-driven encounter checks passed.")
'''
(ROOT / "tools/check_balance.py").write_text(check, encoding="utf-8")
