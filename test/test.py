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
# Testbench-only signals -- NOT pins on the ASIC. These are declared in tb.v
# and exist only in simulation; nothing below is available on real silicon.
#
#   uo_out_0            mirror of uo_out[0], exposed because Icarus VPI cannot
#                       register an edge trigger directly on a bit-select
# ---------------------------------------------------------------------------

async def static_PWM_test(dut, l_h):
    start_value = dut.uo_out[0].value
    await ClockCycles(dut.clk, 3)
    end_value = dut.uo_out[0].value

    if (l_h == start_value and l_h == end_value):
        return True
    else:
        return False
            
async def find_period(dut):
    await RisingEdge(dut.uo_out_0)
    start_time = cocotb.utils.get_sim_time(units="ns")
    await RisingEdge(dut.uo_out_0)
    end_time = cocotb.utils.get_sim_time(units="ns")
    return end_time - start_time

# Only handles non-static (i.e cannot be 0% or 100% PWM) duty cycles
async def find_duty_cycle(dut):
    await RisingEdge(dut.uo_out_0)
    start_time = cocotb.utils.get_sim_time(units="ns")
    await FallingEdge(dut.uo_out_0)
    end_time = cocotb.utils.get_sim_time(units="ns")
    period = await find_period(dut)
    return ((end_time - start_time) / period) * 100

async def await_half_sclk(dut):
    """Wait for the SCLK signal to go high or low."""
    start_time = cocotb.utils.get_sim_time(units="ns")
    while True:
        await ClockCycles(dut.clk, 1)
        # Wait for half of the SCLK period (10 us)
        if (start_time + 100*100*0.5) < cocotb.utils.get_sim_time(units="ns"):
            break
    return

def ui_in_logicarray(ncs, bit, sclk):
    """Setup the ui_in value as a LogicArray."""
    return LogicArray(f"00000{ncs}{bit}{sclk}")

async def send_spi_transaction(dut, r_w, address, data):
    """
    Send an SPI transaction with format:
    - 1 bit for Read/Write
    - 7 bits for address
    - 8 bits for data
    
    Parameters:
    - r_w: boolean, True for write, False for read
    - address: int, 7-bit address (0-127)
    - data: LogicArray or int, 8-bit data
    """
    # Convert data to int if it's a LogicArray
    if isinstance(data, LogicArray):
        data_int = int(data)
    else:
        data_int = data
    # Validate inputs
    if address < 0 or address > 127:
        raise ValueError("Address must be 7-bit (0-127)")
    if data_int < 0 or data_int > 255:
        raise ValueError("Data must be 8-bit (0-255)")
    # Combine RW and address into first byte
    first_byte = (int(r_w) << 7) | address
    # Start transaction - pull CS low
    sclk = 0
    ncs = 0
    bit = 0
    # Set initial state with CS low
    dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
    await ClockCycles(dut.clk, 1)
    # Send first byte (RW + Address)
    for i in range(8):
        bit = (first_byte >> (7-i)) & 0x1
        # SCLK low, set COPI
        sclk = 0
        dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
        await await_half_sclk(dut)
        # SCLK high, keep COPI
        sclk = 1
        dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
        await await_half_sclk(dut)
    # Send second byte (Data)
    for i in range(8):
        bit = (data_int >> (7-i)) & 0x1
        # SCLK low, set COPI
        sclk = 0
        dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
        await await_half_sclk(dut)
        # SCLK high, keep COPI
        sclk = 1
        dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
        await await_half_sclk(dut)
    # End transaction - return CS high
    sclk = 0
    ncs = 1
    bit = 0
    dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
    await ClockCycles(dut.clk, 600)
    return ui_in_logicarray(ncs, bit, sclk)

