"""
Intermediate Representation (IR) Generator
Converts Python AST to a simplified IR for transpilation
"""
import re
from typing import Dict, List, Any, Tuple

class IRGenerator:
    """Generates intermediate representation from Python code"""
    
    def __init__(self):
        self.warnings = []
    
    def parse_to_ir(self, python_code: str) -> Tuple[Dict, List[Dict]]:
        """
        Parse Python code to IR
        
        Args:
            python_code: Python source code
            
        Returns:
            Tuple of (ir_dict, warnings_list)
        """
        self.warnings = []
        lines = python_code.split('\n')
        body = self._parse_block(lines, 0, 0)
        includes = self._detect_includes(body)
        
        ir = {
            'type': 'program',
            'body': body,
            'includes': includes
        }
        
        return ir, self.warnings
    
    def _get_indent(self, line: str) -> int:
        """Get indentation level of a line"""
        match = re.match(r'^(\s*)', line)
        return len(match.group(1)) if match else 0
    
    def _parse_block(self, lines: List[str], start_idx: int, base_indent: int) -> List[Dict]:
        """Parse a block of Python code"""
        nodes = []
        i = start_idx
        
        while i < len(lines):
            line = lines[i]
            trimmed = line.strip()
            
            # Skip empty lines and comments
            if not trimmed or trimmed.startswith('#'):
                if trimmed.startswith('#'):
                    nodes.append({
                        'type': 'comment',
                        'text': trimmed[1:].strip(),
                        'line': i + 1
                    })
                i += 1
                continue
            
            indent = self._get_indent(line)
            if indent < base_indent:
                break
            if indent > base_indent:
                i += 1
                continue
            
            # Function definition
            if trimmed.startswith('def '):
                func_node, next_i = self._parse_function(lines, i, indent)
                if func_node:
                    nodes.append(func_node)
                i = next_i
                continue
            
            # If statement
            if trimmed.startswith('if ') and trimmed.endswith(':'):
                if_node, next_i = self._parse_if(lines, i, indent)
                nodes.append(if_node)
                i = next_i
                continue
            
            # While loop
            if trimmed.startswith('while ') and trimmed.endswith(':'):
                while_node, next_i = self._parse_while(lines, i, indent)
                nodes.append(while_node)
                i = next_i
                continue
            
            # For loop
            if trimmed.startswith('for ') and ' in range(' in trimmed:
                for_node, next_i = self._parse_for(lines, i, indent)
                if for_node:
                    nodes.append(for_node)
                i = next_i
                continue
            
            # Unsupported for loop
            if trimmed.startswith('for ') and ' in range(' not in trimmed:
                self.warnings.append({
                    'type': 'warning',
                    'message': "Only 'for x in range(...)' loops are supported",
                    'line': i + 1
                })
                body_lines = self._collect_block(lines, i + 1, indent)
                i = i + 1 + body_lines
                continue

            # try/except block — parse try body, wrap in comment, skip except
            if trimmed == 'try:':
                try_body_lines = self._collect_block(lines, i + 1, indent)
                try_body = self._parse_block(lines, i + 1, indent + 4)
                nodes.extend(try_body)
                next_i = i + 1 + try_body_lines
                # skip except clauses
                while next_i < len(lines):
                    next_trimmed = lines[next_i].strip()
                    next_indent = self._get_indent(lines[next_i]) if lines[next_i].strip() else indent + 1
                    if next_indent == indent and (next_trimmed.startswith('except') or next_trimmed.startswith('finally')):
                        except_body_lines = self._collect_block(lines, next_i + 1, indent)
                        next_i = next_i + 1 + except_body_lines
                    else:
                        break
                i = next_i
                continue

            # except / finally — skip if encountered at top level
            if trimmed.startswith('except') or trimmed.startswith('finally'):
                body_lines = self._collect_block(lines, i + 1, indent)
                i = i + 1 + body_lines
                continue

            # Return statement
            if trimmed.startswith('return'):
                return_val = trimmed[6:].strip() if len(trimmed) > 6 else None
                nodes.append({
                    'type': 'return',
                    'value': self._parse_expression(return_val) if return_val else None,
                    'line': i + 1
                })
                i += 1
                continue
            
            # Print statement — match print(...) with balanced parens
            if trimmed.startswith('print('):
                # find matching closing paren
                depth = 0
                end_pos = -1
                for ci, ch in enumerate(trimmed):
                    if ch == '(':
                        depth += 1
                    elif ch == ')':
                        depth -= 1
                        if depth == 0:
                            end_pos = ci
                            break
                if end_pos != -1:
                    inner = trimmed[6:end_pos]
                    args = self._split_args(inner)
                    nodes.append({
                        'type': 'print',
                        'args': [self._parse_expression(arg.strip()) for arg in args],
                        'line': i + 1
                    })
                    i += 1
                    continue
            
            # Input statement
            if '= input(' in trimmed or '= int(input(' in trimmed or '= float(input(' in trimmed:
                input_node = self._parse_input(trimmed)
                input_node['line'] = i + 1
                nodes.append(input_node)
                i += 1
                continue
            
            # Tuple swap: a, b = b, a  (two vars on each side)
            tuple_swap = re.match(r'^(\w+)\s*,\s*(\w+)\s*=\s*(\w+)\s*,\s*(\w+)$', trimmed)
            if tuple_swap:
                lhs1, lhs2, rhs1, rhs2 = tuple_swap.groups()
                nodes.append({
                    'type': 'tuple_swap',
                    'targets': [lhs1, lhs2],
                    'values': [rhs1, rhs2],
                    'line': i + 1
                })
                i += 1
                continue

            # Assignment
            if '=' in trimmed and '==' not in trimmed and not trimmed.startswith(('if', 'while')):
                eq_idx = trimmed.find('=')
                if eq_idx > 0 and trimmed[eq_idx - 1] not in '!<>':
                    target = trimmed[:eq_idx].strip()
                    value = trimmed[eq_idx + 1:].strip()
                    
                    # Handle augmented assignment
                    if target.endswith(('+', '-', '*', '/')):
                        op = target[-1]
                        real_target = target[:-1].strip()
                        nodes.append({
                            'type': 'assign',
                            'target': real_target,
                            'value': self._parse_expression(f'{real_target} {op} {value}'),
                            'inferredType': self._infer_type(value),
                            'isDeclaration': False,
                            'line': i + 1
                        })
                    else:
                        nodes.append({
                            'type': 'assign',
                            'target': target,
                            'value': self._parse_expression(value),
                            'inferredType': self._infer_type(value),
                            'isDeclaration': True,
                            'line': i + 1
                        })
            
            i += 1
        
        return nodes
    
    def _parse_function(self, lines: List[str], i: int, indent: int) -> Tuple[Dict, int]:
        """Parse function definition"""
        trimmed = lines[i].strip()
        match = re.match(r'^def\s+(\w+)\s*\(([^)]*)\)\s*:', trimmed)
        
        if not match:
            return None, i + 1
        
        name = match.group(1)
        params_str = match.group(2)
        params = []
        
        if params_str:
            for param in params_str.split(','):
                param = param.strip()
                if param:
                    params.append({
                        'name': param,
                        'inferredType': 'int'
                    })
        
        body_lines = self._collect_block(lines, i + 1, indent)
        body = self._parse_block(lines, i + 1, indent + 4)
        return_type = self._detect_return_type(body)
        
        func_node = {
            'type': 'function',
            'name': name,
            'params': params,
            'returnType': return_type,
            'body': body,
            'line': i + 1
        }
        
        return func_node, i + 1 + body_lines
    
    def _parse_if(self, lines: List[str], i: int, indent: int) -> Tuple[Dict, int]:
        """Parse if statement"""
        trimmed = lines[i].strip()
        condition = trimmed[3:-1].strip()  # Remove 'if ' and ':'
        
        body_lines = self._collect_block(lines, i + 1, indent)
        body = self._parse_block(lines, i + 1, indent + 4)
        
        next_i = i + 1 + body_lines
        elifs = []
        else_body = []
        
        # Check for elif and else
        while next_i < len(lines):
            next_line = lines[next_i].strip()
            next_indent = self._get_indent(lines[next_i])
            
            if next_indent != indent:
                break
            
            if next_line.startswith('elif ') and next_line.endswith(':'):
                elif_cond = next_line[5:-1].strip()
                elif_body_lines = self._collect_block(lines, next_i + 1, indent)
                elif_body = self._parse_block(lines, next_i + 1, indent + 4)
                elifs.append({
                    'condition': self._parse_expression(elif_cond),
                    'body': elif_body
                })
                next_i = next_i + 1 + elif_body_lines
            elif next_line == 'else:':
                else_body_lines = self._collect_block(lines, next_i + 1, indent)
                else_body = self._parse_block(lines, next_i + 1, indent + 4)
                next_i = next_i + 1 + else_body_lines
                break
            else:
                break
        
        if_node = {
            'type': 'if',
            'condition': self._parse_expression(condition),
            'body': body,
            'elifs': elifs,
            'elseBody': else_body,
            'line': i + 1
        }
        
        return if_node, next_i
    
    def _parse_while(self, lines: List[str], i: int, indent: int) -> Tuple[Dict, int]:
        """Parse while loop"""
        trimmed = lines[i].strip()
        condition = trimmed[6:-1].strip()  # Remove 'while ' and ':'
        
        body_lines = self._collect_block(lines, i + 1, indent)
        body = self._parse_block(lines, i + 1, indent + 4)
        
        while_node = {
            'type': 'while',
            'condition': self._parse_expression(condition),
            'body': body,
            'line': i + 1
        }
        
        return while_node, i + 1 + body_lines
    
    def _parse_for(self, lines: List[str], i: int, indent: int) -> Tuple[Dict, int]:
        """Parse for loop"""
        trimmed = lines[i].strip()
        match = re.match(r'^for\s+(\w+)\s+in\s+range\((.+)\)\s*:', trimmed)
        
        if not match:
            return None, i + 1
        
        variable = match.group(1)
        # Handle arguments separated by comma (assuming no commas in the expressions themselves for now)
        range_args = [arg.strip() for arg in match.group(2).split(',')]
        
        if len(range_args) == 1:
            start = self._parse_expression('0')
            end = self._parse_expression(range_args[0])
        else:
            start = self._parse_expression(range_args[0])
            end = self._parse_expression(range_args[1])
        
        body_lines = self._collect_block(lines, i + 1, indent)
        body = self._parse_block(lines, i + 1, indent + 4)
        
        for_node = {
            'type': 'for',
            'variable': variable,
            'start': start,
            'end': end,
            'body': body,
            'line': i + 1
        }
        
        return for_node, i + 1 + body_lines
    
    def _parse_input(self, trimmed: str) -> Dict:
        """Parse input statement"""
        eq_idx = trimmed.find('=')
        target = trimmed[:eq_idx].strip()
        inferred_type = 'string'
        prompt = None
        
        if 'int(input(' in trimmed:
            inferred_type = 'int'
            match = re.search(r'int\(input\(([^)]*)\)\)', trimmed)
            if match and match.group(1):
                prompt = self._parse_expression(match.group(1))
        elif 'float(input(' in trimmed:
            inferred_type = 'float'
            match = re.search(r'float\(input\(([^)]*)\)\)', trimmed)
            if match and match.group(1):
                prompt = self._parse_expression(match.group(1))
        else:
            match = re.search(r'input\(([^)]*)\)', trimmed)
            if match and match.group(1):
                prompt = self._parse_expression(match.group(1))
        
        return {
            'type': 'input',
            'target': target,
            'prompt': prompt,
            'inferredType': inferred_type
        }
    
    def _parse_expression(self, expr_str: str) -> Dict:
        """Parse an expression"""
        if not expr_str:
            return {'exprType': 'literal', 'value': '', 'dataType': 'string'}
        
        expr_str = expr_str.strip()
        
        # String literal
        if (expr_str.startswith('"') and expr_str.endswith('"')) or \
           (expr_str.startswith("'") and expr_str.endswith("'")):
            return {
                'exprType': 'literal',
                'value': expr_str[1:-1],
                'dataType': 'string'
            }
        
        # Number literal
        if expr_str.replace('.', '', 1).replace('-', '', 1).isdigit():
            return {
                'exprType': 'literal',
                'value': float(expr_str) if '.' in expr_str else int(expr_str),
                'dataType': 'float' if '.' in expr_str else 'int'
            }
        
        # Boolean literal
        if expr_str in ('True', 'False'):
            return {
                'exprType': 'literal',
                'value': expr_str == 'True',
                'dataType': 'bool'
            }
        
        # Binary operation
        for op in ['==', '!=', '<=', '>=', '<', '>', '+', '-', '*', '/', '%', 'and', 'or']:
            if op in expr_str:
                parts = expr_str.split(op, 1)
                if len(parts) == 2:
                    return {
                        'exprType': 'binary_op',
                        'operator': op,
                        'left': self._parse_expression(parts[0].strip()),
                        'right': self._parse_expression(parts[1].strip())
                    }
        
        # Function call
        if '(' in expr_str and expr_str.endswith(')'):
            paren_idx = expr_str.index('(')
            func_name = expr_str[:paren_idx]
            args_str = expr_str[paren_idx + 1:-1]
            args = [self._parse_expression(arg.strip()) for arg in self._split_args(args_str)]
            return {
                'exprType': 'call',
                'function': func_name,
                'args': args
            }
        
        # Variable
        return {
            'exprType': 'variable',
            'name': expr_str
        }
    
    def _collect_block(self, lines: List[str], start_idx: int, base_indent: int) -> int:
        """Count lines in a block"""
        count = 0
        expected_indent = base_indent + 4
        
        for i in range(start_idx, len(lines)):
            line = lines[i]
            if not line.strip():
                count += 1
                continue
            
            indent = self._get_indent(line)
            if indent < expected_indent:
                break
            count += 1
        
        return count
    
    def _split_args(self, args_str: str) -> List[str]:
        """Split function arguments"""
        if not args_str.strip():
            return []
        
        args = []
        current = []
        paren_depth = 0
        in_string = False
        string_char = None
        
        for char in args_str:
            if char in ('"', "'") and not in_string:
                in_string = True
                string_char = char
                current.append(char)
            elif char == string_char and in_string:
                in_string = False
                string_char = None
                current.append(char)
            elif char == '(' and not in_string:
                paren_depth += 1
                current.append(char)
            elif char == ')' and not in_string:
                paren_depth -= 1
                current.append(char)
            elif char == ',' and paren_depth == 0 and not in_string:
                args.append(''.join(current))
                current = []
            else:
                current.append(char)
        
        if current:
            args.append(''.join(current))
        
        return args
    
    def _infer_type(self, value_str: str) -> str:
        """Infer type from value"""
        value_str = value_str.strip()
        
        if value_str.startswith(('"', "'")):
            return 'string'
        if '.' in value_str and value_str.replace('.', '', 1).replace('-', '', 1).isdigit():
            return 'float'
        if value_str.replace('-', '', 1).isdigit():
            return 'int'
        if value_str in ('True', 'False'):
            return 'bool'
        
        return 'int'
    
    def _detect_return_type(self, body: List[Dict]) -> str:
        """Detect return type from function body"""
        for node in body:
            if node.get('type') == 'return':
                ret_val = node.get('value')
                if ret_val is None:
                    return 'void'
                if ret_val.get('dataType'):
                    return ret_val['dataType']
        return 'void'
    
    def _detect_includes(self, nodes: List[Dict]) -> List[str]:
        """Detect required includes"""
        includes = set()
        
        def walk(node):
            if node.get('type') == 'print':
                includes.add('stdio')
            elif node.get('type') == 'input':
                includes.add('stdio')
            elif node.get('type') == 'function':
                for child in node.get('body', []):
                    walk(child)
            elif node.get('type') == 'if':
                for child in node.get('body', []):
                    walk(child)
                for child in node.get('elseBody', []):
                    walk(child)
                for elif_block in node.get('elifs', []):
                    for child in elif_block.get('body', []):
                        walk(child)
            elif node.get('type') in ('while', 'for'):
                for child in node.get('body', []):
                    walk(child)
        
        for node in nodes:
            walk(node)
        
        return list(includes)
