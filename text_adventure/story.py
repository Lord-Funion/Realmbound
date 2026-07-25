"""Main story flow for the text adventure.

Each scene is a small function. That keeps the story readable and makes it
easier to change one encounter without scrolling through the whole game.
"""

import getpass
import random
from pathlib import Path

from . import cloud_saves
from .combat import GameOver, game_over, spell_fight
from .data import LONG_ROAD_ENEMIES
from .encounter_data import additions, encounter
from .logo import show_startup_logo
from .pacing import ask, say, set_autosave_hook, set_quick_menu_hook
from .player import activate_frog_partner, add_frog_attack, add_spell, create_player, offer_potions, print_stats
from .save_system import (
    SaveError,
    default_save_path,
    list_save_files,
    load_game,
    load_game_text,
    make_save_text,
    path_from_player_input,
    write_save_text,
)
from .shop import run_shop
from .terminal_colors import Fore, Style
from .ui import MenuOption, ask_choice, choose_menu, money_text


FINISHED_SCENE = "finished"
EXIT_LABEL = "Exit Game"
SCENE_ORDER = (
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
)
SCENE_TITLES = {
    "intro": "Chocolate Frog",
    "wizard": "Rumblerod",
    "locked_door": "Locked Door",
    "first_goblin": "First Goblin",
    "village": "Village",
    "forest": "Forest Trail",
    "twin_doors": "Twin Doors",
    "witch": "Witch",
    "mountain_pass": "Mountain Pass",
    "moonlit_market": "Moonlit Market",
    "vampire_castle": "Vampire Castle",
    "false_throne": "False Throne",
    "underkeep": "Underkeep",
    "clocktower": "Clocktower",
    "well": "Old Well",
    "hundred_day_road": "The Hundred-Day Road",
    "dragon_gate": "Dragon Gate",
    "final_battle": "Final Battle",
    FINISHED_SCENE: "Finished Game",
}


class ExitGame(SystemExit):
    """Raised when the player chooses an explicit terminal Exit option."""


def _exit_game():
    say("\nGoodbye.", "quick")
    raise ExitGame(0)


def yes_no(prompt):
    """Ask a yes/no question until the player gives a valid answer."""
    return ask_choice(
        prompt,
        {
            "yes": ("yes", "y", "1"),
            "no": ("no", "n", "2"),
        },
        "\nPlease answer yes or no.",
    )


def fight_or_run(prompt="\nDo you fight or run? "):
    """Ask for a combat choice until it is valid."""
    return ask_choice(
        prompt,
        {
            "fight": ("fight", "f", "1"),
            "run": ("run", "r", "2"),
        },
        "\nPlease choose fight or run.",
    )


def choose_left_or_right(prompt):
    """Ask for a path or door choice until it is valid."""
    return ask_choice(
        prompt,
        {
            "left": ("left", "l", "1"),
            "right": ("right", "r", "2"),
        },
        "\nPlease choose left or right.",
    )


def _create_shop_stock():
    return {
        "Arcane Blast": True,
        "Thunderstorm": True,
        "Restoration Incantation": True,
        "Frost Nova": True,
        "Solar Beam": True,
        "Life Bloom": True,
        "Glorious Helmet": True,
        "Mage Boots": True,
        "Crystal Sword": True,
        "Phoenix Feather": True,
        "Dragon Scale Shield": True,
        "Star Cloak": True,
        "Croak Fu Primer": True,
        "Bubble Burp Codex": True,
        "Royal Croak Sheet Music": True,
        "Snack Break Cookbook": True,
        "Moon Leap Manual": True,
        "Golden Fly Protein": True,
        "Dragonfly Tactics": True,
        "Clockwork Compass": True,
        "Old Bell Manual": True,
        "Well Whisper Notes": True,
    }


def _new_state():
    return {
        "player": create_player(),
        "shop_stock": _create_shop_stock(),
        "next_scene": SCENE_ORDER[0],
    }


def _scene_title(scene_id):
    return SCENE_TITLES.get(scene_id, scene_id.replace("_", " ").title())


def _next_scene(scene_id):
    index = SCENE_ORDER.index(scene_id)
    if index + 1 >= len(SCENE_ORDER):
        return FINISHED_SCENE
    return SCENE_ORDER[index + 1]


def _normalize_int(value, name):
    if isinstance(value, bool) or not isinstance(value, int):
        raise SaveError(f"Save field '{name}' is not a valid number.")
    return value


def _normalize_string_list(value, name):
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise SaveError(f"Save field '{name}' is not a valid list.")
    return list(value)


def _normalize_bool(value, name):
    if not isinstance(value, bool):
        raise SaveError(f"Save field '{name}' is not a valid true/false value.")
    return value


def _normalize_state(raw_state):
    if not isinstance(raw_state, dict):
        raise SaveError("The save does not contain game state.")

    raw_player = raw_state.get("player")
    if not isinstance(raw_player, dict):
        raise SaveError("The save does not contain a valid player.")

    player = create_player()
    name = raw_player.get("name", player["name"])
    if not isinstance(name, str):
        raise SaveError("Save field 'name' is not valid text.")
    player["name"] = " ".join(name.split()) or "Adventurer"

    for key in (
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
    ):
        player[key] = _normalize_int(raw_player.get(key, player[key]), key)
    player["roadProgress"] = max(0, min(player["roadProgress"], len(LONG_ROAD_ENEMIES)))
    player["frogMode"] = _normalize_bool(raw_player.get("frogMode", player["frogMode"]), "frogMode")
    player["backpack"] = _normalize_string_list(raw_player.get("backpack", []), "backpack")
    player["spells"] = _normalize_string_list(raw_player.get("spells", []), "spells")
    player["frogAttacks"] = _normalize_string_list(
        raw_player.get("frogAttacks", player["frogAttacks"]),
        "frogAttacks",
    )
    if "Magic Wand" not in player["backpack"] and "Magical Chocolate Frog" in player["backpack"]:
        activate_frog_partner(player)
    if player["frogMode"] and not player["frogAttacks"]:
        add_frog_attack(player, "Tongue Slap")

    raw_stock = raw_state.get("shop_stock", {})
    if not isinstance(raw_stock, dict):
        raise SaveError("The save does not contain valid shop stock.")

    shop_stock = _create_shop_stock()
    for item_name in shop_stock:
        value = raw_stock.get(item_name, shop_stock[item_name])
        if not isinstance(value, bool):
            raise SaveError(f"Save field '{item_name}' is not valid shop stock.")
        shop_stock[item_name] = value

    next_scene = raw_state.get("next_scene")
    if next_scene not in SCENE_ORDER and next_scene != FINISHED_SCENE:
        raise SaveError("The save points to an unknown story checkpoint.")

    return {
        "player": player,
        "shop_stock": shop_stock,
        "next_scene": next_scene,
    }


def _load_state_from_payload(payload):
    if not isinstance(payload, dict):
        raise SaveError("The save payload is not valid.")
    if payload.get("game") != "Adventure Game":
        raise SaveError("This save belongs to a different game.")
    return _normalize_state(payload.get("state"))


def _load_state_from_path(path):
    return _load_state_from_payload(load_game(path))


def _load_state_from_text(save_text):
    return _load_state_from_payload(load_game_text(save_text))


