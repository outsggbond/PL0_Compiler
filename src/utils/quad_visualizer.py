# src/utils/quad_visualizer.py
"""四元式执行过程可视化 (第6章语义分析加分项)

根据实验书要求：
- 能够将四元式执行过程可视化
- 包括：跳转控制流、临时变量使用情况

功能：
1. 控制流图 (CFG) — 从四元式序列构建基本块和跳转关系
2. 四元式执行轨迹可视化
3. 临时变量生命周期分析
4. DOT 格式输出 (Graphviz 渲染)
"""

from .quad_generator import QuadGenerator, QuadVM


# ── 基本块 ──────────────────────────────────────────────────────────

class BasicBlock:
    """控制流图中的基本块。"""

    def __init__(self, block_id, label=None):
        self.block_id = block_id
        self.label = label          # 块标签
        self.quads = []             # 块内的四元式 (索引号)
        self.successors = []        # 后继块索引
        self.predecessors = []      # 前驱块索引
        self.is_entry = False
        self.is_exit = False

    def first_quad_idx(self):
        return self.quads[0] if self.quads else -1

    def last_quad_idx(self):
        return self.quads[-1] if self.quads else -1

    def __repr__(self):
        qrange = f"Q{self.first_quad_idx()}..Q{self.last_quad_idx()}" if self.quads else "empty"
        succ = f" → B{','.join(map(str, self.successors))}" if self.successors else ""
        return f"B{self.block_id}({qrange}){succ}"


# ── 控制流图构建 ──────────────────────────────────────────────────

def is_jump_op(op):
    """判断是否为跳转操作。"""
    return op in ('jump', 'j=', 'j#', 'j<', 'j<=', 'j>', 'j>=', 'j!=', 'call', 'ret', 'halt')


def is_conditional_jump(op):
    """判断是否为条件跳转。"""
    return op in ('j=', 'j#', 'j<', 'j<=', 'j>', 'j>=', 'j!=')


def is_unconditional_jump(op):
    """判断是否为无条件跳转。"""
    return op in ('jump',)


def is_terminator(op):
    """判断是否为基本块终止指令。"""
    return is_jump_op(op) or op in ('halt', 'ret')


