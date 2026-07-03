"""Startup logo rendering for the terminal game."""

import os

from .terminal_colors import Fore, Style


def _print_text_logo():
    print(
        Fore.LIGHTYELLOW_EX
        + r"""
 ____            _           _                           _
|  _ \ ___  __ _| |_ __ ___ | |__   ___  _   _ _ __   __| |
| |_) / _ \/ _` | | '_ ` _ \| '_ \ / _ \| | | | '_ \ / _` |
|  _ <  __/ (_| | | | | | | | |_) | (_) | |_| | | | | (_| |
|_| \_\___|\__,_|_|_| |_| |_|_.__/ \___/ \__,_|_| |_|\__,_|
"""
        + Style.RESET_ALL
    )


def show_startup_logo():
    """Show the Realmbound logo before the main menu or loaded save starts."""
    if os.getenv("TEXT_ADVENTURE_HIDE_LOGO"):
        return

    _print_text_logo()
