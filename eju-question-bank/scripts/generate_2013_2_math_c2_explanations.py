#!/usr/bin/env python3
"""Generate comprehensive pedagogical explanations for 2013-2 EJU Math Course 2 (8 items)."""

import json
from pathlib import Path

math_c2_questions = [
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
        "title": "数学 コース2 第I問 [1]：2次関数の最大値・軸・交点と平行移動",
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
            "$$y = -\\left(x + \\frac{a}{2}\\right)^2 + \\frac{a^2}{4} + 3$$\n"
            "上に凸の放物線であるため、最大値は頂点 $x = -\\frac{a}{2}$ における $\\frac{a^2}{4} + 3$ である。\n"
            "最大値が 7 であるから：\n"
            "$$\\frac{a^2}{4} + 3 = 7 \\implies \\frac{a^2}{4} = 4 \\implies a^2 = 16$$\n"
            "$a > 0$ より：\n"
            "$$a = 4 \\quad (\\text{A} = 4)$$\n"
            "このとき、軸の方程式は：\n"
            "$$x = -\\frac{a}{2} = -2 \\quad (\\text{BC} = -2)$$\n"
            "グラフと $x$ 軸の交点の $x$ 座標は、$x^2 + 4x - 3 = 0$ を解いて：\n"
            "$$x = -2 \\pm \\sqrt{4 - (-3)} = -2 \\pm \\sqrt{7}$$\n"
            "与式 $\\text{DE} \\pm \\sqrt{\\text{F}}$ と比較して：\n"
            "$$\\text{DE} = -2, \\quad \\text{F} = 7 \\implies \\text{DEF} = -27$$\n\n"
            "**(2) グラフの平行移動**\n"
            "$x$ 軸方向に 2、$y$ 軸方向に -3 平行移動すると：\n"
            "$$y - (-3) = -(x - 2)^2 - a(x - 2) + 3 \\implies y = -(x - 2)^2 - a(x - 2)$$\n"
            "この曲線が点 $(-3, -5)$ を通るから：\n"
            "$$-5 = -(-3 - 2)^2 - a(-3 - 2) = -25 + 5a$$\n"
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
        "title": "数学 コース2 第I問 [2]：同値変形と必要条件・十分条件の判定",
        "points": [
            "多項式等式の因数分解と条件 $p$ の代数的意味の把握",
            "必要条件・十分条件・必要十分条件の論理的判定",
            "平方完成による正値条件と必要十分条件となるパラメータ範囲の決定"
        ],
        "solution": (
            "**【題目大意】**\n"
            "実数 $x, y$ についての条件を考える：\n"
            "$p$：$(x+y)^2 = a(x^2+y^2) + bxy$（$a, b$ は実数の定数）\n"
            "$q$：$x=0$ かつ $y=0$\n"
            "$r$：$x=0$ または $y=0$\n"
            "(1) $a=b=1$ のとき、$p$ は $q$ であるための何条件か（H）、また $r$ であるための何条件か（I）。\n"
            "(2) $a=b=2$ のとき、$p$ は $q$ であるための何条件か（J）、また $r$ であるための何条件か（K）。\n"
            "(3) $a=2$ のとき、$p$ を平方完成の形に変形し、$p$ が $q$ であるための必要十分条件となる $b$ の範囲を求める。\n\n"
            "**【公式正解】**\n"
            "$\\text{H} = 1$\n"
            "$\\text{I} = 0$\n"
            "$\\text{J} = 0$\n"
            "$\\text{K} = 2$\n"
            "$\\text{LMNOP} = 22124$\n"
            "$\\text{QR} = 04$\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "**(1) $a=b=1$ の場合**\n"
            "$(x+y)^2 = x^2+y^2 + xy \\iff 2xy = xy \\iff xy = 0$。\n"
            "条件 $p$ は「$xy = 0$」と同値であり、これは条件 $r$（$x=0$ または $y=0$）と完全に一致する。\n"
            "- $p$ と $q$：$q \\implies p$（$x=y=0 \\implies xy=0$）は真だが、$p \\implies q$ は偽（反例：$x=1, y=0$）。\n"
            "  よって $p$ は $q$ であるための「必要条件であるが十分条件ではない」（$\\textcircled{1} \\implies \\text{H} = 1$）。\n"
            "- $p$ と $r$：$p \\iff r$ であるから、「必要十分条件である」（$\\textcircled{0} \\implies \\text{I} = 0$）。\n\n"
            "**(2) $a=b=2$ の場合**\n"
            "$(x+y)^2 = 2(x^2+y^2) + 2xy \\iff x^2 + 2xy + y^2 = 2x^2 + 2y^2 + 2xy \\iff x^2 + y^2 = 0$。\n"
            "$x, y$ は実数であるから、$x^2 + y^2 = 0 \\iff x = 0 \\text{ かつ } y = 0$（条件 $q$）。\n"
            "- $p$ と $q$：$p \\iff q$ であるから、「必要十分条件である」（$\\textcircled{0} \\implies \\text{J} = 0$）。\n"
            "- $p$ と $r$：$p \\implies r$ は真だが、$r \\implies p$ は偽。\n"
            "  よって $p$ は $r$ であるための「十分条件であるが必要条件ではない」（$\\textcircled{2} \\implies \\text{K} = 2$）。\n\n"
            "**(3) $a=2$ のときの変形と条件**\n"
            "$(x+y)^2 = 2(x^2+y^2) + bxy \\iff x^2 + (b-2)xy + y^2 = 0$。\n"
            "$x$ について平方完成すると：\n"
            "$$\\left(x + \\frac{b-2}{2}y\\right)^2 + \\left(1 - \\frac{(b-2)^2}{4}\\right)y^2 = 0$$\n"
            "与式 $\\left(x + \\frac{b-\\text{L}}{\\text{M}}y\\right)^2 + \\left(\\text{N} - \\frac{(b-\\text{O})^2}{\\text{P}}\\right)y^2 = 0$ と比較して：\n"
            "$$\\text{L} = 2, \\quad \\text{M} = 2, \\quad \\text{N} = 1, \\quad \\text{O} = 2, \\quad \\text{P} = 4 \\implies \\text{LMNOP} = 22124$$\n"
            "解が $(x, y) = (0, 0)$ のみ（条件 $q$）となる条件は、$y^2$ の係数が正であることである：\n"
            "$$1 - \\frac{(b-2)^2}{4} > 0 \\iff (b-2)^2 < 4 \\iff -2 < b - 2 < 2 \\iff 0 < b < 4$$\n"
            "与式 $\\text{Q} < b < \\text{R}$ と比較して：\n"
            "$$\\text{Q} = 0, \\quad \\text{R} = 4 \\implies \\text{QR} = 04$$\n\n"
            "**【考査考点】**\n"
            "- 命題と論理（必要条件・十分条件・必要十分条件）の判定。\n"
            "- 2変数2次斉次式の平方完成と自明な解 $(0, 0)$ のみの存在条件。"
        )
    },
    {
        "q_num": "II_1",
        "localKey": "math-q-II_1",
        "answer_ref": "II:1",
        "answer": {
            "AB": "-2",
            "C": "4",
            "DE": "32",
            "FG": "34",
            "HI": "14",
            "JKLM": "3643"
        },
        "title": "数学 コース2 第II問 (1)(2)：等差数列の決定と無限等比級数の収束条件・和",
        "points": [
            "等差数列の条件方程式 $a_2=2, a_6=3a_3$ からの初項 $a=-2$、公差 $d=4$ の決定",
            "一般項 $a_n = 4n - 6$ と級数の初項 $3r^2$、公比 $\\frac{3}{r^4}$ の導出",
            "収束条件 $r > \\sqrt[4]{3}$ および等比級数の和 $S = \\frac{3r^6}{r^4 - 3}$ の計算"
        ],
        "solution": (
            "**【題目大意】**\n"
            "等差数列 $\\{a_n\\}$ が $a_2 = 2, a_6 = 3a_3$ を満たしている。級数 $\\sum_{n=1}^\\infty \\frac{3^n}{r^{a_n}}$（$r > 0$）を考える。\n"
            "(1) 初項 $a$ と公差 $d$ を求める。\n"
            "(2) 級数の初項、公比、収束条件 $r > \\text{H}\\sqrt[\\text{I}]{3}$、および和 $S$ を求める。\n\n"
            "**【公式正解】**\n"
            "$\\text{AB} = -2$\n"
            "$\\text{C} = 4$\n"
            "$\\text{DE} = 32$ （初項 $3r^2$）\n"
            "$\\text{FG} = 34$ （公比 $\\frac{3}{r^4}$）\n"
            "$\\text{HI} = 14$ （$r > 1\\sqrt[4]{3} = \\sqrt[4]{3}$）\n"
            "$\\text{JKLM} = 3643$ （$S = \\frac{3r^6}{r^4 - 3}$）\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "**(1) 初項 $a$ と公差 $d$ の決定**\n"
            "等差数列の一般項は $a_n = a + (n - 1)d$ である。\n"
            "与えられた条件より：\n"
            "$$a_2 = a + d = 2 \\quad \\cdots \\textcircled{1}$$\n"
            "$$a_6 = a + 5d, \\quad a_3 = a + 2d$$\n"
            "$$a_6 = 3a_3 \\implies a + 5d = 3(a + 2d) = 3a + 6d$$\n"
            "$$2a + d = 0 \\implies d = -2a \\quad \\cdots \\textcircled{2}$$\n"
            "$\\textcircled{2}$ を $\\textcircled{1}$ に代入すると：\n"
            "$$a + (-2a) = 2 \\implies -a = 2 \\implies a = -2 \\quad (\\text{AB} = -2)$$\n"
            "これより：\n"
            "$$d = -2(-2) = 4 \\quad (\\text{C} = 4)$$\n"
            "したがって、一般項は：\n"
            "$$a_n = -2 + 4(n - 1) = 4n - 6$$\n\n"
            "**(2) 級数の初項、公比、収束条件、和**\n"
            "級数の第 $n$ 項 $u_n$ は：\n"
            "$$u_n = \\frac{3^n}{r^{a_n}} = \\frac{3^n}{r^{4n - 6}} = 3^n r^{6 - 4n}$$\n"
            "初項（$n = 1$）は：\n"
            "$$u_1 = \\frac{3^1}{r^{a_1}} = \\frac{3}{r^{-2}} = 3r^2$$\n"
            "与式 $\\text{D}r^{\\text{E}}$ と比較して：\n"
            "$$\\text{D} = 3, \\quad \\text{E} = 2 \\implies \\text{DE} = 32$$\n"
            "公比は：\n"
            "$$\\frac{u_{n+1}}{u_n} = \\frac{3^{n+1} r^{6 - 4(n+1)}}{3^n r^{6 - 4n}} = 3 \\cdot r^{-4} = \\frac{3}{r^4}$$\n"
            "与式 $\\frac{\\text{F}}{r^{\\text{G}}}$ と比較して：\n"
            "$$\\text{F} = 3, \\quad \\text{G} = 4 \\implies \\text{FG} = 34$$\n"
            "無限等比級数が収束するための必要十分条件は、公比の絶対値が 1 未満であることである（$r > 0$）：\n"
            "$$\\left|\\frac{3}{r^4}\\right| < 1 \\iff r^4 > 3 \\iff r > \\sqrt[4]{3} = 1\\sqrt[4]{3}$$\n"
            "与式 $r > \\text{H}\\sqrt[\\text{I}]{3}$ と比較して：\n"
            "$$\\text{H} = 1, \\quad \\text{I} = 4 \\implies \\text{HI} = 14$$\n"
            "このとき、和 $S$ は無限等比級数の和の公式 $S = \\frac{\\text{初項}}{1 - \\text{公比}}$ より：\n"
            "$$S = \\frac{3r^2}{1 - \\frac{3}{r^4}} = \\frac{3r^2 \\cdot r^4}{r^4 - 3} = \\frac{3r^6}{r^4 - 3}$$\n"
            "与式 $\\frac{\\text{J}r^{\\text{K}}}{r^{\\text{L}} - \\text{M}}$ と比較して：\n"
            "$$\\text{J} = 3, \\quad \\text{K} = 6, \\quad \\text{L} = 4, \\quad \\text{M} = 3 \\implies \\text{JKLM} = 3643$$\n\n"
            "**【考査考点】**\n"
            "- 等差数列の一般項の決定。\n"
            "- 指数法則を用いた無限等比級数の初項と公比の特定。\n"
            "- 無限等比級数の収束条件と和の計算公式。"
        )
    },
    {
        "q_num": "II_2",
        "localKey": "math-q-II_2",
        "answer_ref": "II:2",
        "answer": {
            "NO": "31"
        },
        "title": "数学 コース2 第II問 (3)：無限等比級数の和の最小値と微分法",
        "points": [
            "和の関数 $S(r) = \\frac{3r^6}{r^4 - 3}$ の変数変換 $u = r^2$ による簡約",
            "商の微分法による極値条件 $u = 3 \\implies r = \\sqrt{3}$ の特定",
            "指数表記 $r = 3^{1/2}$ の同定"
        ],
        "solution": (
            "**【題目大意】**\n"
            "第II問(2)の級数の和 $S = \\frac{3r^6}{r^4 - 3}$（$r > \\sqrt[4]{3}$）が最小となるときの $r$ の値を求める。\n\n"
            "**【公式正解】**\n"
            "$\\text{NO} = 31$ （$r = 3^{1/2} = \\sqrt{3}$）\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "$u = r^2$ とおく。$r > \\sqrt[4]{3}$ より $u > \\sqrt{3}$ である。\n"
            "和 $S$ は $u$ の関数として：\n"
            "$$S(u) = \\frac{3u^3}{u^2 - 3}$$\n"
            "$u$ で微分すると：\n"
            "$$S'(u) = \\frac{(9u^2)(u^2 - 3) - (3u^3)(2u)}{(u^2 - 3)^2} = \\frac{9u^4 - 27u^2 - 6u^4}{(u^2 - 3)^2} = \\frac{3u^4 - 27u^2}{(u^2 - 3)^2} = \\frac{3u^2(u^2 - 9)}{(u^2 - 3)^2}$$\n"
            "$u > \\sqrt{3}$ の範囲において：\n"
            "- $\\sqrt{3} < u < 3$ のとき、$u^2 - 9 < 0$ より $S'(u) < 0$（単調減少）\n"
            "- $u > 3$ のとき、$u^2 - 9 > 0$ より $S'(u) > 0$（単調増加）\n"
            "したがって、$S(u)$ は $u = 3$ のとき極小かつ最小となる。\n"
            "$u = r^2 = 3$ より：\n"
            "$$r = \\sqrt{3} = 3^{\\frac{1}{2}}$$\n"
            "与式 $r = \\text{N}^{\\frac{\\text{O}}{2}}$ と比較して：\n"
            "$$\\text{N} = 3, \\quad \\text{O} = 1 \\implies \\text{NO} = 31$$\n\n"
            "**【考査考点】**\n"
            "- 分数関数の微分法による極値問題の解法。\n"
            "- 変数変換（置換）による高次関数の効率的な増減解析。"
        )
    },
    {
        "q_num": "III_1",
        "localKey": "math-q-III_1",
        "answer_ref": "III:1",
        "answer": {
            "ABC": "132",
            "D": "2"
        },
        "title": "数学 コース2 第III問 (1)：三角関数の合成と変数の変域決定",
        "points": [
            "三角関数の合成公式 $t = \\sin x + \\cos x = \\sqrt{2}\\sin(x + \\frac{\\pi}{4})$",
            "制限された定義域 $-\\frac{\\pi}{3} \\le x \\le \\frac{\\pi}{3}$ における位相範囲の決定",
            "端点および極大値による $t$ の値域 $[\\frac{1-\\sqrt{3}}{2}, \\sqrt{2}]$ の算出"
        ],
        "solution": (
            "**【題目大意】**\n"
            "$-\\frac{\\pi}{3} \\le x \\le \\frac{\\pi}{3}$ の範囲において、関数 $f(x) = \\sin 2x - 3(\\sin x + \\cos x)$ を考える。\n"
            "$t = \\sin x + \\cos x$ とおくとき、$t$ のとり得る値の範囲を求める。\n\n"
            "**【公式正解】**\n"
            "$\\text{ABC} = 132$ （下限 $\\frac{1-\\sqrt{3}}{2}$）\n"
            "$\\text{D} = 2$ （上限 $\\sqrt{2}$）\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "三角関数の合成公式を適用する：\n"
            "$$t = \\sin x + \\cos x = \\sqrt{1^2 + 1^2} \\sin\\left(x + \\frac{\\pi}{4}\\right) = \\sqrt{2}\\sin\\left(x + \\frac{\\pi}{4}\\right)$$\n"
            "定義域 $-\\frac{\\pi}{3} \\le x \\le \\frac{\\pi}{3}$ より、位相 $x + \\frac{\\pi}{4}$ の範囲は：\n"
            "$$-\\frac{\\pi}{3} + \\frac{\\pi}{4} \\le x + \\frac{\\pi}{4} \\le \\frac{\\pi}{3} + \\frac{\\pi}{4}$$\n"
            "$$-\\frac{\\pi}{12} \\le x + \\frac{\\pi}{4} \\le \\frac{7\\pi}{12}$$\n"
            "この区間内において：\n"
            "- $x + \\frac{\\pi}{4} = \\frac{\\pi}{2}$（すなわち $x = \\frac{\\pi}{4}$）のとき、正弦は最大値 $1$ をとる。\n"
            "  したがって、$t$ の最大値は：\n"
            "  $$t_{\\max} = \\sqrt{2} \\times 1 = \\sqrt{2}$$\n"
            "- 最小値は区間の端点で比較する：\n"
            "  $x = -\\frac{\\pi}{3}$ のとき：\n"
            "  $$\\sin\\left(-\\frac{\\pi}{3}\\right) + \\cos\\left(-\\frac{\\pi}{3}\\right) = -\\frac{\\sqrt{3}}{2} + \\frac{1}{2} = \\frac{1 - \\sqrt{3}}{2}$$\n"
            "  $x = \\frac{\\pi}{3}$ のとき：\n"
            "  $$\\sin\\left(\\frac{\\pi}{3}\\right) + \\cos\\left(\\frac{\\pi}{3}\\right) = \\frac{\\sqrt{3}}{2} + \\frac{1}{2} = \\frac{1 + \\sqrt{3}}{2}$$\n"
            "  $\\frac{1 - \\sqrt{3}}{2} < \\frac{1 + \\sqrt{3}}{2}$ であるから、最小値は $\\frac{1 - \\sqrt{3}}{2}$ である。\n\n"
            "したがって、$t$ のとり得る値の範囲は：\n"
            "$$\\frac{1 - \\sqrt{3}}{2} \\le t \\le \\sqrt{2}$$\n"
            "与式 $\\frac{\\text{A} - \\sqrt{\\text{B}}}{\\text{C}} \\le t \\le \\sqrt{\\text{D}}$ と比較して：\n"
            "$$\\text{A} = 1, \\quad \\text{B} = 3, \\quad \\text{C} = 2 \\implies \\text{ABC} = 132$$\n"
            "$$\\text{D} = 2$$\n\n"
            "**【考査考点】**\n"
            "- 三角関数の合成公式の適用。\n"
            "- 制限された変域における位相の追跡と最大値・最小値の正確な決定。"
        )
    },
    {
        "q_num": "III_2",
        "localKey": "math-q-III_2",
        "answer_ref": "III:2",
        "answer": {
            "EFG": "132",
            "HI": "14"
        },
        "title": "数学 コース2 第III問 (2)：2倍角公式による2次式変換と関数の最小値",
        "points": [
            "2倍角公式 $\\sin 2x = t^2 - 1$ による関数 $f(t) = t^2 - 3t - 1$ の導出",
            "軸 $t = 3/2$ に対する変域の位置関係（単調減少区間）の把握",
            "端点 $t = \\sqrt{2}$（$x = \\frac{\\pi}{4}$）における最小値 $1 - 3\\sqrt{2}$ の決定"
        ],
        "solution": (
            "**【題目大意】**\n"
            "第III問の関数 $f(x) = \\sin 2x - 3(\\sin x + \\cos x)$ の最小値および最小値をとる $x$ の値を求める。\n\n"
            "**【公式正解】**\n"
            "$\\text{EFG} = 132$ （最小値 $1 - 3\\sqrt{2}$）\n"
            "$\\text{HI} = 14$ （$x = \\frac{1}{4}\\pi$）\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "**(1) $f(x)$ の $t$ による表現**\n"
            "$t = \\sin x + \\cos x$ の両辺を2乗すると：\n"
            "$$t^2 = (\\sin x + \\cos x)^2 = \\sin^2 x + 2\\sin x \\cos x + \\cos^2 x = 1 + \\sin 2x$$\n"
            "これより：\n"
            "$$\\sin 2x = t^2 - 1$$\n"
            "したがって、$f(x)$ は $t$ の2次関数として表される：\n"
            "$$f(x) = (t^2 - 1) - 3t = t^2 - 3t - 1$$\n\n"
            "**(2) 最小値の探索**\n"
            "平方完成すると：\n"
            "$$f(t) = \\left(t - \\frac{3}{2}\\right)^2 - \\frac{9}{4} - 1 = \\left(t - \\frac{3}{2}\\right)^2 - \\frac{13}{4}$$\n"
            "放物線の軸は $t = \\frac{3}{2} = 1.5$ である。\n"
            "(1)で求めた $t$ の変域は：\n"
            "$$\\frac{1 - \\sqrt{3}}{2} \\le t \\le \\sqrt{2}$$\n"
            "$\\sqrt{2} \\approx 1.414 < 1.5$ であるから、変域全体が軸 $t = 1.5$ の左側に位置する。\n"
            "したがって、$f(t)$ はこの区間において**単調減少**である。\n"
            "よって、最小値は $t$ が最大となる右端点 $t = \\sqrt{2}$ でとる。\n\n"
            "**(3) 最小値と $x$ の値の決定**\n"
            "$t = \\sqrt{2}$ を代入すると：\n"
            "$$f(\\sqrt{2}) = (\\sqrt{2})^2 - 3\\sqrt{2} - 1 = 2 - 3\\sqrt{2} - 1 = 1 - 3\\sqrt{2}$$\n"
            "与式 $\\text{E} - \\text{F}\\sqrt{\\text{G}}$ と比較して：\n"
            "$$\\text{E} = 1, \\quad \\text{F} = 3, \\quad \\text{G} = 2 \\implies \\text{EFG} = 132$$\n"
            "また、$t = \\sqrt{2}$ となるのは：\n"
            "$$\\sqrt{2}\\sin\\left(x + \\frac{\\pi}{4}\\right) = \\sqrt{2} \\implies \\sin\\left(x + \\frac{\\pi}{4}\\right) = 1$$\n"
            "区間 $-\\frac{\\pi}{12} \\le x + \\frac{\\pi}{4} \\le \\frac{7\\pi}{12}$ より：\n"
            "$$x + \\frac{\\pi}{4} = \\frac{\\pi}{2} \\implies x = \\frac{\\pi}{4} = \\frac{1}{4}\\pi$$\n"
            "与式 $x = \\frac{\\text{H}}{\\text{I}}\\pi$ と比較して：\n"
            "$$\\text{H} = 1, \\quad \\text{I} = 4 \\implies \\text{HI} = 14$$\n\n"
            "**【考査考点】**\n"
            "- $\\sin x + \\cos x$ による $\\sin 2x$ の置き換え手法。\n"
            "- 軸が定義域の外側にある場合の2次関数の単調性と端点極値。"
        )
    },
    {
        "q_num": "IV_1",
        "localKey": "math-q-IV_1",
        "answer_ref": "IV:1",
        "answer": {
            "AB": "12",
            "CD": "04",
            "E": "4",
            "FG": "21",
            "H": "9",
            "I": "7"
        },
        "title": "数学 コース2 第IV問 [1]：関数 f(x) = (log x)/x の増減と指数の大小比較",
        "points": [
            "商の微分法による導関数 $f'(x) = \\frac{1-\\log x}{x^2}$ の計算",
            "増減表に基づく単調増加区間 $(0, e]$ および単調減少区間 $[e, \\infty)$ の特定",
            "対数の差の恒等変形 $\\log p - \\log q = (a^2+a)[f(a)-f(a+1)]$ と単調性による大小判定"
        ],
        "solution": (
            "**【題目大意】**\n"
            "関数 $f(x) = \\frac{\\log x}{x}$（$x > 0$）の性質を用いて、$a^{a+1}$ と $(a+1)^a$ の大小関係を調べる。\n"
            "(1) $f(x)$ の導関数、単調増加区間、単調減少区間を求める。\n"
            "(2) $p = a^{a+1}, q = (a+1)^a$ のとき、$\\log p - \\log q$ の式を変形し、$0 < a < \\frac{3}{2}$ および $3 < a$ における $p$ と $q$ の大小関係を判定する。\n"
            "選択肢：$\\textcircled{0}\\ 0, \\textcircled{1}\\ 1, \\textcircled{2}\\ 2, \\textcircled{3}\\ 3, \\textcircled{4}\\ e, \\textcircled{5}\\ e+1, \\textcircled{6}\\ 1/e, \\textcircled{7}\\ >, \\textcircled{8}\\ =, \\textcircled{9}\\ <$\n\n"
            "**【公式正解】**\n"
            "$\\text{AB} = 12$\n"
            "$\\text{CD} = 04$ （$0 < x \\le e$）\n"
            "$\\text{E} = 4$ （$e \\le x$）\n"
            "$\\text{FG} = 21$\n"
            "$\\text{H} = 9$ （$<$）\n"
            "$\\text{I} = 7$ （$>$）\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "**(1) $f(x)$ の導関数と増減**\n"
            "商の微分公式より：\n"
            "$$f'(x) = \\frac{(\\log x)' \\cdot x - \\log x \\cdot (x)'}{x^2} = \\frac{\\frac{1}{x} \\cdot x - \\log x \\cdot 1}{x^2} = \\frac{1 - \\log x}{x^2}$$\n"
            "与式 $\\frac{\\text{A} - \\log x}{x^{\\text{B}}}$ と比較して：\n"
            "$$\\text{A} = \\textcircled{1} (1), \\quad \\text{B} = \\textcircled{2} (2) \\implies \\text{AB} = 12$$\n"
            "$f'(x) = 0 \\iff \\log x = 1 \\iff x = e$。\n"
            "- $0 < x \\le e$ において $1 - \\log x \\ge 0$ より $f'(x) \\ge 0$（単調増加）：$C = \\textcircled{0} (0), D = \\textcircled{4} (e) \\implies \\text{CD} = 04$\n"
            "- $e \\le x$ において $1 - \\log x \\le 0$ より $f'(x) \\le 0$（単調減少）：$E = \\textcircled{4} (e)$\n\n"
            "**(2) $p$ と $q$ の大小関係**\n"
            "両辺の自然対数をとる：\n"
            "$$\\log p = \\log(a^{a+1}) = (a + 1)\\log a = a(a + 1) \\frac{\\log a}{a} = a(a + 1)f(a)$$\n"
            "$$\\log q = \\log((a+1)^a) = a\\log(a + 1) = a(a + 1) \\frac{\\log(a + 1)}{a + 1} = a(a + 1)f(a + 1)$$\n"
            "差をとると：\n"
            "$$\\log p - \\log q = a(a + 1)\\left[f(a) - f(a + 1)\\right] = (a^2 + a)\\left[f(a) - f(a + 1)\\right]$$\n"
            "与式 $(a^{\\text{F}} + a)\\left[f(a) - f(a + \\text{G})\\right]$ と比較して：\n"
            "$$\\text{F} = \\textcircled{2} (2), \\quad \\text{G} = \\textcircled{1} (1) \\implies \\text{FG} = 21$$\n\n"
            "大小判定：\n"
            "- $0 < a < \\frac{3}{2}$ のとき：\n"
            "  $a + 1 < \\frac{3}{2} + 1 = 2.5 < e \\approx 2.718$ であるから、$0 < a < a + 1 \\le e$。\n"
            "  $(0, e]$ において $f(x)$ は単調増加であるから、$f(a) < f(a + 1)$。\n"
            "  したがって、$f(a) - f(a + 1) < 0$ となり、$\\log p - \\log q < 0 \\implies p < q$。\n"
            "  よって $\\text{H} = \\textcircled{9} (<)$ である。\n"
            "- $3 < a$ のとき：\n"
            "  $e < 3 < a < a + 1$ である。\n"
            "  $[e, \\infty)$ において $f(x)$ は単調減少であるから、$f(a) > f(a + 1)$。\n"
            "  したがって、$f(a) - f(a + 1) > 0$ となり、$\\log p - \\log q > 0 \\implies p > q$。\n"
            "  よって $\\text{I} = \\textcircled{7} (>)$ である。\n\n"
            "**【考査考点】**\n"
            "- 対数関数の微分法と商の微分公式の適用。\n"
            "- 微分を用いた関数の単調性解析と指数の大小関係への応用。"
        )
    },
    {
        "q_num": "IV_2",
        "localKey": "math-q-IV_2",
        "answer_ref": "IV:2",
        "answer": {
            "JKL": "142",
            "MNOPQR": "142232",
            "S": "1",
            "TU": "11"
        },
        "title": "数学 コース2 第IV問 [2]：部分積分法と2領域の面積和の最小化",
        "points": [
            "部分積分法による $xe^{2x}$ の不定積分 $\\frac{1}{4}(2x-1)e^{2x} + C$ の計算",
            "符号変化に応じた定積分による面積関数 $S(a)$ の立式",
            "微積分学の基本定理による導関数 $S'(a) = 0$ の解法と最小をとる $a = \\frac{1}{e^2+1}$ の決定"
        ],
        "solution": (
            "**【題目大意】**\n"
            "$0 < a < 1$ とする。曲線 $y = xe^{2x}$ と $x$ 軸および直線 $x = a - 1$ で囲まれる部分の面積と、直線 $x = a$ で囲まれる部分の面積の和を $S(a)$ とする。$S(a)$ を最小とする $a$ の値を求める。\n\n"
            "**【公式正解】**\n"
            "$\\text{JKL} = 142$\n"
            "$\\text{MNOPQR} = 142232$\n"
            "$\\text{S} = 1$\n"
            "$\\text{TU} = 11$\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "**(1) $xe^{2x}$ の不定積分**\n"
            "部分積分法を用いる：\n"
            "$$\\int x e^{2x} dx = x \\cdot \\frac{e^{2x}}{2} - \\int 1 \\cdot \\frac{e^{2x}}{2} dx = \\frac{1}{2} x e^{2x} - \\frac{1}{4} e^{2x} + C = \\frac{1}{4}(2x - 1)e^{2x} + C$$\n"
            "与式 $\\frac{\\text{J}}{\\text{K}}(\\text{L}x - 1)e^{2x} + C$ と比較して：\n"
            "$$\\text{J} = 1, \\quad \\text{K} = 4, \\quad \\text{L} = 2 \\implies \\text{JKL} = 142$$\n\n"
            "**(2) 面積和 $S(a)$ の立式**\n"
            "$0 < a < 1$ より、$a - 1 < 0$ かつ $a > 0$ である。\n"
            "- $x < 0$ の区間 $[a - 1, 0]$ では $y = xe^{2x} \\le 0$ であるため、面積は：\n"
            "  $$S_1 = -\\int_{a-1}^0 xe^{2x} dx = -[F(0) - F(a-1)] = F(a-1) - F(0)$$\n"
            "- $x \\ge 0$ の区間 $[0, a]$ では $y = xe^{2x} \\ge 0$ であるため、面積は：\n"
            "  $$S_2 = \\int_0^a xe^{2x} dx = F(a) - F(0)$$\n"
            "したがって：\n"
            "$$S(a) = S_1 + S_2 = F(a-1) + F(a) - 2F(0)$$\n"
            "$F(0) = \\frac{1}{4}(2 \\cdot 0 - 1)e^0 = -\\frac{1}{4}$ であるから、$-2F(0) = \\frac{1}{2} = \\frac{2}{4}$。\n"
            "$$S(a) = \\frac{1}{4}\\left[ (2(a-1) - 1)e^{2(a-1)} + (2a - 1)e^{2a} + 2 \\right]$$\n"
            "$$= \\frac{1}{4}\\left\\{ 2 + (2a - 3)e^{2(a-1)} + (2a - 1)e^{2a} \\right\\}$$\n"
            "与式 $\\frac{\\text{M}}{\\text{N}}\\{ \\text{O} + (\\text{P}a - \\text{Q})e^{2(a-1)} + (\\text{R}a - 1)e^{2a} \\}$ と比較して：\n"
            "$$\\text{M} = 1, \\quad \\text{N} = 4, \\quad \\text{O} = 2, \\quad \\text{P} = 2, \\quad \\text{Q} = 3, \\quad \\text{R} = 2 \\implies \\text{MNOPQR} = 142232$$\n\n"
            "**(3) $S(a)$ の最小化**\n"
            "微積分学の基本定理より、$S(a) = -\\int_{a-1}^0 xe^{2x} dx + \\int_0^a xe^{2x} dx$ を $a$ で微分すると：\n"
            "$$S'(a) = -\\left(- (a-1)e^{2(a-1)}\\right) + ae^{2a} = (a - 1)e^{2(a-1)} + ae^{2a}$$\n"
            "与式 $(a - \\text{S})e^{2(a-1)} + ae^{2a}$ と比較して：\n"
            "$$\\text{S} = 1$$\n"
            "$S'(a) = 0$ とおくと：\n"
            "$$ae^{2a} = -(a - 1)e^{2(a-1)} = (1 - a)e^{2a - 2} = (1 - a)e^{2a}e^{-2}$$\n"
            "$e^{2a} > 0$ で両辺を割ると：\n"
            "$$a = (1 - a)e^{-2} \\implies a e^2 = 1 - a \\implies a(e^2 + 1) = 1$$\n"
            "$$a = \\frac{1}{e^2 + 1}$$\n"
            "与式 $a = \\frac{\\text{T}}{e^2 + \\text{U}}$ と比較して：\n"
            "$$\\text{T} = 1, \\quad \\text{U} = 1 \\implies \\text{TU} = 11$$\n"
            "これは $0 < \\frac{1}{e^2 + 1} < 1$ を満たし、この点で $S(a)$ は最小となる。\n\n"
            "**【考査考点】**\n"
            "- 部分積分法による指数関数と多項式の積の積分。\n"
            "- 積分区間の上端・下端が変数である関数の微分法（ライプニッツの規則）。\n"
            "- 面積最小化問題における極値の導出。"
        )
    }
]

def main():
    work_dir = Path("work/2013-2-math-c2")
    work_dir.mkdir(parents=True, exist_ok=True)
    docs_dir = Path("docs/explanations")
    docs_dir.mkdir(parents=True, exist_ok=True)

    json_path = work_dir / "explanations.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(math_c2_questions, f, ensure_ascii=False, indent=2)
    print(f"Generated {json_path} ({len(math_c2_questions)} questions)")

    md_path = docs_dir / "2013-2-math-c2-solutions.md"
    lines = [
        "# 2013-2 EJU 数学 コース2 詳解・完全解説\n",
        "> 本ドキュメントは 2013年度第2回 EJU（日本留学試験）数学コース2に対する公式正解準拠の完全詳解である。\n",
        "---\n"
    ]

    for item in math_c2_questions:
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

