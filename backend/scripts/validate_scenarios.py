import asyncio
import re
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings
from app.llm.tools import format_tool_result
from app.mcp.client import McpClient

TEST_EMAIL = "donaldgarcia@example.net"
TEST_PIN = "7912"


async def main() -> None:
    client = McpClient(get_settings().mcp_server_url)

    safe_print("Scenario: product availability")
    products = await client.call_tool("search_products", {"query": "monitor"})
    safe_print(format_tool_result(products), limit=2200)
    safe_print("")

    safe_print("Scenario: customer authentication")
    auth = await client.call_tool(
        "verify_customer_pin",
        {"email": TEST_EMAIL, "pin": TEST_PIN},
    )
    auth_text = format_tool_result(auth)
    safe_print(auth_text)
    safe_print("")

    customer_id = _extract_customer_id(auth_text)
    if not customer_id:
        raise SystemExit("Could not extract customer ID from auth response")

    safe_print("Scenario: order history")
    orders = await client.call_tool("list_orders", {"customer_id": customer_id})
    safe_print(format_tool_result(orders))


def _extract_customer_id(text: str) -> str | None:
    match = re.search(r"Customer ID:\s*([a-f0-9-]+)", text, flags=re.IGNORECASE)
    return match.group(1) if match else None


def safe_print(text: str, limit: int | None = None) -> None:
    value = text if limit is None else text[:limit]
    print(value.encode("ascii", "backslashreplace").decode())


if __name__ == "__main__":
    asyncio.run(main())
