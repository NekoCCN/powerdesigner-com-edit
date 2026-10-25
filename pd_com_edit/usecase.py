#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UML Use Case Diagram Builder with Collision-Free Auto-Layout and Verified Association Links
"""

from typing import Dict, Tuple, List, Optional, Any
from .collision import CollisionDetector
from .client import attach_link_symbol, KIND_ACTOR, KIND_USECASE, KIND_USECASE_ASSOC, KIND_DEPENDENCY


class UseCaseDiagramBuilder:
    """
    Constructs clean, collision-free Use Case Diagrams with full association link support.
    
    Coordinates use PowerDesigner logical units (~3000-4000 units per cm):
    - col1_x: Primary Actors on the left (e.g. -38000)
    - col2_x: Center-Left Use Cases (e.g. -14000)
    - col3_x: Center-Right Use Cases (e.g. 14000)
    - col4_x: Secondary / External System Actors on the right (e.g. 38000)
    """

    def __init__(
        self,
        diagram: Any,
        col1_x: int = -38000,
        col2_x: int = -14000,
        col3_x: int = 14000,
        col4_x: int = 38000,
        start_y: int = 28000,
        step_y: int = -8000,
    ):
        self.diagram = diagram
        self.model = diagram.Model
        self.col1_x = col1_x
        self.col2_x = col2_x
        self.col3_x = col3_x
        self.col4_x = col4_x
        self.start_y = start_y
        self.step_y = step_y

        self.actors: Dict[str, Tuple[Any, Any]] = {}
        self.use_cases: Dict[str, Tuple[Any, Any]] = {}
        self.links: List[Tuple[Any, Any]] = []

    def add_actor(
        self,
        name: str,
        code: str = "",
        is_secondary: bool = False,
        is_primary: Optional[bool] = None,
        column: int = 1,
        x: Optional[int] = None,
        y: Optional[int] = None,
    ) -> Any:
        """Create and attach an Actor symbol to the diagram."""
        if is_primary is not None:
            is_secondary = not is_primary

        try:
            act = self.model.CreateObject(KIND_ACTOR)
        except Exception:
            act = self.model.Actors.CreateNew()

        act.SetName(name)
        if code:
            act.Code = code
        elif hasattr(act, "Code") and not act.Code:
            act.Code = f"Actor_{len(self.actors) + 1}"

        sym = self.diagram.AttachObject(act)

        # Coordinate positioning
        idx = len(self.actors)
        default_x = self.col4_x if (is_secondary or column >= 4) else self.col1_x
        pos_x = x if x is not None else default_x
        pos_y = y if y is not None else (self.start_y + idx * self.step_y)

        try:
            if hasattr(sym, "Position"):
                sym.Position.X = pos_x
                sym.Position.Y = pos_y
        except Exception:
            pass

        self.actors[name] = (act, sym)
        return act

    def add_system(
        self,
        name: str,
        code: str = "",
        x: Optional[int] = None,
        y: Optional[int] = None,
    ) -> Any:
        """Convenience method to register an External System / Secondary Actor on the right."""
        return self.add_actor(name=name, code=code, is_secondary=True, column=4, x=x, y=y)

    def add_use_case(
        self,
        name: str,
        code: str = "",
        column: int = 2,
        x: Optional[int] = None,
        y: Optional[int] = None,
        width: int = 14000,
        height: int = 4000,
    ) -> Any:
        """Create and attach a Use Case symbol to the diagram."""
        try:
            uc = self.model.CreateObject(KIND_USECASE)
        except Exception:
            uc = self.model.UseCases.CreateNew()

        full_name = f"{code} {name}".strip() if code else name
        uc.SetName(full_name)
        if code:
            uc.Code = code

        sym = self.diagram.AttachObject(uc)

        idx = len(self.use_cases)
        col_x = self.col2_x if column <= 2 else self.col3_x
        pos_x = x if x is not None else col_x
        pos_y = y if y is not None else (self.start_y + idx * self.step_y)

        try:
            if hasattr(sym, "Position"):
                sym.Position.X = pos_x
                sym.Position.Y = pos_y
            if hasattr(sym, "Size"):
                if hasattr(sym.Size, "X"):
                    sym.Size.X = width
                    sym.Size.Y = height
                elif hasattr(sym.Size, "Width"):
                    sym.Size.Width = width
                    sym.Size.Height = height
        except Exception:
            pass

        self.use_cases[name] = (uc, sym)
        return uc

    add_usecase = add_use_case

    def link(self, actor_name: str, use_case_name: str, stereotype: str = "") -> Any:
        """
        Create a solid UML Association link between an Actor and a Use Case.
        Uses PowerDesigner's native Use Case Association (403775603) and attaches
        via AttachLinkObject.
        """
        if actor_name not in self.actors or use_case_name not in self.use_cases:
            return None

        act_obj, _ = self.actors[actor_name]
        uc_obj, _ = self.use_cases[use_case_name]

        try:
            assoc = self.model.CreateObject(KIND_USECASE_ASSOC)
        except Exception:
            assoc = self.model.Associations.CreateNew()

        assoc.Object1 = act_obj
        assoc.Object2 = uc_obj
        if stereotype and hasattr(assoc, "Stereotype"):
            assoc.Stereotype = stereotype

        sym_l = attach_link_symbol(self.diagram, assoc)
        self.links.append((assoc, sym_l))
        return sym_l

    def link_use_cases(
        self,
        source_uc_name: str,
        target_uc_name: str,
        stereotype: str = "include",
    ) -> Any:
        """
        Create an <<include>> or <<extend>> dependency link between two use cases.
        Attaches via AttachLinkObject.
        """
        if source_uc_name not in self.use_cases or target_uc_name not in self.use_cases:
            return None

        src_obj, _ = self.use_cases[source_uc_name]
        tgt_obj, _ = self.use_cases[target_uc_name]

        try:
            dep = self.model.CreateObject(KIND_DEPENDENCY)
        except Exception:
            dep = self.model.ExtendedDependencies.CreateNew()

        dep.Object1 = src_obj
        dep.Object2 = tgt_obj
        if stereotype and hasattr(dep, "Stereotype"):
            dep.Stereotype = stereotype

        sym_l = attach_link_symbol(self.diagram, dep)
        self.links.append((dep, sym_l))
        return sym_l

    def connect(self, source: str, target: str, stereotype: str = "") -> Any:
        """
        Universal connection helper:
        - If (Actor, UseCase) or (UseCase, Actor): creates Use Case Association.
        - If (UseCase, UseCase): creates <<include>> / <<extend>> dependency.
        """
        if source in self.actors and target in self.use_cases:
            return self.link(source, target, stereotype)
        elif source in self.use_cases and target in self.actors:
            return self.link(target, source, stereotype)
        elif source in self.use_cases and target in self.use_cases:
            return self.link_use_cases(source, target, stereotype or "include")
        return None

    def layout_three_column(self, min_spacing: int = 1500):
        """
        Arrange all actors and use cases into structured columns:
        - Left: Primary human actors
        - Center: Core system use cases (supports 1 or 2 center columns)
        - Right: External systems / secondary actors
        """
        # Reposition primary actors
        primary_actors = [item for item in self.actors.values() if item[1] is not None]
        for idx, (_, sym) in enumerate(primary_actors):
            try:
                # If actor is near right side, keep it right, else left
                if hasattr(sym, "Position"):
                    if sym.Position.X < 0:
                        sym.Position.X = self.col1_x
                        sym.Position.Y = self.start_y + idx * self.step_y
                    else:
                        sym.Position.X = self.col4_x
                        sym.Position.Y = self.start_y + idx * self.step_y
            except Exception:
                pass

        self.audit_and_fix_overlaps(min_spacing=min_spacing)

    def audit_and_fix_overlaps(self, min_spacing: int = 1500):
        """Run collision detection on use cases and auto-adjust vertical spacing."""
        symbols = [sym for _, sym in self.use_cases.values() if sym is not None]
        if symbols:
            CollisionDetector.auto_resolve_vertical_overlaps(symbols, min_spacing=min_spacing)
