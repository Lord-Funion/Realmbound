"""Player state, inventory, and stat screens."""

from collections import Counter
import random

from .data import SELLABLE_LOOT
from .pacing import say
from .terminal_colors import Fore, Style
from .ui import MenuOption, choose_menu, divider, money_text, stat_meter


def create_player():
    """Create a normal starting character.

    The player starts with a small safety fund, one potion, sturdier health, and
    enough mana to experiment after learning magic.
    """
    return {
        "name": "Adventurer",
        "money": 20,
        "health": 120,
        "healthMax": 120,
        "mana": 120,
        "manaMax": 120,
        "armor": 0,
        "weaponDamage": 0,
        "extraDamage": 0,
        "frogMode": False,
        "frogPower": 0,
        "frogEnergy": 0,
        "frogEnergyMax": 0,
        "roadProgress": 0,
        "backpack": ["Small Health Potion"],
        "spells": [],
        "frogAttacks": [],
    }


def add_spell(player, spell_name):
    """Teach a spell once; duplicate spell entries make menus confusing."""
    if spell_name not in player["spells"]:
        player["spells"].append(spell_name)


def add_frog_attack(player, attack_name):
    """Teach the frog route a combat trick once."""
    player.setdefault("frogAttacks", [])
    if attack_name not in player["frogAttacks"]:
        player["frogAttacks"].append(attack_name)


def activate_frog_partner(player):
    """Switch the player into the frog companion route."""
    player["frogMode"] = True
    player["frogPower"] = max(player.get("frogPower", 0), 4)
    player["frogEnergyMax"] = max(player.get("frogEnergyMax", 0), 25)
    player["frogEnergy"] = max(player.get("frogEnergy", 0), player["frogEnergyMax"])
    add_frog_attack(player, "Tongue Slap")


def print_stats(player):
    """Show the current player state in a compact, readable format."""
    divider("Player Stats")
    print(f"Whoop Nickels: {money_text(player['money'])}")
    print(
        f"Health: {Fore.RED}{stat_meter(player['health'], player['healthMax'])} "
        f"{player['health']}/{player['healthMax']}{Style.RESET_ALL}"
    )
    print(
        f"Mana: {Fore.BLUE}{stat_meter(player['mana'], player['manaMax'])} "
        f"{player['mana']}/{player['manaMax']}{Style.RESET_ALL}"
    )
    print(f"Armor: {Fore.LIGHTCYAN_EX}{player['armor']}{Style.RESET_ALL}")
    print(f"Spell Damage: {Fore.LIGHTMAGENTA_EX}+{player['extraDamage']}{Style.RESET_ALL}")
    if player.get("weaponDamage"):
        print(f"Weapon Damage: {Fore.LIGHTMAGENTA_EX}+{player['weaponDamage']}{Style.RESET_ALL}")

    spells = ", ".join(player["spells"]) if player["spells"] else "None"
    print(f"Spells: {Fore.MAGENTA}{spells}{Style.RESET_ALL}")
    if player.get("frogMode"):
        frog_attacks = ", ".join(player.get("frogAttacks", [])) or "None"
        print(
            f"Frog Energy: {Fore.GREEN}{stat_meter(player['frogEnergy'], player['frogEnergyMax'])} "
            f"{player['frogEnergy']}/{player['frogEnergyMax']}{Style.RESET_ALL}"
        )
        print(f"Frog Attacks: {Fore.GREEN}{frog_attacks}{Style.RESET_ALL}")

    if player["backpack"]:
        item_counts = Counter(player["backpack"])
        items = [
            f"{item} x{count}" if count > 1 else item
            for item, count in sorted(item_counts.items())
        ]
        print(f"Items: {Fore.LIGHTGREEN_EX}{', '.join(items)}{Style.RESET_ALL}\n")
    else:
        print(f"Items: {Fore.LIGHTGREEN_EX}None{Style.RESET_ALL}\n")


def sell_scraps(player):
    """Automatically sell monster junk when the player reaches a shop."""
    sold_anything = False
    for item in player["backpack"][:]:
        if item in SELLABLE_LOOT:
            worth = random.randint(8, 14)
            player["backpack"].remove(item)
            player["money"] += worth
            sold_anything = True
            say(f"\nYou sold a(n) {item} for {money_text(worth)}.", "quick")
    return sold_anything


def offer_potions(player):
    """Let the player drink one potion after dangerous scenes."""
    while True:
        max_health = player["healthMax"]
        big_count = player["backpack"].count("Big Health Potion")
        small_count = player["backpack"].count("Small Health Potion")

        if player["health"] >= max_health:
            if big_count or small_count:
                say("\nYour health is full, so you save your potions.", "quick")
            return False

        if not big_count and not small_count:
            say("\nNo health potions available.", "quick")
            return False

        subtitle = (
            f"Health: {Fore.RED}{stat_meter(player['health'], max_health)} "
            f"{player['health']}/{max_health}{Style.RESET_ALL}"
        )
        choice = choose_menu(
            "Potion Menu",
            [
                MenuOption(
                    "1",
                    "Drink Big Health Potion",
                    "big",
                    "restore to full",
                    aliases=("big", "big potion", "full"),
                    enabled=big_count > 0,
                    status=f"x{big_count}" if big_count else "none",
                ),
                MenuOption(
                    "2",
                    "Drink Small Health Potion",
                    "small",
                    "+30 health",
                    aliases=("small", "small potion"),
                    enabled=small_count > 0,
                    status=f"x{small_count}" if small_count else "none",
                ),
                MenuOption(
                    "3",
                    "Save potions",
                    "exit",
                    aliases=("exit", "leave", "back", "no", "n", "q"),
                ),
            ],
            prompt="Potion choice: ",
            subtitle=subtitle,
        )

        if choice == "big":
            player["health"] = max_health
            player["backpack"].remove("Big Health Potion")
            say(f"\nYour health is restored to {player['health']}.")
            break
        if choice == "small":
            player["health"] = min(max_health, player["health"] + 30)
            player["backpack"].remove("Small Health Potion")
            say(f"\nYour health is now {player['health']}.")
            break
        if choice == "exit":
            say("\nYou save your potions for later.", "quick")
            return False

    return True
