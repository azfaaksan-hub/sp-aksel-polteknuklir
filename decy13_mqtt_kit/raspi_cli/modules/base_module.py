#!/usr/bin/env python3
"""
KONTRAK INTERFACE DASAR MODUL HARDWARE (DIVISI 1 — CORE BACKEND)
================================================================
PERingatan: File ini adalah kontrak standar antar-divisi.
Anggota Divisi 2, 3, 4, 5, 6 DILARANG mengubah file ini tanpa persetujuan
Lead Core Raspi (Divisi 1).

Setiap modul hardware wajib mewarisi `HardwareModule` dan mengimplementasikan:
  1. setup()               -> Inisialisasi pin GPIO / SPI / DMA / Thread
  2. update(state, dt, now)-> Dipanggil berkala oleh Core Daemon untuk sinkronisasi
  3. cleanup()             -> Mematikan aktuator dengan aman saat program berhenti
"""

from typing import Dict, Any


class HardwareModule:
    """Kelas dasar (Base Contract) untuk seluruh subsistem hardware RPi 3B+."""

    def __init__(self, config: Dict[str, Any]):
        self.cfg = config
        self.enabled = False
        self.name = self.__class__.__name__

    def setup(self) -> bool:
        """
        Inisialisasi perangkat keras.
        Return True jika hardware nyata terdeteksi, False jika berjalan dalam
        mode simulasi (misal saat diuji di laptop Windows/Linux tanpa RPi).
        """
        return False

    def update(self, state: Dict[str, Any], dt: float, now: float) -> None:
        """
        Sinkronisasi kondisi perangkat keras dengan dictionary `state` utama.
        Catatan:
        - Modul boleh membaca key apapun dari `state`.
        - Modul hanya boleh mengubah key `state` yang menjadi tanggung jawabnya
          (contoh: `mod_vacuum_safety` boleh memicu `emergency`, `mod_led_ws2812b`
          mengupdate `activeLedIdx` dan `shootLedIdx`).
        """
        pass

    def cleanup(self) -> None:
        """Bersihkan resource (matikan relay/LED/thread) saat daemon dihentikan."""
        pass
