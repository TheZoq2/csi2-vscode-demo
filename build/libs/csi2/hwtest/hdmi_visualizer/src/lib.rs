mod event_queue;

use image::{io::Reader as ImageReader, GenericImageView};

use std::{io::Cursor, sync::Arc};

use event_queue::EventQueue;
use futures::executor::block_on;
use macroquad::{
    color::{Color, BLACK, GRAY},
    input::{is_quit_requested, prevent_quit},
    miniquad::conf::Platform,
    shapes::{draw_line, draw_rectangle},
    window::{clear_background, next_frame, Conf},
};
use tokio::sync::{
    broadcast::{channel, Sender},
    RwLock,
};
use anyhow::Result;

#[cxx::bridge(namespace = "ffi")]
mod ffi {
    extern "Rust" {
        fn new_state() -> Box<SimState>;

        fn start_gui(state: &SimState);

    }

    extern "Rust" {
        type RenderState;
    }

    extern "Rust" {
        type SimState;

        fn is_exited(&self) -> bool;
        fn push_pixel_read(&self, x: i16, y: i16, r: u8, g: u8, b: u8) -> Result<()>;
        fn push_addr_read(&self, avalon_id: u8, addr: u32) -> Result<()>;
        fn push_request_addr(&self, addr: u32) -> Result<()>;
        fn read_value(&self, addr: u32) -> u16;
    }
}

fn new_state() -> Box<SimState> {
    let shared = Shared {
        exit: Arc::new(RwLock::new(false)),
    };
    let (drawn_pixels_tx, _) = channel(1024 * 1024);
    let (read_addrs_tx, _) = channel(1024 * 1024);
    let (request_addrs_tx, _) = channel(1024 * 1024);

    let img = ImageReader::new(Cursor::new(include_bytes!("../test_image.jpg")))
        .with_guessed_format()
        .expect("Failed to get format")
        .decode()
        .expect("Failed to decode image");

    let pixels = img.pixels();

    let mut pairs = Box::new([[(128, 128); 600]; 512]);
    for (x, y, pixel) in pixels {
        let data = &mut pairs[x as usize / 2][y as usize];
        // NOTE: These colors make it seem like the image is read upside-down compared
        // to the datasheet
        let value = match ((x % 2) == 1, (y % 2) == 1) {
            (false, false) => pixel.0[0],
            (false, true) => pixel.0[1],
            (true, false) => pixel.0[1],
            (true, true) => pixel.0[2],
        };
        if x % 2 == 0 {
            data.0 = value;
        } else {
            data.1 = value;
        }
    }

    println!("Pixel data set up");

    let mut pixel_data = vec![0; 512 * 600];

    for addr in 0..512 * 600 {
        let (x, y) = x_y_from_addr(addr);
        let pair = pairs[x / 2][y];
        let value = ((pair.0 as u16) << 8) + pair.1 as u16;
        pixel_data[addr as usize] = value;
    }

    let sim = SimState {
        shared: shared.clone(),
        drawn_pixels_tx,
        read_addrs_tx,
        request_addrs_tx,
        pixel_data,
    };

    Box::new(sim)
}

#[derive(Clone)]
struct Shared {
    exit: Arc<RwLock<bool>>,
}

struct SimState {
    shared: Shared,
    drawn_pixels_tx: Sender<(i16, i16, (u8, u8, u8))>,
    read_addrs_tx: Sender<(u8, u32)>,
    request_addrs_tx: Sender<u32>,
    pixel_data: Vec<u16>,
}

impl SimState {
    fn create_render_state(&self) -> RenderState {
        RenderState {
            shared: self.shared.clone(),
            drawn_pixels: EventQueue::new(&self.drawn_pixels_tx),
            read_addrs: EventQueue::new(&self.read_addrs_tx),
            request_addrs: EventQueue::new(&self.request_addrs_tx),
        }
    }

    fn is_exited(&self) -> bool {
        *block_on(self.shared.exit.read())
    }

    fn push_pixel_read(&self, x: i16, y: i16, r: u8, g: u8, b: u8) -> Result<()>{
        self.drawn_pixels_tx.send((x, y, (r, g, b)))?;
        Ok(())
    }

    fn push_addr_read(&self, avalon_id: u8, addr: u32) -> Result<()> {
        self.read_addrs_tx.send((avalon_id, addr))?;
        Ok(())
    }
    fn push_request_addr(&self, addr: u32) -> Result<()> {
        self.request_addrs_tx.send(addr)?;
        Ok(())
    }
    fn read_value(&self, addr: u32) -> u16 {
        self.pixel_data
            .get(addr as usize)
            .cloned()
            .unwrap_or_else(|| {
                0xffff
            })
    }
}

struct RenderState {
    shared: Shared,
    drawn_pixels: EventQueue<(i16, i16, (u8, u8, u8)), { 1024 * 100 }>,
    read_addrs: EventQueue<(u8, u32), { 1024 * 100 }>,
    request_addrs: EventQueue<u32, { 1024 * 100 / 64 }>,
}

