"""Screen-edge voice visualiser for J.A.R.V.I.S. — arc style.

Concentric glowing arcs around all 4 screen edges (left, right, top, bottom),
cyan→violet gradient. Innermost arcs light up first; outer arcs cascade in as
the voice gets louder — giving a "wave radiating outward" effect.

stdin protocol (JSON, one object per line):
    {"amp": 0.0-1.0}    current voice loudness (0 = silence, 1 = peak)
    {"show": true}      fade the overlay in
    {"show": false}     fade the overlay out
    {"quit": true}      exit cleanly
"""
import ctypes
import json
import math
import sys
import threading
import tkinter as tk

# This colour is made transparent by Windows, so arcs float on the desktop.
CHROMA = "#010203"

N_ARCS     = 16      # concentric arcs per edge
SPAN_FRAC  = 0.88    # fraction of the perpendicular screen dimension each arc spans
MIN_DEPTH  = 14      # px — innermost arc protrusion from the edge
DEPTH_STEP = 18      # px — spacing between consecutive arcs

# Depths of arcs 0..N_ARCS-1 (0 = innermost, closest to screen centre)
_DEPTHS = [MIN_DEPTH + DEPTH_STEP * i for i in range(N_ARCS)]

# Core colours, innermost (0) → outermost (15): bright cyan → deep violet
_CORE = [
    "#70e0ff", "#56d0ff", "#4ac0ff", "#40b0ff",
    "#40a0ff", "#4a8eff", "#5a7eff", "#6a72ff",
    "#7a68ff", "#8a64ff", "#9b6bff", "#9458ee",
    "#8448dc", "#7038cc", "#5e28bc", "#4e18ac",
]


def _dim(c: str, f: float) -> str:
    """Return colour `c` multiplied by factor `f` (0..1)."""
    r, g, b = int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16)
    return f"#{int(r*f):02x}{int(g*f):02x}{int(b*f):02x}"


