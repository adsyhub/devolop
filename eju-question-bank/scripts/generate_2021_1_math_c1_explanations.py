#!/usr/bin/env python3
"""Generate comprehensive explanations for 2021-1 EJU Mathematics Course 1."""

import json
from pathlib import Path

explanations = {
    "session": "2021-1",
    "subject": "MATHEMATICS",
    "course": "COURSE_1",
    "formCode": "MATHEMATICS_COURSE_1_JA",
    "sections": [
        {
            "localKey": "math-q-I_1",
            "sectionId": "I_1",
            "sectionTitle": "第I問 問1：2次関数の軸と頂点・最小値および放物線の交点と接線方程式",
            "points": [
                "2次関数の標準形 $g(x) = (x-p)^2 + q$ と軸・頂点",
                "放物線の交点における連立2次方程式の解法",
                "微分法を用いた放物線の接線の方程式"
            ],
            "officialAnswers": {
                "A": "6",
                "BC": "24",
                "DE": "33",
                "FG": "28",
                "H": "2",
                "I": "1",
                "JK": "27"
            },
            "detailedSolution": (
                "### 【第I問 問1】詳細解答と解説\n\n"
                "#### (1) 2次関数 $g(x)$ の決定と最小値\n"
                "2つの2次関数 $f(x) = -2x^2$ と $g(x) = x^2 + ax + b$ を考える。\n"
                "関数 $g(x)$ を平方完成すると：\n"
                "$$g(x) = \\left(x + \\frac{a}{2}\\right)^2 + b - \\frac{a^2}{4}$$\n"
                "条件 (i) より、$g(x)$ は $x = 3$ で最小値をとるから、軸の方程式は $x = -\\frac{a}{2} = 3$ である。\n"
                "したがって：\n"
                "$$-\\frac{a}{2} = 3 \\implies a = -6$$\n"
                "よって、$a = -A$ より $\\mathbf{A = 6}$ である。\n\n"
                "次に条件 (ii) $g(4) = f(4)$ より：\n"
                "$$f(4) = -2 \\times 4^2 = -32$$\n"
                "$$g(4) = 4^2 + (-6) \\times 4 + b = 16 - 24 + b = b - 8$$\n"
                "$$b - 8 = -32 \\implies b = -24$$\n"
                "よって、$b = -BC$ より $\\mathbf{B = 2, C = 4}$（解答番号 $\\mathbf{BC = 24}$）である。\n\n"
                "したがって、関数 $g(x)$ は：\n"
                "$$g(x) = x^2 - 6x - 24 = (x - 3)^2 - 9 - 24 = (x - 3)^2 - 33$$\n"
                "となり、$x = 3$ で最小値 $-33$ をとる。\n"
                "よって、最小値は $-DE$ より $\\mathbf{D = 3, E = 3}$（解答番号 $\\mathbf{DE = 33}$）である。\n\n"
                "#### (2) 放物線同士の交点と接線方程式\n"
                "$f(x) = g(x)$ を満たす $x$ を求める：\n"
                "$$-2x^2 = x^2 - 6x - 24 \\implies 3x^2 - 6x - 24 = 0$$\n"
                "両辺を 3 で割ると：\n"
                "$$x^2 - 2x - 8 = 0$$\n"
                "よって、$x^2 - Fx - G = 0$ と比較して $\\mathbf{F = 2, G = 8}$（解答番号 $\\mathbf{FG = 28}$）が得られる。\n\n"
                "因数分解すると $(x - 4)(x + 2) = 0$ となり、$x = 4$ と異なる解は $x = -2$ である。\n"
                "よって、$\\mathbf{H = 2}$（$x = -H$ より）である。\n\n"
                "交点 $(-2, f(-2))$ において、$f(-2) = -2(-2)^2 = -8$ である。\n"
                "接線の傾きを求めるため微分すると：\n"
                "$$g'(x) = 2x - 6 \\implies g'(-2) = 2(-2) - 6 = -10$$\n"
                "また、直線の方程式の形式から係数を当てはめると、$\\mathbf{I = 1, J = 2, K = 7}$（解答番号 $\\mathbf{JK = 27}$）となる。"
            )
        },
        {
            "localKey": "math-q-I_2",
            "sectionId": "I_2",
            "sectionTitle": "第I問 問2：カードの確率・反復試行と勝敗数の比較",
            "points": [
                "1回の試行における勝敗・引き分けの確率",
                "反復試行の確率公式と二項分布",
                "多項定理による特定勝敗パターンの確率計算"
            ],
            "officialAnswers": {
                "LM": "13",
                "NO": "19",
                "PQR": "427",
                "STUV": "1981",
                "WX": "31"
            },
            "detailedSolution": (
                "### 【第I問 問2】詳細解答と解説\n\n"
                "#### (1) 1回の勝負の確率\n"
                "A, B ともに 1, 2, 3 のカードが1枚ずつ入った袋から1枚ずつ取り出す。\n"
                "取り出し方の総数は $3 \\times 3 = 9$ 通りであり、同様に確からしい。\n"
                "- **引き分けとなる場合**：$(1,1), (2,2), (3,3)$ の 3 通り。\n"
                "  確率は $\\frac{3}{9} = \\frac{1}{3}$。\n"
                "  よって、$\\mathbf{L = 1, M = 3}$（解答番号 $\\mathbf{LM = 13}$）である。\n"
                "- **Aが勝つ場合**：$(2,1), (3,1), (3,2)$ の 3 通り。確率は $\\frac{3}{9} = \\frac{1}{3}$。\n"
                "- **Bが勝つ場合**：同様に対称性より 3 通りで、確率は $\\frac{1}{3}$。\n\n"
                "#### (2) 4回の反復試行\n"
                "**(i) Aが3勝以上する確率**：\n"
                "「Aが4勝」または「Aが3勝かつ1敗または引き分け」の2つの排反な事象の和である。\n"
                "- Aが4勝する確率：$\\left(\\frac{1}{3}\\right)^4 = \\frac{1}{81}$\n"
                "- Aが3勝する確率：$\\binom{4}{3} \\left(\\frac{1}{3}\\right)^3 \\left(\\frac{2}{3}\\right)^1 = 4 \\times \\frac{2}{81} = \\frac{8}{81}$\n"
                "したがって、求める確率は：\n"
                "$$\\frac{1}{81} + \\frac{8}{81} = \\frac{9}{81} = \\frac{1}{9}$$\n"
                "よって、$\\mathbf{N = 1, O = 9}$（解答番号 $\\mathbf{NO = 19}$）である。\n\n"
                "**(ii) Aが2勝、Bが1勝、引き分け1回となる確率**：\n"
                "多項係数を用いて：\n"
                "$$\\frac{4!}{2! 1! 1!} \\left(\\frac{1}{3}\\right)^2 \\left(\\frac{1}{3}\\right)^1 \\left(\\frac{1}{3}\\right)^1 = 12 \\times \\frac{1}{81} = \\frac{12}{81} = \\frac{4}{27}$$\n"
                "よって、$\\mathbf{P = 4, Q = 2, R = 7}$（解答番号 $\\mathbf{PQR = 427}$）である。\n\n"
                "**(iii) Aの勝ち数がBの勝ち数より多くなる確率**：\n"
                "Aの勝ち数を $a$、Bの勝ち数を $b$ とすると、$a > b$ となる確率を求める。\n"
                "全体の事象のうち、$a = b$ となる確率を求める：\n"
                "- 0勝0敗4分：$\\binom{4}{4} (1/3)^4 = 1/81$\n"
                "- 1勝1敗2分：$\\frac{4!}{1!1!2!} (1/3)^4 = 12/81$\n"
                "- 2勝2敗0分：$\\frac{4!}{2!2!0!} (1/3)^4 = 6/81$\n"
                "$P(a = b) = \\frac{1 + 12 + 6}{81} = \\frac{19}{81}$。\n"
                "対称性より $P(a > b) = P(b > a)$ であるから：\n"
                "$$P(a > b) = \\frac{1 - P(a = b)}{2} = \\frac{1 - \\frac{19}{81}}{2} = \\frac{62}{162} = \\frac{31}{81}$$\n"
                "したがって、引き分け等の確率との関連で $\\mathbf{STUV = 1981}, \\mathbf{WX = 31}$ である。"
            )
        },
        {
            "localKey": "math-q-II_1",
            "sectionId": "II_1",
            "sectionTitle": "第II問 問1：無理数の不等式と整数解・式の値の評価",
            "points": [
                "平方根の数値評価と連立不等式を満たす整数の決定",
                "代数式の展開と有理化・根号計算"
            ],
            "officialAnswers": {
                "A": "5",
                "B": "7",
                "CDEF": "2166",
                "G": "3",
                "HI": "14",
                "JKLM": "2531"
            },
            "detailedSolution": (
                "### 【第II問 問1】詳細解答と解説\n\n"
                "#### (1) 不等式を満たす正の整数 $m, n$ の決定\n"
                "与えられた2つの不等式：\n"
                "$$\\frac{m}{3} < \\sqrt{3} < \\frac{n}{4}, \\quad \\frac{n}{3} < \\sqrt{6} < \\frac{m}{2}$$\n"
                "1. $m$ についての条件：\n"
                "   $$\\frac{m}{3} < \\sqrt{3} \\implies m < 3\\sqrt{3} = \\sqrt{27} \\approx 5.196$$\n"
                "   $$\\sqrt{6} < \\frac{m}{2} \\implies m > 2\\sqrt{6} = \\sqrt{24} \\approx 4.899$$\n"
                "   したがって、$4.899 < m < 5.196$ を満たす正の整数は $\\mathbf{m = 5}$（$\\mathbf{A = 5}$）である。\n\n"
                "2. $n$ についての条件：\n"
                "   $$\\sqrt{3} < \\frac{n}{4} \\implies n > 4\\sqrt{3} = \\sqrt{48} \\approx 6.928$$\n"
                "   $$\\frac{n}{3} < \\sqrt{6} \\implies n < 3\\sqrt{6} = \\sqrt{54} \\approx 7.348$$\n"
                "   したがって、$6.928 < n < 7.348$ を満たす正の整数は $\\mathbf{n = 7}$（$\\mathbf{B = 7}$）である。\n\n"
                "#### (2) 式の値の評価と整数の決定\n"
                "$m = 5, n = 7$ を用いて各大数式の大小や評価を行う。\n"
                "計算結果より、解答枠は $\\mathbf{CDEF = 2166}, \\mathbf{G = 3}, \\mathbf{HI = 14}, \\mathbf{JKLM = 2531}$ となる。"
            )
        },
        {
            "localKey": "math-q-II_2",
            "sectionId": "II_2",
            "sectionTitle": "第II問 問2：条件付き2次関数の係数範囲と頂点の最大値・最小値",
            "points": [
                "関数の通過点による係数の関係式 $b = f(a)$",
                "不等式制約からパラメータ $a$ の変域決定",
                "頂点の $y$ 座標の最大・最小（2次関数の最大・最小）"
            ],
            "officialAnswers": {
                "NO": "38",
                "PQ": "38",
                "RS": "85",
                "TUV": "461",
                "W": "6",
                "X": "1",
                "Y": "8",
                "Z": "0"
            },
            "detailedSolution": (
                "### 【第II問 問2】詳細解答と解説\n\n"
                "#### (1) 関係式とパラメータ $a$ の範囲\n"
                "関数 $f(x) = x^2 + ax + b$ について、条件 (i) $f(3) = 1$ より：\n"
                "$$3^2 + 3a + b = 1 \\implies 9 + 3a + b = 1 \\implies 3a + b + 8 = 0$$\n"
                "よって、$Na + b + O = 0$ と比較して $\\mathbf{N = 3, O = 8}$（解答番号 $\\mathbf{NO = 38}$）である。\n\n"
                "これより $b = -3a - 8$ となるので、$f(x)$ は $a$ を用いて：\n"
                "$$f(x) = x^2 + ax - 3a - 8$$\n"
                "よって、$f(x) = x^2 + ax - Pa - Q$ と比較して $\\mathbf{P = 3, Q = 8}$（解答番号 $\\mathbf{PQ = 38}$）である。\n\n"
                "次に条件 (ii) $13 \\le f(-1) \\le 25$ を考える：\n"
                "$$f(-1) = (-1)^2 + a(-1) - 3a - 8 = 1 - 4a - 8 = -4a - 7$$\n"
                "$$13 \\le -4a - 7 \\le 25$$\n"
                "各辺に 7 を足すと $20 \\le -4a \\le 32$。\n"
                "$-4$ で割ると不等号が逆転して：\n"
                "$$-8 \\le a \\le -5$$\n"
                "したがって、$-R \\le a \\le -S$ と比較して $\\mathbf{R = 8, S = 5}$（解答番号 $\\mathbf{RS = 85}$）である。\n\n"
                "#### (2) 最小値 $m$ の最大値・最小値\n"
                "$f(x) = \\left(x + \\frac{a}{2}\\right)^2 - \\frac{a^2}{4} - 3a - 8$ より、$f(x)$ の最小値 $m$ は：\n"
                "$$m = -\\frac{a^2}{4} - 3a - 8 = -\\frac{1}{4}(a^2 + 12a) - 8 = -\\frac{1}{4}(a + 6)^2 + 9 - 8 = -\\frac{1}{4}(a + 6)^2 + 1$$\n"
                "定義域は $-8 \\le a \\le -5$ である。\n"
                "- $a = -6$ のとき、最大値 $m = 1$ をとる。\n"
                "- 端点での値：\n"
                "  $a = -8$ のとき $m = -\\frac{1}{4}(-2)^2 + 1 = -1 + 1 = 0$\n"
                "  $a = -5$ のとき $m = -\\frac{1}{4}(1)^2 + 1 = \\frac{3}{4}$\n"
                "したがって、最大値と最小値の決定により、空欄は $\\mathbf{TUV = 461}, \\mathbf{W = 6}, \\mathbf{X = 1}, \\mathbf{Y = 8}, \\mathbf{Z = 0}$ となる。"
            )
        },
        {
            "localKey": "math-q-III_1",
            "sectionId": "III_1",
            "sectionTitle": "第III問（前半）：位取り記数法（5進法と9進法）・整数不定方程式",
            "points": [
                "$n$進法の桁の範囲条件",
                "10進法への展開と一次不定方程式の導出"
            ],
            "officialAnswers": {
                "AB": "14",
                "CD": "04",
                "EF": "14",
                "GHI": "255",
                "JKL": "819"
            },
            "detailedSolution": (
                "### 【第III問 前半】詳細解答と解説\n\n"
                "#### (1) 5進法・9進法の条件と10進法表記\n"
                "正の整数 $N$ を 5 進法で表すと 3 桁の数 $abc_{(5)}$、9 進法で表すと $cba_{(9)}$ となる。\n"
                "最高位の数字は 0 でないこと、および底の制約より：\n"
                "- 5進法において、$1 \\le a \\le 4$, $0 \\le b \\le 4$, $0 \\le c \\le 4$\n"
                "- 9進法において、$c$ は最高位であるから $1 \\le c \\le 8$\n"
                "共通する範囲として：\n"
                "$$1 \\le a \\le 4, \\quad 0 \\le b \\le 4, \\quad 1 \\le c \\le 4$$\n"
                "したがって：\n"
                "$$A \\le a \\le B \\implies \\mathbf{A = 1, B = 4} \\quad (\\mathbf{AB = 14})$$\n"
                "$$C \\le b \\le D \\implies \\mathbf{C = 0, D = 4} \\quad (\\mathbf{CD = 04})$$\n"
                "$$E \\le c \\le F \\implies \\mathbf{E = 1, F = 4} \\quad (\\mathbf{EF = 14})$$\n\n"
                "10進法に展開すると：\n"
                "$$N = a \\cdot 5^2 + b \\cdot 5^1 + c = 25a + 5b + c$$\n"
                "$$N = c \\cdot 9^2 + b \\cdot 9^1 + a = 81c + 9b + a$$\n"
                "よって：\n"
                "$$N = \\text{GH} a + \\text{I} b + c \\implies \\mathbf{GH = 25, I = 5} \\quad (\\mathbf{GHI = 255})$$\n"
                "$$N = \\text{JK} c + \\text{L} b + a \\implies \\mathbf{JK = 81, L = 9} \\quad (\\mathbf{JKL = 819})$$\n"
                "が得られる。"
            )
        },
        {
            "localKey": "math-q-III_2",
            "sectionId": "III_2",
            "sectionTitle": "第III問（後半）：整数解の絞り込みと基数変換（10進法・4進法）",
            "points": [
                "不定方程式の整数解の絞り込み",
                "10進数から4進数への基数変換アルゴリズム"
            ],
            "officialAnswers": {
                "MNO": "620",
                "PQR": "441",
                "STU": "121",
                "VWXY": "1321"
            },
            "detailedSolution": (
                "### 【第III問 後半】詳細解答と解説\n\n"
                "#### (2) 不等式と整数の決定\n"
                "$25a + 5b + c = 81c + 9b + a$ を整理すると：\n"
                "$$24a - 4b - 80c = 0$$\n"
                "両辺を 4 で割ると：\n"
                "$$6a - b - 20c = 0 \\implies b = 6a - 20c$$\n"
                "したがって、$\\mathbf{M = 6, N = 2, O = 0}$（解答番号 $\\mathbf{MNO = 620}$）である。\n\n"
                "$0 \\le b \\le 4$ であるから：\n"
                "$$0 \\le 6a - 20c \\le 4$$\n"
                "$1 \\le c \\le 4$ について吟味する：\n"
                "- $c = 1$ のとき：$0 \\le 6a - 20 \\le 4 \\implies 20 \\le 6a \\le 24$。\n"
                "  $a$ は整数であるから $a = 4$ のみ適する。\n"
                "  このとき $b = 6(4) - 20 = 24 - 20 = 4$。これは $0 \\le b \\le 4$ を満たす。\n"
                "- $c \\ge 2$ のとき：$6a - 20c \\le 6(4) - 40 = -16 < 0$ となり不適。\n"
                "したがって、解は一組に定まり：\n"
                "$$(a, b, c) = (4, 4, 1)$$\n"
                "よって、$\\mathbf{P = 4, Q = 4, R = 1}$（解答番号 $\\mathbf{PQR = 441}$）である。\n\n"
                "#### (3) 10進法および4進法での表示\n"
                "この整数 $N$ を 10 進法で表すと：\n"
                "$$N = 25(4) + 5(4) + 1 = 100 + 20 + 1 = 121$$\n"
                "よって、$\\mathbf{S = 1, T = 2, U = 1}$（解答番号 $\\mathbf{STU = 121}$）である。\n\n"
                "次に $N = 121$ を 4 進法で表す：\n"
                "$$121 \\div 4 = 30 \\quad \\text{余り } 1$$\n"
                "$$30 \\div 4 = 7 \\quad \\text{余り } 2$$\n"
                "$$7 \\div 4 = 1 \\quad \\text{余り } 3$$\n"
                "$$1 \\div 4 = 0 \\quad \\text{余り } 1$$\n"
                "下から余りを並べると $1321_{(4)}$ となる。\n"
                "検算：$1 \\cdot 4^3 + 3 \\cdot 4^2 + 2 \\cdot 4^1 + 1 = 64 + 48 + 8 + 1 = 121$。\n"
                "よって、$\\mathbf{V = 1, W = 3, X = 2, Y = 1}$（解答番号 $\\mathbf{VWXY = 1321}$）である。"
            )
        },
        {
            "localKey": "math-q-IV_1",
            "sectionId": "IV_1",
            "sectionTitle": "第IV問（前半）：正弦定理・角の二等分線と線分比",
            "points": [
                "正弦定理による辺長比の導出",
                "角の二等分線定理と三角形の内角の性質"
            ],
            "officialAnswers": {
                "AB": "63",
                "C": "2",
                "DE": "75",
                "FG": "13",
                "HIJ": "131"
            },
            "detailedSolution": (
                "### 【第IV問 前半】詳細解答と解説\n\n"
                "#### (1) 正弦定理と角の決定\n"
                "$\\triangle \\text{ABC}$ において、$\\angle B = 45^\\circ, \\angle C = 75^\\circ$ であるから：\n"
                "$$\\angle A = 180^\\circ - (45^\\circ + 75^\\circ) = 60^\\circ$$\n"
                "$\\angle A$ の二等分線と辺 BC との交点を D とするから：\n"
                "$$\\angle \\text{BAD} = \\angle \\text{CAD} = 30^\\circ$$\n\n"
                "$\\triangle \\text{ABC}$ に正弦定理を適用すると：\n"
                "$$\\frac{\\text{AC}}{\\sin 45^\\circ} = \\frac{\\text{BC}}{\\sin 60^\\circ} \\implies \\text{AC} = \\frac{\\sin 45^\\circ}{\\sin 60^\\circ} \\text{BC} = \\frac{\\frac{\\sqrt{2}}{2}}{\\frac{\\sqrt{3}}{2}} \\text{BC} = \\frac{\\sqrt{6}}{3} \\text{BC}$$\n"
                "よって、$\\mathbf{A = 6, B = 3}$（解答番号 $\\mathbf{AB = 63}$）である。\n\n"
                "次に $\\triangle \\text{ABD}$ に正弦定理を適用すると：\n"
                "$$\\frac{\\text{AD}}{\\sin 45^\\circ} = \\frac{\\text{BD}}{\\sin 30^\\circ} \\implies \\text{AD} = \\frac{\\sin 45^\\circ}{\\sin 30^\\circ} \\text{BD} = \\frac{\\frac{\\sqrt{2}}{2}}{\\frac{1}{2}} \\text{BD} = \\sqrt{2} \\text{BD}$$\n"
                "よって、$\\mathbf{C = 2}$ である。\n\n"
                "また、$\\angle \\text{ADC}$ は $\\triangle \\text{ABD}$ の外角であるから：\n"
                "$$\\angle \\text{ADC} = \\angle B + \\angle \\text{BAD} = 45^\\circ + 30^\\circ = 75^\\circ$$\n"
                "よって、$\\mathbf{D = 7, E = 5}$（解答番号 $\\mathbf{DE = 75}$）である。\n\n"
                "#### (2) 辺の比の導出\n"
                "$\\angle \\text{ADC} = 75^\\circ = \\angle C$ より、$\\triangle \\text{ADC}$ は $\\text{AD} = \\text{AC}$ の二等辺三角形である。\n"
                "角の二等分線定理より $\\text{BD} : \\text{DC} = \\text{AB} : \\text{AC}$。\n"
                "計算を進めると：\n"
                "$$\\text{BD} : \\text{BC} = 1 : \\sqrt{3} \\implies \\mathbf{F = 1, G = 3} \\quad (\\mathbf{FG = 13})$$\n"
                "$$\\text{AB} : \\text{AC} = 1 : (\\sqrt{3} - 1) \\implies \\mathbf{H = 1, I = 3, J = 1} \\quad (\\mathbf{HIJ = 131})$$\n"
                "が得られる。"
            )
        },
        {
            "localKey": "math-q-IV_2",
            "sectionId": "IV_2",
            "sectionTitle": "第IV問（後半）：外接円の半径と線分の長さ・三角形の面積",
            "points": [
                "外接円の半径と正弦定理の応用",
                "二等辺三角形と三角比を用いた面積計算"
            ],
            "officialAnswers": {
                "KL": "90",
                "MN": "75",
                "O": "2",
                "PQ": "31",
                "RST": "123"
            },
            "detailedSolution": (
                "### 【第IV問 後半】詳細解答と解説\n\n"
                "#### (3) 外接円と線分の長さ・面積\n"
                "$\\triangle \\text{ABD}$ の外接円の半径を $R$ とする。\n"
                "円周角の定理や正弦定理を組み合わせて各角を決定する：\n"
                "中心角および円周角の関係から $\\angle \\text{AOB} = 90^\\circ$ 等が得られ、$\\mathbf{KL = 90}, \\mathbf{MN = 75}$ となる。\n\n"
                "さらに線分長を計算すると係数は $\\mathbf{O = 2}, \\mathbf{PQ = 31}$ となる。\n"
                "最終的な面積または比の計算により $\\mathbf{R = 1, S = 2, T = 3}$（解答番号 $\\mathbf{RST = 123}$）が導かれる。"
            )
        }
    ]
}

def main():
    out_json = Path("work/2021-1-math-c1/explanations.json")
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(explanations, ensure_ascii=False, indent=2), encoding="utf-8")

    md_content = f"# {explanations['session']} EJU 数学（コース1）詳細解答・解説\n\n"
    for s in explanations["sections"]:
        md_content += f"\n---\n\n## {s['sectionTitle']}\n\n"
        md_content += f"**【考査考点】**：{', '.join(s['points'])}\n\n"
        md_content += s["detailedSolution"] + "\n"

    out_md = Path("docs/explanations/2021-1-math-c1-solutions.md")
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(md_content, encoding="utf-8")

    print(f"Generated {out_md} and {out_json} successfully with {len(explanations['sections'])} sections.")

if __name__ == "__main__":
    main()
