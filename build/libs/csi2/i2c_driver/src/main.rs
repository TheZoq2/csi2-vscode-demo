//! Blinks an LED
//!
//! This assumes that a LED is connected to pc13 as is the case on the blue pill board.
//!
//! Note: Without additional hardware, PC13 should not be used to drive an LED, see page 5.1.2 of
//! the reference manual for an explanation. This is not an issue on the blue pill.

#![deny(unsafe_code)]
#![no_std]
#![no_main]

use panic_rtt_target as _;
use rtt_target::{rprintln, rtt_init_print};

use nb::block;

use cortex_m_rt::entry;
use stm32f1xx_hal::{
    gpio::{Alternate, OpenDrain, PB8, PB9},
    i2c::{BlockingI2c, Mode},
    pac,
    prelude::*,
    timer::Timer,
};

fn write_cmos_sensor(
    i2c: &mut BlockingI2c<pac::I2C1, (PB8<Alternate<OpenDrain>>, PB9<Alternate<OpenDrain>>)>,
    addr: u16,
    value: u8,
) {
    rprintln!("Writing {} to {}", value, addr);
    i2c.write(0x10, &[(addr >> 8) as u8, addr as u8, value])
        .expect("Failed to write to camera")
}


fn write_cmos_sensor_u16(
    i2c: &mut BlockingI2c<pac::I2C1, (PB8<Alternate<OpenDrain>>, PB9<Alternate<OpenDrain>>)>,
    addr: u16,
    value: u16,
) {
    write_cmos_sensor(i2c, addr, ((value >> 8) & 0xFF) as u8); //framelength
    write_cmos_sensor(i2c, addr+1, (value & 0xFF) as u8);
}


// NOTE: Remember to set power enable on the camera from the FPGA before running this

