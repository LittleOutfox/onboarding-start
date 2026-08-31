`default_nettype none

module spi_peripheral (
    input wire clk,
    input wire rising_edge,  //3ff synced
    input wire nCS,  //2ff synced
    input wire COPI,  //2ff synced  
    input wire reset_n,
    output reg [7:0] en_reg_out_7_0,
    output reg [7:0] en_reg_out_15_8,
    output reg [7:0] en_reg_pwm_7_0,
    output reg [7:0] en_reg_pwm_15_8,
    output reg [7:0] pwm_duty_cycle
);
  localparam [1:0] IDLE = 2'd0, DATA = 2'd1, OUTPUT = 2'd2;
  localparam [6:0] max_address = 7'h04;  // 0x00 to 0x04 are valid addresses

  reg [1:0] state;
  reg [1:0] next_state;
  reg [3:0] counter;  //needs to set to 0 on reset
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

  // Async reset w/ transition logic
  always @(posedge clk or negedge reset_n) begin
    if (!reset_n) begin
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

  //Output logic (Sequential since we need stored info)
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
            //Read or Write 
            if (counter == 0) begin
              raw_data[0] <= COPI;
              counter  <= counter + 1;
            end else if ((counter >= 1) & (counter <= 7)) begin  //address
              raw_data[8-counter] <= COPI;
              counter <= counter + 1;
            end else if ((counter >= 8) & (counter <= 14)) begin  //everything that makes it here should be data
              raw_data[23-counter] <= COPI;
              counter <= counter + 1;
            end else begin  // counter is 15
              raw_data[23-counter] <= COPI;
              counter <= 0;
              data_done <= 1;
            end
          end
        end

        OUTPUT: begin
          data_done <= 0;
          //ignore if read op || invalid address
          if ((raw_data[0] == 1) && (raw_data[7:1] <= max_address) && nCS_rising_edge) begin
            if (raw_data[7:1] == 7'h00) begin
              en_reg_out_7_0 <= raw_data[15:8];
            end else if (raw_data[7:1] == 7'h01) begin
              en_reg_out_15_8 <= raw_data[15:8];
            end else if (raw_data[7:1] == 7'h02) begin
              en_reg_pwm_7_0 <= raw_data[15:8];
            end else if (raw_data[7:1] == 7'h03) begin
              en_reg_pwm_15_8 <= raw_data[15:8];
            end else if (raw_data[7:1] == 7'h04) begin
              pwm_duty_cycle <= raw_data[15:8];
            end
          end
        end

        default;
      endcase
    end
  end
endmodule

