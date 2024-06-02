// top=hdmi::hdmi_out_impl

#define TOP hdmi_out_impl
#include <verilator_util.hpp>

#define TICK \
    dut->vga_clk_i = 1; \
    dut->dram_clk_i = 1; \
    ctx->timeInc(1); \
    dut->eval(); \
    dut->vga_clk_i = 0; \
    dut->dram_clk_i = 0; \
    ctx->timeInc(1); \
    dut->eval();

TEST_CASE(it_works, {
    for(int y = 0; y < 600; y++) {
        // Kind there are front and back porches which we'll just ignore, simulate around 10 lines
        for (int x = 0; x < 780; x++) {
            TICK
        }
    }
    return 0;
})

MAIN