def _save_detail(path):
    try:
        payload = load_game(path)
        state = _normalize_state(payload.get("state"))
    except SaveError:
        return "unreadable or tampered"

    player = state["player"]
    saved_at = payload.get("saved_at", "unknown time")
    return f"{_scene_title(state['next_scene'])}, {money_text(player['money'])}, saved {saved_at}"


def _save_state_interactive(state):
    suggested_path = default_save_path()
    typed_path = ask(f"\nSave name or path [{suggested_path.name}]: ")
    path = suggested_path if not typed_path else path_from_player_input(typed_path, for_save=True)
    save_text = make_save_text(state)

    try:
        final_path = write_save_text(save_text, path)
    except OSError as exc:
        say(f"\nSave failed: {exc}", "quick")
        return

    say(f"\nSaved encrypted checkpoint to {final_path}.", "quick")
    if cloud_saves.is_signed_in():
        try:
            cloud_saves.upload_save(final_path.stem, save_text)
        except cloud_saves.CloudSaveError as exc:
            say(f"\nCloud sync failed: {exc}", "quick")
        else:
            say(f"\nSynced cloud save slot '{final_path.stem}'.", "quick")


def _cloud_status():
    try:
        api_url = cloud_saves.current_api_url()
    except cloud_saves.CloudSaveError as exc:
        api_part = f"API URL problem: {exc}"
    else:
        api_part = f"API: {api_url}"

    if cloud_saves.is_signed_in():
        account_part = f"Signed in: {cloud_saves.current_username()}"
    else:
        account_part = "Not signed in"
    return f"{api_part} | {account_part}"


def _cloud_register():
    username = ask("\nChoose cloud username: ")
    if not username:
        say("\nNo username entered.", "quick")
        return

    password = getpass.getpass("Choose cloud password: ").strip()
    confirm = getpass.getpass("Confirm cloud password: ").strip()
    if password != confirm:
        say("\nPasswords did not match.", "quick")
        return

    try:
        cloud_saves.register(username, password)
    except cloud_saves.CloudSaveError as exc:
        say(f"\nCloud registration failed: {exc}", "quick")
    else:
        say(f"\nSigned in to cloud saves as {cloud_saves.current_username()}.", "quick")


def _cloud_login():
    username = ask("\nCloud username: ")
    if not username:
        say("\nNo username entered.", "quick")
        return

    password = getpass.getpass("Cloud password: ").strip()
    try:
        cloud_saves.login(username, password)
    except cloud_saves.CloudSaveError as exc:
        say(f"\nCloud sign-in failed: {exc}", "quick")
    else:
        say(f"\nSigned in to cloud saves as {cloud_saves.current_username()}.", "quick")


def _cloud_upload_current(state):
    if state is None:
        say("\nStart or load a game before uploading a cloud save.", "quick")
        return
    if not cloud_saves.is_signed_in():
        say("\nSign in before uploading cloud saves.", "quick")
        return

    typed_slot = ask("\nCloud save slot [autosave]: ")
    slot_name = cloud_saves.normalize_slot_name(typed_slot or "autosave")
    save_text = make_save_text(state)

    try:
        cloud_saves.upload_save(slot_name, save_text)
    except cloud_saves.CloudSaveError as exc:
        say(f"\nCloud upload failed: {exc}", "quick")
    else:
        say(f"\nUploaded cloud save slot '{slot_name}'.", "quick")


def _cloud_load_interactive():
    if not cloud_saves.is_signed_in():
        say("\nSign in before loading cloud saves.", "quick")
        return None

    try:
        cloud_slots = cloud_saves.list_saves()
    except cloud_saves.CloudSaveError as exc:
        say(f"\nCloud saves are unavailable: {exc}", "quick")
        return None

    options = []
    for index, cloud_slot in enumerate(cloud_slots[:9], start=1):
        slot_name = cloud_slot.get("slot_name", "")
        if not slot_name:
            continue
        updated_at = cloud_slot.get("updated_at", "unknown time")
        options.append(
            MenuOption(
                str(index),
                slot_name,
                slot_name,
                f"updated {updated_at}",
                aliases=(slot_name,),
            )
        )

    if not options:
        say("\nNo cloud saves found for this account.", "quick")
        return None

    options.append(
        MenuOption(
            str(len(options) + 1),
            "Back",
            "back",
            aliases=("back", "cancel"),
        )
    )
    options.append(
        MenuOption(
            str(len(options) + 1),
            EXIT_LABEL,
            "exit",
            aliases=("exit", "quit", "q"),
        )
    )

    slot_name = choose_menu(
        "Load Cloud Save",
        options,
        prompt="Cloud save choice: ",
        subtitle="Downloaded cloud saves are also copied into saves/ for offline loading.",
    )
    if slot_name == "back":
        return None
    if slot_name == "exit":
        _exit_game()

    try:
        response = cloud_saves.download_save(slot_name)
        save_text = response["save_data"]
        state = _load_state_from_text(save_text)
    except (cloud_saves.CloudSaveError, SaveError) as exc:
        say(f"\nCloud load failed: {exc}", "quick")
        return None

    local_path = default_save_path(f"cloud_{slot_name}")
    try:
        write_save_text(save_text, local_path)
    except OSError as exc:
        say(f"\nLoaded cloud save, but local copy failed: {exc}", "quick")
    else:
        say(f"\nDownloaded cloud save to {local_path}.", "quick")

    say(f"\nLoaded cloud save slot '{slot_name}'.", "quick")
    return state


def _cloud_menu(current_state=None):
    while True:
        options = []
        if cloud_saves.is_signed_in():
            next_key = 1
            if current_state is not None:
                options.append(
                    MenuOption(
                        str(next_key),
                        "Upload Current Save",
                        "upload",
                        aliases=("upload", "sync", "save"),
                    )
                )
                next_key += 1
            options.extend(
                [
                    MenuOption(
                        str(next_key),
                        "Load Cloud Save",
                        "load",
                        aliases=("load", "download"),
                    ),
                    MenuOption(
                        str(next_key + 1),
                        "Sign Out",
                        "logout",
                        aliases=("logout", "sign out"),
                    ),
                    MenuOption(
                        str(next_key + 2),
                        "Back",
                        "back",
                        aliases=("back", "cancel"),
                    ),
                    MenuOption(
                        str(next_key + 3),
                        EXIT_LABEL,
                        "exit",
                        aliases=("exit", "quit", "q"),
                    ),
                ]
            )
        else:
            options.extend(
                [
                    MenuOption("1", "Create Account", "register", aliases=("register", "create")),
                    MenuOption("2", "Sign In", "login", aliases=("login", "sign in")),
                    MenuOption("3", "Back", "back", aliases=("back", "cancel")),
                    MenuOption("4", EXIT_LABEL, "exit", aliases=("exit", "quit", "q")),
                ]
            )

        choice = choose_menu(
            "Cloud Saves",
            options,
            prompt="Cloud choice: ",
            subtitle=_cloud_status(),
        )

        if choice == "register":
            _cloud_register()
        elif choice == "login":
            _cloud_login()
        elif choice == "upload":
            _cloud_upload_current(current_state)
        elif choice == "load":
            loaded_state = _cloud_load_interactive()
            if loaded_state is not None:
                return loaded_state
        elif choice == "logout":
            cloud_saves.sign_out()
            say("\nSigned out of cloud saves on this device.", "quick")
        elif choice == "back":
            return None
        elif choice == "exit":
            _exit_game()


