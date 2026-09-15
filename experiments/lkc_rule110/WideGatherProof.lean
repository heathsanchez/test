import GenericPackProof
import GatherPairProof
import WideHierarchyProof
import Submission

namespace WideGather

open GenericPack
open GatherPair
open WideHierarchy
open Submission

set_option maxRecDepth 1048576
set_option exponentiation.threshold 20000
set_option maxHeartbeats 4000000

def dense1 (x : Nat) : Nat := bits1 x
theorem dense1_lt (x : Nat) : dense1 x < 2 ^ 1 := by
  unfold dense1 bits1 ones1
  exact shrMask_lt_pow 1 1 31 (raw1 x) (by decide)

def dense2 (x : Nat) : Nat :=
  packW 1 (dense1 x) (dense1 (x + 1 * stepConst))

theorem dense2_lt (x : Nat) : dense2 x < 2 ^ 2 := by
  unfold dense2
  exact packW_lt_double 1
    (dense1 x) (dense1 (x + 1 * stepConst))
    (dense1_lt x) (dense1_lt (x + 1 * stepConst))

def dense4 (x : Nat) : Nat :=
  packW 2 (dense2 x) (dense2 (x + 2 * stepConst))

theorem dense4_lt (x : Nat) : dense4 x < 2 ^ 4 := by
  unfold dense4
  exact packW_lt_double 2
    (dense2 x) (dense2 (x + 2 * stepConst))
    (dense2_lt x) (dense2_lt (x + 2 * stepConst))

def dense8 (x : Nat) : Nat :=
  packW 4 (dense4 x) (dense4 (x + 4 * stepConst))

theorem dense8_lt (x : Nat) : dense8 x < 2 ^ 8 := by
  unfold dense8
  exact packW_lt_double 4
    (dense4 x) (dense4 (x + 4 * stepConst))
    (dense4_lt x) (dense4_lt (x + 4 * stepConst))

def dense16 (x : Nat) : Nat :=
  packW 8 (dense8 x) (dense8 (x + 8 * stepConst))

theorem dense16_lt (x : Nat) : dense16 x < 2 ^ 16 := by
  unfold dense16
  exact packW_lt_double 8
    (dense8 x) (dense8 (x + 8 * stepConst))
    (dense8_lt x) (dense8_lt (x + 8 * stepConst))

def dense32 (x : Nat) : Nat :=
  packW 16 (dense16 x) (dense16 (x + 16 * stepConst))

theorem dense32_lt (x : Nat) : dense32 x < 2 ^ 32 := by
  unfold dense32
  exact packW_lt_double 16
    (dense16 x) (dense16 (x + 16 * stepConst))
    (dense16_lt x) (dense16_lt (x + 16 * stepConst))

def dense64 (x : Nat) : Nat :=
  packW 32 (dense32 x) (dense32 (x + 32 * stepConst))

theorem dense64_lt (x : Nat) : dense64 x < 2 ^ 64 := by
  unfold dense64
  exact packW_lt_double 32
    (dense32 x) (dense32 (x + 32 * stepConst))
    (dense32_lt x) (dense32_lt (x + 32 * stepConst))

def dense128 (x : Nat) : Nat :=
  packW 64 (dense64 x) (dense64 (x + 64 * stepConst))

theorem dense128_lt (x : Nat) : dense128 x < 2 ^ 128 := by
  unfold dense128
  exact packW_lt_double 64
    (dense64 x) (dense64 (x + 64 * stepConst))
    (dense64_lt x) (dense64_lt (x + 64 * stepConst))

def dense256 (x : Nat) : Nat :=
  packW 128 (dense128 x) (dense128 (x + 128 * stepConst))

theorem dense256_lt (x : Nat) : dense256 x < 2 ^ 256 := by
  unfold dense256
  exact packW_lt_double 128
    (dense128 x) (dense128 (x + 128 * stepConst))
    (dense128_lt x) (dense128_lt (x + 128 * stepConst))

def phys1_1 (x : Nat) : Nat := dense1 x
theorem phys1_1_lt (x : Nat) : phys1_1 x < 2 ^ 64 := by
  unfold phys1_1
  exact Nat.lt_of_lt_of_le (dense1_lt x)
    (Nat.pow_le_pow_right (by omega) (by decide))

def phys1_2 (x : Nat) : Nat :=
  packW 64 (phys1_1 x)
    (phys1_1 (x + 1 * stepConst))

theorem phys1_2_lt (x : Nat) :
    phys1_2 x < 2 ^ 128 := by
  unfold phys1_2
  simpa [show 64 + 64 = 128 by decide] using
    (packW_lt_double 64
      (phys1_1 x)
      (phys1_1 (x + 1 * stepConst))
      (phys1_1_lt x)
      (phys1_1_lt (x + 1 * stepConst)))

def phys1_4 (x : Nat) : Nat :=
  packW 128 (phys1_2 x)
    (phys1_2 (x + 2 * stepConst))

theorem phys1_4_lt (x : Nat) :
    phys1_4 x < 2 ^ 256 := by
  unfold phys1_4
  simpa [show 128 + 128 = 256 by decide] using
    (packW_lt_double 128
      (phys1_2 x)
      (phys1_2 (x + 2 * stepConst))
      (phys1_2_lt x)
      (phys1_2_lt (x + 2 * stepConst)))

def phys1_8 (x : Nat) : Nat :=
  packW 256 (phys1_4 x)
    (phys1_4 (x + 4 * stepConst))

theorem phys1_8_lt (x : Nat) :
    phys1_8 x < 2 ^ 512 := by
  unfold phys1_8
  simpa [show 256 + 256 = 512 by decide] using
    (packW_lt_double 256
      (phys1_4 x)
      (phys1_4 (x + 4 * stepConst))
      (phys1_4_lt x)
      (phys1_4_lt (x + 4 * stepConst)))

def phys1_16 (x : Nat) : Nat :=
  packW 512 (phys1_8 x)
    (phys1_8 (x + 8 * stepConst))

theorem phys1_16_lt (x : Nat) :
    phys1_16 x < 2 ^ 1024 := by
  unfold phys1_16
  simpa [show 512 + 512 = 1024 by decide] using
    (packW_lt_double 512
      (phys1_8 x)
      (phys1_8 (x + 8 * stepConst))
      (phys1_8_lt x)
      (phys1_8_lt (x + 8 * stepConst)))

