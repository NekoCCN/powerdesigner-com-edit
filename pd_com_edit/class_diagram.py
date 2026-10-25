#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UML Class Diagram Builder with Attributes, Operations & Relationship Routing
"""

from typing import Dict, Tuple, List, Any, Optional
from .collision import CollisionDetector

class ClassDiagramBuilder:
    """
    Constructs an OOM Class Diagram with:
    - Classes and Interfaces
    - Attributes (types, visibility: +, -, #)
    - Operations / Methods (parameters, return types)
    - Inheritance (Generalization), Implementation (Realization), and Associations
    - Automatic collision avoidance and vertical tree layout
    """

    def __init__(self, diagram: Any, start_x: int = 2000, spacing_x: int = 4000, start_y: int = -1500, spacing_y: int = -2500):
        self.diagram = diagram
        self.model = diagram.Model
        self.start_x = start_x
        self.spacing_x = spacing_x
        self.start_y = start_y
        self.spacing_y = spacing_y

        self.classes: Dict[str, Tuple[Any, Any]] = {}

    def add_class(self, name: str, is_interface: bool = False, x: Optional[int] = None, y: Optional[int] = None) -> Any:
        cls = self.model.Classes.CreateNew()
        cls.SetName(name)
        if is_interface:
            cls.Stereotype = "Interface"

        sym = self.diagram.AttachObject(cls)
        idx = len(self.classes)
        x_pos = x if x is not None else self.start_x + (idx % 3) * self.spacing_x
        y_pos = y if y is not None else self.start_y + (idx // 3) * self.spacing_y

        try:
            sym.Position.X = x_pos
            sym.Position.Y = y_pos
            sym.Size.Width = 3200
            sym.Size.Height = 1800
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

    def add_generalization(self, sub_class: str, super_class: str):
        """Add inheritance (subClass extends superClass)."""
        if sub_class not in self.classes or super_class not in self.classes:
            return
        sub_obj, _ = self.classes[sub_class]
        sup_obj, _ = self.classes[super_class]
        gen = self.model.Generalizations.CreateNew()
        gen.Child = sub_obj
        gen.Parent = sup_obj
        self.diagram.AttachObject(gen)

    def add_association(self, class_a: str, class_b: str, role_a: str = "", role_b: str = "", cardinality_b: str = "*"):
        """Add association link between two classes."""
        if class_a not in self.classes or class_b not in self.classes:
            return
        obj_a, _ = self.classes[class_a]
        obj_b, _ = self.classes[class_b]
        assoc = self.model.Associations.CreateNew()
        assoc.ClassA = obj_a
        assoc.ClassB = obj_b
        if hasattr(assoc, "RoleB"):
            assoc.RoleB = role_b
        if hasattr(assoc, "CardinalityB"):
            assoc.CardinalityB = cardinality_b
        self.diagram.AttachObject(assoc)

    def audit_and_fix_overlaps(self):
        """Auto-resolve overlapping class boxes."""
        symbols = [sym for _, sym in self.classes.values()]
        CollisionDetector.auto_resolve_vertical_overlaps(symbols, min_spacing=400)
