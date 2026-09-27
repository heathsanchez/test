#!/usr/bin/env python3
"""Run the exact RIGID recharge SCC/cycle audit on frozen + prospective bands."""
import collatz_q0_rigid_recharge_audit as r
print("=== FROZEN 3..8191 K128 ===")
r.analyze(8191,128,3)
print("=== PROSPECTIVE 8193..32767 K128 ===")
r.analyze(32767,128,8193)
