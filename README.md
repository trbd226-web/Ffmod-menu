# ⚡ FF Mod Menu

Root-based mod menu for Free Fire / Free Fire MAX.

## Features
| Feature | Key | How it works |
|---------|-----|-------------|
| 🎯 Body → Headshot | `headshot` | Forces bone-target to head ID + zeroes recoil |
| 📍 Location ESP | `location` | Sets enemy-visibility flag → always render |
| 👁️ X-Ray Vision | `xray` | Bypasses wall-occlusion check in renderer |
| 🕊️ Flying Mode | `fly` | Sets gravity scale to 0.0 |

## Requirements
- Rooted Android device (Magisk / KernelSU)
- Free Fire **or** Free Fire MAX installed
- Android 8.0+ (API 26+)
- Grant `SYSTEM_ALERT_WINDOW` permission when asked

## GitHub Actions APK Build
1. Push this repo to GitHub (any branch)
2. Actions tab → **Build FF Mod APK** runs automatically
3. Download `FFModMenu-debug.apk` from the **Artifacts** section

## Manual build (local)
```bash
cd app
pip install buildozer cython
buildozer android debug
# APK → app/bin/
```

## Updating Offsets
After a game update, offsets in `app/mod_engine.py → OFFSETS` need refreshing.
Use GameGuardian or IDA Pro to find the new addresses in `libil2cpp.so`.

## File Structure
```
ffmod/
├── app/
│   ├── main.py          # Kivy app entry point
│   ├── mod_engine.py    # Root memory R/W engine
│   ├── overlay.py       # Floating Kivy overlay widget
│   └── buildozer.spec   # Android build config
├── jni/
│   └── OverlayService.java  # Android foreground service for overlay
└── .github/
    └── workflows/
        └── build.yml    # GitHub Actions CI — auto-builds APK on push
```
