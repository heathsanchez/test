structure History where
  previous : Bool × Bool
  present : Bool × Bool

def h0 : History := ⟨(false, true), (false, false)⟩
def h1 : History := ⟨(true, true), (false, false)⟩

def StatelessObserver := Bool × Bool → Bool
def Separates (q : History → Bool) (a b : History) : Prop := q a ≠ q b

theorem stateless_no_separator (m : StatelessObserver) :
    ¬ Separates (fun h => m h.present) h0 h1 := by
  simp [Separates, h0, h1]

structure CompleteStateless (M : Type) : Type where
  denotes : M → StatelessObserver
  complete : ∀ f : StatelessObserver, ∃ m, denotes m = f

structure NoSeparator (M : Type) (denotes : M → StatelessObserver) : Prop where
  noSep : ∀ m, ¬ Separates (fun h => denotes m h.present) h0 h1

structure UnknownExpressivityExperimentMeta (M : Type) where
  p_complete : CompleteStateless M
  p_noSep : NoSeparator M p_complete.denotes

structure MachineObserver where
  transition : Bool → (Bool × Bool) → Bool
  output : Bool → Bool

def runMachine (m : MachineObserver) (h : History) : Bool :=
  m.output (m.transition false h.previous)

def constructed : MachineObserver where
  transition := fun _ input => input.1
  output := id

theorem constructed_separates : Separates (runMachine constructed) h0 h1 := by
  simp [Separates, runMachine, constructed, h0, h1]

theorem extension_is_not_stateless :
    ¬ ∃ m : StatelessObserver,
      (m h0.present = runMachine constructed h0 ∧
       m h1.present = runMachine constructed h1) := by
  simp [runMachine, constructed, h0, h1]

structure MetaExtension (M : Type) where
  observer : History → Bool
  novel : Separates observer h0 h1

def extendMeta {M : Type} (_ : UnknownExpressivityExperimentMeta M)
    (delta : MetaExtension M) : MetaExtension M := delta

-- Deliberately absent: constructors from timeout, failed heuristic search,
-- stale certificates, or a bare NoSeparator proof.
