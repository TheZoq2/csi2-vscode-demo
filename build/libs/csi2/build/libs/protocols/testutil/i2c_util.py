from typing import Callable

from cocotb.triggers import FallingEdge

def assert_eq(lhs, rhs):
    if lhs != rhs:
        assert False, f"{lhs} != {rhs}"


class Config:
    def __init__(self, clk_period):
        self.clk_period = clk_period

    def to_spade(self) -> str:
        return f"I2CConfig$(clk_period: {self.clk_period})"


async def receive_byte(sysclk, sclk, sda, cfg: Config) -> int:
    result = 0
    for _ in range(0, 8):
        for _ in range(0, cfg.clk_period // 2):
            assert_eq(sclk.value, 0)
            await FallingEdge(sysclk)

        value = sda.value.binstr
        assert value in ["0", "z"]

        print(value)
        if value == "0":
            result = result << 1
        else:
            result = (result << 1) | 1

        for _ in range(0, cfg.clk_period // 2):
            assert_eq(sclk.value, 1)
            # Not allowed to change values on the high side of the clock
            assert_eq(sda.value.binstr, value)
            await FallingEdge(sysclk)

    return result
