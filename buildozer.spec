
[app]
title = NYB-UAP
package.name = nybuap
package.domain = org.haikalgod
source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,json,onnx,tflite
version = 0.1.0
requirements = python3,kivy,opencv,numpy
orientation = landscape
fullscreen = 1

android.permissions = CAMERA,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION,RECORD_AUDIO
android.api = 35
android.minapi = 24
android.archs = arm64-v8a
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 0
