#!/usr/bin/env python3
"""Generate comprehensive explanations for 2023-2 EJU Mathematics Course 2."""

import json
from pathlib import Path

# Load Math 1 solutions for Question I
math_c1 = json.loads(Path("work/2023-2-math-c1/explanations.json").read_text(encoding="utf-8"))
q1_1 = math_c1["sections"][0]
q1_2 = math_c1["sections"][1]

explanations = {
    "session": "2023-2",
    "subject": "MATHEMATICS",
    "course": "COURSE_2",
    "formCode": "MATHEMATICS_COURSE_2_JA",
    "sections": [
        q1_1,
        q1_2,
        {
            "sectionId": "II_1",
            "sectionTitle": "第II問 問1：長方形内のベクトル演算・直交条件と内積・余弦の決定",
            "points": ["平面ベクトルの線分比と内分点公式", "直交条件（内積＝0）による未知数の決定", "ベクトルの内積と成す角の余弦（cos θ）"],
            "officialAnswers": {
                "AB": "12",
                "C": "1",
                "D": "0",
                "EF": "62",
                "G": "9",
                "H": "0",
                "IJ": "53",
                "KLM": "539"
            },
            "detailedSolution": (
                "### 【第II問 問1】詳細解答と解説\n\n"
                "#### (1) 線分比 $AG : GC$ とベクトル $\\overrightarrow{BG}$ の表現\n"
                "長方形 $ABCD$ において、$\\overrightarrow{AB} = \\vec{a}, \\overrightarrow{AD} = \\vec{b}$ とする。\n"
                "長方形であるから $\\vec{a} \\perp \\vec{b}$、すなわち $\\vec{a} \\cdot \\vec{b} = 0$ である。\n"
                "また、$BC = |\\vec{b}| = \\sqrt{3}$ である。\n"
                "点 $E$ は辺 $AB$ を $1:5$ に内分するので：\n"
                "$$\\overrightarrow{AE} = \\frac{1}{6}\\vec{a}$$\n"
                "点 $F$ は辺 $CD$ を $1:2$ に内分する。\n"
                "$C$ の位置ベクトルは $\\vec{a} + \\vec{b}$、$D$ の位置ベクトルは $\\vec{b}$ であるから：\n"
                "$$\\overrightarrow{AF} = \\overrightarrow{AC} + \\frac{1}{3}(\\overrightarrow{AD} - \\overrightarrow{AC}) = (\\vec{a} + \\vec{b}) + \\frac{1}{3}(\\vec{b} - (\\vec{a} + \\vec{b})) = \\frac{2}{3}\\vec{a} + \\vec{b}$$\n\n"
                "点 $G$ は対角線 $AC$ と線分 $EF$ の交点である。\n"
                "$G$ は $AC$ 上にあるので、実数 $k$ を用いて $\\overrightarrow{AG} = k\\overrightarrow{AC} = k(\\vec{a} + \\vec{b})$ と表せる。\n"
                "また、$G$ は線分 $EF$ 上にあるので、実数 $s$ を用いて：\n"
                "$$\\overrightarrow{AG} = (1 - s)\\overrightarrow{AE} + s\\overrightarrow{AF} = (1 - s)\\left(\\frac{1}{6}\\vec{a}\\right) + s\\left(\\frac{2}{3}\\vec{a} + \\vec{b}\\right) = \\left(\\frac{1}{6} + \\frac{1}{2}s\\right)\\vec{a} + s\\vec{b}$$\n"
                "$\\vec{a}$ と $\\vec{b}$ は 1 次独立であるから、各成分を比較して：\n"
                "$$s = k, \\quad k = \\frac{1}{6} + \\frac{1}{2}k \\implies \\frac{1}{2}k = \\frac{1}{6} \\implies k = \\frac{1}{3}$$\n"
                "したがって、$\\overrightarrow{AG} = \\frac{1}{3}\\overrightarrow{AC}$ であるから：\n"
                "$$AG : GC = 1 : 2$$\n"
                "よって、$\\mathbf{A = 1, B = 2}$（解答番号 $\\mathbf{AB = 12}$）。\n\n"
                "これより、$\\overrightarrow{BG}$ を $\\vec{a}, \\vec{b}$ で表すと：\n"
                "$$\\overrightarrow{BG} = \\overrightarrow{AG} - \\overrightarrow{AB} = \\frac{1}{3}(\\vec{a} + \\vec{b}) - \\vec{a} = \\frac{1}{3}(-2\\vec{a} + \\vec{b})$$\n"
                "選択肢の形式と比較すると、$\\textcircled{1}$「$\\frac{1}{3}(-2\\vec{a} + \\vec{b})$」に一致する。\n"
                "よって、$\\mathbf{C = 1}$。\n\n"
                "#### (2) 直交条件と辺 $AB$ の長さ\n"
                "線分 $BG$ と $AC$ は直交しているため：\n"
                "$$\\overrightarrow{BG} \\cdot \\overrightarrow{AC} = 0$$\n"
                "よって、$\\mathbf{D = 0}$。\n\n"
                "この内積を計算すると：\n"
                "$$\\overrightarrow{BG} \\cdot \\overrightarrow{AC} = \\frac{1}{3}(-2\\vec{a} + \\vec{b}) \\cdot (\\vec{a} + \\vec{b}) = \\frac{1}{3}\\left(-2|\\vec{a}|^2 + |\\vec{b}|^2 - \\vec{a} \\cdot \\vec{b}\\right)$$\n"
                "$\\vec{a} \\cdot \\vec{b} = 0$ かつ $|\\vec{b}| = \\sqrt{3} \\implies |\\vec{b}|^2 = 3$ であるから：\n"
                "$$\\frac{1}{3}\\left(-2|\\vec{a}|^2 + 3\\right) = 0 \\implies 2|\\vec{a}|^2 = 3 \\implies |\\vec{a}|^2 = \\frac{3}{2}$$\n"
                "したがって、$AB = |\\vec{a}| = \\sqrt{\\frac{3}{2}} = \\frac{\\sqrt{6}}{2}$ である。\n"
                "問題文の形式 $AB = \\frac{\\sqrt{\\text{E}}}{\\text{F}}$ より：\n"
                "$$\\mathbf{E = 6, F = 2} \\implies \\mathbf{EF = 62}$$\n\n"
                "#### (3) $\\overrightarrow{GC}, \\overrightarrow{GF}$ の表示と $\\cos \\angle CGF$ の決定\n"
                "点 $G$ は $AC$ を $1:2$ に内分するので：\n"
                "$$\\overrightarrow{GC} = \\frac{2}{3}\\overrightarrow{AC} = \\frac{2}{3}(\\vec{a} + \\vec{b})$$\n"
                "選択肢 $\\textcircled{9}$「$\\frac{2}{3}(\\vec{a} + \\vec{b})$」より、$\\mathbf{G = 9}$。\n\n"
                "また、$\\overrightarrow{GF} = \\overrightarrow{AF} - \\overrightarrow{AG}$ より：\n"
                "$$\\overrightarrow{GF} = \\left(\\frac{2}{3}\\vec{a} + \\vec{b}\\right) - \\frac{1}{3}(\\vec{a} + \\vec{b}) = \\frac{1}{3}\\vec{a} + \\frac{2}{3}\\vec{b} = \\frac{1}{3}(\\vec{a} + 2\\vec{b})$$\n"
                "選択肢 $\\textcircled{0}$「$\\frac{1}{3}(\\vec{a} + 2\\vec{b})$」より、$\\mathbf{H = 0}$。\n\n"
                "内積 $\\overrightarrow{GC} \\cdot \\overrightarrow{GF}$ を計算する：\n"
                "$$\\overrightarrow{GC} \\cdot \\overrightarrow{GF} = \\frac{2}{3}(\\vec{a} + \\vec{b}) \\cdot \\frac{1}{3}(\\vec{a} + 2\\vec{b}) = \\frac{2}{9}\\left(|\\vec{a}|^2 + 2|\\vec{b}|^2 + 3\\vec{a} \\cdot \\vec{b}\\right)$$\n"
                "$|\\vec{a}|^2 = \\frac{3}{2}, |\\vec{b}|^2 = 3, \\vec{a} \\cdot \\vec{b} = 0$ を代入すると：\n"
                "$$\\overrightarrow{GC} \\cdot \\overrightarrow{GF} = \\frac{2}{9}\\left(\\frac{3}{2} + 6\\right) = \\frac{2}{9} \\times \\frac{15}{2} = \\frac{5}{3}$$\n"
                "問題文の形式 $\\frac{\\text{I}}{\\text{J}}$ より：\n"
                "$$\\mathbf{I = 5, J = 3} \\implies \\mathbf{IJ = 53}$$\n\n"
                "各ベクトルの大きさを計算する：\n"
                "$$|\\overrightarrow{GC}|^2 = \\frac{4}{9}(|\\vec{a}|^2 + |\\vec{b}|^2) = \\frac{4}{9}\\left(\\frac{3}{2} + 3\\right) = \\frac{4}{9} \\times \\frac{9}{2} = 2 \\implies |\\overrightarrow{GC}| = \\sqrt{2}$$\n"
                "$$|\\overrightarrow{GF}|^2 = \\frac{1}{9}(|\\vec{a}|^2 + 4|\\vec{b}|^2) = \\frac{1}{9}\\left(\\frac{3}{2} + 12\\right) = \\frac{1}{9} \\times \\frac{27}{2} = \\frac{3}{2} \\implies |\\overrightarrow{GF}| = \\sqrt{\\frac{3}{2}}$$\n"
                "したがって：\n"
                "$$\\cos \\theta = \\frac{\\overrightarrow{GC} \\cdot \\overrightarrow{GF}}{|\\overrightarrow{GC}| |\\overrightarrow{GF}|} = \\frac{\\frac{5}{3}}{\\sqrt{2} \\times \\sqrt{\\frac{3}{2}}} = \\frac{\\frac{5}{3}}{\\sqrt{3}} = \\frac{5}{3\\sqrt{3}} = \\frac{5\\sqrt{3}}{9}$$\n"
                "問題文の形式 $\\frac{\\text{K}\\sqrt{\\text{L}}}{\\text{M}}$ より：\n"
                "$$\\mathbf{K = 5, L = 3, M = 9} \\implies \\mathbf{KLM = 539}$$"
            )
        },
        {
            "sectionId": "II_2",
            "sectionTitle": "第II問 問2：円の方程式・直線に関する線対称変換・点と直線の距離と接線",
            "points": ["円の標準形と中心・半径", "直線に関する点の対称移動（垂直条件と中点条件）", "点と直線の距離公式による円の接する条件"],
            "officialAnswers": {
                "NO": "21",
                "PQ": "25",
                "RS": "95",
                "TUVW": "3445",
                "X": "2"
            },
            "detailedSolution": (
                "### 【第II問 問2】詳細解答と解説\n\n"
                "#### (1) 円 $C$ の中心と半径\n"
                "与えられた円の方程式は：\n"
                "$$C: x^2 + y^2 - 4x - 2y + 5 - r^2 = 0$$\n"
                "平方完成を行うと：\n"
                "$$(x^2 - 4x + 4) + (y^2 - 2y + 1) - 4 - 1 + 5 - r^2 = 0$$\n"
                "$$(x - 2)^2 + (y - 1)^2 = r^2$$\n"
                "したがって、円 $C$ の中心は **$(2, 1)$**、半径は $r$ である。\n"
                "よって、$\\mathbf{N = 2, O = 1} \\implies \\mathbf{NO = 21}$。\n\n"
                "#### (2) 直線 $\\ell$ に関して対称な円 $C'$ の中心座標\n"
                "円 $C'$ は円 $C$ を直線 $\\ell: y = 2x - 1 \\iff 2x - y - 1 = 0$ に関して対称移動した円である。\n"
                "円 $C$ の中心 $(2, 1)$ の直線 $\\ell$ に関する対称点を $(a, b)$ とする。\n"
                "1. **垂直条件**：中心を結ぶ直線の傾きは $\\ell$ の傾き $2$ と直交するため $-\\frac{1}{2}$ である：\n"
                "   $$\\frac{b - 1}{a - 2} = -\\frac{1}{2} \\implies 2(b - 1) = -(a - 2) \\implies a + 2b - 4 = 0$$\n"
                "2. **中点条件**：線分の中点 $\\left(\\frac{a + 2}{2}, \\frac{b + 1}{2}\\right)$ が直線 $\\ell$ 上にある：\n"
                "   $$2\\left(\\frac{a + 2}{2}\\right) - \\left(\\frac{b + 1}{2}\\right) - 1 = 0$$\n"
                "   $$2(a + 2) - (b + 1) - 2 = 0 \\implies 2a - b + 1 = 0 \\implies b = 2a + 1$$\n"
                "垂直条件の式に代入すると：\n"
                "$$a + 2(2a + 1) - 4 = 0 \\implies 5a - 2 = 0 \\implies a = \\frac{2}{5}$$\n"
                "$$b = 2\\left(\\frac{2}{5}\\right) + 1 = \\frac{9}{5}$$\n"
                "したがって、対称円 $C'$ の中心は $\\left(\\frac{2}{5}, \\frac{9}{5}\\right)$ である。\n"
                "問題文の形式 $a = \\frac{\\text{P}}{\\text{Q}}, b = \\frac{\\text{R}}{\\text{S}}$ より：\n"
                "$$\\mathbf{P = 2, Q = 5, R = 9, S = 5} \\implies \\mathbf{PQ = 25, RS = 95}$$\n\n"
                "#### (3) 円 $C'$ が直線 $m$ に接する条件と半径 $r$\n"
                "直線 $m$ の方程式は $y = \\frac{3}{4}x - 1 \\iff 3x - 4y - 4 = 0$ である。\n"
                "対称移動しても円の半径は不変であるから、$C'$ の半径も $r$ である。\n"
                "円 $C'$ が直線 $m$ に接するとき、中心 $(a, b)$ と直線 $m$ との距離が半径 $r$ に等しい：\n"
                "$$r = \\frac{|3a - 4b - 4|}{\\sqrt{3^2 + (-4)^2}} = \\frac{|3a - 4b - 4|}{\\sqrt{25}} = \\frac{|3a - 4b - 4|}{5}$$\n"
                "問題文の形式 $\\frac{|\\text{T}a - \\text{U}b - \\text{V}|}{\\text{W}}$ と比較して：\n"
                "$$\\mathbf{T = 3, U = 4, V = 4, W = 5} \\implies \\mathbf{TUVW = 3445}$$\n\n"
                "求めた $a = \\frac{2}{5}, b = \\frac{9}{5}$ を代入すると：\n"
                "$$3a - 4b - 4 = 3\\left(\\frac{2}{5}\\right) - 4\\left(\\frac{9}{5}\\right) - 4 = \\frac{6 - 36 - 20}{5} = \\frac{-50}{5} = -10$$\n"
                "したがって：\n"
                "$$r = \\frac{|-10|}{5} = \\frac{10}{5} = 2$$\n"
                "よって、$\\mathbf{X = 2}$。"
            )
        },
        {
            "sectionId": "III",
            "sectionTitle": "第III問：3次関数の接線の方程式・共有点・平行接線・面積",
            "points": ["3次関数の微分係数と接線の方程式", "3次方程式の重解と因数定理（共有点の決定）", "放物線・3次曲線と接線が囲む面積公式（1/12公式）"],
            "officialAnswers": {
                "CD": "38",
                "EFG": "241",
                "HIJ": "-53",
                "KLM": "2-7",
                "NO": "53",
                "PQRS": "7727",
                "TUV": "152",
                "WXY": "112"
            },
            "detailedSolution": (
                "### 【第III問】詳細解答と解説\n\n"
                "#### (1) 任意の点における接線と点 $A$ における接線 $l$\n"
                "関数 $f(x) = x^3 - 4x^2 + 1$ に対し、導関数は：\n"
                "$$f'(x) = 3x^2 - 8x$$\n"
                "点 $(t, f(t))$ における接線の傾きは $f'(t) = 3t^2 - 8t$ である。\n"
                "問題文の形式 $Ct^2 - Dt$ より：\n"
                "$$\\mathbf{C = 3, D = 8} \\implies \\mathbf{CD = 38}$$\n\n"
                "接線の方程式は：\n"
                "$$y - f(t) = f'(t)(x - t) \\implies y = (3t^2 - 8t)x - t(3t^2 - 8t) + (t^3 - 4t^2 + 1)$$\n"
                "$$y = (3t^2 - 8t)x - 2t^3 + 4t^2 + 1$$\n"
                "したがって、$y$ 切片は $-2t^3 + 4t^2 + 1$ である。\n"
                "問題文の形式 $-Et^3 + Ft^2 + G$ より：\n"
                "$$\\mathbf{E = 2, F = 4, G = 1} \\implies \\mathbf{EFG = 241}$$\n\n"
                "点 $A(1, a)$ は $C$ 上の点であるから、$a = f(1) = 1 - 4 + 1 = -2$ である。\n"
                "接線 $l$ は $t = 1$ における接線であるから：\n"
                "傾き: $3(1)^2 - 8(1) = -5$\n"
                "$y$ 切片: $-2(1)^3 + 4(1)^2 + 1 = 3$\n"
                "したがって、接線 $l$ の方程式は：\n"
                "$$y = -5x + 3$$\n"
                "問題文の形式 $y = HI x + J$ より：\n"
                "$$\\mathbf{HI = -5, J = 3} \\implies \\mathbf{HIJ = -53}$$\n\n"
                "#### (2) $C$ と $l$ の共有点 $B$\n"
                "曲線 $C$ と直線 $l$ の共有点の $x$ 座標は連立方程式を満たす：\n"
                "$$x^3 - 4x^2 + 1 = -5x + 3 \\iff x^3 - 4x^2 + 5x - 2 = 0$$\n"
                "$x = 1$ で接することから、左辺は必ず $(x - 1)^2$ を因数にもつ：\n"
                "$$x^3 - 4x^2 + 5x - 2 = (x - 1)^2 (x - 2) = 0$$\n"
                "したがって、$A$ と異なる共有点 $B$ の $x$ 座標は $x = 2$ である。\n"
                "$y$ 座標は $l$ に代入して $y = -5(2) + 3 = -7$。\n"
                "よって、点 $B$ の座標は **$(2, -7)$** である。\n"
                "問題文の形式 $\\boxed{K, LM}$ より：\n"
                "$$\\mathbf{K = 2, LM = -7} \\implies \\mathbf{KLM = 2-7}$$\n\n"
                "#### (3) $l$ に平行な接線 $m$\n"
                "直線 $m$ は $l$ と平行であるから、傾きが $-5$ で接点の $x$ 座標を $t$ とすると：\n"
                "$$3t^2 - 8t = -5 \\iff 3t^2 - 8t + 5 = 0 \\iff (t - 1)(3t - 5) = 0$$\n"
                "$l$ とは異なる接線であるから $t \\neq 1$ より：\n"
                "$$t = \\frac{5}{3}$$\n"
                "問題文の形式 $\\frac{\\text{N}}{\\text{O}}$ より：\n"
                "$$\\mathbf{N = 5, O = 3} \\implies \\mathbf{NO = 53}$$\n\n"
                "$m$ の $y$ 切片は、$t = \\frac{5}{3}$ を切片の式 $-2t^3 + 4t^2 + 1$ に代入して：\n"
                "$$-2\\left(\\frac{5}{3}\\right)^3 + 4\\left(\\frac{5}{3}\\right)^2 + 1 = -2\\left(\\frac{125}{27}\\right) + 4\\left(\\frac{25}{9}\\right) + 1 = -\\frac{250}{27} + \\frac{300}{27} + \\frac{27}{27} = \\frac{77}{27}$$\n"
                "したがって、直線 $m$ の方程式は $y = -5x + \\frac{77}{27}$ である。\n"
                "問題文の形式 $y = HI x + \\frac{\\text{PQ}}{\\text{RS}}$ より：\n"
                "$$\\mathbf{PQ = 77, RS = 27} \\implies \\mathbf{PQRS = 7727}$$\n\n"
                "#### (4) $y$ 切片が $l$ と同じ（切片が 3）である他の 2 本の接線\n"
                "接線の $y$ 切片が 3 となる接点の $x$ 座標 $t$ の方程式は：\n"
                "$$-2t^3 + 4t^2 + 1 = 3 \\iff 2t^3 - 4t^2 + 2 = 0 \\iff t^3 - 2t^2 + 1 = 0$$\n"
                "$l$ の接点 $t = 1$ が解であるから $(t - 1)$ で因数分解できる：\n"
                "$$(t - 1)(t^2 - t - 1) = 0$$\n"
                "他の 2 接点は $t^2 - t - 1 = 0$ の 2 根である：\n"
                "$$t = \\frac{1 \\pm \\sqrt{1^2 - 4(1)(-1)}}{2} = \\frac{1 \\pm \\sqrt{5}}{2}$$\n"
                "問題文の形式 $\\frac{\\text{T} - \\sqrt{\\text{U}}}{\\text{V}}$ と $\\frac{\\text{T} + \\sqrt{\\text{U}}}{\\text{V}}$ より：\n"
                "$$\\mathbf{T = 1, U = 5, V = 2} \\implies \\mathbf{TUV = 152}$$\n\n"
                "#### (5) $C$ と $l$ で囲まれた部分の面積\n"
                "区間 $[1, 2]$ において、直線 $l$ は曲線 $C$ の上側にある。\n"
                "囲まれた部分の面積 $S$ は：\n"
                "$$S = \\int_1^2 \\left[(-5x + 3) - (x^3 - 4x^2 + 1)\\right] dx = \\int_1^2 -(x - 1)^2 (x - 2) \\, dx$$\n"
                "ここで $x - 1 = u$ と置換すると、$dx = du$、積分区間は $0 \\le u \\le 1$ となり：\n"
                "$$S = \\int_0^1 -u^2 (u - 1) \\, du = \\int_0^1 (u^2 - u^3) \\, du = \\left[\\frac{u^3}{3} - \\frac{u^4}{4}\\right]_0^1 = \\frac{1}{3} - \\frac{1}{4} = \\frac{1}{12}$$\n"
                "問題文の形式 $\\frac{\\text{W}}{\\text{XY}}$ より：\n"
                "$$\\mathbf{W = 1, XY = 12} \\implies \\mathbf{WXY = 112}$$\n\n"
                "**【解法テクニック・面積の 1/12 公式】**\n"
                "- 3次曲線と接線が囲む面積は、接点 $\\alpha$、交点 $\\beta$ と最高次の係数 $a$ を用いて $S = \\frac{|a|}{12}(\\beta - \\alpha)^4$ で瞬時に計算可能です。本問では $a = 1, \\alpha = 1, \\beta = 2$ であるから $S = \\frac{1}{12}(2 - 1)^4 = \\frac{1}{12}$ と一瞬で検算できます。"
            )
        },
        {
            "sectionId": "IV",
            "sectionTitle": "第IV問：絶対値付き指数関数の定積分・微分と増減表・最小値の決定",
            "points": ["絶対値を含む関数の場合分け", "積分区間と折れ曲がり点の相対位置による関数の区分", "微分積分の基本定理による導関数の計算と増減・極小値"],
            "officialAnswers": {
                "A": "2",
                "BC": "21",
                "DE": "21",
                "F": "1",
                "G": "1",
                "HIJK": "4641",
                "LM": "41",
                "NO": "41",
                "P": "1",
                "Q": "0",
                "RS": "12",
                "T": "1",
                "U": "0",
                "VW": "41"
            },
            "detailedSolution": (
                "### 【第IV問】詳細解答と解説\n\n"
                "#### (1) 絶対値の解除と場合分けの基準\n"
                "被積分関数は $|e^x - 2|$ である。\n"
                "$e^x - 2 = 0 \\iff e^x = 2 \\iff x = \\log 2$ であるから：\n"
                "$$|e^x - 2| = \\begin{cases} e^x - 2 & (x \\ge \\log 2) \\\\ 2 - e^x & (x \\le \\log 2) \\end{cases}$$\n"
                "問題文の形式より、$\\mathbf{A = 2}$。\n\n"
                "積分区間は $[a, a + 1]$ であり、その区間幅は 1 である。\n"
                "折れ曲がり点 $x = \\log 2$ と区間 $[a, a + 1]$ の位置関係により、以下の 3 つの場合に分けられる：\n"
                "- (i) $a + 1 \\le \\log 2 \\iff a \\le \\log 2 - 1$（区間全体が $\\log 2$ の左側）\n"
                "- (ii) $a \\le \\log 2 \\le a + 1 \\iff \\log 2 - 1 \\le a \\le \\log 2$（区間内に $\\log 2$ を含む）\n"
                "- (iii) $a \\ge \\log 2$（区間全体が $\\log 2$ の右側）\n\n"
                "#### (2) 各区間における関数の表示と導関数\n\n"
                "**(i) $a < \\log 2 - 1$ のとき**\n"
                "区間内のすべての $x$ で $e^x - 2 \\le 0$ であるから、被積分関数は $2 - e^x$ である。\n"
                "問題文の形式 $\\log \\text{B} - \\text{C}$ より：$\\mathbf{B = 2, C = 1} \\implies \\mathbf{BC = 21}$。\n\n"
                "$$f(a) = \\int_a^{a+1} (2 - e^x) \\, dx = \\left[2x - e^x\\right]_a^{a+1} = \\{2(a + 1) - e^{a+1}\\} - (2a - e^a) = 2 - e^a(e - 1) = 2 + e^a(1 - e)$$\n"
                "問題文の形式 $D + e^a(E - e)$ より：$\\mathbf{D = 2, E = 1} \\implies \\mathbf{DE = 21}$。\n\n"
                "$a$ で微分すると：\n"
                "$$f'(a) = e^a(1 - e)$$\n"
                "問題文の形式 $e^a(F - e)$ より：$\\mathbf{F = 1}$。\n"
                "$e \\approx 2.718 > 1$ より $1 - e < 0$、かつ $e^a > 0$ であるから、$f'(a) < 0$ が恒等的に成り立つ。\n"
                "したがって、$f(a)$ は **単調減少** である。\n"
                "選択肢 $\\textcircled{1}$「減少」より、$\\mathbf{G = 1}$。\n\n"
                "**(ii) $\\log 2 - 1 \\le a < \\log 2$ のとき**\n"
                "区間内に折れ曲がり点 $x = \\log 2$ を含むため、積分を 2 つに分割する：\n"
                "$$f(a) = \\int_a^{\\log 2} (2 - e^x) \\, dx + \\int_{\\log 2}^{a+1} (e^x - 2) \\, dx$$\n"
                "各部分を計算すると：\n"
                "$$\\int_a^{\\log 2} (2 - e^x) \\, dx = \\left[2x - e^x\\right]_a^{\\log 2} = (2\\log 2 - 2) - (2a - e^a) = 2\\log 2 - 2 - 2a + e^a$$\n"
                "$$\\int_{\\log 2}^{a+1} (e^x - 2) \\, dx = \\left[e^x - 2x\\right]_{\\log 2}^{a+1} = \\{e^{a+1} - 2(a + 1)\\} - (2 - 2\\log 2) = e \\cdot e^a - 2a - 4 + 2\\log 2$$\n"
                "両者を足し合わせると：\n"
                "$$f(a) = 4\\log 2 - 6 - 4a + e^a(e + 1)$$\n"
                "問題文の形式 $H\\log 2 - I - Ja + e^a(e + K)$ と比較して：\n"
                "$$\\mathbf{H = 4, I = 6, J = 4, K = 1} \\implies \\mathbf{HIJK = 4641}$$\n\n"
                "$a$ で微分すると：\n"
                "$$f'(a) = -4 + e^a(e + 1)$$\n"
                "問題文の形式 $-L + e^a(e + M)$ より：$\\mathbf{L = 4, M = 1} \\implies \\mathbf{LM = 41}$。\n\n"
                "$f'(a) = 0$ となる $a$ を求めると：\n"
                "$$e^a(e + 1) = 4 \\iff e^a = \\frac{4}{e + 1} \\iff a = \\log \\frac{4}{e + 1}$$\n"
                "問題文の形式 $\\log \\frac{\\text{N}}{e + \\text{O}}$ より：$\\mathbf{N = 4, O = 1} \\implies \\mathbf{NO = 41}$。\n\n"
                "ここで $\\frac{4}{e + 1}$ の値の範囲を確認すると、$2 < e < 3$ より $3 < e + 1 < 4$ であるから：\n"
                "$$1 < \\frac{4}{e + 1} < \\frac{4}{3} < 2$$\n"
                "よって $0 < \\log \\frac{4}{e + 1} < \\log 2$ であり、区間 $[\\log 2 - 1, \\log 2]$ に確かに属する。\n"
                "増減を調べると：\n"
                "- $\\log 2 - 1 \\le a < \\log \\frac{4}{e + 1}$ においては $e^a(e + 1) < 4$ より $f'(a) < 0$ となり、$f(a)$ は **減少**（選択肢 $\\textcircled{1}$、$\\mathbf{P = 1}$）。\n"
                "- $\\log \\frac{4}{e + 1} < a < \\log 2$ においては $e^a(e + 1) > 4$ より $f'(a) > 0$ となり、$f(a)$ は **増加**（選択肢 $\\textcircled{0}$、$\\mathbf{Q = 0}$）。\n\n"
                "**(iii) $a \\ge \\log 2$ のとき**\n"
                "区間内のすべての $x$ で $e^x - 2 \\ge 0$ であるから、被積分関数は $e^x - 2$ である。\n"
                "$$f(a) = \\int_a^{a+1} (e^x - 2) \\, dx = \\left[e^x - 2x\\right]_a^{a+1} = \\{e^{a+1} - 2(a + 1)\\} - (e^a - 2a) = e^a(e - 1) - 2$$\n"
                "問題文の形式 $e^a(e - R) - S$ より：$\\mathbf{R = 1, S = 2} \\implies \\mathbf{RS = 12}$。\n\n"
                "$a$ で微分すると：\n"
                "$$f'(a) = e^a(e - 1)$$\n"
                "問題文の形式 $e^a(e - T)$ より：$\\mathbf{T = 1}$。\n"
                "$e - 1 > 0$ かつ $e^a > 0$ であるから、$f'(a) > 0$ が恒等的に成り立つ。\n"
                "したがって、$f(a)$ は **単調増加** である。\n"
                "選択肢 $\\textcircled{0}$「増加」より、$\\mathbf{U = 0}$。\n\n"
                "#### (3) 最小値をとる $a$ の決定\n"
                "以上の (i), (ii), (iii) の増減を統合すると：\n"
                "- $a < \\log \\frac{4}{e + 1}$ では $f(a)$ は単調減少。\n"
                "- $a > \\log \\frac{4}{e + 1}$ では $f(a)$ は単調増加。\n"
                "したがって、$f(a)$ は $a = \\log \\frac{4}{e + 1}$ において全体で最小値をとる。\n"
                "問題文の形式 $\\log \\frac{\\text{V}}{e + \\text{W}}$ より：\n"
                "$$\\mathbf{V = 4, W = 1} \\implies \\mathbf{VW = 41}$$\n\n"
                "**【解法テクニック・易錯点】**\n"
                "- 区間が動く積分関数では、折れ曲がり点 $x_0 = \\log 2$ が積分の「左端の左側」「区間の内部」「右端の右側」のどこにあるかを境界値 $a = \\log 2 - 1, \\log 2$ で几帳面に分類するのが基本です。導関数の符号変化から極値が区間 (ii) の内部に存在することが鮮やかに導かれます。"
            )
        }
    ]
}

