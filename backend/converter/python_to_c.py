"""
Python to C Converter
Converts Python code to C using IR
"""
from typing import Dict, Any
from .base_converter import BaseConverter
from .ir_generator import IRGenerator
from .semantic_analyzer import SemanticAnalyzer

class PythonToCConverter(BaseConverter):
    """Converts Python code to C"""
    
    def __init__(self):
        super().__init__()
        self.ir_generator = IRGenerator()
        self.semantic_analyzer = SemanticAnalyzer()
    
    def convert(self, python_code: str) -> Dict[str, Any]:
        """
        Convert Python code to C
        
        Args:
            python_code: Python source code string
            
        Returns:
            Dictionary with code, warnings, and ir
        """
        self.reset()
        
        try:
            # Generate IR
            ir, parse_warnings = self.ir_generator.parse_to_ir(python_code)
            self.warnings.extend(parse_warnings)
            
            # Semantic analysis
            semantic_warnings = self.semantic_analyzer.analyze(ir)
            self.warnings.extend(semantic_warnings)
            
            # Generate C code
            code = self.generate_code(ir)
            
            return {
                'code': code,
                'warnings': self.warnings,
                'ir': ir
            }
        
        except Exception as e:
            self.add_warning('error', f'Conversion failed: {str(e)}')
            return {
                'code': f'// Error during conversion\n// {str(e)}',
                'warnings': self.warnings,
                'ir': {'type': 'program', 'body': [], 'includes': []}
            }
    
    def generate_code(self, ir: Dict) -> str:
        """Generate C code from IR"""
        lines = []
        
        # Add includes
        lines.append('#include <stdio.h>')
        lines.append('#include <string.h>')
        
        if self._needs_math(ir):
            lines.append('#include <math.h>')
        
        lines.append('')
        
        # Separate functions and top-level code
        body = ir.get('body', [])
        functions = [node for node in body if node.get('type') == 'function']
        top_level = [node for node in body if node.get('type') != 'function']
        
        # Generate function definitions
        for func in functions:
            lines.append(self._generate_function(func, 0))
            lines.append('')
        
        # Generate main function
        if top_level:
            lines.append('int main() {')
            for node in top_level:
                line = self._generate_node(node, 1)
                if line:
                    lines.append(line)
            lines.append('    return 0;')
            lines.append('}')
        
        return '\n'.join(lines)
    
    def _generate_function(self, node: Dict, level: int) -> str:
        """Generate function definition"""
        name = node.get('name')
        return_type = self.map_type(node.get('returnType', 'void'))
        params = node.get('params', [])
        
        # Generate parameter list
        param_strs = []
        for param in params:
            param_type = self.map_type(param.get('inferredType', 'int'))
            param_name = param.get('name')
            param_strs.append(f'{param_type} {param_name}')
        
        param_list = ', '.join(param_strs) if param_strs else 'void'
        
        lines = [f'{return_type} {name}({param_list}) {{']
        
        # Generate body
        for body_node in node.get('body', []):
            line = self._generate_node(body_node, 1)
            if line:
                lines.append(line)
        
        lines.append('}')
        return '\n'.join(lines)
    
    def _generate_node(self, node: Dict, level: int) -> str:
        """Generate code for a node"""
        node_type = node.get('type')
        
        if node_type == 'assign':
            return self._generate_assign(node, level)
        elif node_type == 'return':
            return self._generate_return(node, level)
        elif node_type == 'if':
            return self._generate_if(node, level)
        elif node_type == 'while':
            return self._generate_while(node, level)
        elif node_type == 'for':
            return self._generate_for(node, level)
        elif node_type == 'print':
            return self._generate_print(node, level)
        elif node_type == 'input':
            return self._generate_input(node, level)
        elif node_type == 'tuple_swap':
            return self._generate_tuple_swap(node, level)
        elif node_type == 'comment':
            return f'{self._indent(level)}// {node.get("text", "")}'
        else:
            return f'{self._indent(level)}// Unsupported: {node_type}'
    
    def _generate_assign(self, node: Dict, level: int) -> str:
        """Generate assignment statement"""
        target = node.get('target')
        value = self._generate_expr(node.get('value'))
        inferred_type = self.map_type(node.get('inferredType', 'int'))
        is_declaration = node.get('isDeclaration', True)
        
        if is_declaration:
            return f'{self._indent(level)}{inferred_type} {target} = {value};'
        else:
            return f'{self._indent(level)}{target} = {value};'
    
    def _generate_return(self, node: Dict, level: int) -> str:
        """Generate return statement"""
        value = node.get('value')
        if value:
            return f'{self._indent(level)}return {self._generate_expr(value)};'
        else:
            return f'{self._indent(level)}return;'
    
    def _generate_if(self, node: Dict, level: int) -> str:
        """Generate if statement"""
        lines = []
        condition = self._generate_expr(node.get('condition'))
        
        lines.append(f'{self._indent(level)}if ({condition}) {{')
        for body_node in node.get('body', []):
            line = self._generate_node(body_node, level + 1)
            if line:
                lines.append(line)
        lines.append(f'{self._indent(level)}}}')
        
        # Handle elifs
        for elif_block in node.get('elifs', []):
            elif_cond = self._generate_expr(elif_block.get('condition'))
            lines.append(f'{self._indent(level)}else if ({elif_cond}) {{')
            for body_node in elif_block.get('body', []):
                line = self._generate_node(body_node, level + 1)
                if line:
                    lines.append(line)
            lines.append(f'{self._indent(level)}}}')
        
        # Handle else
        else_body = node.get('elseBody', [])
        if else_body:
            lines.append(f'{self._indent(level)}else {{')
            for body_node in else_body:
                line = self._generate_node(body_node, level + 1)
                if line:
                    lines.append(line)
            lines.append(f'{self._indent(level)}}}')
        
        return '\n'.join(lines)
    
    def _generate_while(self, node: Dict, level: int) -> str:
        """Generate while loop"""
        lines = []
        condition = self._generate_expr(node.get('condition'))
        
        lines.append(f'{self._indent(level)}while ({condition}) {{')
        for body_node in node.get('body', []):
            line = self._generate_node(body_node, level + 1)
            if line:
                lines.append(line)
        lines.append(f'{self._indent(level)}}}')
        
        return '\n'.join(lines)
    
    def _generate_for(self, node: Dict, level: int) -> str:
        """Generate for loop"""
        lines = []
        variable = node.get('variable')
        start = self._generate_expr(node.get('start'))
        end = self._generate_expr(node.get('end'))
        
        lines.append(f'{self._indent(level)}for (int {variable} = {start}; {variable} < {end}; {variable}++) {{')
        for body_node in node.get('body', []):
            line = self._generate_node(body_node, level + 1)
            if line:
                lines.append(line)
        lines.append(f'{self._indent(level)}}}')
        
        return '\n'.join(lines)
    
    def _generate_print(self, node: Dict, level: int) -> str:
        """Generate print statement for C"""
        args = node.get('args', [])
        
        format_parts = []
        arg_parts = []
        
        for arg in args:
            expr_type = arg.get('exprType')
            data_type = arg.get('dataType', '')
            if expr_type == 'literal' and data_type == 'string':
                # Inline string literal — embed directly in format string
                val = str(arg.get('value', '')).replace('"', '\\"')
                format_parts.append(val)
            else:
                # Variable or numeric literal — use format specifier
                fmt = self._get_format_specifier(arg)
                format_parts.append(fmt)
                arg_parts.append(self._generate_expr(arg))
        
        format_str = ' '.join(format_parts)
        
        if arg_parts:
            args_str = ', '.join(arg_parts)
            return f'{self._indent(level)}printf("{format_str}\\n", {args_str});'
        else:
            return f'{self._indent(level)}printf("{format_str}\\n");'
    
    def _generate_input(self, node: Dict, level: int) -> str:
        """Generate input statement for C"""
        lines = []
        target = node.get('target')
        prompt = node.get('prompt')
        inferred_type = node.get('inferredType', 'int')
        c_type = self.map_type(inferred_type)
        
        # Print prompt
        if prompt:
            prompt_str = self._generate_expr(prompt)
            lines.append(f'{self._indent(level)}printf({prompt_str});')
        
        # Declare variable
        lines.append(f'{self._indent(level)}{c_type} {target};')
        
        # Read input
        fmt = self._get_input_format(inferred_type)
        lines.append(f'{self._indent(level)}scanf("{fmt}", &{target});')
        
        return '\n'.join(lines)
    
    def _generate_expr(self, expr: Dict) -> str:
        """Generate expression code"""
        if not expr:
            return ''
        
        expr_type = expr.get('exprType')
        
        if expr_type == 'literal':
            value = expr.get('value')
            data_type = expr.get('dataType')
            if data_type == 'string':
                return f'"{value}"'
            elif data_type == 'bool':
                return 'true' if value else 'false'
            else:
                return str(value)
        
        elif expr_type == 'variable':
            return expr.get('name', '')
        
        elif expr_type == 'binary_op':
            left = self._generate_expr(expr.get('left'))
            right = self._generate_expr(expr.get('right'))
            op = expr.get('operator')
            
            # Map Python operators to C
            op_map = {
                'and': '&&',
                'or': '||',
                'not': '!'
            }
            c_op = op_map.get(op, op)
            
            return f'{left} {c_op} {right}'
        
        elif expr_type == 'call':
            func_name = expr.get('function')
            args = expr.get('args', [])
            arg_strs = [self._generate_expr(arg) for arg in args]
            return f'{func_name}({", ".join(arg_strs)})'
        
        return ''
    
    def _get_format_specifier(self, expr: Dict) -> str:
        """Get printf format specifier for expression"""
        data_type = expr.get('dataType', '')
        expr_type = expr.get('exprType', '')
        # For variables, infer from context — default to %d (most common)
        if not data_type and expr_type == 'variable':
            return '%d'
        if data_type == 'string':
            return '%s'
        elif data_type == 'float':
            return '%f'
        elif data_type == 'int':
            return '%d'
        else:
            return '%d'

    def _generate_tuple_swap(self, node: Dict, level: int) -> str:
        """Generate tuple swap: int _tmp = a; a = b; b = _tmp;"""
        targets = node.get('targets', [])
        values = node.get('values', [])
        if len(targets) == 2 and len(values) == 2:
            a, b = targets[0], targets[1]
            lines = [
                f'{self._indent(level)}int _tmp_{a} = {a};',
                f'{self._indent(level)}{a} = {b};',
                f'{self._indent(level)}{b} = _tmp_{a};',
            ]
            return '\n'.join(lines)
        return f'{self._indent(level)}// Unsupported tuple swap'
    
    def _get_input_format(self, inferred_type: str) -> str:
        """Get scanf format specifier"""
        if inferred_type == 'int':
            return '%d'
        elif inferred_type == 'float':
            return '%f'
        else:
            return '%s'
    
    def _indent(self, level: int) -> str:
        """Generate indentation"""
        return '    ' * level
    
    def _needs_math(self, ir: Dict) -> bool:
        """Check if math.h is needed"""
        # Simple check - can be expanded
        return False
