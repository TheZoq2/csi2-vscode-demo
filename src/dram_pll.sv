`default_nettype none

module dram_pll(
    input  wire          clk25,
    input wire           rst,
    output[1:0]          output__
);
    wire main_ecp5pll0_clkout0;
    wire main_ecp5pll0_clkout1;

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
        .CLKOP(main_ecp5pll0_clkout0),
        .CLKOS(main_ecp5pll0_clkout1),
        .CLKFB(),
        .PHASESEL1(),
        .PHASESEL0(),
        .PHASEDIR(),
        .PHASESTEP(),
        .PHASELOADREG(),
        .STDBY(),
        .PLLWAKESYNC(),
        .ENCLKOP(),
        .ENCLKOS(),
        .ENCLKOS2(),
        .ENCLKOS3(),
        .CLKOS2(),
        .CLKOS3(),
        .LOCK(),
        .INTLOCK(),
        .REFCLK(),
        .CLKINTFB()
    );

    assign output__ = {main_ecp5pll0_clkout0, main_ecp5pll0_clkout1};

endmodule
