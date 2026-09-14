#!/usr/bin/env python3
"""Generate comprehensive pedagogical explanations for 2012-1 EJU Math Course 1 (8 questions)."""

import json
from pathlib import Path

math_c1_questions = [
    {
        "q_num": 1,
        "localKey": "math-q-I_1",
        "answer_ref": "MATH_C1:I_1",
        "answer": "ABCD: -273, EF: 46, G: 4, HI: 43, J: 1",
        "title": "数学 コース1 第I問 [1]：2次関数の平行移動と接線条件",
        "points": [
            "2次関数 $y = 4x^2 + 2ax + b$ のグラフを $x$ 軸方向に $a$，$y$ 軸方向に $1-7a$ だけ平行移動する変換",
            "平行移動後のグラフが点 $(0, 4)$ を通る条件から $b = -2a^2 + 7a + 3$ の導出",
            "移動後の2次関数 $y = 4x^2 - 6ax + 4$ の決定",
            "判別式 $D = 0$ による接線条件から $a = \\frac{4}{3}$，接点 $x = 1$ の算出"
        ],
        "solution": (
            "**【題目大意】**\n"
            "$a, b$ を定数とし，$a > 0$ とする。2次関数 $y = 4x^2 + 2ax + b$ のグラフを $x$ 軸方向に $a$，$y$ 軸方向に $1 - 7a$ だけ平行移動する。\n"
            "平行移動後のグラフが点 $(0, 4)$ を通るとき，$b$ を $a$ で表し，移動後の2次関数を求め，さらにそのグラフが $x$ 軸に接するときの $a$ と接点を求める。\n\n"
            "**【公式正解】**\n"
            "正解：\n"
            "$\\text{ABCD} = -273$\n"
            "$\\text{EF} = 46$\n"
            "$\\text{G} = 4$\n"
            "$\\text{HI} = 43$\n"
            "$\\text{J} = 1$\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "1. **平行移動後の2次関数の導出**：\n"
            "元の関数 $y = 4x^2 + 2ax + b$ のグラフを $x$ 軸方向に $a$，$y$ 軸方向に $1 - 7a$ だけ平行移動すると：\n"
            "$$y - (1 - 7a) = 4(x - a)^2 + 2a(x - a) + b$$\n"
            "右辺を展開する：\n"
            "$$y = 4(x^2 - 2ax + a^2) + 2a(x - a) + b + 1 - 7a$$\n"
            "$$= 4x^2 - 8ax + 4a^2 + 2ax - 2a^2 + b + 1 - 7a$$\n"
            "$$= 4x^2 - 6ax + (2a^2 + b + 1 - 7a)$$\n\n"
            "2. **点 $(0, 4)$ を通る条件**：\n"
            "移動後のグラフが $(0, 4)$ を通るため：\n"
            "$$4 = 2a^2 + b + 1 - 7a$$\n"
            "$$b = -2a^2 + 7a + 3$$\n"
            "したがって，$\\text{A} = -2, \\text{B} = 7, \\text{C} = 3$（$\\text{ABCD} = -273$ → $A=-$, $B=2$, $C=7$, $D=3$）である。\n\n"
            "3. **移動後の2次関数の定数項**：\n"
            "$b = -2a^2 + 7a + 3$ を代入すると，定数項は：\n"
            "$$2a^2 + (-2a^2 + 7a + 3) + 1 - 7a = 4$$\n"
            "したがって，移動後の2次関数は：\n"
            "$$y = 4x^2 - 6ax + 4$$\n"
            "これより $\\text{E} = 4, \\text{F} = 6$（$\\text{EF} = 46$），$\\text{G} = 4$ である。\n\n"
            "4. **$x$ 軸に接する条件**：\n"
            "2次関数 $y = 4x^2 - 6ax + 4$ が $x$ 軸に接するための条件は判別式 $D = 0$ である：\n"
            "$$D = (-6a)^2 - 4 \\cdot 4 \\cdot 4 = 36a^2 - 64 = 0$$\n"
            "$$a^2 = \\frac{64}{36} = \\frac{16}{9}$$\n"
            "$a > 0$ より：\n"
            "$$a = \\frac{4}{3}$$\n"
            "これより $\\text{H} = 4, \\text{I} = 3$（$\\text{HI} = 43$）である。\n\n"
            "5. **接点の $x$ 座標**：\n"
            "接点の $x$ 座標は：\n"
            "$$x = \\frac{6a}{2 \\cdot 4} = \\frac{6 \\cdot \\frac{4}{3}}{8} = \\frac{8}{8} = 1$$\n"
            "これより $\\text{J} = 1$ である。\n\n"
            "**【考査考点】**\n"
            "2次関数の平行移動，通過点条件による未定係数の決定，判別式による接線条件の適用。"
        )
    },
    {
        "q_num": 2,
        "localKey": "math-q-I_2",
        "answer_ref": "MATH_C1:I_2",
        "answer": "K: 0, LM: -7, NOP: 422, Q: 5, R: 2, ST: 11",
        "title": "数学 コース1 第I問 [2]：多項式の有理数条件と素数条件",
        "points": [
            "多項式 $P = x^2 + 2(a-1)x - 8a - 8$ に $x = 1 - \\sqrt{2}$ を代入して有理数条件を適用",
            "因数分解 $P = (x - 4)(x + 2a + 2)$ の導出",
            "$x, a$ が正の整数のとき $P$ が素数となる条件 $x = 5, a = 2$ の決定"
        ],
        "solution": (
            "**【題目大意】**\n"
            "多項式 $P = x^2 + 2(a - 1)x - 8a - 8$ を考える。\n"
            "(1) $a$ を有理数とし，$x = 1 - \\sqrt{2}$ のとき $P$ が有理数になる $a$ と $P$ の値を求める。\n"
            "(2) $P$ を因数分解し，$x, a$ が正の整数で $P$ が素数になる条件を求める。\n\n"
            "**【公式正解】**\n"
            "正解：\n"
            "$\\text{K} = 0$\n"
            "$\\text{LM} = -7$\n"
            "$\\text{NOP} = 422$\n"
            "$\\text{Q} = 5$\n"
            "$\\text{R} = 2$\n"
            "$\\text{ST} = 11$\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "1. **(1) 有理数条件**：\n"
            "$x = 1 - \\sqrt{2}$ を代入する：\n"
            "$$P = (1 - \\sqrt{2})^2 + 2(a - 1)(1 - \\sqrt{2}) - 8a - 8$$\n"
            "$$= 1 - 2\\sqrt{2} + 2 + 2(a - 1) - 2(a - 1)\\sqrt{2} - 8a - 8$$\n"
            "$$= (3 + 2a - 2 - 8a - 8) + (-2 - 2a + 2)\\sqrt{2}$$\n"
            "$$= (-6a - 7) + (-2a)\\sqrt{2}$$\n"
            "$P$ が有理数であるための条件は $\\sqrt{2}$ の係数が $0$ であること：\n"
            "$$-2a = 0 \\implies a = 0$$\n"
            "これより $\\text{K} = 0$ である。\n"
            "このとき $P = -6(0) - 7 = -7$ である。\n"
            "これより $\\text{LM} = -7$ である。\n\n"
            "2. **(2) 因数分解**：\n"
            "$P = x^2 + 2(a - 1)x - 8(a + 1)$ を因数分解する。\n"
            "定数項 $-8(a + 1)$ と $x$ の係数 $2(a - 1)$ から，因数を推定する：\n"
            "$$(x - 4)(x + 2a + 2) = x^2 + (2a + 2 - 4)x - 4(2a + 2) = x^2 + (2a - 2)x - 8a - 8$$\n"
            "$$= x^2 + 2(a - 1)x - 8(a + 1) = P$$\n"
            "したがって，$\\text{N} = 4, \\text{O} = 2, \\text{P} = 2$（$\\text{NOP} = 422$）である。\n\n"
            "3. **$P$ が素数となる条件**：\n"
            "$P = (x - 4)(x + 2a + 2)$ において，$x, a$ は正の整数（$x \\geq 1, a \\geq 1$）である。\n"
            "$P$ が素数であるためには，2つの因数の一方が $1$ で他方が素数でなければならない。\n"
            "$a \\geq 1$ のとき $x + 2a + 2 \\geq x + 4 \\geq 5 > 1$ であるから，\n"
            "$$x - 4 = 1 \\implies x = 5$$\n"
            "これより $\\text{Q} = 5$ である。\n\n"
            "4. **最小の $a$ と $P$ の値**：\n"
            "$x = 5$ のとき $P = 1 \\cdot (5 + 2a + 2) = 2a + 7$ である。\n"
            "$P$ が素数となる最小の正の整数 $a$ を求める：\n"
            "- $a = 1$：$P = 9 = 3^2$（合成数，不適）\n"
            "- $a = 2$：$P = 11$（素数 ✓）\n"
            "したがって $a = 2$ で $P = 11$ である。\n"
            "これより $\\text{R} = 2, \\text{ST} = 11$ である。\n\n"
            "**【考査考点】**\n"
            "無理数を含む式の有理化条件，多項式の因数分解，整数条件と素数判定。"
        )
    },
    {
        "q_num": 3,
        "localKey": "math-q-II_1",
        "answer_ref": "MATH_C1:II_1",
        "answer": "ABC: 881, D: 5, E: 4, FG: 04, HI: 32, J: 1, KL: 16",
        "title": "数学 コース1 第II問 [1]：サイコロの確率と点の移動",
        "points": [
            "3の倍数の目が出る確率 $\\frac{1}{3}$，それ以外の確率 $\\frac{2}{3}$ の二項分布の適用",
            "到達し得る5個の点 $(k, 4-k)$（$0 \\leq k \\leq 4$）の列挙",
            "確率 $p_k = \\binom{4}{k}\\left(\\frac{1}{3}\\right)^k\\left(\\frac{2}{3}\\right)^{4-k}$ の最大値・最小値の決定",
            "条件付き確率（$(1,1)$ 経由で $(2,2)$ に到達）の乗法計算"
        ],
        "solution": (
            "**【題目大意】**\n"
            "座標平面上の点 P は原点 $(0,0)$ にあり，サイコロを投げて3の倍数の目が出れば $x$ 軸正方向に1，それ以外なら $y$ 軸正方向に1移動する。サイコロを4回投げるとき，到達確率を求める。\n\n"
            "**【公式正解】**\n"
            "正解：\n"
            "$\\text{ABC} = 881$（$A/BC = 8/81$）\n"
            "$\\text{D} = 5$\n"
            "$\\text{E} = 4$\n"
            "$\\text{FG} = 04$（$F = 0, G = 4$）\n"
            "$\\text{HI} = 32$\n"
            "$\\text{J} = 1$\n"
            "$\\text{KL} = 16$\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "1. **基本確率の設定**：\n"
            "1個のサイコロで3の倍数の目（3, 6）が出る確率は $p = \\frac{2}{6} = \\frac{1}{3}$，\n"
            "3の倍数でない目（1, 2, 4, 5）が出る確率は $q = \\frac{4}{6} = \\frac{2}{3}$ である。\n\n"
            "2. **(1) P が $(3, 1)$ に到達する確率**：\n"
            "4回中3回 $x$ 方向，1回 $y$ 方向に移動する：\n"
            "$$\\binom{4}{3}\\left(\\frac{1}{3}\\right)^3\\left(\\frac{2}{3}\\right)^1 = 4 \\cdot \\frac{1}{27} \\cdot \\frac{2}{3} = \\frac{8}{81}$$\n"
            "これより $\\text{A} = 8, \\text{BC} = 81$（$\\text{ABC} = 881$）である。\n\n"
            "3. **(2) 到達し得る点の個数と座標**：\n"
            "4回投げるとき，$x$ 方向に $k$ 回，$y$ 方向に $4-k$ 回移動するから，到達点は：\n"
            "$$(k, 4-k) \\quad (0 \\leq k \\leq 4)$$\n"
            "全部で $5$ 個の点に到達し得る。$\\text{D} = 5, \\text{E} = 4, \\text{F} = 0, \\text{G} = 4$ である。\n\n"
            "4. **$p_k$ の最大値と最小値**：\n"
            "$$p_k = \\binom{4}{k}\\left(\\frac{1}{3}\\right)^k\\left(\\frac{2}{3}\\right)^{4-k}$$\n"
            "各 $p_k$ を計算すると（分母は $3^4 = 81$）：\n"
            "| $k$ | $\\binom{4}{k}$ | $p_k$ |\n"
            "|-----|------------------|--------|\n"
            "| 0 | 1 | $\\frac{16}{81}$ |\n"
            "| 1 | 4 | $\\frac{32}{81}$ |\n"
            "| 2 | 6 | $\\frac{24}{81}$ |\n"
            "| 3 | 4 | $\\frac{8}{81}$ |\n"
            "| 4 | 1 | $\\frac{1}{81}$ |\n"
            "最大値は $p_1 = \\frac{32}{81}$，最小値は $p_4 = \\frac{1}{81}$ である。\n"
            "これより $\\text{HI} = 32, \\text{J} = 1$ である。\n\n"
            "5. **(3) $(1,1)$ を通り $(2,2)$ に到達する確率**：\n"
            "2回目終了時に $(1,1)$ にいる確率：\n"
            "$$\\binom{2}{1}\\left(\\frac{1}{3}\\right)^1\\left(\\frac{2}{3}\\right)^1 = 2 \\cdot \\frac{1}{3} \\cdot \\frac{2}{3} = \\frac{4}{9}$$\n"
            "$(1,1)$ から残り2回で $(2,2)$ に到達する確率（さらに $x$方向1回，$y$方向1回）：\n"
            "$$\\binom{2}{1}\\left(\\frac{1}{3}\\right)^1\\left(\\frac{2}{3}\\right)^1 = \\frac{4}{9}$$\n"
            "したがって：\n"
            "$$P = \\frac{4}{9} \\times \\frac{4}{9} = \\frac{16}{81}$$\n"
            "これより $\\text{KL} = 16$ である。\n\n"
            "**【考査考点】**\n"
            "二項分布，場合の数と確率，条件付き確率の乗法定理。"
        )
    },
    {
        "q_num": 4,
        "localKey": "math-q-II_2",
        "answer_ref": "MATH_C1:II_2",
        "answer": "MN: 29, O: 3, PQ: 16, RST: 336",
        "title": "数学 コース1 第II問 [2]：三角形の内分点と面積比",
        "points": [
            "三角形 ABC の各辺を $k:(1-k)$ に内分する点 D, E, F による面積比",
            "$k = \\frac{1}{3}$ のとき $\\triangle ADF = \\frac{2}{9} \\triangle ABC$ と $\\triangle ABC = 3 \\triangle DEF$",
            "$\\triangle DEF = \\frac{1}{2} \\triangle ABC$ となる条件 $k(1-k) = \\frac{1}{6}$ の導出",
            "$k = \\frac{3 - \\sqrt{3}}{6}$ の解法"
        ],
        "solution": (
            "**【題目大意】**\n"
            "三角形 ABC の3辺 AB, BC, CA を $k:(1-k)$ の比に内分する点をそれぞれ D, E, F とする（$0 < k \\leq \\frac{1}{2}$）。\n"
            "(1) $k = \\frac{1}{3}$ のとき，$\\triangle ABC$ は $\\triangle DEF$ の何倍か。\n"
            "(2) $\\triangle DEF = \\frac{1}{2} \\triangle ABC$ となる $k$ を求める。\n\n"
            "**【公式正解】**\n"
            "正解：\n"
            "$\\text{MN} = 29$\n"
            "$\\text{O} = 3$\n"
            "$\\text{PQ} = 16$\n"
            "$\\text{RST} = 336$\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "1. **(1) $k = \\frac{1}{3}$ のときの面積比**：\n"
            "辺 AB 上の点 D は $AD:DB = k:(1-k) = 1:2$ に内分する。同様に BC 上の E，CA 上の F もそれぞれ $1:2$ に内分する。\n"
            "三角形 ADF について：\n"
            "$$\\frac{\\triangle ADF}{\\triangle ABC} = \\frac{AD}{AB} \\cdot \\frac{AF}{AC} = k \\cdot (1-k)$$\n"
            "$k = \\frac{1}{3}$ のとき：\n"
            "$$\\frac{\\triangle ADF}{\\triangle ABC} = \\frac{1}{3} \\cdot \\frac{2}{3} = \\frac{2}{9}$$\n"
            "対称性により $\\triangle BED = \\triangle CFE = \\frac{2}{9} \\triangle ABC$ である。\n"
            "これより $\\text{M} = 2, \\text{N} = 9$（$\\text{MN} = 29$）である。\n\n"
            "$$\\triangle DEF = \\triangle ABC - 3 \\cdot \\frac{2}{9} \\triangle ABC = \\left(1 - \\frac{6}{9}\\right)\\triangle ABC = \\frac{1}{3} \\triangle ABC$$\n"
            "したがって $\\triangle ABC = 3 \\triangle DEF$ である。\n"
            "これより $\\text{O} = 3$ である。\n\n"
            "2. **(2) $\\triangle DEF = \\frac{1}{2} \\triangle ABC$ となる条件**：\n"
            "一般に $\\frac{\\triangle DEF}{\\triangle ABC} = 1 - 3k(1-k)$ であるから：\n"
            "$$1 - 3k(1-k) = \\frac{1}{2} \\implies k(1-k) = \\frac{1}{6}$$\n"
            "これより $\\text{P} = 1, \\text{Q} = 6$（$\\text{PQ} = 16$）である。\n\n"
            "$$k^2 - k + \\frac{1}{6} = 0 \\implies 6k^2 - 6k + 1 = 0$$\n"
            "$$k = \\frac{6 \\pm \\sqrt{36 - 24}}{12} = \\frac{6 \\pm \\sqrt{12}}{12} = \\frac{6 \\pm 2\\sqrt{3}}{12} = \\frac{3 \\pm \\sqrt{3}}{6}$$\n"
            "$0 < k \\leq \\frac{1}{2}$ であるから：\n"
            "$$k = \\frac{3 - \\sqrt{3}}{6}$$\n"
            "（$\\frac{3 + \\sqrt{3}}{6} \\approx 0.789 > \\frac{1}{2}$ なので不適。）\n"
            "これより $\\text{R} = 3, \\text{S} = 3, \\text{T} = 6$（$\\text{RST} = 336$）である。\n\n"
            "**【考査考点】**\n"
            "三角形の辺の内分と面積比，2次方程式の解法，根号を含む式の整理。"
        )
    },
    {
        "q_num": 5,
        "localKey": "math-q-III_1",
        "answer_ref": "MATH_C1:III_1",
        "answer": "A: 2, B: 2, C: 4, D: 1, E: 2",
        "title": "数学 コース1 第III問 (前半)：放物線 y=x² 上の2点と交点・面積",
        "points": [
            "放物線 $y = x^2$ 上の点 $A(a, ma+1), B(b, mb+1)$ の座標条件 $x^2 = mx + 1$ の導出",
            "解の公式による $a = \\frac{m - \\sqrt{m^2 + 4}}{2}$，$b = \\frac{m + \\sqrt{m^2 + 4}}{2}$ の表現",
            "直線 AB と $y$ 軸の交点 $c = 1$ の算出",
            "三角形 OAB の面積 $S = \\frac{1}{2}(b - a)$ の導出"
        ],
        "solution": (
            "**【題目大意】**\n"
            "$m$ を実数とする。O を原点とする座標平面上で，放物線 $y = x^2$ とその曲線上にある2点 $A(a, ma+1)$，$B(b, mb+1)$（$a < 0 < b$）を考える。\n"
            "(1) 2点の $x$ 座標 $a, b$ を $m$ で表す。\n"
            "(2) 線分 AB と $y$ 軸の交点を求める。\n"
            "(3) 三角形 OAB の面積を $a, b$ で表す。\n\n"
            "**【公式正解】**\n"
            "正解：\n"
            "$\\text{A} = 2$\n"
            "$\\text{B} = 2$\n"
            "$\\text{C} = 4$\n"
            "$\\text{D} = 1$\n"
            "$\\text{E} = 2$（選択肢 $\\textcircled{2}$：$b - a$）\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "1. **(1) $a, b$ の導出**：\n"
            "点 A は放物線 $y = x^2$ 上にあるから：\n"
            "$$a^2 = ma + 1 \\implies a^2 - ma - 1 = 0$$\n"
            "同様に $b^2 - mb - 1 = 0$ である。\n"
            "すなわち $a, b$ は2次方程式 $x^2 - mx - 1 = 0$ の2つの解である。\n"
            "解の公式より：\n"
            "$$x = \\frac{m \\pm \\sqrt{m^2 + 4}}{2}$$\n"
            "$a < 0 < b$ であるから：\n"
            "$$a = \\frac{m - \\sqrt{m^2 + 4}}{2}, \\quad b = \\frac{m + \\sqrt{m^2 + 4}}{2}$$\n"
            "したがって $\\text{A} = 2, \\text{B} = 2, \\text{C} = 4$（$D = m^2 + 4$）である。\n\n"
            "2. **(2) 直線 AB と $y$ 軸の交点**：\n"
            "2点 A, B はともに $y = mx + 1$ を満たす（$x^2 = mx + 1$ より $y = x^2 = mx + 1$）。\n"
            "したがって直線 AB の方程式は $y = mx + 1$ である。\n"
            "$y$ 軸との交点は $x = 0$ を代入して $y = 1$ であるから，$c = 1$ である。\n"
            "これより $\\text{D} = 1$ である。\n\n"
            "3. **(3) 三角形 OAB の面積**：\n"
            "原点 O$(0, 0)$ から直線 $y = mx + 1$（すなわち $mx - y + 1 = 0$）までの距離は：\n"
            "$$d = \\frac{|1|}{\\sqrt{m^2 + 1}} = \\frac{1}{\\sqrt{m^2 + 1}}$$\n"
            "線分 AB の長さは：\n"
            "$$|AB| = \\sqrt{1 + m^2} \\cdot |b - a| = \\sqrt{1 + m^2} \\cdot (b - a)$$\n"
            "三角形 OAB の面積は：\n"
            "$$S = \\frac{1}{2} |AB| \\cdot d = \\frac{1}{2} \\sqrt{1 + m^2} \\cdot (b - a) \\cdot \\frac{1}{\\sqrt{m^2 + 1}} = \\frac{1}{2}(b - a)$$\n"
            "したがって $\\text{E} = 2$（選択肢 $\\textcircled{2}$：$b - a$）である。\n\n"
            "**【考査考点】**\n"
            "放物線と直線の関係，2次方程式の解と係数の関係，点と直線の距離公式，三角形の面積計算。"
        )
    },
    {
        "q_num": 6,
        "localKey": "math-q-III_2",
        "answer_ref": "MATH_C1:III_2",
        "answer": "FGH: 124, I: 0, J: 1",
        "title": "数学 コース1 第III問 (後半)：面積の m による表現と最小値",
        "points": [
            "面積 $S = \\frac{1}{2}(b - a) = \\frac{1}{2}\\sqrt{m^2 + 4}$ の表現",
            "$S$ の最小値が $m = 0$ のとき $S = 1$ であることの導出"
        ],
        "solution": (
            "**【題目大意】**\n"
            "前半で得た面積 $S = \\frac{1}{2}(b - a)$ を $m$ の式で表し，$S$ の最小値とそのときの $m$ の値を求める。\n\n"
            "**【公式正解】**\n"
            "正解：\n"
            "$\\text{FGH} = 124$\n"
            "$\\text{I} = 0$\n"
            "$\\text{J} = 1$\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "1. **面積の $m$ による表現**：\n"
            "前半の結果より：\n"
            "$$b - a = \\frac{m + \\sqrt{m^2 + 4}}{2} - \\frac{m - \\sqrt{m^2 + 4}}{2} = \\sqrt{m^2 + 4}$$\n"
            "したがって：\n"
            "$$S = \\frac{1}{2}\\sqrt{m^2 + 4} = \\frac{1}{2}(m^2 + 4)^{1/2}$$\n"
            "これより $\\text{F} = 1, \\text{G} = 2, \\text{H} = 4$（$\\text{FGH} = 124$）である。\n\n"
            "2. **$S$ の最小値**：\n"
            "$m^2 \\geq 0$ であるから $m^2 + 4 \\geq 4$ であり，$S = \\frac{1}{2}\\sqrt{m^2 + 4}$ は $m^2 = 0$，すなわち $m = 0$ のとき最小値をとる：\n"
            "$$S_{\\text{min}} = \\frac{1}{2}\\sqrt{4} = \\frac{1}{2} \\cdot 2 = 1$$\n"
            "これより $\\text{I} = 0$（$m = 0$），$\\text{J} = 1$（$S_{\\text{min}} = 1$）である。\n\n"
            "**【考査考点】**\n"
            "根号関数の最小値，2次式の非負性，変数変換による面積関数の解析。"
        )
    },
    {
        "q_num": 7,
        "localKey": "math-q-IV_1",
        "answer_ref": "MATH_C1:IV_1",
        "answer": "ABCD: 1032, EF: -2, G: 1",
        "title": "数学 コース1 第IV問 (前半)：2次式 A+B=0, AB=0 を満たす a の範囲",
        "points": [
            "$A + B = 2x^2 + (2a+3)x + 5 = 0$ の判別式条件による $a$ の範囲の決定",
            "$A = 0$ または $B = 0$ の判別式条件の合併（和集合）による $a$ の範囲"
        ],
        "solution": (
            "**【題目大意】**\n"
            "$a$ を実数とし，$x$ の2次式 $A = x^2 + ax + 1$，$B = x^2 + (a+3)x + 4$ を考える。\n"
            "(1) $A + B = 0$ を満たす実数 $x$ が存在するような $a$ の範囲を求める。\n"
            "(2) $AB = 0$ を満たす実数 $x$ が存在するような $a$ の範囲を求める。\n\n"
            "**【公式正解】**\n"
            "正解：\n"
            "$\\text{ABCD} = 1032$\n"
            "$\\text{EF} = -2$\n"
            "$\\text{G} = 1$\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "1. **(1) $A + B = 0$ の条件**：\n"
            "$$A + B = 2x^2 + (2a + 3)x + 5 = 0$$\n"
            "実数 $x$ が存在するための条件は判別式 $D \\geq 0$：\n"
            "$$D = (2a + 3)^2 - 4 \\cdot 2 \\cdot 5 = 4a^2 + 12a + 9 - 40 = 4a^2 + 12a - 31 \\geq 0$$\n"
            "解の公式より：\n"
            "$$a = \\frac{-12 \\pm \\sqrt{144 + 496}}{8} = \\frac{-12 \\pm \\sqrt{640}}{8} = \\frac{-12 \\pm 8\\sqrt{10}}{8} = \\frac{-3 \\pm 2\\sqrt{10}}{2}$$\n"
            "したがって：\n"
            "$$a \\leq \\frac{-3 - 2\\sqrt{10}}{2} = -\\sqrt{10} - \\frac{3}{2} \\quad \\text{または} \\quad a \\geq -\\frac{3}{2} + \\sqrt{10} = \\sqrt{10} - \\frac{3}{2}$$\n"
            "これより $\\text{A} = 10, \\text{B} = 3, \\text{C} = 2$（$\\text{ABCD} = 1032$ → $\\sqrt{\\text{AB}} = \\sqrt{10}, \\frac{C}{D} = \\frac{3}{2}$）である。\n\n"
            "2. **(2) $AB = 0$ の条件**：\n"
            "$A = 0$ または $B = 0$ を満たす実数 $x$ が存在すればよい。\n"
            "- **$A = 0$**：$x^2 + ax + 1 = 0$ の判別式 $D_A = a^2 - 4 \\geq 0 \\implies |a| \\geq 2$\n"
            "  すなわち $a \\leq -2$ または $a \\geq 2$\n"
            "- **$B = 0$**：$x^2 + (a+3)x + 4 = 0$ の判別式 $D_B = (a+3)^2 - 16 \\geq 0 \\implies |a+3| \\geq 4$\n"
            "  すなわち $a \\leq -7$ または $a \\geq 1$\n"
            "両者の和集合をとると：\n"
            "$$a \\leq -2 \\quad \\text{または} \\quad a \\geq 1$$\n"
            "これより $\\text{EF} = -2, \\text{G} = 1$ である。\n\n"
            "**【考査考点】**\n"
            "2次方程式の実数解存在条件（判別式），不等式の和集合・共通部分の処理。"
        )
    },
    {
        "q_num": 8,
        "localKey": "math-q-IV_2",
        "answer_ref": "MATH_C1:IV_2",
        "answer": "H: 2, IJ: -1",
        "title": "数学 コース1 第IV問 (後半)：A²+B²=0 を満たす条件",
        "points": [
            "$A^2 + B^2 = 0$ が成り立つのは $A = 0$ かつ $B = 0$ を同時に満たす場合に限ること",
            "連立方程式 $A = B = 0$ の解法（差をとって $3x + 3 = 0 \\implies x = -1$）",
            "$a = 2, x = -1$ の決定"
        ],
        "solution": (
            "**【題目大意】**\n"
            "$A^2 + B^2 = 0$ を満たす実数 $x$ が存在するような $a$ の値と，そのときの $x$ を求める。\n\n"
            "**【公式正解】**\n"
            "正解：\n"
            "$\\text{H} = 2$\n"
            "$\\text{IJ} = -1$\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "1. **$A^2 + B^2 = 0$ の必要十分条件**：\n"
            "実数の2乗は非負であるから，$A^2 \\geq 0$ かつ $B^2 \\geq 0$ である。\n"
            "したがって $A^2 + B^2 = 0$ が成り立つのは：\n"
            "$$A = 0 \\quad \\text{かつ} \\quad B = 0$$\n"
            "の場合に限る。\n\n"
            "2. **連立方程式の解法**：\n"
            "$$\\begin{cases} x^2 + ax + 1 = 0 \\\\ x^2 + (a+3)x + 4 = 0 \\end{cases}$$\n"
            "2式の差をとると：\n"
            "$$3x + 3 = 0 \\implies x = -1$$\n"
            "$x = -1$ を $A = 0$ に代入すると：\n"
            "$$(-1)^2 + a(-1) + 1 = 0 \\implies 2 - a = 0 \\implies a = 2$$\n"
            "検証：$B = (-1)^2 + (2+3)(-1) + 4 = 1 - 5 + 4 = 0$ ✓\n\n"
            "したがって $a = 2, x = -1$ である。\n"
            "これより $\\text{H} = 2, \\text{IJ} = -1$ である。\n\n"
            "**【考査考点】**\n"
            "実数の非負性の利用（$A^2 + B^2 = 0 \\iff A = B = 0$），連立方程式の消去法。"
        )
    }
]

def main():
    out_dir = Path("work/2012-1-math-c1")
    out_dir.mkdir(parents=True, exist_ok=True)

    # Save math-c1 explanations to json
    c1_path = out_dir / "explanations.json"
    with open(c1_path, "w", encoding="utf-8") as f:
        json.dump(math_c1_questions, f, ensure_ascii=False, indent=2)
    print(f"Generated {c1_path} ({len(math_c1_questions)} questions)")

    # Generate markdown documentation
    md_path = Path("docs/explanations/2012-1-math-c1-solutions.md")
    md_path.parent.mkdir(parents=True, exist_ok=True)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# 2012-1 EJU 数学 コース1 詳解\n\n")
        for q in math_c1_questions:
            f.write(f"## {q['title']}\n\n")
            f.write(q["solution"] + "\n\n---\n\n")
    print(f"Generated {md_path}")

if __name__ == "__main__":
    main()

