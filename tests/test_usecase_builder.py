"""
Unit tests for UseCaseDiagramBuilder (Offline Mock Tests).
Verifies link attachment via AttachLinkObject, Object1/Object2 endpoint binding,
and 3-column collision-free layout.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pd_com_edit.usecase import UseCaseDiagramBuilder
from pd_com_edit.client import KIND_ACTOR, KIND_USECASE, KIND_USECASE_ASSOC, KIND_DEPENDENCY


class MockPosition:
    def __init__(self, x=0, y=0):
        self.X = x
        self.Y = y


class MockSize:
    def __init__(self, x=10000, y=4000):
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


class MockModelObject:
    def __init__(self, kind, name=""):
        self.kind = kind
        self.Name = name
        self.Code = ""
        self.Stereotype = ""
        self.Object1 = None
        self.Object2 = None

    def SetName(self, name):
        self.Name = name


class MockCollection:
    def __init__(self, kind):
        self.kind = kind
        self.items = []

    def CreateNew(self):
        obj = MockModelObject(self.kind)
        self.items.append(obj)
        return obj

    def __len__(self):
        return len(self.items)


class MockModel:
    def __init__(self):
        self.Actors = MockCollection(KIND_ACTOR)
        self.UseCases = MockCollection(KIND_USECASE)
        self.Associations = MockCollection(KIND_USECASE_ASSOC)
        self.ExtendedDependencies = MockCollection(KIND_DEPENDENCY)
        self.created_objects = []

    def CreateObject(self, kind):
        obj = MockModelObject(kind)
        self.created_objects.append(obj)
        return obj


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


class TestUseCaseDiagramBuilder(unittest.TestCase):
    def setUp(self):
        self.model = MockModel()
        self.diag = MockDiagram(self.model)
        self.builder = UseCaseDiagramBuilder(self.diag)

    def test_add_actor_and_system(self):
        act = self.builder.add_actor("Customer", is_primary=True)
        self.assertEqual(act.Name, "Customer")
        self.assertIn("Customer", self.builder.actors)
        self.assertEqual(self.builder.actors["Customer"][1].Position.X, self.builder.col1_x)

        sys_act = self.builder.add_system("PaymentGateway")
        self.assertEqual(sys_act.Name, "PaymentGateway")
        self.assertIn("PaymentGateway", self.builder.actors)
        self.assertEqual(self.builder.actors["PaymentGateway"][1].Position.X, self.builder.col4_x)

    def test_add_use_case_and_alias(self):
        uc1 = self.builder.add_use_case("Book Room", code="UC01", column=2)
        self.assertEqual(uc1.Name, "UC01 Book Room")
        self.assertIn("Book Room", self.builder.use_cases)
        self.assertEqual(self.builder.use_cases["Book Room"][1].Position.X, self.builder.col2_x)

        uc2 = self.builder.add_usecase("Cancel Order", column=3)
        self.assertEqual(uc2.Name, "Cancel Order")
        self.assertIn("Cancel Order", self.builder.use_cases)
        self.assertEqual(self.builder.use_cases["Cancel Order"][1].Position.X, self.builder.col3_x)

    def test_link_uses_attach_link_object_and_sets_endpoints(self):
        self.builder.add_actor("Customer")
        self.builder.add_use_case("Book Room")

        link_sym = self.builder.link("Customer", "Book Room")
        self.assertIsNotNone(link_sym)

        # Verify link is attached via AttachLinkObject, NOT AttachObject
        self.assertEqual(len(self.diag.link_objects_attached), 1)
        assoc_obj = self.diag.link_objects_attached[0]
        self.assertEqual(assoc_obj.kind, KIND_USECASE_ASSOC)

        # Verify Object1 and Object2 are bound to Actor and Use Case
        self.assertEqual(assoc_obj.Object1.Name, "Customer")
        self.assertEqual(assoc_obj.Object2.Name, "Book Room")

    def test_link_use_cases_dependency(self):
        self.builder.add_use_case("Checkout")
        self.builder.add_use_case("Pay Deposit")

        dep_sym = self.builder.link_use_cases("Checkout", "Pay Deposit", stereotype="include")
        self.assertIsNotNone(dep_sym)

        self.assertEqual(len(self.diag.link_objects_attached), 1)
        dep_obj = self.diag.link_objects_attached[0]
        self.assertEqual(dep_obj.kind, KIND_DEPENDENCY)
        self.assertEqual(dep_obj.Stereotype, "include")
        self.assertEqual(dep_obj.Object1.Name, "Checkout")
        self.assertEqual(dep_obj.Object2.Name, "Pay Deposit")

    def test_connect_delegation(self):
        self.builder.add_actor("Receptionist")
        self.builder.add_use_case("Check In")
        self.builder.add_use_case("Verify ID")

        # Actor -> Use Case
        self.builder.connect("Receptionist", "Check In")
        # Use Case -> Actor (reverse order)
        self.builder.connect("Check In", "Receptionist")
        # Use Case -> Use Case
        self.builder.connect("Check In", "Verify ID", stereotype="include")

        self.assertEqual(len(self.diag.link_objects_attached), 3)

    def test_layout_three_column(self):
        self.builder.add_actor("Guest")
        self.builder.add_system("NotificationService")
        self.builder.add_use_case("Reserve")
        self.builder.connect("Guest", "Reserve")
        self.builder.connect("Reserve", "NotificationService")

        # Must execute without errors
        self.builder.layout_three_column()
        guest_sym = self.builder.actors["Guest"][1]
        notif_sym = self.builder.actors["NotificationService"][1]
        self.assertEqual(guest_sym.Position.X, self.builder.col1_x)
        self.assertEqual(notif_sym.Position.X, self.builder.col4_x)


if __name__ == "__main__":
    unittest.main()
