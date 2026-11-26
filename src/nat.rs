use std::cmp::Ordering;

const BASE: u64 = 1_000_000_000;

#[derive(Clone, Debug, Eq, Hash, PartialEq)]
pub struct BigNat(Vec<u32>);

impl BigNat {
    pub fn zero() -> Self {
        Self(Vec::new())
    }

    pub fn parse_decimal(text: &str) -> Option<Self> {
        if text.is_empty() || !text.bytes().all(|byte| byte.is_ascii_digit()) {
            return None;
        }
        if text.len() > 1 && text.as_bytes()[0] == b'0' {
            return None;
        }
        if text == "0" {
            return Some(Self::zero());
        }
        let mut limbs = Vec::with_capacity(text.len().div_ceil(9));
        let mut end = text.len();
        while end > 0 {
            let start = end.saturating_sub(9);
            let limb = text[start..end].parse::<u32>().ok()?;
            limbs.push(limb);
            end = start;
        }
        let mut value = Self(limbs);
        value.normalize();
        Some(value)
    }

    pub fn is_zero(&self) -> bool {
        self.0.is_empty()
    }

    pub(crate) fn limb_count(&self) -> usize {
        self.0.len()
    }

    pub fn pred(&self) -> Option<Self> {
        if self.is_zero() {
            return None;
        }
        let mut out = self.clone();
        let mut index = 0;
        loop {
            if out.0[index] > 0 {
                out.0[index] -= 1;
                break;
            }
            out.0[index] = (BASE - 1) as u32;
            index += 1;
        }
        out.normalize();
        Some(out)
    }

    pub fn add(&self, other: &Self) -> Self {
        let count = self.0.len().max(other.0.len());
        let mut out = Vec::with_capacity(count + 1);
        let mut carry = 0u64;
        for index in 0..count {
            let left = u64::from(*self.0.get(index).unwrap_or(&0));
            let right = u64::from(*other.0.get(index).unwrap_or(&0));
            let total = left + right + carry;
            out.push((total % BASE) as u32);
            carry = total / BASE;
        }
        if carry != 0 {
            out.push(carry as u32);
        }
        Self(out)
    }

    pub fn sub_trunc(&self, other: &Self) -> Self {
        if self.compare(other) == Ordering::Less {
            return Self::zero();
        }
        let mut out = Vec::with_capacity(self.0.len());
        let mut borrow = 0i64;
        for index in 0..self.0.len() {
            let left = i64::from(self.0[index]) - borrow;
            let right = i64::from(*other.0.get(index).unwrap_or(&0));
            if left < right {
                out.push((left + BASE as i64 - right) as u32);
                borrow = 1;
            } else {
                out.push((left - right) as u32);
                borrow = 0;
            }
        }
        let mut value = Self(out);
        value.normalize();
        value
    }

    pub fn compare(&self, other: &Self) -> Ordering {
        match self.0.len().cmp(&other.0.len()) {
            Ordering::Equal => self.0.iter().rev().cmp(other.0.iter().rev()),
            order => order,
        }
    }

    pub fn mul_bounded(&self,other:&Self,work:&mut usize)->Option<Self> {
        let cost=self.0.len().checked_mul(other.0.len())?.checked_add(1)?;
        *work=work.checked_sub(cost)?;
        if self.is_zero() || other.is_zero() {return Some(Self::zero());}
        let mut out=vec![0u32;self.0.len().checked_add(other.0.len())?];
        for (i,left) in self.0.iter().enumerate() {
            let mut carry=0u64;
            for (j,right) in other.0.iter().enumerate() {
                let total=u64::from(out[i+j])+u64::from(*left)*u64::from(*right)+carry;
                out[i+j]=(total%BASE) as u32;carry=total/BASE;
            }
            out[i+other.0.len()]=carry as u32;
        }
        let mut result=Self(out);result.normalize();Some(result)
    }

    pub fn pow_bounded(&self,exponent:&Self,work:&mut usize)->Option<Self> {
        // Match the pinned kernel's 32-bit exponent limit, then account for
        // each limb multiplication before allocating its result.
        let mut count=0u64;
        for limb in exponent.0.iter().rev() {count=count.checked_mul(BASE)?.checked_add(u64::from(*limb))?;}
        if count>u64::from(u32::MAX) {return None;}
        let mut result=Self(vec![1]);let mut base=self.clone();
        while count!=0 {
            *work=work.checked_sub(1)?;
            if count&1==1 {result=result.mul_bounded(&base,work)?;}
            count>>=1;
            if count!=0 {base=base.mul_bounded(&base,work)?;}
        }
        Some(result)
    }

