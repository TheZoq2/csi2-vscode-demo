// top=hdmi::hdmi_out_th

#include "verilated.h"
#include <array>
#include <cstddef>
#include <cstdint>
#include <deque>
#include <format>
#include <lib.rs.h>
#include <stdexcept>
#define TOP hdmi_out_th
#include <verilator_util.hpp>

struct BurstData {
  size_t start;
  size_t count;
  size_t offset;
};

struct Avalon {
  IData &address;
  CData &burstcount;
  CData &read;
  SData &readdata;
  CData &readdatavalid;
  CData &waitrequest;
};

class AvalonReadWrapper {
public:
  AvalonReadWrapper(Avalon avalon, uint8_t id) : avalon(avalon), id(id) {}
  void tick(ffi::SimState const &state) {
    if (avalon.read == true) {
      state.push_request_addr(avalon.address);
      for (int i = 0; i < 64; i++) {
        int addr = avalon.address + i;
        // std::cout << "Pushing " << addr << " into read queue from a request
        // for "
        //   << field_to_uint(read->address) << std::endl;
        read_commands.push_back(addr);
      }
    }

    if (read_commands.size() > 0) {
      auto addr = read_commands.front();
      read_commands.pop_front();
      auto val = state.read_value(addr);
      avalon.readdata = val;
      avalon.readdatavalid = true;
      state.push_addr_read(id, addr);
    } else {
      avalon.readdata = 0;
      avalon.readdatavalid = false;
    }
  }


  std::deque<size_t> read_commands;

  Avalon avalon;
  uint8_t id;
};

#define RAW_TICK                                                               \
  ctx->timeInc(1);                                                             \
  dut->eval();                                                                 \
  ctx->timeInc(1);                                                             \
  dut->vga_clk = 1;                                                            \
  dut->dram_clk = 1;                                                           \
  dut->eval();                                                                 \
  ctx->timeInc(1);                                                             \
  dut->vga_clk = 0;                                                            \
  dut->dram_clk = 0;                                                           \
  dut->eval();                                                                 \
  ctx->timeInc(1);

#define TICK_BOTH                                                              \
  RAW_TICK                                                                     \
  av0.tick(*state);                                                            \
  av1.tick(*state);                                                            \
  av2.tick(*state);                                                            \

TEST_CASE(it_works, ({
            return [&]() {
              auto av0 = AvalonReadWrapper(Avalon{
                  .address = dut->av0_address,
                  .burstcount = dut->av0_burstcount,
                  .read = dut->av0_read,
                  .readdata = dut->av0_readdata,
                  .readdatavalid = dut->av0_readdatavalid,
                  .waitrequest = dut->av0_waitrequest,
              }, 0);
              auto av1 = AvalonReadWrapper(Avalon{
                  .address = dut->av1_address,
                  .burstcount = dut->av1_burstcount,
                  .read = dut->av1_read,
                  .readdata = dut->av1_readdata,
                  .readdatavalid = dut->av1_readdatavalid,
                  .waitrequest = dut->av1_waitrequest,
              }, 1);
              auto av2 = AvalonReadWrapper(Avalon{
                  .address = dut->av2_address,
                  .burstcount = dut->av2_burstcount,
                  .read = dut->av2_read,
                  .readdata = dut->av2_readdata,
                  .readdatavalid = dut->av2_readdatavalid,
                  .waitrequest = dut->av2_waitrequest,
              }, 2);

              dut->rst = true;
              for(int i = 0; i < 100; i++) {
                RAW_TICK
              }
              dut->rst = false;

              auto state = ffi::new_state();
              ffi::start_gui(*state);

              while (!state->is_exited()) {
                TICK_BOTH;
                state->push_pixel_read(dut->out_x, dut->out_y, dut->out_r, dut->out_g, dut->out_b);
              }

              return 0;
            }();
          });)

MAIN
