"""
Intermediate Representation (IR) Generator
Converts Python AST to a simplified IR for transpilation
"""
import ast
from typing import Dict, List, Any, Tuple

class IRGenerator:
    """Generates intermediate representation from Python code using Python's AST"""
    
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
        try:
            tree = ast.parse(python_code)
            body = self._parse_block(tree.body)
            includes = self._detect_includes(body)
            
            ir = {
                'type': 'program',
                'body': body,
                'includes': includes
            }
            return ir, self.warnings
        except SyntaxError as e:
            self.warnings.append({
                'type': 'error',
                'message': f"Syntax error: {e.msg}",
                'line': e.lineno
            })
            return {'type': 'program', 'body': [], 'includes': []}, self.warnings

    def _parse_block(self, ast_nodes: List[ast.AST]) -> List[Dict]:
        nodes = []
        for node in ast_nodes:
            parsed_node = self._parse_node(node)
            if parsed_node:
                if isinstance(parsed_node, list):
                    nodes.extend(parsed_node)
                else:
                    nodes.append(parsed_node)
        return nodes

    def _parse_node(self, node: ast.AST) -> Any:
        if isinstance(node, ast.FunctionDef):
            params = [{'name': arg.arg, 'inferredType': 'int'} for arg in node.args.args]
            body = self._parse_block(node.body)
            returnType = self._detect_return_type(body)
            return {
                'type': 'function',
                'name': node.name,
                'params': params,
                'returnType': returnType,
                'body': body,
                'line': getattr(node, 'lineno', 0)
            }
        
        elif isinstance(node, ast.If):
            condition = self._parse_expression(node.test)
            body = self._parse_block(node.body)
            
            elifs = []
            elseBody = []
            
            current_orelse = node.orelse
            while current_orelse and len(current_orelse) == 1 and isinstance(current_orelse[0], ast.If):
                elif_node = current_orelse[0]
                elifs.append({
                    'condition': self._parse_expression(elif_node.test),
                    'body': self._parse_block(elif_node.body)
                })
                current_orelse = elif_node.orelse
            
            if current_orelse:
                elseBody = self._parse_block(current_orelse)
                
            return {
                'type': 'if',
                'condition': condition,
                'body': body,
                'elifs': elifs,
                'elseBody': elseBody,
                'line': getattr(node, 'lineno', 0)
            }
        
        elif isinstance(node, ast.While):
            return {
                'type': 'while',
                'condition': self._parse_expression(node.test),
                'body': self._parse_block(node.body),
                'line': getattr(node, 'lineno', 0)
            }
            
        elif isinstance(node, ast.For):
            if isinstance(node.iter, ast.Call) and isinstance(node.iter.func, ast.Name) and node.iter.func.id == 'range':
                args = node.iter.args
                if len(args) == 1:
                    start = {'exprType': 'literal', 'value': 0, 'dataType': 'int'}
                    end = self._parse_expression(args[0])
                else:
                    start = self._parse_expression(args[0])
                    end = self._parse_expression(args[1])
                    
                var_name = node.target.id if isinstance(node.target, ast.Name) else 'i'
                
                return {
                    'type': 'for',
                    'variable': var_name,
                    'start': start,
                    'end': end,
                    'body': self._parse_block(node.body),
                    'line': getattr(node, 'lineno', 0)
                }
            else:
                self.warnings.append({
                    'type': 'warning',
                    'message': "Only 'for x in range(...)' loops are fully supported",
                    'line': getattr(node, 'lineno', 0)
                })
                return None

        elif isinstance(node, ast.Return):
            return {
                'type': 'return',
                'value': self._parse_expression(node.value) if node.value else None,
                'line': getattr(node, 'lineno', 0)
            }
            
        elif isinstance(node, ast.Assign):
            if len(node.targets) == 1 and isinstance(node.targets[0], ast.Tuple):
                if isinstance(node.value, ast.Tuple):
                    t1 = [elt.id for elt in node.targets[0].elts if isinstance(elt, ast.Name)]
                    v1 = [elt.id for elt in node.value.elts if isinstance(elt, ast.Name)]
                    if len(t1) == 2 and len(v1) == 2:
                        return {
                            'type': 'tuple_swap',
                            'targets': t1,
                            'values': v1,
                            'line': getattr(node, 'lineno', 0)
                        }
            
            # Normal assignment
            target_node = node.targets[0]
            if isinstance(target_node, ast.Name):
                target = target_node.id
                
                # Check for input()
                is_input, input_data = self._check_input_call(node.value)
                if is_input:
                    return {
                        'type': 'input',
                        'target': target,
                        'prompt': input_data['prompt'],
                        'inferredType': input_data['type'],
                        'line': getattr(node, 'lineno', 0)
                    }
                
                value = self._parse_expression(node.value)
                inferred = self._infer_type_from_expr(value)
                
                return {
                    'type': 'assign',
                    'target': target,
                    'value': value,
                    'inferredType': inferred,
                    'isDeclaration': True, # Will be refined by semantic analyzer
                    'line': getattr(node, 'lineno', 0)
                }
                
        elif isinstance(node, ast.AugAssign):
            if isinstance(node.target, ast.Name):
                target = node.target.id
                op_map = {ast.Add: '+', ast.Sub: '-', ast.Mult: '*', ast.Div: '/', ast.Mod: '%'}
                op_type = type(node.op)
                if op_type in op_map:
                    val_expr = self._parse_expression(node.value)
                    left_expr = {'exprType': 'variable', 'name': target}
                    bin_op = {
                        'exprType': 'binary_op',
                        'operator': op_map[op_type],
                        'left': left_expr,
                        'right': val_expr
                    }
                    return {
                        'type': 'assign',
                        'target': target,
                        'value': bin_op,
                        'inferredType': self._infer_type_from_expr(val_expr),
                        'isDeclaration': False,
                        'line': getattr(node, 'lineno', 0)
                    }

        elif isinstance(node, ast.Expr):
            if isinstance(node.value, ast.Call):
                if isinstance(node.value.func, ast.Name) and node.value.func.id == 'print':
                    return {
                        'type': 'print',
                        'args': [self._parse_expression(arg) for arg in node.value.args],
                        'line': getattr(node, 'lineno', 0)
                    }
                else:
                    return {
                        'type': 'expr_stmt',
                        'value': self._parse_expression(node.value),
                        'line': getattr(node, 'lineno', 0)
                    }

        return None

    def _check_input_call(self, node: ast.AST) -> Tuple[bool, Dict]:
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id == 'input':
                prompt = self._parse_expression(node.args[0]) if node.args else None
                return True, {'prompt': prompt, 'type': 'string'}
            elif node.func.id in ('int', 'float') and node.args and isinstance(node.args[0], ast.Call):
                inner_call = node.args[0]
                if isinstance(inner_call.func, ast.Name) and inner_call.func.id == 'input':
                    prompt = self._parse_expression(inner_call.args[0]) if inner_call.args else None
                    return True, {'prompt': prompt, 'type': node.func.id}
        return False, {}

    def _parse_expression(self, expr: ast.AST) -> Dict:
        if isinstance(expr, ast.Constant):
            if isinstance(expr.value, str):
                return {'exprType': 'literal', 'value': expr.value, 'dataType': 'string'}
            elif isinstance(expr.value, bool):
                return {'exprType': 'literal', 'value': expr.value, 'dataType': 'bool'}
            elif isinstance(expr.value, float):
                return {'exprType': 'literal', 'value': expr.value, 'dataType': 'float'}
            elif isinstance(expr.value, int):
                return {'exprType': 'literal', 'value': expr.value, 'dataType': 'int'}
                
        elif isinstance(expr, ast.Name):
            return {'exprType': 'variable', 'name': expr.id}
            
        elif isinstance(expr, ast.BinOp):
            op_map = {
                ast.Add: '+', ast.Sub: '-', ast.Mult: '*', ast.Div: '/', ast.Mod: '%'
            }
            op_str = op_map.get(type(expr.op), '+')
            return {
                'exprType': 'binary_op',
                'operator': op_str,
                'left': self._parse_expression(expr.left),
                'right': self._parse_expression(expr.right)
            }
            
        elif isinstance(expr, ast.BoolOp):
            op_str = 'and' if isinstance(expr.op, ast.And) else 'or'
            # Convert multi-value bool ops to nested binary ops
            res = self._parse_expression(expr.values[-1])
            for val in reversed(expr.values[:-1]):
                res = {
                    'exprType': 'binary_op',
                    'operator': op_str,
                    'left': self._parse_expression(val),
                    'right': res
                }
            return res
            
        elif isinstance(expr, ast.Compare):
            op_map = {
                ast.Eq: '==', ast.NotEq: '!=', ast.Lt: '<', ast.LtE: '<=', ast.Gt: '>', ast.GtE: '>='
            }
            if expr.ops:
                op_str = op_map.get(type(expr.ops[0]), '==')
                return {
                    'exprType': 'binary_op',
                    'operator': op_str,
                    'left': self._parse_expression(expr.left),
                    'right': self._parse_expression(expr.comparators[0])
                }
                
        elif isinstance(expr, ast.Call):
            if isinstance(expr.func, ast.Name):
                return {
                    'exprType': 'call',
                    'function': expr.func.id,
                    'args': [self._parse_expression(arg) for arg in expr.args]
                }
                
        return {'exprType': 'literal', 'value': '', 'dataType': 'string'}

    def _infer_type_from_expr(self, expr: Dict) -> str:
        if not expr: return 'int'
        if expr.get('exprType') == 'literal':
            return expr.get('dataType', 'int')
        if expr.get('exprType') == 'binary_op':
            l_type = self._infer_type_from_expr(expr.get('left', {}))
            r_type = self._infer_type_from_expr(expr.get('right', {}))
            if l_type == 'float' or r_type == 'float': return 'float'
            if l_type == 'string' or r_type == 'string': return 'string'
            return l_type
        return 'int'

    def _detect_return_type(self, body: List[Dict]) -> str:
        for node in body:
            if node.get('type') == 'return':
                val = node.get('value')
                if val:
                    return self._infer_type_from_expr(val)
        return 'void'

    def _detect_includes(self, nodes: List[Dict]) -> List[str]:
        includes = set()
        def walk(node):
            if node.get('type') in ('print', 'input'):
                includes.add('stdio')
            elif node.get('type') == 'function':
                for child in node.get('body', []): walk(child)
            elif node.get('type') == 'if':
                for child in node.get('body', []): walk(child)
                for child in node.get('elseBody', []): walk(child)
                for elif_block in node.get('elifs', []):
                    for child in elif_block.get('body', []): walk(child)
            elif node.get('type') in ('while', 'for'):
                for child in node.get('body', []): walk(child)
        for node in nodes: walk(node)
        return list(includes)
