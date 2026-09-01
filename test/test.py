# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
from cocotb.triggers import FallingEdge
from cocotb.triggers import ClockCycles
from cocotb.types import Logic
from cocotb.types import LogicArray

# ---------------------------------------------------------------------------
# Pinout
#
#   ui_in [0] SCLK      uo_out[0] PWM0      uio_out[0] PWM8
#   ui_in [1] COPI      uo_out[1] PWM1      uio_out[1] PWM9
#   ui_in [2] nCS       uo_out[2] PWM2      uio_out[2] PWM10
#   ui_in [3] -         uo_out[3] PWM3      uio_out[3] PWM11
#   ui_in [4] -         uo_out[4] PWM4      uio_out[4] PWM12
#   ui_in [5] -         uo_out[5] PWM5      uio_out[5] PWM13
#   ui_in [6] -         uo_out[6] PWM6      uio_out[6] PWM14
#   ui_in [7] -         uo_out[7] PWM7      uio_out[7] PWM15
#
# Simulation-only signal declared in tb.v; this is not an ASIC pin.
#
#   uo_out_0            Mirror of uo_out[0]. Icarus VPI cannot register an edge
#                       trigger directly on a bit-select.
# ---------------------------------------------------------------------------

async def static_PWM_test(dut, l_h):
    # Hold the observation window slightly longer than one period at 2.97 kHz.
    for i in range(3370):
        await ClockCycles(dut.clk, 1)
        value = dut.uo_out[0].value
        if(value != l_h):
            return False

    return True  # The output stayed at the expected level for the full window.
            
async def find_period(dut):
    await RisingEdge(dut.uo_out_0)
    start_time = cocotb.utils.get_sim_time(units="ns")
    await RisingEdge(dut.uo_out_0)
    end_time = cocotb.utils.get_sim_time(units="ns")
    return end_time - start_time

# Edge-based measurement is only valid for non-static duty cycles.
async def find_duty_cycle(dut):
    await RisingEdge(dut.uo_out_0)
    start_time = cocotb.utils.get_sim_time(units="ns")
    await FallingEdge(dut.uo_out_0)
    end_time = cocotb.utils.get_sim_time(units="ns")
    period = await find_period(dut)
    return ((end_time - start_time) / period) * 100

async def await_half_sclk(dut):
    """Wait for one 5 us half-period of the 100 kHz SPI clock."""
    start_time = cocotb.utils.get_sim_time(units="ns")
    while True:
        await ClockCycles(dut.clk, 1)
        # One system-clock period is 100 ns.
        if (start_time + 100*100*0.5) < cocotb.utils.get_sim_time(units="ns"):
            break
    return

def ui_in_logicarray(ncs, bit, sclk):
    """Pack nCS, COPI, and SCLK into the Tiny Tapeout input bus."""
    return LogicArray(f"00000{ncs}{bit}{sclk}")

async def send_spi_transaction(dut, r_w, address, data):
    """Send one MSB-first frame: R/W bit, 7-bit address, then 8-bit data."""
    # Accept either an integer or cocotb LogicArray as the data byte.
    if isinstance(data, LogicArray):
        data_int = int(data)
    else:
        data_int = data
    # Fail early instead of silently truncating an invalid frame.
    if address < 0 or address > 127:
        raise ValueError("Address must be 7-bit (0-127)")
    if data_int < 0 or data_int > 255:
        raise ValueError("Data must be 8-bit (0-255)")
    # The R/W bit occupies bit 15 of the complete transaction.
    first_byte = (int(r_w) << 7) | address
    # Start the transaction with SCLK low for SPI Mode 0.
    sclk = 0
    ncs = 0
    bit = 0
    # Assert nCS before starting the first SCLK low half-period.
    dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
    await ClockCycles(dut.clk, 1)
    # Send the R/W bit and address MSB first.
    for i in range(8):
        bit = (first_byte >> (7-i)) & 0x1
        # Change COPI while SCLK is low.
        sclk = 0
        dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
        await await_half_sclk(dut)
        # Hold COPI stable through the rising edge.
        sclk = 1
        dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
        await await_half_sclk(dut)
    # Send the data byte MSB first.
    for i in range(8):
        bit = (data_int >> (7-i)) & 0x1
        # Change COPI while SCLK is low.
        sclk = 0
        dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
        await await_half_sclk(dut)
        # Hold COPI stable through the rising edge.
        sclk = 1
        dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
        await await_half_sclk(dut)
    # End the transaction so the peripheral can commit a valid write.
    sclk = 0
    ncs = 1
    bit = 0
    dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
    await ClockCycles(dut.clk, 600)
    return ui_in_logicarray(ncs, bit, sclk)

