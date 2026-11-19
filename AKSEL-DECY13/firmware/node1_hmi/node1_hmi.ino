#include <AcceleratorLink.h>
#include <Adafruit_GFX.h>
#include <MCUFRIEND_kbv.h>
#include <CalibratedTouch.h>
#include <avr/pgmspace.h>
#include <stdio.h>
#include <string.h>

// ============================================================
// TFT dan touchscreen. Kalibrasi mengikuti sketch awal.
// ============================================================

MCUFRIEND_kbv tft;

CalibratedTouch touchPanel;


// Warna RGB565
const uint16_t BG     = 0x0841;
const uint16_t PANEL  = 0x10A2;
const uint16_t EDGE   = 0x4228;
const uint16_t MUTED  = 0xAD55;
const uint16_t CYAN   = 0x05DF;
const uint16_t BLUE   = 0x03DF;
const uint16_t GREEN  = 0x07E0;
const uint16_t YELLOW = 0xFFE0;
const uint16_t RED    = 0xF800;
const uint16_t WHITE  = 0xFFFF;

// ============================================================
// Keadaan sistem
// ============================================================

enum { SIAGA, AKTIF, JEDA };

enum {
  TANPA_TOMBOL,
  TOMBOL_MULAI,
  TOMBOL_ULANG,
  RPM_KURANG,
  RPM_TAMBAH,
  LAJU_KURANG,
  LAJU_TAMBAH,
  TOMBOL_OTOMATIS,
  UJI_LED,
  UJI_KIPAS,
  UJI_ALARM,
  UJI_RELAI,
  UJI_KATUP
};

// Dua bit pertama untuk LED. Bit berikutnya untuk keluaran biner.
const byte MASK_LED   = 0x03;
const byte MASK_KIPAS = 0x04;
const byte MASK_ALARM = 0x08;
const byte MASK_RELAI = 0x10;

byte modeSistem = SIAGA;
byte currentPage = 0;
byte laju = 1;                       // 0 lambat, 1 normal, 2 cepat

int rpm = 0;
int target = 6000;

UsbLink usb;
bool otomatis=false, pembuka=true, guard=false, linkAktuator=false;
bool adaSensor=false, adaAktuator=false, adaPi=false, sensorKotor=true;
byte bits=0, sisa=0, pesan=0, barisHapus=0, bagianLayar=0;
long nilaiLama[5], vakum=0;
int tegangan=0, suhu=0;
unsigned int urutan=0, menunggu=0;
PGM_P aksiKirim=nullptr;
int nilaiKirim=0;
unsigned long mulaiPembuka=0, rxSensor=0, rxAktuator=0, rxPi=0, waktuCmd=0, waktuPaket=0;
bool infoKotor=true, tungguStatus=false;
byte inputDigital=0;

byte zonaRPM() {
  return rpm==0 ? 0 : rpm>=target/100*80 ? 3 : rpm>=target/2 ? 2 : 1;
}

void pindahHalaman(byte halaman) {
  currentPage=halaman; barisHapus=bagianLayar=0;
  for (byte i=0; i<5; ++i) nilaiLama[i]=-1;
  sensorKotor=infoKotor=true;
}

void tekanTombol(byte tombol, unsigned long sekarang) {
  if (!tombol) return;
  if (!adaAktuator || !adaPi) { pesan=6; infoKotor=true; return; }
  if (menunggu || tungguStatus) { pesan=7; infoKotor=true; return; }
  PGM_P action;
  int val=1;
  switch (tombol) {
    case TOMBOL_MULAI: action=modeSistem==AKTIF ? PSTR("STOP") : PSTR("START"); break;
    case TOMBOL_ULANG: action=PSTR("RESET"); break;
    case RPM_KURANG: case RPM_TAMBAH:
      action=PSTR("TARGET"); val=constrain(target+(tombol==RPM_TAMBAH?500:-500),2000,9000); break;
    case LAJU_KURANG: case LAJU_TAMBAH:
      action=PSTR("RATE"); val=constrain(int(laju)+(tombol==LAJU_TAMBAH?1:-1),0,2); break;
    case TOMBOL_OTOMATIS: action=PSTR("AUTO"); val=!otomatis; break;
    case UJI_LED: action=PSTR("LED"); val=((bits&MASK_LED)+1)%4; break;
    case UJI_KIPAS: action=PSTR("FAN"); val=!(bits&MASK_KIPAS); break;
    case UJI_ALARM: action=PSTR("BUZZER"); val=!(bits&MASK_ALARM); break;
    case UJI_RELAI: action=PSTR("RELAY_1"); val=!(bits&MASK_RELAI); break;
    case UJI_KATUP: action=PSTR("VALVE"); val=!(bits&32); break;
    default: return;
  }
  urutan=urutan%32767+1;
  menunggu=urutan; aksiKirim=action; nilaiKirim=val;
  waktuCmd=sekarang; pesan=7; infoKotor=true;
}

