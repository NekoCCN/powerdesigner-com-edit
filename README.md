# powerdesigner-com-edit

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Platform: Windows](https://img.shields.io/badge/platform-Windows-lightgrey.svg)](https://microsoft.com/windows)

PowerDesigner COM Edit (`powerdesigner-com-edit`) is an Agent Skill (`SKILL.md`) and Python automation toolkit for SAP PowerDesigner (16.5+). It enables AI coding assistants (such as Claude Code, Google Antigravity, and Codex) and human developers to programmatically generate, layout, audit, and export UML and database models via Windows COM (`PowerDesigner.Application`).

---

## Agent Skill Installation

This repository is structured as a standard Agent Skill. When installed, AI agents automatically recognize when you need PowerDesigner automation and leverage this skill to construct clean, collision-free diagrams.

### 1. One-Line Installer (Recommended)

Run the included installer to automatically detect your agent directories and install the skill:

```bash
# Clone the repository
git clone https://github.com/NekoCCN/powerdesigner-com-edit.git
cd powerdesigner-com-edit

# Install for both Claude Code and Antigravity (Gemini)
python install.py

# Or install for a specific agent:
python install.py --target claude    # Only Claude Code
python install.py --target gemini    # Only Antigravity / Gemini
python install.py --target local     # Project-local (.agents/skills)
```

Windows PowerShell one-liner:
```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

### 2. Manual Installation by Agent Platform

#### For Claude Code
Clone or link the repository into your global Claude skills directory:
```bash
git clone https://github.com/NekoCCN/powerdesigner-com-edit.git ~/.claude/skills/powerdesigner-com-edit
```
On Windows:
```powershell
git clone https://github.com/NekoCCN/powerdesigner-com-edit.git "$HOME\.claude\skills\powerdesigner-com-edit"
```

#### For Google Antigravity / Gemini CLI
Clone into your global Antigravity skills directory:
```bash
git clone https://github.com/NekoCCN/powerdesigner-com-edit.git ~/.gemini/skills/powerdesigner-com-edit
```
On Windows:
```powershell
git clone https://github.com/NekoCCN/powerdesigner-com-edit.git "$HOME\.gemini\skills\powerdesigner-com-edit"
```

#### For Project-Local Repositories
Place the skill into your project's `.agents/skills` folder:
```bash
mkdir -p .agents/skills
git clone https://github.com/NekoCCN/powerdesigner-com-edit.git .agents/skills/powerdesigner-com-edit
```

### 3. Python Package & CLI Installation
If you also want to use the Python API or the `pd-edit` command-line tool directly in your terminal:
```bash
cd powerdesigner-com-edit
pip install -e .
```
Or install dependencies only:
```bash
pip install -r requirements.txt
```

---

## How Agents Use This Skill

Once installed, your coding assistant will automatically trigger this skill whenever you ask it to:
- Generate sequence diagrams with activation bars that do not overlap into solid black boxes.
- Create 3-column use case diagrams (Actors on left, Use Cases in center, External Systems on right).
- Build Physical Data Models (PDM) with primary keys, foreign key joins, and cardinality.
- Audit diagrams for AABB symbol overlaps or clean up leftover draft notes.
- Batch export cropped, high-resolution PNG diagrams for reports.

Example agent prompts:
- *"Use powerdesigner-com-edit to create a sequence diagram for our order checkout flow."*
- *"Check if any symbols or activation bars overlap in my_model.oom and fix them."*
- *"Build a PDM schema for our user and order tables with foreign key joins."*
- *"Export all diagrams in the current model to PNG with blank borders cropped."*

---

## Core Capabilities

- **Stack-Aware Activation Bar Alignment**: Tracks nested call depth and shifts concurrent activation bars horizontally (`X_offset = X_base + depth * 120`). Prevents overlapping calls from rendering as solid black blocks.
- **AABB Collision Detection & Spacing Audit**: Checks bounding boxes with clearance buffers (default 150 units). Finds colliding symbols and provides auto-relaxation algorithms.
- **Three-Column Use Case Layout**: Canonical layout with Primary Actors on the left (`X = 0`), Core Use Cases in the center (`X = 14,000`), and Secondary Systems on the right (`X = 28,000`).
- **Physical & Conceptual Models (PDM / CDM)**: Programmatic generation of tables, columns, primary keys, foreign key joins (`ReferenceJoin`), and multi-tier layout.
- **Class Diagram Hierarchy**: Builds classes, interfaces, attributes, methods with visibility markers (`+`, `-`, `#`), and association/inheritance links.
- **Smart Image Export**: Exports diagrams via COM and trims surrounding whitespace margins with NumPy and Pillow.
- **Draft Note Removal**: One-command cleanup for stray notes left behind during development (e.g. "实现中" or "待整链验收").

---

## Real-World Examples

### Example 1: Multi-Tier Microservice Sequence Diagram

Demonstrates a real-world cold-chain container allocation flow across Dispatcher, API Gateway, Allocation Service, Route Optimization Engine, and Database:

```python
from pd_com_edit import PowerDesignerClient, SequenceDiagramBuilder

client = PowerDesignerClient()
client.start(visible=True)

model = client.create_oom(name="ColdChainLogistics")
diag = model.SequenceDiagrams.CreateNew()
diag.Name = "Container Allocation Flow"

builder = SequenceDiagramBuilder(diag)

# Register lifelines across system layers
builder.add_lifeline("Dispatcher", is_actor=True)
builder.add_lifeline("APIGateway")
builder.add_lifeline("AllocationService")
builder.add_lifeline("RouteOptimizer")
builder.add_lifeline("ContainerDB")

# Message exchanges with nested activation stacking
builder.add_message("Dispatcher", "APIGateway", "allocateContainers(orderId, tempZone)", message_type="sync")
builder.add_message("APIGateway", "AllocationService", "POST /api/allocations", message_type="sync")

# Nested calls (depth = 1)
builder.add_message("AllocationService", "RouteOptimizer", "solveVRP(order, constraints)", message_type="sync")
builder.add_message("RouteOptimizer", "AllocationService", "optimalRoutePlan", message_type="reply")

# Database persistence (depth = 1)
builder.add_message("AllocationService", "ContainerDB", "lockAndAssign(containerIds)", message_type="sync")
builder.add_message("ContainerDB", "AllocationService", "assignmentCommitted", message_type="reply")

# Returns back to caller
builder.add_message("AllocationService", "APIGateway", "201 Created (summary)", message_type="reply")
builder.add_message("APIGateway", "Dispatcher", "renderAllocationSuccess()", message_type="reply")

# Apply stack-aware layout
builder.layout_diagram()
client.save_model(model, "cold_chain_allocation.oom")
```

### Example 2: Three-Column Use Case Layout

Organizes 3 human roles, 5 core use cases, and 3 external systems without crossing lines:

```python
from pd_com_edit import PowerDesignerClient, UseCaseDiagramBuilder

client = PowerDesignerClient()
client.start(visible=False)

model = client.create_oom(name="Hospital_UseCases")
diag = model.UseCaseDiagrams.Item(0)

builder = UseCaseDiagramBuilder(diag)

# Left column: Primary Actors (X = 0)
builder.add_actor("Patient", is_primary=True)
builder.add_actor("Doctor", is_primary=True)
builder.add_actor("Nurse", is_primary=True)

# Center column: Core Use Cases (X = 14,000)
builder.add_usecase("Register Online Appointment")
builder.add_usecase("Verify Insurance Coverage")
builder.add_usecase("Conduct Clinical Examination")
builder.add_usecase("Prescribe Medication")
builder.add_usecase("Discharge Patient")

# Right column: External Systems (X = 28,000)
builder.add_system("National Insurance API")
builder.add_system("Pharmacy Warehouse")
builder.add_system("SMS Notification Service")

# Connect relationships cleanly
builder.connect("Patient", "Register Online Appointment")
builder.connect("Patient", "Verify Insurance Coverage")
builder.connect("Verify Insurance Coverage", "National Insurance API")
builder.connect("Doctor", "Conduct Clinical Examination")
builder.connect("Doctor", "Prescribe Medication")
builder.connect("Prescribe Medication", "Pharmacy Warehouse")
builder.connect("Nurse", "Discharge Patient")
builder.connect("Discharge Patient", "SMS Notification Service")

builder.layout_three_column()
client.save_model(model, "hospital_usecases.oom")
```

### Example 3: Relational Database Schema with Foreign Keys

Generates a PostgreSQL Physical Data Model with lookup tables, business entities, transaction tables, and explicit foreign key joins:

```python
from pd_com_edit import PowerDesignerClient, PdmBuilder

client = PowerDesignerClient()
client.start(visible=False)

model = client.create_pdm(name="WarehouseSchema", dbms="PostgreSQL 12")
diag = model.PhysicalDiagrams.Item(0)

builder = PdmBuilder(model, diag)

# Table 1: Category (Lookup Table)
builder.add_table("Product Category", "t_category", [
    {"name": "Category ID", "code": "category_id", "type": "INTEGER", "pk": True},
    {"name": "Code", "code": "cat_code", "type": "VARCHAR(32)", "mandatory": True},
    {"name": "Name", "code": "cat_name", "type": "VARCHAR(128)", "mandatory": True}
], x=0, y=10000)

# Table 2: Product (Core Entity)
builder.add_table("Product", "t_product", [
    {"name": "Product ID", "code": "product_id", "type": "BIGINT", "pk": True},
    {"name": "SKU", "code": "sku", "type": "VARCHAR(64)", "mandatory": True},
    {"name": "Price", "code": "price", "type": "DECIMAL(12,2)", "mandatory": True},
    {"name": "Category ID", "code": "category_id", "type": "INTEGER", "mandatory": True}
], x=14000, y=10000)

# Table 3: Order Item (Transaction Table)
builder.add_table("Order Item", "t_order_item", [
    {"name": "Item ID", "code": "item_id", "type": "BIGINT", "pk": True},
    {"name": "Order ID", "code": "order_id", "type": "BIGINT", "mandatory": True},
    {"name": "Product ID", "code": "product_id", "type": "BIGINT", "mandatory": True},
    {"name": "Quantity", "code": "quantity", "type": "INTEGER", "mandatory": True}
], x=28000, y=10000)

# Establish Foreign Key Joins
builder.add_reference("Product Category", "Product", "category_id", "category_id", "FK_Product_Category")
builder.add_reference("Product", "Order Item", "product_id", "product_id", "FK_Item_Product")

builder.auto_layout()
client.save_model(model, "warehouse_schema.pdm")
```

### Example 4: Layout Audit & Whitespace-Cropped Export Pipeline

Audits an existing model for symbol collisions, cleans up draft notes, and batch-exports trimmed diagrams:

```python
from pd_com_edit import PowerDesignerClient, LayoutAuditor, CollisionDetector, ImageExporter

client = PowerDesignerClient()
client.start(visible=False)

model = client.open_model("lab_assignment.oom")

# Step 1: Strip draft notes left during modeling
cleaned = CollisionDetector.strip_draft_notes(model)
print(f"Removed {cleaned} draft annotations.")

# Step 2: Audit remaining diagrams for symbol overlaps
auditor = LayoutAuditor()
report = auditor.audit_model(model)
print(report.get_summary())

# Step 3: Batch export diagrams with auto-cropped margins
exporter = ImageExporter(output_dir="./exports", crop_margins=True, padding=20)
exported_files = exporter.export_model_diagrams(model)
for f in exported_files:
    print(f"Exported clean diagram: {f}")

client.save_model(model)
client.close_model(model)
```

---

## CLI Reference (`pd-edit`)

```bash
# Check model for symbol overlaps and draft notes
pd-edit audit --model path/to/model.oom

# Strip unapproved draft notes and save
pd-edit clean-notes --model path/to/model.oom --save

# Export diagrams to PNG and remove blank borders
pd-edit export --model path/to/model.oom --output-dir ./exports --crop

# Terminate hanging PowerDesigner processes
pd-edit kill-pd
```

---

## Project Structure

```
powerdesigner-com-edit/
├── SKILL.md                      # Agent Skill specification (Claude Code & Antigravity)
├── install.py                    # Multi-platform Agent Skill installer
├── install.ps1                   # PowerShell installer script
├── pd_com_edit/                  # Core Python package
│   ├── client.py                 # COM lifecycle and process safety
│   ├── collision.py              # AABB collision detector and auditor
│   ├── sequence.py               # Sequence builder with activation bar stacking
│   ├── usecase.py                # 3-column use case layout builder
│   ├── class_diagram.py          # Class diagram builder
│   ├── pdm.py                    # PDM tables, columns, references
│   ├── export.py                 # PNG export with Pillow/NumPy cropping
│   └── cli.py                    # pd-edit CLI tool
├── examples/                     # Ready-to-run examples
│   ├── 01_sequence_with_activation_bars.py
│   ├── 02_usecase_three_column_layout.py
│   ├── 03_pdm_database_schema.py
│   ├── 04_batch_diagram_auditor.py
│   ├── 05_cold_chain_allocation_pipeline.py
│   └── 06_domain_model_class_hierarchy.py
├── references/                   # Reference notes and cheat sheets
│   ├── com_api_cheatsheet.md
│   ├── overlap_detection_guide.md
│   ├── sequence_activation_guide.md
│   ├── pdm_database_modeling_guide.md
│   └── class_and_usecase_guide.md
├── scripts/
│   └── pd_automation.py          # Standalone all-in-one script
├── tests/
│   └── test_collision_detector.py# Offline unit tests
├── pyproject.toml
└── README.md
```

---

## 中文说明

`powerdesigner-com-edit` 既是一个标准的 **AI Agent Skill**（适配 Claude Code、Google Antigravity、Codex 等），也是一套可以通过 Windows COM 接口（`PowerDesigner.Application`）操控 SAP PowerDesigner 的 Python 工具库与命令行工具。

### Skill 安装与配置

#### 1. 一键安装
```bash
git clone https://github.com/NekoCCN/powerdesigner-com-edit.git
cd powerdesigner-com-edit

# 自动检测并安装到 Claude Code 和 Antigravity 全局 Skills 目录
python install.py
```
或在 Windows PowerShell 中直接运行：
```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

#### 2. 手动安装
- **Claude Code**：克隆到 `~/.claude/skills/powerdesigner-com-edit`
- **Google Antigravity / Gemini CLI**：克隆到 `~/.gemini/skills/powerdesigner-com-edit`
- **项目本地**：克隆到当前工程的 `.agents/skills/powerdesigner-com-edit`

安装后，AI 助手在收到与 PowerDesigner 建模、时序图排版、重叠检查、PDM 建表、图片导出相关的请求时，会自动调取本技能完成操作。

---

## License

MIT License. See [LICENSE](LICENSE) for details.
