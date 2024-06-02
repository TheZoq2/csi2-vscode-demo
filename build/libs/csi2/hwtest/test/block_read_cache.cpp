// top=block_read_cache::brc_block_read_cache_th

#include <array>
#include <cstddef>
#include <cstdint>
#include <deque>
#include <format>
#include <stdexcept>
#define TOP brc_block_read_cache_th
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

template <typename Read, typename Control> class AvalonReadWrapper {
public:
  void tick(Read read, Control control) {
    if ((*read->read) == "true") {
      for (int i = 0; i < 64; i++) {
        int addr = field_to_uint(read->address) + i;
        // std::cout << "Pushing " << addr << " into read queue from a request for "
        //   << field_to_uint(read->address) << std::endl;
        read_commands.push_back(addr);
      }
    }

    if (read_commands.size() > 0) {
      auto addr = read_commands.front();
      read_commands.pop_front();
      auto val = content[addr];
      std::cout << std::format("Responding to {} with 0x{:x}", addr, val)
                << std::endl;
      control =
          std::format("AvalonReadIn$(readdata: {}, readdatavalid: true)", val);
    } else {
      control = std::format("AvalonReadIn$(readdata: 0, readdatavalid: false)");
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
  av0.tick(s.o->av0_read, s.i->av0in);                                         \
  av1.tick(s.o->av1_read, s.i->av1in);                                         \
  av2.tick(s.o->av2_read, s.i->av2in);                                         \
  av3.tick(s.o->av3_read, s.i->av3in);

TEST_CASE(it_works, ({
  return [&]() {
    AvalonReadWrapper<brc_block_read_cache_th_spade_t_o_av0_read *,
                      brc_block_read_cache_th_spade_t_i_av0in>
        av0;
    AvalonReadWrapper<brc_block_read_cache_th_spade_t_o_av1_read *,
                      brc_block_read_cache_th_spade_t_i_av1in>
        av1;
    AvalonReadWrapper<brc_block_read_cache_th_spade_t_o_av2_read *,
                      brc_block_read_cache_th_spade_t_i_av2in>
        av2;
    AvalonReadWrapper<brc_block_read_cache_th_spade_t_o_av3_read *,
                      brc_block_read_cache_th_spade_t_i_av3in>
        av3;

    auto memory_value = [](uint16_t x, uint16_t y) {
      return (((x << 8) & 0xff00) + (y & 0xff));
    };

    for (int by = 0; by < 600 / 8; by++) {
      for (int bx = 0; bx < 32 / 8; bx++) {
        for (int iy = 0; iy < 8; iy++) {
          for (int ix = 0; ix < 8; ix++) {
            auto block_start = bx * 64 + by * 512 * 8;
            auto block_inner = ix + iy * 8;

            auto addr = block_start + block_inner;
            auto x = bx + ix;
            auto y = by + iy;
            auto val = memory_value(bx * 8 + ix, by * 8 + iy);
            std::cout
                << std::format("Writing 0x{:x} to {} from ({}, {})",
                               val, addr, x, y)
                << std::endl;
            av0.content[addr] = val;
            av1.content[addr] = val;
            av2.content[addr] = val;
            av3.content[addr] = val;
          }
        }
      }
    }

    s.i->rst = "true";
    s.i->image_height = "600";
    s.i->pixel_read_addr = "None";
    s.i->xblocks_to_fetch = "64";
    TICK_BOTH
    TICK_BOTH
    TICK_BOTH
    TICK_BOTH
    TICK_BOTH
    TICK_BOTH
    s.i->rst = "false";

    // The first 5 lines will be wrong because the caches will not be
    // full yet.
    int valid_lines_start = 8 * 5;
    for (int y = 0; y < valid_lines_start; y++) {
      std::cout << y << std::endl;
      for (int x = 0; x < 512; x++) {
        // We run at half frequency because this assumes to not be
        // 100% untilized For performance problem reasons, we'll only
        // run with different y values since the performance problems
        // stem from constantly re-compiling this thing
        s.i->pixel_read_addr = std::format("Some((0, {}))", y);
        TICK_BOTH
        TICK_BOTH
      }
    }

    // Make sure that all 4 caches work
    for (int y = valid_lines_start; y < valid_lines_start + 48; y++) {
      // The very edges have edge cases, we don't care about the
      // behaviour there
      for (int x = 1; x < 10; x++) {
        // We run at half frequency because this assumes to not be
        // 100% untilized
        s.i->pixel_read_addr = std::format("Some(({}, {}))", x, y);
        TICK_BOTH
        // We should have the result now
        ASSERT_EQ(
            s.o->read_result,
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
            ));
        TICK_BOTH
      }
    }

    return 0;
  }();
});)


TEST_CASE(wraparound_works, ({
  return [&]() {
    AvalonReadWrapper<brc_block_read_cache_th_spade_t_o_av0_read *,
                      brc_block_read_cache_th_spade_t_i_av0in>
        av0;
    AvalonReadWrapper<brc_block_read_cache_th_spade_t_o_av1_read *,
                      brc_block_read_cache_th_spade_t_i_av1in>
        av1;
    AvalonReadWrapper<brc_block_read_cache_th_spade_t_o_av2_read *,
                      brc_block_read_cache_th_spade_t_i_av2in>
        av2;
    AvalonReadWrapper<brc_block_read_cache_th_spade_t_o_av3_read *,
                      brc_block_read_cache_th_spade_t_i_av3in>
        av3;

    auto memory_value = [](uint16_t x, uint16_t y) {
      return y == 0 ? 255 : 0;
    };

    // Initialize all avalon contents
    for (int y = 0; y < 600; y++) {
      std::cout << y << std::endl;
      for (int x = 0; x < 64; x++) {
      }
    }
    for (int by = 0; by < 600 / 8; by++) {
      for (int bx = 0; bx < 32 / 8; bx++) {
        for (int iy = 0; iy < 8; iy++) {
          for (int ix = 0; ix < 8; ix++) {
            auto block_start = bx * 64 + by * 512 * 8;
            auto block_inner = ix + iy * 8;

            auto addr = block_start + block_inner;
            auto x = bx + ix;
            auto y = by + iy;
            auto val = memory_value(bx * 8 + ix, by * 8 + iy);
            std::cout
                << std::format("Writing 0x{:x} to {} from ({}, {})",
                               val, addr, x, y)
                << std::endl;
            av0.content[addr] = val;
            av1.content[addr] = val;
            av2.content[addr] = val;
            av3.content[addr] = val;
          }
        }
      }
    }

    s.i->rst = "true";
    s.i->image_height = "80";
    s.i->pixel_read_addr = "None";
    s.i->xblocks_to_fetch = "64";
    TICK_BOTH
    TICK_BOTH
    TICK_BOTH
    TICK_BOTH
    TICK_BOTH
    TICK_BOTH
    s.i->rst = "false";

    // Do a two frames
    int num_lines = 8 * 10;
    for (int y = 0; y < num_lines; y++) {
      std::cout << y << std::endl;
      for (int x = 0; x < 512; x++) {
        // We run at half frequency because this assumes to not be
        // 100% untilized For performance problem reasons, we'll only
        // run with different y values since the performance problems
        // stem from constantly re-compiling this thing
        s.i->pixel_read_addr = std::format("Some((0, {}))", y);
        TICK_BOTH
        TICK_BOTH
      }
    }

    for (int y = 0; y < num_lines; y++) {
      std::cout << y << std::endl;
      for (int x = 0; x < 512; x++) {
        // We run at half frequency because this assumes to not be
        // 100% untilized For performance problem reasons, we'll only
        // run with different y values since the performance problems
        // stem from constantly re-compiling this thing
        s.i->pixel_read_addr = std::format("Some((0, {}))", y);
        TICK_BOTH
        TICK_BOTH
      }
    }

    // Make sure that all 4 caches work
    for (int y = 1; y < 16; y++) {
      // The very edges have edge cases, we don't care about the
      // behaviour there
      for (int x = 1; x < 10; x++) {
        // We run at half frequency because this assumes to not be
        // 100% untilized
        s.i->pixel_read_addr = std::format("Some(({}, {}))", x, y);
        TICK_BOTH
        // We should have the result now
        ASSERT_EQ(
            s.o->read_result,
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
            ));
        TICK_BOTH
      }
    }

    return 0;
  }();
});)

MAIN


TEST_CASE(runtime_reduced_wraparound_works, ({
  return [&]() {
    AvalonReadWrapper<brc_block_read_cache_th_spade_t_o_av0_read *,
                      brc_block_read_cache_th_spade_t_i_av0in>
        av0;
    AvalonReadWrapper<brc_block_read_cache_th_spade_t_o_av1_read *,
                      brc_block_read_cache_th_spade_t_i_av1in>
        av1;
    AvalonReadWrapper<brc_block_read_cache_th_spade_t_o_av2_read *,
                      brc_block_read_cache_th_spade_t_i_av2in>
        av2;
    AvalonReadWrapper<brc_block_read_cache_th_spade_t_o_av3_read *,
                      brc_block_read_cache_th_spade_t_i_av3in>
        av3;

    auto memory_value = [](uint16_t x, uint16_t y) {
      return y == 0 ? 255 : 0;
    };

    // Initialize all avalon contents
    for (int y = 0; y < 600; y++) {
      std::cout << y << std::endl;
      for (int x = 0; x < 64; x++) {
      }
    }
    for (int by = 0; by < 600 / 8; by++) {
      for (int bx = 0; bx < 32 / 8; bx++) {
        for (int iy = 0; iy < 8; iy++) {
          for (int ix = 0; ix < 8; ix++) {
            auto block_start = bx * 64 + by * 512 * 8;
            auto block_inner = ix + iy * 8;

            auto addr = block_start + block_inner;
            auto x = bx + ix;
            auto y = by + iy;
            auto val = memory_value(bx * 8 + ix, by * 8 + iy);
            std::cout
                << std::format("Writing 0x{:x} to {} from ({}, {})",
                               val, addr, x, y)
                << std::endl;
            av0.content[addr] = val;
            av1.content[addr] = val;
            av2.content[addr] = val;
            av3.content[addr] = val;
          }
        }
      }
    }

    s.i->rst = "true";
    s.i->image_height = "80";
    s.i->pixel_read_addr = "None";
    s.i->xblocks_to_fetch = "10";
    TICK_BOTH
    TICK_BOTH
    TICK_BOTH
    TICK_BOTH
    TICK_BOTH
    TICK_BOTH
    s.i->rst = "false";

    // Do a two frames
    int num_lines = 8 * 10;
    for (int y = 0; y < num_lines; y++) {
      std::cout << y << std::endl;
      for (int x = 0; x < 80; x++) {
        // We run at half frequency because this assumes to not be
        // 100% untilized For performance problem reasons, we'll only
        // run with different y values since the performance problems
        // stem from constantly re-compiling this thing
        s.i->pixel_read_addr = std::format("Some((0, {}))", y);
        TICK_BOTH
        TICK_BOTH
      }
    }

    for (int y = 0; y < num_lines; y++) {
      std::cout << y << std::endl;
      for (int x = 0; x < 80; x++) {
        // We run at half frequency because this assumes to not be
        // 100% untilized For performance problem reasons, we'll only
        // run with different y values since the performance problems
        // stem from constantly re-compiling this thing
        s.i->pixel_read_addr = std::format("Some((0, {}))", y);
        TICK_BOTH
        TICK_BOTH
      }
    }

    // Make sure that all 4 caches work
    for (int y = 1; y < 16; y++) {
      // The very edges have edge cases, we don't care about the
      // behaviour there
      for (int x = 1; x < 10; x++) {
        // We run at half frequency because this assumes to not be
        // 100% untilized
        s.i->pixel_read_addr = std::format("Some(({}, {}))", x, y);
        TICK_BOTH
        // We should have the result now
        ASSERT_EQ(
            s.o->read_result,
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
            ));
        TICK_BOTH
      }
    }

    return 0;
  }();
});)
