import json
import ollama
import asyncio
import sys
from contextlib import AsyncExitStack
from mcp import ClientSession
from mcp.client.sse import sse_client

# Configuration
OLLAMA_MODEL = "llama3.2"
# FastMCP SSE default endpoint appends /sse
MCP_SERVER_URL = "http://127.0.0.1:9090/sse"

# ------------------------------------------------------------
# Main conversation loop
# ------------------------------------------------------------
async def main(user_msg):
    # Use AsyncExitStack to manage the SSE connection lifecycle
    async with AsyncExitStack() as stack:
        print("🔍 Connecting to MCP server...")
        
        try:
            # 1. Connect to SSE Transport
            streams = await stack.enter_async_context(sse_client(MCP_SERVER_URL))
            
            # 2. Open Client Session
            session = await stack.enter_async_context(ClientSession(streams[0], streams[1]))
            await session.initialize()
        except Exception as e:
            print(f"❌ ERROR connecting to MCP server: {e}")
            print(f"\nMake sure the server is running: python server.py")
            sys.exit(1)

        # 3. Discover Tools
        print("🔍 Loading MCP tools...")
        tools_list = await session.list_tools()
        
        # Convert to format Ollama understands
        ollama_tools = []
        for tool in tools_list.tools:
            ollama_tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema,
                },
            })

        print(f"✅ Loaded {len(ollama_tools)} tools:")
        for tool in ollama_tools:
            print(f"   - {tool['function']['name']}: {tool['function']['description']}")
        print()
        
        print(f"👤 User: {user_msg}\n")

        # 4. First Ollama Call
        try:
            response = ollama.chat(
                model=OLLAMA_MODEL,
                messages=[{"role": "user", "content": user_msg}],
                tools=ollama_tools,
                stream=False,
            )
        except Exception as e:
            print(f"❌ ERROR calling Ollama: {e}")
            sys.exit(1)

        # Check: Did AI want to use tools?
        if not response.get("message", {}).get("tool_calls"):
            print("🤖 AI answered directly (no tools needed):")
            print(response["message"]["content"])
            return

        # 5. Process tool calls
        messages = [
            {"role": "user", "content": user_msg},
            response["message"]
        ]

        for tool_call in response["message"]["tool_calls"]:
            tool_name = tool_call["function"]["name"]
            args = tool_call["function"]["arguments"]

            # Parse if arguments are JSON string
            if isinstance(args, str):
                args = json.loads(args)

            print(f"🔧 Tool requested: {tool_name}")
            print(f"📝 Arguments: {args}")

            # Execute the tool via the active session
            try:
                result = await session.call_tool(tool_name, arguments=args)
                # Extract text content from MCP result
                tool_result = "".join([c.text for c in result.content if getattr(c, 'type', '') == 'text'])
                print(f"✅ Tool returned data successfully.\n")
            except Exception as e:
                print(f"❌ ERROR executing tool {tool_name}: {e}")
                tool_result = f"Error: {str(e)}"

            # Add tool response to conversation
            messages.append({
                "role": "tool",
                "content": tool_result,
            })

        # 6. Send tool results back to AI for final answer
        print("🤖 Generating Final AI response...\n")
        final = ollama.chat(
            model=OLLAMA_MODEL,
            messages=messages,
        )

        print("=======================")
        print(final["message"]["content"])
        print("=======================")

if __name__ == "__main__":
    user_msg = input("Enter a GitHub related query (e.g., create/delete github repo): ")
    asyncio.run(main(user_msg))