class ControlFlowGraph:
    """从四元式序列构建控制流图 (CFG)。"""

    def __init__(self, quads):
        """
        Args:
            quads: list of Quad objects (from QuadGenerator.quads)
        """
        self.quads = quads
        self.blocks = []
        self._build()

    def _build(self):
        """构建基本块和边。"""
        if not self.quads:
            return

        # Step 1: 识别基本块的起始指令
        # 起始指令集合: 第一条指令 + 跳转目标 + 跳转指令的下一条
        leaders = {0}
        label_to_quad = {}  # label名称 → 四元式索引

        for i, q in enumerate(self.quads):
            if q.op == 'label':
                label_to_quad[q.result] = i
                leaders.add(i)
            elif is_jump_op(q.op):
                # 跳转指令的下一条是 leader
                if i + 1 < len(self.quads):
                    leaders.add(i + 1)

        # 跳转目标也是 leader
        for i, q in enumerate(self.quads):
            if is_jump_op(q.op) and q.result is not None:
                target = q.result
                if isinstance(target, str):
                    # 可能是标签名，也可能是临时变量 (条件跳转的 true 分支)
                    if target in label_to_quad:
                        leaders.add(label_to_quad[target])

        # Step 2: 从 leader 切分基本块
        leaders = sorted(leaders)
        quad_to_block = {}  # quad_idx -> block
        label_to_block = {}  # label_name -> block

        for i, leader in enumerate(leaders):
            end = leaders[i + 1] if i + 1 < len(leaders) else len(self.quads)
            block = BasicBlock(len(self.blocks))
            block.quads = list(range(leader, end))

            # 检查块内是否有 label 指令
            for qi in block.quads:
                q = self.quads[qi]
                if q.op == 'label':
                    block.label = q.result
                    label_to_block[q.result] = block

            if leader == 0:
                block.is_entry = True

            self.blocks.append(block)
            for qi in block.quads:
                quad_to_block[qi] = block

        # Step 3: 构建边
        for block in self.blocks:
            last_q = self.quads[block.last_quad_idx()] if block.quads else None
            if last_q is None:
                continue

            op = last_q.op

            if op in ('halt', 'ret'):
                block.is_exit = True
                # halt 没有后继

            elif is_conditional_jump(op):
                # 条件跳转: 有两个后继
                # (1) 跳转目标
                target_label = last_q.result
                if target_label in label_to_block:
                    target_block = label_to_block[target_label]
                else:
                    # 查找下一个 label 指令 (回填可能被解析)
                    target_block = None
                if target_block:
                    block.successors.append(target_block.block_id)
                    target_block.predecessors.append(block.block_id)

                # (2) 下一条指令 (fall-through)
                fall_quad = block.last_quad_idx() + 1
                if fall_quad in quad_to_block:
                    fall_block = quad_to_block[fall_quad]
                    # 检查是否和跳转目标相同 (避免重复边)
                    if fall_block.block_id not in block.successors:
                        block.successors.append(fall_block.block_id)
                        fall_block.predecessors.append(block.block_id)

            elif is_unconditional_jump(op):
                target_label = last_q.result
                if target_label in label_to_block:
                    target_block = label_to_block[target_label]
                    block.successors.append(target_block.block_id)
                    target_block.predecessors.append(block.block_id)
                else:
                    # 尝试按索引查找 (回填后的标签如 "L5")
                    pass

            else:
                # 顺序执行: 下一条指令所在块
                fall_quad = block.last_quad_idx() + 1
                if fall_quad in quad_to_block:
                    fall_block = quad_to_block[fall_quad]
                    block.successors.append(fall_block.block_id)
                    fall_block.predecessors.append(fall_block.block_id)

    # ── 可视化输出 ───────────────────────────────────────────────

    def to_dot(self, title="Control Flow Graph"):
        """生成控制流图的 DOT 格式。

        Returns:
            str: DOT format string
        """
        lines = [
            f"// {title}",
            f"digraph CFG {{",
            '  rankdir=TB;',
            '  node [shape=record, style=filled, fontname="Courier New", fontsize=10];',
            '  edge [fontname="Courier New", fontsize=9];',
            '',
        ]

        for block in self.blocks:
            # 构建块标签
            quad_lines = []
            for qi in block.quads[:8]:  # 最多显示8条
                q = self.quads[qi]
                quad_lines.append(f"  [{qi:2d}] {q}")
            if len(block.quads) > 8:
                quad_lines.append(f"  ... (+{len(block.quads) - 8} more)")

            label = f"B{block.block_id}"
            if block.label:
                label += f" ({block.label})"
            if block.is_entry:
                label += "\\n[ENTRY]"
            if block.is_exit:
                label += "\\n[EXIT]"

            label = label + "\\n" + "\\n".join(quad_lines)

            # 颜色
            if block.is_entry:
                fill = "#D4EDDA"  # green
            elif block.is_exit:
                fill = "#F8D7DA"  # red
            elif block.successors:
                fill = "#E8F0FE"  # blue
            else:
                fill = "#FFFFFF"

            lines.append(f'  B{block.block_id} [label="{label}", fillcolor="{fill}"];')

        lines.append("")

        # 边
        drawn_edges = set()
        for block in self.blocks:
            for succ_id in block.successors:
                edge_key = (block.block_id, succ_id)
                if edge_key in drawn_edges:
                    continue
                drawn_edges.add(edge_key)

                # 判断是否为回边 (循环)
                is_back = succ_id <= block.block_id
                if is_back:
                    style = 'style="dashed" color="#CC3333" constraint=false'
                else:
                    style = 'style="solid"'

                # 判断是否为条件跳转 (查找对应四元式)
                last_q = self.quads[block.last_quad_idx()] if block.quads else None
                edge_label = ""
                if last_q and is_conditional_jump(last_q.op):
                    # 确定这是 true 分支还是 fall-through
                    if last_q.result:
                        # 这是条件为真的目标
                        edge_label = last_q.op
                    else:
                        edge_label = "else"

                lines.append(f'  B{block.block_id} -> B{succ_id} [{style}, label="{edge_label}"];')

        lines.append("}")
        return "\n".join(lines)

    def to_ascii(self):
        """生成控制流图的 ASCII 文本表示。

        Returns:
            str: ASCII CFG
        """
        lines = []
        lines.append("=" * 70)
        lines.append("  CONTROL FLOW GRAPH (CFG)")
        lines.append("-" * 70)

        for block in self.blocks:
            label_str = f" ({block.label})" if block.label else ""
            entry_str = " [ENTRY]" if block.is_entry else ""
            exit_str = " [EXIT]" if block.is_exit else ""
            lines.append(f"\n  B{block.block_id}{label_str}{entry_str}{exit_str}:")

            for qi in block.quads:
                lines.append(f"    [{qi:3d}] {self.quads[qi]}")

            succ_str = ", ".join(f"B{s}" for s in block.successors) if block.successors else "none"
            pred_str = ", ".join(f"B{p}" for p in block.predecessors) if block.predecessors else "none"
            lines.append(f"    pred: [{pred_str}]  succ: [{succ_str}]")

        lines.append("")
        lines.append("=" * 70)

        # 简易流程图
        lines.append("\n  CFG 结构:")
        for block in self.blocks:
            for succ_id in block.successors:
                lines.append(f"    B{block.block_id} → B{succ_id}")
        lines.append("")
        return "\n".join(lines)

    def to_dict(self):
        """导出 CFG 为结构化字典。"""
        blocks_data = []
        for block in self.blocks:
            quads_data = []
            for qi in block.quads:
                q = self.quads[qi]
                quads_data.append({
                    "index": qi,
                    "op": q.op,
                    "arg1": str(q.arg1) if q.arg1 is not None else None,
                    "arg2": str(q.arg2) if q.arg2 is not None else None,
                    "result": str(q.result) if q.result is not None else None,
                })

            blocks_data.append({
                "id": block.block_id,
                "label": block.label,
                "is_entry": block.is_entry,
                "is_exit": block.is_exit,
                "quads": quads_data,
                "successors": block.successors,
                "predecessors": block.predecessors,
            })

        return {"blocks": blocks_data, "num_blocks": len(self.blocks)}


