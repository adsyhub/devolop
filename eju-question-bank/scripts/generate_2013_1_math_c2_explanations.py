#!/usr/bin/env python3
"""Generate comprehensive pedagogical explanations for 2013-1 EJU Math Course 2 (8 questions)."""

import json
from pathlib import Path

math_c2_questions = [
    {
        "localKey": "math-q-I_1",
        "title": "数学 コース2 第I問 [1]：2次関数の決定と指定区間における単調増加条件",
        "answer": "ABC: -26, DEF: -32, GH: 13, IJ: 32, KLM: -32",
        "points": [
            "2点 $(-1, -8)$ と $(3, 16)$ を通る条件からの係数関係式 $b = -2a + 6$, $c = -3a - 2$ の導出",
            "放物線の軸の方程式 $x = 1 - \\frac{3}{a}$ の導出",
            "区間 $[-1, 3]$ で単調増加するための放物線の軸と開きの向きによる場合分け（$a > 0$ および $a < 0$）"
        ],
        "solution": (
            "**【題目大意】**\n"
            "$x$ の2次関数 $y = ax^2 + bx + c$ が，条件【*】「$x = -1$ で $y = -8$，$x = 3$ で $y = 16$ であり，区間 $-1 \\le x \\le 3$ において $x$ の値が増加すると共に $y$ の値も増加する」を満たすとき，$a, b, c$ の関係式および $a$ のとり得る範囲を求める。\n\n"
            "**【公式正解】**\n"
            "- $b = \\boxed{\\text{AB}} a + \\boxed{\\text{C}} \\implies b = -2a + 6$ （$\\text{ABC} = -26$）\n"
            "- $c = \\boxed{\\text{DE}} a - \\boxed{\\text{F}} \\implies c = -3a - 2$ （$\\text{DEF} = -32$）\n"
            "- 軸の方程式：$x = \\boxed{\\text{G}} - \\frac{\\boxed{\\text{H}}}{a} \\implies x = 1 - \\frac{3}{a}$ （$\\text{GH} = 13$）\n"
            "- $a$ の範囲：$0 < a \\le \\frac{\\boxed{\\text{I}}}{\\boxed{\\text{J}}} \\implies 0 < a \\le \\frac{3}{2}$ （$\\text{IJ} = 32$） または $\\frac{\\boxed{\\text{KL}}}{\\boxed{\\text{M}}} \\le a < 0 \\implies -\\frac{3}{2} \\le a < 0$ （$\\text{KLM} = -32$）\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "1. **2点を通る条件からの $b, c$ の表式**：\n"
            "$y = ax^2 + bx + c$ に対し：\n"
            "- $x = -1$ のとき：$a(-1)^2 + b(-1) + c = -8 \\implies a - b + c = -8 \\quad \\textcircled{A}$\n"
            "- $x = 3$ のとき：$a(3)^2 + b(3) + c = 16 \\implies 9a + 3b + c = 16 \\quad \\textcircled{B}$\n"
            "$\\textcircled{B} - \\textcircled{A}$ より：\n"
            "$$8a + 4b = 24 \\implies 2a + b = 6 \\implies b = -2a + 6$$\n"
            "よって，$\\boxed{\\text{AB}} = -2, \\; \\boxed{\\text{C}} = 6$（$\\text{ABC} = -26$）である。\n\n"
            "これを $\\textcircled{A}$ に代入すると：\n"
            "$$c = -8 - a + b = -8 - a + (-2a + 6) = -3a - 2$$\n"
            "形式 $c = \\boxed{\\text{DE}} a - \\boxed{\\text{F}}$ より：\n"
            "$$\\boxed{\\text{DE}} = -3, \\; \\boxed{\\text{F}} = 2 \\implies \\text{DEF} = -32$$\n\n"
            "2. **放物線の軸の方程式**：\n"
            "$$y = a\\left(x + \\frac{b}{2a}\\right)^2 + c - \\frac{b^2}{4a}$$\n"
            "軸の方程式は：\n"
            "$$x = -\\frac{b}{2a} = -\\frac{-2a + 6}{2a} = 1 - \\frac{3}{a}$$\n"
            "したがって，$\\boxed{\\text{G}} = 1, \\; \\boxed{\\text{H}} = 3$（$\\text{GH} = 13$）である。\n\n"
            "3. **区間 $[-1, 3]$ で単調増加する条件**：\n"
            "- **$a > 0$（下に凸）のとき**：\n"
            "軸が区間の左端以下にあればよい：\n"
            "$$\\text{軸} \\le -1 \\implies 1 - \\frac{3}{a} \\le -1 \\implies \\frac{3}{a} \\ge 2 \\implies a \\le \\frac{3}{2}$$\n"
            "$a > 0$ と合わせて：$0 < a \\le \\frac{3}{2}$（$\\text{IJ} = 32$）。\n\n"
            "- **$a < 0$（上に凸）のとき**：\n"
            "軸が区間の右端以上にあればよい：\n"
            "$$\\text{軸} \\ge 3 \\implies 1 - \\frac{3}{a} \\ge 3 \\implies -\\frac{3}{a} \\ge 2 \\implies a \\ge -\\frac{3}{2}$$\n"
            "$a < 0$ と合わせて：$-\\frac{3}{2} \\le a < 0$（$\\text{KLM} = -32$）。\n\n"
            "**【考査考点】**\n"
            "2次関数の決定，軸の方程式，閉区間における2次関数の単調性の条件分岐。"
        )
    },
    {
        "localKey": "math-q-I_2",
        "title": "数学 コース2 第I問 [2]：区間の集合演算（共通部分・和集合・補集合）と2次不等式",
        "answer": "NO: -3, P: 1, Q: 3, R: 8, ST: -6, U: 1, V: 3, W: 6",
        "points": [
            "共通部分 $A \\cap B = [b, c]$ と 2次不等式 $x^2 - 4x + 3 \\le 0$ の解 $[1, 3]$ の一致（$b = 1, c = 3$）",
            "(1) 和集合 $A \\cup B = [a, d] = [-3, 8]$ からの $a = -3, d = 8$",
            "(2) 差集合 $[a, 1)$ および $(3, d]$ からの $a = -6, d = 6$"
        ],
        "solution": (
            "**【題目大意】**\n"
            "$a < b < c < d$ に対し，$A = [a, c], B = [b, d]$ とする。$A \\cap B = \\{x \\mid x^2 - 4x + 3 \\le 0\\}$ が与えられたとき，(1) $A \\cup B$ および (2) $A \\cap \\overline{B}, \\overline{A} \\cap B$ の条件から $a, b, c, d$ の値を求める。\n\n"
            "**【公式正解】**\n"
            "- (1) $a = -3, b = 1, c = 3, d = 8$ （$\\text{NO} = -3, \\text{P} = 1, \\text{Q} = 3, \\text{R} = 8$）\n"
            "- (2) $a = -6, b = 1, c = 3, d = 6$ （$\\text{ST} = -6, \\text{U} = 1, \\text{V} = 3, \\text{W} = 6$）\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "1. **共通部分の同定**：\n"
            "$$A \\cap B = [b, c] = \\{x \\mid x^2 - 4x + 3 \\le 0\\} = [1, 3]$$\n"
            "したがって，直ちに $b = 1, c = 3$ である。\n\n"
            "2. **(1) 和集合**：\n"
            "$$A \\cup B = [a, d] = \\{x \\mid x^2 - 5x - 24 \\le 0\\} = [-3, 8]$$\n"
            "したがって，$a = -3, d = 8$ である。\n"
            "$\\boxed{\\text{NO}} = -3, \\; \\boxed{\\text{P}} = 1, \\; \\boxed{\\text{Q}} = 3, \\; \\boxed{\\text{R}} = 8$ となる。\n\n"
            "3. **(2) 差集合・補集合**：\n"
            "- $A \\cap \\overline{B} = [a, b) = [a, 1) = \\{x \\mid x^2 + 5x - 6 \\le 0 \\text{ かつ } x \\neq 1\\} = [-6, 1)$\n"
            "  したがって，$a = -6$ である。\n"
            "- $\\overline{A} \\cap B = (c, d] = (3, d] = \\{x \\mid x^2 - 9x + 18 \\le 0 \\text{ かつ } x \\neq 3\\} = (3, 6]$\n"
            "  したがって，$d = 6$ である。\n"
            "$\\boxed{\\text{ST}} = -6, \\; \\boxed{\\text{U}} = 1, \\; \\boxed{\\text{V}} = 3, \\; \\boxed{\\text{W}} = 6$ となる。\n\n"
            "**【考査考点】**\n"
            "実数直線の区間表現，集合演算（共通部分・和集合・補集合），2次不等式の解。"
        )
    },
    {
        "localKey": "math-q-II_1",
        "title": "数学 コース2 第II問 (1)：単位球面上直交ベクトルと底面三角形の計量",
        "answer": "A: 1, B: 2, CD: 12, EF: 32",
        "points": [
            "直交単位ベクトル $\\vec{OA}, \\vec{OB}, \\vec{OC}$ の内積演算（$\\vec{AB} \\cdot \\vec{AC} = 1$）",
            "辺長 $|\\vec{AB}| = \\sqrt{2}$ と角の余弦 $\\cos \\angle \\text{BAC} = \\frac{1}{2}$（$\\angle \\text{BAC} = 60^\\circ$）の導出",
            "正三角形 $\\triangle \\text{ABC}$ の面積 $S = \\frac{\\sqrt{3}}{2}$ の算出"
        ],
        "solution": (
            "**【題目大意】**\n"
            "原点 O を中心とする半径 1 の球面上に 3 点 A, B, C があり，$\\vec{OA} \\cdot \\vec{OB} = \\vec{OB} \\cdot \\vec{OC} = \\vec{OC} \\cdot \\vec{OA} = 0$ を満たしている。(1) $\\vec{AB} \\cdot \\vec{AC}, |\\vec{AB}|, \\cos \\angle \\text{BAC}$ および三角形 ABC の面積を求める。\n\n"
            "**【公式正解】**\n"
            "- $\\vec{AB} \\cdot \\vec{AC} = \\boxed{\\text{A}} = 1$\n"
            "- $|\\vec{AB}| = \\sqrt{\\boxed{\\text{B}}} = \\sqrt{2}$\n"
            "- $\\cos \\angle \\text{BAC} = \\frac{\\boxed{\\text{C}}}{\\boxed{\\text{D}}} = \\frac{1}{2}$\n"
            "- 三角形 ABC の面積：$\\frac{\\sqrt{\\boxed{\\text{E}}}}{\\boxed{\\text{F}}} = \\frac{\\sqrt{3}}{2}$\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "条件より，$\\vec{OA}, \\vec{OB}, \\vec{OC}$ は互いに直交する単位ベクトルである：\n"
            "$$|\\vec{OA}| = |\\vec{OB}| = |\\vec{OC}| = 1, \\quad \\vec{OA} \\cdot \\vec{OB} = \\vec{OB} \\cdot \\vec{OC} = \\vec{OC} \\cdot \\vec{OA} = 0$$\n\n"
            "1. **$\\vec{AB} \\cdot \\vec{AC}$ の計算**：\n"
            "$$\\vec{AB} = \\vec{OB} - \\vec{OA}, \\quad \\vec{AC} = \\vec{OC} - \\vec{OA}$$\n"
            "$$\\vec{AB} \\cdot \\vec{AC} = (\\vec{OB} - \\vec{OA}) \\cdot (\\vec{OC} - \\vec{OA}) = \\vec{OB} \\cdot \\vec{OC} - \\vec{OB} \\cdot \\vec{OA} - \\vec{OA} \\cdot \\vec{OC} + |\\vec{OA}|^2$$\n"
            "直交性と単位ベクトルより：\n"
            "$$\\vec{AB} \\cdot \\vec{AC} = 0 - 0 - 0 + 1^2 = 1$$\n"
            "したがって，$\\boxed{\\text{A}} = 1$ である。\n\n"
            "2. **$|\\vec{AB}|$ の計算**：\n"
            "$$|\\vec{AB}|^2 = |\\vec{OB} - \\vec{OA}|^2 = |\\vec{OB}|^2 - 2\\vec{OA} \\cdot \\vec{OB} + |\\vec{OA}|^2 = 1 - 0 + 1 = 2$$\n"
            "$$|\\vec{AB}| = \\sqrt{2}$$\n"
            "同様に，対称性より $|\\vec{AC}| = |\\vec{BC}| = \\sqrt{2}$ である。\n"
            "したがって，$\\boxed{\\text{B}} = 2$ である。\n\n"
            "3. **$\\cos \\angle \\text{BAC}$ の計算**：\n"
            "$$\\cos \\angle \\text{BAC} = \\frac{\\vec{AB} \\cdot \\vec{AC}}{|\\vec{AB}||\\vec{AC}|} = \\frac{1}{\\sqrt{2} \\times \\sqrt{2}} = \\frac{1}{2}$$\n"
            "（これにより $\\angle \\text{BAC} = 60^\\circ$，すなわち $\\triangle \\text{ABC}$ は 1 辺 $\\sqrt{2}$ の正三角形である）。\n"
            "したがって，$\\boxed{\\text{C}} = 1, \\; \\boxed{\\text{D}} = 2$ である。\n\n"
            "4. **三角形 ABC の面積**：\n"
            "$$\\sin \\angle \\text{BAC} = \\sin 60^\\circ = \\frac{\\sqrt{3}}{2}$$\n"
            "$$S_{\\triangle \\text{ABC}} = \\frac{1}{2} |\\vec{AB}||\\vec{AC}| \\sin \\angle \\text{BAC} = \\frac{1}{2} \\times \\sqrt{2} \\times \\sqrt{2} \\times \\frac{\\sqrt{3}}{2} = \\frac{\\sqrt{3}}{2}$$\n"
            "したがって，$\\boxed{\\text{E}} = 3, \\; \\boxed{\\text{F}} = 2$ である。\n\n"
            "**【考査考点】**\n"
            "空間ベクトルの内積計算，単位直交基底の性質，三角形の面積公式。"
        )
    },
    {
        "localKey": "math-q-II_2",
        "title": "数学 コース2 第II問 (2)：三角形の重心・球面上の点と四面体の体積",
        "answer": "GH: 13, IJ: 33, KLM: 333, N: 0, OPQ: 316",
        "points": [
            "重心ベクトル $\\vec{OG} = \\frac{1}{3}(\\vec{OA} + \\vec{OB} + \\vec{OC})$ と長さ $|\\vec{OG}| = \\frac{\\sqrt{3}}{3}$",
            "球面上の交点 P に対する高さ $|\\vec{PG}| = \\frac{3 - \\sqrt{3}}{3}$ と直交性 $\\vec{AG} \\cdot \\vec{PG} = 0$",
            "四面体 PABC の体積 $V = \\frac{1}{3} S_{\\triangle \\text{ABC}} |\\vec{PG}| = \\frac{\\sqrt{3} - 1}{6}$ の導出"
        ],
        "solution": (
            "**【題目大意】**\n"
            "三角形 ABC の重心を G，半直線 OG と球面 S の交点を P とするとき，$\\vec{OG}, |\\vec{OG}|, |\\vec{PG}|, \\vec{AG} \\cdot \\vec{PG}$ および四面体 PABC の体積を求める。\n\n"
            "**【公式正解】**\n"
            "- $\\vec{OG} = \\frac{\\boxed{\\text{G}}}{\\boxed{\\text{H}}}(\\vec{OA} + \\vec{OB} + \\vec{OC}) \\implies \\frac{1}{3}(\\vec{OA} + \\vec{OB} + \\vec{OC})$ （$\\text{GH} = 13$）\n"
            "- $|\\vec{OG}| = \\frac{\\sqrt{\\boxed{\\text{I}}}}{\\boxed{\\text{J}}} = \\frac{\\sqrt{3}}{3}$ （$\\text{IJ} = 33$）\n"
            "- $|\\vec{PG}| = \\frac{\\boxed{\\text{K}} - \\sqrt{\\boxed{\\text{L}}}}{\\boxed{\\text{M}}} = \\frac{3 - \\sqrt{3}}{3}$ （$\\text{KLM} = 333$）\n"
            "- $\\vec{AG} \\cdot \\vec{PG} = \\boxed{\\text{N}} = 0$\n"
            "- 四面体 PABC の体積：$\\frac{\\sqrt{\\boxed{\\text{O}}} - \\boxed{\\text{P}}}{\\boxed{\\text{Q}}} = \\frac{\\sqrt{3} - 1}{6}$ （$\\text{OPQ} = 316$）\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "1. **重心ベクトル $\\vec{OG}$ とその大きさ**：\n"
            "重心の定義より：\n"
            "$$\\vec{OG} = \\frac{1}{3}\\left(\\vec{OA} + \\vec{OB} + \\vec{OC}\\right)$$\n"
            "したがって，$\\boxed{\\text{G}} = 1, \\; \\boxed{\\text{H}} = 3$ である。\n"
            "その大きさの2乗は：\n"
            "$$|\\vec{OG}|^2 = \\frac{1}{9}|\\vec{OA} + \\vec{OB} + \\vec{OC}|^2 = \\frac{1}{9}\\left(|\\vec{OA}|^2 + |\\vec{OB}|^2 + |\\vec{OC}|^2 + 2(0 + 0 + 0)\\right) = \\frac{1}{9}(1 + 1 + 1) = \\frac{3}{9} = \\frac{1}{3}$$\n"
            "$$|\\vec{OG}| = \\frac{1}{\\sqrt{3}} = \\frac{\\sqrt{3}}{3}$$\n"
            "したがって，$\\boxed{\\text{I}} = 3, \\; \\boxed{\\text{J}} = 3$ である。\n\n"
            "2. **$|\\vec{PG}|$ の計算**：\n"
            "P は半直線 OG 上で球面 S（半径 1）上にあるため，$|\\vec{OP}| = 1$ である。\n"
            "G は線分 OP 上にあるから：\n"
            "$$|\\vec{PG}| = |\\vec{OP}| - |\\vec{OG}| = 1 - \\frac{\\sqrt{3}}{3} = \\frac{3 - \\sqrt{3}}{3}$$\n"
            "したがって，$\\boxed{\\text{K}} = 3, \\; \\boxed{\\text{L}} = 3, \\; \\boxed{\\text{M}} = 3$ である。\n\n"
            "3. **$\\vec{AG} \\cdot \\vec{PG}$ の計算**：\n"
            "直線 PG は直線 OG と一致する。\n"
            "ベクトル $\\vec{OG}$ と平面 ABC 上の任意のベクトル（例えば $\\vec{AB}$）の内積を調べると：\n"
            "$$\\vec{OG} \\cdot \\vec{AB} = \\frac{1}{3}(\\vec{OA} + \\vec{OB} + \\vec{OC}) \\cdot (\\vec{OB} - \\vec{OA}) = \\frac{1}{3}(|\\vec{OB}|^2 - |\\vec{OA}|^2) = \\frac{1}{3}(1 - 1) = 0$$\n"
            "同様に $\\vec{OG} \\cdot \\vec{AC} = 0$ である。\n"
            "すなわち，直線 OG は平面 ABC の法線ベクトルである。\n"
            "$\\vec{AG}$ は平面 ABC 上のベクトルであるから，法線方向のベクトル $\\vec{PG}$ と直交する：\n"
            "$$\\vec{AG} \\cdot \\vec{PG} = 0$$\n"
            "したがって，$\\boxed{\\text{N}} = 0$ である。\n\n"
            "4. **四面体 PABC の体積**：\n"
            "線分 PG は底面 $\\triangle \\text{ABC}$ に垂直であるから，PG の長さは四面体 PABC の頂点 P から底面 $\\triangle \\text{ABC}$ に下ろした高さそのものである。\n"
            "したがって，体積 $V$ は：\n"
            "$$V = \\frac{1}{3} \\times S_{\\triangle \\text{ABC}} \\times |\\vec{PG}| = \\frac{1}{3} \\times \\frac{\\sqrt{3}}{2} \\times \\frac{3 - \\sqrt{3}}{3} = \\frac{\\sqrt{3}(3 - \\sqrt{3})}{18} = \\frac{3\\sqrt{3} - 3}{18} = \\frac{\\sqrt{3} - 1}{6}$$\n"
            "問題文の形式 $\\frac{\\sqrt{\\boxed{\\text{O}}} - \\boxed{\\text{P}}}{\\boxed{\\text{Q}}}$ より：\n"
            "$$\\boxed{\\text{O}} = 3, \\; \\boxed{\\text{P}} = 1, \\; \\boxed{\\text{Q}} = 6$$\n\n"
            "**【考査考点】**\n"
            "空間幾何における重心と法線ベクトルの関係，内積の直交判定，錐体の体積計算。"
        )
    },
    {
        "localKey": "math-q-III_1",
        "title": "数学 コース2 第III問 (1)：楕円上の点の媒介変数表示と三角関数の合成による最大値",
        "answer": "A: 2, BC: 23, DE: 33, FG: 33, HI: 63, JK: 33",
        "points": [
            "楕円 $\\frac{x^2}{2} + \\frac{y^2}{4} = 1$ のパラメータ表示 $x = \\sqrt{2}\\cos\\theta, y = 2\\sin\\theta$",
            "2倍角の公式による式変形 $P = \\sqrt{2}\\sin 2\\theta - \\cos 2\\theta + 3$",
            "三角関数の合成 $P = \\sqrt{3}\\sin(2\\theta - \\alpha) + 3$ と最大値 $\\sqrt{3} + 3$ の算出"
        ],
        "solution": (
            "**【題目大意】**\n"
            "実数 $x, y$ が $\\frac{x^2}{2} + \\frac{y^2}{4} = 1, x \\ge 0, y \\ge 0$ を満たすとき，$P = x^2 + xy + y^2$ の最大値を求める。\n\n"
            "**【公式正解】**\n"
            "- $y = \\boxed{\\text{A}} \\sin\\theta \\implies 2\\sin\\theta$ （$\\text{A} = 2$）\n"
            "- $P = \\sqrt{\\boxed{\\text{B}}} \\sin 2\\theta - \\cos 2\\theta + \\boxed{\\text{C}} \\implies \\sqrt{2}\\sin 2\\theta - \\cos 2\\theta + 3$ （$\\text{BC} = 23$）\n"
            "- $P = \\sqrt{\\boxed{\\text{D}}} \\sin(2\\theta - \\alpha) + \\boxed{\\text{E}} \\implies \\sqrt{3}\\sin(2\\theta - \\alpha) + 3$ （$\\text{DE} = 33$）\n"
            "- $\\sin\\alpha = \\frac{\\sqrt{\\boxed{\\text{F}}}}{\\boxed{\\text{G}}} = \\frac{\\sqrt{3}}{3}$ （$\\text{FG} = 33$），$\\cos\\alpha = \\frac{\\sqrt{\\boxed{\\text{H}}}}{\\boxed{\\text{I}}} = \\frac{\\sqrt{6}}{3}$ （$\\text{HI} = 63$）\n"
            "- $P$ の最大値：$\\sqrt{\\boxed{\\text{J}}} + \\boxed{\\text{K}} = \\sqrt{3} + 3$ （$\\text{JK} = 33$）\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "1. **媒介変数表示**：\n"
            "$\\frac{x^2}{2} + \\frac{y^2}{4} = 1$ において，$x = \\sqrt{2}\\cos\\theta$（$0 \\le \\theta \\le \\frac{\\pi}{2}$）とおくと：\n"
            "$$\\cos^2\\theta + \\frac{y^2}{4} = 1 \\implies \\frac{y^2}{4} = 1 - \\cos^2\\theta = \\sin^2\\theta$$\n"
            "$y \\ge 0$ より：\n"
            "$$y = 2\\sin\\theta$$\n"
            "したがって，$\\boxed{\\text{A}} = 2$ である。\n\n"
            "2. **2倍角の公式による整理**：\n"
            "$$P = x^2 + xy + y^2 = (\\sqrt{2}\\cos\\theta)^2 + (\\sqrt{2}\\cos\\theta)(2\\sin\\theta) + (2\\sin\\theta)^2$$\n"
            "$$P = 2\\cos^2\\theta + 2\\sqrt{2}\\sin\\theta\\cos\\theta + 4\\sin^2\\theta$$\n"
            "半角・2倍角の公式 $\\cos^2\\theta = \\frac{1 + \\cos 2\\theta}{2}, \\sin^2\\theta = \\frac{1 - \\cos 2\\theta}{2}, 2\\sin\\theta\\cos\\theta = \\sin 2\\theta$ を用いると：\n"
            "$$P = (1 + \\cos 2\\theta) + \\sqrt{2}\\sin 2\\theta + 2(1 - \\cos 2\\theta)$$\n"
            "$$P = \\sqrt{2}\\sin 2\\theta - \\cos 2\\theta + 3$$\n"
            "したがって，$\\boxed{\\text{B}} = 2, \\; \\boxed{\\text{C}} = 3$（$\\text{BC} = 23$）である。\n\n"
            "3. **三角関数の合成**：\n"
            "係数 $\\sqrt{2}$ と $-1$ を合成する：\n"
            "$$\\sqrt{(\\sqrt{2})^2 + (-1)^2} = \\sqrt{2 + 1} = \\sqrt{3}$$\n"
            "$$P = \\sqrt{3}\\left(\\sin 2\\theta \\cdot \\frac{\\sqrt{2}}{\\sqrt{3}} - \\cos 2\\theta \\cdot \\frac{1}{\\sqrt{3}}\\right) + 3$$\n"
            "加法定理 $\\sin(2\\theta - \\alpha) = \\sin 2\\theta \\cos\\alpha - \\cos 2\\theta \\sin\\alpha$ と比較すると：\n"
            "$$P = \\sqrt{3}\\sin(2\\theta - \\alpha) + 3$$\n"
            "ここで $\\alpha$ は：\n"
            "$$\\cos\\alpha = \\frac{\\sqrt{2}}{\\sqrt{3}} = \\frac{\\sqrt{6}}{3}, \\quad \\sin\\alpha = \\frac{1}{\\sqrt{3}} = \\frac{\\sqrt{3}}{3} \\quad \\left(0 < \\alpha < \\frac{\\pi}{2}\\right)$$\n"
            "したがって，$\\boxed{\\text{D}} = 3, \\; \\boxed{\\text{E}} = 3$（$\\text{DE} = 33$），$\\boxed{\\text{F}} = 3, \\; \\boxed{\\text{G}} = 3$（$\\text{FG} = 33$），$\\boxed{\\text{H}} = 6, \\; \\boxed{\\text{I}} = 3$（$\\text{HI} = 63$）である。\n\n"
            "4. **最大値の決定**：\n"
            "$0 \\le \\theta \\le \\frac{\\pi}{2}$ より $0 \\le 2\\theta \\le \\pi$ であるから：\n"
            "$$-\\alpha \\le 2\\theta - \\alpha \\le \\pi - \\alpha$$\n"
            "$0 < \\alpha < \\frac{\\pi}{2}$ であるため，角 $\\frac{\\pi}{2}$ はこの区間内に含まれる。\n"
            "したがって，$\\sin(2\\theta - \\alpha)$ は最大値 $1$ をとることができる。\n"
            "よって，$P$ の最大値は：\n"
            "$$P_{\\text{max}} = \\sqrt{3}(1) + 3 = \\sqrt{3} + 3$$\n"
            "これより，$\\boxed{\\text{J}} = 3, \\; \\boxed{\\text{K}} = 3$（$\\text{JK} = 33$）である。\n\n"
            "**【考査考点】**\n"
            "2次曲線の媒介変数表示，2倍角の公式，三角関数の合成と変域における最大値決定。"
        )
    },
    {
        "localKey": "math-q-III_2",
        "title": "数学 コース2 第III問 (2)：最大値を与える偏角における三角比の決定",
        "answer": "L: 2, MN: 63, OP: 33",
        "points": [
            "最大値条件 $2\\theta_0 - \\alpha = \\frac{\\pi}{2} \\implies 2\\theta_0 = \\alpha + \\frac{\\pi}{2}$",
            "加法定理による $\\sin 2\\theta_0 = \\cos\\alpha = \\frac{\\sqrt{6}}{3}$ の算出",
            "加法定理による $\\cos 2\\theta_0 = -\\sin\\alpha = -\\frac{\\sqrt{3}}{3}$ の算出"
        ],
        "solution": (
            "**【題目大意】**\n"
            "$P$ の値が最大になるときの $\\theta$ を $\\theta_0$ とするとき，$2\\theta_0$ の表式および $\\sin 2\\theta_0, \\cos 2\\theta_0$ の値を求める。\n\n"
            "**【公式正解】**\n"
            "- $2\\theta_0 = \\alpha + \\frac{\\pi}{\\boxed{\\text{L}}} \\implies \\alpha + \\frac{\\pi}{2}$ （$\\text{L} = 2$）\n"
            "- $\\sin 2\\theta_0 = \\frac{\\sqrt{\\boxed{\\text{M}}}}{\\boxed{\\text{N}}} = \\frac{\\sqrt{6}}{3}$ （$\\text{MN} = 63$）\n"
            "- $\\cos 2\\theta_0 = -\\frac{\\sqrt{\\boxed{\\text{O}}}}{\\boxed{\\text{P}}} = -\\frac{\\sqrt{3}}{3}$ （$\\text{OP} = 33$）\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "1. **$2\\theta_0$ の導出**：\n"
            "$P = \\sqrt{3}\\sin(2\\theta - \\alpha) + 3$ が最大値をとるのは，正弦関数の偏角が $\\frac{\\pi}{2}$ となるときである：\n"
            "$$2\\theta_0 - \\alpha = \\frac{\\pi}{2} \\implies 2\\theta_0 = \\alpha + \\frac{\\pi}{2}$$\n"
            "問題文の形式 $2\\theta_0 = \\alpha + \\frac{\\pi}{\\boxed{\\text{L}}}$ より：\n"
            "$$\\boxed{\\text{L}} = 2$$\n\n"
            "2. **$\\sin 2\\theta_0$ および $\\cos 2\\theta_0$ の計算**：\n"
            "三角関数の加法定理（または位相シフトの公式）を用いる：\n"
            "- $\\sin 2\\theta_0 = \\sin\\left(\\alpha + \\frac{\\pi}{2}\\right) = \\cos\\alpha$\n"
            "  前半で求めた $\\cos\\alpha = \\frac{\\sqrt{6}}{3}$ を代入すると：\n"
            "  $$\\sin 2\\theta_0 = \\frac{\\sqrt{6}}{3}$$\n"
            "  したがって，$\\boxed{\\text{M}} = 6, \\; \\boxed{\\text{N}} = 3$（$\\text{MN} = 63$）である。\n\n"
            "- $\\cos 2\\theta_0 = \\cos\\left(\\alpha + \\frac{\\pi}{2}\\right) = -\\sin\\alpha$\n"
            "  前半で求めた $\\sin\\alpha = \\frac{\\sqrt{3}}{3}$ を代入すると：\n"
            "  $$\\cos 2\\theta_0 = -\\frac{\\sqrt{3}}{3}$$\n"
            "  問題文の形式 $-\\frac{\\sqrt{\\boxed{\\text{O}}}}{\\boxed{\\text{P}}}$ より：\n"
            "  $$\\boxed{\\text{O}} = 3, \\; \\boxed{\\text{P}} = 3 \\implies \\text{OP} = 33$$\n\n"
            "**【考査考点】**\n"
            "三角関数の最大条件と偏角，加法定理および $\\frac{\\pi}{2}$ シフトの公式。"
        )
    },
    {
        "localKey": "math-q-IV_1",
        "title": "数学 コース2 第IV問 [1]：積分の不等式評価による級数の発散証明と区分求積法",
        "answer": "AB: 13, C: 9, D: 7, E: 7, FG: 15, H: 2, I: 0, J: 7, KL: 41, MN: 01, OP: 22",
        "points": [
            "関数 $y = x^{-1/2}$ の導関数 $y' = -\\frac{1}{2x\\sqrt{x}}$ による単調減少性の確認",
            "区間積分の不等式 $\\frac{1}{\\sqrt{k}} > \\int_k^{k+1} \\frac{1}{\\sqrt{x}} dx$ と $S_n > 2(\\sqrt{n+1} - 1) \\to \\infty$ の導出",
            "区分求積法 $\\lim_{n \\to \\infty} \\frac{1}{n}\\sum_{k=1}^n \\frac{1}{\\sqrt{1 + k/n}} = \\int_0^1 \\frac{1}{\\sqrt{1+x}}dx = 2(\\sqrt{2} - 1)$ の導出"
        ],
        "solution": (
            "**【題目大意】**\n"
            "数列 $S_n = \\sum_{k=1}^n \\frac{1}{\\sqrt{k}}$ について，(1) 不等式評価による $\\lim_{n \\to \\infty} S_n = \\infty$ の証明，および (2) 区分求積法による $\\lim_{n \\to \\infty} \\frac{S_{2n} - S_n}{\\sqrt{n}}$ の計算を行う。\n\n"
            "**【公式正解】**\n"
            "- (1) $y' = -\\frac{\\boxed{\\text{A}}}{2\\sqrt{x}^{\\boxed{\\text{B}}}} \\implies -\\frac{1}{2\\sqrt{x}^3}$ （$\\text{AB} = 13$）\n"
            "- 関数 $y$ は：$\\textcircled{9}$ （単調減少）\n"
            "- 不等式：$\\frac{1}{\\sqrt{k}} \\; \\boxed{\\text{D}} \\; \\int_k^{k+1} \\frac{1}{\\sqrt{x}} dx \\implies >$ （$\\text{D} = 7$）\n"
            "- 和の不等式：$S_n \\; \\boxed{\\text{E}} \\; \\int_{\\boxed{\\text{F}}}^{\\boxed{\\text{G}}} \\frac{1}{\\sqrt{x}} dx = \\boxed{\\text{H}}(\\sqrt{\\boxed{\\text{G}}} - 1) \\implies S_n > \\int_1^{n+1} \\frac{1}{\\sqrt{x}} dx = 2(\\sqrt{n+1} - 1)$ （$\\text{E} = 7, \\text{FG} = 15, \\text{H} = 2$）\n"
            "- 極限：$\\lim_{n \\to \\infty} S_n = \\boxed{\\text{I}} \\implies \\infty$ （$\\text{I} = 0$）\n"
            "- (2) $S_{2n} - S_n = \\sum_{k=1}^n \\frac{1}{\\sqrt{\\boxed{\\text{J}}}} \\implies \\frac{1}{\\sqrt{n+k}}$ （$\\text{J} = 7$）\n"
            "- 区分求積：$\\frac{1}{\\boxed{\\text{K}}} \\sum_{k=1}^n \\frac{1}{\\sqrt{\\boxed{\\text{L}} + \\frac{k}{n}}} \\implies \\frac{1}{n} \\sum_{k=1}^n \\frac{1}{\\sqrt{1 + \\frac{k}{n}}}$ （$\\text{KL} = 41$）\n"
            "- 定積分：$\\int_{\\boxed{\\text{M}}}^{\\boxed{\\text{N}}} \\frac{1}{\\sqrt{1+x}} dx = \\int_0^1 \\frac{1}{\\sqrt{1+x}} dx$ （$\\text{MN} = 01$）\n"
            "- 極限値：$\\boxed{\\text{O}}(\\sqrt{\\boxed{\\text{P}}} - 1) = 2(\\sqrt{2} - 1)$ （$\\text{OP} = 22$）\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "1. **(1) 不等式評価と $S_n$ の発散**：\n"
            "$y = \\frac{1}{\\sqrt{x}} = x^{-1/2}$ を微分すると：\n"
            "$$y' = -\\frac{1}{2} x^{-3/2} = -\\frac{1}{2\\sqrt{x^3}} = -\\frac{1}{2\\sqrt{x}^3}$$\n"
            "したがって，$\\boxed{\\text{A}} = 1, \\; \\boxed{\\text{B}} = 3$（$\\text{AB} = 13$）である。\n"
            "$x > 0$ において $y' < 0$ であるから，関数 $y$ は**単調減少**（$\\textcircled{9}$，$\\boxed{\\text{C}} = 9$）である。\n\n"
            "区間 $[k, k+1]$ において，$k \\le x \\le k+1$ より $\\frac{1}{\\sqrt{k}} \\ge \\frac{1}{\\sqrt{x}}$（等号は $x=k$ のみ）であるから：\n"
            "$$\\int_k^{k+1} \\frac{1}{\\sqrt{x}} dx < \\int_k^{k+1} \\frac{1}{\\sqrt{k}} dx = \\frac{1}{\\sqrt{k}}$$\n"
            "すなわち $\\frac{1}{\\sqrt{k}} > \\int_k^{k+1} \\frac{1}{\\sqrt{x}} dx$ である（$\\textcircled{7}$，$\\boxed{\\text{D}} = 7$）。\n\n"
            "$k = 1$ から $k = n$ まで足し合わせると：\n"
            "$$S_n = \\sum_{k=1}^n \\frac{1}{\\sqrt{k}} > \\sum_{k=1}^n \\int_k^{k+1} \\frac{1}{\\sqrt{x}} dx = \\int_1^{n+1} \\frac{1}{\\sqrt{x}} dx$$\n"
            "したがって，不等号は $>$（$\\textcircled{7}$，$\\boxed{\\text{E}} = 7$），積分区間は $1$ から $n+1$（$\\boxed{\\text{F}} = 1, \\; \\boxed{\\text{G}} = n+1 \\implies \\textcircled{5}$，$\\text{FG} = 15$）。\n"
            "定積分を計算すると：\n"
            "$$\\int_1^{n+1} x^{-1/2} dx = \\left[2\\sqrt{x}\\right]_1^{n+1} = 2\\left(\\sqrt{n+1} - 1\\right)$$\n"
            "よって $\\boxed{\\text{H}} = 2$ である。\n"
            "$n \\to \\infty$ のとき $2(\\sqrt{n+1} - 1) \\to \\infty$ であるから，追い出しの原理（比較判定法）より：\n"
            "$$\\lim_{n \\to \\infty} S_n = \\infty \\quad (\\textcircled{0}, \\; \\boxed{\\text{I}} = 0)$$\n\n"
            "2. **(2) 区分求積法による極限計算**：\n"
            "$$S_{2n} - S_n = \\sum_{j=n+1}^{2n} \\frac{1}{\\sqrt{j}}$$\n"
            "$j = n + k$（$k = 1, 2, \\dots, n$）とおくと：\n"
            "$$S_{2n} - S_n = \\sum_{k=1}^n \\frac{1}{\\sqrt{n+k}}$$\n"
            "したがって，$\\boxed{\\text{J}} = n+k$（$\\textcircled{7}$）である。\n\n"
            "両辺を $\\sqrt{n}$ で割ると：\n"
            "$$\\frac{S_{2n} - S_n}{\\sqrt{n}} = \\sum_{k=1}^n \\frac{1}{\\sqrt{n}\\sqrt{n+k}} = \\sum_{k=1}^n \\frac{1}{n\\sqrt{1 + \\frac{k}{n}}} = \\frac{1}{n}\\sum_{k=1}^n \\frac{1}{\\sqrt{1 + \\frac{k}{n}}}$$\n"
            "したがって，$\\boxed{\\text{K}} = n$（$\\textcircled{4}$），$\\boxed{\\text{L}} = 1$（$\\textcircled{1}$）より $\\text{KL} = 41$ である。\n\n"
            "区分求積法の公式 $\\lim_{n \\to \\infty} \\frac{1}{n}\\sum_{k=1}^n f\\left(\\frac{k}{n}\\right) = \\int_0^1 f(x) dx$ より：\n"
            "$$\\lim_{n \\to \\infty} \\frac{S_{2n} - S_n}{\\sqrt{n}} = \\int_0^1 \\frac{1}{\\sqrt{1+x}} dx$$\n"
            "したがって，積分範囲は $0$ から $1$（$\\boxed{\\text{M}} = 0, \\; \\boxed{\\text{N}} = 1 \\implies \\text{MN} = 01$）である。\n\n"
            "定積分を計算する：\n"
            "$$\\int_0^1 (1+x)^{-1/2} dx = \\left[2\\sqrt{1+x}\\right]_0^1 = 2\\left(\\sqrt{2} - \\sqrt{1}\\right) = 2(\\sqrt{2} - 1)$$\n"
            "形式 $\\boxed{\\text{O}}(\\sqrt{\\boxed{\\text{P}}} - 1)$ より：\n"
            "$$\\boxed{\\text{O}} = 2, \\; \\boxed{\\text{P}} = 2 \\implies \\text{OP} = 22$$\n\n"
            "**【考査考点】**\n"
            "積分の不等式評価を用いた無限級数の発散証明，区分求積法の基本変形と定積分計算。"
        )
    },
    {
        "localKey": "math-q-IV_2",
        "title": "数学 コース2 第IV問 [2]：積分方程式・微分方程式の解法とネイピア数の定義による極限",
        "answer": "Q: 1, R: 2, S: 7, T: 2, U: 0, V: 4, W: 2, X: 0, Y: 2",
        "points": [
            "積分方程式の両辺微分による微分関係式 $(1 + e^{-x})(f(x) - f'(x)) = 2$",
            "変数変換 $f(x) = e^x g(x)$ による変数分離形 $g'(x) = \\frac{-2e^{-x}}{1 + e^{-x}}$ の導出",
            "初期条件 $g(0) = f(0) = 2\\log 2$ からの $C = 0$ と $f(x) = 2e^x \\log(1 + e^{-x})$ の決定",
            "ネイピア数の定義 $\\lim_{t \\to 0} (1+t)^{1/t} = e$ を用いた極限値 $\\lim_{x \\to \\infty} f(x) = 2$ の導出"
        ],
        "solution": (
            "**【題目大意】**\n"
            "微分可能な関数 $f(x)$ が等式\n"
            "$$\\int_0^x f(t) dt = (1 + e^{-x}) f(x) + 2x - 4\\log 2 \\quad \\textcircled{1}$$\n"
            "を満たすとき，$f(x)$ を求め，さらに極限値 $\\lim_{x \\to \\infty} f(x)$ を求める。\n\n"
            "**【公式正解】**\n"
            "- $(1 + e^{-x})(\\boxed{\\text{Q}}) = \\boxed{\\text{R}} \\implies (1 + e^{-x})(f(x) - f'(x)) = 2$ （$\\text{Q} = 1, \\text{R} = 2$）\n"
            "- $g'(x) = \\frac{\\boxed{\\text{S}}}{1 + e^{-x}} \\implies \\frac{-2e^{-x}}{1 + e^{-x}}$ （$\\text{S} = 7$）\n"
            "- $g(x) = \\boxed{\\text{T}}\\log(1 + e^{-x}) + C \\implies 2\\log(1 + e^{-x}) + C$ （$\\text{T} = 2$）\n"
            "- $C = \\boxed{\\text{U}} = 0$\n"
            "- $f(x) = \\boxed{\\text{V}}\\log(1 + e^{-x}) \\implies 2e^x \\log(1 + e^{-x})$ （$\\text{V} = 4$）\n"
            "- $f(x) = \\boxed{\\text{W}}\\log(1 + t)^{1/t} \\implies 2\\log(1 + t)^{1/t}$ （$\\text{W} = 2$）\n"
            "- 極限：$\\lim_{t \\to \\boxed{\\text{X}}} W\\log(1 + t)^{1/t} = \\boxed{\\text{Y}} \\implies \\lim_{t \\to 0} 2\\log(1 + t)^{1/t} = 2$ （$\\text{X} = 0, \\text{Y} = 2$）\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "1. **等式 $\\textcircled{1}$ の微分と変形**：\n"
            "$$\\int_0^x f(t) dt = (1 + e^{-x}) f(x) + 2x - 4\\log 2$$\n"
            "両辺を $x$ で微分する：\n"
            "$$f(x) = \\left(-e^{-x}\\right)f(x) + (1 + e^{-x})f'(x) + 2$$\n"
            "左辺に $e^{-x}f(x)$ を移項すると：\n"
            "$$(1 + e^{-x})f(x) = (1 + e^{-x})f'(x) + 2$$\n"
            "$$(1 + e^{-x})\\left(f(x) - f'(x)\\right) = 2 \\quad \\textcircled{2}$$\n"
            "選択肢 $\\textcircled{1}$ は $f(x) - f'(x)$ であるから，$\\boxed{\\text{Q}} = 1, \\; \\boxed{\\text{R}} = 2$ である。\n\n"
            "2. **変数変換 $f(x) = e^x g(x)$ による解法**：\n"
            "積の微分法より：\n"
            "$$f'(x) = e^x g(x) + e^x g'(x)$$\n"
            "したがって：\n"
            "$$f(x) - f'(x) = e^x g(x) - \\left(e^x g(x) + e^x g'(x)\\right) = -e^x g'(x)$$\n"
            "これを $\\textcircled{2}$ に代入すると：\n"
            "$$(1 + e^{-x})\\left(-e^x g'(x)\\right) = 2$$\n"
            "両辺を $-e^x(1 + e^{-x})$ で割ると：\n"
            "$$g'(x) = \\frac{-2}{e^x(1 + e^{-x})} = \\frac{-2e^{-x}}{1 + e^{-x}}$$\n"
            "選択肢 $\\textcircled{7}$ は $-2e^{-x}$ であるから，$\\boxed{\\text{S}} = 7$ である。\n\n"
            "3. **$g(x)$ の積分と積分定数 $C$ の決定**：\n"
            "$$g(x) = \\int \\frac{-2e^{-x}}{1 + e^{-x}} dx$$\n"
            "分子は分母の微分 $(1 + e^{-x})' = -e^{-x}$ の $2$ 倍であるから：\n"
            "$$g(x) = 2\\int \\frac{(1 + e^{-x})'}{1 + e^{-x}} dx = 2\\log(1 + e^{-x}) + C$$\n"
            "したがって，$\\boxed{\\text{T}} = 2$ である。\n\n"
            "初期条件として，元の等式 $\\textcircled{1}$ に $x = 0$ を代入する：\n"
            "$$\\int_0^0 f(t) dt = 0 = (1 + e^0)f(0) + 0 - 4\\log 2 = 2f(0) - 4\\log 2$$\n"
            "$$2f(0) = 4\\log 2 \\implies f(0) = 2\\log 2$$\n"
            "一方，$f(0) = e^0 g(0) = g(0)$ であるから：\n"
            "$$g(0) = 2\\log(1 + e^0) + C = 2\\log 2 + C$$\n"
            "$$2\\log 2 + C = 2\\log 2 \\implies C = 0$$\n"
            "したがって，$\\boxed{\\text{U}} = 0$ である。\n\n"
            "これより $g(x) = 2\\log(1 + e^{-x})$ となり：\n"
            "$$f(x) = e^x g(x) = 2e^x \\log(1 + e^{-x})$$\n"
            "選択肢 $\\textcircled{4}$ は $2e^x$ であるから，$\\boxed{\\text{V}} = 4$ である。\n\n"
            "4. **$x \\to \\infty$ における極限値の算出**：\n"
            "$t = e^{-x}$ とおくと，$e^x = \\frac{1}{t}$ である。\n"
            "$$f(x) = 2 \\cdot \\frac{1}{t} \\log(1 + t) = 2\\log(1 + t)^{1/t}$$\n"
            "したがって，$\\boxed{\\text{W}} = 2$ である。\n"
            "$x \\to \\infty$ のとき $t = e^{-x} \\to 0$ であるから：\n"
            "$$\\boxed{\\text{X}} = 0$$\n"
            "自然対数の底（ネイピア数）の定義 $\\lim_{t \\to 0} (1 + t)^{1/t} = e$ より：\n"
            "$$\\lim_{x \\to \\infty} f(x) = \\lim_{t \\to 0} 2\\log(1 + t)^{1/t} = 2\\log e = 2 \\times 1 = 2$$\n"
            "したがって，$\\boxed{\\text{Y}} = 2$ である。\n\n"
            "**【考査考点】**\n"
            "微分積分学の基本定理を用いた積分方程式の解法，未知関数の変数変換による微分方程式の解法，ネイピア数 $e$ の定義に基づく極限計算。"
        )
    }
]

def main():
    out_dir = Path("work/2013-1-math-c2")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Save json
    json_path = out_dir / "explanations.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(math_c2_questions, f, ensure_ascii=False, indent=2)
    print(f"Generated {json_path} ({len(math_c2_questions)} questions)")
    
    # Save md
    md_path = Path("docs/explanations/2013-1-math-c2-solutions.md")
    md_path.parent.mkdir(parents=True, exist_ok=True)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# 2013-1 EJU 数学 コース2 詳解\n\n")
        for q in math_c2_questions:
            f.write(f"## {q['title']}\n\n")
            f.write(q["solution"] + "\n\n---\n\n")
    print(f"Generated {md_path}")

if __name__ == "__main__":
    main()

