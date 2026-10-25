"""
Example 04: Batch Diagram Auditor & Export
Demonstrates opening an existing model file, running collision detection across all diagrams,
cleaning up draft notes, and batch exporting high-resolution cropped PNG images.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pd_com_edit import PowerDesignerClient, LayoutAuditor, ImageExporter


def audit_and_export_model(model_path: str, export_dir: str = "exports"):
    print(f"[1/3] Loading model: {model_path}")
    client = PowerDesignerClient()
    client.start(visible=False)

    model = client.open_model(model_path)
    if not model:
        print(f"Failed to open model: {model_path}")
        return

    auditor = LayoutAuditor()
    print(f"[2/3] Auditing all diagrams in model: {model.Name}...")
    report = auditor.audit_model(model)
    print(report.get_summary())

    if report.total_collisions > 0:
        print(f"Warning: Found {report.total_collisions} collisions:")
        for diag_name, collisions in report.collisions_by_diagram.items():
            print(f"  Diagram '{diag_name}':")
            for c in collisions:
                print(f"    - [{c.collision_type}] {c.symbol1_name} and {c.symbol2_name} (Overlap: dx={c.overlap_x}, dy={c.overlap_y})")

    print(f"[3/3] Exporting cropped high-resolution diagrams to '{export_dir}'...")
    exporter = ImageExporter(output_dir=export_dir, crop_margins=True, padding=20)
    exported_files = exporter.export_model_diagrams(model)

    print(f"\nSuccessfully exported {len(exported_files)} diagrams:")
    for path in exported_files:
        print(f"  - {path}")

    client.close_model(model)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_path = sys.argv[1]
    else:
        print("Usage: python 04_batch_diagram_auditor.py <path_to_model_file.oom|pdm>")
        sys.exit(1)

    audit_and_export_model(target_path)
