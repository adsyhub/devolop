#!/usr/bin/env python3
"""Generate comprehensive pedagogical explanations for 2014-1 EJU Math Course 1 (8 items)."""

import json
from pathlib import Path

math_c1_questions = [
    {
        "q_num": "I_1",
        "localKey": "math-q-I_1",
        "answer_ref": "I:1",
        "answer": {
            "AB": "-6",
            "CD": "23",
            "EFG": "523",
            "HI": "-1",
            "J": "6",
            "K": "6"
        },
        "title": "数学 コース1 第I問 [1]：2次関数の軸・最大値条件と連立方程式",
        "points": [
            "2次関数の頂点の $x$ 座標（軸の方程式 $x = -\\frac{b}{2a}$）",
            "通る点の座標の代入による $a, b$ の関係式の立式",
            "最大値をもつ条件（上に凸 $a<0$）に基づく解の選定"
        ],
        "solution": (
            "**【題目大意】**\n"
            "2次関数 $y = ax^2 + bx + \\frac{3}{a}$ が次の2つの条件を満たすとき、$a, b$ の値と最大値を求める。\n"
            "(i) $x = 3$ のとき、$y$ は最大値をとる。\n"
            "(ii) $x = 1$ のとき、$y$ の値は $2$ である。\n\n"
            "**【公式正解】**\n"
            "$\\text{AB} = -6$ （$b = -6a$）\n"
            "$\\text{CD} = 23$ （$2 = a + b + \\frac{3}{a}$）\n"
            "$\\text{EFG} = 523$ （$5a^2 + 2a - 3 = 0$）\n"
            "$\\text{HI} = -1$ （$a = -1$）\n"
            "$\\text{J} = 6$ （$b = 6$）\n"
            "$\\text{K} = 6$ （最大値は $6$）\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "**(1) 条件 (i), (ii) による連立関係式**\n"
            "- 条件 (i) より、放物線の軸は $x = 3$ である。\n"
            "  平方完成すると $y = a\\left(x + \\frac{b}{2a}\\right)^2 + \\dots$ より、軸は $x = -\\frac{b}{2a}$ であるから：\n"
            "  $$-\\frac{b}{2a} = 3 \\implies b = -6a \\quad (\\text{AB} = -6)$$\n"
            "- 条件 (ii) より、$x = 1$ のとき $y = 2$ であるから：\n"
            "  $$2 = a(1)^2 + b(1) + \\frac{3}{a} \\implies 2 = a + b + \\frac{3}{a}$$\n"
            "  与式 $\\text{C} = a + b + \\frac{\\text{D}}{a}$ と比較して、$\\text{CD} = 23$ である。\n\n"
            "**(2) $a$ に関する方程式の導出と解法**\n"
            "$b = -6a$ を代入すると：\n"
            "$$2 = a - 6a + \\frac{3}{a} = -5a + \\frac{3}{a}$$\n"
            "両辺に $a$ を掛けて移項すると：\n"
            "$$2a = -5a^2 + 3 \\iff 5a^2 + 2a - 3 = 0$$\n"
            "したがって、$\\text{E}a^2 + \\text{F}a - \\text{G} = 0$ より、$\\text{EFG} = 523$ である。\n\n"
            "因数分解すると：\n"
            "$$(5a - 3)(a + 1) = 0 \\implies a = \\frac{3}{5}, \\quad a = -1$$\n"
            "条件 (i) で「$y$ は最大値をとる」とあるため、放物線は上に凸（$a < 0$）でなければならない。\n"
            "したがって：\n"
            "$$a = -1 \\quad (\\text{HI} = -1)$$\n"
            "このとき：\n"
            "$$b = -6(-1) = 6 \\quad (\\text{J} = 6)$$\n\n"
            "**(3) 最大値の計算**\n"
            "関数の式は：\n"
            "$$y = -x^2 + 6x - 3 = -(x - 3)^2 + 9 - 3 = -(x - 3)^2 + 6$$\n"
            "したがって、$x = 3$ のときの最大値は **6** である（$\\text{K} = 6$）。\n\n"
            "**【考査考点】**\n"
            "- 2次関数の軸と頂点（最大値条件における2次の係数の負値判定 $a<0$）。\n"
            "- 連立代数方程式の立式と因数分解による求解。"
        )
    },
    {
        "q_num": "I_2",
        "localKey": "math-q-I_2",
        "answer_ref": "I:2",
        "answer": {
            "LMN": "223",
            "OPQR": "3141",
            "STU": "365"
        },
        "title": "数学 コース1 第I問 [2]：多項式の因数分解と無理数の有理化代入計算",
        "points": [
            "2つの整式 $P, Q$ を用いた多項式の因数分解（平方の差と共通因数のくくり出し）",
            "$x$ の多項式への展開と因数分解",
            "分母の有理化による無理数代入と対称式の簡潔な評価"
        ],
        "solution": (
            "**【題目大意】**\n"
            "$P = 2x^2 - x + 2, Q = x^2 - 2x + 1$ に対し、$E = P^2 - 4Q^2 - 3P + 6Q$ を考える。\n"
            "(1) $E$ を因数分解する。\n"
            "(2) $E$ を $x$ の式で表す。\n"
            "(3) $x = -\\frac{1-\\sqrt{5}}{3-\\sqrt{5}}$ のときの $E$ の値を求める。\n\n"
            "**【公式正解】**\n"
            "$\\text{LMN} = 223$ （$E = (P - 2Q)(P + 2Q - 3)$）\n"
            "$\\text{OPQR} = 3141$ （$E = 3x(x - 1)(4x - 1)$）\n"
            "$\\text{STU} = 365$ （$E = 3 + 6\\sqrt{5}$）\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "**(1) $E$ の因数分解**\n"
            "式をグループ分けして整理する：\n"
            "$$E = (P^2 - 4Q^2) - 3(P - 2Q)$$\n"
            "前半に平方の差の公式を適用すると：\n"
            "$$E = (P - 2Q)(P + 2Q) - 3(P - 2Q) = (P - 2Q)(P + 2Q - 3)$$\n"
            "与式 $(P - \\text{L}Q)(P + \\text{M}Q - \\text{N})$ と比較して：\n"
            "$$\\text{L} = 2, \\quad \\text{M} = 2, \\quad \\text{N} = 3 \\implies \\text{LMN} = 223$$\n\n"
            "**(2) $x$ の式への代入展開**\n"
            "- $P - 2Q$ を計算する：\n"
            "  $$P - 2Q = (2x^2 - x + 2) - 2(x^2 - 2x + 1) = 2x^2 - x + 2 - 2x^2 + 4x - 2 = 3x$$\n"
            "- $P + 2Q - 3$ を計算する：\n"
            "  $$P + 2Q - 3 = (2x^2 - x + 2) + 2(x^2 - 2x + 1) - 3 = 4x^2 - 5x + 1$$\n"
            "  たすき掛けにより因数分解すると：\n"
            "  $$4x^2 - 5x + 1 = (x - 1)(4x - 1)$$\n"
            "したがって：\n"
            "$$E = 3x(x - 1)(4x - 1)$$\n"
            "与式 $\\text{O}x(x - \\text{P})(\\text{Q}x - \\text{R})$ と比較して：\n"
            "$$\\text{O} = 3, \\quad \\text{P} = 1, \\quad \\text{Q} = 4, \\quad \\text{R} = 1 \\implies \\text{OPQR} = 3141$$\n\n"
            "**(3) 無理数の代入計算**\n"
            "与えられた $x$ の分母を有理化する：\n"
            "$$x = -\\frac{1 - \\sqrt{5}}{3 - \\sqrt{5}} = \\frac{\\sqrt{5} - 1}{3 - \\sqrt{5}} = \\frac{(\\sqrt{5} - 1)(3 + \\sqrt{5})}{(3 - \\sqrt{5})(3 + \\sqrt{5})} = \\frac{3\\sqrt{5} + 5 - 3 - \\sqrt{5}}{9 - 5} = \\frac{2 + 2\\sqrt{5}}{4} = \\frac{1 + \\sqrt{5}}{2}$$\n"
            "各因数を計算する：\n"
            "- $x - 1 = \\frac{1 + \\sqrt{5}}{2} - 1 = \\frac{\\sqrt{5} - 1}{2}$\n"
            "- $3x(x - 1) = 3 \\left(\\frac{\\sqrt{5} + 1}{2}\\right) \\left(\\frac{\\sqrt{5} - 1}{2}\\right) = 3 \\cdot \\frac{5 - 1}{4} = 3 \\times 1 = 3$\n"
            "- $4x - 1 = 4 \\left(\\frac{1 + \\sqrt{5}}{2}\\right) - 1 = 2(1 + \\sqrt{5}) - 1 = 1 + 2\\sqrt{5}$\n"
            "したがって：\n"
            "$$E = [3x(x - 1)] (4x - 1) = 3(1 + 2\\sqrt{5}) = 3 + 6\\sqrt{5}$$\n"
            "与式 $\\text{S} + \\text{T}\\sqrt{\\text{U}}$ と比較して、$\\text{STU} = 365$ である。\n\n"
            "**【考査考点】**\n"
            "- 置き換えを利用した代数式の効率的な因数分解。\n"
            "- 分母の有理化と平方根を含む式の工夫した代入計算。"
        )
    },
    {
        "q_num": "II_1",
        "localKey": "math-q-II_1",
        "answer_ref": "II:1",
        "answer": {
            "AB": "20",
            "CD": "12",
            "EFGHI": "14334",
            "JK": "34",
            "L": "3",
            "M": "6"
        },
        "title": "数学 コース1 第II問 [1]：反復試行の確率・余事象と高次不等式の整数解",
        "points": [
            "球の復元抽出における反復試行の確率",
            "余事象（少なくとも1回白球、少なくとも2回白球）の確率計算",
            "高次不等式 $p < q$ の因数分解と条件を満たす整数 $n$ の最大値の決定"
        ],
        "solution": (
            "**【題目大意】**\n"
            "赤球 $n$ 個、白球 $(20-n)$ 個（計20個）が入った箱から1球取り出して戻す試行を繰り返す。\n"
            "(1) 赤球が出る確率 $x$ を表す。\n"
            "(2) 2回試行で少なくとも1回白球が出る確率 $p$ を表す。\n"
            "(3) 4回試行で少なくとも2回白球が出る確率 $q$ を表す。\n"
            "(4) $p < q$ となる $n$ の最大値を求める。\n\n"
            "**【公式正解】**\n"
            "$\\text{AB} = 20$ （$x = \\frac{n}{20}$）\n"
            "$\\text{CD} = 12$ （$p = 1 - x^2$）\n"
            "$\\text{EFGHI} = 14334$ （$q = 1 - 4x^3 + 3x^4$）\n"
            "$\\text{JK} = 34$ （$3x^2 - 4x + 1 > 0$）\n"
            "$\\text{L} = 3$ （$x < \\frac{1}{3}$）\n"
            "$\\text{M} = 6$\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "**(1) 赤球の確率 $x$**\n"
            "全球数は $n + (20 - n) = 20$ 個であるから：\n"
            "$$x = \\frac{n}{20} \\quad (\\text{AB} = 20)$$\n\n"
            "**(2) 2回試行における確率 $p$**\n"
            "「少なくとも1回は白球が出る」余事象は「2回とも赤球が出る」ことである：\n"
            "$$p = 1 - x^2$$\n"
            "与式 $p = \\text{C} - x^\\text{D}$ より、$\\text{CD} = 12$ である。\n\n"
            "**(3) 4回試行における確率 $q$**\n"
            "「少なくとも2回は白球が出る」余事象は、「白球が0回（赤4回）」または「白球が1回（赤3回、白1回）」である：\n"
            "- 赤4回の確率：$x^4$\n"
            "- 赤3回・白1回の確率：$\\binom{4}{3} x^3 (1 - x) = 4x^3(1 - x) = 4x^3 - 4x^4$\n"
            "余事象の確率の和は：\n"
            "$$x^4 + (4x^3 - 4x^4) = 4x^3 - 3x^4$$\n"
            "したがって：\n"
            "$$q = 1 - (4x^3 - 3x^4) = 1 - 4x^3 + 3x^4$$\n"
            "与式 $q = \\text{E} - \\text{F}x^\\text{G} + \\text{H}x^\\text{I}$ より、$\\text{EFGHI} = 14334$ である。\n\n"
            "**(4) $p < q$ の不等式と $n$ の最大値**\n"
            "$$p < q \\iff 1 - x^2 < 1 - 4x^3 + 3x^4 \\iff 3x^4 - 4x^3 + x^2 > 0$$\n"
            "$0 < n < 20$ より $0 < x < 1$ であるから、両辺を $x^2 > 0$ で割ると：\n"
            "$$3x^2 - 4x + 1 > 0$$\n"
            "与式 $\\text{J}x^2 - \\text{K}x + 1 > 0$ より、$\\text{JK} = 34$ である。\n\n"
            "因数分解すると：\n"
            "$$(3x - 1)(x - 1) > 0$$\n"
            "$x < 1$ であるから、不等式の解は：\n"
            "$$x < \\frac{1}{3} \\quad (\\text{L} = 3)$$\n"
            "$x = \\frac{n}{20}$ を代入すると：\n"
            "$$\\frac{n}{20} < \\frac{1}{3} \\iff n < \\frac{20}{3} = 6.666\\dots$$\n"
            "$n$ は自然数であるから、満たす最大の $n$ は **6** である（$\\text{M} = 6$）。\n\n"
            "**【考査考点】**\n"
            "- 反復試行の確率公式と余事象の考え方。\n"
            "- 確率変数の多項式不等式の因数分解と整数条件の処理。"
        )
    },
    {
        "q_num": "II_2",
        "localKey": "math-q-II_2",
        "answer_ref": "II:2",
        "answer": {
            "NOP": "177",
            "QR": "17",
            "ST": "28",
            "UV": "27",
            "WX": "72",
            "YZ": "24"
        },
        "title": "数学 コース1 第II問 [2]：不定方程式と素数条件による整数の組の決定",
        "points": [
            "分数方程式の両辺の分母払拭と積の形 $(x - a)(py - b) = c$ への式変形",
            "素数 7 の約数分解（1 と 7）による $x$ の値の決定",
            "素数 $p$ の性質に基づく解 $(p, x, y)$ の全列挙"
        ],
        "solution": (
            "**【題目大意】**\n"
            "$p$ を素数、$x, y$ を正の整数とするとき、等式 $\\frac{p}{x} + \\frac{7}{y} = p$ を満たす組 $(p, x, y)$ をすべて求める。\n\n"
            "**【公式正解】**\n"
            "$\\text{NOP} = 177$ （$(x - 1)(py - 7) = 7$）\n"
            "$\\text{QR} = 17$ （$x - 1 = 1$ または $7$）\n"
            "$\\text{ST} = 28$ （$x = 2$ または $8$）\n"
            "$\\text{UV} = 27$ （$p = 2, y = 7$）\n"
            "$\\text{WX} = 72$ （$p = 7, y = 2$）\n"
            "$\\text{YZ} = 24$ （$p = 2, y = 4$）\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "**(1) 方程式の変形**\n"
            "両辺に $xy$ を掛けて分母を払う：\n"
            "$$py + 7x = pxy \\iff pxy - py - 7x = 0$$\n"
            "因数分解の形に変形する：\n"
            "$$py(x - 1) - 7(x - 1) = 7 \\iff (x - 1)(py - 7) = 7$$\n"
            "与式 $(x - \\text{N})(py - \\text{O}) = \\text{P}$ と比較して：\n"
            "$$\\text{N} = 1, \\quad \\text{O} = 7, \\quad \\text{P} = 7 \\implies \\text{NOP} = 177$$\n\n"
            "**(2) $x$ の値の候補**\n"
            "$x, y$ は正の整数であり、$7$ は素数である。\n"
            "もし $x = 1$ ならば左辺が $0$ となり不適であるから、$x - 1 \\ge 1$ である。\n"
            "積が $7$（正の素数）であるから、因数 $x - 1$ は $7$ の正の約数に限られる：\n"
            "$$x - 1 = 1 \\quad \\text{または} \\quad x - 1 = 7 \\quad (\\text{QR} = 17)$$\n"
            "したがって：\n"
            "$$x = 2 \\quad \\text{または} \\quad x = 8 \\quad (\\text{ST} = 28)$$\n\n"
            "**(3) $x = 2$ のとき**\n"
            "$$py - 7 = \\frac{7}{x - 1} = 7 \\implies py = 14 = 2 \\times 7$$\n"
            "$p$ は素数、$y$ は正の整数であるから、素数 $p$ は $14$ の素因数である $2$ または $7$ である：\n"
            "1. $p = 2$ のとき：$y = \\frac{14}{2} = 7$（$\\text{U} = 2, \\text{V} = 7 \\implies \\text{UV} = 27$）\n"
            "2. $p = 7$ のとき：$y = \\frac{14}{7} = 2$（$\\text{W} = 7, \\text{X} = 2 \\implies \\text{WX} = 72$）\n\n"
            "**(4) $x = 8$ のとき**\n"
            "$$py - 7 = \\frac{7}{x - 1} = 1 \\implies py = 8 = 2^3$$\n"
            "$p$ は素数であるから、$p$ は $8$ の唯一の素因数である $2$ に限られる：\n"
            "$$p = 2 \\implies y = \\frac{8}{2} = 4$$\n"
            "したがって、$\\text{Y} = 2, \\text{Z} = 4 \\implies \\text{YZ} = 24$ である。\n\n"
            "**【考査考点】**\n"
            "- 不定方程式の因数分解による標準化 $(x-a)(y-b)=c$。\n"
            "- 素数の定義と約数の性質を用いた整数の絞り込み。"
        )
    },
    {
        "q_num": "III_1",
        "localKey": "math-q-III_1",
        "answer_ref": "III:1",
        "answer": {
            "A": "1",
            "BC": "-2"
        },
        "title": "数学 コース1 第III問 (1)：2点を通る放物線の係数決定",
        "points": [
            "2次関数 $y = ax^2 + bx + c$ への2点 $(-1, -1), (2, 2)$ の代入",
            "係数 $b, c$ の $a$ による線形表現の導出"
        ],
        "solution": (
            "**【題目大意】**\n"
            "2次関数 $y = ax^2 + bx + c$ $\\textcircled{1}$ のグラフが2点 $(-1, -1)$ と $(2, 2)$ を通るとき、$b, c$ を $a$ の式で表す。\n\n"
            "**【公式正解】**\n"
            "$\\text{A} = 1$ （$b = 1 - a$）\n"
            "$\\text{BC} = -2$ （$c = -2a$）\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "グラフが点 $(-1, -1)$ を通ることから：\n"
            "$$a(-1)^2 + b(-1) + c = -1 \\iff a - b + c = -1 \\quad \\dots (1)$$\n"
            "グラフが点 $(2, 2)$ を通ることから：\n"
            "$$a(2)^2 + b(2) + c = 2 \\iff 4a + 2b + c = 2 \\quad \\dots (2)$$\n\n"
            "式 (2) から式 (1) を引くと：\n"
            "$$(4a + 2b + c) - (a - b + c) = 2 - (-1)$$\n"
            "$$3a + 3b = 3 \\iff a + b = 1 \\iff b = 1 - a$$\n"
            "したがって、$b = \\text{A} - a$ より、$\\text{A} = 1$ である。\n\n"
            "これを式 (1) に代入して $c$ を求める：\n"
            "$$c = -1 - a + b = -1 - a + (1 - a) = -2a$$\n"
            "したがって、$c = \\text{BC} a$ より、$\\text{BC} = -2$ である。\n\n"
            "**【考査考点】**\n"
            "- 2次関数の決定（連立方程式の加減法による未知係数の消去）。"
        )
    },
    {
        "q_num": "III_2",
        "localKey": "math-q-III_2",
        "answer_ref": "III:2",
        "answer": {
            "D": "0",
            "EF": "12",
            "GHI": "-18",
            "J": "0"
        },
        "title": "数学 コース1 第III問 (2)(3)：解の配置問題と2次式の値域評価",
        "points": [
            "開区間 $0 < x \\le 1$ に $x$ 切片をもつための境界値条件（$f(0)f(1) \\le 0$）",
            "パラメータ $a$ の存在範囲 $0 < a \\le 1/2$ の決定",
            "$a + bc$ の平方完成による最小値・最大値の導出"
        ],
        "solution": (
            "**【題目大意】**\n"
            "(2) 放物線と $x$ 軸との交点の1つが $0 < x \\le 1$ の範囲にあるときの $a$ の範囲を求める。\n"
            "(3) そのときの $a + bc$ のとり得る値の範囲を求める。\n\n"
            "**【公式正解】**\n"
            "$\\text{D} = 0, \\text{EF} = 12$ （$0 < a \\le \\frac{1}{2}$）\n"
            "$\\text{GHI} = -18$ （最小値は $-\\frac{1}{8}$）\n"
            "$\\text{J} = 0$ （最大値は $0$）\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "**(1) $a$ の範囲の決定**\n"
            "$f(x) = ax^2 + (1 - a)x - 2a$ とおく。\n"
            "端点での値を調べると：\n"
            "- $f(0) = -2a$\n"
            "- $f(1) = a(1)^2 + (1 - a)(1) - 2a = a + 1 - a - 2a = 1 - 2a$\n\n"
            "放物線が 2点 $(-1, -1)$ と $(2, 2)$ を通ることから、$a > 0$（下に凸）のとき：\n"
            "- $f(0) = -2a < 0$ である。\n"
            "- $0 < x \\le 1$ の区間に解をもつためには、$f(1) \\ge 0$ でなければならない：\n"
            "  $$1 - 2a \\ge 0 \\iff 2a \\le 1 \\iff a \\le \\frac{1}{2}$$\n"
            "したがって、$a$ の範囲は：\n"
            "$$0 < a \\le \\frac{1}{2}$$\n"
            "与式 $\\text{D} < a \\le \\frac{\\text{E}}{\\text{F}}$ と比較して、$\\text{D} = 0, \\text{EF} = 12$ である。\n\n"
            "**(2) $a + bc$ の範囲**\n"
            "$b = 1 - a, c = -2a$ を代入すると：\n"
            "$$a + bc = a + (1 - a)(-2a) = a - 2a + 2a^2 = 2a^2 - a$$\n"
            "$g(a) = 2a^2 - a$ とおき、$0 < a \\le \\frac{1}{2}$ における値域を求める。\n"
            "平方完成すると：\n"
            "$$g(a) = 2\\left(a - \\frac{1}{4}\\right)^2 - \\frac{1}{8}$$\n"
            "- 頂点は $a = \\frac{1}{4} \\in \\left(0, \\frac{1}{2}\\right]$ にあり、最小値は：\n"
            "  $$g\\left(\\frac{1}{4}\\right) = -\\frac{1}{8} \\quad (\\text{GHI} = -18)$$\n"
            "- 端点での値：\n"
            "  - $a = \\frac{1}{2}$ のとき：$g\\left(\\frac{1}{2}\\right) = 2\\left(\\frac{1}{4}\\right) - \\frac{1}{2} = 0$\n"
            "  - $a \\to 0^+$ のとき：$g(a) \\to 0$\n"
            "したがって、最大値は $0$（$\\text{J} = 0$）である。\n\n"
            "よって、求める値の範囲は：\n"
            "$$-\\frac{1}{8} \\le a + bc \\le 0$$\n"
            "正解は $\\text{GHI} = -18, \\text{J} = 0$ である。\n\n"
            "**【考査考点】**\n"
            "- 2次方程式の実数解の存在範囲（中間値の定理・解の配置）。\n"
            "- 2次関数の定義域付き最大値・最小値問題。"
        )
    },
    {
        "q_num": "IV_1",
        "localKey": "math-q-IV_1",
        "answer_ref": "IV:1",
        "answer": {
            "AB": "14",
            "CDE": "154",
            "FGHIJK": "161515"
        },
        "title": "数学 コース1 第IV問 (1)：三角形の余弦定理・正弦定理と外接円の半径",
        "points": [
            "3辺の長さ（7, 8, 6）から余弦定理による $\\cos\\angle BAC$ の計算",
            "相互関係 $\\sin^2\\theta + \\cos^2\\theta = 1$ による $\\sin\\angle BAC$ の導出",
            "正弦定理 $2r = \\frac{BC}{\\sin A}$ による外接円の半径 $r$ の計算"
        ],
        "solution": (
            "**【題目大意】**\n"
            "$AB = 7, BC = 8, CA = 6$ の三角形 $ABC$ において、$\\cos\\angle BAC, \\sin\\angle BAC$ および外接円の半径 $r$ を求める。\n\n"
            "**【公式正解】**\n"
            "$\\text{AB} = 14$ （$\\cos\\angle BAC = \\frac{1}{4}$）\n"
            "$\\text{CDE} = 154$ （$\\sin\\angle BAC = \\frac{\\sqrt{15}}{4}$）\n"
            "$\\text{FGHIJK} = 161515$ （$r = \\frac{16\\sqrt{15}}{15}$）\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "**(1) $\\cos\\angle BAC$ の計算**\n"
            "$\\triangle ABC$ において余弦定理を適用する：\n"
            "$$\\cos\\angle BAC = \\frac{AB^2 + AC^2 - BC^2}{2 \\cdot AB \\cdot AC} = \\frac{7^2 + 6^2 - 8^2}{2 \\times 7 \\times 6}$$\n"
            "$$= \\frac{49 + 36 - 64}{84} = \\frac{21}{84} = \\frac{1}{4}$$\n"
            "したがって、$\\cos\\angle BAC = \\frac{\\text{A}}{\\text{B}}$ より、$\\text{AB} = 14$ である。\n\n"
            "**(2) $\\sin\\angle BAC$ の計算**\n"
            "$0^\\circ < \\angle BAC < 180^\\circ$ より $\\sin\\angle BAC > 0$ であるから：\n"
            "$$\\sin\\angle BAC = \\sqrt{1 - \\cos^2\\angle BAC} = \\sqrt{1 - \\left(\\frac{1}{4}\\right)^2} = \\sqrt{\\frac{15}{16}} = \\frac{\\sqrt{15}}{4}$$\n"
            "したがって、$\\sin\\angle BAC = \\frac{\\sqrt{\\text{CD}}}{\\text{E}}$ より、$\\text{CDE} = 154$ である。\n\n"
            "**(3) 外接円の半径 $r$**\n"
            "正弦定理より：\n"
            "$$\\frac{BC}{\\sin\\angle BAC} = 2r \\implies 2r = \\frac{8}{\\frac{\\sqrt{15}}{4}} = \\frac{32}{\\sqrt{15}}$$\n"
            "$$r = \\frac{16}{\\sqrt{15}} = \\frac{16\\sqrt{15}}{15}$$\n"
            "したがって、$r = \\frac{\\text{FG}\\sqrt{\\text{HI}}}{\\text{JK}}$ より、$\\text{FGHIJK} = 161515$ である。\n\n"
            "**【考査考点】**\n"
            "- 余弦定理による三角形の内角の余弦の算出。\n"
            "- 正弦定理と外接円の半径の幾何学的関係。"
        )
    },
    {
        "q_num": "IV_2",
        "localKey": "math-q-IV_2",
        "answer_ref": "IV:2",
        "answer": {
            "LM": "16",
            "NOPQR": "16155"
        },
        "title": "数学 コース1 第IV問 (2)：外接円の接線の交点と線分長の幾何学的極値（最短距離）",
        "points": [
            "円の接線と中心を結ぶ直角三角形の幾何学的性質（$\\angle OBD = 90^\\circ$）",
            "中心角と円周角の関係（$\\angle BOD = \\angle BAC$）による接線長 $BD$ の計算",
            "外部の点から円周上の点への最短距離 $DP_{\\min} = OD - r$ の導出"
        ],
        "solution": (
            "**【題目大意】**\n"
            "外接円上の点 B, C における2本の接線の交点を D とするとき、$BD$ の長さ、および円周上の点 P に対する線分 DP の最短距離を求める。\n\n"
            "**【公式正解】**\n"
            "$\\text{LM} = 16$ （$BD = 16$）\n"
            "$\\text{NOPQR} = 16155$ （最短の長さは $\\frac{16\\sqrt{15}}{5}$）\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "**(1) 接線長 $BD$ の計算**\n"
            "点 D は B, C における接線の交点であるから、$DB = DC$ であり、四角形 $OBDC$ において $\\angle OBD = \\angle OCD = 90^\\circ$ である。\n"
            "円周角の定理より、中心角 $\\angle BOC = 2\\angle BAC$ である。\n"
            "線分 $OD$ は $\\angle BOC$ を二等分するため：\n"
            "$$\\angle BOD = \\angle BAC$$\n"
            "直角三角形 $OBD$ において：\n"
            "$$\\cos\\angle BOD = \\frac{OB}{OD} = \\cos\\angle BAC = \\frac{1}{4}$$\n"
            "これより、$OD = 4 OB = 4r$ である。\n"
            "三平方の定理より：\n"
            "$$BD = \\sqrt{OD^2 - OB^2} = \\sqrt{(4r)^2 - r^2} = \\sqrt{15} r$$\n"
            "前問で求めた $r = \\frac{16}{\\sqrt{15}}$ を代入すると：\n"
            "$$BD = \\sqrt{15} \\times \\frac{16}{\\sqrt{15}} = 16 \\quad (\\text{LM} = 16)$$\n\n"
            "**(2) 線分 DP の最短距離**\n"
            "点 D は円の外部にあり、P は円周上の点である。\n"
            "D と中心 O を結ぶ直線が円周と交わる2点のうち、D に近い方の点 P をとるとき、線分 DP は最短となる：\n"
            "$$DP_{\\min} = OD - r = 4r - r = 3r$$\n"
            "$r = \\frac{16\\sqrt{15}}{15}$ を代入すると：\n"
            "$$DP_{\\min} = 3 \\times \\frac{16\\sqrt{15}}{15} = \\frac{16\\sqrt{15}}{5}$$\n"
            "与式 $\\frac{\\text{NO}\\sqrt{\\text{PQ}}}{\\text{R}}$ と比較して：\n"
            "$$\\text{NO} = 16, \\quad \\text{PQ} = 15, \\quad \\text{R} = 5 \\implies \\text{NOPQR} = 16155$$\n\n"
            "**【考査考点】**\n"
            "- 円の接線の性質（接線と半径の垂直性、対称性）。\n"
            "- 中心角と円周角の関係を利用した三角比の直角三角形への適用。\n"
            "- 円外の点と円周上の点との最短距離の幾何学的決定（$d - r$）。"
        )
    }
]

