#include <AcceleratorLink.h>
// 0 = kabel langsung; 1 = shield TFT dan rangkaian I/O pada README.
#ifndef USE_LOCAL_TFT
#define USE_LOCAL_TFT 0
#endif
#if USE_LOCAL_TFT
#include <NodePanel.h>
NodePanel panel;
#endif


UsbLink usb;
// Logic-level driver inputs. Change this polarity before wiring active-low modules.
const byte OUTPUT_ON=HIGH, OUTPUT_OFF=LOW;
#if USE_LOCAL_TFT
// Shield tanpa kartu SD. OE ditahan HIGH oleh pull-up eksternal saat Uno reset.
const byte INTERLOCK=A5, SHIFT_OE=10, SHIFT_DATA=11, SHIFT_LATCH=12, SHIFT_CLOCK=13;
#else
const byte INTERLOCK=2, RELAY=4, VALVE=5, FAN=6, BUZZ=7, GREEN=8, YELLOW=9, RED=10;
#endif
enum { STANDBY, RUNNING, PAUSED };
enum { LED_MASK=3, FAN_BIT=4, BUZZ_BIT=8, RELAY_BIT=16, VALVE_BIT=32 };
int rpm=0, targetRPM=6000;
byte mode=STANDBY, rate=1, bits=0;
bool rising=true, automatic=false, lease=false, guard=false, closing=false, dirty=true;
unsigned long lastBeat=0, closedSince=0, standbySince=0, lastStep=0, lastReport=0;

#if USE_LOCAL_TFT
void writeDriver(byte next) {
  // Q0..Q6: relai, katup, kipas, buzzer, LED hijau, kuning, merah.
  byte levels=((next >> 4) & 3) | (next & (FAN_BIT|BUZZ_BIT));
  byte led=next & LED_MASK;
  if (led) levels |= byte(1U << (led+3));
  if (OUTPUT_ON==LOW) levels=~levels;
  if (!next) digitalWrite(SHIFT_OE,HIGH);
  digitalWrite(SHIFT_LATCH,LOW);
  shiftOut(SHIFT_DATA,SHIFT_CLOCK,MSBFIRST,levels);
  digitalWrite(SHIFT_LATCH,HIGH);
  digitalWrite(SHIFT_OE,next ? LOW : HIGH);
}
#endif

void outputs(byte next) {
  if (bits==next) return;
  bits=next; dirty=true;
#if USE_LOCAL_TFT
  writeDriver(next);
#else
  digitalWrite(RELAY,bits&RELAY_BIT ? OUTPUT_ON : OUTPUT_OFF);
  digitalWrite(VALVE,bits&VALVE_BIT ? OUTPUT_ON : OUTPUT_OFF);
  digitalWrite(FAN,bits&FAN_BIT ? OUTPUT_ON : OUTPUT_OFF);
  digitalWrite(BUZZ,bits&BUZZ_BIT ? OUTPUT_ON : OUTPUT_OFF);
  digitalWrite(GREEN,(bits&LED_MASK)==1 ? OUTPUT_ON : OUTPUT_OFF);
  digitalWrite(YELLOW,(bits&LED_MASK)==2 ? OUTPUT_ON : OUTPUT_OFF);
  digitalWrite(RED,(bits&LED_MASK)==3 ? OUTPUT_ON : OUTPUT_OFF);
#endif
}

void trip() {
  outputs(0); mode=PAUSED; rpm=0; rising=true; automatic=false; dirty=true;
}

void safety(unsigned long now) {
  if (lease && now-lastBeat>3000UL) { lease=false; trip(); }
  if (digitalRead(INTERLOCK)!=LOW) {
    closing=false;
    if (guard) { guard=false; trip(); }
  } else if (!closing) {
    closing=true; closedSince=now;
  } else if (!guard && now-closedSince>=50) {
    guard=true; dirty=true;
  }
}

void autoOutputs() {
  byte led=rpm==0 ? 0 : rpm>=targetRPM/100*80 ? 3 : rpm>=targetRPM/2 ? 2 : 1;
  outputs(led | RELAY_BIT | (rpm>3500 ? FAN_BIT : 0) |
          (rpm>=targetRPM/100*85 ? BUZZ_BIT : 0));
}

void startRun(unsigned long now) {
  if (mode==RUNNING) return;
  mode=RUNNING; lastStep=now; autoOutputs(); dirty=true;
}

// Return codes: 0 accepted, 1 invalid, 2 no heartbeat, 3 interlock open, 4 running.
byte command(const char *a,long v,unsigned long now) {
  if (!strcmp_P(a,PSTR("STOP")) && v==1) {
    outputs(0); mode=PAUSED; return 0;
  }
  if (!strcmp_P(a,PSTR("RESET")) && v==1) {
    outputs(0); mode=STANDBY; rpm=0; rising=true; standbySince=now; return 0;
  }
  if (!strcmp_P(a,PSTR("TARGET")) && v>=2000 && v<=9000 && v%500==0) {
    targetRPM=v;
    if (rpm>=targetRPM) { rpm=targetRPM; rising=false; }
    if (mode==RUNNING) autoOutputs();
    return 0;
  }
  if (!strcmp_P(a,PSTR("RATE")) && v>=0 && v<=2) { rate=v; return 0; }
  if (!lease) return 2;
  if (!guard) return 3;
  if (!strcmp_P(a,PSTR("START")) && v==1) { startRun(now); return 0; }
  if (!strcmp_P(a,PSTR("AUTO")) && (v==0 || v==1)) {
    automatic=v; standbySince=now; return 0;
  }
  if (mode==RUNNING) return 4;
  byte mask=0;
  if (!strcmp_P(a,PSTR("LED"))) mask=LED_MASK;
  else if (!strcmp_P(a,PSTR("FAN"))) mask=FAN_BIT;
  else if (!strcmp_P(a,PSTR("BUZZER"))) mask=BUZZ_BIT;
  else if (!strcmp_P(a,PSTR("RELAY_1"))) mask=RELAY_BIT;
  else if (!strcmp_P(a,PSTR("VALVE"))) mask=VALVE_BIT;
  if (!mask || v<0 || v>(mask==LED_MASK ? 3 : 1)) return 1;
  mode=PAUSED;
  outputs((bits & ~mask) | (mask==LED_MASK ? byte(v) : v ? mask : 0));
  return 0;
}