@cocotb.test()
async def test_spi(dut):
    dut._log.info("Start SPI test")

    # Tiny Tapeout supplies a 10 MHz system clock.
    clock = Clock(dut.clk, 100, units="ns")
    cocotb.start_soon(clock.start())

    # Reset with the SPI bus in its idle state.
    dut._log.info("Reset")
    dut.ena.value = 1
    ncs = 1
    bit = 0
    sclk = 0
    dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 5)

    dut._log.info("Test project behavior")
    dut._log.info("Write transaction, address 0x00, data 0xF0")
    ui_in_val = await send_spi_transaction(dut, 1, 0x00, 0xF0)  # Write transaction
    assert dut.uo_out.value == 0xF0, f"Expected 0xF0, got {dut.uo_out.value}"
    await ClockCycles(dut.clk, 1000) 

    dut._log.info("Write transaction, address 0x01, data 0xCC")
    ui_in_val = await send_spi_transaction(dut, 1, 0x01, 0xCC)  # Write transaction
    assert dut.uio_out.value == 0xCC, f"Expected 0xCC, got {dut.uio_out.value}"
    await ClockCycles(dut.clk, 100)

    dut._log.info("Write transaction, address 0x30 (invalid), data 0xAA")
    ui_in_val = await send_spi_transaction(dut, 1, 0x30, 0xAA)
    await ClockCycles(dut.clk, 100)

    dut._log.info("Read transaction (ignored), address 0x30, data 0xBE")
    ui_in_val = await send_spi_transaction(dut, 0, 0x30, 0xBE)
    assert dut.uo_out.value == 0xF0, f"Expected 0xF0, got {dut.uo_out.value}"
    await ClockCycles(dut.clk, 100)
    
    dut._log.info("Read transaction (ignored), address 0x41, data 0xEF")
    ui_in_val = await send_spi_transaction(dut, 0, 0x41, 0xEF)
    await ClockCycles(dut.clk, 100)

    dut._log.info("Write transaction, address 0x02, data 0xFF")
    ui_in_val = await send_spi_transaction(dut, 1, 0x02, 0xFF)  # Write transaction
    await ClockCycles(dut.clk, 100)

    dut._log.info("Write transaction, address 0x04, data 0xCF")
    ui_in_val = await send_spi_transaction(dut, 1, 0x04, 0xCF)  # Write transaction
    await ClockCycles(dut.clk, 30000)

    dut._log.info("Write transaction, address 0x04, data 0xFF")
    ui_in_val = await send_spi_transaction(dut, 1, 0x04, 0xFF)  # Write transaction
    await ClockCycles(dut.clk, 30000)

    dut._log.info("Write transaction, address 0x04, data 0x00")
    ui_in_val = await send_spi_transaction(dut, 1, 0x04, 0x00)  # Write transaction
    await ClockCycles(dut.clk, 30000)

    dut._log.info("Write transaction, address 0x04, data 0x01")
    ui_in_val = await send_spi_transaction(dut, 1, 0x04, 0x01)  # Write transaction
    await ClockCycles(dut.clk, 30000)

    dut._log.info("SPI test completed successfully")

