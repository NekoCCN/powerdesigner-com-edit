#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UML Activity Diagram Builder (活动图构建器)
Features:
- Initial Nodes, Activity Actions, Decisions, Fork/Join Bars, Final Nodes
- Control Flows connecting workflow states with guard conditions
- Top-to-bottom automatic vertical workflow layout
"""

from typing import Dict, Tuple, List, Optional, Any
from .collision import CollisionDetector
from .client import attach_link_symbol


class ActivityDiagramBuilder:
    """
    Constructs UML Activity Diagrams (活动图) in PowerDesigner OOM.
    Supports business process flows, control decisions, and concurrency.
    """

    def __init__(
        self,
        diagram: Any,
        start_x: int = 0,
        start_y: int = 24000,
        step_y: int = -6000,
        node_width: int = 14000,
        node_height: int = 4000,
    ):
        self.diagram = diagram
        self.model = diagram.Model
        self.start_x = start_x
        self.start_y = start_y
        self.step_y = step_y
        self.node_width = node_width
        self.node_height = node_height

        self.nodes: Dict[str, Tuple[Any, Any]] = {}
        self.flows: List[Tuple[Any, Any]] = []

    def add_activity(
        self,
        name: str,
        x: Optional[int] = None,
        y: Optional[int] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
    ) -> Any:
        """Create and attach an Activity / Action node."""
        act = self.model.Activities.CreateNew()
        act.Name = name
        sym = self.diagram.AttachObject(act)

        idx = len(self.nodes)
        pos_x = x if x is not None else self.start_x
        pos_y = y if y is not None else (self.start_y + idx * self.step_y)
        w = width or self.node_width
        h = height or self.node_height

        try:
            if hasattr(sym, "Position"):
                sym.Position.X = pos_x
                sym.Position.Y = pos_y
            if hasattr(sym, "Size"):
                if hasattr(sym.Size, "X"):
                    sym.Size.X = w
                    sym.Size.Y = h
                elif hasattr(sym.Size, "Width"):
                    sym.Size.Width = w
                    sym.Size.Height = h
        except Exception:
            pass

        self.nodes[name] = (act, sym)
        return act

    def add_decision(
        self,
        name: str,
        x: Optional[int] = None,
        y: Optional[int] = None,
    ) -> Any:
        """Create a Decision / Merge diamond node."""
        dec = self.model.Decisions.CreateNew()
        dec.Name = name
        sym = self.diagram.AttachObject(dec)

        idx = len(self.nodes)
        pos_x = x if x is not None else self.start_x
        pos_y = y if y is not None else (self.start_y + idx * self.step_y)

        try:
            if hasattr(sym, "Position"):
                sym.Position.X = pos_x
                sym.Position.Y = pos_y
        except Exception:
            pass

        self.nodes[name] = (dec, sym)
        return dec

    def add_flow(
        self,
        from_name: str,
        to_name: str,
        guard: str = "",
    ) -> Any:
        """Create a directed Control Flow connector between two activity nodes."""
        if from_name not in self.nodes or to_name not in self.nodes:
            return None

        src_obj, _ = self.nodes[from_name]
        tgt_obj, _ = self.nodes[to_name]

        flow = self.model.Flows.CreateNew()
        flow.Object1 = src_obj
        flow.Object2 = tgt_obj
        if guard:
            if hasattr(flow, "Condition"):
                flow.Condition = guard
            if hasattr(flow, "Name"):
                flow.Name = f"[{guard}]"

        sym_l = attach_link_symbol(self.diagram, flow)
        self.flows.append((flow, sym_l))
        return sym_l

    def layout_vertical(self, min_spacing: int = 1500):
        """Linearly arrange nodes top-to-bottom and fix overlaps."""
        symbols = [sym for _, sym in self.nodes.values() if sym is not None]
        if symbols:
            CollisionDetector.auto_resolve_vertical_overlaps(symbols, min_spacing=min_spacing)