void kirimPerintah() {
  if (!aksiKirim) return;
  if (!adaAktuator || !adaPi) { aksiKirim=nullptr; menunggu=0; pesan=6; infoKotor=true; return; }
  if (usb.send(PSTR("{\"node\":\"hmi\",\"type\":\"cmd\",\"target\":\"actuator\",\"action\":\"%S\",\"val\":%d,\"id\":%u}"),
               aksiKirim,nilaiKirim,menunggu)) aksiKirim=nullptr;
}

void terima(unsigned long now) {
  if (!usb.receive()) return;
  Message &m=usb.msg;
  if (m.is(PSTR("node"),PSTR("hmi")) && m.is(PSTR("type"),PSTR("heartbeat")) && m.is(PSTR("src"),PSTR("pi"))) {
    if (!adaPi) infoKotor=true;
    adaPi=true; rxPi=now;
  } else if (m.is(PSTR("node"),PSTR("sensor")) && m.is(PSTR("type"),PSTR("telemetry"))) {
    long p=m.num(PSTR("vac_pa")), v=m.num(PSTR("hv_v")), t=m.num(PSTR("temp_dc"));
    if (p<0 || p>101325 || v<0 || v>1000 || t < -200 || t>1200) return;
    byte din=m.num(PSTR("din"),0)==1;
    sensorKotor |= !adaSensor || p!=vakum || v!=tegangan || t!=suhu || din!=inputDigital;
    inputDigital=din;
    vakum=p; tegangan=v; suhu=t; rxSensor=now; adaSensor=true;
  } else if (m.is(PSTR("node"),PSTR("actuator"))) {
    if (m.is(PSTR("type"),PSTR("ack"))) {
      if (menunggu && m.num(PSTR("id"))==menunggu) {
        menunggu=0; tungguStatus=m.num(PSTR("ok"))==1; pesan=tungguStatus ? 1 : m.num(PSTR("code"),0)==6 ? 5 : 2; infoKotor=true;
      }
    } else if (m.is(PSTR("type"),PSTR("telemetry"))) {
      long tujuan=m.num(PSTR("target")), r=m.num(PSTR("rpm")), mask=m.num(PSTR("bits"));
      if (tujuan<2000 || tujuan>9000 || r<0 || r>tujuan || mask<0 || mask>63) return;
      bool g=m.num(PSTR("guard"),0)==1, l=m.num(PSTR("link"),0)==1;
      infoKotor |= !adaAktuator || guard!=g || linkAktuator!=l;
      guard=g; linkAktuator=l; target=tujuan; rpm=r; bits=mask;
      modeSistem=m.num(PSTR("mode"),0); laju=m.num(PSTR("rate"),1);
      otomatis=m.num(PSTR("auto"),0)==1; sisa=m.num(PSTR("left"),0);
      rxAktuator=now; adaAktuator=true; tungguStatus=false;
    }
  }
}

bool diDalam(int x, int y, int kiri, int atas, int lebar, int tinggi) {
  return x >= kiri && x < kiri + lebar && y >= atas && y < atas + tinggi;
}

byte tombolPada(int x, int y) {
  if (currentPage == 0) {
    if (diDalam(x, y, 10, 192, 145, 40)) return TOMBOL_MULAI;
    if (diDalam(x, y, 165, 192, 145, 40)) return TOMBOL_ULANG;
  } else if (currentPage == 1) {
    for (byte i = 0; i < 2; ++i) {
      int atas = 58 + 68 * i;
      if (diDalam(x, y, 10, atas, 60, 38))
        return i ? LAJU_KURANG : RPM_KURANG;
      if (diDalam(x, y, 250, atas, 60, 38))
        return i ? LAJU_TAMBAH : RPM_TAMBAH;
    }
    if (diDalam(x, y, 10, 183, 300, 43)) return TOMBOL_OTOMATIS;
  } else if (modeSistem != AKTIF) {
    for (byte i = 0; i < 5; ++i) {
      if (diDalam(x, y, 240, 35 + 38 * i, 70, 34)) return UJI_LED + i;
    }
  }
  return TANPA_TOMBOL;
}

