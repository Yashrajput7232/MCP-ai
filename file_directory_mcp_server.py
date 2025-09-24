
"""
Simple MCP Server for File Management
This server provides tools to list and read files in a directory.
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, List

class MCPServer:
    def __init__(self):
        self.tools = {
            "list_files": {
                "name": "list_files",
                "description": "List files in a directory",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Directory path to list files from"
                        }
                    },
                    "required": ["path"]
                }
            },
            "read_file": {
                "name": "read_file",
                "description": "Read contents of a file",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "File path to read"
                        }
                    },
                    "required": ["path"]
                }
            }
        }
        
    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP requests"""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")
        
        try:
            if method == "initialize":
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {}
                        },
                        "serverInfo": {
                            "name": "file-manager-server",
                            "version": "1.0.0"
                        }
                    }
                }
            
            elif method == "tools/list":
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "tools": list(self.tools.values())
                    }
                }
            
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                
                if tool_name == "list_files":
                    result = self._list_files(arguments.get("path", "."))
                elif tool_name == "read_file":
                    result = self._read_file(arguments.get("path"))
                else:
                    raise ValueError(f"Unknown tool: {tool_name}")
                
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": result
                            }
                        ]
                    }
                }
            
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
                
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
    
    def _list_files(self, path: str) -> str:
        """List files in a directory"""
        try:
            path_obj = Path(path)
            if not path_obj.exists():
                return f"Error: Path '{path}' does not exist"
            
            if not path_obj.is_dir():
                return f"Error: Path '{path}' is not a directory"
            
            files = []
            for item in path_obj.iterdir():
                if item.is_file():
                    files.append(f"📄 {item.name} ({item.stat().st_size} bytes)")
                elif item.is_dir():
                    files.append(f"📁 {item.name}/")
            
            if not files:
                return f"Directory '{path}' is empty"
            
            return f"Contents of '{path}':\n" + "\n".join(sorted(files))
            
        except Exception as e:
            return f"Error listing files: {str(e)}"
    
    def _read_file(self, path: str) -> str:
        """Read contents of a file"""
        try:
            path_obj = Path(path)
            if not path_obj.exists():
                return f"Error: File '{path}' does not exist"
            
            if not path_obj.is_file():
                return f"Error: '{path}' is not a file"
            
            # Limit file size for safety
            if path_obj.stat().st_size > 1024 * 1024:  # 1MB limit
                return f"Error: File '{path}' is too large (max 1MB)"
            
            with open(path_obj, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return f"Contents of '{path}':\n\n{content}"
            
        except UnicodeDecodeError:
            return f"Error: Cannot read '{path}' - appears to be a binary file"
        except Exception as e:
            return f"Error reading file: {str(e)}"
    
    def run(self):
        """Run the MCP server"""
        print("🚀 MCP File Manager Server started!", file=sys.stderr)
        print("💡 Send JSON-RPC requests via stdin", file=sys.stderr)
        
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
                
            try:
                request = json.loads(line)
                response = self.handle_request(request)
                print(json.dumps(response))
                sys.stdout.flush()
            except json.JSONDecodeError as e:
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": f"Parse error: {str(e)}"
                    }
                }
                print(json.dumps(error_response))
                sys.stdout.flush()

if __name__ == "__main__":
    server = MCPServer()
    server.run()