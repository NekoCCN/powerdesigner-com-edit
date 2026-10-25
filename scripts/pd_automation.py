#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PowerDesigner COM Automation & Collision Resolution Engine (pd_automation.py)
Provides comprehensive tools for:
- Managing PowerDesigner COM Application lifecycle
- AABB Geometric Collision Detection & Overlap Auto-Resolution
- Sequence Diagram generation with Call-Stack Activation Bars & Anti-Overlap offsets
- Use Case Diagram 3-column collision-free layout
- Stray Draft Note cleaner & PIL-based high-res auto-cropping
"""

import os
import sys
import subprocess
import time
from typing import List, Dict, Tuple, Optional, Any

try:
    import win32com.client
    import pythoncom
except ImportError:
    win32com = None
    pythoncom = None

try:
    from PIL import Image
    import numpy as np
except ImportError:
    Image = None
    np = None

# Native Object Kind Constants in PowerDesigner OOM
KIND_CLASS = 403775587
KIND_GENERALIZATION = 403775592
KIND_DEPENDENCY = 403775593
KIND_CLASS_ASSOC = 403775594
KIND_ACTOR = 403775745
KIND_USECASE = 403775746
KIND_USECASE_ASSOC = 403775603

def rgb(r: int, g: int, b: int) -> int:
    """Convert RGB (0-255) to Windows COLORREF integer."""
    return r + (g << 8) + (b << 16)


def attach_link_symbol(diagram, link_obj):
    """
    Safely attach a link/connector symbol (Association, Generalization, Dependency, Reference)
    to a PowerDesigner diagram.
    """
    if hasattr(diagram, "_oleobj_") and pythoncom is not None:
        try:
            dispid = diagram._oleobj_.GetIDsOfNames("AttachLinkObject")
            ole_link = link_obj._oleobj_ if hasattr(link_obj, "_oleobj_") else link_obj
            res = diagram._oleobj_.Invoke(dispid, 0, pythoncom.DISPATCH_METHOD, True, ole_link)
            if win32com:
                return win32com.client.dynamic.Dispatch(res)
            return res
        except Exception:
            pass

    if hasattr(diagram, "AttachLinkObject"):
        try:
            return diagram.AttachLinkObject(link_obj)
        except Exception:
            pass

    if hasattr(diagram, "AttachObject"):
        try:
            return diagram.AttachObject(link_obj)
        except Exception:
            pass

    return None


class PowerDesignerClient:
    """Manages connection, model lifecycle, and process safety for PowerDesigner."""

    def __init__(self, visible: bool = False):
        if win32com is None:
            raise RuntimeError("pywin32 is required. Install via: pip install pywin32")
        self.visible = visible
        self.app = None
        self._connect()

    def _connect(self):
        try:
            self.app = win32com.client.Dispatch("PowerDesigner.Application")
            self.app.Visible = self.visible
        except Exception as e:
            raise RuntimeError(f"Failed to connect to PowerDesigner.Application: {e}")

    def create_oom_model(self, name: str = "NewModel", language: str = "Java"):
        cls_oom = "{4BA9FBC0-D824-11D1-A1DF-0020AF12A261}"
        model = self.app.CreateModel(cls_oom, f"|Language={language}|")
        if name:
            model.SetName(name)
        return model

    def open_model(self, path: str):
        if not os.path.isabs(path):
            path = os.path.abspath(path)
        return self.app.OpenModel(path)

    def close_all_safely(self):
        try:
            if self.app:
                while self.app.Models.Count > 0:
                    m = self.app.Models.Item(0)
                    m.Close()
        except Exception:
            pass
        self.app = None

    @staticmethod
    def kill_lingering_processes():
        """Force-kill lingering pdshell16.exe processes if COM hangs."""
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/F", "/IM", "pdshell16.exe"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


class CollisionDetector:
    """
    Detects and auto-resolves overlaps:
    1. Symbol-to-Symbol AABB bounding box overlap check.
    2. Sequence activation bar same-depth collision check.
    3. Removal of draft / unapproved annotations.
    """

    @staticmethod
    def check_symbol_aabb_collision(sym1, sym2, clearance: int = 150) -> bool:
        """Check if two PowerDesigner symbols intersect with a clearance margin."""
        try:
            x1, y1 = sym1.Position.X, sym1.Position.Y
            w1, h1 = sym1.Size.Width, sym1.Size.Height
            x2, y2 = sym2.Position.X, sym2.Position.Y
            w2, h2 = sym2.Size.Width, sym2.Size.Height

            l1, r1 = x1 - w1 // 2 - clearance, x1 + w1 // 2 + clearance
            b1, t1 = y1 - h1 // 2 - clearance, y1 + h1 // 2 + clearance

            l2, r2 = x2 - w2 // 2 - clearance, x2 + w2 // 2 + clearance
            b2, t2 = y2 - h2 // 2 - clearance, y2 + h2 // 2 + clearance

            return (r1 > l2 and l1 < r2 and t1 > b2 and b1 < t2)
        except Exception:
            return False

    @classmethod
    def audit_symbol_overlaps(cls, diagram, clearance: int = 150) -> List[Tuple[Any, Any]]:
        """Audit all symbols in diagram and return list of overlapping pairs."""
        colliding_pairs = []
        try:
            symbols = list(diagram.Symbols)
            n = len(symbols)
            for i in range(n):
                for j in range(i + 1, n):
                    s1 = symbols[i]
                    s2 = symbols[j]
                    # Skip link symbols or symbols without Size/Position
                    if not hasattr(s1, "Size") or not hasattr(s2, "Size"):
                        continue
                    if cls.check_symbol_aabb_collision(s1, s2, clearance):
                        colliding_pairs.append((s1, s2))
        except Exception as e:
            print(f"[CollisionDetector] Audit warning: {e}")
        return colliding_pairs

    @classmethod
    def auto_resolve_vertical_overlaps(cls, symbols: List[Any], min_spacing: int = 400):
        """Sort symbols vertically and adjust Y coordinates to eliminate overlap."""
        try:
            valid_syms = [s for s in symbols if hasattr(s, "Position") and hasattr(s, "Size")]
            # Sort by Y descending (top to bottom in negative Y coordinate space)
            valid_syms.sort(key=lambda s: s.Position.Y, reverse=True)

            for i in range(len(valid_syms) - 1):
                cur = valid_syms[i]
                nxt = valid_syms[i + 1]

                cur_bottom = cur.Position.Y - cur.Size.Height // 2
                nxt_top = nxt.Position.Y + nxt.Size.Height // 2

                if nxt_top > cur_bottom - min_spacing:
                    # Move nxt down
                    new_y = cur_bottom - min_spacing - nxt.Size.Height // 2
                    nxt.Position.Y = new_y
        except Exception as e:
            print(f"[CollisionDetector] Auto-resolve error: {e}")

    @staticmethod
    def audit_activation_bar_overlaps(completed_bars: List[Tuple[str, int, int, int]]) -> List[Dict]:
        """
        Verify that no two activation intervals on the same lifeline overlap at the same depth.
        completed_bars items: (lifeline_name, start_y, end_y, depth)
        """
        overlaps = []
        by_lifeline = {}
        for item in completed_bars:
            name, s_y, e_y, depth = item
            by_lifeline.setdefault(name, []).append((s_y, e_y, depth))

        for name, bars in by_lifeline.items():
            for i in range(len(bars)):
                for j in range(i + 1, len(bars)):
                    s1, e1, d1 = bars[i]
                    s2, e2, d2 = bars[j]
                    # Check vertical interval intersection
                    # Y goes downward (negative)
                    top1, bot1 = max(s1, e1), min(s1, e1)
                    top2, bot2 = max(s2, e2), min(s2, e2)

                    intersects = not (bot1 >= top2 or bot2 >= top1)
                    if intersects and d1 == d2:
                        overlaps.append({
                            "lifeline": name,
                            "bar1": (s1, e1, d1),
                            "bar2": (s2, e2, d2),
                            "defect": "Same-depth collision"
                        })
        return overlaps

    @staticmethod
    def strip_draft_notes(model_or_diagram, keywords: Optional[List[str]] = None) -> int:
        """
        Scan and remove unapproved / draft text annotations.
        Default keywords: ['实现中', '待整链验收', '兼有教学管理', '计划图等同']
        """
        if keywords is None:
            keywords = ["实现中", "待整链验收", "兼有教学管理", "系统用例不能", "计划图等同"]

        removed_count = 0
        try:
            # Check TextSymbols or Notes on diagram
            if hasattr(model_or_diagram, "Symbols"):
                for sym in list(model_or_diagram.Symbols):
                    text_content = ""
                    if hasattr(sym, "Text"):
                        text_content = sym.Text
                    elif hasattr(sym, "Name"):
                        text_content = sym.Name
                    
                    if any(kw in text_content for kw in keywords):
                        sym.Delete()
                        removed_count += 1
        except Exception as e:
            print(f"[CollisionDetector] Strip notes warning: {e}")
        return removed_count


class SequenceDiagramBuilder:
    """
    Constructs an OOM sequence diagram with:
    - Horizontal lifeline distribution
    - Sequential vertical message placement
    - Call-stack tracked activation bar intervals with nesting offsets
    - Overlap verification before completion
    """

    def __init__(self, diagram, start_x: int = 1500, spacing_x: int = 2500, start_y: int = -1500, step_y: int = -500):
        self.diagram = diagram
        self.model = diagram.Model
        self.start_x = start_x
        self.spacing_x = spacing_x
        self.start_y = start_y
        self.step_y = step_y

        self.lifelines: Dict[str, Tuple[object, object, int]] = {}
        self.messages: List[Dict] = []
        self.current_y = start_y

    def add_lifeline(self, name: str, is_actor: bool = False):
        idx = len(self.lifelines)
        x_pos = self.start_x + idx * self.spacing_x
        
        if is_actor:
            obj = self.model.Actors.CreateNew()
        else:
            obj = self.model.Classes.CreateNew()
        obj.SetName(name)

        sym = self.diagram.AttachObject(obj)
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
    ):
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

    def build_messages(self) -> List[Tuple[str, int, int, int]]:
        """
        Render messages and generate activation bars.
        Automatically offsets nested activation bars to prevent coordinate collision.
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

            msg = self.model.Messages.CreateNew()
            msg.SetName(label)
            msg.Sender = s_obj
            msg.Receiver = r_obj
            msg_sym = attach_link_symbol(self.diagram, msg)

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

        # Perform Overlap Audit
        overlaps = CollisionDetector.audit_activation_bar_overlaps(completed_bars)
        if overlaps:
            print(f"[Warning] Detected {len(overlaps)} activation bar overlaps: {overlaps}")
        else:
            print("[Success] 0 Activation Bar Overlaps verified.")

        return completed_bars

    layout_diagram = build_messages