    pub fn land_bounded(&self, other: &Self, work: &mut usize) -> Option<Self> {
        *work = work.checked_sub(1)?;
        if self.is_zero() || other.is_zero() { return Some(Self::zero()); }
        let left = self.binary_digits_bounded(work)?;
        let right = other.binary_digits_bounded(work)?;
        let mut result = Self::zero();
        for i in (0..left.len().min(right.len())).rev() {
            result.append_bit_bounded(left[i] && right[i], work)?;
        }
        Some(result)
    }

    pub fn shift_right_bounded(&self, shift: &Self, work: &mut usize) -> Option<Self> {
        *work = work.checked_sub(1)?;
        // BASE < 2^30, so this bounds the bit length without materializing it.
        let bound = u64::try_from(self.0.len().checked_mul(30)?).ok()?;
        let count = shift.to_u64();
        if count.is_none_or(|n| n >= bound) { return Some(Self::zero()); }
        let count = usize::try_from(count?).ok()?;
        if count == 0 {
            *work = work.checked_sub(self.0.len())?;
            return Some(self.clone());
        }
        let bits = self.binary_digits_bounded(work)?;
        let mut result = Self::zero();
        if count < bits.len() {
            for bit in bits[count..].iter().rev() { result.append_bit_bounded(*bit, work)?; }
        }
        Some(result)
    }

    pub fn div_mod_bounded(&self, divisor: &Self, work: &mut usize) -> Option<(Self,Self)> {
        *work = work.checked_sub(1)?;
        if divisor.is_zero() {
            *work = work.checked_sub(self.0.len())?;
            return Some((Self::zero(),self.clone()));
        }
        *work = work.checked_sub(self.0.len().max(divisor.0.len()))?;
        if self.compare(divisor) == Ordering::Less {
            *work = work.checked_sub(self.0.len())?;
            return Some((Self::zero(),self.clone()));
        }
        let bits = self.binary_digits_bounded(work)?;
        let mut quotient = Self::zero();
        let mut remainder = Self::zero();
        for bit in bits.iter().rev() {
            remainder.append_bit_bounded(*bit,work)?;
            *work = work.checked_sub(remainder.0.len().max(divisor.0.len()))?;
            let subtract = remainder.compare(divisor) != Ordering::Less;
            if subtract {
                *work = work.checked_sub(remainder.0.len().checked_add(1)?)?;
                remainder = remainder.sub_trunc(divisor);
            }
            quotient.append_bit_bounded(subtract,work)?;
        }
        Some((quotient,remainder))
    }

    fn to_u64(&self) -> Option<u64> {
        let mut result = 0u64;
        for limb in self.0.iter().rev() {
            result = result.checked_mul(BASE)?.checked_add(u64::from(*limb))?;
        }
        Some(result)
    }

    fn binary_digits_bounded(&self, work: &mut usize) -> Option<Vec<bool>> {
        *work = work.checked_sub(self.0.len().checked_add(1)?)?;
        let mut number = self.clone();
        let mut bits = Vec::new();
        while !number.is_zero() {
            *work = work.checked_sub(number.0.len().checked_add(1)?)?;
            let mut carry = 0u64;
            for limb in number.0.iter_mut().rev() {
                let value = carry * BASE + u64::from(*limb);
                *limb = (value / 2) as u32;
                carry = value % 2;
            }
            number.normalize();
            bits.push(carry != 0);
        }
        Some(bits)
    }

    fn append_bit_bounded(&mut self, bit: bool, work: &mut usize) -> Option<()> {
        *work = work.checked_sub(self.0.len().checked_add(1)?)?;
        let mut carry = u64::from(bit);
        for limb in &mut self.0 {
            let value = u64::from(*limb) * 2 + carry;
            *limb = (value % BASE) as u32;
            carry = value / BASE;
        }
        if carry != 0 { self.0.push(carry as u32); }
        Some(())
    }

    fn normalize(&mut self) {
        while self.0.last() == Some(&0) {
            self.0.pop();
        }
    }
}

#[cfg(test)]
mod tests {
    use super::BigNat;
    use std::cmp::Ordering;

    #[test]
    fn parses_beyond_u64_and_steps_exactly() {
        let n = BigNat::parse_decimal("18446744073709551616").unwrap();
        let p = n.pred().unwrap();
        assert_eq!(p.compare(&n), Ordering::Less);
        assert_eq!(p.add(&BigNat::parse_decimal("1").unwrap()), n);
    }

