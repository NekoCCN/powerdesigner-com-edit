#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Physical Data Model (PDM) & Relational Schema Builder
"""

from typing import Dict, Tuple, List, Optional, Any
from .client import attach_link_symbol
from .collision import CollisionDetector


class PdmBuilder:
    """
    Constructs a Physical Data Model (PDM) with:
    - Tables & Columns (Datatype, Primary Key, Foreign Key, Nullable, Default)
    - Foreign Key References and Cardinalities (1..1, 1..*, 0..1)
    - Indexes (Unique / Non-unique)
    - Physical Diagram Symbols & Clean Orthogonal Layout
    """

    def __init__(
        self,
        model: Any,
        diagram: Optional[Any] = None,
        start_x: int = 2000,
        spacing_x: int = 14000,
        start_y: int = 12000,
        spacing_y: int = -8000,
    ):
        self.model = model
        self.diagram = diagram if diagram else (
            model.PhysicalDiagrams.Item(0)
            if model.PhysicalDiagrams.Count > 0
            else model.PhysicalDiagrams.CreateNew()
        )
        self.start_x = start_x
        self.spacing_x = spacing_x
        self.start_y = start_y
        self.spacing_y = spacing_y

        self.tables: Dict[str, Tuple[Any, Any]] = {}
        self.references: List[Tuple[Any, Any]] = []

    def _find_table(self, identifier: str) -> Optional[Tuple[Any, Any]]:
        """Look up a registered table by code or name (case-insensitive)."""
        if identifier in self.tables:
            return self.tables[identifier]
        low = identifier.lower().strip()
        for k, v in self.tables.items():
            if k.lower().strip() == low:
                return v
            tbl_obj, _ = v
            if hasattr(tbl_obj, "Name") and tbl_obj.Name.lower().strip() == low:
                return v
            if hasattr(tbl_obj, "Code") and tbl_obj.Code.lower().strip() == low:
                return v
        return None

    def add_table(
        self,
        code: str = "",
        name: str = "",
        columns: Optional[List[Dict[str, Any]]] = None,
        x: Optional[int] = None,
        y: Optional[int] = None,
        width: int = 10000,
        height: int = 6000,
    ) -> Any:
        # Support positional or keyword arguments where name/code may be swapped
        tbl_code = code or name
        tbl_name = name or code or tbl_code

        tbl = self.model.Tables.CreateNew()
        tbl.Code = tbl_code
        tbl.SetName(tbl_name)

        sym = self.diagram.AttachObject(tbl)
        idx = len(self.tables)
        x_pos = x if x is not None else self.start_x + (idx % 3) * self.spacing_x
        y_pos = y if y is not None else self.start_y + (idx // 3) * self.spacing_y

        try:
            if hasattr(sym, "Position"):
                sym.Position.X = x_pos
                sym.Position.Y = y_pos
            if hasattr(sym, "Size"):
                if hasattr(sym.Size, "X"):
                    sym.Size.X = width
                    sym.Size.Y = height
                elif hasattr(sym.Size, "Width"):
                    sym.Size.Width = width
                    sym.Size.Height = height
        except Exception:
            pass

        self.tables[tbl_code] = (tbl, sym)
        if tbl_name != tbl_code:
            self.tables[tbl_name] = (tbl, sym)

        if columns:
            for col_def in columns:
                c_name = col_def.get("name", "")
                c_code = col_def.get("code", c_name)
                c_type = col_def.get("type", col_def.get("data_type", "VARCHAR(64)"))
                is_pk = bool(col_def.get("pk", col_def.get("is_pk", False)))
                is_mand = bool(col_def.get("mandatory", col_def.get("is_mandatory", True)))
                default_val = str(col_def.get("default", col_def.get("default_val", "")))
                self.add_column(
                    table_code=tbl_code,
                    col_code=c_code,
                    col_name=c_name,
                    data_type=c_type,
                    is_pk=is_pk,
                    is_mandatory=is_mand,
                    default_val=default_val,
                )

        return tbl

    def add_column(
        self,
        table_code: str,
        col_code: str,
        col_name: str = "",
        data_type: str = "VARCHAR(64)",
        is_pk: bool = False,
        is_mandatory: bool = True,
        default_val: str = "",
    ):
        """Add a column to a table with data type and constraints."""
        found = self._find_table(table_code)
        if not found:
            return
        tbl_obj, _ = found
        col = tbl_obj.Columns.CreateNew()
        col.Code = col_code
        col.SetName(col_name if col_name else col_code)
        col.DataType = data_type
        col.Mandatory = is_mandatory
        if default_val:
            col.DefaultValue = default_val

        if is_pk:
            col.Primary = True
            pk_key = None
            for k in tbl_obj.Keys:
                if k.Primary:
                    pk_key = k
                    break
            if not pk_key:
                pk_key = tbl_obj.Keys.CreateNew()
                pk_key.Code = f"PK_{tbl_obj.Code}"
                pk_key.SetName(f"PK_{tbl_obj.Code}")
                pk_key.Primary = True
            pk_key.Columns.Add(col)

    def add_reference(
        self,
        parent_table: str,
        child_table: str,
        parent_col: str,
        child_col: str,
        ref_code: str = "",
        name: str = "",
    ) -> Any:
        """Create a foreign key reference between parent and child tables. Attaches via AttachLinkObject."""
        p_entry = self._find_table(parent_table)
        c_entry = self._find_table(child_table)
        if not p_entry or not c_entry:
            return None
        p_obj, _ = p_entry
        c_obj, _ = c_entry

        ref = self.model.References.CreateNew()
        code = ref_code or name or f"FK_{c_obj.Code}_{p_obj.Code}"
        ref.Code = code
        ref.SetName(name or code)
        ref.ParentTable = p_obj
        ref.ChildTable = c_obj
        if hasattr(ref, "Object1"):
            ref.Object1 = p_obj
        if hasattr(ref, "Object2"):
            ref.Object2 = c_obj

        # Add join pair
        join = ref.Joins.CreateNew()
        for c in p_obj.Columns:
            if c.Code.lower() == parent_col.lower() or (hasattr(c, "Name") and c.Name.lower() == parent_col.lower()):
                join.ParentTableColumn = c
                break
        for c in c_obj.Columns:
            if c.Code.lower() == child_col.lower() or (hasattr(c, "Name") and c.Name.lower() == child_col.lower()):
                join.ChildTableColumn = c
                break

        sym_l = attach_link_symbol(self.diagram, ref)
        self.references.append((ref, sym_l))
        return sym_l

    def auto_layout(self, min_spacing: int = 1500):
        """Auto-resolve overlapping table boxes."""
        symbols = [sym for _, sym in self.tables.values() if sym is not None]
        # De-duplicate symbols
        unique_syms = []
        seen = set()
        for s in symbols:
            s_id = id(s)
            if s_id not in seen:
                seen.add(s_id)
                unique_syms.append(s)
        if unique_syms:
            CollisionDetector.auto_resolve_vertical_overlaps(unique_syms, min_spacing=min_spacing)
