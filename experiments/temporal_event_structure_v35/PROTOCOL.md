# Temporal Event-Structure Genesis V35 — Frozen Protocol

## Question

Can V34's fixed-length, one-symbol-per-step reference result survive when the raw boundary is a variable-length binary microstream and no macro-event boundary, event position, motif, window, or coordinate-address instruction is supplied?

V35 does not attempt presuppositionless event genesis. It keeps binary micro-symbols and their order. It removes the assumption that a consequential event is one particular micro-symbol at one particular position.

The kernel receives a complete finite consequence table over all binary microstreams up to a declared training length. It must construct the smallest recurrent residual machine it can warrant from future consequence alone.

## Frozen substrate

The input is only a variable-length stream over the anonymous alphabet `{0,1}` plus authoritative consequence at possible stopping points.

There are no supplied:

- event boundaries;
- event names;
- absolute position reads;
- fixed windows;
- motifs or substring detectors;
- tuple/pair constructors;
- history registers;
- domain semantics.

The executable hypothesis is only a deterministic finite machine whose current state has an externally verified consequence label and whose sole transition consumes the next anonymous symbol.

## Residual construction

For an anonymous prefix `p`, and a finite suffix probe family `E_h` containing all suffixes of length at most `h`, define its observed future-consequence signature:

    R_h(p) = ( C(p ++ s) )_{s in E_h}.

Two prefixes are provisionally the same present exactly when these complete observed consequence vectors agree.

The kernel searches the distinguishing horizon `h` from the weakest to stronger future views. A candidate quotient is admitted only if:

1. every prefix in the same residual class has the same current consequence;
2. consuming `0` from any representative of a class reaches one unique residual class;
3. consuming `1` likewise reaches one unique residual class;
4. the resulting recurrent machine exactly replays the entire complete training table.

Among admitted residual quotients, the kernel selects minimum state count, then minimum distinguishing horizon.

The post-freeze evaluator tests longer streams than the training horizon. Thus a finite prefix memorizer is insufficient when a recurrent structure is required.

## Scientific target

If V35 passes, the claim is bounded:

> within a finite binary sequential substrate, consequence can identify recurrent state transitions whose stable loops and multi-step paths are naturally interpretable after the fact as temporally extended events, without the kernel receiving event boundaries, event locations, fixed windows, or named pattern detectors.

A state-preserving micro-symbol is consequentially ignorable in that state. A state-changing micro-symbol changes the residual future. A multi-step event is represented by a path through intermediate residual states. Variable duration is represented by self-loops inside that path.

## Frozen gates

E1. Frozen scientific core remains byte-identical after hidden worlds are committed.
E2. One frozen kernel exactly replays every complete post-freeze training world.
E3. Every learned machine exactly transfers to a longer held-out stream horizon.
E4. Constant consequence contracts to one recurrent state.
E5. A position-free trigger is represented by two states: irrelevant micro-symbols self-loop until the decisive transition occurs.
E6. A recurrent parity world requires two persistent states rather than a positional memory register.
E7. A two-microstep consequential structure requires a third intermediate residual state.
E8. A three-microstep consequential structure requires a deeper residual and four states.
E9. A variable-duration structure contains an internal self-loop that preserves the unfinished residual across arbitrary duration.
E10. The same learned structure is recognized at several absolute stream positions.
E11. The same learned structure is recognized across several internal durations.
E12. Binary symbol relabelling preserves canonical machine structure.
E13. A large raw stream table contracts to a tiny recurrent state machine.
E14. The frozen kernel contains no absolute-position read, window, motif, substring, or named event constructor.
E15. Incomplete consequence authority remains UNKNOWN.
E16. Removing verification authorizes no machine construction.
E17. No single fixed absolute length-3 window solves the shifted multi-step structure.
E18. Training through length 6 transfers exactly through length 10.
E19. The post-freeze benchmark families recover their independently expected minimum recurrent state counts.

## Claim boundary

V35 still supplies substantial priors:

- a binary symbol alphabet;
- micro-symbol segmentation;
- sequential order and direction;
- deterministic recurrence;
- complete finite training authority;
- an external consequence verifier.

Therefore a pass does **not** establish genesis of symbol boundaries, temporal order, causal direction, or arbitrary events from an unsegmented physical signal.

The next step after a pass is to weaken micro-symbol segmentation itself: give a finer raw boundary and ask whether consequence earns the temporal units over which the recurrent residual machine should operate.
