[app]
title = FF Mod Menu
package.name = ffmod
package.domain = com.ffmod

source.dir = .
source.include_exts = py,png,kv,atlas

version = 1.0

requirements = python3,kivy,pyjnius,android

orientation = portrait
fullscreen = 0

android.permissions =
    SYSTEM_ALERT_WINDOW,
    FOREGROUND_SERVICE,
    READ_EXTERNAL_STORAGE,
    WRITE_EXTERNAL_STORAGE,
    RECEIVE_BOOT_COMPLETED

android.api = 33
android.minapi = 26
android.ndk = 25b
android.sdk = 33
android.ndk_api = 26
android.arch = arm64-v8a

android.accept_sdk_license = True
android.logcat_filters = *:S python:D

android.add_java_dir = ../jni
android.add_jars =

[buildozer]
log_level = 2
warn_on_root = 0
