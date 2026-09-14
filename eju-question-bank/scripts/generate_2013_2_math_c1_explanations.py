#!/usr/bin/env python3
"""Generate comprehensive pedagogical explanations for 2013-2 EJU Math Course 1 (8 items)."""

import json
from pathlib import Path

math_c1_questions = [
    {
        "q_num": "I_1",
        "localKey": "math-q-I_1",
        "answer_ref": "I:1",
        "answer": {
            "A": "4",
            "BC": "-2",
            "DEF": "-27",
            "G": "4"
        },
        "title": "数学 コース1 第I問 [1]：2次関数の最大値・軸・交点と平行移動",
        "points": [
            "平方完成による最大値条件と未知係数 $a>0$ の決定",
            "対称軸の方程式 $x = -a/2$ および $x$ 軸との交点座標（解の公式）",
            "グラフの平行移動と通過点条件による係数の逆算"
        ],
        "solution": (
            "**【題目大意】**\n"
            "2次関数 $y = -x^2 - ax + 3$ ① について考える。\n"
            "(1) $a > 0$ であって、関数 ① の最大値が 7 であるとき、$a$ の値、軸の方程式、および $x$ 軸との交点の $x$ 座標を求める。\n"
            "(2) 関数 ① のグラフを $x$ 軸方向に 2、$y$ 軸方向に -3 だけ平行移動した曲線が $(-3, -5)$ を通るとき、$a$ の値を求める。\n\n"
            "**【公式正解】**\n"
            "$\\text{A} = 4$\n"
            "$\\text{BC} = -2$\n"
            "$\\text{DEF} = -27$ （$x = -2 \\pm \\sqrt{7}$）\n"
            "$\\text{G} = 4$\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "**(1) 最大値と係数 $a$、軸、交点**\n"
            "2次関数 $y = -x^2 - ax + 3$ を平方完成する：\n"
            "$$y = -\\left(x^2 + ax\\right) + 3 = -\\left(x + \\frac{a}{2}\\right)^2 + \\frac{a^2}{4} + 3$$\n"
            "放物線は上に凸（$x^2$ の係数が $-1 < 0$）であるから、$x = -\\frac{a}{2}$ において最大値 $\\frac{a^2}{4} + 3$ をとる。\n"
            "最大値が 7 であるから：\n"
            "$$\\frac{a^2}{4} + 3 = 7 \\implies \\frac{a^2}{4} = 4 \\implies a^2 = 16$$\n"
            "問題文の条件 $a > 0$ より：\n"
            "$$a = 4 \\quad (\\text{A} = 4)$$\n"
            "このとき、軸の方程式は：\n"
            "$$x = -\\frac{a}{2} = -\\frac{4}{2} = -2 \\quad (\\text{BC} = -2)$$\n"
            "また、$x$ 軸との交点の $x$ 座標は、$y = 0$ とおいた方程式 $-x^2 - 4x + 3 = 0 \\iff x^2 + 4x - 3 = 0$ の解である。\n"
            "解の公式より：\n"
            "$$x = -2 \\pm \\sqrt{2^2 - 1(-3)} = -2 \\pm \\sqrt{4 + 3} = -2 \\pm \\sqrt{7}$$\n"
            "与式 $\\text{DE} \\pm \\sqrt{\\text{F}}$ と比較して：\n"
            "$$\\text{DE} = -2, \\quad \\text{F} = 7 \\implies \\text{DEF} = -27$$\n\n"
            "**(2) グラフの平行移動**\n"
            "$y = -x^2 - ax + 3$ のグラフを $x$ 軸方向に 2、$y$ 軸方向に -3 平行移動した曲線の方程式は：\n"
            "$$y - (-3) = -(x - 2)^2 - a(x - 2) + 3$$\n"
            "$$y + 3 = -(x - 2)^2 - a(x - 2) + 3 \\implies y = -(x - 2)^2 - a(x - 2)$$\n"
            "この曲線が点 $(-3, -5)$ を通るから、$x = -3, y = -5$ を代入する：\n"
            "$$-5 = -(-3 - 2)^2 - a(-3 - 2) = -(-5)^2 - a(-5) = -25 + 5a$$\n"
            "$$5a = 20 \\implies a = 4 \\quad (\\text{G} = 4)$$\n\n"
            "**【考査考点】**\n"
            "- 2次関数の平方完成、頂点と軸の決定。\n"
            "- 解の公式を用いた $x$ 切片の算出。\n"
            "- 座標平面における放物線の平行移動（$x \\to x-p, y \\to y-q$）。"
        )
    },
    {
        "q_num": "I_2",
        "localKey": "math-q-I_2",
        "answer_ref": "I:2",
        "answer": {
            "H": "1",
            "I": "0",
            "J": "0",
            "K": "2",
            "LMNOP": "22124",
            "QR": "04"
        },
        "title": "数学 コース1 第I問 [2]：同値変形と必要条件・十分条件の判定",
        "points": [
            "多項式等式の因数分解と条件 $p$ の代数的意味の把握",
            "必要条件・十分条件・必要十分条件の論理的判定",
            "平方完成による正値条件と必要十分条件となるパラメータ範囲の決定"
        ],
        "solution": (
            "**【題目大意】**\n"
            "実数 $x, y$ についての3つの条件を考える：\n"
            "$p$：$(x+y)^2 = a(x^2+y^2) + bxy$（$a, b$ は実数の定数）\n"
            "$q$：$x=0$ かつ $y=0$\n"
            "$r$：$x=0$ または $y=0$\n"
            "(1) $a=b=1$ のとき、$p$ は $q$ であるための何条件か（H）、また $r$ であるための何条件か（I）。\n"
            "(2) $a=b=2$ のとき、$p$ は $q$ であるための何条件か（J）、また $r$ であるための何条件か（K）。\n"
            "(3) $a=2$ のとき、$p$ を平方完成の形に変形し、$p$ が $q$ であるための必要十分条件となる $b$ の範囲を求める。\n"
            "選択肢：$\\textcircled{0}$ 必要十分条件、$\\textcircled{1}$ 必要条件であるが十分条件ではない、$\\textcircled{2}$ 十分条件であるが必要条件ではない、$\\textcircled{3}$ 必要条件でも十分条件でもない\n\n"
            "**【公式正解】**\n"
            "$\\text{H} = 1$\n"
            "$\\text{I} = 0$\n"
            "$\\text{J} = 0$\n"
            "$\\text{K} = 2$\n"
            "$\\text{LMNOP} = 22124$\n"
            "$\\text{QR} = 04$\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "**(1) $a=b=1$ の場合**\n"
            "$(x+y)^2 = (x^2+y^2) + xy \\iff x^2 + 2xy + y^2 = x^2 + y^2 + xy \\iff xy = 0$。\n"
            "したがって、条件 $p$ は「$xy = 0$」と同値であり、これは条件 $r$（$x=0$ または $y=0$）そのものである。\n"
            "- $p$ と $q$ の関係：$q \\implies p$（$x=y=0$ ならば $xy=0$）は真だが、$p \\implies q$（例えば $x=1, y=0$ ならば $xy=0$ だが $q$ は不成立）は偽である。\n"
            "  よって $p$ は $q$ であるための「必要条件であるが十分条件ではない」（$\\textcircled{1} \\implies \\text{H} = 1$）。\n"
            "- $p$ と $r$ の関係：$p \\iff r$ であるから、「必要十分条件である」（$\\textcircled{0} \\implies \\text{I} = 0$）。\n\n"
            "**(2) $a=b=2$ の場合**\n"
            "$(x+y)^2 = 2(x^2+y^2) + 2xy \\iff x^2 + 2xy + y^2 = 2x^2 + 2y^2 + 2xy \\iff x^2 + y^2 = 0$。\n"
            "$x, y$ は実数であるから、$x^2 + y^2 = 0 \\iff x = 0 \\text{ かつ } y = 0$。\n"
            "したがって、条件 $p$ は条件 $q$ と完全に同値である。\n"
            "- $p$ と $q$ の関係：$p \\iff q$ であるから、「必要十分条件である」（$\\textcircled{0} \\implies \\text{J} = 0$）。\n"
            "- $p$ と $r$ の関係：$p$（$x=y=0$）が成り立てば $r$（$x=0$ または $y=0$）は真であるが、$r \\implies p$ は偽である（反例：$x=1, y=0$）。\n"
            "  よって $p$ は $r$ であるための「十分条件であるが必要条件ではない」（$\\textcircled{2} \\implies \\text{K} = 2$）。\n\n"
            "**(3) $a=2$ のときの変形と条件**\n"
            "$(x+y)^2 = 2(x^2+y^2) + bxy \\iff x^2 + (b-2)xy + y^2 = 0$。\n"
            "$x$ について平方完成すると：\n"
            "$$\\left(x + \\frac{b-2}{2}y\\right)^2 - \\frac{(b-2)^2}{4}y^2 + y^2 = 0$$\n"
            "$$\\left(x + \\frac{b-2}{2}y\\right)^2 + \\left(1 - \\frac{(b-2)^2}{4}\\right)y^2 = 0$$\n"
            "与式 $\\left(x + \\frac{b-\\text{L}}{\\text{M}}y\\right)^2 + \\left(\\text{N} - \\frac{(b-\\text{O})^2}{\\text{P}}\\right)y^2 = 0$ と比較して：\n"
            "$$\\text{L} = 2, \\quad \\text{M} = 2, \\quad \\text{N} = 1, \\quad \\text{O} = 2, \\quad \\text{P} = 4 \\implies \\text{LMNOP} = 22124$$\n"
            "この式の実数解が $(x, y) = (0, 0)$（すなわち条件 $q$）のみとなるための必要十分条件は、$y^2$ の係数が正であることである：\n"
            "$$1 - \\frac{(b-2)^2}{4} > 0 \\iff (b-2)^2 < 4 \\iff -2 < b - 2 < 2 \\iff 0 < b < 4$$\n"
            "与式 $\\text{Q} < b < \\text{R}$ と比較して：\n"
            "$$\\text{Q} = 0, \\quad \\text{R} = 4 \\implies \\text{QR} = 04$$\n\n"
            "**【考査考点】**\n"
            "- 命題と論理（必要条件・十分条件・必要十分条件）の判定。\n"
            "- 2変数2次斉次式の平方完成と自明な解 $(0, 0)$ のみの存在条件（正定値性）。"
        )
    },
    {
        "q_num": "II_1",
        "localKey": "math-q-II_1",
        "answer_ref": "II:1",
        "answer": {
            "A": "8",
            "BCD": "112",
            "EF": "29",
            "GHI": "389"
        },
        "title": "数学 コース1 第II問 [1]：玉の同時抽出と得点の確率分布・期待値",
        "points": [
            "全事象 $\\binom{9}{2} = 36$ 通りにおける確率の立式",
            "最高得点（8点）および指定得点（6点）の事象の場合分け計算",
            "期待値の定義または線形性を利用した期待値の計算"
        ],
        "solution": (
            "**【題目大意】**\n"
            "袋の中に白球1個（5点）、赤球3個（3点）、黒球5個（1点）の計9個が入っている。同時に2個の球を取り出し、得点の合計を考える。\n"
            "(1) 最高得点 A と、それが起こる確率 $\\frac{\\text{B}}{\\text{CD}}$ を求める。\n"
            "(2) 得点が 6 になる確率 $\\frac{\\text{E}}{\\text{F}}$ を求める。\n"
            "(3) 得点の期待値 $\\frac{\\text{GH}}{\\text{I}}$ を求める。\n\n"
            "**【公式正解】**\n"
            "$\\text{A} = 8$\n"
            "$\\text{BCD} = 112$ （確率 $\\frac{1}{12}$）\n"
            "$\\text{EF} = 29$ （確率 $\\frac{2}{9}$）\n"
            "$\\text{GHI} = 389$ （期待値 $\\frac{38}{9}$）\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "9個の球から同時に2個を取り出す全事象の総数は：\n"
            "$$N = \\binom{9}{2} = \\frac{9 \\times 8}{2 \\times 1} = 36\\text{ 通り}$$\n\n"
            "**(1) 最高得点とその確率**\n"
            "白球は1個しかないため、白球2個（10点）は不可能である。\n"
            "したがって、最高の得点は白球1個（5点）と赤球1個（3点）を取り出す場合であり：\n"
            "$$\\text{最高得点} = 5 + 3 = 8\\text{ 点} \\quad (\\text{A} = 8)$$\n"
            "その組み合わせの数は $\\binom{1}{1} \\times \\binom{3}{1} = 1 \\times 3 = 3\\text{ 通り}$。\n"
            "よって確率は：\n"
            "$$P(8) = \\frac{3}{36} = \\frac{1}{12} \\quad (\\text{BCD} = 112)$$\n\n"
            "**(2) 得点が 6 になる確率**\n"
            "合計が 6 点になる組み合わせは次の2通りである：\n"
            "1. 白球1個（5点）と黒球1個（1点）：$\\binom{1}{1} \\times \\binom{5}{1} = 1 \\times 5 = 5\\text{ 通り}$\n"
            "2. 赤球2個（$3 + 3 = 6$点）：$\\binom{3}{2} = 3\\text{ 通り}$\n"
            "合計で $5 + 3 = 8\\text{ 通り}$ である。\n"
            "よって確率は：\n"
            "$$P(6) = \\frac{8}{36} = \\frac{2}{9} \\quad (\\text{EF} = 29)$$\n\n"
            "**(3) 得点の期待値**\n"
            "各球1個あたりの得点の期待値を $E_1$ とすると、無作為に1個を取り出したときの期待値は：\n"
            "$$E_1 = 5 \\times \\frac{1}{9} + 3 \\times \\frac{3}{9} + 1 \\times \\frac{5}{9} = \\frac{5 + 9 + 5}{9} = \\frac{19}{9}$$\n"
            "期待値の線形性より、同時に2個を取り出したときの合計得点の期待値 $E$ は：\n"
            "$$E = 2 \\times E_1 = 2 \\times \\frac{19}{9} = \\frac{38}{9}$$\n"
            "（検算：可能な得点は 8点(3通り), 6点(8通り), 4点(赤1黒1, $3 \\times 5 = 15$通り), 2点(黒2, $\\binom{5}{2} = 10$通り)。\n"
            "$\\sum X P(X) = \\frac{8 \\times 3 + 6 \\times 8 + 4 \\times 15 + 2 \\times 10}{36} = \\frac{24 + 48 + 60 + 20}{36} = \\frac{152}{36} = \\frac{38}{9}$）\n"
            "与式 $\\frac{\\text{GH}}{\\text{I}}$ と比較して：\n"
            "$$\\text{GH} = 38, \\quad \\text{I} = 9 \\implies \\text{GHI} = 389$$\n\n"
            "**【考査考点】**\n"
            "- 組合せを用いた確率の基本的計算。\n"
            "- 確率変数の期待値の定義および期待値の加法性の活用。"
        )
    },
    {
        "q_num": "II_2",
        "localKey": "math-q-II_2",
        "answer_ref": "II:2",
        "answer": {
            "J": "1",
            "KL": "13",
            "M": "6",
            "N": "7",
            "OP": "36",
            "Q": "4",
            "R": "5",
            "ST": "64"
        },
        "title": "数学 コース1 第II問 [2]：完全平方数・完全立方数と整数方程式（因数分解法）",
        "points": [
            "平方の差 $y^2 - x^2 = (y-x)(y+x) = 13$ と素数条件による自然数解の決定",
            "立方の差 $y^3 - x^3 = (y-x)(y^2+xy+x^2) = 61$ による自然数解の決定",
            "完全平方数 $n = 36$ および完全立方数 $n = 64$ の特定"
        ],
        "solution": (
            "**【題目大意】**\n"
            "(i) $n$ を完全平方数（$n=x^2$）とする。$n$ に 13 を加えた数も完全平方数（$y^2$）であるとき、$n$ を求める。\n"
            "(ii) $n$ を完全立方数（$n=x^3$）とする。$n$ に 61 を加えた数も完全立方数（$y^3$）であるとき、$n$ を求める。\n\n"
            "**【公式正解】**\n"
            "$\\text{J} = 1$\n"
            "$\\text{KL} = 13$\n"
            "$\\text{M} = 6$\n"
            "$\\text{N} = 7$\n"
            "$\\text{OP} = 36$\n"
            "$\\text{Q} = 4$\n"
            "$\\text{R} = 5$\n"
            "$\\text{ST} = 64$\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "**(1) 条件(i)の完全平方数の決定**\n"
            "$n = x^2$（$x$ は自然数）であり、$x^2 + 13 = y^2$（$y$ は自然数）と表せる。\n"
            "移行して因数分解すると：\n"
            "$$y^2 - x^2 = 13 \\iff (y - x)(y + x) = 13$$\n"
            "$x, y$ は自然数であり、$y^2 = x^2 + 13 > x^2$ より $y > x$、すなわち $y - x > 0, y + x > 0$ である。\n"
            "また $y - x < y + x$ であり、13 は素数であるから、約数の組み合わせはただ1通りに定まる：\n"
            "$$y - x = 1 \\quad (\\text{J} = 1)$$\n"
            "$$y + x = 13 \\quad (\\text{KL} = 13)$$\n"
            "2式の和をとると $2y = 14 \\implies y = 7 \\quad (\\text{N} = 7)$。\n"
            "差をとると $2x = 12 \\implies x = 6 \\quad (\\text{M} = 6)$。\n"
            "したがって、求める完全平方数 $n$ は：\n"
            "$$n = x^2 = 6^2 = 36 \\quad (\\text{OP} = 36)$$\n\n"
            "**(2) 条件(ii)の完全立方数の決定**\n"
            "$n = x^3$（$x$ は自然数）であり、$x^3 + 61 = y^3$（$y$ は自然数）と表せる。\n"
            "移行して立方の差の公式により因数分解すると：\n"
            "$$y^3 - x^3 = 61 \\iff (y - x)(y^2 + xy + x^2) = 61$$\n"
            "$x, y$ は自然数で $y > x \\ge 1$ であるから：\n"
            "$$y^2 + xy + x^2 > y - x \\ge 1$$\n"
            "61 は素数であるから：\n"
            "$$y - x = 1 \\implies y = x + 1$$\n"
            "これを $y^2 + xy + x^2 = 61$ に代入する：\n"
            "$$(x + 1)^2 + x(x + 1) + x^2 = 61$$\n"
            "$$x^2 + 2x + 1 + x^2 + x + x^2 = 61 \\implies 3x^2 + 3x + 1 = 61$$\n"
            "$$3x^2 + 3x - 60 = 0 \\implies x^2 + x - 20 = 0$$\n"
            "因数分解すると：\n"
            "$$(x + 5)(x - 4) = 0$$\n"
            "$x$ は自然数（$x > 0$）であるから：\n"
            "$$x = 4 \\quad (\\text{Q} = 4)$$\n"
            "$$y = x + 1 = 5 \\quad (\\text{R} = 5)$$\n"
            "したがって、求める完全立方数 $n$ は：\n"
            "$$n = x^3 = 4^3 = 64 \\quad (\\text{ST} = 64)$$\n\n"
            "**【考査考点】**\n"
            "- 平方の差・立方の差の因数分解公式の適用。\n"
            "- 素数の性質を利用した整数方程式（不定方程式）の解法。"
        )
    },
    {
        "q_num": "III_1",
        "localKey": "math-q-III_1",
        "answer_ref": "III:1",
        "answer": {
            "ABCD": "2421",
            "EF": "-7",
            "G": "3"
        },
        "title": "数学 コース1 第III問 (1)：2次不等式がすべての実数で成り立つ条件",
        "points": [
            "2次式の平方完成 $(x - a - 2)^2 - a^2 - 4a + 21$",
            "すべての実数で常に正となる条件（頂点の $y$ 座標 $> 0$ または判別式 $D < 0$）",
            "2次不等式の解法によるパラメータ範囲 $-7 < a < 3$ の決定"
        ],
        "solution": (
            "**【題目大意】**\n"
            "$a$ を定数とする。2次不等式\n"
            "$$x^2 - 2(a + 2)x + 25 > 0 \\quad \\cdots \\textcircled{1}$$\n"
            "について、左辺を平方完成し、すべての実数 $x$ に対して不等式 $\\textcircled{1}$ が成り立つ条件を求める。\n\n"
            "**【公式正解】**\n"
            "$\\text{ABCD} = 2421$\n"
            "$\\text{EF} = -7$\n"
            "$\\text{G} = 3$\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "**(1) 左辺の平方完成**\n"
            "左辺の $x$ の1次の係数は $-2(a + 2)$ であるから：\n"
            "$$x^2 - 2(a + 2)x + 25 = \\left[x - (a + 2)\\right]^2 - (a + 2)^2 + 25$$\n"
            "$$= (x - a - 2)^2 - (a^2 + 4a + 4) + 25 = (x - a - 2)^2 - a^2 - 4a + 21$$\n"
            "与式 $(x - a - \\text{A})^2 - a^2 - \\text{B}a + \\text{CD}$ と比較して：\n"
            "$$\\text{A} = 2, \\quad \\text{B} = 4, \\quad \\text{CD} = 21 \\implies \\text{ABCD} = 2421$$\n\n"
            "**(2) すべての実数 $x$ で成り立つ条件**\n"
            "放物線 $y = (x - a - 2)^2 - a^2 - 4a + 21$ は下に凸である。\n"
            "すべての実数 $x$ に対して $y > 0$ が成り立つためには、頂点の $y$ 座標が正であればよい：\n"
            "$$-a^2 - 4a + 21 > 0 \\iff a^2 + 4a - 21 < 0$$\n"
            "因数分解すると：\n"
            "$$(a + 7)(a - 3) < 0$$\n"
            "したがって、求める条件は：\n"
            "$$-7 < a < 3$$\n"
            "与式 $\\text{EF} < a < \\text{G}$ と比較して：\n"
            "$$\\text{EF} = -7, \\quad \\text{G} = 3$$\n\n"
            "**【考査考点】**\n"
            "- 2次関数の平方完成と頂点の座標の特定。\n"
            "- 2次不等式が全実数で成立する条件（判別式 $D/4 < 0$）。"
        )
    },
    {
        "q_num": "III_2",
        "localKey": "math-q-III_2",
        "answer_ref": "III:2",
        "answer": {
            "HIJ": "-15",
            "K": "3"
        },
        "title": "数学 コース1 第III問 (2)：半無限区間 x >= -1 において2次不等式が常に成り立つ条件",
        "points": [
            "放物線の軸 $x = a + 2$ と定義域境界 $x = -1$ の位置関係による場合分け",
            "区間外（$a+2 < -1$）における端点条件 $f(-1) > 0$ の立式",
            "区間内（$a+2 \\ge -1$）における頂点条件との統合による $-15 < a < 3$ の導出"
        ],
        "solution": (
            "**【題目大意】**\n"
            "第III問の2次不等式 $x^2 - 2(a + 2)x + 25 > 0$ ① が、$x \\geq -1$ を満たすすべての実数 $x$ に対して成り立つための $a$ の条件を求める。\n\n"
            "**【公式正解】**\n"
            "$\\text{HIJ} = -15$\n"
            "$\\text{K} = 3$\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "$f(x) = x^2 - 2(a + 2)x + 25 = (x - (a + 2))^2 - a^2 - 4a + 21$ とおく。\n"
            "放物線の軸は $x = a + 2$ である。\n"
            "$x \\ge -1$ において常に $f(x) > 0$ が成り立つためには、区間 $x \\ge -1$ における $f(x)$ の最小値が正であればよい。\n"
            "軸の位置により場合分けを行う：\n\n"
            "**[ケース1] 軸が区間の左側にある場合（$a + 2 < -1 \\iff a < -3$）**\n"
            "$x \\ge -1$ において $f(x)$ は単調増加であるから、最小値は端点 $x = -1$ でとる。\n"
            "$$f(-1) = (-1)^2 - 2(a + 2)(-1) + 25 = 1 + 2a + 4 + 25 = 2a + 30$$\n"
            "最小値が正となる条件は：\n"
            "$$2a + 30 > 0 \\iff 2a > -30 \\iff a > -15$$\n"
            "$a < -3$ との共通範囲をとると：\n"
            "$$-15 < a < -3$$\n\n"
            "**[ケース2] 軸が区間内にある場合（$a + 2 \\ge -1 \\iff a \\ge -3$）**\n"
            "$x \\ge -1$ において $f(x)$ は頂点 $x = a + 2$ で最小値をとる。\n"
            "最小値が正となる条件は、(1)で求めたように：\n"
            "$$-a^2 - 4a + 21 > 0 \\iff -7 < a < 3$$\n"
            "$a \\ge -3$ との共通範囲をとると：\n"
            "$$-3 \\le a < 3$$\n\n"
            "**[ケース1とケース2の統合]**\n"
            "求める条件は、両ケースの和集合である：\n"
            "$$(-15 < a < -3) \\cup (-3 \\le a < 3) \\implies -15 < a < 3$$\n"
            "与式 $\\text{HIJ} < a < \\text{K}$ と比較して：\n"
            "$$\\text{HIJ} = -15, \\quad \\text{K} = 3$$\n\n"
            "**【考査考点】**\n"
            "- 定義域が制限された2次関数の最小値問題（軸の位置による場合分け）。\n"
            "- 不等式の解の配置問題と端点・頂点の条件検討。"
        )
    },
    {
        "q_num": "IV_1",
        "localKey": "math-q-IV_1",
        "answer_ref": "IV:1",
        "answer": {
            "ABCD": "1574",
            "E": "6"
        },
        "title": "数学 コース1 第IV問 (1)：三角形の余弦定理と面積・線分長",
        "points": [
            "三角比の相互関係 $\\sin^2 A + \\cos^2 A = 1$ による $\\sin\\angle BAC$ の算出",
            "三角形の面積公式 $S = \\frac{1}{2}AB \\cdot AC \\sin\\angle BAC$ の適用",
            "余弦定理による対辺長 $BC = 6$ の決定"
        ],
        "solution": (
            "**【題目大意】**\n"
            "$\\triangle \\text{ABC}$ において、$AB = 4, AC = 5, \\cos \\angle \\text{BAC} = \\frac{1}{8}$ である。\n"
            "$\\triangle \\text{ABC}$ の面積 $S$ および辺 $BC$ の長さを求める。\n\n"
            "**【公式正解】**\n"
            "$\\text{ABCD} = 1574$ （$S = \\frac{15\\sqrt{7}}{4}$）\n"
            "$\\text{E} = 6$\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "**(1) $\\triangle \\text{ABC}$ の面積 $S$**\n"
            "$0 < \\angle \\text{BAC} < 180^\\circ$ より $\\sin \\angle \\text{BAC} > 0$ である。\n"
            "$$\\sin \\angle \\text{BAC} = \\sqrt{1 - \\cos^2 \\angle \\text{BAC}} = \\sqrt{1 - \\left(\\frac{1}{8}\\right)^2} = \\sqrt{1 - \\frac{1}{64}} = \\sqrt{\\frac{63}{64}} = \\frac{3\\sqrt{7}}{8}$$\n"
            "三角形の面積公式より：\n"
            "$$S = \\frac{1}{2} \\times AB \\times AC \\times \\sin \\angle \\text{BAC} = \\frac{1}{2} \\times 4 \\times 5 \\times \\frac{3\\sqrt{7}}{8} = 10 \\times \\frac{3\\sqrt{7}}{8} = \\frac{15\\sqrt{7}}{4}$$\n"
            "与式 $\\frac{\\text{AB}\\sqrt{\\text{C}}}{\\text{D}}$ と比較して：\n"
            "$$\\text{AB} = 15, \\quad \\text{C} = 7, \\quad \\text{D} = 4 \\implies \\text{ABCD} = 1574$$\n\n"
            "**(2) 辺 $BC$ の長さ**\n"
            "余弦定理より：\n"
            "$$BC^2 = AB^2 + AC^2 - 2 \\times AB \\times AC \\times \\cos \\angle \\text{BAC}$$\n"
            "$$BC^2 = 4^2 + 5^2 - 2 \\times 4 \\times 5 \\times \\frac{1}{8} = 16 + 25 - 5 = 36$$\n"
            "$BC > 0$ であるから：\n"
            "$$BC = 6 \\quad (\\text{E} = 6)$$\n\n"
            "**【考査考点】**\n"
            "- 三角比の基本公式と面積計算。\n"
            "- 余弦定理を用いた対辺長の算出。"
        )
    },
    {
        "q_num": "IV_2",
        "localKey": "math-q-IV_2",
        "answer_ref": "IV:2",
        "answer": {
            "FG": "49",
            "HIJK": "2536",
            "LMNOP": "25748",
            "QR": "56"
        },
        "title": "数学 コース1 第IV問 (2)(3)：相似な三角形の面積比と幾何学的長さ・面積の計算",
        "points": [
            "角の相等条件に基づく相似三角形の発見（$\\triangle ABD \\sim \\triangle CBA$ など）",
            "相似比と面積比（相似比の2乗）による面積比 $S : S_1 : S_2 = 1 : \\frac{4}{9} : \\frac{25}{36}$ の決定",
            "幾何学的関係に基づく $\\triangle ADE$ の面積 $T$ および線分長 $DE = \\frac{5}{6}$ の導出"
        ],
        "solution": (
            "**【題目大意】**\n"
            "第IV問(1)の設定のもとで、$\\angle \\text{BAD} = \\angle \\text{ACB}$、$\\angle \\text{CAE} = \\angle \\text{ABC}$ であるとする（点 D, E は直線 BC 上にある）。\n"
            "(2) $\\triangle \\text{ABD}, \\triangle \\text{ACE}$ の面積をそれぞれ $S_1, S_2$ とするとき、面積比 $S : S_1 : S_2$ を求める。\n"
            "(3) $\\triangle \\text{ADE}$ の面積 $T$ および線分 $DE$ の長さを求める。\n\n"
            "**【公式正解】**\n"
            "$\\text{FG} = 49$ （比 $\\frac{4}{9}$）\n"
            "$\\text{HIJK} = 2536$ （比 $\\frac{25}{36}$）\n"
            "$\\text{LMNOP} = 25748$ （$T = \\frac{25\\sqrt{7}}{48}$）\n"
            "$\\text{QR} = 56$ （$DE = \\frac{5}{6}$）\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "**(1) 相似比と面積比 $S : S_1 : S_2$**\n"
            "$\\triangle \\text{ABD}$ と $\\triangle \\text{CBA}$ について：\n"
            "- 条件より $\\angle \\text{BAD} = \\angle \\text{BCA}$\n"
            "- $\\angle \\text{B}$ は共通\n"
            "2組の角がそれぞれ等しいので、$\\triangle \\text{ABD} \\sim \\triangle \\text{CBA}$ である。\n"
            "相似比は対応する辺の比：\n"
            "$$\\frac{AB}{CB} = \\frac{4}{6} = \\frac{2}{3}$$\n"
            "面積比は相似比の2乗であるから：\n"
            "$$\\frac{S_1}{S} = \\left(\\frac{2}{3}\\right)^2 = \\frac{4}{9} \\quad (\\text{FG} = 49)$$\n\n"
            "同様に、$\\triangle \\text{ACE}$ と $\\triangle \\text{BCA}$ について：\n"
            "- 条件より $\\angle \\text{CAE} = \\angle \\text{CBA}$\n"
            "- $\\angle \\text{C}$ は共通\n"
            "2組の角がそれぞれ等しいので、$\\triangle \\text{ACE} \\sim \\triangle \\text{BCA}$ である。\n"
            "相似比は：\n"
            "$$\\frac{AC}{BC} = \\frac{5}{6}$$\n"
            "面積比は相似比の2乗であるから：\n"
            "$$\\frac{S_2}{S} = \\left(\\frac{5}{6}\\right)^2 = \\frac{25}{36} \\quad (\\text{HIJK} = 2536)$$\n"
            "したがって、$S : S_1 : S_2 = 1 : \\frac{4}{9} : \\frac{25}{36}$ である。\n\n"
            "**(2) 線分 $BD, CE$ と $DE$ の長さ**\n"
            "$\\triangle \\text{ABD} \\sim \\triangle \\text{CBA}$ より：\n"
            "$$\\frac{BD}{BA} = \\frac{AB}{CB} \\implies BD = \\frac{AB^2}{BC} = \\frac{4^2}{6} = \\frac{16}{6} = \\frac{8}{3}$$\n"
            "$\\triangle \\text{ACE} \\sim \\triangle \\text{BCA}$ より：\n"
            "$$\\frac{CE}{CA} = \\frac{AC}{BC} \\implies CE = \\frac{AC^2}{BC} = \\frac{5^2}{6} = \\frac{25}{6}$$\n"
            "点 D, E は線分 BC 上にあり、\n"
            "$$DE = BC - (BC - BD) - (BC - CE) = BD + CE - BC$$\n"
            "$$DE = \\frac{16}{6} + \\frac{25}{6} - 6 = \\frac{41}{6} - \\frac{36}{6} = \\frac{5}{6} \\quad (\\text{QR} = 56)$$\n\n"
            "**(3) $\\triangle \\text{ADE}$ の面積 $T$**\n"
            "$\\triangle \\text{ADE}$ と $\\triangle \\text{ABC}$ は底辺を直線 BC 上に共有し、高さが共通である。\n"
            "したがって、面積比は底辺の長さの比に等しい：\n"
            "$$\\frac{T}{S} = \\frac{DE}{BC} = \\frac{\\frac{5}{6}}{6} = \\frac{5}{36}$$\n"
            "(1)で求めた $S = \\frac{15\\sqrt{7}}{4}$ を代入すると：\n"
            "$$T = \\frac{5}{36} \\times \\frac{15\\sqrt{7}}{4} = \\frac{5 \\times 5\\sqrt{7}}{12 \\times 4} = \\frac{25\\sqrt{7}}{48}$$\n"
            "与式 $\\frac{\\text{LM}\\sqrt{\\text{N}}}{\\text{OP}}$ と比較して：\n"
            "$$\\text{LM} = 25, \\quad \\text{N} = 7, \\quad \\text{OP} = 48 \\implies \\text{LMNOP} = 25748$$\n\n"
            "**【考査考点】**\n"
            "- 三角形の相似条件と相似比・面積比の関係。\n"
            "- 同一の高さをもつ三角形の面積比と底辺比の性質。"
        )
    }
]

def main():
    work_dir = Path("work/2013-2-math-c1")
    work_dir.mkdir(parents=True, exist_ok=True)
    docs_dir = Path("docs/explanations")
    docs_dir.mkdir(parents=True, exist_ok=True)

    json_path = work_dir / "explanations.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(math_c1_questions, f, ensure_ascii=False, indent=2)
    print(f"Generated {json_path} ({len(math_c1_questions)} questions)")

    md_path = docs_dir / "2013-2-math-c1-solutions.md"
    lines = [
        "# 2013-2 EJU 数学 コース1 詳解・完全解説\n",
        "> 本ドキュメントは 2013年度第2回 EJU（日本留学試験）数学コース1に対する公式正解準拠の完全詳解である。\n",
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

