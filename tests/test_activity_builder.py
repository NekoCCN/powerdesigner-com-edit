"""
Unit tests for ActivityDiagramBuilder and StatechartDiagramBuilder (Offline Mock Tests).
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pd_com_edit.activity import ActivityDiagramBuilder
from pd_com_edit.statechart import StatechartDiagramBuilder


class MockPosition:
    def __init__(self, x=0, y=0):
        self.X = x
        self.Y = y


class MockSize:
    def __init__(self, x=12000, y=5000):
        self.X = x
        self.Y = y
        self.Width = x
        self.Height = y


class MockSymbol:
    def __init__(self, name="Symbol"):
        self.Name = name
        self.Position = MockPosition()
        self.Size = MockSize()


class MockLinkSymbol(MockSymbol):
    pass


class MockItemCollection:
    def __init__(self, factory):
        self.factory = factory
        self.items = []

    def CreateNew(self):
        item = self.factory()
        self.items.append(item)
        return item

    def __iter__(self):
        return iter(self.items)

    def __len__(self):
        return len(self.items)


class MockNamedObject:
    def __init__(self):
        self.Name = ""
        self.Condition = ""
        self.Event = ""
        self.Object1 = None
        self.Object2 = None


class MockModel:
    def __init__(self):
        self.Activities = MockItemCollection(MockNamedObject)
        self.Decisions = MockItemCollection(MockNamedObject)
        self.Flows = MockItemCollection(MockNamedObject)
        self.States = MockItemCollection(MockNamedObject)
        self.Transitions = MockItemCollection(MockNamedObject)


class MockDiagram:
    def __init__(self, model):
        self.Model = model
        self.Symbols = []
        self.link_objects_attached = []
        self.objects_attached = []

    def AttachObject(self, obj):
        sym = MockSymbol(getattr(obj, "Name", "ObjSym"))
        self.Symbols.append(sym)
        self.objects_attached.append(obj)
        return sym

    def AttachLinkObject(self, link_obj):
        sym = MockLinkSymbol(getattr(link_obj, "Name", "LinkSym"))
        self.Symbols.append(sym)
        self.link_objects_attached.append(link_obj)
        return sym


class TestActivityAndStatechartBuilders(unittest.TestCase):
    def setUp(self):
        self.model = MockModel()
        self.diag = MockDiagram(self.model)

    def test_activity_diagram_flow(self):
        builder = ActivityDiagramBuilder(self.diag)
        builder.add_activity("Fill Booking Form")
        builder.add_decision("Is Room Available?")
        builder.add_activity("Process Payment")

        flow1 = builder.add_flow("Fill Booking Form", "Is Room Available?")
        self.assertIsNotNone(flow1)
        flow2 = builder.add_flow("Is Room Available?", "Process Payment", guard="Yes")
        self.assertIsNotNone(flow2)

        self.assertEqual(len(self.diag.link_objects_attached), 2)
        self.assertEqual(self.diag.link_objects_attached[1].Name, "[Yes]")

    def test_statechart_diagram_transitions(self):
        builder = StatechartDiagramBuilder(self.diag)
        builder.add_state("PendingPayment")
        builder.add_state("OrderConfirmed")
        builder.add_state("Cancelled")

        trans1 = builder.add_transition(
            "PendingPayment", "OrderConfirmed",
            event="paymentSuccess", guard="balance >= amount", action="sendReceipt()"
        )
        self.assertIsNotNone(trans1)
        self.assertEqual(len(self.diag.link_objects_attached), 1)
        trans_obj = self.diag.link_objects_attached[0]
        self.assertEqual(trans_obj.Object1.Name, "PendingPayment")
        self.assertEqual(trans_obj.Object2.Name, "OrderConfirmed")


if __name__ == "__main__":
    unittest.main()
