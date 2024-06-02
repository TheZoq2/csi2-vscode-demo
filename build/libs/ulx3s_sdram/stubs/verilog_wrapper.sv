module sdram_controller_wrapper(
    input  wire          clk25,
    input  wire          rst,
    output reg           uart_tx,
    input  wire          uart_rx,
    output wire   [12:0] sdram_a,
    output wire    [1:0] sdram_ba,
    output wire          sdram_ras_n,
    output wire          sdram_cas_n,
    output wire          sdram_we_n,
    output wire          sdram_cs_n,
    output wire    [1:0] sdram_dm,
    input  wire   [15:0] sdram_dq,
    output wire          sdram_cke,
    output wire          init_done,
    output wire          init_error,
    output wire          sdram_clock,
    output wire          user_rst,

    ##IO_WIRES##

    // The outputs passed to spade as outputs rather than &mut
    output wire          sys_clk
);

    wire main_ecp5pll0_clkout0;
    wire main_ecp5pll0_clkout1;
    wire sys_ps_clk;


    wire builder_basesoc_ecp5pll0_ecp5pll;
    wire builder_basesoc_ecp5pll0_locked;

    reg main_pll_stdby = 1'd0;

    (* FREQUENCY_PIN_CLKI = "25.0", FREQUENCY_PIN_CLKOP = "50.0", FREQUENCY_PIN_CLKOS = "50.0", ICP_CURRENT = "6", LPF_RESISTOR = "16", MFG_ENABLE_FILTEROPAMP = "1", MFG_GMCREF_SEL = "2" *)
    EHXPLLL #(
        .CLKFB_DIV(5'd16),
        .CLKI_DIV(1'd1),
        .CLKOP_CPHASE(3'd7),
        .CLKOP_DIV(4'd8),
        .CLKOP_ENABLE("ENABLED"),
        .CLKOP_FPHASE(1'd0),
        .CLKOS2_CPHASE(1'd0),
        .CLKOS2_DIV(1'd1),
        .CLKOS2_ENABLE("ENABLED"),
        .CLKOS2_FPHASE(1'd0),
        .CLKOS_CPHASE(4'd9),
        .CLKOS_DIV(4'd8),
        .CLKOS_ENABLE("ENABLED"),
        .CLKOS_FPHASE(1'd0),
        .FEEDBK_PATH("INT_OS2")
    ) EHXPLLL (
        .CLKI(clk25),
        .RST(rst),
        .STDBY(main_pll_stdby),
        .CLKOP(main_ecp5pll0_clkout0),
        .CLKOS(main_ecp5pll0_clkout1),
        .CLKOS2(builder_basesoc_ecp5pll0_ecp5pll),
        .LOCK(builder_basesoc_ecp5pll0_locked)
    );

    wire user_clk;

    sdram_controller sub
        ( .uart_tx(uart_tx)
        , .uart_rx(uart_rx)
        , .clk(main_ecp5pll0_clkout0)
        , .rst(rst)
        , .sdram_a(sdram_a)
        , .sdram_ba(sdram_ba)
        , .sdram_ras_n(sdram_ras_n)
        , .sdram_cas_n(sdram_cas_n)
        , .sdram_we_n(sdram_we_n)
        , .sdram_cs_n(sdram_cs_n)
        , .sdram_dm(sdram_dm)
        , .sdram_dq(sdram_dq)
        , .sdram_cke(sdram_cke)
        , .init_done(init_done)
        , .init_error(init_error)
        , .user_clk(user_clk)
        , .user_rst(user_rst)
        ##IO_MAPPINGS##
        );



    assign sys_ps_clk = main_ecp5pll0_clkout1;
    ODDRX1F ODDRX1F(
        .D0(1'd1),
        .D1(1'd0),
        .SCLK(sys_ps_clk),
        .Q(sdram_clock)
    );

    assign sys_clk = main_ecp5pll0_clkout0;

endmodule
