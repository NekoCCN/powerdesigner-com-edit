#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Physical Data Model (PDM) & Relational Schema Builder
"""

from typing import Dict, Tuple, List, Optional, Any

class PdmBuilder:
    """
    Constructs a Physical Data Model (PDM) with:
    - Tables & Columns (Datatype, Primary Key, Foreign Key, Nullable, Default)
    - Foreign Key References and Cardinalities (1..1, 1..*, 0..1)
    - Indexes (Unique / Non-unique)
    - Physical Diagram Symbols & Clean Orthogonal Layout
    """

    def __init__(self, model: Any, diagram: Optional[Any] = None, start_x: int = 2000, spacing_x: int = 4500, start_y: int = -1500, spacing_y: int = -3000):
        self.model = model
        self.diagram = diagram if diagram else (model.PhysicalDiagrams.Item(0) if model.PhysicalDiagrams.Count > 0 else model.PhysicalDiagrams.CreateNew())
        self.start_x = start_x
        self.spacing_x = spacing_x
        self.start_y = start_y
        self.spacing_y = spacing_y

        self.tables: Dict[str, Tuple[Any, Any]] = {}

    def add_table(self, code: str, name: str = "", x: Optional[int] = None, y: Optional[int] = None) -> Any:
        tbl = self.model.Tables.CreateNew()
        tbl.Code = code
        tbl.SetName(name if name else code)

        sym = self.diagram.AttachObject(tbl)
        idx = len(self.tables)
        x_pos = x if x is not None else self.start_x + (idx % 3) * self.spacing_x
        y_pos = y if y is not None else self.start_y + (idx // 3) * self.spacing_y

        try:
            sym.Position.X = x_pos
            sym.Position.Y = y_pos
            sym.Size.Width = 3500
            sym.Size.Height = 2200
        except Exception:
            pass

        self.tables[code] = (tbl, sym)
        return tbl

    def add_column(self, table_code: str, col_code: str, col_name: str = "", data_type: str = "VARCHAR(64)",
                   is_pk: bool = False, is_mandatory: bool = True, default_val: str = ""):
        """Add a column to a table with data type and constraints."""
        if table_code not in self.tables:
            return
        tbl_obj, _ = self.tables[table_code]
        col = tbl_obj.Columns.CreateNew()
        col.Code = col_code
        col.SetName(col_name if col_name else col_code)
        col.DataType = data_type
        col.Mandatory = is_mandatory
        if default_val:
            col.DefaultValue = default_val

        if is_pk:
            col.Primary = True
            # Associate to table primary key
            pk_key = None
            for k in tbl_obj.Keys:
                if k.Primary:
                    pk_key = k
                    break
            if not pk_key:
                pk_key = tbl_obj.Keys.CreateNew()
                pk_key.Code = f"PK_{table_code}"
                pk_key.SetName(f"PK_{table_code}")
                pk_key.Primary = True
            pk_key.Columns.Add(col)

    def add_reference(self, parent_table: str, child_table: str, parent_col: str, child_col: str, ref_code: str = ""):
        """Create a foreign key reference between parent and child tables."""
        if parent_table not in self.tables or child_table not in self.tables:
            return
        p_obj, _ = self.tables[parent_table]
        c_obj, _ = self.tables[child_table]

        ref = self.model.References.CreateNew()
        code = ref_code if ref_code else f"FK_{child_table}_{parent_table}"
        ref.Code = code
        ref.SetName(code)
        ref.ParentTable = p_obj
        ref.ChildTable = c_obj

        # Add join pair
        join = ref.Joins.CreateNew()
        for c in p_obj.Columns:
            if c.Code.lower() == parent_col.lower():
                join.ParentTableColumn = c
                break
        for c in c_obj.Columns:
            if c.Code.lower() == child_col.lower():
                join.ChildTableColumn = c
                break

        self.diagram.AttachObject(ref)
