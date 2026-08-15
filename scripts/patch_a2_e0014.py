from pathlib import Path

SESSION_BUDGET = 2_621_440


def patch_session_budget(root: str) -> None:
    p = Path(root) / 'src/tc.rs'
    s = p.read_text()
    old = 'const SESSION_BUDGET: usize = 1 << 20;'
    assert old in s
    p.write_text(s.replace(old, f'const SESSION_BUDGET: usize = {SESSION_BUDGET};', 1))


def patch_two_way_prune_dm(root: str) -> None:
    p = Path(root) / 'src/util.rs'
    s = p.read_text()
    old = "    pub(crate) prune_dm: Box<[(usize, u64, Option<E<'a>>); PRUNE_DM_LEN]>,"
    new = old + "\n    pub(crate) prune_dm2: Box<[(usize, u64, Option<E<'a>>); PRUNE_DM_LEN]>,"
    assert old in s
    s = s.replace(old, new, 1)

    old = "            prune_dm: Box::new([(0, 0, None); PRUNE_DM_LEN]),"
    new = old + "\n            prune_dm2: Box::new([(0, 0, None); PRUNE_DM_LEN]),"
    assert old in s
    s = s.replace(old, new, 1)

    # Both full clear and session clear reset prune_dm; reset the second way too.
    old = "        self.prune_dm.fill((0, 0, None));"
    new = old + "\n        self.prune_dm2.fill((0, 0, None));"
    assert s.count(old) >= 2
    s = s.replace(old, new)
    p.write_text(s)

    p = Path(root) / 'src/eval.rs'
    s = p.read_text()
    old = '''        let ent = self.tc_cache.prune_dm[slot];
        if ent.0 == e as *const value::Env<'t> as usize && ent.1 == mask {
            if let Some(hit) = ent.2 {
                match e {
                    value::Env::Cons { prune, .. } | value::Env::Framed { prune, .. } =>
                        prune.set((mask, Some(hit))),
                    value::Env::Nil { .. } => {}
                }
                return hit;
            }
        }
        self.prune_env_cold(e, mask, slot)'''
    new = '''        let env_addr = e as *const value::Env<'t> as usize;
        let ent = self.tc_cache.prune_dm[slot];
        if ent.0 == env_addr && ent.1 == mask {
            if let Some(hit) = ent.2 {
                match e {
                    value::Env::Cons { prune, .. } | value::Env::Framed { prune, .. } =>
                        prune.set((mask, Some(hit))),
                    value::Env::Nil { .. } => {}
                }
                return hit;
            }
        }
        let ent2 = self.tc_cache.prune_dm2[slot];
        if ent2.0 == env_addr && ent2.1 == mask {
            if let Some(hit) = ent2.2 {
                match e {
                    value::Env::Cons { prune, .. } | value::Env::Framed { prune, .. } =>
                        prune.set((mask, Some(hit))),
                    value::Env::Nil { .. } => {}
                }
                return hit;
            }
        }
        self.prune_env_cold(e, mask, slot)'''
    assert old in s
    s = s.replace(old, new, 1)

    old = '''        self.tc_cache.prune_dm[slot] = (e as *const value::Env<'t> as usize, mask, Some(r));'''
    new = '''        self.tc_cache.prune_dm2[slot] = self.tc_cache.prune_dm[slot];
        self.tc_cache.prune_dm[slot] = (e as *const value::Env<'t> as usize, mask, Some(r));'''
    assert old in s
    s = s.replace(old, new, 1)
    p.write_text(s)


patch_session_budget('a2')
patch_session_budget('e0014')
patch_two_way_prune_dm('e0014')
