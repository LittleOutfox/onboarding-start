module sync_2ff #(
    parameter RESET_VALUE = 1'b0
) (
    input  wire async_in,
    input  wire clk,
    input  wire rst_n,
    output wire synced_input
);
  (* ASYNC_REG = "TRUE", SHREG_EXTRACT = "NO" *)reg filter1;
  (* ASYNC_REG = "TRUE", SHREG_EXTRACT = "NO" *)reg filter2;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      filter1 <= RESET_VALUE;
      filter2 <= RESET_VALUE;
    end else begin
      filter1 <= async_in;
      filter2 <= filter1;
    end
  end

  assign synced_input = filter2;
endmodule