# Measure PWM0 after enabling output 0 and its PWM control bit.
@cocotb.test()
async def test_pwm_freq(dut):
    dut._log.info("Start PWM Frequency test")

    # Tiny Tapeout supplies a 10 MHz system clock.
    clock = Clock(dut.clk, 100, units="ns")
    cocotb.start_soon(clock.start())

    # Reset with the SPI bus in its idle state.
    dut._log.info("Reset")
    dut.ena.value = 1
    ncs = 1
    bit = 0
    sclk = 0
    dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 5)

    # Enable the lower output bank.
    dut._log.info("Write transaction, address 0x00, data 0xFF")
    await send_spi_transaction(dut, 1, 0x00, 0xFF)  # Write transaction
    assert dut.uo_out.value == 0xFF, f"Expected 0xFF, got {dut.uo_out.value}"
    await ClockCycles(dut.clk, 1000) 

    # Enable PWM on the lower output bank.
    dut._log.info("Write transaction, address 0x02, data 0xFF")
    await send_spi_transaction(dut, 1, 0x02, 0xFF)
    await ClockCycles(dut.clk, 1000) 

    # Use a 50% duty cycle so period measurement has clean rising edges.
    dut._log.info("Write transaction, address 0x04, data 0x80")
    await send_spi_transaction(dut, 1, 0x04, 0x80)
    await ClockCycles(dut.clk, 1000) 

    # Convert the measured period from nanoseconds to hertz.
    period = await find_period(dut)
    frequency = 1e9/period

    assert frequency >= 2970, f"Expected 3000 +- 30, got {frequency}"
    assert frequency <= 3030, f"Expected 3000 +- 30, got {frequency}"

    dut._log.info("PWM Frequency test completed successfully")

# Check PWM0 at the two static endpoints and at a measurable 50% duty cycle.
@cocotb.test()
async def test_pwm_duty(dut):
    dut._log.info("Start PWM Duty Cycle test")
    
    # Tiny Tapeout supplies a 10 MHz system clock.
    clock = Clock(dut.clk, 100, units="ns")
    cocotb.start_soon(clock.start())
    
    # Reset with the SPI bus in its idle state.
    dut._log.info("Reset")
    dut.ena.value = 1
    ncs = 1
    bit = 0
    sclk = 0
    dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 5)
    
    # Enable the lower output bank.
    dut._log.info("Write transaction, address 0x00, data 0xFF")
    await send_spi_transaction(dut, 1, 0x00, 0xFF)  # Write transaction
    assert dut.uo_out.value == 0xFF, f"Expected 0xFF, got {dut.uo_out.value}"
    await ClockCycles(dut.clk, 1000) 
    
    # Enable PWM on the lower output bank.
    dut._log.info("Write transaction, address 0x02, data 0xFF")
    await send_spi_transaction(dut, 1, 0x02, 0xFF)
    await ClockCycles(dut.clk, 1000) 

    # A duty register of 0xFF must produce a constant high output.
    dut._log.info("Write transaction, address 0x04, data 0xFF")
    await send_spi_transaction(dut, 1, 0x04, 0xFF)
    await ClockCycles(dut.clk, 1000) 

    # Edge-based measurement would hang here, so observe a full period instead.
    assert await static_PWM_test(dut, 1), f"Expected constant high, got changing signal"

    # A duty register of 0x00 must produce a constant low output.
    dut._log.info("Write transaction, address 0x04, data 0x00")
    await send_spi_transaction(dut, 1, 0x04, 0x00)
    await ClockCycles(dut.clk, 1000) 

    # Again, check the static level across a full PWM period.
    assert await static_PWM_test(dut, 0), f"Expected constant low, got changing signal"

    # The midpoint can be measured from its rising and falling edges.
    dut._log.info("Write transaction, address 0x04, data 0x80")
    await send_spi_transaction(dut, 1, 0x04, 0x80)
    await ClockCycles(dut.clk, 1000) 

    # Allow 1% tolerance around the requested 50% duty cycle.
    duty_cycle = await find_duty_cycle(dut)
    assert duty_cycle >= 49, f"Expected 50% duty cycle, got {duty_cycle}"
    assert duty_cycle <= 51, f"Expected 50% duty cycle, got {duty_cycle}"

    dut._log.info("PWM Duty Cycle test completed successfully")
