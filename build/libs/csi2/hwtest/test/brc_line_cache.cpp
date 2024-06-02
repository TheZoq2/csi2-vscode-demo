// top=block_read_cache::brc_line_cache_th

#include <array>
#include <cstddef>
#include <cstdint>
#include <deque>
#include <format>
#include <stdexcept>
#define TOP brc_line_cache_th
#include <verilator_util.hpp>

struct BurstData {
  size_t start;
  size_t count;
  size_t offset;
};

template <typename T> uint32_t field_to_uint(const T &field) {
  std::string str = field->spade_repr();
  try {
    return std::stoll(str, 0, 10);
  } catch (const std::out_of_range &e) {
    throw std::runtime_error(
        std::format("Failed to convert {} to int. {}", str, e.what()));
  } catch (const std::invalid_argument &e) {
    throw std::runtime_error(
        std::format("Failed to convert {} to int. {}", str, e.what()));
  }
}

class AvalonReadWrapper {
public:
  void tick(verilator_util::spade_wrapper &s) {
    if ((*s.o->read) == "true") {
      for (int i = 0; i < 64; i++) {
        int addr = field_to_uint(s.o->address) + i;
        // std::cout << "Pushing " << addr << " into read queue from a request
        // for " << field_to_uint(s.o->address) << std::endl;
        read_commands.push_back(addr);
      }
    }

    if (read_commands.size() > 0) {
      auto addr = read_commands.front();
      auto val = content[addr];
      read_commands.pop_front();
      // std::cout << std::format("Responding to {} with 0x{:x}", addr, val)
      //           << std::endl;
      s.i->readdata = std::format("{}", val);
      s.i->readdatavalid = std::format("true");
    } else {
      s.i->readdata = std::format("0");
      s.i->readdatavalid = std::format("false");
    }
  }

  static constexpr size_t size = 1024 * 600;
  std::array<uint16_t, size> content;

  std::deque<size_t> read_commands;
};

#define TICK_BOTH                                                              \
  ctx->timeInc(1);                                                             \
  dut->eval();                                                                 \
  ctx->timeInc(1);                                                             \
  dut->pixel_clk_i = 1;                                                        \
  dut->dram_clk_i = 1;                                                         \
  dut->eval();                                                                 \
  ctx->timeInc(1);                                                             \
  dut->pixel_clk_i = 0;                                                        \
  dut->dram_clk_i = 0;                                                         \
  dut->eval();                                                                 \
  ctx->timeInc(1);                                                             \
  avalon.tick(s);