#[entry]
fn main() -> ! {
    rtt_init_print!();
    // Get access to the core peripherals from the cortex-m crate
    let mut cp = cortex_m::Peripherals::take().unwrap();
    // Get access to the device specific peripherals from the peripheral access crate
    let dp = pac::Peripherals::take().unwrap();

    cp.DCB.enable_trace();
    cp.DWT.enable_cycle_counter();

    // Take ownership over the raw flash and rcc devices and convert them into the corresponding
    // HAL structs
    let mut flash = dp.FLASH.constrain();
    let rcc = dp.RCC.constrain();

    let mut afio = dp.AFIO.constrain();

    // Freeze the configuration of all the clocks in the system and store the frozen frequencies in
    // `clocks`
    let clocks = rcc.cfgr.freeze(&mut flash.acr);

    // Acquire the GPIOC peripheral
    let mut gpiob = dp.GPIOB.split();
    let mut gpioc = dp.GPIOC.split();

    // Configure gpio C pin 13 as a push-pull output. The `crh` register is passed to the function
    // in order to configure the port. For pins 0-7, crl should be passed instead.
    let mut led = gpioc.pc13.into_push_pull_output(&mut gpioc.crh);
    // Configure the syst timer to trigger an update every second
    let mut timer = Timer::syst(cp.SYST, &clocks).counter_hz();
    timer.start(1.Hz()).unwrap();

    let sda = gpiob.pb9.into_alternate_open_drain(&mut gpiob.crh);
    let sclk = gpiob.pb8.into_alternate_open_drain(&mut gpiob.crh);

    let mut i2c = BlockingI2c::i2c1(
        dp.I2C1,
        (sclk, sda),
        &mut afio.mapr,
        Mode::Standard {
            frequency: 100.kHz(),
        },
        clocks,
        100000,
        10,
        100000,
        100000,
    );

    // rprintln!("Up and running. Waiting");
    // block!(timer.wait()).unwrap();
    // block!(timer.wait()).unwrap();

    let framelength: u16 = 1120;
    let linelength: u16 = 3448;
    let pixel_width: u16 = 1024;
    let pixel_height: u16 = 600;

    let binning = 2;
    let bin_config = match binning {
        1 => 0,
        2 => 1,
        4 => 2,
        other => panic!("Invalid binning")
    };

    let pll_offset = 16;


    // Based on "Preview Setting" from a Linux driver
    write_cmos_sensor(&mut i2c, 0x0100, 0x00); //standby mode
    write_cmos_sensor(&mut i2c, 0x30EB, 0x05); //mfg specific access begin
    write_cmos_sensor(&mut i2c, 0x30EB, 0x0C); //
    write_cmos_sensor(&mut i2c, 0x300A, 0xFF); //
    write_cmos_sensor(&mut i2c, 0x300B, 0xFF); //
    write_cmos_sensor(&mut i2c, 0x30EB, 0x05); //
    write_cmos_sensor(&mut i2c, 0x30EB, 0x09); //mfg specific access end
    write_cmos_sensor(&mut i2c, 0x0114, 0x01); //CSI_LANE_MODE: 2-lane
    write_cmos_sensor(&mut i2c, 0x0128, 0x00); //DPHY_CTRL: auto mode (?)
    write_cmos_sensor(&mut i2c, 0x012A, 0x18); //EXCK_FREQ[15:8] = 24MHz
    write_cmos_sensor(&mut i2c, 0x012B, 0x00); //EXCK_FREQ[7:0]
    write_cmos_sensor(&mut i2c, 0x0160, ((framelength >> 8) & 0xFF) as u8); //framelength
    write_cmos_sensor(&mut i2c, 0x0161, (framelength & 0xFF) as u8);
    write_cmos_sensor(&mut i2c, 0x0162, ((linelength >> 8) & 0xFF) as u8);
    write_cmos_sensor(&mut i2c, 0x0163, (linelength & 0xFF) as u8);
    write_cmos_sensor(&mut i2c, 0x0164, 0x00); //X_ADD_STA_A[11:8]
    write_cmos_sensor(&mut i2c, 0x0165, 0x00); //X_ADD_STA_A[7:0]
    write_cmos_sensor_u16(&mut i2c, 0x166, pixel_width * binning); // X_ADD_END_A
    write_cmos_sensor(&mut i2c, 0x0168, 0x00); //Y_ADD_STA_A[11:8]
    write_cmos_sensor(&mut i2c, 0x0169, 0x00); //Y_ADD_STA_A[7:0]
    write_cmos_sensor_u16(&mut i2c, 0x016A, pixel_height * binning); //Y_ADD_END_A[11:8]
    write_cmos_sensor(&mut i2c, 0x016C, ((pixel_width >> 8) & 0xFF) as u8); //x_output_size[11:8] = 640
    write_cmos_sensor(&mut i2c, 0x016D, (pixel_width & 0xFF) as u8); //x_output_size[7:0]
    write_cmos_sensor(&mut i2c, 0x016E, ((pixel_height >> 8) & 0xff) as u8); //y_output_size[11:8] = 480
    write_cmos_sensor(&mut i2c, 0x016F, (pixel_height & 0xFF) as u8); //y_output_size[7:0]
    write_cmos_sensor(&mut i2c, 0x0170, 0x01); //X_ODD_INC_A
    write_cmos_sensor(&mut i2c, 0x0171, 0x01); //Y_ODD_INC_A
    write_cmos_sensor(&mut i2c, 0x0172, 0b00); //Image orientation (flip both)
    write_cmos_sensor(&mut i2c, 0x0174, bin_config); //BINNING_MODE_H_A = x4-binning
    write_cmos_sensor(&mut i2c, 0x0175, bin_config); //BINNING_MODE_V_A = x4-binning
    write_cmos_sensor(&mut i2c, 0x018C, 0x08); //CSI_DATA_FORMAT_A[15:8]
    write_cmos_sensor(&mut i2c, 0x018D, 0x08); //CSI_DATA_FORMAT_A[7:0]
    write_cmos_sensor(&mut i2c, 0x0301, 0x08); //VTPXCK_DIV
    write_cmos_sensor(&mut i2c, 0x0303, 0x01); //VTSYCK_DIV
    write_cmos_sensor(&mut i2c, 0x0304, 0x02); //PREPLLCK_VT_DIV
    write_cmos_sensor(&mut i2c, 0x0305, 0x02); //PREPLLCK_OP_DIV
    write_cmos_sensor_u16(&mut i2c, 0x0306, 0x0014 + pll_offset); //PLL_VT_MPY[10:8]
    write_cmos_sensor(&mut i2c, 0x0309, 0x08); //OPPXCK_DIV
    write_cmos_sensor(&mut i2c, 0x030B, 0x02); //OPSYCK_DIV
    write_cmos_sensor_u16(&mut i2c, 0x030C, 0x000A + pll_offset); //PLL_OP_MPY[10:8]
    write_cmos_sensor(&mut i2c, 0x455E, 0x00); //??
    write_cmos_sensor(&mut i2c, 0x471E, 0x4B); //??
    write_cmos_sensor(&mut i2c, 0x4767, 0x0F); //??
    write_cmos_sensor(&mut i2c, 0x4750, 0x14); //??
    write_cmos_sensor(&mut i2c, 0x4540, 0x00); //??
    write_cmos_sensor(&mut i2c, 0x47B4, 0x14); //??
    write_cmos_sensor(&mut i2c, 0x4713, 0x30); //??
    write_cmos_sensor(&mut i2c, 0x478B, 0x10); //??
    write_cmos_sensor(&mut i2c, 0x478F, 0x10); //??
    write_cmos_sensor(&mut i2c, 0x4793, 0x10); //??
    write_cmos_sensor(&mut i2c, 0x4797, 0x0E); //??
    write_cmos_sensor(&mut i2c, 0x479B, 0x0E); //??

    write_cmos_sensor_u16(&mut i2c, 0x189A, 0x01F4 / 2); // COARSE_INTEG_TIME_SHORT_A
    write_cmos_sensor_u16(&mut i2c, 0x0388, 0x01F4 / 2); // FINE_INTEG_TIME


    write_cmos_sensor(&mut i2c, 0x0157,  232); // ANA_GAIN_GLOBAL_A
    write_cmos_sensor(&mut i2c, 0x0257,  232); // ANA_GAIN_GLOBAL_B

    write_cmos_sensor(&mut i2c, 0x0600,  0x00); // Test pattern: disable
    write_cmos_sensor(&mut i2c, 0x0601,  0x00); // Test pattern: disable
    /*
    write_cmos_sensor(&mut i2c, 0x0600,  0x00); // Test pattern: disable
    write_cmos_sensor(&mut i2c, 0x0601,  0x05); // Test pattern: disable

    write_cmos_sensor(&mut i2c, 0x0602,  0x02); // Test pattern: red
    write_cmos_sensor(&mut i2c, 0x0603,  0xAA); //

    write_cmos_sensor(&mut i2c, 0x0604,  0x02); // Test pattern: greenR
    write_cmos_sensor(&mut i2c, 0x0605,  0xAA); //

    write_cmos_sensor(&mut i2c, 0x0606,  0x02); // Test pattern: blue
    write_cmos_sensor(&mut i2c, 0x0607,  0xAA); //

    write_cmos_sensor(&mut i2c, 0x0608,  0x02); // Test pattern: greenB
    write_cmos_sensor(&mut i2c, 0x0609,  0xAA); //

    write_cmos_sensor(&mut i2c, 0x0624,  0x02); // Test pattern width
    write_cmos_sensor(&mut i2c, 0x0625,  0x80); //

    write_cmos_sensor(&mut i2c, 0x0626,  0x07); // Test pattern height
    write_cmos_sensor(&mut i2c, 0x0627,  0x80); //
    */


    write_cmos_sensor(&mut i2c, 0x0100, 0x01);
    // Wait for the timer to trigger an update and change the state of the LED
    loop {
        block!(timer.wait()).unwrap();
        led.set_high();
        block!(timer.wait()).unwrap();
        led.set_low();
    }
}