def main():
    work_dir = Path("work/2014-1-math-c1")
    work_dir.mkdir(parents=True, exist_ok=True)
    docs_dir = Path("docs/explanations")
    docs_dir.mkdir(parents=True, exist_ok=True)

    json_path = work_dir / "explanations.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(math_c1_questions, f, ensure_ascii=False, indent=2)
    print(f"Generated {json_path} ({len(math_c1_questions)} questions)")

    md_path = docs_dir / "2014-1-math-c1-solutions.md"
    lines = [
        "# 2014-1 EJU 数学 コース1 詳解・完全解説\n",
        "> 本ドキュメントは 2014年度第1回 EJU（日本留学試験）数学コース1に対する公式正解準拠の完全詳解である。\n",
        "---\n"
    ]

    for item in math_c1_questions:
        lines.append(f"## {item['title']}\n")
        ans_str = ", ".join(f"{k} = {v}" for k, v in item["answer"].items())
        lines.append(f"**問題コード**: `{item['localKey']}` | **配点参照**: `{item['answer_ref']}` | **正解**: `{ans_str}`\n")
        lines.append("### 出題のポイント")
        for pt in item["points"]:
            lines.append(f"- {pt}")
        lines.append("\n### 詳細解説")
        lines.append(item["solution"])
        lines.append("\n---\n")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Generated {md_path}")

if __name__ == "__main__":
    main()

