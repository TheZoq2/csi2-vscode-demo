module top
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
  parameter xadjustf =  0, // adjust -3..3 if no picture
  parameter yadjustf =  0, // or to fine-tune f
  parameter c_ddr    =  1  // 0:SDR 1:DDR
)
(
  input        clk_25mhz,
  input  [6:0] btn,
  output [7:0] led,
  output [3:0] gpdi_dp,
  output       user_programn,
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
  wire clk_shift;
  wire clk_pixel;

  // VGA signal generator
  wire [7:0] vga_r, vga_g, vga_b;
  wire vga_hsync, vga_vsync, vga_blank;

  wire [1:0] tmds_clock, tmds_red, tmds_green, tmds_blue;

  \hdmi::main::main  main(
    .clk_25mhz(clk_25mhz),
    .gpdi_dp3(gpdi_dp[3]),
    .output__({tmds_red, tmds_green, tmds_blue, tmds_clock, clk_pixel, clk_shift})
  );


  // ODDRX1F ddr0_clock (.D0(tmds_clock[0]), .D1(tmds_clock[1]), .Q(gpdi_dp[3]), .SCLK(clk_shift), .RST(0));
  ODDRX1F ddr0_red   (.D0(tmds_red  [0]), .D1(tmds_red  [1]), .Q(gpdi_dp[2]), .SCLK(clk_shift), .RST(0));
  ODDRX1F ddr0_green (.D0(tmds_green[0]), .D1(tmds_green[1]), .Q(gpdi_dp[1]), .SCLK(clk_shift), .RST(0));
  ODDRX1F ddr0_blue  (.D0(tmds_blue [0]), .D1(tmds_blue [1]), .Q(gpdi_dp[0]), .SCLK(clk_shift), .RST(0));
endmodule
