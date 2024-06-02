#
# This file is heavily inspired by gen.py of LiteDRAM.
#
# Original copyright
#
# Copyright (c) 2018-2021 Florent Kermarrec <florent@enjoy-digital.fr>
# Copyright (c) 2020 Stefan Schrijvers <ximin@ximinity.net>
# SPDX-License-Identifier: BSD-2-Clause

from typing import Any, Tuple, Dict
import yaml
import argparse
import pathlib
import os

class Port:
    def __init__(
        self,
        # The port defintiion of the #[no_mangle] entity to be generated
        spade_stub_head,
        # Extra code in the body of the spade module to map ports to
        # spade struct
        spade_body,
        # Bindings from the things defined in spade_body to the stub
        spade_bindings,
        # Port binding to return from the module
        spade_return_port,
        # Output port definitions of the spade module
        spade_output_type,
    ) -> None:
        self.spade_stub_head = spade_stub_head
        self.spade_body = spade_body
        self.spade_bindings = spade_bindings
        self.spade_output_type = spade_output_type
        self.spade_return_port = spade_return_port

def generate_wishbone(port: Tuple[str, Dict[str, Any]]) -> Port:
    (port_name, props) = port
    spade_stub_head = "\n    ".join([
        f"#[no_mangle] user_port_{port_name}_adr: uint<24>,",
        f"#[no_mangle] user_port_{port_name}_dat_w: uint<16>,",
        f"#[no_mangle] user_port_{port_name}_dat_r: &mut uint<16>,",
        f"#[no_mangle] user_port_{port_name}_sel: uint<2>,",
        f"#[no_mangle] user_port_{port_name}_cyc: bool,",
        f"#[no_mangle] user_port_{port_name}_stb: bool,",
        f"#[no_mangle] user_port_{port_name}_ack: &mut bool,",
        f"#[no_mangle] user_port_{port_name}_we: bool,",
        f"#[no_mangle] user_port_{port_name}_err: &mut bool,",
    ])
    spade_body = "\n    ".join([
        f"let ({port_name}, {port_name}_inv) = port;",

        f"let ({port_name}_we, {port_name}_data_w) = match *{port_name}_inv.write {{",
            f"Some(data) => (true, data),",
            f"None => (false, 0) // NOTE: Placeholder 0",
        f"}};"
    ])
    spade_bindings = "\n        ".join([
        f"user_port_{port_name}_adr: *{port_name}_inv.addr,",
        f"user_port_{port_name}_dat_w: {port_name}_data_w,",
        f"user_port_{port_name}_dat_r: {port_name}_inv.data_out,",
        f"user_port_{port_name}_sel: *{port_name}_inv.sel,",
        f"user_port_{port_name}_cyc: *{port_name}_inv.cyc,",
        f"user_port_{port_name}_stb: *{port_name}_inv.stb,",
        f"user_port_{port_name}_ack: {port_name}_inv.ack,",
        f"user_port_{port_name}_we: {port_name}_we,",
        f"user_port_{port_name}_err: {port_name}_inv.err,",
    ])
    spade_return_port = f"{port_name}"

    return Port(
        spade_stub_head=spade_stub_head,
        spade_body=spade_body,
        spade_bindings=spade_bindings,
        spade_return_port=spade_return_port,
        spade_output_type="DramWishbone"
    )

def generate_avalon(port: Tuple[str, Dict[str, Any]]) -> Port:
    (port_name, props) = port
    spade_stub_head = "\n    ".join([
        f"#[no_mangle] user_port_{port_name}_address: uint<24>,",
        f"#[no_mangle] user_port_{port_name}_burstcount: uint<8>,",
        f"#[no_mangle] user_port_{port_name}_byteenable: uint<2>,",
        f"#[no_mangle] user_port_{port_name}_read: bool,",
        f"#[no_mangle] user_port_{port_name}_readdata: &mut uint<16>,",
        f"#[no_mangle] user_port_{port_name}_readdatavalid: &mut bool,",
        f"#[no_mangle] user_port_{port_name}_waitrequest: &mut bool,",
        f"#[no_mangle] user_port_{port_name}_write: bool,",
        f"#[no_mangle] user_port_{port_name}_writedata: uint<16>,",
    ])
    spade_body = "\n    ".join([
        f"let ({port_name}, {port_name}_inv) = port;",
    ])
    spade_bindings = "\n        ".join([
        f"user_port_{port_name}_address: *{port_name}_inv.address,",
        f"user_port_{port_name}_burstcount: *{port_name}_inv.burstcount,",
        f"user_port_{port_name}_byteenable: *{port_name}_inv.byteenable,",
        f"user_port_{port_name}_read: *{port_name}_inv.read,",
        f"user_port_{port_name}_readdata: {port_name}_inv.readdata,",
        f"user_port_{port_name}_readdatavalid: {port_name}_inv.readdatavalid,",
        f"user_port_{port_name}_waitrequest: {port_name}_inv.waitrequest,",
        f"user_port_{port_name}_write: *{port_name}_inv.write,",
        f"user_port_{port_name}_writedata: *{port_name}_inv.writedata,",
    ])
    spade_return_port = f"{port_name}"

    return Port(
        spade_stub_head=spade_stub_head,
        spade_body=spade_body,
        spade_bindings=spade_bindings,
        spade_return_port=spade_return_port,
        spade_output_type="AvalonPort"
    )

