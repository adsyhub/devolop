#!/usr/bin/env python3
"""Generate comprehensive pedagogical explanations for 2016-1 EJU Math Course 2 (8 questions)."""

import json
from pathlib import Path

math_c2_sections = [
    {
        "q_num": 1,
        "localKey": "math-q-I_1",
        "answer_ref": "MATH_C2:I_1",
        "answer": {
            "A": "4",
            "B": "2",
            "CDEF": "-241",
            "G": "1",
            "H": "3",
            "IJ": "18"
        },
        "title": "大問I 問1：2次関数の頂点軌跡・最大値および接線条件による値域",
        "points": [
            "2次関数の平方完成と頂点 $(p, q)$ の導出",
            "頂点の直線上の運動によるパラメータ消去と2次関数の最大値",
            "$x$ 軸との接点条件（頂点 $q = 0$）による不等式の導出"
        ],
        "solution": (
            "**【題目大意】**\n"
            "2次関数 $y = -\\frac{1}{8}x^2 + ax + b$ $\\textcircled{1}$ のグラフの頂点を $(p, q)$ とし、(1) 頂点が直線 $x + y = 1$ 上を動くときの $8a + b$ の最大値、および (2) グラフが $x$ 軸に接するときの $a + b$ のとり得る値の範囲を求める。\n\n"
            "**【公式正解】**\n"
            "- $\\text{A} = 4, \\text{B} = 2$ ($p = 4a, q = 2a^2 + b$)\n"
            "- $\\text{CDEF} = -241$ ($b = -2a^2 - 4a + 1$)\n"
            "- $\\text{G} = 1, \\text{H} = 3$ ($a = 1$ で最大値 3)\n"
            "- $\\text{IJ} = 18$ ($a + b \\leq \\frac{1}{8}$)\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "**(1) 頂点の座標の算出**\n"
            "関数 $\\textcircled{1}$ を平方完成する：\n"
            "$$y = -\\frac{1}{8}(x^2 - 8ax) + b = -\\frac{1}{8}(x - 4a)^2 + 2a^2 + b$$\n"
            "したがって、グラフの頂点の座標 $(p, q)$ は：\n"
            "$$p = 4a, \\quad q = 2a^2 + b$$\n"
            "よって、$\\text{A} = 4, \\text{B} = 2$ である。\n\n"
            "**(2) 頂点が直線 $x + y = 1$ 上にある条件と最大値**\n"
            "点 $(p, q)$ が直線 $x + y = 1$ 上にあるので、代入すると：\n"
            "$$4a + (2a^2 + b) = 1 \\implies b = -2a^2 - 4a + 1$$\n"
            "したがって、$\\text{CD} = -2, \\text{E} = 4, \\text{F} = 1$ (CDEF = -241) である。\n"
            "このとき、$8a + b$ を $a$ の式として表すと：\n"
            "$$8a + b = 8a + (-2a^2 - 4a + 1) = -2a^2 + 4a + 1$$\n"
            "これを平方完成すると：\n"
            "$$-2(a^2 - 2a) + 1 = -2(a - 1)^2 + 2 + 1 = -2(a - 1)^2 + 3$$\n"
            "したがって、$a = 1$ のとき最大値 3 をとる。\n"
            "よって、$\\text{G} = 1, \\text{H} = 3$ である。\n\n"
            "**(3) グラフが $x$ 軸に接する条件**\n"
            "放物線 $\\textcircled{1}$ が $x$ 軸に接するとき、頂点の $y$ 座標 $q$ は 0 であるから：\n"
            "$$2a^2 + b = 0 \\implies b = -2a^2$$\n"
            "このとき、$a + b$ は：\n"
            "$$a + b = a - 2a^2 = -2\\left(a^2 - \\frac{1}{2}a\\right) = -2\\left(a - \\frac{1}{4}\\right)^2 + \\frac{1}{8}$$\n"
            "したがって、$a + b$ は $a = \\frac{1}{4}$ で最大値 $\\frac{1}{8}$ をとる。\n"
            "よって、とり得る値の範囲は：\n"
            "$$a + b \\leq \\frac{1}{8}$$\n"
            "すなわち、$\\text{I} = 1, \\text{J} = 8$ (IJ = 18) である。\n\n"
            "**【考査考点】**\n"
            "- 2次関数の標準形への変形（平方完成）と頂点座標の特定。\n"
            "- 条件式を用いた多変数関数の1変数化と2次関数の最大値の計算。\n"
            "- 放物線が $x$ 軸に接する幾何学的条件（判別式 $D=0$ または頂点 $y=0$）の理解と活用。"
        )
    },
    {
        "q_num": 2,
        "localKey": "math-q-I_2",
        "answer_ref": "MATH_C2:I_2",
        "answer": {
            "KLM": "220",
            "N": "3",
            "O": "8",
            "PQ": "12",
            "R": "8",
            "STU": "200",
            "VW": "48"
        },
        "title": "大問I 問2：格子点上の3点による三角形形成の場合の数",
        "points": [
            "12個の点からの3点選択の組合せ数 $\\binom{12}{3}$",
            "共線点（一直線上に並ぶ点）による三角形非形成パターンの除外（包除原理）",
            "特定線分（底辺）上の2頂点指定条件下での三角形形成条件"
        ],
        "solution": (
            "**【題目大意】**\n"
            "座標平面上に $4 \\times 3$ の長方形状に並んだ12個の格子点 $(x, y)$ ($x \\in \\{1, 2, 3, 4\\}, y \\in \\{1, 2, 3\\}$) がある。これらから3個の点を選んで三角形を作る。全体の三角形の個数、および線分 $AB$ ($A(1, 1), B(4, 1)$) 上に2頂点をもつ三角形の個数を求める。\n\n"
            "**【公式正解】**\n"
            "- $\\text{KLM} = 220$ (選び出し総数 220 通り)\n"
            "- $\\text{N} = 3$ (4点を通る直線 3 本)\n"
            "- $\\text{O} = 8$ (3点を通る直線 8 本)\n"
            "- $\\text{PQ} = 12$ (4点直線上の非三角形 12 通り)\n"
            "- $\\text{R} = 8$ (3点直線上の非三角形 8 通り)\n"
            "- $\\text{STU} = 200$ (作られる三角形 200 個)\n"
            "- $\\text{VW} = 48$ (線分 $AB$ 上に2頂点をもつ三角形 48 個)\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "**(1) 12点から3点を選ぶ場合の数**\n"
            "12個の相異なる点から3個の点を選び出す組合せ数は：\n"
            "$$\\binom{12}{3} = \\frac{12 \\times 11 \\times 10}{3 \\times 2 \\times 1} = 220$$\n"
            "よって、$\\text{KLM} = 220$ 通りである。\n\n"
            "**(2) 3点以上が一直線上に並ぶ直線の本数**\n"
            "格子の配置は横4点、縦3点である。\n"
            "(i) 4点を通る直線：\n"
            "- 水平線 $y = 1, y = 2, y = 3$ の 3 本のみである。\n"
            "したがって、$\\text{N} = 3$ 本である。\n\n"
            "(ii) ちょうど3点を通る直線：\n"
            "- 垂直線 $x = 1, x = 2, x = 3, x = 4$ の 4 本。\n"
            "- 傾き 1 の対角線：$(1, 1)-(2, 2)-(3, 3)$ および $(2, 1)-(3, 2)-(4, 3)$ の 2 本。\n"
            "- 傾き -1 の対角線：$(1, 3)-(2, 2)-(3, 1)$ および $(2, 3)-(3, 2)-(4, 1)$ の 2 本。\n"
            "合計で $4 + 2 + 2 = 8$ 本ある。\n"
            "したがって、$\\text{O} = 8$ 本である。\n\n"
            "**(3) 三角形をなさない3点の組合せ数**\n"
            "同一直線上にある3点を選ぶと三角形にならない。\n"
            "- (i) 4点を通る直線 3 本から3点を選ぶ選び方は：\n"
            "$$3 \\times \\binom{4}{3} = 3 \\times 4 = 12 \\text{ 通り}$$\n"
            "よって、$\\text{PQ} = 12$ 通りである。\n\n"
            "- (ii) 3点を通る直線 8 本から3点を選ぶ選び方は：\n"
            "$$8 \\times \\binom{3}{3} = 8 \\times 1 = 8 \\text{ 通り}$$\n"
            "よって、$\\text{R} = 8$ 通りである。\n\n"
            "**(4) 作成できる三角形の総数**\n"
            "全体の3点の選び方から、共線となる組合せを引くと：\n"
            "$$220 - 12 - 8 = 200$$\n"
            "よって、三角形は全部で $\\text{STU} = 200$ 個できる。\n\n"
            "**(5) 線分 $AB$ 上に2つの頂点をもつ三角形の個数**\n"
            "線分 $AB$ は直線 $y = 1$ 上の 4 点 $(1, 1), (2, 1), (3, 1), (4, 1)$ を含む。\n"
            "この4点から2頂点を選ぶ組合せは：\n"
            "$$\\binom{4}{2} = \\frac{4 \\times 3}{2} = 6 \\text{ 通り}$$\n"
            "第3の頂点は、同一直線 $y = 1$ 上にない残りの点、すなわち $y = 2$ または $y = 3$ にある点から選べばよい。\n"
            "直線 $y = 1$ 上にない点は全部で $12 - 4 = 8$ 点ある。\n"
            "選ばれた2点は $y=1$ 上にあり、第3の点は $y \\neq 1$ 上にあるため、これら3点は決して同一直線上に並ばず、必ず三角形を形成する。\n"
            "したがって、求める三角形の個数は：\n"
            "$$6 \\times 8 = 48$$\n"
            "よって、$\\text{VW} = 48$ 個である。\n\n"
            "**【考査考点】**\n"
            "- 組合せの基本計算 $\\binom{n}{r}$。\n"
            "- 平面格子点における同一直線（水平、垂直、斜め対角線）の網羅的分類と重複のない数え上げ。\n"
            "- 条件を満たす三角形の形成条件の分析。"
        )
    },
    {
        "q_num": 3,
        "localKey": "math-q-II_1",
        "answer_ref": "MATH_C2:II_1",
        "answer": {
            "AB": "-6",
            "CD": "32",
            "EFGH": "4639",
            "IJK": "172"
        },
        "title": "大問II 問1：余弦定理・ベクトルの内積と区分求積法（リーマン和の極限）",
        "points": [
            "余弦定理による $\\cos \\theta$ の導出およびベクトル内積 $\\overrightarrow{AB} \\cdot \\overrightarrow{BC}$ の計算",
            "分点ベクトル表現の展開による内積 $\\overrightarrow{AP_{k-1}} \\cdot \\overrightarrow{AP_k}$ の $k, n$ 依存性の整理",
            "区分求積法 $\\lim_{n \\to \\infty} \\frac{1}{n} \\sum f(k/n) = \\int_0^1 f(x)dx$ による極限値計算"
        ],
        "solution": (
            "**【題目大意】**\n"
            "$\\triangle ABC$ において $AB=2, BC=3, CA=4$ とする。\n"
            "(1) $\\angle ABC = \\theta$ とおき、余弦定理を用いてベクトル内積 $\\overrightarrow{AB} \\cdot \\overrightarrow{BC}$ を求める。\n"
            "(2) 辺 $BC$ を $n$ 等分する分点を $P_0=B, P_1, \\dots, P_n=C$ とするとき、内積 $\\overrightarrow{AP_{k-1}} \\cdot \\overrightarrow{AP_k}$ を計算し、極限 $\\lim_{n \\to \\infty} \\frac{1}{n} \\sum_{k=1}^n \\overrightarrow{AP_{k-1}} \\cdot \\overrightarrow{AP_k}$ を求める。\n\n"
            "**【公式正解】**\n"
            "- $\\text{AB} = -6$ ($\\overrightarrow{AB} \\cdot \\overrightarrow{BC} = -6 \\cos \\theta$)\n"
            "- $\\text{CD} = 32$ ($\\overrightarrow{AB} \\cdot \\overrightarrow{BC} = \\frac{3}{2}$)\n"
            "- $\\text{EFGH} = 4639$ ($\\overrightarrow{AP_{k-1}} \\cdot \\overrightarrow{AP_k} = 4 + \\frac{6k - 3}{2n} + \\frac{9(k^2 - k)}{n^2}$)\n"
            "- $\\text{IJK} = 172$ (極限値 $\\frac{17}{2}$)\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "**(1) 余弦定理と内積の計算**\n"
            "ベクトル $\\overrightarrow{AB}$ と $\\overrightarrow{BC}$ のなす角は $\\pi - \\theta$ である。\n"
            "したがって：\n"
            "$$\\overrightarrow{AB} \\cdot \\overrightarrow{BC} = |\\overrightarrow{AB}| |\\overrightarrow{BC}| \\cos(\\pi - \\theta) = -|\\overrightarrow{AB}| |\\overrightarrow{BC}| \\cos \\theta$$\n"
            "$AB = 2, BC = 3$ であるから：\n"
            "$$\\overrightarrow{AB} \\cdot \\overrightarrow{BC} = -(2)(3) \\cos \\theta = -6 \\cos \\theta$$\n"
            "よって、$\\text{AB} = -6$ である。\n\n"
            "次に、$\\triangle ABC$ において余弦定理を適用すると：\n"
            "$$CA^2 = AB^2 + BC^2 - 2 \\, AB \\cdot BC \\cos \\theta$$\n"
            "$$4^2 = 2^2 + 3^2 - 2(2)(3) \\cos \\theta$$\n"
            "$$16 = 13 - 12 \\cos \\theta \\implies 12 \\cos \\theta = -3 \\implies \\cos \\theta = -\\frac{1}{4}$$\n"
            "これを内積の式に代入すると：\n"
            "$$\\overrightarrow{AB} \\cdot \\overrightarrow{BC} = -6 \\times \\left(-\\frac{1}{4}\\right) = \\frac{6}{4} = \\frac{3}{2}$$\n"
            "したがって、$\\text{C} = 3, \\text{D} = 2$ (CD = 32) である。\n\n"
            "**(2) 内積 $\\overrightarrow{AP_{k-1}} \\cdot \\overrightarrow{AP_k}$ の導出**\n"
            "辺 $BC$ の分点 $P_k$ について、$\\overrightarrow{BP_k} = \\frac{k}{n} \\overrightarrow{BC}$ であるから：\n"
            "$$\\overrightarrow{AP_k} = \\overrightarrow{AB} + \\overrightarrow{BP_k} = \\overrightarrow{AB} + \\frac{k}{n} \\overrightarrow{BC}$$\n"
            "同様に：\n"
            "$$\\overrightarrow{AP_{k-1}} = \\overrightarrow{AB} + \\frac{k-1}{n} \\overrightarrow{BC}$$\n"
            "両者の内積を展開すると：\n"
            "$$\\overrightarrow{AP_{k-1}} \\cdot \\overrightarrow{AP_k} = \\left(\\overrightarrow{AB} + \\frac{k-1}{n} \\overrightarrow{BC}\\right) \\cdot \\left(\\overrightarrow{AB} + \\frac{k}{n} \\overrightarrow{BC}\\right)$$\n"
            "$$= |\\overrightarrow{AB}|^2 + \\left(\\frac{k-1}{n} + \\frac{k}{n}\\right) \\overrightarrow{AB} \\cdot \\overrightarrow{BC} + \\frac{k(k-1)}{n^2} |\\overrightarrow{BC}|^2$$\n"
            "各数値を代入する（$|\\overrightarrow{AB}|^2 = 4$、$|\\overrightarrow{BC}|^2 = 9$、$\\overrightarrow{AB} \\cdot \\overrightarrow{BC} = \\frac{3}{2}$）：\n"
            "$$= 4 + \\frac{2k - 1}{n} \\times \\frac{3}{2} + \\frac{k^2 - k}{n^2} \\times 9$$\n"
            "$$= 4 + \\frac{6k - 3}{2n} + \\frac{9(k^2 - k)}{n^2}$$\n"
            "問題の形式 $E + \\frac{Fk - G}{2n} + \\frac{H(k^2 - k)}{n^2}$ と比較すると：\n"
            "$$E = 4, \\quad F = 6, \\quad G = 3, \\quad H = 9$$\n"
            "したがって、$\\text{EFGH} = 4639$ である。\n\n"
            "**(3) 極限値の計算（区分求積法）**\n"
            "求める極限は：\n"
            "$$\\lim_{n \\to \\infty} \\frac{1}{n} \\sum_{k=1}^n \\overrightarrow{AP_{k-1}} \\cdot \\overrightarrow{AP_k}$$\n"
            "$$= \\lim_{n \\to \\infty} \\frac{1}{n} \\sum_{k=1}^n \\left[ 4 + 3 \\cdot \\frac{k}{n} - \\frac{3}{2n} + 9 \\left(\\frac{k}{n}\\right)^2 - \\frac{9k}{n^2} \\right]$$\n"
            "区分求積法（$\\lim_{n \\to \\infty} \\frac{1}{n} \\sum_{k=1}^n f(k/n) = \\int_0^1 f(x)dx$）を適用する。\n"
            "$\\frac{1}{n}$ 次の微小項 $\\frac{3}{2n}$ や $\\frac{9k}{n^2}$ は極限で 0 に収束するため：\n"
            "$$= \\int_0^1 4 \\, dx + \\int_0^1 3x \\, dx + \\int_0^1 9x^2 \\, dx$$\n"
            "それぞれ定積分を計算すると：\n"
            "- $\\int_0^1 4 \\, dx = 4$\n"
            "- $\\int_0^1 3x \\, dx = \\left[ \\frac{3}{2}x^2 \\right]_0^1 = \\frac{3}{2}$\n"
            "- $\\int_0^1 9x^2 \\, dx = \\left[ 3x^3 \\right]_0^1 = 3$\n"
            "したがって、合計は：\n"
            "$$4 + \\frac{3}{2} + 3 = 7 + \\frac{3}{2} = \\frac{17}{2}$$\n"
            "よって、$\\text{IJK} = 172$ である。\n\n"
            "**【考査考点】**\n"
            "- ベクトルの幾何学的定義（始点を揃えたときのなす角と内積の符号）。\n"
            "- 余弦定理を用いた三角形の内角の余弦の決定。\n"
            "- 分点ベクトルの線形結合表現および内積展開。\n"
            "- リーマン和（区分求積法）による定積分への帰着と極限計算。"
        )
    },
    {
        "q_num": 4,
        "localKey": "math-q-II_2",
        "answer_ref": "MATH_C2:II_2",
        "answer": {
            "LM": "12",
            "NO": "25",
            "PQR": "101",
            "STU": "102",
            "VWXY": "1212"
        },
        "title": "大問II 問2：複素数平面上の円領域と直線の交線上の絶対値の最大・最小",
        "points": [
            "共役複素数を用いた円の方程式 $|z - \alpha|^2 \\leq r^2$ への標準化",
            "複素数表示された直線の方程式の実数直交座標 $x, y$ への変換",
            "直線と円の交線（線分）上の点における絶対値 $|z| = \\sqrt{x^2 + y^2}$ の最大値および最小値の決定"
        ],
        "solution": (
            "**【題目大意】**\n"
            "複素数 $z$ が条件 $z\\bar{z} - (1 - 2i)z - (1 + 2i)\\bar{z} \\leq 15$ $\\textcircled{1}$ を満たす。\n"
            "(1) 不等式 $\\textcircled{1}$ が表す円の中心と半径を求める。\n"
            "(2) 直線 $(1 - i)z - (1 + i)\\bar{z} = 2i$ 上にあり、不等式 $\\textcircled{1}$ を満たす $z$ のうち、$|z|$ が最大となる $z_1$ と最小となる $z_2$ を求める。\n\n"
            "**【公式正解】**\n"
            "- $\\text{LM} = 12$ (中心 $1 + 2i$)\n"
            "- $\\text{NO} = 25$ (半径 $2\\sqrt{5}$)\n"
            "- $\\text{PQR} = 101, \\text{STU} = 102$ ($z_1 = \\sqrt{10} + 1 + (\\sqrt{10} + 2)i$)\n"
            "- $\\text{VWXY} = 1212$ ($z_2 = -\\frac{1}{2} + \\frac{1}{2}i$)\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "**(1) 円の方程式の導出**\n"
            "$\\alpha = 1 + 2i$ とおくと、$\\bar{\\alpha} = 1 - 2i$ である。\n"
            "条件式 $\\textcircled{1}$ の左辺を平方完成する：\n"
            "$$z\\bar{z} - \\bar{\\alpha}z - \\alpha\\bar{z} = (z - \\alpha)(\\bar{z} - \\bar{\\alpha}) - \\alpha\\bar{\\alpha} = |z - \\alpha|^2 - |\\alpha|^2$$\n"
            "ここで $|\\alpha|^2 = 1^2 + 2^2 = 5$ であるから：\n"
            "$$|z - (1 + 2i)|^2 - 5 \\leq 15 \\implies |z - (1 + 2i)|^2 \\leq 20$$\n"
            "両辺の平方根をとると：\n"
            "$$|z - (1 + 2i)| \\leq \\sqrt{20} = 2\\sqrt{5}$$\n"
            "したがって、中心は $1 + 2i$、半径は $2\\sqrt{5}$ である。\n"
            "よって、$\\text{L} = 1, \\text{M} = 2$ (LM = 12)、$\\text{N} = 2, \\text{O} = 5$ (NO = 25) である。\n\n"
            "**(2) 直線の方程式の実部・虚部による表現**\n"
            "$z = x + yi$ ($x, y$ は実数) とおくと、$\\bar{z} = x - yi$ である。\n"
            "与えられた直線の方程式は：\n"
            "$$(1 - i)(x + yi) - (1 + i)(x - yi) = 2i$$\n"
            "左辺を展開・整理する：\n"
            "$$(x + y + i(y - x)) - (x + y + i(x - y)) = 2i(y - x)$$\n"
            "したがって：\n"
            "$$2i(y - x) = 2i \\implies y - x = 1 \\implies y = x + 1$$\n"
            "すなわち、直線の方程式は $y = x + 1$ である。\n\n"
            "**(3) 円領域との共通部分（線分）**\n"
            "円領域は $(x - 1)^2 + (y - 2)^2 \\leq 20$ である。\n"
            "$y = x + 1$ を代入すると、$y - 2 = x - 1$ となるので：\n"
            "$$(x - 1)^2 + (x - 1)^2 \\leq 20 \\implies 2(x - 1)^2 \\leq 20 \\implies (x - 1)^2 \\leq 10$$\n"
            "$$-\\sqrt{10} \\leq x - 1 \\leq \\sqrt{10} \\implies 1 - \\sqrt{10} \\leq x \\leq 1 + \\sqrt{10}$$\n"
            "媒介変数 $t = x - 1$ ($-\\sqrt{10} \\leq t \\leq \\sqrt{10}$) を用いると：\n"
            "$$x = 1 + t, \\quad y = 2 + t$$\n\n"
            "**(4) $|z|$ の最大値・最小値の導出**\n"
            "$|z|^2 = x^2 + y^2$ を $t$ で表すと：\n"
            "$$|z|^2 = (1 + t)^2 + (2 + t)^2 = 2t^2 + 6t + 5 = 2\\left(t + \\frac{3}{2}\\right)^2 + 5 - \\frac{9}{2} = 2\\left(t + \\frac{3}{2}\\right)^2 + \\frac{1}{2}$$\n"
            "-$|z|$ の最大値：\n"
            "軸 $t = -\\frac{3}{2}$ から最も遠い端点は $t = \\sqrt{10}$ である。\n"
            "このとき：\n"
            "$$x = 1 + \\sqrt{10}, \\quad y = 2 + \\sqrt{10}$$\n"
            "したがって：\n"
            "$$z_1 = (1 + \\sqrt{10}) + (2 + \\sqrt{10})i = \\sqrt{10} + 1 + (\\sqrt{10} + 2)i$$\n"
            "問題の形 $z_1 = \\sqrt{PQ} + R + (\\sqrt{ST} + U)i$ と比較すると：\n"
            "$$PQ = 10, \\quad R = 1, \\quad ST = 10, \\quad U = 2$$\n"
            "よって、$\\text{PQR} = 101, \\text{STU} = 102$ である。\n\n"
            "-$|z|$ の最小値：\n"
            "頂点 $t = -\\frac{3}{2}$ は区間 $[-\\sqrt{10}, \\sqrt{10}]$ (約 $[-3.16, 3.16]$) に含まれる。\n"
            "したがって、$t = -\\frac{3}{2}$ のとき $|z|^2$ は最小値 $\\frac{1}{2}$ をとる。\n"
            "このとき：\n"
            "$$x = 1 - \\frac{3}{2} = -\\frac{1}{2}, \\quad y = 2 - \\frac{3}{2} = \\frac{1}{2}$$\n"
            "したがって：\n"
            "$$z_2 = -\\frac{1}{2} + \\frac{1}{2}i$$\n"
            "問題の形 $z_2 = -\\frac{V}{W} + \\frac{X}{Y}i$ と比較すると：\n"
            "$$V = 1, \\quad W = 2, \\quad X = 1, \\quad Y = 2$$\n"
            "よって、$\\text{VWXY} = 1212$ である。\n\n"
            "**【考査考点】**\n"
            "- 複素数と共役複素数の性質を用いた円の方程式の決定。\n"
            "- 複素数表現の直線から実数直交座標方程式への変換。\n"
            "- 媒介変数を用いた線分上の点と原点からの距離 $|z|$ の2次関数解析（最大値・最小値）。"
        )
    },
    {
        "q_num": 5,
        "localKey": "math-q-III_1",
        "answer_ref": "MATH_C2:III_1",
        "answer": {
            "AB": "23",
            "CD": "66",
            "E": "0",
            "FG": "26"
        },
        "title": "大問III [1]：条件を満たす円弧の幾何学的特徴と一次結合 $t = x + y$ の値域",
        "points": [
            "不等式 $y \\geq |x|$ と円 $x^2 + y^2 = 12$ による円弧（四分円）の特定",
            "四分円の半径および端点座標の幾何学的決定",
            "直線 $x + y = t$ と円弧の共有点条件による $t$ の値域解析"
        ],
        "solution": (
            "**【題目大意】**\n"
            "実数 $x, y, t, u$ が $y \\geq |x|$ $\\textcircled{1}$、$x + y = t$ $\\textcircled{2}$、$x^2 + y^2 = 12$ $\\textcircled{3}$、$x^3 + y^3 = u$ $\\textcircled{4}$ を満たす。\n"
            "点 $(x, y)$ がなす円弧の半径と両端点の座標を求め、$t$ がとり得る値の範囲を決定する。\n\n"
            "**【公式正解】**\n"
            "- $\\text{AB} = 23$ (半径 $2\\sqrt{3}$)\n"
            "- $\\text{CD} = 66$ (端点の座標 $(\\sqrt{6}, \\sqrt{6})$, $(-\\sqrt{6}, \\sqrt{6})$)\n"
            "- $\\text{E} = 0, \\text{FG} = 26$ ($0 \\leq t \\leq 2\\sqrt{6}$)\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "**(1) 円弧の特定と半径・端点の導出**\n"
            "$\\textcircled{3}$ より、点 $(x, y)$ は原点を中心とする円 $x^2 + y^2 = 12$ 上にある。\n"
            "この円の半径は：\n"
            "$$r = \\sqrt{12} = 2\\sqrt{3}$$\n"
            "したがって、$\\text{AB} = 23$ である。\n\n"
            "次に、$\\textcircled{1}$ は $y \\geq x$ かつ $y \\geq -x$ を意味し、直線 $y = x$ と $y = -x$ の間の上側領域を表す。\n"
            "円 $x^2 + y^2 = 12$ とこの境界線との交点を求める。\n"
            "-$y = x$ との交点（第1象限）：\n"
            "$$x^2 + x^2 = 12 \\implies 2x^2 = 12 \\implies x^2 = 6$$\n"
            "$y \\geq 0$ より $x = \\sqrt{6}, y = \\sqrt{6}$。\n"
            "-$y = -x$ との交点（第2象限）：\n"
            "$$x^2 + (-x)^2 = 12 \\implies 2x^2 = 12 \\implies x = -\\sqrt{6}, y = \\sqrt{6}$。\n"
            "偏角 $\\theta$ で見ると、$\\frac{\\pi}{4} \\leq \\theta \\leq \\frac{3\\pi}{4}$ の範囲の四分円の弧（中心角 $\\frac{\\pi}{2}$）をなしている。\n"
            "したがって、弧の両端点の座標は：\n"
            "$$\\left(\\sqrt{6}, \\sqrt{6}\\right), \\quad \\left(-\\sqrt{6}, \\sqrt{6}\\right)$$\n"
            "よって、$\\text{CD} = 66$ である。\n\n"
            "**(2) $t = x + y$ のとり得る値の範囲**\n"
            "直線 $x + y = t$ とこの円弧 $\\frac{\\pi}{4} \\leq \\theta \\leq \\frac{3\\pi}{4}$ が共有点をもつ $t$ の範囲を調べる。\n"
            "点 $(x, y)$ は $x = \\sqrt{12}\\cos \\theta, y = \\sqrt{12}\\sin \\theta$ と表せるので：\n"
            "$$t = x + y = \\sqrt{12}(\\cos \\theta + \\sin \\theta) = \\sqrt{12} \\cdot \\sqrt{2} \\sin\\left(\\theta + \\frac{\\pi}{4}\\right) = \\sqrt{24} \\sin\\left(\\theta + \\frac{\\pi}{4}\\right) = 2\\sqrt{6} \\sin\\left(\\theta + \\frac{\\pi}{4}\\right)$$\n"
            "$\\theta \\in \\left[\\frac{\\pi}{4}, \\frac{3\\pi}{4}\\right]$ より、$\\theta + \\frac{\\pi}{4} \\in \\left[\\frac{\\pi}{2}, \\pi\\right]$ である。\n"
            "この区間において：\n"
            "-最大値：$\\theta + \\frac{\\pi}{4} = \\frac{\\pi}{2}$（すなわち $\\theta = \\frac{\\pi}{4}$、端点 $(\\sqrt{6}, \\sqrt{6})$）のとき、\n"
            "$$\\sin\\left(\\frac{\\pi}{2}\\right) = 1 \\implies t = 2\\sqrt{6}$$\n"
            "-最小値：$\\theta + \\frac{\\pi}{4} = \\pi$（すなわち $\\theta = \\frac{3\\pi}{4}$、端点 $(-\\sqrt{6}, \\sqrt{6})$）のとき、\n"
            "$$\\sin(\\pi) = 0 \\implies t = 0$$\n"
            "したがって、$t$ のとり得る値の範囲は：\n"
            "$$0 \\leq t \\leq 2\\sqrt{6} \\quad \\textcircled{5}$$\n"
            "よって、$\\text{E} = 0, \\text{FG} = 26$ である。\n\n"
            "**【考査考点】**\n"
            "- 円と絶対値不等式が定める領域の境界（円弧）の同定。\n"
            "- 円弧の端点座標の幾何学的計算。\n"
            "- 三角関数の合成法を用いた線形和 $x + y$ のとり得る値域の導出。"
        )
    },
    {
        "q_num": 6,
        "localKey": "math-q-III_2",
        "answer_ref": "MATH_C2:III_2",
        "answer": {
            "HIJK": "1212",
            "LMNO": "1236",
            "PQRS": "3212",
            "T": "0",
            "UVW": "243"
        },
        "title": "大問III [2]：対称式の変数変換・微分法による3次式の値域決定",
        "points": [
            "基本対称式 $x+y=t, x^2+y^2=12$ を用いた積 $xy$ の $t$ による表現",
            "3次対称式 $x^3+y^3=u$ の $t$ による表現",
            "導関数 $\\frac{du}{dt}$ の増減表解析と閉区間における $u$ の最大値・最小値の決定"
        ],
        "solution": (
            "**【題目大意】**\n"
            "$x + y = t$、 $x^2 + y^2 = 12$、$x^3 + y^3 = u$ のもとで、$xy$ および $u$ を $t$ の式で表し、導関数 $\\frac{du}{dt}$ を求めて、$0 \\leq t \\leq 2\\sqrt{6}$ における $u$ のとり得る値の範囲を決定する。\n\n"
            "**【公式正解】**\n"
            "- $\\text{HIJK} = 1212$ ($xy = \\frac{1}{2}(t^2 - 12)$)\n"
            "- $\\text{LMNO} = 1236$ ($u = \\frac{1}{2}(36t - t^3)$)\n"
            "- $\\text{PQRS} = 3212$ ($\\frac{du}{dt} = \\frac{3}{2}(12 - t^2)$)\n"
            "- $\\text{T} = 0, \\text{UVW} = 243$ ($0 \\leq u \\leq 24\\sqrt{3}$)\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "**(1) $xy$ を $t$ で表す**\n"
            "$(x + y)^2 = x^2 + 2xy + y^2$ より：\n"
            "$$t^2 = 12 + 2xy \\implies xy = \\frac{1}{2}(t^2 - 12)$$\n"
            "問題の形 $xy = \\frac{H}{I}(t^2 - JK)$ と比較すると：\n"
            "$$H = 1, \\quad I = 2, \\quad JK = 12$$\n"
            "したがって、$\\text{HIJK} = 1212$ である。\n\n"
            "**(2) $u$ を $t$ で表す**\n"
            "3次対称式の展開公式 $x^3 + y^3 = (x + y)^3 - 3xy(x + y)$ を用いる：\n"
            "$$u = t^3 - 3 \\left[\\frac{1}{2}(t^2 - 12)\\right] t = t^3 - \\frac{3}{2}t^3 + 18t = 18t - \\frac{1}{2}t^3 = \\frac{1}{2}(36t - t^3)$$\n"
            "問題の形 $u = \\frac{L}{M}(NO \\, t - t^3)$ と比較すると：\n"
            "$$L = 1, \\quad M = 2, \\quad NO = 36$$\n"
            "したがって、$\\text{LMNO} = 1236$ である。\n\n"
            "**(3) 導関数 $\\frac{du}{dt}$ の計算**\n"
            "$u = 18t - \\frac{1}{2}t^3$ を $t$ で微分すると：\n"
            "$$\\frac{du}{dt} = 18 - \\frac{3}{2}t^2 = \\frac{3}{2}(12 - t^2)$$\n"
            "問題の形 $\\frac{du}{dt} = \\frac{P}{Q}(RS - t^2)$ と比較すると：\n"
            "$$P = 3, \\quad Q = 2, \\quad RS = 12$$\n"
            "したがって、$\\text{PQRS} = 3212$ である。\n\n"
            "**(4) $u$ の増減ととり得る値の範囲**\n"
            "$0 \\leq t \\leq 2\\sqrt{6}$ において、$\\frac{du}{dt} = 0$ となるのは：\n"
            "$$t^2 = 12 \\implies t = \\sqrt{12} = 2\\sqrt{3}$$\n"
            "増減表を作成する：\n\n"
            "| $t$ | $0$ | $\\dots$ | $2\\sqrt{3}$ | $\\dots$ | $2\\sqrt{6}$ |\n"
            "| :---: | :---: | :---: | :---: | :---: | :---: |\n"
            "| $\\frac{du}{dt}$ | | $+$ | $0$ | $-$ | |\n"
            "| $u$ | $0$ | $\\nearrow$ | 極大 | $\\searrow$ | $12\\sqrt{6}$ |\n\n"
            "各点での $u$ の値を計算する：\n"
            "- $t = 0$ のとき：\n"
            "$$u = \\frac{1}{2}(0 - 0) = 0$$\n"
            "- $t = 2\\sqrt{3}$ のとき（極大値）：\n"
            "$$u = 18(2\\sqrt{3}) - \\frac{1}{2}(2\\sqrt{3})^3 = 36\\sqrt{3} - \\frac{1}{2}(24\\sqrt{3}) = 36\\sqrt{3} - 12\\sqrt{3} = 24\\sqrt{3}$$\n"
            "- $t = 2\\sqrt{6}$ のとき（端点）：\n"
            "$$u = 18(2\\sqrt{6}) - \\frac{1}{2}(2\\sqrt{6})^3 = 36\\sqrt{6} - \\frac{1}{2}(48\\sqrt{6}) = 36\\sqrt{6} - 24\\sqrt{6} = 12\\sqrt{6}$$\n"
            "ここで、$24\\sqrt{3}$ と $12\\sqrt{6}$ の大きさを比較すると：\n"
            "$$(24\\sqrt{3})^2 = 576 \\times 3 = 1728$$\n"
            "$$(12\\sqrt{6})^2 = 144 \\times 6 = 864$$\n"
            "より、$24\\sqrt{3} > 12\\sqrt{6}$ である。\n"
            "また、区間内の最小値は $t = 0$ のときの $u = 0$ である。\n"
            "したがって、$u$ のとり得る値の範囲は：\n"
            "$$0 \\leq u \\leq 24\\sqrt{3}$$\n"
            "よって、$\\text{T} = 0, \\text{UVW} = 243$ である。\n\n"
            "**【考査考点】**\n"
            "- 対称式の基本性質と変数変換による次数の整理。\n"
            "- 微分法による3次関数の増減、極値の判定。\n"
            "- 閉区間における極大値と端点値の比較による値域（最大値・最小値）の確定。"
        )
    },
    {
        "q_num": 7,
        "localKey": "math-q-IV_1",
        "answer_ref": "MATH_C2:IV_1",
        "answer": {
            "A": "3",
            "B": "3",
            "CDE": "122"
        },
        "title": "大問IV [1]：三角関数で囲まれた図形の面積積分と導関数の定式化",
        "points": [
            "三角関数のグラフと直線による面積の定積分計算",
            "媒介変数 $t$ ($a\\cos 3t = 1$) による面積 $S, T$ の表現",
            "差の関数 $f(t) = T - S$ の商の微分法による導関数 $f'(t)$ の導出"
        ],
        "solution": (
            "**【題目大意】**\n"
            "$a > 1$ とする。領域 $0 \\leq x \\leq \\frac{\\pi}{6}, 0 \\leq y \\leq a \\cos 3x$ を直線 $y = 1$ で分割し、$y \\geq 1$ の面積を $S$、$y \\leq 1$ の面積を $T$ とする。\n"
            "$a \\cos 3t = 1$ ($0 \\leq t \\leq \\frac{\\pi}{6}$) とおくとき、$S$、$S + T$ を $t$ で表し、$f(t) = T - S$ の導関数 $f'(t)$ を求める。\n\n"
            "**【公式正解】**\n"
            "- $\\text{A} = 3$ ($S = \\frac{\\sin 3t}{3\\cos 3t} - t$)\n"
            "- $\\text{B} = 3$ ($S + T = \\frac{1}{3\\cos 3t}$)\n"
            "- $\\text{CDE} = 122$ ($f'(t) = \\frac{(1 - 2\\sin 3t)\\sin 3t}{\\cos^2 3t}$)\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "**(1) 面積 $S$ および $S + T$ の計算**\n"
            "条件より $a \\cos 3t = 1$ であるから：\n"
            "$$a = \\frac{1}{\\cos 3t}$$\n"
            "区間 $0 \\leq x \\leq t$ では $a \\cos 3x \\geq 1$ である。\n"
            "したがって、$y \\geq 1$ の部分の面積 $S$ は：\n"
            "$$S = \\int_0^t (a \\cos 3x - 1) \\, dx = \\left[ \\frac{a}{3}\\sin 3x - x \\right]_0^t = \\frac{a}{3}\\sin 3t - t$$\n"
            "$a = \\frac{1}{\\cos 3t}$ を代入すると：\n"
            "$$S = \\frac{\\sin 3t}{3 \\cos 3t} - t$$\n"
            "よって、$\\text{A} = 3$ である。\n\n"
            "次に、$S + T$ は領域全体の面積、すなわち $0 \\leq x \\leq \\frac{\\pi}{6}$ における $y = a \\cos 3x$ の定積分である：\n"
            "$$S + T = \\int_0^{\\pi/6} a \\cos 3x \\, dx = \\left[ \\frac{a}{3}\\sin 3x \\right]_0^{\\pi/6} = \\frac{a}{3}\\sin\\left(\\frac{\\pi}{2}\\right) = \\frac{a}{3}$$\n"
            "$a = \\frac{1}{\\cos 3t}$ を代入すると：\n"
            "$$S + T = \\frac{1}{3 \\cos 3t}$$\n"
            "よって、$\\text{B} = 3$ である。\n\n"
            "**(2) $f(t) = T - S$ の導関数の導出**\n"
            "$T = (S + T) - S$ より：\n"
            "$$f(t) = T - S = (S + T) - 2S = \\frac{1}{3 \\cos 3t} - 2\\left(\\frac{\\sin 3t}{3 \\cos 3t} - t\\right) = \\frac{1 - 2\\sin 3t}{3 \\cos 3t} + 2t$$\n"
            "これを $t$ で微分する。\n"
            "第1項 $\\frac{1 - 2\\sin 3t}{3 \\cos 3t}$ の微分には商の微分法を用いる：\n"
            "$$\\frac{d}{dt}\\left[\\frac{1 - 2\\sin 3t}{3 \\cos 3t}\\right] = \\frac{(-6\\cos 3t)(3\\cos 3t) - (1 - 2\\sin 3t)(-9\\sin 3t)}{9 \\cos^2 3t}$$\n"
            "$$= \\frac{-18 \\cos^2 3t + 9 \\sin 3t - 18 \\sin^2 3t}{9 \\cos^2 3t} = \\frac{-18(\\cos^2 3t + \\sin^2 3t) + 9 \\sin 3t}{9 \\cos^2 3t}$$\n"
            "$$= \\frac{-18 + 9 \\sin 3t}{9 \\cos^2 3t} = \\frac{-2 + \\sin 3t}{\\cos^2 3t}$$\n"
            "第2項 $2t$ の微分は $2 = \\frac{2\\cos^2 3t}{\\cos^2 3t} = \\frac{2(1 - \\sin^2 3t)}{\\cos^2 3t}$ である。\n"
            "したがって、両者を足し合わせると：\n"
            "$$f'(t) = \\frac{-2 + \\sin 3t + 2 - 2\\sin^2 3t}{\\cos^2 3t} = \\frac{\\sin 3t - 2\\sin^2 3t}{\\cos^2 3t} = \\frac{(1 - 2\\sin 3t)\\sin 3t}{\\cos^2 3t}$$\n"
            "問題の形 $f'(t) = \\frac{(C - D\\sin 3t)\\sin 3t}{\\cos^E 3t}$ と比較すると：\n"
            "$$C = 1, \\quad D = 2, \\quad E = 2$$\n"
            "したがって、$\\text{CDE} = 122$ である。\n\n"
            "**【考査考点】**\n"
            "- 三角関数の定積分による面積の計算。\n"
            "- 方程式の根 $t$ をパラメータとする関数関係の定式化。\n"
            "- 商の微分法および三角関数の基本恒等式 $\\sin^2 \\theta + \\cos^2 \\theta = 1$ を用いた導関数の因数分解。"
        )
    },
    {
        "q_num": 8,
        "localKey": "math-q-IV_2",
        "answer_ref": "MATH_C2:IV_2",
        "answer": {
            "FG": "18",
            "HIJ": "233",
            "K": "9"
        },
        "title": "大問IV [2]：面積差の最大化・最適パラメータと最大値の導出",
        "points": [
            "導関数 $f'(t) = 0$ の解の特定による増減分析",
            "最大値を与える媒介変数 $t$ から元パラメータ $a$ の逆算",
            "面積差 $T - S$ の最大値の厳密な計算"
        ],
        "solution": (
            "**【題目大意】**\n"
            "$f(t) = T - S$ を最大にする $t$ の値、そのときのパラメータ $a$ の値、および $T - S$ の最大値を求める。\n\n"
            "**【公式正解】**\n"
            "- $\\text{FG} = 18$ ($t = \\frac{\\pi}{18}$)\n"
            "- $\\text{HIJ} = 233$ ($a = \\frac{2\\sqrt{3}}{3}$)\n"
            "- $\\text{K} = 9$ (最大値 $\\frac{\\pi}{9}$)\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "**(1) $T - S$ を最大にする $t$ の導出**\n"
            "導関数は：\n"
            "$$f'(t) = \\frac{(1 - 2\\sin 3t)\\sin 3t}{\\cos^2 3t}$$\n"
            "$0 < t < \\frac{\\pi}{6}$ において、$0 < 3t < \\frac{\\pi}{2}$ であるから、$\\sin 3t > 0$ かつ $\\cos 3t > 0$ である。\n"
            "したがって、$f'(t)$ の符号は $1 - 2\\sin 3t$ の符号と一致する。\n"
            "$f'(t) = 0$ となるのは：\n"
            "$$1 - 2\\sin 3t = 0 \\implies \\sin 3t = \\frac{1}{2}$$\n"
            "$0 < 3t < \\frac{\\pi}{2}$ より：\n"
            "$$3t = \\frac{\\pi}{6} \\implies t = \\frac{\\pi}{18}$$\n"
            "区間 $\\left(0, \\frac{\\pi}{6}\\right)$ における増減は以下のようになる：\n"
            "- $0 < t < \\frac{\\pi}{18}$ では $\\sin 3t < \\frac{1}{2}$ なので $f'(t) > 0$（単調増加）。\n"
            "- $\\frac{\\pi}{18} < t < \\frac{\\pi}{6}$ では $\\sin 3t > \\frac{1}{2}$ なので $f'(t) < 0$（単調減少）。\n"
            "したがって、$f(t) = T - S$ は $t = \\frac{\\pi}{18}$ で極大かつ最大となる。\n"
            "よって、$\\text{FG} = 18$ である。\n\n"
            "**(2) 最大値を与えるパラメータ $a$ の導出**\n"
            "$a = \\frac{1}{\\cos 3t}$ であるから、$t = \\frac{\\pi}{18}$（すなわち $3t = \\frac{\\pi}{6}$）を代入すると：\n"
            "$$a = \\frac{1}{\\cos(\\pi/6)} = \\frac{1}{\\frac{\\sqrt{3}}{2}} = \\frac{2}{\\sqrt{3}} = \\frac{2\\sqrt{3}}{3}$$\n"
            "問題の形 $a = \\frac{H\\sqrt{I}}{J}$ と比較すると：\n"
            "$$H = 2, \\quad I = 3, \\quad J = 3$$\n"
            "したがって、$\\text{HIJ} = 233$ である。\n\n"
            "**(3) $T - S$ の最大値の計算**\n"
            "$t = \\frac{\\pi}{18}$ のときの $f(t) = \\frac{1 - 2\\sin 3t}{3\\cos 3t} + 2t$ を計算する。\n"
            "$\\sin 3t = \\frac{1}{2}$ であるから、第1項の分子は $1 - 2\\left(\\frac{1}{2}\\right) = 0$ となる。\n"
            "したがって：\n"
            "$$f\\left(\\frac{\\pi}{18}\\right) = 0 + 2\\left(\\frac{\\pi}{18}\\right) = \\frac{\\pi}{9}$$\n"
            "問題の形 $\\frac{\\pi}{K}$ と比較すると：\n"
            "$$K = 9$$\n"
            "よって、$\\text{K} = 9$ である。\n\n"
            "**【考査考点】**\n"
            "- 微分を用いた極値条件の判定と増減表の作成。\n"
            "- 媒介変数と元の幾何学的パラメータの相互変換。\n"
            "- 関数の最大値計算における代数的単純化の活用。"
        )
    }
]

