#!/usr/bin/env python3
"""Generate comprehensive pedagogical explanations for 2017-1 EJU Math Course 2 (8 questions)."""

import json
from pathlib import Path

math_c2_sections = [
    {
        "q_num": 1,
        "localKey": "math-q-I_1",
        "answer_ref": "MATH_C2:I_1",
        "answer": {
            "ABCDE": "31214",
            "F": "2",
            "G": "8",
            "HIJ": "326",
            "K": "1",
            "LM": "15"
        },
        "title": "大問I 問1：2次関数の平行移動と対称移動・共有点問題",
        "points": [
            "2次関数の平行移動による係数決定と標準形への変形",
            "直線 y = c に関する線対称移動の式変形",
            "2つの放物線の共有点がただ1つとなる判別式重解条件の適用"
        ],
        "solution": (
            "**【題目大意】**\n"
            "2次関数 $y = 3x^2 - 6$ を平行移動して2点 $(1, 5)$, $(4, 14)$ を通る放物線 $\\textcircled{1}$ と、直線 $y = c$ に関して対称移動した放物線 $\\textcircled{2}$ について、その方程式および $\\textcircled{1}$ と $\\textcircled{2}$ がただ1つの共有点をもつときの条件を求める。\n\n"
            "**【公式正解】**\n"
            "- $\\text{ABCDE} = 31214$ ($y = 3x^2 - 12x + 14$)\n"
            "- $\\text{F} = 2, \\text{G} = 8$ ($x$ 軸方向に 2、$y$ 軸方向に 8 平行移動)\n"
            "- $\\text{HIJ} = 326$ ($y = -3x^2 + 2c + 6$)\n"
            "- $\\text{K} = 1$ ($c = 1$)\n"
            "- $\\text{LM} = 15$ (共有点の座標 $(1, 5)$)\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "**(1) 平行移動した放物線の方程式と平行移動量の特定**\n"
            "$y = 3x^2 - 6$ のグラフを平行移動した放物線は、$x^2$ の係数が 3 のままであるから、$y = 3x^2 + bx + c'$ とおくことができる。\n"
            "このグラフが 2 点 $(1, 5)$, $(4, 14)$ を通ることから：\n"
            "$$\n"
            "\\begin{cases}\n"
            "3(1)^2 + b(1) + c' = 5 \\implies b + c' = 2 \\\\\n"
            "3(4)^2 + b(4) + c' = 14 \\implies 48 + 4b + c' = 14 \\implies 4b + c' = -34\n"
            "\\end{cases}\n"
            "$$\n"
            "下の式から上の式を引くと：\n"
            "$$3b = -36 \\implies b = -12$$\n"
            "これより $c' = 2 - (-12) = 14$ となる。\n"
            "したがって、放物線の方程式は：\n"
            "$$y = 3x^2 - 12x + 14$$\n"
            "よって、$\\text{A} = 3, \\text{BC} = 12, \\text{DE} = 14$ より $\\mathbf{ABCDE = 31214}$ である。\n\n"
            "次に平行移動量を求めるため、平方完成を行う：\n"
            "$$y = 3(x^2 - 4x) + 14 = 3(x - 2)^2 - 12 + 14 = 3(x - 2)^2 + 2$$\n"
            "元の放物線 $y = 3x^2 - 6$ の頂点は $(0, -6)$、移動後の放物線の頂点は $(2, 2)$ である。\n"
            "したがって、$x$ 軸方向への移動量は $2 - 0 = 2$、\n"
            "$y$ 軸方向への移動量は $2 - (-6) = 8$ である。\n"
            "よって、$\\mathbf{F = 2}, \\mathbf{G = 8}$ である。\n\n"
            "**(2) 直線 $y = c$ に関する対称移動と共有点の決定**\n"
            "点 $(x, y)$ を直線 $y = c$ に関して対称移動した点を $(X, Y)$ とすると：\n"
            "$$X = x, \\quad \\frac{y + Y}{2} = c \\implies Y = 2c - y$$\n"
            "元の放物線 $y = 3x^2 - 6$ に代入すると：\n"
            "$$2c - y = 3x^2 - 6 \\implies y = -3x^2 + 2c + 6$$\n"
            "よって、$\\text{H} = 3, \\text{I} = 2, \\text{J} = 6$ より $\\mathbf{HIJ = 326}$ である。\n\n"
            "2つの放物線 $\\textcircled{1}$ と $\\textcircled{2}$ が共有点を 1 つだけもつ条件を考える。\n"
            "$$3x^2 - 12x + 14 = -3x^2 + 2c + 6$$\n"
            "整理すると：\n"
            "$$6x^2 - 12x + (8 - 2c) = 0 \\iff 3x^2 - 6x + (4 - c) = 0$$\n"
            "共有点が 1 つだけ存在するためには、この 2 次方程式が重解をもてばよい。\n"
            "判別式を $D$ とすると：\n"
            "$$D/4 = (-3)^2 - 3(4 - c) = 9 - 12 + 3c = 3c - 3 = 0 \\implies c = 1$$\n"
            "よって、$\\mathbf{K = 1}$ である。\n\n"
            "$c = 1$ のとき、方程式は：\n"
            "$$3x^2 - 6x + 3 = 0 \\iff 3(x - 1)^2 = 0 \\implies x = 1$$\n"
            "このときの $y$ 座標は：\n"
            "$$y = 3(1)^2 - 12(1) + 14 = 5$$\n"
            "したがって、共有点の座標は $(1, 5)$ である。\n"
            "よって、$\\text{L} = 1, \\text{M} = 5$ より $\\mathbf{LM = 15}$ である。\n\n"
            "**【考査考点】**\n"
            "2次関数の決定（未定係数法）、放物線の頂点座標と平行移動の関係、直線 $y = c$ に関する対称移動の幾何的代数化、2次方程式の判別式による接点条件（重解条件）の分析。"
        )
    },
    {
        "q_num": 2,
        "localKey": "math-q-I_2",
        "answer_ref": "MATH_C2:I_2",
        "answer": {
            "NO": "90",
            "PQ": "12",
            "RS": "33",
            "TUV": "415",
            "WXYZ": "1330"
        },
        "title": "大問I 問2：カードの順列・組合せと非復元抽出の確率",
        "points": [
            "白4枚・赤3枚・黒3枚の計10枚の相異なるカードの分配",
            "同色・異色を取り出す組合せと余事象の活用",
            "非復元抽出における条件付き事象の確率計算"
        ],
        "solution": (
            "**【題目大意】**\n"
            "白4枚、赤3枚、黒3枚の計10枚のカード（すべて相異なる数字が記されている）からカードを選び、箱に入れたり非復元抽出したりするときの順列・組合せおよび確率を求める。\n\n"
            "**【公式正解】**\n"
            "- $\\text{NO} = 90$ (全部で 90 通り)\n"
            "- $\\text{PQ} = 12$ (同色 12 通り)\n"
            "- $\\text{RS} = 33$ (異色 33 通り)\n"
            "- $\\text{TUV} = 415$ (同色である確率 $\\frac{4}{15}$)\n"
            "- $\\text{WXYZ} = 1330$ (条件を満たす確率 $\\frac{13}{30}$)\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "**(1) 10枚から2枚を選び、箱A, Bに1枚ずつ入れる方法**\n"
            "異なる10枚から相異なる2枚を選んで順序をつけて箱A, Bに入れる順列の総数は：\n"
            "$$_{10}\\text{P}_2 = 10 \\times 9 = 90$$\n"
            "よって、$\\mathbf{NO = 90}$ である。\n\n"
            "**(2) 2枚とも同じ色、および異なる色の選び方**\n"
            "10枚から2枚を選ぶ組合せについて：\n"
            "- 2枚とも白である選び方：$_4\\text{C}_2 = \\frac{4 \\times 3}{2} = 6$ 通り\n"
            "- 2枚とも赤である選び方：$_3\\text{C}_2 = 3$ 通り\n"
            "- 2枚とも黒である選び方：$_3\\text{C}_2 = 3$ 通り\n"
            "これらは互いに排反であるから、2枚とも同じ色となる選び方は：\n"
            "$$6 + 3 + 3 = 12 \\text{ 通り}$$\n"
            "よって、$\\mathbf{PQ = 12}$ である。\n\n"
            "10枚から2枚を選ぶすべての組合せは：\n"
            "$$_{10}\\text{C}_2 = \\frac{10 \\times 9}{2} = 45 \\text{ 通り}$$\n"
            "したがって、2枚の色が異なるような選び方は余事象より：\n"
            "$$45 - 12 = 33 \\text{ 通り}$$\n"
            "よって、$\\mathbf{RS = 33}$ である。\n\n"
            "**(3) 取り出した2枚が同じ色である確率**\n"
            "同様に確からしい全事象は $_{10}\\text{C}_2 = 45$ 通りであり、2枚が同じ色である事象は 12 通りであるから：\n"
            "$$P = \\frac{12}{45} = \\frac{4}{15}$$\n"
            "よって、$\\text{T} = 4, \\text{UV} = 15$ より $\\mathbf{TUV = 415}$ である。\n\n"
            "**(4) 1枚目が白か赤、かつ2枚目が赤か黒である確率**\n"
            "1枚目に取り出す事象によって排反に場合分けする：\n"
            "- **場合 1：1枚目が「白」のとき**\n"
            "  1枚目に白を取り出す確率は $\\frac{4}{10}$。\n"
            "  白が1枚減り、残りは白3枚、赤3枚、黒3枚の計9枚となる。\n"
            "  この中から2枚目に赤または黒（計6枚）を取り出す確率は $\\frac{6}{9}$。\n"
            "  $$P_1 = \\frac{4}{10} \\times \\frac{6}{9} = \\frac{24}{90}$$\n"
            "- **場合 2：1枚目が「赤」のとき**\n"
            "  1枚目に赤を取り出す確率は $\\frac{3}{10}$。\n"
            "  赤が1枚減り、残りは白4枚、赤2枚、黒3枚の計9枚となる。\n"
            "  この中から2枚目に赤または黒（計 $2 + 3 = 5$ 枚）を取り出す確率は $\\frac{5}{9}$。\n"
            "  $$P_2 = \\frac{3}{10} \\times \\frac{5}{9} = \\frac{15}{90}$$\n"
            "これら2つの場合は排反であるから、求める確率は：\n"
            "$$P = P_1 + P_2 = \\frac{24 + 15}{90} = \\frac{39}{90} = \\frac{13}{30}$$\n"
            "よって、$\\text{WX} = 13, \\text{YZ} = 30$ より $\\mathbf{WXYZ = 1330}$ である。\n\n"
            "**【考査考点】**\n"
            "場合の数（順列・組合せ）、余事象の考え方、非復元抽出における確率の乗法定理と排反事象の加法定理。"
        )
    },
    {
        "q_num": 3,
        "localKey": "math-q-II_1",
        "answer_ref": "MATH_C2:II_1",
        "answer": {
            "ABC": "214",
            "DE": "32",
            "FG": "56",
            "HI": "16",
            "JKL": "396"
        },
        "title": "大問II 問1：平面ベクトルと重心・共線条件・内積計算",
        "points": [
            "交点 D の位置ベクトルの導出と共線条件（係数の和が 1）の利用",
            "三角形の重心 G の位置ベクトルの線形表現",
            "内積の定義とベクトルの大きさの計算（余弦定理的展開）"
        ],
        "solution": (
            "**【題目大意】**\n"
            "1辺 $OA$ を共有する $\\triangle OAB$ と $\\triangle OAC$ において、$\\overrightarrow{OC} = x\\overrightarrow{OA} + \\frac{1}{2}\\overrightarrow{OB}$ であり、$\\triangle OAC$ の重心 $G$ が線分 $AB$ 上にあるとき、$x$ の値を求め、$\\overrightarrow{OG}$ および $OG$ の長さを計算する。\n\n"
            "**【公式正解】**\n"
            "- $\\text{ABC} = 214$ ($\\overrightarrow{OD} = \\frac{x}{2}\\overrightarrow{OA} + \\frac{1}{4}\\overrightarrow{OB}$)\n"
            "- $\\text{DE} = 32$ ($x = \\frac{3}{2}$)\n"
            "- $\\text{FG} = 56, \\text{HI} = 16$ ($\\overrightarrow{OG} = \\frac{5}{6}\\overrightarrow{OA} + \\frac{1}{6}\\overrightarrow{OB}$)\n"
            "- $\\text{JKL} = 396$ ($OG = \\frac{\\sqrt{39}}{6}$)\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "**(1) 交点 $D$ の位置ベクトルと $x$ の決定**\n"
            "線分 $OC$ と線分 $AB$ の交点を $D$ とする。\n"
            "$D$ は直線 $OC$ 上にあるから、実数 $k$ を用いて $\\overrightarrow{OD} = k\\overrightarrow{OC}$ と表せる。\n"
            "問題文の形式 $\\overrightarrow{OD} = \\frac{x}{\\text{A}}\\overrightarrow{OA} + \\frac{\\text{B}}{\\text{C}}\\overrightarrow{OB}$ に着目すると：\n"
            "$\\overrightarrow{OC} = x\\overrightarrow{OA} + \\frac{1}{2}\\overrightarrow{OB}$ より、両辺に $k = \\frac{1}{2}$ を掛けると：\n"
            "$$\\overrightarrow{OD} = \\frac{x}{2}\\overrightarrow{OA} + \\frac{1}{4}\\overrightarrow{OB}$$\n"
            "よって、$\\text{A} = 2, \\text{B} = 1, \\text{C} = 4$ より $\\mathbf{ABC = 214}$ である。\n\n"
            "点 $D$ は線分 $AB$ 上にあるから、$\\overrightarrow{OA}$ と $\\overrightarrow{OB}$ の係数の和は 1 である：\n"
            "$$\\frac{x}{2} + \\frac{1}{4} = 1 \\implies \\frac{x}{2} = \\frac{3}{4} \\implies x = \\frac{3}{2}$$\n"
            "よって、$\\text{D} = 3, \\text{E} = 2$ より $\\mathbf{DE = 32}$ である。\n\n"
            "**(2) 重心 $G$ の位置ベクトルの表現**\n"
            "$\\triangle OAC$ の頂点は $O(0), A, C$ であるから、重心 $G$ の位置ベクトルは：\n"
            "$$\\overrightarrow{OG} = \\frac{\\overrightarrow{OO} + \\overrightarrow{OA} + \\overrightarrow{OC}}{3} = \\frac{\\overrightarrow{OA} + \\left(x\\overrightarrow{OA} + \\frac{1}{2}\\overrightarrow{OB}\\right)}{3} = \\frac{1 + x}{3}\\overrightarrow{OA} + \\frac{1}{6}\\overrightarrow{OB}$$\n"
            "$x = \\frac{3}{2}$ を代入すると：\n"
            "$$\\frac{1 + \\frac{3}{2}}{3} = \\frac{\\frac{5}{2}}{3} = \\frac{5}{6}$$\n"
            "したがって：\n"
            "$$\\overrightarrow{OG} = \\frac{5}{6}\\overrightarrow{OA} + \\frac{1}{6}\\overrightarrow{OB}$$\n"
            "よって、$\\text{FG} = 56, \\text{HI} = 16$ である。\n"
            "（なお、係数の和 $\\frac{5}{6} + \\frac{1}{6} = 1$ より、条件(ii)「$G$ が線分 $AB$ 上にある」ことと完全に整合している）\n\n"
            "**(3) $OG$ の大きさの計算**\n"
            "$OA = 1, OB = 2, \\angle AOB = 60^\\circ$ のとき：\n"
            "$$\\overrightarrow{OA} \\cdot \\overrightarrow{OB} = |\\overrightarrow{OA}| |\\overrightarrow{OB}| \\cos 60^\\circ = 1 \\times 2 \\times \\frac{1}{2} = 1$$\n"
            "$$|\\overrightarrow{OG}|^2 = \\left|\\frac{5}{6}\\overrightarrow{OA} + \\frac{1}{6}\\overrightarrow{OB}\\right|^2 = \\frac{1}{36}\\left(25|\\overrightarrow{OA}|^2 + 10\\overrightarrow{OA} \\cdot \\overrightarrow{OB} + |\\overrightarrow{OB}|^2\\right)$$\n"
            "$$= \\frac{1}{36}\\left(25 \\times 1^2 + 10 \\times 1 + 2^2\\right) = \\frac{25 + 10 + 4}{36} = \\frac{39}{36}$$\n"
            "したがって：\n"
            "$$OG = \\frac{\\sqrt{39}}{6}$$\n"
            "よって、$\\text{J} = 3, \\text{K} = 9, \\text{L} = 6$ より $\\mathbf{JKL = 396}$ である。\n\n"
            "**【考査考点】**\n"
            "平面ベクトルの線形独立性と一次結合、線分の交点ベクトルの導出、共線条件（係数の和が 1）、三角形の重心の公式、ベクトルの内積とノルムの計算。"
        )
    },
    {
        "q_num": 4,
        "localKey": "math-q-II_2",
        "answer_ref": "MATH_C2:II_2",
        "answer": {
            "M": "2",
            "N": "7",
            "OP": "12",
            "Q": "3",
            "RS": "12",
            "TU": "16"
        },
        "title": "大問II 問2：複素数平面上の三角形の面積と二等辺三角形の条件",
        "points": [
            "絶対値 |z| = 2 を満たす複素数の極形式表現",
            "複素数平面上の原点を含む三角形の面積公式と最大値の決定",
            "二等辺三角形条件（OA = OB）の幾何的・代数的導出と偏角 arg の決定"
        ],
        "solution": (
            "**【題目大意】**\n"
            "$|z| = 2$ を満たす複素数 $z$ について、$A(1 + z)$, $B(1 - \\frac{1}{2}z)$ とおく。$z$ の極形式表示、$\\triangle OAB$ の面積 $S$ の式および最大値、そして $\\triangle OAB$ が $OA = OB$ の二等辺三角形となるときの辺長および各点の偏角を求める。\n\n"
            "**【公式正解】**\n"
            "- $\\text{M} = 2$ ($z = 2(\\cos\\theta + i\\sin\\theta)$)\n"
            "- $\\text{N} = 7$ ($S = \\frac{3}{2}|\\sin\\theta|$、選択肢 $\\textcircled{7}$)\n"
            "- $\\text{OP} = 12$ (最大となるのは $\\theta = \\pm \\frac{1}{2}\\pi$)\n"
            "- $\\text{Q} = 3$ ($|1 + z| = |1 - \\frac{1}{2}z| = \\sqrt{3}$)\n"
            "- $\\text{RS} = 12$ ($\\arg(1 + z) = \\pm \\frac{1}{2}\\pi$)\n"
            "- $\\text{TU} = 16$ ($\\arg(1 - \\frac{1}{2}z) = \\mp \\frac{1}{6}\\pi$)\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "**(1) 極形式と $\\triangle OAB$ の面積**\n"
            "$|z| = 2$ より、$z$ は極形式で次のように表される：\n"
            "$$z = 2(\\cos\\theta + i\\sin\\theta) \\quad (-\\pi \\leq \\theta < \\pi)$$\n"
            "よって、$\\mathbf{M = 2}$ である。\n\n"
            "各点の座標を $(x, y)$ で表すと：\n"
            "- 点 $A$ は $1 + z = (1 + 2\\cos\\theta) + i(2\\sin\\theta)$ より：$A(1 + 2\\cos\\theta, 2\\sin\\theta)$\n"
            "- 点 $B$ は $1 - \\frac{1}{2}z = (1 - \\cos\\theta) - i(\\sin\\theta)$ より：$B(1 - \\cos\\theta, -\\sin\\theta)$\n"
            "原点 $O$ と 2 点 $A(x_A, y_A), B(x_B, y_B)$ がつくる三角形の面積公式は：\n"
            "$$S = \\frac{1}{2} |x_A y_B - x_B y_A|$$\n"
            "行列式（たすき掛け）を計算すると：\n"
            "$$x_A y_B - x_B y_A = (1 + 2\\cos\\theta)(-\\sin\\theta) - (1 - \\cos\\theta)(2\\sin\\theta)$$\n"
            "$$= -\\sin\\theta - 2\\sin\\theta\\cos\\theta - 2\\sin\\theta + 2\\sin\\theta\\cos\\theta = -3\\sin\\theta$$\n"
            "したがって、面積は：\n"
            "$$S = \\frac{1}{2} |-3\\sin\\theta| = \\frac{3}{2} |\\sin\\theta|$$\n"
            "これは選択肢 $\\textcircled{7}$ であるから、$\\mathbf{N = 7}$ である。\n\n"
            "$S$ が最大となるのは $|\\sin\\theta| = 1$、すなわち $\\theta = \\pm \\frac{1}{2}\\pi$ のときである。\n"
            "よって、$\\text{O} = 1, \\text{P} = 2$ より $\\mathbf{OP = 12}$ である。\n\n"
            "**(2) 二等辺三角形 $OA = OB$ の条件と偏角**\n"
            "$OA = OB \\iff |1 + z|^2 = \\left|1 - \\frac{1}{2}z\\right|^2$ である。\n"
            "複素数の絶対値の 2 乗を計算する：\n"
            "$$|1 + z|^2 = (1 + 2\\cos\\theta)^2 + (2\\sin\\theta)^2 = 1 + 4\\cos\\theta + 4\\cos^2\\theta + 4\\sin^2\\theta = 5 + 4\\cos\\theta$$\n"
            "$$\\left|1 - \\frac{1}{2}z\\right|^2 = (1 - \\cos\\theta)^2 + (-\\sin\\theta)^2 = 1 - 2\\cos\\theta + \\cos^2\\theta + \\sin^2\\theta = 2 - 2\\cos\\theta$$\n"
            "両者が等しいので：\n"
            "$$5 + 4\\cos\\theta = 2 - 2\\cos\\theta \\implies 6\\cos\\theta = -3 \\implies \\cos\\theta = -\\frac{1}{2}$$\n"
            "このとき：\n"
            "$$|1 + z|^2 = 5 + 4\\left(-\\frac{1}{2}\\right) = 5 - 2 = 3$$\n"
            "したがって、$|1 + z| = \\left|1 - \\frac{1}{2}z\\right| = \\sqrt{3}$ である。\n"
            "よって、$\\mathbf{Q = 3}$ である。\n\n"
            "次に偏角を求める。\n"
            "$\\cos\\theta = -\\frac{1}{2}$ より、$\\sin\\theta = \\pm \\frac{\\sqrt{3}}{2}$ である。\n"
            "- **$\\sin\\theta = \\frac{\\sqrt{3}}{2}$（$\\theta = \\frac{2\\pi}{3}$）のとき**：\n"
            "  $$1 + z = 1 + 2\\left(-\\frac{1}{2} + i\\frac{\\sqrt{3}}{2}\\right) = 1 - 1 + i\\sqrt{3} = i\\sqrt{3}$$\n"
            "  純虚数で虚部が正であるから：\n"
            "  $$\\arg(1 + z) = \\frac{\\pi}{2} = \\frac{1}{2}\\pi$$\n"
            "  また：\n"
            "  $$1 - \\frac{1}{2}z = 1 - \\left(-\\frac{1}{2} + i\\frac{\\sqrt{3}}{2}\\right) = \\frac{3}{2} - i\\frac{\\sqrt{3}}{2} = \\sqrt{3}\\left(\\frac{\\sqrt{3}}{2} - \\frac{1}{2}i\\right)$$\n"
            "  したがって：\n"
            "  $$\\arg\\left(1 - \\frac{1}{2}z\\right) = -\\frac{\\pi}{6} = -\\frac{1}{6}\\pi$$\n"
            "- **$\\sin\\theta = -\\frac{\\sqrt{3}}{2}$（$\\theta = -\\frac{2\\pi}{3}$）のとき**：\n"
            "  同様に対称性より：\n"
            "  $$\\arg(1 + z) = -\\frac{\\pi}{2} = -\\frac{1}{2}\\pi, \\quad \\arg\\left(1 - \\frac{1}{2}z\\right) = \\frac{\\pi}{6} = \\frac{1}{6}\\pi$$\n"
            "複号同順でまとめると：\n"
            "$$\\arg(1 + z) = \\pm \\frac{1}{2}\\pi, \\quad \\arg\\left(1 - \\frac{1}{2}z\\right) = \\mp \\frac{1}{6}\\pi$$\n"
            "よって、$\\text{R} = 1, \\text{S} = 2$ より $\\mathbf{RS = 12}$、$\\text{T} = 1, \\text{U} = 6$ より $\\mathbf{TU = 16}$ である。\n\n"
            "**【考査考点】**\n"
            "複素数の極形式、複素数平面上の座標変換と三角形の面積公式、複素数の絶対値の性質、二等辺三角形条件の解析、偏角 arg の決定。"
        )
    },
    {
        "q_num": 5,
        "localKey": "math-q-III_1",
        "answer_ref": "MATH_C2:III_1",
        "answer": {
            "ABC": "235",
            "DEFG": "3222"
        },
        "title": "大問III 問1：指数関数の導関数と最小値問題",
        "points": [
            "指数関数の商の微分法および対数微分法の適用",
            "導関数の符号変化と極小値（最小値）の決定",
            "底の変換公式を用いた常用対数表現への書き換え"
        ],
        "solution": (
            "**【題目大意】**\n"
            "関数 $y = \\frac{2^{x^2}}{5^{3x}}$ ($x \\geq 0$) について、導関数 $\\frac{dy}{dx}$ を求め、$y$ が最小値をとるときの $x$ の値を常用対数を用いて表す。\n\n"
            "**【公式正解】**\n"
            "- $\\text{ABC} = 235$ ($\\frac{dy}{dx} = \\frac{2^{x^2}}{5^{3x}} (2x\\log_e 2 - 3\\log_e 5)$)\n"
            "- $\\text{DEFG} = 3222$ ($x = \\frac{3(1 - \\log_{10} 2)}{2\\log_{10} 2}$)\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "**(1) 導関数の計算**\n"
            "$y > 0$ であるから、両辺の自然対数をとる：\n"
            "$$\\log_e y = \\log_e \\left(\\frac{2^{x^2}}{5^{3x}}\\right) = \\log_e (2^{x^2}) - \\log_e (5^{3x}) = x^2 \\log_e 2 - 3x \\log_e 5$$\n"
            "両辺を $x$ で微分すると：\n"
            "$$\\frac{1}{y} \\frac{dy}{dx} = 2x \\log_e 2 - 3 \\log_e 5$$\n"
            "両辺に $y = \\frac{2^{x^2}}{5^{3x}}$ を掛けると：\n"
            "$$\\frac{dy}{dx} = \\frac{2^{x^2}}{5^{3x}} \\left(2x \\log_e 2 - 3 \\log_e 5\\right)$$\n"
            "したがって、$\\text{A} = 2, \\text{B} = 3, \\text{C} = 5$ より $\\mathbf{ABC = 235}$ である。\n\n"
            "**(2) $y$ が最小になる $x$ の決定**\n"
            "$\\frac{2^{x^2}}{5^{3x}} > 0$ であるから、$\\frac{dy}{dx} = 0$ となるのは：\n"
            "$$2x \\log_e 2 - 3 \\log_e 5 = 0 \\implies x = \\frac{3 \\log_e 5}{2 \\log_e 2}$$\n"
            "この前後で導関数の符号は負から正に変わるため、この $x$ において $y$ は最小となる。\n"
            "ここで底の変換公式（底を 10 とする常用対数）を用いる：\n"
            "$$\\frac{\\log_e 5}{\\log_e 2} = \\frac{\\frac{\\log_{10} 5}{\\log_{10} e}}{\\frac{\\log_{10} 2}{\\log_{10} e}} = \\frac{\\log_{10} 5}{\\log_{10} 2}$$\n"
            "さらに $\\log_{10} 5 = \\log_{10}\\left(\\frac{10}{2}\\right) = \\log_{10} 10 - \\log_{10} 2 = 1 - \\log_{10} 2$ であるから：\n"
            "$$x = \\frac{3(1 - \\log_{10} 2)}{2 \\log_{10} 2}$$\n"
            "問題文の形式 $x = \\frac{\\text{D}(1 - \\log_{10} \\text{E})}{\\text{F} \\log_{10} \\text{G}}$ と比較すると：\n"
            "$\\text{D} = 3, \\text{E} = 2, \\text{F} = 2, \\text{G} = 2$\n"
            "したがって、$\\mathbf{DEFG = 3222}$ である。\n\n"
            "**【考査考点】**\n"
            "対数微分法、合成関数の微分、増減表に基づく最小値の判定、常用対数の底の変換公式、$\\log_{10} 5 = 1 - \\log_{10} 2$ の恒等変形。"
        )
    },
    {
        "q_num": 6,
        "localKey": "math-q-III_2",
        "answer_ref": "MATH_C2:III_2",
        "answer": {
            "HIJKL": "22353",
            "MNOP": "7892",
            "Q": "9"
        },
        "title": "大問III 問2：指数不等式の対数化と整数解の評価",
        "points": [
            "不等式 y > 1000 の常用対数による2次不等式への帰着",
            "近似値 log_{10} 2 = 0.3 を適用した2次方程式の解の公式の計算",
            "平方根の数値評価による不等式を満たす最小の正の整数の決定"
        ],
        "solution": (
            "**【題目大意】**\n"
            "不等式 $\\frac{2^{x^2}}{5^{3x}} > 1000$ を常用対数を用いて変形し、$\\log_{10} 2 \\approx 0.3$ を用いて不等式を解くことで、不等式を満たす最小の正の整数 $x$ を求める。\n\n"
            "**【公式正解】**\n"
            "- $\\text{HIJKL} = 22353$ ($x^2 \\log_{10} 2 - 3x \\log_{10} 5 - 3 > 0$)\n"
            "- $\\text{MNOP} = 7892$ ($x > \\frac{7 + \\sqrt{89}}{2}$)\n"
            "- $\\text{Q} = 9$ (最小の正の整数 $x = 9$)\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "**(1) 常用対数による不等式の変形**\n"
            "不等式 $\\frac{2^{x^2}}{5^{3x}} > 1000$ の両辺の常用対数をとると：\n"
            "$$\\log_{10}\\left(\\frac{2^{x^2}}{5^{3x}}\\right) > \\log_{10} 1000$$\n"
            "左辺を展開し、右辺は $\\log_{10} 10^3 = 3$ であるから：\n"
            "$$x^2 \\log_{10} 2 - 3x \\log_{10} 5 > 3 \\iff x^2 \\log_{10} 2 - 3x \\log_{10} 5 - 3 > 0$$\n"
            "問題文の形式 $x^{\\text{H}} \\log_{10} \\text{I} - \\text{J} x \\log_{10} \\text{K} - \\text{L} > 0$ と比較すると：\n"
            "$\\text{H} = 2, \\text{I} = 2, \\text{J} = 3, \\text{K} = 5, \\text{L} = 3$\n"
            "したがって、$\\mathbf{HIJKL = 22353}$ である。\n\n"
            "**(2) 不等式の近似計算と解の導出**\n"
            "$\\log_{10} 2 = 0.3$ を用いると：\n"
            "$$\\log_{10} 5 = 1 - \\log_{10} 2 = 1 - 0.3 = 0.7$$\n"
            "これを不等式に代入する：\n"
            "$$0.3 x^2 - 3(0.7)x - 3 > 0 \\iff 0.3 x^2 - 2.1 x - 3 > 0$$\n"
            "両辺を 10 倍して：\n"
            "$$3x^2 - 21x - 30 > 0$$\n"
            "両辺を 3 で割ると：\n"
            "$$x^2 - 7x - 10 > 0$$\n"
            "2次方程式 $x^2 - 7x - 10 = 0$ の解は：\n"
            "$$x = \\frac{7 \\pm \\sqrt{(-7)^2 - 4(1)(-10)}}{2} = \\frac{7 \\pm \\sqrt{49 + 40}}{2} = \\frac{7 \\pm \\sqrt{89}}{2}$$\n"
            "$x \\geq 0$ であるから、不等式の解は：\n"
            "$$x > \\frac{7 + \\sqrt{89}}{2}$$\n"
            "したがって、$\\text{M} = 7, \\text{N} = 8, \\text{O} = 9, \\text{P} = 2$ より $\\mathbf{MNOP = 7892}$ である。\n\n"
            "**(3) 最小の正の整数 $x$ の特定**\n"
            "$\\sqrt{89}$ の大きさを評価する：\n"
            "$$9^2 = 81 < 89 < 100 = 10^2 \\implies 9 < \\sqrt{89} < 10$$\n"
            "より精密には、$9.4^2 = 88.36 < 89 < 9.5^2 = 90.25$ より $\\sqrt{89} \\approx 9.43$ である。\n"
            "したがって：\n"
            "$$\\frac{7 + \\sqrt{89}}{2} \\approx \\frac{7 + 9.43}{2} = \\frac{16.43}{2} = 8.215$$\n"
            "$x > 8.215$ を満たす最小の正の整数は $x = 9$ である。\n"
            "よって、$\\mathbf{Q = 9}$ である。\n\n"
            "**【考査考点】**\n"
            "指数不等式の対数変換、常用対数の近似計算、2次不等式の解法と解の公式の活用、無理数の近似評価と整数解の同定。"
        )
    },
    {
        "q_num": 7,
        "localKey": "math-q-IV_1",
        "answer_ref": "MATH_C2:IV_1",
        "answer": {
            "A": "0",
            "BC": "35",
            "D": "6"
        },
        "title": "大問IV 問1：三角関数の積の接線方程式と接点決定",
        "points": [
            "原点を通る接線が満たすべき条件式 f(t) = t f'(t) の立式",
            "積の微分法および合成関数の微分法による導関数の導出",
            "三角方程式の零点解析による接点の x 座標の決定"
        ],
        "solution": (
            "**【題目大意】**\n"
            "区間 $0 \\leq x \\leq \\pi$ で関数 $f(x) = x\\sin^2 x$ を考える。原点を通る接線 $l$（ただし $x$ 軸ではない）と接点 $(t, f(t))$ について、成り立つ等式、導関数 $f'(t)$、および接点の $x$ 座標 $t$ を求める。\n\n"
            "**【公式正解】**\n"
            "- $\\text{A} = 0$ ($f(t) = t f'(t)$、選択肢 $\\textcircled{0}$)\n"
            "- $\\text{BC} = 35$ ($f'(t) = \\sin^2 t + 2t\\sin t\\cos t$、B: 選択肢 $\\textcircled{3}$、C: 選択肢 $\\textcircled{5}$)\n"
            "- $\\text{D} = 6$ ($t = \\frac{\\pi}{2}$、選択肢 $\\textcircled{6}$)\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "**(1) 原点を通る接線が満たす等式**\n"
            "曲線 $y = f(x)$ 上の点 $(t, f(t))$ における接線 $l$ の方程式は：\n"
            "$$y - f(t) = f'(t)(x - t)$$\n"
            "接線 $l$ が原点 $(0, 0)$ を通るので、代入すると：\n"
            "$$0 - f(t) = f'(t)(0 - t) \\iff -f(t) = -t f'(t) \\iff f(t) = t f'(t)$$\n"
            "これは選択肢 $\\textcircled{0}$ であるから、$\\mathbf{A = 0}$ である。\n\n"
            "**(2) 導関数 $f'(t)$ の計算**\n"
            "$f(x) = x \\sin^2 x$ を積の微分法で微分する：\n"
            "$$f'(x) = (x)' \\sin^2 x + x (\\sin^2 x)' = 1 \\cdot \\sin^2 x + x \\cdot 2\\sin x (\\sin x)' = \\sin^2 x + 2x \\sin x \\cos x$$\n"
            "したがって：\n"
            "$$f'(t) = \\sin^2 t + 2t \\sin t \\cos t$$\n"
            "問題文の形式 $f'(t) = \\text{B} + 2t \\text{C}$ と比較すると：\n"
            "- $\\text{B} = \\sin^2 t$（選択肢 $\\textcircled{3}$）\n"
            "- $\\text{C} = \\sin t \\cos t$（選択肢 $\\textcircled{5}$）\n"
            "よって、$\\mathbf{BC = 35}$ である。\n\n"
            "**(3) 接点の $x$ 座標 $t$ の決定**\n"
            "$f(t) = t f'(t)$ に代入すると：\n"
            "$$t \\sin^2 t = t\\left(\\sin^2 t + 2t \\sin t \\cos t\\right)$$\n"
            "展開して整理すると：\n"
            "$$t \\sin^2 t = t \\sin^2 t + 2t^2 \\sin t \\cos t \\iff 2t^2 \\sin t \\cos t = 0$$\n"
            "接線 $l$ は $x$ 軸ではないから $t \\neq 0$ であり、$0 < t \\leq \\pi$ の範囲を考える。\n"
            "もし $\\sin t = 0$ ならば $t = \\pi$ となり、このとき $f(\\pi) = 0, f'(\\pi) = 0$ より接線は $y = 0$（$x$ 軸）となって問題の条件に反する。\n"
            "したがって、$\\cos t = 0$ でなければならない。\n"
            "区間 $0 < t < \\pi$ において $\\cos t = 0$ を解くと：\n"
            "$$t = \\frac{\\pi}{2}$$\n"
            "これは選択肢 $\\textcircled{6}$ であるから、$\\mathbf{D = 6}$ である。\n\n"
            "**【考査考点】**\n"
            "微分法による接線方程式の導出、原点通過条件の代数化、積の微分法・合成関数の微分法、三角関数の値の範囲と方程式の解法。"
        )
    },
    {
        "q_num": 8,
        "localKey": "math-q-IV_2",
        "answer_ref": "MATH_C2:IV_2",
        "answer": {
            "EFG": "089",
            "HIJKLM": "116214"
        },
        "title": "大問IV 問2：部分積分法と曲線および接線で囲まれる面積",
        "points": [
            "半角公式と部分積分法を用いた不定積分 \\int x \\sin^2 x dx の計算",
            "接線方程式 y = x の導出と関数の上下関係の評価",
            "定積分による囲まれた面積 S = \\frac{1}{16}\\pi^2 - \\frac{1}{4} の完全導出"
        ],
        "solution": (
            "**【題目大意】**\n"
            "関数 $f(x) = x\\sin^2 x$ の不定積分を求め、曲線 $y = f(x)$ と接線 $l$ で囲まれる部分の面積 $S$ を計算する。\n\n"
            "**【公式正解】**\n"
            "- $\\text{EFG} = 089$ (E: $\\frac{1}{8}$[選択肢0], F: $\\sin 2x$[選択肢8], G: $\\cos 2x$[選択肢9])\n"
            "- $\\text{HIJKLM} = 116214$ ($S = \\frac{1}{16}\\pi^2 - \\frac{1}{4}$)\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "**(1) 不定積分の計算**\n"
            "半角の公式 $\\sin^2 x = \\frac{1 - \\cos 2x}{2}$ を用いて被積分関数を変形する：\n"
            "$$\\int f(x) \\, dx = \\int x \\sin^2 x \\, dx = \\int x \\left(\\frac{1 - \\cos 2x}{2}\\right) dx = \\frac{1}{2} \\int x \\, dx - \\frac{1}{2} \\int x \\cos 2x \\, dx$$\n"
            "第1項は：\n"
            "$$\\frac{1}{2} \\int x \\, dx = \\frac{1}{4} x^2$$\n"
            "第2項に部分積分法を適用する：\n"
            "$$\\int x \\cos 2x \\, dx = x \\left(\\frac{\\sin 2x}{2}\\right) - \\int 1 \\cdot \\left(\\frac{\\sin 2x}{2}\\right) dx = \\frac{1}{2} x \\sin 2x - \\frac{1}{2} \\left(-\\frac{\\cos 2x}{2}\\right) = \\frac{1}{2} x \\sin 2x + \\frac{1}{4} \\cos 2x$$\n"
            "これらを合わせると：\n"
            "$$\\int f(x) \\, dx = \\frac{1}{4} x^2 - \\frac{1}{2}\\left(\\frac{1}{2} x \\sin 2x + \\frac{1}{4} \\cos 2x\\right) + C = \\frac{1}{4} x^2 - \\frac{1}{4} x \\sin 2x - \\frac{1}{8} \\cos 2x + C$$\n"
            "全体を $\\frac{1}{8}$ でくくり出すと：\n"
            "$$\\int f(x) \\, dx = \\frac{1}{8} \\left(2x^2 - 2x \\sin 2x - \\cos 2x\\right) + C$$\n"
            "問題文の形式 $\\text{E} (2x^2 - 2x \\text{F} - \\text{G}) + C$ と比較すると：\n"
            "- $\\text{E} = \\frac{1}{8}$（選択肢 $\\textcircled{0}$）\n"
            "- $\\text{F} = \\sin 2x$（選択肢 $\\textcircled{8}$）\n"
            "- $\\text{G} = \\cos 2x$（選択肢 $\\textcircled{9}$）\n"
            "したがって、$\\mathbf{EFG = 089}$ である。\n\n"
            "**(2) 面積 $S$ の計算**\n"
            "接点 $t = \\frac{\\pi}{2}$ において：\n"
            "$$f\\left(\\frac{\\pi}{2}\\right) = \\frac{\\pi}{2} \\sin^2\\left(\\frac{\\pi}{2}\\right) = \\frac{\\pi}{2} \\times 1^2 = \\frac{\\pi}{2}$$\n"
            "$$f'\\left(\\frac{\\pi}{2}\\right) = \\sin^2\\left(\\frac{\\pi}{2}\\right) + 2\\left(\\frac{\\pi}{2}\\right) \\sin\\left(\\frac{\\pi}{2}\\right) \\cos\\left(\\frac{\\pi}{2}\\right) = 1 + \\pi \\times 1 \\times 0 = 1$$\n"
            "したがって、原点を通る接線 $l$ の方程式は $y = x$ である。\n"
            "区間 $0 \\leq x \\leq \\frac{\\pi}{2}$ において、$0 \\leq \\sin^2 x \\leq 1$ であるから：\n"
            "$$f(x) = x \\sin^2 x \\leq x$$\n"
            "すなわち、この区間で直線 $y = x$ は常に曲線 $y = f(x)$ の上側にある。\n"
            "したがって、求める面積 $S$ は：\n"
            "$$S = \\int_0^{\\pi/2} (x - f(x)) \\, dx = \\left[ \\frac{1}{2} x^2 \\right]_0^{\\pi/2} - \\int_0^{\\pi/2} f(x) \\, dx$$\n"
            "まず直線の積分は：\n"
            "$$\\left[ \\frac{1}{2} x^2 \\right]_0^{\\pi/2} = \\frac{1}{2} \\left(\\frac{\\pi}{2}\\right)^2 = \\frac{\\pi^2}{8}$$\n"
            "次に $f(x)$ の定積分を不定積分の結果を用いて計算する：\n"
            "$$\\int_0^{\\pi/2} f(x) \\, dx = \\left[ \\frac{1}{8} (2x^2 - 2x \\sin 2x - \\cos 2x) \\right]_0^{\\pi/2}$$\n"
            "- $x = \\frac{\\pi}{2}$ のとき：\n"
            "  $$2\\left(\\frac{\\pi}{2}\\right)^2 - 2\\left(\\frac{\\pi}{2}\\right) \\sin\\pi - \\cos\\pi = \\frac{\\pi^2}{2} - 0 - (-1) = \\frac{\\pi^2}{2} + 1$$\n"
            "- $x = 0$ のとき：\n"
            "  $$2(0)^2 - 2(0) \\sin 0 - \\cos 0 = -1$$\n"
            "したがって：\n"
            "$$\\int_0^{\\pi/2} f(x) \\, dx = \\frac{1}{8} \\left[ \\left(\\frac{\\pi^2}{2} + 1\\right) - (-1) \\right] = \\frac{1}{8} \\left(\\frac{\\pi^2}{2} + 2\\right) = \\frac{\\pi^2}{16} + \\frac{1}{4}$$\n"
            "これより面積 $S$ は：\n"
            "$$S = \\frac{\\pi^2}{8} - \\left(\\frac{\\pi^2}{16} + \\frac{1}{4}\\right) = \\frac{\\pi^2}{16} - \\frac{1}{4}$$\n"
            "問題文の形式 $S = \\frac{\\text{H}}{\\text{IJ}} \\pi^{\\text{K}} - \\frac{\\text{L}}{\\text{M}}$ と比較すると：\n"
            "$\\text{H} = 1, \\text{IJ} = 16, \\text{K} = 2, \\text{L} = 1, \\text{M} = 4$\n"
            "したがって、$\\mathbf{HIJKLM = 116214}$ である。\n\n"
            "**【考査考点】**\n"
            "半角の公式と部分積分法、積の定積分の計算技法、曲線の上下関係に基づく面積の立式、三角関数の特殊角における値の正確な代入評価。"
        )
    }
]

def main():
    work_dir = Path("work/2017-1-math-c2")
    docs_dir = Path("docs/explanations")
    work_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)

    json_path = work_dir / "explanations.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(math_c2_sections, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(math_c2_sections)} questions to {json_path}")

    md_lines = [
        "# 2017-1 EJU 数学（コース2）詳細解答と徹底解説",
        "",
        "**対象試験**：2017年度第1回（2017年6月実施）日本留学試験（EJU）数学コース2  ",
        "**大問構成**：大問I（問1, 問2）、大問II（問1, 問2）、大問III（問1, 問2）、大問IV（問1, 問2）（全8小問）  ",
        "**準拠公式正解**：JASSO 公式正解発表完全準拠",
        "",
        "---",
        ""
    ]

    for q in math_c2_sections:
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

    md_path = docs_dir / "2017-1-math-c2-solutions.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))
    print(f"Wrote markdown solutions to {md_path}")

if __name__ == "__main__":
    main()
