use std::io::{self,BufReader};
use std::process::ExitCode;
fn main()->ExitCode {
 let budget=std::env::args().nth(1).expect("explicit budget").parse::<usize>().expect("usize budget");
 let worker=std::thread::Builder::new().stack_size(64*1024*1024).spawn(move||{
  match metatron_kernel::parser::parse(BufReader::new(io::stdin().lock())).and_then(|x|x.resolve()){
   Ok(export)=>metatron_kernel::checker::check_export(export,metatron_kernel::checker::Limits{judgment_steps:budget}).exit_code()as u8,
   Err(_)=>3,
  }
 }).expect("worker");
 ExitCode::from(worker.join().expect("checker thread"))
}
