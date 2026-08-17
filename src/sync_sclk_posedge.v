module sync_sclk_posedge (
    input  wire async_in,
    input  wire clk,
    input  wire rst_n,
    output wire synced_posedge
);
  wire synced_sclk;
  reg  synced_sclk_prev;
  wire rising_edge = synced_sclk & !synced_sclk_prev;
  assign synced_posedge = rising_edge;

  sync_2ff #(
      .RESET_VALUE(1'b0)
  ) u_sync_2ff (
      .async_in(async_in),
      .clk(clk),
      .rst_n(rst_n),
      .synced_input(synced_sclk)
  );

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      synced_sclk_prev <= 1'b0;
    end else begin
      synced_sclk_prev <= synced_sclk;
    end
  end
endmodule
