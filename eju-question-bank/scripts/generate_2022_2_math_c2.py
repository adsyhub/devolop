#!/usr/bin/env python3
"""Generate comprehensive explanations for 2022-2 EJU Mathematics Course 2."""

import json
from pathlib import Path

explanations = {
    "session": "2022-2",
    "subject": "MATHEMATICS",
    "course": "COURSE_2",
    "formCode": "MATHEMATICS_COURSE_2_JA",
    "sections": [
        {
            "sectionId": "I_1",
            "sectionTitle": "第I問 問1：2次関数の決定・交点間距離と平行移動・方程式の決定",
            "points": ["2次関数の軸と対称性", "直線 $y=k$ との交点間距離 $2|\\alpha - p|$", "頂点座標と2次関数の係数決定"],
            "officialAnswers": {
                "A": "2",
                "BC": "41",
                "DE": "93",
                "FG": "25",
                "HI": "35",
                "JK": "45",
                "LM": "15"
            },
            "detailedSolution": (
                "### 【第I問 問1】詳細解答と解説\n\n"
                "#### (1) 直線との交点間距離から 2 次関数の決定\n"
                "2次関数 $y = ax^2 + bx + c$ ($a \\ne 0$) のグラフ $C$ の頂点の座標を $(p, q)$ とおくと、放物線の方程式は標準形で次のように表される：\n"
                "$$y = a(x - p)^2 + q$$\n"
                "放物線は軸 $x = p$ に関して対称である。\n"
                "グラフ $C$ と直線 $y = 1$ との交点間の距離は 4 であるから、軸から交点までの距離は：\n"
                "$$|\\alpha - p| = \\frac{4}{2} = 2 \\implies \\mathbf{A = 2}$$\n"
                "交点の座標 $(\\alpha, 1)$ を代入すると：\n"
                "$$a(\\alpha - p)^2 + q = 1 \\implies 4a + q = 1$$\n"
                "よって、$\\mathbf{B = 4, C = 1}$（解答番号 $\\mathbf{BC = 41}$）である。\n\n"
                "同様に、直線 $y = 3$ との交点間距離は 6 であるから、軸からの距離は $\\frac{6}{2} = 3$ である。\n"
                "交点の座標を代入すると：\n"
                "$$a \\cdot 3^2 + q = 3 \\implies 9a + q = 3$$\n"
                "よって、$\\mathbf{D = 9, E = 3}$（解答番号 $\\mathbf{DE = 93}$）である。\n\n"
                "連立方程式を解く：\n"
                "$$\\begin{cases} 4a + q = 1 \\\\ 9a + q = 3 \\end{cases} \\implies 5a = 2 \\implies a = \\frac{2}{5}, \\quad q = 1 - 4\\left(\\frac{2}{5}\\right) = -\\frac{3}{5}$$\n"
                "したがって：\n"
                "$$a = \\frac{2}{5} \\implies \\mathbf{F = 2, G = 5} \\quad (\\mathbf{FG = 25})$$\n"
                "$$q = -\\frac{3}{5} \\implies \\mathbf{H = 3, I = 5} \\quad (\\mathbf{HI = 35})$$\n\n"
                "#### (2) 点 $(2, -1/5)$ を通過する条件と係数の決定\n"
                "放物線の方程式 $y = \\frac{2}{5}(x - p)^2 - \\frac{3}{5}$ が点 $\\left(2, -\\frac{1}{5}\\right)$ を通るから：\n"
                "$$-\\frac{1}{5} = \\frac{2}{5}(2 - p)^2 - \\frac{3}{5} \\implies 2(2 - p)^2 = 2 \\implies (2 - p)^2 = 1$$\n"
                "条件 $p < 2$ より、$2 - p = 1 \\implies p = 1$ である。\n"
                "したがって、放物線の方程式は：\n"
                "$$y = \\frac{2}{5}(x - 1)^2 - \\frac{3}{5} = \\frac{2}{5}x^2 - \\frac{4}{5}x - \\frac{1}{5}$$\n"
                "もとの式 $y = ax^2 + bx + c$ と比較して：\n"
                "$$b = -\\frac{4}{5} \\implies \\mathbf{J = 4, K = 5} \\quad (\\mathbf{JK = 45})$$\n"
                "$$c = -\\frac{1}{5} \\implies \\mathbf{L = 1, M = 5} \\quad (\\mathbf{LM = 15})$$"
            )
        },
        {
            "sectionId": "I_2",
            "sectionTitle": "第I問 問2：サイコロの試行・「つながっている目」の推移確率と終了条件",
            "points": ["事象の分類（端の目 1, 6 と中の目 2, 3, 4, 5）", "条件付き確率と全確率の公式", "余事象による終了確率の計算"],
            "officialAnswers": {
                "NO": "49",
                "PQ": "59",
                "R": "2",
                "S": "7",
                "T": "3"
            },
            "detailedSolution": (
                "### 【第I問 問2】詳細解答と解説\n\n"
                "#### (1) 2 回目の操作を終えた時点で試行が終了していない確率\n"
                "出目をグループ E（端の目 1, 6：つながる目 2 通り、継続確率 $\\frac{1}{3}$）とグループ M（中の目 2, 3, 4, 5：つながる目 3 通り、継続確率 $\\frac{1}{2}$）に分ける。\n"
                "$$P(\\text{2回継続}) = \\frac{2}{6} \\times \\frac{2}{6} + \\frac{4}{6} \\times \\frac{3}{6} = \\frac{1}{3} \\times \\frac{1}{3} + \\frac{2}{3} \\times \\frac{1}{2} = \\frac{1}{9} + \\frac{1}{3} = \\frac{4}{9}$$\n"
                "したがって、$\\mathbf{N = 4, O = 9}$（解答番号 $\\mathbf{NO = 49}$）である。\n\n"
                "#### (2) 2 回目の操作で試行が終了する確率\n"
                "$$P(\\text{2回終了}) = 1 - P(\\text{2回継続}) = 1 - \\frac{4}{9} = \\frac{5}{9}$$\n"
                "したがって、$\\mathbf{P = 5, Q = 9}$（解答番号 $\\mathbf{PQ = 59}$）である。\n\n"
                "#### (3) 3 回目の操作を終えた時点で試行が終了していない確率 R\n"
                "2 回継続した 16 通りの出目のうち、2 回目の目が端 E となるのは 4 通り（確率 $\\frac{4}{36} = \\frac{1}{9}$）、中 M となるのは 12 通り（確率 $\\frac{12}{36} = \\frac{1}{3}$）である。\n"
                "3 回目に継続する確率は：\n"
                "$$P(\\text{3回継続}) = \\frac{1}{9} \\times \\frac{1}{3} + \\frac{1}{3} \\times \\frac{1}{2} = \\frac{1}{27} + \\frac{1}{6} = \\frac{11}{54}$$\n"
                "選択肢 $\\textcircled{2}$ の $\\frac{11}{54}$ に一致する。よって $\\mathbf{R = 2}$ である。\n\n"
                "#### (4) 3 回以下の操作で試行が終了する確率 S\n"
                "$$P(\\text{3回以下で終了}) = 1 - P(\\text{3回継続}) = 1 - \\frac{11}{54} = \\frac{43}{54}$$\n"
                "選択肢 $\\textcircled{7}$ の $\\frac{43}{54}$ に一致する。よって $\\mathbf{S = 7}$ である。\n\n"
                "#### (5) 3 回目の操作で試行が終了する確率 T\n"
                "$$P(\\text{3回目で終了}) = P(\\text{2回継続}) - P(\\text{3回継続}) = \\frac{4}{9} - \\frac{11}{54} = \\frac{13}{54}$$\n"
                "選択肢 $\\textcircled{3}$ の $\\frac{13}{54}$ に一致する。よって $\\mathbf{T = 3}$ である。"
            )
        },
        {
            "sectionId": "II_1",
            "sectionTitle": "第II問 問1：数列の因数分解と倍数条件・剰余類の和の計算",
            "points": ["2次式の因数分解 $a_n = (n+2)(4n-3)$", "素数5の倍数条件と剰余類（$n \\equiv 3, 2 \\pmod 5$）", "自然数の和の公式 $\\sum k, \\sum k^2$ による総和計算"],
            "officialAnswers": {
                "ABC": "243",
                "D": "1",
                "E": "5",
                "F": "5",
                "G": "3",
                "H": "2",
                "I": "9",
                "J": "8",
                "K": "4",
                "L": "6",
                "M": "2"
            },
            "detailedSolution": (
                "### 【第II問 問1】詳細解答と解説\n\n"
                "#### (1) 因数分解と 5 の倍数条件\n"
                "第 $n$ 項が $a_n = 4n^2 + 5n - 6$ で与えられる数列を考える。\n"
                "たすき掛けにより因数分解すると：\n"
                "$$a_n = (n + 2)(4n - 3)$$\n"
                "したがって、$\\mathbf{A = 2, B = 4, C = 3}$（解答番号 $\\mathbf{ABC = 243}$）である。\n\n"
                "5 は素数であるから、$a_n$ が 5 の倍数となるのは「$n+2$ が 5 の倍数」または「$4n-3$ が 5 の倍数」のときである。\n\n"
                "**(i) $n+2$ が 5 の倍数のとき**：\n"
                "整数 $k$ を用いて $n+2 = 5k \\implies n = 5k - 2$ と表される。\n"
                "選択肢 $\\textcircled{1}$「$5k - 2$」に一致する。よって $\\mathbf{D = 1}$ である。\n"
                "このとき $a_n$ は：\n"
                "$$a_n = (5k)(4(5k - 2) - 3) = 5k(20k - 11) = 5(20k^2 - 11k)$$\n"
                "選択肢 $\\textcircled{5}$ に一致する。よって $\\mathbf{E = 5}$ である。\n\n"
                "**(ii) $4n - 3$ が 5 の倍数のとき**：\n"
                "整数 $j$ を用いて $4n - 3 = 5j$ と表す（$\\mathbf{F = 5}$）。\n"
                "この式は：\n"
                "$$4n - 3 = 5(n - j) - n - 3 \\implies n + 3 = 5(n - j)$$\n"
                "と変形できる。よって $\\mathbf{G = 3}$ である。\n"
                "$n + 3$ は 5 の倍数であるから、整数 $k$ を用いて $n + 3 = 5k \\implies n = 5k - 3$ と表される。\n"
                "選択肢 $\\textcircled{2}$「$5k - 3$」に一致する。よって $\\mathbf{H = 2}$ である。\n"
                "このとき $a_n$ は：\n"
                "$$n + 2 = 5k - 1, \\quad 4n - 3 = 4(5k - 3) - 3 = 20k - 15 = 5(4k - 3)$$\n"
                "$$a_n = (5k - 1) \\cdot 5(4k - 3) = 5(20k^2 - 19k + 3)$$\n"
                "選択肢 $\\textcircled{9}$ に一致する。よって $\\mathbf{I = 9}$ である。\n\n"
                "#### (2) 最初の 20 項における個数と総和\n"
                "$a_n$ が 5 の倍数となる $n$ の条件は $n = 5k - 3$ または $n = 5k - 2$（$n \\equiv 2, 3 \\pmod 5$）である。\n"
                "1 周期（5個ごと）に 2 個現れるので、$n = 1 \\dots 20$（4周期分、$\\mathbf{K = 4}$）に含まれる個数は：\n"
                "$$J = 4 \\times 2 = 8 \\implies \\mathbf{J = 8}$$\n\n"
                "各周期 $k$ における 2 項の和 $L$ は：\n"
                "$$L = 5(20k^2 - 11k) + 5(20k^2 - 19k + 3) = 5(40k^2 - 30k + 3)$$\n"
                "選択肢 $\\textcircled{6}$「$5(40k^2 - 30k + 3)$」に一致する。よって $\\mathbf{L = 6}$ である。\n\n"
                "和 $S = \\sum_{k=1}^4 5(40k^2 - 30k + 3)$ を計算する：\n"
                "$$\\sum_{k=1}^4 k^2 = 1 + 4 + 9 + 16 = 30, \\quad \\sum_{k=1}^4 k = 1 + 2 + 3 + 4 = 10, \\quad \\sum_{k=1}^4 1 = 4$$\n"
                "$$S = 5 \\times [40(30) - 30(10) + 3(4)] = 5 \\times (1200 - 300 + 12) = 5 \\times 912 = 4560$$\n"
                "選択肢 $\\textcircled{2}$ の 4560 に一致する。よって $\\mathbf{M = 2}$ である。"
            )
        },
        {
            "sectionId": "II_2",
            "sectionTitle": "第II問 問2：複素数平面・回転と線対称・直角三角形の幾何学的解法",
            "points": ["複素数の絶対値と偏角", "複素数の商と回転角（$\\sin\\theta$ の決定）", "直線に関する線対称移動と複素数表示", "正弦定理による $\\sin\\angle OBA$ の計算"],
            "officialAnswers": {
                "NO": "42",
                "PQR": "255",
                "S": "8",
                "T": "2",
                "UVW": "345",
                "XYZ": "213"
            },
            "detailedSolution": (
                "### 【第II問 問2】詳細解答と解説\n\n"
                "#### (1) $|\\beta|$ の値\n"
                "関係式 $4(1 + 3i)\\alpha - (7 + i)\\beta = 0$ より：\n"
                "$$\\frac{\\beta}{\\alpha} = \\frac{4(1 + 3i)}{7 + i} = \\frac{4(1 + 3i)(7 - i)}{7^2 + 1^2} = \\frac{4(7 - i + 21i + 3)}{50} = \\frac{4(10 + 20i)}{50} = \\frac{4 + 8i}{5}$$\n"
                "両辺の絶対値をとると：\n"
                "$$\\left|\\frac{\\beta}{\\alpha}\\right| = \\frac{\\sqrt{4^2 + 8^2}}{5} = \\frac{\\sqrt{80}}{5} = \\frac{4\\sqrt{5}}{5} = \\frac{4}{\\sqrt{5}}$$\n"
                "$|\\alpha| = \\sqrt{10}$ であるから：\n"
                "$$|\\beta| = \\left|\\frac{\\beta}{\\alpha}\\right| |\\alpha| = \\frac{4\\sqrt{5}}{5} \\times \\sqrt{10} = \\frac{4\\sqrt{50}}{5} = \\frac{4 \\times 5\\sqrt{2}}{5} = 4\\sqrt{2}$$\n"
                "したがって、$\\mathbf{N = 4, O = 2}$（解答番号 $\\mathbf{NO = 42}$）である。\n\n"
                "#### (2) $\\sin \\theta$ の値\n"
                "$\\frac{\\beta}{\\alpha} = \\frac{4}{5} + \\frac{8}{5}i$ であり、その絶対値は $\\frac{4\\sqrt{5}}{5}$ である。\n"
                "極形式 $\\frac{\\beta}{\\alpha} = \\left|\\frac{\\beta}{\\alpha}\\right|(\\cos\\theta + i\\sin\\theta)$ の虚部を比較すると：\n"
                "$$\\left|\\frac{\\beta}{\\alpha}\\right| \\sin\\theta = \\frac{8}{5} \\implies \\frac{4\\sqrt{5}}{5} \\sin\\theta = \\frac{8}{5} \\implies \\sin\\theta = \\frac{8}{4\\sqrt{5}} = \\frac{2}{\\sqrt{5}} = \\frac{2\\sqrt{5}}{5}$$\n"
                "したがって、$\\mathbf{P = 2, Q = 5, R = 5}$（解答番号 $\\mathbf{PQR = 255}$）である。\n\n"
                "#### (3) 三角形 OAB の面積\n"
                "三角形 OAB の面積 $S$ は：\n"
                "$$S = \\frac{1}{2} OA \\cdot OB \\cdot \\sin\\theta = \\frac{1}{2} |\\alpha| |\\beta| \\sin\\theta = \\frac{1}{2} \\times \\sqrt{10} \\times 4\\sqrt{2} \\times \\frac{2\\sqrt{5}}{5} = \\frac{1}{2} \\times 8\\sqrt{5} \\times \\frac{2\\sqrt{5}}{5} = 8$$\n"
                "したがって、$\\mathbf{S = 8}$ である。\n\n"
                "#### (4) 対称点 C の複素数表示\n"
                "直線 OB に関して点 A と対称な点を C とする。\n"
                "原点 O を基準とすると、$OA = OC = |\\alpha|$ であり、直線 OB は $\\angle AOC$ の二等分線である。\n"
                "点 A から点 B への回転角が $\\theta$ であるから、点 A から点 C への回転角は $2\\theta$ である。よって $\\mathbf{T = 2}$ である。\n"
                "2倍角の公式より：\n"
                "$$\\cos 2\\theta = 1 - 2\\sin^2\\theta = 1 - 2\\left(\\frac{4}{5}\\right) = -\\frac{3}{5}$$\n"
                "$$\\sin 2\\theta = 2\\sin\\theta\\cos\\theta = 2 \\times \\frac{2\\sqrt{5}}{5} \\times \\frac{\\sqrt{5}}{5} = \\frac{4}{5}$$\n"
                "したがって、点 C を表す複素数 $\\gamma$ は：\n"
                "$$\\gamma = (\\cos 2\\theta + i\\sin 2\\theta)\\alpha = \\left(-\\frac{3}{5} + \\frac{4}{5}i\\right)\\alpha = \\frac{-3 + 4i}{5}\\alpha$$\n"
                "よって、$\\mathbf{U = 3, V = 4, W = 5}$（解答番号 $\\mathbf{UVW = 345}$）である。\n\n"
                "#### (5) $\\sin \\angle OBA$ の値\n"
                "線分 AB の長さを求める：\n"
                "$$\\beta - \\alpha = \\left(\\frac{4+8i}{5} - 1\\right)\\alpha = \\frac{-1+8i}{5}\\alpha$$\n"
                "$$|\\beta - \\alpha|^2 = \\frac{(-1)^2 + 8^2}{25} |\\alpha|^2 = \\frac{65}{25} \\times 10 = 26 \\implies AB = \\sqrt{26}$$\n"
                "$\\triangle OAB$ において正弦定理を用いる：\n"
                "$$\\frac{OA}{\\sin\\angle OBA} = \\frac{AB}{\\sin\\theta} \\implies \\sin\\angle OBA = \\frac{OA \\sin\\theta}{AB} = \\frac{\\sqrt{10} \\times \\frac{2\\sqrt{5}}{5}}{\\sqrt{26}} = \\frac{2\\sqrt{2}}{\\sqrt{26}} = \\frac{2}{\\sqrt{13}} = \\frac{2\\sqrt{13}}{13}$$\n"
                "したがって、$\\mathbf{X = 2, Y = 1, Z = 3}$（解答番号 $\\mathbf{XYZ = 213}$）である。"
            )
        },
        {
            "sectionId": "III_1",
            "sectionTitle": "第III問 (前半)：対数関数の変数変換と3次関数の導関数・極値条件",
            "points": ["底の変換・対数変数変換 $t = \\log_4 x$", "3次関数の導関数と因数分解", "極値を与える点 $t$ の方程式への代入"],
            "officialAnswers": {
                "AB": "74",
                "CDE": "363",
                "FG": "12",
                "HI": "32",
                "JKL": "145",
                "MNO": "947"
            },
            "detailedSolution": (
                "### 【第III問 (前半)】詳細解答と解説\n\n"
                "#### (1) 変数変換による 3 次関数の導出\n"
                "与えられた関数は：\n"
                "$$y = (\\log_4 a^3)(\\log_4 x)(\\log_4 ax) + (\\log_4 b^3)\\left(\\log_4 \\frac{x}{b}\\right)(\\log_4 x) + (\\log_4 x)^3$$\n"
                "$\\log_4 a = p, \\log_4 b = q, \\log_4 x = t$ とおくと：\n"
                "- $\\log_4 a^3 = 3p$\n"
                "- $\\log_4 ax = \\log_4 a + \\log_4 x = p + t$\n"
                "- $\\log_4 b^3 = 3q$\n"
                "- $\\log_4 \\frac{x}{b} = \\log_4 x - \\log_4 b = t - q$\n\n"
                "各項を代入して整理する：\n"
                "$$y = 3pt(p + t) + 3qt(t - q) + t^3 = 3p^2 t + 3p t^2 + 3q t^2 - 3q^2 t + t^3 = t^3 + 3(p+q)t^2 + 3(p^2 - q^2)t$$\n"
                "選択肢より：\n"
                "$$t^2 \\text{ の係数} = 3(p+q) \\implies \\mathbf{A = 7} \\quad (\\textcircled{7})$$\n"
                "$$t \\text{ の係数} = 3(p^2 - q^2) \\implies \\mathbf{B = 4} \\quad (\\textcircled{4})$$\n"
                "したがって、$\\mathbf{AB = 74}$ である。\n\n"
                "#### (2) 導関数 $g'(t)$\n"
                "$$g'(t) = 3t^2 + 6(p+q)t + 3(p^2 - q^2) = 3\\{t^2 + 2(p+q)t + (p^2 - q^2)\\}$$\n"
                "選択肢と比較して：\n"
                "$$\\mathbf{C = 3}, \\quad 2(p+q) \\implies \\mathbf{D = 6} \\quad (\\textcircled{6}), \\quad (p^2 - q^2) \\implies \\mathbf{E = 3} \\quad (\\textcircled{3})$$\n"
                "したがって、$\\mathbf{CDE = 363}$ である。\n\n"
                "#### (3) 極値をとる $t$ の値と関係式\n"
                "- $x = \\frac{1}{2}$ のとき：$t = \\log_4 \\frac{1}{2} = \\log_4 (4^{-1/2}) = -\\frac{1}{2}$。\n"
                "  よって、$t = -\\frac{\\text{F}}{\\text{G}} = -\\frac{1}{2} \\implies \\mathbf{FG = 12}$。\n"
                "- $x = 8$ のとき：$t = \\log_4 8 = \\log_4 (2^3) = \\log_4 (4^{3/2}) = \\frac{3}{2}$。\n"
                "  よって、$t = \\frac{\\text{H}}{\\text{I}} = \\frac{3}{2} \\implies \\mathbf{HI = 32}$。\n\n"
                "$g'(t) = 0$ に $t = -\\frac{1}{2}$ を代入すると：\n"
                "$$\\left(-\\frac{1}{2}\\right)^2 + 2(p+q)\\left(-\\frac{1}{2}\\right) + (p^2 - q^2) = 0 \\implies \\frac{1}{4} - (p+q) + (p^2 - q^2) = 0$$\n"
                "よって、$\\mathbf{JKL = 145}$（選択肢 $\\textcircled{5}$ は $(p+q)$）。\n\n"
                "$t = \\frac{3}{2}$ を代入すると：\n"
                "$$\\left(\\frac{3}{2}\\right)^2 + 2(p+q)\\left(\\frac{3}{2}\\right) + (p^2 - q^2) = 0 \\implies \\frac{9}{4} + 3(p+q) + (p^2 - q^2) = 0$$\n"
                "よって、$\\mathbf{MNO = 947}$（選択肢 $\\textcircled{7}$ は $3(p+q)$）である。"
            )
        },
        {
            "sectionId": "III_2",
            "sectionTitle": "第III問 (後半)：定数 $a, b$ の決定と極値の差 $|m_1 - m_2|$ の計算",
            "points": ["解と係数の関係による連立方程式の求解", "定数 $p, q$ および $a, b$ の決定", "3次関数の極大値と極小値の差の公式"],
            "officialAnswers": {
                "PQ": "12",
                "RS": "-1",
                "T": "2",
                "UV": "14",
                "W": "4"
            },
            "detailedSolution": (
                "### 【第III問 (後半)】詳細解答と解説\n\n"
                "#### (1) $p, q$ の決定\n"
                "$t^2 + 2(p+q)t + (p^2 - q^2) = 0$ の 2 解が $t = -\\frac{1}{2}, \\frac{3}{2}$ であるから、解と係数の関係より：\n"
                "- 解の和：\n"
                "  $$\\left(-\\frac{1}{2}\\right) + \\frac{3}{2} = 1 = -2(p+q) \\implies p+q = -\\frac{1}{2}$$\n"
                "- 解の積：\n"
                "  $$\\left(-\\frac{1}{2}\\right)\\left(\\frac{3}{2}\\right) = -\\frac{3}{4} = p^2 - q^2 = (p+q)(p-q)$$\n"
                "$p+q = -\\frac{1}{2}$ を代入すると：\n"
                "$$-\\frac{1}{2}(p-q) = -\\frac{3}{4} \\implies p-q = \\frac{3}{2}$$\n\n"
                "連立方程式を解く：\n"
                "$$\\begin{cases} p + q = -\\frac{1}{2} \\\\ p - q = \\frac{3}{2} \\end{cases} \\implies 2p = 1 \\implies p = \\frac{1}{2}, \\quad q = -\\frac{1}{2} - \\frac{1}{2} = -1$$\n"
                "したがって：\n"
                "$$p = \\frac{1}{2} \\implies \\mathbf{P = 1, Q = 2} \\quad (\\mathbf{PQ = 12})$$\n"
                "$$q = -1 \\implies \\mathbf{RS = -1}$$\n\n"
                "#### (2) 定数 $a, b$ の決定\n"
                "$$\\log_4 a = p = \\frac{1}{2} \\implies a = 4^{1/2} = 2 \\implies \\mathbf{T = 2}$$\n"
                "$$\\log_4 b = q = -1 \\implies b = 4^{-1} = \\frac{1}{4} \\implies \\mathbf{U = 1, V = 4} \\quad (\\mathbf{UV = 14})$$\n\n"
                "#### (3) 極値の差 $|m_1 - m_2|$ の計算\n"
                "関数 $g(t) = t^3 - \\frac{3}{2}t^2 - \\frac{9}{4}t$ は 3 次関数（最高次の係数 $k = 1$）である。\n"
                "極値をとる 2 点の $t$ 座標の差は：\n"
                "$$\\Delta t = \\frac{3}{2} - \\left(-\\frac{1}{2}\\right) = 2$$\n"
                "3 次関数の極大値と極小値の差の公式より：\n"
                "$$|m_1 - m_2| = \\frac{|k|}{2} (\\Delta t)^3 = \\frac{1}{2} \\times 2^3 = 4$$\n"
                "（直接代入検算：\n"
                "$g(-1/2) = -1/8 - 3/8 + 9/8 = 5/8$\n"
                "$g(3/2) = 27/8 - 27/8 - 27/8 = -27/8$\n"
                "$|m_1 - m_2| = 5/8 - (-27/8) = 32/8 = 4$）。\n\n"
                "したがって、$\\mathbf{W = 4}$ である。"
            )
        },
        {
            "sectionId": "IV_1",
            "sectionTitle": "第IV問 (前半)：商の微分法・接線の方程式と増減の解析",
            "points": ["商の微分法 $\\left(\\frac{u}{v}\\right)'$", "曲線上の点における接線の方程式", "点 $(1, a)$ を通る条件方程式 $a = f(t)$", "導関数 $f'(t)$ と増減区間の判定"],
            "officialAnswers": {
                "ABC": "426",
                "DEF": "274",
                "GH": "16",
                "I": "0",
                "J": "3",
                "K": "1",
                "L": "3",
                "M": "6",
                "N": "2",
                "O": "3"
            },
            "detailedSolution": (
                "### 【第IV問 (前半)】詳細解答と解説\n\n"
                "#### (1) 接線の方程式の導出\n"
                "曲線 $y = \\frac{x - 2}{x^2} = x^{-1} - 2x^{-2}$ の導関数は：\n"
                "$$y' = -x^{-2} + 4x^{-3} = -\\frac{x - 4}{x^3}$$\n"
                "曲線上の点 $\\left(t, \\frac{t - 2}{t^2}\\right)$ における接線の方程式は：\n"
                "$$y - \\frac{t - 2}{t^2} = -\\frac{t - 4}{t^3}(x - t)$$\n"
                "展開して整理すると：\n"
                "$$y = -\\frac{t - 4}{t^3} x + \\frac{t - 4}{t^2} + \\frac{t - 2}{t^2} = -\\frac{t - 4}{t^3} x + \\frac{2t - 6}{t^2}$$\n"
                "問題文の形式と比較して：\n"
                "$$\\mathbf{A = 4, B = 2, C = 6} \\quad (\\mathbf{ABC = 426})$$\n\n"
                "#### (2) 点 $(1, a)$ を通る条件方程式 $a = f(t)$\n"
                "この接線が点 $(1, a)$ を通るので、$x = 1, y = a$ を代入する：\n"
                "$$a = -\\frac{t - 4}{t^3}(1) + \\frac{2t - 6}{t^2} = \\frac{-(t - 4) + t(2t - 6)}{t^3} = \\frac{2t^2 - 7t + 4}{t^3}$$\n"
                "したがって、$\\mathbf{D = 2, E = 7, F = 4}$（解答番号 $\\mathbf{DEF = 274}$）である。\n\n"
                "#### (3) 導関数 $f'(t)$ と増減の判定\n"
                "$f(t) = \\frac{2t^2 - 7t + 4}{t^3}$ を微分する：\n"
                "$$f'(t) = \\frac{(4t - 7)t^3 - (2t^2 - 7t + 4)(3t^2)}{t^6} = \\frac{(4t^2 - 7t) - (6t^2 - 21t + 12)}{t^4} = \\frac{-2t^2 + 14t - 12}{t^4} = -\\frac{2(t - 1)(t - 6)}{t^4}$$\n"
                "$G < H$ であるから、$\\mathbf{G = 1, H = 6}$（解答番号 $\\mathbf{GH = 16}$）である。\n\n"
                "$t^4 > 0$ ($t \\ne 0$) より、$f'(t)$ の符号は $-(t - 1)(t - 6)$ で決まる：\n"
                "- $t < 0$ のとき：$f'(t) < 0$ より **減少**（選択肢 $\\textcircled{3}$）。$\\mathbf{I = 0, J = 3}$\n"
                "- $0 < t < 1$ のとき：$f'(t) < 0$ より **減少**（選択肢 $\\textcircled{3}$）。$\\mathbf{K = 1, L = 3}$\n"
                "- $1 < t < 6$ のとき：$f'(t) > 0$ より **増加**（選択肢 $\\textcircled{2}$）。$\\mathbf{M = 6, N = 2}$\n"
                "- $6 < t$ のとき：$f'(t) < 0$ より **減少**（選択肢 $\\textcircled{3}$）。$\\mathbf{O = 3}$"
            )
        },
        {
            "sectionId": "IV_2",
            "sectionTitle": "第IV問 (後半)：極限値・増減表と3本の接線が引けるパラメータ $a$ の範囲",
            "points": ["無限遠および原点付近の極限値計算", "増減表の作成と極大値・極小値", "直線 $y=a$ との共有点の個数による解の分離"],
            "officialAnswers": {
                "P": "0",
                "Q": "4",
                "R": "5",
                "S": "1",
                "T": "0",
                "U": "0",
                "VWXYZ": "17108"
            },
            "detailedSolution": (
                "### 【第IV問 (後半)】詳細解答と解説\n\n"
                "#### (1) 極限値の計算\n"
                "$f(t) = \\frac{2}{t} - \\frac{7}{t^2} + \\frac{4}{t^3}$ について：\n"
                "- $t \\to \\pm\\infty$ のとき：\n"
                "  $$\\lim_{t \\to \\infty} f(t) = \\lim_{t \\to -\\infty} f(t) = 0$$\n"
                "  選択肢 $\\textcircled{0}$ の 0 に一致する。よって $\\mathbf{P = 0}$ である。\n"
                "- $t \\to +0$ のとき：分母 $t^3 > 0$ であり分子 $4 > 0$ であるから：\n"
                "  $$\\lim_{t \\to +0} f(t) = +\\infty$$\n"
                "  選択肢 $\\textcircled{4}$ の $\\infty$ に一致する。よって $\\mathbf{Q = 4}$ である。\n"
                "- $t \\to -0$ のとき：分母 $t^3 < 0$ であり分子 $4 > 0$ であるから：\n"
                "  $$\\lim_{t \\to -0} f(t) = -\\infty$$\n"
                "  選択肢 $\\textcircled{5}$ の $-\\infty$ に一致する。よって $\\mathbf{R = 5}$ である。\n\n"
                "#### (2) 極値の計算\n"
                "- $t = 1$ で極小値：\n"
                "  $$f(1) = \\frac{2(1)^2 - 7(1) + 4}{1^3} = \\frac{2 - 7 + 4}{1} = -1$$\n"
                "- $t = 6$ で極大値：\n"
                "  $$f(6) = \\frac{2(6)^2 - 7(6) + 4}{6^3} = \\frac{72 - 42 + 4}{216} = \\frac{34}{216} = \\frac{17}{108}$$\n\n"
                "#### (3) 3 本の接線が引ける $a$ の範囲\n"
                "点 $(1, a)$ から曲線へ 3 本の接線が引けるための必要十分条件は、方程式 $a = f(t)$ が異なる 3 つの実数解をもつことである。\n"
                "グラフ $y = f(t)$ と水平直線 $y = a$ の共有点の個数を調べる：\n"
                "- $t < 0$ の区間：$-\\infty$ から 0 まで単調減少。値域は $(-\\infty, 0)$。任意の $a < 0$ に対してちょうど 1 つの解をもつ。\n"
                "- $t > 0$ の区間：\n"
                "  $+\\infty$ から極小値 $-1$ まで減少し、極小値 $-1$ から極大値 $\\frac{17}{108}$ まで増加し、極大値から 0 へ単調減少する。\n\n"
                "したがって、全体の共有点数が 3 個となるのは以下の 2 つの領域である：\n"
                "1. **$-1 < a < 0$ のとき**：\n"
                "   $t < 0$ に 1 個、$t > 0$ に 2 個の計 3 個の解をもつ。\n"
                "2. **$0 < a < \\frac{17}{108}$ のとき**：\n"
                "   $t < 0$ に 0 個、$t > 0$ に 3 個の計 3 個の解をもつ。\n\n"
                "問題文の形式 $-S < a < T, \\quad U < a < \\frac{VW}{XYZ}$ と比較して：\n"
                "- $-1 < a < 0 \\implies \\mathbf{S = 1, T = 0}$\n"
                "- $0 < a < \\frac{17}{108} \\implies \\mathbf{U = 0, VW = 17, XYZ = 108} \\quad (\\mathbf{VWXYZ = 17108})$\n\n"
                "したがって、求める $a$ の範囲は **$-1 < a < 0, \\quad 0 < a < \\frac{17}{108}$** である。"
            )
        }
    ]
}

