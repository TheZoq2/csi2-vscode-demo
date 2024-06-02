use std::time::Duration;

use color_eyre::{eyre::Context, Result};
use serial2::SerialPort;

fn write_camera_val(serial: &SerialPort, addr: u16, value: u8) -> Result<()> {
    serial
        .write_all(&[0, (addr >> 8) as u8, addr as u8, value])
        .with_context(|| format!("Failed to write to serial port"))?;

    std::thread::sleep(Duration::from_millis(1));

    Ok(())
}

fn write_output_param(serial: &SerialPort, addr: u8, value: u16) -> Result<()> {
    serial
        .write_all(&[1, addr, (value >> 8) as u8, value as u8])
        .with_context(|| format!("Failed to write to serial port"))?;

    std::thread::sleep(Duration::from_millis(1));

    Ok(())
}

fn main() -> Result<()> {
    let port_name =
        "/dev/serial/by-id/usb-FER-RADIONA-EMARD_ULX3S_FPGA_85K_v3.0.8_D00252-if00-port0";
    let port = serial2::SerialPort::open(port_name, 115200)
        .with_context(|| format!("failed to open {port_name}"))?;


    let framelength: u16 = 1120;
    let linelength: u16 = 3448;
    let pixel_width: u16 = 1024;
    let pixel_height: u16 = 600;
    let coarse_integ_time: u16 = 32;
    let fine_integ_time: u16 = 1;

    // let binning = 2;
    // let bin_config = match binning {
    //     1 => 0,
    //     2 => 1,
    //     4 => 2,
    //     // other => panic!("Invalid binning")
    // };
    let trunc = |x: u16| x as u8;

    let bin_config = 1;
    let pll_offset: u16 = 16;

    // NOTE: For now, there is a bug where if the length of this array changes,
    // there will be a type error which is very hard to decipher here. The fix is to
    // set N in the turbofish at the instantiation site
    let configuration: &[(u16, u8)] =
        &[
            // Based on "Preview Setting" from a Linux driver
            (0x0100, 0x00), //standby mode
            (0x30EB, 0x05), //mfg specific access begin
            (0x30EB, 0x0C), //
            (0x300A, 0xFF), //
            (0x300B, 0xFF), //
            (0x30EB, 0x05), //
            (0x30EB, 0x09), //mfg specific access end
            (0x0114, 0x01), //CSI_LANE_MODE: 2-lane
            (0x0128, 0x00), //DPHY_CTRL: auto mode (?)
            (0x012A, 0x18), //EXCK_FREQ[15:8] = 24MHz
            (0x012B, 0x00), //EXCK_FREQ[7:0]
            (0x0160, trunc(framelength >> 8)), //framelength
            (0x0161, trunc(framelength)),
            (0x0162, trunc(linelength >> 8)),
            (0x0163, trunc(linelength)),
            (0x0164, 0x00), //X_ADD_STA_A[11:8]
            (0x0165, 0x00), //X_ADD_STA_A[7:0]
            (0x0166, trunc((pixel_width << bin_config) >> 8)), // X_ADD_END_A
            (0x0167, trunc(pixel_width << bin_config)), // X_ADD_END_A
            (0x0168, 0x00), //Y_ADD_STA_A[11:8]
            (0x0169, 0x00), //Y_ADD_STA_A[7:0]
            (0x016A, trunc((pixel_height << bin_config) >> 8)), //Y_ADD_END_A[11:8]
            (0x016B, trunc(pixel_height << bin_config)), //Y_ADD_END_A[11:8]
            (0x016C, trunc(pixel_width >> 8)), //x_output_size[11:8] = 640
            (0x016D, trunc(pixel_width)), //x_output_size[7:0]
            (0x016E, trunc(pixel_height >> 8)), //y_output_size[11:8] = 480
            (0x016F, trunc(pixel_height)), //y_output_size[7:0]
            (0x0170, 0x01), //X_ODD_INC_A
            (0x0171, 0x01), //Y_ODD_INC_A
            (0x0172, 0b00), //Image orientation (flip both)
            (0x0174, trunc(bin_config)), //BINNING_MODE_H_A = x4-binning
            (0x0175, trunc(bin_config)), //BINNING_MODE_V_A = x4-binning
            (0x018C, 0x08), //CSI_DATA_FORMAT_A[15:8]
            (0x018D, 0x08), //CSI_DATA_FORMAT_A[7:0]
            (0x0301, 0x08), //VTPXCK_DIV
            (0x0303, 0x01), //VTSYCK_DIV
            (0x0304, 0x02), //PREPLLCK_VT_DIV
            (0x0305, 0x02), //PREPLLCK_OP_DIV
            // write_cmos_sensor_u16(&mut i2c, 0x0306, 0x0014 + pll_offset); //PLL_VT_MPY[10:8]
            (0x0306, trunc((0x0014 + pll_offset) >> 8)),
            (0x0307, trunc((0x0014 + pll_offset))),
            (0x0309, 0x08), //OPPXCK_DIV
            (0x030B, 0x02), //OPSYCK_DIV
            (0x030C, trunc((0x000A + pll_offset) >> 8)), //PLL_OP_MPY[10:8]
            (0x030D, trunc((0x000A + pll_offset))), //PLL_OP_MPY[10:8]
            (0x455E, 0x00), //??
            (0x471E, 0x4B), //??
            (0x4767, 0x0F), //??
            (0x4750, 0x14), //??
            (0x4540, 0x00), //??
            (0x47B4, 0x14), //??
            (0x4713, 0x30), //??
            (0x478B, 0x10), //??
            (0x478F, 0x10), //??
            (0x4793, 0x10), //??
            (0x4797, 0x0E), //??
            (0x479B, 0x0E), //??

            (0x189A, trunc(coarse_integ_time >> 8)), // COARSE_INTEG_TIME_SHORT_A
            (0x189B, trunc(coarse_integ_time)), // COARSE_INTEG_TIME_SHORT_A
            (0x0389, trunc(fine_integ_time >> 8)), // FINE_INTEG_TIME
            (0x0389, trunc(fine_integ_time)), // FINE_INTEG_TIME


            (0x0157,  120), // ANA_GAIN_GLOBAL_A
            (0x0257,  120), // ANA_GAIN_GLOBAL_B

            (0x0600,  0x00), // Test pattern: disable
            (0x0601,  0x00), // Test pattern: disable

            (0x0100, 0x01)
        ];

    for (addr, val) in configuration {
        write_camera_val(&port, *addr, *val)?;
    }

    println!("Starting");

    let max_sun = false;

    // This seems to have no effect
    let coarse_integ_time = if max_sun {0x3e8 >> 5} else {0x3e8};
    let analog_gain = if max_sun {0} else {128};
    let digital_gain = 255;

    let pixel_width: u16 = 3280;
    let pixel_height: u16 = 2464;
    let bin_config = 2;

    write_camera_val(&port, 0x0166, ((pixel_width) >> 8) as u8)?; // X_ADD_END_A
    write_camera_val(&port, 0x0167, (pixel_width) as u8)?; // X_ADD_END_A
    write_camera_val(&port, 0x016A, ((pixel_height) >> 8) as u8)?; //Y_ADD_END_A[11:8]
    write_camera_val(&port, 0x016B, (pixel_height) as u8)?; //Y_ADD_END_A[11:8]
    write_camera_val(&port, 0x0174, (bin_config) as u8)?; //BINNING_MODE_H_A = x4-binning
    write_camera_val(&port, 0x0175, (bin_config) as u8)?; //BINNING_MODE_V_A = x4-binning

    write_camera_val(&port, 0x15A, (coarse_integ_time >> 8) as u8)?;
    write_camera_val(&port, 0x15B, (coarse_integ_time) as u8)?;

    write_camera_val(&port, 0x0157, analog_gain)?;
    write_camera_val(&port, 0x0158, trunc(digital_gain >> 8))?;
    write_camera_val(&port, 0x0159, trunc(digital_gain))?;

    write_output_param(&port, 100, ((1.0 / 0.83) * 255.) as u16)?; // r
    write_output_param(&port, 101, ((1.0 / 1.2) * 255.) as u16)?; // g
    write_output_param(&port, 102, ((1.0 / 0.90) * 255.) as u16)?; // b

    Ok(())
}
