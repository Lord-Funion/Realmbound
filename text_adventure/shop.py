"""Shop menus and purchase behavior."""

from .data import FROG_ATTACKS, SPELLS
from .pacing import ask, say
from .player import add_spell, sell_scraps
from .ui import MenuOption, choose_menu, money_text, normalize_choice, stat_meter


def _buy_spell(player, stock, spell_name, price):
    """Buy a one-time spell if it is affordable and still stocked."""
    if not stock.get(spell_name, True):
        say("\nThat spell is out of stock.", "quick")
        return
    if player["money"] < price:
        say("\nYou don't have enough money.", "quick")
        return

    player["money"] -= price
    add_spell(player, spell_name)
    stock[spell_name] = False
    say(f"\nYou learned {spell_name}.")
    say(f"You have {money_text(player['money'])} left.", "quick")


def _buy_item(player, item_name, price):
    """Buy a normal inventory item."""
    if player["money"] < price:
        say("\nYou don't have enough money.", "quick")
        return

    player["money"] -= price
    player["backpack"].append(item_name)
    say(f"\nYou bought a {item_name}.")
    say(f"You have {money_text(player['money'])} left.", "quick")


def _buy_mana_flask(player):
    """Buy a consumable mana refill."""
    price = 60
    if player["money"] < price:
        say("\nYou don't have enough Whoop Nickels.", "quick")
        return

    player["money"] -= price
    player["mana"] = min(player["manaMax"], player["mana"] + 35)
    say(f"\nYou drink a Mana Flask and recover to {player['mana']}/{player['manaMax']} mana.")
    say(f"You have {money_text(player['money'])} left.", "quick")


def _buy_mana(player):
    """Let the player permanently increase maximum mana."""
    price_each = 4
    while True:
        amount_text = normalize_choice(
            ask(f"\nMax mana to buy ({money_text(price_each)} each, 'all' for max, or 'back'): ")
        )
        if amount_text in {"back", "b", "cancel", "leave", "q"}:
            say("\nYou decide not to buy mana.", "quick")
            return
        if amount_text in {"all", "max"}:
            if player["money"] <= 0:
                say("\nYou don't have enough Whoop Nickels.", "quick")
                return
            amount = player["money"] // price_each
        elif amount_text.isdigit():
            amount = int(amount_text)
        else:
            say("\nPlease enter a number, 'all', or 'back'.", "quick")
            continue

        if amount <= 0:
            say("\nPlease enter a positive number.", "quick")
            continue
        cost = amount * price_each
        if player["money"] < cost:
            say("\nYou don't have enough Whoop Nickels.", "quick")
            return

        player["money"] -= cost
        player["mana"] += amount
        player["manaMax"] += amount
        say(f"\nYou bought {amount} max mana.")
        say(f"You have {money_text(player['money'])} left.", "quick")
        return


def _price_status(player, price, unavailable=False, unavailable_label="owned"):
    """Summarize affordability and one-time stock state for menu rows."""
    if unavailable:
        return unavailable_label
    if player["money"] < price:
        return f"need {money_text(price - player['money'])} more"
    return ""


def _buy_equipment(player, stock, item_name, price, stat_name, amount):
    """Buy one-time equipment and apply its permanent stat bonus."""
    if not stock.get(item_name, True):
        say("\nThat equipment is out of stock.", "quick")
        return
    if player["money"] < price:
        say("\nYou don't have enough money.", "quick")
        return

    player["money"] -= price
    player[stat_name] += amount
    player["backpack"].append(item_name)
    stock[item_name] = False
    say(f"\nYou bought {item_name}.")
    say(f"You have {money_text(player['money'])} left.", "quick")


def _buy_stocked_item(player, stock, item_name, price):
    if not stock.get(item_name, True):
        say("\nThat item is out of stock.", "quick")
        return
    if player["money"] < price:
        say("\nYou don't have enough Whoop Nickels.", "quick")
        return

    player["money"] -= price
    player["backpack"].append(item_name)
    stock[item_name] = False
    say(f"\nYou bought a {item_name}.")
    say(f"You have {money_text(player['money'])} left.", "quick")


def _buy_frog_attack(player, stock, stock_name, price, attack_name):
    if not player.get("frogMode"):
        say("\nYou need to keep the frog as your partner to use that.", "quick")
        return
    if not stock.get(stock_name, True):
        say("\nThat training book is already read.", "quick")
        return
    if player["money"] < price:
        say("\nYou don't have enough Whoop Nickels.", "quick")
        return

    player["money"] -= price
    from .player import add_frog_attack

    add_frog_attack(player, attack_name)
    stock[stock_name] = False
    say(f"\nThe frog learns {attack_name}.")
    say(f"You have {money_text(player['money'])} left.", "quick")


