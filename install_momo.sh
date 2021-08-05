#!/usr/bin/env sh

wget -O maimemo.apk https://cdn.maimemo.com/apk/maimemo_v3.8.56_1617086292.apk
adb install -r -g maimemo.apk
adb shell pm list packages com.maimemo.android.momo