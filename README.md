# bm7-battery-monitor
Read data from Ancel BM300 Pro BLE battery monitors without the invasive app.

Based on https://github.com/JeffWDH/bm6-battery-monitor

# Python application
```
usage: bm7-battery-monitor.py [-h] [--format {ascii,json}] (--address <address> | --scan)

bm7-battery-monitor.py --scan
Address           RSSI
E0:4E:7A:xx:xx:xx -83

bm7-battery-monitor.py --address E0:4E:7A:xx:xx:xx
Voltage: 11.93v
Temperature: 24C
SoC: 76%

bm7-battery-monitor.py --address E0:4E:7A:xx:xx:xx --format=json
{"voltage": 11.93, "temperature": 24, "soc": 76}
```
# ESPHome
Under the ESPHome directory you can find a configuration that will allow you to read your Ancel BM300 Pro battery monitor using an ESP32 and ESPHome. This was tested on ESPHome 2025.8.4 and may break at any time...

I have added the dynamic polling interval - every minute if voltage is above 13.0V (the engine started), otherwise every 30 min.

Note the OTA update is impossible on 4MB ESP devices if the framework type is `arduino` because the binary size is too big.
I have used the type `esp-idf`. But the build in Home Assistant ESPHome addod failed with the linker error: undefined reference to `mbedtls_aes_init` because of the bug in `platform-espressif32`.
I was able to build the binary for the type `esp-idf` using manually installed ESPHome and the following [workaround](https://github.com/platformio/platform-espressif32/issues/957).
Just update the line
```
idf_component_register(SRCS ${app_sources})
```
with 
```
idf_component_register(SRCS ${app_sources} INCLUDE_DIRS "." REQUIRES mbedtls)
```
in the file `.esphome\build\bm7\src\CMakeLists.txt` and run `esphome run bm7.yaml`.
