#top = test::axi_read_test::read_harness
from cocotb import cocotb
from cocotb.triggers import FallingEdge
from cocotbext.axi import AxiBus, AxiRam
from cocotbext.axi.axi_channels import define_stream
from cocotb.clock import Clock
from spade import SpadeExt

async def wait_read(clk, s: SpadeExt, expected: str, timeout: int):
    cycles = 0
    while True:
        if not s.o.is_eq("None()"):
            break

        if cycles == timeout:
            raise Exception("Did not get any read data back")
        await FallingEdge(clk)
        cycles += 1

    print(f"Got read response after {cycles} cycles");
    # s.o.assert_eq(expected)

@cocotb.test()
async def test(dut):
    bus = AxiBus.from_prefix(dut, "")
    ram = AxiRam(bus, dut.clk, size=2**10)

    clk = dut.clk_i

    s = SpadeExt(dut)
    cocotb.start_soon(Clock(dut.clk_i, 1, "ns").start())

    ram.write_word(0, 0xbad)
    ram.write_word(2, 0xdead)

    # Reset state machines
    s.i.rst = "true"
    await FallingEdge(dut.clk_i)
    await FallingEdge(dut.clk_i)
    s.i.rst = "false"

    s.i.read_addr = "Some(2)";
    await FallingEdge(dut.clk_i)
    s.i.read_addr = "None()"
    await wait_read(clk, s, "Some(0xdead)", 10)
    await FallingEdge(clk)


    s.i.read_addr = "Some(0)";
    await FallingEdge(dut.clk_i)
    s.i.read_addr = "None()";
    await wait_read(clk, s, "Some(0xbad)", 10)
    await FallingEdge(clk)
