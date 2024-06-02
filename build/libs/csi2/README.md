# Spade CSI2

Work in progress Spade library for parsing CSI2 data streams like those coming
out of the raspberry pi camera.

Currently being tested on a ULX3s with a hacked together camera connector ->
PMOD differential pair adapter. The initial i2c setup of the camera is done by
the `i2c_driver` running on an stm32f103 microcontroller whose i2c pins are
connected to the camera's.

Big thanks to gatecat for their CSI2 verilog implementation here https://github.com/gatecat/CSI2Rx.
