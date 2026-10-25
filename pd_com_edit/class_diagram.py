#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UML Class Diagram Builder with Attributes, Operations & Relationship Routing
"""

from typing import Dict, Tuple, List, Any, Optional
from .collision import CollisionDetector
from .client import (
    attach_link_symbol,
    KIND_CLASS,
    KIND_INTERFACE,
    KIND_GENERALIZATION,
    KIND_CLASS_ASSOC,
    KIND_DEPENDENCY,
)


class ClassDiagramBuilder:
    """
    Constructs an OOM Class Diagram with:
    - Classes and Interfaces
    - Attributes (types, visibility: +, -, #)
    - Operations / Methods (parameters, return types)
    - Inheritance (Generalization), Implementation (Realization), and Associations
    - Automatic collision avoidance and vertical tree layout
    """

    def __init__(
        self,
        diagram: Any,
        start_x: int = 2000,
        spacing_x: int = 12000,
        start_y: int = 16000,
        spacing_y: int = -8000,
    ):
        self.diagram = diagram
        self.model = diagram.Model
        self.start_x = start_x
        self.spacing_x = spacing_x
        self.start_y = start_y
        self.spacing_y = spacing_y

        self.classes: Dict[str, Tuple[Any, Any]] = {}
        self.links: List[Tuple[Any, Any]] = []

    def add_class(
        self,
        name: str,
        is_interface: bool = False,
        x: Optional[int] = None,
        y: Optional[int] = None,
        width: int = 8000,
        height: int = 5000,
    ) -> Any:
        try:
            cls = self.model.CreateObject(KIND_INTERFACE if is_interface else KIND_CLASS)
        except Exception:
            cls = self.model.Classes.CreateNew()

        cls.SetName(name)
        if is_interface and hasattr(cls, "Stereotype"):
            cls.Stereotype = "Interface"

        sym = self.diagram.AttachObject(cls)
        idx = len(self.classes)
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

        self.classes[name] = (cls, sym)
        return cls

    def add_attribute(self, class_name: str, name: str, data_type: str = "String", visibility: str = "-"):
        """Add an attribute (field) to a class with visibility (+, -, #)."""
        if class_name not in self.classes:
            return
        cls_obj, _ = self.classes[class_name]
        attr = cls_obj.Attributes.CreateNew()
        attr.SetName(name)
        attr.DataType = data_type
        # Visibility mapping: + = Public, - = Private, # = Protected
        vis_map = {"+": 0, "-": 1, "#": 2}
        if hasattr(attr, "Visibility"):
            attr.Visibility = vis_map.get(visibility, 1)

    def add_operation(self, class_name: str, name: str, return_type: str = "void", visibility: str = "+"):
        """Add an operation (method) to a class."""
        if class_name not in self.classes:
            return
        cls_obj, _ = self.classes[class_name]
        op = cls_obj.Operations.CreateNew()
        op.SetName(name)
        op.ReturnType = return_type
        vis_map = {"+": 0, "-": 1, "#": 2}
        if hasattr(op, "Visibility"):
            op.Visibility = vis_map.get(visibility, 0)

    def add_generalization(self, sub_class: str, super_class: str) -> Any:
        """Add inheritance (subClass extends superClass). Attaches link symbol via AttachLinkObject."""
        if sub_class not in self.classes or super_class not in self.classes:
            return None
        sub_obj, _ = self.classes[sub_class]
        sup_obj, _ = self.classes[super_class]
        try:
            gen = self.model.CreateObject(KIND_GENERALIZATION)
        except Exception:
            gen = self.model.Generalizations.CreateNew()

        if hasattr(gen, "Child"):
            gen.Child = sub_obj
        if hasattr(gen, "Parent"):
            gen.Parent = sup_obj
        if hasattr(gen, "Object1"):
            gen.Object1 = sub_obj
        if hasattr(gen, "Object2"):
            gen.Object2 = sup_obj

        sym_l = attach_link_symbol(self.diagram, gen)
        self.links.append((gen, sym_l))
        return sym_l

    def add_association(
        self,
        class_a: str,
        class_b: str,
        role_a: str = "",
        role_b: str = "",
        cardinality_b: str = "*",
        name: str = "",
        role: str = "",
    ) -> Any:
        """Add association link between two classes. Attaches link symbol via AttachLinkObject."""
        if class_a not in self.classes or class_b not in self.classes:
            return None
        obj_a, _ = self.classes[class_a]
        obj_b, _ = self.classes[class_b]

        try:
            assoc = self.model.CreateObject(KIND_CLASS_ASSOC)
        except Exception:
            assoc = self.model.Associations.CreateNew()

        if name:
            assoc.SetName(name)

        if hasattr(assoc, "Object1"):
            assoc.Object1 = obj_a
        if hasattr(assoc, "Object2"):
            assoc.Object2 = obj_b
        if hasattr(assoc, "ClassA"):
            assoc.ClassA = obj_a
        if hasattr(assoc, "ClassB"):
            assoc.ClassB = obj_b

        # Resolve role / cardinality
        if role:
            if any(c.isalpha() for c in role):
                eff_role_b = role_b or role
                eff_card_b = cardinality_b or "*"
            else:
                eff_card_b = role
                eff_role_b = role_b
        else:
            eff_role_b = role_b
            eff_card_b = cardinality_b or "*"

        if eff_role_b and hasattr(assoc, "RoleB"):
            assoc.RoleB = eff_role_b
        if eff_card_b and hasattr(assoc, "CardinalityB"):
            assoc.CardinalityB = eff_card_b

        sym_l = attach_link_symbol(self.diagram, assoc)
        self.links.append((assoc, sym_l))
        return sym_l

    def audit_and_fix_overlaps(self, min_spacing: int = 1000):
        """Auto-resolve overlapping class boxes."""
        symbols = [sym for _, sym in self.classes.values() if sym is not None]
        if symbols:
            CollisionDetector.auto_resolve_vertical_overlaps(symbols, min_spacing=min_spacing)
