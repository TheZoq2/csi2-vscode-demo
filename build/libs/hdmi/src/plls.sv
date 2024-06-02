`default_nettype none

module vga_pll
#(
  //  modes tested on lenovo monitor
  //  640x400  @50Hz
  //  640x400  @60Hz
  //  640x480  @50Hz
  //  640x480  @60Hz
  //  720x576  @50Hz
  //  720x576  @60Hz
  //  800x480  @60Hz
  //  800x600  @60Hz
  // 1024x768  @60Hz
  // 1280x768  @60Hz
  // 1366x768  @60Hz
  // 1280x1024 @60Hz
  // 1920x1080 @30Hz
  // 1920x1080 @50Hz overclock 540MHz
  // 1920x1200 @50Hz overclock 600MHz
  parameter x =  1366,      // pixels
  parameter y =  768,      // pixels
  parameter f =   30,      // Hz 60,50,30
)
(
    input clk_25mhz,
    output[1:0] __output,
);
  function integer F_find_next_f(input integer f);
    if(25000000>f)
      F_find_next_f=25000000;
    else if(27000000>f)
      F_find_next_f=27000000;
    else if(40000000>f)
      F_find_next_f=40000000;
    else if(50000000>f)
      F_find_next_f=50000000;
    else if(54000000>f)
      F_find_next_f=54000000;
    else if(60000000>f)
      F_find_next_f=60000000;
    else if(65000000>f)
      F_find_next_f=65000000;
    else if(75000000>f)
      F_find_next_f=75000000;
    else if(80000000>f)
      F_find_next_f=80000000;  // overclock
    else if(100000000>f)
      F_find_next_f=100000000; // overclock
    else if(108000000>f)
      F_find_next_f=108000000; // overclock
    else if(120000000>f)
      F_find_next_f=120000000; // overclock
  endfunction
  
  localparam xminblank         = x/64; // initial estimate
  localparam yminblank         = y/64; // for minimal blank space
  localparam min_pixel_f       = f*(x+xminblank)*(y+yminblank);
  localparam pixel_f           = F_find_next_f(min_pixel_f);


  // clock generator
  wire clk_locked;
  wire [3:0] clocks;
  wire clk_shift = clocks[0];
  wire clk_pixel = clocks[1];
  ecp5pll
  #(
      .in_hz(25000000),
    .out0_hz(pixel_f*5*1),
    .out1_hz(pixel_f)
  )
  ecp5pll_inst
  (
    .clk_i(clk_25mhz),
    .clk_o(clocks),
    .locked(clk_locked)
  );

  assign __output = {clk_pixel, clk_shift};
endmodule

module pll_640_480_60(input clk_25mhz, output[1:0] output__);
  vga_pll#(.x(640), .y(640), .f(60)) impl(.clk_25mhz(clk_25mhz), .__output(output__));
endmodule

module pll_1366_768_30(input clk_25mhz, output[1:0] output__);
  vga_pll#(.x(1366), .y(768), .f(30)) impl(.clk_25mhz(clk_25mhz), .__output(output__));
endmodule


module pll_1280_720_30(input clk_25mhz, output[1:0] output__);
  vga_pll#(.x(1280), .y(720), .f(30)) impl(.clk_25mhz(clk_25mhz), .__output(output__));
endmodule


module pll_1280_720_60(input clk_25mhz, output[1:0] output__);
  vga_pll#(.x(1280), .y(720), .f(30)) impl(.clk_25mhz(clk_25mhz), .__output(output__));
endmodule

module pll_1024_600_60(input clk_25mhz, output[1:0] output__);
  vga_pll#(.x(1280), .y(720), .f(30)) impl(.clk_25mhz(clk_25mhz), .__output(output__));
endmodule


module pll_480_800_60(input clk_25mhz, output[1:0] output__);
  parameter pixel_f = 31000000;
  wire [3:0] clocks;
  wire clk_shift = clocks[0];
  wire clk_pixel = clocks[1];
  ecp5pll
  #(
      .in_hz(25000000),
    .out0_hz(pixel_f*5*1),
    .out1_hz(pixel_f)
  )
  ecp5pll_inst
  (
    .clk_i(clk_25mhz),
    .clk_o(clocks),
  );

  assign output__ = {clk_pixel, clk_shift};
endmodule
