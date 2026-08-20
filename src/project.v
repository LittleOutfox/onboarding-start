/*
 * Copyright (c) 2024 Ethan Tiong
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module tt_um_uwasic_onboarding_ethan_tiong (
    input  wire [7:0] ui_in,    // Dedicated inputs
    output wire [7:0] uo_out,   // Dedicated outputs
    input  wire [7:0] uio_in,   // IOs: Input path
    output wire [7:0] uio_out,  // IOs: Output path
    output wire [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)
    input  wire       ena,      // always 1 when the design is powered, so you can ignore it
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);
  wire [7:0] en_reg_out_7_0;
  wire [7:0] en_reg_out_15_8;
  wire [7:0] en_reg_pwm_7_0;
  wire [7:0] en_reg_pwm_15_8;
  wire [7:0] pwm_duty_cycle;
  wire [15:0] spi_out;
  wire nCS_synced;
  wire COPI_synced;
  wire spi_peripheral_rising_edge;

  assign uio_oe  = 8'hFF;  // Set all IOs to output
  assign uo_out  = spi_out[7:0];  // Lower 8 bits to uo_out
  assign uio_out = spi_out[15:8];  // Upper 8 bits to uio_out

  pwm_peripheral u_pwm_peripheral (
      .clk(clk),
      .rst_n(rst_n),
      .en_reg_out_7_0(en_reg_out_7_0),
      .en_reg_out_15_8(en_reg_out_15_8),
      .en_reg_pwm_7_0(en_reg_pwm_7_0),
      .en_reg_pwm_15_8(en_reg_pwm_15_8),
      .pwm_duty_cycle(pwm_duty_cycle),
      .out(spi_out)
  );

  sync_2ff #(
      .RESET_VALUE(1'b1)
  ) u_sync_nCS (
      .async_in(ui_in[2]),
      .clk(clk),
      .rst_n(rst_n),
      .synced_input(nCS_synced)
  );

  sync_2ff #(
      .RESET_VALUE(1'b0)
  ) u_sync_COPI (
      .async_in(ui_in[1]),
      .clk(clk),
      .rst_n(rst_n),
      .synced_input(COPI_synced)
  );

  sync_sclk_posedge u_sync_sclk_posedge (
      .async_in(ui_in[0]),
      .clk(clk),
      .rst_n(rst_n),
      .synced_posedge(spi_peripheral_rising_edge)
  );

  spi_peripheral u_spi_peripheral (
      .clk(clk),
      .rising_edge(spi_peripheral_rising_edge),
      .nCS(nCS_synced),
      .COPI(COPI_synced),
      .reset_n(rst_n),
      .en_reg_out_7_0(en_reg_out_7_0),
      .en_reg_out_15_8(en_reg_out_15_8),
      .en_reg_pwm_7_0(en_reg_pwm_7_0),
      .en_reg_pwm_15_8(en_reg_pwm_15_8),
      .pwm_duty_cycle(pwm_duty_cycle)
  );


endmodule
