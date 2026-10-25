# PowerDesigner Sequence Diagram & Activation Bar Guide

This guide provides technical specifications, coordinate rules, and COM manipulation instructions for generating sequence diagrams in SAP PowerDesigner with exact, collision-free activation bars (execution specifications) and interaction fragments (`alt`, `opt`, `loop`).

---

## 1. Sequence Diagram Architecture in PowerDesigner

In SAP PowerDesigner 16.5+, Sequence Diagrams are part of the Object-Oriented Model (OOM).

### Core COM Classes & Stereotypes
| Concept | COM Object / Metaclass | Visual Symbol Class | Note |
| :--- | :--- | :--- | :--- |
| **Actor** | `Actor` | `ActorSymbol` | Leftmost or initiator lifelines |
| **Lifeline / Object** | `SequenceDiagramObject` | `SequenceDiagramObjectSymbol` | Target objects or services |
| **Message** | `Message` | `MessageSymbol` | Synchronous (`Call`), Asynchronous (`Send`), Return (`Reply`) |
| **Combined Fragment**| `InteractionFragment` | `InteractionFragmentSymbol` | `alt`, `opt`, `loop`, `par` frames |
| **Operand / Branch** | `InteractionOperand` | Child partition inside fragment | Guard conditions like `[valid == true]` |

---

## 2. The Activation Bar Overlap Problem

### Why Activation Bars Overlap
When multiple synchronous calls or nested self-calls target the same lifeline without explicit depth coordinates:
1. PowerDesigner defaults activation bar width to approx 300 - 400 units and centers it directly over the lifeline's center axis (`X_lifeline`).
2. If nested activations occur simultaneously, they render at the exact same X coordinate, appearing as an illegible, thick black solid block.

### The Nested Stack Coordinate Calculation
To create visually distinct activation tiers (nesting / recursion / callback):
1. **Lifeline Center Axis**: `X_lifeline`
2. **Base Activation Width**: `W_act = 240` units
3. **Activation Horizontal Offset**:
   `X_center(depth) = X_lifeline + depth * 120`
   Where:
   - `depth = 0`: Top-level call on this lifeline (centered).
   - `depth = 1`: First nested call received while previous is active (+120 units).
   - `depth = 2`: Further re-entrant or nested call (+240 units).

### Vertical Spacing & Ordering
- **Header Margin**: Top lifeline symbols at `Y = 5,000`.
- **First Message**: Starts at `Y = 3,500`.
- **Step Interval**: `step_y = -1,800` to `-2,400` units per exchange (message + reply).
- **Minimum Activation Length**: `min_len = 1,200` units (ensures legible vertical span).

---

## 3. Combined Fragment Calculation (`alt` / `opt` / `loop`)

Interaction fragments must visually enclose all messages and lifelines participating in the conditional block.

### Bounding Calculation
Given a subset of lifelines and messages inside an alt branch:

```text
X_left   = min(lifeline.left) - pad_x
X_right  = max(lifeline.right) + pad_x
Y_top    = max(message.y) + pad_y
Y_bottom = min(message.y) - pad_y
```

Recommended padding:
- `pad_x = 1,200` units (clears lifeline text and activation bars)
- `pad_y = 800` units (clears message text and arrowheads)

### Partitioning `alt` Operands
For an `alt` fragment with `k` branches (e.g. Success vs. Failure):
- Divider lines are placed at equal vertical intervals:
  `Y_div_i = Y_top - i * (Y_top - Y_bottom) / k`
- Guard conditions (e.g. `[Credentials Valid]`, `[User Not Found]`) are positioned top-left of each operand quadrant with a `+200` unit vertical offset.

---

## 4. COM Implementation Reference

```python
from pd_com_edit import PowerDesignerClient, SequenceDiagramBuilder

client = PowerDesignerClient()
client.start(visible=True)
model = client.create_oom(name="OrderProcessing_OOM")
diag = model.SequenceDiagrams.CreateNew()
diag.Name = "Order Checkout Flow"

builder = SequenceDiagramBuilder(diag)
u = builder.add_lifeline("Customer", is_actor=True)
web = builder.add_lifeline("WebStore")
pay = builder.add_lifeline("PaymentGateway")
inv = builder.add_lifeline("InventoryService")

# Add message flow with automatic activation bar tracking
builder.add_message("Customer", "WebStore", "submitOrder(cart)", message_type="sync")
builder.add_message("WebStore", "InventoryService", "reserveStock(items)", message_type="sync")
builder.add_message("InventoryService", "WebStore", "stockReserved", message_type="reply")
builder.add_message("WebStore", "PaymentGateway", "charge(amount)", message_type="sync")
builder.add_message("PaymentGateway", "WebStore", "chargeSuccess", message_type="reply")
builder.add_message("WebStore", "Customer", "orderConfirmed", message_type="reply")

builder.layout_diagram()
client.save_model(model, "order_flow.oom")
```
