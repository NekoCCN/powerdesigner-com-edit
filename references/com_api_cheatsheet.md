# PowerDesigner COM API Reference & Cheatsheet

## 1. Application & Model Management

### ProgID & Dispatch
```python
import win32com.client

# Connect to running instance or create new one
app = win32com.client.Dispatch("PowerDesigner.Application")
app.Visible = True  # or False for headless automation
```

### Model Creation & Opening
```python
# Model Type Constants (PdCommon / PdOOM / PdPDM / PdCDM)
cls_OOM = "{4BA9FBC0-D824-11D1-A1DF-0020AF12A261}"  # Object Oriented Model
cls_PDM = "{CDE44E21-3017-11D2-8A2D-00609756FE6C}"  # Physical Data Model
cls_CDM = "{9C84FDF4-9E0C-11D1-A1DE-0020AF12A261}"  # Conceptual Data Model

# Create Model
oom_model = app.CreateModel(cls_OOM, "|Language=Java|")
oom_model.SetName("ColdChainSystemModel")

# Open Existing Model
model = app.OpenModel(r"E:\path\to\model.oom")

# Save & Close
model.Save()
model.Close()
```

---

## 2. Diagram Symbols & Geometry Properties

In PowerDesigner COM, symbols expose bounding geometry:

```python
# Position is centered or top-left depending on symbol kind
sym.Position.X = 5000  # Horizontal coordinate (approx 100 units = 1 mm)
sym.Position.Y = -2500  # Inverted vertical coordinate (negative downward)

# Size
sym.Size.Width = 3200
sym.Size.Height = 1200

# Boundary corners:
left = sym.Position.X - sym.Size.Width // 2
right = sym.Position.X + sym.Size.Width // 2
top = sym.Position.Y + sym.Size.Height // 2
bottom = sym.Position.Y - sym.Size.Height // 2
```

---

## 3. Sequence Diagram & Messages

```python
# Create Message Object
msg = model.Messages.CreateNew()
msg.SetName("allocateContainer(orderId, containerId)")
msg.Sender = sender_lifeline_obj
msg.Receiver = receiver_lifeline_obj

# Create Message Symbol
msg_sym = diagram.AttachObject(msg)
msg_sym.SourcePoint.Y = -3500
msg_sym.DestinationPoint.Y = -3500

# Activation Symbol geometry
# Activation bars attach to lifelines and span between call and return Y coordinates
```

---

## 4. Symbol Styling & Native Colors

PowerDesigner colors are Windows `COLORREF` integers (`R + (G << 8) + (B << 16)`):

```python
def rgb(r, g, b):
  return r + (g << 8) + (b << 16)


NAVY_BORDER = rgb(40, 80, 160)
SOFT_BLUE_FILL = rgb(230, 240, 255)
WHITE = rgb(255, 255, 255)

symbol.LineColor = NAVY_BORDER
symbol.FillColor = SOFT_BLUE_FILL
symbol.BrushStyle = 0  # Solid
symbol.LineWidth = 1
```

---

## 5. Clean Diagram Exporting

```python
# Native COM Export (PNG, JPEG, EMF, BMP)
diagram.ExportImage(r"E:\output\diagram.png", "PNG")
```

---

## 6. Connectors & Association Links (AttachLinkObject vs AttachObject)

### Critical Distinction: 2D Symbols vs 1D Connectors
- **2D Shapes** (Actors, Use Cases, Classes, Tables):
  Use `diagram.AttachObject(obj)`.
- **1D Connectors & Lines** (Use Case Associations, Generalizations, Dependencies, Physical References):
  **MUST** use `diagram.AttachLinkObject(linkObj)` via `attach_link_symbol()`.
  Calling `AttachObject` on link objects silently returns `None` and draws 0 lines on the diagram.

### pywin32 Safe Dispatch Helper
Under pywin32, direct calls to `diagram.AttachLinkObject(link)` often trigger COM argument type coercion errors (`The Python instance can not be converted to a COM object`). Dispatching via `_oleobj_.Invoke` resolves this cleanly:

```python
import pythoncom
import win32com.client

def attach_link_symbol(diagram, link_obj):
    if hasattr(diagram, "_oleobj_") and pythoncom is not None:
        try:
            dispid = diagram._oleobj_.GetIDsOfNames("AttachLinkObject")
            ole_link = link_obj._oleobj_ if hasattr(link_obj, "_oleobj_") else link_obj
            res = diagram._oleobj_.Invoke(dispid, 0, pythoncom.DISPATCH_METHOD, True, ole_link)
            return win32com.client.dynamic.Dispatch(res)
        except Exception:
            pass
    if hasattr(diagram, "AttachLinkObject"):
        return diagram.AttachLinkObject(link_obj)
    return diagram.AttachObject(link_obj)
```

### Native Object Kinds & Endpoint Properties

| Diagram Element | Native Kind Int | Endpoint 1 Property | Endpoint 2 Property | Attachment Method |
|---|---|---|---|---|
| Actor | `403775745` | N/A | N/A | `AttachObject` |
| Use Case | `403775746` | N/A | N/A | `AttachObject` |
| UseCase Association | `403775603` | `Object1` (Actor) | `Object2` (UseCase) | `AttachLinkObject` |
| UseCase Dependency | `403775593` | `Object1` (Source UC) | `Object2` (Target UC) | `AttachLinkObject` |
| Class | `403775587` | N/A | N/A | `AttachObject` |
| Interface | `403775588` | N/A | N/A | `AttachObject` |
| Generalization | `403775592` | `Child` / `Object1` | `Parent` / `Object2` | `AttachLinkObject` |
| Class Association | `403775594` | `ClassA` / `Object1` | `ClassB` / `Object2` | `AttachLinkObject` |
| PDM Table | Collection | N/A | N/A | `AttachObject` |
| PDM Reference | Collection | `ParentTable` / `Object1` | `ChildTable` / `Object2` | `AttachLinkObject` |

