#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UML Sequence Diagram Builder with Call-Stack Activation Bar Automation
"""

from typing import List, Dict, Tuple, Optional, Any
from .collision import CollisionDetector
from .client import attach_link_symbol, ensure_dynamic

class SequenceDiagramBuilder:
    """
    Constructs an OOM sequence diagram with:
    - Horizontal lifeline distribution
    - Sequential vertical message placement
    - Call-stack tracked activation bar intervals with nesting offsets
    - Combined fragments (alt, opt, loop) framing
    - Overlap verification before completion
    """

    def __init__(self, diagram: Any, start_x: int = 1500, spacing_x: int = 2500, start_y: int = -1500, step_y: int = -500):
        self.diagram = ensure_dynamic(diagram)
        self.model = ensure_dynamic(self.diagram.Model)
        self.start_x = start_x
        self.spacing_x = spacing_x
        self.start_y = start_y
        self.step_y = step_y

        self.lifelines: Dict[str, Tuple[object, object, int]] = {}  # name -> (obj, sym, x)
        self.messages: List[Dict[str, Any]] = []
        self.current_y = start_y
        self.fragments: List[Dict[str, Any]] = []

    def add_lifeline(self, name: str, is_actor: bool = False) -> Tuple[object, object]:
        """Add an Actor or Class lifeline."""
        idx = len(self.lifelines)
        x_pos = self.start_x + idx * self.spacing_x
        
        if is_actor:
            obj = ensure_dynamic(self.model.Actors.CreateNew())
        else:
            obj = ensure_dynamic(self.model.Classes.CreateNew())
        try:
            obj.SetName(name)
        except Exception:
            obj.Name = name

        sym = ensure_dynamic(self.diagram.AttachObject(obj))
        try:
            sym.Position.X = x_pos
            sym.Position.Y = self.start_y + 800
        except Exception:
            pass

        self.lifelines[name] = (obj, sym, x_pos)
        return obj, sym

    def add_message(
        self,
        sender_name: str,
        receiver_name: str,
        label: str,
        is_return: bool = False,
        message_type: str = "sync",
    ) -> int:
        """Add a synchronous, asynchronous, or reply message along the timeline."""
        if sender_name not in self.lifelines or receiver_name not in self.lifelines:
            raise ValueError(f"Unknown sender '{sender_name}' or receiver '{receiver_name}'")

        eff_return = is_return or (message_type.lower() in ("reply", "return"))

        y = self.current_y
        self.messages.append({
            "sender": sender_name,
            "receiver": receiver_name,
            "label": label,
            "is_return": eff_return,
            "y": y
        })
        self.current_y += self.step_y
        return y

    def add_combined_fragment(self, operator: str, participants: List[str], start_msg_idx: int, end_msg_idx: int, guard: str = ""):
        """Define an alt/opt/loop combined fragment over a range of messages."""
        self.fragments.append({
            "operator": operator,
            "participants": participants,
            "start_msg_idx": start_msg_idx,
            "end_msg_idx": end_msg_idx,
            "guard": guard
        })

    def build_messages(self) -> List[Tuple[str, int, int, int]]:
        """
        Render all messages, compute activation bars with nesting offsets, and build fragments.
        Returns list of completed activation bars: (lifeline_name, start_y, end_y, depth)
        """
        active_stacks: Dict[str, List[int]] = {name: [] for name in self.lifelines}
        completed_bars: List[Tuple[str, int, int, int]] = []

        for msg_info in self.messages:
            s_name = msg_info["sender"]
            r_name = msg_info["receiver"]
            y = msg_info["y"]
            label = msg_info["label"]
            is_ret = msg_info["is_return"]

            s_obj, s_sym, _ = self.lifelines[s_name]
            r_obj, r_sym, _ = self.lifelines[r_name]

            msg = ensure_dynamic(self.model.Messages.CreateNew())
            try:
                msg.SetName(label)
            except Exception:
                msg.Name = label
            msg.Sender = s_obj
            msg.Receiver = r_obj
            msg_sym = ensure_dynamic(attach_link_symbol(self.diagram, msg))

            try:
                if hasattr(msg_sym, "SourcePoint"):
                    msg_sym.SourcePoint.Y = y
                if hasattr(msg_sym, "DestinationPoint"):
                    msg_sym.DestinationPoint.Y = y
            except Exception:
                pass

            if not is_ret:
                depth = len(active_stacks[r_name])
                active_stacks[r_name].append(y)
            else:
                if active_stacks[s_name]:
                    start_y = active_stacks[s_name].pop()
                    depth = len(active_stacks[s_name])
                    completed_bars.append((s_name, start_y, y, depth))

        for name, stack in active_stacks.items():
            while stack:
                start_y = stack.pop()
                depth = len(stack)
                completed_bars.append((name, start_y, self.current_y, depth))

        # Build Combined Fragments
        for frag in self.fragments:
            self._render_fragment(frag)

        # Audit Activation Bar Overlaps
        overlaps = CollisionDetector.audit_activation_bar_overlaps(completed_bars)
        if overlaps:
            print(f"[SequenceDiagramBuilder] Warning: Detected {len(overlaps)} activation bar overlaps.")
        else:
            print("[SequenceDiagramBuilder] Verification passed: 0 Activation Bar Overlaps.")

        return completed_bars

    layout_diagram = build_messages

    def _render_fragment(self, frag: Dict[str, Any]):
        """Render a CombinedFragment symbol bounding the participants and message range."""
        try:
            pts = frag["participants"]
            xs = [self.lifelines[p][2] for p in pts if p in self.lifelines]
            if not xs:
                return

            x_left = min(xs) - 400
            x_right = max(xs) + 400

            s_idx = max(0, min(frag["start_msg_idx"], len(self.messages) - 1))
            e_idx = max(0, min(frag["end_msg_idx"], len(self.messages) - 1))

            y_top = self.messages[s_idx]["y"] + 300
            y_bottom = self.messages[e_idx]["y"] - 300

            cf = self.model.CombinedFragments.CreateNew()
            cf.SetName(frag["operator"])
            if hasattr(cf, "InteractionOperator"):
                cf.InteractionOperator = frag["operator"]

            sym = self.diagram.AttachObject(cf)
            if hasattr(sym, "Position") and hasattr(sym, "Size"):
                sym.Position.X = (x_left + x_right) // 2
                sym.Position.Y = (y_top + y_bottom) // 2
                sym.Size.Width = abs(x_right - x_left)
                sym.Size.Height = abs(y_top - y_bottom)
        except Exception as e:
            print(f"[SequenceDiagramBuilder] Fragment render note: {e}")
