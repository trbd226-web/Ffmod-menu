"""
Free Fire Mod Menu - Main App
Root-based memory injection for Free Fire / Free Fire MAX
"""

import os
import subprocess
import threading
import time
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.switch import Switch
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle
from kivy.clock import Clock
from kivy.utils import platform

from mod_engine import ModEngine
from overlay import FloatingMenu

PACKAGE_FF   = "com.dts.freefireth"
PACKAGE_FFMAX = "com.dts.freefiremax"


class ModMenuApp(App):
    def build(self):
        Window.clearcolor = (0.05, 0.05, 0.08, 1)
        self.engine = ModEngine()
        self.ff_pkg  = self._detect_ff()
        return MainLayout(self.engine, self.ff_pkg)

    def _detect_ff(self):
        for pkg in [PACKAGE_FFMAX, PACKAGE_FF]:
            r = subprocess.run(
                ["su", "-c", f"pm path {pkg}"],
                capture_output=True, text=True
            )
            if "package:" in r.stdout:
                return pkg
        return None


class MainLayout(FloatLayout):
    def __init__(self, engine, ff_pkg, **kw):
        super().__init__(**kw)
        self.engine = engine
        self.ff_pkg = ff_pkg
        self._build_ui()

    def _build_ui(self):
        root = BoxLayout(orientation='vertical', padding=20, spacing=12,
                         size_hint=(1, 1))

        # ── header ──────────────────────────────────────────────
        hdr = Label(
            text="[b][color=ff4444]⚡ FF MOD MENU[/color][/b]",
            markup=True, font_size='22sp', size_hint_y=None, height=50
        )
        root.add_widget(hdr)

        # ── status ───────────────────────────────────────────────
        root_ok = self.engine.check_root()
        status_color = "44ff44" if root_ok else "ff4444"
        status_text  = "ROOT: OK" if root_ok else "ROOT: NOT FOUND"
        self.status_lbl = Label(
            text=f"[color={status_color}]{status_text}[/color]",
            markup=True, font_size='14sp', size_hint_y=None, height=30
        )
        root.add_widget(self.status_lbl)

        # FF detection
        pkg_txt = self.ff_pkg if self.ff_pkg else "NOT INSTALLED"
        self.pkg_lbl = Label(
            text=f"[color=aaaaaa]Game: {pkg_txt}[/color]",
            markup=True, font_size='12sp', size_hint_y=None, height=25
        )
        root.add_widget(self.pkg_lbl)

        # ── scrollable mod list ──────────────────────────────────
        sv = ScrollView(size_hint=(1, 1))
        mod_box = BoxLayout(orientation='vertical', spacing=10,
                            size_hint_y=None, padding=[0, 10, 0, 10])
        mod_box.bind(minimum_height=mod_box.setter('height'))

        self.mods = [
            ("🎯 Body Headshot",  "headshot",  "Auto-converts body hits → headshot damage"),
            ("📍 Location ESP",   "location",   "Draws enemy position markers"),
            ("👁️ X-Ray Vision",   "xray",       "See enemies through walls"),
            ("🕊️ Flying Mode",    "fly",        "Disable gravity — free movement"),
        ]

        self.switches = {}
        for name, key, desc in self.mods:
            row = self._make_mod_row(name, key, desc)
            mod_box.add_widget(row)
            mod_box.add_widget(BoxLayout(size_hint_y=None, height=1))  # divider

        sv.add_widget(mod_box)
        root.add_widget(sv)

        # ── launch button ─────────────────────────────────────────
        self.launch_btn = Button(
            text="🚀  LAUNCH FREE FIRE" if self.ff_pkg else "❌  GAME NOT FOUND",
            size_hint_y=None, height=55,
            background_color=(0.2, 0.7, 0.2, 1) if self.ff_pkg else (0.4, 0.4, 0.4, 1),
            disabled=self.ff_pkg is None,
            font_size='16sp'
        )
        self.launch_btn.bind(on_press=self._launch_game)
        root.add_widget(self.launch_btn)

        self.add_widget(root)

    def _make_mod_row(self, name, key, desc):
        row = BoxLayout(orientation='horizontal', size_hint_y=None, height=70,
                        padding=[10, 5, 10, 5], spacing=10)
        with row.canvas.before:
            Color(0.1, 0.1, 0.15, 1)
            row._rect = RoundedRectangle(pos=row.pos, size=row.size, radius=[8])
        row.bind(pos=lambda w, v: setattr(w._rect, 'pos', v),
                 size=lambda w, v: setattr(w._rect, 'size', v))

        txt_box = BoxLayout(orientation='vertical', size_hint_x=0.75)
        txt_box.add_widget(Label(text=f"[b]{name}[/b]", markup=True,
                                 font_size='14sp', halign='left',
                                 text_size=(300, None)))
        txt_box.add_widget(Label(text=f"[color=888888]{desc}[/color]",
                                 markup=True, font_size='11sp', halign='left',
                                 text_size=(300, None)))
        row.add_widget(txt_box)

        sw = Switch(active=False, size_hint_x=0.25)
        sw.bind(active=lambda inst, val, k=key: self._toggle_mod(k, val))
        self.switches[key] = sw
        row.add_widget(sw)
        return row

    def _toggle_mod(self, key, state):
        if state:
            self.engine.enable(key)
        else:
            self.engine.disable(key)

    def _launch_game(self, *a):
        if not self.ff_pkg:
            return
        # start floating overlay service
        from android.permissions import request_permissions, Permission
        try:
            request_permissions([
                Permission.SYSTEM_ALERT_WINDOW,
                Permission.FOREGROUND_SERVICE,
            ])
        except Exception:
            pass

        # start overlay in background thread
        t = threading.Thread(target=self._start_overlay, daemon=True)
        t.start()
        time.sleep(0.5)

        # launch the game
        subprocess.Popen([
            "su", "-c",
            f"monkey -p {self.ff_pkg} -c android.intent.category.LAUNCHER 1"
        ])

    def _start_overlay(self):
        from jnius import autoclass
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        Intent = autoclass('android.content.Intent')
        ctx = PythonActivity.mActivity
        svc_cls = autoclass('com.ffmod.OverlayService')
        intent = Intent(ctx, svc_cls)
        ctx.startForegroundService(intent)


if __name__ == "__main__":
    ModMenuApp().run()
