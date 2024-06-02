#top=test::uart_loopback

from spade import *

from cocotb.clock import Clock
from cocotb.triggers import ClockCycles

BIT_TIME=10

async def check_next_bit(s: SpadeExt, clk, set):
    [await FallingEdge(clk) for _ in range(0, BIT_TIME)]
    s.o.tx.assert_eq("true" if set else "false")


async def init_test(dut, stop_bits=None, parity=None) -> (SpadeExt, any):
    s = SpadeExt(dut)

    clk = dut.clk_i
    await cocotb.start(Clock(clk, 1, units = 'ns').start())

    s.i.config = f"UartConfig$(bit_time: {BIT_TIME}, stop_bits: {stop_bits}, parity: {parity})"

    s.i.to_transmit = "None()"
    s.i.rst = "true"
    await FallingEdge(clk);
    await FallingEdge(clk);
    s.i.rst = "false"

    return (s, clk)

async def run_test(dut, stop_bits: int, parity: bool):
    (s, clk) = await init_test(dut, stop_bits=stop_bits, parity="true" if parity else "false")

    for i in range(0, 255):
        s.i.to_transmit = f"Some({i}u)"
        await FallingEdge(clk)
        s.i.to_transmit = "None()"

        # +10 for some extra padding
        [await FallingEdge(clk) for _ in range(0, BIT_TIME * (8 + 1 + stop_bits + parity + 10))]

        s.o.assert_eq(f"protocols::uart::UartOut::Ok({i}u)")


@cocotb.test()
async def no_parity_one_stop(dut):
    await run_test(dut, 1, False)


@cocotb.test()
async def no_parity_two_stop(dut):
    await run_test(dut, 2, False)

@cocotb.test()
async def parity_one_stop(dut):
    await run_test(dut, 1, True)

@cocotb.test()
async def parity_two_stop(dut):
    await run_test(dut, 2, True)





