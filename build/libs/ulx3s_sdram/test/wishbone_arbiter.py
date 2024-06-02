#top = test::wishbone_arbiter::wb_harness

from cocotb import cocotb
from cocotb.triggers import FallingEdge
from cocotb.clock import Clock
from spade import SpadeExt

@cocotb.test()
async def test(dut):
    clk = dut.clk_i

    s = SpadeExt(dut)
    cocotb.start_soon(Clock(dut.clk_i, 1, "ns").start())

    await FallingEdge(clk)
    s.i.rst = "true"
    await FallingEdge(clk)
    s.i.rst = "false"


    for i in range(0, 300):
        print(s.o.value())
        await FallingEdge(clk)