#if USE_LOCAL_TFT
void localScreen(unsigned long now) {
  static byte result=0;
  byte key=panel.button(now);
  if (key) {
    // Re-evaluate the physical contact and heartbeat at the point of use.
    unsigned long sampled=millis();
    safety(sampled);
    if (key==1) result=command("FAN",!(bits & FAN_BIT),sampled);
    if (key==2) result=command("RELAY_1",!(bits & RELAY_BIT),sampled);
    if (key==3) result=command("STOP",1,sampled);
    dirty=true;
  }
  int row=panel.dueRow(now);
  if (row<0) return;
  char line[26];
  switch (row) {
    case 0: snprintf_P(line,sizeof(line),PSTR("RPM %d / %d"),rpm,targetRPM); break;
    case 1: snprintf_P(line,sizeof(line),PSTR("Kontak %S  Pi %S"),guard?PSTR("OK"):PSTR("buka"),lease?PSTR("OK"):PSTR("--")); break;
    case 2: snprintf_P(line,sizeof(line),PSTR("Kipas %d  Relai %d"),!!(bits&FAN_BIT),!!(bits&RELAY_BIT)); break;
    default:
      snprintf_P(line,sizeof(line),PSTR("%S"),result==2 ? PSTR("Heartbeat belum aktif") :
                 result==3 ? PSTR("Interlock terbuka") : result==4 ? PSTR("Jeda untuk uji manual") :
                 mode==RUNNING ? PSTR("Berjalan") : mode==PAUSED ? PSTR("Dijeda") : PSTR("Siaga"));
      break;
  }
  panel.row(row,line);
}
#endif

void setup() {
#if USE_LOCAL_TFT
  digitalWrite(SHIFT_OE,HIGH); pinMode(SHIFT_OE,OUTPUT);
  pinMode(SHIFT_DATA,OUTPUT); pinMode(SHIFT_CLOCK,OUTPUT); pinMode(SHIFT_LATCH,OUTPUT);
  writeDriver(0);
#else
  const byte pins[]={RELAY,VALVE,FAN,BUZZ,GREEN,YELLOW,RED};
  for (byte p:pins) { digitalWrite(p,OUTPUT_OFF); pinMode(p,OUTPUT); }
#endif
  pinMode(INTERLOCK,INPUT_PULLUP);
  Serial.begin(115200);
#if USE_LOCAL_TFT
  panel.begin(F("Node 3 - Aktuator"),F("Kipas"),F("Relai"),F("Jeda"));
#endif
}

void loop() {
  unsigned long now=millis();
  safety(now);
  usb.pump();
  if (usb.idle() && usb.receive()) {
    Message &m=usb.msg;
    if (m.is(PSTR("node"),PSTR("actuator")) && m.is(PSTR("src"),PSTR("pi"))) {
      if (m.is(PSTR("type"),PSTR("heartbeat"))) {
        if (!lease) dirty=true;
        lease=true; lastBeat=now;
      } else if (m.is(PSTR("type"),PSTR("cmd"))) {
        long id=m.num(PSTR("id"));
        if (id>=1 && id<=32767) {
          byte rc=command(m.word(PSTR("action")),m.num(PSTR("val")),now); dirty=true;
          usb.send(PSTR("{\"node\":\"actuator\",\"type\":\"ack\",\"id\":%ld,\"ok\":%d,\"code\":%u,\"bits\":%u}"),
                   id,rc==0,unsigned(rc),unsigned(bits));
        }
      }
    }
  }
  if (lease && guard && mode==STANDBY && automatic && now-standbySince>=10000UL) startRun(now);
  if (mode==RUNNING && now-lastStep>=35) {
    lastStep=now;
    if (rising) {
      rpm=min(targetRPM,rpm+(rate==0 ? 45 : rate==1 ? 90 : 180));
      if (rpm==targetRPM) rising=false;
    } else {
      rpm=max(800,rpm-(rate==0 ? 35 : rate==1 ? 70 : 140));
      if (rpm==800) rising=true;
    }
    autoOutputs();
  }
  if (usb.idle() && (now-lastReport>=200 || (dirty && now-lastReport>=60))) {
    lastReport=now; dirty=false;
    unsigned long elapsed=now-standbySince;
    int left=(mode==STANDBY && automatic && elapsed<10000UL) ? 10-int(elapsed/1000) : 0;
    usb.send(PSTR("{\"node\":\"actuator\",\"type\":\"telemetry\",\"rpm\":%d,\"target\":%d,\"mode\":%u,\"rate\":%u,\"auto\":%d,\"left\":%d,\"bits\":%u,\"guard\":%d,\"link\":%d}"),
             rpm,targetRPM,unsigned(mode),unsigned(rate),automatic,left,unsigned(bits),guard,lease);
  }
#if USE_LOCAL_TFT
  localScreen(now);
#endif
}