void bacaSentuhan(unsigned long sekarang) {
  static byte tombolAwal=TANPA_TOMBOL;
  CalibratedTouch::Event event=touchPanel.poll(sekarang);
  if (event==CalibratedTouch::DOWN) tombolAwal=tombolPada(touchPanel.x, touchPanel.y);
  if (event==CalibratedTouch::TAP && tombolAwal==tombolPada(touchPanel.x, touchPanel.y))
    tekanTombol(tombolAwal, sekarang);
  if (event==CalibratedTouch::SWIPE_LEFT || event==CalibratedTouch::SWIPE_RIGHT) {
    pindahHalaman((currentPage+(event==CalibratedTouch::SWIPE_LEFT ? 1 : 2))%3);
    waktuPaket=sekarang-100UL;
  }
}

// ---------- Komponen tampilan ----------

void pena(int x, int y, byte ukuran, uint16_t warna) {
  tft.setCursor(x, y);
  tft.setTextSize(ukuran);
  tft.setTextColor(warna);
}

void label(int x, int y, byte ukuran, uint16_t warna,
           const __FlashStringHelper *teks) {
  pena(x, y, ukuran, warna);
  tft.print(teks);
}

void kotakTombol(int x, int y, int w, int h, uint16_t warna,
                 const __FlashStringHelper *teks) {
  tft.fillRoundRect(x, y, w, h, 5, warna);
  terima(millis()); usb.pump();
  int lebarTeks = 12 * strlen_P(reinterpret_cast<PGM_P>(teks));
  label(x + (w - lebarTeks) / 2, y + (h - 16) / 2, 2, BG, teks);
}

uint16_t warnaZona(byte zona) {
  if (zona == 3) return RED;
  if (zona == 2) return YELLOW;
  if (zona == 1) return GREEN;
  return MUTED;
}

bool berubah(byte slot, long nilai) {
  if (nilaiLama[slot] == nilai) return false;
  nilaiLama[slot] = nilai;
  return true;
}

void kerangka() {
  tft.fillRect(0, 0, 320, 28, PANEL);
  tft.drawFastHLine(0, 28, 320, CYAN);
  label(10, 6, 2, WHITE, currentPage == 0 ? F("Dasbor utama") :
                         currentPage == 1 ? F("Pengaturan") : F("Keluaran USB"));
  pena(274, 6, 2, CYAN);
  tft.print(currentPage + 1);
  tft.print(F("/3"));

  if (currentPage == 0) {
    tft.drawRoundRect(10, 35, 300, 82, 6, EDGE);
    label(20, 43, 1, MUTED, F("KECEPATAN PUTARAN"));
    label(250, 86, 2, CYAN, F("RPM"));
    tft.drawRect(10, 119, 300, 18, EDGE);
    kotakTombol(165, 192, 145, 40, CYAN, F("ULANG"));
  } else if (currentPage == 1) {
    for (byte i = 0; i < 2; ++i) {
      int y = 58 + 68 * i;
      label(12, y - 15, 1, MUTED,
            i ? F("KECEPATAN AKSELERASI") : F("TARGET RPM"));
      kotakTombol(10, y, 60, 38, CYAN, F("-"));
      kotakTombol(250, y, 60, 38, CYAN, F("+"));
    }
  } else {
    label(10, 223, 1, MUTED, F("Uji manual saat siaga atau dijeda"));
  }
}

