#!/usr/bin/env python3
"""Generate comprehensive explanations for 2020-2 EJU Mathematics Course 2."""

import json
from pathlib import Path

math_c2_sections = [
    {
        "localKey": "math-q-I_1",
        "sectionId": "I_1",
        "sectionTitle": "第I問 [1]：2次関数の平行移動と不等式・線分の長さ",
        "points": ["放物線の平行移動（2次係数の不変性）", "2次不等式の解法", "解と係数の関係を用いた線分の長さの公式"],
        "officialAnswers": {
            "ABCD": "1442",
            "EFG": "248",
            "HI": "68",
            "JKLM": "2940",
            "NO": "59"
        },
        "detailedSolution": (
            "**【題目大意】**\n"
            "$a$ は正の定数とする。2次関数 $y = \\frac{1}{4}x^2$ のグラフを平行移動し、$x$ 軸との交点が $(-2a, 0), (4a, 0)$ である放物線を $y = f(x)$ とする。\n"
            "(1) $f(x)$ の因数分解形を求めよ。\n"
            "(2) 不等式 $f(x) \\le 10a^2$ の解を求めよ。\n"
            "(3) 直線 $y = 10a$ が放物線 $y = f(x)$ によって切り取られる線分の長さが 10 のとき、$a$ の値を求めよ。\n\n"
            "**【公式正解】**\n"
            "- $\\text{ABCD} = \\mathbf{1442}$\n"
            "- $\\text{EFG} = \\mathbf{248}, \\quad \\text{HI} = \\mathbf{68}$\n"
            "- $\\text{JKLM} = \\mathbf{2940}, \\quad \\text{NO} = \\mathbf{59}$\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "**(1) $f(x)$ の式の決定**\n"
            "平行移動した放物線の $x^2$ の係数は元の関数と同じ $\\frac{1}{4}$ である。\n"
            "$x$ 軸との交点が $x = -2a, 4a$ であるから、因数定理より：\n"
            "$$f(x) = \\frac{1}{4} (x - 4a)(x + 2a)$$\n"
            "よって、$A = 1, B = 4, C = 4, D = 2$ となり、$\\text{ABCD} = \\mathbf{1442}$ である。\n\n"
            "**(2) $y \\le 10a^2$ の解**\n"
            "不等式を展開して整理する：\n"
            "$$\\frac{1}{4}(x^2 - 2ax - 8a^2) \\le 10a^2$$\n"
            "両辺に 4 を掛けると：\n"
            "$$x^2 - 2ax - 8a^2 \\le 40a^2 \\implies x^2 - 2ax - 48a^2 \\le 0$$\n"
            "したがって、$E = 2, FG = 48$（$\\text{EFG} = \\mathbf{248}$）である。\n"
            "左辺を因数分解すると：\n"
            "$$(x - 8a)(x + 6a) \\le 0$$\n"
            "$a > 0$ であるから、解は：\n"
            "$$-6a \\le x \\le 8a$$\n"
            "よって、$H = 6, I = 8$（$\\text{HI} = \\mathbf{68}$）である。\n\n"
            "**(3) 切り取られる線分の長さと $a$ の決定**\n"
            "放物線 $y = f(x)$ と直線 $y = 10a$ の交点の $x$ 座標は方程式：\n"
            "$$\\frac{1}{4}(x^2 - 2ax - 8a^2) = 10a \\iff x^2 - 2ax - (8a^2 + 40a) = 0$$\n"
            "の2実数解 $\\alpha, \\beta$（$\\alpha < \\beta$）である。\n"
            "解と係数の関係より、$\\alpha + \\beta = 2a, \\quad \\alpha \\beta = -(8a^2 + 40a)$ である。\n"
            "切り取られる線分の長さ $L$ は：\n"
            "$$L = \\beta - \\alpha = \\sqrt{(\\alpha + \\beta)^2 - 4\\alpha\\beta} = \\sqrt{(2a)^2 + 4(8a^2 + 40a)} = \\sqrt{36a^2 + 160a} = 2\\sqrt{9a^2 + 40a}$$\n"
            "これが 10 に等しいので：\n"
            "$$2\\sqrt{9a^2 + 40a} = 10 \\implies \\sqrt{9a^2 + 40a} = 5$$\n"
            "したがって、$J = 2, K = 9, LM = 40$（$\\text{JKLM} = \\mathbf{2940}$）である。\n"
            "両辺を2乗して整理すると：\n"
            "$$9a^2 + 40a = 25 \\iff 9a^2 + 40a - 25 = 0$$\n"
            "因数分解すると $(9a - 5)(a + 5) = 0$ となり、$a > 0$ より：\n"
            "$$a = \\frac{5}{9}$$\n"
            "よって、$N = 5, O = 9$（$\\text{NO} = \\mathbf{59}$）である。"
        )
    },
    {
        "localKey": "math-q-I_2",
        "sectionId": "I_2",
        "sectionTitle": "第I問 [2]：階段ののぼり方（1段・2段のぼり）と場合の数",
        "points": ["反復試行・同じものを含む順列", "フィボナッチ数列による漸化式の応用", "隣り合わない（連続しない）条件における空隙挿入法"],
        "officialAnswers": {
            "P": "4",
            "QR": "35",
            "ST": "87",
            "U": "6",
            "VW": "21",
            "XY": "40"
        },
        "detailedSolution": (
            "**【題目大意】**\n"
            "10段の階段を、1段のぼりまたは2段のぼりで上がる（どちらも必ず1回以上使用）。\n"
            "(1) 2段のぼりが連続してもよい場合：\n"
            "    (i) 2段のぼりが3回のときの1段のぼりの回数と総数\n"
            "    (ii) 連続してもよい場合の全通り数\n"
            "(2) 2段のぼりが連続しない場合：\n"
            "    (i) 2段のぼりが2回のときの1段のぼりの回数と総数\n"
            "    (ii) 連続しない場合の全通り数\n\n"
            "**【公式正解】**\n"
            "- $P = \\mathbf{4}, \\quad \\text{QR} = \\mathbf{35}$\n"
            "- $\\text{ST} = \\mathbf{87}$\n"
            "- $U = \\mathbf{6}, \\quad \\text{VW} = \\mathbf{21}$\n"
            "- $\\text{XY} = \\mathbf{40}$\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "**(1) 2段のぼりが連続してもよい場合**\n"
            "(i) 2段のぼりが3回のとき：\n"
            "のぼる段数は $3 \\times 2 = 6$ 段であるから、残る段数は $10 - 6 = 4$ 段。\n"
            "したがって、1段のぼりの回数は $P = \\mathbf{4}$ 回である。\n"
            "のぼり方は、2段のぼり3回と1段のぼり4回の合計7回の並べ替え数であるから：\n"
            "$$\\binom{7}{3} = \\frac{7 \\times 6 \\times 5}{3 \\times 2 \\times 1} = 35\\text{ 通り}$$\n"
            "よって、$\\text{QR} = \\mathbf{35}$ である。\n\n"
            "(ii) 全体ののぼり方の総数：\n"
            "$n$ 段の階段を1段または2段でのぼる総数を $a_n$ とすると、第1歩が1段か2段かで漸化式 $a_n = a_{n-1} + a_{n-2}$ が成り立つ。\n"
            "$a_1 = 1, a_2 = 2, a_3 = 3, a_4 = 5, a_5 = 8, a_6 = 13, a_7 = 21, a_8 = 34, a_9 = 55, a_{10} = 89$。\n"
            "問題文の条件「1段のぼりも2段のぼりも必ず1回はある」より：\n"
            "- すべて1段のぼり（10回）の1通りを除く\n"
            "- すべて2段のぼり（5回）の1通りを除く\n"
            "したがって、求める総数は：\n"
            "$$89 - 1 - 1 = 87\\text{ 通り}$$\n"
            "よって、$\\text{ST} = \\mathbf{87}$ である。\n\n"
            "**(2) 2段のぼりが連続しない場合**\n"
            "(i) 2段のぼりが2回のとき：\n"
            "2段のぼりによる段数は $2 \\times 2 = 4$ 段、1段のぼりの回数は $10 - 4 = 6$ 回（$U = \\mathbf{6}$）。\n"
            "2段のぼりが連続しないためには、6回の1段のぼりの両端および隙間（合計7箇所）から2箇所を選んで2段のぼりを配置すればよい：\n"
            "$$\\binom{7}{2} = \\frac{7 \\times 6}{2 \\times 1} = 21\\text{ 通り}$$\n"
            "よって、$\\text{VW} = \\mathbf{21}$ である。\n\n"
            "(ii) 連続しない場合の全通り数：\n"
            "2段のぼりの回数 $k$（$1 \\le k \\le 5$）で場合分けする：\n"
            "- $k = 1$ のとき：1段のぼり 8 回。隙間 9 箇所から 1 箇所選ぶ $\\implies \\binom{9}{1} = 9$ 通り\n"
            "- $k = 2$ のとき：1段のぼり 6 回。隙間 7 箇所から 2 箇所選ぶ $\\implies \\binom{7}{2} = 21$ 通り\n"
            "- $k = 3$ のとき：1段のぼり 4 回。隙間 5 箇所から 3 箇所選ぶ $\\implies \\binom{5}{3} = 10$ 通り\n"
            "- $k \\ge 4$ のとき：2段のぼりが4回なら1段のぼりは2回で隙間3箇所しかなく不可能。\n"
            "合計すると：\n"
            "$$9 + 21 + 10 = 40\\text{ 通り}$$\n"
            "よって、$\\text{XY} = \\mathbf{40}$ である。"
        )
    },
    {
        "localKey": "math-q-II_1",
        "sectionId": "II_1",
        "sectionTitle": "第II問 [1]：等差数列の和・積の数列とその和の最小値",
        "points": ["数列の和 $S_n$ からの一般項 $a_n$ の導出", "積の数列 $b_n = a_n a_{n+5}$ の展開とシグマ和 $T_n$", "項の符号変化に基づく和の増減と最小値の判定"],
        "officialAnswers": {
            "A": "1",
            "B": "4",
            "C": "9",
            "DEF": "310",
            "GH": "58",
            "I": "1",
            "J": "8",
            "K": "9",
            "L": "6"
        },
        "detailedSolution": (
            "**【題目大意】**\n"
            "初項から第 $n$ 項までの和が $S_n = \\frac{n^2 - 17n}{4}$ で表される数列 $\{a_n\}$ に対応して、数列 $\{b_n\}$ を $b_n = a_n \\cdot a_{n+5} \\quad (n = 1, 2, 3, \\dots)$ と定める。\n"
            "(1) $a_n = \\text{A}, b_n = \\text{B}, T_n = \\sum_{k=1}^n b_k = \\text{C}$ を選択肢 $\\textcircled{0} \\sim \\textcircled{9}$ から選べ。\n"
            "(2) $b_n > 0$ となる $n$ の範囲（$n \\le D$ または $EF \\le n$）、および $b_n < 0$ となる $n$ の範囲（$G \\le n \\le H$）を求めよ。\n"
            "    これより $T_n$ が最小となる3つの番号 $n = I, J, K$（$I < J < K$）とその最小値 $L$ を求めよ。\n\n"
            "**【公式正解】**\n"
            "- $A = \\mathbf{1}, \\quad B = \\mathbf{4}, \\quad C = \\mathbf{9}$\n"
            "- $\\text{DEF} = \\mathbf{310} \\implies D = \\mathbf{3}, \\quad \\text{EF} = \\mathbf{10}$\n"
            "- $\\text{GH} = \\mathbf{58} \\implies G = \\mathbf{5}, \\quad H = \\mathbf{8}$\n"
            "- $I = \\mathbf{1}, \\quad J = \\mathbf{8}, \\quad K = \\mathbf{9}, \\quad L = \\mathbf{6}$\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "**(1) $a_n, b_n, T_n$ の導出**\n"
            "一般項 $a_n$ は $S_n$ の差分より：\n"
            "$$a_n = S_n - S_{n-1} = \\frac{n^2 - 17n - ((n-1)^2 - 17(n-1))}{4}$$\n"
            "$$= \\frac{n^2 - 17n - (n^2 - 2n + 1 - 17n + 17)}{4} = \\frac{2n - 18}{4} = \\frac{n - 9}{2}$$\n"
            "これは $n = 1$ のとき $a_1 = \\frac{1-9}{2} = -4 = S_1$ となり成り立ちます。\n"
            "選択肢 $\\textcircled{1} \\implies A = \\mathbf{1}$ である。\n\n"
            "次に、$a_{n+5} = \\frac{(n+5) - 9}{2} = \\frac{n - 4}{2}$ であるから：\n"
            "$$b_n = a_n \\cdot a_{n+5} = \\frac{n - 9}{2} \\cdot \\frac{n - 4}{2} = \\frac{n^2 - 13n + 36}{4}$$\n"
            "選択肢 $\\textcircled{4} \\implies B = \\mathbf{4}$ である。\n\n"
            "数列 $\{b_n\}$ の初項から第 $n$ 項までの和 $T_n$ を計算する：\n"
            "$$T_n = \\sum_{k=1}^n b_k = \\frac{1}{4} \\sum_{k=1}^n (k^2 - 13k + 36)$$\n"
            "自然数の和の公式を代入する：\n"
            "$$\\sum_{k=1}^n k^2 = \\frac{n(n+1)(2n+1)}{6}, \\qquad \\sum_{k=1}^n k = \\frac{n(n+1)}{2}, \\qquad \\sum_{k=1}^n 36 = 36n$$\n"
            "共通因数 $\\frac{n}{6}$ で括ると：\n"
            "$$T_n = \\frac{1}{4} \\cdot \\frac{n}{6} \\left[ (n+1)(2n+1) - 39(n+1) + 216 \\right]$$\n"
            "かっこ内を整理する：\n"
            "$$(2n^2 + 3n + 1) - (39n + 39) + 216 = 2n^2 - 36n + 178 = 2(n^2 - 18n + 89)$$\n"
            "したがって：\n"
            "$$T_n = \\frac{n}{24} \\cdot 2(n^2 - 18n + 89) = \\frac{n(n^2 - 18n + 89)}{12}$$\n"
            "選択肢 $\\textcircled{9} \\implies C = \\mathbf{9}$ である。\n\n"
            "**(2) $T_n$ の最小値の決定**\n"
            "$b_n = \\frac{(n-4)(n-9)}{4}$ の符号を調べる：\n"
            "- $b_n > 0 \\iff (n-4)(n-9) > 0 \\iff n < 4$ または $n > 9$\n"
            "  $n$ は自然数であるから、$n \\le 3$ または $n \\ge 10$。\n"
            "  したがって、$D = 3, \\text{EF} = 10$ である。\n"
            "- $b_n < 0 \\iff 4 < n < 9 \\iff 5 \\le n \\le 8$\n"
            "  したがって、$G = 5, H = 8$ である。\n"
            "- $n = 4$ および $n = 9$ のとき $b_4 = 0, b_9 = 0$ である。\n\n"
            "和 $T_n$ と項 $b_n$ の関係 $T_n - T_{n-1} = b_n$ より：\n"
            "- $n = 1, 2, 3$ では $b_n > 0$ であるから、$T_n$ は増加する。\n"
            "  $T_1 = b_1 = \\frac{(-3)(-8)}{4} = 6$\n"
            "  $T_2 = 6 + \\frac{7}{2} = 9.5, \\quad T_3 = 9.5 + \\frac{3}{2} = 11$\n"
            "- $n = 4$ では $b_4 = 0$ であるから、$T_4 = T_3 = 11$\n"
            "- $n = 5, 6, 7, 8$ では $b_n < 0$ であるから、$T_n$ は減少する：\n"
            "  $T_5 = 11 - 1 = 10, \\quad T_6 = 10 - 1.5 = 8.5$\n"
            "  $T_7 = 8.5 - 1.5 = 7, \\quad T_8 = 7 - 1 = 6$\n"
            "- $n = 9$ では $b_9 = 0$ であるから、$T_9 = T_8 = 6$\n"
            "- $n \\ge 10$ では $b_n > 0$ であるから、$T_n$ は再び単調増加する：\n"
            "  $T_{10} = 6 + 1.5 = 7.5, \\quad T_{11} = 7.5 + 3.5 = 11, \\dots$\n\n"
            "以上の推移を比較すると、$T_n$ の値は：\n"
            "$$T_1 = 6, \\quad T_8 = 6, \\quad T_9 = 6$$\n"
            "であり、他のすべての自然数 $n$ において $T_n > 6$ である。\n"
            "したがって、$T_n$ は $n = 1, 8, 9$ の3箇所で最小値 6 をとる。\n"
            "$I < J < K$ より、$I = \\mathbf{1}, J = \\mathbf{8}, K = \\mathbf{9}$ であり、最小値は $L = \\mathbf{6}$ である。"
        )
    },
    {
        "localKey": "math-q-II_2",
        "sectionId": "II_2",
        "sectionTitle": "第II問 [2]：複素数平面・極形式・多項式の因数分解",
        "points": ["複素数の極形式表現とド・モアブルの定理", "累乗根 $z^n = w$ の解と偏角の分配", "高次複素数方程式の根の対応と積の計算"],
        "officialAnswers": {
            "MN": "16",
            "OP": "33",
            "Q": "2",
            "R": "6",
            "STUV": "1357",
            "W": "4",
            "XY": "-4"
        },
        "detailedSolution": (
            "**【題目大意】**\n"
            "(1) 複素数 $8 + 8\\sqrt{3}i$ を極形式 $\\text{MN}(\\cos \\frac{\\pi}{O} + i\\sin \\frac{\\pi}{P})$ で表せ。\n"
            "(2) 方程式 $z^4 = 8 + 8\\sqrt{3}i$（$0 \\le \\arg z < 2\\pi$）の解を偏角順に $z_1, z_2, z_3, z_4$ とする。\n"
            "    $|z| = Q$、および $\\arg \\frac{z_1 z_2 z_3}{z_4} = \\frac{\\pi}{R}$ を求めよ。\n"
            "(3) 方程式 $w^8 - 16w^4 + 256 = 0$（$0 \\le \\arg w < 2\\pi$）の8根 $w_1 \\sim w_8$ のうち、$z_1 \\sim z_4$ と一致する添字 $\\text{STUV}$ を求めよ。\n"
            "    また、$w_1 w_8 = W, w_3 w_4 = \\text{XY}i$ を求めよ。\n\n"
            "**【公式正解】**\n"
            "- $\\text{MN} = \\mathbf{16}, \\quad O = \\mathbf{3}, \\quad P = \\mathbf{3}$\n"
            "- $Q = \\mathbf{2}, \\quad R = \\mathbf{6}$\n"
            "- $\\text{STUV} = \\mathbf{1357}$\n"
            "- $W = \\mathbf{4}, \\quad \\text{XY} = \\mathbf{-4}$\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "**(1) 極形式の計算**\n"
            "絶対値 $r$ は：\n"
            "$$r = \\sqrt{8^2 + (8\\sqrt{3})^2} = \\sqrt{64 + 192} = \\sqrt{256} = 16$$\n"
            "偏角 $\\theta$ は $\\cos \\theta = \\frac{8}{16} = \\frac{1}{2}, \\sin \\theta = \\frac{8\\sqrt{3}}{16} = \\frac{\\sqrt{3}}{2}$ より $\\theta = \\frac{\\pi}{3}$ である。\n"
            "したがって：\n"
            "$$8 + 8\\sqrt{3}i = 16\\left(\\cos\\frac{\\pi}{3} + i\\sin\\frac{\\pi}{3}\\right)$$\n"
            "よって、$\\text{MN} = \\mathbf{16}, O = \\mathbf{3}, P = \\mathbf{3}$ である。\n\n"
            "**(2) 4乗根の決定と偏角の合成**\n"
            "$z^4 = 16 e^{i\\pi/3}$ より、$|z|^4 = 16 \\implies |z| = \\sqrt[4]{16} = 2$（$Q = \\mathbf{2}$）。\n"
            "偏角の範囲 $0 \\le \\arg z < 2\\pi$ における4つの根の偏角は：\n"
            "$$\\arg z_k = \\frac{\\frac{\\pi}{3} + 2k\\pi}{4} = \\frac{\\pi}{12} + \\frac{k\\pi}{2} \\quad (k = 0, 1, 2, 3)$$\n"
            "偏角の小さい順に：\n"
            "$$\\arg z_1 = \\frac{\\pi}{12}, \\quad \\arg z_2 = \\frac{7\\pi}{12}, \\quad \\arg z_3 = \\frac{13\\pi}{12}, \\quad \\arg z_4 = \\frac{19\\pi}{12}$$\n"
            "商と積の偏角公式より：\n"
            "$$\\arg \\frac{z_1 z_2 z_3}{z_4} \\equiv \\arg z_1 + \\arg z_2 + \\arg z_3 - \\arg z_4 \\pmod{2\\pi}$$\n"
            "$$= \\frac{\\pi + 7\\pi + 13\\pi - 19\\pi}{12} = \\frac{2\\pi}{12} = \\frac{\\pi}{6}$$\n"
            "したがって、$R = \\mathbf{6}$ である。\n\n"
            "**(3) 8次方程式の根の対応と積**\n"
            "方程式 $(w^4)^2 - 16(w^4) + 256 = 0$ を $w^4$ の2次方程式として解く：\n"
            "$$w^4 = \\frac{16 \\pm \\sqrt{256 - 1024}}{2} = \\frac{16 \\pm \\sqrt{-768}}{2} = \\frac{16 \\pm 16\\sqrt{3}i}{2} = 8 \\pm 8\\sqrt{3}i$$\n"
            "- 第1の組：$w^4 = 8 + 8\\sqrt{3}i = 16 e^{i\\pi/3}$\n"
            "  偏角は $\\frac{\\pi}{12}, \\frac{7\\pi}{12}, \\frac{13\\pi}{12}, \\frac{19\\pi}{12}$（これは $z_1, z_2, z_3, z_4$ と完全に一致）。\n"
            "- 第2の組：$w^4 = 8 - 8\\sqrt{3}i = 16 e^{i 5\\pi/3}$\n"
            "  偏角は $\\frac{5\\pi/3 + 2k\\pi}{4} = \\frac{5\\pi}{12} + \\frac{k\\pi}{2}$ より $\\frac{5\\pi}{12}, \\frac{11\\pi}{12}, \\frac{17\\pi}{12}, \\frac{23\\pi}{12}$。\n\n"
            "全8個の解を偏角の昇順に並べると：\n"
            "1. $w_1 = z_1$（偏角 $\\pi/12$）\n"
            "2. $w_2$（偏角 $5\\pi/12$）\n"
            "3. $w_3 = z_2$（偏角 $7\\pi/12$）\n"
            "4. $w_4$（偏角 $11\\pi/12$）\n"
            "5. $w_5 = z_3$（偏角 $13\\pi/12$）\n"
            "6. $w_6$（偏角 $17\\pi/12$）\n"
            "7. $w_7 = z_4$（偏角 $19\\pi/12$）\n"
            "8. $w_8$（偏角 $23\\pi/12$）\n\n"
            "したがって、$w_1 = z_1, w_3 = z_2, w_5 = z_3, w_7 = z_4$ であり、$\\text{STUV} = \\mathbf{1357}$ である。\n\n"
            "最後に根の積を計算する（$|w_k| = 2$）：\n"
            "- $w_1 w_8$ の絶対値は $2 \\times 2 = 4$、偏角は $\\frac{\\pi}{12} + \\frac{23\\pi}{12} = \\frac{24\\pi}{12} = 2\\pi \\equiv 0$ であるから：\n"
            "  $$w_1 w_8 = 4(\\cos 0 + i\\sin 0) = 4 \\implies W = \\mathbf{4}$$\n"
            "- $w_3 w_4$ の絶対値は $2 \\times 2 = 4$、偏角は $\\frac{7\\pi}{12} + \\frac{11\\pi}{12} = \\frac{18\\pi}{12} = \\frac{3\\pi}{2}$ であるから：\n"
            "  $$w_3 w_4 = 4\\left(\\cos\\frac{3\\pi}{2} + i\\sin\\frac{3\\pi}{2}\\right) = 4(0 - i) = -4i$$\n"
            "  問題文の形式 $w_3 w_4 = \\text{XY} i$ より、$\\text{XY} = \\mathbf{-4}$ である。"
        )
    },
    {
        "localKey": "math-q-III_1",
        "sectionId": "III_1",
        "sectionTitle": "第III問 [1]：3次関数の接線方程式と交点座標",
        "points": ["3次関数の導関数と接線公式", "曲線外の点から引いた接線と接点の決定", "2直線の連立方程式と交点座標の計算"],
        "officialAnswers": {
            "ABC": "324",
            "DE": "-1",
            "F": "6",
            "GHI": "324",
            "JKL": "234",
            "M": "2",
            "NOP": "812",
            "QR": "24"
        },
        "detailedSolution": (
            "**【題目大意】**\n"
            "関数 $f(x) = x^3 - 4x + 4$ について考える。\n"
            "$y = f(x)$ のグラフ上の点 $A(-1, 7)$ における接線を $\ell$ とし、$y = f(x)$ のグラフに点 $B(0, -12)$ から引いた接線を $m$ とする。\n"
            "(1) $f'(x) = A x^B - C$ を求め、接線 $\ell$ の傾き $\\text{DE}$ と方程式 $y = \\text{DE}x + F$ を求めよ。\n"
            "(2) 接点 $(a, f(a))$ における接線 $m$ の方程式を $a$ で表し、$B(0, -12)$ を通る条件から $a = M$、接線 $m$ の方程式 $y = Nx - \\text{OP}$、および交点 $C(Q, R)$ を求めよ。\n\n"
            "**【公式正解】**\n"
            "- $\\text{ABC} = \\mathbf{324}, \\quad \\text{DE} = \\mathbf{-1}, \\quad F = \\mathbf{6}$\n"
            "- $\\text{GHI} = \\mathbf{324}, \\quad \\text{JKL} = \\mathbf{234}, \\quad M = \\mathbf{2}$\n"
            "- $\\text{NOP} = \\mathbf{812}, \\quad \\text{QR} = \\mathbf{24}$\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "**(1) 導関数と接線 $\\ell$ の方程式**\n"
            "$f(x) = x^3 - 4x + 4$ を微分すると：\n"
            "$$f'(x) = 3x^2 - 4$$\n"
            "したがって、$A = 3, B = 2, C = 4$（$\\text{ABC} = \\mathbf{324}$）である。\n\n"
            "点 $A(-1, 7)$ における接線の傾きは：\n"
            "$$f'(-1) = 3(-1)^2 - 4 = 3 - 4 = -1$$\n"
            "よって、接線 $\\ell$ の傾きは $\\text{DE} = \\mathbf{-1}$ である。\n"
            "接線 $\\ell$ の方程式は：\n"
            "$$y - 7 = -1(x - (-1)) \\iff y - 7 = -x - 1 \\iff y = -x + 6$$\n"
            "したがって、$F = \\mathbf{6}$ である。\n\n"
            "**(2) 外部の点からの接線 $m$ と交点 $C$**\n"
            "接点 $(a, a^3 - 4a + 4)$ における接線の方程式は：\n"
            "$$y - (a^3 - 4a + 4) = (3a^2 - 4)(x - a)$$\n"
            "展開して整理すると：\n"
            "$$y = (3a^2 - 4)x - 3a^3 + 4a + a^3 - 4a + 4$$\n"
            "$$y = (3a^2 - 4)x - 2a^3 + 4$$\n"
            "したがって、$G = 3, H = 2, I = 4$（$\\text{GHI} = \\mathbf{324}$）、$J = 2, K = 3, L = 4$（$\\text{JKL} = \\mathbf{234}$）である。\n\n"
            "この接線 $m$ が点 $B(0, -12)$ を通るから、$x = 0, y = -12$ を代入する：\n"
            "$$-12 = -2a^3 + 4 \\iff 2a^3 = 16 \\iff a^3 = 8$$\n"
            "$a$ は実数であるから $a = 2$ である（$M = \\mathbf{2}$）。\n\n"
            "$a = 2$ を接線方程式に代入すると：\n"
            "$$y = (3 \\cdot 2^2 - 4)x - 2 \\cdot 2^3 + 4 = (12 - 4)x - 16 + 4 = 8x - 12$$\n"
            "したがって、$N = 8, OP = 12$（$\\text{NOP} = \\mathbf{812}$）である。\n\n"
            "2直線 $\\ell: y = -x + 6$ と $m: y = 8x - 12$ の交点 $C$ の座標を求める：\n"
            "$$-x + 6 = 8x - 12 \\iff 9x = 18 \\iff x = 2$$\n"
            "$y = -2 + 6 = 4$。\n"
            "したがって、交点 $C$ の座標は $(2, 4)$ であり、$Q = 2, R = 4$（$\\text{QR} = \\mathbf{24}$）である。"
        )
    },
    {
        "localKey": "math-q-III_2",
        "sectionId": "III_2",
        "sectionTitle": "第III問 [2]：2直線のなす角となす角の正接",
        "points": ["直線と $x$ 軸正の向きのなす角の傾き表現（$\tan \theta = m$）", "正接の加法定理となす角公式 $\tan \theta = |\\frac{\\tan \\beta - \\tan \\alpha}{1 + \\tan \\alpha \\tan \\beta}|$"],
        "officialAnswers": {
            "ST": "-1",
            "U": "8",
            "VW": "97"
        },
        "detailedSolution": (
            "**【題目大意】**\n"
            "2直線 $\\ell, m$ と $x$ 軸の正の向きとのなす角をそれぞれ $\\alpha, \\beta$ とするとき、$\\tan \\alpha = \\text{ST}, \\tan \\beta = U$ を求め、2直線のなす角 $\\theta \\ (0 < \\theta < \\frac{\\pi}{2})$ に対する $\\tan \\theta = \\frac{V}{W}$ を求めよ。\n\n"
            "**【公式正解】**\n"
            "- $\\text{ST} = \\mathbf{-1}, \\quad U = \\mathbf{8}$\n"
            "- $\\text{VW} = \\mathbf{97}$\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "直線の傾きは $x$ 軸の正の向きとのなす角の正接（タンジェント）に等しい。\n"
            "接線 $\\ell$ の方程式は $y = -x + 6$ であるから、傾きは $-1$ である：\n"
            "$$\\tan \\alpha = -1 \\implies \\text{ST} = \\mathbf{-1}$$\n"
            "接線 $m$ の方程式は $y = 8x - 12$ であるから、傾きは 8 である：\n"
            "$$\\tan \\beta = 8 \\implies U = \\mathbf{8}$$\n\n"
            "2直線のなす鋭角 $\\theta \\ (0 < \\theta < \\frac{\\pi}{2})$ に対し、正接の加法定理より：\n"
            "$$\\tan \\theta = |\\tan(\\beta - \\alpha)| = \\left| \\frac{\\tan \\beta - \\tan \\alpha}{1 + \\tan \\alpha \\tan \\beta} \\right|$$\n"
            "値を代入すると：\n"
            "$$\\tan \\theta = \\left| \\frac{8 - (-1)}{1 + (-1) \\times 8} \\right| = \\left| \\frac{9}{1 - 8} \\right| = \\left| \\frac{9}{-7} \\right| = \\frac{9}{7}$$\n"
            "形式 $\\frac{V}{W}$ より、$V = 9, W = 7$。\n"
            "したがって、$\\text{VW} = \\mathbf{97}$ である。"
        )
    },
    {
        "localKey": "math-q-IV_1",
        "sectionId": "IV_1",
        "sectionTitle": "第IV問 [1]：三角関数の導関数・増減表と極値・正値性の証明",
        "points": ["三角関数の微分と加法定理・倍角公式による因数分解", "導関数の符号変化と関数の増減の特定", "極小値の正値性に基づく区間内正値性の証明"],
        "officialAnswers": {
            "ABCD": "2121",
            "E": "4",
            "FG": "23",
            "HI": "34",
            "J": "4",
            "K": "0",
            "LM": "23",
            "N": "1",
            "OP": "34",
            "Q": "0",
            "R": "1",
            "ST": "34"
        },
        "detailedSolution": (
            "**【題目大意】**\n"
            "区間 $0 \\le x \\le \\pi$ において、関数 $f(x) = \\sin x + \\frac{\\sin 2x}{2} + \\frac{\\sin 3x}{3}$ を考える。\n"
            "(1) $f'(x) = (A\\cos^2 x - B)(C\\cos x + D)$ と因数分解し、$f'(x)=0$ の3根 $x = \\frac{\\pi}{E}, \\frac{F}{G}\\pi, \\frac{H}{I}\\pi$ を求めよ。\n"
            "(2) 4つの区間における増減（0: 増加, 1: 減少）を調べ、極小値 $f(\\frac{L}{M}\\pi) = \\frac{\\sqrt{S}}{T} > 0$ を示すことで、$0 < x < \\pi$ で $f(x) > 0$ を証明せよ。\n\n"
            "**【公式正解】**\n"
            "- $\\text{ABCD} = \\mathbf{2121}$\n"
            "- $E = \\mathbf{4}, \\quad \\text{FG} = \\mathbf{23}, \\quad \\text{HI} = \\mathbf{34}$\n"
            "- $J = \\mathbf{4}, \\quad K = \\mathbf{0}$\n"
            "- $\\text{LM} = \\mathbf{23}, \\quad N = \\mathbf{1}$\n"
            "- $\\text{OP} = \\mathbf{34}, \\quad Q = \\mathbf{0}$\n"
            "- $R = \\mathbf{1}$\n"
            "- $\\text{ST} = \\mathbf{34}$\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "**(1) 導関数の因数分解と零点の決定**\n"
            "$f(x) = \\sin x + \\frac{1}{2}\\sin 2x + \\frac{1}{3}\\sin 3x$ を微分する：\n"
            "$$f'(x) = \\cos x + \\frac{1}{2}(2\\cos 2x) + \\frac{1}{3}(3\\cos 3x) = \\cos x + \\cos 2x + \\cos 3x$$\n"
            "和積の公式 $\\cos x + \\cos 3x = 2\\cos 2x \\cos x$ を適用すると：\n"
            "$$f'(x) = \\cos 2x + 2\\cos 2x \\cos x = \\cos 2x (2\\cos x + 1)$$\n"
            "2倍角の公式 $\\cos 2x = 2\\cos^2 x - 1$ を代入すると：\n"
            "$$f'(x) = (2\\cos^2 x - 1)(2\\cos x + 1)$$\n"
            "したがって、$A = 2, B = 1, C = 2, D = 1$（$\\text{ABCD} = \\mathbf{2121}$）である。\n\n"
            "区間 $0 \\le x \\le \\pi$ において $f'(x) = 0$ を解く：\n"
            "1. $2\\cos^2 x - 1 = 0 \\iff \\cos^2 x = \\frac{1}{2} \\iff \\cos x = \\pm \\frac{\\sqrt{2}}{2}$\n"
            "   $0 \\le x \\le \\pi$ より $x = \\frac{\\pi}{4}, \\frac{3\\pi}{4}$\n"
            "2. $2\\cos x + 1 = 0 \\iff \\cos x = -\\frac{1}{2}$\n"
            "   $0 \\le x \\le \\pi$ より $x = \\frac{2\\pi}{3}$\n"
            "解を昇順に並べると：\n"
            "$$x = \\frac{\\pi}{4}, \\quad \\frac{2}{3}\\pi, \\quad \\frac{3}{4}\\pi$$\n"
            "したがって、$E = 4, FG = 23, HI = 34$（$\\text{FG} = \\mathbf{23}, \\text{HI} = \\mathbf{34}$）である。\n\n"
            "**(2) 増減の追跡と $f(x) > 0$ の証明**\n"
            "4つの区間に分割して導関数の符号を調べる：\n"
            "1. $0 \\le x \\le \\frac{\\pi}{4}$（$J = \\mathbf{4}$）：\n"
            "   $\\cos x \\ge \\frac{\\sqrt{2}}{2}$ であるから、$2\\cos^2 x - 1 \\ge 0$ かつ $2\\cos x + 1 > 0$。\n"
            "   したがって $f'(x) \\ge 0$ となり「増加」（$K = \\mathbf{0}$）。\n"
            "2. $\\frac{\\pi}{4} \\le x \\le \\frac{2}{3}\\pi$（$\\text{LM} = \\mathbf{23}$）：\n"
            "   $-\\frac{1}{2} \\le \\cos x \\le \\frac{\\sqrt{2}}{2}$ であるから、$2\\cos^2 x - 1 \\le 0$ かつ $2\\cos x + 1 \\ge 0$。\n"
            "   したがって $f'(x) \\le 0$ となり「減少」（$N = \\mathbf{1}$）。\n"
            "3. $\\frac{2}{3}\\pi \\le x \\le \\frac{3}{4}\\pi$（$\\text{OP} = \\mathbf{34}$）：\n"
            "   $-\\frac{\\sqrt{2}}{2} \\le \\cos x \\le -\\frac{1}{2}$ であるから、$2\\cos^2 x - 1 \\le 0$ かつ $2\\cos x + 1 \\le 0$。\n"
            "   負数同士の積は正であるから $f'(x) \\ge 0$ となり「増加」（$Q = \\mathbf{0}$）。\n"
            "4. $\\frac{3}{4}\\pi \\le x \\le \\pi$：\n"
            "   $-1 \\le \\cos x \\le -\\frac{\\sqrt{2}}{2}$ であるから、$2\\cos^2 x - 1 \\ge 0$ かつ $2\\cos x + 1 < 0$。\n"
            "   したがって $f'(x) \\le 0$ となり「減少」（$R = \\mathbf{1}$）。\n\n"
            "極小値 $f(\\frac{2}{3}\\pi)$ の値を計算する：\n"
            "$$f\\left(\\frac{2\\pi}{3}\\right) = \\sin\\frac{2\\pi}{3} + \\frac{1}{2}\\sin\\frac{4\\pi}{3} + \\frac{1}{3}\\sin 2\\pi$$\n"
            "$$= \\frac{\\sqrt{3}}{2} + \\frac{1}{2}\\left(-\\frac{\\sqrt{3}}{2}\\right) + 0 = \\frac{\\sqrt{3}}{2} - \\frac{\\sqrt{3}}{4} = \\frac{\\sqrt{3}}{4}$$\n"
            "したがって、$S = 3, T = 4$（$\\text{ST} = \\mathbf{34}$）である。\n\n"
            "境界値は $f(0) = 0, f(\\pi) = 0$ であり、区間 $(0, \\pi)$ 内の唯一の極小値は $f(2\\pi/3) = \\frac{\\sqrt{3}}{4} > 0$、極大値 $f(\\pi/4) > 0, f(3\\pi/4) > 0$ である。\n"
            "したがって、開区間 $0 < x < \\pi$ において常に $f(x) > 0$ が成立する。"
        )
    },
    {
        "localKey": "math-q-IV_2",
        "sectionId": "IV_2",
        "sectionTitle": "第IV問 [2]：三角関数の定積分と曲線とx軸で囲まれた部分の面積",
        "points": ["三角関数の基本定積分公式", "対称区間・周期性による積分の相殺", "正値領域における定積分と面積の導出"],
        "officialAnswers": {
            "UVW": "209"
        },
        "detailedSolution": (
            "**【題目大意】**\n"
            "区間 $0 \\le x \\le \\pi$ において、曲線 $y = f(x)$ と $x$ 軸とで囲まれた部分の面積 $S$ を求めよ。\n\n"
            "**【公式正解】**\n"
            "- $\\text{UVW} = \\mathbf{209}$\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "前問 (1) より、区間 $0 < x < \\pi$ において常に $f(x) > 0$ である。\n"
            "したがって、曲線 $y = f(x)$ と $x$ 軸で囲まれた部分の面積 $S$ はそのまま定積分によって計算できる：\n"
            "$$S = \\int_0^\\pi f(x) \\, dx = \\int_0^\\pi \\left( \\sin x + \\frac{\\sin 2x}{2} + \\frac{\\sin 3x}{3} \\right) dx$$\n\n"
            "各項を個別に積分する：\n"
            "1. $\\int_0^\\pi \\sin x \\, dx = \\left[ -\\cos x \\right]_0^\\pi = (-\\cos \\pi) - (-\\cos 0) = -(-1) - (-1) = 1 + 1 = 2$\n"
            "2. $\\int_0^\\pi \\frac{\\sin 2x}{2} \\, dx = \\left[ -\\frac{\\cos 2x}{4} \\right]_0^\\pi = -\\frac{1}{4}(\\cos 2\\pi - \\cos 0) = -\\frac{1}{4}(1 - 1) = 0$\n"
            "3. $\\int_0^\\pi \\frac{\\sin 3x}{3} \\, dx = \\left[ -\\frac{\\cos 3x}{9} \\right]_0^\\pi = -\\frac{1}{9}(\\cos 3\\pi - \\cos 0) = -\\frac{1}{9}(-1 - 1) = -\\frac{1}{9}(-2) = \\frac{2}{9}$\n\n"
            "以上を合算すると：\n"
            "$$S = 2 + 0 + \\frac{2}{9} = \\frac{18 + 2}{9} = \\frac{20}{9}$$\n"
            "形式 $\\frac{\\text{UV}}{W}$ より、$U = 2, V = 0, W = 9$。\n"
            "したがって、$\\text{UVW} = \\mathbf{209}$ である。"
        )
    },
]

