"""
PowerDesigner COM Edit (pd_com_edit)
A comprehensive automation and collision-free modeling framework for SAP PowerDesigner.
"""

__version__ = "1.0.0"
__author__ = "Ext Culith (NekoCCN)"

from .client import PowerDesignerClient, rgb
from .collision import CollisionDetector, LayoutAuditor, BoundingBox, CollisionRecord, AuditReport
from .sequence import SequenceDiagramBuilder
from .usecase import UseCaseDiagramBuilder
from .class_diagram import ClassDiagramBuilder
from .communication import CommunicationDiagramBuilder
from .activity import ActivityDiagramBuilder
from .statechart import StatechartDiagramBuilder
from .component import ComponentDiagramBuilder
from .deployment import DeploymentDiagramBuilder
from .pdm import PdmBuilder
from .export import ImageExporter

__all__ = [
    "PowerDesignerClient",
    "SequenceDiagramBuilder",
    "UseCaseDiagramBuilder",
    "ClassDiagramBuilder",
    "CommunicationDiagramBuilder",
    "ActivityDiagramBuilder",
    "StatechartDiagramBuilder",
    "ComponentDiagramBuilder",
    "DeploymentDiagramBuilder",
    "PdmBuilder",
    "CollisionDetector",
    "LayoutAuditor",
    "BoundingBox",
    "CollisionRecord",
    "AuditReport",
    "ImageExporter",
    "rgb",
]
