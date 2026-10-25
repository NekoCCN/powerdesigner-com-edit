"""
Unit tests for CollisionDetector, BoundingBox, and LayoutAuditor (Offline Mock Tests).
Runs in any Python environment without requiring SAP PowerDesigner or pywin32 COM runtime.
"""

import unittest
import sys
import os

# Ensure package root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pd_com_edit.collision import BoundingBox, CollisionDetector, CollisionRecord, LayoutAuditor


class MockSymbol:
    """Mock PowerDesigner Symbol with Rect property."""
    def __init__(self, name: str, left: int, top: int, right: int, bottom: int, class_name: str = "Symbol"):
        self.Name = name
        self.Rect = f"{left} {top} {right} {bottom}"
        self.ClassName = class_name


class MockDiagram:
    """Mock PowerDesigner Diagram with Symbols collection."""
    def __init__(self, name: str, symbols: list):
        self.Name = name
        self.Symbols = symbols


class TestCollisionDetector(unittest.TestCase):
    def setUp(self):
        self.detector = CollisionDetector(clearance=150)

    def test_bounding_box_parsing(self):
        # PowerDesigner format: left top right bottom
        symbol = MockSymbol("BoxA", left=1000, top=5000, right=3000, bottom=2000)
        bbox = self.detector.parse_rect(symbol.Rect)
        self.assertIsNotNone(bbox)
        self.assertEqual(bbox.left, 1000)
        self.assertEqual(bbox.right, 3000)
        self.assertEqual(bbox.bottom, 2000)
        self.assertEqual(bbox.top, 5000)
        self.assertEqual(bbox.width, 2000)
        self.assertEqual(bbox.height, 3000)

    def test_aabb_no_overlap(self):
        box1 = BoundingBox(left=0, bottom=0, right=1000, top=1000)
        box2 = BoundingBox(left=2000, bottom=0, right=3000, top=1000)
        self.assertFalse(self.detector.check_overlap(box1, box2))

    def test_aabb_overlap_direct(self):
        box1 = BoundingBox(left=0, bottom=0, right=1500, top=1500)
        box2 = BoundingBox(left=1000, bottom=500, right=2500, top=2000)
        self.assertTrue(self.detector.check_overlap(box1, box2))

    def test_aabb_clearance_touch(self):
        # Distance is 100, which is < clearance (150), so it should report overlap
        box1 = BoundingBox(left=0, bottom=0, right=1000, top=1000)
        box2 = BoundingBox(left=1100, bottom=0, right=2100, top=1000)
        self.assertTrue(self.detector.check_overlap(box1, box2))

        # Distance is 200, which is > clearance (150), so no overlap
        box3 = BoundingBox(left=1200, bottom=0, right=2200, top=1000)
        self.assertFalse(self.detector.check_overlap(box1, box3))

    def test_diagram_symbol_audit(self):
        # Symbol 1 and Symbol 2 overlap
        s1 = MockSymbol("Actor1", left=0, top=4000, right=2000, bottom=0)
        s2 = MockSymbol("UseCase1", left=1500, top=3000, right=3500, bottom=1000)
        # Symbol 3 is far away
        s3 = MockSymbol("System1", left=20000, top=4000, right=25000, bottom=0)

        diag = MockDiagram("TestDiagram", [s1, s2, s3])
        collisions = self.detector.check_diagram_collisions(diag)

        self.assertEqual(len(collisions), 1)
        c = collisions[0]
        self.assertEqual(c.symbol1_name, "Actor1")
        self.assertEqual(c.symbol2_name, "UseCase1")
        self.assertEqual(c.collision_type, "symbol_overlap")

    def test_activation_collision_detection(self):
        # Two activations on same lifeline at same depth with overlapping time
        act1 = {
            "lifeline": "ServiceA",
            "start_y": 3000,
            "end_y": 1000,
            "depth": 0
        }
        act2 = {
            "lifeline": "ServiceA",
            "start_y": 2500,
            "end_y": 500,
            "depth": 0
        }
        collisions = self.detector.check_activation_collisions([act1, act2])
        self.assertEqual(len(collisions), 1)
        self.assertEqual(collisions[0].collision_type, "activation_overlap")

        # Now give act2 depth = 1 (nested stack tier offset)
        act2_nested = {
            "lifeline": "ServiceA",
            "start_y": 2500,
            "end_y": 500,
            "depth": 1
        }
        collisions_nested = self.detector.check_activation_collisions([act1, act2_nested])
        self.assertEqual(len(collisions_nested), 0)


class TestLayoutAuditor(unittest.TestCase):
    def test_audit_summary_format(self):
        class MockModel:
            Name = "Hospital_System"
            Diagrams = [
                MockDiagram("Sequence_1", [
                    MockSymbol("A", 0, 1000, 500, 0),
                    MockSymbol("B", 200, 800, 700, 100)
                ])
            ]

        auditor = LayoutAuditor()
        report = auditor.audit_model(MockModel())
        self.assertEqual(report.total_collisions, 1)
        summary = report.get_summary()
        self.assertIn("Hospital_System", summary)
        self.assertIn("1", summary)


if __name__ == "__main__":
    unittest.main()
