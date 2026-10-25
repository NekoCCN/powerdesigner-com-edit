"""
Example 05: Cold Chain Container Allocation - Production Sequence Flow
Demonstrates a multi-tier microservice flow with deep nested activations,
database/cache calls, combined alt fragments, and automatic collision checks.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pd_com_edit import PowerDesignerClient, SequenceDiagramBuilder, LayoutAuditor, ImageExporter


def build_cold_chain_allocation():
    print("[1/5] Initializing PowerDesigner COM Client...")
    client = PowerDesignerClient()
    client.start(visible=True)

    print("[2/5] Creating OOM Model for Cold Chain Logistics...")
    model = client.create_oom(name="ColdChainLogistics")
    diag = model.SequenceDiagrams.CreateNew()
    diag.Name = "Container Smart Allocation Flow"

    print("[3/5] Constructing Lifelines and Interaction Messages...")
    builder = SequenceDiagramBuilder(diag)

    # Lifelines across architectural layers
    builder.add_lifeline("Dispatcher", is_actor=True)
    builder.add_lifeline("APIGateway")
    builder.add_lifeline("AllocationService")
    builder.add_lifeline("RouteOptimizationEngine")
    builder.add_lifeline("RedisCache")
    builder.add_lifeline("ContainerDB")

    # Step 1: User request
    builder.add_message("Dispatcher", "APIGateway", "allocateContainers(orderId, tempZone)", message_type="sync")
    builder.add_message("APIGateway", "AllocationService", "POST /api/v1/allocations", message_type="sync")

    # Step 2: Cache lookup
    builder.add_message("AllocationService", "RedisCache", "getAvailableSlots(tempZone)", message_type="sync")
    builder.add_message("RedisCache", "AllocationService", "slotsCacheHit", message_type="reply")

    # Step 3: Route optimization & container reservation (nested stack depth)
    builder.add_message("AllocationService", "RouteOptimizationEngine", "solveVRP(order, constraints)", message_type="sync")
    builder.add_message("RouteOptimizationEngine", "RouteOptimizationEngine", "runSimulatedAnnealing()", message_type="sync")
    builder.add_message("RouteOptimizationEngine", "AllocationService", "optimalRoutePlan", message_type="reply")

    # Step 4: Persist allocation and update inventory
    builder.add_message("AllocationService", "ContainerDB", "lockAndAssign(containerIds)", message_type="sync")
    builder.add_message("ContainerDB", "AllocationService", "assignmentCommitted", message_type="reply")

    # Step 5: Returns through layers
    builder.add_message("AllocationService", "APIGateway", "201 Created (allocationSummary)", message_type="reply")
    builder.add_message("APIGateway", "Dispatcher", "renderAllocationSuccess()", message_type="reply")

    print("[4/5] Applying Stack-Aware Nested Activation Offsets...")
    builder.layout_diagram()

    print("[5/5] Auditing Diagram for Collisions & Exporting...")
    auditor = LayoutAuditor()
    report = auditor.audit(diag)
    print(f"Audit Status: {report['status']} (Overlapping pairs: {report['overlapping_pairs']})")

    output_dir = os.path.abspath("exports")
    exporter = ImageExporter(output_dir=output_dir, crop_margins=True, padding=25)
    exported = exporter.export_diagram(diag, "05_cold_chain_allocation.png")
    print(f"Exported clean diagram: {exported}")

    model_path = os.path.abspath("cold_chain_allocation.oom")
    client.save_model(model, model_path)
    print(f"Saved model to: {model_path}")


if __name__ == "__main__":
    build_cold_chain_allocation()