def _load_state_interactive():
    while True:
        save_files = list_save_files()
        options = []
        for index, path in enumerate(save_files[:9], start=1):
            options.append(
                MenuOption(
                    str(index),
                    path.name,
                    str(path),
                    _save_detail(path),
                    aliases=(path.stem, path.name),
                )
            )

        custom_key = str(len(options) + 1)
        options.append(
            MenuOption(
                custom_key,
                "Load other file",
                "custom",
                "type a .tasave path",
                aliases=("custom", "other", "file", "path"),
            )
        )
        options.append(
            MenuOption(
                str(len(options) + 1),
                "Back",
                "back",
                aliases=("back", "cancel"),
            )
        )
        options.append(
            MenuOption(
                str(len(options) + 1),
                EXIT_LABEL,
                "exit",
                aliases=("exit", "quit", "q"),
            )
        )

        choice = choose_menu(
            "Load Game",
            options,
            prompt="Load choice: ",
            subtitle="Encrypted save files end in .tasave.",
        )
        if choice == "back":
            return None
        if choice == "exit":
            _exit_game()
        if choice == "custom":
            typed_path = ask("\nSave file path: ")
            if not typed_path:
                say("\nNo file selected.", "quick")
                continue
            path = path_from_player_input(typed_path)
        else:
            path = Path(choice)

        try:
            state = _load_state_from_path(path)
        except SaveError as exc:
            say(f"\nLoad failed: {exc}", "quick")
            continue

        say(f"\nLoaded save from {path}.", "quick")
        return state


def _autosave_state(state, sync_cloud=False):
    save_text = make_save_text(state)
    try:
        write_save_text(save_text, default_save_path("autosave"))
    except OSError:
        return False, False

    cloud_synced = False
    if sync_cloud and cloud_saves.is_signed_in():
        try:
            cloud_saves.upload_save("autosave", save_text, timeout=2)
        except cloud_saves.CloudSaveError:
            cloud_synced = False
        else:
            cloud_synced = True
    return True, cloud_synced


def _checkpoint_menu(state):
    while True:
        subtitle = f"Next: {_scene_title(state['next_scene'])} | Autosave: saves/autosave.tasave"
        if cloud_saves.is_signed_in():
            subtitle += f" | Cloud: {cloud_saves.current_username()}"
        choice = choose_menu(
            "Checkpoint",
            [
                MenuOption("1", "Continue", "continue", aliases=("continue", "c", "next")),
                MenuOption("2", "Save Game", "save", aliases=("save", "s")),
                MenuOption("3", "Load Game", "load", aliases=("load", "l")),
                MenuOption("4", "Cloud Saves", "cloud", aliases=("cloud", "online", "sync")),
                MenuOption("5", EXIT_LABEL, "exit", aliases=("exit", "quit", "q")),
            ],
            prompt="Checkpoint choice: ",
            subtitle=subtitle,
        )

        if choice == "continue":
            return state
        if choice == "save":
            _save_state_interactive(state)
        elif choice == "load":
            loaded_state = _load_state_interactive()
            if loaded_state is not None:
                return loaded_state
        elif choice == "cloud":
            loaded_state = _cloud_menu(state)
            if loaded_state is not None:
                return loaded_state
        elif choice == "exit":
            _exit_game()


def _run_scene(scene_id, player, shop_stock):
    if scene_id == "intro":
        intro_scene(player)
    elif scene_id == "wizard":
        wizard_scene(player)
    elif scene_id == "locked_door":
        locked_door_scene(player)
    elif scene_id == "first_goblin":
        first_goblin_scene(player)
    elif scene_id == "village":
        village_scene(player, shop_stock)
    elif scene_id == "forest":
        forest_scene(player, shop_stock)
    elif scene_id == "twin_doors":
        twin_doors_scene(player)
    elif scene_id == "witch":
        witch_scene(player)
    elif scene_id == "mountain_pass":
        mountain_pass_scene(player)
    elif scene_id == "moonlit_market":
        moonlit_market_scene(player, shop_stock)
    elif scene_id == "vampire_castle":
        vampire_castle_scene(player)
    elif scene_id == "false_throne":
        false_throne_scene(player, shop_stock)
    elif scene_id == "underkeep":
        underkeep_scene(player)
    elif scene_id == "clocktower":
        clocktower_scene(player, shop_stock)
    elif scene_id == "well":
        well_scene(player)
    elif scene_id == "hundred_day_road":
        hundred_day_road_scene(player, shop_stock)
    elif scene_id == "dragon_gate":
        dragon_gate_scene(player, shop_stock)
    elif scene_id == "final_battle":
        final_battle_scene(player)
    else:
        raise SaveError("Unknown story checkpoint.")

    for encounter_id in additions(scene_id):
        _run_json_encounter(encounter_id, player, shop_stock)


def _json_lines(value):
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(line) for line in value]
    return [str(value)]


def _show_json_text(value, pace="beat"):
    for line in _json_lines(value):
        if line:
            say("\n" + line, pace)


def _json_money(value):
    if isinstance(value, dict):
        return random.randint(int(value.get("min", 0)), int(value.get("max", 0)))
    return int(value)


def _apply_json_rewards(rewards, player):
    for reward in rewards or []:
        if not isinstance(reward, dict):
            continue
        if "item" in reward:
            player["backpack"].append(str(reward["item"]))
        if "money" in reward:
            amount = _json_money(reward["money"])
            player["money"] += amount
            say(f"\nYou receive {money_text(amount)}.", "quick")
        if "health" in reward:
            amount = max(0, int(reward["health"]))
            gained = min(amount, player["healthMax"] - player["health"])
            player["health"] += gained
            say(f"\nHealth +{gained}.", "quick")
        if "mana" in reward:
            amount = max(0, int(reward["mana"]))
            gained = min(amount, player["manaMax"] - player["mana"])
            player["mana"] += gained
            say(f"\nMana +{gained}.", "quick")


def _restore_json_player(player, restore):
    restore = restore if isinstance(restore, dict) else {"health": "full", "mana": "full"}
    gains = {}
    for stat, maximum in (("health", "healthMax"), ("mana", "manaMax")):
        value = restore.get(stat)
        if value is None:
            gains[stat] = 0
            continue
        before = player[stat]
        if value == "full":
            player[stat] = player[maximum]
        else:
            player[stat] = min(player[maximum], player[stat] + max(0, int(value)))
        gains[stat] = player[stat] - before
    return gains


