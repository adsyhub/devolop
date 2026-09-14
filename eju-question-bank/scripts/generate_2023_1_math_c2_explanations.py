#!/usr/bin/env python3
"""Generate comprehensive explanations for 2023-1 EJU Mathematics Course 2."""

import json
from pathlib import Path

# Load Math C1 for shared Question I
math_c1 = json.loads(Path("/workspace/Develop/eju-question-bank/work/2023-1-math-c1/explanations.json").read_text(encoding="utf-8"))

explanations = {
    "session": "2023-1",
    "subject": "MATHEMATICS",
    "course": "COURSE_2",
    "formCode": "MATHEMATICS_COURSE_2_JA",
    "sections": [
        math_c1["sections"][0],  # I_1
        math_c1["sections"][1],  # I_2
        {
            "sectionId": "II_1",
            "sectionTitle": "第II問 問1：平面ベクトルの内積・基底分解と対角線の交点比",
            "points": [
                "垂直条件 $\\vec{u} \\perp \\vec{v} \\iff \\vec{u} \\cdot \\vec{v} = 0$ による内積の導出",
                "ベクトルの大きさの 2 乗展開による内積 $\\vec{c} \\cdot \\vec{a}$ の決定",
                "一次独立な基底への分解と連立方程式による係数決定",
                "同一直線上の点（共線条件）による対角線の交点比の計算"
            ],
            "officialAnswers": {
                "AB": "32",
                "C": "4",
                "D": "2",
                "EFG": "838",
                "HI": "34",
                "J": "2",
                "K": "0",
                "L": "5"
            },
            "detailedSolution": (
                "### 【第II問 問1】詳細解答と解説\n\n"
                "四角形 $OABC$ において、$\\angle OAB = 90^\\circ, \\angle OCB = 90^\\circ$ である。\n"
                "辺の長さは $OA = 2, OC = \\sqrt{2}$、対角線 $AC = \\sqrt{3}$。\n"
                "$\\overrightarrow{OA} = \\vec{a}, \\overrightarrow{OB} = \\vec{b}, \\overrightarrow{OC} = \\vec{c}$ とおく。\n"
                "大きさは $|\\vec{a}| = 2 \\implies |\\vec{a}|^2 = 4$、$|\\vec{c}| = \\sqrt{2} \\implies |\\vec{c}|^2 = 2$ である。\n\n"
                "#### (1) 内積 $\\vec{c} \\cdot \\vec{a}$ の計算\n"
                "$\\overrightarrow{AC} = \\vec{c} - \\vec{a}$ であるから、その大きさの 2 乗を計算する：\n"
                "$$|\\overrightarrow{AC}|^2 = |\\vec{c} - \\vec{a}|^2 = |\\vec{c}|^2 - 2\\vec{c} \\cdot \\vec{a} + |\\vec{a}|^2$$\n"
                "与えられた数値を代入すると：\n"
                "$$(\\sqrt{3})^2 = 2 - 2\\vec{c} \\cdot \\vec{a} + 4$$\n"
                "$$3 = 6 - 2\\vec{c} \\cdot \\vec{a} \\implies 2\\vec{c} \\cdot \\vec{a} = 3 \\implies \\vec{c} \\cdot \\vec{a} = \\frac{3}{2}$$\n"
                "問題文の形式 $\\frac{\\text{A}}{\\text{B}}$ より：\n"
                "$$\\mathbf{A = 3, B = 2} \\implies \\mathbf{AB = 32}$$\n\n"
                "#### (2) 内積 $\\vec{a} \\cdot \\vec{b}$ と $\\vec{b} \\cdot \\vec{c}$ の計算\n"
                "1. $\\angle OAB = 90^\\circ$ より $\\overrightarrow{OA} \\perp \\overrightarrow{AB}$ である。\n"
                "   $$\\vec{a} \\cdot (\\vec{b} - \\vec{a}) = 0 \\implies \\vec{a} \\cdot \\vec{b} - |\\vec{a}|^2 = 0 \\implies \\vec{a} \\cdot \\vec{b} = |\\vec{a}|^2 = 4$$\n"
                "   よって、$\\mathbf{C = 4}$。\n"
                "2. $\\angle OCB = 90^\\circ$ より $\\overrightarrow{OC} \\perp \\overrightarrow{CB}$ である。\n"
                "   $$\\vec{c} \\cdot (\\vec{b} - \\vec{c}) = 0 \\implies \\vec{c} \\cdot \\vec{b} - |\\vec{c}|^2 = 0 \\implies \\vec{b} \\cdot \\vec{c} = |\\vec{c}|^2 = 2$$\n"
                "   よって、$\\mathbf{D = 2}$。\n\n"
                "#### (3) $\\vec{b}$ を $\\vec{a}$ と $\\vec{c}$ で表す（係数 $s, t$ の決定）\n"
                "$\\vec{b} = s\\vec{a} + t\\vec{c}$ とおく。\n"
                "1. 両辺と $\\vec{a}$ の内積をとる：\n"
                "   $$\\vec{a} \\cdot \\vec{b} = s|\\vec{a}|^2 + t(\\vec{a} \\cdot \\vec{c})$$\n"
                "   $$4 = 4s + \\frac{3}{2}t$$\n"
                "   両辺に 2 を掛けると：\n"
                "   $$8s + 3t = 8$$\n"
                "   問題文の形式 $\\text{E}s + \\text{F}t = \\text{G}$ と比較して：\n"
                "   $$\\mathbf{E = 8, F = 3, G = 8} \\implies \\mathbf{EFG = 838}$$\n"
                "2. 両辺と $\\vec{c}$ の内積をとる：\n"
                "   $$\\vec{b} \\cdot \\vec{c} = s(\\vec{a} \\cdot \\vec{c}) + t|\\vec{c}|^2$$\n"
                "   $$2 = \\frac{3}{2}s + 2t$$\n"
                "   両辺に 2 を掛けると：\n"
                "   $$3s + 4t = 4$$\n"
                "   問題文の形式 $\\text{H}s + \\text{I}t = 4$ と比較して：\n"
                "   $$\\mathbf{H = 3, I = 4} \\implies \\mathbf{HI = 34}$$\n\n"
                "連立方程式を解く：\n"
                "$$\\begin{cases} 8s + 3t = 8 & \\times 4 \\implies 32s + 12t = 32 \\\\ 3s + 4t = 4 & \\times 3 \\implies 9s + 12t = 12 \\end{cases}$$\n"
                "引き算すると：$23s = 20 \\implies s = \\frac{20}{23}$。\n"
                "代入して：$4t = 4 - 3\\left(\\frac{20}{23}\\right) = \\frac{92 - 60}{23} = \\frac{32}{23} \\implies t = \\frac{8}{23}$。\n"
                "選択肢一覧より：\n"
                "- $s = \\frac{20}{23}$ は $\\textcircled{2}$ に対応。よって、$\\mathbf{J = 2}$。\n"
                "- $t = \\frac{8}{23}$ は $\\textcircled{0}$ に対応。よって、$\\mathbf{K = 0}$。\n\n"
                "#### (4) 対角線の交点 $D$ と $\\overrightarrow{OD}$\n"
                "交点 $D$ は線分 $AC$ 上にあるため、実数 $u$ を用いて次のように表せる：\n"
                "$$\\overrightarrow{OD} = (1 - u)\\vec{a} + u\\vec{c}$$\n"
                "また、$D$ は線分 $OB$ 上にあるため、実数 $k$ を用いて：\n"
                "$$\\overrightarrow{OD} = k\\vec{b} = k(s\\vec{a} + t\\vec{c}) = ks\\vec{a} + kt\\vec{c}$$\n"
                "$\\vec{a}$ と $\\vec{c}$ は一次独立であるから、係数を比較すると：\n"
                "$$ks = 1 - u, \\quad kt = u$$\n"
                "2 式を加えると：\n"
                "$$k(s + t) = 1 \\implies k = \\frac{1}{s + t}$$\n"
                "求めた $s, t$ の値を代入すると：\n"
                "$$s + t = \\frac{20}{23} + \\frac{8}{23} = \\frac{28}{23}$$\n"
                "$$k = \\frac{1}{\\frac{28}{23}} = \\frac{23}{28}$$\n"
                "したがって、$\\overrightarrow{OD} = \\frac{23}{28}\\vec{b}$ である。\n"
                "選択肢一覧より、$\\frac{23}{28}$ は $\\textcircled{5}$ に対応する。\n"
                "よって、$\\mathbf{L = 5}$。"
            )
        },
        {
            "sectionId": "II_2",
            "sectionTitle": "第II問 問2：複素数平面上の商の幾何学的意味・三角形の形状決定",
            "points": [
                "複素数の商 $\\frac{z_3 - z_2}{z_2 - z_1}$ の偏角と直交・共線条件",
                "オイラーの公式・極形式を用いた三角関数の積の簡約化",
                "直角三角形の角の決定と複素数の偏角・絶対値の幾何的同定"
            ],
            "officialAnswers": {
                "M": "0",
                "N": "3",
                "OP": "-8",
                "Q": "0",
                "RS": "-1",
                "TU": "23",
                "V": "2",
                "W": "2",
                "X": "3",
                "Y": "6"
            },
            "detailedSolution": (
                "### 【第II問 問2】詳細解答と解説\n\n"
                "複素数平面上の異なる 3 点 $A(z_1), B(z_2), C(z_3)$ に対して：\n"
                "$$\\frac{z_3 - z_2}{z_2 - z_1} = a + bi$$\n"
                "とおく。\n\n"
                "#### (1) 実部・虚部が 0 のときの幾何学的性質\n"
                "$\\frac{z_3 - z_2}{z_2 - z_1}$ の偏角 $\\theta = \\arg\\left(\\frac{z_3 - z_2}{z_2 - z_1}\\right)$ は、ベクトル $\\overrightarrow{BA}$ から $\\overrightarrow{BC}$ への回転角を表す。\n"
                "1. **$a = 0$ のとき**：\n"
                "   商は純虚数 $bi$ となるため、偏角は $\\pm \\frac{\\pi}{2}$ である。\n"
                "   したがって、直線 $AB$ と直線 $BC$ は垂直となる。\n"
                "   選択肢 $\\textcircled{0}$「直線 ABと直線 BCは垂直」が適する。\n"
                "   よって、$\\mathbf{M = 0}$。\n"
                "2. **$b = 0$ のとき**：\n"
                "   商は実数 $a$ となるため、偏角は $0$ または $\\pi$ である。\n"
                "   したがって、$A, B, C$ は一直線上にあり、直線 $AB$ と直線 $BC$ は同一直線となる。\n"
                "   選択肢 $\\textcircled{3}$「直線 ABと直線 BCは同一直線」が適する。\n"
                "   よって、$\\mathbf{N = 3}$。\n\n"
                "#### (2) 三角関数の複素数表現と角の決定\n"
                "与えられた $a$ の式は：\n"
                "$$a = \\frac{(i\\cos A + \\sin A)(i\\cos B - \\sin B)}{\\cos C - i\\sin C}$$\n"
                "各因数をオイラーの公式または極形式に変形する：\n"
                "- $i\\cos A + \\sin A = i(\\cos A - i\\sin A) = i e^{-iA}$\n"
                "- $i\\cos B - \\sin B = i(\\cos B + i\\sin B) = i e^{iB}$\n"
                "分子の積は：\n"
                "$$(i e^{-iA})(i e^{iB}) = i^2 e^{i(B - A)} = -e^{i(B - A)}$$\n"
                "分母は：\n"
                "$$\\cos C - i\\sin C = e^{-iC}$$\n"
                "したがって、商は：\n"
                "$$\\frac{-e^{i(B - A)}}{e^{-iC}} = -e^{i(B - A + C)} = -(\\cos(-A + B + C) + i\\sin(-A + B + C))$$\n"
                "問題文の形式 $-(\\cos P + i\\sin P)$ より、先頭の符号は負（$-$）で、偏角の中身は $-A + B + C$ である。\n"
                "選択肢一覧より、$\\textcircled{8}$ が $(-A + B + C)$ に対応する。\n"
                "よって、$\\mathbf{O = -, P = 8} \\implies \\mathbf{OP = -8}$。\n\n"
                "$a$ は実数であるから、虚部が 0 でなければならない：\n"
                "$$\\sin(-A + B + C) = 0$$\n"
                "三角形の内角の和は $A + B + C = \\pi$ であるから、$-A + B + C = \\pi - 2A$ と表せる。\n"
                "$$\\sin(\\pi - 2A) = \\sin 2A = 0$$\n"
                "$A$ は三角形の内角なので $0 < A < \\pi \\implies 0 < 2A < 2\\pi$。\n"
                "したがって：\n"
                "$$2A = \\pi \\implies A = \\frac{\\pi}{2}$$\n"
                "したがって、$\\triangle ABC$ は $A = \\frac{\\pi}{2}$ の直角三角形である。\n"
                "選択肢 $\\textcircled{0}$ が $A$ に該当する。よって、$\\mathbf{Q = 0}$。\n\n"
                "このとき、$-A + B + C = \\pi - 2A = 0$ となるため：\n"
                "$$a = -\\cos 0 = -1$$\n"
                "問題文の形式 $a = \\text{RS}$ より：\n"
                "$$\\mathbf{R = -, S = 1} \\implies \\mathbf{RS = -1}$$\n\n"
                "#### (3) 偏角と辺の比・三角形の内角の決定\n"
                "$a = -1, b = \\sqrt{3}$ であるから：\n"
                "$$\\frac{z_3 - z_2}{z_2 - z_1} = -1 + \\sqrt{3}i = 2\\left(-\\frac{1}{2} + \\frac{\\sqrt{3}}{2}i\\right) = 2\\left(\\cos\\frac{2}{3}\\pi + i\\sin\\frac{2}{3}\\pi\\right)$$\n"
                "したがって：\n"
                "- 偏角 $\\theta = \\frac{2}{3}\\pi \\implies \\mathbf{T = 2, U = 3} \\implies \\mathbf{TU = 23}$。\n"
                "- 絶対値 $\\left|\\frac{z_3 - z_2}{z_2 - z_1}\\right| = 2 \\implies \\mathbf{V = 2}$。\n\n"
                "幾何学的に、$\\overrightarrow{BA}$ から $\\overrightarrow{BC}$ への角が $\\frac{2}{3}\\pi = 120^\\circ$ の外角に相当するため、内角 $B$ は：\n"
                "$$B = \\pi - \\frac{2}{3}\\pi = \\frac{\\pi}{3} \\implies X = 3$$\n"
                "$A = \\frac{\\pi}{2} \\implies W = 2$。\n"
                "残る内角 $C$ は：\n"
                "$$C = \\pi - A - B = \\pi - \\frac{\\pi}{2} - \\frac{\\pi}{3} = \\frac{\\pi}{6} \\implies Y = 6$$\n"
                "よって、$\\mathbf{W = 2, X = 3, Y = 6}$。"
            )
        },
        {
            "sectionId": "III",
            "sectionTitle": "第III問：分段関数の定積分・微積分学の基本定理と最大値問題",
            "points": [
                "分段関数の定積分の定義と区間分割による積分の計算",
                "パラメータ $a$ の動く区間における関数の単調性と不等式評価",
                "微分積分学の基本定理 $S'(a) = f(a+2) - f(a)$ による増減表と極値決定",
                "高次式の次数下げによる最大値の有理化・根号計算"
            ],
            "officialAnswers": {
                "A": "2",
                "BCD": "103",
                "E": "0",
                "F": "0",
                "GHIJK": "-1322",
                "LMN": "103",
                "OP": "42",
                "QR": "22",
                "ST": "22",
                "UVWX": "2423"
            },
            "detailedSolution": (
                "### 【第III問】詳細解答と解説\n\n"
                "与えられた関数は：\n"
                "$$f(x) = \\begin{cases} x + 2 & (x < 0) \\\\ -x^2 + x + 2 & (x \\ge 0) \\end{cases}$$\n"
                "積分区間の幅が 2 の関数 $S(a) = \\int_{a}^{a+2} f(x) \\, dx$ を考える。\n\n"
                "#### (1) 端点 $a = -2$ および $a = 0$ での積分値\n"
                "1. **$a = -2$ のとき**：積分区間は $[-2, 0]$ であり、常に $x \\le 0$ である：\n"
                "   $$S(-2) = \\int_{-2}^0 (x + 2) \\, dx = \\left[\\frac{x^2}{2} + 2x\\right]_{-2}^0 = 0 - \\left(\\frac{4}{2} - 4\\right) = -(-2) = 2$$\n"
                "   よって、$\\mathbf{A = 2}$。\n"
                "2. **$a = 0$ のとき**：積分区間は $[0, 2]$ であり、常に $x \\ge 0$ である：\n"
                "   $$S(0) = \\int_0^2 (-x^2 + x + 2) \\, dx = \\left[-\\frac{x^3}{3} + \\frac{x^2}{2} + 2x\\right]_0^2 = -\\frac{8}{3} + 2 + 4 = \\frac{10}{3}$$\n"
                "   よって、$\\mathbf{BCD = 103}$。\n\n"
                "#### (2) 外側領域での単調性と不等式評価\n"
                "- $a < -2$ のとき：区間 $[a, a+2] \\subset (-\\infty, 0)$ である。\n"
                "  $x < 0$ において $f(x) = x + 2$ は単調増加関数であるから、区間を左にずらすほど被積分関数は小さくなる。\n"
                "  したがって、$a < -2$ のとき $S(a) < S(-2)$ である。\n"
                "  選択肢 $\\textcircled{0}$（$<$）が適する。よって、$\\mathbf{E = 0}$。\n"
                "- $a > 0$ のとき：区間 $[a, a+2] \\subset (0, \\infty)$ である。\n"
                "  $f(x) = -x^2 + x + 2$ は $x \\ge \\frac{1}{2}$ で単調減少する。\n"
                "  $a > 0$ では右にずらすほど $f(x)$ の値は急速に減少するため、$S(a) < S(0)$ である。\n"
                "  選択肢 $\\textcircled{0}$（$<$）が適する。よって、$\\mathbf{F = 0}$。\n\n"
                "#### (3) $-2 \\le a \\le 0$ における $S(a)$ の導出と導関数\n"
                "このとき、積分区間 $[a, a+2]$ は $x = 0$ をまたぐため、2 つの区間に分割する：\n"
                "$$S(a) = \\int_a^0 (x + 2) \\, dx + \\int_0^{a+2} (-x^2 + x + 2) \\, dx$$\n"
                "それぞれの積分を計算する：\n"
                "1. $\\int_a^0 (x + 2) \\, dx = \\left[\\frac{x^2}{2} + 2x\\right]_a^0 = -\\left(\\frac{a^2}{2} + 2a\\right) = -\\frac{1}{2}a^2 - 2a$\n"
                "2. $\\int_0^{a+2} (-x^2 + x + 2) \\, dx = \\left[-\\frac{x^3}{3} + \\frac{x^2}{2} + 2x\\right]_0^{a+2} = -\\frac{(a+2)^3}{3} + \\frac{(a+2)^2}{2} + 2(a+2)$\n"
                "展開して合算すると：\n"
                "$$-\\frac{a^3 + 6a^2 + 12a + 8}{3} + \\frac{a^2 + 4a + 4}{2} + 2a + 4$$\n"
                "$$= -\\frac{1}{3}a^3 + \\left(-2 + \\frac{1}{2}\\right)a^2 + (-4 + 2 + 2)a + \\left(-\\frac{8}{3} + 2 + 4\\right) = -\\frac{1}{3}a^3 - \\frac{3}{2}a^2 + \\frac{10}{3}$$\n"
                "これに第 1 区間の $-\\frac{1}{2}a^2 - 2a$ を加えると：\n"
                "$$S(a) = -\\frac{1}{3}a^3 - 2a^2 - 2a + \\frac{10}{3}$$\n"
                "問題文の形式 $\\frac{\\text{GH}}{\\text{I}}a^3 - \\text{J}a^2 - \\text{K}a + \\frac{\\text{LM}}{\\text{N}}$ と比較して：\n"
                "$$\\mathbf{GHIJK = -1322, \\quad LMN = 103}$$\n\n"
                "導関数 $S'(a)$ は、微積分学の基本定理より：\n"
                "$$S'(a) = f(a+2) \\cdot 1 - f(a) \\cdot 1$$\n"
                "$a+2 \\ge 0$ より $f(a+2) = -(a+2)^2 + (a+2) + 2 = -a^2 - 3a$\n"
                "$a \\le 0$ より $f(a) = a + 2$\n"
                "$$S'(a) = (-a^2 - 3a) - (a + 2) = -a^2 - 4a - 2$$\n"
                "問題文の形式 $S'(a) = -a^2 - \\text{O}a - \\text{P}$ より：\n"
                "$$\\mathbf{O = 4, P = 2} \\implies \\mathbf{OP = 42}$$\n\n"
                "#### (4) 極大値および最大値の決定\n"
                "$S'(a) = 0$ を解くと：\n"
                "$$a^2 + 4a + 2 = 0 \\implies a = \\frac{-4 \\pm \\sqrt{16 - 8}}{2} = -2 \\pm \\sqrt{2}$$\n"
                "定義域 $-2 \\le a \\le 0$ にある解は：\n"
                "$$a = -2 + \\sqrt{2}$$\n"
                "$S'(a)$ の符号は負から正、そして正から負へと変わるため、$a = -2 + \\sqrt{2}$ で極大かつ最大となる。\n"
                "問題文の形式 $a = -\\text{Q} + \\sqrt{\\text{R}}$ および最大をとる $a = -\\text{S} + \\sqrt{\\text{T}}$ より：\n"
                "$$\\mathbf{QR = 22, \\quad ST = 22}$$\n\n"
                "$S(-2 + \\sqrt{2})$ の最大値を次数下げで計算する：\n"
                "$a^2 + 4a + 2 = 0 \\implies a^2 = -4a - 2$ より：\n"
                "$$a^3 = a(-4a - 2) = -4a^2 - 2a = -4(-4a - 2) - 2a = 14a + 8$$\n"
                "これを $S(a)$ に代入すると：\n"
                "$$S(a) = -\\frac{1}{3}(14a + 8) - 2(-4a - 2) - 2a + \\frac{10}{3}$$\n"
                "$$= -\\frac{14}{3}a - \\frac{8}{3} + 8a + 4 - 2a + \\frac{10}{3} = \\frac{4}{3}a + \\frac{14}{3}$$\n"
                "$a = -2 + \\sqrt{2}$ を代入する：\n"
                "$$S(-2 + \\sqrt{2}) = \\frac{4}{3}(-2 + \\sqrt{2}) + \\frac{14}{3} = -\\frac{8}{3} + \\frac{14}{3} + \\frac{4\\sqrt{2}}{3} = 2 + \\frac{4\\sqrt{2}}{3}$$\n"
                "問題文の形式 $\\text{U} + \\frac{\\text{V}\\sqrt{\\text{W}}}{\\text{X}}$ と比較して：\n"
                "$$\\mathbf{U = 2, V = 4, W = 2, X = 3} \\implies \\mathbf{UVWX = 2423}$$\n\n"
                "**【解法テクニック・易錯点】**\n"
                "- 3次式に無理数 $-2+\\sqrt{2}$ を直接代入して3乗展開すると計算ミスの温床になります。割り算または関係式 $a^2 = -4a - 2$ による次数下げ（剰余の定理）を用いることで、1次式 $\\frac{4}{3}a + \\frac{14}{3}$ に落とし込み、瞬時に正確な値を導けます。"
            )
        },
        {
            "sectionId": "IV",
            "sectionTitle": "第IV問：定積分で定義された関数・部分積分と曲線の接線",
            "points": [
                "定積分の微分法 $\\frac{d}{dx}\\int_0^x g(t)dt = g(x)$ による極値条件",
                "三角関数の半角・倍角公式による被積分関数の変形",
                "部分積分法 $\\int t \\cos 4t dt$ による不定積分の厳密計算",
                "極値の比較による最大値の決定と指定点における接線の方程式"
            ],
            "officialAnswers": {
                "A": "4",
                "BCD": "512",
                "EFG": "124",
                "HI": "12",
                "JKL": "124",
                "MNO": "184",
                "PQ": "18",
                "RST": "972",
                "UVW": "382"
            },
            "detailedSolution": (
                "### 【第IV問】詳細解答と解説\n\n"
                "与えられた関数は：\n"
                "$$f(x) = \\int_{0}^{x} t(a\\sin^2 2t - 1) \\, dt \\quad \\left(0 < x < \\frac{\\pi}{2}\\right)$$\n\n"
                "#### (1) 極値条件によるパラメータ $a$ の決定と別の極値\n"
                "微分積分学の基本定理より：\n"
                "$$f'(x) = x(a\\sin^2 2x - 1)$$\n"
                "$f(x)$ が $x = \\frac{\\pi}{12}$ で極値をもつので、$f'\\left(\\frac{\\pi}{12}\\right) = 0$ が成り立つ：\n"
                "$$\\frac{\\pi}{12} \\left(a\\sin^2\\left(2 \\cdot \\frac{\\pi}{12}\\right) - 1\\right) = 0$$\n"
                "$$\\sin\\frac{\\pi}{6} = \\frac{1}{2} \\implies a\\left(\\frac{1}{2}\\right)^2 - 1 = 0 \\implies \\frac{a}{4} = 1 \\implies a = 4$$\n"
                "よって、$\\mathbf{A = 4}$。\n\n"
                "別の極値となる $x$ を求める：\n"
                "$$f'(x) = x(4\\sin^2 2x - 1) = 0$$\n"
                "$0 < x < \\frac{\\pi}{2}$ では $x > 0$ であるから：\n"
                "$$\\sin^2 2x = \\frac{1}{4} \\implies \\sin 2x = \\frac{1}{2} \\quad (\\because 0 < 2x < \\pi)$$\n"
                "したがって：\n"
                "$$2x = \\frac{\\pi}{6}, \\quad \\frac{5\\pi}{6} \\implies x = \\frac{\\pi}{12}, \\quad \\frac{5\\pi}{12}$$\n"
                "したがって、別の極値をとる点は $x = \\frac{5}{12}\\pi$ である。\n"
                "問題文の形式 $\\frac{\\text{B}}{\\text{CD}}\\pi$ より：\n"
                "$$\\mathbf{B = 5, CD = 12} \\implies \\mathbf{BCD = 512}$$\n\n"
                "#### (2) 被積分関数の変形と部分積分による $f(x)$ の決定\n"
                "半角の公式 $\\sin^2 2t = \\frac{1 - \\cos 4t}{2}$ を代入する：\n"
                "$$a\\sin^2 2t - 1 = 4\\left(\\frac{1 - \\cos 4t}{2}\\right) - 1 = 2(1 - \\cos 4t) - 1 = 1 - 2\\cos 4t$$\n"
                "問題文の形式 $t(\\text{E} - \\text{F}\\cos \\text{G}t)$ と比較して：\n"
                "$$\\mathbf{E = 1, F = 2, G = 4} \\implies \\mathbf{EFG = 124}$$\n\n"
                "被積分関数を展開して定積分を実行する：\n"
                "$$f(x) = \\int_0^x (t - 2t\\cos 4t) \\, dt = \\int_0^x t \\, dt - 2\\int_0^x t\\cos 4t \\, dt$$\n"
                "1. $\\int_0^x t \\, dt = \\frac{1}{2}x^2$\n"
                "2. $\\int_0^x t\\cos 4t \\, dt$ に部分積分法を用いる：\n"
                "   $$\\int_0^x t\\cos 4t \\, dt = \\left[t \\cdot \\frac{\\sin 4t}{4}\\right]_0^x - \\int_0^x \\frac{\\sin 4t}{4} \\, dt = \\frac{x\\sin 4x}{4} - \\left[-\\frac{\\cos 4t}{16}\\right]_0^x$$\n"
                "   $$= \\frac{x\\sin 4x}{4} + \\frac{\\cos 4x - 1}{16}$$\n\n"
                "これを代入すると：\n"
                "$$f(x) = \\frac{1}{2}x^2 - 2\\left(\\frac{x\\sin 4x}{4} + \\frac{\\cos 4x - 1}{16}\\right) = \\frac{1}{2}x^2 - \\frac{1}{2}x\\sin 4x - \\frac{1}{8}\\cos 4x + \\frac{1}{8}$$\n"
                "問題文の形式 $\\frac{\\text{H}}{\\text{I}}x^2 - \\frac{\\text{J}}{\\text{K}}x\\sin\\text{L}x - \\frac{\\text{M}}{\\text{N}}\\cos\\text{O}x + \\frac{\\text{P}}{\\text{Q}}$ と比較して：\n"
                "$$\\mathbf{HI = 12, \\quad JKL = 124, \\quad MNO = 184, \\quad PQ = 18}$$\n\n"
                "#### (3) $f(x)$ の最大値の計算\n"
                "$f'(x) = x(4\\sin^2 2x - 1)$ の増減表を考える：\n"
                "- $0 < x < \\frac{\\pi}{12}$ では $f'(x) < 0$（単調減少）\n"
                "- $\\frac{\\pi}{12} < x < \\frac{5\\pi}{12}$ では $f'(x) > 0$（単調増加）\n"
                "- $\\frac{5\\pi}{12} < x < \\frac{\\pi}{2}$ では $f'(x) < 0$（単調減少）\n"
                "したがって、$f(x)$ は $x = \\frac{5\\pi}{12}$ で最大値をとる。\n\n"
                "$x = \\frac{5\\pi}{12}$ を代入する：\n"
                "$$4x = 4 \\cdot \\frac{5\\pi}{12} = \\frac{5\\pi}{3}$$\n"
                "$$\\sin\\frac{5\\pi}{3} = -\\frac{\\sqrt{3}}{2}, \\quad \\cos\\frac{5\\pi}{3} = \\frac{1}{2}$$\n"
                "代入して計算すると：\n"
                "$$f\\left(\\frac{5\\pi}{12}\\right) = \\frac{1}{2}\\left(\\frac{5\\pi}{12}\\right)^2 - \\frac{1}{2}\\left(\\frac{5\\pi}{12}\\right)\\left(-\\frac{\\sqrt{3}}{2}\\right) - \\frac{1}{8}\\left(\\frac{1}{2}\\right) + \\frac{1}{8}$$\n"
                "$$= \\frac{1}{2} \\cdot \\frac{25\\pi^2}{144} + \\frac{5\\sqrt{3}\\pi}{48} - \\frac{1}{16} + \\frac{1}{8} = \\frac{25}{288}\\pi^2 + \\frac{5\\sqrt{3}}{48}\\pi + \\frac{1}{16}$$\n"
                "選択肢一覧より：\n"
                "- $\\frac{25}{288}$ は $\\textcircled{9}$\n"
                "- $\\frac{5\\sqrt{3}}{48}$ は $\\textcircled{7}$\n"
                "- $\\frac{1}{16}$ は $\\textcircled{2}$\n"
                "よって、$\\mathbf{R = 9, S = 7, T = 2} \\implies \\mathbf{RST = 972}$。\n\n"
                "#### (4) 点 $\\left(\\frac{\\pi}{4}, f\\left(\\frac{\\pi}{4}\\right)\\right)$ における接線の方程式\n"
                "1. **接点の $y$ 座標**：\n"
                "   $x = \\frac{\\pi}{4}$ のとき $4x = \\pi$ であるから、$\\sin\\pi = 0, \\cos\\pi = -1$。\n"
                "   $$f\\left(\\frac{\\pi}{4}\\right) = \\frac{1}{2}\\left(\\frac{\\pi}{4}\\right)^2 - 0 - \\frac{1}{8}(-1) + \\frac{1}{8} = \\frac{\\pi^2}{32} + \\frac{1}{4}$$\n"
                "2. **接線の傾き**：\n"
                "   $$f'\\left(\\frac{\\pi}{4}\\right) = \\frac{\\pi}{4}\\left(4\\sin^2\\frac{\\pi}{2} - 1\\right) = \\frac{\\pi}{4}(4 \\cdot 1 - 1) = \\frac{3\\pi}{4}$$\n"
                "3. **接線の方程式**：\n"
                "   $$y - \\left(\\frac{\\pi^2}{32} + \\frac{1}{4}\\right) = \\frac{3\\pi}{4}\\left(x - \\frac{\\pi}{4}\\right)$$\n"
                "   $$y = \\frac{3}{4}\\pi x - \\frac{3\\pi^2}{16} + \\frac{\\pi^2}{32} + \\frac{1}{4} = \\frac{3}{4}\\pi x - \\frac{5}{32}\\pi^2 + \\frac{1}{4}$$\n"
                "問題文の形式 $y = \\text{U}\\pi x - \\text{V}\\pi^2 + \\text{W}$ より：\n"
                "- $\\text{U}$ は $\\frac{3}{4}$ で $\\textcircled{3}$\n"
                "- $\\text{V}$ は $\\frac{5}{32}$ で $\\textcircled{8}$\n"
                "- $\\text{W}$ は $\\frac{1}{4}$ で $\\textcircled{2}$\n"
                "よって、$\\mathbf{U = 3, V = 8, W = 2} \\implies \\mathbf{UVW = 382}$。"
            )
        }
    ]
}