def phys1_32 (x : Nat) : Nat :=
  packW 1024 (phys1_16 x)
    (phys1_16 (x + 16 * stepConst))

theorem phys1_32_lt (x : Nat) :
    phys1_32 x < 2 ^ 2048 := by
  unfold phys1_32
  simpa [show 1024 + 1024 = 2048 by decide] using
    (packW_lt_double 1024
      (phys1_16 x)
      (phys1_16 (x + 16 * stepConst))
      (phys1_16_lt x)
      (phys1_16_lt (x + 16 * stepConst)))

def phys1_64 (x : Nat) : Nat :=
  packW 2048 (phys1_32 x)
    (phys1_32 (x + 32 * stepConst))

theorem phys1_64_lt (x : Nat) :
    phys1_64 x < 2 ^ 4096 := by
  unfold phys1_64
  simpa [show 2048 + 2048 = 4096 by decide] using
    (packW_lt_double 2048
      (phys1_32 x)
      (phys1_32 (x + 32 * stepConst))
      (phys1_32_lt x)
      (phys1_32_lt (x + 32 * stepConst)))

def phys1_128 (x : Nat) : Nat :=
  packW 4096 (phys1_64 x)
    (phys1_64 (x + 64 * stepConst))

theorem phys1_128_lt (x : Nat) :
    phys1_128 x < 2 ^ 8192 := by
  unfold phys1_128
  simpa [show 4096 + 4096 = 8192 by decide] using
    (packW_lt_double 4096
      (phys1_64 x)
      (phys1_64 (x + 64 * stepConst))
      (phys1_64_lt x)
      (phys1_64_lt (x + 64 * stepConst)))

def phys1_256 (x : Nat) : Nat :=
  packW 8192 (phys1_128 x)
    (phys1_128 (x + 128 * stepConst))

theorem phys1_256_lt (x : Nat) :
    phys1_256 x < 2 ^ 16384 := by
  unfold phys1_256
  simpa [show 8192 + 8192 = 16384 by decide] using
    (packW_lt_double 8192
      (phys1_128 x)
      (phys1_128 (x + 128 * stepConst))
      (phys1_128_lt x)
      (phys1_128_lt (x + 128 * stepConst)))

def phys2_1 (x : Nat) : Nat := dense2 x
theorem phys2_1_lt (x : Nat) : phys2_1 x < 2 ^ 128 := by
  unfold phys2_1
  exact Nat.lt_of_lt_of_le (dense2_lt x)
    (Nat.pow_le_pow_right (by omega) (by decide))

def phys2_2 (x : Nat) : Nat :=
  packW 128 (phys2_1 x)
    (phys2_1 (x + 2 * stepConst))

theorem phys2_2_lt (x : Nat) :
    phys2_2 x < 2 ^ 256 := by
  unfold phys2_2
  simpa [show 128 + 128 = 256 by decide] using
    (packW_lt_double 128
      (phys2_1 x)
      (phys2_1 (x + 2 * stepConst))
      (phys2_1_lt x)
      (phys2_1_lt (x + 2 * stepConst)))

def phys2_4 (x : Nat) : Nat :=
  packW 256 (phys2_2 x)
    (phys2_2 (x + 4 * stepConst))

theorem phys2_4_lt (x : Nat) :
    phys2_4 x < 2 ^ 512 := by
  unfold phys2_4
  simpa [show 256 + 256 = 512 by decide] using
    (packW_lt_double 256
      (phys2_2 x)
      (phys2_2 (x + 4 * stepConst))
      (phys2_2_lt x)
      (phys2_2_lt (x + 4 * stepConst)))

def phys2_8 (x : Nat) : Nat :=
  packW 512 (phys2_4 x)
    (phys2_4 (x + 8 * stepConst))

theorem phys2_8_lt (x : Nat) :
    phys2_8 x < 2 ^ 1024 := by
  unfold phys2_8
  simpa [show 512 + 512 = 1024 by decide] using
    (packW_lt_double 512
      (phys2_4 x)
      (phys2_4 (x + 8 * stepConst))
      (phys2_4_lt x)
      (phys2_4_lt (x + 8 * stepConst)))

def phys2_16 (x : Nat) : Nat :=
  packW 1024 (phys2_8 x)
    (phys2_8 (x + 16 * stepConst))

theorem phys2_16_lt (x : Nat) :
    phys2_16 x < 2 ^ 2048 := by
  unfold phys2_16
  simpa [show 1024 + 1024 = 2048 by decide] using
    (packW_lt_double 1024
      (phys2_8 x)
      (phys2_8 (x + 16 * stepConst))
      (phys2_8_lt x)
      (phys2_8_lt (x + 16 * stepConst)))

def phys2_32 (x : Nat) : Nat :=
  packW 2048 (phys2_16 x)
    (phys2_16 (x + 32 * stepConst))

theorem phys2_32_lt (x : Nat) :
    phys2_32 x < 2 ^ 4096 := by
  unfold phys2_32
  simpa [show 2048 + 2048 = 4096 by decide] using
    (packW_lt_double 2048
      (phys2_16 x)
      (phys2_16 (x + 32 * stepConst))
      (phys2_16_lt x)
      (phys2_16_lt (x + 32 * stepConst)))

def phys2_64 (x : Nat) : Nat :=
  packW 4096 (phys2_32 x)
    (phys2_32 (x + 64 * stepConst))

theorem phys2_64_lt (x : Nat) :
    phys2_64 x < 2 ^ 8192 := by
  unfold phys2_64
  simpa [show 4096 + 4096 = 8192 by decide] using
    (packW_lt_double 4096
      (phys2_32 x)
      (phys2_32 (x + 64 * stepConst))
      (phys2_32_lt x)
      (phys2_32_lt (x + 64 * stepConst)))

def phys2_128 (x : Nat) : Nat :=
  packW 8192 (phys2_64 x)
    (phys2_64 (x + 128 * stepConst))

theorem phys2_128_lt (x : Nat) :
    phys2_128 x < 2 ^ 16384 := by
  unfold phys2_128
  simpa [show 8192 + 8192 = 16384 by decide] using
    (packW_lt_double 8192
      (phys2_64 x)
      (phys2_64 (x + 128 * stepConst))
      (phys2_64_lt x)
      (phys2_64_lt (x + 128 * stepConst)))

