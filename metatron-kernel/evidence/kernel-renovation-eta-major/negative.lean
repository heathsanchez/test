universe u v

/--
Neighboring malformed control for the eta-major fixture.

It differs only in the source type of `x`: `p.2` cannot inhabit the
recursor result `p.1`. Both the official kernel and Nucleus must refuse it.
-/
def nucleusEtaMajorBad
    (p : Prod (Type u) (Type v))
    (x : p.2) :
    @Prod.rec (Type u) (Type v) (fun _ => Type u) (fun a _ => a) p :=
  x
