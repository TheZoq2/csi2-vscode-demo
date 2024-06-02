`include "test/vatch/main.v"

module uart_rx_tb;
    `SETUP_TEST
    // 5 should flush the whole pipeline before doing anything
    `CLK_AND_RST(clk, rst, 5)

    reg[8:0] to_transmit;
    reg rx;

    wire validn;
    wire[7:0] data;

    reg is_last_bit;

    localparam BIT_TIME = 100;

    `define SEND_BIT(B) \
        rx = B; \
        repeat(BIT_TIME) @(negedge clk);

    initial begin
        @(negedge rst);

        `ASSERT_EQ(validn, 1);

        // Pre transmission
        `SEND_BIT(1);

        // Start bit
        `SEND_BIT(0);

        // 0b11001010
        `SEND_BIT(0);
        `SEND_BIT(1);
        `SEND_BIT(0);
        `SEND_BIT(1);
        `SEND_BIT(0);
        `SEND_BIT(0);
        `SEND_BIT(1);
        is_last_bit = 1;
        `SEND_BIT(1);

        // Stop bit
        `SEND_BIT(1);
        is_last_bit = 0;

        // Post transmission
        `SEND_BIT(1);
        `SEND_BIT(1);

        `END_TEST
    end

    reg got_result;

    initial begin
        forever begin
            @(posedge is_last_bit);
            got_result = 0;

            while (got_result == 0) begin
                if(!validn && is_last_bit) begin
                    `ASSERT_EQ(data, 'b11001010);
                    got_result = 1;
                end
                `ASSERT_EQ(is_last_bit, 1, "Did not get result before is_last_bit")
                @(negedge clk);
            end
        end
    end

    e_protocols_uart_uart_rx uut
        ( ._i_protocols_uart_clk(clk)
        , ._i_protocols_uart_rst(rst)
        , ._i_protocols_uart_rx(rx)
        , ._i_protocols_uart_config(BIT_TIME)
        , .__output({validn, data})
        );
endmodule
