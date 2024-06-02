fn main() {
    cxx_build::bridge("src/lib.rs")
        .compile("hdmi_visualizer");

    println!("cargo:rerun-if-changed=src/lib.rs");
}