def _buy_frog_training(player, stock, stock_name, price, power=0, energy=0):
    if not player.get("frogMode"):
        say("\nYou need to keep the frog as your partner to use that.", "quick")
        return
    if not stock.get(stock_name, True):
        say("\nThat training is already complete.", "quick")
        return
    if player["money"] < price:
        say("\nYou don't have enough Whoop Nickels.", "quick")
        return

    player["money"] -= price
    player["frogPower"] += power
    player["frogEnergyMax"] += energy
    player["frogEnergy"] += energy
    stock[stock_name] = False
    say("\nThe frog trains until it looks unfairly confident.")
    say(f"You have {money_text(player['money'])} left.", "quick")


def run_shop(player, stock, advanced=False, legendary=False):
    """Run Harold's or Miss Costalot's shop menu."""
    sell_scraps(player)

    while True:
        options = [
            MenuOption(
                "1",
                "Arcane Blast",
                "arcane",
                f"{money_text(45)} - {SPELLS['Arcane Blast']['description']}",
                aliases=("arcane", "arcane blast", "spell 1"),
                enabled=stock.get("Arcane Blast", True),
                status=_price_status(
                    player,
                    45,
                    not stock.get("Arcane Blast", True),
                    "learned",
                ),
            ),
            MenuOption(
                "2",
                "Small Health Potion",
                "small_potion",
                f"{money_text(28)} - heals 15 health",
                aliases=("small", "small potion", "health potion", "potion"),
                status=_price_status(player, 28),
            ),
            MenuOption(
                "3",
                "Thunderstorm",
                "thunderstorm",
                f"{money_text(90)} - {SPELLS['Thunderstorm']['description']}",
                aliases=("thunder", "thunderstorm", "spell 3"),
                enabled=stock.get("Thunderstorm", True),
                status=_price_status(
                    player,
                    90,
                    not stock.get("Thunderstorm", True),
                    "learned",
                ),
            ),
            MenuOption(
                "4",
                "Restoration Incantation",
                "restoration",
                f"{money_text(75)} - {SPELLS['Restoration Incantation']['description']}",
                aliases=("restore", "restoration", "heal spell", "spell 4"),
                enabled=stock.get("Restoration Incantation", True),
                status=_price_status(
                    player,
                    75,
                    not stock.get("Restoration Incantation", True),
                    "learned",
                ),
            ),
            MenuOption(
                "5",
                "Add Mana",
                "mana",
                f"{money_text(4)} = +1 max mana",
                aliases=("mana", "add mana", "buy mana"),
                status="spend any amount" if player["money"] else "no money",
            ),
            MenuOption(
                "6",
                "Mana Flask",
                "mana_flask",
                f"{money_text(60)} - recover 35 mana now",
                aliases=("flask", "mana flask", "refill"),
                status=_price_status(player, 60),
            ),
        ]
        if advanced:
            options.extend(
                [
                    MenuOption(
                        "7",
                        "Big Health Potion",
                        "big_potion",
                        f"{money_text(95)} - restores full health",
                        aliases=("big", "big potion", "full potion"),
                        status=_price_status(player, 95),
                    ),
                    MenuOption(
                        "8",
                        "Glorious Helmet",
                        "helmet",
                        f"{money_text(140)} - +5 armor",
                        aliases=("helmet", "armor"),
                        enabled=stock.get("Glorious Helmet", True),
                        status=_price_status(
                            player,
                            140,
                            not stock.get("Glorious Helmet", True),
                            "owned",
                        ),
                    ),
                    MenuOption(
                        "9",
                        "Mage Boots",
                        "boots",
                        f"{money_text(130)} - +3 spell damage",
                        aliases=("boots", "mage boots", "damage"),
                        enabled=stock.get("Mage Boots", True),
                        status=_price_status(
                            player,
                            130,
                            not stock.get("Mage Boots", True),
                            "owned",
                        ),
                    ),
                ]
            )
            if player.get("frogMode"):
                options.extend(
                    [
                        MenuOption(
                            "10",
                            "Bubble Burp Codex",
                            "bubble_burp",
                            f"{money_text(70)} - {FROG_ATTACKS['Bubble Burp']['description']}",
                            aliases=("bubble", "bubble burp", "codex"),
                            enabled=stock.get("Bubble Burp Codex", True),
                            status=_price_status(player, 70, not stock.get("Bubble Burp Codex", True), "read"),
                        ),
                        MenuOption(
                            "11",
                            "Croak Fu Primer",
                            "croak_fu",
                            f"{money_text(85)} - +3 frog power",
                            aliases=("croak", "frog power", "primer"),
                            enabled=stock.get("Croak Fu Primer", True),
                            status=_price_status(player, 85, not stock.get("Croak Fu Primer", True), "read"),
                        ),
                    ]
                )
            else:
                options.extend(
                    [
                        MenuOption(
                            "10",
                            "Frost Nova",
                            "frost_nova",
                            f"{money_text(120)} - {SPELLS['Frost Nova']['description']}",
                            aliases=("frost", "frost nova"),
                            enabled=stock.get("Frost Nova", True),
                            status=_price_status(player, 120, not stock.get("Frost Nova", True), "learned"),
                        ),
                        MenuOption(
                            "11",
                            "Crystal Sword",
                            "crystal_sword",
                            f"{money_text(160)} - +8 basic attack damage",
                            aliases=("sword", "crystal sword"),
                            enabled=stock.get("Crystal Sword", True),
                            status=_price_status(player, 160, not stock.get("Crystal Sword", True), "owned"),
                        ),
                    ]
                )
            if legendary:
                options.extend(
                    [
                        MenuOption(
                            "12",
                            "Phoenix Feather",
                            "phoenix_feather",
                            f"{money_text(180)} - revives you once in combat",
                            aliases=("phoenix", "feather", "revive"),
                            enabled=stock.get("Phoenix Feather", True),
                            status=_price_status(player, 180, not stock.get("Phoenix Feather", True), "owned"),
                        ),
                        MenuOption(
                            "13",
                            "Dragon Scale Shield",
                            "dragon_shield",
                            f"{money_text(220)} - +8 armor",
                            aliases=("shield", "dragon shield"),
                            enabled=stock.get("Dragon Scale Shield", True),
                            status=_price_status(player, 220, not stock.get("Dragon Scale Shield", True), "owned"),
                        ),
                        MenuOption(
                            "14",
                            "Solar Beam",
                            "solar_beam",
                            f"{money_text(240)} - {SPELLS['Solar Beam']['description']}",
                            aliases=("solar", "solar beam"),
                            enabled=stock.get("Solar Beam", True),
                            status=_price_status(player, 240, not stock.get("Solar Beam", True), "learned"),
                        ),
                    ]
                )
            options.append(
                MenuOption(
                    str(len(options) + 1),
                    "Leave store",
                    "leave",
                    aliases=("leave", "exit", "back", "q"),
                )
            )
        else:
            options.append(
                MenuOption(
                    "7",
                    "Leave store",
                    "leave",
                    aliases=("leave", "exit", "back", "q"),
                )
            )

        subtitle = (
            f"Whoop Nickels: {money_text(player['money'])} | "
            f"Health: {stat_meter(player['health'], player['healthMax'])} "
            f"{player['health']}/{player['healthMax']} | "
            f"Mana: {stat_meter(player['mana'], player['manaMax'])} "
            f"{player['mana']}/{player['manaMax']}"
        )
        choice = choose_menu("Shop Menu", options, prompt="Shop choice: ", subtitle=subtitle)

        if choice == "arcane":
            _buy_spell(player, stock, "Arcane Blast", 45)
        elif choice == "small_potion":
            _buy_item(player, "Small Health Potion", 28)
        elif choice == "thunderstorm":
            _buy_spell(player, stock, "Thunderstorm", 90)
        elif choice == "restoration":
            _buy_spell(player, stock, "Restoration Incantation", 75)
        elif choice == "mana":
            _buy_mana(player)
        elif choice == "mana_flask":
            _buy_mana_flask(player)
        elif choice == "big_potion":
            _buy_item(player, "Big Health Potion", 95)
        elif choice == "helmet":
            _buy_equipment(player, stock, "Glorious Helmet", 140, "armor", 5)
        elif choice == "boots":
            _buy_equipment(player, stock, "Mage Boots", 130, "extraDamage", 3)
        elif choice == "bubble_burp":
            _buy_frog_attack(player, stock, "Bubble Burp Codex", 70, "Bubble Burp")
        elif choice == "croak_fu":
            _buy_frog_training(player, stock, "Croak Fu Primer", 85, power=3, energy=10)
        elif choice == "frost_nova":
            _buy_spell(player, stock, "Frost Nova", 120)
        elif choice == "crystal_sword":
            _buy_equipment(player, stock, "Crystal Sword", 160, "weaponDamage", 8)
        elif choice == "phoenix_feather":
            _buy_stocked_item(player, stock, "Phoenix Feather", 180)
        elif choice == "dragon_shield":
            _buy_equipment(player, stock, "Dragon Scale Shield", 220, "armor", 8)
        elif choice == "solar_beam":
            _buy_spell(player, stock, "Solar Beam", 240)
        elif choice == "leave":
            say("\nYou leave the store.", "quick")
            return
