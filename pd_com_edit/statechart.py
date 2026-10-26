#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UML State Machine / Statechart Diagram Builder (状态机图 / 状态图构建器)
Features:
- States (Composite / Simple), Initial / Final States
- Transitions with Event, Guard Condition, and Action triggers
- Pipeline / Layered state machine layout
"""

from typing import Dict, Tuple, List, Optional, Any
from .collision import CollisionDetector
from .client import attach_link_symbol


class StatechartDiagramBuilder:
    """
    Constructs UML State Machine Diagrams (状态机图) in PowerDesigner OOM.
    Models entity lifecycles, states, and event-driven transitions.
    """

    def __init__(
        self,
        diagram: Any,
        start_x: int = -20000,
        step_x: int = 15000,
        start_y: int = 0,
        step_y: int = -8000,
        state_width: int = 12000,
        state_height: int = 5000,
    ):
        self.diagram = diagram
        self.model = diagram.Model
        self.start_x = start_x
        self.step_x = step_x
        self.start_y = start_y
        self.step_y = step_y
        self.state_width = state_width
        self.state_height = state_height

        self.states: Dict[str, Tuple[Any, Any]] = {}
        self.transitions: List[Tuple[Any, Any]] = []

    def add_state(
        self,
        name: str,
        x: Optional[int] = None,
        y: Optional[int] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
    ) -> Any:
        """Create and attach a State node to the diagram."""
        st = self.model.States.CreateNew()
        st.Name = name
        sym = self.diagram.AttachObject(st)

        idx = len(self.states)
        pos_x = x if x is not None else (self.start_x + (idx % 4) * self.step_x)
        pos_y = y if y is not None else (self.start_y + (idx // 4) * self.step_y)
        w = width or self.state_width
        h = height or self.state_height

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

        self.states[name] = (st, sym)
        return st

    def add_transition(
        self,
        from_state: str,
        to_state: str,
        event: str = "",
        guard: str = "",
        action: str = "",
    ) -> Any:
        """
        Create a Transition link between two states.
        UML standard transition label format: event [guard] / action
        """
        if from_state not in self.states or to_state not in self.states:
            return None

        src_obj, _ = self.states[from_state]
        tgt_obj, _ = self.states[to_state]

        trans = self.model.Transitions.CreateNew()
        trans.Object1 = src_obj
        trans.Object2 = tgt_obj

        parts = []
        if event:
            parts.append(event)
        if guard:
            parts.append(f"[{guard}]")
        if action:
            parts.append(f"/ {action}")
        label = " ".join(parts).strip()

        if label:
            try:
                if hasattr(trans, "Event"):
                    trans.Event = label
                elif hasattr(trans, "Condition"):
                    trans.Condition = label
                elif hasattr(trans, "Comment"):
                    trans.Comment = label
            except Exception:
                pass

        sym_l = attach_link_symbol(self.diagram, trans)
        self.transitions.append((trans, sym_l))
        return sym_l

    def layout_pipeline(self, min_spacing: int = 1500):
        """Align states horizontally in lifecycle progression order."""
        for idx, (_, sym) in enumerate(self.states.values()):
            try:
                if hasattr(sym, "Position"):
                    sym.Position.X = self.start_x + idx * self.step_x
                    sym.Position.Y = self.start_y
            except Exception:
                pass
