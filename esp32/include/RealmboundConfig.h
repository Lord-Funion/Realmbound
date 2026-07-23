#pragma once

// Default wiring uses the ESP32 VSPI pins for the TFT.
// Change these values to match your board before uploading.
#define REALMBOUND_TFT_CS 5
#define REALMBOUND_TFT_DC 16
#define REALMBOUND_TFT_RST 17
#define REALMBOUND_TFT_BL 4
#define REALMBOUND_TFT_SCLK 18
#define REALMBOUND_TFT_MOSI 23

// Display driver selection.
#define REALMBOUND_DISPLAY_ST7735 1
#define REALMBOUND_DISPLAY_ST7789 2
#define REALMBOUND_DISPLAY_DRIVER REALMBOUND_DISPLAY_ST7735

// ST7735 boards often use INITR_BLACKTAB, INITR_GREENTAB, or INITR_REDTAB.
#define REALMBOUND_TFT_TAB INITR_BLACKTAB

// Only used by the ST7789 driver option.
#define REALMBOUND_TFT_WIDTH 160
#define REALMBOUND_TFT_HEIGHT 128

#define REALMBOUND_TFT_ROTATION 1

// Buttons are active-low: one side to the GPIO, the other side to GND.
#define REALMBOUND_BUTTON_UP 32
#define REALMBOUND_BUTTON_DOWN 33
#define REALMBOUND_BUTTON_SELECT 25
#define REALMBOUND_BUTTON_BACK 26
