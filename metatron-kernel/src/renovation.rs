//! First source-defined fragment of the 3.2 kernel interface.
//! A direct contradiction of an explicit feature's necessary conditions
//! warrants rejection. Acceptance is separate: a whole-export declaration
//! reconstruction must discharge every obligation of the admitted fragment.
//! Rules from lean4#16595, beta toolchain 55bd690fabf6bef8dc50a63f4e3b34ce17556045:
//! init_K_target, init_projs_eta, check_large_elim, is_rec,
//! mutual block flags and omission of small-elimination computation rules.
use serde_json::Value;
use std::{collections::HashSet, io::{BufRead, Read}};

mod nullary;

type Checked<T> = Result<T, &'static str>;

const FEATURE_KEYS: [&str; 5] = [
    "isImpredicative", "isK", "hasProjections", "hasEta", "hasLargeElim",
];

pub(crate) fn has_feature_fields(item: &Value) -> bool {
    FEATURE_KEYS.iter().any(|key| item.get(*key).is_some())
}

/// Inspect only a bounded initial prefix of a version-3.1 stream. Never
/// rewrite its metadata or discard a byte. Later flagged blocks that were
/// not observed here are refused by the legacy inductive parser.
pub(crate) fn probe_legacy<R: BufRead>(reader: &mut R) -> std::io::Result<(Vec<u8>, bool)> {
    const CAP: usize = 64 * 1024;
    let mut prefix = Vec::new();
    while prefix.len() < CAP {
        let start = prefix.len();
        let n = (&mut *reader).take((CAP - start) as u64).read_until(b'\n', &mut prefix)?;
        if n == 0 { break; }
        let line = &prefix[start..];
        if line.last() != Some(&b'\n') && prefix.len() == CAP { break; }
        let Ok(row) = serde_json::from_slice::<Value>(line) else { break; };
        if let Some(block) = row.get("inductive") {
            let flagged = block.get("types").and_then(Value::as_array)
                .is_some_and(|types| types.iter().any(has_feature_fields));
            return Ok((prefix, flagged));
        }
    }
    Ok((prefix, false))
}

#[derive(Clone, Copy)]
struct Features {
    imp: bool,
    k: bool,
    projections: bool,
    eta: bool,
    large: bool,
}

impl Features {
    fn read(v: &Value) -> Checked<Self> {
        Ok(Self {
            imp: boolean(v, "isImpredicative")?,
            k: boolean(v, "isK")?,
            projections: boolean(v, "hasProjections")?,
            eta: boolean(v, "hasEta")?,
            large: boolean(v, "hasLargeElim")?,
        })
    }

    fn direct_refutation(self) -> Option<&'static str> {
        if self.eta && !self.projections {
            Some("eta-without-projections")
        } else if self.imp && self.projections {
            Some("impredicative-projections")
        } else if self.imp && self.large {
            Some("impredicative-large")
        } else {
            None
        }
    }
}

fn boolean(v: &Value, key: &str) -> Checked<bool> {
    v.get(key).and_then(Value::as_bool).ok_or("missing or nonboolean feature")
}

fn integer(v: &Value) -> Checked<usize> {
    v.as_u64().and_then(|n| usize::try_from(n).ok()).ok_or("invalid natural ID")
}
fn number(v: &Value, key: &str) -> Checked<usize> {
    integer(v.get(key).ok_or("missing integer")?)
}
fn array<'a>(v: &'a Value, key: &str) -> Checked<&'a Vec<Value>> {
    v.get(key).and_then(Value::as_array).ok_or("missing array")
}

// A universe assignment is a genuine finite witness, not a guessed normalized
// form. At the all-zero and all-one parameter assignments, exact zero/nonzero
// is closed under succ/max/imax. imax(a,b)=0 iff b=0.
#[derive(Clone, Copy)]
struct Zeros { at_zero: bool, at_one: bool }
const ZERO: Zeros = Zeros { at_zero: true, at_one: true };

