#pragma once
#include <MCUFRIEND_kbv.h>
#include <CalibratedTouch.h>
#include <avr/pgmspace.h>
#include <string.h>

// Panel bersama untuk TFT sensor dan aktuator.
class NodePanel {
  MCUFRIEND_kbv tft;
  CalibratedTouch touch;
  char previous[4][26] = {};
  byte pageIndex = 0, framePart = 0, nextRow = 0;
  byte pressed = 0, enabledKeys = 0;
  unsigned long lastRow = 0;
  static const uint16_t BG = 0x0841, CYAN = 0x05DF, WHITE = 0xffff;

  byte keyAt(int x, int y) const {
    if (y < 32 && x >= 240) return 4;  // Tombol MODE di kanan atas.
    if (framePart < 4 || y < 184 || y >= 230) return 0;
    for (byte i = 0; i < 3; ++i) {
      int left = 8 + i * 104;
      if ((enabledKeys & (1 << i)) && x >= left && x < left + 96) return i + 1;
    }
    return 0;
  }

  void changePage(byte advance) {
    pageIndex = (pageIndex + advance) % 3;
    framePart = nextRow = pressed = enabledKeys = 0;
  }

public:
  void begin() {
    uint16_t id = tft.readID();
    tft.begin(id == 0xD3D3 ? 0x9341 : id);
    tft.setRotation(CalibratedTouch::ROTATION);
    tft.setTextWrap(false);
    tft.fillScreen(BG);
  }

  byte page() const { return pageIndex; }
  bool needsFrame() const { return framePart < 4; }

  byte button(unsigned long now) {
    CalibratedTouch::Event e = touch.poll(now);
    if (e == CalibratedTouch::DOWN) pressed = keyAt(touch.x, touch.y);
    if (e == CalibratedTouch::SWIPE_LEFT) changePage(1);
    if (e == CalibratedTouch::SWIPE_RIGHT) changePage(2);
    if (e == CalibratedTouch::TAP && pressed && pressed == keyAt(touch.x, touch.y)) {
      byte key = pressed;
      pressed = 0;
      if (key <= 3) return key;
      changePage(1);
    }
    return 0;
  }

  // Gambar satu bagian per putaran agar serial dan interlock tetap dilayani.
  void drawFrame(const __FlashStringHelper *title, const __FlashStringHelper *left,
                 const __FlashStringHelper *middle, const __FlashStringHelper *right) {
    if (!needsFrame()) return;
    if (framePart == 0) {
      tft.fillRect(0, 0, 320, 32, BG);
      tft.setTextColor(WHITE); tft.setTextSize(2);
      tft.setCursor(8, 8); tft.print(title);
      tft.setTextColor(CYAN); tft.setTextSize(1);
      tft.setCursor(263, 1); tft.print(F("MODE >"));
      tft.setTextSize(2); tft.setCursor(261, 13);
      tft.print(pageIndex + 1); tft.print(F("/3"));
      tft.drawFastHLine(0, 32, 320, CYAN);
    } else {
      byte i = framePart - 1;
      int x = 8 + i * 104;
      const __FlashStringHelper *label = i == 0 ? left : i == 1 ? middle : right;
      if (label) {
        enabledKeys |= 1 << i;
        tft.fillRoundRect(x, 184, 96, 46, 5, CYAN);
        int width = 12 * strlen_P(reinterpret_cast<PGM_P>(label));
        tft.setTextSize(2); tft.setTextColor(BG);
        tft.setCursor(x + (96 - width) / 2, 199); tft.print(label);
      } else {
        tft.fillRect(x, 184, 96, 46, BG);
      }
    }
    ++framePart;
  }

  int dueRow(unsigned long now) {
    if (needsFrame() || now - lastRow < 35) return -1;
    lastRow = now;
    byte row = nextRow;
    nextRow = (nextRow + 1) % 4;
    return row;
  }

  void row(byte i, const char (&value)[26]) {
    char *old = previous[i];
    if (strcmp(old, value) == 0) return;
    tft.setCursor(10, 45 + 32 * i);
    tft.setTextSize(2); tft.setTextColor(WHITE, BG);
    tft.print(value);
    for (int n = int(strlen(old)) - int(strlen(value)); n > 0; --n) tft.print(' ');
    strcpy(old, value);
  }
};
