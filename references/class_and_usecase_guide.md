# PowerDesigner Class & Use Case Diagram Layout Guide

This guide covers structured generation, positioning heuristics, and collision avoidance rules for UML Class Diagrams and Use Case Diagrams in SAP PowerDesigner.

---

## 1. Use Case Diagram: The 3-Column Canonical Layout

A common pitfall in automated UML generation is the "spaghetti web" where actors and use cases are scattered randomly. The **3-Column Architecture** cleanly separates roles, primary tasks, and external integrations.

```
+-------------------+      +-------------------------+      +--------------------+
|  PRIMARY ACTORS   |      |   SYSTEM USE CASES      |      | SECONDARY SYSTEMS  |
|                   |      |                         |      |                    |
|   [Registered]    | ---> |    (Search Catalog)     |      |    [SMS Gateway]   |
|      User         |      |    (Place Order)        | ---> |                    |
|                   |      |    (View Order History) |      |   [Stripe Payment] |
|     [System]      | ---> |                         |      |                    |
|      Admin        |      |    (Manage Inventory)   |      |                    |
+-------------------+      +-------------------------+      +--------------------+
     X = 0                      X = 14,000                       X = 28,000
```

### Coordinate Heuristics
1. **Left Column (Primary Human Actors)**:
   - Centered around `X = 0`.
   - Vertical step: `step_y = -6,000` to `-8,000` units.
2. **Center Column (Core Use Cases)**:
   - Centered around `X = 14,000`.
   - Vertical step: `step_y = -3,500` to `-4,500` units.
   - Use cases with `<<include>>` or `<<extend>>` can be offset by `+4,000` units horizontally (`X = 18,000`) to represent child tiers.
3. **Right Column (External / Secondary Systems)**:
   - Centered around `X = 28,000`.
   - Vertical step: `step_y = -6,000` to `-8,000` units.

---

## 2. UML Class Diagram: Layered Hierarchy Layout

Class diagrams should reflect architectural layering (e.g., Domain Entity -> Repository -> Service -> Controller) or Inheritance Trees (Superclass -> Subclasses).

### Top-Down Inheritance Hierarchy
- **Level 0 (Base Classes / Interfaces)**: Top tier (`Y = 15,000`).
- **Level 1 (Direct Subclasses / Concrete Impls)**: Middle tier (`Y = 8,000`).
- **Level 2 (Specialized Subclasses / Adapters)**: Lower tier (`Y = 1,000`).

### Horizontal Distribution
For `N` classes on the same level:
`X_i = -((N - 1) * gap_x) / 2 + i * gap_x`
Where `gap_x = 10,000` units for classes with up to 8 attributes/methods.

### Class Box Dimension Rules
PowerDesigner symbols auto-size or clip text based on width and height:
- Width: `W_class = max(6000, max_str_len * 180)`
- Height: `H_class = 1200 + 380 * (num_attributes + num_operations)`

---

## 3. Relationship Styling Best Practices

| Relationship | PowerDesigner Metaclass | Line Style | Arrowhead |
| :--- | :--- | :--- | :--- |
| **Association** | `Association` | Solid (0) | None or simple open arrow |
| **Generalization** | `Generalization` | Solid (0) | Closed hollow triangle pointing to parent |
| **Realization / Implements**| `Realization` | Dashed (2) | Closed hollow triangle pointing to interface |
| **Dependency / Include / Extend**| `Dependency` | Dashed (2) | Open arrow with stereotype label |

---

## 4. Automation Snippet

```python
from pd_com_edit import PowerDesignerClient, UseCaseDiagramBuilder

client = PowerDesignerClient()
client.start(visible=False)
model = client.create_oom(name="ECommerce_UseCases")
diag = model.UseCaseDiagrams.Item(0)

builder = UseCaseDiagramBuilder(diag)
builder.add_actor("Customer", is_primary=True)
builder.add_actor("Administrator", is_primary=True)

builder.add_usecase("Browse Catalog")
builder.add_usecase("Checkout Order")
builder.add_usecase("Manage Products")

builder.add_system("Payment Gateway")

builder.connect("Customer", "Browse Catalog")
builder.connect("Customer", "Checkout Order")
builder.connect("Checkout Order", "Payment Gateway")
builder.connect("Administrator", "Manage Products")

builder.layout_three_column()
client.save_model(model, "usecases.oom")
```
