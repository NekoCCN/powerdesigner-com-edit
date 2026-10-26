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
        default_radius: int = 25000,
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
        width: int = 13000,
        height: int = 4200,
    ) -> Any:
        """
        Create and attach an interacting Object/Instance node conforming to UML 2.5 Lifeline standards.
        Supports:
        - Anonymous instance (Textbook Standard, no duplicate words): name="" or name=":ClassName" -> renders ':ClassName'
        - Named instance: name="ctrl", class_name="OrderController" -> renders 'ctrl : OrderController'
        """
        obj = ensure_dynamic(self.model.Objects.CreateNew())
        
        display_key = name
        if name.startswith(":") and not class_name:
            class_name = name[1:].strip()
            name = ""

        # Standard UML 2.5 Lifeline Classifier Association
        if class_name:
            try:
                cls_obj = None
                if hasattr(self.model, "Classes"):
                    for c in self.model.Classes:
                        if c.Name == class_name:
                            cls_obj = c
                            break
                    if not cls_obj:
                        cls_obj = ensure_dynamic(self.model.Classes.CreateNew())
                        cls_obj.Name = class_name
                if hasattr(obj, "Class") and cls_obj:
                    obj.Class = cls_obj
            except Exception:
                pass

            if hasattr(obj, "ClassName"):
                try:
                    obj.ClassName = class_name
                except Exception:
                    pass

        # If anonymous instance, empty name renders ':ClassName' (avoids repeated name:Class text)
        try:
            obj.Name = name
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

        reg_name = display_key or name or (f":{class_name}" if class_name else "Object")
        self.objects[reg_name] = (obj, sym)
        if class_name and reg_name != class_name:
            self.objects[class_name] = (obj, sym)
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
        try:
            sym_l.CornerStyle = 0
        except Exception:
            pass
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
        p1 = self._resolve_participant(sender_name)
        p2 = self._resolve_participant(receiver_name)
        if not p1 or not p2:
            return None
        sender_obj = p1[0]
        receiver_obj = p2[0]

        msg = ensure_dynamic(self.model.Messages.CreateNew())
        clean_seq = sequence_number.strip().rstrip(":")
        clean_label = label.strip()

        # In PowerDesigner OOM, setting SequenceNumber natively prefixes the colon and arrow
        if clean_seq and hasattr(msg, "SequenceNumber"):
            try:
                msg.SequenceNumber = clean_seq
                msg.Name = clean_label
            except Exception:
                msg.Name = f"{clean_seq}: {clean_label}"
        else:
            msg.Name = clean_label

        msg.Sender = sender_obj
        msg.Receiver = receiver_obj

        key = tuple(sorted([sender_name, receiver_name]))
        link_tuple = self.links.get(key)
        if not link_tuple:
            # Create link and insert message BEFORE attaching symbol so diagram engine
            # binds the message symbol directly to the link symbol without displacement
            link = ensure_dynamic(self.model.InstanceLinks.CreateNew())
            link.Object1 = sender_obj
            link.Object2 = receiver_obj
            try:
                link.Messages.Insert(-1, msg)
            except Exception:
                pass
            sym_l = ensure_dynamic(attach_link_symbol(self.diagram, link))
            try:
                sym_l.CornerStyle = 0
            except Exception:
                pass
            self.links[key] = (link, sym_l)
        else:
            link, _ = link_tuple
            try:
                link.Messages.Insert(-1, msg)
            except Exception:
                try:
                    link.Messages.Add(msg)
                except Exception:
                    pass

        self.messages.append({
            "sender": sender_name,
            "receiver": receiver_name,
            "label": clean_label,
            "seq": clean_seq,
            "msg": msg
        })
        return msg

    def straighten_links(
        self,
        base_offset: int = 2200,
        step_offset: int = 2000,
        arrow_len: int = 3500,
    ):
        """
        Enforce clean, direct straight lines for all instance links and automatically
        offset message arrows/labels perpendicular to each link so that fonts NEVER
        touch, cross, or cover the link line.
        """
        diag_symbols = []
        try:
            if hasattr(self.diagram, "Symbols"):
                for i in range(self.diagram.Symbols.Count):
                    diag_symbols.append(ensure_dynamic(self.diagram.Symbols.Item(i)))
        except Exception:
            pass

        all_parts = list(self.actors.values()) + list(self.objects.values())

        for (k1, k2), (link, sym_l) in self.links.items():
            if not sym_l or not hasattr(sym_l, "ListOfPoints"):
                continue

            # Look up participant symbols directly from link.Object1 and link.Object2
            sym1 = None
            sym2 = None
            obj1 = getattr(link, "Object1", None)
            obj2 = getattr(link, "Object2", None)
            if not obj1 or not obj2:
                continue

            oid1 = getattr(obj1, "ObjectID", None)
            oid2 = getattr(obj2, "ObjectID", None)

            for part_obj, part_sym in all_parts:
                part_oid = getattr(part_obj, "ObjectID", None)
                if part_oid == oid1 and not sym1:
                    sym1 = part_sym
                elif part_oid == oid2 and not sym2:
                    sym2 = part_sym

            if not sym1 or not sym2:
                continue

            if hasattr(sym1, "Position") and hasattr(sym2, "Position"):
                x1, y1 = sym1.Position.X, sym1.Position.Y
                x2, y2 = sym2.Position.X, sym2.Position.Y
                try:
                    sym_l.CornerStyle = 0
                except Exception:
                    pass
                try:
                    sym_l.ListOfPoints.AsText = f"(({x1},{y1}),({x2},{y2}))"
                except Exception:
                    pass

                # Offset all message symbols associated with this link
                link_msgs = [
                    m for m in self.messages
                    if (m["sender"] in (k1, k2)) and (m["receiver"] in (k1, k2))
                ]
                if not link_msgs:
                    continue

                dx = x2 - x1
                dy = y2 - y1
                L = math.sqrt(dx * dx + dy * dy)
                if L <= 0:
                    continue

                ux = dx / L
                uy = dy / L
                nx = -uy
                ny = ux
                if ny < -0.01 or (abs(ny) <= 0.01 and nx < -0.01):
                    nx = -nx
                    ny = -ny

                for m_idx, m_info in enumerate(link_msgs):
                    label = m_info["label"]
                    msg_obj = m_info["msg"]
                    # Find matching Communication Message Symbol
                    msg_sym = None
                    for s in diag_symbols:
                        cname = getattr(s, "ClassName", "")
                        if "Message" in cname or "Communication Message" in cname:
                            s_obj = getattr(s, "Object", None)
                            if (s_obj and getattr(s_obj, "ObjectID", None) == getattr(msg_obj, "ObjectID", None)) or s.Name == label:
                                msg_sym = s
                                break

                    if not msg_sym or not hasattr(msg_sym, "ListOfPoints"):
                        continue

                    # Direction relative to link.Object1 -> link.Object2
                    snd = getattr(msg_obj, "Sender", None)
                    is_forward = (getattr(snd, "ObjectID", None) == oid1)
                    dir_sign = 1.0 if is_forward else -1.0
                    
                    # Position arrow towards receiver (68%) to guarantee text clearance from sender box
                    t_pos = 0.68 if is_forward else 0.32
                    mx = x1 + t_pos * dx
                    my = y1 + t_pos * dy

                    offset_d = base_offset + m_idx * step_offset

                    ax1 = int(mx - dir_sign * (arrow_len / 2.0) * ux + offset_d * nx)
                    ay1 = int(my - dir_sign * (arrow_len / 2.0) * uy + offset_d * ny)
                    ax2 = int(mx + dir_sign * (arrow_len / 2.0) * ux + offset_d * nx)
                    ay2 = int(my + dir_sign * (arrow_len / 2.0) * uy + offset_d * ny)

                    try:
                        msg_sym.ListOfPoints.AsText = f"(({ax1},{ay1}),({ax2},{ay2}))"
                    except Exception:
                        pass

    def layout_tiered(
        self,
        tiers: List[List[Any]],
        start_x: int = -42000,
        spacing_x: int = 28000,
        spacing_y: int = 16000,
    ):
        """
        Arrange interacting nodes in multi-tier architecture columns:
        Tier 0: Actors (e.g. ['Guest'])
        Tier 1: Boundary / Controller (e.g. [':OrderController'])
        Tier 2: Domain Services (e.g. [':RoomInventoryService', ':PaymentGateway', ':NotificationService'])
        Tier 3: Repositories / External Gateways (e.g. [(':RoomRepository', 16000), (':BankService', 0)])
        
        Supports tuple items `(name, custom_y)` to align dependencies with their caller's Y row.
        """
        for t_idx, tier_nodes in enumerate(tiers):
            col_x = start_x + t_idx * spacing_x
            n = len(tier_nodes)
            total_h = (n - 1) * spacing_y
            start_y = total_h / 2.0
            for r_idx, item in enumerate(tier_nodes):
                if isinstance(item, tuple):
                    name, custom_y = item
                    row_y = custom_y
                else:
                    name = item
                    row_y = int(start_y - r_idx * spacing_y)

                part = self._resolve_participant(name)
                if not part or not part[1]:
                    continue
                sym = part[1]
                try:
                    if hasattr(sym, "Position"):
                        sym.Position.X = col_x
                        sym.Position.Y = row_y
                except Exception:
                    pass
        self.straighten_links()

    def layout_pipeline(
        self,
        sequence: List[str],
        start_x: int = -30000,
        spacing_x: int = 24000,
        y: int = 0,
    ):
        """
        Arrange interacting nodes in a left-to-right architectural pipeline (Tiered Flow).
        Standard for linear usecase realizations (Actor -> Controller -> Services -> DB).
        """
        for idx, name in enumerate(sequence):
            part = self._resolve_participant(name)
            if not part or not part[1]:
                continue
            sym = part[1]
            try:
                if hasattr(sym, "Position"):
                    sym.Position.X = start_x + idx * spacing_x
                    sym.Position.Y = y
            except Exception:
                pass
        self.straighten_links()

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
        - Automatically straightens all instance link lines and snaps directional message arrows.
        """
        r = radius or self.default_radius
        all_nodes = {**self.actors, **self.objects}
        if not all_nodes:
            return

        # Pick center node
        center_key = center_name
        if not center_key or center_key not in all_nodes:
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

        # Straighten links and offset message labels away from lines
        self.straighten_links()

    def layout_grid(
        self,
        cols: int = 3,
        spacing_x: int = 18000,
        spacing_y: int = 12000,
        start_x: int = -18000,
        start_y: int = 12000,
    ):
        """Arrange nodes in structured rectangular grid and straighten connecting links."""
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

        self.straighten_links()

    def audit_and_fix_overlaps(self, min_spacing: int = 1500):
        """Auto-resolve overlapping object boxes."""
        symbols = [sym for _, sym in list(self.actors.values()) + list(self.objects.values()) if sym is not None]
        if symbols:
            CollisionDetector.auto_resolve_vertical_overlaps(symbols, min_spacing=min_spacing)
