module posedge_detector #(
    parameter RESET_VALUE = 1'b0
) (
    input  wire sig_in,
    input  wire clk,
    input  wire rst_n,
    output wire posedge_out
);
  reg sig_prev;

  assign posedge_out = sig_in & !sig_prev;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      sig_prev <= RESET_VALUE;
    end else begin
      sig_prev <= sig_in;
    end
  end
endmodule
