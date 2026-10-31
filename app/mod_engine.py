"""
mod_engine.py — Root-based memory R/W engine for Free Fire
Uses /proc/<pid>/mem via su for direct process memory patching.
"""

import os
import re
import struct
import subprocess
import ctypes
from typing import Optional


# ─────────────────────────────────────────────────────────────
#  Free Fire memory offsets (arm64, OB47 patch)
#  Update these after each game update using GameGuardian or IDA
# ─────────────────────────────────────────────────────────────
OFFSETS = {
    # Headshot: hit-detection bone target override
    # 0 = auto (game picks), 1 = force head bone
    "headshot_bone":    0x0523_B4C0,   # int32  0→1

    # Recoil: vertical kick multiplier (float, normally 1.0 → 0.0 no recoil)
    "recoil_v":         0x0523_B8F0,   # float

    # ESP / Location: render flag for enemy nametag beyond fog distance
    # normally 0 (hidden) → 1 (always visible)
    "enemy_vis_flag":   0x04FF_1200,   # int32

    # X-Ray: wall-check bypass flag
    # 0 = normal  1 = skip wall occlusion
    "xray_flag":        0x0500_AA20,   # int32

    # Flying: gravity scale (float  9.81 normal → 0.0 float)
    "gravity":          0x0508_CC40,   # float
}

PACKAGE_FF    = "com.dts.freefireth"
PACKAGE_FFMAX = "com.dts.freefiremax"


class ModEngine:
    def __init__(self):
        self.pid: Optional[int] = None
        self.base: Optional[int] = None
        self._active: dict[str, bool] = {}

    # ── root check ───────────────────────────────────────────
    def check_root(self) -> bool:
        try:
            r = subprocess.run(["su", "-c", "id"],
                               capture_output=True, text=True, timeout=3)
            return "uid=0" in r.stdout
        except Exception:
            return False

    # ── PID / base resolution ────────────────────────────────
    def _find_pid(self) -> Optional[int]:
        for pkg in [PACKAGE_FFMAX, PACKAGE_FF]:
            r = subprocess.run(
                ["su", "-c", f"pidof {pkg}"],
                capture_output=True, text=True
            )
            pid_str = r.stdout.strip().split()[0] if r.stdout.strip() else ""
            if pid_str.isdigit():
                return int(pid_str)
        return None

    def _find_base(self, pid: int) -> Optional[int]:
        """Parse /proc/<pid>/maps to get the .so base address."""
        r = subprocess.run(
            ["su", "-c", f"cat /proc/{pid}/maps"],
            capture_output=True, text=True
        )
        for line in r.stdout.splitlines():
            if "libil2cpp.so" in line and "r-xp" in line:
                addr = int(line.split("-")[0], 16)
                return addr
        return None

    def _ensure_target(self) -> bool:
        self.pid  = self._find_pid()
        if not self.pid:
            return False
        self.base = self._find_base(self.pid)
        return self.base is not None

    # ── raw memory write ─────────────────────────────────────
    def _write_mem(self, offset: int, data: bytes):
        if not self._ensure_target():
            return
        addr = self.base + offset
        hex_bytes = data.hex()
        # write via dd reading from /proc self-mem via su
        cmd = (
            f"printf '\\x{chr(10).join(hex_bytes[i:i+2] for i in range(0,len(hex_bytes),2))}' "
            f"| dd of=/proc/{self.pid}/mem bs=1 seek={addr} conv=notrunc 2>/dev/null"
        )
        subprocess.run(["su", "-c", cmd], capture_output=True)

    def _write_int32(self, offset: int, value: int):
        self._write_mem(offset, struct.pack("<i", value))

    def _write_float(self, offset: int, value: float):
        self._write_mem(offset, struct.pack("<f", value))

    # ── feature toggles ──────────────────────────────────────
    def enable(self, key: str):
        self._active[key] = True
        self._apply(key, True)

    def disable(self, key: str):
        self._active[key] = False
        self._apply(key, False)

    def _apply(self, key: str, on: bool):
        if key == "headshot":
            # force bone target to 0 (head) when on, restore to -1 when off
            self._write_int32(OFFSETS["headshot_bone"], 0 if on else -1)
            # also kill vertical recoil
            self._write_float(OFFSETS["recoil_v"], 0.0 if on else 1.0)

        elif key == "location":
            # make all enemies visible on minimap regardless of distance
            self._write_int32(OFFSETS["enemy_vis_flag"], 1 if on else 0)

        elif key == "xray":
            # bypass wall-occlusion check
            self._write_int32(OFFSETS["xray_flag"], 1 if on else 0)

        elif key == "fly":
            # zero gravity → float; restore to 9.81 when off
            self._write_float(OFFSETS["gravity"], 0.0 if on else 9.80665)
