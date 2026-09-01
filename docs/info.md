## Design

A write-only SPI Mode 0 peripheral controls 16 static/PWM outputs. The design uses a 10 MHz system clock and a shared PWM waveform at approximately 3 kHz.

### Transaction format

Frames contain 16 bits, captured MSB first:

| Bits | Field | Meaning |
|---|---|---|
| 15 | R/W | `1` writes; `0` is ignored |
| 14:8 | Address | Selects a control register |
| 7:0 | Data | New 8-bit register value |

### Register map

| Address | Register | Function |
|---|---|---|
| `0x00` | `en_reg_out_7_0` | Enables outputs 0-7 |
| `0x01` | `en_reg_out_15_8` | Enables outputs 8-15 |
| `0x02` | `en_reg_pwm_7_0` | Enables PWM on outputs 0-7 |
| `0x03` | `en_reg_pwm_15_8` | Enables PWM on outputs 8-15 |
| `0x04` | `pwm_duty_cycle` | Sets the shared 8-bit duty cycle |

Disabled outputs stay low. Enabled outputs stay high or follow the shared waveform, depending on their PWM-enable bit. Reads and unmapped addresses leave all registers unchanged; there is no readback pin.

### Clocking and FSM

Separate 2-FF synchronizers bring `SCLK`, `COPI`, and `nCS` into the system-clock domain. Parameterized reset values hold `nCS` high and the other inputs low. A rising-edge detector on synchronized `SCLK` generates a one-cycle capture enable.

| State | Behaviour |
|---|---|
| `IDLE` | Waits for `nCS` to go low |
| `DATA` | Shifts in bits on detected `SCLK` rising edges until the frame is complete |
| `OUTPUT` | Commits a mapped write on the `nCS` rising edge, then returns to `IDLE` |

The interface assumes complete 16-bit frames and time for synchronization and the transition to `OUTPUT` before `nCS` rises. An early `nCS` rise does not clear a partial frame or exit `DATA`.

### Capture optimization

Counter-indexed writes were replaced with `raw_data <= {raw_data[14:0], COPI}`. Fixed serial ordering eliminates variable-index capture steering; the counter only tracks frame length. Final synthesis: **417 cells** for the complete design.

## Results

Three cocotb tests passed at RTL and gate level, covering register control, PWM frequency, and 0%, 50%, and 100% duty cycles. The Yosys/OpenLane2 flow completed GDS generation and passed Tiny Tapeout precheck.

The integrated PWM generator is Damir Gazizullin's block in `src/pwm_peripheral.v`.
