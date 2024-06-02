#top = write_cache::write_cache_test_harness

import random
from typing import List, Optional, Tuple
from cocotb.clock import Clock
from spade import FallingEdge, SpadeExt
from cocotb import cocotb

async def fill_buffer(s, camera_clk, start: int, data: List[int]):
    for (i, d) in enumerate(data):
        s.i.write = f"Some({d})"
        await FallingEdge(camera_clk)

    s.i.write = f"None()"

@cocotb.test()
async def test(dut):
    s = SpadeExt(dut) # Wrap the dut in the Spade wrapper

    camera_clk = dut.camera_clk_i

    await cocotb.start(Clock(
        camera_clk,
        period=10,
        units='ns'
    ).start())

    dram_clk = dut.dram_clk_i

    await cocotb.start(Clock(
        dram_clk,
        period=9,
        units='ns'
    ).start())


    s.i.write = "None()"
    s.i.rst = "true"
    s.i.av_waitrequest = "false"
    s.i.is_frame_start = "false"
    [await FallingEdge(camera_clk) for i in range(0, 20)]
    s.i.rst = "false"

    [await FallingEdge(camera_clk) for i in range(0, 5)]

    await cocotb.start(fill_buffer(s, camera_clk, 100, list(range(0, 700))))

    [await FallingEdge(camera_clk) for i in range(0, 512)]
    s.i.av_waitrequest = "true"
    [await FallingEdge(camera_clk) for i in range(0, 20)]
    s.i.av_waitrequest = "false"
    [await FallingEdge(camera_clk) for i in range(0, 512)]


    s.i.is_frame_start = "true"
    await FallingEdge(camera_clk)
    s.i.is_frame_start = "false"
    await cocotb.start(fill_buffer(s, camera_clk, 100, list(range(0, 700))))

    [await FallingEdge(camera_clk) for i in range(0, 1024)]



@cocotb.test()
async def test_with_waitrequest(dut):
    s = SpadeExt(dut) # Wrap the dut in the Spade wrapper

    camera_clk = dut.camera_clk_i

    await cocotb.start(Clock(
        camera_clk,
        period=10,
        units='ns'
    ).start())

    dram_clk = dut.dram_clk_i

    await cocotb.start(Clock(
        dram_clk,
        period=9,
        units='ns'
    ).start())


    s.i.write = "None()"
    s.i.rst = "true"
    s.i.av_waitrequest = "true"
    s.i.is_frame_start = "false"
    [await FallingEdge(camera_clk) for i in range(0, 20)]
    s.i.rst = "false"

    [await FallingEdge(camera_clk) for i in range(0, 5)]

    await cocotb.start(fill_buffer(s, camera_clk, 100, list(range(0, 700))))

    for _ in range(0, 1024):
        await FallingEdge(dram_clk)
        while random.random() < 0.5:
            s.i.av_waitrequest = "true"
            await FallingEdge(dram_clk)
            s.i.av_waitrequest = "false"


    s.i.is_frame_start = "true"
    await FallingEdge(camera_clk)
    s.i.is_frame_start = "false"
    await cocotb.start(fill_buffer(s, camera_clk, 100, list(range(0, 700))))

    [await FallingEdge(camera_clk) for i in range(0, 1024)]



@cocotb.test()
async def long_test(dut):
    s = SpadeExt(dut) # Wrap the dut in the Spade wrapper

    camera_clk = dut.camera_clk_i

    await cocotb.start(Clock(
        camera_clk,
        period=10,
        units='ns'
    ).start())

    dram_clk = dut.dram_clk_i

    await cocotb.start(Clock(
        dram_clk,
        period=9,
        units='ns'
    ).start())


    s.i.write = "None()"
    s.i.rst = "true"
    s.i.av_waitrequest = "false"
    s.i.is_frame_start = "false"
    [await FallingEdge(camera_clk) for i in range(0, 20)]
    s.i.rst = "false"

    [await FallingEdge(camera_clk) for i in range(0, 5)]

    await cocotb.start(fill_buffer(s, camera_clk, 100, list(range(0, 700))))

    [await FallingEdge(camera_clk) for i in range(0, 512)]
    s.i.av_waitrequest = "true"
    [await FallingEdge(camera_clk) for i in range(0, 20)]
    s.i.av_waitrequest = "false"
    [await FallingEdge(camera_clk) for i in range(0, 512)]


    s.i.is_frame_start = "true"
    await FallingEdge(camera_clk)
    s.i.is_frame_start = "false"
    await cocotb.start(fill_buffer(s, camera_clk, 100, list(range(0, 700))))

    [await FallingEdge(camera_clk) for i in range(0, 1024)]