def phys4_1 (x : Nat) : Nat := dense4 x
theorem phys4_1_lt (x : Nat) : phys4_1 x < 2 ^ 256 := by
  unfold phys4_1
  exact Nat.lt_of_lt_of_le (dense4_lt x)
    (Nat.pow_le_pow_right (by omega) (by decide))

def phys4_2 (x : Nat) : Nat :=
  packW 256 (phys4_1 x)
    (phys4_1 (x + 4 * stepConst))

theorem phys4_2_lt (x : Nat) :
    phys4_2 x < 2 ^ 512 := by
  unfold phys4_2
  simpa [show 256 + 256 = 512 by decide] using
    (packW_lt_double 256
      (phys4_1 x)
      (phys4_1 (x + 4 * stepConst))
      (phys4_1_lt x)
      (phys4_1_lt (x + 4 * stepConst)))

def phys4_4 (x : Nat) : Nat :=
  packW 512 (phys4_2 x)
    (phys4_2 (x + 8 * stepConst))

theorem phys4_4_lt (x : Nat) :
    phys4_4 x < 2 ^ 1024 := by
  unfold phys4_4
  simpa [show 512 + 512 = 1024 by decide] using
    (packW_lt_double 512
      (phys4_2 x)
      (phys4_2 (x + 8 * stepConst))
      (phys4_2_lt x)
      (phys4_2_lt (x + 8 * stepConst)))

def phys4_8 (x : Nat) : Nat :=
  packW 1024 (phys4_4 x)
    (phys4_4 (x + 16 * stepConst))

theorem phys4_8_lt (x : Nat) :
    phys4_8 x < 2 ^ 2048 := by
  unfold phys4_8
  simpa [show 1024 + 1024 = 2048 by decide] using
    (packW_lt_double 1024
      (phys4_4 x)
      (phys4_4 (x + 16 * stepConst))
      (phys4_4_lt x)
      (phys4_4_lt (x + 16 * stepConst)))

def phys4_16 (x : Nat) : Nat :=
  packW 2048 (phys4_8 x)
    (phys4_8 (x + 32 * stepConst))

theorem phys4_16_lt (x : Nat) :
    phys4_16 x < 2 ^ 4096 := by
  unfold phys4_16
  simpa [show 2048 + 2048 = 4096 by decide] using
    (packW_lt_double 2048
      (phys4_8 x)
      (phys4_8 (x + 32 * stepConst))
      (phys4_8_lt x)
      (phys4_8_lt (x + 32 * stepConst)))

def phys4_32 (x : Nat) : Nat :=
  packW 4096 (phys4_16 x)
    (phys4_16 (x + 64 * stepConst))

theorem phys4_32_lt (x : Nat) :
    phys4_32 x < 2 ^ 8192 := by
  unfold phys4_32
  simpa [show 4096 + 4096 = 8192 by decide] using
    (packW_lt_double 4096
      (phys4_16 x)
      (phys4_16 (x + 64 * stepConst))
      (phys4_16_lt x)
      (phys4_16_lt (x + 64 * stepConst)))

def phys4_64 (x : Nat) : Nat :=
  packW 8192 (phys4_32 x)
    (phys4_32 (x + 128 * stepConst))

theorem phys4_64_lt (x : Nat) :
    phys4_64 x < 2 ^ 16384 := by
  unfold phys4_64
  simpa [show 8192 + 8192 = 16384 by decide] using
    (packW_lt_double 8192
      (phys4_32 x)
      (phys4_32 (x + 128 * stepConst))
      (phys4_32_lt x)
      (phys4_32_lt (x + 128 * stepConst)))

def phys8_1 (x : Nat) : Nat := dense8 x
theorem phys8_1_lt (x : Nat) : phys8_1 x < 2 ^ 512 := by
  unfold phys8_1
  exact Nat.lt_of_lt_of_le (dense8_lt x)
    (Nat.pow_le_pow_right (by omega) (by decide))

def phys8_2 (x : Nat) : Nat :=
  packW 512 (phys8_1 x)
    (phys8_1 (x + 8 * stepConst))

theorem phys8_2_lt (x : Nat) :
    phys8_2 x < 2 ^ 1024 := by
  unfold phys8_2
  simpa [show 512 + 512 = 1024 by decide] using
    (packW_lt_double 512
      (phys8_1 x)
      (phys8_1 (x + 8 * stepConst))
      (phys8_1_lt x)
      (phys8_1_lt (x + 8 * stepConst)))

def phys8_4 (x : Nat) : Nat :=
  packW 1024 (phys8_2 x)
    (phys8_2 (x + 16 * stepConst))

theorem phys8_4_lt (x : Nat) :
    phys8_4 x < 2 ^ 2048 := by
  unfold phys8_4
  simpa [show 1024 + 1024 = 2048 by decide] using
    (packW_lt_double 1024
      (phys8_2 x)
      (phys8_2 (x + 16 * stepConst))
      (phys8_2_lt x)
      (phys8_2_lt (x + 16 * stepConst)))

def phys8_8 (x : Nat) : Nat :=
  packW 2048 (phys8_4 x)
    (phys8_4 (x + 32 * stepConst))

theorem phys8_8_lt (x : Nat) :
    phys8_8 x < 2 ^ 4096 := by
  unfold phys8_8
  simpa [show 2048 + 2048 = 4096 by decide] using
    (packW_lt_double 2048
      (phys8_4 x)
      (phys8_4 (x + 32 * stepConst))
      (phys8_4_lt x)
      (phys8_4_lt (x + 32 * stepConst)))

def phys8_16 (x : Nat) : Nat :=
  packW 4096 (phys8_8 x)
    (phys8_8 (x + 64 * stepConst))

theorem phys8_16_lt (x : Nat) :
    phys8_16 x < 2 ^ 8192 := by
  unfold phys8_16
  simpa [show 4096 + 4096 = 8192 by decide] using
    (packW_lt_double 4096
      (phys8_8 x)
      (phys8_8 (x + 64 * stepConst))
      (phys8_8_lt x)
      (phys8_8_lt (x + 64 * stepConst)))

