import os
from weasyprint import HTML

# Create a professional HTML template with beautiful vector SVGs for all requested diagrams
html_content = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>编译原理词法分析可视化报告</title>
    <style>
        @page {
            size: A4;
            margin: 20mm 15mm;
            @bottom-right {
                content: "第 " counter(page) " 页 / 共 " counter(pages) " 页";
                font-family: "Helvetica Neue", Arial, "PingFang SC", sans-serif;
                font-size: 9pt;
                color: #64748b;
            }
            @bottom-left {
                content: "PL/0 编译原理实验报告 - 词法分析";
                font-family: "Helvetica Neue", Arial, "PingFang SC", sans-serif;
                font-size: 9pt;
                color: #64748b;
            }
        }
        
        body {
            margin: 0;
            padding: 0;
            font-family: "Helvetica Neue", Arial, "PingFang SC", "Microsoft YaHei", sans-serif;
            color: #1e293b;
            background-color: #ffffff;
            line-height: 1.6;
            font-size: 10.5pt;
        }

        h1 {
            font-size: 22pt;
            color: #0f172a;
            text-align: center;
            margin-bottom: 5px;
            padding-bottom: 10px;
            border-bottom: 2px solid #cbd5e1;
        }

        .subtitle {
            text-align: center;
            color: #64748b;
            font-size: 11pt;
            margin-bottom: 30px;
        }

        h2 {
            font-size: 14pt;
            color: #1e3a8a;
            border-left: 4px solid #2563eb;
            padding-left: 10px;
            margin-top: 25px;
            margin-bottom: 15px;
            page-break-after: avoid;
        }

        p {
            margin-bottom: 12px;
            text-indent: 2em;
            color: #334155;
        }

        .diagram-container {
            text-align: center;
            margin: 20px 0;
            page-break-inside: avoid;
        }

        .diagram-title {
            font-size: 10pt;
            font-weight: bold;
            color: #475569;
            margin-top: 8px;
            margin-bottom: 15px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
            font-size: 10pt;
        }

        th {
            background-color: #f1f5f9;
            color: #1e293b;
            font-weight: bold;
            padding: 8px 12px;
            border: 1px solid #cbd5e1;
            text-align: left;
        }

        td {
            padding: 8px 12px;
            border: 1px solid #e2e8f0;
            text-align: left;
        }

        tr:nth-child(even) {
            background-color: #f8fafc;
        }

        .code-block {
            font-family: "Courier New", Courier, monospace;
            background-color: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            padding: 12px;
            font-size: 9.5pt;
            white-space: pre-wrap;
            margin: 15px 0;
        }
        
        .page-break {
            page-break-before: always;
        }
    </style>