def _run_json_step(step, player, shop_stock):
    if not isinstance(step, dict):
        raise SaveError("A custom encounter step must be an object.")

    step_type = step.get("type", "text")
    if step_type == "sequence":
        _show_json_text(step.get("intro"))
        _run_json_steps(step.get("steps", []), player, shop_stock)
        return

    if step_type == "text":
        _show_json_text(step.get("text", step.get("lines")))
        return

    if step_type == "choice":
        _show_json_text(step.get("intro"))
        answer = yes_no(step.get("prompt", "\nDo you continue? (yes/no): "))
        _run_json_steps(step.get(answer, []), player, shop_stock)
        return

    if step_type == "battle":
        _show_json_text(step.get("intro"))
        if step.get("choice") == "fight_or_run" and fight_or_run(step.get("prompt", "\nDo you fight or run? ")) == "run":
            result = step.get("run", {})
            _show_json_text(result.get("text"))
            if result.get("game_over"):
                game_over(player)
            return
        spell_fight(step["enemy"], player)
        victory = step.get("victory", {})
        _apply_json_rewards(victory.get("rewards", []), player)
        _show_json_text(victory.get("text"), "quick")
        if victory.get("offer_potions"):
            offer_potions(player)
        return

    if step_type == "shop":
        _show_json_text(step.get("intro"))
        optional = bool(step.get("optional", step.get("prompt") is not None))
        if optional and yes_no(step.get("prompt", "\nVisit the shop? (yes/no): ")) == "no":
            _show_json_text(step.get("decline_text"), "quick")
            return
        _show_json_text(step.get("enter_text"), "quick")
        run_shop(
            player,
            shop_stock,
            advanced=bool(step.get("advanced", False)),
            legendary=bool(step.get("legendary", False)),
            title=step.get("name", "Shop Menu"),
            leave_text=step.get("leave_text", "You leave the store."),
        )
        return

    if step_type in {"church", "rest"}:
        _show_json_text(step.get("intro"))
        optional = bool(step.get("optional", True))
        default_prompt = f"\nEnter {step.get('name', 'the church')}? (yes/no): "
        if optional and yes_no(step.get("prompt", default_prompt)) == "no":
            _show_json_text(step.get("decline_text", "You continue down the road."), "quick")
            return
        _show_json_text(step.get("enter_text"), "quick")
        gains = _restore_json_player(player, step.get("restore"))
        _show_json_text(
            step.get(
                "rest_text",
                f"You rest safely. Health +{gains['health']}, mana +{gains['mana']}.",
            ),
            "beat",
        )
        return

    if step_type == "reward":
        _show_json_text(step.get("intro"))
        _apply_json_rewards(step.get("rewards", []), player)
        _show_json_text(step.get("text"), "quick")
        return

    raise SaveError(f"Unsupported custom encounter type: {step_type}")


def _run_json_steps(steps, player, shop_stock):
    for step in steps or []:
        _run_json_step(step, player, shop_stock)


def _run_json_encounter(encounter_id, player, shop_stock):
    entry = encounter(encounter_id)
    _run_json_step(entry, player, shop_stock)



def _extra_fight(player, monster_name, intro, run_text):
    say(f"\n{intro}", "beat")
    if fight_or_run() == "run":
        say(f"\n{run_text}", "beat")
        game_over(player)
    spell_fight(monster_name, player)
    offer_potions(player)


def _visit_church(player, church_name, automatic=False):
    """Offer a quiet sanctuary without turning checkpoints into another menu."""
    say(f"\nYou arrive at {church_name}. Its doors stand open and warm lamplight fills the road.")
    if not automatic and yes_no("\nRest inside the church? (yes/no): ") == "no":
        say("\nYou leave the sanctuary quiet for the next traveler.", "quick")
        return False

    health_gain = max(0, player["healthMax"] - player["health"])
    mana_gain = max(0, player["manaMax"] - player["mana"])
    player["health"] = player["healthMax"]
    player["mana"] = player["manaMax"]

    if health_gain or mana_gain:
        say(
            f"\nThe church bells ring once. Health +{health_gain}, mana +{mana_gain}; "
            "both are now fully restored.",
            "beat",
        )
    else:
        say("\nYou rest beneath the painted windows. You were already fully restored.", "beat")
    return True


def _finish_game(player):
    say("\nThe Realmbound Dragon's storm breaks apart into silver sparks above the saved realm.", "scene")
    say(f"\nGood job, {player.get('name', 'Adventurer')}, you have completed the game.", "scene")
    say("\nCredits: Realmbound by Thunderstruck7 and Lord Funion.", "scene")
    say(f"\nTHE END\nYou finished with {money_text(player['money'])}.", "none")
    _postgame_menu(player)


def _postgame_has(player, item):
    return item in player["backpack"]


def _postgame_add_once(player, item):
    if not _postgame_has(player, item):
        player["backpack"].append(item)
        return True
    return False


def _postgame_spend(player, amount):
    if player["money"] < amount:
        say(f"\nYou need {money_text(amount - player['money'])} more.", "quick")
        return False
    player["money"] -= amount
    return True


def _postgame_status(player):
    milestones = [
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
    ]
    unlocked = [item for item in milestones if _postgame_has(player, item)]
    say(f"\nWhoop Nickels: {money_text(player['money'])}", "quick")
    say("Settlement: " + (", ".join(unlocked) if unlocked else "nothing built yet"), "quick")


def _postgame_menu(player):
    while True:
        choice = choose_menu(
            "Postgame",
            [
                MenuOption("1", "Build or Upgrade Home", "house", aliases=("house", "build", "upgrade")),
                MenuOption("2", "Family and Home", "family", aliases=("family", "home")),
                MenuOption("3", "Garden and Craft", "garden", aliases=("garden", "farm", "craft")),
                MenuOption("4", "Run Your Shop", "shop", aliases=("shop", "store")),
                MenuOption("5", "Rebuild the Realm", "town", aliases=("town", "help", "realm")),
                MenuOption("6", "Jobs Board", "quest", aliases=("quest", "job", "jobs")),
                MenuOption("7", "Hold a Festival", "festival", aliases=("festival", "party")),
                MenuOption("8", "Fish and Sail", "river", aliases=("fish", "river", "sail")),
                MenuOption("9", "Train an Apprentice", "apprentice", aliases=("train", "apprentice")),
                MenuOption("10", "Settlement Status", "status", aliases=("status", "settlement")),
                MenuOption("11", EXIT_LABEL, "exit", aliases=("exit", "quit", "q")),
            ],
            prompt="Postgame choice: ",
            subtitle="The realm is safe enough to live in now.",
        )
        if choice == "house":
            if not _postgame_has(player, "Postgame House"):
                if _postgame_spend(player, 25):
                    _postgame_add_once(player, "Postgame House")
                    say("\nYou buy land near the road and build a small house with a sturdy roof.", "scene")
                    say("You hang a lantern by the door and finally have a place to come back to.", "scene")
            elif not _postgame_has(player, "Second Floor"):
                if _postgame_spend(player, 60):
                    _postgame_add_once(player, "Second Floor")
                    say("\nYou add a second floor, a guest room, and a balcony facing the hills.", "scene")
            else:
                say("\nYou patch the roof, oil the hinges, and make the house a little nicer.", "scene")
        elif choice == "family":
            if not _postgame_has(player, "Postgame House"):
                say("\nYou should build a home first.", "scene")
            elif _postgame_add_once(player, "Family Hearth"):
                say("\nYou meet someone kind, and over time you start a family in the quiet part of the valley.", "scene")
                say("The house gets louder, warmer, and a lot more lived in.", "scene")
            else:
                say("\nYou spend the day at home cooking, telling stories, and fixing a mysteriously broken chair.", "scene")
        elif choice == "garden":
            _postgame_add_once(player, "Garden Patch")
            player["backpack"].append("Potion Herbs")
            say("\nYou tend the garden and harvest Potion Herbs.", "scene")
            say("The frog supervises the garden like it owns the property.", "scene")
        elif choice == "shop":
            if _postgame_add_once(player, "Hero Shop Ledger"):
                say("\nYou open a tiny shop and sell repair kits, jam, and honest advice.", "scene")
            earnings = random.randint(8, 22)
            player["money"] += earnings
            say(f"Travelers buy supplies and leave {money_text(earnings)} on the counter.", "scene")
        elif choice == "town":
            if _postgame_add_once(player, "Town Charter"):
                say("\nYou help repair roads, roofs, and the old bridge over the river.", "scene")
                say("The village starts looking like a place people can grow old in.", "scene")
            elif _postgame_add_once(player, "Hero Statue"):
                say("\nThe town builds a small statue of you. It looks almost, but not quite, like you.", "scene")
            else:
                say("\nYou spend the afternoon settling disputes, moving lumber, and signing very official papers.", "scene")
        elif choice == "quest":
            reward = random.randint(10, 30)
            player["money"] += reward
            outcome = random.choice([
                "A farmer hires you to find three missing sheep. You return with four, because one tagged along.",
                "The blacksmith asks for rare ore. You spend the afternoon in the hills and come back with a strange blue stone.",
                "A child asks for a hero story. You make one up, then realize it is almost true.",
                "A courier needs help crossing the old road. You escort them past three suspicious puddles.",
            ])
            say(f"\n{outcome}", "scene")
            say(f"You earn {money_text(reward)}.", "scene")
        elif choice == "festival":
            _postgame_add_once(player, "Festival Banner")
            say("\nYou help organize a town festival with lanterns, music, and too many pies.", "scene")
            say("By nightfall the whole valley feels warmer.", "scene")
        elif choice == "river":
            if _postgame_add_once(player, "Fishing Rod"):
                say("\nYou carve a fishing rod and learn that hero work did not teach patience.", "scene")
            elif _postgame_add_once(player, "River Boat"):
                say("\nYou build a small river boat and map the bends beyond town.", "scene")
            else:
                catch = random.choice(["Silver Minnow", "Boot With Teeth Marks", "Tiny Treasure Chest"])
                player["backpack"].append(catch)
                say(f"\nYou fish until sunset and catch a {catch}.", "scene")
        elif choice == "apprentice":
            if _postgame_add_once(player, "Apprentice Badge"):
                say("\nA young adventurer asks to train with you. You give them an Apprentice Badge.", "scene")
            else:
                say("\nYou teach your apprentice how to pack snacks, read maps, and run only when running helps.", "scene")
        elif choice == "adventure":
            find = random.choice(["Starlit Pebble", "Old Road Coin", "Map to Nowhere"])
            player["backpack"].append(find)
            say(f"\nYou take one more walk into the hills and return with a {find}.", "scene")
        elif choice == "status":
            _postgame_status(player)
        elif choice == "exit":
            _exit_game()


