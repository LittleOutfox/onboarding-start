`default_nettype none

module spi_peripheral (
    input wire clk,
    input wire rising_edge,  // One-cycle pulse from the synchronized SCLK
    input wire nCS,          // Synchronized active-low chip select
    input wire COPI,         // Synchronized controller output
    input wire reset_n,
    output reg [7:0] en_reg_out_7_0,
    output reg [7:0] en_reg_out_15_8,
    output reg [7:0] en_reg_pwm_7_0,
    output reg [7:0] en_reg_pwm_15_8,
    output reg [7:0] pwm_duty_cycle
);
  localparam [1:0] IDLE = 2'd0, DATA = 2'd1, OUTPUT = 2'd2;

  reg [1:0] state;
  reg [1:0] next_state;
  reg [3:0] counter;
  reg [15:0] raw_data;
  reg data_done;
  wire nCS_rising_edge;

  posedge_detector #(
      .RESET_VALUE(1'b1)
  ) u_nCS_posedge (
      .sig_in(nCS),
      .clk(clk),
      .rst_n(reset_n),
      .posedge_out(nCS_rising_edge)
  );

  // State register with an asynchronous active-low reset.
  always @(posedge clk or negedge reset_n) begin
    if (!reset_n) begin
      state <= IDLE;
    end else begin
      state <= next_state;
    end
  end

  // Next-state logic.
  always @(*) begin
    next_state = state;
    case (state)
      IDLE: begin
        next_state = (nCS == 0) ? DATA : IDLE;
      end

      DATA: begin
        if (data_done) begin
          next_state = OUTPUT;
        end
      end

      OUTPUT: begin
        if (nCS_rising_edge) begin
          next_state = IDLE;
        end
      end

      default next_state = IDLE;
    endcase
  end

  // Capture the serial frame and update control registers.
  always @(posedge clk or negedge reset_n) begin
    if (!reset_n) begin
      raw_data <= 0;
      counter <= 0;
      en_reg_out_7_0 <= 0;
      en_reg_out_15_8 <= 0;
      en_reg_pwm_7_0 <= 0;
      en_reg_pwm_15_8 <= 0;
      pwm_duty_cycle <= 0;
      data_done <= 0;
    end else begin
      case (state)
        DATA: begin
          if (rising_edge) begin
            raw_data <= {raw_data[14:0], COPI};
            if (counter == 15) begin
              counter <= 0;
              data_done <= 1;
            end else begin
              counter <= counter + 1;
            end
          end
        end

        OUTPUT: begin
          data_done <= 0;
          // Only write transactions to mapped addresses can change a register.
          if ((raw_data[15] == 1) && nCS_rising_edge) begin
            case (raw_data[14:8])
              7'h00: en_reg_out_7_0 <= raw_data[7:0];
              7'h01: en_reg_out_15_8 <= raw_data[7:0];
              7'h02: en_reg_pwm_7_0 <= raw_data[7:0];
              7'h03: en_reg_pwm_15_8 <= raw_data[7:0];
              7'h04: pwm_duty_cycle <= raw_data[7:0];
              default;
            endcase
          end
        end

        default;
      endcase
    end
  end
endmodule
