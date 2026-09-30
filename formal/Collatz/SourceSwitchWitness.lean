import Collatz.GuardedDyadicSwitch
import Collatz.SourceCylinderExit

set_option maxRecDepth 10000
set_option maxHeartbeats 2000000

namespace CollatzFinal.SourceProduct

def switchSource (t : Nat) := 3294206330938702138381104133963803 + 84740873427720190311783157213303496617381798500264465924096*t
def switchOwner0 (t : Nat) := 401921098006060864059822585962556501 + 10339104923144442364280990139412146030954577709855307334680576*t
def switchOwner1 (t : Nat) := 1287599767586799477097898430908365823 + 33122493848022796070335730617521040092330558766777671593183232*t
def switchOwner2 (t : Nat) := 1448549738535149411735135734771911551 + 37262805579025645579127696944711170103871878612624880542331136*t

theorem iter_at_source_period {n k y q period unit : Nat}
    (htrace : sourceOrbit n k = (y,q)) (hperiod : period = 2^k*unit)
    (t : Nat) : iter shortcut k (n+period*t) = y + (3^q*unit)*t := by
  have hp := (sourceOrbit_correct n k).symm.trans htrace
  have hy := congrArg Prod.fst hp
  have hq := congrArg Prod.snd hp
  change iter shortcut k n = y at hy
  change oddCount n k = q at hq
  have he : n+period*t = n+2^k*(unit*t) := by rw [hperiod, Nat.mul_assoc]
  rw [he, shortcut_iter_source_lift, hy, hq, Nat.mul_assoc]

theorem switch_source_endpoint_0 (t : Nat) :
    iter shortcut 167 (switchSource t) + 1 = 4*switchOwner0 t := by
  have ht := iter_at_source_period (n := 3294206330938702138381104133963803) (k := 167) (y := 1607684392024243456239290343850226003) (q := 111) (period := 84740873427720190311783157213303496617381798500264465924096) (unit := 452984832) (by decide) (by decide) t
  change iter shortcut 167 (3294206330938702138381104133963803+84740873427720190311783157213303496617381798500264465924096*t)+1 = 4*(401921098006060864059822585962556501+10339104923144442364280990139412146030954577709855307334680576*t)
  rw [ht]
  simp only [Nat.mul_add]
  omega

theorem switch_source_endpoint_1 (t : Nat) :
    iter shortcut 178 (switchSource t) + 1 = 4*switchOwner1 t := by
  have ht := iter_at_source_period (n := 3294206330938702138381104133963803) (k := 178) (y := 5150399070347197908391593723633463291) (q := 119) (period := 84740873427720190311783157213303496617381798500264465924096) (unit := 221184) (by decide) (by decide) t
  change iter shortcut 178 (3294206330938702138381104133963803+84740873427720190311783157213303496617381798500264465924096*t)+1 = 4*(1287599767586799477097898430908365823+33122493848022796070335730617521040092330558766777671593183232*t)
  rw [ht]
  simp only [Nat.mul_add]
  omega

theorem switch_source_endpoint_2 (t : Nat) :
    iter shortcut 181 (switchSource t) + 1 = 4*switchOwner2 t := by
  have ht := iter_at_source_period (n := 3294206330938702138381104133963803) (k := 181) (y := 5794198954140597646940542939087646203) (q := 121) (period := 84740873427720190311783157213303496617381798500264465924096) (unit := 27648) (by decide) (by decide) t
  change iter shortcut 181 (3294206330938702138381104133963803+84740873427720190311783157213303496617381798500264465924096*t)+1 = 4*(1448549738535149411735135734771911551+37262805579025645579127696944711170103871878612624880542331136*t)
  rw [ht]
  simp only [Nat.mul_add]
  omega

theorem switch_returns_actual (t : Nat) :
    iter shortcut 11 (iter shortcut 167 (switchSource t)) = iter shortcut 178 (switchSource t) ∧
    iter shortcut 3 (iter shortcut 178 (switchSource t)) = iter shortcut 181 (switchSource t) := by
  constructor
  · rw [← iter_add]
  · rw [← iter_add]

theorem switch_owner_odd (t : Nat) :
    switchOwner0 t % 2 = 1 ∧ switchOwner1 t % 2 = 1 ∧ switchOwner2 t % 2 = 1 := by
  simp only [switchOwner0,switchOwner1,switchOwner2]
  constructor
  · omega
  constructor <;> omega