</head>
<body>

    <h1>PL/0 词法分析可视化运行报告</h1>
    <div class="subtitle">根据实验书第4章要求自动构建生成</div>

    <h2>1. 词法识别核心流程图</h2>
    <p>词法分析器（Lexer）的核心任务是扫描源程序字符流，过滤空白与注释，并根据状态转移规则切分出合法的 Token 序列。以下展示完整的词法识别逻辑流程图：</p>

    <div class="diagram-container">
        <svg width="550" height="740" style="background: #fafafa; border: 1px solid #e2e8f0; border-radius: 8px;">
            <defs>
                <marker id="arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                    <path d="M 0 1 L 10 5 L 0 9 z" fill="#475569" />
                </marker>
            </defs>
            
            <rect x="210" y="20" width="130" height="35" rx="17.5" fill="#e8f0fe" stroke="#2563eb" stroke-width="1.5"/>
            <text x="275" y="42" font-size="11" text-anchor="middle" font-weight="bold" fill="#1e40af">开始 (GetToken)</text>
            
            <rect x="185" y="85" width="180" height="40" rx="4" fill="#ffffff" stroke="#64748b" stroke-width="1.5"/>
            <text x="275" y="102" font-size="10.5" text-anchor="middle" fill="#1e293b">跳过空白字符</text>
            <text x="275" y="118" font-size="9.5" text-anchor="middle" fill="#64748b">(空格 / 制表符 / 换行)</text>
            
            <rect x="185" y="155" width="180" height="35" rx="4" fill="#ffffff" stroke="#64748b" stroke-width="1.5"/>
            <text x="275" y="177" font-size="10.5" text-anchor="middle" fill="#1e293b">读取当前字符 ch</text>
            
            <polygon points="275,215 375,245 275,275 175,245" fill="#fff3cd" stroke="#d97706" stroke-width="1.5"/>
            <text x="275" y="249" font-size="10.5" text-anchor="middle" fill="#92400e">文件结束 (EOF)?</text>
            
            <rect x="40" y="227" width="100" height="35" rx="4" fill="#d4edda" stroke="#10b981" stroke-width="1.5"/>
            <text x="90" y="249" font-size="10.5" text-anchor="middle" font-weight="bold" fill="#15803d">返回 EOF</text>
            
            <polygon points="275,305 385,335 275,365 165,335" fill="#fff3cd" stroke="#d97706" stroke-width="1.5"/>
            <text x="275" y="339" font-size="10.5" text-anchor="middle" fill="#92400e">注释 // 或 /* ?</text>
            
            <rect x="420" y="315" width="110" height="40" rx="4" fill="#ffffff" stroke="#475569" stroke-width="1.5"/>
            <text x="475" y="332" font-size="10.5" text-anchor="middle" fill="#1e293b">跳过注释内容</text>
            <text x="475" y="347" font-size="9.5" text-anchor="middle" fill="#475569">回到开关重新读</text>
            
            <rect x="175" y="410" width="200" height="230" rx="6" fill="#f1f5f9" stroke="#cbd5e1" stroke-width="1.5"/>
            <text x="275" y="430" font-size="11" text-anchor="middle" font-weight="bold" fill="#334155">字符类型分支判断</text>
            
            <rect x="195" y="450" width="160" height="30" rx="4" fill="#ffffff" stroke="#2563eb" stroke-width="1.2"/>
            <text x="275" y="469" font-size="10" text-anchor="middle" fill="#1e293b">1. 字母 → 识别标识符/保留字</text>
            
            <rect x="195" y="495" width="160" height="30" rx="4" fill="#ffffff" stroke="#2563eb" stroke-width="1.2"/>
            <text x="275" y="514" font-size="10" text-anchor="middle" fill="#1e293b">2. 数字 → 识别无符号整数</text>
            
            <rect x="195" y="540" width="160" height="30" rx="4" fill="#ffffff" stroke="#2563eb" stroke-width="1.2"/>
            <text x="275" y="559" font-size="10" text-anchor="middle" fill="#1e293b">3. 符号 : / &lt; / &gt; → 双字运算符</text>
            
            <rect x="195" y="585" width="160" height="30" rx="4" fill="#ffffff" stroke="#2563eb" stroke-width="1.2"/>
            <text x="275" y="604" font-size="10" text-anchor="middle" fill="#1e293b">4. 其他算符/界符 → 单字处理</text>
            
            <rect x="195" y="680" width="160" height="35" rx="4" fill="#f8d7da" stroke="#f43f5e" stroke-width="1.5"/>
            <text x="275" y="702" font-size="10.5" text-anchor="middle" font-weight="bold" fill="#991b1b">非法字符报错并跳过</text>

            <line x1="275" y1="55" x2="275" y2="85" stroke="#475569" stroke-width="1.5" marker-end="url(#arrow)" />
            <line x1="275" y1="125" x2="275" y2="155" stroke="#475569" stroke-width="1.5" marker-end="url(#arrow)" />
            <line x1="275" y1="190" x2="275" y2="215" stroke="#475569" stroke-width="1.5" marker-end="url(#arrow)" />
            
            <line x1="175" y1="245" x2="140" y2="245" stroke="#475569" stroke-width="1.5" marker-end="url(#arrow)" />
            <text x="158" y="238" font-size="9.5" fill="#15803d" font-weight="bold">是</text>
            <line x1="275" y1="275" x2="275" y2="305" stroke="#475569" stroke-width="1.5" marker-end="url(#arrow)" />
            <text x="282" y="292" font-size="9.5" fill="#b45309" font-weight="bold">否</text>
            
            <line x1="385" y1="335" x2="420" y2="335" stroke="#475569" stroke-width="1.5" marker-end="url(#arrow)" />
            <text x="400" y="328" font-size="9.5" fill="#15803d" font-weight="bold">是</text>
            
            <path d="M 475 315 L 475 65 L 275 65 L 275 85" fill="none" stroke="#475569" stroke-width="1.2" marker-end="url(#arrow)"/>
            
            <line x1="275" y1="365" x2="275" y2="410" stroke="#475569" stroke-width="1.5" marker-end="url(#arrow)" />
            <text x="282" y="388" font-size="9.5" fill="#b45309" font-weight="bold">否</text>
            
            <line x1="275" y1="640" x2="275" y2="680" stroke="#475569" stroke-width="1.5" marker-end="url(#arrow)" />
            <text x="282" y="660" font-size="9.5" fill="#991b1b">不匹配</text>
        </svg>
        <div class="diagram-title">图 1.1 PL/0 词法分析主调度流程图</div>
    </div>

    <div class="page-break"></div>

    <h2>2. 状态转换图 (DFA 可视化)</h2>
    <p>依据正规式设计确定有限自动机（DFA），以下分别为标识符识别、数字识别、以及针对 PL/0 语言完整算符界符进行状态合并后的全景有限自动机状态转换图。</p>

    <h3>2.1 标识符 DFA 状态转换图</h3>
    <div class="diagram-container">
        <svg width="450" height="120" style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 6px;">
            <defs>
                <marker id="arrow2" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                    <path d="M 0 1 L 10 5 L 0 9 z" fill="#475569" />
                </marker>
            </defs>
            <line x1="30" y1="60" x2="70" y2="60" stroke="#475569" stroke-width="1.5" marker-end="url(#arrow2)" />
            <circle cx="95" cy="60" r="22" fill="#e8f0fe" stroke="#2563eb" stroke-width="2" />
            <text x="95" y="64" font-family="monospace" font-size="11" text-anchor="middle" font-weight="bold" fill="#1e3a8a">S0</text>
            
            <line x1="117" y1="60" x2="210" y2="60" stroke="#475569" stroke-width="1.5" marker-end="url(#arrow2)" />
            <text x="160" y="52" font-size="10" text-anchor="middle" fill="#334155">letter</text>
            
            <circle cx="235" cy="60" r="22" fill="#d4edda" stroke="#10b981" stroke-width="2" />
            <circle cx="235" cy="60" r="18" fill="none" stroke="#10b981" stroke-width="1.2" />
            <text x="235" y="64" font-family="monospace" font-size="11" text-anchor="middle" font-weight="bold" fill="#065f46">S1</text>
            
            <path d="M 225 40 C 210 10, 260 10, 245 40" fill="none" stroke="#475569" stroke-width="1.5" marker-end="url(#arrow2)" />
            <text x="235" y="8" font-size="9.5" text-anchor="middle" fill="#334155">letter / digit</text>
        </svg>
        <div class="diagram-title">图 2.1 标识符识别有限自动机 (IDENT_DFA)</div>
    </div>

    <h3>2.2 无符号整数 DFA 状态转换图</h3>
    <div class="diagram-container">
        <svg width="450" height="120" style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 6px;">
            <line x1="30" y1="60" x2="70" y2="60" stroke="#475569" stroke-width="1.5" marker-end="url(#arrow2)" />
            <circle cx="95" cy="60" r="22" fill="#e8f0fe" stroke="#2563eb" stroke-width="2" />
            <text x="95" y="64" font-family="monospace" font-size="11" text-anchor="middle" font-weight="bold" fill="#1e3a8a">S0</text>
            
            <line x1="117" y1="60" x2="210" y2="60" stroke="#475569" stroke-width="1.5" marker-end="url(#arrow2)" />
            <text x="160" y="52" font-size="10" text-anchor="middle" fill="#334155">digit</text>
            
            <circle cx="235" cy="60" r="22" fill="#d4edda" stroke="#10b981" stroke-width="2" />
            <circle cx="235" cy="60" r="18" fill="none" stroke="#10b981" stroke-width="1.2" />
            <text x="235" y="64" font-family="monospace" font-size="11" text-anchor="middle" font-weight="bold" fill="#065f46">S2</text>
            
            <path d="M 225 40 C 210 10, 260 10, 245 40" fill="none" stroke="#475569" stroke-width="1.5" marker-end="url(#arrow2)" />
            <text x="235" y="8" font-size="9.5" text-anchor="middle" fill="#334155">digit</text>
        </svg>
        <div class="diagram-title">图 2.2 无符号整数识别有限自动机 (NUMBER_DFA)</div>
    </div>

    <h3>2.3 PL/0 词法分析完整自动机 (合并全景视图)</h3>
    <p>下图展示了将单字符算符、双字符算符（<code>:=</code>, <code>&lt;=</code>, <code>&gt;=</code>）以及标识符、数字自动机合并后的统一高效状态转换矩阵：</p>

    <div class="diagram-container">
        <svg width="560" height="420" style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 6px;">
            <line x1="15" y1="200" x2="45" y2="200" stroke="#475569" stroke-width="1.5" marker-end="url(#arrow2)" />
            <circle cx="70" cy="200" r="22" fill="#e8f0fe" stroke="#2563eb" stroke-width="2" />
            <text x="70" y="204" font-family="monospace" font-size="11" text-anchor="middle" font-weight="bold" fill="#1e3a8a">S0</text>
            
            <circle cx="260" cy="45" r="20" fill="#d4edda" stroke="#10b981" stroke-width="2" />
            <circle cx="260" cy="45" r="16" fill="none" stroke="#10b981" stroke-width="1" />
            <text x="260" y="49" font-family="monospace" font-size="10" text-anchor="middle" fill="#065f46">S1</text>
            <path d="M 85 185 L 242 55" fill="none" stroke="#475569" stroke-width="1.2" marker-end="url(#arrow2)"/>
            <text x="145" y="110" font-size="9.5" fill="#334155">letter</text>
            <path d="M 253 26 C 245 5, 275 5, 267 26" fill="none" stroke="#475569" stroke-width="1" marker-end="url(#arrow2)" />
            <text x="260" y="2" font-size="8.5" text-anchor="middle" fill="#475569">letter/digit</text>

            <circle cx="260" cy="105" r="20" fill="#d4edda" stroke="#10b981" stroke-width="2" />
            <circle cx="260" cy="105" r="16" fill="none" stroke="#10b981" stroke-width="1" />
            <text x="260" y="109" font-family="monospace" font-size="10" text-anchor="middle" fill="#065f46">S2</text>
            <path d="M 90 190 L 242 115" fill="none" stroke="#475569" stroke-width="1.2" marker-end="url(#arrow2)"/>
            <text x="155" y="147" font-size="9.5" fill="#334155">digit</text>
            <path d="M 253 86 C 245 65, 275 65, 267 86" fill="none" stroke="#475569" stroke-width="1" marker-end="url(#arrow2)" />
            <text x="260" y="62" font-size="8.5" text-anchor="middle" fill="#475569">digit</text>

            <circle cx="480" cy="200" r="22" fill="#d4edda" stroke="#10b981" stroke-width="2" />
            <circle cx="480" cy="200" r="18" fill="none" stroke="#10b981" stroke-width="1.2" />
            <text x="480" y="204" font-family="monospace" font-size="10" text-anchor="middle" fill="#065f46">S3</text>
            
            <path d="M 92 200 L 458 200" fill="none" stroke="#475569" stroke-width="1.2" marker-end="url(#arrow2)"/>
            <text x="260" y="194" font-size="9.5" fill="#334155" text-anchor="middle">+, -, *, /, =, #, (, ), ;, ,, .</text>

            <circle cx="260" cy="225" r="20" fill="#ffffff" stroke="#475569" stroke-width="1.5" />
            <text x="260" y="229" font-family="monospace" font-size="10" text-anchor="middle">S4</text>
            <path d="M 90 208 L 240 222" fill="none" stroke="#475569" stroke-width="1.2" marker-end="url(#arrow2)"/>
            <text x="155" y="212" font-size="9.5" fill="#334155">:</text>
            
            <path d="M 280 225 L 458 203" fill="none" stroke="#10b981" stroke-width="1.2" stroke-dasharray="2,2" marker-end="url(#arrow2)"/>
            <text x="370" y="210" font-size="9.5" fill="#15803d">=</text>

            <circle cx="260" cy="295" r="20" fill="#ffffff" stroke="#475569" stroke-width="1.5" />
            <text x="260" y="299" font-family="monospace" font-size="10" text-anchor="middle">S5</text>
            <path d="M 88 215 L 242 285" fill="none" stroke="#475569" stroke-width="1.2" marker-end="url(#arrow2)"/>
            <text x="150" y="258" font-size="9.5" fill="#334155">&lt;</text>
            
            <path d="M 280 295 L 462 215" fill="none" stroke="#10b981" stroke-width="1.2" stroke-dasharray="2,2" marker-end="url(#arrow2)"/>
            <text x="360" y="260" font-size="9.5" fill="#15803d">=</text>

            <circle cx="260" cy="365" r="20" fill="#ffffff" stroke="#475569" stroke-width="1.5" />
            <text x="260" y="369" font-family="monospace" font-size="10" text-anchor="middle">S6</text>
            <path d="M 82 218 L 244 355" fill="none" stroke="#475569" stroke-width="1.2" marker-end="url(#arrow2)"/>
            <text x="140" y="305" font-size="9.5" fill="#334155">&gt;</text>
            
            <path d="M 280 365 L 468 220" fill="none" stroke="#10b981" stroke-width="1.2" stroke-dasharray="2,2" marker-end="url(#arrow2)"/>
            <text x="350" y="310" font-size="9.5" fill="#15803d">=</text>
        </svg>
        <div class="diagram-title">图 2.3 PL/0 全语言词法识别状态合并全景自动机</div>
    </div>

    <h2>3. 状态转换矩阵映射表</h2>
    <table>
        <thead>
            <tr>
                <th>当前状态</th>
                <th>输入字符类型 / 字符</th>
                <th>下一目标状态</th>
                <th>对应输出 Token 类别</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>S0 (初态)</td>
                <td>letter (字母)</td>
                <td>S1</td>
                <td>处理中...</td>
            </tr>
            <tr>
                <td>S1 (接收)</td>
                <td>letter / digit</td>
                <td>S1</td>
                <td>标识符 (Identifier) / 保留字 (Keyword)</td>
            </tr>
            <tr>
                <td>S0 (初态)</td>
                <td>digit (数字)</td>
                <td>S2</td>
                <td>处理中...</td>
            </tr>
            <tr>
                <td>S2 (接收)</td>
                <td>digit</td>
                <td>S2</td>
                <td>无符号整数 (Number)</td>
            </tr>
            <tr>
                <td>S0 (初态)</td>
                <td>:</td>
                <td>S4</td>
                <td>期待匹配 '='</td>
            </tr>
            <tr>
                <td>S4</td>
                <td>=</td>
                <td>S3 (接收)</td>
                <td>赋值算符 (<code>:=</code>)</td>
            </tr>
            <tr>
                <td>S0 (初态)</td>
                <td>&lt;</td>
                <td>S5</td>
                <td>期待匹配 '='</td>
            </tr>
            <tr>
                <td>S5</td>
                <td>=</td>
                <td>S3 (接收)</td>
                <td>小于等于算符 (<code>&lt;=</code>)</td>
            </tr>
        </tbody>
    </table>

</body>
</html>
"""

# Generate real PDF output
output_pdf_path = "lexer_flowchart_visual.pdf"
HTML(string=html_content).write_pdf(output_pdf_path)
print(f"Success: PDF generated at {output_pdf_path}")