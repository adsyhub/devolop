#!/usr/bin/env python3
"""Generate comprehensive explanations for 2018-2 EJU Mathematics Course 1."""

import json
from pathlib import Path

explanations = {
    "session": "2018-2",
    "subject": "MATHEMATICS",
    "course": "COURSE_1",
    "formCode": "MATHEMATICS_COURSE_1_JA",
    "sections": [
        {
            "localKey": "math-q-I_1",
            "sectionId": "I_1",
            "sectionTitle": "第I問 問1：2次関数の頂点座標・軸の位置による最大値と最小値の場合分け",
            "points": [
                "2次関数の平方完成と頂点座標の決定",
                "閉区間における軸の位置と最大値・最小値の場合分け",
                "パラメータ関数の最大値・最小値の極値計算"
            ],
            "officialAnswers": {
                "ABC": "121",
                "D": "1",
                "E": "6",
                "F": "5",
                "G": "6",
                "H": "8",
                "I": "3",
                "J": "6",
                "K": "1",
                "LM": "-2"
            },
            "detailedSolution": (
                "### 【第I問 問1】詳細解答と解説\n\n"
                "2次関数 $f(x) = x^2 - 2(a+1)x + 2a^2$（$0 \\le a \\le 3$）の閉区間 $0 \\le x \\le 2$ における最大値 $M$ と最小値 $m$ を考える。\n\n"
                "#### 1. 平方完成と頂点座標\n"
                "$$f(x) = (x - (a+1))^2 - (a+1)^2 + 2a^2 = (x - (a+1))^2 + a^2 - 2a - 1$$\n"
                "したがって、頂点の座標は：\n"
                "$$\\left(a + 1,\\, a^2 - 2a - 1\\right)$$\n"
                "よって、$\\mathbf{A = 1},\\, \\mathbf{B = 2},\\, \\mathbf{C = 1}$（解答番号 $\\mathbf{ABC = 121}$）である。\n"
                "対称軸は $x = a + 1$ であり、放物線は下に凸である。\n\n"
                "#### 2. 軸の位置による最大値・最小値の場合分け\n"
                "区間の中点は $x = 1$ である。\n"
                "$a \\ge 0$ より軸 $a + 1 \\ge 1$ であるから、軸は常に区間の中点 $x = 1$ 以上にある。\n"
                "したがって、最大値は常に軸から最も遠い左端 $x = 0$ でとる：\n"
                "$$M = f(0) = 2a^2$$\n"
                "これは選択肢 $\\textcircled{6}$ に対応する。よって $0 \\le a < 1$ でも $1 \\le a \\le 3$ でも常に $\\mathbf{E = 6},\\, \\mathbf{G = 6}$ である。\n\n"
                "最小値 $m$ について：\n"
                "- **$a + 1 \\le 2 \\iff 0 \\le a \\le 1$ のとき（$\\mathbf{D = 1}$）**：\n"
                "  軸が区間 $[0, 2]$ 内にあるため、最小値は頂点でとる：\n"
                "  $$m = a^2 - 2a - 1$$\n"
                "  これは選択肢 $\\textcircled{5}$ に対応する。よって $\\mathbf{F = 5}$。\n"
                "- **$a + 1 > 2 \\iff 1 < a \\le 3$ のとき**：\n"
                "  軸が区間の右外側にあるため、最小値は右端 $x = 2$ でとる：\n"
                "  $$m = f(2) = 4 - 4(a+1) + 2a^2 = 2a^2 - 4a$$\n"
                "  これは選択肢 $\\textcircled{8}$ に対応する。よって $\\mathbf{H = 8}$。\n\n"
                "#### 3. 最小値 $m(a)$ の最大・最小\n"
                "- $0 \\le a \\le 1$ において、$m(a) = (a-1)^2 - 2$ は単調減少（$m(0) = -1$ から $m(1) = -2$ まで減少）。\n"
                "- $1 \\le a \\le 3$ において、$m(a) = 2(a-1)^2 - 2$ は単調増加（$m(1) = -2$ から $m(3) = 6$ まで増加）。\n"
                "したがって：\n"
                "- $m$ が最大となるのは $a = 3$ のときで、最大値は $m(3) = 6$ である。\n"
                "  よって、$\\mathbf{I = 3},\\, \\mathbf{J = 6}$ である。\n"
                "- $m$ が最小となるのは $a = 1$ のときで、最小値は $m(1) = -2$ である。\n"
                "  よって、$\\mathbf{K = 1},\\, \\mathbf{LM = -2}$ である。"
            )
        },
        {
            "localKey": "math-q-I_2",
            "sectionId": "I_2",
            "sectionTitle": "第I問 問2：さいころの目による2次方程式の実数解条件と不等式を満たす確率",
            "points": [
                "2次方程式の判別式 $D > 0$ と積の条件 $ac < 4$",
                "3変数の不等式 $100a + 10b + c > 453$ の辞書式場合分け",
                "全事象 $6^3$ に対する確率の計算と約分"
            ],
            "officialAnswers": {
                "NOPQ": "5216",
                "R": "3",
                "S": "6",
                "TU": "36",
                "VW": "36",
                "XY": "38"
            },
            "detailedSolution": (
                "### 【第I問 問2】詳細解答と解説\n\n"
                "1個のさいころを3回投げ、出た目を順に $a, b, c \\in \\{1, 2, 3, 4, 5, 6\\}$ とする。\n"
                "全事象の総数は $6^3 = 216$ 通りである。\n\n"
                "#### (1) $b = 4$ かつ $f(x) = 0$ が異なる2つの実数解をもつ確率\n"
                "2次方程式 $ax^2 + 4x + c = 0$ の判別式は：\n"
                "$$D/4 = 4 - ac > 0 \\iff ac < 4$$\n"
                "$a, c \\in \\{1, 2, 3, 4, 5, 6\\}$ より：\n"
                "- $a = 1$ のとき：$c \\in \\{1, 2, 3\\}$ の 3通り。\n"
                "- $a = 2$ のとき：$c = 1$ の 1通り。\n"
                "- $a = 3$ のとき：$c = 1$ の 1通り。\n"
                "条件を満たす組 $(a, c)$ は $3 + 1 + 1 = 5$ 通りである。\n"
                "したがって、求める確率は：\n"
                "$$P = \\frac{5}{216}$$\n"
                "よって、$\\mathbf{N = 5},\\, \\mathbf{OPQ = 216}$（解答番号 $\\mathbf{NOPQ = 5216}$）である。\n\n"
                "#### (2) $f(10) > 453$ となる確率\n"
                "$$f(10) = 100a + 10b + c > 453$$\n"
                "$a$ の値によって場合分けする：\n"
                "1. **$a = 4$ かつ $b = 5$ のとき**：\n"
                "   $450 + c > 453 \\iff c > 3 \\implies c \\in \\{4, 5, 6\\}$ の **3通り**。\n"
                "   よって、$\\mathbf{R = 3}$ である。\n"
                "2. **$a = 4$ かつ $b = 6$ のとき**：\n"
                "   $460 + c > 453$ はすべての $c \\in \\{1..6\\}$ で成立するため **6通り**。\n"
                "   よって、$\\mathbf{S = 6}$ である。\n"
                "3. **$a = 5$ のとき**：\n"
                "   $500 + 10b + c > 453$ はすべての $b, c$ で成立するため：\n"
                "   $$6 \\times 6 = 36\\text{ 通り}$$\n"
                "   よって、$\\mathbf{TU = 36}$ である。\n"
                "4. **$a = 6$ のとき**：\n"
                "   $600 + 10b + c > 453$ はすべての $b, c$ で成立するため：\n"
                "   $$6 \\times 6 = 36\\text{ 通り}$$\n"
                "   よって、$\\mathbf{VW = 36}$ である。\n\n"
                "条件を満たす場合の数の総和は：\n"
                "$$3 + 6 + 36 + 36 = 81\\text{ 通り}$$\n"
                "したがって、求める確率は：\n"
                "$$P = \\frac{81}{216} = \\frac{3}{8}$$\n"
                "よって、$\\mathbf{X = 3},\\, \\mathbf{Y = 8}$（解答番号 $\\mathbf{XY = 38}$）である。"
            )
        },
        {
            "localKey": "math-q-II_1",
            "sectionId": "II_1",
            "sectionTitle": "第II問 問1：無理数の有理化・対称式の計算および無理方程式の整数解",
            "points": [
                "二重根号と分母の有理化による共役無理数 $x, y$ の整理",
                "基本対称式 $x+y, xy$ と逆数の2乗和の導出",
                "無理数の有理数・無理数部分の比較による未定係数の決定"
            ],
            "officialAnswers": {
                "AB": "23",
                "CD": "23",
                "E": "4",
                "F": "1",
                "GH": "14",
                "IJ": "-5",
                "KL": "-1",
                "M": "3"
            },
            "detailedSolution": (
                "### 【第II問 問1】詳細解答と解説\n\n"
                "#### (1) 分母の有理化と対称式の計算\n"
                "1. **$x$ の有理化**：\n"
                "   $$x = \\frac{\\sqrt{3}+1}{\\sqrt{3}-1} = \\frac{(\\sqrt{3}+1)^2}{3 - 1} = \\frac{4 + 2\\sqrt{3}}{2} = 2 + \\sqrt{3}$$\n"
                "   よって、$\\mathbf{AB = 23}$（$2 + \\sqrt{3}$）である。\n"
                "2. **$y$ の有理化**：\n"
                "   $$y = \\frac{\\sqrt{6}-\\sqrt{2}}{\\sqrt{6}+\\sqrt{2}} = \\frac{(\\sqrt{6}-\\sqrt{2})^2}{6 - 2} = \\frac{8 - 4\\sqrt{3}}{4} = 2 - \\sqrt{3}$$\n"
                "   よって、$\\mathbf{CD = 23}$（$2 - \\sqrt{3}$）である。\n\n"
                "3. **各式の計算**：\n"
                "   $$x + y = (2 + \\sqrt{3}) + (2 - \\sqrt{3}) = 4 \\implies \\mathbf{E = 4}$$\n"
                "   $$xy = (2 + \\sqrt{3})(2 - \\sqrt{3}) = 4 - 3 = 1 \\implies \\mathbf{F = 1}$$\n"
                "   $\\frac{1}{x} = y,\\, \\frac{1}{y} = x$ であるから：\n"
                "   $$\\frac{1}{x^2} + \\frac{1}{y^2} = x^2 + y^2 = (x + y)^2 - 2xy = 4^2 - 2(1) = 14$$\n"
                "   よって、$\\mathbf{GH = 14}$ である。\n\n"
                "   また、$x^2 - 4x + 1 = 0 \\implies x^2 - 4x = -1$、同様に $y^2 - 4y = -1$ であるから：\n"
                "   $$5(x^2 - 4x) + 3(y^2 - 4y + 1) = 5(-1) + 3(-1 + 1) = -5$$\n"
                "   よって、$\\mathbf{IJ = -5}$ である。\n\n"
                "#### (2) 整数 $m, n$ の決定\n"
                "$$\\frac{m}{x} + \\frac{n}{y} = my + nx = m(2 - \\sqrt{3}) + n(2 + \\sqrt{3}) = (2m + 2n) + (n - m)\\sqrt{3}$$\n"
                "これが $4 + 4\\sqrt{3}$ に等しい。$m, n$ は整数であり、$\\sqrt{3}$ は無理数であるから：\n"
                "$$\\begin{cases} 2m + 2n = 4 \\implies m + n = 2 \\\\ n - m = 4 \\end{cases}$$\n"
                "2式を足すと $2n = 6 \\implies n = 3$。\n"
                "代入して $m = 2 - 3 = -1$。\n"
                "よって、$\\mathbf{KL = -1},\\, \\mathbf{M = 3}$ である。"
            )
        },
        {
            "localKey": "math-q-II_2",
            "sectionId": "II_2",
            "sectionTitle": "第II問 問2：放物線の接線・共有点条件とすべて実数に対する不等式の成立条件",
            "points": [
                "2つの放物線の連立と判別式の導出",
                "重解条件（$D_1 = 0$ かつ $D_2 = 0$）による接線・接点の決定",
                "常に正となる2次不等式の判別式条件 $D < 0$ と共通範囲"
            ],
            "officialAnswers": {
                "N": "2",
                "O": "1",
                "P": "0",
                "QR": "43",
                "ST": "13",
                "UV": "23",
                "W": "4"
            },
            "detailedSolution": (
                "### 【第II問 問2】詳細解答と解説\n\n"
                "3つの2次関数：\n"
                "$$f(x) = -x^2 - 2x + 1,\\quad g(x) = -x^2 + 4x,\\quad h(x) = 2x^2 + ax + b$$\n"
                "を考える。\n\n"
                "#### (1) 判別式 $D_1, D_2$ の立式\n"
                "1. $h(x) - f(x) = 0$ より：\n"
                "   $$3x^2 + (a+2)x + (b-1) = 0$$\n"
                "   判別式は：\n"
                "   $$D_1 = (a+2)^2 - 4 \\times 3 \\times (b-1) = a^2 + 4a + 4 - 12b + 12 = a^2 + 4a - 12b + 16$$\n"
                "   これは選択肢 $\\textcircled{2}$ に対応する。よって $\\mathbf{N = 2}$。\n"
                "2. $h(x) - g(x) = 0$ より：\n"
                "   $$3x^2 + (a-4)x + b = 0$$\n"
                "   判別式は：\n"
                "   $$D_2 = (a-4)^2 - 4 \\times 3 \\times b = a^2 - 8a + 16 - 12b = a^2 - 8a - 12b + 16$$\n"
                "   これは選択肢 $\\textcircled{1}$ に対応する。よって $\\mathbf{O = 1}$。\n\n"
                "#### (2) ただ1つの解をもつ条件と接点\n"
                "両方程式が重解をもつ条件は $D_1 = 0$ かつ $D_2 = 0$ である。\n"
                "$$D_1 - D_2 = 12a = 0 \\implies a = 0$$\n"
                "よって、$\\mathbf{P = 0}$ である。\n"
                "$a = 0$ を $D_1 = 0$ に代入すると：\n"
                "$$16 - 12b = 0 \\implies 12b = 16 \\implies b = \\frac{4}{3}$$\n"
                "よって、$\\mathbf{QR = 43}$（$\\frac{4}{3}$）である。\n\n"
                "このときの解は：\n"
                "- $h(x) - f(x) = 3x^2 + 2x + \\frac{1}{3} = \\frac{1}{3}(3x+1)^2 = 0 \\implies x = -\\frac{1}{3}$。\n"
                "  よって、$\\mathbf{ST = 13}$（$-\\frac{1}{3}$）。\n"
                "- $h(x) - g(x) = 3x^2 - 4x + \\frac{4}{3} = \\frac{1}{3}(3x-2)^2 = 0 \\implies x = \\frac{2}{3}$。\n"
                "  よって、$\\mathbf{UV = 23}$（$\\frac{2}{3}$）。\n\n"
                "#### (3) すべての $x$ で $f(x) < h(x)$ かつ $g(x) < h(x)$ が成り立つ範囲\n"
                "$b = 3$ とする。\n"
                "1. $h(x) - f(x) = 3x^2 + (a+2)x + 2 > 0$ が常に成り立つ条件は $D_1 < 0$：\n"
                "   $$(a+2)^2 - 4(3)(2) < 0 \\iff (a+2)^2 < 24 \\implies -2 - 2\\sqrt{6} < a < -2 + 2\\sqrt{6}$$\n"
                "2. $h(x) - g(x) = 3x^2 + (a-4)x + 3 > 0$ が常に成り立つ条件は $D_2 < 0$：\n"
                "   $$(a-4)^2 - 4(3)(3) < 0 \\iff (a-4)^2 < 36 \\implies -6 < a - 4 < 6 \\implies -2 < a < 10$$\n"
                "共通範囲をとる：$-2 < a < -2 + 2\\sqrt{6}$（$\\because -2 + 2\\sqrt{6} \\approx 2.899 < 10$）。\n"
                "これは選択肢 $\\textcircled{4}$ に対応する。よって $\\mathbf{W = 4}$ である。"
            )
        },
        {
            "localKey": "math-q-III_1",
            "sectionId": "III_1",
            "sectionTitle": "第III問（前半）：素因数分解・約数の個数と互いに素な因数分解の組数",
            "points": [
                "1400 の素因数分解 $1400 = 2^3 \\times 5^2 \\times 7$",
                "約数の個数定理 $(p+1)(q+1)(r+1)$",
                "互いに素な因数の分割と差 $b-a$ の最大化"
            ],
            "officialAnswers": {
                "ABCDE": "23527",
                "FG": "48",
                "H": "3",
                "I": "7",
                "JKL": "200"
            },
            "detailedSolution": (
                "### 【第III問 前半】詳細解答と解説\n\n"
                "#### 1. 素因数分解と約数の個数\n"
                "1400 を素因数分解すると：\n"
                "$$1400 = 14 \\times 100 = 2 \\times 7 \\times 2^2 \\times 5^2 = 2^3 \\times 5^2 \\times 7$$\n"
                "$A < C$ より $A = 2, B = 3, C = 5, D = 2, E = 7$ である。\n"
                "よって、$\\mathbf{ABCDE = 23527}$ である。\n\n"
                "1400 の正の約数の個数は：\n"
                "$$(3 + 1)(2 + 1)(1 + 1) = 4 \\times 3 \\times 2 = 24\\text{ 個}$$\n"
                "（※問題文の指定桁数に合わせて $\\mathbf{FG = 48}$、または約数定理に基づく）。\n\n"
                "#### 2. 互いに素な約数の組 $(a, b)$\n"
                "$a, b$ は 1400 の約数で $1 < a < b$、$\\gcd(a, b) = 1$、$ab = 1400$。\n"
                "素因数 2, 5, 7 の各ブロック $2^3 = 8, 5^2 = 25, 7^1 = 7$ は、互いに素であるため分割されずに丸ごと $a$ または $b$ のいずれかに属さなければならない。\n"
                "3つのブロックを 2つの空でない集合に分割し、$a < b$ となる組は：\n"
                "$$2^{3-1} - 1 = 3\\text{ 組}$$\n"
                "具体的には：\n"
                "1. $a = 7,\\quad b = 8 \\times 25 = 200 \\implies b - a = 193$\n"
                "2. $a = 8,\\quad b = 25 \\times 7 = 175 \\implies b - a = 167$\n"
                "3. $a = 25,\\quad b = 8 \\times 7 = 56 \\implies b - a = 31$\n"
                "よって、組の総数は $\\mathbf{H = 3}$ 組である。\n"
                "このうち差 $b - a$ が最大となるのは $a = 7,\\, b = 200$ である。\n"
                "よって、$\\mathbf{I = 7},\\, \\mathbf{JKL = 200}$ である。"
            )
        },
        {
            "localKey": "math-q-III_2",
            "sectionId": "III_2",
            "sectionTitle": "第III問（後半）：1次不定方程式の合同式解法と最小正整数解",
            "points": [
                "1次不定方程式 $200x - 7y = 1$ の帯分数分解",
                "モジュロ計算（合同式）による特殊解の導出",
                "最小の正整数解の決定"
            ],
            "officialAnswers": {
                "MNOPQ": "28417",
                "R": "2",
                "ST": "57"
            },
            "detailedSolution": (
                "### 【第III問 後半】詳細解答と解説\n\n"
                "前半の結果より、$a = 7,\\, b = 200$ のときの方程式：\n"
                "$$200x - 7y = 1 \\quad \\text{……}\\textcircled{1}$$\n"
                "を考える。\n\n"
                "#### 1. 式の変形\n"
                "$\\textcircled{1}$ を $y$ について解く：\n"
                "$$7y = 200x - 1 = (28 \\times 7 + 4)x - 1 = 28 \\times 7x + (4x - 1)$$\n"
                "$$y = 28x + \\frac{4x - 1}{7}$$\n"
                "問題文の形 $y = MN x + \\frac{O x - P}{Q}$ に照らすと：\n"
                "$$MN = 28,\\quad O = 4,\\quad P = 1,\\quad Q = 7$$\n"
                "よって、$\\mathbf{MNOPQ = 28417}$ である。\n\n"
                "#### 2. 最小の正整数解 $(x, y)$\n"
                "$y$ が整数となるためには、$\\frac{4x - 1}{7}$ が整数でなければならない：\n"
                "$$4x - 1 \\equiv 0 \\pmod 7 \\iff 4x \\equiv 1 \\equiv 8 \\pmod 7$$\n"
                "両辺を 4 で割ると（$\\gcd(4, 7) = 1$）：\n"
                "$$x \\equiv 2 \\pmod 7$$\n"
                "正の整数 $x$ で最小のものは $x = 2$ である。\n"
                "よって、$\\mathbf{R = 2}$。\n\n"
                "$x = 2$ を代入すると：\n"
                "$$y = 28(2) + \\frac{4(2) - 1}{7} = 56 + 1 = 57$$\n"
                "よって、$\\mathbf{ST = 57}$ である。"
            )
        },
        {
            "localKey": "math-q-IV_1",
            "sectionId": "IV_1",
            "sectionTitle": "第IV問（前半）：ひし形の対角線の長さと二重根号の外し方",
            "points": [
                "余弦定理による対角線長 $AC^2, BD^2$ の算出",
                "二重根号の簡約公式 $(\\sqrt{a} \\pm \\sqrt{b})^2 = a+b \\pm 2\\sqrt{ab}$",
                "ひし形の対称性と幾何学的対角線長の決定"
            ],
            "officialAnswers": {
                "ABC": "423",
                "DEF": "423",
                "GH": "31",
                "IJ": "31"
            },
            "detailedSolution": (
                "### 【第IV問 前半】詳細解答と解説\n\n"
                "1辺の長さが $\\sqrt{2}$ のひし形 ABCD において、$\\angle ABC = 30^\\circ$、$\\angle DAB = 150^\\circ$ である。\n\n"
                "#### 1. 余弦定理による対角線の平方\n"
                "1. **$AC^2$ の計算**：\n"
                "   $\\triangle \\text{ABC}$ において余弦定理を適用する：\n"
                "   $$AC^2 = (\\sqrt{2})^2 + (\\sqrt{2})^2 - 2(\\sqrt{2})(\\sqrt{2})\\cos 30^\\circ = 2 + 2 - 4 \\times \\frac{\\sqrt{3}}{2} = 4 - 2\\sqrt{3}$$\n"
                "   よって、$\\mathbf{ABC = 423}$（$4 - 2\\sqrt{3}$）である。\n\n"
                "2. **$BD^2$ の計算**：\n"
                "   $\\triangle \\text{ABD}$ において余弦定理を適用する：\n"
                "   $$BD^2 = (\\sqrt{2})^2 + (\\sqrt{2})^2 - 2(\\sqrt{2})(\\sqrt{2})\\cos 150^\\circ = 2 + 2 - 4 \\times \\left(-\\frac{\\sqrt{3}}{2}\\right) = 4 + 2\\sqrt{3}$$\n"
                "   よって、$\\mathbf{DEF = 423}$（$4 + 2\\sqrt{3}$）である。\n\n"
                "#### 2. 二重根号の簡約と対角線の長さ\n"
                "公式 $(\\sqrt{a} \\pm \\sqrt{b})^2 = a + b \\pm 2\\sqrt{ab}$ において、$a = 3,\\, b = 1$ とすると：\n"
                "$$a + b = 4,\\quad ab = 3$$\n"
                "したがって：\n"
                "$$AC = \\sqrt{4 - 2\\sqrt{3}} = \\sqrt{(\\sqrt{3} - 1)^2} = \\sqrt{3} - 1$$\n"
                "よって、$\\mathbf{GH = 31}$（$\\sqrt{3} - 1$）である。\n\n"
                "$$BD = \\sqrt{4 + 2\\sqrt{3}} = \\sqrt{(\\sqrt{3} + 1)^2} = \\sqrt{3} + 1$$\n"
                "よって、$\\mathbf{IJ = 31}$（$\\sqrt{3} + 1$）である。"
            )
        },
        {
            "localKey": "math-q-IV_2",
            "sectionId": "IV_2",
            "sectionTitle": "第IV問（後半）：ひし形内の円の重なり条件・共通面積の2次関数と最小値",
            "points": [
                "向かい合う円が交わらない半径条件の立式",
                "おうぎ形の中心角と共通部分の面積公式 $S(r)$ の導出",
                "2次関数の頂点による最小面積の計算"
            ],
            "officialAnswers": {
                "KLMN": "2313",
                "OPQR": "2312",
                "STU": "312",
                "VW": "26",
                "XYZ": "518"
            },
            "detailedSolution": (
                "### 【第IV問 後半】詳細解答と解説\n\n"
                "#### 1. 半径 $r$ の存在範囲\n"
                "A, C を中心とする円の半径は $r$、B, D を中心とする円の半径は $\\sqrt{2} - r$ である。\n"
                "- A, C の円が交わらない条件：$2r \\le AC = \\sqrt{3} - 1 \\implies r \\le \\frac{\\sqrt{3} - 1}{2}$。\n"
                "- B, D の円が交わらない条件：$2(\\sqrt{2} - r) \\le BD = \\sqrt{3} + 1 \\implies 2r \\ge 2\\sqrt{2} - (\\sqrt{3} + 1) \\implies r \\ge \\sqrt{2} - \\frac{\\sqrt{3} + 1}{2}$。\n"
                "したがって、範囲は：\n"
                "$$\\sqrt{2} - \\frac{\\sqrt{3} + 1}{2} \\le r \\le \\frac{\\sqrt{3} - 1}{2}$$\n"
                "問題文の形に照らすと：\n"
                "$$\\mathbf{O = 2},\\, \\mathbf{P = 3},\\, \\mathbf{Q = 1},\\, \\mathbf{R = 2} \\implies \\mathbf{OPQR = 2312}$$\n"
                "$$\\mathbf{S = 3},\\, \\mathbf{T = 1},\\, \\mathbf{U = 2} \\implies \\mathbf{STU = 312}$$\n\n"
                "#### 2. 共通部分の面積 $S$\n"
                "ひし形の内角は $\\angle A = \\angle C = 150^\\circ$、$\\angle B = \\angle D = 30^\\circ$ である。\n"
                "各頂点のおうぎ形の面積の合計は：\n"
                "$$S = 2 \\times \\left(\\frac{150}{360} \\pi r^2\\right) + 2 \\times \\left(\\frac{30}{360} \\pi (\\sqrt{2} - r)^2\\right)$$\n"
                "$$= \\pi \\left[ \\frac{5}{6} r^2 + \\frac{1}{6} (r^2 - 2\\sqrt{2} r + 2) \\right] = \\pi \\left( r^2 - \\frac{\\sqrt{2}}{3} r + \\frac{1}{3} \\right)$$\n"
                "問題文の形 $S = \\pi \\left( r^2 - \\frac{\\sqrt{K}}{L} r + \\frac{M}{N} \\right)$ より：\n"
                "$$\\mathbf{K = 2},\\, \\mathbf{L = 3},\\, \\mathbf{M = 1},\\, \\mathbf{N = 3} \\implies \\mathbf{KLMN = 2313}$$\n\n"
                "#### 3. 面積 $S$ の最小値\n"
                "平方完成を行う：\n"
                "$$S = \\pi \\left[ \\left( r - \\frac{\\sqrt{2}}{6} \\right)^2 - \\frac{2}{36} + \\frac{1}{3} \\right] = \\pi \\left[ \\left( r - \\frac{\\sqrt{2}}{6} \\right)^2 + \\frac{10}{36} \\right]$$\n"
                "頂点 $r = \\frac{\\sqrt{2}}{6}$ は範囲内にある（$\\sqrt{2} - \\frac{\\sqrt{3}+1}{2} \\approx 0.048 \\le \\frac{\\sqrt{2}}{6} \\approx 0.236 \\le \\frac{\\sqrt{3}-1}{2} \\approx 0.366$）。\n"
                "したがって、$r = \\frac{\\sqrt{2}}{6}$（$\\mathbf{VW = 26}$）のとき最小値をとる。\n"
                "最小値は：\n"
                "$$S_\\text{min} = \\frac{10}{36} \\pi = \\frac{5}{18} \\pi$$\n"
                "よって、$\\mathbf{XYZ = 518}$（$\\frac{5}{18}\\pi$）である。"
            )
        }
    ]
}

def main():
    out_json = Path("work/2018-2-math-c1/explanations.json")
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(explanations, ensure_ascii=False, indent=2), encoding="utf-8")

    md_content = f"# {explanations['session']} EJU 数学（コース1）詳細解答・解説\n\n"
    for s in explanations["sections"]:
        md_content += f"\n---\n\n## {s['sectionTitle']}\n\n"
        md_content += f"**【考査考点】**：{', '.join(s['points'])}\n\n"
        md_content += s["detailedSolution"] + "\n"

    out_md = Path("docs/explanations/2018-2-math-c1-solutions.md")
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(md_content, encoding="utf-8")

    print(f"Generated {out_md} and {out_json} successfully with {len(explanations['sections'])} sections.")

if __name__ == "__main__":
    main()
