#pragma once
#include <Arduino.h>
#include <TouchScreen.h>

// Hasil kalibrasi Uno pengguna, dalam orientasi landscape (rotasi 1).
class CalibratedTouch {
  static const uint8_t XP=6, XM=A2, YP=A1, YM=7;
  static const int LEFT=146, RIGHT=894, TOP=920, BOTTOM=187;
  TouchScreen panel;
  unsigned long lastSample=0, began=0, lastContact=0;
  int startX=0, startY=0;
  bool down=false, tap=false;

public:
  enum Event { NONE, DOWN, TAP, SWIPE_LEFT, SWIPE_RIGHT };
  static const uint8_t ROTATION=1;
  int x=0, y=0;

  CalibratedTouch() : panel(XP, YP, XM, YM, 300) {}

  Event poll(unsigned long now) {
    if (now-lastSample < 8) return NONE;
    lastSample=now;
    TSPoint p=panel.getPoint();
    pinMode(XM, OUTPUT);
    pinMode(YP, OUTPUT);

    if (p.z>200 && p.z<1000) {
      long mappedX=map(p.y, TOP, BOTTOM, 0, 319);
      long mappedY=map(p.x, RIGHT, LEFT, 0, 239);
      x=constrain(mappedX, 0L, 319L);
      y=constrain(mappedY, 0L, 239L);
      lastContact=now;
      if (!down) {
        down=tap=true;
        startX=x; startY=y; began=now;
        return DOWN;
      }
      if (abs(x-startX)>14 || abs(y-startY)>14) tap=false;
      return NONE;
    }

    if (!down || now-lastContact<32) return NONE;
    down=false;
    int dx=x-startX, dy=y-startY;
    if (abs(dx)>55 && abs(dx)>abs(dy)) return dx<0 ? SWIPE_LEFT : SWIPE_RIGHT;
    return tap && lastContact-began>=16 ? TAP : NONE;
  }
};
