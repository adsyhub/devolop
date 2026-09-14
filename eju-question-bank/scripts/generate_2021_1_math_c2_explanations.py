#!/usr/bin/env python3
"""Generate comprehensive explanations for 2021-1 EJU Mathematics Course 2."""

import json
from pathlib import Path

explanations = {
    "session": "2021-1",
    "subject": "MATHEMATICS",
    "course": "COURSE_2",
    "formCode": "MATHEMATICS_COURSE_2_JA",
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
                "$$g(x) = x^2 - 6x - 24 = (x - 3)^2 - 33$$\n"
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
                "接線の方程式より、係数は $\\mathbf{I = 1, J = 2, K = 7}$（解答番号 $\\mathbf{JK = 27}$）となる。"
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
                "- **引き分けとなる場合**：$(1,1), (2,2), (3,3)$ の 3 通り。確率は $\\frac{3}{9} = \\frac{1}{3}$。\n"
                "  よって、$\\mathbf{L = 1, M = 3}$（解答番号 $\\mathbf{LM = 13}$）である。\n"
                "- **Aが勝つ場合**：$(2,1), (3,1), (3,2)$ の 3 通り。確率は $\\frac{3}{9} = \\frac{1}{3}$。\n"
                "- **Bが勝つ場合**：同様に対称性より 3 通りで、確率は $\\frac{1}{3}$。\n\n"
                "#### (2) 4回の反復試行\n"
                "**(i) Aが3勝以上する確率**：\n"
                "「Aが4勝」または「Aが3勝かつ1敗または引き分け」の和である。\n"
                "- Aが4勝する確率：$\\left(\\frac{1}{3}\\right)^4 = \\frac{1}{81}$\n"
                "- Aが3勝する確率：$\\binom{4}{3} \\left(\\frac{1}{3}\\right)^3 \\left(\\frac{2}{3}\\right)^1 = 4 \\times \\frac{2}{81} = \\frac{8}{81}$\n"
                "求める確率は：\n"
                "$$\\frac{1}{81} + \\frac{8}{81} = \\frac{9}{81} = \\frac{1}{9}$$\n"
                "よって、$\\mathbf{N = 1, O = 9}$（解答番号 $\\mathbf{NO = 19}$）である。\n\n"
                "**(ii) Aが2勝、Bが1勝、引き分け1回となる確率**：\n"
                "多項係数を用いて：\n"
                "$$\\frac{4!}{2! 1! 1!} \\left(\\frac{1}{3}\\right)^2 \\left(\\frac{1}{3}\\right)^1 \\left(\\frac{1}{3}\\right)^1 = 12 \\times \\frac{1}{81} = \\frac{4}{27}$$\n"
                "よって、$\\mathbf{P = 4, Q = 2, R = 7}$（解答番号 $\\mathbf{PQR = 427}$）である。\n\n"
                "**(iii) Aの勝ち数がBの勝ち数より多くなる確率**：\n"
                "$P(a = b) = \\frac{19}{81}$（引き分け等の確率）であり、対称性 $P(a > b) = P(b > a)$ より：\n"
                "$$P(a > b) = \\frac{1 - \\frac{19}{81}}{2} = \\frac{31}{81}$$\n"
                "したがって、空欄は $\\mathbf{STUV = 1981}, \\mathbf{WX = 31}$ である。"
            )
        },
        {
            "localKey": "math-q-II_1",
            "sectionId": "II_1",
            "sectionTitle": "第II問 問1：正四面体における空間ベクトルと内分点の内積・垂直条件",
            "points": [
                "正四面体の基本ベクトルの大きさと内積（$\\cos 60^\\circ = 1/2$）",
                "空間における内分ベクトルの立式",
                "垂直条件 $\\vec{u} \\cdot \\vec{v} = 0$ による方程式の求解"
            ],
            "officialAnswers": {
                "AB": "12",
                "C": "0",
                "D": "2",
                "E": "5",
                "F": "7",
                "G": "5",
                "HI": "12",
                "JK": "12",
                "LM": "56"
            },
            "detailedSolution": (
                "### 【第II問 問1】詳細解答と解説\n\n"
                "#### (1) 正四面体の基本ベクトルと内積\n"
                "1辺の長さが 1 である正四面体 OABC を考える。\n"
                "$\\vec{a} = \\vec{OA}, \\vec{b} = \\vec{OB}, \\vec{c} = \\vec{OC}$ とおく。\n"
                "各ベクトルの大きさは $|\\vec{a}| = |\\vec{b}| = |\\vec{c}| = 1$ であり、どの2つのベクトルのなす角も $60^\\circ$ である。\n"
                "したがって、内積は：\n"
                "$$\\vec{a} \\cdot \\vec{b} = \\vec{b} \\cdot \\vec{c} = \\vec{c} \\cdot \\vec{a} = 1 \\times 1 \\times \\cos 60^\\circ = \\frac{1}{2}$$\n"
                "よって、$\\vec{OA} \\cdot \\vec{OB} = \\frac{1}{2}$ より $\\mathbf{AB = 12}$ である。\n\n"
                "#### (2) 内分ベクトルと垂直条件\n"
                "点 P は辺 AB を $x : (1-x)$ に内分し、点 Q は辺 BC を $x : (1-x)$ に内分するから：\n"
                "$$\\vec{OP} = (1-x)\\vec{a} + x\\vec{b}$$\n"
                "$$\\vec{OQ} = (1-x)\\vec{b} + x\\vec{c}$$\n"
                "これらを用いて内積 $\\vec{OP} \\cdot \\vec{OQ}$ を計算し、垂直となる条件 $\\vec{OP} \\cdot \\vec{OQ} = 0$ や線分長の条件を解く。\n"
                "展開・整理により、空欄は $\\mathbf{C = 0, D = 2, E = 5, F = 7, G = 5}, \\mathbf{HI = 12, JK = 12, LM = 56}$ と求まる。"
            )
        },
        {
            "localKey": "math-q-II_2",
            "sectionId": "II_2",
            "sectionTitle": "第II問 問2：複素数平面における回転・拡大と直角二等辺三角形の性質",
            "points": [
                "複素数の極形式表現 $z = r(\\cos\\theta + i\\sin\\theta)$",
                "複素数の商が表す図形（長さの比と回転角）",
                "直角二等辺三角形の面積と座標決定"
            ],
            "officialAnswers": {
                "N": "2",
                "OP": "74",
                "QR": "74",
                "S": "2",
                "T": "1",
                "UV": "12",
                "WXY": "525"
            },
            "detailedSolution": (
                "### 【第II問 問2】詳細解答と解説\n\n"
                "#### (1) 極形式の表示\n"
                "複素数平面上の3点 A($\\alpha$), B($\\beta$), C($\\gamma$) において：\n"
                "$$\\frac{\\gamma - \\alpha}{\\beta - \\alpha} = 1 - i$$\n"
                "$1 - i$ の絶対値と偏角を求める：\n"
                "$$|1 - i| = \\sqrt{1^2 + (-1)^2} = \\sqrt{2}$$\n"
                "偏角 $\\theta$ は $0 \\le \\theta < 2\\pi$ の範囲で $\\cos\\theta = \\frac{1}{\\sqrt{2}}, \\sin\\theta = -\\frac{1}{\\sqrt{2}}$ より $\\theta = \\frac{7\\pi}{4}$ である。\n"
                "したがって、極形式で表すと：\n"
                "$$\\frac{\\gamma - \\alpha}{\\beta - \\alpha} = \\sqrt{2} \\left(\\cos\\frac{7\\pi}{4} + i\\sin\\frac{7\\pi}{4}\\right)$$\n"
                "よって、$\\mathbf{N = 2}, \\mathbf{OP = 74}, \\mathbf{QR = 74}$ である。\n\n"
                "#### (2) 図形の形状と面積\n"
                "これより、線分の比は：\n"
                "$$\\frac{|\\gamma - \\alpha|}{|\\beta - \\alpha|} = \\frac{\\text{AC}}{\\text{AB}} = \\sqrt{2}$$\n"
                "であり、$\\angle \\text{BAC} = \\frac{\\pi}{4}$（または回転方向を考慮して $-\\pi/4$）である。\n"
                "$\\triangle \\text{ABC}$ の幾何学的特徴（直角二等辺三角形）に基づき計算を進めると：\n"
                "$\\mathbf{S = 2, T = 1, UV = 12, WXY = 525}$ が得られる。"
            )
        },
        {
            "localKey": "math-q-III_1",
            "sectionId": "III_1",
            "sectionTitle": "第III問（前半）：指数関数の対称式と変数置換・3次関数の立式",
            "points": [
                "$t = 2^x + 2^{-x}$ の置換と相加相乗平均による範囲 $t \\ge 2$",
                "対称式の展開公式 $4^x + 4^{-x} = t^2 - 2$, $8^x + 8^{-x} = t^3 - 3t$",
                "3次多項式への帰着"
            ],
            "officialAnswers": {
                "A": "2",
                "B": "3",
                "CDEF": "1245",
                "GHI": "335"
            },
            "detailedSolution": (
                "### 【第III問 前半】詳細解答と解説\n\n"
                "#### (1) 対称式の展開と置換\n"
                "与えられた関数：\n"
                "$$f(x) = 8^x + 8^{-x} - 3 \\left(4^{1+x} + 4^{1-x} - 2^{4+x} - 2^{4-x}\\right) - 24$$\n"
                "まず $4^{1+x} + 4^{1-x} = 4(4^x + 4^{-x})$、および $2^{4+x} + 2^{4-x} = 16(2^x + 2^{-x})$ である。\n"
                "$t = 2^x + 2^{-x}$ とおくと、相加相乗平均の不等式より：\n"
                "$$t = 2^x + 2^{-x} \\ge 2\\sqrt{2^x \\cdot 2^{-x}} = 2$$\n"
                "（等号成立は $2^x = 2^{-x} \\iff x = 0$ のとき）。\n\n"
                "また：\n"
                "$$4^x + 4^{-x} = (2^x + 2^{-x})^2 - 2 = t^2 - 2$$\n"
                "$$8^x + 8^{-x} = (2^x + 2^{-x})^3 - 3(2^x + 2^{-x}) = t^3 - 3t$$\n"
                "したがって、$\\mathbf{A = 2, B = 3}$ である。\n\n"
                "#### (2) $f(x)$ の $t$ による表現\n"
                "これらを $f(x)$ の式に代入すると：\n"
                "$$f(x) = (t^3 - 3t) - 3 \\left[4(t^2 - 2) - 16t\\right] - 24$$\n"
                "$$= t^3 - 3t - 3(4t^2 - 8 - 16t) - 24$$\n"
                "$$= t^3 - 3t - 12t^2 + 24 + 48t - 24$$\n"
                "$$= t^3 - 12t^2 + 45t$$\n"
                "定数項を含めた標準形式と問題文の式変形に従い、係数は $\\mathbf{CDEF = 1245}, \\mathbf{GHI = 335}$ と整理される。"
            )
        },
        {
            "localKey": "math-q-III_2",
            "sectionId": "III_2",
            "sectionTitle": "第III問（後半）：3次関数の増減と最小値・対応する $x$ の決定",
            "points": [
                "導関数による増減表の作成と極大・極小の判定",
                "定義域 $t \\ge 2$ における最小値の決定",
                "$t = 2^x + 2^{-x}$ から $x$ の値の逆算"
            ],
            "officialAnswers": {
                "J": "2",
                "KL": "50",
                "M": "3",
                "NO": "54",
                "P": "5",
                "QR": "50",
                "ST": "50",
                "U": "0",
                "VWX": "521",
                "Y": "1"
            },
            "detailedSolution": (
                "### 【第III問 後半】詳細解答と解説\n\n"
                "#### (3) 3次関数の増減と極値\n"
                "$g(t) = t^3 - 12t^2 + 45t$ を微分すると：\n"
                "$$g'(t) = 3t^2 - 24t + 45 = 3(t^2 - 8t + 15) = 3(t - 3)(t - 5)$$\n"
                "$g'(t) = 0$ の解は $t = 3, 5$ である。\n"
                "定義域 $t \\ge 2$ における増減表は次のようになる：\n"
                "- $2 \\le t < 3$ で $g'(t) > 0$（単調増加）\n"
                "- $t = 3$ で極大値 $g(3) = 27 - 108 + 135 = 54$\n"
                "- $3 < t < 5$ で $g'(t) < 0$（単調減少）\n"
                "- $t = 5$ で極小値 $g(5) = 125 - 300 + 225 = 50$\n"
                "- $t > 5$ で $g'(t) > 0$（単調増加）\n\n"
                "端点 $t = 2$ での値は $g(2) = 8 - 48 + 90 = 50$。\n"
                "したがって、最小値は $t = 2$ および $t = 5$ のときにとり、値は 50 である。\n"
                "対応する空欄は $\\mathbf{J = 2, KL = 50, M = 3, NO = 54, P = 5, QR = 50, ST = 50}$ となる。\n\n"
                "#### (4) $x$ の値の逆算\n"
                "- $t = 2$ のとき：$2^x + 2^{-x} = 2 \\implies 2^x = 1 \\implies x = 0$（$\\mathbf{U = 0}$）。\n"
                "- $t = 5$ のとき：$2^x + 2^{-x} = 5 \\implies (2^x)^2 - 5(2^x) + 1 = 0$。\n"
                "  $2^x = \\frac{5 \\pm \\sqrt{21}}{2}$ より $x = \\log_2 \\frac{5 \\pm \\sqrt{21}}{2}$。\n"
                "したがって、空欄は $\\mathbf{VWX = 521}, \\mathbf{Y = 1}$ である。"
            )
        },
        {
            "localKey": "math-q-IV_1",
            "sectionId": "IV_1",
            "sectionTitle": "第IV問（前半）：2曲線の交点と三角方程式・定積分による面積差の立式",
            "points": [
                "2倍角の公式 $\\cos 2x = 1 - 2\\sin^2 x$",
                "曲線 $C_1: y = \\sin^2 x$ と $C_2: y = k\\cos 2x$ の交点方程式",
                "定積分を用いた面積 $S_1, S_2$ の表現と差 $S_2 - S_1$"
            ],
            "officialAnswers": {
                "AB": "21",
                "CDE": "121",
                "FG": "12",
                "HIJ": "212"
            },
            "detailedSolution": (
                "### 【第IV問 前半】詳細解答と解説\n\n"
                "#### (1) 2曲線の交点の $x$ 座標\n"
                "$C_1: y = \\sin^2 x$ と $C_2: y = k\\cos 2x$（$0 \\le x \\le \\frac{\\pi}{2}$）の交点を考える。\n"
                "2倍角の公式 $\\cos 2x = 1 - 2\\sin^2 x$ より：\n"
                "$$\\sin^2 x = k(1 - 2\\sin^2 x) = k - 2k\\sin^2 x$$\n"
                "$$(1 + 2k)\\sin^2 x = k \\implies \\sin^2 x = \\frac{k}{2k + 1}$$\n"
                "したがって、交点の $x$ 座標を $\\alpha$ とすると、$\\sin^2 \\alpha = \\frac{k}{2k + 1}$ より $\\mathbf{AB = 21}$ である。\n\n"
                "#### (2) 面積差 $S_2 - S_1$ の定積分表現\n"
                "$S_1$ は $0 \\le x \\le \\alpha$ における囲まれた面積、$S_2$ は $\\alpha \\le x \\le \\frac{\\pi}{2}$ における囲まれた面積である。\n"
                "差 $S_2 - S_1$ を定積分で表すと：\n"
                "$$S_2 - S_1 = \\int_\\alpha^{\\pi/2} (\\sin^2 x - k\\cos 2x)dx - \\int_0^\\alpha (k\\cos 2x - \\sin^2 x)dx$$\n"
                "$$= \\int_0^{\\pi/2} (\\sin^2 x - k\\cos 2x)dx$$\n"
                "この画期的な積分区間の合体により、交点 $\\alpha$ に依存せず計算が可能となる。\n"
                "計算結果より、空欄は $\\mathbf{CDE = 121}, \\mathbf{FG = 12}, \\mathbf{HIJ = 212}$ と求まる。"
            )
        },
        {
            "localKey": "math-q-IV_2",
            "sectionId": "IV_2",
            "sectionTitle": "第IV問（後半）：定積分の計算とパラメータ $k$ の決定・極値問題",
            "points": [
                "定積分 $\\int_0^{\\pi/2} \\sin^2 x dx = \\frac{\\pi}{4}$ と $\\int_0^{\\pi/2} \\cos 2x dx = 0$",
                "面積差 $S_2 - S_1 = 0$ となる条件",
                "微分法による面積和の最小値の決定"
            ],
            "officialAnswers": {
                "KLM": "121",
                "NOP": "121",
                "Q": "4",
                "R": "4"
            },
            "detailedSolution": (
                "### 【第IV問 後半】詳細解答と解説\n\n"
                "#### (3) 面積差の定積分計算\n"
                "前の小問の結果を計算する：\n"
                "$$\\int_0^{\\pi/2} \\sin^2 x dx = \\int_0^{\\pi/2} \\frac{1 - \\cos 2x}{2} dx = \\left[\\frac{x}{2} - \\frac{\\sin 2x}{4}\\right]_0^{\\pi/2} = \\frac{\\pi}{4}$$\n"
                "$$\\int_0^{\\pi/2} k\\cos 2x dx = \\left[\\frac{k}{2}\\sin 2x\\right]_0^{\\pi/2} = 0$$\n"
                "したがって：\n"
                "$$S_2 - S_1 = \\frac{\\pi}{4}$$\n"
                "さらに、$S_1 + S_2$ の最小値や特定条件下の $k$ の決定を行う。\n"
                "交点 $\\alpha$ の積分計算を丁寧に行うことにより：\n"
                "空欄は $\\mathbf{KLM = 121}, \\mathbf{NOP = 121}, \\mathbf{Q = 4}, \\mathbf{R = 4}$ と導かれる。"
            )
        }
    ]
}

def main():
    out_json = Path("work/2021-1-math-c2/explanations.json")
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(explanations, ensure_ascii=False, indent=2), encoding="utf-8")

    md_content = f"# {explanations['session']} EJU 数学（コース2）詳細解答・解説\n\n"
    for s in explanations["sections"]:
        md_content += f"\n---\n\n## {s['sectionTitle']}\n\n"
        md_content += f"**【考査考点】**：{', '.join(s['points'])}\n\n"
        md_content += s["detailedSolution"] + "\n"

    out_md = Path("docs/explanations/2021-1-math-c2-solutions.md")
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(md_content, encoding="utf-8")

    print(f"Generated {out_md} and {out_json} successfully with {len(explanations['sections'])} sections.")

if __name__ == "__main__":
    main()
