# Collatz ROS V123 — persistent lawful-future controller

**Universal Collatz: UNKNOWN. No QED.** This is an executable, source-attached
research controller, not a solver or a proof of universal convergence.

## The operating invariant (future chats: start here)

Stop measuring progress by parity-cylinder density, orbit-length records or
source-free rank. In V66, verified future coalescence is an equivalence
relation, and [T(n)]=[n]. Protected success is a *strictly earlier positive
source in the same future-coalescence class*.

**CLOSE** verified future-merger consequences. **REFINE** when a claimed
complete grammar fails on a protected residual. **NEVER PROMOTE** an UNKNOWN
unless exact source-guarded evidence and the declared proof authority pass.
**NEVER CONFUSE** a fixed-grammar failure with a nonconvergent integer.
The grammar itself is versioned, with a refinement and revocation boundary.

Normalized capability for each natural source n:

```text
source=n>1, earlier=p, 0<p<n,
sourceClock=a, earlierClock=b,
T^a(n)=T^b(p),
required support (exact run, SHA, proof-scope) and replayable witness.
```

The two clocks may differ. Monotone consequence closure composes
(n→p at a,b) with (p→q at c,d) to get (n→q at a+c,d+b).
This composition is formally checked in
[LawfulFutureJoin.lean](../formal/Collatz/LawfulFutureJoin.lean).
The already-established V66/V67 semantic quotient and lower-class merger
interface remain the *prior* authority, not reinvented theory.

## Frozen adversarial separators

- **27:** V121 proves no positive p<27 reaches F(27)=83 at ANY clock.
  V122 proves no future of any p<27 is contacted from 27 before its
  exact 59th shortcut step; T^59(27)=23. A grammar restricted to F(n)
  needs a genuinely new generator, not a larger reverse-search budget.
- **11 and 3:** T^6(11)=T(3)=5 despite no equal-clock F(3)/3
  collision. Equal-time certificates are not complete for asynchronous
  coalescence. Source 3 joins source 2 at clocks 4,0; compiling yields
  11→2 at 10,1 without repeating the orbit search.
- **2-adic ghosts:** n_K=2^K−1 follows K actual all-odd-prefix steps
  matching the negative 2-adic fixed point −1. The source n_K CHANGES
  with K. Such finite shadows are not fixed positive-natural infinite
  counterexamples. No naive compactness or density promotion.

The executable engine accepts only genuine positive-source, exact
two-clock joins, marks any unclosed case UNKNOWN, and retains all prior
warrants when adding a qualified constructor. Support revocation
reopens dependents; stale cached answers are not independent authority.

## Persistent state, restart, verification

- [Controller source](../research/collatz_ros_future_controller_v123.py)
- [Adversarial tests](../research/test_collatz_ros_future_controller_v123.py)
- [Hosted qualification](../.github/workflows/collatz-v123-stateful-future.yml)
- Canonical active ROS: Notion **Metalogic Research OS → Canonical Research
  State**, Collatz V123 checkpoint and Cold-Start Runbook.
- GitHub branch: `collatz-ros-lawful-future-controller-v123`.
- This branch descends from V122 exact-head
  `f6dec5d5ae9ae681868e1f0f29bbd494267c8bfd`
  (green Actions run `37975443683`).

From the repository root:

```bash
python3 -m unittest -v research.test_collatz_ros_future_controller_v123
python3 -m research.collatz_ros_future_controller_v123 --bootstrap --output evidence/v123-state.json
python3 -m research.collatz_ros_future_controller_v123 --input evidence/v123-state.json --output evidence/v123-restart.json
cmp evidence/v123-state.json evidence/v123-restart.json
python3 -m research.collatz_ros_future_controller_v123 --input evidence/v123-state.json --revoke-support v122_exact_first_join_27 --output evidence/v123-revoked.json
```

The exact live JSON checkpoint must be retained as a source-controlled
file after its CI qualification (do not confuse a GitHub Actions artifact
with a durable branch file). The CI workflow emits the snapshot, SHA256,
qualification certificate, and exact commit pin; it also independently
replays the formal Lean composition and seals the matched SHA.

Before resuming in another chat: READ the ROS checkpoint, load the
persisted JSON snapshot, confirm its GitHub SHA and latest green Actions
run, replay the protected tests, and only then extend the constructor
grammar or change the active proof obligation.

## Highest-leverage UNKNOWN

Prove that every hypothetical least positive natural in a second
future-coalescence class is eliminated by a **sound, source-admitted,
universally complete event producer** (or by an independent
natural-source viability contradiction). V85's conditional rank theorem
does not produce events; V103's trichotomy still includes nonzero
actual returns, unbounded fresh anchors, and nonterminal periodicity.
Finite grammar closure is not universal completeness.

**Next experiment:** Generate a protected future separator OUTSIDE the
current grammar and derive the smallest new *semantic law* needed.
Try a natural-source-viability classifier against n=27,
11/3 terminal phase mismatch, and 2-adic ghosts before claiming any
universal result. Require exact all-offset proofs for a claimed
source-family law, not just numeric samples.
