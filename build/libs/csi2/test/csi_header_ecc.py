#top = ecc::csi_header_ecc

from cocotb.clock import Clock
from cocotb.triggers import Timer
from spade import FallingEdge, SpadeExt
from cocotb import cocotb

@cocotb.test()
async def test(dut):
    s = SpadeExt(dut) # Wrap the dut in the Spade wrapper

    # To access unmangled signals as cocotb values (without the spade wrapping) use
    # <signal_name>_i
    # For cocotb functions like the clock generator, we need a cocotb value

    # The ECC from the datasheet
    s.i.data = "0x01f037";
    await Timer(1.0, units="ns")
    s.o.assert_eq("0x3f")