def phys8_32 (x : Nat) : Nat :=
  packW 8192 (phys8_16 x)
    (phys8_16 (x + 128 * stepConst))

theorem phys8_32_lt (x : Nat) :
    phys8_32 x < 2 ^ 16384 := by
  unfold phys8_32
  simpa [show 8192 + 8192 = 16384 by decide] using
    (packW_lt_double 8192
      (phys8_16 x)
      (phys8_16 (x + 128 * stepConst))
      (phys8_16_lt x)
      (phys8_16_lt (x + 128 * stepConst)))

def phys16_1 (x : Nat) : Nat := dense16 x
theorem phys16_1_lt (x : Nat) : phys16_1 x < 2 ^ 1024 := by
  unfold phys16_1
  exact Nat.lt_of_lt_of_le (dense16_lt x)
    (Nat.pow_le_pow_right (by omega) (by decide))

def phys16_2 (x : Nat) : Nat :=
  packW 1024 (phys16_1 x)
    (phys16_1 (x + 16 * stepConst))

theorem phys16_2_lt (x : Nat) :
    phys16_2 x < 2 ^ 2048 := by
  unfold phys16_2
  simpa [show 1024 + 1024 = 2048 by decide] using
    (packW_lt_double 1024
      (phys16_1 x)
      (phys16_1 (x + 16 * stepConst))
      (phys16_1_lt x)
      (phys16_1_lt (x + 16 * stepConst)))

def phys16_4 (x : Nat) : Nat :=
  packW 2048 (phys16_2 x)
    (phys16_2 (x + 32 * stepConst))

theorem phys16_4_lt (x : Nat) :
    phys16_4 x < 2 ^ 4096 := by
  unfold phys16_4
  simpa [show 2048 + 2048 = 4096 by decide] using
    (packW_lt_double 2048
      (phys16_2 x)
      (phys16_2 (x + 32 * stepConst))
      (phys16_2_lt x)
      (phys16_2_lt (x + 32 * stepConst)))

def phys16_8 (x : Nat) : Nat :=
  packW 4096 (phys16_4 x)
    (phys16_4 (x + 64 * stepConst))

theorem phys16_8_lt (x : Nat) :
    phys16_8 x < 2 ^ 8192 := by
  unfold phys16_8
  simpa [show 4096 + 4096 = 8192 by decide] using
    (packW_lt_double 4096
      (phys16_4 x)
      (phys16_4 (x + 64 * stepConst))
      (phys16_4_lt x)
      (phys16_4_lt (x + 64 * stepConst)))

def phys16_16 (x : Nat) : Nat :=
  packW 8192 (phys16_8 x)
    (phys16_8 (x + 128 * stepConst))

theorem phys16_16_lt (x : Nat) :
    phys16_16 x < 2 ^ 16384 := by
  unfold phys16_16
  simpa [show 8192 + 8192 = 16384 by decide] using
    (packW_lt_double 8192
      (phys16_8 x)
      (phys16_8 (x + 128 * stepConst))
      (phys16_8_lt x)
      (phys16_8_lt (x + 128 * stepConst)))

def phys32_1 (x : Nat) : Nat := dense32 x
theorem phys32_1_lt (x : Nat) : phys32_1 x < 2 ^ 2048 := by
  unfold phys32_1
  exact Nat.lt_of_lt_of_le (dense32_lt x)
    (Nat.pow_le_pow_right (by omega) (by decide))

def phys32_2 (x : Nat) : Nat :=
  packW 2048 (phys32_1 x)
    (phys32_1 (x + 32 * stepConst))

theorem phys32_2_lt (x : Nat) :
    phys32_2 x < 2 ^ 4096 := by
  unfold phys32_2
  simpa [show 2048 + 2048 = 4096 by decide] using
    (packW_lt_double 2048
      (phys32_1 x)
      (phys32_1 (x + 32 * stepConst))
      (phys32_1_lt x)
      (phys32_1_lt (x + 32 * stepConst)))

def phys32_4 (x : Nat) : Nat :=
  packW 4096 (phys32_2 x)
    (phys32_2 (x + 64 * stepConst))

theorem phys32_4_lt (x : Nat) :
    phys32_4 x < 2 ^ 8192 := by
  unfold phys32_4
  simpa [show 4096 + 4096 = 8192 by decide] using
    (packW_lt_double 4096
      (phys32_2 x)
      (phys32_2 (x + 64 * stepConst))
      (phys32_2_lt x)
      (phys32_2_lt (x + 64 * stepConst)))

def phys32_8 (x : Nat) : Nat :=
  packW 8192 (phys32_4 x)
    (phys32_4 (x + 128 * stepConst))

theorem phys32_8_lt (x : Nat) :
    phys32_8 x < 2 ^ 16384 := by
  unfold phys32_8
  simpa [show 8192 + 8192 = 16384 by decide] using
    (packW_lt_double 8192
      (phys32_4 x)
      (phys32_4 (x + 128 * stepConst))
      (phys32_4_lt x)
      (phys32_4_lt (x + 128 * stepConst)))

def phys64_1 (x : Nat) : Nat := dense64 x
theorem phys64_1_lt (x : Nat) : phys64_1 x < 2 ^ 4096 := by
  unfold phys64_1
  exact Nat.lt_of_lt_of_le (dense64_lt x)
    (Nat.pow_le_pow_right (by omega) (by decide))

def phys64_2 (x : Nat) : Nat :=
  packW 4096 (phys64_1 x)
    (phys64_1 (x + 64 * stepConst))

theorem phys64_2_lt (x : Nat) :
    phys64_2 x < 2 ^ 8192 := by
  unfold phys64_2
  simpa [show 4096 + 4096 = 8192 by decide] using
    (packW_lt_double 4096
      (phys64_1 x)
      (phys64_1 (x + 64 * stepConst))
      (phys64_1_lt x)
      (phys64_1_lt (x + 64 * stepConst)))

def phys64_4 (x : Nat) : Nat :=
  packW 8192 (phys64_2 x)
    (phys64_2 (x + 128 * stepConst))

