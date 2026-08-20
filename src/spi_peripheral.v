`default_nettype none

module spi_peripheral (
    input wire rising_edge,  //3ff synced
    input wire nCS,  //2ff synced
    input wire COPI,  //2ff synced  
    input wire reset_n,
    output wire [7:0] en_reg_out_7_0,
    output wire [7:0] en_reg_out_15_8,
    output wire [7:0] en_reg_pwm_7_0,
    output wire [7:0] en_reg_pwm_15_8,
    output wire [7:0] pwm_duty_cycle
);

  reg [ 1:0] state = IDLE;
  reg [ 1:0] next_state = 0;
  reg [ 3:0] counter = 0;  //needs to set to 0 on reset
  reg [15:0] raw_data = 0;

  lcoalparam [1:0] IDLE = 2'd0, DATA = 2'd1, OUTPUT = 2'd2;
  // Async reset w/ transition logic
  always @(posedge clk or negedge reset_n) begin
    if (reset) begin
      state <= IDLE;
    end else begin
      state <= next_state;
    end
  end

  // Combinational Logic for Next State
  always @(*) begin
    next_state = state;
    case (state)
      IDLE: begin
        next_state = (nCS == 0) ? DATA : IDLE;
      end

      DATA: begin  // only move on after 16 clock cycles
        if (counter == 16) begin
          next_state = OUTPUT;
        end
      end

      OUTPUT: begin
        next_state = IDLE;
      end

      default next_state = IDLE;
    endcase
  end

  //Output logic (Sequential since we need stored info)
  always @(posedge clk or negedge reset_n) begin
    if (reset) begin
      counter <= 0;
      en_reg_out_7_0 <= 0;
      en_reg_out_15_8 <= 0;
      en_reg_pwm_7_0 <= 0;
      en_reg_pwm_15_8 <= 0;
      pwm_duty_cycle <= 0;
    end else begin
      case (state)
        DATA: begin
          if (rising_edge) begin
            raw_data[counter] <= COPI;
            if (counter <= 15) begin
              counter <= counter + 1;
            end else begin  // for the 16th operation
              counter <= 0;
            end
          end
        end

        OUTPUT: begin
          if (raw_data[0] == 1) begin  //ignore if read operation
            if (raw_data[7:5] == 0) begin
              en_reg_out_7_0 <= raw_data[15:8];
            end else if (raw_data[7:5] == 1) begin
              en_reg_out_15_8 <= raw_data[15:8];
            end else if (raw_data[7:5] == 2) begin
              en_reg_pwm_7_0 <= raw_data[15:8];
            end else if (raw_data[7:5] == 3) begin
              en_reg_pwm_15_8 <= raw_data[15:8];
            end else if (raw_data[7:5] == 4) begin
              pwm_duty_cycle <= raw_data[15:8];
            end
          end
        end
      endcase
    end
  end
endmodule

