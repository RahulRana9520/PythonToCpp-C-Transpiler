"""
Base Converter class for Python to C/C++ transpilation
Provides common functionality for all converters
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any

class BaseConverter(ABC):
    """Abstract base class for code converters"""
    
    def __init__(self):
        self.warnings = []
        self.includes = set()
        
    @abstractmethod
    def convert(self, python_code: str) -> Dict[str, Any]:
        """
        Convert Python code to target language
        
        Args:
            python_code: Python source code string
            
        Returns:
            Dictionary containing:
                - code: Converted code string
                - warnings: List of warning dictionaries
                - ir: Intermediate representation dictionary
        """
        pass
    
    @abstractmethod
    def generate_code(self, ir: Dict) -> str:
        """
        Generate target language code from IR
        
        Args:
            ir: Intermediate representation dictionary
            
        Returns:
            Generated code string
        """
        pass
    
    def reset(self):
        """Reset converter state"""
        self.warnings = []
        self.includes = set()
    
    def add_warning(self, warning_type: str, message: str, line: int = None):
        """Add a warning message"""
        warning = {
            'type': warning_type,
            'message': message
        }
        if line is not None:
            warning['line'] = line
        self.warnings.append(warning)
    
    def detect_includes(self, ir_nodes: List[Dict]) -> List[str]:
        """
        Detect required includes/imports based on IR nodes
        
        Args:
            ir_nodes: List of IR node dictionaries
            
        Returns:
            List of include names
        """
        includes = set()
        
        def walk_node(node):
            if node.get('type') == 'print':
                includes.add('stdio')
            elif node.get('type') == 'input':
                includes.add('stdio')
            elif node.get('type') == 'function':
                for child in node.get('body', []):
                    walk_node(child)
            elif node.get('type') == 'if':
                for child in node.get('body', []):
                    walk_node(child)
                for child in node.get('elseBody', []):
                    walk_node(child)
                for elif_block in node.get('elifs', []):
                    for child in elif_block.get('body', []):
                        walk_node(child)
            elif node.get('type') == 'while':
                for child in node.get('body', []):
                    walk_node(child)
            elif node.get('type') == 'for':
                for child in node.get('body', []):
                    walk_node(child)
        
        for node in ir_nodes:
            walk_node(node)
        
        return list(includes)
    
    def map_type(self, py_type: str) -> str:
        """
        Map Python type to C/C++ type
        
        Args:
            py_type: Python type string
            
        Returns:
            C/C++ type string
        """
        type_map = {
            'int': 'int',
            'float': 'float',
            'double': 'double',
            'string': 'char*',
            'str': 'char*',
            'bool': 'bool',
            'void': 'void'
        }
        return type_map.get(py_type, 'int')
