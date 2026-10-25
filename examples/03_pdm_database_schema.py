"""
Example 03: Physical Data Model (PDM) Relational Schema Builder
Demonstrates creating tables, columns, primary keys, and foreign keys with tiered layout.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pd_com_edit import PowerDesignerClient, PdmBuilder


def main():
    print("[1/4] Connecting to SAP PowerDesigner...")
    client = PowerDesignerClient()
    client.start(visible=True)

    print("[2/4] Initializing Physical Data Model (PDM) for PostgreSQL...")
    model = client.create_pdm(name="ECommerce_Warehouse", dbms="PostgreSQL 12")
    diag = model.PhysicalDiagrams.Item(0)

    print("[3/4] Defining Tables, Columns, and Constraints...")
    builder = PdmBuilder(model, diag)

    # 1. Lookup Table: Category
    builder.add_table(
        name="Product Category",
        code="t_category",
        columns=[
            {"name": "Category ID", "code": "category_id", "type": "INTEGER", "pk": True},
            {"name": "Category Code", "code": "cat_code", "type": "VARCHAR(32)", "mandatory": True},
            {"name": "Display Name", "code": "display_name", "type": "VARCHAR(128)", "mandatory": True}
        ],
        x=0, y=10000
    )

    # 2. Main Table: Products
    builder.add_table(
        name="Product Item",
        code="t_product",
        columns=[
            {"name": "Product ID", "code": "product_id", "type": "BIGINT", "pk": True},
            {"name": "SKU Number", "code": "sku", "type": "VARCHAR(64)", "mandatory": True},
            {"name": "Unit Price", "code": "unit_price", "type": "DECIMAL(12,2)", "mandatory": True},
            {"name": "Category ID", "code": "category_id", "type": "INTEGER", "mandatory": True}
        ],
        x=14000, y=10000
    )

    # 3. Transaction Table: Order Lines
    builder.add_table(
        name="Order Item Line",
        code="t_order_item",
        columns=[
            {"name": "Line Item ID", "code": "line_id", "type": "BIGINT", "pk": True},
            {"name": "Order ID", "code": "order_id", "type": "BIGINT", "mandatory": True},
            {"name": "Product ID", "code": "product_id", "type": "BIGINT", "mandatory": True},
            {"name": "Quantity", "code": "quantity", "type": "INTEGER", "mandatory": True}
        ],
        x=28000, y=10000
    )

    # Foreign Keys
    builder.add_reference(
        parent_table="Product Category",
        child_table="Product Item",
        parent_col="category_id",
        child_col="category_id",
        name="FK_Product_Category"
    )

    builder.add_reference(
        parent_table="Product Item",
        child_table="Order Item Line",
        parent_col="product_id",
        child_col="product_id",
        name="FK_OrderItem_Product"
    )

    print("[4/4] Executing Collision-Free PDM Tiered Layout...")
    builder.auto_layout()

    output_path = os.path.abspath("ecommerce_warehouse.pdm")
    client.save_model(model, output_path)
    print(f"Done! Saved PDM to: {output_path}")


if __name__ == "__main__":
    main()