def generate_axi(port: Tuple[str, Dict[str, Any]]) -> Port:
    (port_name, props) = port
    id_width = props["id_width"]
    spade_stub_head = "\n    ".join([
        f"#[no_mangle] user_port_{port_name}_awvalid: bool,",
        f"#[no_mangle] user_port_{port_name}_awready: &mut bool,",
        f"#[no_mangle] user_port_{port_name}_awaddr: int<25>,",
        f"#[no_mangle] user_port_{port_name}_awburst: int<2>,",
        f"#[no_mangle] user_port_{port_name}_awlen: int<8>,",
        f"#[no_mangle] user_port_{port_name}_awsize: int<4>,",
        f"#[no_mangle] user_port_{port_name}_awid: int<{id_width}>,",
        f"#[no_mangle] user_port_{port_name}_wvalid: bool,",
        f"#[no_mangle] user_port_{port_name}_wready: &mut bool,",
        f"#[no_mangle] user_port_{port_name}_wlast: bool,",
        f"#[no_mangle] user_port_{port_name}_wstrb: int<2>,",
        f"#[no_mangle] user_port_{port_name}_wdata: int<16>,",
        f"#[no_mangle] user_port_{port_name}_bvalid: &mut bool,",
        f"#[no_mangle] user_port_{port_name}_bready: bool,",
        f"#[no_mangle] user_port_{port_name}_bresp: &mut int<2>,",
        f"#[no_mangle] user_port_{port_name}_bid: &mut int<{id_width}>,",
        f"#[no_mangle] user_port_{port_name}_arvalid: bool,",
        f"#[no_mangle] user_port_{port_name}_arready: &mut bool,",
        f"#[no_mangle] user_port_{port_name}_araddr: int<25>,",
        f"#[no_mangle] user_port_{port_name}_arburst: int<2>,",
        f"#[no_mangle] user_port_{port_name}_arlen: int<8>,",
        f"#[no_mangle] user_port_{port_name}_arsize: int<4>,",
        f"#[no_mangle] user_port_{port_name}_arid: int<{id_width}>,",
        f"#[no_mangle] user_port_{port_name}_rvalid: &mut bool,",
        f"#[no_mangle] user_port_{port_name}_rready: bool,",
        f"#[no_mangle] user_port_{port_name}_rlast: &mut bool,",
        f"#[no_mangle] user_port_{port_name}_rresp: &mut int<2>,",
        f"#[no_mangle] user_port_{port_name}_rdata: &mut int<16>,",
        f"#[no_mangle] user_port_{port_name}_rid: &mut int<{id_width}>,",
    ])
    spade_return_port = f"{port_name}"

    spade_body = "\n    ".join([
        f"let ({port_name}, {port_name}_inv) = port;"
    ])
    spade_bindings = "\n        ".join([
        f"user_port_{port_name}_awvalid: *{port_name}_inv.aw.valid,",
        f"user_port_{port_name}_awready: {port_name}_inv.aw.ready,",
        f"user_port_{port_name}_awaddr: *{port_name}_inv.aw.addr,",
        f"user_port_{port_name}_awburst: *{port_name}_inv.aw.burst,",
        f"user_port_{port_name}_awlen: *{port_name}_inv.aw.len,",
        f"user_port_{port_name}_awsize: *{port_name}_inv.aw.size,",
        f"user_port_{port_name}_awid: *{port_name}_inv.aw.id,",

        f"user_port_{port_name}_wvalid: *{port_name}_inv.w.valid,",
        f"user_port_{port_name}_wready: {port_name}_inv.w.ready,",
        f"user_port_{port_name}_wlast: *{port_name}_inv.w.last,",
        f"user_port_{port_name}_wstrb: *{port_name}_inv.w.strb,",
        f"user_port_{port_name}_wdata: *{port_name}_inv.w.data,",

        f"user_port_{port_name}_bvalid: {port_name}_inv.b.valid,",
        f"user_port_{port_name}_bready: *{port_name}_inv.b.ready,",
        f"user_port_{port_name}_bresp: {port_name}_inv.b.resp,",
        f"user_port_{port_name}_bid: {port_name}_inv.b.id,",

        f"user_port_{port_name}_arvalid: *{port_name}_inv.ar.valid,",
        f"user_port_{port_name}_arready: {port_name}_inv.ar.ready,",
        f"user_port_{port_name}_araddr: *{port_name}_inv.ar.addr,",
        f"user_port_{port_name}_arburst: *{port_name}_inv.ar.burst,",
        f"user_port_{port_name}_arlen: *{port_name}_inv.ar.len,",
        f"user_port_{port_name}_arsize: *{port_name}_inv.ar.size,",
        f"user_port_{port_name}_arid: *{port_name}_inv.ar.id,",

        f"user_port_{port_name}_rvalid: {port_name}_inv.r.valid,",
        f"user_port_{port_name}_rready: *{port_name}_inv.r.ready,",
        f"user_port_{port_name}_rlast: {port_name}_inv.r.last,",
        f"user_port_{port_name}_rresp: {port_name}_inv.r.resp,",
        f"user_port_{port_name}_rdata: {port_name}_inv.r.data,",
        f"user_port_{port_name}_rid: {port_name}_inv.r.id,",
    ])
    return Port(
        spade_stub_head=spade_stub_head,
        spade_body=spade_body,
        spade_bindings=spade_bindings,
        spade_return_port=spade_return_port,
        spade_output_type=f"AxiPort<{id_width}>"
    )

