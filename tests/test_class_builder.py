"""
Unit tests for ClassDiagramBuilder (Offline Mock Tests).
Verifies class/interface registration, generalization/association creation,
and AttachLinkObject connector attachment.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pd_com_edit.class_diagram import ClassDiagramBuilder
from pd_com_edit.client import KIND_CLASS, KIND_INTERFACE, KIND_GENERALIZATION, KIND_CLASS_ASSOC


class MockPosition:
    def __init__(self, x=0, y=0):
        self.X = x
        self.Y = y


class MockSize:
    def __init__(self, x=8000, y=5000):
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


class MockAttribute:
    def __init__(self, name=""):
        self.Name = name
        self.DataType = "String"
        self.Visibility = 1

    def SetName(self, name):
        self.Name = name


class MockOperation:
    def __init__(self, name=""):
        self.Name = name
        self.ReturnType = "void"
        self.Visibility = 0

    def SetName(self, name):
        self.Name = name


class MockClass:
    def __init__(self, kind, name=""):
        self.kind = kind
        self.Name = name
        self.Stereotype = ""
        self.Attributes = MockItemCollection(MockAttribute)
        self.Operations = MockItemCollection(MockOperation)

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


class MockGeneralization:
    def __init__(self):
        self.kind = KIND_GENERALIZATION
        self.Child = None
        self.Parent = None
        self.Object1 = None
        self.Object2 = None


class MockAssociation:
    def __init__(self):
        self.kind = KIND_CLASS_ASSOC
        self.Name = ""
        self.ClassA = None
        self.ClassB = None
        self.Object1 = None
        self.Object2 = None
        self.RoleB = ""
        self.CardinalityB = ""

    def SetName(self, name):
        self.Name = name


class MockModel:
    def __init__(self):
        self.Classes = MockItemCollection(lambda: MockClass(KIND_CLASS))
        self.Generalizations = MockItemCollection(MockGeneralization)
        self.Associations = MockItemCollection(MockAssociation)

    def CreateObject(self, kind):
        if kind == KIND_INTERFACE:
            c = MockClass(KIND_INTERFACE)
            c.Stereotype = "Interface"
            return c
        elif kind == KIND_CLASS:
            return MockClass(KIND_CLASS)
        elif kind == KIND_GENERALIZATION:
            return MockGeneralization()
        elif kind == KIND_CLASS_ASSOC:
            return MockAssociation()
        return MockClass(kind)


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


class TestClassDiagramBuilder(unittest.TestCase):
    def setUp(self):
        self.model = MockModel()
        self.diag = MockDiagram(self.model)
        self.builder = ClassDiagramBuilder(self.diag)

    def test_add_class_and_interface(self):
        cls = self.builder.add_class("BaseEntity")
        self.assertEqual(cls.Name, "BaseEntity")
        self.assertIn("BaseEntity", self.builder.classes)

        iface = self.builder.add_class("IRepository", is_interface=True)
        self.assertEqual(iface.Name, "IRepository")
        self.assertEqual(iface.Stereotype, "Interface")

    def test_add_attribute_and_operation(self):
        self.builder.add_class("User")
        self.builder.add_attribute("User", "username", data_type="String", visibility="-")
        self.builder.add_operation("User", "login", return_type="boolean", visibility="+")

        user_cls = self.builder.classes["User"][0]
        self.assertEqual(len(user_cls.Attributes), 1)
        self.assertEqual(user_cls.Attributes.items[0].Name, "username")
        self.assertEqual(len(user_cls.Operations), 1)
        self.assertEqual(user_cls.Operations.items[0].Name, "login")

    def test_add_generalization_uses_attach_link_object(self):
        self.builder.add_class("Animal")
        self.builder.add_class("Dog")

        gen_sym = self.builder.add_generalization("Dog", "Animal")
        self.assertIsNotNone(gen_sym)

        self.assertEqual(len(self.diag.link_objects_attached), 1)
        gen = self.diag.link_objects_attached[0]
        self.assertEqual(gen.Child.Name, "Dog")
        self.assertEqual(gen.Parent.Name, "Animal")
        self.assertEqual(gen.Object1.Name, "Dog")
        self.assertEqual(gen.Object2.Name, "Animal")

    def test_add_association_uses_attach_link_object(self):
        self.builder.add_class("Order")
        self.builder.add_class("OrderItem")

        assoc_sym = self.builder.add_association(
            "Order", "OrderItem", name="contains", role="1..*"
        )
        self.assertIsNotNone(assoc_sym)

        self.assertEqual(len(self.diag.link_objects_attached), 1)
        assoc = self.diag.link_objects_attached[0]
        self.assertEqual(assoc.Name, "contains")
        self.assertEqual(assoc.Object1.Name, "Order")
        self.assertEqual(assoc.Object2.Name, "OrderItem")
        self.assertEqual(assoc.CardinalityB, "1..*")


if __name__ == "__main__":
    unittest.main()