# Write Markdown
md_content = r"""# 2020年度 第2回（2020-2）EJU 日本留学試験 数学（コース2）全問詳細解説

- **試験科目**：数学（コース2 / Mathematics Course 2）
- **対象試験**：2020年度第2回（令和2年11月実施）
- **形式コード**：`MATHEMATICS_COURSE_2_JA`
- **問題構成**：第I問 ～ 第IV問（計4大問、8問ユニット）
- **解答形式**：数字マーク式（DIGIT_GRID）

---

## 数学コース2 公式正解一覧表

| 大問 | 設問 | 解答記号 | 公式正解 | 考査分野・要点 |
| :--- | :--- | :--- | :--- | :--- |
| **I** | [1] | ABCD | **1442** | 放物線の平行移動・2次関数決定 |
| | | EFG | **248** | 2次不等式の整理 |
| | | HI | **68** | 2次不等式の解（境界値） |
| | | JKLM | **2940** | 放物線と直線で切り取られる線分長 |
| | | NO | **59** | 定数 $a$ の決定 |
| | [2] | P | **4** | 階段ののぼり方（1段のぼり回数） |
| | | QR | **35** | 反復試行によるのぼり方総数 |
| | | ST | **87** | フィボナッチ数列と条件付き総数 |
| | | U | **6** | 連続しない2段のぼり（1段回数） |
| | | VW | **21** | 隙間挿入法による配置通り数 |
| | | XY | **40** | 連続しないのぼり方の全通り数 |
| **II** | [1] | A | **1** | 数列の和 $S_n$ からの一般項 $a_n$ 導出 |
| | | B | **4** | 積の数列 $b_n = a_n a_{n+5}$ の展開形 |
| | | C | **9** | シグマ和 $T_n = \sum b_k$ の公式適用 |
| | | DEF | **310** | $b_n > 0$ となる $n$ の範囲 ($n \le 3$ または $10 \le n$) |
| | | GH | **58** | $b_n < 0$ となる $n$ の範囲 ($5 \le n \le 8$) |
| | | I, J, K | **1, 8, 9** | $T_n$ を最小にする3つの $n$ |
| | | L | **6** | $T_n$ の最小値 |
| | [2] | MN | **16** | 複素数 $8+8\sqrt{3}i$ の絶対値 |
| | | OP | **33** | 複素数 $8+8\sqrt{3}i$ の偏角 ($\pi/3$) |
| | | Q | **2** | 4乗根の絶対値 $|z| = 2$ |
| | | R | **6** | 偏角の合成計算 ($\arg(z_1 z_2 z_3 / z_4) = \pi/6$) |
| | | STUV | **1357** | 8次方程式の根と4乗根の対応添字 |
| | | W | **4** | 根の積 $w_1 w_8 = 4$ |
| | | XY | **-4** | 根の積 $w_3 w_4 = -4i$ ($\text{XY} = -4$) |
| **III** | [1] | ABC | **324** | 3次関数の導関数 $f'(x) = 3x^2 - 4$ |
| | | DE, F | **-1, 6** | 接線 $\ell$ の傾きと方程式 ($y = -x + 6$) |
| | | GHI | **324** | 任意接点における傾き表現 |
| | | JKL | **234** | 任意接点における $y$ 切片表現 |
| | | M | **2** | 点 $B(0, -12)$ を通る接点の $x$ 座標 |
| | | NOP | **812** | 接線 $m$ の方程式 ($y = 8x - 12$) |
| | | QR | **24** | 2接線の交点 $C(2, 4)$ |
| | [2] | ST, U | **-1, 8** | 直線と $x$ 軸正の向きのなす角の正接 |
| | | VW | **97** | 2直線のなす角の正接 ($\tan \theta = 9/7$) |
| **IV** | [1] | ABCD | **2121** | 導関数の因数分解 $(2\cos^2 x - 1)(2\cos x + 1)$ |
| | | E, FG, HI | **4, 23, 34** | $f'(x) = 0$ の3零点 ($\pi/4, 2\pi/3, 3\pi/4$) |
| | | J, K | **4, 0** | 区間 $[0, \pi/4]$ の増減 (増加) |
| | | LM, N | **23, 1** | 区間 $[\pi/4, 2\pi/3]$ の増減 (減少) |
| | | OP, Q | **34, 0** | 区間 $[2\pi/3, 3\pi/4]$ の増減 (増加) |
| | | R | **1** | 区間 $[3\pi/4, \pi]$ の増減 (減少) |
| | | ST | **34** | 極小値 $f(2\pi/3) = \sqrt{3}/4$ |
| | [2] | UVW | **209** | 曲線と $x$ 軸で囲まれた面積 $S = 20/9$ |

---

## 逐問詳細推導与解説

"""

for sec in math_c2_sections:
    s_title = sec['sectionTitle']
    s_pts = ", ".join(sec['points'])
    s_sol = sec['detailedSolution']
    md_content += f"\n---\n\n## {s_title}\n\n**【考査考点】**：{s_pts}\n\n{s_sol}\n"

out_md = Path("docs/explanations/2020-2-math-c2-solutions.md")
out_md.parent.mkdir(parents=True, exist_ok=True)
out_md.write_text(md_content, encoding="utf-8")

payload = {"sections": math_c2_sections}
out_json = Path("work/2020-2-math-c2/explanations.json")
out_json.parent.mkdir(parents=True, exist_ok=True)
out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"Generated {out_md} and {out_json} successfully.")

