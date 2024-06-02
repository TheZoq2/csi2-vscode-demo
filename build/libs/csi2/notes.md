`csi_rx_ice40` parameters
- lanes 2
- Pairswap: ice40 does this, we *probably* don't need to
- Leave the rest

Stuff downstream of `csi_rx_ice40` seems like it can be ignored

`cam_scl` and `cam_sda` is tri-stated in `top` Keep this

# Pin mappings inside rx_ice40
Docs about everything but PIN_TYPE
https://stackoverflow.com/questions/60957971/understanding-the-sb-io-primitive-in-lattice-ice40
# And pin types
file:///home/frans/Downloads/FPGA-TN-02026-3-2-iCE40-Technology-Library.pdf

`dphy_clk_lane` is a LVDS input. It is connected to a `clk_gbuf` to make `dphy_clk`

`dphy_data_lane` is a DDR LVDS input (or `PIN_INPUT_REGISTERED`)

