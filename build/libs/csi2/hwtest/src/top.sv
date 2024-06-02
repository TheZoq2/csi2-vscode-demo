module top(input clk_25mhz, output[7:0] led);
    reg rst = 1;
    always @(posedge clk_25mhz) begin
        rst <= 0;
    end

    \proj::main::main main
        ( .clk_i(clk_25mhz)
        , .rst_i(rst)
        , .output__(led)
        );
endmodule