@cocotb.test()
async def test_spi(dut):
    dut._log.info("Start SPI test")

    # Set the clock period to 100 ns (10 MHz)
    clock = Clock(dut.clk, 100, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
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

    dut._log.info("Read transaction (invalid), address 0x00, data 0xBE")
    ui_in_val = await send_spi_transaction(dut, 0, 0x30, 0xBE)
    assert dut.uo_out.value == 0xF0, f"Expected 0xF0, got {dut.uo_out.value}"
    await ClockCycles(dut.clk, 100)
    
    dut._log.info("Read transaction (invalid), address 0x41 (invalid), data 0xEF")
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

# Test only works on 0x00 reg because you are testing PWM not other functions
@cocotb.test()
async def test_pwm_freq(dut):
    # Write your test here
    dut._log.info("Start PWM Frequency test")

    # Set the clock period to 100 ns (10 MHz)
    clock = Clock(dut.clk, 100, units="ns")
    cocotb.start_soon(clock.start())

    # Reset Sequence
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

    # Enabling registers 7:0  
    dut._log.info("Write transaction, address 0x00, data 0xFF")
    await send_spi_transaction(dut, 1, 0x00, 0xFF)  # Write transaction
    assert dut.uo_out.value == 0xFF, f"Expected 0xFF, got {dut.uo_out.value}"
    await ClockCycles(dut.clk, 1000) 

    # Enabling PWM registers 7:0  
    dut._log.info("Write transaction, address 0x02, data 0xFF")
    await send_spi_transaction(dut, 1, 0x02, 0xFF)
    await ClockCycles(dut.clk, 1000) 

    # Setting PWM to 50%
    dut._log.info("Write transaction, address 0x04, data 0x80")
    await send_spi_transaction(dut, 1, 0x04, 0x80)
    await ClockCycles(dut.clk, 1000) 

    # Finding period
    period = await find_period(dut)
    frequncy = 1e9/period #converts from ns to second

    assert frequncy >= 2970, f"Expected 3000 +- 30, got {frequncy}"
    assert frequncy <= 3030, f"Expected 3000 +- 30, got {frequncy}"

    dut._log.info("PWM Frequency test completed successfully")

# Test only works on 0x00 reg because you are testing PWM not other functions
@cocotb.test()
async def test_pwm_duty(dut):
    # Write your test here
    dut._log.info("Start PWM Frequency test")
    
    # Set the clock period to 100 ns (10 MHz)
    clock = Clock(dut.clk, 100, units="ns")
    cocotb.start_soon(clock.start())
    
    # Reset Sequence
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
    
    # Enabling registers 7:0  
    dut._log.info("Write transaction, address 0x00, data 0xFF")
    await send_spi_transaction(dut, 1, 0x00, 0xFF)  # Write transaction
    assert dut.uo_out.value == 0xFF, f"Expected 0xFF, got {dut.uo_out.value}"
    await ClockCycles(dut.clk, 1000) 
    
    # Enabling PWM registers 7:0  
    dut._log.info("Write transaction, address 0x02, data 0xFF")
    await send_spi_transaction(dut, 1, 0x02, 0xFF)
    await ClockCycles(dut.clk, 1000) 

    # Setting PWM to 100%
    dut._log.info("Write transaction, address 0x04, data 0xFF")
    await send_spi_transaction(dut, 1, 0x04, 0xFF)
    await ClockCycles(dut.clk, 1000) 

    # Check for constant high
    assert await static_PWM_test(dut, 1), f"Expected constant high, got changing signal"

    # Setting PWM to 0%
    dut._log.info("Write transaction, address 0x04, data 0x00")
    await send_spi_transaction(dut, 1, 0x04, 0x00)
    await ClockCycles(dut.clk, 1000) 

    # Check for constant low
    assert await static_PWM_test(dut, 0), f"Expected constant low, got changing signal"

    # Setting PWM to 50%
    dut._log.info("Write transaction, address 0x04, data 0x80")
    await send_spi_transaction(dut, 1, 0x04, 0x80)
    await ClockCycles(dut.clk, 1000) 

    # Verifying Duty Cycle 50%
    duty_cycle = await find_duty_cycle(dut)
    assert duty_cycle >= 49, f"Expected 50% duty cycle, got {duty_cycle}"
    assert duty_cycle <= 51, f"Expected 50% duty cycle, got {duty_cycle}"

    dut._log.info("PWM Duty Cycle test completed successfully")
