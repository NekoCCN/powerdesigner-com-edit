#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
High-Resolution Diagram Exporter with Smart Margin Auto-Cropping
"""

import os
from typing import Optional, Any

try:
    from PIL import Image
    import numpy as np
except ImportError:
    Image = None
    np = None


class ImageExporter:
    """Exports diagrams to image files with automatic whitespace cropping."""

    @staticmethod
    def export(diagram: Any, output_path: str, format_name: str = "PNG", auto_crop: bool = True, padding: int = 25) -> bool:
        """
        Export a single diagram to an image file.
        If auto_crop=True, crops unnecessary white background canvas margins using numpy/PIL.
        """
        if not os.path.isabs(output_path):
            output_path = os.path.abspath(output_path)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        try:
            diagram.ExportImage(output_path, format_name)
        except Exception as e:
            print(f"[ImageExporter] COM ExportImage error: {e}")
            return False

        if auto_crop and Image is not None and np is not None and os.path.exists(output_path):
            try:
                img = Image.open(output_path).convert("RGB")
                arr = np.array(img)
                # Find all non-white pixels (pixel < 250 in any channel)
                mask = np.any(arr < 250, axis=2)
                coords = np.argwhere(mask)
                if len(coords) > 0:
                    y0, x0 = coords.min(axis=0)
                    y1, x1 = coords.max(axis=0)
                    h, w = arr.shape[:2]
                    x0 = max(0, x0 - padding)
                    y0 = max(0, y0 - padding)
                    x1 = min(w - 1, x1 + padding)
                    y1 = min(h - 1, y1 + padding)
                    cropped = img.crop((x0, y0, x1 + 1, y1 + 1))
                    cropped.save(output_path)
            except Exception as e:
                print(f"[ImageExporter] Auto-crop warning: {e}")

        return os.path.exists(output_path)

    @classmethod
    def export_all_diagrams(cls, model: Any, output_dir: str, format_name: str = "PNG", auto_crop: bool = True) -> int:
        """Batch-export all diagrams across all packages in a model."""
        count = 0
        os.makedirs(output_dir, exist_ok=True)

        # Collect all diagram collections (OOM, PDM, CDM)
        diagram_types = [
            "SequenceDiagrams", "UseCaseDiagrams", "ClassDiagrams",
            "PhysicalDiagrams", "ConceptualDiagrams", "ActivityDiagrams"
        ]

        def process_package(pkg):
            nonlocal count
            for dtype in diagram_types:
                if hasattr(pkg, dtype):
                    coll = getattr(pkg, dtype)
                    for diag in coll:
                        diag_name = getattr(diag, "Name", f"diagram_{count+1}")
                        # Clean invalid path characters
                        safe_name = "".join(c for c in diag_name if c.isalnum() or c in "._- ")
                        out_path = os.path.join(output_dir, f"{safe_name}.{format_name.lower()}")
                        if cls.export(diag, out_path, format_name, auto_crop):
                            count += 1
            # Sub-packages
            if hasattr(pkg, "Packages"):
                for sub in pkg.Packages:
                    process_package(sub)

        process_package(model)
        return count