def _quick_menu(state):
    choice = choose_menu(
        "~ Menu",
        [
            MenuOption("1", "Player Stats", "stats", aliases=("stats", "status")),
            MenuOption("2", "Back", "back", aliases=("back", "return", "cancel")),
        ],
        prompt="~ menu choice: ",
        subtitle="Opened with ~.",
    )
    if choice == "stats":
        print_stats(state["player"])


def _run_story(state):
    set_autosave_hook(lambda: _autosave_state(state, sync_cloud=False))
    set_quick_menu_hook(lambda: _quick_menu(state))
    try:
        while True:
            scene_id = state["next_scene"]
            if scene_id == FINISHED_SCENE:
                _finish_game(state["player"])
                return

            _run_scene(scene_id, state["player"], state["shop_stock"])

            state["next_scene"] = _next_scene(scene_id)
            if state["next_scene"] == FINISHED_SCENE:
                _finish_game(state["player"])
                return

            autosaved, cloud_synced = _autosave_state(state, sync_cloud=True)
            if autosaved:
                message = "\nAutosaved."
                if cloud_synced:
                    message += " Cloud synced."
                say(message, "quick")
    finally:
        set_autosave_hook(None)
        set_quick_menu_hook(None)


def _restart_menu():
    return choose_menu(
        "Game Over",
        [
            MenuOption("1", "Restart", "restart", aliases=("restart", "r", "new game", "new")),
            MenuOption("2", "Main Menu", "main", aliases=("main", "menu", "m")),
            MenuOption("3", EXIT_LABEL, "exit", aliases=("exit", "quit", "q")),
        ],
        prompt="Game over choice: ",
    )


def run_game(load_path=None):
    """Create or load a player and play the text adventure."""
    show_startup_logo()

    if load_path is not None:
        try:
            state = _load_state_from_path(path_from_player_input(str(load_path)))
        except SaveError as exc:
            say(f"\nLoad failed: {exc}", "quick")
            return
        while True:
            try:
                _run_story(state)
                return
            except GameOver:
                choice = _restart_menu()
                if choice == "restart":
                    show_startup_logo()
                    state = _new_state()
                    continue
                if choice == "main":
                    show_startup_logo()
                    break
                if choice == "exit":
                    _exit_game()

    mode = "menu"
    while True:
        if mode == "restart":
            try:
                _run_story(_new_state())
                return
            except GameOver:
                choice = _restart_menu()
                if choice == "restart":
                    show_startup_logo()
                    mode = "restart"
                elif choice == "main":
                    show_startup_logo()
                    mode = "menu"
                elif choice == "exit":
                    _exit_game()
                continue

        try:
            state = _main_menu_state()
        except GameOver:
            choice = _restart_menu()
            if choice == "restart":
                show_startup_logo()
                mode = "restart"
            elif choice == "main":
                show_startup_logo()
                mode = "menu"
            elif choice == "exit":
                _exit_game()
            continue
        if state is None:
            continue
        try:
            _run_story(state)
            return
        except GameOver:
            choice = _restart_menu()
            if choice == "restart":
                show_startup_logo()
                mode = "restart"
            elif choice == "main":
                show_startup_logo()
                mode = "menu"
            elif choice == "exit":
                _exit_game()


def _main_menu_state():
    while True:
        choice = choose_menu(
            "Realmbound",
            [
                MenuOption("1", "New Game", "new", aliases=("new", "start")),
                MenuOption("2", "Load Game", "load", aliases=("load", "continue")),
                MenuOption("3", "Cloud Saves", "cloud", aliases=("cloud", "online", "sync")),
                MenuOption("4", EXIT_LABEL, "exit", aliases=("exit", "quit", "q")),
            ],
            prompt="Main menu choice: ",
        )

        if choice == "new":
            return _new_state()
        if choice == "load":
            state = _load_state_interactive()
            if state is not None:
                return state
        if choice == "cloud":
            state = _cloud_menu()
            if state is not None:
                return state
        if choice == "exit":
            _exit_game()


def intro_scene(player):
    """The player finds the frog that starts the adventure."""
    name = ask("\nWhat is your adventurer name? ")
    player["name"] = " ".join(name.split()) or "Adventurer"
    say("\nYou are out on a casual stroll when a magical chocolate frog hops around your feet.")

    choice = yes_no("\nDo you pick it up? (yes/no): ")
    if choice == "yes":
        say("\nYou pick up the frog and store it in your backpack.")
    else:
        say("\nYou start to walk away. RIBBIT.")
        say("The frog hops into your backpack anyway.", "beat")

    player["backpack"].append("Magical Chocolate Frog")


