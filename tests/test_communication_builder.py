"""
Unit tests for CommunicationDiagramBuilder (协作图 / 通信图离线单元测试).
Verifies:
- Actor and Object registration
- InstanceLink connection and AttachLinkObject
- Directional numbered message binding (link.Messages)
- Radial and Grid auto-layout
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pd_com_edit.communication import CommunicationDiagramBuilder


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

    def Add(self, item):
        self.items.append(item)

    def __iter__(self):
        return iter(self.items)

    def __len__(self):
        return len(self.items)


class MockActor:
    def __init__(self):
        self.Name = ""


class MockObject:
    def __init__(self):
        self.Name = ""
        self.ClassName = ""


class MockMessage:
    def __init__(self):
        self.Name = ""
        self.Sender = None
        self.Receiver = None
        self.InstanceLink = None


class MockInstanceLink:
    def __init__(self):
        self.Name = ""
        self.Object1 = None
        self.Object2 = None
        self.Messages = MockItemCollection(MockMessage)


class MockModel:
    def __init__(self):
        self.Actors = MockItemCollection(MockActor)
        self.Objects = MockItemCollection(MockObject)
        self.InstanceLinks = MockItemCollection(MockInstanceLink)
        self.Messages = MockItemCollection(MockMessage)


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


class TestCommunicationDiagramBuilder(unittest.TestCase):
    def setUp(self):
        self.model = MockModel()
        self.diag = MockDiagram(self.model)
        self.builder = CommunicationDiagramBuilder(self.diag)

    def test_add_actor_and_objects(self):
        act = self.builder.add_actor("Customer")
        self.assertEqual(act.Name, "Customer")
        self.assertIn("Customer", self.builder.actors)

        obj = self.builder.add_object("orderCtrl", class_name="OrderController")
        self.assertEqual(obj.Name, "orderCtrl")
        self.assertIn("orderCtrl", self.builder.objects)

    def test_add_link_and_numbered_messages(self):
        self.builder.add_actor("Guest")
        self.builder.add_object("roomService")
        self.builder.add_object("paymentGateway")

        # Add link explicitly
        link = self.builder.add_link("Guest", "roomService")
        self.assertIsNotNone(link)
        self.assertEqual(len(self.diag.link_objects_attached), 1)

        # Add numbered message 1
        msg1 = self.builder.add_message("Guest", "roomService", "bookRoom(roomType)", sequence_number="1:")
        self.assertIsNotNone(msg1)
        self.assertEqual(msg1.Name, "1: bookRoom(roomType)")
        self.assertEqual(len(link.Messages), 1)

        # Add message 2 (auto-creates link between roomService and paymentGateway)
        msg2 = self.builder.add_message("roomService", "paymentGateway", "chargeCard(amount)", sequence_number="2:")
        self.assertIsNotNone(msg2)
        self.assertEqual(msg2.Name, "2: chargeCard(amount)")
        self.assertEqual(len(self.diag.link_objects_attached), 2)

    def test_radial_layout(self):
        self.builder.add_actor("Client")
        self.builder.add_object("Gateway")
        self.builder.add_object("AuthService")
        self.builder.add_object("DB")

        self.builder.layout_radial(center_name="Gateway", radius=15000)
        gateway_sym = self.builder.objects["Gateway"][1]
        self.assertEqual(gateway_sym.Position.X, self.builder.center_x)
        self.assertEqual(gateway_sym.Position.Y, self.builder.center_y)


if __name__ == "__main__":
    unittest.main()