# Write Markdown
md_content = r"""# 2023年度 第1回（2023-1）EJU 日本留学試験 数学（コース2）全問詳細解説

- **試験科目**：数学（コース2 / Mathematics Course 2）
- **対象試験**：2023年度第1回（令和5年6月実施）
- **形式コード**：`MATHEMATICS_COURSE_2_JA`
- **問題構成**：大問 I ～ IV（計4大問、8設問ブロック）
- **解答形式**：マーク式（数値・符号・アルファベット選択）

---

## 数学（コース2）公式正解一覧表

| 大問 | 設問 | 解答記号 | 公式正解 | 考査分野・要点 |
| :--- | :--- | :--- | :--- | :--- |
| **I** | 問1 | ABC | **634** | 2次関数の交点条件 |
| | | DE | **33** | グラフの交点連立方程式 |
| | | F | **2** | 定数 $b$ の消去決定 |
| | | GHI | **916** | 最大値と最小値の差 |
| | | JK, L | **23**, **2** | $a = -2/3, c = 2$ |
| | 問2 | M | **0** ($8/81$) | 3箱からの抽出確率（$a=b\neq c$） |
| | | N | **2** ($56/81$) | 3数相異なる確率 |
| | | OP | **24** ($2 \le b \le 4$) | 不等式 $a > 2b > 3c$ の範囲 |
| | | Q | **9** ($10/729$) | 不等式を満たす確率 $p$ |
| | | R | **4** ($25/126$) | 5枚中奇数4枚偶数1枚 |
| | | S | **7** ($125/126$) | 余事象（少なくとも1枚奇数） |
| **II** | 問1 | AB | **32** ($3/2$) | 内積 $\vec{c} \cdot \vec{a}$ の計算 |
| | | C, D | **4**, **2** | 垂直条件による内積 $\vec{a} \cdot \vec{b}, \vec{b} \cdot \vec{c}$ |
| | | EFG | **838** | $\vec{a}$ との内積式 $8s + 3t = 8$ |
| | | HI | **34** | $\vec{c}$ との内積式 $3s + 4t = 4$ |
| | | J, K | **2**, **0** | 基底係数 $s = 20/23, t = 8/23$ |
| | | L | **5** ($23/28$) | 対角線交点比 $\overrightarrow{OD} = \frac{23}{28}\vec{b}$ |
| | 問2 | M | **0** | $a = 0$（直線ABとBCが垂直） |
| | | N | **3** | $b = 0$（直線ABとBCが同一直線） |
| | | OP | **-8** | 三角関数の極形式商と偏角 $-A+B+C$ |
| | | Q | **0** | 直角の頂点 $A = \pi/2$ |
| | | RS | **-1** | 実部 $a = -1$ |
| | | TU, V | **23**, **2** | 偏角 $\theta = 2\pi/3$、絶対値 $2$ |
| | | W, X, Y | **2**, **3**, **6** | 直角三角形の内角 $\pi/2, \pi/3, \pi/6$ |
| **III** | | A, BCD | **2**, **103** | 端点値 $S(-2) = 2, S(0) = 10/3$ |
| | | E, F | **0**, **0** | 外側領域での単調性と不等号 $<$ |
| | | GHIJK | **-1322** | $S(a) = -\frac{1}{3}a^3 - 2a^2 - 2a + \frac{10}{3}$ |
| | | LMN | **103** | 定数項 $10/3$ |
| | | OP | **42** | 導関数 $S'(a) = -a^2 - 4a - 2$ |
| | | QR | **22** | 極大値を与える $a = -2 + \sqrt{2}$ |
| | | ST | **22** | 最大値を与える $a = -2 + \sqrt{2}$ |
| | | UVWX | **2423** | 最大値 $2 + \frac{4\sqrt{2}}{3}$ |
| **IV** | | A | **4** | 極値条件より $a = 4$ |
| | | BCD | **512** | 別の極値点 $x = \frac{5}{12}\pi$ |
| | | EFG | **124** | 被積分関数の変形 $1 - 2\cos 4t$ |
| | | HI | **12** | 2次項係数 $1/2$ |
| | | JKL | **124** | $x\sin 4x$ の係数 $1/2$ |
| | | MNO, PQ | **184**, **18** | $\cos 4x$ 係数 $1/8$、定数項 $1/8$ |
| | | RST | **972** | 最大値 $\frac{25}{288}\pi^2 + \frac{5\sqrt{3}}{48}\pi + \frac{1}{16}$ |
| | | UVW | **382** | 接線 $y = \frac{3}{4}\pi x - \frac{5}{32}\pi^2 + \frac{1}{4}$ |

---

## 逐問詳細推導与解説

"""

for s in explanations["sections"]:
    md_content += f"\n---\n\n## {s['sectionTitle']}\n\n"
    md_content += f"**【考査考点】**：{', '.join(s['points'])}\n\n"
    md_content += s["detailedSolution"] + "\n"

out_md = Path("/workspace/Develop/eju-question-bank/docs/explanations/2023-1-math-c2-solutions.md")
out_md.parent.mkdir(parents=True, exist_ok=True)
out_md.write_text(md_content, encoding="utf-8")

# Save as work JSON
out_json = Path("/workspace/Develop/eju-question-bank/work/2023-1-math-c2/explanations.json")
out_json.parent.mkdir(parents=True, exist_ok=True)
out_json.write_text(json.dumps(explanations, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"Generated {out_md} and {out_json} successfully.")
