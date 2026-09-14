#!/usr/bin/env python3
"""Generate comprehensive pedagogical explanations for 2011-2 EJU Math Course 2 (8 questions)."""

import json
from pathlib import Path

math_c2_questions = [
    {
        "q_num": 1,
        "localKey": "math-q-I_1",
        "answer_ref": "I:1",
        "answer": "A: 3, BC: -1, DE: 34, F: 1, G: 4, HIJKL: 12154, M: 1",
        "title": "数学 コース2 第I問 [1]：3次式の展開公式と実数解の導出",
        "points": [
            "3次式の対称展開公式 $(a+b)^3 = a^3 + b^3 + 3ab(a+b)$ の適用",
            "$a^3 = \\frac{1}{\\sqrt{5}-2} = \\sqrt{5}+2$ および $b^3 = 2-\\sqrt{5}$ より $ab = -1, a^3+b^3 = 4$ の算出",
            "$x = a+b$ に関する3次方程式 $x^3 + 3x - 4 = 0$ の立式",
            "因数分解 $(x-1)(x^2+x+4) = 0$ と平方完成による唯一の実数解 $x = 1$ の導出"
        ],
        "solution": (
            "**【題目大意】**\n"
            "2つの実数 $a, b$ が $a^3 = \\frac{1}{\\sqrt{5} - 2}, \\quad b^3 = 2 - \\sqrt{5}$ を満たすとき，$a + b$ の値を求める。\n"
            "$a + b = x$ とおき，$x^3$ を展開して $x$ が満たす3次方程式を導き，それを因数分解して $x = a + b$ を決定する。\n\n"
            "**【公式正解】**\n"
            "正解：\n"
            "$\\text{A} = 3$\n"
            "$\\text{BC} = -1$\n"
            "$\\text{DE} = 34$\n"
            "$\\text{F} = 1$\n"
            "$\\text{G} = 4$\n"
            "$\\text{HIJKL} = 12154$\n"
            "$\\text{M} = 1$\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "1. **3次式の展開と基本対称式の計算**：\n"
            "$x = a + b$ とおくと，3次式の和の立方展開公式より：\n"
            "$$x^3 = (a + b)^3 = a^3 + 3a^2b + 3ab^2 + b^3 = a^3 + b^3 + 3ab(a + b)$$\n"
            "したがって $\\text{A} = 3$ である。\n\n"
            "次に，$a^3$ の分母を有理化する：\n"
            "$$a^3 = \\frac{1}{\\sqrt{5} - 2} = \\frac{\\sqrt{5} + 2}{(\\sqrt{5} - 2)(\\sqrt{5} + 2)} = \\frac{\\sqrt{5} + 2}{5 - 4} = \\sqrt{5} + 2$$\n"
            "与えられた $b^3 = 2 - \\sqrt{5}$ と掛け合わせると：\n"
            "$$a^3 b^3 = (ab)^3 = (\\sqrt{5} + 2)(2 - \\sqrt{5}) = 4 - 5 = -1$$\n"
            "$ab$ は実数であるから：\n"
            "$$ab = \\sqrt[3]{-1} = -1$$\n"
            "したがって $\\text{BC} = -1$ である。\n\n"
            "また，2数の立方和は：\n"
            "$$a^3 + b^3 = (\\sqrt{5} + 2) + (2 - \\sqrt{5}) = 4$$\n\n"
            "2. **$x$ の満たす3次方程式の立式**：\n"
            "これらを $x^3 = a^3 + b^3 + 3ab \\cdot x$ に代入すると：\n"
            "$$x^3 = 4 + 3(-1)x = 4 - 3x$$\n"
            "項を左辺に移項して整理すると：\n"
            "$$x^3 + 3x - 4 = 0$$\n"
            "これより $\\text{D} = 3, \\text{E} = 4$（$\\text{DE} = 34$）である。\n\n"
            "3. **因数分解と実数解の特定**：\n"
            "$x = 1$ を代入すると $1^3 + 3(1) - 4 = 0$ となることから，$(x - 1)$ を因数にもつ。\n"
            "$$x^3 + 3x - 4 = (x^3 - 1) + 3(x - 1) = (x - 1)(x^2 + x + 1) + 3(x - 1)$$\n"
            "$$= (x - 1)(x^2 + x + 1 + 3) = (x - 1)(x^2 + x + 4)$$\n"
            "したがって $\\text{F} = 1, \\text{G} = 4$ である。\n\n"
            "ここで2次因数 $x^2 + x + 4$ を平方完成すると：\n"
            "$$x^2 + x + 4 = \\left(x + \\frac{1}{2}\\right)^2 - \\frac{1}{4} + 4 = \\left(x + \\frac{1}{2}\\right)^2 + \\frac{15}{4}$$\n"
            "実数 $x$ に対して $\\left(x + \\frac{1}{2}\\right)^2 \\geq 0$ であるため，$x^2 + x + 4 \\geq \\frac{15}{4} > 0$ である。\n"
            "これより $\\text{H} = 1, \\text{I} = 2, \\text{JK} = 15, \\text{L} = 4$（$\\text{HIJKL} = 12154$）である。\n\n"
            "したがって，実数解は $x - 1 = 0$ のみであり：\n"
            "$$x = a + b = 1$$\n"
            "これより $\\text{M} = 1$ である。\n\n"
            "**【考査考点】**\n"
            "分母の有理化，3次式の展開公式，対称式の基本変形，高次方程式の因数定理と平方完成による実数解の判別。"
        )
    },
    {
        "q_num": 2,
        "localKey": "math-q-I_2",
        "answer_ref": "I:2",
        "answer": "N: 2, O: 1, P: 0, QR: 15, STUV: 1465, W: 3, X: 1",
        "title": "数学 コース2 第I問 [2]：放物線と直線の位置関係および差の最小値の最大化",
        "points": [
            "放物線 $y = x^2 + ax + a$ と直線 $y = x + 1$ の連立方程式 $x^2 + (a-1)x + (a-1) = 0$",
            "判別式 $D = (a-1)(a-5)$ による共有点の個数の分類（異なる2点：$a<1$ または $a>5$，接する：$a=1, 5$，共有点なし：$1<a<5$）",
            "差の関数 $g(x) = x^2 + (a-1)x + a - 1$ の最小値 $m = -\\frac{1}{4}(a^2 - 6a + 5)$ の導出",
            "$a$ の2次関数 $m(a)$ の平方完成による最大値 $m = 1$（$a = 3$ のとき）の決定"
        ],
        "solution": (
            "**【題目大意】**\n"
            "2つの関数 $y = x^2 + ax + a$ と $y = x + 1$ を考える。\n"
            "(1) 2つの関数の共有点の個数と $a$ の条件を分類する。\n"
            "(2) グラフがつねに上方にある条件のもとで，差の関数の最小値 $m$ を表し，$m$ の最大値とそのときの $a$ を求める。\n\n"
            "**【公式正解】**\n"
            "正解：\n"
            "$\\text{N} = 2$（選択肢 $\\textcircled{2}$：$a < Q$ または $R < a$）\n"
            "$\\text{O} = 1$（選択肢 $\\textcircled{1}$：$a = Q$ または $a = R$）\n"
            "$\\text{P} = 0$（選択肢 $\\textcircled{0}$：$Q < a < R$）\n"
            "$\\text{QR} = 15$\n"
            "$\\text{STUV} = 1465$\n"
            "$\\text{W} = 3$\n"
            "$\\text{X} = 1$\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "1. **(1) 共有点の個数の判定**：\n"
            "2式の差をとって $y$ を消去する：\n"
            "$$x^2 + ax + a = x + 1 \\implies x^2 + (a - 1)x + (a - 1) = 0$$\n"
            "この2次方程式の判別式を $D$ とすると：\n"
            "$$D = (a - 1)^2 - 4 \\cdot 1 \\cdot (a - 1) = (a - 1)[(a - 1) - 4] = (a - 1)(a - 5)$$\n"
            "$D = 0$ の解は $a = 1, 5$ であるから，$Q = 1, R = 5$（$\\text{QR} = 15$）である。\n"
            "- (i) 異なる2点で交わる $\\iff D > 0 \\iff a < 1$ または $5 < a$（選択肢 $\\textcircled{2}$，$\\text{N} = 2$）。\n"
            "- (ii) 1点で接する $\\iff D = 0 \\iff a = 1$ または $a = 5$（選択肢 $\\textcircled{1}$，$\\text{O} = 1$）。\n"
            "- (iii) 放物線がつねに直線上側にある $\\iff D < 0 \\iff 1 < a < 5$（選択肢 $\\textcircled{0}$，$\\text{P} = 0$）。\n\n"
            "2. **(2) 差の関数の最小値 $m$**：\n"
            "条件 P（$1 < a < 5$）において，$g(x) = x^2 + (a - 1)x + (a - 1)$ を平方完成する：\n"
            "$$g(x) = \\left(x + \\frac{a - 1}{2}\\right)^2 - \\frac{(a - 1)^2}{4} + (a - 1)$$\n"
            "$$= \\left(x + \\frac{a - 1}{2}\\right)^2 - \\frac{a^2 - 2a + 1 - 4a + 4}{4}$$\n"
            "$$= \\left(x + \\frac{a - 1}{2}\\right)^2 - \\frac{a^2 - 6a + 5}{4}$$\n"
            "下に凸の放物線であるため，最小値 $m$ は頂点でとり：\n"
            "$$m = -\\frac{1}{4}(a^2 - 6a + 5)$$\n"
            "したがって $\\text{S} = 1, \\text{T} = 4, \\text{U} = 6, \\text{V} = 5$（$\\text{STUV} = 1465$）である。\n\n"
            "3. **$m$ の最大値とそのときの $a$**：\n"
            "$m$ を $a$ の関数として平方完成する：\n"
            "$$m = -\\frac{1}{4}[(a - 3)^2 - 9 + 5] = -\\frac{1}{4}(a - 3)^2 + 1$$\n"
            "$1 < a < 5$ の範囲において，$a = 3$ は定義域に含まれており，$a = 3$ のとき最大値をとる：\n"
            "$$m_{\\text{max}} = 1 \\quad (a = 3 \\text{ のとき})$$\n"
            "したがって $\\text{W} = 3, \\text{X} = 1$ である。\n\n"
            "**【考査考点】**\n"
            "放物線と直線の共有点判定（判別式の正負），2変数の最大・最小問題（2段階の平方完成）。"
        )
    },
    {
        "q_num": 3,
        "localKey": "math-q-II_1",
        "answer_ref": "II:1",
        "answer": "AB: 22, CD: 22, EF: 24, G: 2",
        "title": "数学 コース2 第II問 (前半)：内分点ベクトルと線分ベクトルの成分表示",
        "points": [
            "点 P, Q の位置ベクトル $\\overrightarrow{OP} = \\frac{2\\overrightarrow{OA} + k\\overrightarrow{OB}}{k+2}, \\overrightarrow{OQ} = \\frac{2\\overrightarrow{OC} + k\\overrightarrow{OD}}{k+2}$ の内分公式適用",
            "座標値 $A(1,0), B(0,1), C(3,0), D(0,2)$ の代入による $\\overrightarrow{OP} = (\\frac{2}{k+2}, \\frac{k}{k+2}), \\overrightarrow{OQ} = (\\frac{6}{k+2}, \\frac{2k}{k+2})$ の導出",
            "$\\overrightarrow{PQ} = (x, y) = \\frac{1}{k+2}(4, k)$ の成分表示",
            "線形結合 $x + 2y = 2$ の恒等的成立の証明"
        ],
        "solution": (
            "**【題目大意】**\n"
            "座標平面上に4点 $A(1, 0), B(0, 1), C(3, 0), D(0, 2)$ をとり，線分 AB, CD 上にそれぞれ点 P, Q を $AP : PB = CQ : QD = k : 2$ となるようにとる。\n"
            "$\\overrightarrow{PQ} = (x, y)$ とおき，$x + 2y$ の値を求める。\n\n"
            "**【公式正解】**\n"
            "正解：\n"
            "$\\text{AB} = 22$\n"
            "$\\text{CD} = 22$\n"
            "$\\text{EF} = 24$\n"
            "$\\text{G} = 2$\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "1. **位置ベクトル $\\overrightarrow{OP}$ と $\\overrightarrow{OQ}$ の立式**：\n"
            "内分点の公式より，点 P は線分 AB を $k : 2$ に内分するため：\n"
            "$$\\overrightarrow{OP} = \\frac{2\\overrightarrow{OA} + k\\overrightarrow{OB}}{k + 2}$$\n"
            "したがって $\\text{A} = 2, \\text{B} = 2$（$\\text{AB} = 22$）である。\n\n"
            "同様に，点 Q は線分 CD を $k : 2$ に内分するため：\n"
            "$$\\overrightarrow{OQ} = \\frac{2\\overrightarrow{OC} + k\\overrightarrow{OD}}{k + 2}$$\n"
            "したがって $\\text{C} = 2, \\text{D} = 2$（$\\text{CD} = 22$）である。\n\n"
            "2. **成分の代入と $\\overrightarrow{PQ}$ の算出**：\n"
            "各点の座標を代入する：\n"
            "$$\\overrightarrow{OP} = \\frac{2(1, 0) + k(0, 1)}{k + 2} = \\left(\\frac{2}{k + 2}, \\frac{k}{k + 2}\\right)$$\n"
            "$$\\overrightarrow{OQ} = \\frac{2(3, 0) + k(0, 2)}{k + 2} = \\left(\\frac{6}{k + 2}, \\frac{2k}{k + 2}\\right)$$\n"
            "ベクトル $\\overrightarrow{PQ}$ は：\n"
            "$$\\overrightarrow{PQ} = \\overrightarrow{OQ} - \\overrightarrow{OP} = \\left(\\frac{6 - 2}{k + 2}, \\frac{2k - k}{k + 2}\\right) = \\left(\\frac{4}{k + 2}, \\frac{k}{k + 2}\\right) = \\frac{1}{k + 2}(4, k)$$\n"
            "問題文の形式 $(x, y) = \\frac{1}{k + \\text{E}}(\\text{F}, k)$ と比較すると：\n"
            "$$\\text{E} = 2, \\quad \\text{F} = 4$$\n"
            "これより $\\text{EF} = 24$ である。\n\n"
            "3. **$x + 2y$ の計算**：\n"
            "$x = \\frac{4}{k + 2}, y = \\frac{k}{k + 2}$ であるから：\n"
            "$$x + 2y = \\frac{4}{k + 2} + 2 \\cdot \\frac{k}{k + 2} = \\frac{4 + 2k}{k + 2} = \\frac{2(k + 2)}{k + 2} = 2$$\n"
            "したがって $\\text{G} = 2$ である。\n\n"
            "**【考査考点】**\n"
            "平面ベクトルの内分公式，成分計算，線形従属関係（パラメータの消去）。"
        )
    },
    {
        "q_num": 4,
        "localKey": "math-q-II_2",
        "answer_ref": "II:2",
        "answer": "HIJ: 584, KL: 45, MNO: 255, P: 8",
        "title": "数学 コース2 第II問 (後半)：線分長の2乗の最小化とパラメータの決定",
        "points": [
            "関係式 $x = 2 - 2y$ の代入による $PQ^2 = 5y^2 - 8y + 4$ の導出",
            "平方完成 $5(y - \\frac{4}{5})^2 + \\frac{4}{5}$ による最小値の特定",
            "$y = \\frac{4}{5}$ のとき最小値 $PQ = \\frac{2\\sqrt{5}}{5}$ の算出",
            "$y = \\frac{k}{k+2} = \\frac{4}{5}$ からの $k = 8$ の決定"
        ],
        "solution": (
            "**【題目大意】**\n"
            "前半の結果を用いて $PQ^2$ を $y$ の式で表し，線分 PQ の最小値とそのときの $y$ および $k$ の値を求める。\n\n"
            "**【公式正解】**\n"
            "正解：\n"
            "$\\text{HIJ} = 584$\n"
            "$\\text{KL} = 45$\n"
            "$\\text{MNO} = 255$\n"
            "$\\text{P} = 8$\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "1. **$PQ^2$ を $y$ で表す**：\n"
            "前半の結果より $x + 2y = 2$ であるから：\n"
            "$$x = 2 - 2y$$\n"
            "線分 PQ の長さの2乗は：\n"
            "$$PQ^2 = x^2 + y^2 = (2 - 2y)^2 + y^2 = 4 - 8y + 4y^2 + y^2 = 5y^2 - 8y + 4$$\n"
            "したがって $\\text{H} = 5, \\text{I} = 8, \\text{J} = 4$（$\\text{HIJ} = 584$）である。\n\n"
            "2. **平方完成による最小値の導出**：\n"
            "$$PQ^2 = 5\\left(y^2 - \\frac{8}{5}y\\right) + 4 = 5\\left(y - \\frac{4}{5}\\right)^2 - 5 \\cdot \\frac{16}{25} + 4 = 5\\left(y - \\frac{4}{5}\\right)^2 - \\frac{16}{5} + \\frac{20}{5} = 5\\left(y - \\frac{4}{5}\\right)^2 + \\frac{4}{5}$$\n"
            "したがって，$PQ^2$ は $y = \\frac{4}{5}$ のとき最小値 $\\frac{4}{5}$ をとる。\n"
            "これより $\\text{K} = 4, \\text{L} = 5$（$\\text{KL} = 45$）である。\n\n"
            "3. **線分 PQ の最小値の算出**：\n"
            "$$PQ = \\sqrt{\\frac{4}{5}} = \\frac{2}{\\sqrt{5}} = \\frac{2\\sqrt{5}}{5}$$\n"
            "これより $\\text{M} = 2, \\text{N} = 5, \\text{O} = 5$（$\\text{MNO} = 255$）である。\n\n"
            "4. **そのときの $k$ の値の決定**：\n"
            "$y = \\frac{k}{k + 2}$ であったから：\n"
            "$$\\frac{k}{k + 2} = \\frac{4}{5} \\implies 5k = 4(k + 2) = 4k + 8 \\implies k = 8$$\n"
            "これより $\\text{P} = 8$ である。\n\n"
            "**【考査考点】**\n"
            "2次式の平方完成，分母の有理化，有理方程式によるパラメータの特定。"
        )
    },
    {
        "q_num": 5,
        "localKey": "math-q-III_1",
        "answer_ref": "III:1",
        "answer": "AB: 43, CD: 12, E: 4, FG: 45, HI: 13, J: 3, KL: 15",
        "title": "数学 コース2 第III問 (前半)：三角形に内接・外接する2円と三角関数の加法定理",
        "points": [
            "直角三角形 ABC（$AB = 9, BC = 12, \\angle B = 90^\\circ$）における $AC = 15$",
            "角の二等分線による $\\tan 2\\alpha = \\tan A = \\frac{4}{3}$ と2倍角公式からの $\\tan\\alpha = \\frac{1}{2}$ の導出",
            "接点 D の線分長 $AD = \\frac{2r}{\\tan\\alpha} = 4r$",
            "$\\alpha + \\beta = 45^\\circ$ と加法定理による $\\tan\\beta = \\frac{1}{3}$ および $CE = 3r$ の導出"
        ],
        "solution": (
            "**【題目大意】**\n"
            "$AB = 9, BC = 12, \\angle ABC = 90^\\circ$ である三角形 ABC と，半径 $2r$ の円 $O_1$，半径 $r$ の円 $O_2$ がある。\n"
            "円 $O_1$ と円 $O_2$ は互いに外接し，円 $O_1$ は辺 AB, AC と接し，円 $O_2$ は辺 CA, CB と接している。\n"
            "(1) 接点を D, E とし，$\\angle O_1AC = \\alpha, \\angle O_2CA = \\beta$ とするとき，$\\tan\\alpha, AD, \\tan\\beta, CE, AC$ を求める。\n\n"
            "**【公式正解】**\n"
            "正解：\n"
            "$\\text{AB} = 43$\n"
            "$\\text{CD} = 12$\n"
            "$\\text{E} = 4$\n"
            "$\\text{FG} = 45$\n"
            "$\\text{HI} = 13$\n"
            "$\\text{J} = 3$\n"
            "$\\text{KL} = 15$\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "1. **直角三角形 ABC の寸法**：\n"
            "三平方の定理より：\n"
            "$$AC = \\sqrt{AB^2 + BC^2} = \\sqrt{9^2 + 12^2} = \\sqrt{81 + 144} = \\sqrt{225} = 15$$\n"
            "したがって $\\text{KL} = 15$ である。\n\n"
            "2. **$\\tan\\alpha$ および $AD$ の導出**：\n"
            "円 $O_1$ は2辺 AB, AC に接するため，直線 $AO_1$ は $\\angle A$ の二等分線である。\n"
            "したがって $\\angle A = 2\\alpha$ である。\n"
            "直角三角形 ABC より：\n"
            "$$\\tan 2\\alpha = \\tan A = \\frac{BC}{AB} = \\frac{12}{9} = \\frac{4}{3}$$\n"
            "これより $\\text{A} = 4, \\text{B} = 3$（$\\text{AB} = 43$）である。\n\n"
            "2倍角の公式 $\\tan 2\\alpha = \\frac{2\\tan\\alpha}{1 - \\tan^2\\alpha} = \\frac{4}{3}$ より：\n"
            "$$6\\tan\\alpha = 4(1 - \\tan^2\\alpha) \\implies 4\\tan^2\\alpha + 6\\tan\\alpha - 4 = 0 \\implies 2\\tan^2\\alpha + 3\\tan\\alpha - 2 = 0$$\n"
            "因数分解すると $(2\\tan\\alpha - 1)(\\tan\\alpha + 2) = 0$。\n"
            "$\\alpha$ は鋭角（$0 < \\alpha < 45^\\circ$）であるから $\\tan\\alpha > 0$ より：\n"
            "$$\\tan\\alpha = \\frac{1}{2}$$\n"
            "これより $\\text{C} = 1, \\text{D} = 2$（$\\text{CD} = 12$）である。\n\n"
            "直角三角形 $AO_1D$ において，$O_1D = 2r$ であるから：\n"
            "$$AD = \\frac{O_1D}{\\tan\\alpha} = \\frac{2r}{1/2} = 4r$$\n"
            "したがって $\\text{E} = 4$ である。\n\n"
            "3. **$\\tan\\beta$ および $CE$ の導出**：\n"
            "同様に，直線 $CO_2$ は $\\angle C$ の二等分線であるから $\\angle C = 2\\beta$ である。\n"
            "$\\triangle ABC$ は直角三角形（$\\angle B = 90^\\circ$）であるから：\n"
            "$$\\angle A + \\angle C = 90^\\circ \\implies 2\\alpha + 2\\beta = 90^\\circ \\implies \\alpha + \\beta = 45^\\circ$$\n"
            "したがって $\\text{FG} = 45$ である。\n\n"
            "加法定理より：\n"
            "$$\\tan\\beta = \\tan(45^\\circ - \\alpha) = \\frac{\\tan 45^\\circ - \\tan\\alpha}{1 + \\tan 45^\\circ \\tan\\alpha} = \\frac{1 - 1/2}{1 + 1 \\cdot (1/2)} = \\frac{1/2}{3/2} = \\frac{1}{3}$$\n"
            "したがって $\\text{H} = 1, \\text{I} = 3$（$\\text{HI} = 13$）である。\n\n"
            "直角三角形 $CO_2E$ において，$O_2E = r$ であるから：\n"
            "$$CE = \\frac{O_2E}{\\tan\\beta} = \\frac{r}{1/3} = 3r$$\n"
            "したがって $\\text{J} = 3$ である。\n\n"
            "**【考査考点】**\n"
            "円の接線と角の二等分線の幾何学的性質，三角関数の2倍角公式，加法定理の適用。"
        )
    },
    {
        "q_num": 6,
        "localKey": "math-q-III_2",
        "answer_ref": "III:2",
        "answer": "MN: 22, OPQRS: 15722",
        "title": "数学 コース2 第III問 (後半)：外接する2円の中心間距離と半径 r の決定",
        "points": [
            "2円の中心間距離 $O_1O_2 = 2r + r = 3r$ と辺 AC からの中心の高さの差 $2r - r = r$",
            "三平方の定理による接点間距離 $DE = \\sqrt{(3r)^2 - r^2} = 2\\sqrt{2}r$ の算出",
            "辺 AC の分割 $AC = AD + DE + EC = (7 + 2\\sqrt{2})r = 15$ の立式",
            "有理化による $r = \\frac{15(7 - 2\\sqrt{2})}{41}$ の導出"
        ],
        "solution": (
            "**【題目大意】**\n"
            "前半の結果をもとに，線分 DE の長さを求め，辺 AC の長さとの関係から半径 $r$ の値を決定する。\n\n"
            "**【公式正解】**\n"
            "正解：\n"
            "$\\text{MN} = 22$\n"
            "$\\text{OPQRS} = 15722$\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "1. **線分 DE の長さの導出**：\n"
            "2円 $O_1, O_2$ は互いに外接しているため，中心間距離は：\n"
            "$$O_1O_2 = 2r + r = 3r$$\n"
            "中心 $O_1$ から辺 AC（直線 DE）までの距離は $O_1D = 2r$ である。\n"
            "中心 $O_2$ から辺 AC までの距離は $O_2E = r$ である。\n"
            "$O_2$ から線分 $O_1D$ に垂線 $O_2H$ を下ろすと，$O_2HDE$ は長方形となり：\n"
            "$$O_2H = DE, \\quad O_1H = O_1D - HD = 2r - r = r$$\n"
            "直角三角形 $O_1HO_2$ において三平方の定理を適用すると：\n"
            "$$DE = O_2H = \\sqrt{O_1O_2^2 - O_1H^2} = \\sqrt{(3r)^2 - r^2} = \\sqrt{9r^2 - r^2} = \\sqrt{8r^2} = 2\\sqrt{2}r$$\n"
            "問題文の形式 $\\text{M}\\sqrt{\\text{N}}r$ より，$\\text{M} = 2, \\text{N} = 2$（$\\text{MN} = 22$）である。\n\n"
            "2. **$r$ の値の決定**：\n"
            "線分 AC は点 D, E によって $AD, DE, EC$ の3つの部分に分割されている：\n"
            "$$AC = AD + DE + EC = 4r + 2\\sqrt{2}r + 3r = (7 + 2\\sqrt{2})r$$\n"
            "前半より $AC = 15$ であるから：\n"
            "$$(7 + 2\\sqrt{2})r = 15$$\n"
            "両辺を $7 + 2\\sqrt{2}$ で割って有理化する：\n"
            "$$r = \\frac{15}{7 + 2\\sqrt{2}} = \\frac{15(7 - 2\\sqrt{2})}{(7 + 2\\sqrt{2})(7 - 2\\sqrt{2})} = \\frac{15(7 - 2\\sqrt{2})}{49 - 8} = \\frac{15(7 - 2\\sqrt{2})}{41}$$\n"
            "問題文の形式 $r = \\frac{\\text{OP}(\\text{Q} - \\text{R}\\sqrt{\\text{S}})}{41}$ と比較すると：\n"
            "$$\\text{OP} = 15, \\quad \\text{Q} = 7, \\quad \\text{R} = 2, \\quad \\text{S} = 2$$\n"
            "これより $\\text{OPQRS} = 15722$ である。\n\n"
            "**【考査考点】**\n"
            "外接する2円の中心間距離と共通接線間の距離，直角台形の幾何学的分解，根号を含む分数の有理化。"
        )
    },
    {
        "q_num": 7,
        "localKey": "math-q-IV_1",
        "answer_ref": "IV:1",
        "answer": "AB: 56, CD: 76, EFG: -12, HI: 12, JK: 33, LM: 33",
        "title": "数学 コース2 第IV問 [1]：指数・三角関数の零点と微分による不定積分・定積分の計算",
        "points": [
            "$f(x) = 4\\sqrt{3}e^{-x}\\cos x + 6e^{-x} = 0$ からの $\\cos x = -\\frac{\\sqrt{3}}{2}$ の導出",
            "$0 \\le x < 2\\pi$ における解 $a = \\frac{5}{6}\\pi, b = \\frac{7}{6}\\pi$ の同定",
            "積の微分法による定数決定：$p = -\\frac{1}{2}, q = \\frac{1}{2}$",
            "定積分 $\\int_a^b f(x)dx = (3-\\sqrt{3})e^{-a} - (3+\\sqrt{3})e^{-b}$ の導出"
        ],
        "solution": (
            "**【題目大意】**\n"
            "$f(x) = 4\\sqrt{3}e^{-x}\\cos x + 6e^{-x}$ とする。\n"
            "(1) $0 \\le x < 2\\pi$ において $f(x) = 0$ となる解 $a, b$（$a < b$）を求める。\n"
            "(2) $\\frac{d}{dx}(pe^{-x}\\cos x + qe^{-x}\\sin x) = e^{-x}\\cos x$ を満たす定数 $p, q$ を求める。\n"
            "(3) $e^{-a} = A, e^{-b} = B$ とおき，定積分 $\\int_a^b f(x)dx$ を計算する。\n\n"
            "**【公式正解】**\n"
            "正解：\n"
            "$\\text{AB} = 56$\n"
            "$\\text{CD} = 76$\n"
            "$\\text{EFG} = -12$\n"
            "$\\text{HI} = 12$\n"
            "$\\text{JK} = 33$\n"
            "$\\text{LM} = 33$\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "1. **(1) $f(x) = 0$ の解の算出**：\n"
            "$$f(x) = 2e^{-x}(2\\sqrt{3}\\cos x + 3) = 0$$\n"
            "$e^{-x} > 0$ であるから：\n"
            "$$2\\sqrt{3}\\cos x + 3 = 0 \\implies \\cos x = -\\frac{3}{2\\sqrt{3}} = -\\frac{\\sqrt{3}}{2}$$\n"
            "$0 \\le x < 2\\pi$ の範囲において：\n"
            "$$x = \\pi - \\frac{\\pi}{6} = \\frac{5}{6}\\pi, \\quad x = \\pi + \\frac{\\pi}{6} = \\frac{7}{6}\\pi$$\n"
            "$a < b$ より：\n"
            "$$a = \\frac{5}{6}\\pi, \\quad b = \\frac{7}{6}\\pi$$\n"
            "したがって $\\text{AB} = 56, \\text{CD} = 76$ である。\n\n"
            "2. **(2) 微分による未定係数 $p, q$ の決定**：\n"
            "積の微分公式を適用する：\n"
            "$$\\frac{d}{dx}\\left(pe^{-x}\\cos x + qe^{-x}\\sin x\\right) = p\\left(-e^{-x}\\cos x - e^{-x}\\sin x\\right) + q\\left(-e^{-x}\\sin x + e^{-x}\\cos x\\right)$$\n"
            "$$= e^{-x}[(-p + q)\\cos x + (-p - q)\\sin x]$$\n"
            "これが $e^{-x}\\cos x$ に恒等的に一致するため：\n"
            "$$\\begin{cases} -p + q = 1 \\\\ -p - q = 0 \\end{cases}$$\n"
            "第2式より $q = -p$。第1式に代入すると $-2p = 1 \\implies p = -\\frac{1}{2}$，したがって $q = \\frac{1}{2}$。\n"
            "問題文の形式 $\\frac{\\text{EF}}{\\text{G}}, \\frac{\\text{H}}{\\text{I}}$ より：\n"
            "$$p = \\frac{-1}{2} \\implies \\text{EFG} = -12, \\quad q = \\frac{1}{2} \\implies \\text{HI} = 12$$\n"
            "である。\n\n"
            "3. **(3) 定積分 $\\int_a^b f(x)dx$ の計算**：\n"
            "(2) の結果より：\n"
            "$$\\int e^{-x}\\cos x dx = -\\frac{1}{2}e^{-x}\\cos x + \\frac{1}{2}e^{-x}\\sin x + C$$\n"
            "また，$\\int 6e^{-x}dx = -6e^{-x} + C$ である。\n"
            "したがって：\n"
            "$$F(x) = \\int f(x)dx = 4\\sqrt{3}\\left(-\\frac{1}{2}e^{-x}\\cos x + \\frac{1}{2}e^{-x}\\sin x\\right) - 6e^{-x}$$\n"
            "$$= e^{-x}(-2\\sqrt{3}\\cos x + 2\\sqrt{3}\\sin x - 6)$$\n\n"
            "端点での値を計算する：\n"
            "- $x = a = \\frac{5}{6}\\pi$ のとき，$\\cos a = -\\frac{\\sqrt{3}}{2}, \\sin a = \\frac{1}{2}$ であるから：\n"
            "  $$-2\\sqrt{3}\\left(-\\frac{\\sqrt{3}}{2}\\right) + 2\\sqrt{3}\\left(\\frac{1}{2}\\right) - 6 = 3 + \\sqrt{3} - 6 = \\sqrt{3} - 3 = -(3 - \\sqrt{3})$$\n"
            "  $$F(a) = -(3 - \\sqrt{3})e^{-a}$$\n\n"
            "- $x = b = \\frac{7}{6}\\pi$ のとき，$\\cos b = -\\frac{\\sqrt{3}}{2}, \\sin b = -\\frac{1}{2}$ であるから：\n"
            "  $$-2\\sqrt{3}\\left(-\\frac{\\sqrt{3}}{2}\\right) + 2\\sqrt{3}\\left(-\\frac{1}{2}\\right) - 6 = 3 - \\sqrt{3} - 6 = -3 - \\sqrt{3} = -(3 + \\sqrt{3})$$\n"
            "  $$F(b) = -(3 + \\sqrt{3})e^{-b}$$\n\n"
            "したがって：\n"
            "$$\\int_a^b f(x)dx = F(b) - F(a) = -(3 + \\sqrt{3})e^{-b} - [-(3 - \\sqrt{3})e^{-a}] = (3 - \\sqrt{3})e^{-a} - (3 + \\sqrt{3})e^{-b}$$\n"
            "$e^{-a} = A, e^{-b} = B$ とおくと：\n"
            "$$(3 - \\sqrt{3})A - (3 + \\sqrt{3})B$$\n"
            "問題文の形式 $(J - \\sqrt{K})A - (L + \\sqrt{M})B$ より：\n"
            "$$\\text{J} = 3, \\text{K} = 3, \\text{L} = 3, \\text{M} = 3$$\n"
            "これより $\\text{JK} = 33, \\text{LM} = 33$ である。\n\n"
            "**【考査考点】**\n"
            "三角方程式の解法，指数関数と三角関数の積の不定積分（未定係数法），微分積分学の基本定理による定積分の評価。"
        )
    },
    {
        "q_num": 8,
        "localKey": "math-q-IV_2",
        "answer_ref": "IV:2",
        "answer": "NOPQR: 18422, S: 1, T: 8, UV: 52, WXYZ: 2315",
        "title": "数学 コース2 第IV問 [2]：無理関数の置換積分と無限遠における増大度の極限",
        "points": [
            "変数変換 $t = \\sqrt{\\frac{1}{3}x + 2}$ による $x = 3t^2 - 6, dx = 6t dt$ の置換",
            "被積分関数の多項式化 $18\\int(t^4 - 2t^2)dt$",
            "不定積分 $S = \\frac{6}{5}t^3(3t^2 - 10) + C$（選択肢 $\\textcircled{1}$）の導出",
            "定積分 $S = [\\frac{6}{5}t^3(3t^2-10)]_{\\sqrt{2}}^{\\sqrt{a/3+2}}$ の立式（選択肢 $\\textcircled{8}$）",
            "増大度比較による極限 $\\lim_{a \\to \\infty} \\frac{S}{a^{5/2}} = \\frac{2\\sqrt{3}}{15}$ の決定"
        ],
        "solution": (
            "**【題目大意】**\n"
            "定積分 $S = \\int_0^a x\\sqrt{\\frac{1}{3}x + 2} dx$ を考える。\n"
            "(1) $t = \\sqrt{\\frac{1}{3}x + 2}$ とおいて不定積分を計算する。\n"
            "(2) 定積分 $S$ を求め，$\\lim_{a \\to \\infty} \\frac{S}{a^{5/2}}$ の極限値を求める。\n\n"
            "**【公式正解】**\n"
            "正解：\n"
            "$\\text{NOPQR} = 18422$\n"
            "$\\text{S} = 1$（選択肢 $\\textcircled{1}$：$\\frac{6}{5}t^3(3t^2 - 10)$）\n"
            "$\\text{T} = 8$（選択肢 $\\textcircled{8}$）\n"
            "$\\text{UV} = 52$\n"
            "$\\text{WXYZ} = 2315$\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "1. **(1) 置換積分の実行**：\n"
            "$t = \\sqrt{\\frac{1}{3}x + 2}$ とおく。\n"
            "両辺を2乗すると：\n"
            "$$t^2 = \\frac{1}{3}x + 2 \\implies \\frac{1}{3}x = t^2 - 2 \\implies x = 3(t^2 - 2) = 3t^2 - 6$$\n"
            "両辺を $t$ で微分すると：\n"
            "$$dx = 6t dt$$\n"
            "被積分関数に代入すると：\n"
            "$$\\int x\\sqrt{\\frac{1}{3}x + 2} dx = \\int (3t^2 - 6) \\cdot t \\cdot (6t dt) = 18\\int (t^2 - 2)t^2 dt = 18\\int (t^4 - 2t^2) dt$$\n"
            "問題文の形式 $\\text{NO}\\int(t^{\\text{P}} - \\text{Q}t^{\\text{R}})dt$ と比較すると：\n"
            "$$\\text{NO} = 18, \\quad \\text{P} = 4, \\quad \\text{Q} = 2, \\quad \\text{R} = 2$$\n"
            "これより $\\text{NOPQR} = 18422$ である。\n\n"
            "2. **多項式積分の実行**：\n"
            "$$18\\int (t^4 - 2t^2) dt = 18\\left(\\frac{t^5}{5} - \\frac{2t^3}{3}\\right) = \\frac{18}{5}t^5 - 12t^3 = \\frac{6}{5}t^3(3t^2 - 10)$$\n"
            "したがって，不定積分は：\n"
            "$$\\frac{6}{5}t^3(3t^2 - 10) + C$$\n"
            "これは選択肢 $\\textcircled{1}$ に合致するため，$\\text{S} = 1$ である。\n\n"
            "3. **(2) 定積分の立式**：\n"
            "積分区間の対応を調べる：\n"
            "- $x = 0$ のとき：$t = \\sqrt{2}$\n"
            "- $x = a$ のとき：$t = \\sqrt{\\frac{1}{3}a + 2}$\n"
            "下端 $t = \\sqrt{2}$ における値：\n"
            "$$\\frac{6}{5}(\\sqrt{2})^3(3 \\cdot 2 - 10) = \\frac{6}{5}(2\\sqrt{2})(-4) = -\\frac{48\\sqrt{2}}{5}$$\n"
            "したがって，定積分 $S$ は選択肢 $\\textcircled{8}$ の式で表される：\n"
            "$$S = \\textcircled{8} \\implies \\text{T} = 8$$\n\n"
            "4. **無限大における極限値の算出**：\n"
            "$a \\to \\infty$ において，$t = \\sqrt{\\frac{a}{3} + 2} \\approx \\sqrt{\\frac{a}{3}} = \\frac{a^{1/2}}{\\sqrt{3}}$ である。\n"
            "最高次の項は：\n"
            "$$S \\approx \\frac{18}{5}t^5 = \\frac{18}{5}\\left(\\frac{a}{3}\\right)^{5/2} = \\frac{18}{5} \\cdot \\frac{a^{5/2}}{9\\sqrt{3}} = \\frac{2}{5\\sqrt{3}} a^{5/2} = \\frac{2\\sqrt{3}}{15} a^{5/2}$$\n"
            "分母の形式は $a^{\\text{U}/\\text{V}} = a^{5/2}$ であるから，$\\text{UV} = 52$ である。\n"
            "極限値は：\n"
            "$$\\lim_{a \\to \\infty} \\frac{S}{a^{5/2}} = \\frac{2\\sqrt{3}}{15}$$\n"
            "問題文の形式 $\\frac{\\text{W}\\sqrt{\\text{X}}}{\\text{YZ}}$ より：\n"
            "$$\\text{W} = 2, \\quad \\text{X} = 3, \\quad \\text{YZ} = 15$$\n"
            "これより $\\text{WXYZ} = 2315$ である。\n\n"
            "**【考査考点】**\n"
            "無理関数の置換積分法，共通因数のくくり出しによる因数分解，関数の漸近挙動と無限大における増大度の極限評価。"
        )
    }
]

def main():
    out_dir = Path("work/2011-2-math-c2")
    out_dir.mkdir(parents=True, exist_ok=True)

    c2_path = out_dir / "explanations.json"
    with open(c2_path, "w", encoding="utf-8") as f:
        json.dump(math_c2_questions, f, ensure_ascii=False, indent=2)
    print(f"Generated {c2_path} ({len(math_c2_questions)} questions)")

    md_path = Path("docs/explanations/2011-2-math-c2-solutions.md")
    md_path.parent.mkdir(parents=True, exist_ok=True)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# 2011-2 EJU 数学 コース2 詳解\n\n")
        for q in math_c2_questions:
            f.write(f"## {q['title']}\n\n")
            f.write(q["solution"] + "\n\n---\n\n")
    print(f"Generated {md_path}")

if __name__ == "__main__":
    main()

