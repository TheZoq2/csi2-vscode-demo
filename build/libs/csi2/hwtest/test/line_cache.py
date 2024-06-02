#top = line_cache::line_cache_test_harness

from typing import Optional, Tuple
from cocotb.clock import Clock
from spade import FallingEdge, SpadeExt
from cocotb import cocotb

class ReadRequest:
    def __init__(self, start_addr: int, count: int, latency: int):
        self.started = False
        self.start_addr = start_addr
        self.count = count
        self.latency = latency

        print(f"Initializing read at {start_addr}")

    def start(self, start_time: int):
        self.start_time = start_time
        self.started = True


    # Step one cycle, returning the address that would be read this particular cycle
    def step_cycle(self, cycle_num: int) -> Tuple[Optional[int], bool]:
        offset = cycle_num - (self.start_time + self.latency)
        if offset >= self.count:
            return (None, True)
        if offset >= 0:
            print(f"- Reading at {self.start_addr + offset}")
            return (self.start_addr + offset, False)
        return (None, False)


async def avalon_read_bus(
    data_gen,

    initial_latency,

    clk,
    address,
    burstcount,
    byteenable, # Ignored here
    read,
    readdata,
    readdatavalid,
    waitrequest,
):
    waitrequest.value = False
    cc = 0;
    read_requests = []
    while True:
        print(len(read_requests))
        await FallingEdge(clk)

        if read == 1:
            read_requests.append(ReadRequest(int(address), int(burstcount), initial_latency))

        if len(read_requests) != 0:
            if not read_requests[0].started:
                read_requests[0].start(cc)
            (read_addr, done) = read_requests[0].step_cycle(cc)
            if done:
                read_requests.pop(0)
            if not read_addr is None:
                readdata.value = data_gen(read_addr)
                readdatavalid.value = True
            else:
                readdatavalid.value = False
        cc += 1




@cocotb.test()
async def test(dut):
    s = SpadeExt(dut) # Wrap the dut in the Spade wrapper

    vga_clk = dut.vga_clk_i

    await cocotb.start(Clock(
        vga_clk,
        period=10,
        units='ns'
    ).start())

    dram_clk = dut.dram_clk_i

    await cocotb.start(Clock(
        dram_clk,
        period=9,
        units='ns'
    ).start())

    s.i.rst = "true";
    # Make sure both clocks have triggered before starting the avalon signals
    await FallingEdge(vga_clk)
    await FallingEdge(dram_clk)
    await cocotb.start(avalon_read_bus(
        lambda addr: addr,
        10,
        dram_clk,
        dut.av0_address,
        dut.av0_burstcount,
        dut.av0_byteenable,
        dut.av0_read,
        dut.av0_readdata,
        dut.av0_readdatavalid,
        dut.av0_waitrequest,
    ))

    await cocotb.start(avalon_read_bus(
        lambda addr: addr * 2,
        10,
        dram_clk,
        dut.av1_address,
        dut.av1_burstcount,
        dut.av1_byteenable,
        dut.av1_read,
        dut.av1_readdata,
        dut.av1_readdatavalid,
        dut.av1_waitrequest,
    ))

    [await FallingEdge(vga_clk) for _ in range(0, 5)];
    s.i.rst = "false";

    s.i.line = "Some(LineCacheCommand$(y: 10, width: 640))"
    await FallingEdge(vga_clk)
    s.i.line = "None()"

    [await FallingEdge(vga_clk) for _ in range(0, 100)];

    for i in range(0, 640):
        s.i.read_addr = f"{i}";
        await FallingEdge(vga_clk)
        s.o.assert_eq(f"{640 * 10 + i}")

    await FallingEdge(vga_clk)
    s.i.line = "Some(LineCacheCommand$(y: 10, width: 640))"
    await FallingEdge(vga_clk)
    s.i.line = "None()"

    [await FallingEdge(vga_clk) for _ in range(0, 20)];

    for i in range(0, 640):
        s.i.read_addr = f"{i}";
        await FallingEdge(vga_clk)
        s.o.assert_eq(f"{(640 * 10 + i)*2}")


    [await FallingEdge(vga_clk) for _ in range(0, 100)];


    # s.i.a = "2"
    # s.i.b = "3"
    # await FallingEdge(clk)
    # s.o.sum.assert_eq("5")
    # s.o.product.assert_eq("6")
