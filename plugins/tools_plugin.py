"""
Tools Plugin - Custom tools integration plugin
"""

import logging
from typing import Dict, Optional, List, Any, Callable
import json
import asyncio
from datetime import datetime

from .base_plugin import BasePlugin

logger = logging.getLogger(__name__)


class ToolsPlugin(BasePlugin):
    """
    Tools plugin for integrating custom function tools.
    Allows registration and execution of custom tools/functions.
    """
    
    def __init__(self):
        """Initialize Tools plugin"""
        super().__init__()
        self.name = "ToolsPlugin"
        self.metadata = {
            'version': '1.0.0',
            'author': 'Avatar Factory',
            'description': 'Custom tools and function calling capabilities'
        }
        
        # Registered tools
        self.tools = {}
        self.tool_schemas = {}
        
        # Execution settings
        self.max_execution_time = 30
        self.allow_parallel = True
        
    def initialize(self, config: Dict) -> bool:
        """
        Initialize Tools plugin with configuration.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            True if initialization successful
        """
        try:
            self.config = config
            
            # Get configuration
            self.max_execution_time = config.get('max_execution_time', 30)
            self.allow_parallel = config.get('allow_parallel', True)
            
            # Load configured tools
            enabled_tools = config.get('enabled_tools', [])
            for tool_name in enabled_tools:
                self._load_tool(tool_name)
            
            logger.info(f"Tools plugin initialized with {len(self.tools)} tools")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Tools plugin: {e}")
            return False
    
    def _load_tool(self, tool_name: str):
        """Load a tool by name"""
        try:
            # In production, would dynamically load tool modules
            # For now, create mock tools
            
            if tool_name == 'weather':
                self.register_tool(
                    name='weather',
                    function=self._mock_weather_tool,
                    schema={
                        'description': 'Get weather information',
                        'parameters': {
                            'location': {'type': 'string', 'required': True}
                        }
                    }
                )
            elif tool_name == 'calculator':
                self.register_tool(
                    name='calculator',
                    function=self._mock_calculator_tool,
                    schema={
                        'description': 'Perform calculations',
                        'parameters': {
                            'expression': {'type': 'string', 'required': True}
                        }
                    }
                )
            elif tool_name == 'web_search':
                self.register_tool(
                    name='web_search',
                    function=self._mock_search_tool,
                    schema={
                        'description': 'Search the web',
                        'parameters': {
                            'query': {'type': 'string', 'required': True},
                            'max_results': {'type': 'integer', 'default': 5}
                        }
                    }
                )
            
            logger.info(f"Loaded tool: {tool_name}")
            
        except Exception as e:
            logger.error(f"Failed to load tool {tool_name}: {e}")
    
    def register_tool(self, name: str, function: Callable, schema: Optional[Dict] = None):
        """
        Register a new tool.
        
        Args:
            name: Tool name
            function: Tool function (callable)
            schema: Tool schema/description
        """
        self.tools[name] = function
        
        if schema:
            self.tool_schemas[name] = schema
        else:
            self.tool_schemas[name] = {
                'description': f'Tool: {name}',
                'parameters': {}
            }
        
        logger.info(f"Tool registered: {name}")
    
    def unregister_tool(self, name: str):
        """
        Unregister a tool.
        
        Args:
            name: Tool name to unregister
        """
        if name in self.tools:
            del self.tools[name]
            del self.tool_schemas[name]
            logger.info(f"Tool unregistered: {name}")
    
    async def process(self, input_data: Dict) -> Optional[Dict]:
        """
        Process input to detect and execute tool calls.
        
        Args:
            input_data: Input data
            
        Returns:
            Response with tool execution results
        """
        if not self.enabled:
            return None
        
        try:
            content = input_data.get('content', '')
            
            # Detect tool calls in content
            tool_calls = self._detect_tool_calls(content)
            
            if not tool_calls:
                return None
            
            # Execute tools
            results = await self._execute_tools(tool_calls)
            
            # Format response
            return self._format_tool_results(results)
            
        except Exception as e:
            return self.handle_error(e, "processing tool calls")
    
    def _detect_tool_calls(self, content: str) -> List[Dict]:
        """
        Detect tool calls in content.
        
        Args:
            content: Input content
            
        Returns:
            List of detected tool calls
        """
        tool_calls = []
        
        # Simple pattern matching (in production, would use more sophisticated detection)
        content_lower = content.lower()
        
        # Check for tool mentions
        for tool_name in self.tools.keys():
            if tool_name in content_lower:
                # Extract parameters (simplified)
                params = self._extract_parameters(content, tool_name)
                
                tool_calls.append({
                    'name': tool_name,
                    'parameters': params
                })
        
        # Also check for explicit tool call syntax
        # Format: @tool_name(param1=value1, param2=value2)
        import re
        pattern = r'@(\w+)\((.*?)\)'
        matches = re.findall(pattern, content)
        
        for match in matches:
            tool_name = match[0]
            params_str = match[1]
            
            if tool_name in self.tools:
                params = self._parse_parameters(params_str)
                tool_calls.append({
                    'name': tool_name,
                    'parameters': params
                })
        
        return tool_calls
    
    def _extract_parameters(self, content: str, tool_name: str) -> Dict:
        """Extract parameters for a tool from content"""
        # Simplified parameter extraction
        params = {}
        
        schema = self.tool_schemas.get(tool_name, {})
        param_specs = schema.get('parameters', {})
        
        # Extract based on schema (simplified)
        for param_name, param_spec in param_specs.items():
            if param_spec.get('required', False):
                # Try to extract from content
                if param_name == 'location':
                    # Look for city names (simplified)
                    cities = ['london', 'new york', 'tokyo', 'paris']
                    for city in cities:
                        if city in content.lower():
                            params[param_name] = city.title()
                            break
                elif param_name == 'query':
                    # Use the whole content as query
                    params[param_name] = content
                elif param_name == 'expression':
                    # Look for mathematical expressions
                    import re
                    expr_pattern = r'[\d\+\-\*\/\(\)\s]+'
                    match = re.search(expr_pattern, content)
                    if match:
                        params[param_name] = match.group().strip()
        
        return params
    
    def _parse_parameters(self, params_str: str) -> Dict:
        """Parse parameter string into dictionary"""
        params = {}
        
        # Parse key=value pairs
        pairs = params_str.split(',')
        for pair in pairs:
            if '=' in pair:
                key, value = pair.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"\'')
                
                # Try to parse value type
                try:
                    # Try integer
                    value = int(value)
                except:
                    try:
                        # Try float
                        value = float(value)
                    except:
                        # Keep as string
                        pass
                
                params[key] = value
        
        return params
    
    async def _execute_tools(self, tool_calls: List[Dict]) -> List[Dict]:
        """
        Execute tool calls.
        
        Args:
            tool_calls: List of tool calls to execute
            
        Returns:
            List of execution results
        """
        results = []
        
        if self.allow_parallel and len(tool_calls) > 1:
            # Execute in parallel
            tasks = []
            for tool_call in tool_calls:
                task = self._execute_single_tool(tool_call)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Convert exceptions to error results
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    results[i] = {
                        'tool': tool_calls[i]['name'],
                        'error': str(result),
                        'success': False
                    }
        else:
            # Execute sequentially
            for tool_call in tool_calls:
                result = await self._execute_single_tool(tool_call)
                results.append(result)
        
        return results
    
    async def _execute_single_tool(self, tool_call: Dict) -> Dict:
        """Execute a single tool call"""
        tool_name = tool_call['name']
        parameters = tool_call.get('parameters', {})
        
        if tool_name not in self.tools:
            return {
                'tool': tool_name,
                'error': f'Tool {tool_name} not found',
                'success': False
            }
        
        try:
            # Get tool function
            tool_function = self.tools[tool_name]
            
            # Execute with timeout
            if asyncio.iscoroutinefunction(tool_function):
                result = await asyncio.wait_for(
                    tool_function(**parameters),
                    timeout=self.max_execution_time
                )
            else:
                # Run sync function in executor
                loop = asyncio.get_event_loop()
                result = await asyncio.wait_for(
                    loop.run_in_executor(None, tool_function, **parameters),
                    timeout=self.max_execution_time
                )
            
            return {
                'tool': tool_name,
                'result': result,
                'success': True,
                'parameters': parameters
            }
            
        except asyncio.TimeoutError:
            return {
                'tool': tool_name,
                'error': f'Tool execution timeout ({self.max_execution_time}s)',
                'success': False
            }
        except Exception as e:
            return {
                'tool': tool_name,
                'error': str(e),
                'success': False
            }
    
    def _format_tool_results(self, results: List[Dict]) -> Dict:
        """Format tool execution results"""
        successful = [r for r in results if r.get('success', False)]
        failed = [r for r in results if not r.get('success', False)]
        
        # Build response content
        content_parts = []
        
        for result in successful:
            tool_name = result['tool']
            tool_result = result.get('result', 'No result')
            content_parts.append(f"**{tool_name}**: {tool_result}")
        
        for result in failed:
            tool_name = result['tool']
            error = result.get('error', 'Unknown error')
            content_parts.append(f"**{tool_name}** (failed): {error}")
        
        return {
            'content': '\n\n'.join(content_parts),
            'metadata': {
                'plugin': self.name,
                'tools_executed': len(results),
                'successful': len(successful),
                'failed': len(failed),
                'tools': [r['tool'] for r in results]
            }
        }
    
    # Mock tool implementations
    async def _mock_weather_tool(self, location: str) -> str:
        """Mock weather tool"""
        await asyncio.sleep(0.5)  # Simulate API call
        return f"Weather in {location}: Sunny, 22°C"
    
    async def _mock_calculator_tool(self, expression: str) -> str:
        """Mock calculator tool"""
        try:
            # Safe evaluation (in production, use proper math parser)
            result = eval(expression, {"__builtins__": {}}, {})
            return f"{expression} = {result}"
        except Exception as e:
            return f"Calculation error: {e}"
    
    async def _mock_search_tool(self, query: str, max_results: int = 5) -> str:
        """Mock search tool"""
        await asyncio.sleep(1)  # Simulate search
        return f"Search results for '{query}': Found {max_results} results"
    
    async def cleanup(self):
        """Clean up Tools plugin resources"""
        try:
            # Clear registered tools
            self.tools.clear()
            self.tool_schemas.clear()
            
            logger.info("Tools plugin cleaned up")
            
        except Exception as e:
            logger.error(f"Error during Tools plugin cleanup: {e}")
    
    def get_available_tools(self) -> List[Dict]:
        """Get list of available tools with their schemas"""
        tools = []
        
        for name, schema in self.tool_schemas.items():
            tools.append({
                'name': name,
                'description': schema.get('description', ''),
                'parameters': schema.get('parameters', {})
            })
        
        return tools
    
    def get_statistics(self) -> Dict:
        """Get Tools plugin statistics"""
        return {
            'total_tools': len(self.tools),
            'tools': list(self.tools.keys()),
            'max_execution_time': self.max_execution_time,
            'allow_parallel': self.allow_parallel
        }
