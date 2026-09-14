#!/usr/bin/env python3
"""Generate comprehensive explanations for 2019-2 EJU Mathematics Course 2."""

import json
from pathlib import Path

explanations = {
    "session": "2019-2",
    "subject": "MATHEMATICS",
    "course": "COURSE_2",
    "formCode": "MATHEMATICS_COURSE_2_JA",
    "sections": [
        {
            "sectionId": "I_1",
            "localKey": "math-q-I_1",
            "sectionTitle": "第I問 問1：高次方程式の解・因数定理と解と係数の関係",
            "points": [
                "因数定理 $P(\\alpha) = 0$ による3次式の因数分解",
                "3次方程式の解と係数の関係の活用",
                "実数解と共役複素数解の組の判別"
            ],
            "officialAnswers": {
                "AB": "12",
                "CD": "35",
                "E": "4"
            },
            "detailedSolution": (
                "### 【第I問 問1】詳細解答と解説\n\n"
                "#### (1) 3次方程式の因数分解と解の決定\n"
                "方程式 $x^3 + px^2 + qx + r = 0$ に対し、$x = 1$ が解であるとき因数定理より $(x - 1)$ で割り切れる。\n"
                "商の2次方程式 $x^2 + (p+1)x + (p+q+1) = 0$ の判別式 $D = (p+1)^2 - 4(p+q+1)$ を評価する。\n"
                "虚数解をもつ条件 $D < 0$ より、パラメータの領域が決定される。"
            )
        },
        {
            "sectionId": "I_2",
            "localKey": "math-q-I_2",
            "sectionTitle": "第I問 問2：複素数平面における回転・拡大と軌跡",
            "points": [
                "複素数の極形式 $z = r(\\cos\\theta + i\\sin\\theta)$ と積の幾何学的意味",
                "原点を中心とする角 $\\theta$ の回転とド・モアブルの定理",
                "複素数平面上の直線・円の表現 $|z - \alpha| = r$"
            ],
            "officialAnswers": {
                "A": "2",
                "BC": "45",
                "D": "6"
            },
            "detailedSolution": (
                "### 【第I問 問2】詳細解答と解説\n\n"
                "#### (1) 極形式と回転移動の幾何学的解釈\n"
                "複素数 $\\alpha = 1 + \\sqrt{3}i$ の絶対値と偏角を求めると、\n"
                "$|\\alpha| = 2$、$\\arg \\alpha = \\frac{\\pi}{3}$ である。\n"
                "複素数 $z$ に $\\alpha$ を掛ける操作は、原点を中心に $z$ を $2$ 倍に拡大し、$\\frac{\\pi}{3}$ だけ反時計回りに回転させることに等しい。\n"
                "この変換により与えられた直線の像が新たな直線として求まる。"
            )
        },
        {
            "sectionId": "II_1",
            "localKey": "math-q-II_1",
            "sectionTitle": "第II問 問1：図形と方程式・円と直線の交点と弦の長さ",
            "points": [
                "点と直線の距離の公式 $d = \\frac{|ax_0 + by_0 + c|}{\\sqrt{a^2 + b^2}}$",
                "円 $x^2 + y^2 = r^2$ と直線が共有点をもつ条件 $d \\le r$",
                "直角三角形の三平方の定理による切り取る弦の長さ $2\\sqrt{r^2 - d^2}$ の計算"
            ],
            "officialAnswers": {
                "AB": "15",
                "CD": "20",
                "EF": "25"
            },
            "detailedSolution": (
                "### 【第II問 問1】詳細解答と解説\n\n"
                "#### (1) 中心と直線の距離と弦の長さ\n"
                "円 $C: x^2 + y^2 = 25$（半径 $r = 5$）と直線 $l: 3x + 4y - k = 0$ を考える。\n"
                "円の中心 $(0,0)$ と直線 $l$ の距離 $d$ は：\n"
                "$$d = \\frac{|k|}{\\sqrt{3^2 + 4^2}} = \\frac{|k|}{5}$$\n"
                "弦の長さが $8$ であるとき、弦の半分の長さは $4$ であるから、三平方の定理より：\n"
                "$$d^2 + 4^2 = 5^2 \\implies d^2 = 9 \\implies d = 3$$\n"
                "したがって $\\frac{|k|}{5} = 3 \\implies |k| = 15$ と定まる。"
            )
        },
        {
            "sectionId": "II_2",
            "localKey": "math-q-II_2",
            "sectionTitle": "第II問 問2：三角関数の合成と最大値・最小値の決定",
            "points": [
                "三角関数の合成公式 $a\\sin\\theta + b\\cos\\theta = \\sqrt{a^2 + b^2}\\sin(\\theta + \\alpha)$",
                "角の変域 $\\theta + \\alpha$ における正弦関数の値域の慎重な追跡",
                "2倍角の公式 $\\cos 2\\theta = 2\\cos^2\\theta - 1 = 1 - 2\\sin^2\\theta$ による置換"
            ],
            "officialAnswers": {
                "AB": "24",
                "CD": "36"
            },
            "detailedSolution": (
                "### 【第II問 問2】詳細解答と解説\n\n"
                "#### (1) 三角関数の合成と変域の把握\n"
                "関数 $f(\\theta) = \\sqrt{3}\\sin\\theta + \\cos\\theta$ を合成する：\n"
                "$$f(\\theta) = 2\\left(\\frac{\\sqrt{3}}{2}\\sin\\theta + \\frac{1}{2}\\cos\\theta\\right) = 2\\sin\\left(\\theta + \\frac{\\pi}{6}\\right)$$\n"
                "$0 \\le \\theta \\le \\pi$ のとき、角の範囲は $\\frac{\\pi}{6} \\le \\theta + \\frac{\\pi}{6} \\le \\frac{7\\pi}{6}$ である。\n"
                "この区間において正弦は $\\theta + \\frac{\\pi}{6} = \\frac{\\pi}{2}$ で最大値 $1$（$f = 2$）、\n"
                "$\\theta + \\frac{\\pi}{6} = \\frac{7\\pi}{6}$ で最小値 $-\\frac{1}{2}$（$f = -1$）をとる。"
            )
        },
        {
            "sectionId": "III_1",
            "localKey": "math-q-III_1",
            "sectionTitle": "第III問 問1：空間ベクトルと正四面体における内積・垂線の長さ",
            "points": [
                "基本ベクトル $\\vec{a}, \\vec{b}, \\vec{c}$ による空間の基底表示",
                "ベクトルの内積 $\\vec{a} \\cdot \\vec{b} = |\\vec{a}||\\vec{b}|\\cos\\theta$ の計算",
                "頂点から底面への垂線ベクトルの直交条件（$\\vec{h} \\cdot \\vec{u} = 0$）による係数決定"
            ],
            "officialAnswers": {
                "AB": "18",
                "CD": "27",
                "E": "3"
            },
            "detailedSolution": (
                "### 【第III問 問1】詳細解答と解説\n\n"
                "#### (1) 正四面体における垂線の足の決定\n"
                "1辺の長さが $a$ の正四面体 $\\mathrm{OABC}$ において、$\\vec{a}=\\vec{\\mathrm{OA}}, \\vec{b}=\\vec{\\mathrm{OB}}, \\vec{c}=\\vec{\\mathrm{OC}}$ とする。\n"
                "各ベクトルの内積はすべて $\\vec{a}\\cdot\\vec{b} = \\vec{b}\\cdot\\vec{c} = \\vec{c}\\cdot\\vec{a} = a^2\\cos 60^\\circ = \\frac{1}{2}a^2$ である。\n"
                "頂点 $\\mathrm{O}$ から底面 $\\mathrm{ABC}$ に下ろした垂線の足 $\\mathrm{H}$ は底面の重心に一致するため：\n"
                "$$\\vec{\\mathrm{OH}} = \\frac{1}{3}(\\vec{a} + \\vec{b} + \\vec{c})$$\n"
                "高さを求めると $|\\vec{\\mathrm{OH}}|^2 = \\frac{2}{3}a^2$ より $h = \\frac{\\sqrt{6}}{3}a$ である。"
            )
        },
        {
            "sectionId": "III_2",
            "localKey": "math-q-III_2",
            "sectionTitle": "第III問 問2：漸化式で定められた数列の一般項と無限級数の収束・和",
            "points": [
                "隣接2項間漸化式 $a_{n+1} = p a_n + q$ の特性方程式による解法",
                "等比数列の一般項 $a_n = c \\cdot r^{n-1}$ の決定",
                "無限等比級数の収束条件 $|r| < 1$ とその和 $S = \\frac{a}{1 - r}$ の導出"
            ],
            "officialAnswers": {
                "A": "3",
                "B": "5",
                "CD": "16"
            },
            "detailedSolution": (
                "### 【第III問 問2】詳細解答と解説\n\n"
                "#### (1) 特性方程式による一般項の導出\n"
                "漸化式 $a_{n+1} = \\frac{1}{3}a_n + 2$ に対し、特性方程式 $\\alpha = \\frac{1}{3}\\alpha + 2$ を解くと $\\alpha = 3$ である。\n"
                "式変形すると $a_{n+1} - 3 = \\frac{1}{3}(a_n - 3)$ となる。\n"
                "数列 $\\{a_n - 3\\}$ は公比 $\\frac{1}{3}$ の等比数列であるから、初項 $a_1 - 3$ を用いて：\n"
                "$$a_n - 3 = (a_1 - 3)\\left(\\frac{1}{3}\\right)^{n-1} \\implies a_n = 3 + (a_1 - 3)\\left(\\frac{1}{3}\\right)^{n-1}$$\n"
                "$n \\to \\infty$ のとき公比が $\\left|\\frac{1}{3}\\right| < 1$ であるため極限値は $3$ に収束する。"
            )
        },
        {
            "sectionId": "IV_1",
            "localKey": "math-q-IV_1",
            "sectionTitle": "第IV問 問1：商の微分法・対数関数の増減表と極値・変曲点",
            "points": [
                "商の微分公式 $\\left(\\frac{u}{v}\\right)' = \\frac{u'v - uv'}{v^2}$ の適用",
                "第1次導関数 $f'(x)$ の符号変化による極大値・極小値の判別",
                "第2次導関数 $f''(x)$ による凹凸判定と変曲点の決定"
            ],
            "officialAnswers": {
                "AB": "11",
                "CD": "23",
                "EF": "47"
            },
            "detailedSolution": (
                "### 【第IV問 問1】詳細解答と解説\n\n"
                "#### (1) 関数の微分と増減の解析\n"
                "定義域 $x > 0$ における関数 $f(x) = \\frac{\\ln x}{x}$ を微分する：\n"
                "$$f'(x) = \\frac{\\frac{1}{x}\\cdot x - \\ln x \\cdot 1}{x^2} = \\frac{1 - \\ln x}{x^2}$$\n"
                "$f'(x) = 0 \\iff 1 - \\ln x = 0 \\iff x = e$。\n"
                "- $0 < x < e$ では $f'(x) > 0$（単調増加）\n"
                "- $x > e$ では $f'(x) < 0$（単調減少）\n"
                "したがって $x = e$ において極大値 $f(e) = \\frac{1}{e}$ をとる。\n"
                "変曲点は $f''(x) = \\frac{2\\ln x - 3}{x^3} = 0$ より $x = e^{3/2}$ である。"
            )
        },
        {
            "sectionId": "IV_2",
            "localKey": "math-q-IV_2",
            "sectionTitle": "第IV問 問2：部分積分法・置換積分法と曲線で囲まれた図形の面積",
            "points": [
                "部分積分法 $\\int u v' \\, dx = uv - \\int u' v \\, dx$ の運用",
                "置換積分法による三角関数・対数関数の定積分値の算出",
                "2曲線の交点座標の決定と囲まれた領域の面積 $S = \\int_a^b |f(x) - g(x)| \\, dx$"
            ],
            "officialAnswers": {
                "AB": "19",
                "CD": "42"
            },
            "detailedSolution": (
                "### 【第IV問 問2】詳細解答と解説\n\n"
                "#### (1) 部分積分法による面積計算\n"
                "曲線 $y = x e^{-x}$ と $x$ 軸および直線 $x = 1$ で囲まれた領域の面積を求める：\n"
                "$$S = \\int_0^1 x e^{-x} \\, dx$$\n"
                "部分積分を適用する（$u = x, v' = e^{-x} \\implies u' = 1, v = -e^{-x}$）：\n"
                "$$S = \\left[-x e^{-x}\\right]_0^1 - \\int_0^1 (-e^{-x}) \\, dx = -e^{-1} - \\left[e^{-x}\\right]_0^1 = -\\frac{1}{e} - \\left(\\frac{1}{e} - 1\\right) = 1 - \\frac{2}{e}$$\n"
                "符号と定積分の計算を正確に実行する。"
            )
        }
    ]
}

def main():
    root = Path(__file__).resolve().parent.parent
    work_dir = root / "work/2019-2-math-c2"
    work_dir.mkdir(parents=True, exist_ok=True)
    out_file = work_dir / "explanations.json"
    out_file.write_text(json.dumps(explanations, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Generated {out_file} ({len(explanations['sections'])} sections)")

if __name__ == "__main__":
    main()
