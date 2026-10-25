#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AABB Collision Detection, Layout Auditing & Draft Cleanup Engine
"""

from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field


@dataclass
class BoundingBox:
    """Axis-Aligned Bounding Box (AABB) in PowerDesigner coordinates."""
    left: int
    bottom: int
    right: int
    top: int

    @property
    def width(self) -> int:
        return abs(self.right - self.left)

    @property
    def height(self) -> int:
        return abs(self.top - self.bottom)

    @property
    def center_x(self) -> int:
        return (self.left + self.right) // 2

    @property
    def center_y(self) -> int:
        return (self.bottom + self.top) // 2


@dataclass
class CollisionRecord:
    """Information regarding a detected collision or layout violation."""
    collision_type: str  # 'symbol_overlap' or 'activation_overlap'
    symbol1_name: str
    symbol2_name: str
    overlap_x: int = 0
    overlap_y: int = 0
    details: str = ""


@dataclass
class AuditReport:
    """Consolidated layout audit report for a model or diagram."""
    model_name: str
    total_diagrams: int = 0
    total_symbols: int = 0
    total_collisions: int = 0
    collisions_by_diagram: Dict[str, List[CollisionRecord]] = field(default_factory=dict)
    stray_draft_notes: int = 0
    warnings: List[str] = field(default_factory=list)
    status: str = "PASS"

    def get_summary(self) -> str:
        res = [
            f"=== Layout Audit Report for [{self.model_name}] ===",
            f"Status: {self.status}",
            f"Diagrams Scanned: {self.total_diagrams}",
            f"Total Symbols: {self.total_symbols}",
            f"Collisions Detected: {self.total_collisions}",
            f"Stray Draft Notes: {self.stray_draft_notes}"
        ]
        if self.warnings:
            res.append("Warnings / Violations:")
            for w in self.warnings:
                res.append(f"  * {w}")
        return "\n".join(res)


class CollisionDetector:
    """
    Detects and auto-resolves layout conflicts:
    1. Symbol-to-Symbol AABB bounding box collision checking.
    2. Sequence activation bar same-depth collision checking.
    3. Detection and removal of unapproved draft notes.
    """

    def __init__(self, clearance: int = 150):
        self.clearance = clearance

    @staticmethod
    def parse_rect(rect_str: str) -> Optional[BoundingBox]:
        """
        Parses PowerDesigner symbol Rect string formatted as 'left top right bottom'
        or 'left bottom right top'.
        """
        try:
            parts = [int(p) for p in rect_str.strip().split()]
            if len(parts) == 4:
                # PowerDesigner typically uses: left, top, right, bottom (where top > bottom in PD coord system)
                p0, p1, p2, p3 = parts
                left = min(p0, p2)
                right = max(p0, p2)
                bottom = min(p1, p3)
                top = max(p1, p3)
                return BoundingBox(left=left, bottom=bottom, right=right, top=top)
        except Exception:
            pass
        return None

    def get_symbol_bbox(self, sym: Any) -> Optional[BoundingBox]:
        """Extracts BoundingBox from either Rect string or Position/Size properties."""
        if hasattr(sym, "Rect") and isinstance(sym.Rect, str):
            bbox = self.parse_rect(sym.Rect)
            if bbox:
                return bbox
        if hasattr(sym, "Position") and hasattr(sym, "Size"):
            try:
                x, y = sym.Position.X, sym.Position.Y
                w, h = sym.Size.Width, sym.Size.Height
                return BoundingBox(
                    left=x - w // 2,
                    right=x + w // 2,
                    bottom=y - h // 2,
                    top=y + h // 2
                )
            except Exception:
                pass
        return None

    def check_overlap(self, box1: BoundingBox, box2: BoundingBox, clearance: Optional[int] = None) -> bool:
        """
        Determines if two bounding boxes intersect or violate the clearance margin.
        A collision occurs when both horizontal and vertical distances are less than clearance.
        """
        c = self.clearance if clearance is None else clearance

        # Horizontal distance
        if box1.right < box2.left:
            dist_x = box2.left - box1.right
        elif box2.right < box1.left:
            dist_x = box1.left - box2.right
        else:
            dist_x = 0

        # Vertical distance
        if box1.top < box2.bottom:
            dist_y = box2.bottom - box1.top
        elif box2.top < box1.bottom:
            dist_y = box1.bottom - box2.top
        else:
            dist_y = 0

        return dist_x < c and dist_y < c

    def check_diagram_collisions(self, diagram: Any) -> List[CollisionRecord]:
        """Audits all symbols in a diagram for spatial AABB overlaps."""
        collisions = []
        try:
            symbols = list(getattr(diagram, "Symbols", []))
            n = len(symbols)
            for i in range(n):
                s1 = symbols[i]
                b1 = self.get_symbol_bbox(s1)
                if not b1:
                    continue
                name1 = getattr(s1, "Name", None) or getattr(s1, "ClassName", f"Symbol_{i}")

                for j in range(i + 1, n):
                    s2 = symbols[j]
                    b2 = self.get_symbol_bbox(s2)
                    if not b2:
                        continue
                    name2 = getattr(s2, "Name", None) or getattr(s2, "ClassName", f"Symbol_{j}")

                    if self.check_overlap(b1, b2):
                        ox = min(b1.right, b2.right) - max(b1.left, b2.left)
                        oy = min(b1.top, b2.top) - max(b1.bottom, b2.bottom)
                        collisions.append(CollisionRecord(
                            collision_type="symbol_overlap",
                            symbol1_name=name1,
                            symbol2_name=name2,
                            overlap_x=max(0, ox),
                            overlap_y=max(0, oy),
                            details=f"AABB overlap between {name1} and {name2}"
                        ))
        except Exception as e:
            print(f"[CollisionDetector] Diagram check warning: {e}")
        return collisions

    def check_activation_collisions(self, activation_list: List[Any]) -> List[CollisionRecord]:
        """
        Verify that no two activation intervals on the same lifeline overlap at the same depth.
        Accepts dicts (keys: 'lifeline', 'start_y', 'end_y', 'depth')
        or tuples: (lifeline, start_y, end_y, depth).
        """
        records = []
        by_lifeline: Dict[str, List[Tuple[int, int, int]]] = {}

        for item in activation_list:
            if isinstance(item, dict):
                name = item["lifeline"]
                s_y = item["start_y"]
                e_y = item["end_y"]
                depth = item.get("depth", 0)
            elif isinstance(item, (tuple, list)) and len(item) >= 4:
                name, s_y, e_y, depth = item[0], item[1], item[2], item[3]
            else:
                continue
            by_lifeline.setdefault(name, []).append((s_y, e_y, depth))

        for name, bars in by_lifeline.items():
            n = len(bars)
            for i in range(n):
                for j in range(i + 1, n):
                    s1, e1, d1 = bars[i]
                    s2, e2, d2 = bars[j]
                    top1, bot1 = max(s1, e1), min(s1, e1)
                    top2, bot2 = max(s2, e2), min(s2, e2)

                    intersects = not (bot1 >= top2 or bot2 >= top1)
                    if intersects and d1 == d2:
                        records.append(CollisionRecord(
                            collision_type="activation_overlap",
                            symbol1_name=f"{name}_act_tier{d1}",
                            symbol2_name=f"{name}_act_tier{d2}",
                            overlap_y=min(top1, top2) - max(bot1, bot2),
                            details=f"Same-depth activation overlap on lifeline '{name}' at depth {d1}"
                        ))
        return records

    @staticmethod
    def check_symbol_aabb_collision(sym1: Any, sym2: Any, clearance: int = 150) -> bool:
        """Check if two PowerDesigner symbols intersect with a clearance margin."""
        detector = CollisionDetector(clearance=clearance)
        b1 = detector.get_symbol_bbox(sym1)
        b2 = detector.get_symbol_bbox(sym2)
        if b1 and b2:
            return detector.check_overlap(b1, b2, clearance=clearance)
        return False

    @classmethod
    def audit_symbol_overlaps(cls, diagram: Any, clearance: int = 150) -> List[Tuple[Any, Any]]:
        """Audit all symbols in diagram and return list of overlapping pairs."""
        detector = cls(clearance=clearance)
        colliding_pairs = []
        try:
            symbols = list(getattr(diagram, "Symbols", []))
            n = len(symbols)
            for i in range(n):
                for j in range(i + 1, n):
                    s1, s2 = symbols[i], symbols[j]
                    b1 = detector.get_symbol_bbox(s1)
                    b2 = detector.get_symbol_bbox(s2)
                    if b1 and b2 and detector.check_overlap(b1, b2):
                        colliding_pairs.append((s1, s2))
        except Exception as e:
            print(f"[CollisionDetector] Audit warning: {e}")
        return colliding_pairs

    @classmethod
    def auto_resolve_vertical_overlaps(cls, symbols: List[Any], min_spacing: int = 400):
        """Sort symbols vertically and adjust Y coordinates to eliminate overlap."""
        try:
            valid_syms = [s for s in symbols if hasattr(s, "Position") and hasattr(s, "Size")]
            valid_syms.sort(key=lambda s: s.Position.Y, reverse=True)

            for i in range(len(valid_syms) - 1):
                cur = valid_syms[i]
                nxt = valid_syms[i + 1]

                cur_bottom = cur.Position.Y - cur.Size.Height // 2
                nxt_top = nxt.Position.Y + nxt.Size.Height // 2

                if nxt_top > cur_bottom - min_spacing:
                    new_y = cur_bottom - min_spacing - nxt.Size.Height // 2
                    nxt.Position.Y = new_y
        except Exception as e:
            print(f"[CollisionDetector] Vertical auto-resolve error: {e}")

    @classmethod
    def auto_resolve_horizontal_overlaps(cls, symbols: List[Any], min_spacing: int = 400):
        """Sort symbols horizontally and adjust X coordinates to eliminate overlap."""
        try:
            valid_syms = [s for s in symbols if hasattr(s, "Position") and hasattr(s, "Size")]
            valid_syms.sort(key=lambda s: s.Position.X)

            for i in range(len(valid_syms) - 1):
                cur = valid_syms[i]
                nxt = valid_syms[i + 1]

                cur_right = cur.Position.X + cur.Size.Width // 2
                nxt_left = nxt.Position.X - nxt.Size.Width // 2

                if nxt_left < cur_right + min_spacing:
                    new_x = cur_right + min_spacing + nxt.Size.Width // 2
                    nxt.Position.X = new_x
        except Exception as e:
            print(f"[CollisionDetector] Horizontal auto-resolve error: {e}")

    @staticmethod
    def audit_activation_bar_overlaps(completed_bars: List[Tuple[str, int, int, int]]) -> List[Dict]:
        """Legacy helper for backward compatibility."""
        detector = CollisionDetector()
        records = detector.check_activation_collisions(completed_bars)
        return [
            {
                "lifeline": r.symbol1_name,
                "defect": r.details,
                "overlap_y": r.overlap_y
            }
            for r in records
        ]

    @staticmethod
    def strip_draft_notes(model_or_diagram: Any, keywords: Optional[List[str]] = None) -> int:
        """
        Scan and remove unapproved / draft text annotations.
        Default keywords: ['实现中', '待整链验收', '兼有教学管理', '系统用例不能', '计划图等同']
        """
        if keywords is None:
            keywords = ["实现中", "待整链验收", "兼有教学管理", "系统用例不能", "计划图等同"]

        removed_count = 0
        try:
            symbols = []
            if hasattr(model_or_diagram, "Symbols"):
                symbols = list(model_or_diagram.Symbols)
            elif hasattr(model_or_diagram, "Diagrams"):
                for diag in model_or_diagram.Diagrams:
                    symbols.extend(list(getattr(diag, "Symbols", [])))

            for sym in symbols:
                text_content = getattr(sym, "Text", "") or getattr(sym, "Name", "")
                if any(kw in text_content for kw in keywords):
                    if hasattr(sym, "Delete"):
                        sym.Delete()
                        removed_count += 1
        except Exception as e:
            print(f"[CollisionDetector] Strip notes warning: {e}")
        return removed_count


class LayoutAuditor:
    """Produces a diagnostic report of a PowerDesigner model/diagram layout health."""

    def __init__(self, clearance: int = 150):
        self.detector = CollisionDetector(clearance=clearance)

    def audit(self, diagram: Any) -> Dict[str, Any]:
        """Audits a single diagram and returns a summary dict."""
        report = {
            "diagram_name": getattr(diagram, "Name", "Unknown"),
            "total_symbols": 0,
            "overlapping_pairs": 0,
            "stray_draft_notes": 0,
            "warnings": [],
            "status": "PASS"
        }

        try:
            symbols = list(getattr(diagram, "Symbols", []))
            report["total_symbols"] = len(symbols)

            collisions = self.detector.check_diagram_collisions(diagram)
            report["overlapping_pairs"] = len(collisions)
            if collisions:
                report["warnings"].append(f"Found {len(collisions)} overlapping symbol pairs.")

            keywords = ["实现中", "待整链验收", "兼有教学管理", "系统用例不能", "计划图等同"]
            for sym in symbols:
                txt = getattr(sym, "Text", "") or getattr(sym, "Name", "")
                if any(kw in txt for kw in keywords):
                    report["stray_draft_notes"] += 1
            if report["stray_draft_notes"] > 0:
                report["warnings"].append(f"Found {report['stray_draft_notes']} stray draft annotations.")

            if report["overlapping_pairs"] > 0 or report["stray_draft_notes"] > 0:
                report["status"] = "WARN"

        except Exception as e:
            report["status"] = "ERROR"
            report["warnings"].append(str(e))

        return report

    def audit_model(self, model: Any) -> AuditReport:
        """Audits all diagrams within a model and returns a consolidated AuditReport."""
        model_name = getattr(model, "Name", "UnknownModel")
        report = AuditReport(model_name=model_name)

        diagrams = []
        if hasattr(model, "Diagrams"):
            diagrams = list(model.Diagrams)
        else:
            for coll_name in ["SequenceDiagrams", "UseCaseDiagrams", "ClassDiagrams", "PhysicalDiagrams"]:
                if hasattr(model, coll_name):
                    diagrams.extend(list(getattr(model, coll_name)))

        report.total_diagrams = len(diagrams)

        for diag in diagrams:
            diag_name = getattr(diag, "Name", "UnnamedDiagram")
            symbols = list(getattr(diag, "Symbols", []))
            report.total_symbols += len(symbols)

            collisions = self.detector.check_diagram_collisions(diag)
            if collisions:
                report.total_collisions += len(collisions)
                report.collisions_by_diagram[diag_name] = collisions
                report.warnings.append(f"Diagram '{diag_name}': {len(collisions)} overlapping symbol pairs.")

            keywords = ["实现中", "待整链验收", "兼有教学管理", "系统用例不能", "计划图等同"]
            for sym in symbols:
                txt = getattr(sym, "Text", "") or getattr(sym, "Name", "")
                if any(kw in txt for kw in keywords):
                    report.stray_draft_notes += 1

        if report.stray_draft_notes > 0:
            report.warnings.append(f"Model contains {report.stray_draft_notes} unapproved draft notes.")

        if report.total_collisions > 0 or report.stray_draft_notes > 0:
            report.status = "WARN"

        return report
