#!/usr/bin/env python3
"""Generate comprehensive pedagogical explanations for 2017-2 EJU Math Course 1 (8 questions)."""

import json
from pathlib import Path

math_c1_sections = [
    {
        "q_num": 1,
        "localKey": "math-q-I_1",
        "answer_ref": "MATH_C1:I_1",
        "answer": {
            "ABC": "181",
            "DE": "-2",
            "F": "4",
            "G": "0",
            "HI": "-1",
            "JK": "-1",
            "LM": "-3"
        },
        "title": "大問I 問1：2次関数の決定と最大値・最小値問題",
        "points": [
            "2次関数の平方完成と頂点座標・最小値のパラメータ表示",
            "不等式条件を満たすパラメータ a の変域の決定",
            "軸の位置に応じた最小値 m(a) の最大値・最小値の評価"
        ],
        "solution": (
            "**【題目大意】**\n"
            "2次関数 $f(x) = 2x^2 + ax - 1$ が $f(-1) \\geq -3$ かつ $f(2) \\geq 3$（条件 $\\textcircled{1}$）を満たすとき、$f(x)$ の最小値 $m$ について考える。\n\n"
            "**【公式正解】**\n"
            "- $\\text{ABC} = 181$ ($m = -\\frac{1}{8}a^2 - 1$)\n"
            "- $\\text{DE} = -2, \\text{F} = 4$ ($-2 \\leq a \\leq 4$)\n"
            "- $\\text{G} = 0, \\text{HI} = -1$ (軸 $x = 0$ のとき最大値 $-1$)\n"
            "- $\\text{JK} = -1, \\text{LM} = -3$ (軸 $x = -1$ のとき最小値 $-3$)\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "**(1) $f(x)$ の最小値 $m$ の導出**\n"
            "$f(x)$ を平方完成する：\n"
            "$$f(x) = 2\\left(x^2 + \\frac{a}{2}x\\right) - 1 = 2\\left(x + \\frac{a}{4}\\right)^2 - 2\\left(\\frac{a}{4}\\right)^2 - 1 = 2\\left(x + \\frac{a}{4}\\right)^2 - \\frac{a^2}{8} - 1$$\n"
            "下に凸の放物線であるから、頂点において最小値をとる。\n"
            "$$m = -\\frac{1}{8}a^2 - 1$$\n"
            "よって、$\\text{A} = 1, \\text{B} = 8, \\text{C} = 1$ より $\\mathbf{ABC = 181}$ である。\n\n"
            "**(2) 条件 $\\textcircled{1}$ を満たす $a$ の範囲**\n"
            "条件 $f(-1) \\geq -3$ より：\n"
            "$$f(-1) = 2(-1)^2 + a(-1) - 1 = 2 - a - 1 = 1 - a \\geq -3 \\implies a \\leq 4$$\n"
            "条件 $f(2) \\geq 3$ より：\n"
            "$$f(2) = 2(2)^2 + a(2) - 1 = 8 + 2a - 1 = 2a + 7 \\geq 3 \\implies 2a \\geq -4 \\implies a \\geq -2$$\n"
            "したがって、求める $a$ の値の範囲は：\n"
            "$$-2 \\leq a \\leq 4$$\n"
            "よって、$\\text{DE} = -2, \\text{F} = 4$ である。\n\n"
            "**(3) $m$ の最大値と軸の位置**\n"
            "$m(a) = -\\frac{1}{8}a^2 - 1$ は $a$ についての2次関数（上に凸）であり、$a = 0$ のとき最大値をとる。\n"
            "$a = 0$ は $-2 \\leq a \\leq 4$ の範囲内にある。\n"
            "このとき、放物線 $y = f(x)$ の軸の方程式は：\n"
            "$$x = -\\frac{a}{4} = -\\frac{0}{4} = 0$$\n"
            "そのときの $m$ の最大値は：\n"
            "$$m(0) = -1$$\n"
            "よって、$\\text{G} = 0, \\text{HI} = -1$ である。\n\n"
            "**(4) $m$ の最小値と軸の位置**\n"
            "$m(a) = -\\frac{1}{8}a^2 - 1$ は $a^2$ が最大となるときに最小値をとる。\n"
            "$-2 \\leq a \\leq 4$ において、$a^2$ の最大値は $a = 4$ のときの $4^2 = 16$ である。\n"
            "$a = 4$ のとき、軸の方程式は：\n"
            "$$x = -\\frac{a}{4} = -\\frac{4}{4} = -1$$\n"
            "そのときの $m$ の値は：\n"
            "$$m(4) = -\\frac{16}{8} - 1 = -2 - 1 = -3$$\n"
            "よって、$\\text{JK} = -1, \\text{LM} = -3$ である。"
        )
    },
    {
        "q_num": 2,
        "localKey": "math-q-I_2",
        "answer_ref": "MATH_C1:I_2",
        "answer": {
            "N": "9",
            "OPQ": "754",
            "RSTUV": "13108",
            "WXYZ": "1336"
        },
        "title": "大問I 問2：サイコロの出目による点の移動と推移行列・確率計算",
        "points": [
            "状態遷移規則に基づく各ステップの推移確率",
            "排反な遷移経路の列挙と加法定理",
            "4回以内の累積到達確率の計算"
        ],
        "solution": (
            "**【題目大意】**\n"
            "平面上の三角形 ABC の頂点 A に置かれた球について、サイコロを投げて以下の規則で移動させる：\n"
            "- A にあるとき：目 1 が出れば B へ移動（確率 $\\frac{1}{6}$）、その他は動かない（確率 $\\frac{5}{6}$）。\n"
            "- B にあるとき：目 4 以下が出れば C へ移動（確率 $\\frac{4}{6} = \\frac{2}{3}$）、その他は動かない（確率 $\\frac{2}{6} = \\frac{1}{3}$）。\n"
            "- C に到達すれば試行を終了する。\n"
            "4回以内に球が C に到達する確率を各投擲回数ごとに求める。\n\n"
            "**【公式正解】**\n"
            "- $\\text{N} = 9$ (2回目に到達する確率 $\\frac{1}{9}$)\n"
            "- $\\text{OPQ} = 754$ (3回目に到達する確率 $\\frac{7}{54}$)\n"
            "- $\\text{RSTUV} = 13108$ (4回目に到達する確率 $\\frac{13}{108}$)\n"
            "- $\\text{WXYZ} = 1336$ (4回以内に到達する合計確率 $\\frac{13}{36}$)\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "**(1) 2回目に C に到達する確率**\n"
            "球が2回目に C に到達するための経路は $A \\rightarrow B \\rightarrow C$ の1通りである：\n"
            "- 1回目：A から B へ移動 $\\rightarrow$ 確率 $\\frac{1}{6}$\n"
            "- 2回目：B から C へ移動 $\\rightarrow$ 確率 $\\frac{2}{3}$\n"
            "求める確率は：\n"
            "$$P(2) = \\frac{1}{6} \\times \\frac{2}{3} = \\frac{2}{18} = \\frac{1}{9}$$\n"
            "よって、$\\mathbf{N = 9}$ である。\n\n"
            "**(2) 3回目に C に到達する確率**\n"
            "3回目に C に到達する経路は以下の2つの互いに排反な場合がある：\n"
            "1. $A \\rightarrow A \\rightarrow B \\rightarrow C$（1回目 A に留まり、2回目 B へ、3回目 C へ）：\n"
            "   $$P_1 = \\frac{5}{6} \\times \\frac{1}{6} \\times \\frac{2}{3} = \\frac{10}{108} = \\frac{5}{54}$$\n"
            "2. $A \\rightarrow B \\rightarrow B \\rightarrow C$（1回目 B へ、2回目 B に留まり、3回目 C へ）：\n"
            "   $$P_2 = \\frac{1}{6} \\times \\frac{1}{3} \\times \\frac{2}{3} = \\frac{2}{54}$$\n"
            "合計の確率は：\n"
            "$$P(3) = \\frac{5}{54} + \\frac{2}{54} = \\frac{7}{54}$$\n"
            "よって、$\\mathbf{OPQ = 754}$ である。\n\n"
            "**(3) 4回目に C に到達する確率**\n"
            "4回目に C に到達する経路は以下の3つの互いに排反な場合がある：\n"
            "1. $A \\rightarrow A \\rightarrow A \\rightarrow B \\rightarrow C$：\n"
            "   $$\\left(\\frac{5}{6}\\right)^2 \\times \\frac{1}{6} \\times \\frac{2}{3} = \\frac{25}{36} \\times \\frac{1}{9} = \\frac{25}{324}$$\n"
            "2. $A \\rightarrow A \\rightarrow B \\rightarrow B \\rightarrow C$：\n"
            "   $$\\frac{5}{6} \\times \\frac{1}{6} \\times \\frac{1}{3} \\times \\frac{2}{3} = \\frac{10}{324}$$\n"
            "3. $A \\rightarrow B \\rightarrow B \\rightarrow B \\rightarrow C$：\n"
            "   $$\\frac{1}{6} \\times \\left(\\frac{1}{3}\\right)^2 \\times \\frac{2}{3} = \\frac{1}{6} \\times \\frac{2}{27} = \\frac{4}{324}$$\n"
            "合計の確率は：\n"
            "$$P(4) = \\frac{25 + 10 + 4}{324} = \\frac{39}{324} = \\frac{13}{108}$$\n"
            "よって、$\\mathbf{RSTUV = 13108}$ である。\n\n"
            "**(4) 4回以内に C に到達する全確率**\n"
            "これらはすべて互いに排反であるから、確率の和をとる：\n"
            "$$P(\\leq 4) = P(2) + P(3) + P(4) = \\frac{1}{9} + \\frac{7}{54} + \\frac{13}{108} = \\frac{12 + 14 + 13}{108} = \\frac{39}{108} = \\frac{13}{36}$$\n"
            "よって、$\\mathbf{WXYZ = 1336}$ である。"
        )
    },
    {
        "q_num": 3,
        "localKey": "math-q-II_1",
        "answer_ref": "MATH_C1:II_1",
        "answer": {
            "AB": "51",
            "CDE": "625",
            "F": "2",
            "GH": "-4",
            "I": "2",
            "JK": "51",
            "L": "2"
        },
        "title": "大問II 問1：根号を含む式の分母有理化と2次方程式・1次不等式の整数解条件",
        "points": [
            "共役無理数を用いた分母の有理化",
            "無理数と有理数の相等条件（a + b√5 = 0 の係数比較）",
            "2次方程式の解が1次不等式を満たすための整数パラメータ p の下限評価"
        ],
        "solution": (
            "**【題目大意】**\n"
            "方程式 $x^2 + ax + b = 0$ …… $\\textcircled{1}$ と不等式 $x + 1 < 2x + p + 3$ …… $\\textcircled{2}$ を考える。\n"
            "(1) $x = \\frac{\\sqrt{5} + 3}{\\sqrt{5} + 2}$ を有理化して $\\textcircled{1}$ の係数 $a, b$ を決定する。\n"
            "(2) $\\textcircled{1}$ の2解がともに $\\textcircled{2}$ を満たす最小の整数 $p$ を求める。\n\n"
            "**【公式正解】**\n"
            "- $\\text{AB} = 51$ ($x = \\sqrt{5} - \\sqrt{1}$)\n"
            "- $\\text{CDE} = 625$ ($-a + b + 6 + (a - 2)\\sqrt{5} = 0$)\n"
            "- $\\text{F} = 2, \\text{GH} = -4$ ($a = 2, b = -4$)\n"
            "- $\\text{I} = 2$ ($x > -p - 2$)\n"
            "- $\\text{JK} = 51$ ($p > \\sqrt{5} - 1$)\n"
            "- $\\text{L} = 2$ (最小の整数 $p = 2$)\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "**(1) 分母の有理化と係数 $a, b$ の決定**\n"
            "$x$ の分母・分子に $\\sqrt{5} - 2$ を掛けて分母を有理化する：\n"
            "$$x = \\frac{(\\sqrt{5} + 3)(\\sqrt{5} - 2)}{(\\sqrt{5} + 2)(\\sqrt{5} - 2)} = \\frac{5 - 2\\sqrt{5} + 3\\sqrt{5} - 6}{5 - 4} = \\sqrt{5} - 1$$\n"
            "形式 $x = \\sqrt{A} - \\sqrt{B}$ より、$\\mathbf{AB = 51}$ である。\n\n"
            "この $x = \\sqrt{5} - 1$ を方程式 $\\textcircled{1}$ に代入する：\n"
            "$$(\\sqrt{5} - 1)^2 + a(\\sqrt{5} - 1) + b = 0$$\n"
            "$$(5 - 2\\sqrt{5} + 1) + a\\sqrt{5} - a + b = 0$$\n"
            "$$(6 - a + b) + (a - 2)\\sqrt{5} = 0$$\n"
            "式を整理すると：\n"
            "$$-a + b + 6 + (a - 2)\\sqrt{5} = 0$$\n"
            "したがって、$\\text{C} = 6, \\text{D} = 2, \\text{E} = 5$ より $\\mathbf{CDE = 625}$ である。\n"
            "$a, b$ は有理数、$\\sqrt{5}$ は無理数であるから：\n"
            "$$a - 2 = 0 \\implies a = 2$$\n"
            "$$-2 + b + 6 = 0 \\implies b = -4$$\n"
            "よって、$\\mathbf{F = 2}, \\mathbf{GH = -4}$ である。\n\n"
            "**(2) 最小の整数 $p$ の決定**\n"
            "不等式 $\\textcircled{2}$ を整理する：\n"
            "$$x + 1 < 2x + p + 3 \\implies x > -p - 2$$\n"
            "よって、$\\mathbf{I = 2}$ である。\n"
            "方程式 $\\textcircled{1}$ は $x^2 + 2x - 4 = 0$ となり、その2解は：\n"
            "$$x = \\frac{-2 \\pm \\sqrt{4 - 4(1)(-4)}}{2} = -1 \\pm \\sqrt{5}$$\n"
            "2つの解がともに $x > -p - 2$ を満たすためには、小さい方の解 $-1 - \\sqrt{5}$ がこの条件を満たせば十分である：\n"
            "$$-1 - \\sqrt{5} > -p - 2$$\n"
            "$$p > \\sqrt{5} - 1$$\n"
            "形式 $p > \\sqrt{J} - K$ より、$\\mathbf{JK = 51}$ である。\n"
            "$\\sqrt{5} \\approx 2.236$ であるから、$\\sqrt{5} - 1 \\approx 1.236$ である。\n"
            "したがって、$p > 1.236$ を満たす最小の整数 $p$ は：\n"
            "$$p = 2$$\n"
            "よって、$\\mathbf{L = 2}$ である。"
        )
    },
    {
        "q_num": 4,
        "localKey": "math-q-II_2",
        "answer_ref": "MATH_C1:II_2",
        "answer": {
            "M": "2",
            "NO": "43",
            "P": "4",
            "Q": "1",
            "R": "1",
            "ST": "74",
            "U": "4"
        },
        "title": "大問II 問2：2次関数の軸の場合分けと閉区間における値域の一致条件",
        "points": [
            "放物線の対称軸の導出",
            "定義域と軸の位置関係に応じた単調増加区間と頂点包含区間の場合分け",
            "端点値・頂点値による連立方程式の解と定義域適格性の検証"
        ],
        "solution": (
            "**【題目大意】**\n"
            "2次関数 $f(x) = \\frac{3}{4}x^2 - 3x + 4$ について、$0 < a < b$ かつ $2 < b$ を満たす実数 $a, b$ に対し、$a \\leq x \\leq b$ における値域が $a \\leq y \\leq b$ となる $a, b$ を求める。\n\n"
            "**【公式正解】**\n"
            "- $\\text{M} = 2$ (軸 $x = 2$)\n"
            "- $\\text{NO} = 43, \\text{P} = 4$ ($a = \\frac{4}{3}, b = 4$)\n"
            "- $\\text{Q} = 1, \\text{R} = 1$ (最小値 $1$ より $a = 1$)\n"
            "- $\\text{ST} = 74, \\text{U} = 4$ ($f(a) = \\frac{7}{4}$, $b = 4$)\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "$f(x)$ を平方完成する：\n"
            "$$f(x) = \\frac{3}{4}(x^2 - 4x) + 4 = \\frac{3}{4}(x - 2)^2 - 3 + 4 = \\frac{3}{4}(x - 2)^2 + 1$$\n"
            "したがって、放物線の軸は $x = 2$ である。よって、$\\mathbf{M = 2}$ である。\n\n"
            "**場合分け(i)：$2 \\leq a$ のとき**\n"
            "区間 $[a, b]$ は軸 $x = 2$ の右側に位置するため、$f(x)$ は単調増加する。\n"
            "したがって、値域が $[a, b]$ となるには $f(a) = a$ かつ $f(b) = b$ が必要である。\n"
            "方程式 $f(x) = x$ を解く：\n"
            "$$\\frac{3}{4}x^2 - 3x + 4 = x \\implies \\frac{3}{4}x^2 - 4x + 4 = 0 \\implies 3x^2 - 16x + 16 = 0$$\n"
            "$$(3x - 4)(x - 4) = 0 \\implies x = \\frac{4}{3}, 4$$\n"
            "$a < b$ より $a = \\frac{4}{3}, b = 4$ を得る。\n"
            "しかし、この $a = \\frac{4}{3} < 2$ は条件 $2 \\leq a$ を満たさない。\n"
            "よって、$\\mathbf{NO = 43}, \\mathbf{P = 4}$ である。\n\n"
            "**場合分け(ii)：$0 < a < 2$ のとき**\n"
            "軸 $x = 2$ は区間 $[a, b]$ の内部に含まれる（$a < 2 < b$）。\n"
            "下に凸であるから、最小値は頂点 $x = 2$ で達成され、その値は $f(2) = 1$ である。\n"
            "値域の最小値が $a$ でなければならないため：\n"
            "$$a = 1$$\n"
            "これは $0 < a < 2$ を満たす。よって、$\\mathbf{Q = 1}, \\mathbf{R = 1}$ である。\n\n"
            "このとき、$f(a) = f(1)$ を計算すると：\n"
            "$$f(1) = \\frac{3}{4}(1)^2 - 3(1) + 4 = \\frac{3}{4} + 1 = \\frac{7}{4}$$\n"
            "$\\frac{7}{4} < b$ であり、また軸 $x = 2$ から各端点までの距離を比較すると、$b > 2$ であるから最大値は $x = b$ でとる。\n"
            "したがって、$f(b) = b$ とならなければならない。\n"
            "$b > 2$ かつ $f(b) = b$ を満たす解は $b = 4$ である。\n"
            "よって、$\\mathbf{ST = 74}, \\mathbf{U = 4}$ である。"
        )
    },
    {
        "q_num": 5,
        "localKey": "math-q-III_1",
        "answer_ref": "MATH_C1:III_1",
        "answer": {
            "AB": "16",
            "C": "4",
            "D": "9",
            "E": "4",
            "F": "2"
        },
        "title": "大問III 前半：集合の共通部分の要素決定（自然数解の絞り込み）",
        "points": [
            "自然数集合 A とその平方集合 B の共通部分の性質",
            "共通部分の要素和の不等式による候補の絞り込み",
            "和集合の総和制約による要素の特定"
        ],
        "solution": (
            "**【題目大意】**\n"
            "$1 < a < b < c < d$ を満たす4つの自然数に対し、$A = \\{a, b, c, d\\}$、$B = \\{a^2, b^2, c^2, d^2\\}$ とする。\n"
            "(i) $A \\cap B$ の要素は2個で、その和は 15 以上 25 以下。\n"
            "(ii) $A \\cup B$ の全要素の和は 300 以下。\n"
            "$A \\cap B = \\{x, y\\}$ ($x < y$) の要素 $x, y$ を決定する。\n\n"
            "**【公式正解】**\n"
            "- $\\text{AB} = 16$ ($y = 16$)\n"
            "- $\\text{C} = 4, \\text{D} = 9$ ($x$ は $4$ または $9$)\n"
            "- $\\text{E} = 4$ ($x = 4$)\n"
            "- $\\text{F} = 2$ ($A$ は $2, 2^2, 2^4$ を含む)\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "$x, y \\in A \\cap B$ であり、$x, y \\in B$ であるから、$x, y$ は完全平方数である。\n"
            "$1 < a < b < c < d$ より、集合 $A$ の最小要素 $a \\geq 2$ であるから、最小の平方数は $2^2 = 4$ 以上である。\n"
            "平方数の候補は $4, 9, 16, 25, 36, \\dots$ である。\n"
            "条件(i)より、$15 \\leq x + y \\leq 25$（$x < y$）である。\n"
            "- もし $y = 16$ ならば、$x = 4$ のとき $x + y = 20$（適）、$x = 9$ のとき $x + y = 25$（適）。\n"
            "- もし $y \\geq 25$ ならば、$x \\geq 4$ より $x + y \\geq 29 > 25$ となり不適。\n"
            "- もし $y \\leq 9$ ならば、$x \\leq 4$ より $x + y \\leq 13 < 15$ となり不適。\n"
            "したがって、必ず $y = 16$ であり、小から順に $x = 4$ または $x = 9$ である。\n"
            "よって、$\\mathbf{AB = 16}, \\mathbf{C = 4}, \\mathbf{D = 9}$ である。\n\n"
            "次に、$x = 4$ か $x = 9$ かを条件(ii)により判定する：\n"
            "1. **$x = 9$ の場合**：\n"
            "   $A \\cap B = \\{9, 16\\}$。これらは $B$ の要素であるから、ある $u, v \\in A$ に対して $u^2 = 9, v^2 = 16$ となる。\n"
            "   すなわち $3, 4 \\in A$ である。\n"
            "   すると $A$ は $3, 4, 9, 16$ の4つの数からなる集合 $A = \\{3, 4, 9, 16\\}$ で確定する。\n"
            "   このとき $B = \\{9, 16, 81, 256\\}$ となる。\n"
            "   $A \\cup B$ の要素は $\\{3, 4, 9, 16, 81, 256\\}$ であり、その総和は：\n"
            "   $$3 + 4 + 9 + 16 + 81 + 256 = 369 > 300$$\n"
            "   これは条件(ii)「300以下」に反する。\n"
            "2. **$x = 4$ の場合**：\n"
            "   $A \\cap B = \\{4, 16\\}$。$4, 16 \\in B$ より、ある $u, v \\in A$ に対し $u^2 = 4, v^2 = 16$ であるから、$2, 4 \\in A$。\n"
            "   さらに $16 \\in A$ であるから、$A$ は $2, 4, 16$（すなわち $2, 2^2, 2^4$）を含む。\n"
            "したがって、$x = 4$ であり、$A$ は $2, 2^2, 2^4$ を含む。\n"
            "よって、$\\mathbf{E = 4}, \\mathbf{F = 2}$ である。"
        )
    },
    {
        "q_num": 6,
        "localKey": "math-q-III_2",
        "answer_ref": "MATH_C1:III_2",
        "answer": {
            "GH": "22",
            "I": "3",
            "JKLMN": "23416"
        },
        "title": "大問III 後半：和集合の総和の不等式評価と全要素の同定",
        "points": [
            "残る要素 z を含む和集合の総和の定式化",
            "2次不等式による z の絞り込み",
            "4つの自然数 a, b, c, d の完全同定"
        ],
        "solution": (
            "**【題目大意】**\n"
            "$A = \\{2, 4, 16, z\\}$ とおくとき、条件(ii)の不等式から残る要素 $z$ を求め、$a, b, c, d$ を決定する。\n\n"
            "**【公式正解】**\n"
            "- $\\text{GH} = 22$ ($z^2 + z \\leq 22$)\n"
            "- $\\text{I} = 3$ ($z = 3$)\n"
            "- $\\text{JKLMN} = 23416$ ($a = 2, b = 3, c = 4, d = 16$)\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "$A$ の要素は $2, 4, 16$ と未知の自然数 $z$ である：\n"
            "$$A = \\{2, 4, 16, z\\}$$\n"
            "このとき：\n"
            "$$B = \\{4, 16, 256, z^2\\}$$\n"
            "$A \\cap B = \\{4, 16\\}$ であるから、$z \\neq 2, 4, 16$ かつ $z^2 \\neq 2, 4, 16$。\n"
            "$A \\cup B$ の要素は $\\{2, 4, 16, 256, z, z^2\\}$ である。\n"
            "これらの総和 $S$ は：\n"
            "$$S = 2 + 4 + 16 + 256 + z + z^2 = 278 + z^2 + z$$\n"
            "条件(ii)より $S \\leq 300$ であるから：\n"
            "$$278 + z^2 + z \\leq 300 \\implies z^2 + z \\leq 22$$\n"
            "よって、$\\mathbf{GH = 22}$ である。\n\n"
            "$z$ は $1 < a < b < c < d$ を満たす自然数であり、$z > 1$ である。\n"
            "- $z = 3$ のとき：$3^2 + 3 = 12 \\leq 22$（満たす）\n"
            "- $z = 4$ はすでに $A$ に含まれるため不可。\n"
            "- $z = 5$ のとき：$5^2 + 5 = 30 > 22$（不適）\n"
            "したがって、$z = 3$ に限定される。\n"
            "よって、$\\mathbf{I = 3}$ である。\n\n"
            "以上より、$A$ の要素を昇順に並べると：\n"
            "$$a = 2, \\quad b = 3, \\quad c = 4, \\quad d = 16$$\n"
            "となり、$1 < 2 < 3 < 4 < 16$ を満たしている。\n"
            "よって、$\\mathbf{JKLMN = 23416}$ である。"
        )
    },
    {
        "q_num": 7,
        "localKey": "math-q-IV_1",
        "answer_ref": "MATH_C1:IV_1",
        "answer": {
            "AB": "78",
            "CDE": "158",
            "FGHIJK": "161515"
        },
        "title": "大問IV 前半：余弦定理・正弦定理と三角形の外接円半径の算出",
        "points": [
            "3辺の長さが与えられた三角形に対する余弦定理の適用",
            "三角関数の相互関係による正弦値の導出",
            "正弦定理を用いた外接円半径の計算と有理化"
        ],
        "solution": (
            "**【題目大意】**\n"
            "三角形 ABC の3辺の長さが $\\text{AB} = 6, \\text{BC} = 8, \\text{CA} = 4$ であるとき、$\\cos \\angle \\text{ABC}, \\sin \\angle \\text{ABC}$ および外接円の半径 $R$ を求める。\n\n"
            "**【公式正解】**\n"
            "- $\\text{AB} = 78$ ($\\cos \\angle \\text{ABC} = \\frac{7}{8}$)\n"
            "- $\\text{CDE} = 158$ ($\\sin \\angle \\text{ABC} = \\frac{\\sqrt{15}}{8}$)\n"
            "- $\\text{FGHIJK} = 161515$ ($R = \\frac{16\\sqrt{15}}{15}$)\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "**(1) $\\cos \\angle \\text{ABC}$ と $\\sin \\angle \\text{ABC}$ の計算**\n"
            "三角形 ABC において辺 CA に対する余弦定理を適用する：\n"
            "$$\\text{CA}^2 = \\text{AB}^2 + \\text{BC}^2 - 2 \\text{AB} \\cdot \\text{BC} \\cos \\angle \\text{ABC}$$\n"
            "$$4^2 = 6^2 + 8^2 - 2(6)(8) \\cos \\angle \\text{ABC}$$\n"
            "$$16 = 36 + 64 - 96 \\cos \\angle \\text{ABC}$$\n"
            "$$96 \\cos \\angle \\text{ABC} = 84 \\implies \\cos \\angle \\text{ABC} = \\frac{84}{96} = \\frac{7}{8}$$\n"
            "よって、$\\mathbf{AB = 78}$ である。\n\n"
            "角 $\\angle \\text{ABC}$ は三角形の内角であるから $\\sin \\angle \\text{ABC} > 0$：\n"
            "$$\\sin \\angle \\text{ABC} = \\sqrt{1 - \\cos^2 \\angle \\text{ABC}} = \\sqrt{1 - \\left(\\frac{7}{8}\\right)^2} = \\sqrt{\\frac{64 - 49}{64}} = \\frac{\\sqrt{15}}{8}$$\n"
            "よって、$\\mathbf{CDE = 158}$ である。\n\n"
            "**(2) 外接円半径 $R$ の導出**\n"
            "正弦定理より：\n"
            "$$\\frac{\\text{CA}}{\\sin \\angle \\text{ABC}} = 2R$$\n"
            "$$2R = \\frac{4}{\\frac{\\sqrt{15}}{8}} = \\frac{32}{\\sqrt{15}}$$\n"
            "$$R = \\frac{16}{\\sqrt{15}} = \\frac{16\\sqrt{15}}{15}$$\n"
            "形式 $\\frac{\\text{FG}\\sqrt{\\text{HI}}}{\\text{JK}}$ より、$\\mathbf{FGHIJK = 161515}$ である。"
        )
    },
    {
        "q_num": 8,
        "localKey": "math-q-IV_2",
        "answer_ref": "MATH_C1:IV_2",
        "answer": {
            "LMNOP": "41515",
            "QRSTUV": "281515",
            "WXYZ": "8155"
        },
        "title": "大問IV 後半：接弦定理と2円の中心を結ぶ線分長の幾何学的導出",
        "points": [
            "垂直二等分線上の直角三角形における三平方の定理による OD の算出",
            "円の接線と半径の直交性を用いた直角三角形の三角比による O'D の導出",
            "同一直線上の線分長 OO' の計算"
        ],
        "solution": (
            "**【題目大意】**\n"
            "2点 B, C を通り直線 AB に接する円の中心を $O'$、外接円の中心を $O$ とする。直線 $OO'$ と辺 BC の交点を D とするとき、線分 OD, O'D および OO' の長さを求める。\n\n"
            "**【公式正解】**\n"
            "- $\\text{LMNOP} = 41515$ ($\\text{OD} = \\frac{4\\sqrt{15}}{15}$)\n"
            "- $\\text{QRSTUV} = 281515$ ($\\text{O'D} = \\frac{28\\sqrt{15}}{15}$)\n"
            "- $\\text{WXYZ} = 8155$ ($\\text{OO'} = \\frac{8\\sqrt{15}}{5}$)\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "**(1) 線分 OD の長さ**\n"
            "外接円 $O$ において、弦 BC の垂直二等分線は中心 $O$ を通る。\n"
            "また、円 $O'$ も2点 B, C を通るため、その中心 $O'$ も弦 BC の垂直二等分線上にある。\n"
            "したがって、直線 $OO'$ は弦 BC の垂直二等分線そのものであり、交点 D は辺 BC の中点である。\n"
            "よって、$\\text{BD} = \\text{CD} = \\frac{\\text{BC}}{2} = 4$ であり、$\\angle \\text{ODB} = 90^\\circ$ である。\n"
            "直角三角形 OBD において、三平方の定理より：\n"
            "$$\\text{OD} = \\sqrt{R^2 - \\text{BD}^2} = \\sqrt{\\left(\\frac{16}{\\sqrt{15}}\\right)^2 - 4^2} = \\sqrt{\\frac{256}{15} - \\frac{240}{15}} = \\sqrt{\\frac{16}{15}} = \\frac{4}{\\sqrt{15}} = \\frac{4\\sqrt{15}}{15}$$\n"
            "よって、$\\mathbf{LMNOP = 41515}$ である。\n\n"
            "**(2) 線分 O'D の長さ**\n"
            "円 $O'$ は点 B で直線 AB に接するから、半径 $O'B$ は直線 AB と直交する：\n"
            "$$\\angle O'BA = 90^\\circ$$\n"
            "一方、$\\angle DBA = \\angle \\text{ABC}$ であるから：\n"
            "$$\\angle O'BD = \\angle O'BA - \\angle DBA = 90^\\circ - \\angle \\text{ABC}$$\n"
            "直角三角形 $O'DB$ において $\\angle O'DB = 90^\\circ$ であるから：\n"
            "$$\\tan \\angle O'BD = \\frac{\\text{O'D}}{\\text{BD}} = \\tan(90^\\circ - \\angle \\text{ABC}) = \\frac{1}{\\tan \\angle \\text{ABC}} = \\frac{\\cos \\angle \\text{ABC}}{\\sin \\angle \\text{ABC}}$$\n"
            "$\\text{BD} = 4, \\cos \\angle \\text{ABC} = \\frac{7}{8}, \\sin \\angle \\text{ABC} = \\frac{\\sqrt{15}}{8}$ より：\n"
            "$$\\text{O'D} = 4 \\times \\frac{\\frac{7}{8}}{\\frac{\\sqrt{15}}{8}} = \\frac{28}{\\sqrt{15}} = \\frac{28\\sqrt{15}}{15}$$\n"
            "よって、$\\mathbf{QRSTUV = 281515}$ である。\n\n"
            "**(3) 線分 OO' の長さ**\n"
            "点 A と点 $O$ は直線 BC に対し同じ側にあり、また $\\angle O'BA = 90^\\circ$ かつ $\\angle \\text{ABC} < 90^\\circ$ であることから、$O$ と $O'$ は辺 BC の垂線上で D に対して同じ側に位置する。\n"
            "したがって、$\\text{O'D} > \\text{OD}$ より：\n"
            "$$\\text{OO'} = \\text{O'D} - \\text{OD} = \\frac{28\\sqrt{15}}{15} - \\frac{4\\sqrt{15}}{15} = \\frac{24\\sqrt{15}}{15} = \\frac{8\\sqrt{15}}{5}$$\n"
            "形式 $\\frac{\\text{W}\\sqrt{\\text{XY}}}{\\text{Z}}$ より、$\\mathbf{WXYZ = 8155}$ である。"
        )
    }
]

