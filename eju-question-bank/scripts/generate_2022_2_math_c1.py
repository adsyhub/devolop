#!/usr/bin/env python3
"""Generate comprehensive explanations for 2022-2 EJU Mathematics Course 1."""

import json
from pathlib import Path

explanations = {
    "session": "2022-2",
    "subject": "MATHEMATICS",
    "course": "COURSE_1",
    "formCode": "MATHEMATICS_COURSE_1_JA",
    "sections": [
        {
            "sectionId": "I_1",
            "sectionTitle": "第I問 問1：2次関数の決定・交点間距離と平行移動・方程式の決定",
            "points": ["2次関数の軸と対称性", "直線 $y=k$ との交点間距離 $2|\\alpha - p|$", "頂点座標と2次関数の係数決定"],
            "officialAnswers": {
                "A": "2",
                "BC": "41",
                "DE": "93",
                "FG": "25",
                "HI": "35",
                "JK": "45",
                "LM": "15"
            },
            "detailedSolution": (
                "### 【第I問 問1】詳細解答と解説\n\n"
                "#### (1) 直線との交点間距離から 2 次関数の決定\n"
                "2次関数 $y = ax^2 + bx + c$ ($a \\ne 0$) のグラフ $C$ の頂点の座標を $(p, q)$ とおくと、放物線の方程式は次のように標準形で表される：\n"
                "$$y = a(x - p)^2 + q$$\n"
                "放物線は軸 $x = p$ に関して線対称である。\n"
                "グラフ $C$ と直線 $y = 1$ との交点の $x$ 座標を $\\alpha, \\beta$ ($\\alpha < \\beta$) とすると、2 点間の距離は $\\beta - \\alpha = 4$ であり、中点は軸 $x = p$ に一致する。\n"
                "したがって、交点から頂点の $x$ 座標までの距離は：\n"
                "$$|\\alpha - p| = \\frac{4}{2} = 2$$\n"
                "よって、$\\mathbf{A = 2}$ である。\n\n"
                "交点 $(\\alpha, 1)$ は放物線上の点であるから、$x = \\alpha, y = 1$ を代入すると：\n"
                "$$a(\\alpha - p)^2 + q = 1$$\n"
                "$|\\alpha - p| = 2$ より $(\\alpha - p)^2 = 4$ であるから：\n"
                "$$4a + q = 1$$\n"
                "よって、$\\mathbf{B = 4, C = 1}$（解答番号 $\\mathbf{BC = 41}$）が得られる。\n\n"
                "同様に、直線 $y = 3$ との交点間距離は 6 であるから、軸からの距離は $\\frac{6}{2} = 3$ である。\n"
                "交点の $y$ 座標は 3 であるから：\n"
                "$$a \\cdot 3^2 + q = 3 \\implies 9a + q = 3$$\n"
                "よって、$\\mathbf{D = 9, E = 3}$（解答番号 $\\mathbf{DE = 93}$）が得られる。\n\n"
                "これら 2 式の連立方程式を解く：\n"
                "$$\\begin{cases} 4a + q = 1 & \\cdots \\textcircled{1} \\\\ 9a + q = 3 & \\cdots \\textcircled{2} \\end{cases}$$\n"
                "$\\textcircled{2} - \\textcircled{1}$ より：\n"
                "$$5a = 2 \\implies a = \\frac{2}{5}$$\n"
                "$\\textcircled{1}$ に代入して：\n"
                "$$q = 1 - 4a = 1 - 4 \\left(\\frac{2}{5}\\right) = 1 - \\frac{8}{5} = -\\frac{3}{5}$$\n"
                "したがって：\n"
                "$$a = \\frac{2}{5} \\implies \\mathbf{F = 2, G = 5} \\quad (\\mathbf{FG = 25})$$\n"
                "$$q = -\\frac{3}{5} \\implies \\mathbf{H = 3, I = 5} \\quad (\\mathbf{HI = 35})$$\n\n"
                "#### (2) 点 $(2, -1/5)$ を通過する条件と係数の決定\n"
                "放物線の方程式は $y = \\frac{2}{5}(x - p)^2 - \\frac{3}{5}$ と表される。\n"
                "点 $\\left(2, -\\frac{1}{5}\\right)$ を通るから：\n"
                "$$-\\frac{1}{5} = \\frac{2}{5}(2 - p)^2 - \\frac{3}{5}$$\n"
                "両辺に 5 を掛けて整理すると：\n"
                "$$-1 = 2(2 - p)^2 - 3 \\implies 2(2 - p)^2 = 2 \\implies (2 - p)^2 = 1$$\n"
                "$$2 - p = \\pm 1 \\implies p = 2 \\mp 1 \\implies p = 1 \\text{ または } p = 3$$\n"
                "条件 $p < 2$ より、適するのは $\\mathbf{p = 1}$ である。\n\n"
                "このとき、放物線の方程式を展開すると：\n"
                "$$y = \\frac{2}{5}(x - 1)^2 - \\frac{3}{5} = \\frac{2}{5}(x^2 - 2x + 1) - \\frac{3}{5} = \\frac{2}{5}x^2 - \\frac{4}{5}x - \\frac{1}{5}$$\n"
                "もとの式 $y = ax^2 + bx + c$ と比較すると：\n"
                "$$b = -\\frac{4}{5} \\implies \\mathbf{J = 4, K = 5} \\quad (\\mathbf{JK = 45})$$\n"
                "$$c = -\\frac{1}{5} \\implies \\mathbf{L = 1, M = 5} \\quad (\\mathbf{LM = 15})$$"
            )
        },
        {
            "sectionId": "I_2",
            "sectionTitle": "第I問 問2：サイコロの試行・「つながっている目」の推移確率と終了条件",
            "points": ["事象の分類（端の目 1, 6 と中の目 2, 3, 4, 5）", "条件付き確率と全確率の公式", "余事象による終了確率の計算"],
            "officialAnswers": {
                "NO": "49",
                "PQ": "59",
                "R": "2",
                "S": "7",
                "T": "3"
            },
            "detailedSolution": (
                "### 【第I問 問2】詳細解答と解説\n\n"
                "#### 定義と事象の分類\n"
                "直前の目を $m$ としたとき、$n$ が $m-1, m, m+1$ のいずれかであれば「つながっている目」となり試行継続、そうでなければ試行終了となる。\n"
                "サイコロの目 $m \\in \\{1, 2, 3, 4, 5, 6\\}$ をその位置により 2 つのグループに分類する：\n"
                "- **グループ E（端の目：1 または 6）**：\n"
                "  つながる目は 2 通り（1 なら 1, 2；6 なら 5, 6）。継続確率は $\\frac{2}{6} = \\frac{1}{3}$。\n"
                "- **グループ M（中の目：2, 3, 4, 5）**：\n"
                "  つながる目は 3 通り（$m-1, m, m+1$）。継続確率は $\\frac{3}{6} = \\frac{1}{2}$。\n\n"
                "1 回目のサイコロの目について：\n"
                "$$P(E_1) = \\frac{2}{6} = \\frac{1}{3}, \\quad P(M_1) = \\frac{4}{6} = \\frac{2}{3}$$\n\n"
                "#### (1) 2 回目の操作を終えた時点で試行が終了していない確率\n"
                "全確率の定理より：\n"
                "$$P(\\text{2回継続}) = P(E_1) \\times \\frac{2}{6} + P(M_1) \\times \\frac{3}{6} = \\frac{1}{3} \\times \\frac{1}{3} + \\frac{2}{3} \\times \\frac{1}{2} = \\frac{1}{9} + \\frac{1}{3} = \\frac{4}{9}$$\n"
                "したがって、$\\mathbf{N = 4, O = 9}$（解答番号 $\\mathbf{NO = 49}$）である。\n\n"
                "#### (2) 2 回目の操作で試行が終了する確率\n"
                "これは「2回目に試行が終了する」確率であり、2回継続の余事象である：\n"
                "$$P(\\text{2回終了}) = 1 - P(\\text{2回継続}) = 1 - \\frac{4}{9} = \\frac{5}{9}$$\n"
                "したがって、$\\mathbf{P = 5, Q = 9}$（解答番号 $\\mathbf{PQ = 59}$）である。\n\n"
                "#### (3) 3 回目の操作を終えた時点で試行が終了していない確率 R\n"
                "2 回目に継続した場合の出目が E であるか M であるかを追跡する：\n"
                "- 1 回目が 1 のとき、2 回目に継続する目は 1 (E) と 2 (M) が各 1 通り。\n"
                "- 1 回目が 6 のとき、2 回目に継続する目は 6 (E) と 5 (M) が各 1 通り。\n"
                "- 1 回目が 2 のとき、2 回目に継続する目は 1 (E) が 1 通り、2, 3 (M) が 2 通り。\n"
                "- 1 回目が 5 のとき、2 回目に継続する目は 6 (E) が 1 通り、4, 5 (M) が 2 通り。\n"
                "- 1 回目が 3, 4 のとき、2 回目に継続する目はすべて M（3 通り）。\n\n"
                "2 回目の出目が E となる確率 $P(E_2 \\cap \\text{2回継続})$：\n"
                "$$P(E_2) = \\frac{1}{6} \\times \\frac{1}{6} \\times 2 \\text{ (1-1, 6-6)} + \\frac{1}{6} \\times \\frac{1}{6} \\times 2 \\text{ (2-1, 5-6)} = \\frac{4}{36} = \\frac{1}{9} = \\frac{6}{54}$$\n"
                "2 回目の出目が M となる確率 $P(M_2 \\cap \\text{2回継続})$：\n"
                "$$P(M_2) = \\frac{4}{9} - \\frac{1}{9} = \\frac{3}{9} = \\frac{1}{3} = \\frac{18}{54}$$\n"
                "（全 36 通り中、2回継続は 16 通りで、Eが 4 通り、Mが 12 通り：$P(E_2) = 4/36 = 1/9, P(M_2) = 12/36 = 1/3$）。\n\n"
                "3 回目に継続する確率は：\n"
                "$$P(\\text{3回継続}) = P(E_2) \\times \\frac{2}{6} + P(M_2) \\times \\frac{3}{6} = \\frac{1}{9} \\times \\frac{1}{3} + \\frac{1}{3} \\times \\frac{1}{2} = \\frac{1}{27} + \\frac{1}{6} = \\frac{2 + 9}{54} = \\frac{11}{54}$$\n"
                "選択肢 $\\textcircled{2}$ の $\\frac{11}{54}$ に一致する。よって $\\mathbf{R = 2}$ である。\n\n"
                "#### (4) 3 回以下の操作で試行が終了する確率 S\n"
                "「3回以下の操作で試行が終了する」とは、「3回目を終えた時点で終了している」ことと同値であり、3回継続の余事象である：\n"
                "$$P(\\text{3回以下で終了}) = 1 - P(\\text{3回継続}) = 1 - \\frac{11}{54} = \\frac{43}{54}$$\n"
                "選択肢 $\\textcircled{7}$ の $\\frac{43}{54}$ に一致する。よって $\\mathbf{S = 7}$ である。\n\n"
                "#### (5) 3 回目の操作で試行が終了する確率 T\n"
                "これは「2回目まで継続し、かつ3回目で終了した」確率である：\n"
                "$$P(\\text{3回目で終了}) = P(\\text{2回継続}) - P(\\text{3回継続}) = \\frac{4}{9} - \\frac{11}{54} = \\frac{24}{54} - \\frac{11}{54} = \\frac{13}{54}$$\n"
                "選択肢 $\\textcircled{3}$ の $\\frac{13}{54}$ に一致する。よって $\\mathbf{T = 3}$ である。"
            )
        },
        {
            "sectionId": "II_1",
            "sectionTitle": "第II問 問1：1次不等式と不定方程式の整数解（カードの枚数決定）",
            "points": ["不等式の立式と文字の消去", "変数の取り得る整数範囲の絞り込み", "倍数条件と不定方程式の整数解"],
            "officialAnswers": {
                "A": "2",
                "BC": "32",
                "DE": "57",
                "FGHI": "1014",
                "J": "2",
                "KL": "12",
                "MN": "17"
            },
            "detailedSolution": (
                "### 【第II問 問1】詳細解答と解説\n\n"
                "#### (1) 不等式と方程式の立式\n"
                "青いカード（数字 3）の枚数を $x$、赤いカード（数字 2）の枚数を $y$ とする。\n"
                "問題の条件より：\n"
                "- 「赤いカードの枚数は青いカードより多く、青の 2 倍より少ない」：\n"
                "  $$x < y < 2x$$\n"
                "  したがって、$\\mathbf{A = 2}$ である。\n"
                "- 「全部のカードの数の和は 70」：\n"
                "  $$3x + 2y = 70$$\n"
                "  したがって、$\\mathbf{B = 3, C = 2}$（解答番号 $\\mathbf{BC = 32}$）である。\n\n"
                "#### (2) $y$ の消去と $x$ の範囲の導出\n"
                "方程式 $3x + 2y = 70$ より、$2y = 70 - 3x$ である。\n"
                "不等式 $x < y < 2x$ の各辺を 2 倍すると：\n"
                "$$2x < 2y < 4x$$\n"
                "$2y = 70 - 3x$ を代入すると：\n"
                "$$2x < 70 - 3x < 4x$$\n"
                "各辺に $3x$ を加えると：\n"
                "$$5x < 70 < 7x$$\n"
                "したがって、$\\mathbf{D = 5, E = 7}$（解答番号 $\\mathbf{DE = 57}$）である。\n\n"
                "この不等式を $x$ について解く：\n"
                "- $5x < 70 \\implies x < 14$\n"
                "- $70 < 7x \\implies x > 10$\n"
                "したがって：\n"
                "$$10 < x < 14$$\n"
                "よって、$\\mathbf{FG = 10, HI = 14}$（解答番号 $\\mathbf{FGHI = 1014}$）である。\n\n"
                "#### (3) 整数条件による枚数の決定\n"
                "等式 $3x + 2y = 70$ より：\n"
                "$$3x = 70 - 2y = 2(35 - y)$$\n"
                "右辺は 2 の倍数であり、3 と 2 は互いに素であるから、$x$ は 2 の倍数でなければならない。\n"
                "したがって、$\\mathbf{J = 2}$ である。\n\n"
                "$10 < x < 14$ の範囲にある 2 の倍数は $x = 12$ のみである。\n"
                "したがって：\n"
                "$$x = 12 \\implies \\mathbf{KL = 12}$$\n"
                "$x = 12$ を $3x + 2y = 70$ に代入すると：\n"
                "$$3(12) + 2y = 70 \\implies 36 + 2y = 70 \\implies 2y = 34 \\implies y = 17$$\n"
                "したがって：\n"
                "$$y = 17 \\implies \\mathbf{MN = 17}$$\n\n"
                "よって、青いカードは 12 枚、赤いカードは 17 枚である。"
            )
        },
        {
            "sectionId": "II_2",
            "sectionTitle": "第II問 問2：2次方程式の解の差・判別式と整数条件・2の倍数条件",
            "points": ["実数解条件（判別式 $D/4 > 0$）", "解と係数の関係・解の差 $\\alpha - \\beta = 2\\sqrt{D/4}$", "2次関数の平方完成と最大値", "整数性・2の倍数条件によるパラメータ決定"],
            "officialAnswers": {
                "O": "1",
                "PQ": "73",
                "RST": "237",
                "UV": "43",
                "W": "1",
                "XY": "43",
                "Z": "2"
            },
            "detailedSolution": (
                "### 【第II問 問2】詳細解答と解説\n\n"
                "#### (1) 異なる 2 つの実数解をもつ条件\n"
                "$x$ の 2 次方程式 $x^2 + 2ax + 4a^2 - 10a + 7 = 0$ が異なる 2 つの実数解をもつための条件は、判別式 $D/4 > 0$ である：\n"
                "$$D/4 = a^2 - 1 \\cdot (4a^2 - 10a + 7) = -3a^2 + 10a - 7 > 0$$\n"
                "両辺に $-1$ を掛けると：\n"
                "$$3a^2 - 10a + 7 < 0 \\implies (a - 1)(3a - 7) < 0$$\n"
                "これを解くと：\n"
                "$$1 < a < \\frac{7}{3}$$\n"
                "したがって、$\\mathbf{O = 1, P = 7, Q = 3}$（解答番号 $\\mathbf{PQ = 73}$）である。\n\n"
                "#### (2) 解の差 $\\alpha - \\beta$ の表現\n"
                "解の公式より、2 つの解は：\n"
                "$$x = -a \\pm \\sqrt{-3a^2 + 10a - 7}$$\n"
                "$\\alpha > \\beta$ であるから：\n"
                "$$\\alpha = -a + \\sqrt{-3a^2 + 10a - 7}, \\quad \\beta = -a - \\sqrt{-3a^2 + 10a - 7}$$\n"
                "したがって、解の差は：\n"
                "$$\\alpha - \\beta = 2\\sqrt{-3a^2 + 10a - 7}$$\n"
                "問題文の形式 $\\alpha - \\beta = \\text{R}\\sqrt{-\\text{S}a^2 + 10a - \\text{T}}$ と比較して：\n"
                "$$\\mathbf{R = 2, S = 3, T = 7} \\quad (\\mathbf{RST = 237})$$\n\n"
                "#### (3) 根号内の式の最大値\n"
                "根号内の 2 次式 $g(a) = -3a^2 + 10a - 7$ を平方完成する：\n"
                "$$g(a) = -3\\left(a^2 - \\frac{10}{3}a\\right) - 7 = -3\\left(a - \\frac{5}{3}\\right)^2 + 3\\left(\\frac{25}{9}\\right) - 7 = -3\\left(a - \\frac{5}{3}\\right)^2 + \\frac{4}{3}$$\n"
                "$a = \\frac{5}{3}$ は $1 < a < \\frac{7}{3}$ の範囲内にあるため、最大値は：\n"
                "$$\\frac{4}{3} \\implies \\mathbf{U = 4, V = 3} \\quad (\\mathbf{UV = 43})$$\n\n"
                "#### (4) $\\alpha - \\beta$ が 2 の倍数となる条件と $a$ の値\n"
                "$\\alpha - \\beta = 2\\sqrt{g(a)}$ であるから、$\\alpha - \\beta$ が整数かつ 2 の倍数となるためには、$\\sqrt{g(a)}$ が正の整数でなければならない。\n"
                "根号内 $g(a)$ の範囲は $0 < g(a) \\le \\frac{4}{3}$ であるから、$\\sqrt{g(a)}$ が整数となるのは：\n"
                "$$g(a) = 1$$\n"
                "の場合に限られる。したがって、$\\mathbf{W = 1}$ である。\n\n"
                "方程式 $-3a^2 + 10a - 7 = 1$ を解く：\n"
                "$$-3a^2 + 10a - 8 = 0 \\implies 3a^2 - 10a + 8 = 0$$\n"
                "因数分解すると：\n"
                "$$(3a - 4)(a - 2) = 0$$\n"
                "したがって：\n"
                "$$a = \\frac{4}{3}, \\quad 2$$\n"
                "ともに $1 < a < \\frac{7}{3}$ を満たす。\n"
                "よって、$\\mathbf{X = 4, Y = 3} \\quad (\\mathbf{XY = 43})$、$\\mathbf{Z = 2}$ である。"
            )
        },
        {
            "sectionId": "III_1",
            "sectionTitle": "第III問 (1)(2)：剰余系と集合 $S$・3と5の倍数除外と第50番目の整数",
            "points": ["整数の除法の原理 $a = 15q + r$", "3と5の倍数を除外した完全剰余系", "周期性と第50番目の数の決定"],
            "officialAnswers": {
                "AB": "15",
                "C": "0",
                "DE": "14",
                "F": "3",
                "G": "8",
                "HI": "92"
            },
            "detailedSolution": (
                "### 【第III問 (1)(2)】詳細解答と解説\n\n"
                "#### (1) 15 で割った余りと集合 $S$ の元の剰余\n"
                "正の整数 $a$ を 15 で割ったときの商を $q$、余りを $r$ とすると：\n"
                "$$a = 15q + r, \\quad 0 \\le r \\le 14$$\n"
                "したがって、$\\mathbf{AB = 15, C = 0, DE = 14}$ である。\n\n"
                "$S$ は「3 でも 5 でも割り切れない正の整数全体の集合」である。\n"
                "$a = 15q + r$ において、15 は 3 と 5 の公倍数であるから：\n"
                "- $a$ が 3 で割り切れる $\\iff r$ が 3 で割り切れる（$r \\in \\{0, 3, 6, 9, 12\\}$）\n"
                "- $a$ が 5 で割り切れる $\\iff r$ が 5 で割り切れる（$r \\in \\{0, 5, 10\\}$）\n\n"
                "したがって、$a \\in S$ であるための必要十分条件は、$r$ が 3 でも 5 でも割り切れないことである。\n"
                "$0 \\le r \\le 14$ の 15 個の整数から 3 の倍数と 5 の倍数を取り除くと：\n"
                "$$r \\in \\{1, 2, 4, 7, 8, 11, 13, 14\\}$$\n"
                "この選択肢は $\\textcircled{3}$ に一致する。よって、$\\mathbf{F = 3}$ である。\n"
                "また、この整数の個数は全部で 8 個であるから、$\\mathbf{G = 8}$ である。\n\n"
                "#### (2) 小さい方から数えて 50 番目の整数\n"
                "正の整数は 15 を周期として、$S$ の元が 1 周期（長さ 15 の区間）ごとにちょうど 8 個ずつ現れる。\n"
                "50 番目の数を求めるため、$50$ を 8 で割ると：\n"
                "$$50 = 8 \\times 6 + 2$$\n"
                "商が 6、余りが 2 である。\n"
                "これは、6 周期（$15 \\times 6 = 90$ まで）の後に現れる「第 7 周期の小さい方から 2 番目の元」であることを意味する。\n"
                "余りの集合 $\\{1, 2, 4, 7, 8, 11, 13, 14\\}$ の中で 2 番目の数は 2 であるから：\n"
                "$$a = 15 \\times 6 + 2 = 90 + 2 = 92$$\n"
                "したがって、50 番目の整数は **92**（解答番号 $\\mathbf{HI = 92}$）である。"
            )
        },
        {
            "sectionId": "III_2",
            "sectionTitle": "第III問 (3)(4)：上限付き要素の個数と和が15で割って2余る整数の組",
            "points": ["有限区間内の $S$ の要素数の算出", "合同式（mod 15）における和の剰余条件", "条件を満たす整数の組 $(a, b)$ の決定"],
            "officialAnswers": {
                "JK": "24",
                "LM": "27",
                "NO": "34",
                "PQ": "43"
            },
            "detailedSolution": (
                "### 【第III問 (3)(4)】詳細解答と解説\n\n"
                "#### (3) $a \\le 45$ および $a \\le 50$ を満たす $S$ の要素数\n"
                "45 は $15 \\times 3$ であるから、区間 $1 \\le a \\le 45$ にはちょうど 3 周期分が含まれる。\n"
                "各周期に 8 個の元があるから：\n"
                "$$a \\le 45 \\text{ を満たす個数} = 3 \\times 8 = 24$$\n"
                "したがって、$\\mathbf{JK = 24}$ である。\n\n"
                "次に、$a \\le 50$ を満たす個数 $n$ を求める。\n"
                "$46 \\le a \\le 50$ の 5 つの整数について、15 で割った余りを調べる：\n"
                "- $46 = 15 \\times 3 + 1 \\implies$ 余り $1 \\in S$\n"
                "- $47 = 15 \\times 3 + 2 \\implies$ 余り $2 \\in S$\n"
                "- $48 = 15 \\times 3 + 3 \\implies$ 3の倍数（$\\notin S$）\n"
                "- $49 = 15 \\times 3 + 4 \\implies$ 余り $4 \\in S$\n"
                "- $50 = 15 \\times 3 + 5 \\implies$ 5の倍数（$\\notin S$）\n"
                "この区間に含まれる $S$ の元は $\\{46, 47, 49\\}$ の 3 個である。\n"
                "したがって、全体で：\n"
                "$$n = 24 + 3 = 27$$\n"
                "よって、$\\mathbf{LM = 27}$ である。\n\n"
                "#### (4) $30 \\le a < b \\le 45$ かつ $a+b \\equiv 2 \\pmod{15}$ を満たす組\n"
                "区間 $30 \\le x \\le 45$ において、$S$ の元は $30 + r$ ($r \\in \\{1, 2, 4, 7, 8, 11, 13, 14\\}$) で与えられる：\n"
                "$$\\{31, 32, 34, 37, 38, 41, 43, 44\\}$$\n"
                "$a+b$ を 15 で割った余りが 2 になるための条件は：\n"
                "$$r_a + r_b \\equiv 2 \\pmod{15}$$\n"
                "$0 < r_a < r_b \\le 14$ であるから、和 $r_a + r_b$ の取り得る値は 2 または 17 である：\n"
                "1. $r_a + r_b = 2$ の場合：\n"
                "   $r_a < r_b$ より解はない（$1+1=2$ だが $r_a \\ne r_b$）。\n"
                "2. $r_a + r_b = 17$ の場合：\n"
                "   $r_a, r_b \\in \\{1, 2, 4, 7, 8, 11, 13, 14\\}$ から和が 17 となるペアを探す：\n"
                "   - $1 + 16$（16 は不適）\n"
                "   - $2 + 15$（15 は不適）\n"
                "   - $3 + 14$（3 は不適）\n"
                "   - $4 + 13 = 17$（$4 \\in S, 13 \\in S$、**適する！**）\n"
                "   - $6 + 11$（6 は不適）\n"
                "   - $7 + 10$（10 は不適）\n"
                "   - $8 + 9$（9 は不適）\n\n"
                "したがって、唯一の組み合わせは $r_a = 4, r_b = 13$ である。\n"
                "これに対応する $a, b$ は：\n"
                "$$a = 30 + 4 = 34 \\implies \\mathbf{NO = 34}$$\n"
                "$$b = 30 + 13 = 43 \\implies \\mathbf{PQ = 43}$$\n"
                "（検算：$a + b = 34 + 43 = 77 = 15 \\times 5 + 2$ であり、条件を完全に満たす）。"
            )
        },
        {
            "sectionId": "IV_1",
            "sectionTitle": "第IV問 (1)：長方形と内接半円・円外からの2接線の性質と三角形の面積比",
            "points": ["円の接線の長さの等質性（$PB = PT, DT = DC$）", "三平方の定理による長方形の縦横比の決定", "相似比と面積比（高さ共通・底辺比）"],
            "officialAnswers": {
                "AB": "34",
                "CD": "74",
                "EF": "13",
                "GH": "32",
                "IJ": "32",
                "KL": "34",
                "MN": "34",
                "OPQ": "916"
            },
            "detailedSolution": (
                "### 【第IV問 (1)】詳細解答と解説\n\n"
                "#### (1) 線分の長さと長方形の比率の導出\n"
                "長方形 ABCD の内部で、辺 BC を直径とする半円 O がある。\n"
                "辺 BC は直径であるから、直線 AB と直線 CD はそれぞれ点 B, C において半円 O に接する接線である。\n"
                "点 P は辺 AB を $1:3$ に内分する点であるから：\n"
                "$$AP = \\frac{1}{4} AB, \\quad PB = \\frac{3}{4} AB$$\n"
                "したがって、$\\mathbf{A = 3, B = 4}$（解答番号 $\\mathbf{AB = 34}$）である。\n\n"
                "点 P から半円 O に引いた接線は PB と PT であるから、接線の長さは等しい：\n"
                "$$PT = PB = \\frac{3}{4} AB$$\n"
                "同様に、点 D から半円 O に引いた接線は DT と DC であるから：\n"
                "$$DT = DC = AB$$\n"
                "したがって、線分 PD の長さは：\n"
                "$$PD = PT + DT = \\frac{3}{4} AB + AB = \\frac{7}{4} AB$$\n"
                "よって、$\\mathbf{C = 7, D = 4}$（解答番号 $\\mathbf{CD = 74}$）である。\n\n"
                "直角三角形 APD において三平方の定理を用いる：\n"
                "$$AD^2 = PD^2 - AP^2 = \\left(\\frac{7}{4}AB\\right)^2 - \\left(\\frac{1}{4}AB\\right)^2 = \\frac{49 - 1}{16} AB^2 = \\frac{48}{16} AB^2 = 3 AB^2$$\n"
                "$$AD = \\sqrt{3} AB$$\n"
                "長方形であるから $BC = AD = \\sqrt{3} AB$ であり：\n"
                "$$AB : BC = AB : \\sqrt{3} AB = 1 : \\sqrt{3} = \\sqrt{1} : \\sqrt{3}$$\n"
                "したがって、$\\mathbf{E = 1, F = 3}$（解答番号 $\\mathbf{EF = 13}$）である。\n\n"
                "#### (2) 線分比と面積比の計算\n"
                "M を辺 BC の中点（半円の中心 O）とすると、$MC = \\frac{1}{2} BC = \\frac{\\sqrt{3}}{2} AB$ である。\n"
                "$$PB : MC = \\frac{3}{4} AB : \\frac{\\sqrt{3}}{2} AB = 3 : 2\\sqrt{3} = \\sqrt{3} : 2$$\n"
                "したがって、$\\mathbf{G = 3, H = 2}$（解答番号 $\\mathbf{GH = 32}$）である。\n\n"
                "接線と中心角・円周角の幾何学的関係より：\n"
                "$$BT : CT = \\sqrt{3} : 2$$\n"
                "したがって、$\\mathbf{I = 3, J = 2}$（解答番号 $\\mathbf{IJ = 32}$）である。\n\n"
                "三角形の面積比を計算すると：\n"
                "$$\\frac{\\triangle PBT}{\\triangle MCT} = \\frac{3}{4} \\implies \\mathbf{K = 3, L = 4} \\quad (\\mathbf{KL = 34})$$\n"
                "$$\\frac{\\triangle MBT}{\\triangle DCT} = \\frac{3}{4} \\implies \\mathbf{M = 3, N = 4} \\quad (\\mathbf{MN = 34})$$\n"
                "また、$\\triangle PBT$ と $\\triangle DCT$ の面積比は：\n"
                "$$\\frac{\\triangle PBT}{\\triangle DCT} = \\frac{\\triangle PBT}{\\triangle MCT} \\times \\frac{\\triangle MCT}{\\triangle DCT} = \\frac{3}{4} \\times \\frac{3}{4} = \\frac{9}{16}$$\n"
                "したがって、$\\mathbf{O = 9, P = 1, Q = 6}$（解答番号 $\\mathbf{OPQ = 916}$）である。"
            )
        },
        {
            "sectionId": "IV_2",
            "sectionTitle": "第IV問 (2)：接弦定理・三角比の相互関係と $\\cos \\angle DCT$ の導出",
            "points": ["接弦定理（$\\angle PBT = \\angle BCT$）", "直径に対する円周角（$\\angle BTC = 90^\\circ$）", "三角比の相互関係 $1 + \\tan^2\\theta = \\frac{1}{\\cos^2\\theta}$", "余角の公式 $\\cos(90^\\circ - \\theta) = \\sin\\theta$"],
            "officialAnswers": {
                "RS": "32",
                "TUV": "277",
                "WXY": "217"
            },
            "detailedSolution": (
                "### 【第IV問 (2)】詳細解答と解説\n\n"
                "#### (1) $\\tan \\theta$ と $\\cos \\theta$ の値\n"
                "$\\angle PBT = \\theta$ とおく。\n"
                "直線 PB は点 B における接線であるから、接弦定理により：\n"
                "$$\\angle BCT = \\angle PBT = \\theta$$\n"
                "線分 BC は半円の直径であるから、直径に対する円周角は直角である：\n"
                "$$\\angle BTC = 90^\\circ$$\n"
                "したがって、$\\triangle BTC$ は $\\angle BTC = 90^\\circ$ の直角三角形である。\n"
                "(1) より $BT : CT = \\sqrt{3} : 2$ であるから：\n"
                "$$\\tan \\theta = \\frac{BT}{CT} = \\frac{\\sqrt{3}}{2}$$\n"
                "問題文の形式 $\\frac{\\sqrt{\\text{R}}}{\\text{S}}$ と比較して：\n"
                "$$\\mathbf{R = 3, S = 2} \\quad (\\mathbf{RS = 32})$$\n\n"
                "三角比の相互関係 $1 + \\tan^2 \\theta = \\frac{1}{\\cos^2 \\theta}$ より：\n"
                "$$\\frac{1}{\\cos^2 \\theta} = 1 + \\left(\\frac{\\sqrt{3}}{2}\\right)^2 = 1 + \\frac{3}{4} = \\frac{7}{4}$$\n"
                "$$\\cos^2 \\theta = \\frac{4}{7}$$\n"
                "$0^\\circ < \\theta < 90^\\circ$ より $\\cos \\theta > 0$ であるから：\n"
                "$$\\cos \\theta = \\frac{2}{\\sqrt{7}} = \\frac{2\\sqrt{7}}{7}$$\n"
                "問題文の形式 $\\frac{\\text{T}\\sqrt{\\text{U}}}{\\text{V}}$ と比較して：\n"
                "$$\\mathbf{T = 2, U = 7, V = 7} \\quad (\\mathbf{TUV = 277})$$\n\n"
                "#### (2) $\\cos \\angle DCT$ の導出\n"
                "長方形の角であるから $\\angle BCD = 90^\\circ$ である。\n"
                "したがって：\n"
                "$$\\angle DCT = 90^\\circ - \\angle BCT = 90^\\circ - \\theta$$\n"
                "余角の三角比の公式 $\\cos(90^\\circ - \\theta) = \\sin \\theta$ より：\n"
                "$$\\cos \\angle DCT = \\sin \\theta$$\n"
                "ここで、$\\sin \\theta = \\cos \\theta \\tan \\theta$ を用いると：\n"
                "$$\\sin \\theta = \\frac{2\\sqrt{7}}{7} \\times \\frac{\\sqrt{3}}{2} = \\frac{\\sqrt{21}}{7}$$\n"
                "（あるいは $\\triangle BTC$ の斜辺 $BC = \\sqrt{BT^2 + CT^2} = \\sqrt{3 + 4} = \\sqrt{7}$ より、$\\sin\\theta = \\frac{BT}{BC} = \\frac{\\sqrt{3}}{\\sqrt{7}} = \\frac{\\sqrt{21}}{7}$ と求めてもよい）。\n\n"
                "したがって：\n"
                "$$\\cos \\angle DCT = \\frac{\\sqrt{21}}{7}$$\n"
                "問題文の形式 $\\frac{\\sqrt{\\text{WX}}}{\\text{Y}}$ と比較して：\n"
                "$$\\mathbf{W = 2, X = 1, Y = 7} \\quad (\\mathbf{WXY = 217})$$\n\n"
                "よって、解答は **$\\mathbf{WXY = 217}$** である。"
            )
        }
    ]
}

