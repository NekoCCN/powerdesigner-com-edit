#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UML Use Case Diagram Builder with 3-Column Collision-Free Auto-Layout
"""

from typing import Dict, Tuple, Any
from .collision import CollisionDetector

class UseCaseDiagramBuilder:
    """
    Constructs clean, collision-free 3-column Use Case Diagrams:
    Column 1: Primary Human Actors
    Column 2: System Boundary / Use Cases
    Column 3: Secondary Actors / External Systems
    """

    def __init__(self, diagram: Any, col1_x: int = 1500, col2_x: int = 5500, col3_x: int = 9500, start_y: int = -1000, step_y: int = -1200):
        self.diagram = diagram
        self.model = diagram.Model
        self.col1_x = col1_x
        self.col2_x = col2_x
        self.col3_x = col3_x
        self.start_y = start_y
        self.step_y = step_y

        self.actors: Dict[str, Tuple[Any, Any]] = {}
        self.use_cases: Dict[str, Tuple[Any, Any]] = {}

    def add_actor(self, name: str, is_secondary: bool = False) -> Any:
        act = self.model.Actors.CreateNew()
        act.SetName(name)
        sym = self.diagram.AttachObject(act)
        idx = len(self.actors)
        x = self.col3_x if is_secondary else self.col1_x
        y = self.start_y + idx * self.step_y
        try:
            sym.Position.X = x
            sym.Position.Y = y
        except Exception:
            pass
        self.actors[name] = (act, sym)
        return act

    def add_use_case(self, name: str, code: str = "") -> Any:
        uc = self.model.UseCases.CreateNew()
        full_name = f"{code} {name}".strip() if code else name
        uc.SetName(full_name)
        sym = self.diagram.AttachObject(uc)
        idx = len(self.use_cases)
        x = self.col2_x
        y = self.start_y + idx * self.step_y
        try:
            sym.Position.X = x
            sym.Position.Y = y
            sym.Size.Width = 3200
            sym.Size.Height = 1000
        except Exception:
            pass
        self.use_cases[name] = (uc, sym)
        return uc

    def link(self, actor_name: str, use_case_name: str, stereotype: str = ""):
        """Create an association or stereotype dependency between Actor and UseCase."""
        if actor_name not in self.actors or use_case_name not in self.use_cases:
            return
        act_obj, _ = self.actors[actor_name]
        uc_obj, _ = self.use_cases[use_case_name]
        assoc = self.model.ExtendedDependencies.CreateNew()
        assoc.Source = act_obj
        assoc.Destination = uc_obj
        if stereotype:
            assoc.Stereotype = stereotype
        self.diagram.AttachObject(assoc)

    def link_use_cases(self, source_uc_name: str, target_uc_name: str, stereotype: str = "include"):
        """Create <<include>> or <<extend>> dependency between two use cases."""
        if source_uc_name not in self.use_cases or target_uc_name not in self.use_cases:
            return
        src_obj, _ = self.use_cases[source_uc_name]
        tgt_obj, _ = self.use_cases[target_uc_name]
        dep = self.model.ExtendedDependencies.CreateNew()
        dep.Source = src_obj
        dep.Destination = tgt_obj
        dep.Stereotype = stereotype
        self.diagram.AttachObject(dep)

    def audit_and_fix_overlaps(self):
        """Run collision detection on use cases and auto-adjust spacing if necessary."""
        symbols = [sym for _, sym in self.use_cases.values()]
        CollisionDetector.auto_resolve_vertical_overlaps(symbols, min_spacing=300)