void gambarDasbor(byte slot, unsigned long sekarang) {
  byte zona = zonaRPM();

  if (slot == 0 && berubah(0, adaAktuator ? rpm + zona * 10000L : -2L)) {
    char angka[5];
    snprintf_P(angka, sizeof(angka), PSTR("%04d"), rpm);
    pena(20, 64, 5, warnaZona(zona));
    tft.setTextColor(warnaZona(zona), BG);
    tft.print(adaAktuator ? angka : "----");
  }

  if (slot == 1) {
    int aktif = adaAktuator ? 24L * rpm / target : 0;
    int lama = nilaiLama[1];
    if (!berubah(1, aktif)) return;

    for (int i = 0; i < 24; ++i) {
      if (lama >= 0 && (i < lama) == (i < aktif)) continue;
      uint16_t warna = i >= 19 ? RED : i >= 12 ? YELLOW : GREEN;
      tft.fillRect(16 + 12 * i, 121, 9, 14, i < aktif ? warna : PANEL);
    }
  }

  if (slot == 2) {
    int status;

    if (!adaAktuator) status = 15;
    else if (modeSistem == SIAGA) status = otomatis ? sisa : 11;
    else if (modeSistem == JEDA) status = 12;
    else status = (bits & MASK_ALARM) ? 14 : 13;

    if (!berubah(2, status)) return;

    tft.fillRect(10, 155, 300, 28, PANEL);
    tft.drawRect(10, 155, 300, 28, EDGE);
    uint16_t warna = status == 14 ? RED : status == 12 ? YELLOW :
                     status == 13 ? GREEN : CYAN;
    pena(18, 162, 2, warna);

    if (status <= 10) {
      tft.print(F("Mulai dalam "));
      tft.print(sisa);
      tft.print(F(" detik"));
    } else {
      tft.print(status == 11 ? F("Siaga") : status == 12 ? F("Dijeda") :
                status == 13 ? F("Proses aktif") : status == 15 ? F("Menunggu aktuator") : F("Batas puncak"));
    }
  }

  if (slot == 3 && berubah(3, modeSistem == AKTIF)) {
    kotakTombol(10, 192, 145, 40, modeSistem == AKTIF ? RED : GREEN,
                modeSistem == AKTIF ? F("JEDA") : F("MULAI"));
  }
}

void gambarPengaturan(byte slot) {
  if (slot == 0 && berubah(0, target)) {
    pena(114, 69, 2, WHITE);
    tft.setTextColor(WHITE, BG);
    tft.print(target);
    tft.print(F(" RPM"));
  }

  if (slot == 1 && berubah(1, laju)) {
    pena(122, 137, 2, WHITE);
    tft.setTextColor(WHITE, BG);
    tft.print(laju == 0 ? F("Lambat") : laju == 1 ? F("Normal") : F("Cepat "));
  }

  if (slot == 2 && berubah(2, otomatis)) {
    kotakTombol(10, 183, 300, 43, otomatis ? GREEN : MUTED,
                otomatis ? F("Otomatis 10 dtk: NYALA") : F("Otomatis 10 dtk: MATI"));
  }
}

void gambarKeluaran(byte baris) {
  byte nilai = baris == 0 ? (bits & MASK_LED) :
                           ((bits & (1 << (baris + 1))) != 0);
  bool terkunci = modeSistem == AKTIF;
  if (!berubah(baris, nilai + 4 * terkunci + 8 * adaAktuator)) return;

  int y = 35 + 38 * baris;
  label(10, y + 10, 2, WHITE,
        baris == 0 ? F("Lampu") : baris == 1 ? F("Kipas") :
        baris == 2 ? F("Alarm") : baris == 3 ? F("Relai") : F("Katup"));

  const __FlashStringHelper *teks = nilai ? F("Nyala") : F("Mati");
  if (baris == 0 && nilai) {
    teks = nilai == 1 ? F("Hijau") : nilai == 2 ? F("Kuning") : F("Merah");
  }

  uint16_t warna = baris == 0 ? warnaZona(nilai) : nilai ? GREEN : MUTED;
  kotakTombol(108, y, 118, 34, adaAktuator ? warna : MUTED, adaAktuator ? teks : F("--"));
  kotakTombol(240, y, 70, 34, terkunci ? MUTED : CYAN,
              terkunci ? F("--") : F("Uji"));
}

