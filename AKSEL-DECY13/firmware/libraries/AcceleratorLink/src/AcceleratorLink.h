#pragma once
#include <Arduino.h>
#include <avr/pgmspace.h>
#include <stdlib.h>
#include <stdio.h>
#include <stdarg.h>
#include <string.h>
#include <limits.h>
#include <errno.h>

// Wire subset: plain ASCII string keys, plain ASCII strings or signed int32
// values. Reject duplicate keys, truncation, trailing input and malformed lines.
class Message {
  struct Field { char *key, *value; bool string; };
  Field fields[16];
  byte count = 0;
  static void spaces(char *&p) { while (*p == ' ' || *p == '\t' || *p == '\r') ++p; }
  static char *quoted(char *&p) {
    if (*p != '"') return nullptr;
    char *start = ++p;
    while (*p && *p != '"') {
      if ((uint8_t)*p < 32 || (uint8_t)*p > 126 || *p == '\\') return nullptr;
      ++p;
    }
    if (!*p) return nullptr;
    *p++ = 0;
    return start;
  }
  const Field *find(PGM_P key) const {
    for (byte i=0; i<count; ++i) if (!strcmp_P(fields[i].key,key)) return &fields[i];
    return nullptr;
  }
public:
  bool parse(char *p) {
    count=0; spaces(p);
    if (*p++ != '{') return false;
    while (count < 16) {
      spaces(p);
      char *k=quoted(p);
      if (!k) return false;
      for (byte i=0; i<count; ++i) if (!strcmp(k,fields[i].key)) return false;
      spaces(p); if (*p++ != ':') return false;
      spaces(p);
      bool str=*p=='"'; char *v=p;
      if (str) {
        v=quoted(p); if (!v) return false;
      } else {
        if (*p=='-') ++p;
        if (*p<'0' || *p>'9') return false;
        if (*p=='0') ++p;
        else while (*p>='0' && *p<='9') ++p;
      }
      char *end=p; spaces(p);
      char separator=*p;
      if (separator!=',' && separator!='}') return false;
      ++p;
      if (!str) *end=0;
      fields[count++]={k,v,str};
      if (separator=='}') { spaces(p); return *p==0; }
    }
    return false;
  }
  const char *word(PGM_P key) const {
    const Field *f=find(key);
    return f && f->string ? f->value : "";
  }
  bool is(PGM_P key, PGM_P value) const { return strcmp_P(word(key),value)==0; }
  long num(PGM_P key, long fallback=LONG_MIN) const {
    const Field *f=find(key);
    if (!f || f->string) return fallback;
    errno=0;
    long n=strtol(f->value,nullptr,10);
    return errno==ERANGE ? fallback : n;
  }
};

class UsbLink {
  static const byte SIZE=184;
  char rx[SIZE], tx[SIZE];
  byte used=0, sent=0, length=0;
  bool discard=false;
public:
  Message msg;
  void pump() {
    int room=Serial.availableForWrite();
    if (sent<length && room>0) {
      int left=length-sent;
      sent+=Serial.write((const uint8_t *)tx+sent,min(left,room));
    }
  }
  bool idle() const { return sent==length; }
  bool send(PGM_P format, ...) {
    if (!idle()) return false;
    va_list args; va_start(args,format);
    int n=vsnprintf_P(tx,sizeof(tx),format,args);
    va_end(args);
    if (n<1 || n>=SIZE-1) return false;
    tx[n]='\n'; length=n+1; sent=0; pump(); return true;
  }
  bool receive() {
    for (byte i=0; i<64 && Serial.available(); ++i) {
      int c=Serial.read();
      if (c=='\n') {
        rx[used]=0;
        bool valid=!discard && msg.parse(rx);
        used=0; discard=false;
        if (valid) return true;
      } else if (!discard) {
        if (c<=0 || used>=sizeof(rx)-1) discard=true;
        else rx[used++]=char(c);
      }
    }
    return false;
  }
};