# Write JSON
out_json = Path("work/2022-2-math-c1/explanations.json")
out_json.parent.mkdir(parents=True, exist_ok=True)
out_json.write_text(json.dumps(explanations, ensure_ascii=False, indent=2), encoding="utf-8")

# Write Markdown document
md_content = r"""# 2022年度 第2回（2022-2）EJU 日本留学試験 数学コース1 全問詳細解説

- **試験科目**：数学（コース1 / Course 1）
- **対象試験**：2022年度第2回（令和4年11月実施）
- **形式コード**：`MATHEMATICS_COURSE_1_JA`
- **問題構成**：大問 I（問1, 問2）、大問 II（問1, 問2）、大問 III（前半, 後半）、大問 IV（前半, 後半）
- **解答形式**：マーク式数字空欄（A～Y等）

---

## 数学コース1 公式正解一覧表

| 大問 | 設問 | 空欄記号 | 正解 | 備考 |
| :--- | :--- | :--- | :--- | :--- |
| **第I問** | 問1 (1) | A | **2** | 軸からの距離 $|\alpha - p| = 2$ |
| | | BC | **41** | 等式 $4a + q = 1$ |
| | | DE | **93** | 等式 $9a + q = 3$ |
| | | FG | **25** | $a = 2/5$ |
| | | HI | **35** | $q = -3/5$ |
| | 問1 (2) | JK | **45** | $b = -4/5$ |
| | | LM | **15** | $c = -1/5$ |
| | 問2 (1) | NO | **49** | 2回目終了していない確率 $4/9$ |
| | 問2 (2) | PQ | **59** | 2回目で終了する確率 $5/9$ |
| | 問2 (3) | R | **2** | 3回目終了していない確率 $\frac{11}{54}$ |
| | 問2 (4) | S | **7** | 3回以下で終了する確率 $\frac{43}{54}$ |
| | 問2 (5) | T | **3** | 3回目で終了する確率 $\frac{13}{54}$ |
| **第II問** | 問1 | A | **2** | 不等式 $x < y < 2x$ |
| | | BC | **32** | 方程式 $3x + 2y = 70$ |
| | | DE | **57** | 不等式 $5x < 70 < 7x$ |
| | | FGHI | **1014** | 範囲 $10 < x < 14$ |
| | | J | **2** | $x$ は 2 の倍数 |
| | | KL | **12** | 青カード $x = 12$ 枚 |
| | | MN | **17** | 赤カード $y = 17$ 枚 |
| | 問2 | O | **1** | 下限 $a > 1$ |
| | | PQ | **73** | 上限 $a < 7/3$ |
| | | RST | **237** | $\alpha - \beta = 2\sqrt{-3a^2 + 10a - 7}$ |
| | | UV | **43** | 根号内最大値 $4/3$ |
| | | W | **1** | 整数条件 $-3a^2 + 10a - 7 = 1$ |
| | | XY | **43** | $a = 4/3$ |
| | | Z | **2** | $a = 2$ |
| **第III問** | (1) | AB | **15** | $a = 15q + r$ |
| | | C | **0** | $0 \le r$ |
| | | DE | **14** | $r \le 14$ |
| | | F | **3** | 選択肢 $\textcircled{3}$ ($\{1,2,4,7,8,11,13,14\}$) |
| | | G | **8** | 個数 8 個 |
| | (2) | HI | **92** | 50番目の整数 $90 + 2 = 92$ |
| | (3) | JK | **24** | 45以下の個数 $3 \times 8 = 24$ |
| | | LM | **27** | 50以下の個数 $24 + 3 = 27$ |
| | (4) | NO | **34** | 整数 $a = 34$ |
| | | PQ | **43** | 整数 $b = 43$ |
| **第IV問** | (1) | AB | **34** | $PB = \frac{3}{4} AB$ |
| | | CD | **74** | $PD = \frac{7}{4} AB$ |
| | | EF | **13** | $AB : BC = \sqrt{1} : \sqrt{3}$ |
| | | GH | **32** | $PB : MC = \sqrt{3} : 2$ |
| | | IJ | **32** | $BT : CT = \sqrt{3} : 2$ |
| | | KL | **34** | $\triangle PBT / \triangle MCT = 3/4$ |
| | | MN | **34** | $\triangle MBT / \triangle DCT = 3/4$ |
| | | OPQ | **916** | $\triangle PBT / \triangle DCT = 9/16$ |
| | (2) | RS | **32** | $\tan\theta = \frac{\sqrt{3}}{2}$ |
| | | TUV | **277** | $\cos\theta = \frac{2\sqrt{7}}{7}$ |
| | | WXY | **217** | $\cos\angle DCT = \frac{\sqrt{21}}{7}$ |

---

## 逐問詳細推導与解説

"""

for s in explanations["sections"]:
    md_content += "\n---\n\n## " + s["sectionTitle"] + "\n\n"
    points_str = ", ".join(s["points"])
    md_content += f"**【考査考点】**：{points_str}\n\n"
    md_content += s["detailedSolution"] + "\n"

out_md = Path("docs/explanations/2022-2-math-c1-solutions.md")
out_md.parent.mkdir(parents=True, exist_ok=True)
out_md.write_text(md_content, encoding="utf-8")

print(f"Generated {out_md} and {out_json} successfully with {len(explanations['sections'])} sections.")

