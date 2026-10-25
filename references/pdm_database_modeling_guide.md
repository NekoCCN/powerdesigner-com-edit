# PowerDesigner Physical Data Model (PDM) & CDM Automation Guide

This guide details programmatic modeling of relational databases, entity-relationship diagrams, primary/foreign keys, and layout strategies using SAP PowerDesigner's COM interface.

---

## 1. PDM Object Hierarchy & COM API

In PowerDesigner, a Physical Data Model (`PdPDM.Model`) targets a specific DBMS (e.g., PostgreSQL, MySQL, Oracle, Microsoft SQL Server).

```
Model (PdPDM.Model)
 ├── Tables (PdPDM.Table)
 │    ├── Columns (PdPDM.Column)
 │    │    ├── Name, Code, DataType, Length, Precision
 │    │    ├── Mandatory (Boolean)
 │    │    └── PrimaryKey (Boolean)
 │    ├── Keys (PdPDM.Key)
 │    └── Indexes (PdPDM.Index)
 ├── References (PdPDM.Reference)
 │    ├── ParentTable, ChildTable
 │    ├── Joins (PdPDM.ReferenceJoin)
 │    │    ├── ParentTableColumn
 │    │    └── ChildTableColumn
 │    └── Cardinality ("0..*", "1..*", "0..1", "1..1")
 └── PhysicalDiagrams (PdPDM.PhysicalDiagram)
      └── Symbols (TableSymbol, ReferenceSymbol)
```

---

## 2. Table & Column COM Creation

### Creating a Table
```python
table = model.Tables.CreateNew()
table.Name = "User Account"
table.Code = "t_user_account"
table.Comment = "Stores registered user credentials and audit dates"
```

### Adding Columns & Specifying Types
```python
# Primary Key
col_id = table.Columns.CreateNew()
col_id.Name = "User ID"
col_id.Code = "user_id"
col_id.DataType = "BIGINT"
col_id.Primary = True
col_id.Mandatory = True

# Standard Attributes
col_email = table.Columns.CreateNew()
col_email.Name = "Email Address"
col_email.Code = "email"
col_email.DataType = "VARCHAR(255)"
col_email.Mandatory = True

# Foreign Key
col_dept = table.Columns.CreateNew()
col_dept.Name = "Department ID"
col_dept.Code = "dept_id"
col_dept.DataType = "INTEGER"
col_dept.Mandatory = False
```

---

## 3. Creating Foreign Key References

To establish an explicit Foreign Key relationship in PowerDesigner:
1. Create a `Reference` object on the model.
2. Assign `ParentTable` and `ChildTable`.
3. Create a `ReferenceJoin` mapping the parent column to child column.
4. Set Update/Delete constraints (Cascade, Restrict, Set Null).

```python
ref = model.References.CreateNew()
ref.Name = "FK_User_Department"
ref.Code = "fk_user_dept"
ref.ParentTable = dept_table
ref.ChildTable = user_table
ref.Cardinality = "0..*"
ref.UpdateConstraint = 1  # 1 = Cascade, 2 = Restrict, 3 = Set Null
ref.DeleteConstraint = 2

join = ref.Joins.CreateNew()
join.ParentTableColumn = dept_table.Columns.Item("dept_id")
join.ChildTableColumn = user_table.Columns.Item("dept_id")
```

---

## 4. Automatic Collision-Free Layout for PDM

Database schemas suffer heavily from overlapping table boxes and criss-crossing relationship lines if dumped at coordinates $(0, 0)$.

### Recommended Tiered Grid Layout
Organize tables by dependency level (Foreign Key DAG topology):
1. **Tier 0 (Root Dictionaries / Independent Lookup Tables)**:
   - Place in Column 0 (`X = 0`).
2. **Tier 1 (Core Business Entities)**:
   - Place in Column 1 (`X = 14,000`).
3. **Tier 2 (Transaction / History / Line Items)**:
   - Place in Column 2 (`X = 28,000`).

### Vertical Stacking & Margin Rules
- **Table Box Dimensions**:
  - Width: `6,500` to `8,000` units
  - Height: `1,200 + 450 * number_of_columns` units
- **Vertical Spacing**: Maintain a gap of at least `2,500` units between consecutive tables in the same column to leave clear channels for orthogonal reference lines.

---

## 5. Using `PdmBuilder`

```python
from pd_com_edit import PowerDesignerClient, PdmBuilder

client = PowerDesignerClient()
client.start(visible=False)
model = client.create_pdm(name="ECommerce_Database", dbms="PostgreSQL 12")
diag = model.PhysicalDiagrams.Item(0)

builder = PdmBuilder(model, diag)

# Table 1: Departments
builder.add_table("Department", "t_department", [
    {"name": "ID", "code": "dept_id", "type": "INTEGER", "pk": True},
    {"name": "Title", "code": "dept_name", "type": "VARCHAR(100)", "mandatory": True}
], x=0, y=10000)

# Table 2: Employees
builder.add_table("Employee", "t_employee", [
    {"name": "ID", "code": "emp_id", "type": "INTEGER", "pk": True},
    {"name": "Name", "code": "full_name", "type": "VARCHAR(100)"},
    {"name": "DeptID", "code": "dept_id", "type": "INTEGER"}
], x=15000, y=10000)

builder.add_reference(
    parent_table="Department",
    child_table="Employee",
    parent_col="dept_id",
    child_col="dept_id",
    name="FK_Emp_Dept"
)

builder.auto_layout()
client.save_model(model, "company_schema.pdm")
```
