use std::collections::VecDeque;

use futures::executor::block_on;
use tokio::sync::broadcast::{Receiver, Sender, error::RecvError};

pub struct EventQueue<T, const LEN: usize>
where
    T: Clone,
{
    rx: Receiver<T>,
    content: VecDeque<T>,
}

impl<T, const LEN: usize> EventQueue<T, LEN>
where
    T: Clone,
{
    pub fn new(sender: &Sender<T>) -> Self {
        Self {
            rx: sender.subscribe(),
            content: VecDeque::new(),
        }
    }

    pub fn process_with_cb(&mut self, f: &mut impl FnMut(&T)) -> Result<(), RecvError> {
        while !self.rx.is_empty() {
            let recv =  block_on(self.rx.recv()).unwrap();
            f(&recv);
            self.content.push_back(recv);


            while self.content.len() > LEN {
                self.content.pop_front();
            }
        }
        Ok(())
    }
    pub fn process(&mut self) -> Result<(), RecvError>{
        self.process_with_cb(&mut |_| {})
    }

    pub fn inner(&self) -> &VecDeque<T> {
        &self.content
    }
}
