[![GDS](https://github.com/LittleOutfox/spi-controlled-pwm-asic/actions/workflows/gds.yaml/badge.svg)](https://github.com/LittleOutfox/spi-controlled-pwm-asic/actions/workflows/gds.yaml)
[![Documentation](https://github.com/LittleOutfox/spi-controlled-pwm-asic/actions/workflows/docs.yaml/badge.svg)](https://github.com/LittleOutfox/spi-controlled-pwm-asic/actions/workflows/docs.yaml)
[![Tests](https://github.com/LittleOutfox/spi-controlled-pwm-asic/actions/workflows/test.yaml/badge.svg)](https://github.com/LittleOutfox/spi-controlled-pwm-asic/actions/workflows/test.yaml)

# SPI-Controlled PWM ASIC

This repo contains an SPI-controlled PWM ASIC with 16 output channels. The Verilog design supports disabled, static-high, and PWM outputs at approximately 3 kHz, with a shared 8-bit duty cycle.

## Design

- Implemented a write-only SPI Mode 0 interface with 16-bit, MSB-first frames containing an R/W bit, 7-bit address, and 8-bit data byte.
- Built a three-state FSM to capture frames and commit valid writes on the rising edge of `nCS`. Reads and unmapped addresses are ignored.
- Mapped five control registers to output enables, PWM enables, and duty cycle.
- Synchronized `SCLK`, `COPI`, and `nCS` through separate 2-FF synchronizers, with edge detection keeping all logic in one 10 MHz clock domain.

## Capture optimization

Optimized serial capture by replacing counter-indexed writes with a shift-register datapath:

```verilog
raw_data <= {raw_data[14:0], COPI};
```

SPI's fixed bit order removes the need for variable-index decode/mux steering. The counter tracks frame length while bits shift through fixed connections. The complete design synthesized to **417 cells**.

## Verification and implementation

Built three cocotb tests covering register writes, invalid-address/read traffic, PWM frequency, and 0%, 50%, and 100% duty cycles. Static endpoints use full-period level checks; midpoint duty is measured from signal edges.

Completed the SKY130 RTL-to-GDS flow with Yosys and OpenLane2. RTL simulation, GDS generation, Tiny Tapeout precheck, and gate-level simulation all passed.

[Design notes](docs/info.md) · [Verification details](test/README.md)

The PWM generator in `src/pwm_peripheral.v` is by Damir Gazizullin.