def wizard_scene(player):
    """Trade the frog for the wand, or keep it as a battle companion."""
    say("\nYou bump into an old man with a long white beard.")
    say('"Was that the croak of a chocolate frog?" he asks.', "beat")

    choice = yes_no("\nWhat do you say? (yes/no): ")
    if choice == "no":
        say("\nHis old hearing must be failing him. He wanders off.")
        activate_frog_partner(player)
        say("The frog gives you a tiny nod. It looks ready to fight for itself.", "beat")
        return

    say("\nHe smiles. \"I am Rumblerod The Great, the only remaining wizard in the North.\"")
    trade = yes_no("\nTrade the frog for his spare magic wand? (yes/no): ")
    if trade == "no":
        say("\nRumblerod shrugs and continues down the path.")
        activate_frog_partner(player)
        say("The frog hops onto your shoulder and learns Tongue Slap out of spite.", "beat")
        return

    player["backpack"].remove("Magical Chocolate Frog")
    player["backpack"].append("Magic Wand")
    add_spell(player, "Lockio Reducto")
    say("\nYou receive a Magic Wand.")
    say('Rumblerod says, "Lockio Reducto can unlock any door."', "beat")


def locked_door_scene(player):
    """First fork in the road and the locked door reward."""
    say("\nYou continue your journey and come to a fork in the path.")
    choice = choose_left_or_right("\nDo you go left or right? ")
    if choice == "right":
        say("\nYou notice a locked door on the left and decide not to miss it.")

    amount = random.randint(20, 30)
    if player.get("frogMode"):
        choice = yes_no("\nYou find a locked door. Send the frog through the keyhole? (yes/no): ")
    else:
        choice = yes_no("\nYou find a locked door. Use the wand and say the words? (yes/no): ")
    if choice == "no":
        say("\nA goblin sneaks up behind you and stabs you.", "beat")
        game_over(player)

    player["money"] += amount
    if player.get("frogMode"):
        say(
            f"\nThe frog squeezes under the door, unlocks it, and looks smug. You find {money_text(amount)}.",
            "beat",
        )
    else:
        say(f"\nYou say Lockio Reducto. The door opens and you find {money_text(amount)}.", "beat")


def first_goblin_scene(player):
    """The first goblin is a simple physical fight before spell combat begins."""
    say("\nYou turn to exit, but a goblin blocks your path.")
    if fight_or_run() == "run":
        say("\nThe goblin is faster than you.", "beat")
        game_over(player)

    attack = choose_menu(
        "Quick Fight",
        [
            MenuOption("1", "Uppercut", "uppercut", aliases=("uppercut", "punch")),
            MenuOption("2", "Kick", "kick", aliases=("kick",)),
            MenuOption("3", "Dirt Throw", "dirt", aliases=("dirt", "throw dirt")),
        ],
        prompt="Move: ",
    )

    if attack == "dirt":
        say("\nThe dirt blinds the goblin long enough for you to knock it out.")
    else:
        say(f"\nYour {attack} knocks out the goblin.")
    if player.get("frogMode"):
        add_frog_attack(player, "Bubble Burp")
        say("It drops a page from a frog-training book.", "beat")
        say("The frog eats half the page and learns Bubble Burp.")
    else:
        add_spell(player, "Fireball")
        say("It drops a page from a spell book.", "beat")
        say("You learned Fireball.")
    _extra_fight(
        player,
        "gate rat",
        "The noise wakes a gate rat with opinions about trespassing.",
        "The gate rat follows your shoelaces and wins.",
    )


def village_scene(player, shop_stock):
    """Save the village, receive a potion, and visit Gnome Depot."""
    say("\nYou see a village nearby.")
    say("A troll is attacking the villagers.", "beat")
    if fight_or_run() == "run":
        say("\nThe troll catches you before you can escape.", "beat")
        game_over(player)
    spell_fight("troll", player)
    _extra_fight(
        player,
        "smoke imp",
        "A smoke imp crawls out of the village chimney and starts throwing sparks.",
        "You run through the smoke and smack directly into a fence.",
    )

    say('\nA villager says, "Thank you for saving our village."')
    say('"Take this Big Health Potion. It will restore your health."', "beat")
    player["backpack"].append("Big Health Potion")
    say("\nThe villagers reopen the Church of the Little Lantern and invite you inside.")
    _visit_church(player, "the Church of the Little Lantern")
    offer_potions(player)

    hidden = ask("\nBefore you leave, the cobblestones seem to whisper. Type what you heard or press Enter: ")
    if hidden.strip().lower() == "listen":
        say("\nA loose brick slides aside and reveals a narrow ladder.", "beat")
        clocktower_scene(player, shop_stock)
    elif hidden.strip().lower() == "well":
        well_scene(player)

    enter_store = yes_no("\nYou see Gnome Depot, Harold Sellsalot's shop. Go inside? (yes/no): ")
    if enter_store == "no":
        say("\nA skeleton archer outside the village shoots you.", "beat")
        game_over(player)

    say("\nHarold welcomes you into Gnome Depot.")
    run_shop(player, shop_stock)

    say("\nYou leave the store and encounter a skeleton.")
    if fight_or_run() == "run":
        say("\nThe skeleton catches you near the village gate.", "beat")
        game_over(player)
    spell_fight("skeleton", player)
    offer_potions(player)
    _extra_fight(
        player,
        "curse candle",
        "The village shrine candle grows teeth and blocks the road.",
        "The candle waddles after you. Slowly. Somehow still fast enough.",
    )


def forest_scene(player, shop_stock):
    """Forest fights and Miss Costalot's traveling shop."""
    say("\nYou follow a forest trail.")
    say("A werewolf howls at you from the trees.", "beat")
    if fight_or_run() == "run":
        say("\nThe werewolf catches you in the brush.", "beat")
        game_over(player)
    spell_fight("werewolf", player)
    offer_potions(player)
    _extra_fight(
        player,
        "bramble wolf",
        "The bushes shake, then become a second wolf made mostly of thorns.",
        "You sprint into the brambles and immediately regret the shortcut.",
    )

    say("\nFarther down the trail, a goblin jumps into the path.")
    if fight_or_run() == "run":
        say("\nThe goblin is faster than you.", "beat")
        game_over(player)
    spell_fight("goblin", player)
    offer_potions(player)
    _extra_fight(
        player,
        "treasure mimic",
        "A treasure chest sits in the road. It smiles before you can.",
        "The chest runs faster than a chest should legally run.",
    )

    say("\nAt the forest edge, Miss Costalot waves you over to her traveling cart.")
    run_shop(player, shop_stock, advanced=True)
    if ask("\nA mossy sign points off the road. Type 'detour' to ignore it, or press Enter: ").strip().lower() == "detour":
        say("\nYou push through nettles and find a forgotten well.", "beat")
        well_scene(player)


def twin_doors_scene(player):
    """Handle the left/right door branch and converge back to the main path."""
    say("\nYou find two locked doors at the end of the road.")
    if player.get("frogMode"):
        door = choose_left_or_right("\nDo you send the frog to the left or the right door? ")
        say("\nThe frog shoulder-checks the lock until the door gives up.", "beat")
    else:
        door = choose_left_or_right("\nDo you use the wand on the left or the right door? ")
        say("\nYou say Lockio Reducto and the door opens.", "beat")

    if door == "left":
        say("\nThe left door leads to a dead end guarded by an ogre.")
        if fight_or_run() == "fight":
            spell_fight("ogre", player)
            offer_potions(player)
            say("\nAfter defeating the ogre, you realize this path leads nowhere.")
        else:
            say("\nYou escape back to the corridor.")
        say("The right door is now your only option.", "beat")

    say("\nYou go through the right door and find a chest.")
    say("Before you can open it, an ogre attacks.", "beat")
    if fight_or_run() == "run":
        say("\nYou slide between the ogre's legs and escape.")
        return

    spell_fight("ogre", player)
    amount = random.randint(15, 25)
    player["money"] += amount
    say(f"\nYou find {money_text(amount)} in the chest.", "beat")
    offer_potions(player)