theorem switch_owner_laws (t : Nat) :
    2048*switchOwner1 t = 6561*switchOwner0 t+2443 ∧
    8*switchOwner2 t = 9*switchOwner1 t+1 := by
  simp only [switchOwner0,switchOwner1,switchOwner2,Nat.mul_add]
  constructor <;> omega

theorem switch_owner_expansions (t : Nat) :
    switchOwner0 t < switchOwner1 t ∧ switchOwner1 t < switchOwner2 t := by
  simp only [switchOwner0,switchOwner1,switchOwner2]
  constructor <;> omega

theorem switch_original_source_bounds (t : Nat) :
    switchSource t < 4*switchOwner0 t-1 ∧
    switchSource t < 4*switchOwner1 t-1 ∧
    switchSource t < 4*switchOwner2 t-1 := by
  simp only [switchSource,switchOwner0,switchOwner1,switchOwner2,Nat.mul_add]
  constructor
  · omega
  constructor <;> omega

theorem switch_own_orders_0 (t : Nat) :
    DyadicOrder (returnDefect 6561 2443 2048 (switchOwner0 t)) 12 ∧
    TernaryOrder (returnDefect 6561 2443 2048 (switchOwner0 t)) 0 := by
  have hr : returnDefect 6561 2443 2048 (switchOwner0 t) = -1813869915301352679501979330449017491456 + (-46660380518150868390000108499167015037698009204577002001413439488:Int)*(t:Int) := by
    unfold switchOwner0
    simp only [Int.natCast_add,Int.natCast_mul]
    rw [returnDefect_linear_ray]
    simp [returnDefect]
  rw [hr]
  constructor
  · have hb : DyadicOrder (-1813869915301352679501979330449017491456:Int) 12 := ⟨-442839334790369306519037922472904661, by decide, by decide⟩
    have hc : (-46660380518150868390000108499167015037698009204577002001413439488:Int) = (2:Int)^(12+1)*(-5695847231219588426513685119527223515343995264230591064625664:Int) := by decide
    rw [hc,Int.mul_assoc]
    exact dyadic_even_perturbation hb _
  · have hb : TernaryOrder (-1813869915301352679501979330449017491456:Int) 0 := ⟨-1813869915301352679501979330449017491456, by decide, by decide⟩
    have hc : (-46660380518150868390000108499167015037698009204577002001413439488:Int) = (3:Int)^(0+1)*(-15553460172716956130000036166389005012566003068192334000471146496:Int) := by decide
    rw [hc,Int.mul_assoc]
    exact ternary_multiple_perturbation hb _

theorem switch_own_orders_1 (t : Nat) :
    DyadicOrder (returnDefect 9 1 8 (switchOwner1 t)) 10 ∧
    TernaryOrder (returnDefect 9 1 8 (switchOwner1 t)) 2 := by
  have hr : returnDefect 9 1 8 (switchOwner1 t) = -1287599767586799477097898430908365824 + (-33122493848022796070335730617521040092330558766777671593183232:Int)*(t:Int) := by
    unfold switchOwner1
    simp only [Int.natCast_add,Int.natCast_mul]
    rw [returnDefect_linear_ray]
    simp [returnDefect]
  rw [hr]
  constructor
  · have hb : DyadicOrder (-1287599767586799477097898430908365824:Int) 10 := ⟨-1257421648033983864353416436433951, by decide, by decide⟩
    have hc : (-33122493848022796070335730617521040092330558766777671593183232:Int) = (2:Int)^(10+1)*(-16173092699229880893718618465586445357583280647840659957609:Int) := by decide
    rw [hc,Int.mul_assoc]
    exact dyadic_even_perturbation hb _
  · have hb : TernaryOrder (-1287599767586799477097898430908365824:Int) 2 := ⟨-143066640842977719677544270100929536, by decide, by decide⟩
    have hc : (-33122493848022796070335730617521040092330558766777671593183232:Int) = (3:Int)^(2+1)*(-1226759031408251706308730763611890373790020695065839688636416:Int) := by decide
    rw [hc,Int.mul_assoc]
    exact ternary_multiple_perturbation hb _

#print axioms switch_source_endpoint_0
#print axioms switch_source_endpoint_1
#print axioms switch_source_endpoint_2
#print axioms switch_returns_actual
#print axioms switch_owner_odd
#print axioms switch_owner_laws
#print axioms switch_owner_expansions
#print axioms switch_original_source_bounds
#print axioms switch_own_orders_0
#print axioms switch_own_orders_1

end CollatzFinal.SourceProduct
