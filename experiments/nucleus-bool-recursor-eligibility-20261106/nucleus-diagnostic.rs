use std::{io::{self,BufReader},process::ExitCode};
fn main()->ExitCode{std::thread::Builder::new().stack_size(64*1024*1024).spawn(||{
 let steps=std::env::args().nth(1).expect("explicit diagnostic step limit").parse().unwrap();
 let verdict=match metatron_kernel::parser::parse(BufReader::new(io::stdin().lock())).and_then(|e|e.resolve()){
  Ok(e)=>metatron_kernel::checker::check_export(e,metatron_kernel::checker::Limits{judgment_steps:steps}),
  Err(_)=>metatron_kernel::verdict::Verdict::Error,
 };
 eprintln!("diagnostic_steps={steps}:verdict={verdict:?}");ExitCode::from(verdict.exit_code() as u8)
}).unwrap().join().unwrap()}