# ── 四元式执行轨迹可视化 ──────────────────────────────────────────

class QuadExecutionVisualizer:
    """四元式执行过程可视化。

    使用 QuadVM 执行四元式序列，并生成：
    - 执行轨迹追踪
    - 变量状态变化
    - 跳转路径图
    """

    def __init__(self, quads, input_values=None):
        """
        Args:
            quads: list of Quad objects
            input_values: list of input values for 'read' operations
        """
        self.quads = quads
        self.input_values = input_values or []
        self.vm = QuadVM(quads, input_values)

    def run(self):
        """执行并获取跟踪轨迹。"""
        self.trace = self.vm.run()
        return self.trace

    def to_execution_table(self):
        """生成执行过程表格 (ASCII 格式)。

        Returns:
            str: 表格文本
        """
        if not hasattr(self, 'trace'):
            self.run()

        lines = []
        sep = "=" * 90
        lines.append(sep)
        lines.append(f"{'四元式执行过程':^86s}")
        lines.append("-" * 90)
        lines.append(f"{'PC':>4s} {'操作':>8s} {'arg1':>8s} {'arg2':>8s} {'result':>8s}  |  {'变量状态'}")
        lines.append("-" * 90)

        for pc, q, vars_snap in self.trace:
            a1 = str(q.arg1) if q.arg1 is not None else '_'
            a2 = str(q.arg2) if q.arg2 is not None else '_'
            r = str(q.result) if q.result is not None else '_'
            vars_str = ", ".join(f"{k}={v}" for k, v in sorted(vars_snap.items())[:6])
            if len(vars_snap) > 6:
                vars_str += f", ...({len(vars_snap)} vars)"
            lines.append(f"  {pc:3d} {q.op:>8s} {a1:>8s} {a2:>8s} {r:>8s}  |  {vars_str}")

        lines.append(sep)
        return "\n".join(lines)

    def to_control_flow_trace(self):
        """生成控制流跳转轨迹 (仅显示跳转指令)。

        Returns:
            str: 跳转轨迹文本
        """
        if not hasattr(self, 'trace'):
            self.run()

        lines = []
        lines.append("═══ 控制流跳转轨迹 ═══")
        lines.append("")

        for pc, q, vars_snap in self.trace:
            if is_jump_op(q.op):
                a1 = str(q.arg1) if q.arg1 is not None else '_'
                a2 = str(q.arg2) if q.arg2 is not None else '_'
                target = str(q.result) if q.result is not None else '_'

                if is_conditional_jump(q.op):
                    # 获取条件值
                    val1 = self.vm._get_val(q.arg1) if q.arg1 is not None else '?'
                    val2 = self.vm._get_val(q.arg2) if q.arg2 is not None else '?'
                    taken = self.trace[min(pc + 1, len(self.trace) - 1)][0] != pc + 1 if pc + 1 < len(self.quads) else False
                    lines.append(f"  [{pc:3d}] {q.op} {a1}={val1}, {a2}={val2} → {'TAKEN' if taken else 'FALL-THROUGH'} → {target}")
                else:
                    lines.append(f"  [{pc:3d}] {q.op} → {target}")

        lines.append("")
        return "\n".join(lines)

    def to_dot_trace(self, title="Quad Execution Flow"):
        """生成执行流的 DOT 格式 (实际执行路径高亮)。

        Returns:
            str: DOT format
        """
        if not hasattr(self, 'trace'):
            self.run()

        # 记录实际执行的四元式序列
        executed = [pc for pc, _, _ in self.trace]

        lines = [
            f"// {title}",
            f"digraph QuadExec {{",
            '  rankdir=TB;',
            '  node [shape=box, style=filled, fontname="Courier New", fontsize=10];',
            '  edge [fontname="Courier New", fontsize=9];',
            '',
        ]

        for i, q in enumerate(self.quads):
            fill = "#D4EDDA" if i in executed else "#E2E3E5"
            label = f"[{i:3d}] {q}"
            lines.append(f'  Q{i} [label="{label}", fillcolor="{fill}"];')

        lines.append("")

        # 在跟踪中连接真正执行过的相邻四元式
        for j in range(len(executed) - 1):
            pc = executed[j]
            next_pc = executed[j + 1]
            q = self.quads[pc]
            # 判断边的类型
            if is_conditional_jump(q.op):
                style = 'style="dashed" color="#CC3333"'
                label = q.op
            elif is_unconditional_jump(q.op):
                style = 'style="solid" color="#3366CC"'
                label = "jump"
            else:
                style = 'style="solid" color="#333333"'
                label = ""
            lines.append(f'  Q{pc} -> Q{next_pc} [{style}, label="{label}"];')

        lines.append("}")
        return "\n".join(lines)


