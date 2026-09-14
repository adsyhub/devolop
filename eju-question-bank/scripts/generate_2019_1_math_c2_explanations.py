#!/usr/bin/env python3
"""Generate comprehensive explanations for 2019-1 EJU Mathematics Course 2."""

import json
from pathlib import Path

# Load Math C1 for shared Question I
math_c1 = json.loads(Path("/workspace/Develop/eju-question-bank/work/2019-1-math-c1/explanations.json").read_text(encoding="utf-8"))

explanations = {
    "session": "2019-1",
    "subject": "MATHEMATICS",
    "course": "COURSE_2",
    "formCode": "MATHEMATICS_COURSE_2_JA",
    "sections": [
        math_c1["sections"][0],  # I_1
        math_c1["sections"][1],  # I_2
        {
            "sectionId": "II_1",
            "sectionTitle": "第II問 問1：球に内接する四面体と空間ベクトル・重心と共線条件",
            "points": [
                "球の直径（対蹠点 $\\vec{d} = -\\vec{b}$）と空間ベクトルの基底表示",
                "線分の中点ベクトル（$\\overrightarrow{DA}, \\overrightarrow{MN}, \\overrightarrow{OP}$）の導出",
                "三角形の重心ベクトル $\\overrightarrow{OG} = \\frac{\\vec{b}+\\vec{c}+\\vec{d}}{3}$",
                "内積によるベクトルの大きさの計算（$|\\overrightarrow{PG}|$）",
                "共線条件（実数倍関係 $\\overrightarrow{AG} = k \\overrightarrow{AP}$）の証明"
            ],
            "officialAnswers": {
                "A": "6",
                "BCD": "521",
                "EF": "84",
                "GH": "23",
                "IJ": "76",
                "KL": "43"
            },
            "detailedSolution": (
                "### 【第II問 問1】詳細解答と解説\n\n"
                "原点 O を中心とする半径 2 の球面上に 4 つの頂点をもつ四面体 ABCD を考える。\n"
                "球面上にあるため、$|\\vec{a}| = |\\vec{b}| = |\\vec{c}| = |\\vec{d}| = 2$ である。\n"
                "また、$AB = BC = CA = 2$ であり、辺 BD は球の直径であるから、$\\vec{d} = -\\vec{b}$ である。\n\n"
                "#### (1) ベクトル $\\overrightarrow{DA}$ および $\\overrightarrow{MN}$ の計算\n"
                "1. **$\\overrightarrow{DA}$ の表示**：\n"
                "   $$\\overrightarrow{DA} = \\vec{a} - \\vec{d} = \\vec{a} - (-\\vec{b}) = \\vec{a} + \\vec{b}$$\n"
                "   選択肢の対応表（$\\textcircled{6}: \\vec{a} + \\vec{b}$）より、$\\mathbf{A = 6}$。\n\n"
                "2. **$\\overrightarrow{MN}$ の表示**：\n"
                "   M は線分 DA の中点であるから：\n"
                "   $$\\overrightarrow{OM} = \\frac{\\vec{d} + \\vec{a}}{2} = \\frac{-\\vec{b} + \\vec{a}}{2}$$\n"
                "   N は線分 BC の中点であるから：\n"
                "   $$\\overrightarrow{ON} = \\frac{\\vec{b} + \\vec{c}}{2}$$\n"
                "   したがって：\n"
                "   $$\\overrightarrow{MN} = \\overrightarrow{ON} - \\overrightarrow{OM} = \\frac{\\vec{b} + \\vec{c}}{2} - \\frac{-\\vec{b} + \\vec{a}}{2} = \\frac{2\\vec{b} + \\vec{c} - \\vec{a}}{2} = \\frac{\\vec{c} - \\vec{a}}{2} + \\vec{b}$$\n"
                "   問題文の形式 $\\frac{\\text{B}}{\\text{C}} + \\text{D}$ と比較して：\n"
                "   選択肢 $\\textcircled{5}$ は $\\vec{c} - \\vec{a}$、選択肢 $\\textcircled{1}$ は $\\vec{b}$ であるから：\n"
                "   $$\\mathbf{B = 5, C = 2, D = 1} \\implies \\mathbf{BCD = 521}$$\n\n"
                "#### (2) 点 P, G の位置ベクトルと線分長 $|\\overrightarrow{PG}|$、共線条件の導出\n"
                "1. **線分 MN の中点 P の位置ベクトル $\\overrightarrow{OP}$**：\n"
                "   $$\\overrightarrow{OP} = \\frac{\\overrightarrow{OM} + \\overrightarrow{ON}}{2} = \\frac{\\frac{\\vec{a} - \\vec{b}}{2} + \\frac{\\vec{b} + \\vec{c}}{2}}{2} = \\frac{\\vec{a} + \\vec{c}}{4}$$\n"
                "   選択肢 $\\textcircled{8}$ は $\\vec{c} + \\vec{a}$ であるから：\n"
                "   $$\\mathbf{E = 8, F = 4} \\implies \\mathbf{EF = 84}$$\n\n"
                "2. **三角形 BCD の重心 G の位置ベクトル $\\overrightarrow{OG}$**：\n"
                "   $$\\overrightarrow{OG} = \\frac{\\vec{b} + \\vec{c} + \\vec{d}}{3} = \\frac{\\vec{b} + \\vec{c} - \\vec{b}}{3} = \\frac{\\vec{c}}{3}$$\n"
                "   選択肢 $\\textcircled{2}$ は $\\vec{c}$ であるから：\n"
                "   $$\\mathbf{G = 2, H = 3} \\implies \\mathbf{GH = 23}$$\n\n"
                "3. **線分長 $|\\overrightarrow{PG}|$ の計算**：\n"
                "   $$\\overrightarrow{PG} = \\overrightarrow{OG} - \\overrightarrow{OP} = \\frac{\\vec{c}}{3} - \\frac{\\vec{a} + \\vec{c}}{4} = \\frac{\\vec{c} - 3\\vec{a}}{12}$$\n"
                "   ここで、$|\\vec{a}| = 2, |\\vec{c}| = 2$、また $CA = 2$ より：\n"
                "   $$|\\vec{c} - \\vec{a}|^2 = |\\vec{c}|^2 - 2\\vec{a}\\cdot\\vec{c} + |\\vec{a}|^2 = 4 - 2\\vec{a}\\cdot\\vec{c} + 4 = 2^2 = 4$$\n"
                "   $$8 - 2\\vec{a}\\cdot\\vec{c} = 4 \\implies 2\\vec{a}\\cdot\\vec{c} = 4 \\implies \\vec{a}\\cdot\\vec{c} = 2$$\n"
                "   したがって：\n"
                "   $$|\\vec{c} - 3\\vec{a}|^2 = |\\vec{c}|^2 - 6\\vec{a}\\cdot\\vec{c} + 9|\\vec{a}|^2 = 4 - 6(2) + 9(4) = 4 - 12 + 36 = 28$$\n"
                "   $$|\\vec{c} - 3\\vec{a}| = \\sqrt{28} = 2\\sqrt{7}$$\n"
                "   よって：\n"
                "   $$|\\overrightarrow{PG}| = \\frac{2\\sqrt{7}}{12} = \\frac{\\sqrt{7}}{6}$$\n"
                "   形式 $\\frac{\\sqrt{\\text{I}}}{\\text{J}}$ より：\n"
                "   $$\\mathbf{I = 7, J = 6} \\implies \\mathbf{IJ = 76}$$\n\n"
                "4. **共線条件 $\\overrightarrow{AG} = k \\overrightarrow{AP}$ の係数比**：\n"
                "   $$\\overrightarrow{AP} = \\overrightarrow{OP} - \\vec{a} = \\frac{\\vec{a} + \\vec{c}}{4} - \\vec{a} = \\frac{\\vec{c} - 3\\vec{a}}{4}$$\n"
                "   $$\\overrightarrow{AG} = \\overrightarrow{OG} - \\vec{a} = \\frac{\\vec{c}}{3} - \\vec{a} = \\frac{\\vec{c} - 3\\vec{a}}{3}$$\n"
                "   両者を比較すると：\n"
                "   $$\\overrightarrow{AG} = \\frac{4}{3} \\overrightarrow{AP}$$\n"
                "   形式 $\\frac{\\text{K}}{\\text{L}}$ より：\n"
                "   $$\\mathbf{K = 4, L = 3} \\implies \\mathbf{KL = 43}$$\n"
                "   実数倍の関係が成り立つため、3点 A, P, G は同一直線上にある。"
            )
        },
        {
            "sectionId": "II_2",
            "sectionTitle": "第II問 問2：複素数平面上の正三角形・回転と拡大および三角形の面積",
            "points": [
                "複素数の比 $\\frac{\\gamma - \\alpha}{\\beta - \\alpha}$ と2次方程式の解法",
                "絶対値（比が 1）と偏角（$\\pm \\frac{2}{3}\\pi$）の幾何学的解釈",
                "因数分解・複素数の合成による辺長の決定",
                "正三角形または二等辺三角形の面積公式"
            ],
            "officialAnswers": {
                "MNO": "132",
                "P": "1",
                "QR": "23",
                "STU": "132",
                "V": "3",
                "WXY": "934"
            },
            "detailedSolution": (
                "### 【第II問 問2】詳細解答と解説\n\n"
                "複素数平面上の異なる3点 A($\\alpha$), B($\\beta$), C($\\gamma$) が\n"
                "$$(\\gamma - \\alpha)^2 + (\\gamma - \\alpha)(\\beta - \\alpha) + (\\beta - \\alpha)^2 = 0 \\quad \\cdots \\textcircled{1}$$\n"
                "$$|\\beta - 2\\alpha + \\gamma| = 3 \\quad \\cdots \\textcircled{2}$$\n"
                "を満たす。\n\n"
                "#### (1) 複素数の比 $\\frac{\\gamma - \\alpha}{\\beta - \\alpha}$ の絶対値と偏角\n"
                "A, B は異なる点であるから $\\beta - \\alpha \\neq 0$ である。\n"
                "$\\textcircled{1}$ の両辺を $(\\beta - \\alpha)^2$ で割ると：\n"
                "$$\\left(\\frac{\\gamma - \\alpha}{\\beta - \\alpha}\\right)^2 + \\frac{\\gamma - \\alpha}{\\beta - \\alpha} + 1 = 0$$\n"
                "これは 1 の虚数立方根 $\\omega$ の満たす方程式 $z^2 + z + 1 = 0$ である。\n"
                "解の公式より：\n"
                "$$\\frac{\\gamma - \\alpha}{\\beta - \\alpha} = \\frac{-1 \\pm \\sqrt{3}i}{2}$$\n"
                "問題文の形式 $\\frac{-\\text{M} \\pm \\sqrt{\\text{N}}i}{\\text{O}}$ と比較して：\n"
                "$$\\mathbf{M = 1, N = 3, O = 2} \\implies \\mathbf{MNO = 132}$$\n\n"
                "この複素数の絶対値と偏角を求める：\n"
                "$$\\left|\\frac{\\gamma - \\alpha}{\\beta - \\alpha}\\right| = \\sqrt{\\left(-\\frac{1}{2}\\right)^2 + \\left(\\pm\\frac{\\sqrt{3}}{2}\\right)^2} = \\sqrt{\\frac{1}{4} + \\frac{3}{4}} = 1$$\n"
                "したがって、$\\mathbf{P = 1}$（$AC = AB$ を意味する）。\n\n"
                "偏角は：\n"
                "$$\\arg\\frac{\\gamma - \\alpha}{\\beta - \\alpha} = \\pm \\frac{2}{3}\\pi$$\n"
                "形式 $\\pm \\frac{\\text{Q}}{\\text{R}}\\pi$ より：\n"
                "$$\\mathbf{Q = 2, R = 3} \\implies \\mathbf{QR = 23}$$\n"
                "（これは、点 C が点 A を中心として点 B を $\\pm 120^\\circ$ 回転した点であることを意味する。）\n\n"
                "#### (2) 線分長 $|\\beta - \\alpha|$ の決定\n"
                "$\\beta - 2\\alpha + \\gamma$ を $(\\beta - \\alpha)$ でくくる：\n"
                "$$\\beta - 2\\alpha + \\gamma = (\\beta - \\alpha) + (\\gamma - \\alpha) = (\\beta - \\alpha) \\left(1 + \\frac{\\gamma - \\alpha}{\\beta - \\alpha}\\right)$$\n"
                "ここで、\n"
                "$$1 + \\frac{-1 \\pm \\sqrt{3}i}{2} = \\frac{2 - 1 \\pm \\sqrt{3}i}{2} = \\frac{1 \\pm \\sqrt{3}i}{2}$$\n"
                "問題文の形式 $(\\beta - \\alpha) \\cdot \\frac{\\text{S} \\pm \\sqrt{\\text{T}}i}{\\text{U}}$ と比較して：\n"
                "$$\\mathbf{S = 1, T = 3, U = 2} \\implies \\mathbf{STU = 132}$$\n\n"
                "$\\textcircled{2}$ より $|\\beta - 2\\alpha + \\gamma| = 3$ であるから：\n"
                "$$\\left|(\\beta - \\alpha) \\cdot \\frac{1 \\pm \\sqrt{3}i}{2}\\right| = 3$$\n"
                "$$\\left|\\frac{1 \\pm \\sqrt{3}i}{2}\\right| = \\sqrt{\\frac{1}{4} + \\frac{3}{4}} = 1$$\n"
                "したがって：\n"
                "$$|\\beta - \\alpha| \\times 1 = 3 \\implies |\\beta - \\alpha| = 3$$\n"
                "よって、$\\mathbf{V = 3}$。\n\n"
                "#### (3) 三角形 ABC の面積\n"
                "$\\triangle ABC$ において：\n"
                "- $AB = |\\beta - \\alpha| = 3$\n"
                "- $AC = |\\gamma - \\alpha| = |\\beta - \\alpha| = 3$\n"
                "- 頂角 $\\angle BAC = \\left|\\arg\\frac{\\gamma - \\alpha}{\\beta - \\alpha}\\right| = \\frac{2}{3}\\pi = 120^\\circ$\n"
                "したがって、三角形 ABC の面積は：\n"
                "$$\\text{Area} = \\frac{1}{2} AB \\cdot AC \\sin 120^\\circ = \\frac{1}{2} \\times 3 \\times 3 \\times \\frac{\\sqrt{3}}{2} = \\frac{9\\sqrt{3}}{4}$$\n"
                "形式 $\\frac{\\text{W}\\sqrt{\\text{X}}}{\\text{Y}}$ より：\n"
                "$$\\mathbf{W = 9, X = 3, Y = 4} \\implies \\mathbf{WXY = 934}$$"
            )
        },
        {
            "sectionId": "III_1",
            "sectionTitle": "第III問（前半）：単位円上の動点と線分長・3倍角の公式と微分の極値",
            "points": [
                "動点 P, Q の座標表示と線分長 $\\ell = |\\cos 3\\theta - \\cos\\theta|$",
                "3倍角の公式 $\\cos 3\\theta = 4\\cos^3\\theta - 3\\cos\\theta$",
                "変数変換 $t = \\cos\\theta$ と微分による増減・極値・最大値 $\\frac{8\\sqrt{3}}{9}$ の決定"
            ],
            "officialAnswers": {
                "AB": "32",
                "CDE": "434",
                "FGH": "432",
                "IJ": "33",
                "KLM": "839"
            },
            "detailedSolution": (
                "### 【第III問（前半）】詳細解答と解説\n\n"
                "単位円 $C$ 上の動点 P$(\\cos\\theta, \\sin\\theta)$、Q$(\\cos 3\\theta, \\sin 3\\theta)$（$0 \\le \\theta \\le \\pi$）がある。\n"
                "点 P, Q から $x$ 軸に下ろした垂線の足をそれぞれ A$(\\cos\\theta, 0)$、B$(\\cos 3\\theta, 0)$ とすると、線分 AB の長さは：\n"
                "$$\\ell = |\\cos 3\\theta - \\cos\\theta|$$\n\n"
                "#### (1) $\\theta = \\frac{\\pi}{3}$ のときの $\\ell$\n"
                "$$\\cos\\theta = \\cos\\frac{\\pi}{3} = \\frac{1}{2}, \\quad \\cos 3\\theta = \\cos\\pi = -1$$\n"
                "$$\\ell = \\left|-1 - \\frac{1}{2}\\right| = \\left|-\\frac{3}{2}\\right| = \\frac{3}{2}$$\n"
                "形式 $\\frac{\\text{A}}{\\text{B}}$ より：\n"
                "$$\\mathbf{A = 3, B = 2} \\implies \\mathbf{AB = 32}$$\n\n"
                "#### (2) 3倍角の公式による関数化と微分の導出\n"
                "3倍角の公式 $\\cos 3\\theta = 4\\cos^3\\theta - 3\\cos\\theta$ を用いる。\n"
                "$\\cos\\theta = t$ とおくと（$0 \\le \\theta \\le \\pi$ より $-1 \\le t \\le 1$）：\n"
                "$$\\cos 3\\theta - \\cos\\theta = (4t^3 - 3t) - t = 4t^3 - 4t$$\n"
                "したがって、$\\ell = |4t^3 - 4t|$ である。\n"
                "問題文の形式 $\\ell = |\\text{C}t^{\\text{D}} - \\text{E}t|$ と比較して：\n"
                "$$\\mathbf{C = 4, D = 3, E = 4} \\implies \\mathbf{CDE = 434}$$\n\n"
                "$g(t) = 4t^3 - 4t$ とおき、$t$ で微分する：\n"
                "$$g'(t) = 12t^2 - 4 = 4(3t^2 - 1)$$\n"
                "問題文の形式 $g'(t) = \\text{F}(\\text{G}t^{\\text{H}} - 1)$ と比較して：\n"
                "$$\\mathbf{F = 4, G = 3, H = 2} \\implies \\mathbf{FGH = 432}$$\n\n"
                "#### (3) 最大値の決定\n"
                "$g'(t) = 0 \\iff 3t^2 - 1 = 0 \\iff t = \\pm \\frac{1}{\\sqrt{3}} = \\pm \\frac{\\sqrt{3}}{3}$ である。\n"
                "形式 $\\cos\\theta = \\pm \\frac{\\sqrt{\\text{I}}}{\\text{J}}$ より：\n"
                "$$\\mathbf{I = 3, J = 3} \\implies \\mathbf{IJ = 33}$$\n\n"
                "$g(t)$ の増減および絶対値の評価：\n"
                "- $t = \\frac{1}{\\sqrt{3}}$ のとき：\n"
                "  $$g\\left(\\frac{1}{\\sqrt{3}}\\right) = 4\\left(\\frac{1}{3\\sqrt{3}}\\right) - 4\\left(\\frac{1}{\\sqrt{3}}\\right) = -\\frac{8}{3\\sqrt{3}} = -\\frac{8\\sqrt{3}}{9}$$\n"
                "  $$\\ell = |g(t)| = \\frac{8\\sqrt{3}}{9}$$\n"
                "- $t = -\\frac{1}{\\sqrt{3}}$ のとき：\n"
                "  $$g\\left(-\\frac{1}{\\sqrt{3}}\\right) = \\frac{8\\sqrt{3}}{9} \\implies \\ell = \\frac{8\\sqrt{3}}{9}$$\n"
                "- 端点 $t = \\pm 1$ では $g(\\pm 1) = 0$。\n"
                "したがって、$\\ell$ の最大値は $\\frac{8\\sqrt{3}}{9}$ である。\n"
                "形式 $\\frac{\\text{K}\\sqrt{\\text{L}}}{\\text{M}}$ より：\n"
                "$$\\mathbf{K = 8, L = 3, M = 9} \\implies \\mathbf{KLM = 839}$$"
            )
        },
        {
            "sectionId": "III_2",
            "sectionTitle": "第III問（後半）：$\\ell$ が最大となる点 P, Q の座標決定",
            "points": [
                "三角関数の相互関係 $\\sin\\theta = \\sqrt{1 - \\cos^2\\theta}$",
                "3倍角の公式 $\\sin 3\\theta = 3\\sin\\theta - 4\\sin^3\\theta$",
                "動点 P, Q の具体的な座標計算と選択肢の同定"
            ],
            "officialAnswers": {
                "N": "0",
                "OP": "56",
                "Q": "0",
                "RS": "46"
            },
            "detailedSolution": (
                "### 【第III問（後半）】詳細解答と解説\n\n"
                "$\\ell$ が最大値をとる点 P, Q の座標（2組）を求める。\n\n"
                "#### (1) 組 1：$t = \\cos\\theta = +\\frac{\\sqrt{3}}{3}$ のとき\n"
                "$0 \\le \\theta \\le \\pi$ より $\\sin\\theta \\ge 0$ であるから：\n"
                "$$\\sin\\theta = \\sqrt{1 - \\cos^2\\theta} = \\sqrt{1 - \\frac{1}{3}} = \\sqrt{\\frac{2}{3}} = \\frac{\\sqrt{6}}{3}$$\n"
                "選択肢の表より、$\\textcircled{0}$ は $\\frac{\\sqrt{6}}{3}$ である。\n"
                "したがって、点 P の座標は $P\\left(\\frac{\\sqrt{3}}{3}, \\text{N}\\right)$ より：\n"
                "$$\\mathbf{N = 0}$$\n\n"
                "次に点 Q$(\\cos 3\\theta, \\sin 3\\theta)$ の座標を求める：\n"
                "- $x_Q = \\cos 3\\theta = 4t^3 - 3t = 4\\left(\\frac{\\sqrt{3}}{9}\\right) - 3\\left(\\frac{\\sqrt{3}}{3}\\right) = \\frac{4\\sqrt{3} - 9\\sqrt{3}}{9} = -\\frac{5\\sqrt{3}}{9}$。\n"
                "  選択肢 $\\textcircled{5}$ は $-\\frac{5\\sqrt{3}}{9}$ である。$\\implies \\mathbf{O = 5}$。\n"
                "- $y_Q = \\sin 3\\theta = 3\\sin\\theta - 4\\sin^3\\theta = \\sin\\theta(3 - 4\\sin^2\\theta)$。\n"
                "  $$y_Q = \\frac{\\sqrt{6}}{3} \\left(3 - 4 \\times \\frac{2}{3}\\right) = \\frac{\\sqrt{6}}{3} \\left(3 - \\frac{8}{3}\\right) = \\frac{\\sqrt{6}}{3} \\times \\frac{1}{3} = \\frac{\\sqrt{6}}{9}$$\n"
                "  選択肢 $\\textcircled{6}$ は $\\frac{\\sqrt{6}}{9}$ である。$\\implies \\mathbf{P = 6}$。\n"
                "したがって、$\\mathbf{OP = 56}$。\n\n"
                "#### (2) 組 2：$t = \\cos\\theta = -\\frac{\\sqrt{3}}{3}$ のとき\n"
                "同様に $\\sin\\theta = \\sqrt{1 - \\frac{1}{3}} = \\frac{\\sqrt{6}}{3}$（選択肢 $\\textcircled{0}$）であるから：\n"
                "$$P\\left(-\\frac{\\sqrt{3}}{3}, \\text{Q}\\right) \\implies \\mathbf{Q = 0}$$\n\n"
                "点 Q の座標：\n"
                "- $x_Q = \\cos 3\\theta = 4\\left(-\\frac{\\sqrt{3}}{9}\\right) - 3\\left(-\\frac{\\sqrt{3}}{3}\\right) = \\frac{5\\sqrt{3}}{9}$。\n"
                "  選択肢 $\\textcircled{4}$ は $\\frac{5\\sqrt{3}}{9}$ である。$\\implies \\mathbf{R = 4}$。\n"
                "- $y_Q = \\sin 3\\theta = \\frac{\\sqrt{6}}{9}$。\n"
                "  選択肢 $\\textcircled{6}$ は $\\frac{\\sqrt{6}}{9}$ である。$\\implies \\mathbf{S = 6}$。\n"
                "したがって、$\\mathbf{RS = 46}$。"
            )
        },
        {
            "sectionId": "IV_1",
            "sectionTitle": "第IV問（前半）：対数不等式 $x-1 \\ge \\log x$ の証明と囲まれた面積 $S$ の定積分",
            "points": [
                "関数 $f(x) = x - 1 - \\log x$ の導関数 $f'(x) = 1 - 1/x$ と最小値 0",
                "基本不等式 $x - 1 \\ge \\log x$ による上下関係の決定",
                "部分積分法による $\\int \\log x \\, dx = x(\\log x - 1)$",
                "区間 $[n, n+1]$ における定積分の展開計算"
            ],
            "officialAnswers": {
                "AB": "11",
                "C": "1",
                "D": "0",
                "EF": "22",
                "G": "1",
                "HIJK": "2211"
            },
            "detailedSolution": (
                "### 【第IV問（前半）】詳細解答と解説\n\n"
                "#### (1) $f(x) = x - 1 - \\log x$ の導関数と最小値\n"
                "定義域は $x > 0$ である。\n"
                "導関数は：\n"
                "$$f'(x) = 1 - \\frac{1}{x}$$\n"
                "問題文の形式 $f'(x) = \\text{A} - \\frac{\\text{B}}{x}$ より：\n"
                "$$\\mathbf{A = 1, B = 1} \\implies \\mathbf{AB = 11}$$\n\n"
                "増減を調べると：\n"
                "- $0 < x < 1$ で $f'(x) < 0$（単調減少）\n"
                "- $x = 1$ で $f'(1) = 0$\n"
                "- $x > 1$ で $f'(x) > 0$（単調増加）\n"
                "したがって、$f(x)$ は $x = 1$ において最小値をとる：\n"
                "$$f(1) = 1 - 1 - \\log 1 = 0$$\n"
                "したがって、$x = C$ において最小値 $D$ より：\n"
                "$$\\mathbf{C = 1, D = 0}$$\n"
                "最小値が 0 であることから、すべての $x > 0$ で $f(x) \\ge 0 \\iff x - 1 \\ge \\log x$ が成立する。\n\n"
                "#### (2) 面積 $S$ の定積分表示と展開計算\n"
                "$u = \\frac{x}{k}$ とおくと、(1) の不等式より $\\frac{x}{k} - 1 \\ge \\log\\frac{x}{k}$ が成立する。\n"
                "したがって、区間 $[n, n+1]$ において直線 $y = \\frac{x}{k} - 1$ は常に曲線 $y = \\log\\frac{x}{k}$ の上側にある。\n"
                "囲まれた図形の面積 $S$ は：\n"
                "$$S = \\int_n^{n+1} \\left(\\frac{x}{k} - 1 - \\log\\frac{x}{k}\\right) dx = \\int_n^{n+1} \\left(\\frac{x}{k} - 1 - \\log x + \\log k\\right) dx$$\n\n"
                "不定積分を求める：\n"
                "- $\\int \\frac{x}{k} dx = \\frac{x^2}{2k}$（形式 $\\frac{x^{\\text{E}}}{\\text{F}k}$ より $\\mathbf{E = 2, F = 2} \\implies \\mathbf{EF = 22}$）\n"
                "- $\\int (1 + \\log x) dx$ を考えると、$\\int \\log x \\, dx = x\\log x - x = x(\\log x - 1)$ である。\n"
                "  選択肢 $\\textcircled{1}$ は $x(\\log x - 1)$ である。\n"
                "  これを用いると：\n"
                "  $$-x - x(\\log x - 1) = -x - x\\log x + x = -x\\log x$$\n"
                "  となり、$-\\int (1 + \\log x)dx = -x - \\text{G}$ の形式と一致する。\n"
                "  よって、$\\mathbf{G = 1}$。\n\n"
                "端点 $x = n+1, n$ を代入して展開する：\n"
                "$$S = \\left[\\frac{x^2}{2k} - x\\log x + x\\log k\\right]_n^{n+1}$$\n"
                "1. $\\frac{x^2}{2k}$ の項：\n"
                "   $$\\frac{(n+1)^2 - n^2}{2k} = \\frac{2n + 1}{2k}$$\n"
                "2. $x\\log k$ の項：\n"
                "   $$(n+1)\\log k - n\\log k = \\log k$$\n"
                "3. $-x\\log x$ の項：\n"
                "   $$-(n+1)\\log(n+1) + n\\log n$$\n"
                "これらを合わせると：\n"
                "$$S = \\frac{2n + 1}{2k} + \\log k - (n + 1)\\log(n + 1) + n\\log n$$\n"
                "問題文の形式 $\\frac{\\text{H}n + 1}{\\text{I}k} + \\log k - (n + \\text{J})\\log(n + \\text{K}) + n\\log n$ と比較して：\n"
                "$$\\mathbf{H = 2, I = 2, J = 1, K = 1} \\implies \\mathbf{HIJK = 2211}$$"
            )
        },
        {
            "sectionId": "IV_2",
            "sectionTitle": "第IV問（後半）：面積 $S$ の最小値 $a_n$ と極限値 $\\lim_{n\\to\\infty} a_n$",
            "points": [
                "$k$ に関する微分 $\\frac{dS}{dk} = \\frac{2k - (2n+1)}{2k^2}$",
                "極小・最小点 $k = n + 1/2$ の導出",
                "最小値 $a_n$ の対数変形と自然対数の底 $e$ の定義による極限計算"
            ],
            "officialAnswers": {
                "LMN": "222",
                "OP": "12",
                "QRSTUV": "111222",
                "W": "0"
            },
            "detailedSolution": (
                "### 【第IV問（後半）】詳細解答と解説\n\n"
                "#### (1) $S$ の $k$ による微分と最小点\n"
                "$S = \\frac{2n + 1}{2k} + \\log k - (n + 1)\\log(n + 1) + n\\log n$ を $k$ で微分する：\n"
                "$$\\frac{dS}{dk} = -\\frac{2n + 1}{2k^2} + \\frac{1}{k} = \\frac{2k - (2n + 1)}{2k^2}$$\n"
                "問題文の形式 $\\frac{\\text{L}k - (\\text{M}n + 1)}{\\text{N}k^2}$ と比較して：\n"
                "$$\\mathbf{L = 2, M = 2, N = 2} \\implies \\mathbf{LMN = 222}$$\n\n"
                "$\\frac{dS}{dk} = 0$ とおくと：\n"
                "$$2k - (2n + 1) = 0 \\implies 2k = 2n + 1 \\implies k = n + \\frac{1}{2}$$\n"
                "増減表より、$k = n + \\frac{1}{2}$ で $S$ は極小かつ最小となる。\n"
                "形式 $k = n + \\frac{\\text{O}}{\\text{P}}$ より：\n"
                "$$\\mathbf{O = 1, P = 2} \\implies \\mathbf{OP = 12}$$\n\n"
                "#### (2) 最小値 $a_n$ の対数表示\n"
                "$k = n + \\frac{1}{2} = \\frac{2n+1}{2}$ を $S$ に代入する：\n"
                "$$\\frac{2n+1}{2k} = \\frac{2n+1}{2 \\cdot \\frac{2n+1}{2}} = 1$$\n"
                "したがって：\n"
                "$$a_n = 1 + \\log\\left(\\frac{2n+1}{2}\\right) - (n+1)\\log(n+1) + n\\log n$$\n"
                "対数部分を整理する：\n"
                "$$-(n+1)\\log(n+1) + n\\log n = -\\log\\left((n+1)^{n+1}\\right) + \\log(n^n) = -\\log\\left(\\frac{(n+1)^n (n+1)}{n^n}\\right) = -\\log\\left(\\left(1 + \\frac{1}{n}\\right)^n (n+1)\\right)$$\n"
                "これに $\\log\\left(\\frac{2n+1}{2}\\right)$ を加えると：\n"
                "$$\\log\\left(\\frac{2n+1}{2}\\right) - \\log\\left(\\left(1 + \\frac{1}{n}\\right)^n (n+1)\\right) = -\\left[\\log\\left(\\left(1 + \\frac{1}{n}\\right)^n (n+1)\\right) - \\log\\left(\\frac{2n+1}{2}\\right)\\right]$$\n"
                "$$= -\\log\\left\\{ \\left(1 + \\frac{1}{n}\\right)^n \\cdot \\frac{n+1}{\\frac{2n+1}{2}} \\right\\} = -\\log\\left\\{ \\left(1 + \\frac{1}{n}\\right)^n \\cdot \\frac{2n+2}{2n+1} \\right\\}$$\n"
                "したがって：\n"
                "$$a_n = 1 - \\log\\left\\{ \\left(1 + \\frac{1}{n}\\right)^n \\cdot \\frac{2n+2}{2n+1} \\right\\}$$\n"
                "問題文の形式 $a_n = \\text{Q} - \\log\\left\\{ \\left(\\text{R} + \\frac{\\text{S}}{n}\\right)^n \\cdot \\frac{\\text{T}n + \\text{U}}{\\text{V}n + 1} \\right\\}$ と比較して：\n"
                "$$\\mathbf{Q = 1, R = 1, S = 1, T = 2, U = 2, V = 2} \\implies \\mathbf{QRSTUV = 111222}$$\n\n"
                "#### (3) 極限値 $\\lim_{n \\to \\infty} a_n$ の計算\n"
                "$n \\to \\infty$ のとき：\n"
                "- 自然対数の底 $e$ の定義より：\n"
                "  $$\\lim_{n \\to \\infty} \\left(1 + \\frac{1}{n}\\right)^n = e$$\n"
                "- 分数式の極限：\n"
                "  $$\\lim_{n \\to \\infty} \\frac{2n+2}{2n+1} = \\lim_{n \\to \\infty} \\frac{2 + 2/n}{2 + 1/n} = 1$$\n"
                "したがって、対数の中身の極限は：\n"
                "$$\\lim_{n \\to \\infty} \\left\\{ \\left(1 + \\frac{1}{n}\\right)^n \\cdot \\frac{2n+2}{2n+1} \\right\\} = e \\times 1 = e$$\n"
                "これより：\n"
                "$$\\lim_{n \\to \\infty} a_n = 1 - \\log(e) = 1 - 1 = 0$$\n"
                "したがって、$\\mathbf{W = 0}$。"
            )
        }
    ]
}