fn level_at(levels: &[Option<Zeros>], id: &Value) -> Option<Zeros> {
    levels.get(integer(id).ok()?).copied().flatten()
}
fn read_level(v: &Value, levels: &[Option<Zeros>]) -> Option<Zeros> {
    if let Some(p) = v.get("param") {
        integer(p).ok()?;
        Some(Zeros { at_zero: true, at_one: false })
    } else if let Some(s) = v.get("succ") {
        level_at(levels, s)?;
        Some(Zeros { at_zero: false, at_one: false })
    } else if let Some(a) = v.get("max").and_then(Value::as_array) {
        if a.len() != 2 { return None; }
        let l = level_at(levels, &a[0])?;
        let r = level_at(levels, &a[1])?;
        Some(Zeros { at_zero: l.at_zero && r.at_zero, at_one: l.at_one && r.at_one })
    } else if let Some(a) = v.get("imax").and_then(Value::as_array) {
        if a.len() != 2 { return None; }
        level_at(levels, &a[0])?;
        level_at(levels, &a[1])
    } else {
        None
    }
}

fn telescope(exprs: &[Value], mut id: usize) -> Checked<(Vec<usize>, &Value)> {
    let mut domains = Vec::new();
    loop {
        let row = exprs.get(id).ok_or("unresolved telescope expression")?;
        if let Some(pi) = row.get("forallE") {
            let domain = number(pi, "type")?;
            let body = number(pi, "body")?;
            if domain >= id || body >= id {
                return Err("forward or cyclic telescope edge");
            }
            domains.push(domain);
            id = body;
        } else {
            return Ok((domains, row));
        }
    }
}

fn contains_family(exprs: &[Value], domains: &[usize], names: &HashSet<usize>) -> Checked<bool> {
    let mut pending = domains.to_vec();
    let mut seen = HashSet::new();
    while let Some(id) = pending.pop() {
        if !seen.insert(id) { continue; }
        let row = exprs.get(id).ok_or("unresolved recursive occurrence")?;
        if let Some(c) = row.get("const") {
            if names.contains(&number(c, "name")?) { return Ok(true); }
        }
        for (tag, fields) in [
            ("app", &["fn", "arg"][..]),
            ("forallE", &["type", "body"][..]),
            ("lam", &["type", "body"][..]),
            ("letE", &["type", "value", "body"][..]),
            ("proj", &["struct"][..]),
        ] {
            if let Some(node) = row.get(tag) {
                for field in fields {
                    // Unknown forms are not a witness of recursion.
                    if let Some(edge) = node.get(*field) {
                        let child = integer(edge)?;
                        if child >= id { return Err("forward or cyclic expression edge"); }
                        pending.push(child);
                    }
                }
            }
        }
    }
    Ok(false)
}

fn check_block(block: &Value, exprs: &[Value], levels: &[Option<Zeros>]) -> Checked<Option<&'static str>> {
    let types = array(block, "types")?;
    let constructors = array(block, "ctors")?;
    let recursors = array(block, "recs")?;
    if types.is_empty() { return Err("empty inductive block"); }
    let flags: Vec<Features> = types.iter().map(Features::read).collect::<Checked<_>>()?;
    let first = flags[0];
    if flags.iter().any(|f| f.imp != first.imp) { return Ok(Some("mutual-impredicativity")); }
    if flags.iter().any(|f| f.large != first.large) { return Ok(Some("mutual-large-elimination")); }

    let names = types.iter().map(|t| number(t, "name")).collect::<Checked<HashSet<_>>>()?;
    let mut recursive = false;
    if flags.iter().any(|f| f.eta) {
        for ctor in constructors {
            let (domains, _) = telescope(exprs, number(ctor, "type")?)?;
            recursive |= contains_family(exprs, &domains, &names)?;
        }
    }
    for (t, f) in types.iter().zip(flags.iter().copied()) {
        if let Some(reason) = f.direct_refutation() { return Ok(Some(reason)); }
        let ctors = array(t, "ctors")?;
        let num_params = number(t, "numParams")?;
        let (domains, tail) = telescope(exprs, number(t, "type")?)?;
        let result = tail.get("sort").and_then(|s| level_at(levels, s));
        if f.imp && result.is_some_and(|z| !z.at_one) {
            return Ok(Some("impredicative-nonprop"));
        }
        if f.projections && ctors.len() != 1 {
            return Ok(Some("projection-constructor-count"));
        }
        if f.projections && domains.len() > num_params {
            return Ok(Some("projection-indexed"));
        }
        if f.eta && recursive { return Ok(Some("recursive-eta")); }
        if f.large && result.is_some_and(|z| z.at_zero)
            && (types.len() != 1 || !(ctors.is_empty() || (ctors.len() == 1 && (f.eta || f.k)))) {
            return Ok(Some("large-elimination-prop-shape"));
        }
        if f.k {
            if types.len() != 1 || ctors.len() != 1 || result.is_some_and(|z| !z.at_one) {
                return Ok(Some("invalid-k-shape"));
            }
            let owner = integer(&ctors[0])?;
            for ctor in constructors {
                if number(ctor, "name")? == owner {
                    if telescope(exprs, number(ctor, "type")?)?.0.len() > num_params {
                        return Ok(Some("k-with-fields"));
                    }
                }
            }
        }
        // Only the unambiguous, single, non-nested recursor boundary here.
        if types.len() == 1 && number(t, "numNested")? == 0 && recursors.len() == 1
            && boolean(&recursors[0], "k")? != f.k {
            return Ok(Some("k-recursor-flag"));
        }
    }
    if !first.large {
        for rec in recursors {
            if !array(rec, "rules")?.is_empty() { return Ok(Some("small-elimination-rules")); }
        }
    }
    Ok(None)
}

