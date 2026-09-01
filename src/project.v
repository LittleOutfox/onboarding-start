/*
 * Copyright (c) 2024 Ethan Tiong
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module tt_um_uwasic_onboarding_ethan_tiong (
    input  wire [7:0] ui_in,    // ui_in[0]=SCLK, ui_in[1]=COPI, ui_in[2]=nCS
    output wire [7:0] uo_out,   // PWM channels 0-7
    input  wire [7:0] uio_in,   // Unused input path
    output wire [7:0] uio_out,  // PWM channels 8-15
    output wire [7:0] uio_oe,   // Bidirectional-pin output enables
    input  wire       ena,      // High while this design is selected
    input  wire       clk,      // 10 MHz system clock
    input  wire       rst_n     // Active-low reset
);
  wire [7:0] en_reg_out_7_0;
  wire [7:0] en_reg_out_15_8;
  wire [7:0] en_reg_pwm_7_0;
  wire [7:0] en_reg_pwm_15_8;
  wire [7:0] pwm_duty_cycle;
  wire [15:0] spi_out;
  wire nCS_synced;
  wire COPI_synced;
  wire sclk_synced;
  wire spi_peripheral_rising_edge;

  assign uio_oe  = 8'hFF;  // Channels 8-15 always drive the bidirectional pins
  assign uo_out  = spi_out[7:0];
  assign uio_out = spi_out[15:8];

  // Consume unused top-level inputs so lint does not report them.
  wire _unused = &{ui_in[7:3], ena, uio_in, 1'b0};

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

  sync_2ff #(
      .RESET_VALUE(1'b0)
  ) u_sync_sclk (
      .async_in(ui_in[0]),
      .clk(clk),
      .rst_n(rst_n),
      .synced_input(sclk_synced)
  );

  posedge_detector u_sclk_posedge (
      .sig_in(sclk_synced),
      .clk(clk),
      .rst_n(rst_n),
      .posedge_out(spi_peripheral_rising_edge)
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