# ── 临时变量分析 ──────────────────────────────────────────────────

def analyze_temp_usage(quads):
    """分析四元式序列中临时变量的使用情况。

    Args:
        quads: list of Quad objects

    Returns:
        dict: 分析结果
    """
    temp_defs = {}    # temp_name -> set of (quad_idx where defined)
    temp_uses = {}    # temp_name -> set of (quad_idx where used)
    var_defs = {}
    var_uses = {}

    for i, q in enumerate(quads):
        # 定义点
        if q.result is not None:
            result = str(q.result)
            if result.startswith('T'):
                temp_defs.setdefault(result, set()).add(i)
            elif result != '_' and not is_jump_op(q.op):
                var_defs.setdefault(result, set()).add(i)

        # 使用点
        for arg in (q.arg1, q.arg2):
            if arg is not None:
                arg = str(arg)
                if arg.startswith('T'):
                    temp_uses.setdefault(arg, set()).add(i)
                elif arg != '_' and not arg.isdigit() and not arg.startswith('-'):
                    var_uses.setdefault(arg, set()).add(i)

    # 计算生命周期
    temp_lifetimes = {}
    for t in set(list(temp_defs.keys()) + list(temp_uses.keys())):
        defs = temp_defs.get(t, set())
        uses = temp_uses.get(t, set())
        first_def = min(defs) if defs else -1
        last_use = max(uses) if uses else -1
        temp_lifetimes[t] = {
            "defined_at": sorted(defs),
            "used_at": sorted(uses),
            "live_range": (first_def, last_use) if first_def >= 0 and last_use >= 0 else None,
        }

    return {
        "temp_lifetimes": temp_lifetimes,
        "var_defs": {k: sorted(v) for k, v in var_defs.items()},
        "var_uses": {k: sorted(v) for k, v in var_uses.items()},
        "total_temps": len(temp_defs),
    }


