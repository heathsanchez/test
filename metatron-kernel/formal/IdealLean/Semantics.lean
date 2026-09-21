/-!
# IdealLean portable semantic skeleton

This file is deliberately independent of any checker implementation.  It models
only the declarations, environments, and judgments needed to state a theorem
installation discipline, plus locally nameless binder opening.
-/

namespace IdealLean

abbrev DeclName := String
abbrev FreeVar := Nat

/-- A small, portable expression language.  It is not Lean's full expression
language; in particular it omits universes, inductives, metavariables, and
elaboration artifacts. -/
inductive Expr where
  | sort : Nat → Expr
  | const : DeclName → Expr
  | bvar : Nat → Expr
  | fvar : FreeVar → Expr
  | app : Expr → Expr → Expr
  | lam : Expr → Expr → Expr
  | forallE : Expr → Expr → Expr
  deriving DecidableEq, Repr

/-- `openAt x depth e` opens bound variable `depth` as free variable `x`.
Crossing a binder increments `depth`.  This is the conventional locally
nameless opening operation, independent of evaluator or checker internals. -/
def openAt (x : FreeVar) : Nat → Expr → Expr
  | _, .sort u => .sort u
  | _, .const n => .const n
  | depth, .bvar index => if index = depth then .fvar x else .bvar index
  | _, .fvar y => .fvar y
  | depth, .app fn arg => .app (openAt x depth fn) (openAt x depth arg)
  | depth, .lam domain body =>
      .lam (openAt x depth domain) (openAt x (depth + 1) body)
  | depth, .forallE domain body =>
      .forallE (openAt x depth domain) (openAt x (depth + 1) body)

/-- Open the outermost binder of `body`. -/
def openBinder (body : Expr) (x : FreeVar) : Expr := openAt x 0 body

@[simp] theorem openBinder_bvar_zero (x : FreeVar) :
    openBinder (.bvar 0) x = .fvar x := by
  simp [openBinder, openAt]

@[simp] theorem openBinder_bvar_succ (x index : Nat) :
    openBinder (.bvar (index + 1)) x = .bvar (index + 1) := by
  simp [openBinder, openAt]

@[simp] theorem openBinder_const (x : FreeVar) (name : DeclName) :
    openBinder (.const name) x = .const name := by
  simp [openBinder, openAt]

/-- Constant-reference occurrence, kept separate from typing. -/
inductive Expr.OccursConst (name : DeclName) : Expr → Prop where
  | here : OccursConst name (.const name)
  | appFn : OccursConst name fn → OccursConst name (.app fn arg)
  | appArg : OccursConst name arg → OccursConst name (.app fn arg)
  | lamDomain : OccursConst name domain → OccursConst name (.lam domain body)
  | lamBody : OccursConst name body → OccursConst name (.lam domain body)
  | forallDomain : OccursConst name domain → OccursConst name (.forallE domain body)
  | forallBody : OccursConst name body → OccursConst name (.forallE domain body)

/-- Stored declarations.  A theorem intentionally has no proof-body field;
only definitions are reducible. -/
inductive Declaration where
  | axiom : DeclName → Expr → Declaration
  | definition : DeclName → Expr → Expr → Declaration
  | theorem : DeclName → Expr → Declaration
  | inductiveType : DeclName → Expr → Declaration
  | constructor : DeclName → Expr → Declaration
  | recursor : DeclName → Expr → Declaration
  deriving DecidableEq, Repr

namespace Declaration

def name : Declaration → DeclName
  | .axiom n _ => n
  | .definition n _ _ => n
  | .theorem n _ => n
  | .inductiveType n _ => n
  | .constructor n _ => n
  | .recursor n _ => n

def type : Declaration → Expr
  | .axiom _ ty => ty
  | .definition _ ty _ => ty
  | .theorem _ ty => ty
  | .inductiveType _ ty => ty
  | .constructor _ ty => ty
  | .recursor _ ty => ty

/-- Reducible bodies exist only for definitions. -/
def body : Declaration → Option Expr
  | .definition _ _ value => some value
  | .axiom _ _ => none
  | .theorem _ _ => none
  | .inductiveType _ _ => none
  | .constructor _ _ => none
  | .recursor _ _ => none

end Declaration

