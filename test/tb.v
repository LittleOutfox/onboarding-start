`default_nettype none
`timescale 1ns / 1ps

/* cocotb drives this wrapper for both RTL and gate-level simulation. */
module tb ();

  // Record the full testbench hierarchy for waveform debugging.
  initial begin
    $dumpfile("tb.vcd");
    $dumpvars(0, tb);
    #1;
  end

  // Tiny Tapeout interface signals.
  reg clk;
  reg rst_n;
  reg ena;
  reg [7:0] ui_in;
  reg [7:0] uio_in;
  wire [7:0] uo_out;
  wire [7:0] uio_out;
  wire [7:0] uio_oe;
  wire uo_out_0;
`ifdef GL_TEST
  wire VPWR = 1'b1;
  wire VGND = 1'b0;
`endif

  assign uo_out_0 = uo_out[0];

  // Device under test.
  tt_um_uwasic_onboarding_ethan_tiong user_project (

      // The hardened netlist exposes explicit power pins.
`ifdef GL_TEST
      .VPWR(VPWR),
      .VGND(VGND),
`endif

      .ui_in  (ui_in),
      .uo_out (uo_out),
      .uio_in (uio_in),
      .uio_out(uio_out),
      .uio_oe (uio_oe),
      .ena    (ena),
      .clk    (clk),
      .rst_n  (rst_n)
  );

endmodule