def print_temp_analysis(quads):
    """打印临时变量使用分析。

    Args:
        quads: list of Quad objects

    Returns:
        str: 分析报告
    """
    analysis = analyze_temp_usage(quads)
    lines = []
    sep = "=" * 70
    lines.append(sep)
    lines.append(f"{'临时变量使用情况分析':^66s}")
    lines.append("-" * 70)
    lines.append(f"  临时变量总数: {analysis['total_temps']}")
    lines.append("-" * 70)
    lines.append(f"  {'变量':<10s} {'定义于':<20s} {'使用于':<20s} {'活跃区间'}")
    lines.append("-" * 70)

    for temp, info in sorted(analysis["temp_lifetimes"].items()):
        defs = ", ".join(f"Q{d}" for d in info["defined_at"]) or "-"
        uses = ", ".join(f"Q{u}" for u in info["used_at"]) or "-"
        live = f"Q{info['live_range'][0]}-Q{info['live_range'][1]}" if info['live_range'] else "-"
        lines.append(f"  {temp:<10s} {defs:<20s} {uses:<20s} {live}")

    lines.append(sep)
    return "\n".join(lines)


# ── 便捷入口函数 ──────────────────────────────────────────────────

def visualize_quad_execution(quadgen, input_values=None):
    """便捷函数: 完整可视化四元式执行。

    Args:
        quadgen: QuadGenerator instance (has .quads)
        input_values: optional list of input values

    Returns:
        dict with keys: execution_table, control_flow_trace, cfg_dot, temp_analysis
    """
    quads = quadgen.quads

    # 执行轨迹
    exec_viz = QuadExecutionVisualizer(quads, input_values)
    exec_table = exec_viz.to_execution_table()
    ctrl_trace = exec_viz.to_control_flow_trace()

    # 控制流图
    cfg = ControlFlowGraph(quads)

    # 临时变量分析
    temp_report = print_temp_analysis(quads)

    return {
        "execution_table": exec_table,
        "control_flow_trace": ctrl_trace,
        "cfg_ascii": cfg.to_ascii(),
        "cfg_dot": cfg.to_dot(),
        "exec_dot": exec_viz.to_dot_trace(),
        "temp_analysis": temp_report,
    }


def display_all(quadgen, input_values=None):
    """打印所有可视化输出。"""
    results = visualize_quad_execution(quadgen, input_values)
    print(results["execution_table"])
    print()
    print(results["control_flow_trace"])
    print()
    print(results["cfg_ascii"])
    print()
    print(results["temp_analysis"])
    print()
    print("=== CFG DOT ===")
    print(results["cfg_dot"])
    print()
    print("=== Execution DOT ===")
    print(results["exec_dot"])


# ── 测试入口 ────────────────────────────────────────────────────────
if __name__ == '__main__':
    import sys
    from ..lexer.lexer import Lexer
    from ..parser_ll.ll_parser import LLParser
    from ..semantic_ll.semantic_ll import SemanticLL

    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            source = f.read()
    else:
        source = 'const n=10; var x,y; begin x:=n; y:=x+1; if y#0 then write(x) end.'
        print(f"Usage: python -m src.utils.quad_visualizer <source_file>")
        print(f"Using built-in test:\n---\n{source}\n---\n")

    # 完整编译流程
    lexer = Lexer(source)
    parser = LLParser(lexer)
    tree, parse_errs = parser.parse()
    if parse_errs:
        for e in parse_errs:
            print(f"  [Parse Error] {e}")

    if tree:
        sem = SemanticLL()
        quadgen, sem_errs = sem.analyze(tree)
        if sem_errs:
            for e in sem_errs:
                print(f"  [Semantic Error] {e}")

        quadgen.display()
        display_all(quadgen, input_values=[5, 0])
