# Makefile
# cocotb simulator configuration

# Default to Icarus Verilog for RTL simulation.
SIM ?= icarus
TOPLEVEL_LANG ?= verilog
SRC_DIR = $(PWD)/../src
PROJECT_SOURCES = project.v spi_peripheral.v pwm_peripheral.v sync_2ff.v posedge_detector.v

ifneq ($(GATES),yes)

# RTL simulation
SIM_BUILD				= sim_build/rtl
VERILOG_SOURCES += $(addprefix $(SRC_DIR)/,$(PROJECT_SOURCES))

else

# Gate-level simulation
SIM_BUILD				= sim_build/gl
COMPILE_ARGS    += -DGL_TEST
COMPILE_ARGS    += -DFUNCTIONAL
COMPILE_ARGS    += -DUSE_POWER_PINS
COMPILE_ARGS    += -DSIM
COMPILE_ARGS    += -DUNIT_DELAY=\#1
VERILOG_SOURCES += $(PDK_ROOT)/sky130A/libs.ref/sky130_fd_sc_hd/verilog/primitives.v
VERILOG_SOURCES += $(PDK_ROOT)/sky130A/libs.ref/sky130_fd_sc_hd/verilog/sky130_fd_sc_hd.v

# The GDS workflow copies the hardened netlist here before running cocotb.
VERILOG_SOURCES += $(PWD)/gate_level_netlist.v

endif

# Make source-directory includes available to the design and testbench.
COMPILE_ARGS 		+= -I$(SRC_DIR)

# Add the Verilog testbench wrapper.
VERILOG_SOURCES += $(PWD)/tb.v
TOPLEVEL = tb

# Python test module name, without the .py extension.
MODULE = test

# Load cocotb's simulator rules.
include $(shell cocotb-config --makefiles)/Makefile.sim
