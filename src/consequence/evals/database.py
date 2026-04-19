"""Evaluation suite for the built-in database / lookup MCP server."""

from __future__ import annotations

from consequence.eval import EvalSuite
from consequence.servers.database import make_database_server
from consequence.types import EvalTask

database_suite = EvalSuite(
    name="database",
    server_factory=make_database_server,
    tasks=[
        EvalTask(
            id="db_get_product",
            description="Agent retrieves a product by ID",
            user_message="What is the price of product P002?",
            expected_output="24.99",
            expected_tool_names=["get_product"],
        ),
        EvalTask(
            id="db_check_stock_in",
            description="Agent checks stock for an in-stock product",
            user_message="Is product P001 in stock?",
            expected_output="yes",
            expected_tool_names=["check_stock"],
        ),
        EvalTask(
            id="db_check_stock_out",
            description="Agent identifies an out-of-stock product",
            user_message="Is product P004 available?",
            expected_output="no",
            expected_tool_names=["check_stock"],
        ),
        EvalTask(
            id="db_search_products",
            description="Agent searches products by name keyword",
            user_message="Search for products with 'gadget' in the name.",
            expected_output="Gadget B",
            expected_tool_names=["search_products"],
        ),
        EvalTask(
            id="db_get_employee",
            description="Agent retrieves employee info by ID",
            user_message="What department does employee E002 work in?",
            expected_output="Marketing",
            expected_tool_names=["get_employee"],
        ),
        EvalTask(
            id="db_list_by_department",
            description="Agent lists employees in a specific department",
            user_message="List all employees in the Engineering department.",
            expected_output="Alice",
            expected_tool_names=["list_employees_by_department"],
        ),
        EvalTask(
            id="db_missing_product",
            description="Agent handles a missing product lookup gracefully",
            user_message="Get details for product P999.",
            expected_tool_names=["get_product"],
        ),
    ],
)
