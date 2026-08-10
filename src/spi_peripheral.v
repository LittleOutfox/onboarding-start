`default_nettype none

module spi_peripheral (
    input wire rising_edge,  //3ff synced
    input wire nCS,  //2ff synced
    input wire COPI,  //2ff synced
    output wire [7:0] en_reg_out_7_0,
    output wire [7:0] en_reg_out_15_8,
    output wire [7:0] en_reg_pwm_7_0,
    output wire [7:0] en_reg_pwm_15_8,
    output wire [7:0] pwm_duty_cycle
);
endmodule
