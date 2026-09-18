#!/usr/bin/env python3
"""Ablation: how much transferable closure comes from fragment length 1,2,...?

Train on sources <16384, test untouched 16385..32767.  For each max fragment
length L, rebuild the bank from scratch and measure exact lower-merge closure.
"""
from __future__ import annotations
import collatz_fragment_transfer_probe as ft

for L in range(1,7):
    ns,bank=ft.learn(3,16383,96,L)
    caps=sum(len(v) for v in bank.values())
    cnt,closed,hard,best=ft.heldout(bank,16385,32767,96)
    print("ABLATION",L,
          "train_sources",ns,
          "caps",caps,
          "held_sources",cnt['sources'],
          "closed",len(closed),
          "hard",len(hard),
          "legal",cnt['legal'],
          "frac",f"{len(closed)}/{cnt['sources']}")
    print("HARD_HEAD",L,hard[:40])
print("STATUS FRAGMENT_LENGTH_ABLATION")
