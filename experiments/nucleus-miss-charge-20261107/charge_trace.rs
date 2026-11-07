//! Attribution for decrements of the active declaration's actual work counter.
use std::cell::RefCell;
use std::collections::{HashMap, HashSet};

const MAX_MISS_KEYS: usize = 262_145;
const MISS_CLASSES: [&str; 5] = [
    "first_expression", "new_frame_for_seen_expression", "previous_unproven",
    "previous_active", "previous_proven",
];

#[derive(Clone, Copy)]
enum Status {
    Active,
    Unproven,
    Proven,
}

#[derive(Default)]
struct MissRow {
    distinct_frames: usize,
    debit: [usize; 5],
    samples: Vec<serde_json::Value>,
}

#[derive(Default)]
struct Marker {
    hit: bool,
    miss: Option<((u64,u64),usize)>,
}

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
    markers: Vec<Marker>,
    cache_addresses: HashSet<usize>,
    miss_keys: HashMap<(u64,u64), Status>,
    miss_rows: HashMap<u64, MissRow>,
    miss_debits: [usize; 5],
    miss_overflow: usize,
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
                markers: Vec::new(),
                cache_addresses: HashSet::new(),
                miss_keys: HashMap::new(),
                miss_rows: HashMap::new(),
                miss_debits: [0; 5],
                miss_overflow: 0,
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
            let mut misses: Vec<_> = state.miss_rows.into_iter().collect();
            misses.sort_unstable_by_key(|(expr,row)| (std::cmp::Reverse(row.debit.iter().sum::<usize>()), *expr));
            let miss_rows: Vec<_> = misses.into_iter().map(|(expr,row)| serde_json::json!({
                "expression":expr,"distinct_frames":row.distinct_frames,
                "miss_debit":row.debit.iter().sum::<usize>(),
                "class_debits":row.debit,"samples":row.samples
            })).collect();
            eprintln!("NUCLEUS_CLOSED_ACTIVATION:{}", serde_json::json!({
                "stage":"theorem.value", "root_debit":state.roots,
                "exclusive_by_route":route_totals, "route_names":ROUTES,
                "unclosed":state.children.len()+state.beta_depth,"anomalies":state.anomalies,"top":top,
                "beta_entries":state.beta_entries,
                "infer_class_names":["outside_replay_miss","outside_replay_hit","inside_replay_miss","inside_replay_hit"],
                "infer_class_debit":state.infer_class_debit,
                "cache_addresses":state.cache_addresses.len(),"miss_overflow":state.miss_overflow,
                "distinct_miss_keys":state.miss_keys.len(),"miss_classes":MISS_CLASSES,
                "miss_debits":state.miss_debits,"miss_rows":miss_rows
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
            state.markers.push(Marker::default());
            Some(Self { route, expr: usize::try_from(expr).unwrap_or(MAX_EXPR).min(MAX_EXPR),
                before: *counter })
        }).ok().flatten()
    }

    pub(crate) fn finish(self, after: usize) {
        self.finish_impl(after, None);
    }

    pub(crate) fn finish_infer(self, after: usize, proven: bool) {
        self.finish_impl(after, Some(proven));
    }

    fn finish_impl(self, after: usize, proven: Option<bool>) {
        STATE.with(|state| {
            let mut slot = state.borrow_mut();
            let state = slot.as_mut().expect("active declaration");
            let children = state.children.pop().expect("paired visit");
            let marker = state.markers.pop().expect("paired inference marker");
            let debit = self.before.saturating_sub(after);
            if self.route == 1 {
                let class = usize::from(state.beta_depth > 0) * 2 + usize::from(marker.hit);
                state.infer_class_debit[class] += debit.saturating_sub(children);
                if let Some((key, kind)) = marker.miss {
                    let exclusive = debit.saturating_sub(children);
                    state.miss_debits[kind] += exclusive;
                    state.miss_rows.get_mut(&key.0).expect("recorded miss").debit[kind] += exclusive;
                    let status = if proven.expect("ordinary inference result") {
                        Status::Proven
                    } else {
                        Status::Unproven
                    };
                    state.miss_keys.insert(key, status);
                }
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

pub(crate) fn classify_infer(
    counter: &mut usize, cache: usize, expr: u64, frame: u64, hit: bool,
    sample: impl FnOnce() -> serde_json::Value,
) {
    let identity = counter as *mut usize as usize;
    STATE.with(|state| {
        let mut slot = state.borrow_mut();
        let Some(state) = slot.as_mut() else { return };
        if state.counter != Some(identity) {
            return;
        }
        state.cache_addresses.insert(cache);
        let marker = state.markers.last_mut().expect("wrapped ordinary inference");
        marker.hit = hit;
        if hit {
            return;
        }
        let key = (expr,frame);
        let prior = state.miss_keys.get(&key).copied();
        if prior.is_none() && state.miss_keys.len() >= MAX_MISS_KEYS {
            state.miss_overflow += 1;
            return;
        }
        let row = state.miss_rows.entry(expr).or_default();
        let kind = match prior {
            Some(Status::Unproven) => 2,
            Some(Status::Active) => 3,
            Some(Status::Proven) => 4,
            None => {
                let class = usize::from(row.distinct_frames != 0);
                row.distinct_frames += 1;
                if row.samples.len() < 3 {
                    row.samples.push(serde_json::json!({"frame":frame,"scope":sample()}));
                }
                class
            }
        };
        state.miss_keys.insert(key, Status::Active);
        marker.miss = Some((key,kind));
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
