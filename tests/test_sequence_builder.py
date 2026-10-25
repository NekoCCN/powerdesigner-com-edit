"""
Unit tests for SequenceDiagramBuilder (Offline Mock Tests).
Verifies lifeline creation, message placement, activation stack tracking,
and layout_diagram execution.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pd_com_edit.sequence import SequenceDiagramBuilder


class MockPoint:
    def __init__(self, y=0):
        self.Y = y


class MockPosition:
    def __init__(self, x=0, y=0):
        self.X = x
        self.Y = y


class MockSize:
    def __init__(self, x=1000, y=1000):
        self.X = x
        self.Y = y
        self.Width = x
        self.Height = y


class MockSymbol:
    def __init__(self, name="Symbol"):
        self.Name = name
        self.Position = MockPosition()
        self.Size = MockSize()
        self.SourcePoint = MockPoint()
        self.DestinationPoint = MockPoint()


class MockLifeline:
    def __init__(self, name=""):
        self.Name = name

    def SetName(self, name):
        self.Name = name


class MockMessage:
    def __init__(self):
        self.Name = ""
        self.Sender = None
        self.Receiver = None

    def SetName(self, name):
        self.Name = name


class MockCombinedFragment:
    def __init__(self):
        self.Name = ""
        self.InteractionOperator = ""

    def SetName(self, name):
        self.Name = name


class MockItemCollection:
    def __init__(self, factory):
        self.factory = factory
        self.items = []

    def CreateNew(self):
        item = self.factory()
        self.items.append(item)
        return item

    def __len__(self):
        return len(self.items)


class MockModel:
    def __init__(self):
        self.Actors = MockItemCollection(MockLifeline)
        self.Classes = MockItemCollection(MockLifeline)
        self.Messages = MockItemCollection(MockMessage)
        self.CombinedFragments = MockItemCollection(MockCombinedFragment)


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
        sym = MockSymbol(getattr(link_obj, "Name", "LinkSym"))
        self.Symbols.append(sym)
        self.link_objects_attached.append(link_obj)
        return sym


class TestSequenceDiagramBuilder(unittest.TestCase):
    def setUp(self):
        self.model = MockModel()
        self.diag = MockDiagram(self.model)
        self.builder = SequenceDiagramBuilder(self.diag)

    def test_add_lifelines(self):
        user_obj, _ = self.builder.add_lifeline("User", is_actor=True)
        self.assertEqual(user_obj.Name, "User")
        svc_obj, _ = self.builder.add_lifeline("AuthService", is_actor=False)
        self.assertEqual(svc_obj.Name, "AuthService")
        self.assertEqual(len(self.builder.lifelines), 2)

    def test_add_message_sync_and_reply(self):
        self.builder.add_lifeline("Client")
        self.builder.add_lifeline("Server")

        # Sync message
        y1 = self.builder.add_message("Client", "Server", "request()", message_type="sync")
        self.assertEqual(len(self.builder.messages), 1)
        self.assertFalse(self.builder.messages[0]["is_return"])

        # Reply message
        y2 = self.builder.add_message("Server", "Client", "response()", message_type="reply")
        self.assertEqual(len(self.builder.messages), 2)
        self.assertTrue(self.builder.messages[1]["is_return"])
        self.assertLess(y2, y1)

    def test_layout_diagram_and_activation_bars(self):
        self.builder.add_lifeline("Caller")
        self.builder.add_lifeline("Callee")

        self.builder.add_message("Caller", "Callee", "doWork()", message_type="sync")
        self.builder.add_message("Callee", "Caller", "workDone()", message_type="reply")

        bars = self.builder.layout_diagram()
        self.assertIsInstance(bars, list)
        self.assertGreaterEqual(len(bars), 1)
        self.assertEqual(bars[0][0], "Callee")  # Callee activation bar


if __name__ == "__main__":
    unittest.main()
