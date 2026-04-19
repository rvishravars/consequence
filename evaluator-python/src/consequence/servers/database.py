"""A mock database / lookup MCP server for use in evaluations."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

_PRODUCTS: dict[str, dict] = {
    "P001": {"name": "Widget A", "price": 9.99, "stock": 142},
    "P002": {"name": "Gadget B", "price": 24.99, "stock": 37},
    "P003": {"name": "Doohickey C", "price": 4.49, "stock": 500},
    "P004": {"name": "Thingamajig D", "price": 49.99, "stock": 0},
}

_EMPLOYEES: dict[str, dict] = {
    "E001": {"name": "Alice Smith", "department": "Engineering", "level": "Senior"},
    "E002": {"name": "Bob Jones", "department": "Marketing", "level": "Manager"},
    "E003": {"name": "Carol White", "department": "Engineering", "level": "Junior"},
}


def make_database_server() -> FastMCP:
    """Return a fresh FastMCP server with mock database lookup tools."""
    mcp = FastMCP("database")

    @mcp.tool()
    def get_product(product_id: str) -> dict:
        """Retrieve product details by product ID (e.g. 'P001')."""
        product = _PRODUCTS.get(product_id.upper())
        if product is None:
            return {"error": f"Product '{product_id}' not found"}
        return {"id": product_id.upper(), **product}

    @mcp.tool()
    def search_products(query: str) -> list[dict]:
        """Search products by name (case-insensitive substring match)."""
        query_lower = query.lower()
        return [
            {"id": pid, **info}
            for pid, info in _PRODUCTS.items()
            if query_lower in info["name"].lower()
        ]

    @mcp.tool()
    def check_stock(product_id: str) -> dict:
        """Return the current stock level for a product."""
        product = _PRODUCTS.get(product_id.upper())
        if product is None:
            return {"error": f"Product '{product_id}' not found"}
        return {
            "id": product_id.upper(),
            "name": product["name"],
            "in_stock": product["stock"] > 0,
            "stock": product["stock"],
        }

    @mcp.tool()
    def get_employee(employee_id: str) -> dict:
        """Retrieve employee information by employee ID (e.g. 'E001')."""
        employee = _EMPLOYEES.get(employee_id.upper())
        if employee is None:
            return {"error": f"Employee '{employee_id}' not found"}
        return {"id": employee_id.upper(), **employee}

    @mcp.tool()
    def list_employees_by_department(department: str) -> list[dict]:
        """List all employees in the given department (case-insensitive)."""
        dept_lower = department.lower()
        return [
            {"id": eid, **info}
            for eid, info in _EMPLOYEES.items()
            if info["department"].lower() == dept_lower
        ]

    return mcp
