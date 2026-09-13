from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class Row:
    banks: tuple[tuple[int,...], ...]
    consequence: int|None
@dataclass(frozen=True)
class World:
    world_id: str
    rows: tuple[Row,...]
    complete: bool=True
    probes: tuple[Row,...]=()
@dataclass(frozen=True)
class Term:
    op:str; args:tuple[Any,...]; cost:int; bits:int; deps:tuple[tuple[int,int],...]; depth:int
    def data(self): return ['ATOM',*self.args] if self.op=='ATOM' else ['NAND',self.args[0].data(),self.args[1].data()]
