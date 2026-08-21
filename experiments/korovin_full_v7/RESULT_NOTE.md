# V7 public validation result — preserved negative outcome

GitHub Actions run `32532872420` was the first process to generate the precommitted public validation world.

The fixed seed produced identical primitive transformations:

```text
a = (0,3,3,0)
b = (0,3,3,0)
```

The resulting generated object had only 3 reachable states. Therefore preregistered gate G0 (`state_count >= 6`) failed and the experiment is recorded as **FAILED**. The seed is not replaced and the gate is not relaxed.

All capability-specific gates nevertheless passed:

- at least one primitive generator was non-invertible;
- bounded theory formation exactly matched semantic congruence with zero false merges;
- the initial theory received the global completeness certificate;
- the pruned theory retained global completeness;
- every final rule was causally necessary;
- the theory was compact relative to the state count;
- every final equation was semantically sound;
- every canonical-state × generator edge had an explicit replayable derivation.

The learned globally complete presentation was:

```text
a = b
bb = bbb
```

The failure therefore localizes to the **random-world difficulty distribution**, not to the compact-theory/global-certification mechanism. The next experiment must preserve this negative result and avoid rejection sampling. A precommitted batch of independently derived worlds should report all draws and stratify outcomes by realized object complexity.

Artifact: `korovin-public-synthetic-v7`, run `32532872420`, artifact id `9464454631`.