def witch_scene(player):
    """Fight the witch guarding the way to the mountains."""
    say("\nYou continue down the corridor.")
    if fight_or_run("\nYou see a witch. Do you fight or run? ") == "run":
        say("\nYou run into the ogre's dad, who is very angry with you.", "beat")
        game_over(player)

    spell_fight("witch", player)
    offer_potions(player)
    _extra_fight(
        player,
        "curse candle",
        "The witch's last candle hops down from a shelf and tries to finish the curse.",
        "The candle stamps out your escape plan with tiny wax feet.",
    )


def mountain_pass_scene(player):
    """Climb toward the final valley and meet colder trouble."""
    say("\nPast the witch's corridor, the road climbs into a mountain pass.")
    say("A sign reads: FINAL CASTLE THIS WAY. Under it, someone wrote: probably.", "beat")
    if fight_or_run("\nAn ice goblin rolls down the hill at you. Do you fight or run? ") == "run":
        say("\nYou try to run downhill, which works until the hill runs out.", "beat")
        game_over(player)

    spell_fight("ice goblin", player)
    _extra_fight(
        player,
        "snow bat",
        "A snow bat drops from the pass marker and shakes frost from its wings.",
        "You run downhill; the snow bat takes the express route.",
    )
    reward = random.randint(35, 50)
    player["money"] += reward
    player["backpack"].append("Moon Cheese")
    say(f"\nThe ice goblin's lunchbox pops open. You find {money_text(reward)} and some Moon Cheese.")
    offer_potions(player)


def moonlit_market_scene(player, shop_stock):
    """A late-game market with weapons and stranger magic."""
    say("\nAt the top of the pass, paper lanterns glow over the Moonlit Market.")
    say('A merchant named Madam Probably says, "Everything here is almost safe."', "beat")
    say("Beyond the stalls, the Chapel of the Second Moon keeps its silver doors open all night.")
    _visit_church(player, "the Chapel of the Second Moon")
    run_shop(player, shop_stock, advanced=True)

    say("\nBehind the last stall, a shadow knight blocks the castle road.")
    if fight_or_run() == "run":
        say("\nThe knight sighs, walks faster than you, and bonks you with the flat of a gloomy sword.", "beat")
        game_over(player)
    spell_fight("shadow knight", player)
    _extra_fight(
        player,
        "receipt wraith",
        "The knight's dropped receipt unfolds into a very angry wraith.",
        "The receipt wraith charges a late fee on your escape.",
    )
    player["money"] += 30
    say(f"\nThe shadow knight drops {money_text(30)} and a note that says: please stop Lord Dreadbiscuit.")
    offer_potions(player)
    secret = ask("\nA vendor drops a receipt. Type the first word printed in tiny ink, or press Enter: ")
    if secret.strip().lower() == "clock":
        say("\nThe receipt opens a seam in the market wall.", "beat")
        clocktower_scene(player, shop_stock)


def vampire_castle_scene(player):
    """Sneak through the vampire castle and steal the final key."""
    say("\nYou reach a castle shaped like a fancy tooth.")
    say("Inside, a vampire is practicing scary faces in a mirror that refuses to help.", "beat")
    if fight_or_run("\nThe vampire notices you. Do you fight or run? ") == "run":
        say("\nYou run into a closet full of capes. The capes win.", "beat")
        game_over(player)

    spell_fight("vampire", player)
    _extra_fight(
        player,
        "basement bat",
        "The castle basement answers the noise with an even smaller, meaner bat.",
        "You trip over a cape rack. The bat accepts the assist.",
    )
    player["backpack"].append("Silver Key of Mild Concern")
    player["money"] += 40
    say(f"\nThe vampire turns into a bat and drops the Silver Key of Mild Concern plus {money_text(40)}.")
    say("The key is real, but the real castle keeps moving farther away.", "beat")
    offer_potions(player)


def false_throne_scene(player, shop_stock):
    """A long detour that looks like the end and is not the end."""
    say("\nThe Silver Key opens a hall with a throne made of polished cookies.")
    say("A herald in a paper crown announces that the final castle is 'just ahead' again.", "beat")
    if fight_or_run("\nA mirrored knight steps out of the throne room. Fight or run? ") == "run":
        say("\nYou run, but the hallway keeps becoming longer behind you.", "beat")
        game_over(player)

    spell_fight("shadow knight", player)
    _extra_fight(
        player,
        "sugar golem",
        "The cookie throne melts into a sugar golem with fists like bakery bricks.",
        "The hallway becomes syrup under your boots.",
    )
    reward = random.randint(20, 35)
    player["money"] += reward
    say(f"\nBehind the false throne, you find {money_text(reward)} and a stairway that goes down.")
    offer_potions(player)
    run_shop(player, shop_stock, advanced=True)


def underkeep_scene(player):
    """The road down under the castle before the real last gate."""
    say("\nThe stairway leads under the castle into a damp underkeep.")
    say("A sleepy archivist says the princess is not here, then stamps your map with 'TRY AGAIN'.", "beat")
    if fight_or_run("\nA chained ogre blocks the only tunnel. Fight or run? ") == "run":
        say("\nYou run into a wall of old bricks and lose the argument.", "beat")
        game_over(player)

    spell_fight("ogre", player)
    _extra_fight(
        player,
        "rust rat",
        "A rust rat drops from the pipes and starts chewing the map.",
        "You run into a pipe maze and the rust rat knows every pipe.",
    )
    player["backpack"].append("Ancient Map Fragment")
    player["money"] += 25
    say("\nThe ogre drops an Ancient Map Fragment and a small pouch of Whoop Nickels.")
    say("The fragment points deeper underground, because of course it does.", "beat")
    offer_potions(player)
    if ask("\nThe tunnel breathes once. Type 'deeper' to keep going, or press Enter: ").strip().lower() == "deeper":
        say("\nYou slip into a maintenance passage that should not exist.", "beat")
        well_scene(player)


def clocktower_scene(player, shop_stock):
    """A hidden side path with a slow clockwork quest."""
    say("\nA narrow stair climbs into a clocktower nobody mentioned.")
    say("Each floor is quieter than the last, as if the tower is trying not to be found.", "beat")
    if fight_or_run("\nA brass sentinel blocks the gears. Fight or run? ") == "run":
        say("\nYou run, but the tower ticks its way into your path again.", "beat")
        game_over(player)

    spell_fight("shadow knight", player)
    _extra_fight(
        player,
        "rust rat",
        "A gear hatch opens and another rust rat skitters across the clock face.",
        "The tower ticks your escape route closed.",
    )
    player["money"] += 20
    player["backpack"].append("Clockwork Cog")
    say("\nThe sentinel drops a Clockwork Cog and the tower keeps turning anyway.")
    offer_potions(player)
    run_shop(player, shop_stock, advanced=True)


