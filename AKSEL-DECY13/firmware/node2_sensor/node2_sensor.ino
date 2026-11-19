#include <AcceleratorLink.h>
// 0 = kabel langsung; 1 = shield TFT dan rangkaian I/O pada README.
#ifndef USE_LOCAL_TFT
#define USE_LOCAL_TFT 1
#endif
#if USE_LOCAL_TFT
#include <NodePanel.h>
NodePanel panel;
#endif


UsbLink usb;
#if USE_LOCAL_TFT
// 74HC4051: C/S2 dan INH ke GND; A5 membaca kanal Y0, Y1, Y2.
int sampleAdc[3] = {};  // Sampel yang sama untuk telemetri dan halaman ADC.
const byte MUX_A=11, MUX_B=13, MUX_OUT=A5, DIGITAL_IN=12;
#else
const byte DIGITAL_IN=2;
#endif
int tempOffset=0;                    // 0.1 °C, RAM only
unsigned long lastSample=0;
bool firstSample=true;
long pressurePa=0;
int hvVolts=0, rawTempDc=0;
bool digitalClosed=false;

int readChannel(byte channel) {
#if USE_LOCAL_TFT
  digitalWrite(MUX_A,channel & 1);
  digitalWrite(MUX_B,(channel >> 1) & 1);
  analogRead(MUX_OUT);  // Waktu peralihan mux dan pengisian ADC.
  sampleAdc[channel] = analogRead(MUX_OUT);
  return sampleAdc[channel];
#else
  const byte pins[]={A0,A1,A2};
  return analogRead(pins[channel]);
#endif
}

bool setOffset(long value) {
  if (value < -200 || value > 200) return false;
  tempOffset=int(value);
  return true;
}

#if USE_LOCAL_TFT
void formatSuhu(char (&line)[26], PGM_P label, int dc) {
  snprintf_P(line, sizeof(line), PSTR("%S %s%d.%d C"), label, dc < 0 ? "-" : "",
             abs(dc) / 10, abs(dc) % 10);
}

void localScreen(unsigned long now) {
  byte key = panel.button(now);
  byte page = panel.page();
  if (key == 1) setOffset(max(-200, tempOffset - 10));
  if (key == 2) setOffset(0);
  if (key == 3) setOffset(min(200, tempOffset + 10));

  if (panel.needsFrame()) {
    if (page == 2) panel.drawFrame(F("Sensor - Input ADC"), nullptr, nullptr, nullptr);
    else panel.drawFrame(page == 0 ? F("Sensor - Pantau") : F("Sensor - Kalibrasi"),
                         F("-1 C"), F("Nol"), F("+1 C"));
    return;
  }
  int row = panel.dueRow(now);
  if (row < 0) return;
  char line[26];
  if (page == 0) {
    switch (row) {
      case 0: snprintf_P(line, sizeof(line), PSTR("Vakum %ld Pa"), pressurePa); break;
      case 1: snprintf_P(line, sizeof(line), PSTR("Tegangan %d V"), hvVolts); break;
      case 2: formatSuhu(line, PSTR("Suhu"), rawTempDc + tempOffset); break;
      default: snprintf_P(line, sizeof(line), PSTR("Kontak %S"),
                          digitalClosed ? PSTR("tertutup") : PSTR("terbuka")); break;
    }
  } else if (page == 1) {
    switch (row) {
      case 0: formatSuhu(line, PSTR("Suhu awal"), rawTempDc); break;
      case 1: formatSuhu(line, PSTR("Offset"), tempOffset); break;
      case 2: formatSuhu(line, PSTR("Hasil"), rawTempDc + tempOffset); break;
      default: snprintf_P(line, sizeof(line), PSTR("Batas offset +/-20 C")); break;
    }
  } else {
    switch (row) {
      case 0: snprintf_P(line, sizeof(line), PSTR("ADC vakum    %4d"), sampleAdc[0]); break;
      case 1: snprintf_P(line, sizeof(line), PSTR("ADC tegangan %4d"), sampleAdc[1]); break;
      case 2: snprintf_P(line, sizeof(line), PSTR("ADC suhu     %4d"), sampleAdc[2]); break;
      default: snprintf_P(line, sizeof(line), PSTR("Input digital D12  %d"), digitalClosed); break;
    }
  }
  panel.row(row, line);
}
#endif

void setup() {
#if USE_LOCAL_TFT
  digitalWrite(10,HIGH); pinMode(10,OUTPUT);  // Nonaktifkan chip-select microSD.
  pinMode(MUX_A,OUTPUT); pinMode(MUX_B,OUTPUT);
  panel.begin();
#endif
  pinMode(DIGITAL_IN,INPUT_PULLUP);
  Serial.begin(115200);
}

void loop() {
  usb.pump();
  if (usb.idle() && usb.receive()) {
    Message &m=usb.msg;
    if (m.is(PSTR("node"),PSTR("sensor")) && m.is(PSTR("src"),PSTR("pi")) &&
        m.is(PSTR("type"),PSTR("cmd"))) {
      long id=m.num(PSTR("id")), v=m.num(PSTR("val"));
      if (id>=1 && id<=32767) {
        bool ok=true;
        if (m.is(PSTR("action"),PSTR("CAL_TEMP"))) ok=setOffset(v);
        else if (m.is(PSTR("action"),PSTR("RESET")) && v==1) setOffset(0);
        else ok=false;
        usb.send(PSTR("{\"node\":\"sensor\",\"type\":\"ack\",\"id\":%ld,\"ok\":%d,\"offset_dc\":%d}"),id,ok,tempOffset);
      }
    }
  }
  unsigned long now=millis();
  if (usb.idle() && (firstSample || now-lastSample>=200)) {
    firstSample=false; lastSample=now;
    pressurePa=readChannel(0)*101325L/1023;
    hvVolts=readChannel(1)*1000L/1023;
    rawTempDc=readChannel(2)*1000L/1023;
    digitalClosed=digitalRead(DIGITAL_IN)==LOW;
    usb.send(PSTR("{\"node\":\"sensor\",\"type\":\"telemetry\",\"vac_pa\":%ld,\"hv_v\":%d,\"temp_dc\":%d,\"din\":%d,\"offset_dc\":%d}"),
             pressurePa,hvVolts,rawTempDc+tempOffset,digitalClosed,tempOffset);
  }
#if USE_LOCAL_TFT
  localScreen(now);
#endif
}
