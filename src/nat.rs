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
}