#[derive(Debug, PartialEq, Eq)]
pub(crate) enum Outcome { AcceptNullary, Reject(&'static str), Unknown }

/// Read an already identified renovated stream. Preserve the old refutation
/// fragment. ACCEPT only if a separate complete declaration reconstruction
/// admits the entire canonical export; otherwise return UNKNOWN.
pub(crate) fn check<R: BufRead>(reader: R, canonical_header: bool) -> Checked<Outcome> {
    let mut whole_export = canonical_header.then(Vec::<Value>::new);
    let mut levels = vec![Some(ZERO)];
    let mut exprs = Vec::<Value>::new();
    let mut next_name = 1usize;
    for line in reader.lines() {
        let text = line.map_err(|_| "input read error")?;
        let row: Value = serde_json::from_str(&text).map_err(|_| "invalid JSON")?;
        if !row.is_object() || row.get("meta").is_some() { return Err("invalid record"); }
        // An exact canonical JSON round trip also excludes duplicate keys
        // from the acceptance fragment (they would disappear in Value).
        if let Some(rows) = whole_export.as_mut() {
            if rows.len() < nullary::MAX_RECORDS &&
                serde_json::to_string(&row).ok().as_deref() == Some(text.as_str()) {
                rows.push(row.clone());
            } else {
                whole_export = None;
            }
        }
        if let Some(n) = row.get("in") {
            if integer(n)? != next_name { return Err("nonconsecutive name IDs"); }
            next_name = next_name.checked_add(1).ok_or("name ID overflow")?;
        } else if let Some(n) = row.get("il") {
            if integer(n)? != levels.len() { return Err("nonconsecutive level IDs"); }
            levels.push(read_level(&row, &levels));
        } else if let Some(n) = row.get("ie") {
            if integer(n)? != exprs.len() { return Err("nonconsecutive expression IDs"); }
            exprs.push(row);
        } else if let Some(block) = row.get("inductive") {
            if let Some(reason) = check_block(block, &exprs, &levels)? { return Ok(Outcome::Reject(reason)); }
        }
    }
    if whole_export.as_ref().is_some_and(|rows| nullary::admits(rows)) {
        Ok(Outcome::AcceptNullary)
    } else {
        Ok(Outcome::Unknown)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn direct_features_are_necessary_not_sufficient() {
        let off = Features { imp:false, k:false, projections:false, eta:false, large:false };
        assert_eq!(off.direct_refutation(), None);
        assert_eq!(Features { eta:true, ..off }.direct_refutation(), Some("eta-without-projections"));
        assert_eq!(Features { imp:true, projections:true, ..off }.direct_refutation(), Some("impredicative-projections"));
        assert_eq!(Features { imp:true, large:true, ..off }.direct_refutation(), Some("impredicative-large"));
    }
    #[test]
    fn no_warrant_from_empty_or_malformed_new_input() {
        assert_eq!(check(std::io::Cursor::new(b""), true), Ok(Outcome::Unknown));
        assert!(check(std::io::Cursor::new(b"{\"ie\":2,\"sort\":0}\n"), true).is_err());
    }
}
