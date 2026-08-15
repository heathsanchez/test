from pathlib import Path

SESSION_BUDGET = 2_621_440


def patch_session_budget(root: str) -> None:
    p = Path(root) / "src/tc.rs"
    s = p.read_text()
    old = "const SESSION_BUDGET: usize = 1 << 20;"
    if old not in s:
        raise RuntimeError("expected SESSION_BUDGET definition not found")
    p.write_text(s.replace(old, f"const SESSION_BUDGET: usize = {SESSION_BUDGET};", 1))


def patch_level_cache(root: str) -> None:
    p = Path(root) / "src/util.rs"
    s = p.read_text()
    old = """pub struct ExprCache<'t> {
    pub(crate) inst_cache: FxHashMap<(ExprPtr<'t>, u16), ExprPtr<'t>>,
    pub(crate) subst_cache: FxHashMap<(ExprPtr<'t>, LevelsPtr<'t>, LevelsPtr<'t>), ExprPtr<'t>>,
    pub(crate) dsubst_cache: FxHashMap<(ExprPtr<'t>, LevelsPtr<'t>, LevelsPtr<'t>), ExprPtr<'t>>,
    pub(crate) simplify_cache: FxHashMap<LevelPtr<'t>, LevelPtr<'t>>,
}"""
    new = """pub struct ExprCache<'t> {
    pub(crate) inst_cache: FxHashMap<(ExprPtr<'t>, u16), ExprPtr<'t>>,
    pub(crate) subst_cache: FxHashMap<(ExprPtr<'t>, LevelsPtr<'t>, LevelsPtr<'t>), ExprPtr<'t>>,
    pub(crate) dsubst_cache: FxHashMap<(ExprPtr<'t>, LevelsPtr<'t>, LevelsPtr<'t>), ExprPtr<'t>>,
    pub(crate) simplify_cache: FxHashMap<LevelPtr<'t>, LevelPtr<'t>>,
    pub(crate) eq_cache: FxHashMap<(LevelPtr<'t>, LevelPtr<'t>), bool>,
}"""
    if old not in s:
        raise RuntimeError("ExprCache shape not found")
    s = s.replace(old, new, 1)

    old = """        shrink_map(&mut self.dsubst_cache);
        shrink_map(&mut self.simplify_cache);"""
    new = """        shrink_map(&mut self.dsubst_cache);
        shrink_map(&mut self.simplify_cache);
        shrink_map(&mut self.eq_cache);"""
    if old not in s:
        raise RuntimeError("ExprCache shrink block not found")
    s = s.replace(old, new, 1)

    old = """            dsubst_cache: small_fx_hash_map(),
            simplify_cache: small_fx_hash_map(),"""
    new = """            dsubst_cache: small_fx_hash_map(),
            simplify_cache: small_fx_hash_map(),
            eq_cache: small_fx_hash_map(),"""
    if old not in s:
        raise RuntimeError("ExprCache constructor block not found")
    p.write_text(s.replace(old, new, 1))

    p = Path(root) / "src/level.rs"
    s = p.read_text()
    old = """    pub fn eq_antisymm(&mut self, l: LevelPtr<'t>, r: LevelPtr<'t>) -> bool {
        l == r || (self.leq(l, r) && self.leq(r, l))
    }"""
    new = """    pub fn eq_antisymm(&mut self, l: LevelPtr<'t>, r: LevelPtr<'t>) -> bool {
        if l == r {
            return true;
        }
        let key = if l.get_hash() < r.get_hash() { (l, r) } else { (r, l) };
        if let Some(cached) = self.expr_cache.eq_cache.get(&key).copied() {
            return cached;
        }
        let eq = self.leq(l, r) && self.leq(r, l);
        self.expr_cache.eq_cache.insert(key, eq);
        eq
    }"""
    if old not in s:
        raise RuntimeError("eq_antisymm implementation not found")
    p.write_text(s.replace(old, new, 1))


patch_session_budget("a2")
patch_session_budget("e0012")
patch_level_cache("e0012")
