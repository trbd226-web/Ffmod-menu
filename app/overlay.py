"""
overlay.py — Floating draggable mod menu that sits on top of the game.
Uses Android WindowManager via pyjnius to draw a SYSTEM_ALERT_WINDOW overlay.
"""

import threading
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.switch import Switch
from kivy.uix.boxlayout import BoxLayout
from kivy.graphics import Color, RoundedRectangle
from kivy.core.window import Window


MOD_KEYS = [
    ("🎯 Headshot",  "headshot"),
    ("📍 Location",  "location"),
    ("👁️ X-Ray",    "xray"),
    ("🕊️ Fly",      "fly"),
]


class FloatingMenu(FloatLayout):
    """
    Kivy-side floating widget.  When running on Android the real overlay
    is handled by OverlayService.java (see jni/ folder) which hosts a
    NativeView; this Python class mirrors the toggle state.
    """

    def __init__(self, engine, **kw):
        super().__init__(**kw)
        self.engine = engine
        self._drag_x = 20
        self._drag_y = 200
        self._collapsed = False
        self._build()

    def _build(self):
        self.panel = BoxLayout(
            orientation='vertical',
            size_hint=(None, None),
            size=(220, 40 + len(MOD_KEYS) * 55),
            pos=(self._drag_x, self._drag_y),
            padding=8, spacing=6
        )
        with self.panel.canvas.before:
            Color(0.08, 0.08, 0.12, 0.92)
            self._bg = RoundedRectangle(pos=self.panel.pos,
                                        size=self.panel.size, radius=[12])
        self.panel.bind(
            pos=lambda w, v: setattr(self._bg, 'pos', v),
            size=lambda w, v: setattr(self._bg, 'size', v),
        )

        # title bar (drag handle)
        title = Label(
            text="[b][color=ff4444]⚡ FF MOD[/color][/b]",
            markup=True, size_hint_y=None, height=35, font_size='13sp'
        )
        title.bind(on_touch_move=self._on_drag)
        self.panel.add_widget(title)

        self.switches = {}
        for name, key in MOD_KEYS:
            row = BoxLayout(orientation='horizontal',
                            size_hint_y=None, height=48, spacing=8)
            row.add_widget(Label(text=name, font_size='12sp',
                                 size_hint_x=0.65, halign='left'))
            sw = Switch(active=False, size_hint_x=0.35)
            sw.bind(active=lambda inst, val, k=key: self._toggle(k, val))
            self.switches[key] = sw
            row.add_widget(sw)
            self.panel.add_widget(row)

        self.add_widget(self.panel)

    def _toggle(self, key, state):
        if state:
            self.engine.enable(key)
        else:
            self.engine.disable(key)

    def _on_drag(self, widget, touch):
        if widget.collide_point(*touch.pos):
            self.panel.x += touch.dx
            self.panel.y += touch.dy
