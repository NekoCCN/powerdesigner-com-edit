"""
Unit tests for PdmBuilder (Offline Mock Tests).
Verifies table creation with column lists, foreign key reference creation,
and AttachLinkObject connector attachment.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pd_com_edit.pdm import PdmBuilder


class MockPosition:
    def __init__(self, x=0, y=0):
        self.X = x
        self.Y = y


class MockSize:
    def __init__(self, x=10000, y=6000):
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


class MockColumn:
    def __init__(self):
        self.Code = ""
        self.Name = ""
        self.DataType = ""
        self.Mandatory = True
        self.Primary = False
        self.DefaultValue = ""

    def SetName(self, name):
        self.Name = name


class MockKey:
    def __init__(self):
        self.Code = ""
        self.Name = ""
        self.Primary = False
        self.Columns = MockItemCollection(MockColumn)

    def SetName(self, name):
        self.Name = name


class MockJoin:
    def __init__(self):
        self.ParentTableColumn = None
        self.ChildTableColumn = None


class MockTable:
    def __init__(self):
        self.Code = ""
        self.Name = ""
        self.Columns = MockItemCollection(MockColumn)
        self.Keys = MockItemCollection(MockKey)

    def SetName(self, name):
        self.Name = name


class MockReference:
    def __init__(self):
        self.Code = ""
        self.Name = ""
        self.ParentTable = None
        self.ChildTable = None
        self.Object1 = None
        self.Object2 = None
        self.Joins = MockItemCollection(MockJoin)

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

    def Add(self, item):
        self.items.append(item)

    def __iter__(self):
        return iter(self.items)

    def __len__(self):
        return len(self.items)


class MockModel:
    def __init__(self):
        self.Tables = MockItemCollection(MockTable)
        self.References = MockItemCollection(MockReference)
        self.PhysicalDiagrams = MockItemCollection(lambda: None)


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


class TestPdmBuilder(unittest.TestCase):
    def setUp(self):
        self.model = MockModel()
        self.diag = MockDiagram(self.model)
        self.builder = PdmBuilder(self.model, self.diag)

    def test_add_table_with_columns(self):
        cols = [
            {"name": "User ID", "code": "user_id", "type": "BIGINT", "pk": True},
            {"name": "Username", "code": "username", "type": "VARCHAR(64)", "mandatory": True},
            {"name": "Created At", "code": "created_at", "type": "TIMESTAMP", "default": "NOW()"},
        ]
        tbl = self.builder.add_table(name="t_user", code="t_user", columns=cols)
        self.assertEqual(tbl.Code, "t_user")
        self.assertEqual(len(tbl.Columns), 3)

        # Check primary key column
        pk_col = tbl.Columns.items[0]
        self.assertEqual(pk_col.Code, "user_id")
        self.assertTrue(pk_col.Primary)
        self.assertEqual(len(tbl.Keys), 1)

    def test_add_reference_uses_attach_link_object(self):
        self.builder.add_table(
            name="Product Category",
            code="t_category",
            columns=[{"code": "cat_id", "type": "INT", "pk": True}],
        )
        self.builder.add_table(
            name="Product Item",
            code="t_product",
            columns=[
                {"code": "prod_id", "type": "INT", "pk": True},
                {"code": "cat_id", "type": "INT"},
            ],
        )

        ref_sym = self.builder.add_reference(
            parent_table="Product Category",
            child_table="Product Item",
            parent_col="cat_id",
            child_col="cat_id",
            name="FK_Product_Category",
        )
        self.assertIsNotNone(ref_sym)

        self.assertEqual(len(self.diag.link_objects_attached), 1)
        ref = self.diag.link_objects_attached[0]
        self.assertEqual(ref.Name, "FK_Product_Category")
        self.assertEqual(ref.ParentTable.Code, "t_category")
        self.assertEqual(ref.ChildTable.Code, "t_product")
        self.assertEqual(len(ref.Joins), 1)
        self.assertEqual(ref.Joins.items[0].ParentTableColumn.Code, "cat_id")
        self.assertEqual(ref.Joins.items[0].ChildTableColumn.Code, "cat_id")


if __name__ == "__main__":
    unittest.main()