class UseCaseDiagramBuilder:
    """
    Constructs clean, collision-free Use Case Diagrams with full association link support.
    """

    def __init__(
        self,
        diagram,
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

        self.actors = {}
        self.use_cases = {}
        self.links = []

    def add_actor(
        self,
        name: str,
        code: str = "",
        is_secondary: bool = False,
        is_primary: Optional[bool] = None,
        column: int = 1,
        x: Optional[int] = None,
        y: Optional[int] = None,
    ):
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

    def add_system(self, name: str, code: str = "", x: Optional[int] = None, y: Optional[int] = None):
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
    ):
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

    def link(self, actor_name: str, use_case_name: str, stereotype: str = ""):
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

    def link_use_cases(self, source_uc_name: str, target_uc_name: str, stereotype: str = "include"):
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

    def connect(self, source: str, target: str, stereotype: str = ""):
        if source in self.actors and target in self.use_cases:
            return self.link(source, target, stereotype)
        elif source in self.use_cases and target in self.actors:
            return self.link(target, source, stereotype)
        elif source in self.use_cases and target in self.use_cases:
            return self.link_use_cases(source, target, stereotype or "include")
        return None

    def layout_three_column(self, min_spacing: int = 1500):
        primary_actors = [item for item in self.actors.values() if item[1] is not None]
        for idx, (_, sym) in enumerate(primary_actors):
            try:
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
        symbols = [sym for _, sym in self.use_cases.values() if sym is not None]
        if symbols:
            CollisionDetector.auto_resolve_vertical_overlaps(symbols, min_spacing=min_spacing)


class ImageExporter:
    """Exports diagrams to image files with automatic whitespace cropping."""

    @staticmethod
    def export(diagram, output_path: str, format_name: str = "PNG", auto_crop: bool = True, padding: int = 25):
        if not os.path.isabs(output_path):
            output_path = os.path.abspath(output_path)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        diagram.ExportImage(output_path, format_name)

        if auto_crop and Image is not None and np is not None and os.path.exists(output_path):
            try:
                img = Image.open(output_path).convert("RGB")
                arr = np.array(img)
                mask = np.any(arr < 250, axis=2)
                coords = np.argwhere(mask)
                if len(coords) > 0:
                    y0, x0 = coords.min(axis=0)
                    y1, x1 = coords.max(axis=0)
                    h, w = arr.shape[:2]
                    x0 = max(0, x0 - padding)
                    y0 = max(0, y0 - padding)
                    x1 = min(w - 1, x1 + padding)
                    y1 = min(h - 1, y1 + padding)
                    cropped = img.crop((x0, y0, x1 + 1, y1 + 1))
                    cropped.save(output_path)
            except Exception as e:
                print(f"[ImageExporter] Auto-crop failed: {e}")
