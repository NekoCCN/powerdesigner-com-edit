"""
Example 07: UML Communication / Collaboration Diagram (协作图 / 通信图)
Demonstrates:
- Textbook Standard UML 2.5 Anonymous Lifelines (:ClassName, zero duplicate text)
- 3-tier Hierarchical Message Sequence Numbering: 1 -> 1.1 -> 1.1.1, 1.2 -> 1.2.1, 1.3
- Multi-tier Architecture Layout (Actor -> Controller -> Services -> Repositories/Gateways)
- Automatic Normal-Vector Offset eliminating font-line overlaps
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pd_com_edit import PowerDesignerClient, CommunicationDiagramBuilder


def main():
    print("[1/4] Connecting to PowerDesigner...")
    client = PowerDesignerClient()
    client.start(visible=False)

    print("[2/4] Creating OOM Model and Communication Diagram...")
    model = client.create_oom(name="HotelBooking_Communication")
    diag = model.CommunicationDiagrams.CreateNew()

    print("[3/4] Registering Participants and Hierarchical Interactions...")
    builder = CommunicationDiagramBuilder(
        diag,
        name="Hotel Reservation Communication Flow",
    )

    # Actor: Primary User
    builder.add_actor("Guest")

    # Tier 1: Boundary Controller (Anonymous UML Lifeline :ClassName)
    builder.add_object(":OrderController", width=14000, height=4200)

    # Tier 2: Domain Subsystem Services
    builder.add_object(":RoomInventoryService", width=14000, height=4200)
    builder.add_object(":PaymentGateway", width=14000, height=4200)
    builder.add_object(":NotificationService", width=14000, height=4200)

    # Tier 3: Infrastructure Repositories & External Gateways
    builder.add_object(":RoomRepository", width=14000, height=4200)
    builder.add_object(":BankService", width=14000, height=4200)

    # Message Hierarchical Sequence Flow (1 -> 1.1 -> 1.1.1, 1.2 -> 1.2.1, 1.3):
    # 1. Primary Request from Guest to Controller
    builder.add_message("Guest", ":OrderController", "submitBooking()", sequence_number="1")

    # 1.1 Subordinate call to RoomInventoryService
    builder.add_message(":OrderController", ":RoomInventoryService", "lockRoom()", sequence_number="1.1")

    # 1.1.1 & 1.1.2 Nested calls from RoomInventoryService to RoomRepository
    builder.add_message(":RoomInventoryService", ":RoomRepository", "queryStatus()", sequence_number="1.1.1")
    builder.add_message(":RoomInventoryService", ":RoomRepository", "updateLock()", sequence_number="1.1.2")

    # 1.2 Next sequential transaction: process payment
    builder.add_message(":OrderController", ":PaymentGateway", "processPayment()", sequence_number="1.2")

    # 1.2.1 Nested call to external BankService
    builder.add_message(":PaymentGateway", ":BankService", "authorize()", sequence_number="1.2.1")

    # 1.3 Follow-up transaction: send notification
    builder.add_message(":OrderController", ":NotificationService", "sendConfirmation()", sequence_number="1.3")

    print("[4/4] Applying 4-Tier Architecture Layout...")
    builder.layout_tiered(
        tiers=[
            ["Guest"],
            [":OrderController"],
            [":RoomInventoryService", ":PaymentGateway", ":NotificationService"],
            [(":RoomRepository", 16000), (":BankService", 0)]
        ],
        start_x=-48000,
        spacing_x=34000,
        spacing_y=16000
    )

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    output_oom = os.path.join(base_dir, "hotel_collaboration.oom")
    client.save_model(model, output_oom)
    print(f"Saved collaboration model to: {output_oom}")

    output_png = os.path.join(base_dir, "docs", "images", "collaboration-order-flow.png")
    builder.diagram.ExportImage(output_png)
    print(f"Exported collaboration diagram image to: {output_png}")

    client.close_model(model)


if __name__ == "__main__":
    main()