def well_scene(player):
    """A tiny hidden quest that looks like nothing."""
    say("\nYou find an old well behind a fence that should not be easy to notice.")
    say("Something from below taps back twice, waits, then once more.", "beat")
    choice = yes_no("\nLean over and listen again? (yes/no): ")
    if choice == "no":
        say("\nThe well stays quiet, which is somehow worse.", "beat")
        return
    player["backpack"].append("Well Water")
    player["money"] += 7
    say(f"\nA bucket rises with {money_text(7)} and a bottle of cold well water.")


def hundred_day_road_scene(player, shop_stock):
    """A long required expedition through the realm's sealed outer roads."""
    chapter_names = (
        "Ash Month",
        "Lantern Month",
        "Mirror Month",
        "Storm Month",
        "Crownless Month",
    )
    road_churches = (
        "the Church of First Footfall",
        "Emberglass Chapel",
        "the Church of Honest Mirrors",
        "Stormbell Abbey",
        "the Church of the Empty Crown",
    )

    road_progress = max(0, min(player.get("roadProgress", 0), len(LONG_ROAD_ENEMIES)))
    if road_progress >= len(LONG_ROAD_ENEMIES):
        say("\nRoad checkpoint loaded: all 50 battles complete.", "scene")
    elif road_progress:
        say(f"\nRoad checkpoint loaded: {road_progress}/50 battles complete.", "scene")
        say(f"The road unfolds again at milepost {road_progress + 1}.", "beat")
    else:
        say("\nThe Ancient Map Fragment unfolds into a road that is much longer than the paper should allow.")
        say("Mileposts rise out of the dirt one after another, each carved with a different warning.", "beat")
        say("Rumblerod squints at the first marker and says, 'This is the Hundred-Day Road. Bring snacks.'", "beat")
        say("The Dragon Gate waits at the far end, but the road refuses to be skipped.")
        _visit_church(player, road_churches[0], automatic=True)
        run_shop(player, shop_stock, advanced=True, legendary=True)

    for index, enemy in enumerate(LONG_ROAD_ENEMIES[road_progress:], start=road_progress + 1):
        if (index - 1) % 10 == 0:
            chapter = chapter_names[(index - 1) // 10]
            say(f"\n=== {chapter} ===", "scene")
            say(
                f"The milepost reads {index}/50. The road insists another month has begun.",
                "beat",
            )
            if index > 1:
                _visit_church(
                    player,
                    road_churches[(index - 1) // 10],
                    automatic=True,
                )
                run_shop(player, shop_stock, advanced=True, legendary=True)

        enemy_title = enemy.title()
        if fight_or_run(f"\nEnemy {index}/50: A {enemy_title} blocks the road. Fight or run? ") == "run":
            say("\nYou turn back. The road folds behind you like a map in a bad mood.", "beat")
            game_over(player)

        spell_fight(enemy, player)
        player["roadProgress"] = index
        if index % 5 == 0:
            say(f"\nRoad checkpoint saved: {index}/50 battles complete.", "quick")
        else:
            say(f"\nRoad progress saved: {index}/50.", "quick")

        if index % 5 == 0:
            health_gain = min(30, player["healthMax"] - player["health"])
            mana_gain = min(20, player["manaMax"] - player["mana"])
            player["health"] += health_gain
            player["mana"] += mana_gain
            say(
                "\nA roadside shrine gives you just enough rest to keep going. "
                f"Health +{health_gain}, mana +{mana_gain}.",
                "beat",
            )
            offer_potions(player)

    if "Hundred-Day Road Seal" not in player["backpack"]:
        player["backpack"].append("Hundred-Day Road Seal")
        player["money"] += 150
        say("\nThe fiftieth milepost cracks open and reveals the Hundred-Day Road Seal.")
        say(f"You also pry {money_text(150)} from a stone donation box labeled 'hero maintenance'.", "beat")
    else:
        say("\nYour Hundred-Day Road Seal still glows. This road has already been conquered.")
    say("Behind you, the road is full of footprints. Ahead, the Dragon Gate finally stops pretending to be close.")
    run_shop(player, shop_stock, advanced=True, legendary=True)


def dragon_gate_scene(player, shop_stock):
    """Prepare at the dragon forge and open the last gate."""
    say("\nThe Silver Key fits a gate made of old dragon scales.")
    say("Beside the gate stands the Church of the Last Door, built for heroes who made it this far.")
    _visit_church(player, "the Church of the Last Door", automatic=True)
    say("Next to it, two blacksmiths argue over whether anvils count as musical instruments.")
    say('They call their shop The Dragon Forge and offer one last chance to gear up.', "beat")
    run_shop(player, shop_stock, advanced=True, legendary=True)

    _extra_fight(
        player,
        "glass cobra",
        "A glass cobra uncoils from the gate hinges and reflects your worst angle.",
        "The cobra turns the gate into a mirror maze.",
    )
    say("\nWhen you unlock the gate, a crystal dragon wakes up and sneezes rainbows everywhere.")
    if fight_or_run("\nDo you fight the crystal dragon or run? ") == "run":
        say("\nYou run. The dragon thinks this is fetch.", "beat")
        game_over(player)

    spell_fight("crystal dragon", player)
    _extra_fight(
        player,
        "crown wraith",
        "The dragon's roar shakes a crown-shaped wraith out of the ceiling.",
        "The wraith declares your retreat illegal.",
    )
    player["backpack"].append("Dragon Scale Chip")
    player["money"] += 60
    say(f"\nThe dragon bows, gives you a Dragon Scale Chip, and pushes {money_text(60)} into your hands.")
    say("You are sure this must be the last thing. It is not the last thing.", "beat")
    offer_potions(player)


def final_battle_scene(player):
    """Face the dragon that has been holding the realm together by force."""
    say("\nBeyond the gate stands Lord Dreadbiscuit, wearing a crown far too small for his ego.")
    say('"At last," he says, "someone has come to challenge my mildly inconvenient darkness."', "beat")
    say("Then the crown cracks like thunder and the whole castle tilts toward the sky.", "beat")
    say("A dragon larger than the tower unfolds from the storm clouds, each scale glowing like a sealed doorway.")
    say('Lord Dreadbiscuit points up and whispers, "Technically, I was only renting the throne."', "beat")

    if "Dragon Scale Chip" in player["backpack"]:
        player["health"] = min(player["healthMax"], player["health"] + 40)
        player["mana"] = min(player["manaMax"], player["mana"] + 35)
        say(
            "\nThe Dragon Scale Chip burns white-hot and shields you in old realmfire. "
            f"Health: {player['health']}/{player['healthMax']} Mana: {player['mana']}/{player['manaMax']}.",
            "beat",
        )

    say("\nThe Realmbound Dragon lands on the ruined throne and blocks out every star.")
    if fight_or_run("\nDo you fight the Realmbound Dragon or run? ") == "run":
        say("\nYou run. The dragon inhales once, and the road behind you becomes a memory.", "beat")
        game_over(player)

    spell_fight("realmbound dragon", player)
    say("\nThe Realmbound Dragon crashes across the throne mountain and folds its wings around the broken castle.")
    say("Its final roar turns into sunrise. Every locked road in the realm opens at once.", "beat")
    say("Lord Dreadbiscuit crawls from under a biscuit-shaped shield and immediately retires from evil.")
    say("Rumblerod appears from behind a curtain and insists he was helping invisibly the whole time.", "beat")