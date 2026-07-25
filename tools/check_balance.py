#!/usr/bin/env python3
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

for index, name in enumerate(LONG_ROAD_ENEMIES, start=1):
    monster = MONSTERS[name]
    basic = BASE_BASIC_DAMAGE + (index - 1) // 5
    enemy_turns = max(0, math.ceil(monster["health"] / basic) - 1)
    incoming = enemy_turns * monster["damage"]
    assert incoming < player["healthMax"], (name, monster, basic, incoming)
    assert monster["damage"] <= 10

assert MONSTERS["realmbound dragon"]["damage"] <= 18
assert MONSTERS["realmbound dragon"]["health"] <= 150
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

print("Balance and data-driven encounter checks passed.")
