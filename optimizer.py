import sys
import argparse
import os
from graphviz import Digraph

class TACInstruction:
    """Represents a Three-Address Code (TAC) instruction."""
    def __init__(self, op, arg1, arg2, result):
        self.op = op         # e.g., '+', '-', '*', '=', 'label', 'goto', 'if_false'
        self.arg1 = arg1     # First operand
        self.arg2 = arg2     # Second operand
        self.result = result # Destination variable or label

    def __repr__(self):
        if self.op == '=':
            return f"{self.result} = {self.arg1}"
        elif self.op in ['+', '-', '*', '/']:
            return f"{self.result} = {self.arg1} {self.op} {self.arg2}"
        elif self.op == 'label':
            return f"{self.result}:"
        elif self.op == 'goto':
            return f"goto {self.result}"
        elif self.op == 'if_false':
            return f"if_false {self.arg1} goto {self.result}"
        return f"{self.result} = {self.op} {self.arg1}"


def parse_tac_file(filepath):
    """Parses a raw text file containing TAC instructions."""
    instructions = []
    if not os.path.exists(filepath):
        print(f"[Error] File not found: {filepath}")
        sys.exit(1)

    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue # Skip empty lines and comments

            # Handle labels (e.g., L1:)
            if line.endswith(':'):
                label_name = line[:-1].strip()
                instructions.append(TACInstruction('label', None, None, label_name))
                continue

            # Handle assignments and operations (e.g., x = 5, t1 = x + y)
            if '=' in line:
                parts = line.split('=')
                dest = parts[0].strip()
                expr = parts[1].strip()

                # Check for binary operations (+, -, *, /)
                ops = ['+', '-', '*', '/']
                found_op = None
                for op in ops:
                    if op in expr:
                        found_op = op
                        break

                if found_op:
                    operands = expr.split(found_op)
                    arg1 = parse_operand(operands[0].strip())
                    arg2 = parse_operand(operands[1].strip())
                    instructions.append(TACInstruction(found_op, arg1, arg2, dest))
                else:
                    # Simple assignment (e.g., x = 5)
                    arg1 = parse_operand(expr)
                    instructions.append(TACInstruction('=', arg1, None, dest))
                continue

            # Handle control flow (e.g., goto L1, if_false i > 10 goto L1 -> simplified)
            if line.startswith('goto '):
                target = line.replace('goto', '').strip()
                instructions.append(TACInstruction('goto', None, None, target))
                continue

            if line.startswith('if_false '):
                # Format: if_false var target
                tokens = line.split()
                if len(tokens) >= 3:
                    cond_var = tokens[1]
                    target = tokens[-1]
                    instructions.append(TACInstruction('if_false', cond_var, None, target))

    return instructions


def parse_operand(val_str):
    """Helper to convert string tokens to proper Python data types (int/float or str)."""
    try:
        if '.' in val_str:
            return float(val_str)
        return int(val_str)
    except ValueError:
        return val_str


