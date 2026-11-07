//! Attribution for decrements of the active declaration's actual work counter.
use std::cell::RefCell;

const MAX_EXPR: usize = 12_000;
const ROUTES: [&str; 3] = ["check", "ordinary_infer", "exact_infer"];

#[derive(Clone, Copy, Default)]
struct Entry {
    calls: u64,
    exclusive: usize,
}

struct State {
    counter: Option<usize>,
    children: Vec<usize>,
    rows: [Vec<Entry>; 3],
    roots: usize,
    anomalies: usize,
    beta_depth: usize,
    beta_entries: usize,
    infer_class_debit: [usize; 4],
    hit_by_visit: Vec<bool>,
}

thread_local! {
    static STATE: RefCell<Option<State>> = const { RefCell::new(None) };
}

pub(crate) struct Scope;

impl Scope {
    pub(crate) fn enter() -> Self {
        STATE.with(|state| {
            assert!(state.borrow().is_none());
            state.replace(Some(State {
                counter: None,
                children: Vec::new(),
                rows: std::array::from_fn(|_| vec![Entry::default(); MAX_EXPR + 1]),
                roots: 0,
                anomalies: 0,
                beta_depth: 0,
                beta_entries: 0,
                infer_class_debit: [0; 4],
                hit_by_visit: Vec::new(),
            }));
        });
        Self
    }
}

impl Drop for Scope {
    fn drop(&mut self) {
        if let Ok(Some(state)) = STATE.try_with(|s| s.replace(None)) {
            let mut ranked = Vec::new();
            let mut route_totals = [0usize; 3];
            for (route, rows) in state.rows.iter().enumerate() {
                for (expr, row) in rows.iter().enumerate() {
                    route_totals[route] += row.exclusive;
                    if row.exclusive != 0 {
                        ranked.push((row.exclusive, route, expr, row.calls));
                    }
                }
            }
            ranked.sort_unstable_by(|a, b| b.cmp(a));
            let top: Vec<_> = ranked.into_iter().take(24).map(|(steps, route, expr, calls)| {
                serde_json::json!({"route": ROUTES[route], "expression": expr,
                    "exclusive_debit": steps, "calls": calls})
            }).collect();
            eprintln!("NUCLEUS_CLOSED_ACTIVATION:{}", serde_json::json!({
                "stage":"theorem.value", "root_debit":state.roots,
                "exclusive_by_route":route_totals, "route_names":ROUTES,
                "unclosed":state.children.len()+state.beta_depth,"anomalies":state.anomalies,"top":top,
                "beta_entries":state.beta_entries,
                "infer_class_names":["outside_replay_miss","outside_replay_hit","inside_replay_miss","inside_replay_hit"],
                "infer_class_debit":state.infer_class_debit
            }));
        }
    }
}

pub(crate) struct Visit {
    route: usize,
    expr: usize,
    before: usize,
}

impl Visit {
    pub(crate) fn begin(route: usize, expr: u64, counter: &mut usize) -> Option<Self> {
        let identity = counter as *mut usize as usize;
        STATE.try_with(|state| {
            let mut slot = state.borrow_mut();
            let state = slot.as_mut()?;
            if route == 0 && state.counter.is_none() {
                state.counter = Some(identity);
            }
            if state.counter != Some(identity) {
                return None;
            }
            state.children.push(0);
            state.hit_by_visit.push(false);
            Some(Self { route, expr: usize::try_from(expr).unwrap_or(MAX_EXPR).min(MAX_EXPR),
                before: *counter })
        }).ok().flatten()
    }

    pub(crate) fn finish(self, after: usize) {
        STATE.with(|state| {
            let mut slot = state.borrow_mut();
            let state = slot.as_mut().expect("active declaration");
            let children = state.children.pop().expect("paired visit");
            let hit = state.hit_by_visit.pop().expect("paired inference marker");
            let debit = self.before.saturating_sub(after);
            if self.route == 1 {
                let class = usize::from(state.beta_depth > 0) * 2 + usize::from(hit);
                state.infer_class_debit[class] += debit.saturating_sub(children);
            }
            if after > self.before || children > debit {
                state.anomalies += 1;
            }
            let row = &mut state.rows[self.route][self.expr];
            row.calls += 1;
            row.exclusive += debit.saturating_sub(children);
            if let Some(parent) = state.children.last_mut() {
                *parent += debit;
            } else {
                state.roots += debit;
            }
        });
    }
}

pub(crate) fn classify_infer(counter: &mut usize, hit: bool) {
    let identity = counter as *mut usize as usize;
    STATE.with(|state| {
        if let Some(state) = state.borrow_mut().as_mut() {
            if state.counter == Some(identity) {
                *state.hit_by_visit.last_mut().expect("wrapped ordinary inference") = hit;
            }
        }
    });
}

pub(crate) struct Beta;

impl Beta {
    pub(crate) fn enter(counter: &mut usize) -> Option<Self> {
        let identity = counter as *mut usize as usize;
        STATE.with(|state| {
            let mut state = state.borrow_mut();
            let state = state.as_mut()?;
            if state.counter != Some(identity) {
                return None;
            }
            state.beta_depth += 1;
            state.beta_entries += 1;
            Some(Self)
        })
    }
}

impl Drop for Beta {
    fn drop(&mut self) {
        STATE.with(|state| {
            state.borrow_mut().as_mut().expect("active beta replay").beta_depth -= 1;
        });
    }
}