    #[test]
    fn subtraction_truncates_at_zero() {
        let a = BigNat::parse_decimal("1000000").unwrap();
        let b = BigNat::parse_decimal("1000001").unwrap();
        assert!(a.sub_trunc(&b).is_zero());
    }

    #[test]
    fn bounded_products_and_powers_are_exact_beyond_machine_words() {
        let n=|s:&str|BigNat::parse_decimal(s).unwrap();
        assert_eq!(n("999999999999999999").mul_bounded(&n("999999999999999999"),&mut 64),Some(n("999999999999999998000000000000000001")));
        assert_eq!(n("2").pow_bounded(&n("64"),&mut 128),Some(n("18446744073709551616")));
        assert_eq!(n("0").pow_bounded(&n("0"),&mut 1),Some(n("1")));
        assert_eq!(n("0").pow_bounded(&n("9"),&mut 64),Some(n("0")));
        assert_eq!(n("12").mul_bounded(&n("0"),&mut 1),Some(n("0")));
        assert_eq!(n("2").pow_bounded(&n("32"),&mut 1),None);
        assert_eq!(n("2").pow_bounded(&n("4294967296"),&mut 65536),None);
        assert_eq!(n("999999999999999999").mul_bounded(&n("999999999999999999"),&mut 4),None);
        for a in 0u128..30 {
            for b in 0u128..30 {
                assert_eq!(n(&a.to_string()).mul_bounded(&n(&b.to_string()),&mut 16),Some(n(&(a*b).to_string())));
            }
            for b in 0u32..8 {
                assert_eq!(n(&a.to_string()).pow_bounded(&n(&b.to_string()),&mut 64),Some(n(&a.pow(b).to_string())));
            }
        }
    }
    #[test]
    fn bounded_bit_operations_match_exact_native_arithmetic() {
        let n=|s:&str|BigNat::parse_decimal(s).unwrap();
        for a in 0u64..64 {
            for b in 0u64..64 {
                assert_eq!(n(&a.to_string()).land_bounded(&n(&b.to_string()),&mut 4096),Some(n(&(a&b).to_string())));
            }
            for shift in 0u64..70 {
                assert_eq!(n(&a.to_string()).shift_right_bounded(&n(&shift.to_string()),&mut 4096),Some(n(&a.checked_shr(shift as u32).unwrap_or(0).to_string())));
            }
        }
        let huge=n("170141183460469231731687303715884105770");
        assert_eq!(huge.land_bounded(&n("170141183460469231731687303715884105727"),&mut 32768),Some(n("42")));
        assert_eq!(huge.shift_right_bounded(&n("64"),&mut 32768),Some(n("9223372036854775808")));
        assert_eq!(huge.shift_right_bounded(&n("128"),&mut 32768),Some(n("0")));
        assert_eq!(huge.shift_right_bounded(&n("18446744073709551616"),&mut 1),Some(n("0")));
        assert!(huge.land_bounded(&huge,&mut 1).is_none());
        assert!(huge.shift_right_bounded(&n("1"),&mut 1).is_none());
    }

    #[test]
    fn bounded_division_preserves_euclidean_and_zero_divisor_semantics() {
        let n=|s:&str|BigNat::parse_decimal(s).unwrap();
        for a in 0u64..100 {
            for b in 0u64..50 {
                let (q,r)=if b==0 {(0,a)} else {(a/b,a%b)};
                assert_eq!(n(&a.to_string()).div_mod_bounded(&n(&b.to_string()),&mut 4096),Some((n(&q.to_string()),n(&r.to_string()))));
            }
        }
        assert_eq!(n("18446744073709551616").div_mod_bounded(&n("3"),&mut 32768),Some((n("6148914691236517205"),n("1"))));
        let dividend=n("170141183460469231731687303715884105770");
        let divisor=n("18446744073709551616");
        let (q,r)=dividend.div_mod_bounded(&divisor,&mut 32768).unwrap();
        assert_eq!(q,n("9223372036854775808"));assert_eq!(r,n("42"));
        assert_eq!(q.mul_bounded(&divisor,&mut 32768).unwrap().add(&r),dividend);
        assert!(r.compare(&divisor)==Ordering::Less);
        assert!(dividend.div_mod_bounded(&n("3"),&mut 1).is_none());
    }

}
