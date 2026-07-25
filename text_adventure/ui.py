"""Reusable terminal UI helpers for menus and short choices."""

from dataclasses import dataclass, field
import os
import re
import shutil
import sys

from .pacing import ask as typed_ask
from .pacing import maybe_open_quick_menu
from .pacing import say
from .terminal_colors import Fore, Style


MOUSE_ENABLE = "\x1b[?1000h\x1b[?1006h"
MOUSE_DISABLE = "\x1b[?1000l\x1b[?1006l"
CURSOR_POSITION = "\x1b[6n"
MOUSE_EVENT_RE = re.compile(r"\x1b\[<(\d+);(\d+);(\d+)([Mm])")
ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")
_MOUSE_CAPABLE = None


@dataclass(frozen=True)
class MenuOption:
    """One selectable row in a terminal menu."""

    key: str
    label: str
    value: str
    detail: str = ""
    aliases: tuple[str, ...] = field(default_factory=tuple)
    enabled: bool = True
    status: str = ""


def normalize_choice(value):
    """Normalize player text so menu input feels forgiving."""
    return " ".join(value.strip().lower().split())


def divider(title):
    """Print a compact section title."""
    print(f"\n{Fore.LIGHTYELLOW_EX}{Style.BRIGHT}=== {title} ==={Style.RESET_ALL}")


def stat_meter(current, maximum, width=16):
    """Return a small ASCII meter for health and mana displays."""
    if maximum <= 0:
        return "[" + "-" * width + "]"
    filled = round(width * max(0, min(current, maximum)) / maximum)
    return "[" + "#" * filled + "-" * (width - filled) + "]"


def _option_inputs(option):
    inputs = {option.key, option.label, *option.aliases}
    return {normalize_choice(value) for value in inputs if value}


def _mouse_enabled():
    if _MOUSE_CAPABLE is False:
        return False
    if os.getenv("TEXT_ADVENTURE_MOUSE", "").strip().lower() in {"0", "false", "no", "off"}:
        return False
    return sys.stdin.isatty() and sys.stdout.isatty()


def _remember_mouse_capability(position):
    global _MOUSE_CAPABLE

    _MOUSE_CAPABLE = position is not None
    return position


def _parse_mouse_event(sequence):
    match = MOUSE_EVENT_RE.fullmatch(sequence)
    if not match:
        return None

    button, x_position, y_position, event_type = match.groups()
    if event_type != "M" or int(button) & 3 != 0:
        return None
    return int(x_position), int(y_position)


def _clicked_target(targets, x_position, y_position):
    for target in targets:
        row, start_col, end_col, value, label = target
        if row == y_position and start_col <= x_position <= end_col:
            return value, label
    return None


def _line_target(row, line, value):
    columns = shutil.get_terminal_size((80, 24)).columns
    visible_line = ANSI_RE.sub("", line)
    return (row, 1, max(1, min(columns, len(visible_line))), value, value)