class Overlay:
    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.0)
        self.root.attributes("-transparentcolor", CHROMA)

        self.sw = self.root.winfo_screenwidth()
        self.sh = self.root.winfo_screenheight()
        self.root.geometry(f"{self.sw}x{self.sh}+0+0")

        self.canvas = tk.Canvas(self.root, width=self.sw, height=self.sh,
                                bg=CHROMA, highlightthickness=0, bd=0)
        self.canvas.pack()
        self._make_click_through()

        self.amp = 0.0
        self.cur = 0.0       # eased amplitude
        self.vis = 0.0       # overlay fade (0..1)
        self.want_vis = 0.0
        self.phase = 0.0

        self._arcs = []      # built once, updated every frame
        self._build_arcs()
        self.root.withdraw()

        threading.Thread(target=self._read_stdin, daemon=True).start()
        self._tick()

    # ── setup ─────────────────────────────────────────────────────────────

    def _make_click_through(self):
        """Let all mouse input pass to whatever is underneath."""
        GWL_EXSTYLE       = -20
        WS_EX_LAYERED     = 0x00080000
        WS_EX_TRANSPARENT = 0x00000020
        WS_EX_TOOLWINDOW  = 0x00000080   # hide from taskbar / Alt+Tab
        WS_EX_NOACTIVATE  = 0x08000000
        self.root.update_idletasks()
        hwnd = (ctypes.windll.user32.GetParent(self.root.winfo_id())
                or self.root.winfo_id())
        style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        ctypes.windll.user32.SetWindowLongW(
            hwnd, GWL_EXSTYLE,
            style | WS_EX_LAYERED | WS_EX_TRANSPARENT
                  | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE)

    def _build_arcs(self):
        """Create all canvas arc items once.  The draw loop only updates their
        line-width and visibility — no item recreation needed at 60 fps."""
        w, h = self.sw, self.sh
        cx, cy = w / 2, h / 2

        # Half-extents: how far each arc stretches along the edge it decorates.
        # Left/right arcs span vertically; top/bottom arcs span horizontally.
        hy = h * SPAN_FRAC / 2   # vertical half-span (for left / right edges)
        hx = w * SPAN_FRAC / 2   # horizontal half-span (for top / bottom edges)

        for i, depth in enumerate(_DEPTHS):
            cc = _CORE[i]
            mc = _dim(cc, 0.50)   # mid glow
            gc = _dim(cc, 0.14)   # outer haze

            # Phase offset so ripple cascades outward from the screen edge
            ph = i * 0.36

            # Threshold: outer arcs only appear at higher amplitude
            threshold = 0.03 + 0.40 * (i / (N_ARCS - 1))

            # ── Angle conventions (Tkinter canvas: CCW from east=0°, y-axis down) ──
            # • start=-90, extent=180  → right half of ellipse  (left edge arc)
            # • start= 90, extent=180  → left  half of ellipse  (right edge arc)
            # • start=  0, extent=180  → lower half on screen   (top  edge arc)
            # • start=180, extent=180  → upper half on screen   (bottom edge arc)

            # ── LEFT edge ─────────────────────────────────────────────────────────
            lbb = (-depth, cy - hy, depth, cy + hy)
            lg = self.canvas.create_arc(*lbb, start=-90, extent=180,
                                        style=tk.ARC, outline=gc, width=18, state="hidden")
            lm = self.canvas.create_arc(*lbb, start=-90, extent=180,
                                        style=tk.ARC, outline=mc, width=7,  state="hidden")
            lc = self.canvas.create_arc(*lbb, start=-90, extent=180,
                                        style=tk.ARC, outline=cc, width=2,  state="hidden")

            # ── RIGHT edge ────────────────────────────────────────────────────────
            rbb = (w - depth, cy - hy, w + depth, cy + hy)
            rg = self.canvas.create_arc(*rbb, start=90, extent=180,
                                        style=tk.ARC, outline=gc, width=18, state="hidden")
            rm = self.canvas.create_arc(*rbb, start=90, extent=180,
                                        style=tk.ARC, outline=mc, width=7,  state="hidden")
            rc = self.canvas.create_arc(*rbb, start=90, extent=180,
                                        style=tk.ARC, outline=cc, width=2,  state="hidden")

            # ── TOP edge ──────────────────────────────────────────────────────────
            tbb = (cx - hx, -depth, cx + hx, depth)
            tg = self.canvas.create_arc(*tbb, start=0, extent=180,
                                        style=tk.ARC, outline=gc, width=18, state="hidden")
            tm = self.canvas.create_arc(*tbb, start=0, extent=180,
                                        style=tk.ARC, outline=mc, width=7,  state="hidden")
            tc = self.canvas.create_arc(*tbb, start=0, extent=180,
                                        style=tk.ARC, outline=cc, width=2,  state="hidden")

            # ── BOTTOM edge ───────────────────────────────────────────────────────
            bbb = (cx - hx, h - depth, cx + hx, h + depth)
            bg = self.canvas.create_arc(*bbb, start=180, extent=180,
                                        style=tk.ARC, outline=gc, width=18, state="hidden")
            bm = self.canvas.create_arc(*bbb, start=180, extent=180,
                                        style=tk.ARC, outline=mc, width=7,  state="hidden")
            bc = self.canvas.create_arc(*bbb, start=180, extent=180,
                                        style=tk.ARC, outline=cc, width=2,  state="hidden")

            self._arcs.append({
                "phase":     ph,
                "threshold": threshold,
                "haze":  (lg, rg, tg, bg),
                "mid":   (lm, rm, tm, bm),
                "core":  (lc, rc, tc, bc),
            })

    # ── runtime ───────────────────────────────────────────────────────────

    def _read_stdin(self):
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except ValueError:
                continue
            if msg.get("quit"):
                try:
                    self.root.after(0, self.root.destroy)
                except Exception:
                    pass
                return
            if "amp" in msg:
                self.amp = max(0.0, min(1.0, float(msg["amp"])))
            if "show" in msg:
                self.want_vis = 1.0 if msg["show"] else 0.0

        # EOF means the Jarvis parent exited, including a native crash where its
        # Python finally blocks cannot run. Do not leave an invisible pythonw.exe
        # overlay process behind for every failed launch.
        try:
            self.root.after(0, self.root.destroy)
        except Exception:
            pass

    def _tick(self):
        self.cur   += (self.amp      - self.cur)   * 0.28
        self.vis   += (self.want_vis - self.vis)   * 0.12
        self.phase += 0.07

        if self.vis < 0.01 and self.want_vis == 0.0:
            self.root.withdraw()
        else:
            self.root.deiconify()
            self.root.attributes("-topmost", True)
            self.root.attributes("-alpha", min(0.94 * self.vis, 0.94))
            self._draw()

        self.root.after(16, self._tick)    # ~60 fps

    def _draw(self):
        level = self.cur * self.vis
        for arc in self._arcs:
            # Cascade: subtract per-arc threshold so outer arcs need more signal.
            raw = max(0.0, level - arc["threshold"])
            # Sine wobble gives the column a breathing / ripple feel.
            wobble = 0.55 + 0.45 * math.sin(self.phase + arc["phase"])
            eff = min(raw * wobble * 2.2, 1.0)   # 2.2 = boost so arcs saturate crisply

            visible = eff > 0.008
            state = "normal" if visible else "hidden"

            # Line widths scale with effective amplitude.
            hw = max(4,  min(22, int(20 * eff)))   # haze
            mw = max(2,  min(10, int( 8 * eff)))   # mid glow
            cw = max(1,  min(4,  int( 3 * eff)))   # bright core

            for it in arc["haze"]:
                self.canvas.itemconfigure(it, state=state, width=hw)
            for it in arc["mid"]:
                self.canvas.itemconfigure(it, state=state, width=mw)
            for it in arc["core"]:
                self.canvas.itemconfigure(it, state=state, width=cw)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    Overlay().run()
