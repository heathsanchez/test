use std::cell::RefCell;
thread_local! {static ACTIVE:RefCell<Option<Vec<bool>>>=const{RefCell::new(None)};}
pub(crate) struct SnapshotGuard{previous:Option<Vec<bool>>}
impl SnapshotGuard{
 pub(crate) fn enter()->Self{let flags=KEYS.iter().map(|k|std::env::var_os(k).is_some()).collect();Self::enter_values(flags)}
 fn enter_values(flags:Vec<bool>)->Self{Self{previous:ACTIVE.with(|s|s.replace(Some(flags)))}}
}
impl Drop for SnapshotGuard{fn drop(&mut self){ACTIVE.with(|s|{s.replace(self.previous.take());});}}
#[inline]pub(crate) fn enabled(slot:usize,key:&str)->bool{ACTIVE.with(|s|match s.borrow().as_ref(){Some(flags)=>flags[slot],None=>std::env::var_os(key).is_some()})}
#[cfg(test)]mod settings_snapshot_tests{
 use super::*;
 #[test]fn nested_scopes_restore_settings(){let key=KEYS[0];let outer=SnapshotGuard::enter_values(vec![false;KEYS.len()]);assert!(!enabled(0,key));{let _inner=SnapshotGuard::enter_values(vec![true;KEYS.len()]);assert!(enabled(0,key));}assert!(!enabled(0,key));drop(outer);assert_eq!(enabled(0,key),std::env::var_os(key).is_some());}
 #[test]fn unwinding_restores_previous_scope(){let _outer=SnapshotGuard::enter_values(vec![false;KEYS.len()]);let _=std::panic::catch_unwind(||{let _inner=SnapshotGuard::enter_values(vec![true;KEYS.len()]);panic!("test unwind");});assert!(!enabled(0,KEYS[0]));}
 #[test]fn independent_threads_do_not_share_snapshots(){let _guard=SnapshotGuard::enter_values(vec![true;KEYS.len()]);assert!(enabled(0,KEYS[0]));std::thread::spawn(||{let _g=SnapshotGuard::enter_values(vec![false;KEYS.len()]);assert!(!enabled(0,KEYS[0]));}).join().unwrap();assert!(enabled(0,KEYS[0]));}
}
