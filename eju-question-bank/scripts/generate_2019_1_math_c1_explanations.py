#!/usr/bin/env python3
"""Generate comprehensive explanations for 2019-1 EJU Mathematics Course 1."""

import json
from pathlib import Path

explanations = {
    "session": "2019-1",
    "subject": "MATHEMATICS",
    "course": "COURSE_1",
    "formCode": "MATHEMATICS_COURSE_1_JA",
    "sections": [
        {
            "sectionId": "I_1",
            "sectionTitle": "第I問 問1：2次関数のグラフと係数の符号判定・二次式の最小値問題",
            "points": [
                "2次関数 $y = ax^2 + bx + c$ のグラフの開き（$a$ の正負）と軸の位置（$-b/(2a)$）",
                "$y$ 切片（$c$）と特定の値 $x = 1, -1, 2$ における関数値の符号判定",
                "判別式 $D = b^2 - 4ac$ による共有点の判定",
                "条件 $a+b+c=0$ のもとでの $a^2 - 8b - 8c$ の最小化と変数 $b$ の取り得る値の範囲"
            ],
            "officialAnswers": {
                "A": "9",
                "B": "7",
                "C": "7",
                "D": "8",
                "E": "9",
                "F": "9",
                "G": "7",
                "H": "6",
                "I": "4",
                "J": "0",
                "K": "4"
            },
            "detailedSolution": (
                "### 【第I問 問1】詳細解答と解説\n\n"
                "#### (1) グラフの幾何学的特徴から係数の符号判定\n"
                "与えられた 2 次関数は $y = ax^2 + bx + c$ である。\n"
                "問題図より、放物線は以下の特徴をもつ：\n"
                "1. **上に凸の放物線**：\n"
                "   放物線が上に凸（開口下向き）であることから、$a < 0$ である。\n"
                "   選択肢 $\\textcircled{9}$（$<$）より、$\\mathbf{A = 9}$。\n"
                "2. **対称軸の位置**：\n"
                "   放物線の軸の方程式は $x = -\\frac{b}{2a}$ である。\n"
                "   図より軸は $y$ 軸の右側（$x > 0$）にある。\n"
                "   $a < 0$ より $-2a > 0$ であるから、$-\\frac{b}{2a} > 0 \\iff b > 0$ である。\n"
                "   選択肢 $\\textcircled{7}$（$>$）より、$\\mathbf{B = 7}$。\n"
                "3. **$y$ 切片の符号**：\n"
                "   $x = 0$ のときの $y$ 座標は $c$ である。\n"
                "   図よりグラフと $y$ 軸の交点は原点より上（$y > 0$）にあるため、$c > 0$ である。\n"
                "   選択肢 $\\textcircled{7}$（$>$）より、$\\mathbf{C = 7}$。\n"
                "4. **$x = 1$ における関数値**：\n"
                "   図より、放物線は点 $(1, 0)$ を通過している（$x$ 軸との右側の交点が $x = 1$）。\n"
                "   したがって、$x = 1$ を代入した値 $a(1)^2 + b(1) + c = a + b + c = 0$ である。\n"
                "   選択肢 $\\textcircled{8}$（$=$）より、$\\mathbf{D = 8}$。\n"
                "5. **$x = -1$ における関数値**：\n"
                "   図より、$x = -1$ でのグラフの点は $x$ 軸より下方（$y < 0$）にある。\n"
                "   したがって、$a(-1)^2 + b(-1) + c = a - b + c < 0$ である。\n"
                "   選択肢 $\\textcircled{9}$（$<$）より、$\\mathbf{E = 9}$。\n"
                "6. **$x = 2$ における関数値**：\n"
                "   軸が $0 < x < 1$ にあり、$x = 1$ で $y = 0$、上に凸であるため、$x = 2$ では $y$ 座標は負となる。\n"
                "   したがって、$a(2)^2 + b(2) + c = 4a + 2b + c < 0$ である。\n"
                "   選択肢 $\\textcircled{9}$（$<$）より、$\\mathbf{F = 9}$。\n"
                "7. **判別式の符号**：\n"
                "   放物線は $x$ 軸と異なる 2 点で交わっているため、2次方程式 $ax^2 + bx + c = 0$ の判別式は正である。\n"
                "   したがって、$b^2 - 4ac > 0$ である。\n"
                "   選択肢 $\\textcircled{7}$（$>$）より、$\\mathbf{G = 7}$。\n\n"
                "#### (2) 条件を満たすときの最小値問題と変数の範囲\n"
                "条件 (i) より $a < 0, b > 0, c > 0$、条件 (ii) より $a + b + c = 0$ である。\n"
                "$a + b + c = 0$ より $c = -a - b$ であるから、対象の式を変形する：\n"
                "$$a^2 - 8b - 8c = a^2 - 8b - 8(-a - b) = a^2 - 8b + 8a + 8b = a^2 + 8a$$\n"
                "$b$ の項が相殺され、$a$ の 2次関数となる：\n"
                "$$a^2 + 8a = (a + 4)^2 - 16$$\n"
                "選択肢の数値欄（$\\textcircled{0}:0, \\dots, \\textcircled{5}:-2, \\textcircled{6}:-4$）から、$a < 0$ の範囲でこの 2次式が最小値をとるのは頂点 $a = -4$ のときである。\n"
                "選択肢 $\\textcircled{6}$（$-4$）より、$\\mathbf{H = 6}$（数値としては $a = -4$）。\n\n"
                "$a = -4$ のとき、$c = -a - b = 4 - b$ となる。\n"
                "これを $y = ax^2 + bx + c$ に代入すると：\n"
                "$$y = -4x^2 + bx + (4 - b) = -4x^2 + bx - b + 4$$\n"
                "問題文の形式 $y = \\text{H} x^2 + bx - b + \\text{I}$ と比較すると、$\\text{I}$ の位置には $+4$ が入る。\n"
                "したがって、$\\mathbf{I = 4}$。\n\n"
                "最後に、$b$ の取り得る値の範囲を決定する：\n"
                "- $b > 0$ であること（条件 (i) より）。\n"
                "- $c > 0 \\iff 4 - b > 0 \\iff b < 4$ であること（条件 (i) より）。\n"
                "- また、$x = 1$ で $y = 0$ は常に満たされ、軸 $x = -\\frac{b}{2(-4)} = \\frac{b}{8}$ は $0 < b < 4$ のとき $0 < x < \\frac{1}{2}$ となり、$0 < x < 1$ にあることとも完全に整合する。\n"
                "したがって、求める $b$ の範囲は $0 < b < 4$ である。\n"
                "よって、$\\mathbf{J = 0, K = 4}$。"
            )
        },
        {
            "sectionId": "I_2",
            "sectionTitle": "第I問 問2：不正なサイコロの確率・独立試行と事象の比較",
            "points": [
                "確率の公理と全事象の確率（和が 1）",
                "独立試行における余事象の確率計算",
                "2回の試行における確率の差の評価（$1/36$ との比較）",
                "3回の試行における倍率評価（2倍未満・以上の判定）"
            ],
            "officialAnswers": {
                "L": "2",
                "M": "1",
                "NO": "17",
                "PQRS": "2549",
                "TUVW": "2449",
                "X": "4",
                "Y": "1"
            },
            "detailedSolution": (
                "### 【第I問 問2】詳細解答と解説\n\n"
                "#### (1) 各目が出る確率 $p$ の決定\n"
                "サイコロ X において、1 から 5 までの目が出る確率はそれぞれ $p$ で等しく、6 の目が出る確率は他の目の 2 倍である。\n"
                "したがって、6 の目が出る確率は $2p$ である。よって、$\\mathbf{L = 2}$。\n"
                "全事象の確率は 1 であるから、$\\mathbf{M = 1}$。\n"
                "すべての目の確率の和をとると：\n"
                "$$5 \\times p + 2p = 7p = 1 \\implies p = \\frac{1}{7}$$\n"
                "したがって、$\\mathbf{NO = 17}$（$p = 1/7$）。\n"
                "これより：\n"
                "- 1 から 5 までの目が出る確率：$5p = \\frac{5}{7}$\n"
                "- 6 の目が出る確率：$2p = \\frac{2}{7}$\n\n"
                "#### (2) 2回投げたときの事象 $A, B$ の確率と差の評価\n"
                "- 事象 $A$（2回とも 1 から 5 の目が出る）：\n"
                "  各回独立であるから：\n"
                "  $$P(A) = \\left(\\frac{5}{7}\\right)^2 = \\frac{25}{49}$$\n"
                "  したがって、$\\mathbf{PQRS = 2549}$（$P(A) = 25/49$）。\n"
                "- 事象 $B$（少なくとも 1 回は 6 の目が出る）：\n"
                "  事象 $B$ は事象 $A$ の余事象（全事象から「2回とも 1～5」を除いたもの）であるから：\n"
                "  $$P(B) = 1 - P(A) = 1 - \\frac{25}{49} = \\frac{24}{49}$$\n"
                "  したがって、$\\mathbf{TUVW = 2449}$（$P(B) = 24/49$）。\n\n"
                "- $P(A)$ と $P(B)$ の比較：\n"
                "  $$P(A) - P(B) = \\frac{25}{49} - \\frac{24}{49} = \\frac{1}{49} > 0$$\n"
                "  より、$P(A)$ の方が $P(B)$ より高い。\n"
                "  この差 $\\frac{1}{49}$ と $\\frac{1}{36}$ の大小を比較すると：\n"
                "  $$49 > 36 \\implies \\frac{1}{49} < \\frac{1}{36}$$\n"
                "  したがって、「$P(A)$ の方が $P(B)$ より高く、その差は $\\frac{1}{36}$ 未満」である。\n"
                "  対応する選択肢は $\\textcircled{4}$ である。よって、$\\mathbf{X = 4}$。\n\n"
                "#### (3) 3回投げたときの事象 $C, D$ の確率と倍率の評価\n"
                "- 事象 $C$（3回とも 1 から 5 の目が出る）：\n"
                "  $$P(C) = \\left(\\frac{5}{7}\\right)^3 = \\frac{125}{343}$$\n"
                "- 事象 $D$（少なくとも 1 回は 6 の目が出る）：\n"
                "  $$P(D) = 1 - P(C) = 1 - \\frac{125}{343} = \\frac{218}{343}$$\n"
                "  $125 < 218$ より、$P(C)$ の方が $P(D)$ より低い。\n"
                "- $P(D)$ と $P(C)$ の比（倍率）：\n"
                "  $$\\frac{P(D)}{P(C)} = \\frac{218}{125} = 1.744$$\n"
                "  $1.744 < 2$ であるから、$P(D)$ は $P(C)$ の 2倍未満である。\n"
                "  したがって、「$P(C)$ の方が $P(D)$ より低く、$P(D)$ は $P(C)$ の 2倍未満」である。\n"
                "  対応する選択肢は $\\textcircled{1}$ である。よって、$\\mathbf{Y = 1}$。"
            )
        },
        {
            "sectionId": "II_1",
            "sectionTitle": "第II問 問1：分母の有理化・無理数の整数部分・絶対値不等式の整数解",
            "points": [
                "分母の有理化（共役無理数 $(\\sqrt{5}+\\sqrt{3})$ の積）",
                "無理数の整数部分の評価（$3 < \\sqrt{15} < 4$）",
                "場合分けによる絶対値記号の解除",
                "不等式を満たす整数解の個数と範囲の決定"
            ],
            "officialAnswers": {
                "ABC": "415",
                "D": "7",
                "E": "7",
                "F": "2",
                "G": "8",
                "H": "5",
                "I": "6",
                "J": "8"
            },
            "detailedSolution": (
                "### 【第II問 問1】詳細解答と解説\n\n"
                "#### (1) $\\frac{a}{b}$ の有理化と整数部分の決定\n"
                "$a = \\sqrt{5} + \\sqrt{3}, b = \\sqrt{5} - \\sqrt{3}$ である。\n"
                "分母を有理化するために分子・分母に $\\sqrt{5} + \\sqrt{3}$ を掛ける：\n"
                "$$\\frac{a}{b} = \\frac{\\sqrt{5} + \\sqrt{3}}{\\sqrt{5} - \\sqrt{3}} = \\frac{(\\sqrt{5} + \\sqrt{3})^2}{(\\sqrt{5})^2 - (\\sqrt{3})^2} = \\frac{5 + 2\\sqrt{15} + 3}{5 - 3} = \\frac{8 + 2\\sqrt{15}}{2} = 4 + \\sqrt{15}$$\n"
                "問題文の形式 $\\frac{a}{b} = \\text{A} + \\sqrt{\\text{BC}}$ と比較して：\n"
                "$$\\mathbf{A = 4, BC = 15} \\implies \\mathbf{ABC = 415}$$\n\n"
                "$\\sqrt{15}$ の近似値を評価する：\n"
                "$$9 < 15 < 16 \\implies 3 < \\sqrt{15} < 4$$\n"
                "各辺に 4 を足すと：\n"
                "$$7 < 4 + \\sqrt{15} < 8$$\n"
                "したがって、$\\frac{a}{b}$ より小さい整数の中で最大のものは **7** である。\n"
                "よって、$\\mathbf{D = 7}$。\n\n"
                "#### (2) 整数 $x$ に対する絶対値の解除\n"
                "不等式の左辺は $2\\left|x - \\frac{a}{b}\\right| + x = 2|x - (4 + \\sqrt{15})| + x$ である。\n"
                "$7 < 4 + \\sqrt{15} < 8$ であるため、整数 $x$ において：\n"
                "1. **$x \\le 7$ のとき**：\n"
                "   $x < 4 + \\sqrt{15}$ となるので、$x - \\frac{a}{b} < 0$ である。\n"
                "   したがって絶対値は負の符号をつけて外れる：\n"
                "   $$2\\left|x - \\frac{a}{b}\\right| + x = 2\\left(-(x - 4 - \\sqrt{15})\\right) + x = -2x + 8 + 2\\sqrt{15} + x = -x + 8 + 2\\sqrt{15}$$\n"
                "   これは選択肢 $\\textcircled{2}$ に一致する。\n"
                "   よって、$\\mathbf{E = 7, F = 2}$。\n"
                "2. **$x \\ge 8$ のとき**：\n"
                "   $x > 4 + \\sqrt{15}$ となるので、$x - \\frac{a}{b} > 0$ である。\n"
                "   したがって絶対値はそのまま外れる：\n"
                "   $$2\\left|x - \\frac{a}{b}\\right| + x = 2(x - 4 - \\sqrt{15}) + x = 2x - 8 - 2\\sqrt{15} + x = 3x - 8 - 2\\sqrt{15}$$\n"
                "   これは選択肢 $\\textcircled{5}$ に一致する。\n"
                "   よって、$\\mathbf{G = 8, H = 5}$。\n\n"
                "#### (3) 不等式を満たす整数 $x$ の範囲の決定\n"
                "不等式 $2\\left|x - \\frac{a}{b}\\right| + x < 10$ を各区間で解く：\n"
                "1. **$x \\le 7$ の場合**：\n"
                "   $$-x + 8 + 2\\sqrt{15} < 10 \\iff -x < 2 - 2\\sqrt{15} \\iff x > 2\\sqrt{15} - 2$$\n"
                "   $\\sqrt{15} \\approx 3.873$ より、$2\\sqrt{15} - 2 \\approx 7.746 - 2 = 5.746$。\n"
                "   したがって $x \\ge 6$。$x \\le 7$ と合わせて、$x = 6, 7$ が解となる。\n"
                "2. **$x \\ge 8$ の場合**：\n"
                "   $$3x - 8 - 2\\sqrt{15} < 10 \\iff 3x < 18 + 2\\sqrt{15} \\iff x < 6 + \\frac{2}{3}\\sqrt{15}$$\n"
                "   $\\frac{2}{3}\\sqrt{15} \\approx \\frac{2 \\times 3.873}{3} \\approx 2.58$ より、$x < 8.58$。\n"
                "   $x \\ge 8$ と合わせて、$x = 8$ が解となる。\n\n"
                "以上より、不等式を満たす整数解は $x = 6, 7, 8$ である。\n"
                "したがって、満たす整数 $x$ は **6 以上 8 以下** の整数である。\n"
                "よって、$\\mathbf{I = 6, J = 8}$。"
            )
        },
        {
            "sectionId": "II_2",
            "sectionTitle": "第II問 問2：2つの放物線の交点条件・$y$座標がともに正となる係数の範囲",
            "points": [
                "2次方程式 $f(x) = g(x)$ の判別式による異なる2実数解条件",
                "交点の $y$ 座標が正となるための $x$ 座標の開区間条件（$-2 < x < 2$）",
                "解の配置問題（端点での関数値・対称軸・判別式の連立不等式）"
            ],
            "officialAnswers": {
                "KL": "24",
                "MN": "22",
                "OP": "54",
                "QR": "34",
                "ST": "44",
                "UV": "21"
            },
            "detailedSolution": (
                "### 【第II問 問2】詳細解答と解説\n\n"
                "与えられた関数は：\n"
                "$$f(x) = x^2 + 2ax + a^2 - a, \\quad g(x) = 4 - x^2$$\n\n"
                "#### (1) 方程式 $f(x) = g(x)$ が異なる2つの解をもつ条件\n"
                "$$x^2 + 2ax + a^2 - a = 4 - x^2 \\iff 2x^2 + 2ax + a^2 - a - 4 = 0$$\n"
                "この2次方程式の判別式を $D$ とすると、異なる 2 つの実数解をもつ条件は $D/4 > 0$ である：\n"
                "$$\\frac{D}{4} = a^2 - 2(a^2 - a - 4) = a^2 - 2a^2 + 2a + 8 = -a^2 + 2a + 8 > 0$$\n"
                "両辺に $-1$ を掛けて因数分解する：\n"
                "$$a^2 - 2a - 8 < 0 \\iff (a - 4)(a + 2) < 0 \\iff -2 < a < 4 \\quad \\cdots \\textcircled{1}$$\n"
                "問題文の形式 $-K < a < L$ より：\n"
                "$$\\mathbf{K = 2, L = 4} \\implies \\mathbf{KL = 24}$$\n\n"
                "#### (2) 2つの交点の $y$ 座標がどちらも正となる条件\n"
                "交点の $y$ 座標は $y = g(x) = 4 - x^2$ である。\n"
                "$y > 0 \\iff 4 - x^2 > 0 \\iff -2 < x < 2$ である。\n"
                "したがって、交点の $x$ 座標、すなわち $h(x) = f(x) - g(x) = 2x^2 + 2ax + a^2 - a - 4 = 0$ の 2 つの解がともに開区間 $(-2, 2)$ の間（$-2$ と $2$ の間）にあればよい。\n"
                "よって、$-M$ と $N$ の間より $\\mathbf{M = 2, N = 2} \\implies \\mathbf{MN = 22}$。\n\n"
                "2次関数 $h(x)$ は下に凸（2次の係数 $2 > 0$）であるから、2解が区間 $(-2, 2)$ に収まるための条件は以下の 3 つである：\n"
                "1. **端点 $x = -2$ での符号**：\n"
                "   $$h(-2) = 2(-2)^2 + 2a(-2) + a^2 - a - 4 = 8 - 4a + a^2 - a - 4 = a^2 - 5a + 4 > 0 \\quad \\cdots \\textcircled{2}$$\n"
                "   形式 $a^2 - \\text{O}a + \\text{P} > 0$ より：$\\mathbf{O = 5, P = 4} \\implies \\mathbf{OP = 54}$。\n"
                "   因数分解すると $(a - 1)(a - 4) > 0 \\iff a < 1 \\text{ または } a > 4$。\n"
                "2. **端点 $x = 2$ での符号**：\n"
                "   $$h(2) = 2(2)^2 + 2a(2) + a^2 - a - 4 = 8 + 4a + a^2 - a - 4 = a^2 + 3a + 4 > 0 \\quad \\cdots \\textcircled{3}$$\n"
                "   形式 $a^2 + \\text{Q}a + \\text{R} > 0$ より：$\\mathbf{Q = 3, R = 4} \\implies \\mathbf{QR = 34}$。\n"
                "   $a^2 + 3a + 4 = \\left(a + \\frac{3}{2}\\right)^2 + \\frac{7}{4} > 0$ であり、すべての実数 $a$ で常に成立する。\n"
                "3. **放物線の軸の位置**：\n"
                "   軸の方程式は $x = -\\frac{2a}{2 \\times 2} = -\\frac{a}{2}$ である。\n"
                "   軸が区間 $(-2, 2)$ 内にある条件：\n"
                "   $$-2 < -\\frac{a}{2} < 2 \\iff -4 < a < 4 \\quad \\cdots \\textcircled{4}$$\n"
                "   形式 $-S < a < T$ より：$\\mathbf{S = 4, T = 4} \\implies \\mathbf{ST = 44}$。\n\n"
                "#### (3) すべての条件の共通範囲\n"
                "$\\textcircled{1}, \\textcircled{2}, \\textcircled{3}, \\textcircled{4}$ の共通部分をとる：\n"
                "- $\\textcircled{1}$：$-2 < a < 4$\n"
                "- $\\textcircled{2}$：$a < 1$ または $a > 4$\n"
                "- $\\textcircled{3}$：すべての実数\n"
                "- $\\textcircled{4}$：$-4 < a < 4$\n"
                "これらを連立すると：\n"
                "$$-2 < a < 1$$\n"
                "形式 $-U < a < V$ と比較して：\n"
                "$$\\mathbf{U = 2, V = 1} \\implies \\mathbf{UV = 21}$$"
            )
        },
        {
            "sectionId": "III_1",
            "sectionTitle": "第III問（前半）：有理数の平方根近似と最大の平方数の決定",
            "points": [
                "有理数の通分不等式 $7m + 3n < 21\\sqrt{2}$",
                "両辺の 2乗による上限評価 $(7m+3n)^2 < 882$",
                "882 より小さい最大の平方数 $841 = 29^2$ の決定"
            ],
            "officialAnswers": {
                "AB": "73",
                "CD": "21",
                "EFG": "882",
                "HIJ": "841",
                "KL": "29"
            },
            "detailedSolution": (
                "### 【第III問（前半）】詳細解答と解説\n\n"
                "#### (1) 通分と 2乗による上限評価\n"
                "$m, n$ を正の整数とし、有理数 $r = \\frac{m}{3} + \\frac{n}{7}$ を考える。\n"
                "通分すると：\n"
                "$$r = \\frac{7m + 3n}{21}$$\n"
                "条件 $r < \\sqrt{2}$ に代入すると：\n"
                "$$\\frac{7m + 3n}{21} < \\sqrt{2} \\iff 7m + 3n < 21\\sqrt{2} \\quad \\cdots \\textcircled{1}$$\n"
                "問題文の形式 $\\text{A}m + \\text{B}n < \\text{CD}\\sqrt{2}$ と比較して：\n"
                "$$\\mathbf{A = 7, B = 3, CD = 21} \\implies \\mathbf{AB = 73, CD = 21}$$\n\n"
                "$\\textcircled{1}$ の両辺はともに正であるから、両辺を 2乗すると：\n"
                "$$(7m + 3n)^2 < (21\\sqrt{2})^2 = 441 \\times 2 = 882$$\n"
                "したがって、$\\mathbf{EFG = 882}$。\n\n"
                "#### (2) 最大の平方数の決定\n"
                "$7m + 3n$ は正の整数であるから、$(7m + 3n)^2$ は 882 より小さい平方数（自然数の 2乗）である。\n"
                "882 に近い平方数を探すと：\n"
                "$$30^2 = 900 > 882$$\n"
                "$$29^2 = (30 - 1)^2 = 900 - 60 + 1 = 841 < 882$$\n"
                "したがって、882 より小さい最大の平方数は **841** であり、これは **$29^2$** である。\n"
                "問題文の形式 $\\text{HIJ} = \\text{KL}^2$ と比較して：\n"
                "$$\\mathbf{HIJ = 841, KL = 29}$$"
            )
        },
        {
            "sectionId": "III_2",
            "sectionTitle": "第III問（後半）：一次不定方程式の整数解と $\\sqrt{2}$ の最良近似",
            "points": [
                "一次不定方程式 $7m + 3n = 29$ の立式",
                "倍数条件（合同式）による整数の絞り込み",
                "正の整数解 $(m, n) = (2, 5)$ の一意決定"
            ],
            "officialAnswers": {
                "MNOP": "2973",
                "Q": "3",
                "R": "2",
                "S": "5"
            },
            "detailedSolution": (
                "### 【第III問（後半）】詳細解答と解説\n\n"
                "#### (1) 方程式の変形と倍数条件\n"
                "$7m + 3n$ を $21\\sqrt{2}$ に最も近づけるため、$(7m + 3n)^2$ が最大値 841 をとる場合、すなわち\n"
                "$$7m + 3n = 29$$\n"
                "を考える。\n"
                "この式を $n$ について解くと：\n"
                "$$3n = 29 - 7m \\implies n = \\frac{29 - 7m}{3}$$\n"
                "問題文の形式 $n = \\frac{\\text{MN} - \\text{O}m}{\\text{P}}$ と比較して：\n"
                "$$\\mathbf{MN = 29, O = 7, P = 3} \\implies \\mathbf{MNOP = 2973}$$\n\n"
                "$n$ は正の整数であるから、分子 $29 - 7m$ は分母 3 の倍数でなければならない。\n"
                "したがって、$\\mathbf{Q = 3}$。\n\n"
                "#### (2) 正の整数解 $m, n$ の決定\n"
                "$29 - 7m \\equiv 0 \\pmod 3$ を解く：\n"
                "$$29 \\equiv 2 \\pmod 3, \\quad 7 \\equiv 1 \\pmod 3$$\n"
                "$$2 - m \\equiv 0 \\pmod 3 \\implies m \\equiv 2 \\pmod 3$$\n"
                "$m$ は正の整数であるから、$m = 2, 5, 8, \\dots$ が候補となる。\n"
                "- $m = 2$ のとき：\n"
                "  $$n = \\frac{29 - 7(2)}{3} = \\frac{29 - 14}{3} = \\frac{15}{3} = 5$$\n"
                "  これは正の整数であり適する。\n"
                "- $m \\ge 5$ のとき：\n"
                "  $29 - 7(5) = 29 - 35 = -6 < 0$ となり、$n$ が負になってしまうため不適。\n\n"
                "したがって、求める正の整数解は一意に定まり：\n"
                "$$m = 2, \\quad n = 5$$\n"
                "よって、$\\mathbf{R = 2, S = 5}$。\n"
                "（このとき $r = \\frac{2}{3} + \\frac{5}{7} = \\frac{29}{21} \\approx 1.38095$ であり、$\\sqrt{2} \\approx 1.41421$ に極めて近い。）"
            )
        },
        {
            "sectionId": "IV_1",
            "sectionTitle": "第IV問（前半）：円に内接する四角形・正弦余弦定理と三角形 ABD の面積",
            "points": [
                "外接円の半径 $R = 1$ と正弦定理による弦長 $BD$ の決定",
                "余弦定理による辺長 $AB, AD$ の決定",
                "三角形の面積公式 $S = \\frac{1}{2} a b \\sin\\theta$"
            ],
            "officialAnswers": {
                "A": "3",
                "BCD": "217",
                "EFGH": "3314"
            },
            "detailedSolution": (
                "### 【第IV問（前半）】詳細解答と解説\n\n"
                "半径 $R = 1$ の円に内接する四角形 ABCD において、$AB : AD = 1 : 2$、$\\angle BAD = 120^\\circ$ である。\n\n"
                "#### (1) 対角線 $BD$ の長さ（正弦定理）\n"
                "$\\triangle ABD$ の外接円は四角形 ABCD の外接円そのものであり、その半径は $R = 1$ である。\n"
                "正弦定理より：\n"
                "$$\\frac{BD}{\\sin \\angle BAD} = 2R \\implies \\frac{BD}{\\sin 120^\\circ} = 2 \\times 1 = 2$$\n"
                "$$BD = 2 \\sin 120^\\circ = 2 \\times \\frac{\\sqrt{3}}{2} = \\sqrt{3}$$\n"
                "形式 $BD = \\sqrt{\\text{A}}$ より、$\\mathbf{A = 3}$。\n\n"
                "#### (2) 辺 $AB$ の長さ（余弦定理）\n"
                "$AB : AD = 1 : 2$ より、$AB = x, AD = 2x$ ($x > 0$) とおく。\n"
                "$\\triangle ABD$ において余弦定理を適用すると：\n"
                "$$BD^2 = AB^2 + AD^2 - 2 AB \\cdot AD \\cos \\angle BAD$$\n"
                "$$(\\sqrt{3})^2 = x^2 + (2x)^2 - 2(x)(2x) \\cos 120^\\circ$$\n"
                "$$3 = x^2 + 4x^2 - 4x^2 \\left(-\\frac{1}{2}\\right) = 5x^2 + 2x^2 = 7x^2$$\n"
                "$$x^2 = \\frac{3}{7} \\implies x = \\frac{\\sqrt{3}}{\\sqrt{7}} = \\frac{\\sqrt{21}}{7}$$\n"
                "したがって：\n"
                "$$AB = \\frac{\\sqrt{21}}{7}$$\n"
                "形式 $AB = \\frac{\\sqrt{\\text{BC}}}{\\text{D}}$ より：\n"
                "$$\\mathbf{BC = 21, D = 7} \\implies \\mathbf{BCD = 217}$$\n\n"
                "#### (3) 三角形 ABD の面積 $\\triangle ABD$\n"
                "$$\\triangle ABD = \\frac{1}{2} AB \\cdot AD \\sin \\angle BAD = \\frac{1}{2} \\cdot x \\cdot (2x) \\sin 120^\\circ = x^2 \\cdot \\frac{\\sqrt{3}}{2}$$\n"
                "$x^2 = \\frac{3}{7}$ を代入すると：\n"
                "$$\\triangle ABD = \\frac{3}{7} \\times \\frac{\\sqrt{3}}{2} = \\frac{3\\sqrt{3}}{14} \\quad \\cdots \\textcircled{1}$$\n"
                "形式 $\\frac{\\text{E}\\sqrt{\\text{F}}}{\\text{GH}}$ より：\n"
                "$$\\mathbf{E = 3, F = 3, GH = 14} \\implies \\mathbf{EFGH = 3314}$$"
            )
        },
        {
            "sectionId": "IV_2",
            "sectionTitle": "第IV問（後半）：対角線の交点比・三角形 BCD の面積と四角形全体の面積",
            "points": [
                "対角線の交点分割比と三角形の面積比の関係（高さ共通）",
                "円に内接する四角形の対角の和（$120^\\circ + 60^\\circ = 180^\\circ$）",
                "余弦定理による辺 $BC, CD$ の決定と全体の面積合算"
            ],
            "officialAnswers": {
                "IJ": "34",
                "KL": "32",
                "MNOP": "3217",
                "QRST": "9314",
                "UVW": "637"
            },
            "detailedSolution": (
                "### 【第IV問（後半）】詳細解答と解説\n\n"
                "対角線 BD と AC の交点を E とし、$BE : ED = 3 : 4$ とする。\n\n"
                "#### (1) 三角形の面積比と辺長比 $BC : CD$\n"
                "線分 AC を共通の底辺とみなすと、$\\triangle ABC$ と $\\triangle ACD$ の高さの比は点 B, D から AC への距離の比、すなわち $BE : ED = 3 : 4$ に等しい：\n"
                "$$\\triangle ABC : \\triangle ACD = BE : ED = 3 : 4$$\n"
                "したがって、$\\mathbf{I = 3, J = 4} \\implies \\mathbf{IJ = 34}$。\n\n"
                "また、三角形の面積公式を用いると：\n"
                "$$\\triangle ABC = \\frac{1}{2} AB \\cdot BC \\sin \\angle B, \\quad \\triangle ACD = \\frac{1}{2} AD \\cdot CD \\sin \\angle D$$\n"
                "四角形 ABCD は円に内接するため、対角の和は $180^\\circ$（$\\angle B + \\angle D = 180^\\circ$）である。\n"
                "したがって、$\\sin \\angle B = \\sin(180^\\circ - \\angle D) = \\sin \\angle D$ である。\n"
                "これより、面積比は：\n"
                "$$\\frac{\\triangle ABC}{\\triangle ACD} = \\frac{AB \\cdot BC}{AD \\cdot CD} = \\frac{x \\cdot BC}{2x \\cdot CD} = \\frac{BC}{2 CD} = \\frac{3}{4}$$\n"
                "両辺に 2 を掛けると：\n"
                "$$\\frac{BC}{CD} = \\frac{6}{4} = \\frac{3}{2} \\implies BC : CD = 3 : 2$$\n"
                "したがって、$\\mathbf{K = 3, L = 2} \\implies \\mathbf{KL = 32}$。\n\n"
                "#### (2) 辺 $BC$ の長さと $\\triangle BCD$ の面積\n"
                "$BC = 3y, CD = 2y$ ($y > 0$) とおく。\n"
                "円に内接する四角形の性質より、対角の和は $180^\\circ$ であるから：\n"
                "$$\\angle BCD = 180^\\circ - \\angle BAD = 180^\\circ - 120^\\circ = 60^\\circ$$\n"
                "$\\triangle BCD$ において余弦定理を適用する：\n"
                "$$BD^2 = BC^2 + CD^2 - 2 BC \\cdot CD \\cos \\angle BCD$$\n"
                "$$3 = (3y)^2 + (2y)^2 - 2(3y)(2y) \\cos 60^\\circ = 9y^2 + 4y^2 - 12y^2 \\left(\\frac{1}{2}\\right) = 13y^2 - 6y^2 = 7y^2$$\n"
                "$$y^2 = \\frac{3}{7} \\implies y = \\frac{\\sqrt{21}}{7}$$\n"
                "したがって、$BC = 3y = \\frac{3\\sqrt{21}}{7}$。\n"
                "形式 $\\frac{\\text{M}\\sqrt{\\text{NO}}}{\\text{P}}$ より：\n"
                "$$\\mathbf{M = 3, NO = 21, P = 7} \\implies \\mathbf{MNOP = 3217}$$\n\n"
                "次に、$\\triangle BCD$ の面積を求める：\n"
                "$$\\triangle BCD = \\frac{1}{2} BC \\cdot CD \\sin 60^\\circ = \\frac{1}{2} (3y)(2y) \\frac{\\sqrt{3}}{2} = \\frac{3\\sqrt{3}}{2} y^2$$\n"
                "$y^2 = \\frac{3}{7}$ を代入すると：\n"
                "$$\\triangle BCD = \\frac{3\\sqrt{3}}{2} \\times \\frac{3}{7} = \\frac{9\\sqrt{3}}{14} \\quad \\cdots \\textcircled{2}$$\n"
                "形式 $\\frac{\\text{Q}\\sqrt{\\text{R}}}{\\text{ST}}$ より：\n"
                "$$\\mathbf{Q = 9, R = 3, ST = 14} \\implies \\mathbf{QRST = 9314}$$\n\n"
                "#### (3) 四角形 ABCD の面積\n"
                "$\\textcircled{1}$ と $\\textcircled{2}$ より、四角形全体の面積は：\n"
                "$$\\text{Area}(ABCD) = \\triangle ABD + \\triangle BCD = \\frac{3\\sqrt{3}}{14} + \\frac{9\\sqrt{3}}{14} = \\frac{12\\sqrt{3}}{14} = \\frac{6\\sqrt{3}}{7}$$\n"
                "形式 $\\frac{\\text{U}\\sqrt{\\text{V}}}{\\text{W}}$ より：\n"
                "$$\\mathbf{U = 6, V = 3, W = 7} \\implies \\mathbf{UVW = 637}$$"
            )
        }
    ]
}

