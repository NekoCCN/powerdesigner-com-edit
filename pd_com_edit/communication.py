#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UML Communication / Collaboration Diagram Builder (协作图 / 通信图构建器)
Features:
- Primary Actors & Interacting Objects (Lifelines / Runtime Instances)
- Instance Links connecting collaborating objects
- Directional Numbered Messages (e.g. 1: submit(), 1.1: validate(), 2: notify())
- Auto-Layout algorithms: Radial / Circular Star Topology and Structured Bipartite / Grid
"""

import math
from typing import Dict, Tuple, List, Optional, Any
from .collision import CollisionDetector
from .client import attach_link_symbol


from typing import Dict, Tuple, List, Optional, Any
from .collision import CollisionDetector
from .client import attach_link_symbol, ensure_dynamic


class CommunicationDiagramBuilder:
    """
    Constructs UML Communication Diagrams (协作图 / 通信图).
    Focuses on structural object topologies and numbered message sequence flows.
    """

    def __init__(
        self,
        diagram: Any,
        name: str = "",
        center_x: int = 0,
        center_y: int = 0,
        default_radius: int = 20000,
    ):
        self.diagram = ensure_dynamic(diagram)
        self.model = ensure_dynamic(self.diagram.Model)

        if name:
            try:
                self.diagram.Name = name
            except Exception:
                pass

        self.center_x = center_x
        self.center_y = center_y
        self.default_radius = default_radius

        self.actors: Dict[str, Tuple[Any, Any]] = {}
        self.objects: Dict[str, Tuple[Any, Any]] = {}
        self.links: Dict[Tuple[str, str], Tuple[Any, Any]] = {}
        self.messages: List[Dict[str, Any]] = []

    def _resolve_participant(self, name: str) -> Optional[Tuple[Any, Any]]:
        """Look up participant actor or object by name."""
        if name in self.actors:
            return self.actors[name]
        if name in self.objects:
            return self.objects[name]
        return None

    def add_actor(
        self,
        name: str,
        x: Optional[int] = None,
        y: Optional[int] = None,
    ) -> Any:
        """Register a human or external system actor participating in the collaboration."""
        act = ensure_dynamic(self.model.Actors.CreateNew())
        act.Name = name
        sym = ensure_dynamic(self.diagram.AttachObject(act))

        if x is not None and y is not None:
            try:
                if hasattr(sym, "Position"):
                    sym.Position.X = x
                    sym.Position.Y = y
            except Exception:
                pass

        self.actors[name] = (act, sym)
        return act

    def add_object(
        self,
        name: str,
        class_name: str = "",
        x: Optional[int] = None,
        y: Optional[int] = None,
        width: int = 12000,
        height: int = 5000,
    ) -> Any:
        """Create and attach an interacting Object/Instance node."""
        obj = ensure_dynamic(self.model.Objects.CreateNew())
        obj.Name = name
        if class_name and hasattr(obj, "ClassName"):
            try:
                obj.ClassName = class_name
            except Exception:
                pass

        sym = ensure_dynamic(self.diagram.AttachObject(obj))

        try:
            if x is not None and hasattr(sym, "Position"):
                sym.Position.X = x
            if y is not None and hasattr(sym, "Position"):
                sym.Position.Y = y
            if hasattr(sym, "Size"):
                if hasattr(sym.Size, "X"):
                    sym.Size.X = width
                    sym.Size.Y = height
                elif hasattr(sym.Size, "Width"):
                    sym.Size.Width = width
                    sym.Size.Height = height
        except Exception:
            pass

        self.objects[name] = (obj, sym)
        return obj

    def add_link(self, obj1_name: str, obj2_name: str, name: str = "") -> Any:
        """
        Create an InstanceLink connector between two collaborating objects.
        Attaches symbol via AttachLinkObject.
        """
        key = tuple(sorted([obj1_name, obj2_name]))
        if key in self.links:
            return self.links[key][0]

        p1 = self._resolve_participant(obj1_name)
        p2 = self._resolve_participant(obj2_name)
        if not p1 or not p2:
            return None

        link = ensure_dynamic(self.model.InstanceLinks.CreateNew())
        link.Object1 = p1[0]
        link.Object2 = p2[0]
        if name:
            link.Name = name

        sym_l = ensure_dynamic(attach_link_symbol(self.diagram, link))
        self.links[key] = (link, sym_l)
        return link

    def add_message(
        self,
        sender_name: str,
        receiver_name: str,
        label: str,
        sequence_number: str = "",
    ) -> Any:
        """
        Send a numbered interaction message along the link connecting sender and receiver.
        In PowerDesigner Communication diagrams, messages automatically render directional arrows
        and sequence numbering along the InstanceLink.
        """
        key = tuple(sorted([sender_name, receiver_name]))
        link_tuple = self.links.get(key)
        if not link_tuple:
            # Auto-create link if it does not exist yet
            link_obj = self.add_link(sender_name, receiver_name)
            link_tuple = self.links.get(key)
            if not link_tuple:
                return None

        link, _ = link_tuple
        sender_obj = self._resolve_participant(sender_name)[0]
        receiver_obj = self._resolve_participant(receiver_name)[0]

        msg = ensure_dynamic(self.model.Messages.CreateNew())
        full_label = f"{sequence_number} {label}".strip() if sequence_number else label
        msg.Name = full_label
        msg.Sender = sender_obj
        msg.Receiver = receiver_obj

        # Bind to link
        try:
            if hasattr(link, "Messages"):
                link.Messages.Add(msg)
            elif hasattr(msg, "InstanceLink"):
                msg.InstanceLink = link
        except Exception:
            pass

        self.messages.append({
            "sender": sender_name,
            "receiver": receiver_name,
            "label": full_label,
            "seq": sequence_number,
            "msg": msg
        })
        return msg

    def layout_radial(
        self,
        center_name: Optional[str] = None,
        radius: Optional[int] = None,
        start_angle_deg: float = 0.0,
    ):
        """
        Canonical Star/Radial layout for Collaboration diagrams:
        - Central Controller / Core Service placed at origin (center_x, center_y).
        - Surrounding collaborators evenly spaced on a circle perimeter to avoid link crossings.
        """
        r = radius or self.default_radius
        all_nodes = {**self.actors, **self.objects}
        if not all_nodes:
            return

        # Pick center node
        center_key = center_name
        if not center_key or center_key not in all_nodes:
            # Default to first object or actor
            center_key = list(all_nodes.keys())[0]

        center_sym = all_nodes[center_key][1]
        try:
            if hasattr(center_sym, "Position"):
                center_sym.Position.X = self.center_x
                center_sym.Position.Y = self.center_y
        except Exception:
            pass

        perim_keys = [k for k in all_nodes.keys() if k != center_key]
        n = len(perim_keys)
        if n == 0:
            return

        angle_step = 2.0 * math.pi / n
        start_rad = math.radians(start_angle_deg)

        for i, k in enumerate(perim_keys):
            angle = start_rad + i * angle_step
            pos_x = int(self.center_x + r * math.cos(angle))
            pos_y = int(self.center_y + r * math.sin(angle))
            sym = all_nodes[k][1]
            try:
                if hasattr(sym, "Position"):
                    sym.Position.X = pos_x
                    sym.Position.Y = pos_y
            except Exception:
                pass

    def layout_grid(
        self,
        cols: int = 3,
        spacing_x: int = 16000,
        spacing_y: int = 10000,
        start_x: int = -16000,
        start_y: int = 10000,
    ):
        """Arrange nodes in structured rectangular grid."""
        all_nodes = list(self.actors.values()) + list(self.objects.values())
        for idx, (_, sym) in enumerate(all_nodes):
            row = idx // cols
            col = idx % cols
            x = start_x + col * spacing_x
            y = start_y - row * spacing_y
            try:
                if hasattr(sym, "Position"):
                    sym.Position.X = x
                    sym.Position.Y = y
            except Exception:
                pass

    def audit_and_fix_overlaps(self, min_spacing: int = 1500):
        """Auto-resolve overlapping object boxes."""
        symbols = [sym for _, sym in list(self.actors.values()) + list(self.objects.values()) if sym is not None]
        if symbols:
            CollisionDetector.auto_resolve_vertical_overlaps(symbols, min_spacing=min_spacing)
