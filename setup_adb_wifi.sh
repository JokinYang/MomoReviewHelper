#!/usr/bin/env bash

port=5555
device_ip=$(adb shell ifconfig -a |grep inet|grep -v 127.0.0.1|grep -v inet6|awk '{print $2}'|tr -d "addr:")
adb tcpip 5555
adb connect "${device_ip}:${port}"
