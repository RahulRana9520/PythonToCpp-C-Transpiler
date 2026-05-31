"""
Semantic Analyzer for Python to C/C++ transpilation
Performs type checking and semantic validation
"""
from typing import Dict, List, Any

class SemanticAnalyzer:
    """Analyzes and validates IR for semantic correctness"""
    
    def __init__(self):
        self.warnings = []
        self.symbol_table = {}
        self.current_function = None
    
    def analyze(self, ir: Dict) -> List[Dict]:
        """
        Analyze IR and return warnings
        
        Args:
            ir: Intermediate representation dictionary
            
        Returns:
            List of warning dictionaries
        """
        self.warnings = []
        self.symbol_table = {}
        self.current_function = None
        
        body = ir.get('body', [])
        self._analyze_block(body)
        
        return self.warnings
    
    def _analyze_block(self, nodes: List[Dict]):
        """Analyze a block of IR nodes"""
        for node in nodes:
            node_type = node.get('type')
            
            if node_type == 'function':
                self._analyze_function(node)
            elif node_type == 'assign':
                self._analyze_assign(node)
            elif node_type == 'if':
                self._analyze_if(node)
            elif node_type == 'while':
                self._analyze_while(node)
            elif node_type == 'for':
                self._analyze_for(node)
            elif node_type == 'return':
                self._analyze_return(node)
            elif node_type == 'print':
                self._analyze_print(node)
            elif node_type == 'input':
                self._analyze_input(node)
            elif node_type == 'expr_stmt':
                self._analyze_expression(node.get('value'), node.get('line'))
    
    def _analyze_function(self, node: Dict):
        """Analyze function definition"""
        func_name = node.get('name')
        
        if func_name in self.symbol_table:
            self.warnings.append({
                'type': 'warning',
                'message': f"Function '{func_name}' redefined",
                'line': node.get('line'),
                'hint': "Rename one of the functions or remove the duplicate definition."
            })
        
        # Store function in symbol table
        self.symbol_table[func_name] = {
            'type': 'function',
            'returnType': node.get('returnType'),
            'params': node.get('params', [])
        }
        
        # Analyze function body
        prev_func = self.current_function
        self.current_function = func_name
        
        # Save symbol table state to support local scoping for params
        prev_symbols = dict(self.symbol_table)
        
        # Add params to symbol table before analyzing body
        for param in node.get('params', []):
            self.symbol_table[param['name']] = {
                'type': 'variable',
                'inferredType': param.get('inferredType', 'int')
            }
            
        self._analyze_block(node.get('body', []))
        
        # Restore symbol table (remove locals)
        self.symbol_table = prev_symbols
        self.current_function = prev_func
    
    def _analyze_assign(self, node: Dict):
        """Analyze assignment statement"""
        target = node.get('target')
        value = node.get('value')
        inferred_type = node.get('inferredType')
        line = node.get('line')
        
        # Check if variable exists
        if target in self.symbol_table:
            stored_type = self.symbol_table[target].get('inferredType')
            if stored_type and stored_type != inferred_type:
                self.warnings.append({
                    'type': 'info',
                    'message': f"Variable '{target}' type changed from {stored_type} to {inferred_type}",
                    'line': line,
                    'hint': "Keep a variable's type consistent, or use a new variable for a different type."
                })
        
        # Update symbol table
        self.symbol_table[target] = {
            'type': 'variable',
            'inferredType': inferred_type
        }
        
        # Analyze the value expression
        self._analyze_expression(value, line)
    
    def _analyze_if(self, node: Dict):
        """Analyze if statement"""
        # Analyze condition
        self._analyze_expression(node.get('condition'), node.get('line'))
        
        # Analyze body
        self._analyze_block(node.get('body', []))
        
        # Analyze elifs
        for elif_block in node.get('elifs', []):
            self._analyze_expression(elif_block.get('condition'), node.get('line'))
            self._analyze_block(elif_block.get('body', []))
        
        # Analyze else
        self._analyze_block(node.get('elseBody', []))
    
    def _analyze_while(self, node: Dict):
        """Analyze while loop"""
        self._analyze_expression(node.get('condition'), node.get('line'))
        self._analyze_block(node.get('body', []))
    
    def _analyze_for(self, node: Dict):
        """Analyze for loop"""
        variable = node.get('variable')
        
        # Add loop variable to symbol table
        self.symbol_table[variable] = {
            'type': 'variable',
            'inferredType': 'int'
        }
        
        self._analyze_expression(node.get('start'), node.get('line'))
        self._analyze_expression(node.get('end'), node.get('line'))
        self._analyze_block(node.get('body', []))
    
    def _analyze_return(self, node: Dict):
        """Analyze return statement"""
        if not self.current_function:
            self.warnings.append({
                'type': 'error',
                'message': 'Return statement outside function',
                'line': node.get('line'),
                'hint': 'Move this return statement inside a function body.'
            })
        
        value = node.get('value')
        if value:
            self._analyze_expression(value, node.get('line'))
    
    def _analyze_print(self, node: Dict):
        """Analyze print statement"""
        for arg in node.get('args', []):
            self._analyze_expression(arg, node.get('line'))
    
    def _analyze_input(self, node: Dict):
        """Analyze input statement"""
        prompt = node.get('prompt')
        if prompt:
            self._analyze_expression(prompt, node.get('line'))
    
    def _analyze_expression(self, expr: Dict, line: int | None = None):
        """Analyze an expression"""
        if not expr:
            return
        
        expr_type = expr.get('exprType')
        
        if expr_type == 'variable':
            var_name = expr.get('name')
            if var_name not in self.symbol_table:
                self.warnings.append({
                    'type': 'warning',
                    'message': f"Variable '{var_name}' used before assignment",
                    'line': line,
                    'hint': f"Define '{var_name}' before using it, or check for a typo in the name."
                })
        
        elif expr_type == 'binary_op':
            self._analyze_expression(expr.get('left'), line)
            self._analyze_expression(expr.get('right'), line)
        
        elif expr_type == 'call':
            func_name = expr.get('function')
            if func_name not in self.symbol_table:
                self.warnings.append({
                    'type': 'warning',
                    'message': f"Function '{func_name}' not defined",
                    'line': line,
                    'hint': f"Define function '{func_name}' before calling it, or fix the function name."
                })
            
            for arg in expr.get('args', []):
                self._analyze_expression(arg, line)
