# Singleton proof-record iteration

Base proposal032780e9 reused the qualified telescope checker for literal Prop
results with exactlyonefield. With one constructor and no indices/recursion,
max(field universe,0)=0 proves that sole field is a proof, licensing singleton
large elimination. All signature/rule checks and promotion order are retained.
No name-specific NeZero rule was added.

TwoNeZero slices and recursor/projection witnesses are RED on846bd7 and GREEN
on032780e9. Fresh static review found no additional blocker. This proposal
inherits the beta-ladder regression from846 and is therefore not promoted.

Currentcandidate61d06c70f1ac266663189d07e59a2d7b87e02f80 includes dependency-aware
literal-lambda typing; run36834015096 replays against last qualified f08.
All local target tests pass. Full replay is pending.

Measured whole-file frontier after NeZero: both pair-list files now reach
countermodel (application-function-type). Deep-list files reach dite_eq_right;
fueled-chain reaches Except.instMonad. These are explicit remaining obligations,
not closed whole files. Returned dependent-function type representation remains
outside the currently reviewed literal-lambda fix.
