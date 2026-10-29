# Future-commutation frame calibration — 29 October 2026

**Status:** WARRANTED_BOUNDED for standalone numerical model; **CANDIDATE** for native Nyx remediation. No ANISE/Nyx source mutation, third-party message, safety/flight claim, formal Lean proof or product-level G4 promotion.

## Why this test exists

An earlier private [ANISE/Nyx native audit](https://chatgpt.com/library?file_id=libfile_024ece51277081919d08a24ea67f3767&account_id=personal) established that a separate Nyx `SpacecraftSequence::FrameSwap` event-epoch correction could pass **3/3** native tests yet lead to a rotating-frame trajectory which deviated after 600 seconds from inertial truth by **201.19015652244954 km position / 0.713117640 km/s velocity**. That native frame-swap result was independently found in the private audit, not reproduced by this standalone model. It is **distinct** from upstream [Nyx issue #603](https://github.com/nyx-space/nyx/issues/603), originally reported by scottshambaugh, which concerns ANISE `Almanac::transform` misrotating the Moon position and hence solid tides. Do not attribute the FrameSwap counterexample to the issue reporter or imply our model is a native regression test for issue #603.

We now independently test the **causal physical mechanism** in a standalone constant-spin Earth model. This is not a rerun of the Nyx Rust code.

## Model and independently checked consequences

- Original initial state: Earth two-body gravitational parameter `mu=398600.435436096 km^3/s^2`, `r0=(7000,0) km`, `v0=(0,7.5) km/s`, duration 600 seconds.
- Model Earth spin: `omega=7.2921159e-5 rad/s` constant, standard planar rotation. Fourth-order Runge–Kutta with 1-second steps; closed-form ellipse/Kepler equation independently defines the true terminal orbit.
- Inertial RHS: `dr/dt=v`, `dv/dt=-mu*r/|r|^3`.
- Naive rotating RHS: applies that same inertial RHS to rotating coordinates after a correct *initial* position and velocity basis change.
- Correct rotating RHS: adds `-2 omega × v - omega × (omega × r)` to acceleration (constant spin, zero Euler term). At each future epoch, position is rotated back and velocity includes the moving basis term.

### Fresh local numbers

| Quantity | Measured |
| --- | ---: |
| Naive rotating→inertial vs inertial at 600s, position | `201.19029652728074 km` |
| Naive rotating→inertial vs inertial at 600s, velocity | `0.7131185326672057 km/s` |
| Difference in naive position deviation versus native Nyx report | `0.0001400048312 km` (approximately 0.14 m) |
| Corrected rotating→inertial vs inertial, position | `2.643799571842216e-11 km` |
| Corrected rotating→inertial vs inertial, velocity | `6.286019626323202e-14 km/s` |
| RK4 inertial vs closed-form Kepler, position | `4.952363593497278e-11 km` |
| RK4 inertial vs closed-form Kepler, velocity | `6.323555905157563e-14 km/s` |

Executed `python3 -B -m unittest -v test_future_frame_commutation`: **6/6 passed** on the local runner. Tests cover event-epoch static pass, 600s naive future failure, restored commutation with inertial-force terms, independent Kepler reference literal, causal Earth-spin ablation across 60/600/1200 seconds, and approximate agreement with the previously reported native Nyx counterexample.

## Correct conclusion and next gate

The closeness to the independent native 201.190156 km failure supports the missing rotating-frame dynamics diagnosis. **It does not prove the proposed formula is implemented correctly in Nyx**, or that such propagation is an intended supported contract. The next decisive source-native experiment must choose between (a) explicitly rejecting unsupported rotating-frame propagation; (b) propagating in inertial coordinates and presenting requested frames; or (c) integrating the full non-inertial dynamics, then re-run both native Nyx sequence and original test suites with a source pin. Only independent source-native checks could promote a safe repair.

Physical law perspective: the necessary consequence is a future-commuting observation diagram — initial coordinate equivalence is insufficient when the representation itself changes with time. That generalizes as a **candidate test-design law** to other stateful representational repairs, not a verified universal formula over arbitrary code.

ROS progress ledger: [2026-10-29 seven gates](https://app.notion.com/p/4083e523d7ab81f78ea3f212da9b8509).
