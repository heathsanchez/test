//! Observation scoped to the failing chain9 declaration.
use std::cell::RefCell;

struct Counts {
    owner: String,
    stage: &'static str,
    events: [u64; 10],
    work_before: usize,
    work_after: usize,
    min_remaining: usize,
}

thread_local! {
    static COUNTS: RefCell<Option<Counts>> = const { RefCell::new(None) };
}

pub(crate) struct Scope(Option<Counts>);

impl Scope {
    pub(crate) fn enter(owner: String, stage: &'static str) -> Self {
        Self(COUNTS.with(|counts| counts.replace(Some(Counts {
            owner, stage, events: [0; 10], work_before: 0,
            work_after: 0, min_remaining: usize::MAX,
        }))))
    }
}

impl Drop for Scope {
    fn drop(&mut self) {
        if let Ok(Some(c)) = COUNTS.try_with(|counts| counts.replace(self.0.take())) {
            let [decline, sort_value, pi_value, term_other, term_const, term_sort,
                policy_reject, insertion, slot_reject, hit] = c.events;
            eprintln!("NUCLEUS_CLOSED_ACTIVATION:{}", serde_json::json!({
                "owner": c.owner, "stage": c.stage,
                "producer": {"decline": decline, "sort_value": sort_value,
                    "pi_value": pi_value, "term_other": term_other,
                    "term_const": term_const, "term_sort": term_sort},
                "policy_or_epoch_reject": policy_reject, "inserted": insertion,
                "no_reclaimable_slot": slot_reject, "tagged_hits": hit,
                "producer_work_before_sum": c.work_before,
                "producer_work_after_sum": c.work_after,
                "producer_min_remaining_after": if c.min_remaining == usize::MAX {
                    None
                } else { Some(c.min_remaining) },
            }));
        }
    }
}

pub(crate) fn active() -> bool {
    COUNTS.try_with(|counts| counts.borrow().is_some()).unwrap_or(false)
}

pub(crate) fn event(index: usize) {
    let _ = COUNTS.try_with(|counts| {
        if let Some(c) = counts.borrow_mut().as_mut() { c.events[index] += 1; }
    });
}

pub(crate) fn producer(kind: usize, before: usize, after: usize) {
    COUNTS.with(|counts| {
        if let Some(c) = counts.borrow_mut().as_mut() {
            c.events[kind] += 1;
            c.work_before = c.work_before.saturating_add(before);
            c.work_after = c.work_after.saturating_add(after);
            c.min_remaining = c.min_remaining.min(after);
        }
    });
}
