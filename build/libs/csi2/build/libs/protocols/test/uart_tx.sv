`include "test/vatch/main.v"

module uart_tx_tb;
    `SETUP_TEST
    // 5 should flush the whole pipeline before doing anything
    `CLK_AND_RST(clk, rst, 5)

    reg[8:0] to_transmit;
    wire tx;
    wire ready;

    localparam BIT_TIME = 100;

    initial begin
        @(negedge rst);

        to_transmit <= {1'b1, 8'hx};

        @(negedge clk)
        @(negedge clk)

        // High idle
        `ASSERT_EQ(tx, 1);
        `ASSERT_EQ(ready, 1);

        @(negedge clk)
        to_transmit <= {1'b0, 8'b11001010};
        @(negedge clk)
        // Ready signal goes low right away
        `ASSERT_EQ(ready, 0);
        // Start bit is low
        `ASSERT_EQ(tx, 0);

        to_transmit <= {1'b1, 8'hx};

        // Ignore small errors by sampling between signals
        repeat(BIT_TIME/2) @(negedge clk);

        repeat(BIT_TIME) @(negedge clk);
        `ASSERT_EQ(tx, 0);
        repeat(BIT_TIME) @(negedge clk);
        `ASSERT_EQ(tx, 1);
        repeat(BIT_TIME) @(negedge clk);
        `ASSERT_EQ(tx, 0);
        repeat(BIT_TIME) @(negedge clk);
        `ASSERT_EQ(tx, 1);
        repeat(BIT_TIME) @(negedge clk);
        `ASSERT_EQ(tx, 0);
        repeat(BIT_TIME) @(negedge clk);
        `ASSERT_EQ(tx, 0);
        repeat(BIT_TIME) @(negedge clk);
        `ASSERT_EQ(tx, 1);
        repeat(BIT_TIME) @(negedge clk);
        `ASSERT_EQ(tx, 1);

        // Stop bit is high
        repeat(BIT_TIME) @(negedge clk);
        `ASSERT_EQ(tx, 1);

        // Still high after stop bit but before new transmission
        repeat(BIT_TIME) @(negedge clk);
        `ASSERT_EQ(tx, 1);
        // Ready to receive
        `ASSERT_EQ(ready, 1);

        // Transmission 2
        @(negedge clk)
        to_transmit <= {1'b0, 8'b11110000};
        @(negedge clk)
        // Ready signal goes low right away
        `ASSERT_EQ(ready, 0);
        // Start bit is low
        `ASSERT_EQ(tx, 0);

        to_transmit <= {1'b1, 8'hx};
        @(negedge clk)
        to_transmit <= {1'b0, 8'b11001010};
        @(negedge clk)
        // Ready signal goes low right away
        `ASSERT_EQ(ready, 0);
        // Start bit is low
        `ASSERT_EQ(tx, 0);

        // Prepare to send next set of bytes which will be all 0
        to_transmit <= {1'b0, 8'h0};

        // Ignore small errors by sampling between signals
        repeat(BIT_TIME/2) @(negedge clk);

        repeat(4) begin
            repeat(BIT_TIME) @(negedge clk);
            `ASSERT_EQ(tx, 0);
        end
        repeat(4) begin
            repeat(BIT_TIME) @(negedge clk);
            `ASSERT_EQ(tx, 1);
        end

        // Stop bit is high
        repeat(BIT_TIME) @(negedge clk);
        `ASSERT_EQ(tx, 1);

        `END_TEST
    end

    e_protocols_uart_uart_tx uut
        ( ._i_protocols_uart_clk(clk)
        , ._i_protocols_uart_rst(rst)
        , ._i_protocols_uart_transmit(to_transmit)
        // 100 clock cycles per bit
        , ._i_protocols_uart_config(BIT_TIME)
        , .__output({tx, ready})
        );
endmodule
