\\ V5 exact SEA-based elliptic point-counting with both 876 coefficient signs.
\\ NIST P-256; source-frozen V4 b coefficients, no inferred historical choice.
\\ PARI/GP external arithmetic authority and prime prover.
default(parisizemax, 1500000000);
p=115792089210356248762697446949407573530086143415290314195533631308867097853951;
published_b=41058363725152142129326129780047268409114441015993725554835256314039467401291;
skipped_b_lo=39662553531246491965525372057557462947623851008428349361619641894248715758146;
skipped_b_hi=76129535679109756797172074891850110582462292406861964833913989414618382095805;
checkcurve(label,b)=
{
  my(E,n,ip);
  E=ellinit([-3,b],p);
  n=ellsea(E,1);
  if(n > 0, ip=isprime(n), ip=-1);
  print("V5|",label,"|",n,"|",ip);
};
print("PARI_VERSION|",version());
checkcurve("published",published_b);
checkcurve("skipped_lo",skipped_b_lo);
checkcurve("skipped_hi",skipped_b_hi);
quit(0);