class Optimizer:
    def __init__(self, instructions):
        self.instructions = instructions

    def constant_propagation(self):
        """Pass 1: Constant Propagation & Folding"""
        constants = {}
        optimized = []

        for inst in self.instructions:
            if isinstance(inst.arg1, str) and inst.arg1 in constants:
                inst.arg1 = constants[inst.arg1]
            if isinstance(inst.arg2, str) and inst.arg2 in constants:
                inst.arg2 = constants[inst.arg2]

            if inst.op in ['+', '-', '*', '/'] and isinstance(inst.arg1, (int, float)) and isinstance(inst.arg2, (int, float)):
                try:
                    if inst.op == '+': val = inst.arg1 + inst.arg2
                    elif inst.op == '-': val = inst.arg1 - inst.arg2
                    elif inst.op == '*': val = inst.arg1 * inst.arg2
                    elif inst.op == '/': val = inst.arg1 / inst.arg2
                    
                    inst.op = '='
                    inst.arg1 = val
                    inst.arg2 = None
                except ZeroDivisionError:
                    pass

            if inst.op == '=' and isinstance(inst.arg1, (int, float)):
                constants[inst.result] = inst.arg1
            elif inst.result in constants:
                del constants[inst.result]

            optimized.append(inst)
        
        self.instructions = optimized
        return self.instructions

    def loop_invariant_code_motion(self):
        """Pass 2: Loop Invariant Code Motion (LICM)"""
        optimized = []
        i = 0
        while i < len(self.instructions):
            inst = self.instructions[i]
            
            if inst.op == 'label' and str(inst.result).startswith('L'):
                loop_start_idx = i
                loop_label = inst.result
                
                loop_end_idx = -1
                for j in range(i + 1, len(self.instructions)):
                    if self.instructions[j].op == 'goto' and self.instructions[j].result == loop_label:
                        loop_end_idx = j
                        break
                
                if loop_end_idx != -1:
                    loop_body = self.instructions[loop_start_idx:loop_end_idx + 1]
                    modified_in_loop = {b.result for b in loop_body if b.result and b.op != 'label'}

                    invariant_insts = []
                    remaining_body = []
                    
                    for b_inst in loop_body:
                        if b_inst.op in ['+', '-', '*', '/']:
                            arg1_inv = (not isinstance(b_inst.arg1, str)) or (b_inst.arg1 not in modified_in_loop)
                            arg2_inv = (not isinstance(b_inst.arg2, str)) or (b_inst.arg2 not in modified_in_loop)
                            if arg1_inv and arg2_inv:
                                invariant_insts.append(b_inst)
                                continue
                        remaining_body.append(b_inst)

                    optimized.extend(invariant_insts)
                    optimized.extend(remaining_body)
                    i = loop_end_idx + 1
                    continue

            optimized.append(inst)
            i += 1

        self.instructions = optimized
        return self.instructions

    def generate_cfg(self, output_filename="cfg_output"):
        """Generates and renders a visual Control Flow Graph using Graphviz."""
        dot = Digraph(comment='Control Flow Graph', format='png')
        dot.attr(rankdir='TB', size='8,8')

        # Simple Basic Block partitioner based on labels and jumps
        blocks = []
        current_block = []

        for inst in self.instructions:
            if inst.op == 'label':
                if current_block:
                    blocks.append(current_block)
                    current_block = []
            current_block.append(str(inst))
            if inst.op in ['goto', 'if_false']:
                blocks.append(current_block)
                current_block = []
        
        if current_block:
            blocks.append(current_block)

        # Add nodes to graph
        for idx, block in enumerate(blocks):
            block_label = f"Block {idx}\n" + "\n".join(block)
            dot.node(f"B{idx}", block_label, shape="box", style="rounded,filled", fillcolor="lightblue")

        # Add sequential edges between blocks
        for idx in range(len(blocks) - 1):
            dot.edge(f"B{idx}", f"B{idx+1}")

        try:
            dot.render(output_filename, view=False)
            print(f"\n[Success] Control Flow Graph rendered to '{output_filename}.png'")
        except Exception as e:
            print(f"\n[Note] Graphviz binaries not found on system path, but DOT source was created successfully: {e}")


def main():
    parser = argparse.ArgumentParser(description="Compiler Optimization Toolkit CLI")
    parser.add_argument("input_file", type=str, help="Path to raw TAC / assembly text file")
    parser.add_argument("--optimize", action="store_true", help="Run optimization passes")
    parser.add_argument("--cfg", action="store_true", help="Generate Control Flow Graph visualization")
    args = parser.parse_args()

    print(f"Reading TAC instructions from {args.input_file}...")
    instructions = parse_tac_file(args.input_file)

    print("\n=== INITIAL CODE ===")
    for idx, inst in enumerate(instructions):
        print(f"{idx}: {inst}")

    optimizer = Optimizer(instructions)

    if args.optimize:
        print("\n--- Running Optimization Passes ---")
        optimizer.constant_propagation()
        optimizer.loop_invariant_code_motion()

        print("\n=== OPTIMIZED CODE ===")
        for idx, inst in enumerate(optimizer.instructions):
            print(f"{idx}: {inst}")

    if args.cfg:
        optimizer.generate_cfg()


if __name__ == "__main__":
    main()
