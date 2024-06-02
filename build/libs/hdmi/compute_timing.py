
def F_find_next_f(f: float) -> float:
    if(25000000>f):
      return 25000000;
    elif(27000000>f):
      return 27000000
    elif(40000000>f):
      return 40000000
    elif(50000000>f):
        return 50000000
    elif(54000000>f):
        return 54000000
    elif(60000000>f):
        return 60000000
    elif(65000000>f):
        return 65000000
    elif(75000000>f):
        return 75000000
    elif(80000000>f):
        return 80000000;  # overclock
    elif(100000000>f):
        return 100000000; # overclock
    elif(108000000>f):
        return 108000000; # overclock
    elif(120000000>f):
      return 120000000; # overclok
    raise Exception("Invalid f")

xadjustf = 0 # adjust -3..3 if no picture
yadjustf = 0 # or to fine-tune f
x = 1024
y = 600
f = 60

xminblank         = x//64; # initial estimate
yminblank         = y//64; # for minimal blank space
min_pixel_f       = f*(x+xminblank)*(y+yminblank);
pixel_f           = F_find_next_f(min_pixel_f);
yframe            = y+yminblank;
xframe            = pixel_f//(f*yframe);
xblank            = xframe-x;
yblank            = yframe-y;
hsync_front_porch = xblank//3;
hsync_pulse_width = xblank//3;
hsync_back_porch  = xblank-hsync_pulse_width-hsync_front_porch+xadjustf;
vsync_front_porch = yblank//3;
vsync_pulse_width = yblank//3;
vsync_back_porch  = yblank-vsync_pulse_width-vsync_front_porch+yadjustf;


print(f"let x_pixels = {x};")
print(f"let x_front_porch = {round(hsync_front_porch)};")
print(f"let x_sync_width = {round(hsync_pulse_width)};")
print(f"let x_back_porch = {round(hsync_back_porch)};")

print(f"let y_pixels = {y};")
print(f"let y_front_porch = {round(vsync_front_porch)};")
print(f"let y_sync_width = {round(vsync_pulse_width)};")
print(f"let y_back_porch = {round(vsync_back_porch)};")