void perbaruiLayar(unsigned long sekarang) {
  if (barisHapus < 240) {
    tft.fillRect(0, barisHapus, 320, 12, BG);
    barisHapus += 12;
    return;
  }

  if (barisHapus == 240) {
    kerangka();
    ++barisHapus;
    return;
  }

  if (infoKotor) {
    tft.fillRect(0,233,320,7,BG);
    label(10,233,1,CYAN,!adaPi ? F("USB: menunggu hub") : !adaAktuator ? F("Aktuator terputus") :
          !guard ? F("Interlock terbuka") : !linkAktuator ? F("Menunggu heartbeat") :
          pesan==1 ? F("Perintah diterima") : pesan==2 ? F("Perintah ditolak") :
          pesan==5 ? F("Jawaban kedaluwarsa") : menunggu ? F("Menunggu konfirmasi") : F("USB siap"));
    infoKotor=false;
    return;
  }
  if (currentPage==0 && sensorKotor) {
    tft.fillRect(10,139,300,13,BG);
    pena(12,141,1,CYAN);
    if (adaSensor) {
      tft.print(vakum); tft.print(F(" Pa   ")); tft.print(tegangan); tft.print(F(" V   "));
      if (suhu<0) tft.print('-');
      tft.print(abs(suhu)/10); tft.print('.'); tft.print(abs(suhu)%10); tft.print(F(" C   IN ")); tft.print(inputDigital);
    } else tft.print(F("Sensor: menunggu data"));
    sensorKotor=false;
  }
  if (currentPage == 0) gambarDasbor(bagianLayar, sekarang);
  else if (currentPage == 1) gambarPengaturan(bagianLayar);
  else gambarKeluaran(bagianLayar);

  bagianLayar = (bagianLayar + 1) % (currentPage==2 ? 5 : 4);
}

// ---------- Animasi pembuka ----------

void animasiPembuka(unsigned long sekarang) {
  static byte bingkaiLama = 255;
  unsigned long umur = sekarang - mulaiPembuka;

  if (umur >= 3300UL) {
    pembuka = false;
    pindahHalaman(0);
    return;
  }

  byte bingkai = (umur / 60UL) % 8;
  if (bingkai == bingkaiLama) return;
  bingkaiLama = bingkai;

  static const int8_t titikX[] PROGMEM = {0, 11, 16, 11, 0, -11, -16, -11};
  static const int8_t titikY[] PROGMEM = {-16, -11, 0, 11, 16, 11, 0, -11};

  for (byte i = 0; i < 8; ++i) {
    int dx = (int8_t)pgm_read_byte(titikX + i);
    int dy = (int8_t)pgm_read_byte(titikY + i);
    byte jarak = (bingkai + 8 - i) % 8;
    uint16_t warna = jarak == 0 ? WHITE : jarak < 4 ? CYAN : 0;
    tft.fillCircle(160 + dx, 174 + dy, 3, warna);
  }
}

// ---------- Fungsi utama Arduino ----------

void setup() {
  Serial.begin(115200);

  uint16_t id = tft.readID();
  if (id == 0xD3D3) id = 0x9341;
  tft.begin(id);
  tft.setRotation(CalibratedTouch::ROTATION);
  tft.setTextWrap(false);
  tft.fillScreen(0);

  for (byte i = 0; i < 4; ++i) {
    tft.fillRect(138 + 24 * (i % 2), 32 + 24 * (i / 2), 20, 20, BLUE);
  }
  label(76, 91, 2, WHITE, F("SELAMAT DATANG"));
  label(52, 117, 2, CYAN, F("KONTROL AKSELERASI"));

  mulaiPembuka = waktuPaket = millis();
  animasiPembuka(mulaiPembuka);
}

void loop() {
  unsigned long now=millis();
  usb.pump();
  terima(now);
  if (adaSensor && now-rxSensor>1200) { adaSensor=false; sensorKotor=true; }
  if (adaAktuator && now-rxAktuator>1200) { adaAktuator=false; tungguStatus=false; infoKotor=true; }
  if (adaPi && now-rxPi>3000) { adaPi=false; infoKotor=true; }
  if (menunggu && now-waktuCmd>1800) { menunggu=0; aksiKirim=nullptr; pesan=5; infoKotor=true; }
  if (!pembuka) bacaSentuhan(now);
  kirimPerintah();
  if (now-waktuPaket>=100 && usb.idle()) {
    waktuPaket=now;
    usb.send(PSTR("{\"node\":\"hmi\",\"type\":\"telemetry\",\"page\":%u,\"valid\":%d,"
                  "\"rpm\":%d,\"target\":%d,\"run\":%d,\"led\":%u,\"fan\":%d,\"buzzer\":%d,\"relay\":%d}"),
             unsigned(currentPage),adaAktuator,rpm,target,modeSistem==AKTIF,
             unsigned(bits&MASK_LED),!!(bits&MASK_KIPAS),!!(bits&MASK_ALARM),!!(bits&MASK_RELAI));
  }
  if (pembuka) animasiPembuka(now);
  else perbaruiLayar(now);
}