def main():
    repo_root = Path(__file__).resolve().parent.parent
    work_dir = repo_root / "work" / "2016-1-math-c2"
    work_dir.mkdir(parents=True, exist_ok=True)
    
    # Save explanations.json
    json_path = work_dir / "explanations.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(math_c2_sections, f, ensure_ascii=False, indent=2)
    print(f"Generated {json_path.relative_to(repo_root)} ({len(math_c2_sections)} questions)")
    
    # Save markdown doc
    docs_dir = repo_root / "docs" / "explanations"
    docs_dir.mkdir(parents=True, exist_ok=True)
    md_path = docs_dir / "2016-1-math-c2-solutions.md"
    
    lines = [
        "# 2016年第1回 EJU 数学コース2 解答解説 (Authoritative Solutions)",
        "",
        "> 本ドキュメントは公式解答および厳密な数学的推導に基づく完全解答解説です。",
        ""
    ]
    
    for s in math_c2_sections:
        lines.append(f"## {s['title']}")
        lines.append(f"- **Local Key**: `{s['localKey']}`")
        lines.append(f"- **Answer Ref**: `{s['answer_ref']}`")
        lines.append(f"- **公式正解**: `{s['answer']}`")
        lines.append("")
        lines.append(s["solution"])
        lines.append("")
        lines.append("---")
        lines.append("")
        
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Generated {md_path.relative_to(repo_root)}")

if __name__ == "__main__":
    main()

