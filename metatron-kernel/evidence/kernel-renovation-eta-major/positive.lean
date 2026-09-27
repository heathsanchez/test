universe u v

/--
A free major for a nonrecursive structure recursor.

The declared result type is the recursor computation on `p`, while the
argument `x` has type `p.1`. Kernel checking therefore needs the
structure-major eta path:
  p  ↦  Prod.mk p.1 p.2
before the recursor computation exposes the first field.
-/
def nucleusEtaMajor
    (p : Prod (Type u) (Type v))
    (x : p.1) :
    @Prod.rec (Type u) (Type v) (fun _ => Type u) (fun a _ => a) p :=
  x