/-- Environments are chronological: older declarations occur first. -/
abbrev Environment := List Declaration

namespace Environment

def Declared (env : Environment) (name : DeclName) : Prop :=
  ∃ declaration ∈ env, declaration.name = name

def Fresh (env : Environment) (name : DeclName) : Prop :=
  ¬env.Declared name

/-- All constant references in an expression resolve in `env`. -/
def Supports (env : Environment) (expr : Expr) : Prop :=
  ∀ name, expr.OccursConst name → env.Declared name

end Environment

/-- The candidate carries a proof only while it is being checked. -/
structure TheoremCandidate where
  name : DeclName
  type : Expr
  proof : Expr
  deriving DecidableEq, Repr

namespace Install

/-- `TypeCorrect` is the one intentional semantic parameter.  A client may
instantiate it with any typing relation.  `Checks` adds the portable structural
obligations which that relation alone need not expose. -/
structure Checks
    (TypeCorrect : Environment → Expr → Expr → Prop)
    (prior : Environment) (candidate : TheoremCandidate) : Prop where
  fresh : prior.Fresh candidate.name
  typeSupported : prior.Supports candidate.type
  proofSupported : prior.Supports candidate.proof
  proposition : TypeCorrect prior candidate.type (.sort 0)
  typeCorrect : TypeCorrect prior candidate.proof candidate.type

def installedDeclaration (candidate : TheoremCandidate) : Declaration :=
  .theorem candidate.name candidate.type

/-- Installation appends an opaque theorem after checking against `prior`. -/
def install (prior : Environment) (candidate : TheoremCandidate) : Environment :=
  prior ++ [installedDeclaration candidate]

/-- The specification-level transition.  Its premise mentions only the prior
environment, making check-before-install and declaration order explicit. -/
inductive Step
    (TypeCorrect : Environment → Expr → Expr → Prop) :
    Environment → TheoremCandidate → Environment → Prop where
  | accepted (checked : Checks TypeCorrect prior candidate) :
      Step TypeCorrect prior candidate (install prior candidate)

theorem installed_theorem_has_no_body (candidate : TheoremCandidate) :
    (installedDeclaration candidate).body = none := by
  rfl

/-- The typing premise is necessarily discharged before installation, against
the environment which does not yet contain the candidate. -/
theorem type_correct_in_prior_environment
    (step : Step TypeCorrect prior candidate next) :
    TypeCorrect prior candidate.proof candidate.type := by
  cases step with
  | accepted checked => exact checked.typeCorrect

/-- The theorem's declared type is itself established as a proposition in the
prior environment.  In this skeleton, `Prop` is represented by `sort 0`. -/
theorem theorem_type_is_prop_in_prior_environment
    (step : Step TypeCorrect prior candidate next) :
    TypeCorrect prior candidate.type (.sort 0) := by
  cases step with
  | accepted checked => exact checked.proposition

theorem prior_environment_is_prefix
    (step : Step TypeCorrect prior candidate next) :
    ∃ declaration, next = prior ++ [declaration] := by
  cases step
  exact ⟨installedDeclaration candidate, rfl⟩

theorem checked_proof_uses_prior_environment
    (step : Step TypeCorrect prior candidate next) :
    prior.Supports candidate.proof := by
  cases step with
  | accepted checked => exact checked.proofSupported

/-- A successfully installed theorem cannot cite its own fresh name in its
proof: every proof reference must already resolve in the prior environment. -/
theorem checked_theorem_is_not_self_referential
    (step : Step TypeCorrect prior candidate next) :
    ¬candidate.proof.OccursConst candidate.name := by
  intro selfReference
  cases step with
  | accepted checked =>
      exact checked.fresh (checked.proofSupported candidate.name selfReference)

end Install

/-! ## Opaque inductive-signature promotion

This is the portable warrant used by the current closed, nonrecursive Rust
engine.  It does not validate positivity or derive a particular eliminator;
those remain premises in `SignatureValid`.  It states only the common rule:
signatures validated in dependency order can be installed opaquely while
preserving an independently supplied environment-validity invariant. -/

namespace InductivePromotion

inductive Kind where
  | inductiveType
  | constructor
  | recursor
  deriving DecidableEq, Repr