TEST_CASE(it_works, {
  // Your test code here
  auto avalon = AvalonReadWrapper();

  s.i->rst = "true";
  TICK_BOTH
  TICK_BOTH
  TICK_BOTH
  TICK_BOTH
  TICK_BOTH
  s.i->rst = "false";

  auto memory_value = [](uint16_t x, uint16_t y) {
    return (uint16_t) (((x << 8) & 0xff00) + (y & 0xff));
  };
  for (int by = 0; by < 600 / 8; by++) {
    for (int bx = 0; bx < 32 / 8; bx++) {
      for (int iy = 0; iy < 8; iy++) {
        for (int ix = 0; ix < 8; ix++) {
          auto block_start = bx * 64 + by * 1024 * 8;
          auto block_inner = ix + iy * 8;

          auto addr = block_start + block_inner;
          auto x = bx + ix;
          auto y = by + iy;
          auto val = memory_value(bx*8 + ix, by*8 + iy);
          std::cout << std::format("Writing 0x{:x} to {} from ({}, {})", val, addr, x, y) << std::endl;
          avalon.content[addr] = val;
        }
      }
    }
  }

  // In the first block, put a small square of known data
  // avalon.content[0] = 0;
  // avalon.content[1] = 1;
  // avalon.content[2] = 2;

  // avalon.content[8 + 0] = 3;
  // avalon.content[8 + 1] = 4;
  // avalon.content[8 + 2] = 5;

  // avalon.content[16 + 0] = 6;
  // avalon.content[16 + 1] = 7;
  // avalon.content[16 + 2] = 8;

  s.i->start_fetch = "Some(0)";
  TICK_BOTH
  s.i->start_fetch = "None";

  // Do the fetch
  for (int i = 0; i < 1024 * 8; i++) {
    TICK_BOTH
  }
  // Do some more to avoid edge cases
  for (int i = 0; i < 10; i++) {
    TICK_BOTH
  }

  // Read the content at the expected position
  // s.i->read_addrs = "[[0, 1, 2], [1024, 1025, 1026], [2048, 2049, 2050]]";
  // TICK_BOTH
  // ASSERT_EQ(s.o->read_result, "[[0, 1, 2], [3, 4, 5], [6, 7, 8]]");

  // Also ensure that the center is correct in a bunch of points

  auto read_addr = [](int x, int y) { return x + 1024 * y; };

  for (int x = 1; x < 15; x++) {
    for (int y = 1; y < 7; y++) {
      s.i->read_addrs = std::format(
        "[[{}, {}, {}], [{}, {}, {}], [{}, {}, {}]]",
        read_addr(x - 1, y - 1),
        read_addr(x, y - 1),
        read_addr(x + 1, y - 1),
        read_addr(x - 1, y),
        read_addr(x, y),
        read_addr(x + 1, y),
        read_addr(x - 1, y + 1),
        read_addr(x, y + 1),
        read_addr(x + 1, y + 1)
      );
      TICK_BOTH
      ASSERT_EQ(s.o->read_result,
                std::format(
                  "[[{}, {}, {}], [{}, {}, {}], [{}, {}, {}]]",
                  memory_value(x - 1, y - 1),
                  memory_value(x, y - 1),
                  memory_value(x + 1, y - 1),
                  memory_value(x - 1, y),
                  memory_value(x, y),
                  memory_value(x + 1, y),
                  memory_value(x - 1, y + 1),
                  memory_value(x, y + 1),
                  memory_value(x + 1, y + 1)
                ))
      TICK_BOTH
    }
  }


  // Check to make sure it works on non-zero base addresses
  s.i->start_fetch = std::format("Some({})", 1024*8);
  TICK_BOTH
  s.i->start_fetch = "None";

  // Do the fetch
  for (int i = 0; i < 1024 * 8; i++) {
    TICK_BOTH
  }
  // Do some more to avoid edge cases
  for (int i = 0; i < 10; i++) {
    TICK_BOTH
  }


  for (int x = 1; x < 15; x++) {
    for (int y_local = 1; y_local < 7; y_local++) {
      auto y = y_local + 8;
      s.i->read_addrs = std::format(
        "[[{}, {}, {}], [{}, {}, {}], [{}, {}, {}]]",
        read_addr(x - 1, y_local - 1),
        read_addr(x, y_local - 1),
        read_addr(x + 1, y_local - 1),
        read_addr(x - 1, y_local),
        read_addr(x, y_local),
        read_addr(x + 1, y_local),
        read_addr(x - 1, y_local + 1),
        read_addr(x, y_local + 1),
        read_addr(x + 1, y_local + 1)
      );
      TICK_BOTH
      ASSERT_EQ(s.o->read_result,
                std::format(
                  "[[{}, {}, {}], [{}, {}, {}], [{}, {}, {}]]",
                  memory_value(x - 1, y - 1),
                  memory_value(x, y - 1),
                  memory_value(x + 1, y - 1),
                  memory_value(x - 1, y),
                  memory_value(x, y),
                  memory_value(x + 1, y),
                  memory_value(x - 1, y + 1),
                  memory_value(x, y + 1),
                  memory_value(x + 1, y + 1)
                ))
      TICK_BOTH
    }
  }

  return 0;
})

MAIN
