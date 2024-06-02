# ECP5 stubs

Contains spade stubs and wrappers for ECP5 primitives. These are added on a
by-need basis, so if you need an unsupported wrapper, consider adding it, or
reach out for help.

## Usage

Most of these wrappers can be added to a project by simply adding `https://gitlab.com/spade-lang/lib/ecp5stubs` to the swim.toml

```toml
[libraries]
ecp5stubs = {git = "https://gitlab.com/spade-lang/lib/ecp5stubs", branch = "main"}
```

For using the PLL, some extra effort is required:

First, add the verilog primitive to the synthesis `extra_verilog` list as
```
[synthesis]
extra_verilogs = ["build/deps/ecp5stubs/ecp5pll.sv"]
```

The PLL uses a Verilog primitive to generate parameters for the actual pll.
This wrapper is found in `src/ecp5pll.sv` and must be instantiated manually in a verilog file.

For example, you can create `src/camera_pll.sv` containing
```verilog
`default_nettype none

module camera_pll_impl
(
    input clk,
    output output__,
);
  wire [3:0] clocks;
  wire clk_locked;

  ecp5pll
  #(
      .in_hz(25000000),
    .out0_hz( 5000000),
  )
  ecp5pll_inst
  (
    .clk_i(clk),
    .clk_o(clocks),
    .phasesel(0),
  );

  assign output__ = clocks[0];
endmodule
```

Then expose it to spade in `src/camera_pll.spade` like this:
```spade
#[no_mangle]
entity camera_pll_impl (
    #[no_mangle] clk: clock,
) -> clock __builtin__
```

Remember to add your new Verilog file to the simulation `extra_verilogs` section as well

```toml
[synthesis]
extra_verilogs = ["build/deps/ecp5stubs/ecp5pll.sv", "src/camera_pll.sv"]
```