theorem phys64_4_lt (x : Nat) :
    phys64_4 x < 2 ^ 16384 := by
  unfold phys64_4
  simpa [show 8192 + 8192 = 16384 by decide] using
    (packW_lt_double 8192
      (phys64_2 x)
      (phys64_2 (x + 128 * stepConst))
      (phys64_2_lt x)
      (phys64_2_lt (x + 128 * stepConst)))

def phys128_1 (x : Nat) : Nat := dense128 x
theorem phys128_1_lt (x : Nat) : phys128_1 x < 2 ^ 8192 := by
  unfold phys128_1
  exact Nat.lt_of_lt_of_le (dense128_lt x)
    (Nat.pow_le_pow_right (by omega) (by decide))

def phys128_2 (x : Nat) : Nat :=
  packW 8192 (phys128_1 x)
    (phys128_1 (x + 128 * stepConst))

theorem phys128_2_lt (x : Nat) :
    phys128_2 x < 2 ^ 16384 := by
  unfold phys128_2
  simpa [show 8192 + 8192 = 16384 by decide] using
    (packW_lt_double 8192
      (phys128_1 x)
      (phys128_1 (x + 128 * stepConst))
      (phys128_1_lt x)
      (phys128_1_lt (x + 128 * stepConst)))

def phys256_1 (x : Nat) : Nat := dense256 x
theorem phys256_1_lt (x : Nat) : phys256_1 x < 2 ^ 16384 := by
  unfold phys256_1
  exact Nat.lt_of_lt_of_le (dense256_lt x)
    (Nat.pow_le_pow_right (by omega) (by decide))

theorem bits1_phys (x : Nat) : bits1 x = phys1_1 x := by rfl

theorem bits2_phys (x : Nat)
    (h : x + 1 * stepConst < 2 ^ 64) :
    bits2 x = phys1_2 x := by
  rw [bits2_eq x h]
  unfold phys1_2 phys1_1 dense1
  simp

theorem bits4_phys (x : Nat)
    (h : x + 3 * stepConst < 2 ^ 64) :
    bits4 x = phys1_4 x := by
  unfold phys1_4
  rw [bits4_eq x h]
  rw [bits2_phys x (by omega)]
  rw [bits2_phys (x + 2 * stepConst) (by omega)]

theorem bits8_phys (x : Nat)
    (h : x + 7 * stepConst < 2 ^ 64) :
    bits8 x = phys1_8 x := by
  unfold phys1_8
  rw [bits8_eq x h]
  rw [bits4_phys x (by omega)]
  rw [bits4_phys (x + 4 * stepConst) (by omega)]

theorem bits16_phys (x : Nat)
    (h : x + 15 * stepConst < 2 ^ 64) :
    bits16 x = phys1_16 x := by
  unfold phys1_16
  rw [bits16_eq x h]
  rw [bits8_phys x (by omega)]
  rw [bits8_phys (x + 8 * stepConst) (by omega)]

theorem bits32_phys (x : Nat)
    (h : x + 31 * stepConst < 2 ^ 64) :
    bits32 x = phys1_32 x := by
  unfold phys1_32
  rw [bits32_eq x h]
  rw [bits16_phys x (by omega)]
  rw [bits16_phys (x + 16 * stepConst) (by omega)]

theorem bits64_phys (x : Nat)
    (h : x + 63 * stepConst < 2 ^ 64) :
    bits64 x = phys1_64 x := by
  unfold phys1_64
  rw [bits64_eq x h]
  rw [bits32_phys x (by omega)]
  rw [bits32_phys (x + 32 * stepConst) (by omega)]

theorem bits128_phys (x : Nat)
    (h : x + 127 * stepConst < 2 ^ 64) :
    bits128 x = phys1_128 x := by
  unfold phys1_128
  rw [bits128_eq x h]
  rw [bits64_phys x (by omega)]
  rw [bits64_phys (x + 64 * stepConst) (by omega)]

theorem bits256_phys (x : Nat)
    (h : x + 255 * stepConst < 2 ^ 64) :
    bits256 x = phys1_256 x := by
  unfold phys1_256
  rw [bits256_eq x h]
  rw [bits128_phys x (by omega)]
  rw [bits128_phys (x + 128 * stepConst) (by omega)]
def stageMask1_2 : Nat := lowMask 1
def stageMask1_4 : Nat :=
  maskW 128 stageMask1_2
def stageMask1_8 : Nat :=
  maskW 256 stageMask1_4
def stageMask1_16 : Nat :=
  maskW 512 stageMask1_8
def stageMask1_32 : Nat :=
  maskW 1024 stageMask1_16
def stageMask1_64 : Nat :=
  maskW 2048 stageMask1_32
def stageMask1_128 : Nat :=
  maskW 4096 stageMask1_64
def stageMask1_256 : Nat :=
  maskW 8192 stageMask1_128

theorem stage1_2 (x : Nat) :
    orStage stageMask1_2 63 (phys1_2 x) =
      phys2_1 x := by
  unfold stageMask1_2 phys1_2 phys2_1 dense2
  exact gatherPair_eq 1 (dense1 x)
    (dense1 (x + 1 * stepConst))
    (by decide) (dense1_lt x)
    (dense1_lt (x + 1 * stepConst))

theorem stage1_4 (x : Nat) :
    orStage stageMask1_4 63 (phys1_4 x) =
      phys2_2 x := by
  unfold stageMask1_4 phys1_4 phys2_2
  rw [lift_or_stage 128 stageMask1_2 63
        (phys1_2 x)
        (phys1_2 (x + 2 * stepConst))
        (phys1_2_lt x) (by decide) (by decide) (by decide)]
  rw [stage1_2 x]
  rw [stage1_2 (x + 2 * stepConst)]

theorem stage1_8 (x : Nat) :
    orStage stageMask1_8 63 (phys1_8 x) =
      phys2_4 x := by
  unfold stageMask1_8 phys1_8 phys2_4
  rw [lift_or_stage 256 stageMask1_4 63
        (phys1_4 x)
        (phys1_4 (x + 4 * stepConst))
        (phys1_4_lt x) (by decide) (by decide) (by decide)]
  rw [stage1_4 x]
  rw [stage1_4 (x + 4 * stepConst)]

