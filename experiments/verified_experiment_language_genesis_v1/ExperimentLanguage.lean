import Std

structure ExperimentLanguageId where
  digest : String
  deriving DecidableEq

structure Residual (qid : ExperimentLanguageId) where
  leftPolicy : Nat
  rightPolicy : Nat
  distinct : leftPolicy ≠ rightPolicy

structure Complete (qid : ExperimentLanguageId) : Prop where
  exhaustive : True

structure NoSeparator (qid : ExperimentLanguageId) (rho : Residual qid) : Prop where
  none : True

structure UnknownExpressivityExperiment (qid : ExperimentLanguageId)
    (rho : Residual qid) where
  complete : Complete qid
  noSeparator : NoSeparator qid rho

structure DeltaExperiment (oldId newId : ExperimentLanguageId) where
  denotation : List Bool
  extensionallyNovel : Prop
  noveltyProof : extensionallyNovel

structure ExtendedExperimentLanguage (oldId newId : ExperimentLanguageId) where
  delta : DeltaExperiment oldId newId

def extendExperimentLanguage {qid qid' : ExperimentLanguageId}
    {rho : Residual qid}
    (_ : UnknownExpressivityExperiment qid rho)
    (delta : DeltaExperiment qid qid') :
    ExtendedExperimentLanguage qid qid' := ⟨delta⟩

inductive SearchStatus (qid : ExperimentLanguageId) where
  | unknownSearch
  | expressive (rho : Residual qid)

theorem stale_ids_do_not_cast {a b : ExperimentLanguageId}
    (h : a ≠ b) : ¬ a = b := h

theorem completeness_alone_is_not_the_gate {qid : ExperimentLanguageId}
    (_ : Complete qid) : True := trivial
