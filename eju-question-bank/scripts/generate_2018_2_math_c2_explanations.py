#!/usr/bin/env python3
"""Generate comprehensive explanations for 2018-2 EJU Mathematics Course 2."""

import json
from pathlib import Path

explanations = {
    "session": "2018-2",
    "subject": "MATHEMATICS",
    "course": "COURSE_2",
    "formCode": "MATHEMATICS_COURSE_2_JA",
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
            "sectionTitle": "第II問 問1：漸化式で定義された数列の一般項と無限級数の部分和・極限",
            "points": [
                "変換数列 $b_n$ の比による階乗的消去と一般項 $a_n$ の導出",
                "部分分数分解と隣接項相殺型（望遠鏡型）の級数和",
                "無限級数の極限値の算出"
            ],
            "officialAnswers": {
                "AB": "28",
                "CD": "45",
                "E": "3",
                "FG": "14",
                "HIJ": "-14",
                "KLM": "141",
                "NO": "14"
            },
            "detailedSolution": (
                "### 【第II問 問1】詳細解答と解説\n\n"
                "数列 $\\{a_n\\}$ は $a_1 = \\frac{2}{9}$、および $a_n = \\frac{(n+1)(2n-3)}{3n(2n+1)} a_{n-1}$（$n \\ge 2$）で定義されている。\n\n"
                "#### (1) 数列 $b_n$ の導入と一般項 $a_n$\n"
                "$b_n = \\frac{n+1}{3^n a_n}$ とおき、比 $\\frac{b_n}{b_{n-1}}$ を計算する：\n"
                "$$\\frac{b_n}{b_{n-1}} = \\frac{\\frac{n+1}{3^n a_n}}{\\frac{n}{3^{n-1} a_{n-1}}} = \\frac{n+1}{3n} \\cdot \\frac{a_{n-1}}{a_n}$$\n"
                "したがって、$\\frac{A}{B} = \\frac{n+1}{3n}$ である。選択肢より $n+1$ は $\\textcircled{2}$、$3n$ は $\\textcircled{8}$ であるから、$\\mathbf{AB = 28}$。\n\n"
                "与えられた漸化式より $\\frac{a_{n-1}}{a_n} = \\frac{3n(2n+1)}{(n+1)(2n-3)}$ を代入すると：\n"
                "$$\\frac{b_n}{b_{n-1}} = \\frac{n+1}{3n} \\cdot \\frac{3n(2n+1)}{(n+1)(2n-3)} = \\frac{2n+1}{2n-3}$$\n"
                "選択肢より $2n+1$ は $\\textcircled{4}$、$2n-3$ は $\\textcircled{5}$ であるから、$\\mathbf{CD = 45}$ である。\n\n"
                "初項 $b_1 = \\frac{1+1}{3(2/9)} = \\frac{2}{2/3} = 3$ である。\n"
                "累乗積をとると：\n"
                "$$b_n = b_1 \\cdot \\frac{5}{1} \\cdot \\frac{7}{3} \\cdot \\frac{9}{5} \\cdots \\frac{2n-1}{2n-5} \\cdot \\frac{2n+1}{2n-3} = (2n-1)(2n+1)$$\n"
                "したがって：\n"
                "$$a_n = \\frac{n+1}{3^n b_n} = \\frac{n+1}{3^n (2n-1)(2n+1)}$$\n"
                "選択肢より $2n-1$ は $\\textcircled{3}$ であるから、$\\mathbf{E = 3}$ である。\n\n"
                "#### (2) 無限級数の和\n"
                "$c_n = \\frac{1}{3^n(2n+1)}$ とおく。\n"
                "$$a_n = A c_{n-1} + B c_n = A \\frac{1}{3^{n-1}(2n-1)} + B \\frac{1}{3^n(2n+1)} = \\frac{3A(2n+1) + B(2n-1)}{3^n(2n-1)(2n+1)}$$\n"
                "分子を恒等的に比較する：\n"
                "$$(6A + 2B)n + (3A - B) = n + 1$$\n"
                "連立方程式：\n"
                "$$\\begin{cases} 6A + 2B = 1 \\\\ 3A - B = 1 \\end{cases} \\implies A = \\frac{1}{4},\\quad B = -\\frac{1}{4}$$\n"
                "よって、$A = \\frac{1}{4}$（$\\mathbf{FG = 14}$）、$B = -\\frac{1}{4}$（$\\mathbf{HIJ = -14}$）である。\n\n"
                "したがって、$a_k = \\frac{1}{4}(c_{k-1} - c_k)$ と変形できるため、部分和 $S_n$ は：\n"
                "$$S_n = \\sum_{k=1}^n \\frac{1}{4}(c_{k-1} - c_k) = \\frac{1}{4}(c_0 - c_n)$$\n"
                "$c_0 = \\frac{1}{3^0(1)} = 1$ であるから：\n"
                "$$S_n = \\frac{1}{4}(1 - c_n)$$\n"
                "よって、$\\mathbf{K = 1},\\, \\mathbf{L = 4},\\, \\mathbf{M = 1}$（解答番号 $\\mathbf{KLM = 141}$）である。\n\n"
                "$n \\to \\infty$ のとき $c_n \\to 0$ であるから：\n"
                "$$\\sum_{n=1}^\\infty a_n = \\lim_{n \\to \\infty} S_n = \\frac{1}{4}$$\n"
                "よって、$\\mathbf{NO = 14}$（$\\frac{1}{4}$）である。"
            )
        },
        {
            "localKey": "math-q-II_2",
            "sectionId": "II_2",
            "sectionTitle": "第II問 問2：円の方程式と接線・外部の点から引いた接線長と直交条件",
            "points": [
                "円の方程式の展開と円上の点における接線公式",
                "三平方の定理による接線の長さ公式 $AP = \\sqrt{AC^2 - R^2}$ と最小値",
                "2本の接線が直交する幾何学的条件（直角二等辺三角形の形成）"
            ],
            "officialAnswers": {
                "PQR": "109",
                "STU": "559",
                "V": "0",
                "W": "3",
                "X": "4",
                "Y": "7"
            },
            "detailedSolution": (
                "### 【第II問 問2】詳細解答と解説\n\n"
                "中心 $(5, 0)$、半径 4 の円 $C$ を考える。\n\n"
                "#### (1) 円の方程式と接線の方程式\n"
                "円 $C$ の方程式は：\n"
                "$$(x - 5)^2 + y^2 = 16 \\implies x^2 - 10x + 25 + y^2 = 16 \\implies x^2 - 10x + y^2 + 9 = 0$$\n"
                "よって、点 $P(p, q)$ に対し $p^2 - 10p + q^2 + 9 = 0$ が成り立ち、$\\mathbf{PQR = 109}$ である。\n\n"
                "点 $P(p, q)$ における接線の方程式は：\n"
                "$$(p - 5)(x - 5) + qy = 16 \\implies (p - 5)x + qy = 5(p - 5) + 16 = 5p - 9$$\n"
                "よって、$\\mathbf{S = 5},\\, \\mathbf{T = 5},\\, \\mathbf{U = 9}$（解答番号 $\\mathbf{STU = 559}$）である。\n\n"
                "#### (2) 接線長 AP の最小値と接線の直交条件\n"
                "点 $A(0, a)$（$a \\ge 0$）から円 $C$ に引いた接線の長さを $AP$ とする。\n"
                "円の中心を $C(5, 0)$、半径を $R = 4$ とすると、$\\triangle ACP$ は $\\angle APC = 90^\\circ$ の直角三角形である。\n"
                "三平方の定理より：\n"
                "$$AP^2 = AC^2 - R^2 = (5^2 + a^2) - 4^2 = 25 + a^2 - 16 = a^2 + 9$$\n"
                "$$AP = \\sqrt{a^2 + 9}$$\n"
                "$a \\ge 0$ であるから、$AP$ が最小となるのは $a = 0$ のときであり、最小値は $\\sqrt{9} = 3$ である。\n"
                "よって、$\\mathbf{V = 0},\\, \\mathbf{W = 3}$ である。\n\n"
                "点 $A$ から引いた 2本の接線が直交するとき、点 $A$、2つの接点、円の中心 $C$ で作られる四角形は 1辺が半径 4 の正方形となる。\n"
                "したがって、接線の長さは半径に等しく $AP = 4$ である。よって $\\mathbf{X = 4}$。\n"
                "$$AP = \\sqrt{a^2 + 9} = 4 \\implies a^2 + 9 = 16 \\implies a^2 = 7$$\n"
                "$a \\ge 0$ より $a = \\sqrt{7}$ である。よって $\\mathbf{Y = 7}$ である。"
            )
        },
        {
            "localKey": "math-q-III_1",
            "sectionId": "III_1",
            "sectionTitle": "第III問（前半）：3次関数の導関数の因数分解と極値・増減の場合分け",
            "points": [
                "3次関数の導関数 $f'(x) = 3(x - 2a - 1)(x + 1)$ の因数分解",
                "パラメータ $a$ による2根の大小関係の分類",
                "極大・極小の判定と単調増加条件"
            ],
            "officialAnswers": {
                "ABCD": "3211",
                "EF": "-1",
                "G": "0",
                "H": "1",
                "I": "2",
                "J": "1",
                "K": "0"
            },
            "detailedSolution": (
                "### 【第III問 前半】詳細解答と解説\n\n"
                "3次関数 $f(x) = x^3 - 3ax^2 - 3(2a+1)x + a + 2$ を考える。\n\n"
                "#### 1. 導関数 $f'(x)$ の因数分解\n"
                "$$f'(x) = 3x^2 - 6ax - 3(2a+1) = 3\\left[x^2 - 2ax - (2a+1)\\right]$$\n"
                "定数項 $-(2a+1) = -(2a+1) \\times 1$ であり、和は $-(2a+1) + 1 = -2a$ となる。\n"
                "したがって：\n"
                "$$f'(x) = 3(x - (2a+1))(x + 1)$$\n"
                "問題文の形 $f'(x) = A(x - Ba - C)(x + D)$ に照らすと：\n"
                "$$A = 3,\\quad B = 2,\\quad C = 1,\\quad D = 1$$\n"
                "よって、$\\mathbf{ABCD = 3211}$ である。\n\n"
                "#### 2. $a$ の値による増減と極値の分類\n"
                "$f'(x) = 0$ の2根は $x = 2a+1$ と $x = -1$ である。\n"
                "2根の大小の分岐点は $2a + 1 = -1 \\iff a = -1$ である。よって $\\mathbf{EF = -1}$。\n\n"
                "- **(i) $a > -1$ のとき**：$2a + 1 > -1$ である。\n"
                "  $f'(x)$ の符号は $x < -1$ で正、$-1 < x < 2a+1$ で負、$x > 2a+1$ で正。\n"
                "  したがって、$f(x)$ は $x = -1$ で**極大**（選択肢 $\\textcircled{0} \\implies \\mathbf{G = 0}$）、$x = 2a+1$ で**極小**（選択肢 $\\textcircled{1} \\implies \\mathbf{H = 1}$）となる。\n"
                "- **(ii) $a = -1$ のとき**：$f'(x) = 3(x+1)^2 \\ge 0$ となり、重解をもつ。\n"
                "  したがって、$f(x)$ はつねに**増加**（選択肢 $\\textcircled{2} \\implies \\mathbf{I = 2}$）する。\n"
                "- **(iii) $a < -1$ のとき**：$2a + 1 < -1$ である。\n"
                "  したがって、$f(x)$ は $x = 2a+1$ で**極大**（選択肢 $\\textcircled{0} \\implies \\mathbf{K = 0}$）、$x = -1$ で**極小**（選択肢 $\\textcircled{1} \\implies \\mathbf{J = 1}$）となる。"
            )
        },
        {
            "localKey": "math-q-III_2",
            "sectionId": "III_2",
            "sectionTitle": "第III問（後半）：閉区間における3次関数の最小値関数とその最大値",
            "points": [
                "区間 $[-1, 1]$ に対する極値の位置による最小値関数 $m(a)$ の導出",
                "3次多項式関数の微分法による最大値の特定"
            ],
            "officialAnswers": {
                "L": "0",
                "MN": "-8",
                "OP": "-1",
                "QRST": "-432",
                "UV": "44",
                "WXY": "333"
            },
            "detailedSolution": (
                "### 【第III問 後半】詳細解答と解説\n\n"
                "閉区間 $-1 \\le x \\le 1$ における $f(x)$ の最小値 $m$ を求める。\n\n"
                "#### 1. 最小値 $m(a)$ の場合分け\n"
                "1. **$a \\ge 0$ のとき（$\\mathbf{L = 0}$）**：\n"
                "   極小点の位置は $2a + 1 \\ge 1$ となり、区間 $[-1, 1]$ の右外側にある。\n"
                "   したがって区間 $[-1, 1]$ では $f'(x) \\le 0$（単調減少）となり、最小値は右端 $x = 1$ でとる：\n"
                "   $$m = f(1) = 1 - 3a - 3(2a+1) + a + 2 = -8a$$\n"
                "   よって、$\\mathbf{MN = -8}$ である。\n\n"
                "2. **$-1 \\le a < 0$ のとき（$\\mathbf{OP = -1},\\, \\mathbf{L = 0}$）**：\n"
                "   極小点 $x = 2a+1$ が区間 $[-1, 1]$ の内部にあるため、最小値は極小値 $f(2a+1)$ である：\n"
                "   $$f(2a+1) = (2a+1)^3 - 3a(2a+1)^2 - 3(2a+1)^2 + a + 2$$\n"
                "   $$= -4a^3 - 12a^2 - 8a = -4\\left(a^3 + 3a^2 + 2a\\right)$$\n"
                "   よって、$\\mathbf{QR = -4},\\, \\mathbf{S = 3},\\, \\mathbf{T = 2}$（解答番号 $\\mathbf{QRST = -432}$）である。\n\n"
                "3. **$a < -1$ のとき**：\n"
                "   極大点 $2a+1 < -1$ であり、区間 $[-1, 1]$ では単調増加する。\n"
                "   したがって、最小値は左端 $x = -1$ でとる：\n"
                "   $$m = f(-1) = -1 - 3a + 3(2a+1) + a + 2 = 4a + 4$$\n"
                "   よって、$\\mathbf{UV = 44}$ である。\n\n"
                "#### 2. $m(a)$ が最大となる $a$\n"
                "- $a \\ge 0$ では $m(a) = -8a \\le 0$。\n"
                "- $a < -1$ では $m(a) = 4a + 4 < 0$。\n"
                "- $-1 \\le a \\le 0$ では $m(a) = -4a^3 - 12a^2 - 8a$。\n"
                "微分して極大値を求める：\n"
                "$$\\frac{dm}{da} = -12a^2 - 24a - 8 = -4\\left(3a^2 + 6a + 2\\right) = 0$$\n"
                "$$a = \\frac{-3 \\pm \\sqrt{3^2 - 3 \\times 2}}{3} = \\frac{-3 + \\sqrt{3}}{3} \\quad (\\because -1 \\le a \\le 0)$$\n"
                "問題文の形 $a = \\frac{-W + \\sqrt{X}}{Y}$ に照らすと：\n"
                "$$\\mathbf{W = 3},\\, \\mathbf{X = 3},\\, \\mathbf{Y = 3} \\implies \\mathbf{WXY = 333}$$\n"
                "よって、$\\mathbf{WXY = 333}$ である。"
            )
        },
        {
            "localKey": "math-q-IV_1",
            "sectionId": "IV_1",
            "sectionTitle": "第IV問（前半）：対数関数の接線と接するパラメータ条件・最小値",
            "points": [
                "積の微分法による $y = x\\log ax$ の接線方程式の導出",
                "直線 $y = 2x - 3$ との一致条件によるパラメータ $a$ および接点の決定",
                "導関数の符号と極値・最小値の計算"
            ],
            "officialAnswers": {
                "A": "0",
                "B": "3",
                "CD": "33",
                "EF": "32",
                "GH": "32"
            },
            "detailedSolution": (
                "### 【第IV問 前半】詳細解答と解説\n\n"
                "2つの関数 $y = x\\log ax$（$\\textcircled{1}$）と $y = 2x - 3$（$\\textcircled{2}$）を考える（$a > 0$）。\n\n"
                "#### 1. 接線方程式と接する条件\n"
                "$\\textcircled{1}$ を微分する：\n"
                "$$y' = \\log ax + x \\cdot \\frac{a}{ax} = \\log ax + 1$$\n"
                "点 $(t, t\\log at)$ における接線の方程式は：\n"
                "$$y - t\\log at = (\\log at + 1)(x - t) \\implies y = (\\log at + 1)x - t$$\n"
                "これは選択肢 $\\textcircled{0}$ に対応する。よって $\\mathbf{A = 0}$。\n\n"
                "この直線が $\\textcircled{2}$ $y = 2x - 3$ と一致するための条件は：\n"
                "$$\\begin{cases} \\log at + 1 = 2 \\implies \\log at = 1 \\implies at = e \\\\ -t = -3 \\implies t = 3 \\end{cases}$$\n"
                "したがって：\n"
                "$$3a = e \\implies a = \\frac{e}{3}$$\n"
                "よって、$\\mathbf{B = 3}$ である。\n"
                "接点の座標は $(t, 2t-3) = (3, 3)$ である。よって $\\mathbf{CD = 33}$ である。\n\n"
                "#### 2. 関数 $\\textcircled{1}$ の最小値\n"
                "$a = \\frac{e}{3}$ のとき、$y = x\\log\\left(\\frac{ex}{3}\\right)$ である。\n"
                "$$y' = \\log\\left(\\frac{ex}{3}\\right) + 1 = 0 \\iff \\log\\left(\\frac{ex}{3}\\right) = -1 \\iff \\frac{ex}{3} = e^{-1} \\iff x = 3e^{-2}$$\n"
                "増減表より、$x = 3e^{-2}$ で最小値をとる。よって $\\mathbf{EF = 32}$（$3e^{-2}$）である。\n"
                "最小値は：\n"
                "$$y\\left(3e^{-2}\\right) = 3e^{-2} \\log(e^{-1}) = -3e^{-2}$$\n"
                "よって、$\\mathbf{GH = 32}$（$-3e^{-2}$）である。"
            )
        },
        {
            "localKey": "math-q-IV_2",
            "sectionId": "IV_2",
            "sectionTitle": "第IV問（後半）：部分積分法と曲線・接線・$x$ 軸で囲まれる面積の定積分",
            "points": [
                "部分積分法 $\\int x\\log ax dx = \\frac{1}{2}x^2\\log ax - \\frac{1}{4}x^2 + C$",
                "曲線と接線および $x$ 軸との交点の特定",
                "図形の分割による面積 $S$ の定積分計算"
            ],
            "officialAnswers": {
                "I": "2",
                "JKL": "942"
            },
            "detailedSolution": (
                "### 【第IV問 後半】詳細解答と解説\n\n"
                "#### 1. 不定積分の計算\n"
                "部分積分法を用いる：\n"
                "$$\\int x \\log ax \\, dx = \\frac{1}{2} x^2 \\log ax - \\int \\frac{1}{2} x^2 \\cdot \\frac{1}{x} \\, dx = \\frac{1}{2} x^2 \\log ax - \\frac{1}{4} x^2 + C$$\n"
                "これは選択肢 $\\textcircled{2}$ に対応する。よって $\\mathbf{I = 2}$ である。\n\n"
                "#### 2. 面積 $S$ の計算\n"
                "$a = \\frac{e}{3}$ のとき：\n"
                "- 曲線 $\\textcircled{1}$ $y = x\\log\\left(\\frac{ex}{3}\\right)$ と $x$ 軸の交点：$y = 0 \\iff \\frac{ex}{3} = 1 \\iff x = \\frac{3}{e} = 3e^{-1}$。\n"
                "- 直線 $\\textcircled{2}$ $y = 2x - 3$ と $x$ 軸の交点：$y = 0 \\iff x = \\frac{3}{2}$。\n"
                "- 曲線と直線は点 $(3, 3)$ で接する。\n\n"
                "求める面積 $S$ は、曲線と $x$ 軸および $x = 3$ で囲まれた部分から、直線と $x$ 軸および $x = 3$ で囲まれた直角三角形の面積を引くことで求められる：\n"
                "$$S = \\int_{3e^{-1}}^3 x \\log\\left(\\frac{ex}{3}\\right) \\, dx - \\frac{1}{2} \\left(3 - \\frac{3}{2}\\right) \\times 3$$\n"
                "直角三角形の面積は：\n"
                "$$\\frac{1}{2} \\times \\frac{3}{2} \\times 3 = \\frac{9}{4}$$\n"
                "定積分を計算する：\n"
                "$$\\int_{3e^{-1}}^3 x \\log\\left(\\frac{ex}{3}\\right) \\, dx = \\left[ \\frac{1}{2} x^2 \\log\\left(\\frac{ex}{3}\\right) - \\frac{1}{4} x^2 \\right]_{3e^{-1}}^3$$\n"
                "- 上端 $x = 3$：$\\frac{9}{2} \\log e - \\frac{9}{4} = \\frac{9}{2} - \\frac{9}{4} = \\frac{9}{4}$\n"
                "- 下端 $x = 3e^{-1}$：$\\frac{1}{2} (9e^{-2}) \\log 1 - \\frac{1}{4} (9e^{-2}) = -\\frac{9}{4} e^{-2}$\n"
                "したがって、定積分の値は：\n"
                "$$\\frac{9}{4} - \\left(-\\frac{9}{4} e^{-2}\\right) = \\frac{9}{4} + \\frac{9}{4} e^{-2}$$\n"
                "三角形の面積 $\\frac{9}{4}$ を引くと：\n"
                "$$S = \\left(\\frac{9}{4} + \\frac{9}{4} e^{-2}\\right) - \\frac{9}{4} = \\frac{9}{4} e^{-2}$$\n"
                "問題文の形 $S = \\frac{J}{K} e^{-L}$ に照らすと：\n"
                "$$J = 9,\\quad K = 4,\\quad L = 2$$\n"
                "よって、$\\mathbf{JKL = 942}$ である。"
            )
        }
    ]
}

def main():
    out_json = Path("work/2018-2-math-c2/explanations.json")
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(explanations, ensure_ascii=False, indent=2), encoding="utf-8")

    md_content = f"# {explanations['session']} EJU 数学（コース2）詳細解答・解説\n\n"
    for s in explanations["sections"]:
        md_content += f"\n---\n\n## {s['sectionTitle']}\n\n"
        md_content += f"**【考査考点】**：{', '.join(s['points'])}\n\n"
        md_content += s["detailedSolution"] + "\n"

    out_md = Path("docs/explanations/2018-2-math-c2-solutions.md")
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(md_content, encoding="utf-8")

    print(f"Generated {out_md} and {out_json} successfully with {len(explanations['sections'])} sections.")

if __name__ == "__main__":
    main()
