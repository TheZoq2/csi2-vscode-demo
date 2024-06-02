#top = ecc::apply_header_ecc

from typing import Any
from cocotb.clock import Clock
from cocotb.triggers import Timer
from spade import FallingEdge, List, SpadeExt
from cocotb import cocotb

def list_to_spade(l: List[Any]) -> str:
    inner = ", ".join(map(lambda d: f'0x{d:x}u', l))
    return f"[{inner}]"

@cocotb.test()
async def test(dut):
    s = SpadeExt(dut) # Wrap the dut in the Spade wrapper

    # To access unmangled signals as cocotb values (without the spade wrapping) use
    # <signal_name>_i
    # For cocotb functions like the clock generator, we need a cocotb value

    # The ECC from the datasheet
    input_data = [0x37, 0xf0, 0x01];

    s.i.data = f"{list_to_spade(input_data)}";
    s.i.in_ecc = "0x3F";

    await Timer(1.0, units="ns")
    s.o.data.assert_eq(f"{list_to_spade(input_data)}")
    s.o.error.assert_eq("false")
    s.o.applied_correction.assert_eq("false")


    for byte in range(0, 3):
        for bit in range(0, 8):
            new_input_data = list(map(lambda i: i, input_data))
            new_input_data[byte] ^= (1 << bit)

            s.i.data = f"{list_to_spade(new_input_data)}";
            s.i.in_ecc = "0x3F";

            await Timer(1.0, units="ns")
            s.o.data.assert_eq(f"{list_to_spade(input_data)}")
            s.o.error.assert_eq("false")
            s.o.applied_correction.assert_eq("true")