structure Signature where
  kind : Kind
  name : DeclName
  type : Expr
  deriving DecidableEq, Repr

def installedDeclaration : Signature → Declaration
  | ⟨.inductiveType, name, type⟩ => .inductiveType name type
  | ⟨.constructor, name, type⟩ => .constructor name type
  | ⟨.recursor, name, type⟩ => .recursor name type

/-- Validation is sequential: later signatures are checked in the environment
that already contains the earlier opaque signatures. -/
inductive Validated
    (SignatureValid : Environment → Signature → Prop) :
    Environment → List Signature → Environment → Prop where
  | nil : Validated SignatureValid prior [] prior
  | cons
      (checked : SignatureValid prior signature)
      (rest : Validated SignatureValid
        (prior ++ [installedDeclaration signature]) signatures next) :
      Validated SignatureValid prior (signature :: signatures) next

/-- The smallest semantic promotion law shared by G9/G10/G11.  No concrete
typing relation or whole-checker correctness claim is assumed. -/
theorem promote_preserves_environment_validity
    (EnvironmentValid : Environment → Prop)
    (SignatureValid : Environment → Signature → Prop)
    (extendValid : ∀ environment signature,
      EnvironmentValid environment →
      SignatureValid environment signature →
      EnvironmentValid (environment ++ [installedDeclaration signature]))
    (validated : Validated SignatureValid prior signatures next)
    (priorValid : EnvironmentValid prior) :
    EnvironmentValid next := by
  induction validated with
  | nil => exact priorValid
  | cons checked _ inductionHypothesis =>
      exact inductionHypothesis (extendValid _ _ priorValid checked)

/-- Every promoted signature is opaque; computation rules require a separate
qualification and cannot enter delta authority through this transition. -/
theorem promoted_signatures_are_opaque
    (signatures : List Signature) (declaration : Declaration)
    (member : declaration ∈ signatures.map installedDeclaration) :
    declaration.body = none := by
  obtain ⟨signature, _, rfl⟩ := List.mem_map.mp member
  cases signature with
  | mk kind name type => cases kind <;> rfl

end InductivePromotion

/-! ## Parameterized opaque-signature promotion

This layer adds only an explicit, validated parameter telescope to the opaque
promotion law. It does not derive an inductive declaration, positivity, or a
recursor, and it makes no statement about the Rust implementation. -/

namespace ParameterizedInductivePromotion

structure Parameter where
  name : DeclName
  type : Expr
  deriving DecidableEq, Repr

abbrev Telescope := List Parameter

/-- A parameterized candidate carries the telescope which justified all of its
derived signatures. Signature validation remains sequential in the promoted
environment, exactly as in the nonparameterized rule. -/
structure Validated
    (TelescopeValid : Environment → Telescope → Prop)
    (SignatureValid : Telescope → Environment → InductivePromotion.Signature → Prop)
    (prior : Environment) (telescope : Telescope)
    (signatures : List InductivePromotion.Signature) (next : Environment) : Prop where
  telescopeValid : TelescopeValid prior telescope
  signaturesValid : InductivePromotion.Validated
    (SignatureValid telescope) prior signatures next

/-- If a checked telescope authorizes each sequential opaque-signature
extension, promoting those signatures preserves environment validity. The
typing and derivation relations remain abstract parameters. -/
theorem promote_preserves_environment_validity
    (EnvironmentValid : Environment → Prop)
    (TelescopeValid : Environment → Telescope → Prop)
    (SignatureValid : Telescope → Environment → InductivePromotion.Signature → Prop)
    (extendValid : ∀ environment signature,
      EnvironmentValid environment →
      TelescopeValid prior telescope →
      SignatureValid telescope environment signature →
      EnvironmentValid
        (environment ++ [InductivePromotion.installedDeclaration signature]))
    (validated : Validated TelescopeValid SignatureValid
      prior telescope signatures next)
    (priorValid : EnvironmentValid prior) :
    EnvironmentValid next := by
  apply InductivePromotion.promote_preserves_environment_validity
    EnvironmentValid (SignatureValid telescope)
    (fun environment signature environmentValid signatureValid =>
      extendValid environment signature environmentValid
        validated.telescopeValid signatureValid)
    validated.signaturesValid priorValid

end ParameterizedInductivePromotion
end IdealLean
