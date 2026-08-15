from pathlib import Path

SESSION_BUDGET = 2_621_440


def patch_session_budget(root: str) -> None:
    p = Path(root) / "src/tc.rs"
    s = p.read_text()
    old = "const SESSION_BUDGET: usize = 1 << 20;"
    if old not in s:
        raise RuntimeError("expected SESSION_BUDGET definition not found")
    p.write_text(s.replace(old, f"const SESSION_BUDGET: usize = {SESSION_BUDGET};", 1))


def patch_spine_length(root: str) -> None:
    p = Path(root) / "src/conv.rs"
    s = p.read_text()
    old = """        if std::ptr::eq(sx, sy) {
            return true;
        }
        match (sx, sy) {"""
    new = """        if std::ptr::eq(sx, sy) {
            return true;
        }
        if sx.len() != sy.len() {
            return false;
        }
        match (sx, sy) {"""
    if old not in s:
        raise RuntimeError("expected spine comparison block not found")
    p.write_text(s.replace(old, new, 1))


patch_session_budget("a2")
patch_session_budget("e0013")
patch_spine_length("e0013")