# Write Markdown
md_content = r"""# 2019年度 第1回（2019-1）EJU 日本留学試験 数学 コース2 全問詳細解説

- **試験科目**：数学（コース2 / Mathematics Course 2）
- **対象試験**：2019年度第1回（平成31年6月実施）
- **形式コード**：`MATHEMATICS_COURSE_2_JA`
- **問題構成**：第I問（問1, 問2）、第II問（問1, 問2）、第III問、第IV問
- **解答形式**：マーク式（空欄補充・数値および符号）

---

## 数学 コース2 公式正解一覧表

| 大問 | 設問 | 解答欄 | 公式正解 | 考査分野・要点 |
| :--- | :--- | :--- | :--- | :--- |
| **第I問** | 問1 | A, B, C | **9, 7, 7** ($<, >, >$) | 2次関数のグラフと係数の符号判定（Course 1共通） |
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
| **第II問** | 問1 | A | **6** ($\vec{a}+\vec{b}$) | 球の直径と線分ベクトル $\overrightarrow{DA}$ |
| | | BCD | **521** ($\frac{\vec{c}-\vec{a}}{2} + \vec{b}$) | 中点ベクトル $\overrightarrow{MN}$ |
| | | EF | **84** ($\frac{\vec{c}+\vec{a}}{4}$) | 中点 P の位置ベクトル $\overrightarrow{OP}$ |
| | | GH | **23** ($\frac{\vec{c}}{3}$) | 三角形 BCD の重心 G の位置ベクトル |
| | | IJ | **76** ($\frac{\sqrt{7}}{6}$) | 線分長 $|\overrightarrow{PG}|$ の計算 |
| | | KL | **43** ($\frac{4}{3}$) | 共線条件 $\overrightarrow{AG} = \frac{4}{3}\overrightarrow{AP}$ |
| | 問2 | MNO | **132** ($\frac{-1 \pm \sqrt{3}i}{2}$) | 複素数比の方程式の解 |
| | | P | **1** | 複素数比の絶対値 |
| | | QR | **23** ($\pm \frac{2}{3}\pi$) | 複素数比の偏角 |
| | | STU | **132** ($\frac{1 \pm \sqrt{3}i}{2}$) | 複素数式の因数変形 |
| | | V | **3** | 線分長 $|\beta - \alpha|$ |
| | | WXY | **934** ($\frac{9\sqrt{3}}{4}$) | 三角形 ABC の面積 |
| **第III問** | 前半 | AB | **32** ($3/2$) | $\theta = \pi/3$ のときの線分長 $\ell$ |
| | | CDE | **434** ($|4t^3 - 4t|$) | 3倍角の公式による関数化 |
| | | FGH | **432** ($4(3t^2 - 1)$) | 導関数 $g'(t)$ |
| | | IJ | **33** ($\pm\frac{\sqrt{3}}{3}$) | 最大値をとる $\cos\theta$ |
| | | KLM | **839** ($\frac{8\sqrt{3}}{9}$) | 線分長 $\ell$ の最大値 |
| | 後半 | N | **0** ($\frac{\sqrt{6}}{3}$) | 組 1 の点 P の $y$ 座標 |
| | | OP | **56** ($-\frac{5\sqrt{3}}{9}, \frac{\sqrt{6}}{9}$) | 組 1 の点 Q の座標 |
| | | Q | **0** ($\frac{\sqrt{6}}{3}$) | 組 2 の点 P の $y$ 座標 |
| | | RS | **46** ($\frac{5\sqrt{3}}{9}, \frac{\sqrt{6}}{9}$) | 組 2 の点 Q の座標 |
| **第IV問** | 前半 | AB | **11** ($1 - 1/x$) | 導関数 $f'(x)$ |
| | | C, D | **1, 0** | $x = 1$ における最小値 0 |
| | | EF | **22** ($x^2/(2k)$) | 不定積分の 2次項 |
| | | G | **1** ($x(\log x - 1)$) | 不定積分の対数項 |
| | | HIJK | **2211** ($\frac{2n+1}{2k}$) | 面積 $S$ の定積分展開式 |
| | 後半 | LMN | **222** ($\frac{2k-(2n+1)}{2k^2}$) | 面積 $S$ の $k$ 微分 $\frac{dS}{dk}$ |
| | | OP | **12** ($n + 1/2$) | 最小値をとる $k$ の値 |
| | | QRSTUV | **111222** | 最小値 $a_n$ の対数表示式 |
| | | W | **0** | 極限値 $\lim_{n\to\infty} a_n = 0$ |

---

## 逐問詳細推導与解説

"""

for s in explanations["sections"]:
    md_content += f"\n---\n\n## {s['sectionTitle']}\n\n"
    md_content += f"**【考査考点】**：{', '.join(s['points'])}\n\n"
    md_content += s["detailedSolution"] + "\n"

out_md = Path("docs/explanations/2019-1-math-c2-solutions.md")
out_md.parent.mkdir(parents=True, exist_ok=True)
out_md.write_text(md_content, encoding="utf-8")

# Save JSON
out_json = Path("work/2019-1-math-c2/explanations.json")
out_json.parent.mkdir(parents=True, exist_ok=True)
out_json.write_text(json.dumps(explanations, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"Generated {out_md} and {out_json} successfully.")
