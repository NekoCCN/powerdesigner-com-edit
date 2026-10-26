#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UML Deployment Diagram Builder (部署图构建器)
Features:
- Physical / Virtual Nodes (Servers, Docker Containers, Mobile Clients, Clusters)
- Deployed Artifacts
- Node Communication Associations (HTTP/HTTPS, gRPC, TCP, JDBC)
"""

from typing import Dict, Tuple, List, Optional, Any
from .client import attach_link_symbol


class DeploymentDiagramBuilder:
    """
    Constructs UML Deployment Diagrams (部署图) in PowerDesigner OOM.
    Models physical deployment topology and networking associations.
    """

    def __init__(
        self,
        diagram: Any,
        start_x: int = -20000,
        spacing_x: int = 18000,
        start_y: int = 12000,
        spacing_y: int = -8000,
    ):
        self.diagram = diagram
        self.model = diagram.Model
        self.start_x = start_x
        self.spacing_x = spacing_x
        self.start_y = start_y
        self.spacing_y = spacing_y

        self.nodes: Dict[str, Tuple[Any, Any]] = {}
        self.artifacts: Dict[str, Tuple[Any, Any]] = {}
        self.associations: List[Tuple[Any, Any]] = []

    def add_node(
        self,
        name: str,
        stereotype: str = "",
        x: Optional[int] = None,
        y: Optional[int] = None,
        width: int = 14000,
        height: int = 8000,
    ) -> Any:
        node = self.model.Nodes.CreateNew()
        node.Name = name
        if stereotype and hasattr(node, "Stereotype"):
            node.Stereotype = stereotype

        sym = self.diagram.AttachObject(node)
        idx = len(self.nodes)
        pos_x = x if x is not None else (self.start_x + (idx % 3) * self.spacing_x)
        pos_y = y if y is not None else (self.start_y + (idx // 3) * self.spacing_y)

        try:
            if hasattr(sym, "Position"):
                sym.Position.X = pos_x
                sym.Position.Y = pos_y
            if hasattr(sym, "Size"):
                if hasattr(sym.Size, "X"):
                    sym.Size.X = width
                    sym.Size.Y = height
                elif hasattr(sym.Size, "Width"):
                    sym.Size.Width = width
                    sym.Size.Height = height
        except Exception:
            pass

        self.nodes[name] = (node, sym)
        return node

    def add_connection(
        self,
        node1_name: str,
        node2_name: str,
        protocol: str = "",
    ) -> Any:
        """Create a communication association link between two physical nodes."""
        if node1_name not in self.nodes or node2_name not in self.nodes:
            return None

        n1, _ = self.nodes[node1_name]
        n2, _ = self.nodes[node2_name]

        assoc = self.model.NodeAssociations.CreateNew() if hasattr(self.model, "NodeAssociations") else self.model.ExtendedDependencies.CreateNew()
        assoc.Object1 = n1
        assoc.Object2 = n2
        if protocol and hasattr(assoc, "Stereotype"):
            assoc.Stereotype = protocol

        sym_l = attach_link_symbol(self.diagram, assoc)
        self.associations.append((assoc, sym_l))
        return sym_l
