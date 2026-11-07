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
                "unclosed":state.children.len(),"anomalies":state.anomalies,"top":top
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
            Some(Self { route, expr: usize::try_from(expr).unwrap_or(MAX_EXPR).min(MAX_EXPR),
                before: *counter })
        }).ok().flatten()
    }

    pub(crate) fn finish(self, after: usize) {
        STATE.with(|state| {
            let mut slot = state.borrow_mut();
            let state = slot.as_mut().expect("active declaration");
            let children = state.children.pop().expect("paired visit");
            let debit = self.before.saturating_sub(after);
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
