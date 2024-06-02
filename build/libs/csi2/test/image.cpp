// top=lib::csi2_frontend_th

#include <deque>
#include <exception>
#include <format>
#include <bitset>
#include <cstddef>
#include <cstdint>
#include <stdexcept>
#include <utility>
#define TOP csi2_frontend_th
#include <verilator_util.hpp>

#include <array>

uint8_t xor_bits(std::bitset<24> b, std::vector<size_t> indices) {
    uint8_t result = 0;
    for (auto&& i : indices) {
        result ^= b[i];
    }
    return result;
}
uint8_t header_ecc(std::array<uint8_t, 3> bytes) {
    auto b = std::bitset<24>(
        ((uint32_t)(bytes[0]) << 16)
            | ((uint32_t)(bytes[1]) << 8)
            | (uint32_t)(bytes[0])
    );
    uint8_t p7 = 0;
    uint8_t p6 = 0;
    uint8_t p5 = xor_bits(b, {23, 22, 21, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10});
    uint8_t p4 = xor_bits(b, {23, 22, 20, 19, 18, 17, 16, 9, 8, 7, 6, 5, 4});
    uint8_t p3 = xor_bits(b, {23, 22, 21, 20, 15, 14, 13, 9, 8, 7, 3, 2, 1});
    uint8_t p2 = xor_bits(b, {22, 21, 20, 18, 15, 12, 11, 9, 6, 5, 3, 2, 0});
    uint8_t p1 = xor_bits(b, {23, 22, 21, 20, 17, 14, 12, 10, 8, 6, 4, 3, 1, 0});
    uint8_t p0 = xor_bits(b, {23, 22, 21, 20, 16, 13, 11, 10, 7, 5, 4, 2, 1, 0});

    return (p7 << 7) | (p6 << 6) | (p5 << 5) | (p4 << 4) | (p3 << 3) | (p2 << 2) | (p1 << 1) | p0;
}


std::vector<uint8_t> full_packet(std::array<uint8_t, 3> content) {
    std::vector<uint8_t> result;
    for (auto&& b : content) {
        result.push_back(b);
    }
    auto ecc = header_ecc(content);
    result.push_back(ecc);
    std::cout << std::format("header_ecc: {}", ecc) << std::endl;
    return result;
}


#define TICK \
    dut->sys_clk_i = 1; \
    ctx->timeInc(1); \
    dut->eval(); \
    dut->sys_clk_i = 0; \
    ctx->timeInc(1); \
    dut->eval();

std::pair<std::vector<uint8_t>, std::vector<uint8_t>> split_into_lanes(std::vector<uint8_t> data) {
    std::vector<uint8_t> l0{0xb8};
    std::vector<uint8_t> l1{0xb8};

    for(std::size_t i = 0; i < data.size() / 2 + 1; i++) {
        auto idx0 = i * 2;
        auto idx1 = i * 2 + 1;

        if (idx0 < data.size()) {
            l0.push_back(data[idx0]);
        }
        if (idx1 < data.size()) {
            l1.push_back(data[idx1]);
        }
    }

    // NOTE: There is an end of transmission here but the spade decoder
    // currently ignores those, so we'll use 0
    l0.push_back(0x00);
    l1.push_back(0x00);

    return {l0, l1};
}

TEST_CASE(frame_start, {
    bool seen_frame_start = false;
    auto check_frame_start = ([&s, &seen_frame_start]() {
        if (!(*s.o->short_packets == "ShortPacketStream(None)")) {
            ASSERT_EQ(s.o->short_packets, "ShortPacketStream(Some(csi2::short_packet::ShortPacket::FrameStart))");
            seen_frame_start = true;
        }
    });

    auto to_transmit = full_packet({0x00, 0x00, 0x00});

    auto lanes = split_into_lanes(to_transmit);

    s.i->dphy_lp = "true";
    s.i->unaligned_bytes = "[0, 0]";
    for(int i = 0; i < 10; i++) {
        s.i->rst = "true";
        TICK
    }
    s.i->rst = "false";
    TICK
    s.i->dphy_lp = "false";
    TICK

    for(int i = 0; i < lanes.first.size() + 10; i++) {
        auto l1 = i < lanes.first.size() ? lanes.first[i] : 0;
        auto l2 = i < lanes.second.size() ? lanes.second[i] : 0;

        s.i->unaligned_bytes = std::format("[{}, {}]", l1, l2);
        TICK
        check_frame_start();
    }

    ASSERT(seen_frame_start, "Did no see frame start");

    return 0;
})


TEST_CASE(frame_end, {
    bool seen_frame_end = false;
    auto check_frame_start = ([&s, &seen_frame_end]() {
        if (!(*s.o->short_packets == "ShortPacketStream(None)")) {
            ASSERT_EQ(s.o->short_packets, "ShortPacketStream(Some(csi2::short_packet::ShortPacket::FrameEnd))");
            seen_frame_end = true;
        }
    });

    auto to_transmit = full_packet({0x01, 0x00, 0x00});

    auto lanes = split_into_lanes(to_transmit);

    s.i->dphy_lp = "true";
    s.i->unaligned_bytes = "[0, 0]";
    for(int i = 0; i < 10; i++) {
        s.i->rst = "true";
        TICK
    }
    s.i->rst = "false";
    TICK
    s.i->dphy_lp = "false";
    TICK

    for(int i = 0; i < lanes.first.size() + 10; i++) {
        auto l1 = i < lanes.first.size() ? lanes.first[i] : 0;
        auto l2 = i < lanes.second.size() ? lanes.second[i] : 0;

        s.i->unaligned_bytes = std::format("[{}, {}]", l1, l2);
        TICK
        check_frame_start();
    }

    ASSERT(seen_frame_end, "Did no see frame start");

    return 0;
})

TEST_CASE(pixel_stream_works, return ([&](){
    uint16_t length = 0x110;
    std::array<uint8_t, 3> header{0x2A, 0x01, 0x10};
    std::vector<uint8_t> content{
        0x2A,
        static_cast<unsigned char>(length), static_cast<uint8_t>((length >> 8)), header_ecc(header)
    };

    uint8_t last_value = 0;
    for (uint16_t i = 0; i < length; i++) {
        content.push_back(i);
        last_value += 1;
    }
    // NOTE: WE don't check the ECC on the packet data, so we won't generate it either
    content.push_back(0);
    content.push_back(0);

    uint8_t next_expected = 0;
    auto check_pixel = ([&s, &next_expected]() {
        if (!(*s.o->pixels == "PixelStream(None)")) {
            ASSERT_EQ(s.o->pixels, std::format("PixelStream(Some(({}, {})))", next_expected, next_expected + 1));
            next_expected += 2;
        }
    });

    auto lanes = split_into_lanes(content);

    s.i->dphy_lp = "true";
    s.i->unaligned_bytes = "[0, 0]";
    for(int i = 0; i < 10; i++) {
        s.i->rst = "true";
        TICK
    }
    s.i->rst = "false";
    TICK
    s.i->dphy_lp = "false";
    TICK

    for(int i = 0; i < lanes.first.size() + 10; i++) {
        auto l1 = i < lanes.first.size() ? lanes.first[i] : 0;
        auto l2 = i < lanes.second.size() ? lanes.second[i] : 0;

        s.i->unaligned_bytes = std::format("[{}, {}]", l1, l2);
        TICK
        check_pixel();
    }

    std::cout << "Next expected: " << (int) next_expected << " " << (int) last_value << std::endl;

    ASSERT((next_expected == last_value), "Did no see all pixels");

    return 0;
}());)

MAIN
