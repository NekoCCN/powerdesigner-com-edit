#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UML Component Diagram Builder (组件图 / 构件图构建器)
Features:
- Components (Modules / Microservices) and Interfaces
- Component Dependencies / Assemblies
- Architectural Tier Layout
"""

from typing import Dict, Tuple, List, Optional, Any
from .collision import CollisionDetector
from .client import attach_link_symbol


class ComponentDiagramBuilder:
    """
    Constructs UML Component Diagrams (组件图) in PowerDesigner OOM.
    Models modular subsystem architectures and dependencies.
    """

    def __init__(
        self,
        diagram: Any,
        start_x: int = -20000,
        spacing_x: int = 18000,
        start_y: int = 12000,
        spacing_y: int = -8000,
    ):
        self.diagram = diagram
        self.model = diagram.Model
        self.start_x = start_x
        self.spacing_x = spacing_x
        self.start_y = start_y
        self.spacing_y = spacing_y

        self.components: Dict[str, Tuple[Any, Any]] = {}
        self.interfaces: Dict[str, Tuple[Any, Any]] = {}
        self.dependencies: List[Tuple[Any, Any]] = []

    def add_component(
        self,
        name: str,
        x: Optional[int] = None,
        y: Optional[int] = None,
        width: int = 12000,
        height: int = 6000,
    ) -> Any:
        comp = self.model.Components.CreateNew()
        comp.Name = name
        sym = self.diagram.AttachObject(comp)

        idx = len(self.components)
        pos_x = x if x is not None else (self.start_x + (idx % 3) * self.spacing_x)
        pos_y = y if y is not None else (self.start_y + (idx // 3) * self.spacing_y)

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

        self.components[name] = (comp, sym)
        return comp

    def add_dependency(
        self,
        from_comp: str,
        to_comp: str,
        stereotype: str = "use",
    ) -> Any:
        """Create a directed dependency link between two components."""
        if from_comp not in self.components or to_comp not in self.components:
            return None

        src_obj, _ = self.components[from_comp]
        tgt_obj, _ = self.components[to_comp]

        dep = self.model.ComponentDependencies.CreateNew() if hasattr(self.model, "ComponentDependencies") else self.model.Dependencies.CreateNew()
        dep.Object1 = src_obj
        dep.Object2 = tgt_obj
        if stereotype and hasattr(dep, "Stereotype"):
            dep.Stereotype = stereotype

        sym_l = attach_link_symbol(self.diagram, dep)
        self.dependencies.append((dep, sym_l))
        return sym_l