def generate_port(port: Tuple[str, Dict[str, Any]]) -> Port:
    (_, props) = port
    match props["type"]:
        case "wishbone":
            return generate_wishbone(port)
        case "avalon":
            return generate_avalon(port)
        case "axi":
            return generate_axi(port)
        case other:
            raise ValueError(f"Port of type {other} is unsupported")

def generate_files(
    config: Dict[str, Dict[str, Any]],
    spade_stub_file: pathlib.Path
) -> str:
    ports = [generate_port(port) for port in config["user_ports"].items()]

    with open(spade_stub_file, 'r') as f:
        spade_stub = f.read()

    spade_stub_inputs = " ".join([port.spade_stub_head for port in ports])
    spade_types = ", ".join([port.spade_output_type for port in ports])
    spade_body = "\n".join([port.spade_body for port in ports])
    spade_bindings = "\n".join([port.spade_bindings for port in ports])
    spade_return_port = ", ".join([port.spade_return_port for port in ports])

    sys_clk_freq = config["sys_clk_freq"];
    main_clk = f"clk_{sys_clk_freq}"
    sdram_clk = f"clk_{sys_clk_freq}_180deg"
    spade_clk_inputs = f"{main_clk}: clock,\n{sdram_clk}: clock,";


    return (
        spade_stub
            .replace("##CLK_INPUTS##", spade_clk_inputs)
            .replace("##MAIN_CLK##", main_clk)
            .replace("##SDRAM_CLK##", sdram_clk)
            .replace("##STUB_INPUTS##", spade_stub_inputs)
            .replace("##TYPES##", spade_types)
            .replace("##BODY##", spade_body)
            .replace("##BINDINGS##", spade_bindings)
            .replace("##RETURN_PORTS##", spade_return_port)
    )


def main():
    parser = argparse.ArgumentParser(description="LiteDRAM standalone core generator")
    parser.add_argument("--spade_outdir")
    parser.add_argument("config", help="YAML config file")
    args = parser.parse_args()


    self_dir = pathlib.Path(__file__).parent.resolve()

    config_file = pathlib.Path(args.config)
    spade_stub = self_dir / "stubs" / "spade_stub.spade"

    spade_stub.stat().st_mtime

    out_spade = pathlib.Path(args.spade_outdir) / "sdram_controller.spade"

    # Check if any files need rebuilding
    targets_exists =  out_spade.exists()

    needs_rebuild = (not targets_exists) or any(
            map(
                lambda f: not f.exists() or f.stat().st_mtime > out_spade.stat().st_mtime,
                [config_file, spade_stub, pathlib.Path(__file__)]
            )
        )

    if not needs_rebuild:
        print("Sdram controller is up to date")
        return
    print("Building sddram controller")

    config = yaml.load(open(args.config).read(), Loader=yaml.Loader)

    spade = generate_files(config, spade_stub)

    if not os.path.exists(args.spade_outdir):
        os.mkdir(pathlib.Path(args.spade_outdir))

    with open(out_spade, 'w') as f:
        f.write(spade)

if __name__ == "__main__":
    main()
