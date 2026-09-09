# Procedure repair v1 — frozen protocol

This experiment tests repair of a certificate procedure, not a larger expression search. The previous successful certificate-genesis run is immutable. The original coefficientwise solver and the frozen `experiment.develop` selector remain unchanged. The benchmark designer specifies the obligations and the generic repair language; the repair process receives only exact polynomial obligations and verifier failures, not a named target repair.

## Capability boundary

The initial checker accepts rational polynomials with every coefficient nonnegative. The frozen meta-language permits only: normalize a rational polynomial, factor its least nonnegative monomial power, split a polynomial into coefficientwise-nonnegative summands, complete a rational quadratic square, and partition a compact interval at a rational endpoint. The last operation may use a translated variable and an independently verified interval bound. No arbitrary theorem, target-specific formula, new expression constructor, or post-result extension is permitted. Every accepted certificate must carry an exact polynomial identity and a soundness proof. A failed search means this bounded grammar is insufficient, not that the polynomial is negative.

## Two held-out certificate problems

The first obligation is the derivative numerator of the previously generated quadratic arctangent bound, P=x/2*(x-1)^2. The old checker fails because P has a negative coefficient. A square certificate must be derived from its coefficients, not selected by a target-specific branch. The recovered procedure must certify the original universal lower bound and the genuine OpenAI polar-chart transfer.

The second, source-distinct certificate obligation is nonnegativity of Q=1-x^2 on [0,1]. The old checker and the half-line square constructor must both fail; the intended admissible repair uses the frozen interval-transformation operations. The same controller and budget are used. The second task is sealed from the first repair choice and is opened only after the first capability is installed. No source theorem name or constructor identity is provided to the selector.

## Controls and acceptance

Both residual and pass/fail-only controllers receive the same procedure candidates, order, initial checker, and budget of two promotions per task. Enumerate all permutations of the finite candidate set. Report exact residuals, procedure candidates, selection, verifier calls, failures, held-out adequacy, and removal ablation. If there is only one successful candidate, report the absence of a causal search advantage. The development controller must not be changed after the protocol is frozen.

The mathematical gate must check soundness of the newly installed certificate constructors, then their applications to the two obligations. A successful finite run is not a universal theorem. The generated proof must not import the withheld AB lower estimate. The OpenAI and AB source pins remain 8937a8f4cbc7abaab5e9e97d1cc7f5d2319d9538 and d0124689230b58b4f86e7b90ac59de06404b3b6b. Original upstream files and manifests are not modified. Any mathematical change after observing a result requires a new experiment name.

The strongest permitted claim is bounded, verifier-guided certificate-procedure repair with a held-out constructor change. It does not establish unrestricted self-development, discovery of an unknown physical theorem, or repair of an essential blow-up lemma.