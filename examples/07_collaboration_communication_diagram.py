"""
Example 07: UML Communication / Collaboration Diagram (协作图 / 通信图)
Demonstrates:
- Registering Primary Actors and Domain Service Objects
- Linking interacting participants with InstanceLinks
- Numbered directional interaction messages (e.g. 1: submitOrder(), 1.1: verify(), 2: notify())
- Radial Star Topology Layout to eliminate intersecting links
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
    model = client.create_oom(name="HotelBooking_Collaboration")
    diag = model.CommunicationDiagrams.CreateNew()

    print("[3/4] Registering Actors, Interacting Objects, and Links...")
    builder = CommunicationDiagramBuilder(
        diag,
        name="Hotel Reservation Collaboration Flow",
        center_x=0,
        center_y=0,
        default_radius=24000
    )

    # Actor: Guest
    builder.add_actor("Guest")

    # Central Controller / Coordinator
    builder.add_object("OrderController", class_name="OrderController")

    # Collaborating Subsystem Services
    builder.add_object("RoomInventoryService", class_name="RoomInventoryService", width=10000, height=3600)
    builder.add_object("PaymentGateway", class_name="PaymentGateway", width=9000, height=3600)
    builder.add_object("NotificationService", class_name="NotificationService", width=9000, height=3600)

    # Message sequence:
    # 1. Guest -> OrderController: submitBooking()
    builder.add_message("Guest", "OrderController", "submitBooking()", sequence_number="1")

    # 1.1 OrderController -> RoomInventoryService: lockRoom()
    builder.add_message("OrderController", "RoomInventoryService", "lockRoom()", sequence_number="1.1")

    # 2. OrderController -> PaymentGateway: processPayment()
    builder.add_message("OrderController", "PaymentGateway", "processPayment()", sequence_number="2")

    # 2.1 OrderController -> NotificationService: sendConfirmation()
    builder.add_message("OrderController", "NotificationService", "sendConfirmation()", sequence_number="2.1")

    print("[4/4] Applying Radial Topology Layout...")
    builder.layout_radial(center_name="OrderController", radius=24000)

    output_oom = os.path.abspath("hotel_collaboration.oom")
    client.save_model(model, output_oom)
    print(f"Saved collaboration model to: {output_oom}")

    output_png = os.path.abspath("docs/images/collaboration-order-flow.png")
    builder.diagram.ExportImage(output_png)
    print(f"Exported collaboration diagram image to: {output_png}")

    client.close_model(model)


if __name__ == "__main__":
    main()