theorem stage1_16 (x : Nat) :
    orStage stageMask1_16 63 (phys1_16 x) =
      phys2_8 x := by
  unfold stageMask1_16 phys1_16 phys2_8
  rw [lift_or_stage 512 stageMask1_8 63
        (phys1_8 x)
        (phys1_8 (x + 8 * stepConst))
        (phys1_8_lt x) (by decide) (by decide) (by decide)]
  rw [stage1_8 x]
  rw [stage1_8 (x + 8 * stepConst)]

theorem stage1_32 (x : Nat) :
    orStage stageMask1_32 63 (phys1_32 x) =
      phys2_16 x := by
  unfold stageMask1_32 phys1_32 phys2_16
  rw [lift_or_stage 1024 stageMask1_16 63
        (phys1_16 x)
        (phys1_16 (x + 16 * stepConst))
        (phys1_16_lt x) (by decide) (by decide) (by decide)]
  rw [stage1_16 x]
  rw [stage1_16 (x + 16 * stepConst)]

theorem stage1_64 (x : Nat) :
    orStage stageMask1_64 63 (phys1_64 x) =
      phys2_32 x := by
  unfold stageMask1_64 phys1_64 phys2_32
  rw [lift_or_stage 2048 stageMask1_32 63
        (phys1_32 x)
        (phys1_32 (x + 32 * stepConst))
        (phys1_32_lt x) (by decide) (by decide) (by decide)]
  rw [stage1_32 x]
  rw [stage1_32 (x + 32 * stepConst)]

theorem stage1_128 (x : Nat) :
    orStage stageMask1_128 63 (phys1_128 x) =
      phys2_64 x := by
  unfold stageMask1_128 phys1_128 phys2_64
  rw [lift_or_stage 4096 stageMask1_64 63
        (phys1_64 x)
        (phys1_64 (x + 64 * stepConst))
        (phys1_64_lt x) (by decide) (by decide) (by decide)]
  rw [stage1_64 x]
  rw [stage1_64 (x + 64 * stepConst)]

theorem stage1_256 (x : Nat) :
    orStage stageMask1_256 63 (phys1_256 x) =
      phys2_128 x := by
  unfold stageMask1_256 phys1_256 phys2_128
  rw [lift_or_stage 8192 stageMask1_128 63
        (phys1_128 x)
        (phys1_128 (x + 128 * stepConst))
        (phys1_128_lt x) (by decide) (by decide) (by decide)]
  rw [stage1_128 x]
  rw [stage1_128 (x + 128 * stepConst)]

def stageMask2_2 : Nat := lowMask 2
def stageMask2_4 : Nat :=
  maskW 256 stageMask2_2
def stageMask2_8 : Nat :=
  maskW 512 stageMask2_4
def stageMask2_16 : Nat :=
  maskW 1024 stageMask2_8
def stageMask2_32 : Nat :=
  maskW 2048 stageMask2_16
def stageMask2_64 : Nat :=
  maskW 4096 stageMask2_32
def stageMask2_128 : Nat :=
  maskW 8192 stageMask2_64

theorem stage2_2 (x : Nat) :
    orStage stageMask2_2 126 (phys2_2 x) =
      phys4_1 x := by
  unfold stageMask2_2 phys2_2 phys4_1 dense4
  exact gatherPair_eq 2 (dense2 x)
    (dense2 (x + 2 * stepConst))
    (by decide) (dense2_lt x)
    (dense2_lt (x + 2 * stepConst))

theorem stage2_4 (x : Nat) :
    orStage stageMask2_4 126 (phys2_4 x) =
      phys4_2 x := by
  unfold stageMask2_4 phys2_4 phys4_2
  rw [lift_or_stage 256 stageMask2_2 126
        (phys2_2 x)
        (phys2_2 (x + 4 * stepConst))
        (phys2_2_lt x) (by decide) (by decide) (by decide)]
  rw [stage2_2 x]
  rw [stage2_2 (x + 4 * stepConst)]

theorem stage2_8 (x : Nat) :
    orStage stageMask2_8 126 (phys2_8 x) =
      phys4_4 x := by
  unfold stageMask2_8 phys2_8 phys4_4
  rw [lift_or_stage 512 stageMask2_4 126
        (phys2_4 x)
        (phys2_4 (x + 8 * stepConst))
        (phys2_4_lt x) (by decide) (by decide) (by decide)]
  rw [stage2_4 x]
  rw [stage2_4 (x + 8 * stepConst)]

theorem stage2_16 (x : Nat) :
    orStage stageMask2_16 126 (phys2_16 x) =
      phys4_8 x := by
  unfold stageMask2_16 phys2_16 phys4_8
  rw [lift_or_stage 1024 stageMask2_8 126
        (phys2_8 x)
        (phys2_8 (x + 16 * stepConst))
        (phys2_8_lt x) (by decide) (by decide) (by decide)]
  rw [stage2_8 x]
  rw [stage2_8 (x + 16 * stepConst)]

theorem stage2_32 (x : Nat) :
    orStage stageMask2_32 126 (phys2_32 x) =
      phys4_16 x := by
  unfold stageMask2_32 phys2_32 phys4_16
  rw [lift_or_stage 2048 stageMask2_16 126
        (phys2_16 x)
        (phys2_16 (x + 32 * stepConst))
        (phys2_16_lt x) (by decide) (by decide) (by decide)]
  rw [stage2_16 x]
  rw [stage2_16 (x + 32 * stepConst)]

theorem stage2_64 (x : Nat) :
    orStage stageMask2_64 126 (phys2_64 x) =
      phys4_32 x := by
  unfold stageMask2_64 phys2_64 phys4_32
  rw [lift_or_stage 4096 stageMask2_32 126
        (phys2_32 x)
        (phys2_32 (x + 64 * stepConst))
        (phys2_32_lt x) (by decide) (by decide) (by decide)]
  rw [stage2_32 x]
  rw [stage2_32 (x + 64 * stepConst)]

theorem stage2_128 (x : Nat) :
    orStage stageMask2_128 126 (phys2_128 x) =
      phys4_64 x := by
  unfold stageMask2_128 phys2_128 phys4_64
  rw [lift_or_stage 8192 stageMask2_64 126
        (phys2_64 x)
        (phys2_64 (x + 128 * stepConst))
        (phys2_64_lt x) (by decide) (by decide) (by decide)]
  rw [stage2_64 x]
  rw [stage2_64 (x + 128 * stepConst)]

