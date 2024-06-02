module TRELLIS_FF(input CLK, LSR, CE, DI, M, output reg Q);
endmodule

module TRELLIS_IO(
	(* iopad_external_pin *)
	input B,
	input I,
	input T,
	output O
);
	parameter DIR = "INPUT";

endmodule


module OFS1P3BX(input PD, D, SP, SCLK, output Q);
    parameter GSR = "ENABLED"; (* syn_useioff, ioff_dir="output" *)
endmodule


// Diamond flip-flops
module FD1P3AX(input     D, SP, CK, output Q); parameter GSR = "ENABLED"; endmodule
module FD1P3AY(input     D, SP, CK, output Q); parameter GSR = "ENABLED"; endmodule
module FD1P3BX(input PD, D, SP, CK, output Q); parameter GSR = "ENABLED"; endmodule
module FD1P3DX(input CD, D, SP, CK, output Q); parameter GSR = "ENABLED"; endmodule
module FD1P3IX(input CD, D, SP, CK, output Q); parameter GSR = "ENABLED"; endmodule
module FD1P3JX(input PD, D, SP, CK, output Q); parameter GSR = "ENABLED"; endmodule
module FD1S3AX(input     D,     CK, output Q); parameter GSR = "ENABLED"; endmodule
module FD1S3AY(input     D,     CK, output Q); parameter GSR = "ENABLED"; endmodule
module FD1S3BX(input PD, D,     CK, output Q); parameter GSR = "ENABLED"; endmodule
module FD1S3DX(input CD, D,     CK, output Q); parameter GSR = "ENABLED"; endmodule
module FD1S3IX(input CD, D,     CK, output Q); parameter GSR = "ENABLED"; endmodule
module FD1S3JX(input PD, D,     CK, output Q); parameter GSR = "ENABLED"; endmodule

// TODO: Diamond latches
// module FL1P3AY(); endmodule
// module FL1P3AZ(); endmodule
// module FL1P3BX(); endmodule
// module FL1P3DX(); endmodule
// module FL1P3IY(); endmodule
// module FL1P3JY(); endmodule
// module FL1S3AX(); endmodule
// module FL1S3AY(); endmodule

// Diamond I/O registers
module IFS1P3BX(input PD, D, SP, SCLK, output Q); parameter GSR = "ENABLED"; endmodule
module IFS1P3DX(input CD, D, SP, SCLK, output Q); parameter GSR = "ENABLED"; endmodule
module IFS1P3IX(input CD, D, SP, SCLK, output Q); parameter GSR = "ENABLED"; endmodule
module IFS1P3JX(input PD, D, SP, SCLK, output Q); parameter GSR = "ENABLED"; endmodule

module OFS1P3BX(input PD, D, SP, SCLK, output Q); parameter GSR = "ENABLED"; endmodule
module OFS1P3DX(input CD, D, SP, SCLK, output Q); parameter GSR = "ENABLED"; endmodule
module OFS1P3IX(input CD, D, SP, SCLK, output Q); parameter GSR = "ENABLED"; endmodule
module OFS1P3JX(input PD, D, SP, SCLK, output Q); parameter GSR = "ENABLED"; endmodule

// TODO: Diamond I/O latches
// module IFS1S1B(input PD, D, SCLK, output Q); endmodule
// module IFS1S1D(input CD, D, SCLK, output Q); endmodule
// module IFS1S1I(input PD, D, SCLK, output Q); endmodule
// module IFS1S1J(input CD, D, SCLK, output Q); endmodule


// Diamond I/O buffers
module IB   ((* iopad_external_pin *) input I,     output O); endmodule
module IBPU ((* iopad_external_pin *) input I,     output O); endmodule
module IBPD ((* iopad_external_pin *) input I,     output O); endmodule
module OB   (input I,     (* iopad_external_pin *) output O); endmodule
module OBZ  (input I, T,  (* iopad_external_pin *) output O); endmodule
module OBZPU(input I, T,  (* iopad_external_pin *) output O); endmodule
module OBZPD(input I, T,  (* iopad_external_pin *) output O); endmodule
module OBCO (input I,     output OT, OC); endmodule
module BB   (input I, T,  output O, (* iopad_external_pin *) inout B); endmodule
module BBPU (input I, T,  output O, (* iopad_external_pin *) inout B); endmodule
module BBPD (input I, T,  output O, (* iopad_external_pin *) inout B); endmodule
module ILVDS(input A, AN, (* iopad_external_pin *) output Z    ); endmodule
module OLVDS(input A,     (* iopad_external_pin *) output Z, output ZN); endmodule
