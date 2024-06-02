# Ulx3s HDMI

Spade code (with some verilog black boxes for now) for driving the HDMI port on a ulx3s board

## Use in a subproject

Add the dependency to `swim.toml`. For now you have to use a path dependency
```
mkdir deps
cd deps
git submodule add https://gitlab.com/TheZoq2/ulx3s_hdmi_spade.git
```

Add the dependency and the verilog black box code to the parent project
```toml
extra_verilog = [
    "deps/ulx3s_hdmi_spade/src/ecp5pll.sv",
    "deps/ulx3s_hdmi_spade/src/example_verilog/fake_differential.v",
    "deps/ulx3s_hdmi_spade/src/example_verilog/vga2dvid.v",
    "deps/ulx3s_hdmi_spade/src/example_verilog/tmds_encoder.v",
]

[libraries]
hdmi = {path = "deps/ulx3s_hdmi_spade"}
```

The following code generates a test image
```spade
use hdmi::main::VgaTiming;
use hdmi::main::VgaOutput;
use hdmi::main::vga_fsm;
use hdmi::main::vga_output;
use hdmi::vga2dvid::DviOut;
use hdmi::vga2dvid::vga2dvid;


struct Output {
    dvi: DviOut,
}


entity main(vga_clk: clock, clk_shift: clock, rst: bool) -> Output {
    let timing = VgaTiming$(
        x_pixels: 1366,
        x_front_porch: 7,
        x_sync_width: 7,
        x_back_porch: 8,
        y_pixels: 768,
        y_front_porch: 4,
        y_sync_width: 4,
        y_back_porch: 4,
    );

    let vga_state = inst vga_fsm$(clk: vga_clk, rst, clk_enable: true, timing);
    let VgaOutput$(hsync, vsync, blank, pixel) = vga_output(vga_state);

    let color = match pixel {
        Some((x,y)) => {
            (trunc(x), trunc(y), if x == y {255u} else {0})
        },
        None => {
            (0,0,0)
        }
    };

    let dvi = inst vga2dvid$(
        clk_pixel: vga_clk,
        clk_shift,
        rst,
        hsync,
        vsync,
        blank,
        color
    );

    Output $(dvi)
}
```

The timing here is for 1366x768@30fps. You can get timing requirements for other frame rates using the `compute_timing.py` script.

To instantiate it, use use the code in `src/top_vgatest.spade`

## Testing

`swim upload` should work and display a test pattern


