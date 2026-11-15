
"""
DECY-13 - DIVISI 3
SIMULATOR VISUAL 200 LED CYCLOTRON

150 LED spiral     : 0-149
50 LED extraction  : 150-199

Run:
python 04_simulator_visual_led.py
"""

import math
import time
import tkinter as tk
from tkinter import ttk

from modules.mod_led_ws2812b import (
    CyclotronLED,
    MemoryStrip
)


# ==========================================
# CONFIGURATION
# ==========================================

LED_COUNT = 200
SPIRAL_COUNT = 150
EXTRACTION_COUNT = 50

FRAME_MS = 40

AUTO_ACCEL_SECONDS = 10.0
AUTO_SHOOT_SECONDS = 3.0

BG = "#101827"
OFF = "#263247"

STAGE_NAMES = [
    "Idle",
    "Preparation",
    "Vacuum",
    "Magnetic Field",
    "Injection",
    "Acceleration",
    "Extraction",
    "Complete"
]


class Simulator:

    def __init__(self, root):

        self.root = root

        root.title(
            "DECY-13 | Simulator Visual 200 LED"
        )
        root.geometry("1080x810")
        root.configure(bg=BG)

        self.strip = MemoryStrip(
            count=LED_COUNT
        )

        self.engine = CyclotronLED(
            strip=self.strip,
            brightness=0.35,
            fps=25
        )

        self.stage = tk.IntVar(value=0)
        self.progress = tk.DoubleVar(value=0)

        self.status = tk.StringVar(
            value="READY / IDLE"
        )

        self.auto_mode = False
        self.auto_elapsed = 0.0
        self.last_tick = time.monotonic()

        self.led_items = []

        self.create_interface()
        self.create_diagram()

        root.protocol(
            "WM_DELETE_WINDOW",
            self.close
        )

        self.update_frame()

    # ======================================
    # USER INTERFACE
    # ======================================

    def create_interface(self):

        tk.Label(
            self.root,
            text="DECY-13 | DIVISI 3",
            bg=BG,
            fg="#dcecff",
            font=("Segoe UI", 21, "bold")
        ).pack(pady=(14, 3))

        tk.Label(
            self.root,
            text=(
                "WS2812B | 150 Spiral LED "
                "| 50 Extraction LED"
            ),
            bg=BG,
            fg="#91a8c7",
            font=("Segoe UI", 11)
        ).pack()

        self.canvas = tk.Canvas(
            self.root,
            width=1040,
            height=500,
            bg=BG,
            highlightthickness=0
        )

        self.canvas.pack(pady=4)

        stage_frame = tk.Frame(
            self.root,
            bg=BG
        )
        stage_frame.pack(pady=5)

        names = [
            "0 Idle",
            "1 Prep",
            "2 Vacuum",
            "3 Magnet",
            "4 Injection",
            "5 Acceleration",
            "6 Shoot",
            "7 Complete"
        ]

        for index, name in enumerate(names):

            tk.Radiobutton(
                stage_frame,
                text=name,
                variable=self.stage,
                value=index,
                command=self.change_stage,
                indicatoron=False,
                bg="#25354d",
                fg="white",
                selectcolor="#1974a6",
                activebackground="#1974a6",
                activeforeground="white",
                font=("Segoe UI", 9),
                padx=8,
                pady=8,
                relief="flat"
            ).grid(
                row=0,
                column=index,
                padx=3
            )

        progress_frame = tk.Frame(
            self.root,
            bg=BG
        )

        progress_frame.pack(
            fill="x",
            padx=75,
            pady=(10, 3)
        )

        tk.Label(
            progress_frame,
            text="Progress / Posisi Partikel",
            bg=BG,
            fg="white"
        ).pack(side="left")

        self.progress_label = tk.Label(
            progress_frame,
            text="0%",
            bg=BG,
            fg="#62dafa"
        )

        self.progress_label.pack(side="right")

        self.slider = ttk.Scale(
            self.root,
            from_=0,
            to=100,
            variable=self.progress,
            command=self.change_progress
        )

        self.slider.pack(
            fill="x",
            padx=75
        )

        buttons = tk.Frame(
            self.root,
            bg=BG
        )
        buttons.pack(pady=12)

        controls = [
            (
                "AUTO CYCLOTRON",
                self.start_auto,
                "#126a60"
            ),
            (
                "START / RESUME",
                self.start,
                "#215f83"
            ),
            (
                "PAUSE",
                self.pause,
                "#505b73"
            ),
            (
                "STOP",
                self.stop,
                "#6f4b29"
            ),
            (
                "RESET",
                self.reset,
                "#365173"
            ),
            (
                "E-STOP",
                self.estop,
                "#9e2734"
            )
        ]

        for text, command, color in controls:

            tk.Button(
                buttons,
                text=text,
                command=command,
                bg=color,
                fg="white",
                activebackground=color,
                activeforeground="white",
                relief="flat",
                font=("Segoe UI", 9, "bold"),
                padx=10,
                pady=9
            ).pack(
                side="left",
                padx=4
            )

        tk.Label(
            self.root,
            textvariable=self.status,
            bg=BG,
            fg="#b0d9e8",
            font=("Consolas", 10)
        ).pack(pady=5)

        tk.Label(
            self.root,
            text=(
                "AUTO: Stage 5 -> Stage 6 -> Stage 7"
                " | 10 detik + 3 detik"
            ),
            bg=BG,
            fg="#7797b8",
            font=("Segoe UI", 9)
        ).pack()

    # ======================================
    # DRAW 200 LEDS
    # ======================================

    def create_diagram(self):

        coords = []

        cx = 255
        cy = 255

        # 150 LED spiral, sekitar 3 putaran
        for i in range(SPIRAL_COUNT):

            fraction = i / (
                SPIRAL_COUNT - 1
            )

            angle = (
                6 * math.pi * fraction
            )

            radius = (
                22 + 172 * fraction
            )

            x = (
                cx + radius * math.cos(angle)
            )

            y = (
                cy + radius * math.sin(angle)
            )

            coords.append((x, y))

        last_x, last_y = coords[-1]

        # 50 LED extraction.
        # Jalur dibuat lebih rapat agar muat.
        start_x = last_x + 13
        end_x = 1015

        for j in range(EXTRACTION_COUNT):

            fraction = j / (
                EXTRACTION_COUNT - 1
            )

            x = (
                start_x
                + (end_x - start_x) * fraction
            )

            y = last_y

            coords.append((x, y))

        self.canvas.create_text(
            255,
            23,
            text=(
                "SPIRAL / ACCELERATION "
                "(LED 0-149)"
            ),
            fill="#8da6cb",
            font=("Segoe UI", 11, "bold")
        )

        self.canvas.create_text(
            760,
            198,
            text=(
                "EXTRACTION / SHOOT "
                "(LED 150-199)"
            ),
            fill="#e3ad63",
            font=("Segoe UI", 11, "bold")
        )

        # Spiral connection
        for i in range(
            SPIRAL_COUNT - 1
        ):

            self.canvas.create_line(
                *coords[i],
                *coords[i + 1],
                fill="#33445c",
                width=1
            )

        # Spiral to extraction
        self.canvas.create_line(
            *coords[149],
            *coords[150],
            fill="#38516c",
            width=2
        )

        # Extraction connection
        for i in range(150, 199):

            self.canvas.create_line(
                *coords[i],
                *coords[i + 1],
                fill="#654d35",
                width=2
            )

        # 200 LED points
        for i, (x, y) in enumerate(coords):

            radius = (
                4.3 if i < SPIRAL_COUNT
                else 4.0
            )

            led = self.canvas.create_oval(
                x - radius,
                y - radius,
                x + radius,
                y + radius,
                fill=OFF,
                outline="#536880",
                width=0.7
            )

            self.led_items.append(led)

            if i in (
                0, 25, 50, 75, 100,
                125, 149, 150,
                175, 199
            ):

                self.canvas.create_text(
                    x,
                    y + 14,
                    text=str(i),
                    fill="#8292a9",
                    font=("Consolas", 8)
                )

        self.canvas.create_text(
            260,
            481,
            text=(
                "200 LED virtual - posisi "
                "menyesuaikan rancangan maket"
            ),
            fill="#627e99",
            font=("Segoe UI", 9)
        )

    # ======================================
    # MANUAL STAGE
    # ======================================

    def change_stage(self):

        if self.engine.estop:
            return

        self.auto_mode = False

        self.engine.set_state(
            stage=self.stage.get(),
            progress=self.progress.get()
        )

        self.engine.start()
        self.engine.render(force=True)

    # ======================================
    # SLIDER
    # ======================================

    def change_progress(self, value):

        progress = float(value)

        self.progress_label.config(
            text=f"{progress:.0f}%"
        )

        # Ketika user menggeser manual,
        # mode AUTO dibatalkan.
        self.auto_mode = False

        self.engine.set_state(
            progress=progress
        )

    # ======================================
    # AUTOMATIC CYCLotron
    # ======================================

    def start_auto(self):

        if self.engine.estop:
            return

        self.engine.reset()

        self.auto_mode = True
        self.auto_elapsed = 0.0

        self.stage.set(5)
        self.progress.set(0)

        self.engine.set_state(
            stage=5,
            progress=0
        )

        self.engine.start()

        self.last_tick = time.monotonic()

    def update_auto(self, delta):

        if not self.auto_mode:
            return

        if (
            self.engine.paused
            or not self.engine.running
            or self.engine.estop
        ):
            return

        self.auto_elapsed += delta

        elapsed = self.auto_elapsed

        # Stage 5 - Acceleration
        if elapsed < AUTO_ACCEL_SECONDS:

            progress = (
                elapsed
                / AUTO_ACCEL_SECONDS
                * 100
            )

            self.stage.set(5)
            self.progress.set(progress)

            self.engine.set_state(
                stage=5,
                progress=progress
            )

        # Stage 6 - Extraction
        elif elapsed < (
            AUTO_ACCEL_SECONDS
            + AUTO_SHOOT_SECONDS
        ):

            shoot_elapsed = (
                elapsed - AUTO_ACCEL_SECONDS
            )

            progress = (
                shoot_elapsed
                / AUTO_SHOOT_SECONDS
                * 100
            )

            self.stage.set(6)
            self.progress.set(progress)

            self.engine.set_state(
                stage=6,
                progress=progress
            )

        # Stage 7 - Complete
        else:

            self.stage.set(7)
            self.progress.set(100)

            self.engine.set_state(
                stage=7,
                progress=100
            )

            self.auto_mode = False

    # ======================================
    # CONTROL BUTTONS
    # ======================================

    def start(self):

        self.engine.start()

    def pause(self):

        self.engine.pause()

    def stop(self):

        self.auto_mode = False
        self.engine.stop()

    def reset(self):

        self.auto_mode = False
        self.auto_elapsed = 0.0

        self.engine.reset()

        self.stage.set(0)
        self.progress.set(0)

    def estop(self):

        self.auto_mode = False
        self.engine.emergency_stop()

    # ======================================
    # ANIMATION LOOP
    # ======================================

    def update_frame(self):

        now = time.monotonic()

        delta = min(
            0.25,
            max(0.0, now - self.last_tick)
        )

        self.last_tick = now

        self.update_auto(delta)

        self.engine.render()

        # Render 200 LED
        for i in range(LED_COUNT):

            rgb = self.strip.pixels[i]

            amplified = tuple(
                min(255, int(v * 2.8))
                for v in rgb
            )

            if any(rgb):

                color = (
                    "#%02x%02x%02x"
                    % amplified
                )

            else:
                color = OFF

            self.canvas.itemconfig(
                self.led_items[i],
                fill=color
            )

        state = self.engine.get_status()

        self.progress_label.config(
            text=(
                f"{self.progress.get():.0f}%"
            )
        )

        if state["estop"]:
            mode = "EMERGENCY STOP"

        elif not state["running"]:
            mode = "STOPPED"

        elif state["paused"]:
            mode = "PAUSED"

        elif self.auto_mode:
            mode = "AUTO RUNNING"

        else:
            mode = "MANUAL RUNNING"

        self.status.set(
            f"{mode}"
            f" | {LED_COUNT} LED"
            f" | Stage {state['stage']}: "
            f"{state['stage_name']}"
            f" | Progress {state['progress']:.0f}%"
            f" | Frames {self.strip.frames}"
        )

        self.root.after(
            FRAME_MS,
            self.update_frame
        )

    # ======================================
    # CLOSE
    # ======================================

    def close(self):

        self.auto_mode = False
        self.engine.close()
        self.root.destroy()


# ==========================================
# MAIN
# ==========================================

if __name__ == "__main__":

    root = tk.Tk()

    Simulator(root)

    root.mainloop()
