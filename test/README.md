# Verification

Three cocotb tests exercise the design through its top-level pins. All passed in RTL and gate-level simulation using Icarus Verilog.

| Test | Checks |
|---|---|
| `test_spi` | Writes to both output banks, lower-bank output retention after invalid-address/read traffic, and several duty-register values |
| `test_pwm_freq` | PWM0 frequency within 3 kHz +/- 30 Hz |
| `test_pwm_duty` | Static 0% and 100% outputs; measured midpoint duty within 49-51% |

## Measurements

SPI traffic runs at roughly 100 kHz against the 10 MHz system clock. PWM period and midpoint duty use edge timing on `uo_out_0`, exposed separately because Icarus VPI cannot trigger directly on a bit-select.

The static endpoints are checked over 3,370 system-clock cycles, slightly longer than a full period at the lowest accepted PWM frequency.

## Coverage limits

PWM measurements cover channel 0. Interrupted-frame recovery and exhaustive channel coverage are untested. Read frames use unmapped addresses, so they do not independently verify R/W decoding. The SPI test rate is not a measured interface limit.
