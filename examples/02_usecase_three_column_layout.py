"""
Example 02: Use Case Diagram with Canonical 3-Column Architecture
Demonstrates placing Human Actors on the left, Use Cases in the center, and External Systems on the right.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pd_com_edit import PowerDesignerClient, UseCaseDiagramBuilder


def main():
    print("[1/4] Connecting to SAP PowerDesigner...")
    client = PowerDesignerClient()
    client.start(visible=True)

    print("[2/4] Initializing Object-Oriented Model (OOM)...")
    model = client.create_oom(name="HospitalManagement_OOM")
    diag = model.UseCaseDiagrams.Item(0)
    diag.Name = "Patient Admissions Overview"

    print("[3/4] Registering Actors, Use Cases, and Systems...")
    builder = UseCaseDiagramBuilder(diag)

    # Left Column: Primary Actors
    builder.add_actor("Patient", is_primary=True)
    builder.add_actor("Doctor", is_primary=True)
    builder.add_actor("Nurse", is_primary=True)

    # Center Column: Core Use Cases
    builder.add_usecase("Register Online Appointment")
    builder.add_usecase("Verify Insurance Coverage")
    builder.add_usecase("Conduct Clinical Examination")
    builder.add_usecase("Prescribe Medication")
    builder.add_usecase("Discharge Patient")

    # Right Column: Secondary External Systems
    builder.add_system("National Health Insurance API")
    builder.add_system("Pharmacy Warehouse System")
    builder.add_system("SMS Notification Service")

    # Connect relationships
    builder.connect("Patient", "Register Online Appointment")
    builder.connect("Patient", "Verify Insurance Coverage")
    builder.connect("Verify Insurance Coverage", "National Health Insurance API")
    
    builder.connect("Doctor", "Conduct Clinical Examination")
    builder.connect("Doctor", "Prescribe Medication")
    builder.connect("Prescribe Medication", "Pharmacy Warehouse System")
    
    builder.connect("Nurse", "Discharge Patient")
    builder.connect("Discharge Patient", "SMS Notification Service")

    print("[4/4] Executing 3-Column Layout & Collision Check...")
    builder.layout_three_column()

    output_path = os.path.abspath("hospital_usecases.oom")
    client.save_model(model, output_path)
    print(f"Done! Saved model to: {output_path}")


if __name__ == "__main__":
    main()
