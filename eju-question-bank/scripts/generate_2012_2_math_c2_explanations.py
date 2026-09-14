#!/usr/bin/env python3
"""Generate comprehensive pedagogical explanations for 2012-2 EJU Math Course 2 (8 questions)."""

import json
from pathlib import Path

math_c2_questions = [
    {
        "q_num": 1,
        "localKey": "math-q-I_1",
        "answer_ref": "MATH_C2:I_1",
        "answer": "AB: 24, C: 4, DEF: -28, GHI: 2-8, JK: 10, LM: -8",
        "title": "数学 コース2 第I問 [1]：2次関数の原点対称移動と指定区間における最大・最小値",
        "points": [
            "2次関数 $y = ax^2 - 4x - 4a$ の平方完成と頂点座標 $\\left(\\frac{2}{a}, -\\frac{4}{a}-4a\\right)$ の導出",
            "原点対称移動（$(x, y) \\to (-x, -y)$）による曲線 $G: y = -ax^2 - 4x + 4a$ の決定",
            "2曲線の交点 $(-2, 8)$ および $(2, -8)$ の算出",
            "$a=2$ における放物線 $G$ の区間 $[-2, 2]$ での最大値 $10$ および最小値 $-8$ の同定"
        ],
        "solution": (
            "**【題目大意】**\n"
            "$a \\neq 0$ とする。2次関数 $y = ax^2 - 4x - 4a$ $\\cdots\\textcircled{1}$ のグラフと原点 $(0, 0)$ に関して対称な曲線を $G$ とする。\n"
            "(1) $\\textcircled{1}$ の頂点の座標を求める。\n"
            "(2) 曲線 $G$ を表す2次関数を選択肢の中から選ぶ。\n"
            "(3) $G$ と $\\textcircled{1}$ の交点の座標を求める。\n"
            "(4) $a = 2$ のとき，区間 $DE \\leq x \\leq G$ における $G$ の最大値と最小値を求める。\n\n"
            "**【公式正解】**\n"
            "正解：\n"
            "$\\text{AB} = 24$\n"
            "$\\text{C} = 4$\n"
            "$\\text{DEF} = -28$\n"
            "$\\text{GHI} = 2-8$\n"
            "$\\text{JK} = 10$\n"
            "$\\text{LM} = -8$\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "1. **(1) 頂点座標の算出**：\n"
            "与えられた2次関数の式を変形（平方完成）する：\n"
            "$$y = a\\left(x^2 - \\frac{4}{a}x\\right) - 4a = a\\left(x - \\frac{2}{a}\\right)^2 - a \\cdot \\frac{4}{a^2} - 4a = a\\left(x - \\frac{2}{a}\\right)^2 - \\frac{4}{a} - 4a$$\n"
            "したがって，頂点の座標は：\n"
            "$$\\left(\\frac{2}{a}, -\\frac{4}{a} - 4a\\right)$$\n"
            "これより，$\\text{A} = 2, \\text{B} = 4$（$\\text{AB} = 24$）である。\n\n"
            "2. **(2) 原点対称移動による曲線 $G$ の方程式**：\n"
            "点 $(x, y)$ を原点に関して対称移動させると $(-x, -y)$ に移る。\n"
            "元の関数 $y = ax^2 - 4x - 4a$ の $x$ を $-x$ に，$y$ を $-y$ に置き換えると：\n"
            "$$-y = a(-x)^2 - 4(-x) - 4a = ax^2 + 4x - 4a$$\n"
            "両辺に $-1$ を掛けて整理すると：\n"
            "$$y = -ax^2 - 4x + 4a$$\n"
            "これは選択肢 $\\textcircled{4}$ に一致する。したがって $\\text{C} = 4$ である。\n\n"
            "3. **(3) 2つの放物線の交点座標**：\n"
            "$\\textcircled{1}$ と $G$ の連立方程式を解く：\n"
            "$$ax^2 - 4x - 4a = -ax^2 - 4x + 4a$$\n"
            "両辺の $-4x$ を消去し，移行して整理すると：\n"
            "$$2ax^2 = 8a$$\n"
            "$a \\neq 0$ より，両辺を $2a$ で割ると：\n"
            "$$x^2 = 4 \\implies x = \\pm 2$$\n"
            "- $x = -2$ のとき：\n"
            "  $$y = a(-2)^2 - 4(-2) - 4a = 4a + 8 - 4a = 8$$\n"
            "  交点は $(-2, 8)$ である。これより $\\text{DE} = -2, \\text{F} = 8$（$\\text{DEF} = -28$）。\n"
            "- $x = 2$ のとき：\n"
            "  $$y = a(2)^2 - 4(2) - 4a = 4a - 8 - 4a = -8$$\n"
            "  交点は $(2, -8)$ である。これより $\\text{G} = 2, \\text{HI} = -8$（$\\text{GHI} = 2-8$）。\n\n"
            "4. **(4) $a=2$ のときの区間 $[-2, 2]$ における最大値・最小値**：\n"
            "$a = 2$ のとき，曲線 $G$ の方程式は：\n"
            "$$y = -2x^2 - 4x + 8 = -2(x^2 + 2x) + 8 = -2(x + 1)^2 + 10$$\n"
            "これは上に凸の放物線であり，軸は $x = -1$ である。\n"
            "指定された区間は $-2 \\leq x \\leq 2$ である：\n"
            "- 軸 $x = -1$ は区間 $[-2, 2]$ の内部に含まれるため，最大値は頂点でとり：\n"
            "  $$y_{\\text{max}} = 10 \\quad (x = -1 \\text{ のとき})$$\n"
            "  これより $\\text{JK} = 10$ である。\n"
            "- 最小値は軸 $x = -1$ から最も遠い端点 $x = 2$ でとり：\n"
            "  $$y_{\\text{min}} = -2(2+1)^2 + 10 = -18 + 10 = -8 \\quad (x = 2 \\text{ のとき})$$\n"
            "  これより $\\text{LM} = -8$ である。\n\n"
            "**【考査考点】**\n"
            "2次関数の平方完成，図形の原点対称移動，2次方程式による共有点の算出，定義域制限下の2次関数の最大・最小値問題。"
        )
    },
    {
        "q_num": 2,
        "localKey": "math-q-I_2",
        "answer_ref": "MATH_C2:I_2",
        "answer": "NO: 41, PQR: 421, STUV: 7473, W: 3, X: 3",
        "title": "数学 コース2 第I問 [2]：絶対値を含む1次方程式の解法と整数解条件",
        "points": [
            "絶対値記号の定義に基づく場合分け（$ax \\geq 11$ と $ax < 11$）",
            "$a = \\sqrt{7}$ における有理化と解 $x = \\frac{7(4-\\sqrt{7})}{3}$ の導出",
            "正の整数条件による不定方程式の分析と一意解 $a = 3, x = 3$ の決定"
        ],
        "solution": (
            "**【題目大意】**\n"
            "$a$ を定数とし，$x$ の方程式 $|ax - 11| = 4x - 10$ $\\cdots\\textcircled{1}$ を考える。\n"
            "(1) 絶対値の記号を使わない形に変形する。\n"
            "(2) $a = \\sqrt{7}$ のときの方程式の解を求める。\n"
            "(3) $a$ が正の整数のとき，方程式が正の整数解をもつような $a$ とその解 $x$ を求める。\n\n"
            "**【公式正解】**\n"
            "正解：\n"
            "$\\text{NO} = 41$\n"
            "$\\text{PQR} = 421$\n"
            "$\\text{STUV} = 7473$\n"
            "$\\text{W} = 3$\n"
            "$\\text{X} = 3$\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "1. **(1) 絶対値の解除**：\n"
            "絶対値の中身の正負によって場合分けする：\n"
            "- $ax - 11 \\geq 0$，すなわち $ax \\geq 11$ のとき：\n"
            "  $$ax - 11 = 4x - 10 \\implies (a - 4)x = 1$$\n"
            "  これより $\\text{N} = 4, \\text{O} = 1$（$\\text{NO} = 41$）。\n"
            "- $ax - 11 < 0$，すなわち $ax < 11$ のとき：\n"
            "  $$-(ax - 11) = 4x - 10 \\implies -ax + 11 = 4x - 10 \\implies (a + 4)x = 21$$\n"
            "  これより $\\text{P} = 4, \\text{QR} = 21$（$\\text{PQR} = 421$）。\n\n"
            "2. **(2) $a = \\sqrt{7}$ のときの解**：\n"
            "右辺 $4x - 10$ は絶対値と等しいため，$4x - 10 \\geq 0 \\implies x \\geq \\frac{5}{2} = 2.5$ でなければならない。\n"
            "- もし $ax \\geq 11$ の場合：\n"
            "  $(\\sqrt{7} - 4)x = 1 \\implies x = \\frac{1}{\\sqrt{7} - 4} < 0$ となり，不適。\n"
            "- したがって $ax < 11$ の場合である：\n"
            "  $$(\\sqrt{7} + 4)x = 21 \\implies x = \\frac{21}{4 + \\sqrt{7}}$$\n"
            "  分母を有理化すると：\n"
            "  $$x = \\frac{21(4 - \\sqrt{7})}{(4 + \\sqrt{7})(4 - \\sqrt{7})} = \\frac{21(4 - \\sqrt{7})}{16 - 7} = \\frac{21(4 - \\sqrt{7})}{9} = \\frac{7(4 - \\sqrt{7})}{3}$$\n"
            "  この値について確認すると：\n"
            "  $\\sqrt{7} \\approx 2.646$ より $4 - \\sqrt{7} \\approx 1.354$ であり，$x = \\frac{7 \\times 1.354}{3} \\approx 3.16 > 2.5$ である。\n"
            "  また $ax = \\sqrt{7} \\times 3.16 \\approx 8.36 < 11$ を満たす。\n"
            "  したがって，$x = \\frac{7(4 - \\sqrt{7})}{3}$ である。\n"
            "  これより $\\text{S} = 7, \\text{T} = 4, \\text{U} = 7, \\text{V} = 3$（$\\text{STUV} = 7473$）。\n\n"
            "3. **(3) $a$ が正の整数で正の整数解をもつ条件**：\n"
            "$x$ が正の整数であるとき，方程式の解の候補を吟味する：\n"
            "- **場合 1**：$ax \\geq 11$ のとき，$(a - 4)x = 1$\n"
            "  $a, x$ は整数であるから，$a - 4$ と $x$ は 1 の約数である。\n"
            "  $x > 0$ より $x = 1, a - 4 = 1 \\implies a = 5$。\n"
            "  このとき $ax = 5 \\times 1 = 5$ であるが，前提条件 $ax \\geq 11$ に反するため不適。\n"
            "- **場合 2**：$ax < 11$ のとき，$(a + 4)x = 21$\n"
            "  $a$ は正の整数（$a \\geq 1$）であるから，$a + 4 \\geq 5$ である。\n"
            "  21 の正の約数は $1, 3, 7, 21$ であるから，$a + 4$ の候補は $7$ または $21$ である。\n"
            "  - $a + 4 = 7$ のとき：$a = 3$\n"
            "    このとき $x = \\frac{21}{7} = 3$ である。\n"
            "    条件 $ax < 11$ を確認すると $3 \\times 3 = 9 < 11$ を満たし，適する。\n"
            "  - $a + 4 = 21$ のとき：$a = 17$\n"
            "    このとき $x = 1$ であるが，$ax = 17 \\times 1 = 17 > 11$ となり条件 $ax < 11$ に反するため不適。\n"
            "したがって，求める値は $a = 3, x = 3$ である。\n"
            "これより $\\text{W} = 3, \\text{X} = 3$ である。\n\n"
            "**【考査考点】**\n"
            "絶対値の定義による場合分け，無理数の有理化，約数を用いた整数の不定方程式の整数解の絞り込み。"
        )
    },
    {
        "q_num": 3,
        "localKey": "math-q-II_1",
        "answer_ref": "MATH_C2:II_1",
        "answer": "ABCD: 4323, EFG: -12, H: 1, I: 3",
        "title": "数学 コース2 第II問 (前半)：円に内接する三角形のベクトル方程式と共線条件",
        "points": [
            "ベクトル関係式 $3\\overrightarrow{OA} + 4\\overrightarrow{OB} + 2\\overrightarrow{OC} = \\vec{0}$ からの $\\overrightarrow{OD} = -\\frac{4}{3}k\\overrightarrow{OB} - \\frac{2}{3}k\\overrightarrow{OC}$ の導出",
            "3点 B, C, D の共線条件（係数の和が 1）による $k = -\\frac{1}{2}$ の決定",
            "半径 $OA = 2$ を用いた線分長 $OD = 1$ および $AD = 3$ の算出"
        ],
        "solution": (
            "**【題目大意】**\n"
            "半径 2 の円 O に内接する三角形 ABC が $3\\overrightarrow{OA} + 4\\overrightarrow{OB} + 2\\overrightarrow{OC} = \\vec{0}$ $\\cdots\\textcircled{1}$ を満たしている。\n"
            "直線 AO と線分 BC の交点を D とおく。\n"
            "(1) $\\overrightarrow{OD} = k\\overrightarrow{OA}$ とおくとき，$\\overrightarrow{OD}$ を $\\overrightarrow{OB}, \\overrightarrow{OC}$ で表し，3点 B, C, D が一直線上にあることから $k$ を求め，線分 OD および AD の長さを求める。\n\n"
            "**【公式正解】**\n"
            "正解：\n"
            "$\\text{ABCD} = 4323$\n"
            "$\\text{EFG} = -12$\n"
            "$\\text{H} = 1$\n"
            "$\\text{I} = 3$\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "1. **$\\overrightarrow{OD}$ の基底分解**：\n"
            "条件式 $\\textcircled{1}$ より：\n"
            "$$3\\overrightarrow{OA} = -4\\overrightarrow{OB} - 2\\overrightarrow{OC} \\implies \\overrightarrow{OA} = -\\frac{4}{3}\\overrightarrow{OB} - \\frac{2}{3}\\overrightarrow{OC}$$\n"
            "$\\overrightarrow{OD} = k\\overrightarrow{OA}$ であるから：\n"
            "$$\\overrightarrow{OD} = -\\frac{4}{3}k\\overrightarrow{OB} - \\frac{2}{3}k\\overrightarrow{OC}$$\n"
            "したがって，$\\text{A} = 4, \\text{B} = 3, \\text{C} = 2, \\text{D} = 3$（$\\text{ABCD} = 4323$）である。\n\n"
            "2. **共線条件による $k$ の決定**：\n"
            "点 D は直線 BC 上にあるため，$\\overrightarrow{OB}$ と $\\overrightarrow{OC}$ の係数の和は 1 に等しい：\n"
            "$$-\\frac{4}{3}k - \\frac{2}{3}k = 1$$\n"
            "$$-\\frac{6}{3}k = 1 \\implies -2k = 1 \\implies k = -\\frac{1}{2}$$\n"
            "したがって，$k = \\frac{-1}{2}$ であり，$\\text{EF} = -1, \\text{G} = 2$（$\\text{EFG} = -12$）である。\n\n"
            "3. **線分 OD および AD の長さ**：\n"
            "円 O の半径が 2 であるから，$|\\overrightarrow{OA}| = 2$ である。\n"
            "$\\overrightarrow{OD} = -\\frac{1}{2}\\overrightarrow{OA}$ より：\n"
            "$$OD = |\\overrightarrow{OD}| = \\left|-\\frac{1}{2}\\right| |\\overrightarrow{OA}| = \\frac{1}{2} \\times 2 = 1$$\n"
            "これより $\\text{H} = 1$ である。\n"
            "また，$\\overrightarrow{AD} = \\overrightarrow{OD} - \\overrightarrow{OA} = -\\frac{1}{2}\\overrightarrow{OA} - \\overrightarrow{OA} = -\\frac{3}{2}\\overrightarrow{OA}$ であるから：\n"
            "$$AD = |\\overrightarrow{AD}| = \\frac{3}{2} |\\overrightarrow{OA}| = \\frac{3}{2} \\times 2 = 3$$\n"
            "これより $\\text{I} = 3$ である。\n\n"
            "**【考査考点】**\n"
            "平面ベクトルの1次結合表示，3点の共線条件（係数の和＝1），位置ベクトルと線分比・距離の計算。"
        )
    },
    {
        "q_num": 4,
        "localKey": "math-q-II_2",
        "answer_ref": "MATH_C2:II_2",
        "answer": "JK: 13, LM: 82, NO: 36, PQRS: -114, TUV: 362, WX: 62",
        "title": "数学 コース2 第II問 (後半)：ベクトルの内積と内接円・線分長の決定",
        "points": [
            "内分比による $BD = \\frac{1}{3}BC$ の把握",
            "$|4\\overrightarrow{OB} + 2\\overrightarrow{OC}|^2 = 36$ からの内積 $\\overrightarrow{OB}\\cdot\\overrightarrow{OC} = -\\frac{11}{4}$ の算出",
            "$BC^2 = 8 - 2\\overrightarrow{OB}\\cdot\\overrightarrow{OC} = \\frac{27}{2}$ による線分長 $BC = \\frac{3\\sqrt{6}}{2}$ および $BD = \\frac{\\sqrt{6}}{2}$ の導出"
        ],
        "solution": (
            "**【題目大意】**\n"
            "前半の結果を用いて，内積 $\\overrightarrow{OB} \\cdot \\overrightarrow{OC}$ を求め，線分 BC および線分 BD の長さを求める。\n\n"
            "**【公式正解】**\n"
            "正解：\n"
            "$\\text{JK} = 13$\n"
            "$\\text{LM} = 82$\n"
            "$\\text{NO} = 36$\n"
            "$\\text{PQRS} = -114$\n"
            "$\\text{TUV} = 362$\n"
            "$\\text{WX} = 62$\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "1. **$BD$ と $BC$ の比**：\n"
            "$k = -\\frac{1}{2}$ を代入すると：\n"
            "$$\\overrightarrow{OD} = -\\frac{4}{3}\\left(-\\frac{1}{2}\\right)\\overrightarrow{OB} - \\frac{2}{3}\\left(-\\frac{1}{2}\\right)\\overrightarrow{OC} = \\frac{2}{3}\\overrightarrow{OB} + \\frac{1}{3}\\overrightarrow{OC}$$\n"
            "これは点 D が線分 BC を $1 : 2$ に内分していることを示す。\n"
            "したがって：\n"
            "$$BD = \\frac{1}{3} BC$$\n"
            "これより $\\text{J} = 1, \\text{K} = 3$（$\\text{JK} = 13$）である。\n\n"
            "2. **$BC^2$ と内積の関係**：\n"
            "$\\overrightarrow{BC} = \\overrightarrow{OC} - \\overrightarrow{OB}$ より：\n"
            "$$BC^2 = |\\overrightarrow{OC} - \\overrightarrow{OB}|^2 = |\\overrightarrow{OC}|^2 + |\\overrightarrow{OB}|^2 - 2\\overrightarrow{OB} \\cdot \\overrightarrow{OC}$$\n"
            "点 B, C は半径 2 の円周上にあるため，$|\\overrightarrow{OB}| = |\\overrightarrow{OC}| = 2$ である。\n"
            "したがって：\n"
            "$$BC^2 = 2^2 + 2^2 - 2\\overrightarrow{OB} \\cdot \\overrightarrow{OC} = 8 - 2\\overrightarrow{OB} \\cdot \\overrightarrow{OC}$$\n"
            "これより $\\text{L} = 8, \\text{M} = 2$（$\\text{LM} = 82$）である。\n\n"
            "3. **内積 $\\overrightarrow{OB} \\cdot \\overrightarrow{OC}$ の計算**：\n"
            "条件式 $\\textcircled{1}$ より：\n"
            "$$4\\overrightarrow{OB} + 2\\overrightarrow{OC} = -3\\overrightarrow{OA}$$\n"
            "両辺の大きさの 2 乗をとると：\n"
            "$$|4\\overrightarrow{OB} + 2\\overrightarrow{OC}|^2 = |-3\\overrightarrow{OA}|^2 = 9 |\\overrightarrow{OA}|^2 = 9 \\times 2^2 = 36$$\n"
            "これより $\\text{NO} = 36$ である。\n"
            "左辺を展開すると：\n"
            "$$16|\\overrightarrow{OB}|^2 + 16\\overrightarrow{OB} \\cdot \\overrightarrow{OC} + 4|\\overrightarrow{OC}|^2 = 36$$\n"
            "$$16(4) + 16\\overrightarrow{OB} \\cdot \\overrightarrow{OC} + 4(4) = 36$$\n"
            "$$64 + 16\\overrightarrow{OB} \\cdot \\overrightarrow{OC} + 16 = 36$$\n"
            "$$80 + 16\\overrightarrow{OB} \\cdot \\overrightarrow{OC} = 36 \\implies 16\\overrightarrow{OB} \\cdot \\overrightarrow{OC} = -44$$\n"
            "$$\\overrightarrow{OB} \\cdot \\overrightarrow{OC} = -\\frac{44}{16} = -\\frac{11}{4}$$\n"
            "したがって，$\\text{PQR} = -11, \\text{S} = 4$（$\\text{PQRS} = -114$）である。\n\n"
            "4. **線分 BC および BD の長さの算出**：\n"
            "$$BC^2 = 8 - 2\\left(-\\frac{11}{4}\\right) = 8 + \\frac{11}{2} = \\frac{27}{2}$$\n"
            "$$BC = \\sqrt{\\frac{27}{2}} = \\frac{3\\sqrt{3}}{\\sqrt{2}} = \\frac{3\\sqrt{6}}{2}$$\n"
            "これより $\\text{T} = 3, \\text{U} = 6, \\text{V} = 2$（$\\text{TUV} = 362$）である。\n"
            "したがって，線分 BD の長さは：\n"
            "$$BD = \\frac{1}{3} BC = \\frac{1}{3} \\times \\frac{3\\sqrt{6}}{2} = \\frac{\\sqrt{6}}{2}$$\n"
            "これより $\\text{W} = 6, \\text{X} = 2$（$\\text{WX} = 62$）である。\n\n"
            "**【考査考点】**\n"
            "内積の定義と性質，ベクトルの大きさの2乗展開，外接円の半径と幾何学的線分長の定量的計算。"
        )
    },
    {
        "q_num": 5,
        "localKey": "math-q-III_1",
        "answer_ref": "MATH_C2:III_1",
        "answer": "ABC: 223, DEF: 115",
        "title": "数学 コース2 第III問 (前半)：対数方程式の円の方程式への変形",
        "points": [
            "対数の性質 $\\log_2 \\frac{8x^2}{y^2} = 2\\log_2 x - 2\\log_2 y + 3$ による右辺の線形化",
            "変数変換 $X = \\log_2 x, Y = \\log_2 y$ による2次曲線の整理",
            "平方完成による円の方程式 $(X - 1)^2 + (Y + 1)^2 = 5$（中心 $(1, -1)$，半径 $\\sqrt{5}$）の導出"
        ],
        "solution": (
            "**【題目大意】**\n"
            "正の数 $x, y$ が $(\\log_2 x)^2 + (\\log_2 y)^2 = \\log_2 \\frac{8x^2}{y^2}$ $\\cdots\\textcircled{1}$ を満たす。\n"
            "$X = \\log_2 x, Y = \\log_2 y$ とおくとき，方程式を変形して円の方程式 $(X - D)^2 + (Y + E)^2 = F$ の形に表す。\n\n"
            "**【公式正解】**\n"
            "正解：\n"
            "$\\text{ABC} = 223$\n"
            "$\\text{DEF} = 115$\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "1. **右辺の対数変形**：\n"
            "対数の基本性質 $\\log_a \\frac{M}{N} = \\log_a M - \\log_a N$ および $\\log_a M^p = p\\log_a M$ を用いる：\n"
            "$$\\log_2 \\frac{8x^2}{y^2} = \\log_2 8 + \\log_2 x^2 - \\log_2 y^2 = 3 + 2\\log_2 x - 2\\log_2 y$$\n"
            "整理すると：\n"
            "$$\\log_2 \\frac{8x^2}{y^2} = 2\\log_2 x - 2\\log_2 y + 3$$\n"
            "したがって，$\\text{A} = 2, \\text{B} = 2, \\text{C} = 3$（$\\text{ABC} = 223$）である。\n\n"
            "2. **円の方程式への変形**：\n"
            "$X = \\log_2 x, Y = \\log_2 y$ を与式 $\\textcircled{1}$ に代入する：\n"
            "$$X^2 + Y^2 = 2X - 2Y + 3$$\n"
            "すべての項を左辺に移項して整理する：\n"
            "$$X^2 - 2X + Y^2 + 2Y = 3$$\n"
            "平方完成を行う：\n"
            "$$(X - 1)^2 - 1 + (Y + 1)^2 - 1 = 3$$\n"
            "$$(X - 1)^2 + (Y + 1)^2 = 5$$\n"
            "したがって，$\\text{D} = 1, \\text{E} = 1, \\text{F} = 5$（$\\text{DEF} = 115$）である。\n\n"
            "これは $XY$ 平面において，中心 $(1, -1)$，半径 $\\sqrt{5}$ の円を表す。\n\n"
            "**【考査考点】**\n"
            "対数の演算公式，対数変数変換による非線形方程式の幾何学的表現（円の方程式）への帰着。"
        )
    },
    {
        "q_num": 6,
        "localKey": "math-q-III_2",
        "answer_ref": "MATH_C2:III_2",
        "answer": "G: 2, H: 4, IJ: 16, K: 4, L: 2",
        "title": "数学 コース2 第III問 (後半)：線形計画法（円と直線の接点条件）による xy^2 の最大化",
        "points": [
            "目的関数 $k = \\log_2(xy^2) = X + 2Y$ による直線方程式 $X + 2Y - k = 0$ の設定",
            "点と直線の距離公式 $\\frac{|k+1|}{\\sqrt{5}} \\leq \\sqrt{5}$ による最大値 $k = 4$ の決定",
            "最大値 $xy^2 = 2^4 = 16$ および接点 $(X, Y) = (2, 1)$ からの $x = 4, y = 2$ の導出"
        ],
        "solution": (
            "**【題目大意】**\n"
            "$\\log_2 xy^2 = k$ とおくとき，$k$ の最大値，および $xy^2$ の最大値と，そのときの $x, y$ の値を求める。\n\n"
            "**【公式正解】**\n"
            "正解：\n"
            "$\\text{G} = 2$\n"
            "$\\text{H} = 4$\n"
            "$\\text{IJ} = 16$\n"
            "$\\text{K} = 4$\n"
            "$\\text{L} = 2$\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "1. **直線の方程式**：\n"
            "$\\log_2 xy^2 = \\log_2 x + 2\\log_2 y = X + 2Y$ であるから：\n"
            "$$k = X + 2Y \\implies X + 2Y - k = 0$$\n"
            "したがって $\\text{G} = 2$ である。\n\n"
            "2. **円と直線の共有点条件（接点における最大値）**：\n"
            "円 $(X - 1)^2 + (Y + 1)^2 = 5$ の中心 $(1, -1)$ と直線 $X + 2Y - k = 0$ の距離を $d$ とする。\n"
            "点と直線の距離公式より：\n"
            "$$d = \\frac{|1 \\cdot 1 + 2(-1) - k|}{\\sqrt{1^2 + 2^2}} = \\frac{|1 - 2 - k|}{\\sqrt{5}} = \\frac{|-k - 1|}{\\sqrt{5}} = \\frac{|k + 1|}{\\sqrt{5}}$$\n"
            "直線が円と共有点をもつ条件は $d \\leq \\sqrt{5}$ である：\n"
            "$$\\frac{|k + 1|}{\\sqrt{5}} \\leq \\sqrt{5} \\implies |k + 1| \\leq 5$$\n"
            "$$-5 \\leq k + 1 \\leq 5 \\implies -6 \\leq k \\leq 4$$\n"
            "したがって，$k$ の最大値は：\n"
            "$$k = 4$$\n"
            "これより $\\text{H} = 4$ である。\n"
            "このとき：\n"
            "$$xy^2 = 2^k = 2^4 = 16$$\n"
            "これより $\\text{IJ} = 16$ である。\n\n"
            "3. **そのときの $x, y$ の値**：\n"
            "$k = 4$ のとき，直線は円と接する。\n"
            "直線の法線ベクトルは $\\vec{n} = (1, 2)$ であるから，中心 $(1, -1)$ から半径 $\\sqrt{5}$ だけ法線方向に進んだ接点の座標 $(X, Y)$ は：\n"
            "$$(X, Y) = (1, -1) + \\frac{\\sqrt{5}}{\\sqrt{1^2+2^2}}(1, 2) = (1, -1) + (1, 2) = (2, 1)$$\n"
            "（確認：$2 + 2(1) = 4 = k$，$(2-1)^2 + (1+1)^2 = 1 + 4 = 5$ で円周上にある）\n"
            "したがって：\n"
            "- $X = \\log_2 x = 2 \\implies x = 2^2 = 4 \\implies \\text{K} = 4$\n"
            "- $Y = \\log_2 y = 1 \\implies y = 2^1 = 2 \\implies \\text{L} = 2$\n\n"
            "**【考査考点】**\n"
            "線形計画法（領域と境界線の幾何学的解析），点と直線の距離公式，対数関数の最大・最小問題。"
        )
    },
    {
        "q_num": 7,
        "localKey": "math-q-IV_1",
        "answer_ref": "MATH_C2:IV_1",
        "answer": "AB: 34, CDE: 323, F: 0, G: 3",
        "title": "数学 コース2 第IV問 [1]：三角関数の導関数の因数分解と区間内の最大・最小値",
        "points": [
            "極値条件 $f'(\\pi/3) = 0$ からの定数 $a = \\frac{3}{4}$ の決定",
            "導関数 $f'(x) = 3\\sin x (2\\cos x - 1)(\\sin x - 3)$ への因数分解（CDE: 323）",
            "区間 $[0, \\pi/2]$ における符号変化分析による最大値（$x = 0$）と最小値（$x = \\pi/3$）の特定"
        ],
        "solution": (
            "**【題目大意】**\n"
            "$a$ を定数とする。関数 $f(x) = 2\\sin^3 x + a\\sin 2x + \\frac{9}{2}\\cos 2x - 9\\cos x - 2ax + 6$ が $x = \\frac{\\pi}{3}$ で極値をもつ。\n"
            "(1) $a$ の値を求め，導関数 $f'(x)$ を因数分解する。\n"
            "(2) 区間 $0 \\leq x \\leq \\frac{\\pi}{2}$ における最大値・最小値をとる $x$ の値を求める。\n\n"
            "**【公式正解】**\n"
            "正解：\n"
            "$\\text{AB} = 34$\n"
            "$\\text{CDE} = 323$\n"
            "$\\text{F} = 0$\n"
            "$\\text{G} = 3$\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "1. **(1) 導関数 $f'(x)$ の計算と $a$ の決定**：\n"
            "各項を $x$ で微分する：\n"
            "- $(2\\sin^3 x)' = 6\\sin^2 x \\cos x$\n"
            "- $(a\\sin 2x)' = 2a\\cos 2x$\n"
            "- \\left(\\frac{9}{2}\\cos 2x\\right)' = -9\\sin 2x = -18\\sin x \\cos x$\n"
            "- $(-9\\cos x)' = 9\\sin x$\n"
            "- $(-2ax + 6)' = -2a$\n"
            "したがって：\n"
            "$$f'(x) = 6\\sin^2 x \\cos x + 2a\\cos 2x - 9\\sin 2x + 9\\sin x - 2a$$\n"
            "$x = \\frac{\\pi}{3}$ で極値をもつため，$f'\\left(\\frac{\\pi}{3}\\right) = 0$ である。\n"
            "$\\sin\\frac{\\pi}{3} = \\frac{\\sqrt{3}}{2},\\; \\cos\\frac{\\pi}{3} = \\frac{1}{2},\\; \\sin\\frac{2\\pi}{3} = \\frac{\\sqrt{3}}{2},\\; \\cos\\frac{2\\pi}{3} = -\\frac{1}{2}$ を代入すると：\n"
            "$$f'\\left(\\frac{\\pi}{3}\\right) = 6\\left(\\frac{3}{4}\\right)\\left(\\frac{1}{2}\\right) + 2a\\left(-\\frac{1}{2}\\right) - 9\\left(\\frac{\\sqrt{3}}{2}\\right) + 9\\left(\\frac{\\sqrt{3}}{2}\\right) - 2a = 0$$\n"
            "$$\\frac{9}{4} - a - 2a = 0 \\implies 3a = \\frac{9}{4} \\implies a = \\frac{3}{4}$$\n"
            "したがって，$\\text{A} = 3, \\text{B} = 4$（$\\text{AB} = 34$）である。\n\n"
            "2. **$f'(x)$ の因数分解**：\n"
            "$a = \\frac{3}{4}$ を代入し，$\\cos 2x = 1 - 2\\sin^2 x$ を用いると：\n"
            "$$2a\\cos 2x - 2a = 2a(\\cos 2x - 1) = \\frac{3}{2}(-2\\sin^2 x) = -3\\sin^2 x$$\n"
            "また，$-9\\sin 2x = -18\\sin x \\cos x$ であるから：\n"
            "$$f'(x) = 6\\sin^2 x \\cos x - 3\\sin^2 x - 18\\sin x \\cos x + 9\\sin x$$\n"
            "$$f'(x) = 3\\sin^2 x (2\\cos x - 1) - 9\\sin x (2\\cos x - 1)$$\n"
            "$$f'(x) = 3\\sin x (2\\cos x - 1)(\\sin x - 3)$$\n"
            "したがって，$\\text{C} = 3, \\text{D} = 2, \\text{E} = 3$（$\\text{CDE} = 323$）である。\n\n"
            "3. **(2) 区間 $[0, \\pi/2]$ における最大・最小値の判定**：\n"
            "区間 $0 < x < \\frac{\\pi}{2}$ において各因数の符号を調べる：\n"
            "- $3\\sin x > 0$\n"
            "- $\\sin x \\leq 1$ であるから，常に $\\sin x - 3 < 0$\n"
            "- $2\\cos x - 1$ の符号：\n"
            "  - $0 < x < \\frac{\\pi}{3}$ のとき，$\\cos x > \\frac{1}{2} \\implies 2\\cos x - 1 > 0$\n"
            "    このとき $f'(x) = (+) \\cdot (+) \\cdot (-) < 0$（単調減少）\n"
            "  - $\\frac{\\pi}{3} < x < \\frac{\\pi}{2}$ のとき，$\\cos x < \\frac{1}{2} \\implies 2\\cos x - 1 < 0$\n"
            "    このとき $f'(x) = (+) \\cdot (-) \\cdot (-) > 0$（単調増加）\n"
            "したがって，増減表より：\n"
            "- 最小値は $x = \\frac{\\pi}{3}$（選択肢 $\\textcircled{3}$）でとる $\\implies \\text{G} = 3$。\n"
            "- 最大値の候補は端点 $x = 0$ または $x = \\frac{\\pi}{2}$ である：\n"
            "  $$f(0) = 0 + 0 + \\frac{9}{2}(1) - 9(1) - 0 + 6 = \\frac{3}{2} = 1.5$$\n"
            "  $$f\\left(\\frac{\\pi}{2}\\right) = 2(1) + 0 + \\frac{9}{2}(-1) - 0 - 2\\left(\\frac{3}{4}\\right)\\left(\\frac{\\pi}{2}\\right) + 6 = 8 - 4.5 - \\frac{3\\pi}{4} = 3.5 - 0.75\\pi \\approx 3.5 - 2.356 = 1.144$$\n"
            "  $f(0) > f(\\pi/2)$ であるから，最大値は $x = 0$（選択肢 $\\textcircled{0}$）でとる $\\implies \\text{F} = 0$。\n\n"
            "**【考査考点】**\n"
            "三角関数の導関数の計算，極値条件による未定係数の決定，因数分解と符号解析，閉区間における増減表と端点比較。"
        )
    },
    {
        "q_num": 8,
        "localKey": "math-q-IV_2",
        "answer_ref": "MATH_C2:IV_2",
        "answer": "HIJKL: 54-14, MNO: 141, PQRST: 11214, U: 1, V: 4, W: 0, XY: 43",
        "title": "数学 コース2 第IV問 [2]：定積分漸化式・級数の和およびはさみうちの原理による極限",
        "points": [
            "部分積分法による初項 $a_1 = -\\frac{5}{4}e^{-1/4} + 1$ の算出（HIJKL: 54-14）",
            "部分積分漸化式 $a_{n+1} = -\\left(\\frac{1}{4}\\right)^{n+1}e^{-1/4} + (n+1)a_n$ の導出（MNO: 141）",
            "級数の和 $\\sum_{k=1}^n ka_k = a_{n+1} - a_1 + \\frac{1}{12}e^{-1/4}\\{1 - (1/4)^n\\}$ の立式（PQRST: 11214）",
            "不等式評価とはさみうちの原理による $\\lim a_n = 0$ および無限級数の和 $\\frac{4}{3}e^{-1/4}-1$ の決定"
        ],
        "solution": (
            "**【題目大意】**\n"
            "数列 $\{a_n\}$ を $a_n = \\int_0^{\\frac{1}{4}} x^n e^{-x} dx$ で定める。\n"
            "(1) $a_1$ および $a_{n+1}$ の漸化式を求め，$\\sum_{k=1}^n ka_k$ の和の式を導く。\n"
            "(2) 不等式評価によって $\\lim_{n \\to \\infty} a_n$ を求め，$\\lim_{n \\to \\infty} \\sum_{k=1}^n ka_k$ の値を求める。\n\n"
            "**【公式正解】**\n"
            "正解：\n"
            "$\\text{HIJKL} = 54-14$\n"
            "$\\text{MNO} = 141$\n"
            "$\\text{PQRST} = 11214$\n"
            "$\\text{U} = 1$\n"
            "$\\text{V} = 4$\n"
            "$\\text{W} = 0$\n"
            "$\\text{XY} = 43$\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "1. **$a_1$ の計算（部分積分法）**：\n"
            "$$a_1 = \\int_0^{\\frac{1}{4}} x e^{-x} dx = \\left[-x e^{-x}\\right]_0^{\\frac{1}{4}} + \\int_0^{\\frac{1}{4}} e^{-x} dx = -\\frac{1}{4}e^{-\\frac{1}{4}} + \\left[-e^{-x}\\right]_0^{\\frac{1}{4}}$$\n"
            "$$a_1 = -\\frac{1}{4}e^{-\\frac{1}{4}} - e^{-\\frac{1}{4}} + 1 = -\\frac{5}{4}e^{-\\frac{1}{4}} + 1$$\n"
            "したがって，$\\text{H} = 5, \\text{I} = 4, \\text{JK} = -1, \\text{L} = 4$（$\\text{HIJKL} = 54-14$）である。\n\n"
            "2. **漸化式の導出**：\n"
            "$$a_{n+1} = \\int_0^{\\frac{1}{4}} x^{n+1} e^{-x} dx = \\left[-x^{n+1} e^{-x}\\right]_0^{\\frac{1}{4}} + (n+1)\\int_0^{\\frac{1}{4}} x^n e^{-x} dx$$\n"
            "$$a_{n+1} = -\\left(\\frac{1}{4}\\right)^{n+1} e^{-\\frac{1}{4}} + (n+1)a_n$$\n"
            "したがって，$\\text{M} = 1, \\text{N} = 4, \\text{O} = 1$（$\\text{MNO} = 141$）である。\n\n"
            "3. **和 $\\sum_{k=1}^n ka_k$ の計算**：\n"
            "漸化式を変形すると：\n"
            "$$ka_k = a_{k+1} - a_k + \\left(\\frac{1}{4}\\right)^{k+1} e^{-\\frac{1}{4}}$$\n"
            "$k = 1$ から $n$ までの総和をとる：\n"
            "$$\\sum_{k=1}^n ka_k = \\sum_{k=1}^n (a_{k+1} - a_k) + e^{-\\frac{1}{4}} \\sum_{k=1}^n \\left(\\frac{1}{4}\\right)^{k+1}$$\n"
            "望遠和より $\\sum_{k=1}^n (a_{k+1} - a_k) = a_{n+1} - a_1$ である。\n"
            "幾何級数の和は：\n"
            "$$\\sum_{k=1}^n \\left(\\frac{1}{4}\\right)^{k+1} = \\frac{1}{16} \\frac{1 - (1/4)^n}{1 - 1/4} = \\frac{1}{16} \\cdot \\frac{4}{3} \\left\\{1 - \\left(\\frac{1}{4}\\right)^n\\right\\} = \\frac{1}{12}\\left\\{1 - \\left(\\frac{1}{4}\\right)^n\\right\\}$$\n"
            "したがって：\n"
            "$$\\sum_{k=1}^n ka_k = a_{n+1} - a_1 + \\frac{1}{12} e^{-\\frac{1}{4}} \\left\\{1 - \\left(\\frac{1}{4}\\right)^n\\right\\}$$\n"
            "これより $\\text{P} = 1, \\text{QR} = 12, \\text{S} = 1, \\text{T} = 4$（$\\text{PQRST} = 11214$）である。\n\n"
            "4. **極限の計算**：\n"
            "$0 \\leq x$ において $0 < e^{-x} \\leq 1$（$\\text{U} = 1$）であるから：\n"
            "$$0 < a_n < \\int_0^{\\frac{1}{4}} 1 \\cdot x^n dx = \\left[\\frac{x^{n+1}}{n+1}\\right]_0^{\\frac{1}{4}} = \\frac{1}{(n+1)4^{n+1}}$$\n"
            "これより $\\text{V} = 4$ である。\n"
            "$n \\to \\infty$ のとき $\\frac{1}{(n+1)4^{n+1}} \\to 0$ であるから，はさみうちの原理より：\n"
            "$$\\lim_{n \\to \\infty} a_n = 0$$\n"
            "これより $\\text{W} = 0$ である。\n"
            "したがって：\n"
            "$$\\lim_{n \\to \\infty} \\sum_{k=1}^n ka_k = 0 - a_1 + \\frac{1}{12} e^{-\\frac{1}{4}} (1 - 0)$$\n"
            "ここで $a_1 = -\\frac{5}{4}e^{-\\frac{1}{4}} + 1$ を代入すると：\n"
            "$$\\lim_{n \\to \\infty} \\sum_{k=1}^n ka_k = -\\left(-\\frac{5}{4}e^{-\\frac{1}{4}} + 1\\right) + \\frac{1}{12}e^{-\\frac{1}{4}} = \\left(\\frac{5}{4} + \\frac{1}{12}\\right)e^{-\\frac{1}{4}} - 1 = \\frac{16}{12}e^{-\\frac{1}{4}} - 1 = \\frac{4}{3}e^{-\\frac{1}{4}} - 1$$\n"
            "したがって，$\\text{X} = 4, \\text{Y} = 3$（$\\text{XY} = 43$）である。\n\n"
            "**【考査考点】**\n"
            "部分積分法による定積分漸化式，望遠和・等比級数の和，関数の不等式評価によるはさみうちの原理，無限級数の収束値計算。"
        )
    }
]

def main():
    out_dir = Path("work/2012-2-math-c2")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Save math-c2 explanations to json
    c2_path = out_dir / "explanations.json"
    with open(c2_path, "w", encoding="utf-8") as f:
        json.dump(math_c2_questions, f, ensure_ascii=False, indent=2)
    print(f"Generated {c2_path} ({len(math_c2_questions)} questions)")
    
    # Generate markdown documentation
    md_path = Path("docs/explanations/2012-2-math-c2-solutions.md")
    md_path.parent.mkdir(parents=True, exist_ok=True)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# 2012-2 EJU 数学 コース2 詳解\n\n")
        for q in math_c2_questions:
            f.write(f"## {q['title']}\n\n")
            f.write(q["solution"] + "\n\n---\n\n")
    print(f"Generated {md_path}")

if __name__ == "__main__":
    main()

