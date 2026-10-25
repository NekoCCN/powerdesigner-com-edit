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
