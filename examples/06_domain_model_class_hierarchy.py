"""
Example 06: Domain-Driven Design (DDD) Class Hierarchy Builder
Demonstrates creating a structured UML Class Diagram with base entities,
aggregate roots, value objects, repository interfaces, and inheritance trees.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pd_com_edit import PowerDesignerClient, ClassDiagramBuilder, LayoutAuditor


def build_ddd_domain_model():
    print("[1/4] Connecting to PowerDesigner COM...")
    client = PowerDesignerClient()
    client.start(visible=True)

    print("[2/4] Initializing OOM Model and Class Diagram...")
    model = client.create_oom(name="ColdChain_DomainModel")
    diag = model.ClassDiagrams.Item(0)
    diag.Name = "Container Management Domain Model"

    print("[3/4] Defining Classes, Interfaces, Attributes & Methods...")
    builder = ClassDiagramBuilder(diag)

    # 1. Base Entity
    builder.add_class(
        name="BaseEntity",
        is_interface=False,
        x=14000, y=16000
    )

    # 2. Interface: Repository
    builder.add_class(
        name="IContainerRepository",
        is_interface=True,
        x=26000, y=16000
    )

    # 3. Aggregate Root: ContainerOrder
    builder.add_class(
        name="ContainerOrder",
        is_interface=False,
        x=14000, y=8000
    )

    # 4. Entity: ColdContainer
    builder.add_class(
        name="ColdContainer",
        is_interface=False,
        x=2000, y=8000
    )

    # 5. Value Object: TempZone
    builder.add_class(
        name="TemperatureSpecification",
        is_interface=False,
        x=2000, y=0
    )

    # Connect Inheritance: ContainerOrder inherits BaseEntity
    builder.add_generalization("ContainerOrder", "BaseEntity")
    builder.add_generalization("ColdContainer", "BaseEntity")

    # Connect Associations
    builder.add_association("ContainerOrder", "ColdContainer", name="allocates", role="1..*")
    builder.add_association("ColdContainer", "TemperatureSpecification", name="monitored_by", role="1")

    print("[4/4] Auditing Layout & Saving Model...")
    auditor = LayoutAuditor()
    report = auditor.audit(diag)
    print(f"Audit Status: {report['status']} (Symbols: {report['total_symbols']})")

    output_path = os.path.abspath("domain_model.oom")
    client.save_model(model, output_path)
    print(f"Done! Saved domain model to: {output_path}")


if __name__ == "__main__":
    build_ddd_domain_model()