def _display_rows(line):
    columns = shutil.get_terminal_size((80, 24)).columns
    visible_length = max(1, len(ANSI_RE.sub("", line)))
    return ((visible_length - 1) // max(1, columns)) + 1


def _posix_cursor_position():
    try:
        import select
        import termios
        import tty
    except ImportError:
        return None

    stdin_fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(stdin_fd)
    try:
        tty.setraw(stdin_fd)
        sys.stdout.write(CURSOR_POSITION)
        sys.stdout.flush()

        response = ""
        while True:
            readable, _, _ = select.select([stdin_fd], [], [], 0.15)
            if not readable:
                return None
            chunk = os.read(stdin_fd, 1).decode(errors="ignore")
            response += chunk
            if chunk == "R":
                break
    finally:
        termios.tcsetattr(stdin_fd, termios.TCSADRAIN, old_settings)

    match = re.search(r"\x1b\[(\d+);(\d+)R", response)
    if not match:
        return None
    return int(match.group(1)), int(match.group(2))


def _windows_cursor_position():
    if os.name != "nt":
        return None

    try:
        import ctypes
        from ctypes import wintypes
    except ImportError:
        return None

    class COORD(ctypes.Structure):
        _fields_ = [("X", wintypes.SHORT), ("Y", wintypes.SHORT)]

    class SMALL_RECT(ctypes.Structure):
        _fields_ = [
            ("Left", wintypes.SHORT),
            ("Top", wintypes.SHORT),
            ("Right", wintypes.SHORT),
            ("Bottom", wintypes.SHORT),
        ]

    class CONSOLE_SCREEN_BUFFER_INFO(ctypes.Structure):
        _fields_ = [
            ("dwSize", COORD),
            ("dwCursorPosition", COORD),
            ("wAttributes", wintypes.WORD),
            ("srWindow", SMALL_RECT),
            ("dwMaximumWindowSize", COORD),
        ]

    kernel32 = ctypes.windll.kernel32
    handle = kernel32.GetStdHandle(-11)
    info = CONSOLE_SCREEN_BUFFER_INFO()
    if not kernel32.GetConsoleScreenBufferInfo(handle, ctypes.byref(info)):
        return None
    row = info.dwCursorPosition.Y - info.srWindow.Top + 1
    col = info.dwCursorPosition.X - info.srWindow.Left + 1
    return row, col


def _cursor_position():
    if not _mouse_enabled():
        return None
    if os.name == "nt":
        return _remember_mouse_capability(_windows_cursor_position())
    return _remember_mouse_capability(_posix_cursor_position())


def _enable_windows_virtual_terminal():
    if os.name != "nt":
        return None

    try:
        import ctypes
    except ImportError:
        return None

    kernel32 = ctypes.windll.kernel32
    handles = [kernel32.GetStdHandle(-10), kernel32.GetStdHandle(-11)]
    original_modes = []
    for handle in handles:
        mode = ctypes.c_uint()
        if not kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            continue
        original_modes.append((handle, mode.value))
        if handle == handles[0]:
            kernel32.SetConsoleMode(handle, mode.value | 0x0200)
        else:
            kernel32.SetConsoleMode(handle, mode.value | 0x0004)
    return original_modes


def _restore_windows_console_modes(original_modes):
    if not original_modes:
        return

    import ctypes

    kernel32 = ctypes.windll.kernel32
    for handle, mode in original_modes:
        kernel32.SetConsoleMode(handle, mode)


def _read_posix_clickable(prompt, targets, inline_choices):
    import select
    import termios
    import tty

    stdin_fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(stdin_fd)
    buffer = ""

    try:
        tty.setraw(stdin_fd)
        sys.stdout.write(MOUSE_ENABLE)
        sys.stdout.write(prompt)
        sys.stdout.flush()

        targets = list(targets)
        if inline_choices:
            position = _posix_cursor_position()
            if position is not None:
                row, col = position
            else:
                row, col = None, None

            for label, value in inline_choices:
                text = f" [{label}]"
                if row is not None:
                    start_col = col + 2
                    end_col = start_col + len(label) - 1
                    targets.append((row, start_col, end_col, value, value))
                    col += len(text)
                sys.stdout.write(text)
            sys.stdout.write(" ")
            sys.stdout.flush()

        while True:
            readable, _, _ = select.select([stdin_fd], [], [], None)
            if not readable:
                continue

            char = os.read(stdin_fd, 1).decode(errors="ignore")
            if char in {"\r", "\n"}:
                sys.stdout.write("\n")
                return buffer
            if char in {"\x7f", "\b"}:
                if buffer:
                    buffer = buffer[:-1]
                    sys.stdout.write("\b \b")
                    sys.stdout.flush()
                continue
            if char == "\x1b":
                sequence = char
                while True:
                    readable, _, _ = select.select([stdin_fd], [], [], 0.01)
                    if not readable:
                        break
                    next_char = os.read(stdin_fd, 1).decode(errors="ignore")
                    sequence += next_char
                    if next_char in {"M", "m"} or len(sequence) > 40:
                        break
                event = _parse_mouse_event(sequence)
                if event is None:
                    continue
                clicked = _clicked_target(targets, *event)
                if clicked is None:
                    continue
                value, label = clicked
                sys.stdout.write(f"{label}\n")
                return value
            if char.isprintable():
                buffer += char
                sys.stdout.write(char)
                sys.stdout.flush()
    finally:
        sys.stdout.write(MOUSE_DISABLE)
        sys.stdout.flush()
        termios.tcsetattr(stdin_fd, termios.TCSADRAIN, old_settings)


def _read_windows_clickable(prompt, targets, inline_choices):
    import msvcrt

    original_modes = _enable_windows_virtual_terminal()
    buffer = ""

    try:
        sys.stdout.write(MOUSE_ENABLE)
        sys.stdout.write(prompt)
        sys.stdout.flush()

        targets = list(targets)
        if inline_choices:
            position = _windows_cursor_position()
            if position is not None:
                row, col = position
            else:
                row, col = None, None

            for label, value in inline_choices:
                text = f" [{label}]"
                if row is not None:
                    start_col = col + 2
                    end_col = start_col + len(label) - 1
                    targets.append((row, start_col, end_col, value, value))
                    col += len(text)
                sys.stdout.write(text)
            sys.stdout.write(" ")
            sys.stdout.flush()

        while True:
            char = msvcrt.getwch()
            if char in {"\r", "\n"}:
                sys.stdout.write("\n")
                return buffer
            if char == "\b":
                if buffer:
                    buffer = buffer[:-1]
                    sys.stdout.write("\b \b")
                    sys.stdout.flush()
                continue
            if char == "\x1b":
                sequence = char
                for _ in range(40):
                    if not msvcrt.kbhit():
                        break
                    next_char = msvcrt.getwch()
                    sequence += next_char
                    if next_char in {"M", "m"}:
                        break
                event = _parse_mouse_event(sequence)
                if event is None:
                    continue
                clicked = _clicked_target(targets, *event)
                if clicked is None:
                    continue
                value, label = clicked
                sys.stdout.write(f"{label}\n")
                return value
            if char.isprintable():
                buffer += char
                sys.stdout.write(char)
                sys.stdout.flush()
    finally:
        sys.stdout.write(MOUSE_DISABLE)
        sys.stdout.flush()
        _restore_windows_console_modes(original_modes)


def _read_clickable(prompt, targets=None, inline_choices=None):
    """Read typed input or a terminal mouse click when the terminal supports it."""
    targets = targets or []
    inline_choices = inline_choices or []
    if not _mouse_enabled():
        return typed_ask(prompt)

    try:
        if os.name == "nt":
            return _read_windows_clickable(prompt, targets, inline_choices)
        return _read_posix_clickable(prompt, targets, inline_choices)
    except Exception:
        return typed_ask(prompt)


def _colored_option_line(option):
    if not option.enabled:
        line = f"{option.key}. {option.label}"
        if option.detail:
            line += f" - {option.detail}"
        if option.status:
            line += f" ({option.status})"
        return f"{Style.DIM}{line}{Style.RESET_ALL}"

    line = (
        f"{Fore.LIGHTCYAN_EX}{option.key}{Style.RESET_ALL}. "
        f"{Style.BRIGHT}{Fore.LIGHTGREEN_EX}{option.label}{Style.RESET_ALL}"
    )
    if option.detail:
        detail = option.detail
        if "\033[" not in detail:
            detail = f"{Fore.LIGHTWHITE_EX}{detail}{Style.RESET_ALL}"
        line += f" - {detail}"
    if option.status:
        line += f" ({Fore.LIGHTYELLOW_EX}{option.status}{Style.RESET_ALL})"
    return line


def choose_menu(title, options, prompt="Choose: ", subtitle=None, invalid=None):
    """Render a menu until the player chooses an enabled option."""
    invalid = invalid or "\nPlease choose one of the listed options."

    while True:
        start_position = _cursor_position()
        start_row = start_position[0] if start_position else None
        option_targets = []

        divider(title)
        current_row = start_row + 2 if start_row is not None else None
        if subtitle:
            print(subtitle)
            if current_row is not None:
                current_row += 1

        for option in options:
            line = f"{option.key}. {option.label}"
            if option.detail:
                line += f" - {option.detail}"
            if option.status:
                line += f" ({option.status})"
            if current_row is not None:
                option_targets.append(_line_target(current_row, line, option.key))
                rows_used = _display_rows(line)
            print(_colored_option_line(option))
            if current_row is not None:
                current_row += rows_used

        raw_choice = _read_clickable(prompt, option_targets)
        if maybe_open_quick_menu(raw_choice):
            continue
        choice = normalize_choice(raw_choice)
        for option in options:
            if choice in _option_inputs(option):
                if option.enabled:
                    return option.value
                say(f"\n{option.label} is not available right now.", "quick")
                break
        else:
            say(invalid, "quick")


def ask_choice(prompt, choices, invalid):
    """Ask a short text choice and accept aliases for natural input."""
    normalized_choices = {
        value: {normalize_choice(alias) for alias in aliases}
        for value, aliases in choices.items()
    }
    click_choices = [(value, value) for value in choices]

    while True:
        raw_choice = _read_clickable(prompt, inline_choices=click_choices)
        if maybe_open_quick_menu(raw_choice):
            continue
        choice = normalize_choice(raw_choice)
        for value, aliases in normalized_choices.items():
            if choice in aliases:
                return value
        say(invalid, "quick")


def money_text(amount):
    """Format money consistently across menus."""
    label = "Whoop Nickel" if amount == 1 else "Whoop Nickels"
    return f"{Fore.LIGHTYELLOW_EX}{amount} {label}{Style.RESET_ALL}"