# Write JSON
out_json = Path("work/2023-2-math-c2/explanations.json")
out_json.parent.mkdir(parents=True, exist_ok=True)
out_json.write_text(json.dumps(explanations, ensure_ascii=False, indent=2), encoding="utf-8")

# Write Markdown
md_content = r"""# 2023年度 第2回（2023-2）EJU 日本留学試験 数学コース2 全問詳細解説

- **試験科目**：数学（コース2 / Course 2 理系数学）
- **対象試験**：2023年度第2回（令和5年11月実施）
- **形式コード**：`MATHEMATICS_COURSE_2_JA`
- **問題構成**：大問 I（問1, 問2）、大問 II（問1, 問2）、大問 III、大問 IV
- **解答形式**：マーク式数字空欄（A～X等）

---

## 公式正解一覧表

| 大問 | 設問 | 空欄記号 | 正解 | 備考 |
| :--- | :--- | :--- | :--- | :--- |
| **第I問** | 問1 (1) | AB | **29** | 頂点 $(2, 9)$ |
| | 問1 (2) | CD | **25** | 移動後頂点 $(k+2, 5)$ |
| | 問1 (3) | E | **3** | $k < -3$ かつ $k^2 + 6k + 7 = 0$ |
| | | F | **7** | $k > 2$ かつ $k^2 - 4k + 2 = 0$ |
| | | GH | **32** | $k = -3 - \sqrt{2}$ |
| | | IJ | **22** | $k = 2 + \sqrt{2}$ |
| | 問2 (1) | KL | **15** | 色の組み合わせ $\binom{6}{4}$ |
| | | M | **2** | 正四面体の塗り方 $(3-1)!$ |
| | | NO | **30** | 正四面体総数 $15 \times 2$ |
| | 問2 (2)(i) | PQ | **30** | 立方体6色 $5 \times 3!$ |
| | 問2 (2)(ii)| RS | **15** | 立方体5色 $5 \times 3$ |
| **第II問**| 問1 | AB | **12** | 比率 $AG:GC = 1:2$ |
| | | C | **1** | $\frac{1}{3}(-2\vec{a}+\vec{b})$ |
| | | D | **0** | 直交内積 $0$ |
| | | EF | **62** | $AB = \frac{\sqrt{6}}{2}$ |
| | | G | **9** | $\frac{2}{3}(\vec{a}+\vec{b})$ |
| | | H | **0** | $\frac{1}{3}(\vec{a}+2\vec{b})$ |
| | | IJ | **53** | 内積 $\frac{5}{3}$ |
| | | KLM | **539** | $\cos \theta = \frac{5\sqrt{3}}{9}$ |
| | 問2 (1) | NO | **21** | 中心 $(2, 1)$ |
| | 問2 (2) | PQ | **25** | $a = \frac{2}{5}$ |
| | | RS | **95** | $b = \frac{9}{5}$ |
| | 問2 (3) | TUVW| **3445** | 距離公式分子分母 |
| | | X | **2** | 半径 $r = 2$ |
| **第III問**| (1) | CD | **38** | 傾き $3t^2 - 8t$ |
| | | EFG | **241** | 切片 $-2t^3 + 4t^2 + 1$ |
| | | HIJ | **-53** | 接線 $l: y = -5x + 3$ |
| | (2) | KLM | **2-7** | 共有点 $B(2, -7)$ |
| | (3) | NO | **53** | 接点 $t = \frac{5}{3}$ |
| | | PQRS| **7727** | 切片 $\frac{77}{27}$ |
| | (4) | TUV | **152** | $t = \frac{1 \pm \sqrt{5}}{2}$ |
| | (5) | WXY | **112** | 面積 $S = \frac{1}{12}$ |
| **第IV問** | | A | **2** | $x = \log 2$ |
| | (i) | BC | **21** | $\log 2 - 1$ |
| | | DE | **21** | $2 + e^a(1 - e)$ |
| | | F | **1** | 導関数 $e^a(1 - e)$ |
| | | G | **1** | 減少 |
| | (ii) | HIJK| **4641** | $4\log 2 - 6 - 4a + e^a(e + 1)$ |
| | | LM | **41** | 導関数 $-4 + e^a(e + 1)$ |
| | | NO | **41** | 極値点 $a = \log \frac{4}{e+1}$ |
| | | P | **1** | 減少 |
| | | Q | **0** | 増加 |
| | (iii) | RS | **12** | $e^a(e - 1) - 2$ |
| | | T | **1** | 導関数 $e^a(e - 1)$ |
| | | U | **0** | 増加 |
| | 結論 | VW | **41** | 最小点 $a = \log \frac{4}{e+1}$ |

---

## 逐問詳細推導与解説

"""

for s in explanations["sections"]:
    md_content += "\n---\n\n## " + s["sectionTitle"] + "\n\n"
    points_str = ", ".join(s["points"])
    md_content += f"**【考查考点】**：{points_str}\n\n"
    md_content += s["detailedSolution"] + "\n"

out_md = Path("docs/explanations/2023-2-math-c2-solutions.md")
out_md.write_text(md_content, encoding="utf-8")
print(f"Generated {out_json} and {out_md} successfully.")

