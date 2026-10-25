---
name: powerdesigner-com-edit
description: Automate SAP PowerDesigner modeling, diagram layout, collision/overlap checking, activation bar generation, and batch export via Python COM. Use when creating/editing OOM, CDM, or PDM models, generating sequence diagrams with exact activation bars and alt frames, arranging use case diagrams, fixing overlapping text/lines/activation bars, or exporting clean diagrams for reports.
---

# PowerDesigner COM Automation & Edit Skill (`powerdesigner-com-edit`)

Use this skill to automate, construct, audit, resolve visual overlaps, and batch-export SAP PowerDesigner 16.5+ models (OOM, CDM, PDM) using Python and `pywin32`.

## Core Capabilities

1. **Headless & Interactive COM Control**: Open, create, modify, and save `.pbw` (Workspaces), `.oom` (Object-Oriented Models), and `.pdm` (Physical Data Models).
2. **Collision Detection & Overlap Auditing (重叠检查与自动规避)**:
   - **AABB Geometric Collision Check**: Audits all diagram symbols for bounding box and label intersections.
   - **Activation Bar Collision Check**: Verifies 0 same-depth intersecting activation intervals on all lifelines.
   - **Auto-Resolution Layout Shift**: Automatically adjusts vertical/horizontal coordinates to enforce minimum clearance.
   - **Draft Annotation Cleaner**: Automatically identifies and deletes lingering development notes (e.g. `（实现中，待整链验收）`, `兼有教学管理权限...`).
3. **Sequence Diagram Automation**:
   - Automated timeline placement of lifelines and synchronous/asynchronous messages.
   - **Call-Stack Activation Bar Algorithm**: Accurately bounds activation bars and applies horizontal nesting offsets ($X_{\text{offset}} = X_{\text{base}} + \text{depth} \times 120$) to prevent overlapping blocks.
   - **Combined Fragment (`alt`, `opt`, `loop`) Framing**: Calculates proper bounding boxes covering all participating lifelines and branch regions.
4. **Use Case & Class Diagram Layout**:
   - 3-column collision-free placement (Primary Actors $\to$ System Boundary Use Cases $\to$ External Systems).
   - Dynamic label spacing to eliminate overlapping text.
5. **Clean Production Export**:
   - Batch-export diagrams to PNG/JPEG with automatic bounding-box trimming (removes giant whitespace borders).

---

## 1. Quick Start / CLI Usage

The skill provides a Python automation module in `scripts/pd_automation.py`.

### Sequence Diagram with Activation Bars & Overlap Audit:
```python
from scripts.pd_automation import (
    PowerDesignerClient,
    SequenceDiagramBuilder,
    CollisionDetector,
    ImageExporter
)

client = PowerDesignerClient(visible=False)
model = client.create_oom_model("ColdChainSystem")
diagram = model.SequenceDiagrams.CreateNew()
diagram.SetName("SD_ContainerAllocation")

builder = SequenceDiagramBuilder(diagram)

# Add Lifelines
builder.add_lifeline("Operator", is_actor=True)
builder.add_lifeline("VueGateway")
builder.add_lifeline("OrderController")
builder.add_lifeline("ContainerService")

# Add Synchronous Calls & Returns
builder.add_message("Operator", "VueGateway", "clickAllocate()")
builder.add_message("VueGateway", "OrderController", "POST /allocation")
builder.add_message("OrderController", "ContainerService", "lockAndAssign()")
builder.add_message("ContainerService", "OrderController", "200 ALLOCATED", is_return=True)
builder.add_message("OrderController", "VueGateway", "200 OK", is_return=True)
builder.add_message("VueGateway", "Operator", "renderSuccess()", is_return=True)

# Build, calculate activation bars, and run automated overlap audit
completed_bars = builder.build_messages()

# Save & Export Image (with auto whitespace crop)
ImageExporter.export(diagram, "output/02-allocation-sequence.png", auto_crop=True)
client.close_all_safely()
```

---

## 2. Collision Detection & Overlap Prevention (重叠排查与修复)

### 1. Activation Bar Overlaps
When multiple calls hit the same lifeline:
- **Root Cause**: Scripts rendering activation rectangles at identical X coordinates without tracking call depth.
- **Auto-Fix**: `SequenceDiagramBuilder` automatically computes call nesting depth. If `depth > 0`, horizontal position is shifted:
  $$X_{\text{offset}} = X_{\text{base}} + \text{depth} \times 120$$
- **Verification**: `CollisionDetector.audit_activation_bar_overlaps(completed_bars)` ensures 0 intervals intersect on identical depths.

### 2. Symbol & Text Overlaps (AABB Collision)
```python
# Audit all symbols for overlapping bounding boxes
overlapping_pairs = CollisionDetector.audit_symbol_overlaps(diagram, clearance=150)
if overlapping_pairs:
    print(f"Found {len(overlapping_pairs)} colliding symbols! Auto-resolving...")
    CollisionDetector.auto_resolve_vertical_overlaps([p[1] for p in overlapping_pairs], min_spacing=300)
```

### 3. Cleaning Draft / Stray Annotations
Before submission or publication, strip development-phase text notes that cause label confusion:
```python
# Automatically removes text symbols matching draft patterns
removed = CollisionDetector.strip_draft_notes(diagram, keywords=[
    "实现中", "待整链验收", "兼有教学管理", "系统用例不能", "计划图等同"
])
print(f"Removed {removed} stray draft notes.")
```

---

## 3. Combined Fragments (`alt`, `opt`, `loop`)

To create clean branching blocks without manual coordinate guessing:

```python
# Bounding Box Math for alt / opt:
x_left = min(lifeline.x for lifeline in participants) - 400
x_right = max(lifeline.x for lifeline in participants) + 400
y_top = start_msg.y + 300
y_bottom = end_msg.y - 300

fragment = model.CombinedFragments.CreateNew()
fragment.SetName("alt")
frag_sym = diagram.AttachObject(fragment)
frag_sym.Position.X = (x_left + x_right) // 2
frag_sym.Position.Y = (y_top + y_bottom) // 2
frag_sym.Size.Width = x_right - x_left
frag_sym.Size.Height = y_top - y_bottom
```

---

## 4. Use Case Diagram Layout (防重叠三列布局)

To prevent line crossings and text collisions:
- **Column 1 ($X \approx 1500$)**: Primary Actors (e.g. Operator, Inspector, Dispatcher).
- **Column 2 ($X \approx 5500$)**: Use Cases inside System Boundary ($W=3200, H=1000, \Delta Y=-1200$).
- **Column 3 ($X \approx 9500$)**: Secondary Actors / External Systems (e.g. Customer, Audit System).

Associations are drawn left-to-right into Column 2, ensuring clean horizontal connections with zero diagonal label collisions.

---

## 5. Process Hygiene & Error Recovery

PowerDesigner's COM server (`pdshell16.exe`) can linger in memory if an exception occurs before `Quit()`, causing file-locking errors:

```powershell
# Kill lingering instances via PowerShell
Stop-Process -Name pdshell16 -Force -ErrorAction SilentlyContinue
```

In Python:
```python
from scripts.pd_automation import PowerDesignerClient
PowerDesignerClient.kill_lingering_processes()
```

---

## 6. References & Scripts

- [Overlap Detection Guide](references/overlap_detection_guide.md)
- [COM API Cheatsheet](references/com_api_cheatsheet.md)
- [Standalone Python Utility](scripts/pd_automation.py)