def stageMask4_2 : Nat := lowMask 4
def stageMask4_4 : Nat :=
  maskW 512 stageMask4_2
def stageMask4_8 : Nat :=
  maskW 1024 stageMask4_4
def stageMask4_16 : Nat :=
  maskW 2048 stageMask4_8
def stageMask4_32 : Nat :=
  maskW 4096 stageMask4_16
def stageMask4_64 : Nat :=
  maskW 8192 stageMask4_32

theorem stage4_2 (x : Nat) :
    orStage stageMask4_2 252 (phys4_2 x) =
      phys8_1 x := by
  unfold stageMask4_2 phys4_2 phys8_1 dense8
  exact gatherPair_eq 4 (dense4 x)
    (dense4 (x + 4 * stepConst))
    (by decide) (dense4_lt x)
    (dense4_lt (x + 4 * stepConst))

theorem stage4_4 (x : Nat) :
    orStage stageMask4_4 252 (phys4_4 x) =
      phys8_2 x := by
  unfold stageMask4_4 phys4_4 phys8_2
  rw [lift_or_stage 512 stageMask4_2 252
        (phys4_2 x)
        (phys4_2 (x + 8 * stepConst))
        (phys4_2_lt x) (by decide) (by decide) (by decide)]
  rw [stage4_2 x]
  rw [stage4_2 (x + 8 * stepConst)]

theorem stage4_8 (x : Nat) :
    orStage stageMask4_8 252 (phys4_8 x) =
      phys8_4 x := by
  unfold stageMask4_8 phys4_8 phys8_4
  rw [lift_or_stage 1024 stageMask4_4 252
        (phys4_4 x)
        (phys4_4 (x + 16 * stepConst))
        (phys4_4_lt x) (by decide) (by decide) (by decide)]
  rw [stage4_4 x]
  rw [stage4_4 (x + 16 * stepConst)]

theorem stage4_16 (x : Nat) :
    orStage stageMask4_16 252 (phys4_16 x) =
      phys8_8 x := by
  unfold stageMask4_16 phys4_16 phys8_8
  rw [lift_or_stage 2048 stageMask4_8 252
        (phys4_8 x)
        (phys4_8 (x + 32 * stepConst))
        (phys4_8_lt x) (by decide) (by decide) (by decide)]
  rw [stage4_8 x]
  rw [stage4_8 (x + 32 * stepConst)]

theorem stage4_32 (x : Nat) :
    orStage stageMask4_32 252 (phys4_32 x) =
      phys8_16 x := by
  unfold stageMask4_32 phys4_32 phys8_16
  rw [lift_or_stage 4096 stageMask4_16 252
        (phys4_16 x)
        (phys4_16 (x + 64 * stepConst))
        (phys4_16_lt x) (by decide) (by decide) (by decide)]
  rw [stage4_16 x]
  rw [stage4_16 (x + 64 * stepConst)]

theorem stage4_64 (x : Nat) :
    orStage stageMask4_64 252 (phys4_64 x) =
      phys8_32 x := by
  unfold stageMask4_64 phys4_64 phys8_32
  rw [lift_or_stage 8192 stageMask4_32 252
        (phys4_32 x)
        (phys4_32 (x + 128 * stepConst))
        (phys4_32_lt x) (by decide) (by decide) (by decide)]
  rw [stage4_32 x]
  rw [stage4_32 (x + 128 * stepConst)]

def stageMask8_2 : Nat := lowMask 8
def stageMask8_4 : Nat :=
  maskW 1024 stageMask8_2
def stageMask8_8 : Nat :=
  maskW 2048 stageMask8_4
def stageMask8_16 : Nat :=
  maskW 4096 stageMask8_8
def stageMask8_32 : Nat :=
  maskW 8192 stageMask8_16

theorem stage8_2 (x : Nat) :
    orStage stageMask8_2 504 (phys8_2 x) =
      phys16_1 x := by
  unfold stageMask8_2 phys8_2 phys16_1 dense16
  exact gatherPair_eq 8 (dense8 x)
    (dense8 (x + 8 * stepConst))
    (by decide) (dense8_lt x)
    (dense8_lt (x + 8 * stepConst))

theorem stage8_4 (x : Nat) :
    orStage stageMask8_4 504 (phys8_4 x) =
      phys16_2 x := by
  unfold stageMask8_4 phys8_4 phys16_2
  rw [lift_or_stage 1024 stageMask8_2 504
        (phys8_2 x)
        (phys8_2 (x + 16 * stepConst))
        (phys8_2_lt x) (by decide) (by decide) (by decide)]
  rw [stage8_2 x]
  rw [stage8_2 (x + 16 * stepConst)]

theorem stage8_8 (x : Nat) :
    orStage stageMask8_8 504 (phys8_8 x) =
      phys16_4 x := by
  unfold stageMask8_8 phys8_8 phys16_4
  rw [lift_or_stage 2048 stageMask8_4 504
        (phys8_4 x)
        (phys8_4 (x + 32 * stepConst))
        (phys8_4_lt x) (by decide) (by decide) (by decide)]
  rw [stage8_4 x]
  rw [stage8_4 (x + 32 * stepConst)]

theorem stage8_16 (x : Nat) :
    orStage stageMask8_16 504 (phys8_16 x) =
      phys16_8 x := by
  unfold stageMask8_16 phys8_16 phys16_8
  rw [lift_or_stage 4096 stageMask8_8 504
        (phys8_8 x)
        (phys8_8 (x + 64 * stepConst))
        (phys8_8_lt x) (by decide) (by decide) (by decide)]
  rw [stage8_8 x]
  rw [stage8_8 (x + 64 * stepConst)]

theorem stage8_32 (x : Nat) :
    orStage stageMask8_32 504 (phys8_32 x) =
      phys16_16 x := by
  unfold stageMask8_32 phys8_32 phys16_16
  rw [lift_or_stage 8192 stageMask8_16 504
        (phys8_16 x)
        (phys8_16 (x + 128 * stepConst))
        (phys8_16_lt x) (by decide) (by decide) (by decide)]
  rw [stage8_16 x]
  rw [stage8_16 (x + 128 * stepConst)]

def stageMask16_2 : Nat := lowMask 16
def stageMask16_4 : Nat :=
  maskW 2048 stageMask16_2
