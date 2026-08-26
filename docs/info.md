<!---

This file is used to generate your project datasheet. Please fill in the information below and delete any unused
sections.

You can also include images in this folder and reference them in the markdown. Each image must be less than
512 kb in size, and the combined size of all images must be less than 1 MB.
-->

## How it works

An SPI peripheral driving 16 PWM output channels.

A controller sends 16-bit transactions, MSB first: 1 R/W bit, then a 7-bit address, then 8
bits of data. Only writes do anything. Reads get ignored, and so does any address above 0x04.

| address | register | what it does |
|---------|-----------------|-------------------------------|
| 0x00 | en_reg_out_7_0 | output enable, channels 0-7 |
| 0x01 | en_reg_out_15_8 | output enable, channels 8-15 |
| 0x02 | en_reg_pwm_7_0 | PWM enable, channels 0-7 |
| 0x03 | en_reg_pwm_15_8 | PWM enable, channels 8-15 |
| 0x04 | pwm_duty_cycle | duty cycle, shared by all 16 |

A channel with its output enable set but not its PWM enable just sits high. Set the PWM bit
too and it gets chopped at whatever duty is in 0x04. There's only one duty register so all
the PWM'd channels share it.

SCLK, COPI and nCS arrive on the input pins with no relation to the 10 MHz system clock, so
each one goes through a 2FF synchronizer first. The synchronizer is parameterised on its
reset value because they don't all idle the same way - nCS resets to 1, the other two to 0.
If nCS came out of reset low the FSM would immediately think a transaction was in progress.

SCLK gets one more flop after the synchronizer so I can compare it against its previous
value and get a one cycle pulse on the rising edge. Everything shifts on that pulse, so no
part of the design is clocked off SCLK itself.

The peripheral is a 3 state FSM. IDLE waits for nCS to drop. DATA takes one bit per SCLK
rising edge until all 16 are in. OUTPUT does the actual register write, and it's gated on
the nCS rising edge so a transaction that gets cut off partway never commits.

pwm_peripheral.v was given to us. It divides the 10 MHz clock by (12+1)*256, so the PWM
comes out around 3 kHz.

## How to test

cocotb. From test/:

    make -B

test_spi writes 0xF0 to 0x00 and checks uo_out, writes 0xCC to 0x01 and checks uio_out, then
throws invalid addresses and read transactions at it to confirm they're ignored. It runs SCLK
at 100 kHz, which is 50 system clocks per half period, well clear of the 3 the synchronizer
needs to settle.

Gate level:

    make -B GATES=yes

Waveforms land in tb.vcd.

## External hardware

None needed. LEDs on the outputs if you want to actually see the PWM.
