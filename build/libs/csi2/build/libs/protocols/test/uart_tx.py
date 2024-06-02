#top=uart::uart_tx

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

    s.i.transmit = "None()"
    s.i.rst = "true"
    await FallingEdge(clk);
    await FallingEdge(clk);
    s.i.rst = "false"

    s.i.config = f"UartConfig$(bit_time: {BIT_TIME}, stop_bits: {stop_bits}, parity: {parity})"

    return (s, clk)

# Starts a transmission, check that the start bit and transmitted bits are set correctly.
# Leaves the time at the center of the last bit
async def check_transmission(clk, s: SpadeExt, to_transmit: str):
    to_transmit = to_transmit.replace("_", "")
    s.i.transmit = f"Some(0b{to_transmit})"
    s.o.tx.assert_eq("true")
    s.o.ready.assert_eq("true")

    await FallingEdge(clk)
    s.i.transmit = "None()"
    s.o.ready.assert_eq("false")
    # Start bit
    s.o.tx.assert_eq("false")

    [await FallingEdge(clk) for _ in range(0, BIT_TIME//2)]
    # Start bit should still be false
    s.o.tx.assert_eq("false")

    # Data bits
    for i in range(7, -1, -1):
        print(f"Expecting bit [{i}] = {to_transmit[i]}")
        await check_next_bit(s, clk, to_transmit[i] == '1')


@cocotb.test()
async def simple_tx_test(dut):
    (s, clk) = await init_test(dut, stop_bits=1, parity="false")

    await check_transmission(clk, s, "0011_0101")

    # Stop bit
    await check_next_bit(s, clk, 1)

    [await FallingEdge(clk) for _ in range(0, BIT_TIME//2)]

    s.o.tx.assert_eq("true")
    s.o.ready.assert_eq("true")





@cocotb.test()
async def simple_tx_test_with_2_stop_bits(dut):
    (s, clk) = await init_test(dut, stop_bits=2, parity="false")

    await check_transmission(clk, s, "0011_0101")

    # Stop bit
    await check_next_bit(s, clk, 1)
    await check_next_bit(s, clk, 1)

    [await FallingEdge(clk) for _ in range(0, BIT_TIME//2)]
    s.o.tx.assert_eq("true")
    s.o.ready.assert_eq("true")



@cocotb.test()
async def even_parity_bit_works(dut):
    (s, clk) = await init_test(dut, stop_bits=1, parity="true")

    await check_transmission(clk, s, "0011_0101")

    # Parity bits
    await check_next_bit(s, clk, 0)

    # Stop bit
    await check_next_bit(s, clk, 1)

    [await FallingEdge(clk) for _ in range(0, BIT_TIME//2)]
    s.o.tx.assert_eq("true")
    s.o.ready.assert_eq("true")



@cocotb.test()
async def odd_parity_bit_works(dut):
    (s, clk) = await init_test(dut, stop_bits=1, parity="true")

    await check_transmission(clk, s, "0111_0101")

    # Parity bits
    await check_next_bit(s, clk, 1)

    # Stop bit
    await check_next_bit(s, clk, 1)

    [await FallingEdge(clk) for _ in range(0, BIT_TIME//2)]
    s.o.tx.assert_eq("true")
    s.o.ready.assert_eq("true")


@cocotb.test()
async def even_parity_bit_with_multiple_stop_bit_works(dut):
    (s, clk) = await init_test(dut, stop_bits=2, parity="true")

    await check_transmission(clk, s, "0011_0101")

    # Parity bits
    await check_next_bit(s, clk, 0)

    # Stop bit
    await check_next_bit(s, clk, 1)
    await check_next_bit(s, clk, 1)

    [await FallingEdge(clk) for _ in range(0, BIT_TIME//2)]
    s.o.tx.assert_eq("true")
    s.o.ready.assert_eq("true")
