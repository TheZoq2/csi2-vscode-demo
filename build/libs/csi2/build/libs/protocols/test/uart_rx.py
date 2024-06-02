#top=uart::uart_rx

from spade import *

from cocotb.clock import Clock
from cocotb.triggers import ClockCycles

BIT_TIME=10

async def set_bit(s, clk, value):
    print(f"Setting bit {value}")
    s.i.rx = "true" if value else "false"
    await ClockCycles(clk, BIT_TIME, rising=False)

# Checks that the specified dat has been received within BIT_TIME
async def ensure_received(s: SpadeExt, clk, expected: str):
    print("Running ensure received")
    seen_result = False
    for _ in range(0, BIT_TIME):
        if seen_result:
            s.o.assert_eq("UartOut::None()")
        if not s.o.is_eq("UartOut::None()"):
            s.o.assert_eq(f"{expected}")
            seen_result = True
        await FallingEdge(clk)

    assert seen_result


# Drives the tx line with the specified bits one by one. If the parity bit is used,
# the 8 bits are transmitted, then a coroutine is started which ensures that the bytes
# have been received within ine BIT_TIME
# If parity is not used, the bits are set, and the result is checked
# correct_parity is true if the parity should be correct for this transmission, otherwise false
async def with_data(s: SpadeExt, clk, expected, correct_parity: bool, use_parity_bit=False):
    assert len(expected) == 8
    for i in range(7, 0, -1) if not use_parity_bit else range(7, -1, -1):
        await set_bit(s, clk, int(expected[i]))

    if correct_parity:
        await cocotb.start(ensure_received(s, clk, f"protocols::uart::UartOut::Ok(0b{expected})"))
    else:
        await cocotb.start(ensure_received(s, clk, f"protocols::uart::UartOut::ParityError(0b{expected})"))

    if not use_parity_bit:
        await set_bit(s, clk, int(expected[0]))


async def init_test(dut, stop_bits=None, parity=None) -> (SpadeExt, any):
    s = SpadeExt(dut)

    clk = dut.clk_i
    await cocotb.start(Clock(clk, 1, units = 'ns').start())

    s.i.rst = "true"
    await FallingEdge(clk);
    await FallingEdge(clk);
    s.i.rst = "false"
    s.i.rx = "true"

    s.i.config = f"UartConfig$(bit_time: {BIT_TIME}, stop_bits: {stop_bits}, parity: {parity})"

    # Ensure we don't receive any bits without a start bit sent
    for _ in range(0, 12):
        for _ in range(0, BIT_TIME):
            await FallingEdge(clk)
            s.o.assert_eq("UartOut::None()")

    # Start bit
    await set_bit(s, clk, 1)

    return (s, clk)



@cocotb.test()
async def test(dut):
    (s, clk) = await init_test(dut, stop_bits=1, parity="false")
    await set_bit(s, clk, 0)

    # Data
    await with_data(s, clk, "00001010", True)

    # End bits
    await set_bit(s, clk, 1)

    await set_bit(s, clk, 1)
    await set_bit(s, clk, 1)


@cocotb.test()
async def quick_succession_works(dut):
    (s, clk) = await init_test(dut, stop_bits=1, parity="false")

    # Start bit
    await set_bit(s, clk, 1)
    await set_bit(s, clk, 0)

    # Data
    await with_data(s, clk, "00001010", True)

    # End bits
    await set_bit(s, clk, 1)

    await set_bit(s, clk, 0)
    await with_data(s, clk, "00101010", True)

    await set_bit(s, clk, 1)


@cocotb.test()
async def correct_parity(dut):
    (s, clk) = await init_test(dut, stop_bits=1, parity="true")

    # Start bit
    await set_bit(s, clk, 1)
    await set_bit(s, clk, 0)

    # Data
    await with_data(s, clk, "00001010", True, use_parity_bit=True)

    # End bits
    await set_bit(s, clk, 0) # Parity
    await set_bit(s, clk, 1) # Stop

    await set_bit(s, clk, 0)
    await with_data(s, clk, "00101010", True, use_parity_bit=True)

    await set_bit(s, clk, 1) # Parity
    await set_bit(s, clk, 1) # stop



@cocotb.test()
async def incorrect_parity(dut):
    (s, clk) = await init_test(dut, stop_bits=1, parity="true")

    # Start bit
    await set_bit(s, clk, 1)
    await set_bit(s, clk, 0)

    # Data
    await with_data(s, clk, "00001010", False, use_parity_bit=True)

    # End bits
    await set_bit(s, clk, 1) # Parity
    await set_bit(s, clk, 1) # Stop

    await set_bit(s, clk, 0)
    await with_data(s, clk, "00101010", False, use_parity_bit=True)

    await set_bit(s, clk, 0) # Parity
    await set_bit(s, clk, 1) # stop


@cocotb.test()
async def multiple_stop_bits_work(dut):
    (s, clk) = await init_test(dut, stop_bits=2, parity="false")

    # Start bit
    await set_bit(s, clk, 1)
    await set_bit(s, clk, 0)

    # Data
    await with_data(s, clk, "00001010", True, use_parity_bit=False)

    # Stop bit
    await set_bit(s, clk, 0) # Stop
    await set_bit(s, clk, 1) # Stop

    # Ensure that we don't have any rogue receives
    for _ in range(0, 12):
        for _ in range(0, BIT_TIME):
            await FallingEdge(clk)
            s.o.assert_eq("UartOut::None()")