fn start_gui(state: &SimState) {
    println!("Starting GUI");

    let state = state.create_render_state();

    std::thread::spawn(|| {
        let config = Conf {
            window_resizable: true,
            platform: Platform {
                linux_backend: macroquad::miniquad::conf::LinuxBackend::WaylandOnly,
                ..Default::default()
            },
            window_title: "hdmi_visualizer".to_string(),
            ..Default::default()
        };
        println!("About to start macroquad");
        macroquad::Window::from_config(config, async {
            if let Err(e) = drawing_loop(state).await {
                println!("Exiting gui due to {e:#?}")
            }
        });
    });
}

async fn drawing_loop(mut state: RenderState) -> Result<()> {
    println!("Entering drawing loop");
    let mut color = vec![vec![BLACK; 1024]; 1024];
    loop {
        clear_background(BLACK);

        prevent_quit();
        if is_quit_requested() {
            *state.shared.exit.write().await = true;
            break Ok(());
        }

        state
            .drawn_pixels
            .process_with_cb(&mut |(x, y, (r, g, b))| {
                color
                    .get_mut(*x as usize)
                    .and_then(|row| row.get_mut(*y as usize))
                    .map(|c| {
                        c
                    })
                    .map(|c| *c = Color::new(*r as f32 / 255., *g as f32 / 255., *b as f32 / 255., 255.));
            })?;
        for (x, row) in color.iter().enumerate() {
            for (y, color) in row.iter().enumerate() {
                draw_rectangle(x as f32, y as f32, 1., 1., *color);
            }
        }

        for (i, (x, y, _)) in state.drawn_pixels.inner().iter().enumerate() {
            let a = ((i as f32 / state.drawn_pixels.inner().len() as f32) * 255.) as u8;
            draw_rectangle(*x as f32, *y as f32, 1., 1., Color::from_rgba(255, 0, 0, a))
        }

        let mem_offset = 500;
        draw_rectangle(mem_offset as f32, 0., 512., 600., GRAY);
        {
            state.read_addrs.process()?;
            let addrs = state.read_addrs.inner();
            for (i, (avalon_id, addr)) in addrs.iter().enumerate() {
                let x = addr % 512 + mem_offset;
                let y = addr / 512;
                let a = ((i as f32 / addrs.len() as f32) * 255.) as u8;
                let (r, g, b) = match avalon_id {
                    0 => (255, 0, 0),
                    1 => (0, 255, 0),
                    2 => (0, 0, 255),
                    3 => (255, 0, 255),
                    other => panic!("Unknow avalon id {other}"),
                };
                draw_rectangle(x as f32, y as f32, 1., 1., Color::from_rgba(r, g, b, a))
            }
        }
        {
            state.request_addrs.process()?;
            let addrs = state.request_addrs.inner();
            for (i, addr) in addrs.iter().enumerate() {
                let x = addr % 512 + mem_offset;
                let y = addr / 512;
                let a = ((i as f32 / addrs.len() as f32) * 255.) as u8;
                draw_rectangle(x as f32, y as f32, 1., 1., Color::from_rgba(0, 255, 0, a))
            }
        }

        let block_offset = 1100;

        let addrs = state.read_addrs.inner();
        for (i, (avalon_id, addr)) in addrs.iter().enumerate() {
            let a = ((i as f32 / addrs.len() as f32) * 255.) as u8;
            let (r, g, b) = match avalon_id {
                0 => (255, 0, 0),
                1 => (0, 255, 0),
                2 => (0, 0, 255),
                3 => (255, 0, 255),
                other => panic!("Unknow avalon id {other}"),
            };
            {
                let x = addr % 512 + mem_offset;
                let y = addr / 512;
                draw_rectangle(x as f32, y as f32, 1., 1., Color::from_rgba(r, g, b, a));
            }

            {
                let (x, y) = x_y_from_addr(*addr);

                draw_rectangle(
                    (x + block_offset) as f32,
                    y as f32,
                    1.,
                    1.,
                    Color::from_rgba(r, g, b, a),
                );
            }
        }

        for x in 0..=1024 / 16 {
            let x = x * 16 + block_offset;
            draw_line(x as f32, 0., x as f32, 600., 1., GRAY)
        }
        for y in 0..=600 / 8 {
            let x = block_offset;
            draw_line(
                x as f32,
                (y * 8) as f32,
                (x + block_offset) as f32,
                (y * 8) as f32,
                1.,
                GRAY,
            )
        }

        next_frame().await;
    }
}

fn x_y_from_addr(addr: u32) -> (usize, usize) {
    let block = addr / 64;
    let block_x = block % 64;
    let block_y = block / 64;

    // let in_block = block % 64;
    let in_block = addr % 64;
    let in_x = in_block % 8;
    let in_y = in_block / 8;

    let x = block_x * 16 + in_x * 2;
    let y = block_y * 8 + in_y;

    (x as usize, y as usize)
}
