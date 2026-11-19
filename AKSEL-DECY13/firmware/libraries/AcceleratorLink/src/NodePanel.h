#pragma once
#include <MCUFRIEND_kbv.h>
#include <CalibratedTouch.h>
#include <string.h>
#include <avr/pgmspace.h>

// Panel lokal untuk sensor dan aktuator.
class NodePanel {
  MCUFRIEND_kbv tft;
  CalibratedTouch touch;
  char previous[4][26]={};
  byte pressed=0, next=0;
  unsigned long lastRow=0;
  static const uint16_t BG=0x0841, CYAN=0x05DF, WHITE=0xffff;

  byte keyAt(int x,int y) const {
    if (y<184 || y>=230) return 0;
    for (byte i=0; i<3; ++i) {
      int left=8+i*104;
      if (x>=left && x<left+96) return i+1;
    }
    return 0;
  }

public:
  void begin(const __FlashStringHelper *title, const __FlashStringHelper *left,
             const __FlashStringHelper *middle, const __FlashStringHelper *right) {
    uint16_t id=tft.readID();
    tft.begin(id==0xD3D3 ? 0x9341 : id);
    tft.setRotation(CalibratedTouch::ROTATION);
    tft.setTextWrap(false);
    tft.fillScreen(BG);
    tft.setTextSize(2);
    tft.setTextColor(CYAN);
    tft.setCursor(10,8); tft.print(title);
    tft.drawFastHLine(0,32,320,CYAN);
    const __FlashStringHelper *labels[]={left,middle,right};
    for (byte i=0; i<3; ++i) {
      int x=8+104*i;
      tft.fillRoundRect(x,184,96,46,5,CYAN);
      int width=12*strlen_P(reinterpret_cast<PGM_P>(labels[i]));
      tft.setCursor(x+(96-width)/2,199);
      tft.setTextColor(BG); tft.print(labels[i]);
    }
  }

  byte button(unsigned long now) {
    CalibratedTouch::Event e=touch.poll(now);
    if (e==CalibratedTouch::DOWN) pressed=keyAt(touch.x,touch.y);
    if (e==CalibratedTouch::TAP && pressed==keyAt(touch.x,touch.y)) return pressed;
    return 0;
  }

  // Draw at most one changed row per tick; return to the USB/interlock loop.
  int dueRow(unsigned long now) {
    if (now-lastRow<35) return -1;
    lastRow=now;
    byte row=next;
    next=(next+1)%4;
    return row;
  }

  void row(byte i,const char (&value)[26]) {
    char *old=previous[i];
    if (strcmp(old,value)==0) return;
    tft.setCursor(10,45+32*i);
    tft.setTextColor(WHITE,BG);
    tft.print(value);
    for (int n=int(strlen(old))-int(strlen(value)); n>0; --n) tft.print(' ');
    strcpy(old,value);   // The caller formats each line into char[26].
  }
};
