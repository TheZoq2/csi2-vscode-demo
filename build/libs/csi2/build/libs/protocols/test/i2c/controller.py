# top=i2c::i2c_controller
from os import environ
import sys
from typing import Any, Tuple

from cocotb.clock import Clock
from cocotb.handle import BinaryValue, Release
from cocotb.types.logic import Logic

sys.path.append(f"{environ['SWIM_ROOT']}/testutil")
from i2c_util import Config, assert_eq, receive_byte

from spade import *

import cocotb
from cocotb.triggers import FallingEdge

async def setup(dut) -> Tuple[SpadeExt, Config, Any]:
    config = Config(12)

    clk = dut.clk_i

    s = SpadeExt(dut)

    await cocotb.start(Clock(clk, period=2).start())

    s.i.rst = "true"
    await FallingEdge(clk)
    s.i.rst = "false"
    s.i.cfg = config.to_spade()
    s.i.command = "None()"
    await FallingEdge(clk)

    return (s, config, clk)


async def do_send(value, clk, s, dut, config):
    out = await receive_byte(clk, dut.sclk, dut.sda, config)
    assert_eq(out, value)

async def stop_bit(clk, dut, config):
    # SCLK should be high for the duration of the stop bit
    # Initially, both SDA and SCLK should be low

    for _ in range(0, config.clk_period // 2):
        assert_eq(dut.sclk.value, False)
        assert_eq(dut.sda.value.binstr, "0")
        await FallingEdge(clk)

    # We now need to pull the clock high but leave SDA low for a few cycles
    # to allow for the clock to stabliize
    for _ in range(0, config.clk_period // 4):
        assert_eq(dut.sclk.value, True)
        assert_eq(dut.sda.value.binstr, "0")
        await FallingEdge(clk)

    # After that, we release SDA as well
    for _ in range(0, config.clk_period // 4):
        assert_eq(dut.sclk.value, True)
        assert_eq(dut.sda.value.binstr, "z")
        await FallingEdge(clk)

async def ack(s: SpadeExt, clk, dut, config, set_ack: bool):
    if set_ack:
        s.i.sda_in = "false"
    for _ in range(0, config.clk_period // 2):
        assert_eq(dut.sclk.value, False)
        # assert_eq(dut.sda.value.binstr, "z")
        await FallingEdge(clk)

    assert_eq(dut.sclk.value, True)

    # This cycle, we expect the ack to be set or not set
    if set_ack:
        s.o.assert_eq("Some(Response::Ack())")
    else:
        s.o.assert_eq("Some(Response::Nack())")

    # assert_eq(dut.sda.value.binstr, "z")
    await FallingEdge(clk)

    for _ in range(0, (config.clk_period // 2) - 1):
        assert_eq(dut.sclk.value, True)
        # assert_eq(dut.sda.value.binstr, "z")
        await FallingEdge(clk)
    s.i.sda_in = "true"

@cocotb.test()
async def writing_with_ack_set_works(dut):
    (s, config, clk) = await setup(dut)

    # Without a command, nothing happens
    for _ in range(0, config.clk_period // 2):
        assert_eq(dut.sclk.value, True)
        assert_eq(dut.sda.value.binstr, "z")
        await FallingEdge(clk)


    s.i.command = f"""
    Some(Command::Write$(
        device: 0b1100_101u,
        addr: 0b1111_0000u,
        byte: 0b0000_1111
    ))"""
    await FallingEdge(clk)
    s.i.command = "None()"

    # Start bit
    for _ in range(0, config.clk_period):
        assert_eq(dut.sclk.value, True)
        assert_eq(dut.sda.value.binstr, "0")
        await FallingEdge(clk)

    # Due to FSM synchronisation, we have an additional cycle where the trasmitter
    # is transmitting a start bit
    await FallingEdge(clk)

    out = await receive_byte(clk, dut.sclk, dut.sda, config)
    assert_eq(out, 0b1100_1010)
    await ack(s, clk, dut, config, True)

    out = await receive_byte(clk, dut.sclk, dut.sda, config)
    assert_eq(out, 0b1111_0000)
    await ack(s, clk, dut, config, True)
    out = await receive_byte(clk, dut.sclk, dut.sda, config)
    assert_eq(out, 0b0000_1111)
    await ack(s, clk, dut, config, True)

    await stop_bit(clk, dut, config)

# @cocotb.test()
# async def writing_with_no_ack_aborts(dut):
#     (s, config, clk) = await setup(dut)
# 
#     s.i.command = f"""
#     Some(Command::Write$(
#         device: 0b1100_101u,
#         addr: 0b1111_0000u,
#         byte: 0b0000_1111
#     ))"""
#     await FallingEdge(clk)
#     s.i.command = "None()"
# 
#     # Start bit
#     for _ in range(0, config.clk_period):
#         assert_eq(dut.sclk.value, True)
#         assert_eq(dut.sda.value.binstr, "0")
#         await FallingEdge(clk)
# 
#     # Due to FSM synchronisation, we have an additional cycle where the trasmitter
#     # is transmitting a start bit
#     await FallingEdge(clk)
# 
#     out = await receive_byte(clk, dut.sclk, dut.sda, config)
#     assert_eq(out, 0b1100_1010)
#     await ack(s, clk, dut, config, False)
# 
#     # If there is no ack on the transmission, we should send a stop bit and abort
