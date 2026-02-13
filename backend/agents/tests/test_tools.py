"""Tests for tool registry."""
from django.test import TestCase
from agents.tools_registry import (
    get_market_tools,
    get_behavior_tools,
    get_content_tools,
    get_copytrading_tools,
    get_trading_tools,
    execute_tool,
    TOOL_FUNCTIONS,
)


class ToolRegistryTest(TestCase):
    def test_all_tool_getters_return_lists(self):
        for getter in [get_market_tools, get_behavior_tools, get_content_tools, get_copytrading_tools, get_trading_tools]:
            tools = getter()
            self.assertIsInstance(tools, list)
            self.assertGreater(len(tools), 0, f"{getter.__name__} returned empty list")

    def test_tool_schema_format(self):
        """Each tool must have type=function and a function dict with name, description, parameters."""
        all_tools = (
            get_market_tools()
            + get_behavior_tools()
            + get_content_tools()
            + get_copytrading_tools()
            + get_trading_tools()
        )
        for tool in all_tools:
            self.assertEqual(tool["type"], "function")
            func = tool["function"]
            self.assertIn("name", func)
            self.assertIn("description", func)
            self.assertIn("parameters", func)
            self.assertIn("type", func["parameters"])
            self.assertEqual(func["parameters"]["type"], "object")

    def test_all_registered_tools_are_callable(self):
        for name, func in TOOL_FUNCTIONS.items():
            self.assertTrue(callable(func), f"Tool {name} is not callable")

    def test_all_tool_names_are_registered(self):
        """Every tool name defined in schemas must exist in TOOL_FUNCTIONS."""
        all_tools = (
            get_market_tools()
            + get_behavior_tools()
            + get_content_tools()
            + get_copytrading_tools()
            + get_trading_tools()
        )
        for tool in all_tools:
            name = tool["function"]["name"]
            self.assertIn(name, TOOL_FUNCTIONS, f"Tool {name} is in schema but not in TOOL_FUNCTIONS")

    def test_execute_unknown_tool(self):
        result = execute_tool("nonexistent_tool", {})
        self.assertIn("error", result)

    def test_tool_count(self):
        """Verify we have the expected number of tools."""
        self.assertEqual(len(get_market_tools()), 6)
        self.assertEqual(len(get_behavior_tools()), 3)
        self.assertEqual(len(get_content_tools()), 2)
        self.assertEqual(len(get_copytrading_tools()), 5)
        self.assertEqual(len(get_trading_tools()), 4)
        # 6 market + 3 behavior + 3 content (incl. format_for_platform) + 5 copytrading + 4 trading = 21
        self.assertEqual(len(TOOL_FUNCTIONS), 21)
