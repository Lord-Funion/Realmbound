# Realmbound ESP32 TFT Port

This is a small-screen Arduino/PlatformIO port of Realmbound for an ESP32 and
a 1.8 inch SPI TFT. It defaults to an ST7735-style display and can be switched
to the Adafruit ST7789 driver in `include/RealmboundConfig.h`.

The desktop game is too text-heavy for a 160x128 screen, so this port uses a
compact menu-driven version with the same core ideas: Whoop Nickels, shops,
frog/wand route choice, the Hundred-Day Road with exactly 50 enemy types, and
the Realmbound Dragon finale.

## Controls

Use four active-low buttons. Wire one side of each button to the GPIO and the
other side to GND. The firmware enables the ESP32 internal pullups.

| Action | Default GPIO |
| --- | --- |
| Up | `32` |
| Down | `33` |
| Select | `25` |
| Back / Pause | `26` |

Serial fallback also works at `115200` baud:

- `w` = up
- `s` = down
- `e` or Enter = select
- `b` = back/pause

## Default TFT Wiring

| TFT Pin | ESP32 GPIO |
| --- | --- |
| `SCK` / `SCL` | `18` |
| `SDA` / `MOSI` | `23` |
| `CS` | `5` |
| `DC` / `A0` | `16` |
| `RST` | `17` |
| `BL` / `LED` | `4` |
| `VCC` | `3.3V` |
| `GND` | `GND` |

Some displays label the SPI pins differently. If the screen stays white or the
colors are wrong, try changing `REALMBOUND_TFT_TAB` between `INITR_BLACKTAB`,
`INITR_GREENTAB`, and `INITR_REDTAB`.

For ST7789 displays, set:

```cpp
#define REALMBOUND_DISPLAY_DRIVER REALMBOUND_DISPLAY_ST7789
```

Then set `REALMBOUND_TFT_WIDTH`, `REALMBOUND_TFT_HEIGHT`, and rotation to match
the panel.

## Build And Upload

Install PlatformIO, then run:

```sh
cd esp32
pio run
pio run -t upload
pio device monitor
```

If you use the Arduino IDE instead, copy `src/main.cpp` into a sketch, copy
`include/RealmboundConfig.h` next to it, install the Adafruit GFX and Adafruit
ST7735/ST7789 libraries, and select an ESP32 board.

## Saves

The ESP32 port stores progress in ESP32 NVS flash using Arduino `Preferences`.
It automatically saves after each completed Hundred-Day Road battle, so
`Continue` resumes at the next road enemy. Use `Save Game` from the pause menu
to write progress at other times.