def main():
    work_dir = Path("work/2017-2-math-c1")
    docs_dir = Path("docs/explanations")
    work_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)

    json_path = work_dir / "explanations.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(math_c1_sections, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(math_c1_sections)} questions to {json_path}")

    md_lines = [
        "# 2017-2 EJU 数学（コース1）詳細解答と徹底解説",
        "",
        "**対象試験**：2017年度第2回（2017年11月実施）日本留学試験（EJU）数学コース1  ",
        "**大問構成**：大問I（問1, 問2）、大問II（問1, 問2）、大問III、大問IV（全8小問）  ",
        "**準拠公式正解**：JASSO 公式正解発表完全準拠",
        "",
        "---",
        ""
    ]

    for q in math_c1_sections:
        md_lines.append(f"## {q['title']}")
        md_lines.append(f"- **問題番号**：`{q['localKey']}`")
        md_lines.append(f"- **公式正解**：`{q['answer']}`")
        md_lines.append("- **重要論点**：")
        for pt in q["points"]:
            md_lines.append(f"  - {pt}")
        md_lines.append("")
        md_lines.append(q["solution"])
        md_lines.append("")
        md_lines.append("---")
        md_lines.append("")

    md_path = docs_dir / "2017-2-math-c1-solutions.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))
    print(f"Wrote markdown solutions to {md_path}")

if __name__ == "__main__":
    main()