# Write JSON
out_json = Path("work/2022-2-math-c2/explanations.json")
out_json.parent.mkdir(parents=True, exist_ok=True)
out_json.write_text(json.dumps(explanations, ensure_ascii=False, indent=2), encoding="utf-8")

# Write Markdown document
md_content = r"""# 2022年度 第2回（2022-2）EJU 日本留学試験 数学コース2 全問詳細解説

- **試験科目**：数学（コース2 / Course 2）
- **対象試験**：2022年度第2回（令和4年11月実施）
- **形式コード**：`MATHEMATICS_COURSE_2_JA`
- **問題構成**：大問 I（問1, 問2）、大問 II（問1, 問2）、大問 III（前半, 後半）、大問 IV（前半, 後半）
- **解答形式**：マーク式数字空欄（A～Z等）

---

## 数学コース2 公式正解一覧表

| 大問 | 設問 | 空欄記号 | 正解 | 備考 |
| :--- | :--- | :--- | :--- | :--- |
| **第I問** | 問1 (1) | A | **2** | 軸からの距離 $|\alpha - p| = 2$ |
| | | BC | **41** | 等式 $4a + q = 1$ |
| | | DE | **93** | 等式 $9a + q = 3$ |
| | | FG | **25** | $a = 2/5$ |
| | | HI | **35** | $q = -3/5$ |
| | 問1 (2) | JK | **45** | $b = -4/5$ |
| | | LM | **15** | $c = -1/5$ |
| | 問2 (1) | NO | **49** | 2回目終了していない確率 $4/9$ |
| | 問2 (2) | PQ | **59** | 2回目で終了する確率 $5/9$ |
| | 問2 (3) | R | **2** | 3回目終了していない確率 $\frac{11}{54}$ |
| | 問2 (4) | S | **7** | 3回以下で終了する確率 $\frac{43}{54}$ |
| | 問2 (5) | T | **3** | 3回目で終了する確率 $\frac{13}{54}$ |
| **第II問** | 問1 (1) | ABC | **243** | 因数分解 $(n+2)(4n-3)$ |
| | | D | **1** | $n = 5k - 2$ |
| | | E | **5** | $a_n = 5(20k^2 - 11k)$ |
| | | F | **5** | $4n - 3 = 5j$ |
| | | G | **3** | $n + 3 = 5(n - j)$ |
| | | H | **2** | $n = 5k - 3$ |
| | | I | **9** | $a_n = 5(20k^2 - 19k + 3)$ |
| | 問1 (2) | J | **8** | 5の倍数の項数 8 個 |
| | | K | **4** | 上限 $K = 4$ |
| | | L | **6** | $5(40k^2 - 30k + 3)$ |
| | | M | **2** | 和 $S = 4560$ |
| | 問2 (1) | NO | **42** | $|\beta| = 4\sqrt{2}$ |
| | 問2 (2) | PQR | **255** | $\sin\theta = \frac{2\sqrt{5}}{5}$ |
| | 問2 (3) | S | **8** | 面積 $S = 8$ |
| | 問2 (4) | T | **2** | 回転角 $2\theta$ |
| | | UVW | **345** | $\gamma = \frac{-3+4i}{5}\alpha$ |
| | 問2 (5) | XYZ | **213** | $\sin\varphi = \frac{2\sqrt{13}}{13}$ |
| **第III問** | (前半) | AB | **74** | 係数 $3(p+q), 3(p^2-q^2)$ |
| | | CDE | **363** | 導関数 $3\{t^2 + 2(p+q)t + (p^2-q^2)\}$ |
| | | FG | **12** | 極値点 $t = -1/2$ |
| | | HI | **32** | 極値点 $t = 3/2$ |
| | | JKL | **145** | 等式 $\frac{1}{4} - (p+q) + (p^2-q^2) = 0$ |
| | | MNO | **947** | 等式 $\frac{9}{4} + 3(p+q) + (p^2-q^2) = 0$ |
| | (後半) | PQ | **12** | $p = 1/2$ |
| | | RS | **-1** | $q = -1$ |
| | | T | **2** | $a = 2$ |
| | | UV | **14** | $b = 1/4$ |
| | | W | **4** | 極値の差 $|m_1 - m_2| = 4$ |
| **第IV問** | (前半) | ABC | **426** | 接線 $y = -\frac{t-4}{t^3}x + \frac{2t-6}{t^2}$ |
| | | DEF | **274** | $a = \frac{2t^2 - 7t + 4}{t^3}$ |
| | | GH | **16** | $f'(t) = -\frac{2(t-1)(t-6)}{t^4}$ |
| | | I | **0** | 区間 $t < 0$ |
| | | J | **3** | 減少 |
| | | K | **1** | 区間 $0 < t < 1$ |
| | | L | **3** | 減少 |
| | | M | **6** | 区間 $1 < t < 6$ |
| | | N | **2** | 増加 |
| | | O | **3** | 区間 $6 < t$（減少） |
| | (後半) | P | **0** | 極限 $\lim_{t\to\pm\infty} f(t) = 0$ |
| | | Q | **4** | 極限 $\lim_{t\to +0} f(t) = \infty$ |
| | | R | **5** | 極限 $\lim_{t\to -0} f(t) = -\infty$ |
| | | S | **1** | 下限 $-1$ |
| | | T | **0** | 上限 0 |
| | | U | **0** | 下限 0 |
| | | VWXYZ | **17108** | 上限 $\frac{17}{108}$ |

---

## 逐問詳細推導与解説

"""

for s in explanations["sections"]:
    md_content += "\n---\n\n## " + s["sectionTitle"] + "\n\n"
    points_str = ", ".join(s["points"])
    md_content += f"**【考査考点】**：{points_str}\n\n"
    md_content += s["detailedSolution"] + "\n"

out_md = Path("docs/explanations/2022-2-math-c2-solutions.md")
out_md.parent.mkdir(parents=True, exist_ok=True)
out_md.write_text(md_content, encoding="utf-8")

print(f"Generated {out_md} and {out_json} successfully with {len(explanations['sections'])} sections.")

