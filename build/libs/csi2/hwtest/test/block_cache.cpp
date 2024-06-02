
// top=block_cache::block_cache_th

#include <array>
#include <cstdint>
#include <format>
#include <stdexcept>
#define TOP block_cache_th
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

class AvalonWriterWrapper {
public:
  AvalonWriterWrapper() {
    this->burst = std::nullopt;
    // This leaks, but who cares. There is only one instance
    this->content = new std::array<std::optional<uint16_t>, size>();
    for (int i = 0; i < size; i++) {
      (*this->content)[i] = std::nullopt;
    }
  }

  void tick(verilator_util::spade_wrapper &s) {
    if (*s.o->avalon_write == "true" && !this->burst.has_value()) {
      this->burst = BurstData{
          .start = (uint16_t)field_to_uint(s.o->address),
          .count = (uint16_t)field_to_uint(s.o->burstcount),
          .offset = 0,
      };

      std::cout << std::format("Starting write burst to {}", burst->start)
                << std::endl;
    }
    if (this->burst.has_value()) {
      auto &burst = this->burst.value();

      ASSERT_EQ(s.o->avalon_write, "true");

      auto addr = burst.start + burst.offset;

      if (addr <= size) {
        (*content)[addr] = field_to_uint(s.o->writedata);
      }

      burst.offset = burst.offset + 1;
      if (burst.offset == burst.count) {
        this->burst.reset();
      }
    }
  }

  static constexpr size_t size = 1024 * 600;
  std::optional<BurstData> burst;
  std::array<std::optional<uint16_t>, size> *content;
};

#define TICK_BOTH                                                              \
  ctx->timeInc(1);                                                             \
  dut->eval();                                                                 \
  dut->camera_clk_i = 1;                                                       \
  dut->dram_clk_i = 1;                                                         \
  ctx->timeInc(1);                                                             \
  dut->eval();                                                                 \
  dut->camera_clk_i = 0;                                                       \
  dut->dram_clk_i = 0;                                                         \
  avalon.tick(s);

TEST_CASE(it_works, {
  // Your test code here
  auto avalon = AvalonWriterWrapper();

  s.i->is_frame_start = "false";
  s.i->write = "None()";
  s.i->rst = "true";
  TICK_BOTH
  TICK_BOTH
  TICK_BOTH
  TICK_BOTH
  TICK_BOTH
  s.i->rst = "false";

  for (int y = 0; y < 8; y++) {
    for (int x = 0; x < 1024; x++) {
      // Write vertical stripes in the first block
      uint16_t to_write;
      if (x < 8) {
        to_write = (x % 2);
      }
      // Write horizontal stripes in the next block
      else if (x < 16) {
        to_write = (y % 2);
      } else {
        to_write = 0;
      }
      s.i->write = std::format("Some({})", to_write);
      TICK_BOTH
    }
  }
  s.i->write = "None";
  // At this point there should be a swap, and the cache should dump its
  // content. Ensure that nothing is written in the first line
  for (int y = 0; y < 8; y++) {
    for (int x = 0; x < 1024; x++) {
      auto msg = std::format(
          "Content was written into the array already at {} {}", x, y);
      ASSERT(((*avalon.content)[x + y * 1024] == std::nullopt), msg);
    }
  }
  TICK_BOTH
  TICK_BOTH
  TICK_BOTH
  TICK_BOTH
  TICK_BOTH

  // Evict the cache
  for (int y = 0; y < 8; y++) {
    for (int x = 0; x < 1024; x++) {
      TICK_BOTH
    }
  }

  // Ensure that all words we expect got written
  for (int i = 0; i < 8 * 1024; i++) {
    if (!(*avalon.content)[i].has_value()) {
      ASSERT(false, (std::format("Content at {} was not written", i)));
    }
  }
  // Print them first for easy debugging
  for (int i = 0; i < 128; i++) {
    std::cout << (*avalon.content)[i].value();
  }
  std::cout << std::endl;
  for (int i = 0; i < 64; i++) {
    auto got = (*avalon.content)[i].value();
    auto expected = i % 2;
    ASSERT((got == expected),
           std::format("Invalid content in block 0. At {} e: {} g: {}", i,
                       expected, got))
  }
  for (int i = 64; i < 128; i++) {
    auto got = (*avalon.content)[i].value();
    auto expected = i % 16 >= 8;
    ASSERT((got == expected),
           std::format("Invalid content in block 1. At {} e: {} g: {}", i,
                       expected, got))
  }

  // Now do more of the frames, 2 rows writing all 10
  for (int y = 0; y < 16; y++) {
    std::cout << y << std::endl;
    for (int x = 0; x < 1024; x++) {
      for(int t = 0; t < 2; t++) {
        if (t == 0) {
          // Block0 to all 1
          uint16_t to_write = 10;

          s.i->write = std::format("Some({})", to_write);
        } else {
          s.i->write = "None";
        }
        TICK_BOTH
      }
    }
  }
  s.i->write = "None";

  TICK_BOTH
  TICK_BOTH
  TICK_BOTH
  TICK_BOTH
  // Evict the cache
  for (int y = 0; y < 8; y++) {
    for (int x = 0; x < 1024; x++) {
      TICK_BOTH
    }
  }

  // Ensure that all words we expect got written
  for (int y = 8; y < 24; y++) {
    for (int x = 0; x < 1024; x++) {
      auto i = y * 1024 + x;
      ASSERT((*avalon.content)[i].has_value(),
             (std::format("Content at {} was not written", i)));
      ASSERT((*avalon.content)[i].value() == 10, "Value was not 10");
    }
  }

  TICK_BOTH
  TICK_BOTH
  TICK_BOTH
  TICK_BOTH
  TICK_BOTH
  s.i->is_frame_start = "true";
  TICK_BOTH
  s.i->is_frame_start = "false";
  TICK_BOTH
  TICK_BOTH
  TICK_BOTH
  TICK_BOTH
  TICK_BOTH

  // Replace everything in the previous block with 30 
  for (int y = 0; y < 24; y++) {
    std::cout << y << std::endl;
    for (int x = 0; x < 1024; x++) {
      for(int t = 0; t < 2; t++) {
        if (t == 0) {
          // Block0 to all 1
          uint16_t to_write = 30;

          s.i->write = std::format("Some({})", to_write);
        } else {
          s.i->write = "None";
        }
        TICK_BOTH
      }
    }
  }
  s.i->write = "None";

  TICK_BOTH
  TICK_BOTH
  TICK_BOTH
  TICK_BOTH
  // Evict the cache
  for (int y = 0; y < 8; y++) {
    for (int x = 0; x < 1024; x++) {
      TICK_BOTH
    }
  }


  for (int y = 8; y < 24; y++) {
    for (int x = 0; x < 1024; x++) {
      auto i = y * 1024 + x;
      ASSERT((*avalon.content)[i].has_value(),
             (std::format("Content at {} was not written", i)));
      ASSERT((*avalon.content)[i].value() == 30, "Value was not 30");
    }
  }

  return 0;
})

MAIN
