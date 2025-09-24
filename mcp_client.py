#!/usr/bin/env python3
"""
Simple MCP Client
This client connects to MCP servers and provides a simple interface to interact with them.
"""

import json
import subprocess
import sys
import time
from typing import Dict, Any, Optional

class MCPClient:
    def __init__(self, server_command: str):
        self.server_command = server_command
        self.process = None
        self.request_id = 1
        
    def start_server(self):
        """Start the MCP server process"""
        try:
            self.process = subprocess.Popen(
                self.server_command.split(),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0
            )
            print("✅ MCP Server started successfully!")
            time.sleep(0.5)  # Give server time to start
            return True
        except Exception as e:
            print(f"❌ Failed to start server: {e}")
            return False
    
    def send_request(self, method: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Send a JSON-RPC request to the server"""
        if not self.process:
            raise RuntimeError("Server not started")
        
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method
        }
        
        if params:
            request["params"] = params
        
        self.request_id += 1
        
        # Send request
        request_json = json.dumps(request) + "\n"
        self.process.stdin.write(request_json)
        self.process.stdin.flush()
        
        # Read response
        response_line = self.process.stdout.readline()
        if not response_line:
            raise RuntimeError("No response from server")
        
        return json.loads(response_line.strip())
    
    def initialize(self) -> bool:
        """Initialize the MCP connection"""
        try:
            response = self.send_request("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "simple-mcp-client",
                    "version": "1.0.0"
                }
            })
            
            if "result" in response:
                print("🤝 MCP connection initialized!")
                return True
            else:
                print(f"❌ Initialization failed: {response}")
                return False
                
        except Exception as e:
            print(f"❌ Initialization error: {e}")
            return False
    
    def list_tools(self) -> list:
        """Get list of available tools"""
        try:
            response = self.send_request("tools/list")
            if "result" in response:
                return response["result"]["tools"]
            else:
                print(f"❌ Failed to list tools: {response}")
                return []
        except Exception as e:
            print(f"❌ Error listing tools: {e}")
            return []
    
    def call_tool(self, tool_name: str, arguments: Dict) -> str:
        """Call a tool with given arguments"""
        try:
            response = self.send_request("tools/call", {
                "name": tool_name,
                "arguments": arguments
            })
            
            if "result" in response:
                content = response["result"]["content"]
                if content and len(content) > 0:
                    return content[0]["text"]
                return "No content returned"
            else:
                return f"Error: {response.get('error', {}).get('message', 'Unknown error')}"
                
        except Exception as e:
            return f"Error calling tool: {e}"
    
    def stop_server(self):
        """Stop the MCP server"""
        if self.process:
            self.process.terminate()
            self.process.wait()
            print("🛑 Server stopped")
    
    def interactive_session(self):
        """Run an interactive session with the MCP server"""
        print("\n🎯 MCP Interactive Session")
        print("Commands:")
        print("  list - Show available tools")
        print("  ls <path> - List files in directory")
        print("  cat <file> - Read file contents")
        print("  quit - Exit")
        print("-" * 40)
        
        while True:
            try:
                command = input("\nmcp> ").strip()
                
                if not command:
                    continue
                
                if command == "quit":
                    break
                
                elif command == "list":
                    tools = self.list_tools()
                    print("\n📋 Available Tools:")
                    for tool in tools:
                        print(f"  • {tool['name']}: {tool['description']}")
                
                elif command.startswith("ls "):
                    path = command[3:].strip() or "."
                    result = self.call_tool("list_files", {"path": path})
                    print(f"\n{result}")
                
                elif command.startswith("cat "):
                    filepath = command[4:].strip()
                    if not filepath:
                        print("❌ Please provide a file path")
                        continue
                    result = self.call_tool("read_file", {"path": filepath})
                    print(f"\n{result}")
                
                elif command == "ls":
                    result = self.call_tool("list_files", {"path": "."})
                    print(f"\n{result}")
                
                else:
                    print("❌ Unknown command. Type 'quit' to exit.")
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

def main():
    # You can change this to point to your server script
    server_command = "python3 file_directory_mcp_server.py"  # Adjust path as needed
    
    client = MCPClient(server_command)
    
    try:
        print("🚀 Starting MCP Client Demo")
        
        if not client.start_server():
            return
        
        if not client.initialize():
            return
        
        # Show available tools
        tools = client.list_tools()
        print(f"\n📋 Found {len(tools)} tools:")
        for tool in tools:
            print(f"  • {tool['name']}")
        
        # Demo: List current directory
        print(f"\n📁 Demo: Listing current directory")
        result = client.call_tool("list_files", {"path": "."})
        print(result)
        
        # Start interactive session
        client.interactive_session()
        
    except KeyboardInterrupt:
        print("\n👋 Interrupted by user")
    finally:
        client.stop_server()

if __name__ == "__main__":
    main()