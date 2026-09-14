#!/usr/bin/env python3
"""Generate comprehensive explanations for 2021-2 EJU Mathematics Course 2."""

import json
from pathlib import Path

explanations = {
    "session": "2021-2",
    "subject": "MATHEMATICS",
    "course": "COURSE_2",
    "formCode": "MATHEMATICS_COURSE_2_JA",
    "sections": [
        {
            "localKey": "math-q-I_1",
            "sectionId": "I_1",
            "sectionTitle": "第I問 問1：2次関数の頂点・軸の場合分けと閉区間における最大値条件",
            "points": [
                "2次関数の平方完成 $f(x) = a(x-p)^2 + q$ と頂点の導出",
                "定義域 $1 \\le x \\le 4$ に対する対称軸 $x = a+1$ の位置による場合分け",
                "区間の端点および頂点における最大値方程式の解法"
            ],
            "officialAnswers": {
                "A": "1",
                "B": "2",
                "C": "0",
                "D": "4",
                "E": "4",
                "F": "3",
                "GH": "86",
                "IJKLM": "40126"
            },
            "detailedSolution": (
                "### 【第I問 問1】詳細解答と解説\n\n"
                "#### 1. 平方完成と頂点座標の決定\n"
                "与えられた2次関数は：\n"
                "$$f(x) = -2x^2 + 4(a+1)x - a^2 - 5a$$\n"
                "平方完成を行う：\n"
                "$$f(x) = -2\\left[x^2 - 2(a+1)x\\right] - a^2 - 5a$$\n"
                "$$= -2\\left[(x - (a+1))^2 - (a+1)^2\\right] - a^2 - 5a$$\n"
                "$$= -2(x - (a+1))^2 + 2(a^2 + 2a + 1) - a^2 - 5a$$\n"
                "$$= -2(x - (a+1))^2 + a^2 - a + 2$$\n"
                "したがって、放物線 $y = f(x)$ の頂点の座標は：\n"
                "$$\\left(a + 1,\\, a^2 - a + 2\\right)$$\n"
                "となり、$\\mathbf{A = 1},\\, \\mathbf{B = 2}$ である。\n"
                "また、対称軸の方程式は $x = a + 1$ である。\n\n"
                "#### 2. 軸の位置による場合分けと最大値条件\n"
                "放物線は上に凸（$x^2$ の係数が $-2 < 0$）であるから、閉区間 $1 \\le x \\le 4$ における最大値は軸の位置によって次のように場合分けされる。\n\n"
                "**(i) 軸が定義域の左外側にある場合（$a+1 \\le 1 \\iff a \\le 0$）：**\n"
                "このとき $\\mathbf{C = 0}$ である。\n"
                "関数は区間 $1 \\le x \\le 4$ で単調減少するため、最大値は左端 $x = 1$ でとる。\n"
                "$$f(1) = -2(1)^2 + 4(a+1)(1) - a^2 - 5a = -2 + 4a + 4 - a^2 - 5a = -a^2 - a + 2$$\n"
                "条件より最大値が 2 であるから：\n"
                "$$-a^2 - a + 2 = 2 \\implies a^2 + a = 0 \\implies a(a+1) = 0$$\n"
                "よって $a = 0$ または $a = -1$。いずれも $a \\le 0$ を満たす。\n"
                "- $a = 0$ のとき：\n"
                "  $$f(x) = -2x^2 + 4(0+1)x - 0 = -2x^2 + 4x$$\n"
                "  よって $\\mathbf{D = 4}$ である。\n"
                "- $a = -1$ のとき：\n"
                "  $$f(x) = -2x^2 + 4(0)x - (1 - 5) = -2x^2 + 4$$\n"
                "  よって $\\mathbf{E = 4}$ である。\n\n"
                "**(ii) 軸が定義域の内部にある場合（$1 < a+1 \\le 4 \\iff 0 < a \\le 3$）：**\n"
                "このとき $\\mathbf{F = 3}$ である。\n"
                "最大値は頂点でとり、その値は頂点の $y$ 座標 $a^2 - a + 2$ である。\n"
                "$$a^2 - a + 2 = 2 \\implies a^2 - a = 0 \\implies a(a-1) = 0$$\n"
                "$0 < a \\le 3$ より $a = 1$ である。\n"
                "$a = 1$ を代入すると：\n"
                "$$f(x) = -2x^2 + 4(2)x - (1 + 5) = -2x^2 + 8x - 6$$\n"
                "よって、$\\mathbf{G = 8},\\, \\mathbf{H = 6}$（解答番号 $\\mathbf{GH = 86}$）である。\n\n"
                "**(iii) 軸が定義域の右外側にある場合（$a+1 > 4 \\iff a > 3$）：**\n"
                "関数は区間 $1 \\le x \\le 4$ で単調増加するため、最大値は右端 $x = 4$ でとる。\n"
                "$$f(4) = -2(4)^2 + 4(a+1)(4) - a^2 - 5a = -32 + 16a + 16 - a^2 - 5a = -a^2 + 11a - 16$$\n"
                "条件より最大値が 2 であるから：\n"
                "$$-a^2 + 11a - 16 = 2 \\implies a^2 - 11a + 18 = 0$$\n"
                "$$(a - 2)(a - 9) = 0$$\n"
                "$a > 3$ であるから $a = 9$ と定まる。\n"
                "$a = 9$ を代入すると：\n"
                "$$4(a+1) = 4(10) = 40$$\n"
                "$$-a^2 - 5a = -81 - 45 = -126$$\n"
                "したがって、求める関数は：\n"
                "$$f(x) = -2x^2 + 40x - 126$$\n"
                "よって、$\\mathbf{IJ = 40},\\, \\mathbf{KLM = 126}$（解答番号 $\\mathbf{IJKLM = 40126}$）である。"
            )
        },
        {
            "localKey": "math-q-I_2",
            "sectionId": "I_2",
            "sectionTitle": "第I問 問2：球と箱の順列・重複度と条件付き配置の場合の数",
            "points": [
                "異なる球の異なる箱への順列 $P(n, r)$",
                "同一箱に入る球の選択と箱の割当て",
                "奇数・偶数番号の箱への条件付き配置と積の法則"
            ],
            "officialAnswers": {
                "NOP": "840",
                "QRS": "168",
                "TU": "16",
                "V": "9",
                "WXY": "144"
            },
            "detailedSolution": (
                "### 【第I問 問2】詳細解答と解説\n\n"
                "赤・黄・緑・青の異なる4個の球と、1から7までの番号がついた7個の異なる箱がある。\n\n"
                "#### (1) 4個の球を7個の箱に1個ずつ入れる入れ方\n"
                "7個の異なる箱から4個を選び、4個の異なる球を順序をつけて対応させる順列である：\n"
                "$$P(7, 4) = 7 \\times 6 \\times 5 \\times 4 = 840$$\n"
                "よって、$\\mathbf{NOP = 840}$ 通りである。\n\n"
                "#### (2) 4個のうち3個の球を同じ1つの箱に入れ、残りの1個を他の箱に入れる入れ方\n"
                "1. 同じ箱に入る3個の球の選び方：$\\binom{4}{3} = 4$ 通り。\n"
                "2. その3個の球を入れる箱の選び方：7通り。\n"
                "3. 残った1個の球を入れる箱の選び方：残りの6個の箱から1個選ぶので 6通り。\n"
                "積の法則より：\n"
                "$$4 \\times 7 \\times 6 = 168$$\n"
                "よって、$\\mathbf{QRS = 168}$ 通りである。\n\n"
                "#### (3) 奇数番号箱と偶数番号箱への条件付き配置\n"
                "1から7までの番号のうち：\n"
                "- 奇数番号の箱：1, 3, 5, 7 の計4個。\n"
                "- 偶数番号の箱：2, 4, 6 の計3個。\n\n"
                "1. **赤色と黄色の球の入れ方**：\n"
                "   赤と黄の2個の球を4個の奇数番号の箱に入れる。各球について4つの箱のいずれを選んでもよいため：\n"
                "   $$4 \\times 4 = 16$$\n"
                "   よって、$\\mathbf{TU = 16}$ 通り。\n"
                "2. **緑色と青色の球の入れ方**：\n"
                "   緑と青の2個の球を3個の偶数番号の箱に入れる。各球について3つの箱のいずれを選んでもよいため：\n"
                "   $$3 \\times 3 = 9$$\n"
                "   よって、$\\mathbf{V = 9}$ 通り。\n"
                "3. **全体の入れ方**：\n"
                "   積の法則により：\n"
                "   $$16 \\times 9 = 144$$\n"
                "   よって、$\\mathbf{WXY = 144}$ 通りである。"
            )
        },
        {
            "localKey": "math-q-II_1",
            "sectionId": "II_1",
            "sectionTitle": "第II問 問1：立方体における平面の交線・空間ベクトルの内積と交点・共線条件",
            "points": [
                "空間直交座標系または基底ベクトル表示による直線と平面の交点",
                "ベクトルの内積と成す角の余弦 $\\cos\\theta$ の導出",
                "直線と平面の交点比および共線条件の連立方程式"
            ],
            "officialAnswers": {
                "A": "0",
                "B": "5",
                "C": "1",
                "DE": "89",
                "FG": "24",
                "H": "7",
                "I": "3",
                "J": "3",
                "K": "1",
                "LM": "27"
            },
            "detailedSolution": (
                "### 【第II問 問1】詳細解答と解説\n\n"
                "1辺の長さが 1 の立方体 ABCD-EFGH を考え、$\\overrightarrow{AB} = \\vec{a},\\, \\overrightarrow{AD} = \\vec{b},\\, \\overrightarrow{AE} = \\vec{c}$ とする。\n"
                "$\\vec{a}, \\vec{b}, \\vec{c}$ は互いに直交する単位ベクトルである。\n\n"
                "#### (1) ベクトル $\\overrightarrow{AR}, \\overrightarrow{AS}$ の表示と内積・なす角\n"
                "点 P は辺 BF 上にあり $\\text{BP} = m$ であるから、$\\overrightarrow{AP} = \\vec{a} + m\\vec{c}$。\n"
                "直線 AP と直線 EF の交点を R とする。\n"
                "R は直線 EF 上にあるため、実数 $k$ を用いて $\\overrightarrow{AR} = k\\vec{a} + \\vec{c}$ と表せる。\n"
                "A, P, R が同一直線上にあることから：\n"
                "$$\\overrightarrow{AR} = \\frac{1}{m}\\overrightarrow{AP} = \\frac{1}{m}\\vec{a} + \\vec{c}$$\n"
                "選択肢において $\\frac{1}{m}$ は $\\textcircled{0}$ であるから、$\\mathbf{A = 0}$。\n\n"
                "同様に、点 Q は辺 DH 上にあり $\\text{DQ} = n$ であるから、$\\overrightarrow{AQ} = \\vec{b} + n\\vec{c}$。\n"
                "直線 AQ と直線 EH の交点 S は：\n"
                "$$\\overrightarrow{AS} = \\frac{1}{n}\\vec{b} + \\vec{c}$$\n"
                "選択肢において $\\frac{1}{n}$ は $\\textcircled{5}$ であるから、$\\mathbf{B = 5}$。\n\n"
                "内積 $\\overrightarrow{AR} \\cdot \\overrightarrow{AS}$ を計算する：\n"
                "$$\\overrightarrow{AR} \\cdot \\overrightarrow{AS} = \\left(\\frac{1}{m}\\vec{a} + \\vec{c}\\right) \\cdot \\left(\\frac{1}{n}\\vec{b} + \\vec{c}\\right) = |\\vec{c}|^2 = 1$$\n"
                "よって、$\\mathbf{C = 1}$ である。\n\n"
                "また、各ベクトルの大きさは：\n"
                "$$|\\overrightarrow{AR}| = \\sqrt{\\frac{1}{m^2} + 1} = \\frac{\\sqrt{m^2+1}}{m},\\quad |\\overrightarrow{AS}| = \\frac{\\sqrt{n^2+1}}{n}$$\n"
                "したがって、なす角 $\\theta$ の余弦は：\n"
                "$$\\cos\\theta = \\frac{\\overrightarrow{AR} \\cdot \\overrightarrow{AS}}{|\\overrightarrow{AR}||\\overrightarrow{AS}|} = \\frac{1}{\\frac{\\sqrt{m^2+1}}{m} \\cdot \\frac{\\sqrt{n^2+1}}{n}} = \\frac{mn}{\\sqrt{(m^2+1)(n^2+1)}}$$\n"
                "選択肢より、$mn$ は $\\textcircled{8}$、$(m^2+1)(n^2+1)$ は $\\textcircled{9}$ であるから、$\\mathbf{DE = 89}$ である。\n\n"
                "#### (2) 線分 CE と平面 $\\pi$ の交点 T\n"
                "点 T は直線 CE 上にあるので、$\\overrightarrow{CT} = t\\overrightarrow{CE} = t(-\\vec{a} - \\vec{b} + \\vec{c})$ とおける。\n"
                "一方、$\\overrightarrow{CA} = -\\vec{a} - \\vec{b}$ より：\n"
                "$$\\overrightarrow{AT} = \\overrightarrow{AC} + \\overrightarrow{CT} = (1-t)\\vec{a} + (1-t)\\vec{b} + t\\vec{c}$$\n"
                "4点 A, R, S, T は同一平面 $\\pi$ 上にあるので：\n"
                "$$\\overrightarrow{AT} = r\\overrightarrow{AR} + s\\overrightarrow{AS} = r\\left(\\frac{1}{m}\\vec{a} + \\vec{c}\\right) + s\\left(\\frac{1}{n}\\vec{b} + \\vec{c}\\right) = \\frac{r}{m}\\vec{a} + \\frac{s}{n}\\vec{b} + (r+s)\\vec{c}$$\n"
                "成分を比較すると：\n"
                "$$\\frac{r}{m} = 1-t,\\quad \\frac{s}{n} = 1-t,\\quad r+s = t$$\n"
                "したがって：\n"
                "$$r = m(1-t),\\quad s = n(1-t)$$\n"
                "$$t = r+s = (m+n)(1-t) \\implies t(1+m+n) = m+n \\implies t = \\frac{m+n}{m+n+1}$$\n"
                "これより：\n"
                "$$1-t = \\frac{1}{m+n+1}$$\n"
                "$$r = \\frac{m}{m+n+1},\\quad s = \\frac{n}{m+n+1}$$\n"
                "選択肢の対応より：\n"
                "$m$ は $\\textcircled{2}$、$m+n+1$ は $\\textcircled{4}$、よって $r = \\frac{F}{G}$ より $\\mathbf{FG = 24}$。\n"
                "$n$ は $\\textcircled{7}$、よって $s = \\frac{H}{G}$ より $\\mathbf{H = 7}$。\n"
                "$m+n$ は $\\textcircled{3}$、よって $t = \\frac{I}{G}$ より $\\mathbf{I = 3}$。\n\n"
                "ベクトル $\\overrightarrow{CE}$ の大きさは $|\\overrightarrow{CE}| = \\sqrt{(-1)^2 + (-1)^2 + 1^2} = \\sqrt{3}$ であるから：\n"
                "$$|\\overrightarrow{CT}| = t|\\overrightarrow{CE}| = \\sqrt{3} \\times \\frac{m+n}{m+n+1}$$\n"
                "よって、$\\mathbf{J = 3}$ である。\n\n"
                "さらに、点 G$(1, 1, 1)$ が線分 RS 上にあるとする。\n"
                "$\\overrightarrow{AG} = \\vec{a} + \\vec{b} + \\vec{c}$。\n"
                "直線 RS 上の点は $z = 1$ の平面内にあり、$m\\overrightarrow{AR} + n\\overrightarrow{AS} = \\vec{a} + \\vec{b} + (m+n)\\vec{c}$ と表せる。\n"
                "これが $\\overrightarrow{AG}$ に一致するためには：\n"
                "$$m + n = 1$$\n"
                "よって、$\\mathbf{K = 1}$ であり、このとき：\n"
                "$$\\overrightarrow{AG} = m\\overrightarrow{AR} + n\\overrightarrow{AS}$$\n"
                "係数 $m, n$ はそれぞれ選択肢 $\\textcircled{2}, \\textcircled{7}$ であるから、$\\mathbf{LM = 27}$ である。"
            )
        },
        {
            "localKey": "math-q-II_2",
            "sectionId": "II_2",
            "sectionTitle": "第II問 問2：円と直線の交差条件・点と直線の距離の公式と弦の長さ",
            "points": [
                "円の方程式の標準形と中心・半径の導出",
                "パラメータ $a$ に無関係な直線の定点通過",
                "点と直線の距離の公式 $d = \\frac{|ax_0 + by_0 + c|}{\\sqrt{a^2+b^2}}$ と弦の長さ"
            ],
            "officialAnswers": {
                "NO": "01",
                "P": "2",
                "QR": "30",
                "STU": "311",
                "V": "7",
                "W": "1",
                "X": "1",
                "YZ": "34"
            },
            "detailedSolution": (
                "### 【第II問 問2】詳細解答と解説\n\n"
                "#### 1. 円の中心と半径・直線の通過する定点\n"
                "与えられた円の方程式を変形する：\n"
                "$$x^2 + y^2 - 2y - 1 = 0 \\implies x^2 + (y - 1)^2 = 2$$\n"
                "したがって、円の中心は $(0, 1)$、半径は $\\sqrt{2}$ である。\n"
                "よって、$\\mathbf{NO = 01},\\, \\mathbf{P = 2}$ である。\n\n"
                "与えられた直線の方程式は：\n"
                "$$ax - y + 3a = 0 \\implies a(x + 3) - y = 0$$\n"
                "これは $a$ の値にかかわらず、$x + 3 = 0$ かつ $y = 0$、すなわち点 $(-3, 0)$ を通る。\n"
                "よって、$\\mathbf{QR = 30}$ である。\n\n"
                "#### 2. 点と直線の距離と異なる2点で交わる条件\n"
                "円の中心 $(0, 1)$ と直線 $ax - y + 3a = 0$ の距離 $d$ は、点と直線の距離の公式より：\n"
                "$$d = \\frac{|a(0) - 1 + 3a|}{\\sqrt{a^2 + (-1)^2}} = \\frac{|3a - 1|}{\\sqrt{a^2 + 1}}$$\n"
                "よって、$\\mathbf{S = 3},\\, \\mathbf{T = 1},\\, \\mathbf{U = 1}$（解答番号 $\\mathbf{STU = 311}$）である。\n\n"
                "直線と円が異なる2点 P, Q で交わるための条件は、$d < \\sqrt{2}$ である：\n"
                "$$\\frac{|3a - 1|}{\\sqrt{a^2 + 1}} < \\sqrt{2} \\iff (3a - 1)^2 < 2(a^2 + 1)$$\n"
                "$$9a^2 - 6a + 1 < 2a^2 + 2 \\implies 7a^2 - 6a - 1 < 0$$\n"
                "$$(7a + 1)(a - 1) < 0$$\n"
                "したがって：\n"
                "$$-\\frac{1}{7} < a < 1$$\n"
                "よって、$\\mathbf{V = 7},\\, \\mathbf{W = 1}$ である。\n\n"
                "#### 3. 弦の長さが 2 となる条件\n"
                "線分 PQ の長さが 2 のとき、弦の半分は 1 である。\n"
                "中心から弦に下ろした垂線の長さ（距離 $d$）は三平方の定理より：\n"
                "$$d = \\sqrt{R^2 - 1^2} = \\sqrt{(\\sqrt{2})^2 - 1^2} = \\sqrt{2 - 1} = 1$$\n"
                "よって、$\\mathbf{X = 1}$ である。\n\n"
                "$d = 1$ より：\n"
                "$$\\frac{|3a - 1|}{\\sqrt{a^2 + 1}} = 1 \\iff (3a - 1)^2 = a^2 + 1$$\n"
                "$$9a^2 - 6a + 1 = a^2 + 1 \\implies 8a^2 - 6a = 0 \\implies 2a(4a - 3) = 0$$\n"
                "$a \\neq 0$ であるから：\n"
                "$$a = \\frac{3}{4}$$\n"
                "よって、$\\mathbf{YZ = 34}$（$\\frac{3}{4}$）である。"
            )
        },
        {
            "localKey": "math-q-III_1",
            "sectionId": "III_1",
            "sectionTitle": "第III問（前半）：対数関数の定義域と商の微分法・導関数の符号と増減",
            "points": [
                "対数の真数条件と底の条件による定義域の確定",
                "底の変換公式と商の微分法",
                "2階的導関数の符号変化と極値の存在"
            ],
            "officialAnswers": {
                "ABCD": "1311",
                "E": "3",
                "F": "5",
                "GH": "12",
                "I": "8",
                "J": "9",
                "K": "7",
                "L": "2",
                "M": "9"
            },
            "detailedSolution": (
                "### 【第III問 前半】詳細解答と解説\n\n"
                "関数 $y = \\log_x(3x^2 - x)$ について調べる。\n\n"
                "#### 1. 定義域の決定\n"
                "対数関数の定義域は：\n"
                "1. 底の条件：$x > 0$ かつ $x \\neq 1$\n"
                "2. 真数条件：$3x^2 - x > 0 \\implies x(3x - 1) > 0 \\implies x < 0$ または $x > \\frac{1}{3}$\n"
                "$x > 0$ と合わせると $x > \\frac{1}{3}$ かつ $x \\neq 1$ である。\n"
                "区間として表すと：\n"
                "$$\\frac{1}{3} < x < 1,\\quad 1 < x$$\n"
                "よって、$\\mathbf{ABCD = 1311}$（$\\frac{1}{3} < x < 1,\\, 1 < x$）である。\n\n"
                "#### 2. 底の変換と導関数 $y'$\n"
                "自然対数を用いて底を変換する：\n"
                "$$y = \\frac{\\log(3x^2 - x)}{\\log x} = \\frac{\\log x + \\log(3x - 1)}{\\log x} = 1 + \\frac{\\log(3x - 1)}{\\log x}$$\n"
                "商の微分法を適用する：\n"
                "$$y' = \\frac{\\frac{3}{3x-1} \\log x - \\log(3x - 1) \\cdot \\frac{1}{x}}{(\\log x)^2} = \\frac{3x\\log x - (3x - 1)\\log(3x - 1)}{x(3x - 1)(\\log x)^2}$$\n"
                "分子の式は選択肢 $\\textcircled{3}$ に一致する。よって $\\mathbf{E = 3}$。\n\n"
                "#### 3. 分子 $z(x)$ の増減と導関数の符号\n"
                "$z(x) = 3x\\log x - (3x - 1)\\log(3x - 1)$ とおき、微分する：\n"
                "$$z'(x) = 3\\log x + 3x \\cdot \\frac{1}{x} - \\left[3\\log(3x - 1) + (3x - 1) \\cdot \\frac{3}{3x - 1}\\right]$$\n"
                "$$= 3\\log x + 3 - 3\\log(3x - 1) - 3 = 3\\left(\\log x - \\log(3x - 1)\\right)$$\n"
                "これは選択肢 $\\textcircled{5}$ に一致する。よって $\\mathbf{F = 5}$。\n\n"
                "$z'(x)$ の符号は $\\log\\frac{x}{3x-1}$ の符号で決まる：\n"
                "$$\\frac{x}{3x-1} = 1 \\iff x = 3x - 1 \\iff 2x = 1 \\iff x = \\frac{1}{2}$$\n"
                "よって分岐点は $\\frac{G}{H} = \\frac{1}{2}$ であり、$\\mathbf{GH = 12}$。\n\n"
                "- $x < \\frac{1}{2}$ のとき：$3x - 1 < x$ より $\\frac{x}{3x-1} > 1$ であるから、$z' > 0$（選択肢 $\\textcircled{8} >$）。よって $\\mathbf{I = 8}$。\n"
                "- $x > \\frac{1}{2}$ のとき：$\\frac{x}{3x-1} < 1$ であるから、$z' < 0$（選択肢 $\\textcircled{9} <$）。よって $\\mathbf{J = 9}$。\n"
                "- $x = \\frac{1}{2}$ のとき：$z' = 0$（選択肢 $\\textcircled{7} =$）。よって $\\mathbf{K = 7}$。\n\n"
                "このとき $z\\left(\\frac{1}{2}\\right)$ の値を計算すると：\n"
                "$$z\\left(\\frac{1}{2}\\right) = 3\\left(\\frac{1}{2}\\right)\\log\\frac{1}{2} - \\left(3 \\cdot \\frac{1}{2} - 1\\right)\\log\\left(3 \\cdot \\frac{1}{2} - 1\\right) = \\frac{3}{2}\\log\\frac{1}{2} - \\frac{1}{2}\\log\\frac{1}{2} = \\log\\frac{1}{2} = -\\log 2$$\n"
                "よって、$\\mathbf{L = 2}$ である。\n\n"
                "$z(x)$ は $x = \\frac{1}{2}$ で極大値 $-\\log 2 < 0$ をとるため、区間 $\\left(\\frac{1}{3}, 1\\right)$ 全体で常に $z(x) \\le -\\log 2 < 0$ である。\n"
                "また $x > 1$ においても $z'(x) < 0$ かつ $z(1) = -2\\log 2 < 0$ より常に $z(x) < 0$ である。\n"
                "分母 $x(3x-1)(\\log x)^2 > 0$ であるから、全定義域において常に $y' < 0$（選択肢 $\\textcircled{9} <$）である。\n"
                "よって、$\\mathbf{M = 9}$ である。"
            )
        },
        {
            "localKey": "math-q-III_2",
            "sectionId": "III_2",
            "sectionTitle": "第III問（後半）：対数関数の端点極限値と方程式の実数解の個数",
            "points": [
                "対数関数の境界点における極限の計算",
                "関数の漸近挙動とグラフの概形",
                "水平直線 $y = \\alpha$ との交点数に基づく解の個数の場合分け"
            ],
            "officialAnswers": {
                "N": "7",
                "O": "8",
                "P": "7",
                "QRS": "231",
                "T": "2",
                "U": "2",
                "V": "2",
                "W": "1"
            },
            "detailedSolution": (
                "### 【第III問 後半】詳細解答と解説\n\n"
                "#### 1. 各境界における極限値\n"
                "前半の結果より、$y = 1 + \\frac{\\log(3x-1)}{\\log x}$ である。\n"
                "1. **$x \\to \\frac{1}{3} + 0$ のとき**：\n"
                "   $\\log(3x-1) \\to -\\infty$ であり、分母 $\\log\\frac{1}{3} = -\\log 3 < 0$ である。\n"
                "   よって：\n"
                "   $$\\lim_{x \\to \\frac{1}{3}+0} y = 1 + \\frac{-\\infty}{-\\log 3} = +\\infty$$\n"
                "   選択肢 $\\textcircled{7} \\infty$ より $\\mathbf{N = 7}$。\n"
                "2. **$x \\to 1 - 0$ のとき**：\n"
                "   分子 $\\log(3x-1) \\to \\log 2 > 0$ であり、分母 $\\log x \\to 0^-$ である。\n"
                "   よって：\n"
                "   $$\\lim_{x \\to 1-0} y = 1 + \\frac{\\log 2}{0^-} = -\\infty$$\n"
                "   選択肢 $\\textcircled{8} -\\infty$ より $\\mathbf{O = 8}$。\n"
                "3. **$x \\to 1 + 0$ のとき**：\n"
                "   分子 $\\log(3x-1) \\to \\log 2 > 0$ であり、分母 $\\log x \\to 0^+$ である。\n"
                "   よって：\n"
                "   $$\\lim_{x \\to 1+0} y = 1 + \\frac{\\log 2}{0^+} = +\\infty$$\n"
                "   選択肢 $\\textcircled{7} \\infty$ より $\\mathbf{P = 7}$。\n\n"
                "#### 2. 無限遠での漸近挙動\n"
                "関数を変形する：\n"
                "$$3x^2 - x = x^2\\left(3 - \\frac{1}{x}\\right)$$\n"
                "$$\\log_x(3x^2 - x) = \\frac{2\\log x + \\log\\left(3 - \\frac{1}{x}\\right)}{\\log x} = 2 + \\frac{\\log\\left(3 - \\frac{1}{x}\\right)}{\\log x}$$\n"
                "よって、$\\mathbf{Q = 2},\\, \\mathbf{R = 3},\\, \\mathbf{S = 1}$（解答番号 $\\mathbf{QRS = 231}$）である。\n\n"
                "$x \\to \\infty$ のとき $\\frac{\\log 3}{\\log x} \\to 0$ であるから：\n"
                "$$\\lim_{x \\to \\infty} y = 2$$\n"
                "よって、$\\mathbf{T = 2}$ である。\n\n"
                "#### 3. 方程式 $\\log_x(3x^2 - x) = \\alpha$ の実数解の個数\n"
                "全定義域で $y' < 0$ であるため、各区間において関数は単調減少する：\n"
                "1. 区間 $\\left(\\frac{1}{3}, 1\\right)$ において：\n"
                "   $y$ は $+\\infty$ から $-\\infty$ まで連続かつ単調に減少する。\n"
                "   中間値の定理より、任意の実数 $\\alpha$ に対してこの区間に**必ずちょうど 1 個の解**が存在する。\n"
                "2. 区間 $(1, \\infty)$ において：\n"
                "   $y$ は $+\\infty$ から $2$ まで連続かつ単調に減少する。\n"
                "   - $\\alpha > 2$ のとき：この区間に**ちょうど 1 個の解**が存在する。\n"
                "   - $\\alpha \\le 2$ のとき：この区間に解は存在しない（0 個）。\n\n"
                "両区間を合わせると：\n"
                "- $2 < \\alpha$（$\\mathbf{U = 2}$）のとき：$1 + 1 = 2$ 個（$\\mathbf{V = 2}$）。\n"
                "- $\\alpha \\le 2$ のとき：$1 + 0 = 1$ 個（$\\mathbf{W = 1}$）。\n"
                "よって、$\\mathbf{U = 2},\\, \\mathbf{V = 2},\\, \\mathbf{W = 1}$ である。"
            )
        },
        {
            "localKey": "math-q-IV_1",
            "sectionId": "IV_1",
            "sectionTitle": "第IV問（前半）：2つの分数関数の接線方程式と共通接線の決定",
            "points": [
                "分数関数の導関数と接線の方程式",
                "2つの接線が一致するための係数比較",
                "連立方程式による接点の特定と共通接線の導出"
            ],
            "officialAnswers": {
                "AB": "21",
                "CDEF": "8164",
                "G": "4",
                "HI": "14",
                "J": "0",
                "KLM": "-84"
            },
            "detailedSolution": (
                "### 【第IV問 前半】詳細解答と解説\n\n"
                "2つの曲線：\n"
                "$$C_1: y = \\frac{1}{2x} \\quad (x > 0)$$\n"
                "$$C_2: y = \\frac{4}{2x+1} \\quad \\left(x > -\\frac{1}{2}\\right)$$\n"
                "を考える。\n\n"
                "#### 1. 各曲線における接線の方程式\n"
                "1. **$C_1$ の接線**：\n"
                "   $y' = -\\frac{1}{2x^2}$。\n"
                "   点 $\\left(s, \\frac{1}{2s}\\right)$ における接線の方程式は：\n"
                "   $$y - \\frac{1}{2s} = -\\frac{1}{2s^2}(x - s) \\implies y = -\\frac{1}{2s^2}x + \\frac{1}{2s} + \\frac{1}{2s} = -\\frac{1}{2s^2}x + \\frac{1}{s}$$\n"
                "   問題文の形 $-\\frac{1}{A s^2}x + \\frac{B}{s}$ に照らし合わせて、$\\mathbf{AB = 21}$ である。\n\n"
                "2. **$C_2$ の接線**：\n"
                "   $y' = -\\frac{8}{(2x+1)^2}$。\n"
                "   点 $\\left(t, \\frac{4}{2t+1}\\right)$ における接線の方程式は：\n"
                "   $$y - \\frac{4}{2t+1} = -\\frac{8}{(2t+1)^2}(x - t)$$\n"
                "   $$y = -\\frac{8}{(2t+1)^2}x + \\frac{8t + 4(2t+1)}{(2t+1)^2} = -\\frac{8}{(2t+1)^2}x + \\frac{16t + 4}{(2t+1)^2}$$\n"
                "   問題文の形 $-\\frac{C}{(2t+1)^2}x + \\frac{DE t + F}{(2t+1)^2}$ より、$\\mathbf{CDEF = 8164}$（$C=8, DE=16, F=4$）である。\n\n"
                "#### 2. 共通接線の決定\n"
                "2本の直線が同一であるため、係数を比較する：\n"
                "1. **傾きの比較**：\n"
                "   $$-\\frac{1}{2s^2} = -\\frac{8}{(2t+1)^2} \\iff (2t+1)^2 = 16s^2$$\n"
                "   $s > 0$ かつ $2t+1 > 0$ であるから、正の平方根をとって：\n"
                "   $$2t+1 = 4s$$\n"
                "   よって、$\\mathbf{G = 4}$ である。\n\n"
                "2. **切片の比較**：\n"
                "   $$\\frac{1}{s} = \\frac{16t+4}{(2t+1)^2} = \\frac{8(2t+1) - 4}{(2t+1)^2}$$\n"
                "   $2t+1 = 4s$ を代入すると：\n"
                "   $$\\frac{1}{s} = \\frac{8(4s) - 4}{(4s)^2} = \\frac{32s - 4}{16s^2} = \\frac{8s - 1}{4s^2}$$\n"
                "   両辺に $4s^2$ を掛ける（$s \\neq 0$）：\n"
                "   $$4s = 8s - 1 \\implies 4s = 1 \\implies s = \\frac{1}{4}$$\n"
                "   よって、$\\mathbf{HI = 14}$（$\\frac{1}{4}$）である。\n\n"
                "   $2t+1 = 4s = 1$ より：\n"
                "   $$2t = 0 \\implies t = 0$$\n"
                "   よって、$\\mathbf{J = 0}$ である。\n\n"
                "共通接線 $\\ell$ の方程式は、$s = \\frac{1}{4}$ を代入して：\n"
                "$$y = -\\frac{1}{2(1/16)}x + \\frac{1}{1/4} = -8x + 4$$\n"
                "よって、$\\mathbf{KLM = -84}$（$y = -8x + 4$）である。"
            )
        },
        {
            "localKey": "math-q-IV_2",
            "sectionId": "IV_2",
            "sectionTitle": "第IV問（後半）：曲線の交点と共通接線で囲まれた面積の定積分",
            "points": [
                "2つの曲線の交点方程式の導出",
                "凸性と上下関係に基づく積分区間の分割",
                "対数関数を含む定積分の計算"
            ],
            "officialAnswers": {
                "NO": "16",
                "PQ": "72",
                "RS": "32",
                "TU": "34"
            },
            "detailedSolution": (
                "### 【第IV問 後半】詳細解答と解説\n\n"
                "#### 1. 2曲線 $C_1, C_2$ の交点\n"
                "$$\\frac{1}{2x} = \\frac{4}{2x+1} \\implies 2x+1 = 8x \\implies 6x = 1 \\implies x = \\frac{1}{6}$$\n"
                "よって、交点の $x$ 座標は $\\mathbf{NO = 16}$（$\\frac{1}{6}$）である。\n\n"
                "#### 2. 面積 $S$ の計算\n"
                "$C_1, C_2$ の接点はそれぞれ $x = s = \\frac{1}{4}$ と $x = t = 0$ である。\n"
                "また、交点の $x$ 座標は $x = \\frac{1}{6}$ であり、大小関係は $0 < \\frac{1}{6} < \\frac{1}{4}$ である。\n"
                "$C_1, C_2$ はともに下に凸であり、直線 $\\ell$ は接点以外で曲線と交わらないため：\n"
                "- 区間 $\\left[0, \\frac{1}{6}\\right]$ では $C_2$ が上で $\\ell$ が下にある。\n"
                "- 区間 $\\left[\\frac{1}{6}, \\frac{1}{4}\\right]$ では $C_1$ が上で $\\ell$ が下にある。\n\n"
                "したがって、求める面積 $S$ は次のように分割される：\n"
                "$$S = \\int_0^{1/6} \\left(\\frac{4}{2x+1} - (-8x+4)\\right) dx + \\int_{1/6}^{1/4} \\left(\\frac{1}{2x} - (-8x+4)\\right) dx$$\n\n"
                "各部分を計算する：\n"
                "共通の多項式部分：\n"
                "$$\\int_0^{1/4} (8x - 4) dx = \\left[4x^2 - 4x\\right]_0^{1/4} = 4\\left(\\frac{1}{16}\\right) - 4\\left(\\frac{1}{4}\\right) = \\frac{1}{4} - 1 = -\\frac{3}{4}$$\n\n"
                "分数関数の積分：\n"
                "1. $\\int_0^{1/6} \\frac{4}{2x+1} dx = \\left[2\\log(2x+1)\\right]_0^{1/6} = 2\\log\\left(\\frac{4}{3}\\right) = 4\\log 2 - 2\\log 3$\n"
                "2. $\\int_{1/6}^{1/4} \\frac{1}{2x} dx = \\left[\\frac{1}{2}\\log x\\right]_{1/6}^{1/4} = \\frac{1}{2}\\log\\frac{1}{4} - \\frac{1}{2}\\log\\frac{1}{6}$\n"
                "   $$= \\frac{1}{2}(-2\\log 2) - \\frac{1}{2}(-\\log 6) = -\\log 2 + \\frac{1}{2}(\\log 2 + \\log 3) = -\\frac{1}{2}\\log 2 + \\frac{1}{2}\\log 3$$\n\n"
                "すべてを足し合わせる：\n"
                "$$S = (4\\log 2 - 2\\log 3) + \\left(-\\frac{1}{2}\\log 2 + \\frac{1}{2}\\log 3\\right) - \\frac{3}{4}$$\n"
                "$$= \\left(4 - \\frac{1}{2}\\right)\\log 2 + \\left(-2 + \\frac{1}{2}\\right)\\log 3 - \\frac{3}{4}$$\n"
                "$$= \\frac{7}{2}\\log 2 - \\frac{3}{2}\\log 3 - \\frac{3}{4}$$\n"
                "したがって：\n"
                "$$S = \\frac{7}{2}\\log 2 - \\frac{3}{2}\\log 3 - \\frac{3}{4}$$\n"
                "よって、$\\mathbf{PQ = 72},\\, \\mathbf{RS = 32},\\, \\mathbf{TU = 34}$ である。"
            )
        }
    ]
}

def main():
    out_json = Path("work/2021-2-math-c2/explanations.json")
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(explanations, ensure_ascii=False, indent=2), encoding="utf-8")

    md_content = f"# {explanations['session']} EJU 数学（コース2）詳細解答・解説\n\n"
    for s in explanations["sections"]:
        md_content += f"\n---\n\n## {s['sectionTitle']}\n\n"
        md_content += f"**【考査考点】**：{', '.join(s['points'])}\n\n"
        md_content += s["detailedSolution"] + "\n"

    out_md = Path("docs/explanations/2021-2-math-c2-solutions.md")
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(md_content, encoding="utf-8")

    print(f"Generated {out_md} and {out_json} successfully with {len(explanations['sections'])} sections.")

if __name__ == "__main__":
    main()
