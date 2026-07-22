# Полоски-визуализация голоса по краю экрана (отдельный процесс)

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

CHROMA = "#010203"

N_ARCS     = 16
SPAN_FRAC  = 0.88
MIN_DEPTH  = 14
DEPTH_STEP = 18

_DEPTHS = [MIN_DEPTH + DEPTH_STEP * i for i in range(N_ARCS)]

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


# окно с волной, реагирующей на громкость голоса
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
        self.cur = 0.0
        self.vis = 0.0
        self.want_vis = 0.0
        self.phase = 0.0

        self._arcs = []
        self._build_arcs()
        self.root.withdraw()

        threading.Thread(target=self._read_stdin, daemon=True).start()
        self._tick()


    def _make_click_through(self):
        """Let all mouse input pass to whatever is underneath."""
        GWL_EXSTYLE       = -20
        WS_EX_LAYERED     = 0x00080000
        WS_EX_TRANSPARENT = 0x00000020
        WS_EX_TOOLWINDOW  = 0x00000080
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

        hy = h * SPAN_FRAC / 2
        hx = w * SPAN_FRAC / 2

        for i, depth in enumerate(_DEPTHS):
            cc = _CORE[i]
            mc = _dim(cc, 0.50)
            gc = _dim(cc, 0.14)

            ph = i * 0.36

            threshold = 0.03 + 0.40 * (i / (N_ARCS - 1))


            lbb = (-depth, cy - hy, depth, cy + hy)
            lg = self.canvas.create_arc(*lbb, start=-90, extent=180,
                                        style=tk.ARC, outline=gc, width=18, state="hidden")
            lm = self.canvas.create_arc(*lbb, start=-90, extent=180,
                                        style=tk.ARC, outline=mc, width=7,  state="hidden")
            lc = self.canvas.create_arc(*lbb, start=-90, extent=180,
                                        style=tk.ARC, outline=cc, width=2,  state="hidden")

            rbb = (w - depth, cy - hy, w + depth, cy + hy)
            rg = self.canvas.create_arc(*rbb, start=90, extent=180,
                                        style=tk.ARC, outline=gc, width=18, state="hidden")
            rm = self.canvas.create_arc(*rbb, start=90, extent=180,
                                        style=tk.ARC, outline=mc, width=7,  state="hidden")
            rc = self.canvas.create_arc(*rbb, start=90, extent=180,
                                        style=tk.ARC, outline=cc, width=2,  state="hidden")

            tbb = (cx - hx, -depth, cx + hx, depth)
            tg = self.canvas.create_arc(*tbb, start=0, extent=180,
                                        style=tk.ARC, outline=gc, width=18, state="hidden")
            tm = self.canvas.create_arc(*tbb, start=0, extent=180,
                                        style=tk.ARC, outline=mc, width=7,  state="hidden")
            tc = self.canvas.create_arc(*tbb, start=0, extent=180,
                                        style=tk.ARC, outline=cc, width=2,  state="hidden")

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


    # читаем команды от Джарвиса из stdin
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

        self.root.after(16, self._tick)

    def _draw(self):
        level = self.cur * self.vis
        for arc in self._arcs:
            raw = max(0.0, level - arc["threshold"])
            wobble = 0.55 + 0.45 * math.sin(self.phase + arc["phase"])
            eff = min(raw * wobble * 2.2, 1.0)

            visible = eff > 0.008
            state = "normal" if visible else "hidden"

            hw = max(4,  min(22, int(20 * eff)))
            mw = max(2,  min(10, int( 8 * eff)))
            cw = max(1,  min(4,  int( 3 * eff)))

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
