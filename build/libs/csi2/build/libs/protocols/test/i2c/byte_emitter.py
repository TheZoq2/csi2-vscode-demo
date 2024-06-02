#top = i2c::byte_emitter

from os import environ
import sys
from typing import Any, Tuple

from cocotb.clock import Clock
from cocotb.handle import BinaryValue
from cocotb.types.logic import Logic

sys.path.append(f"{environ['SWIM_ROOT']}/testutil")
from i2c_util import Config, assert_eq, receive_byte

from spade import *

import cocotb
from cocotb.triggers import FallingEdge

async def setup(dut) -> Tuple[SpadeExt, Config, Any]:
    config = Config(10)

    clk = dut.clk_i

    s = SpadeExt(dut)

    await cocotb.start(Clock(clk, period=2).start())

    s.i.rst = "true"
    await FallingEdge(clk)
    s.i.rst = "false"
    s.i.byte = "None()"
    s.i.cfg = config.to_spade()
    await FallingEdge(clk)

    return (s, config, clk)

async def do_send(value, clk, s, dut, config):
    s.i.byte = f"Some({value}u)"
    await FallingEdge(clk)
    s.i.byte = "None()"

    out = await receive_byte(clk, dut.sclk, dut.sda, config)
    assert_eq(out, value)



@cocotb.test()
async def it_works(dut):
    (s, config, clk) = await setup(dut)

    await do_send(0b1100_1010, clk, s, dut, config)

    # Next should be an ack 
    for _ in range(0, config.clk_period // 2):
        assert_eq(dut.sclk.value, False)
        assert_eq(dut.sda.value.binstr, "z")
        await FallingEdge(clk)

    # Next should be an ack 
    for _ in range(0, config.clk_period // 2):
        assert_eq(dut.sclk.value, True)
        assert_eq(dut.sda.value.binstr, "z")
        await FallingEdge(clk)


    # Following that, there should be no more activity
    for _ in range(0, 5):
        assert dut.sclk.value == True
        assert dut.sda.value.binstr == "z"
        assert dut.ready.value == True
        await FallingEdge(clk)