# Write Markdown
md_content = r"""# 2019年度 第1回（2019-1）EJU 日本留学試験 数学 コース1 全問詳細解説

- **試験科目**：数学（コース1 / Mathematics Course 1）
- **対象試験**：2019年度第1回（平成31年6月実施）
- **形式コード**：`MATHEMATICS_COURSE_1_JA`
- **問題構成**：第I問（問1, 問2）、第II問（問1, 問2）、第III問、第IV問
- **解答形式**：マーク式（空欄補充・数値および符号）

---

## 数学 コース1 公式正解一覧表

| 大問 | 設問 | 解答欄 | 公式正解 | 考査分野・要点 |
| :--- | :--- | :--- | :--- | :--- |
| **第I問** | 問1 | A, B, C | **9, 7, 7** ($<, >, >$) | 2次関数のグラフと係数の符号判定 |
| | | D, E, F | **8, 9, 9** ($=, <, <$) | $x = 1, -1, 2$ における関数値の符号 |
| | | G | **7** ($>$) | 判別式 $b^2 - 4ac > 0$ |
| | | H, I | **6, 4** ($a = -4, I = 4$) | $a^2 - 8b - 8c$ の最小化と関数の決定 |
| | | J, K | **0, 4** ($0 < b < 4$) | 変数 $b$ の取り得る値の範囲 |
| | 問2 | L, M | **2, 1** | 不正サイコロの確率（$P(6)=2p$、全事象 1） |
| | | NO | **17** ($p = 1/7$) | 確率 $p$ の決定 |
| | | PQRS | **2549** ($25/49$) | 2回試行における事象 $A$ の確率 |
| | | TUVW | **2449** ($24/49$) | 2回試行における事象 $B$ の確率 |
| | | X | **4** | $P(A)$ と $P(B)$ の差の評価（$1/36$ 未満） |
| | | Y | **1** | 3回試行における事象 $C, D$ の倍率評価（2倍未満） |
| **第II問** | 問1 | ABC | **415** ($4 + \sqrt{15}$) | 分母の有理化 |
| | | D | **7** | $\frac{a}{b}$ より小さい最大の整数 |
| | | E, F | **7, 2** | $x \le 7$ における絶対値の解除 |
| | | G, H | **8, 5** | $x \ge 8$ における絶対値の解除 |
| | | I, J | **6, 8** ($6 \le x \le 8$) | 不等式を満たす整数解の範囲 |
| | 問2 | KL | **24** ($-2 < a < 4$) | 放物線の異なる2交点条件（判別式） |
| | | MN | **22** ($-2 < x < 2$) | $y$ 座標が正となる交点 $x$ 座標の範囲 |
| | | OP | **54** ($a^2 - 5a + 4 > 0$) | 端点 $h(-2) > 0$ の条件 |
| | | QR | **34** ($a^2 + 3a + 4 > 0$) | 端点 $h(2) > 0$ の条件 |
| | | ST | **44** ($-4 < a < 4$) | 放物線の軸の位置の条件 |
| | | UV | **21** ($-2 < a < 1$) | すべての条件を満たす $a$ の範囲 |
| **第III問** | 前半 | AB, CD | **73, 21** ($7m+3n < 21\sqrt{2}$) | 通分による不等式 |
| | | EFG | **882** | 2乗による上限値 $(21\sqrt{2})^2$ |
| | | HIJ, KL | **841, 29** ($841 = 29^2$) | 882 より小さい最大の平方数 |
| | 後半 | MNOP | **2973** ($n = \frac{29-7m}{3}$) | 不定方程式の変形 |
| | | Q | **3** | 倍数条件 |
| | | R, S | **2, 5** ($m = 2, n = 5$) | 正の整数解の決定 |
| **第IV問** | 前半 | A | **3** ($BD = \sqrt{3}$) | 正弦定理による対角線の長さ |
| | | BCD | **217** ($AB = \frac{\sqrt{21}}{7}$) | 余弦定理による辺長決定 |
| | | EFGH | **3314** ($\frac{3\sqrt{3}}{14}$) | $\triangle ABD$ の面積 |
| | 後半 | IJ | **34** ($3 : 4$) | 三角形の面積比（対角線分割比） |
| | | KL | **32** ($3 : 2$) | 辺長比 $BC : CD$ の決定 |
| | | MNOP | **3217** ($BC = \frac{3\sqrt{21}}{7}$) | 辺 $BC$ の長さ |
| | | QRST | **9314** ($\frac{9\sqrt{3}}{14}$) | $\triangle BCD$ の面積 |
| | | UVW | **637** ($\frac{6\sqrt{3}}{7}$) | 四角形 ABCD の面積 |

---

## 逐問詳細推導与解説

"""

for s in explanations["sections"]:
    md_content += f"\n---\n\n## {s['sectionTitle']}\n\n"
    md_content += f"**【考査考点】**：{', '.join(s['points'])}\n\n"
    md_content += s["detailedSolution"] + "\n"

out_md = Path("docs/explanations/2019-1-math-c1-solutions.md")
out_md.parent.mkdir(parents=True, exist_ok=True)
out_md.write_text(md_content, encoding="utf-8")

# Save JSON
out_json = Path("work/2019-1-math-c1/explanations.json")
out_json.parent.mkdir(parents=True, exist_ok=True)
out_json.write_text(json.dumps(explanations, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"Generated {out_md} and {out_json} successfully.")
