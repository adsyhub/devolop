#!/usr/bin/env python3
"""Generate comprehensive pedagogical explanations for 2014-2 EJU Math Course 1 (8 items)."""

import json
from pathlib import Path

math_c1_questions = [
    {
        "q_num": "I_1",
        "localKey": "math-q-I_1",
        "answer_ref": "I:1",
        "answer": {
            "A": "3",
            "BC": "45",
            "DEFG": "4410",
            "H": "2",
            "IJ": "-4",
            "K": "3"
        },
        "title": "数学 コース1 第I問 [1]：2次関数の頂点・最小値と連立方程式の重解条件",
        "points": [
            "平方完成による2次関数の最小値の決定",
            "2つの放物線の交点方程式と接合条件（判別式 $D=0$）",
            "正の実数条件 $a>0$ に基づく係数と接点 $x$ の一意決定"
        ],
        "solution": (
            "**【題目大意】**\n"
            "$a, b$ は実数であり、$a > 0$ とする。2つの2次関数\n"
            "$$f(x) = 2x^2 - 4x + 5, \\quad g(x) = x^2 + ax + b$$\n"
            "を考える。$g(x)$ が次の2つの条件を満たすとき、$a, b$ の値を求める。\n"
            "(i) $g(x)$ の最小値は $f(x)$ の最小値より $8$ だけ小さい\n"
            "(ii) $f(x) = g(x)$ を満たす $x$ がただ1つ存在する\n\n"
            "**【公式正解】**\n"
            "$\\text{A} = 3$\n"
            "$\\text{BC} = 45$ （$b = \\frac{a^2}{4} - 5$）\n"
            "$\\text{DEFG} = 4410$ （$x^2 - (a + 4)x - \\frac{a^2}{4} + 10 = 0$）\n"
            "$\\text{H} = 2$\n"
            "$\\text{IJ} = -4$\n"
            "$\\text{K} = 3$\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "**(1) $f(x)$ と $g(x)$ の最小値と条件 (i)**\n"
            "$f(x)$ を平方完成すると：\n"
            "$$f(x) = 2(x^2 - 2x) + 5 = 2(x - 1)^2 + 3$$\n"
            "したがって、$f(x)$ の最小値は **3** である（$\\text{A} = 3$）。\n\n"
            "$g(x)$ を平方完成すると：\n"
            "$$g(x) = \\left(x + \\frac{a}{2}\\right)^2 + b - \\frac{a^2}{4}$$\n"
            "したがって、$g(x)$ の最小値は $b - \\frac{a^2}{4}$ である。\n"
            "条件 (i)「$g(x)$ の最小値は $f(x)$ の最小値より8だけ小さい」より：\n"
            "$$b - \\frac{a^2}{4} = 3 - 8 = -5 \\implies b = \\frac{a^2}{4} - 5$$\n"
            "これより、$b = \\frac{a^2}{\\text{B}} - \\text{C}$ の空欄は $\\text{BC} = 45$ である。\n\n"
            "**(2) 交点方程式と条件 (ii)**\n"
            "$f(x) = g(x)$ を満たす $x$ を求める方程式は：\n"
            "$$2x^2 - 4x + 5 = x^2 + ax + b \\iff x^2 - (a + 4)x + (5 - b) = 0$$\n"
            "ここに $b = \\frac{a^2}{4} - 5$ を代入すると、定数項は：\n"
            "$$5 - b = 5 - \\left(\\frac{a^2}{4} - 5\\right) = -\\frac{a^2}{4} + 10$$\n"
            "よって、方程式は：\n"
            "$$x^2 - (a + 4)x - \\frac{a^2}{4} + 10 = 0$$\n"
            "となり、$\\text{D} = 4$、$\\text{E} = 4$、$\\text{FG} = 10$（合わせて $\\text{DEFG} = 4410$）を得る。\n\n"
            "条件 (ii)「解がただ1つ存在する」より、この2次方程式の判別式 $D_0$ は $0$ でなければならない：\n"
            "$$D_0 = [-(a + 4)]^2 - 4 \\cdot 1 \\cdot \\left(-\\frac{a^2}{4} + 10\\right) = 0$$\n"
            "$$(a^2 + 8a + 16) + a^2 - 40 = 0$$\n"
            "$$2a^2 + 8a - 24 = 0 \\iff a^2 + 4a - 12 = 0$$\n"
            "$$(a + 6)(a - 2) = 0$$\n"
            "$a > 0$ であるから：\n"
            "$$a = 2 \\quad (\\text{H} = 2)$$\n"
            "このとき、$b$ の値は：\n"
            "$$b = \\frac{2^2}{4} - 5 = 1 - 5 = -4 \\quad (\\text{IJ} = -4)$$\n"
            "また、$a = 2$ のときの方程式は：\n"
            "$$x^2 - 6x + 9 = 0 \\iff (x - 3)^2 = 0$$\n"
            "より、解は重解 $x = 3$（$\\text{K} = 3$）である。\n\n"
            "**【考査考点】**\n"
            "- 2次関数の標準形への変形（平方完成）と頂点の座標・最小値の決定。\n"
            "- 2つの放物線の共有点と2次方程式の判別式（重解条件 $D=0$）。"
        )
    },
    {
        "q_num": "I_2",
        "localKey": "math-q-I_2",
        "answer_ref": "I:2",
        "answer": {
            "L": "2",
            "M": "1",
            "N": "3",
            "O": "0",
            "PQ": "92",
            "RS": "67"
        },
        "title": "数学 コース1 第I問 [2]：集合と命題（必要十分条件）およびド・モルガンの法則による要素数計算",
        "points": [
            "倍数集合における包含関係と命題の必要条件・十分条件の判定",
            "ド・モルガンの法則：$\\overline{A} \\cup \\overline{B} = \\overline{A \\cap B}$ および $\\overline{A} \\cap \\overline{B} = \\overline{A \\cup B}$",
            "包含と排除の原理による補集合の要素数 $|\\overline{A} \\cap C|$ 等の計算"
        ],
        "solution": (
            "**【題目大意】**\n"
            "自然数の部分集合 $A = \\{4m \\mid m \\in \\mathbb{N}\\}$（4の倍数集合）、$B = \\{6m \\mid m \\in \\mathbb{N}\\}$（6の倍数集合）を考える。\n"
            "(1) 自然数 $n$ に対する各命題の必要・十分条件を判定する。\n"
            "(2) $C = \\{1, 2, \\dots, 100\\}$ に対し、$(\\overline{A} \\cup \\overline{B}) \\cap C$ および $\\overline{A} \\cap \\overline{B} \\cap C$ の要素の個数を求める。\n\n"
            "**【公式正解】**\n"
            "$\\text{L} = 2$ （十分条件であるが，必要条件ではない）\n"
            "$\\text{M} = 1$ （必要条件であるが，十分条件ではない）\n"
            "$\\text{N} = 3$ （必要条件でも十分条件でもない）\n"
            "$\\text{O} = 0$ （必要十分条件である）\n"
            "$\\text{PQ} = 92$\n"
            "$\\text{RS} = 67$\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "**(1) 必要・十分条件の判定**\n"
            "- (i) $n \\in A$（$n$ は4の倍数） $\\implies$ $n$ は2で割り切れる（真）。一方、$n$ が2で割り切れる（例：$n=2$） $\\implies$ $n \\in A$（偽）。よって、十分条件であるが，必要条件ではない（$\\text{L} = 2$）。\n"
            "- (ii) $n \\in B$（$n$ は6の倍数） $\\Longleftarrow$ $n$ が24で割り切れる（真）。一方、$n \\in B$（例：$n=6$） $\\implies$ $n$ が24で割り切れる（偽）。よって、必要条件であるが，十分条件ではない（$\\text{M} = 1$）。\n"
            "- (iii) $n \\in A \\cup B$（$n$ は4の倍数または6の倍数）。$n=4 \\in A \\cup B$ は3で割り切れない（十分条件ではない）。また、$n=3$ は3で割り切れるが $A \\cup B$ に属さない（必要条件ではない）。よって、必要条件でも十分条件でもない（$\\text{N} = 3$）。\n"
            "- (iv) $n \\in A \\cap B$ は「$n$ は4の倍数かつ6の倍数」であり、$\\text{lcm}(4, 6) = 12$ より「$n$ は12の倍数」と同値である。よって、必要十分条件である（$\\text{O} = 0$）。\n\n"
            "**(2) 集合の要素の個数計算**\n"
            "$C = \\{1, 2, \\dots, 100\\}$ において、要素の総数は $|C| = 100$ である。\n"
            "- $|A \\cap C| = \\lfloor 100 / 4 \\rfloor = 25$\n"
            "- $|B \\cap C| = \\lfloor 100 / 6 \\rfloor = 16$\n"
            "- $|A \\cap B \\cap C| = \\lfloor 100 / 12 \\rfloor = 8$\n\n"
            "ド・モルガンの法則より：\n"
            "$$\\overline{A} \\cup \\overline{B} = \\overline{A \\cap B}$$\n"
            "したがって：\n"
            "$$|(\\overline{A} \\cup \\overline{B}) \\cap C| = |C| - |(A \\cap B) \\cap C| = 100 - 8 = 92 \\quad (\\text{PQ} = 92)$$\n\n"
            "また：\n"
            "$$\\overline{A} \\cap \\overline{B} = \\overline{A \\cup B}$$\n"
            "包除原理より：\n"
            "$$|(A \\cup B) \\cap C| = |A \\cap C| + |B \\cap C| - |A \\cap B \\cap C| = 25 + 16 - 8 = 33$$\n"
            "したがって：\n"
            "$$|(\\overline{A} \\cap \\overline{B}) \\cap C| = |C| - |(A \\cup B) \\cap C| = 100 - 33 = 67 \\quad (\\text{RS} = 67)$$\n\n"
            "**【考査考点】**\n"
            "- 命題と論理（必要条件・十分条件・必要十分条件）の正確な識別。\n"
            "- 集合の演算（和集合・共通部分・補集合）とド・モルガンの法則。\n"
            "- 有限集合の要素の個数の計算（ガウス記号による倍数カウントと包除原理）。"
        )
    },
    {
        "q_num": "II_1",
        "localKey": "math-q-II_1",
        "answer_ref": "II:1",
        "answer": {
            "ABC": "720",
            "DEF": "120",
            "GHI": "360",
            "J": "6",
            "KL": "24",
            "MNO": "288"
        },
        "title": "数学 コース1 第II問 [1]：順列・組み合わせ（同じものを含む順列と隣り合わない配置）",
        "points": [
            "同じ文字を含む単語 POSITION の文字構成（P:1, O:2, S:1, I:2, T:1, N:1）の把握",
            "隣り合う条件（ブロック化法）と端に位置する条件の順列計算",
            "隣り合わない条件（挿入法・すきまへの配置）と端の条件の組み合わせ"
        ],
        "solution": (
            "**【題目大意】**\n"
            "単語 `POSITION` を構成する8文字（P, O, S, I, T, I, O, N：Iが2個、Oが2個、P, S, T, Nが各1個）を横一列に並べ替える。\n"
            "(1) 2つのIが隣り合い、2つのOも隣り合う並べ方。\n"
            "(2) 2つのIが両端に位置し、2つのOが隣り合う並べ方。\n"
            "(3) 2つのIが両端に位置する並べ方。\n"
            "(4) 8文字のうち、どちらかの端にはIかOが位置し、N, P, S, Tのどの2文字も隣り合わない並べ方。\n\n"
            "**【公式正解】**\n"
            "$\\text{ABC} = 720$\n"
            "$\\text{DEF} = 120$\n"
            "$\\text{GHI} = 360$\n"
            "$\\text{J} = 6$\n"
            "$\\text{KL} = 24$\n"
            "$\\text{MNO} = 288$\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "8文字の内訳は、Iが2個、Oが2個、P, S, T, Nが各1個である。\n\n"
            "**(1) 2つのIが隣り合い、2つのOも隣り合う並べ方**\n"
            "`II` を1つの塊、`OO` を1つの塊とみなすと、並べる対象は [II], [OO], P, S, T, N の6個の異なる要素となる。\n"
            "これらを一列に並べる並べ方は：\n"
            "$$6! = 720 \\text{ 通り} \\quad (\\text{ABC} = 720)$$\n\n"
            "**(2) 2つのIが両端に位置し、2つのOが隣り合う並べ方**\n"
            "配置は `I _ _ _ _ _ _ I` である（2つのIは同種なので両端の配置は1通り）。\n"
            "中間の6箇所に O, O, P, S, T, N を配置する。2つのOが隣り合うため、`OO` を1つの塊とみなすと、[OO], P, S, T, N の5個の異なる要素を並べることになる：\n"
            "$$5! = 120 \\text{ 通り} \\quad (\\text{DEF} = 120)$$\n\n"
            "**(3) 2つのIが両端に位置する並べ方**\n"
            "中間の6箇所に O, O, P, S, T, N（6文字、うちOが2個）を自由に並べる：\n"
            "$$\\frac{6!}{2!} = \\frac{720}{2} = 360 \\text{ 通り} \\quad (\\text{GHI} = 360)$$\n\n"
            "**(4) 端にIまたはOがあり、N, P, S, Tのどの2つも隣り合わない並べ方**\n"
            "- I, I, O, O の4文字を並べる並べ方は、同じものを含む順列より：\n"
            "  $$J = \\frac{4!}{2!2!} = \\frac{24}{4} = 6 \\text{ 通り} \\quad (\\text{J} = 6)$$\n"
            "- N, P, S, T の4文字を並べる並べ方は：\n"
            "  $$KL = 4! = 24 \\text{ 通り} \\quad (\\text{KL} = 24)$$\n"
            "- 4文字の母音群（I, I, O, O）を並べると、その両端および間に計 5 つの「すきま」ができる：\n"
            "  $$\\underline{\\quad 1 \\quad} \\text{ X } \\underline{\\quad 2 \\quad} \\text{ X } \\underline{\\quad 3 \\quad} \\text{ X } \\underline{\\quad 4 \\quad} \\text{ X } \\underline{\\quad 5 \\quad}$$\n"
            "  子音4文字（N, P, S, T）がどの2つも隣り合わないためには、この5つのすきまから4箇所を選んで各1文字ずつ配置すればよい。\n"
            "  すきまの選び方は全部で $\\binom{5}{4} = 5$ 通りある。\n"
            "  ここで、「どちらかの端にはIかOが位置する」という条件は、「両端がともに子音（すきま1とすきま5の両方に子音が入る）ではない」ということである。\n"
            "  両端（すきま1と5）に子音が配置される選び方は、残りの3つのすきま（2, 3, 4）から2箇所を選ぶ $\\binom{3}{2} = 3$ 通りである。\n"
            "  したがって、条件を満たす（少なくとも一端がIまたはOとなる）すきまの選び方は：\n"
            "  $$5 - 3 = 2 \\text{ 通り}$$\n"
            "  （※すきま1のみを選ぶ場合が $\\binom{3}{3}=1$ 通り、すきま5のみを選ぶ場合が $\\binom{3}{3}=1$ 通りで計2通りと直接数えてもよい）。\n"
            "- よって、全体の並べ方は：\n"
            "  $$(\\text{I, I, O, O の並べ方}) \\times (\\text{すきまの選び方}) \\times (\\text{N, P, S, T の並べ方})$$\n"
            "  $$= 6 \\times 2 \\times 24 = 288 \\text{ 通り} \\quad (\\text{MNO} = 288)$$\n\n"
            "**【考査考点】**\n"
            "- 同じものを含む順列の計算公式 $\\frac{n!}{p!q!}$。\n"
            "- 隣り合う条件における「要素のブロック化（束ねる手法）」の適用。\n"
            "- 隣り合わない条件における「すきま挿入法」と余事象・端条件の複合処理。"
        )
    },
    {
        "q_num": "II_2",
        "localKey": "math-q-II_2",
        "answer_ref": "II:2",
        "answer": {
            "PQR": "247",
            "STU": "115",
            "V": "4",
            "W": "1",
            "X": "7",
            "YZ": "52"
        },
        "title": "数学 コース1 第II問 [2]：2変数関数の関係式と整数条件下の最大値・最小値",
        "points": [
            "2次関数 $y = f(x)$ の平方完成と頂点の決定",
            "連立不等式による $x$ の存在範囲の導出（2次不等式の解法）",
            "整数 $x$ の離散値に対する $y$ の値の評価と最大値・最小値の特定"
        ],
        "solution": (
            "**【題目大意】**\n"
            "整数 $x$ と実数 $y$ が等式 $2(y+1) = x(8-x)$ $\\textcircled{1}$ と不等式 $5x - 4y + 1 \\le 0$ $\\textcircled{2}$ を同時に満たすとき、$y$ の最大値 $M$ と最小値 $m$ を求める。\n\n"
            "**【公式正解】**\n"
            "$\\text{PQR} = 247$ （$y = -\\frac{1}{2}(x - 4)^2 + 7$）\n"
            "$\\text{STU} = 115$ （$2x^2 - 11x + 5 \\le 0$）\n"
            "$\\text{V} = 4$\n"
            "$\\text{W} = 1$\n"
            "$\\text{X} = 7$\n"
            "$\\text{YZ} = 52$ （$m = \\frac{5}{2}$）\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "**(1) $y$ を $x$ の2次式として表す**\n"
            "等式 $\\textcircled{1}$ を変形すると：\n"
            "$$2y + 2 = 8x - x^2 \\iff 2y = -(x^2 - 8x) - 2$$\n"
            "両辺を2で割り、平方完成すると：\n"
            "$$y = -\\frac{1}{2}(x^2 - 8x) - 1 = -\\frac{1}{2}[(x - 4)^2 - 16] - 1 = -\\frac{1}{2}(x - 4)^2 + 8 - 1$$\n"
            "$$y = -\\frac{1}{2}(x - 4)^2 + 7$$\n"
            "したがって、$y = -\\frac{1}{\\text{P}}(x - \\text{Q})^2 + \\text{R}$ より、$\\text{PQR} = 247$ である。\n\n"
            "**(2) $x$ に関する不等式の導出**\n"
            "不等式 $\\textcircled{2}$ より、$4y \\ge 5x + 1$ である。\n"
            "$\\textcircled{1}$ 式の両辺を2倍すると $4(y+1) = 2x(8-x) \\iff 4y = 16x - 2x^2 - 4$ であるから、これを不等式に代入する：\n"
            "$$16x - 2x^2 - 4 \\ge 5x + 1$$\n"
            "移項して整理すると：\n"
            "$$2x^2 - 11x + 5 \\le 0$$\n"
            "したがって、$2x^2 - \\text{ST} x + \\text{U} \\le 0$ より、$\\text{STU} = 115$ である。\n\n"
            "**(3) 整数 $x$ の範囲と $y$ の最大値・最小値**\n"
            "2次不等式を因数分解すると：\n"
            "$$(2x - 1)(x - 5) \\le 0 \\iff \\frac{1}{2} \\le x \\le 5$$\n"
            "$x$ は**整数**であるから、とり得る $x$ の値は：\n"
            "$$x \\in \\{1, 2, 3, 4, 5\\}$$\n\n"
            "$y = -\\frac{1}{2}(x - 4)^2 + 7$ は $x = 4$ で上に凸の放物線であるから：\n"
            "- $x = 4$ のとき、$y$ は最大値をとる：\n"
            "  $$M = y(4) = 7 \\quad (\\text{V} = 4, \\text{X} = 7)$$\n"
            "- 頂点 $x = 4$ から最も離れた整数値は $x = 1$（距離 3）である。\n"
            "  $x = 1$ のとき：\n"
            "  $$y(1) = -\\frac{1}{2}(1 - 4)^2 + 7 = -\\frac{9}{2} + 7 = \\frac{5}{2}$$\n"
            "  （なお、$x=5$ では $y(5) = 13/2$、$x=2$ では $y(2)=5$ である）。\n"
            "  したがって、$x = 1$ のとき $y$ は最小値 $m = \\frac{5}{2}$ をとる（$\\text{W} = 1, \\text{YZ} = 52$）。\n\n"
            "**【考査考点】**\n"
            "- 2変数の消去による1変数2次不等式の立式と因数分解。\n"
            "- 実数条件と整数（離散値）条件の区別、および定義域の端点・頂点における評価。"
        )
    },
    {
        "q_num": "III_1",
        "localKey": "math-q-III_1",
        "answer_ref": "III:1",
        "answer": {
            "A": "4",
            "B": "0"
        },
        "title": "数学 コース1 第III問 (1)：連立2次不等式の共通解と補集合の領域判定",
        "points": [
            "2次不等式 $x^2+3x-18<0$ および $x^2-2x-8>0$ の因数分解と解法",
            "数直線を用いた連立不等式の共通範囲の決定",
            "否定（どちらも満たさない）領域の境界値を含む範囲の判定"
        ],
        "solution": (
            "**【題目大意】**\n"
            "2次不等式 $x^2 + 3x - 18 < 0$ $\\textcircled{1}$ と $x^2 - 2x - 8 > 0$ $\\textcircled{2}$ について：\n"
            "(1) $\\textcircled{1}$ と $\\textcircled{2}$ の両方を満たす $x$ の範囲 A、およびどちらも満たさない $x$ の範囲 B を選択肢 $\\textcircled{0} \\sim \\textcircled{5}$ から選ぶ。\n\n"
            "**【公式正解】**\n"
            "$\\text{A} = 4$ （$-6 < x < -2$）\n"
            "$\\text{B} = 0$ （$3 \\le x \\le 4$）\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "**(1) 各不等式の解**\n"
            "- 不等式 $\\textcircled{1}$：\n"
            "  $$x^2 + 3x - 18 < 0 \\iff (x + 6)(x - 3) < 0 \\iff -6 < x < 3$$\n"
            "- 不等式 $\\textcircled{2}$：\n"
            "  $$x^2 - 2x - 8 > 0 \\iff (x - 4)(x + 2) > 0 \\iff x < -2 \\text{ または } x > 4$$\n\n"
            "**(2) 両方を満たす範囲 A**\n"
            "$$(-6 < x < 3) \\cap (x < -2 \\text{ または } x > 4)$$\n"
            "数直線上で共通部分を求めると：\n"
            "$$-6 < x < -2$$\n"
            "選択肢 $\\textcircled{4}$ が $-6 < x < -2$ に該当するため、$\\text{A} = 4$ である。\n\n"
            "**(3) どちらの不等式も満たさない範囲 B**\n"
            "「$\\textcircled{1}$ を満たさない」かつ「$\\textcircled{2}$ を満たさない」範囲を求める。\n"
            "- $\\textcircled{1}$ の否定：$x \\le -6$ または $x \\ge 3$\n"
            "- $\\textcircled{2}$ の否定：$-2 \\le x \\le 4$\n"
            "両者の共通部分は：\n"
            "$$(x \\le -6 \\text{ または } x \\ge 3) \\cap (-2 \\le x \\le 4)$$\n"
            "$x \\le -6$ と $[-2, 4]$ に共通部分はない。一方、$x \\ge 3$ と $[-2, 4]$ の共通部分は：\n"
            "$$3 \\le x \\le 4$$\n"
            "選択肢 $\\textcircled{0}$ が $3 \\le x \\le 4$ に該当するため、$\\text{B} = 0$ である。\n\n"
            "**【考査考点】**\n"
            "- 2次不等式の因数分解による解法。\n"
            "- 数直線上での共通集合（かつ）およびド・モルガンの法則に基づく否定領域の視覚的・論理的処理。"
        )
    },
    {
        "q_num": "III_2",
        "localKey": "math-q-III_2",
        "answer_ref": "III:2",
        "answer": {
            "C": "2",
            "D": "4"
        },
        "title": "数学 コース1 第III問 (2)：媒介変数を含む2次不等式の和集合条件とパラメータ範囲の導出",
        "points": [
            "開区間 $(-6, 3)$ と 2次不等式 $x^2+ax+b<0$ の解区間 $(\\alpha, \\beta)$ の和集合解析",
            "右端点 $\\beta = 7$ から得られる等式 $b = -7a - 49$ の決定",
            "連結区間 $(-6, 7)$ を形成するための左端点 $\\alpha$ の存在範囲（$-6 \\le \\alpha \\le 3$）の評価"
        ],
        "solution": (
            "**【題目大意】**\n"
            "不等式 $\\textcircled{1}$ $x^2 + 3x - 18 < 0$ と $\\textcircled{3}$ $x^2 + ax + b < 0$ の少なくとも一方を満たす $x$ の範囲（和集合）が $-6 < x < 7$ となるとき、$a, b$ が満たす等式 C および $a$ が満たす不等式 D を選択肢から選ぶ。\n\n"
            "**【公式正解】**\n"
            "$\\text{C} = 2$ （$b = -7a - 49$）\n"
            "$\\text{D} = 4$ （$-10 < a \\le -1$）\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "不等式 $\\textcircled{1}$ の解は $-6 < x < 3$ である。\n"
            "不等式 $\\textcircled{3}$ $x^2 + ax + b < 0$ の解は、2次方程式 $x^2 + ax + b = 0$ の相異なる2実数解を $\\alpha < \\beta$ とすると、開区間 $(\\alpha, \\beta)$ である。\n"
            "問題の条件は、2つの区間の和集合が：\n"
            "$$(-6, 3) \\cup (\\alpha, \\beta) = (-6, 7)$$\n"
            "となることである。\n\n"
            "**(1) 等式 C の決定**\n"
            "和集合の右端が $7$ であるから、区間 $(\\alpha, \\beta)$ の右端点は必ず $\\beta = 7$ でなければならない。\n"
            "$x = 7$ は $x^2 + ax + b = 0$ の解であるから：\n"
            "$$7^2 + 7a + b = 0 \\iff 49 + 7a + b = 0 \\iff b = -7a - 49$$\n"
            "これは選択肢 $\\textcircled{2}$ であるため、$\\text{C} = 2$ である。\n\n"
            "**(2) 不等式 D の決定**\n"
            "$b = -7a - 49$ を代入すると、$\\textcircled{3}$ の左辺は：\n"
            "$$x^2 + ax - 7a - 49 = (x - 7)(x + a + 7) < 0$$\n"
            "$\\beta = 7$ より、もう一方の解は $\\alpha = -(a + 7)$ である（$\\alpha < 7 \\iff a > -14$）。\n"
            "2つの区間 $(-6, 3)$ と $(\\alpha, 7)$ の和集合が $(-6, 7)$ という1つの連結な開区間となるための条件は：\n"
            "1. 和集合の左端が $-6$ であることより、$\\alpha$ は $-6$ より小さくなってはならない（もし $\\alpha < -6$ なら和集合の左端が $\\alpha$ に拡張されてしまう）：\n"
            "   $$\\alpha \\ge -6 \\iff -(a + 7) \\ge -6 \\iff a + 7 \\le 6 \\iff a \\le -1$$\n"
            "2. 区間 $(-6, 3)$ と $(\\alpha, 7)$ の間に「すきま（切れ目）」が生じてはならない。\n"
            "   もし $\\alpha > 3$ であれば、$(3, \\alpha]$ の部分が解に含まれず区間が分断されてしまう。また $\\alpha = 3$ の場合も $x = 3$ がどちらにも含まれず穴が空いてしまう。したがって $\\alpha < 3$ でなければならない：\n"
            "   $$\\alpha < 3 \\iff -(a + 7) < 3 \\iff a + 7 > -3 \\iff a > -10$$\n"
            "以上を合わせると、実数 $a$ の満たすべき条件は：\n"
            "$$-10 < a \\le -1$$\n"
            "これは選択肢 $\\textcircled{4}$ に該当するため、$\\text{D} = 4$ である。\n\n"
            "**【考査考点】**\n"
            "- パラメータを含む2次関数の因数分解と解の配置。\n"
            "- 複数の開区間の和集合が連続した1つの区間をなすための端点の包含・接続条件。"
        )
    },
    {
        "q_num": "IV_1",
        "localKey": "math-q-IV_1",
        "answer_ref": "IV:1",
        "answer": {
            "ABC": "843",
            "DE": "88",
            "FG": "90",
            "HI": "22"
        },
        "title": "数学 コース1 第IV問 (1)：円に内接する四角形の余弦定理と対角線の長さ・対角の決定",
        "points": [
            "円に内接する四角形の対角の和の性質（$\\angle BCD = 180^\\circ - \\theta$）",
            "余弦定理の2通りの適用（$\\triangle ABD$ と $\\triangle BCD$）",
            "対角線の長さ $BD$ および内角 $\\theta$ の決定"
        ],
        "solution": (
            "**【題目大意】**\n"
            "円に内接する四角形 $ABCD$ において、$AB = \\sqrt{2}$, $BC = CD = 2$, $DA = \\sqrt{6}$ とする。\n"
            "$\\angle BAD = \\theta$ とおくとき、余弦定理を用いて $BD^2$ を2通りに表し、$\\theta$ と $BD$ の値を求める。\n\n"
            "**【公式正解】**\n"
            "$\\text{ABC} = 843$ （$BD^2 = 8 - 4\\sqrt{3}\\cos\\theta$）\n"
            "$\\text{DE} = 88$ （$BD^2 = 8 + 8\\cos\\theta$）\n"
            "$\\text{FG} = 90$ （$\\theta = 90^\\circ$）\n"
            "$\\text{HI} = 22$ （$BD = 2\\sqrt{2}$）\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "**(1) $\\triangle ABD$ における余弦定理**\n"
            "$\\triangle ABD$ において、$AB = \\sqrt{2}$, $AD = \\sqrt{6}$, $\\angle BAD = \\theta$ であるから：\n"
            "$$BD^2 = AB^2 + AD^2 - 2 \\cdot AB \\cdot AD \\cos\\theta$$\n"
            "$$BD^2 = (\\sqrt{2})^2 + (\\sqrt{6})^2 - 2 \\cdot \\sqrt{2} \\cdot \\sqrt{6} \\cos\\theta = 2 + 6 - 2\\sqrt{12}\\cos\\theta = 8 - 4\\sqrt{3}\\cos\\theta$$\n"
            "したがって、$BD^2 = \\text{A} - \\text{B}\\sqrt{\\text{C}}\\cos\\theta$ より、$\\text{ABC} = 843$ である。\n\n"
            "**(2) $\\triangle BCD$ における余弦定理**\n"
            "四角形 $ABCD$ は円に内接するため、対角の和は $180^\\circ$ である：\n"
            "$$\\angle BCD = 180^\\circ - \\theta$$\n"
            "また $BC = 2, CD = 2$ であるから：\n"
            "$$BD^2 = BC^2 + CD^2 - 2 \\cdot BC \\cdot CD \\cos(180^\\circ - \\theta)$$\n"
            "$\\cos(180^\\circ - \\theta) = -\\cos\\theta$ であるので：\n"
            "$$BD^2 = 2^2 + 2^2 - 2 \\cdot 2 \\cdot 2 (-\\cos\\theta) = 8 + 8\\cos\\theta$$\n"
            "したがって、$BD^2 = \\text{D} + \\text{E}\\cos\\theta$ より、$\\text{DE} = 88$ である。\n\n"
            "**(3) $\\theta$ と $BD$ の決定**\n"
            "両式を等置すると：\n"
            "$$8 - 4\\sqrt{3}\\cos\\theta = 8 + 8\\cos\\theta$$\n"
            "$$(8 + 4\\sqrt{3})\\cos\\theta = 0$$\n"
            "$8 + 4\\sqrt{3} \\ne 0$ であるから、$\\cos\\theta = 0$ を得る。\n"
            "$0^\\circ < \\theta < 180^\\circ$ より：\n"
            "$$\\theta = 90^\\circ \\quad (\\text{FG} = 90)$$\n"
            "$\\cos\\theta = 0$ を代入すると：\n"
            "$$BD^2 = 8 \\implies BD = \\sqrt{8} = 2\\sqrt{2} \\quad (\\text{HI} = 22)$$\n\n"
            "**【考査考点】**\n"
            "- 円に内接する四角形の対角の性質（内角の和 $180^\\circ$ と三角関数の符号反転）。\n"
            "- 共通の対角線に対する余弦定理の立式と未知角の代数的消去。"
        )
    },
    {
        "q_num": "IV_2",
        "localKey": "math-q-IV_2",
        "answer_ref": "IV:2",
        "answer": {
            "JK": "45",
            "LM": "30",
            "NO": "13",
            "PQRS": "2314",
            "TUV": "223"
        },
        "title": "数学 コース1 第IV問 (2)(3)：正弦定理による角・線分の導出と方べきの定理・相似比による延長線の交点",
        "points": [
            "外接円の直径（$2R = BD$）に基づく正弦定理の適用",
            "加法定理を用いた $AC = 1 + \\sqrt{3}$ および $\\sin\\angle ADC$ の厳密計算",
            "円に内接する四角形の対辺の延長がなす相似三角形（$\\triangle EAB \\sim \\triangle ECD$）の幾何学的解法"
        ],
        "solution": (
            "**【題目大意】**\n"
            "前問の円に内接する四角形 $ABCD$（$\\angle BAD = 90^\\circ, BD = 2\\sqrt{2}$）において：\n"
            "(2) $\\angle BAC, \\angle BCA, AC$ および $\\sin\\angle ADC$ を求める。\n"
            "(3) 直線 $AD$ と直線 $BC$ の交点を $E$ とするとき、$EB$ の長さを求める。\n\n"
            "**【公式正解】**\n"
            "$\\text{JK} = 45$ （$\\angle BAC = 45^\\circ$）\n"
            "$\\text{LM} = 30$ （$\\angle BCA = 30^\\circ$）\n"
            "$\\text{NO} = 13$ （$AC = 1 + \\sqrt{3}$）\n"
            "$\\text{PQRS} = 2314$ （$\\sin\\angle ADC = \\frac{\\sqrt{2}(\\sqrt{3} + 1)}{4}$）\n"
            "$\\text{TUV} = 223$ （$EB = 2 + 2\\sqrt{3}$）\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "**(1) 外接円の半径と角の決定**\n"
            "$\\angle BAD = 90^\\circ$ より、$BD$ は外接円の直径である。\n"
            "したがって、外接円の半径 $R$ は：\n"
            "$$2R = BD = 2\\sqrt{2} \\implies R = \\sqrt{2}$$\n"
            "$\\triangle BCD$ において、$BC = CD = 2, BD = 2\\sqrt{2}$ より $BC^2 + CD^2 = BD^2$ が成り立ち、$\\triangle BCD$ は直角二等辺三角形である。よって $\\angle BDC = \\angle DBC = 45^\\circ$ である。\n\n"
            "次に、弦 $BC$ に対する円周角 $\\angle BAC$ は、正弦定理より：\n"
            "$$\\frac{BC}{\\sin\\angle BAC} = 2R \\implies \\sin\\angle BAC = \\frac{2}{2\\sqrt{2}} = \\frac{1}{\\sqrt{2}}$$\n"
            "弦 $AB$ に対する円周角 $\\angle BCA$ は：\n"
            "$$\\frac{AB}{\\sin\\angle BCA} = 2R \\implies \\sin\\angle BCA = \\frac{\\sqrt{2}}{2\\sqrt{2}} = \\frac{1}{2}$$\n"
            "図の配置より、$\\angle BAC = 45^\\circ$（$\\text{JK} = 45$）、$\\angle BCA = 30^\\circ$（$\\text{LM} = 30$）である。\n\n"
            "**(2) 線分 $AC$ の長さ**\n"
            "$\\triangle ABC$ の内角の和より：\n"
            "$$\\angle ABC = 180^\\circ - (45^\\circ + 30^\\circ) = 105^\\circ$$\n"
            "正弦定理より：\n"
            "$$AC = 2R \\sin 105^\\circ = 2\\sqrt{2} \\sin(45^\\circ + 60^\\circ)$$\n"
            "$$\\sin 105^\\circ = \\sin 45^\\circ \\cos 60^\\circ + \\cos 45^\\circ \\sin 60^\\circ = \\frac{\\sqrt{2}}{2} \\cdot \\frac{1}{2} + \\frac{\\sqrt{2}}{2} \\cdot \\frac{\\sqrt{3}}{2} = \\frac{\\sqrt{2} + \\sqrt{6}}{4}$$\n"
            "$$AC = 2\\sqrt{2} \\cdot \\frac{\\sqrt{2} + \\sqrt{6}}{4} = \\frac{4 + 2\\sqrt{12}}{4} = \\frac{4 + 4\\sqrt{3}}{4} = 1 + \\sqrt{3}$$\n"
            "したがって、$AC = \\text{N} + \\sqrt{\\text{O}}$ より、$\\text{NO} = 13$ である。\n\n"
            "**(3) $\\sin\\angle ADC$ の計算**\n"
            "直角三角形 $ABD$ において、$\\sin\\angle ADB = \\frac{AB}{BD} = \\frac{\\sqrt{2}}{2\\sqrt{2}} = \\frac{1}{2}$ より $\\angle ADB = 30^\\circ$ である。\n"
            "また直角二等辺三角形 $BCD$ より $\\angle BDC = 45^\\circ$ であるから：\n"
            "$$\\angle ADC = \\angle ADB + \\angle BDC = 30^\\circ + 45^\\circ = 75^\\circ$$\n"
            "$$\\sin\\angle ADC = \\sin 75^\\circ = \\frac{\\sqrt{6} + \\sqrt{2}}{4} = \\frac{\\sqrt{2}(\\sqrt{3} + 1)}{4}$$\n"
            "したがって、$\\sin\\angle ADC = \\frac{\\sqrt{\\text{P}}(\\sqrt{\\text{Q}} + \\text{R})}{\\text{S}}$ より、$\\text{PQRS} = 2314$ である。\n\n"
            "**(4) 交点 $E$ と $EB$ の長さ**\n"
            "四角形 $ABCD$ は円に内接するため、直線 $AD$ と直線 $BC$ の交点 $E$ に関して：\n"
            "$$\\triangle EAB \\sim \\triangle ECD$$\n"
            "相似比は対応する辺の比より：\n"
            "$$\\frac{CD}{AB} = \\frac{2}{\\sqrt{2}} = \\sqrt{2}$$\n"
            "したがって：\n"
            "$$\\frac{EC}{EA} = \\sqrt{2} \\implies EC = \\sqrt{2} EA$$\n"
            "$$\\frac{ED}{EB} = \\sqrt{2} \\implies ED = \\sqrt{2} EB$$\n"
            "線分の関係より、$EC = EB + BC = EB + 2$、$ED = EA + AD = EA + \\sqrt{6}$ である。\n"
            "第2式より $EA = \\sqrt{2} EB - \\sqrt{6}$。\n"
            "これを第1式 $EB + 2 = \\sqrt{2} EA$ に代入すると：\n"
            "$$EB + 2 = \\sqrt{2}(\\sqrt{2} EB - \\sqrt{6}) = 2 EB - 2\\sqrt{3}$$\n"
            "$$EB = 2 + 2\\sqrt{3}$$\n"
            "したがって、$EB = \\text{T} + \\text{U}\\sqrt{\\text{V}}$ より、$\\text{TUV} = 223$ である。\n\n"
            "**【考査考点】**\n"
            "- 正弦定理・余弦定理の総合的運用（外接円の直径と円周角の関係）。\n"
            "- 加法定理による $105^\\circ, 75^\\circ$ の三角比の厳密計算。\n"
            "- 円に内接する四角形の延長線が形成する相似三角形（方べきの定理）の幾何学的応用。"
        )
    }
]

def main():
    work_dir = Path("work/2014-2-math-c1")
    work_dir.mkdir(parents=True, exist_ok=True)
    docs_dir = Path("docs/explanations")
    docs_dir.mkdir(parents=True, exist_ok=True)

    json_path = work_dir / "explanations.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(math_c1_questions, f, ensure_ascii=False, indent=2)
    print(f"Generated {json_path} ({len(math_c1_questions)} questions)")

    md_path = docs_dir / "2014-2-math-c1-solutions.md"
    lines = [
        "# 2014-2 EJU 数学 コース1 詳解・完全解説\n",
        "> 本ドキュメントは 2014年度第2回 EJU（日本留学試験）数学コース1に対する公式正解準拠の完全詳解である。\n",
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

