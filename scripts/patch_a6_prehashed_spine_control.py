from pathlib import Path

# Prehash-cost control: keep authoritative FxHashMap unchanged, but compute the
# candidate's exact prehash on every spine lookup and black-box it.

p=Path("a6/src/eval.rs")
s=p.read_text()

marker="fn elim_key<'a>(elim: &Elim<'a>) -> u64 {\n    const _: () = assert!(std::mem::align_of::<Value<'static>>() >= 8);\n    elim.raw()\n}\n"
insert=marker+"""
#[inline]
fn spine_hc_candidate_hash(prev_addr: usize, elim_key: u64) -> u64 {
    (prev_addr as u64)
        .wrapping_mul(0x9E3779B97F4A7C15)
        .rotate_left(23)
        ^ elim_key.wrapping_mul(0xBF58476D1CE4E5B9)
}
"""
assert marker in s
s=s.replace(marker,insert,1)

old="""    #[inline]
    fn spine_snoc_hc(&mut self, prev: S<'t>, elim: Elim<'t>) -> S<'t> {
        let key = (prev as *const Spine<'t> as usize, elim_key(&elim));
        let arena = self.arena;
"""
new="""    #[inline]
    fn spine_snoc_hc(&mut self, prev: S<'t>, elim: Elim<'t>) -> S<'t> {
        let key = (prev as *const Spine<'t> as usize, elim_key(&elim));
        let _prehash = std::hint::black_box(spine_hc_candidate_hash(key.0, key.1));
        let arena = self.arena;
"""
assert old in s
s=s.replace(old,new,1)
p.write_text(s)