def stageMask16_8 : Nat :=
  maskW 4096 stageMask16_4
def stageMask16_16 : Nat :=
  maskW 8192 stageMask16_8

theorem stage16_2 (x : Nat) :
    orStage stageMask16_2 1008 (phys16_2 x) =
      phys32_1 x := by
  unfold stageMask16_2 phys16_2 phys32_1 dense32
  exact gatherPair_eq 16 (dense16 x)
    (dense16 (x + 16 * stepConst))
    (by decide) (dense16_lt x)
    (dense16_lt (x + 16 * stepConst))

theorem stage16_4 (x : Nat) :
    orStage stageMask16_4 1008 (phys16_4 x) =
      phys32_2 x := by
  unfold stageMask16_4 phys16_4 phys32_2
  rw [lift_or_stage 2048 stageMask16_2 1008
        (phys16_2 x)
        (phys16_2 (x + 32 * stepConst))
        (phys16_2_lt x) (by decide) (by decide) (by decide)]
  rw [stage16_2 x]
  rw [stage16_2 (x + 32 * stepConst)]

theorem stage16_8 (x : Nat) :
    orStage stageMask16_8 1008 (phys16_8 x) =
      phys32_4 x := by
  unfold stageMask16_8 phys16_8 phys32_4
  rw [lift_or_stage 4096 stageMask16_4 1008
        (phys16_4 x)
        (phys16_4 (x + 64 * stepConst))
        (phys16_4_lt x) (by decide) (by decide) (by decide)]
  rw [stage16_4 x]
  rw [stage16_4 (x + 64 * stepConst)]

theorem stage16_16 (x : Nat) :
    orStage stageMask16_16 1008 (phys16_16 x) =
      phys32_8 x := by
  unfold stageMask16_16 phys16_16 phys32_8
  rw [lift_or_stage 8192 stageMask16_8 1008
        (phys16_8 x)
        (phys16_8 (x + 128 * stepConst))
        (phys16_8_lt x) (by decide) (by decide) (by decide)]
  rw [stage16_8 x]
  rw [stage16_8 (x + 128 * stepConst)]

def stageMask32_2 : Nat := lowMask 32
def stageMask32_4 : Nat :=
  maskW 4096 stageMask32_2
def stageMask32_8 : Nat :=
  maskW 8192 stageMask32_4

theorem stage32_2 (x : Nat) :
    orStage stageMask32_2 2016 (phys32_2 x) =
      phys64_1 x := by
  unfold stageMask32_2 phys32_2 phys64_1 dense64
  exact gatherPair_eq 32 (dense32 x)
    (dense32 (x + 32 * stepConst))
    (by decide) (dense32_lt x)
    (dense32_lt (x + 32 * stepConst))

theorem stage32_4 (x : Nat) :
    orStage stageMask32_4 2016 (phys32_4 x) =
      phys64_2 x := by
  unfold stageMask32_4 phys32_4 phys64_2
  rw [lift_or_stage 4096 stageMask32_2 2016
        (phys32_2 x)
        (phys32_2 (x + 64 * stepConst))
        (phys32_2_lt x) (by decide) (by decide) (by decide)]
  rw [stage32_2 x]
  rw [stage32_2 (x + 64 * stepConst)]

theorem stage32_8 (x : Nat) :
    orStage stageMask32_8 2016 (phys32_8 x) =
      phys64_4 x := by
  unfold stageMask32_8 phys32_8 phys64_4
  rw [lift_or_stage 8192 stageMask32_4 2016
        (phys32_4 x)
        (phys32_4 (x + 128 * stepConst))
        (phys32_4_lt x) (by decide) (by decide) (by decide)]
  rw [stage32_4 x]
  rw [stage32_4 (x + 128 * stepConst)]

def stageMask64_2 : Nat := lowMask 64
def stageMask64_4 : Nat :=
  maskW 8192 stageMask64_2

theorem stage64_2 (x : Nat) :
    orStage stageMask64_2 4032 (phys64_2 x) =
      phys128_1 x := by
  unfold stageMask64_2 phys64_2 phys128_1 dense128
  exact gatherPair_eq 64 (dense64 x)
    (dense64 (x + 64 * stepConst))
    (by decide) (dense64_lt x)
    (dense64_lt (x + 64 * stepConst))

theorem stage64_4 (x : Nat) :
    orStage stageMask64_4 4032 (phys64_4 x) =
      phys128_2 x := by
  unfold stageMask64_4 phys64_4 phys128_2
  rw [lift_or_stage 8192 stageMask64_2 4032
        (phys64_2 x)
        (phys64_2 (x + 128 * stepConst))
        (phys64_2_lt x) (by decide) (by decide) (by decide)]
  rw [stage64_2 x]
  rw [stage64_2 (x + 128 * stepConst)]

def stageMask128_2 : Nat := lowMask 128

theorem stage128_2 (x : Nat) :
    orStage stageMask128_2 8064 (phys128_2 x) =
      phys256_1 x := by
  unfold stageMask128_2 phys128_2 phys256_1 dense256
  exact gatherPair_eq 128 (dense128 x)
    (dense128 (x + 128 * stepConst))
    (by decide) (dense128_lt x)
    (dense128_lt (x + 128 * stepConst))


def compactTree (q0 : Nat) : Nat :=
  let q1 := orStage stageMask1_256 63 q0
  let q2 := orStage stageMask2_128 126 q1
  let q3 := orStage stageMask4_64 252 q2
  let q4 := orStage stageMask8_32 504 q3
  let q5 := orStage stageMask16_16 1008 q4
  let q6 := orStage stageMask32_8 2016 q5
  let q7 := orStage stageMask64_4 4032 q6
  let q8 := orStage stageMask128_2 8064 q7
  q8

theorem compactTree_bits256 (x : Nat)
    (h : x + 255 * stepConst < 2 ^ 64) :
    compactTree (bits256 x) = dense256 x := by
  rw [bits256_phys x h]
  simp only [compactTree]
  rw [stage1_256 x]
  rw [stage2_128 x]
  rw [stage4_64 x]
  rw [stage8_32 x]
  rw [stage16_16 x]
  rw [stage32_8 x]
  rw [stage64_4 x]
  rw [stage128_2 x]
  rfl

end WideGather
