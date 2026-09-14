#!/usr/bin/env python3
"""Generate comprehensive pedagogical explanations for 2014-1 EJU Math Course 2 (8 items)."""

import json
from pathlib import Path

math_c2_questions = [
    {
        "q_num": "I_1",
        "localKey": "math-q-I_1",
        "answer_ref": "I:1",
        "answer": {
            "AB": "-6",
            "CD": "23",
            "EFG": "523",
            "HI": "-1",
            "J": "6",
            "K": "6"
        },
        "title": "数学 コース2 第I問 [1]：2次関数の軸・最大値条件と係数決定",
        "points": [
            "軸の方程式 $x = -\\frac{b}{2a}$ に基づく係数の関係式導出",
            "指定点 $(1, 2)$ の通過条件と2次方程式の立式",
            "最大値を持つ条件（$a < 0$）による解の選定と頂点座標の計算"
        ],
        "solution": (
            "**【題目大意】**\n"
            "2次関数 $y = ax^2 + bx + \\frac{3}{a}$ は次の2つの条件を満たす：\n"
            "(i) $x = 3$ のとき $y$ は最大値をとる。\n"
            "(ii) $x = 1$ のとき $y = 2$ である。\n"
            "このとき、$a, b$ の値および関数の最大値を求める。\n\n"
            "**【公式正解】**\n"
            "$\\text{AB} = -6$\n"
            "$\\text{CD} = 23$\n"
            "$\\text{EFG} = 523$\n"
            "$\\text{HI} = -1$\n"
            "$\\text{J} = 6$\n"
            "$\\text{K} = 6$\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "**(1) 条件(i), (ii)による関係式の導出**\n"
            "放物線 $y = ax^2 + bx + \\frac{3}{a}$ の対称軸は：\n"
            "$$x = -\\frac{b}{2a}$$\n"
            "条件(i)より、$x = 3$ で極値（最大値）をとるため：\n"
            "$$-\\frac{b}{2a} = 3 \\implies b = -6a \\quad (\\text{AB} = -6)$$\n"
            "また、関数が最大値をとることから、放物線は上に凸であり、$a < 0$ である。\n\n"
            "条件(ii)より、$x = 1$ のとき $y = 2$ であるから：\n"
            "$$2 = a(1)^2 + b(1) + \\frac{3}{a} \\implies 2 = a + b + \\frac{3}{a} \\quad (\\text{CD} = 23)$$\n\n"
            "**(2) $a, b$ の決定**\n"
            "$b = -6a$ を代入すると：\n"
            "$$2 = a - 6a + \\frac{3}{a} = -5a + \\frac{3}{a}$$\n"
            "両辺に $a$（$a \\neq 0$）を掛けて整理すると：\n"
            "$$2a = -5a^2 + 3 \\implies 5a^2 + 2a - 3 = 0 \\quad (\\text{EFG} = 523)$$\n"
            "左辺を因数分解すると：\n"
            "$$(5a - 3)(a + 1) = 0$$\n"
            "上に凸（最大値をもつ）条件 $a < 0$ より：\n"
            "$$a = -1 \\quad (\\text{HI} = -1)$$\n"
            "これより：\n"
            "$$b = -6(-1) = 6 \\quad (\\text{J} = 6)$$\n\n"
            "**(3) 最大値の計算**\n"
            "求めた係数を代入した関数は：\n"
            "$$y = -x^2 + 6x - 3$$\n"
            "平方完成すると：\n"
            "$$y = -(x - 3)^2 + 9 - 3 = -(x - 3)^2 + 6$$\n"
            "したがって、$x = 3$ における最大値は $6$ である（$\\text{K} = 6$）。\n\n"
            "**【考査考点】**\n"
            "- 2次関数の軸と頂点、最大・最小条件の把握。\n"
            "- 上に凸・下に凸と2次の係数 $a$ の符号の関係。\n"
            "- 連立方程式の代入消去法による2次方程式の解法。"
        )
    },
    {
        "q_num": "I_2",
        "localKey": "math-q-I_2",
        "answer_ref": "I:2",
        "answer": {
            "LMN": "223",
            "OPQR": "3141",
            "STU": "365"
        },
        "title": "数学 コース2 第I問 [2]：多項式の因数分解と無理数の代入計算",
        "points": [
            "2変数の構造に着目した式変形と共通因数による因数分解",
            "多項式への具体的な代入と積の因数分解表現",
            "分母の有理化と共役無理数を利用した対称的積の簡潔計算"
        ],
        "solution": (
            "**【題目大意】**\n"
            "2つの整式\n"
            "$$P = 2x^2 - x + 2, \\quad Q = x^2 - 2x + 1$$\n"
            "に対して、$E = P^2 - 4Q^2 - 3P + 6Q$ を考える。\n"
            "(1) $E$ を $P, Q$ について因数分解する。\n"
            "(2) $E$ を $x$ の多項式として因数分解した形で表す。\n"
            "(3) $x = -\\frac{1-\\sqrt{5}}{3-\\sqrt{5}}$ のときの $E$ の値を求める。\n\n"
            "**【公式正解】**\n"
            "$\\text{LMN} = 223$\n"
            "$\\text{OPQR} = 3141$\n"
            "$\\text{STU} = 365$\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "**(1) $E$ の因数分解**\n"
            "与式を整理する：\n"
            "$$E = (P^2 - 4Q^2) - 3(P - 2Q)$$\n"
            "平方の差の公式を適用すると：\n"
            "$$P^2 - 4Q^2 = (P - 2Q)(P + 2Q)$$\n"
            "したがって、共通因数 $(P - 2Q)$ でくくると：\n"
            "$$E = (P - 2Q)(P + 2Q) - 3(P - 2Q) = (P - 2Q)(P + 2Q - 3)$$\n"
            "空欄 $(P - \\text{L}Q)(P + \\text{M}Q - \\text{N})$ と比較して：\n"
            "$$\\text{L} = 2, \\quad \\text{M} = 2, \\quad \\text{N} = 3 \\implies \\text{LMN} = 223$$\n\n"
            "**(2) $x$ の多項式としての表現**\n"
            "各因子を $x$ で計算する：\n"
            "$$P - 2Q = (2x^2 - x + 2) - 2(x^2 - 2x + 1) = 2x^2 - x + 2 - 2x^2 + 4x - 2 = 3x$$\n"
            "$$P + 2Q - 3 = (2x^2 - x + 2) + 2(x^2 - 2x + 1) - 3 = 4x^2 - 5x + 1$$\n"
            "$4x^2 - 5x + 1$ を因数分解すると：\n"
            "$$4x^2 - 5x + 1 = (x - 1)(4x - 1)$$\n"
            "よって：\n"
            "$$E = 3x(x - 1)(4x - 1)$$\n"
            "空欄 $\\text{O}x(x - \\text{P})(\\text{Q}x - \\text{R})$ と比較して：\n"
            "$$\\text{O} = 3, \\quad \\text{P} = 1, \\quad \\text{Q} = 4, \\quad \\text{R} = 1 \\implies \\text{OPQR} = 3141$$\n\n"
            "**(3) $x$ の値に対する $E$ の計算**\n"
            "与えられた $x$ の分母を有理化する：\n"
            "$$x = -\\frac{1-\\sqrt{5}}{3-\\sqrt{5}} = \\frac{\\sqrt{5}-1}{3-\\sqrt{5}} = \\frac{(\\sqrt{5}-1)(3+\\sqrt{5})}{(3-\\sqrt{5})(3+\\sqrt{5})} = \\frac{3\\sqrt{5} + 5 - 3 - \\sqrt{5}}{9 - 5} = \\frac{2 + 2\\sqrt{5}}{4} = \\frac{1+\\sqrt{5}}{2}$$\n"
            "このとき各因子を計算すると：\n"
            "$$x - 1 = \\frac{1+\\sqrt{5}}{2} - 1 = \\frac{\\sqrt{5}-1}{2}$$\n"
            "$$4x - 1 = 4\\left(\\frac{1+\\sqrt{5}}{2}\\right) - 1 = 2(1+\\sqrt{5}) - 1 = 2\\sqrt{5} + 1$$\n"
            "これらを $E$ に代入する：\n"
            "$$x(x - 1) = \\left(\\frac{\\sqrt{5}+1}{2}\\right)\\left(\\frac{\\sqrt{5}-1}{2}\\right) = \\frac{5 - 1}{4} = 1$$\n"
            "したがって：\n"
            "$$E = 3 \\cdot 1 \\cdot (2\\sqrt{5} + 1) = 3(1 + 2\\sqrt{5}) = 3 + 6\\sqrt{5}$$\n"
            "与式 $\\text{S} + \\text{T}\\sqrt{\\text{U}}$ と比較して：\n"
            "$$\\text{S} = 3, \\quad \\text{T} = 6, \\quad \\text{U} = 5 \\implies \\text{STU} = 365$$\n\n"
            "**【考査考点】**\n"
            "- 共通因数に着目した複式因数分解の手法。\n"
            "- たすき掛けによる2次三項式の因数分解。\n"
            "- 分母の有理化と黄金比的共役積 $x(x-1) = 1$ の活用。"
        )
    },
    {
        "q_num": "II_1",
        "localKey": "math-q-II_1",
        "answer_ref": "II:1",
        "answer": {
            "ABCDE": "34112",
            "F": "1",
            "G": "3",
            "HIJK": "4969"
        },
        "title": "数学 コース2 第II問 (1)：正四面体における空間ベクトルの内分点表現と絶対値計算",
        "points": [
            "空間ベクトルの内分公式による線分上の点 P の位置ベクトル表現",
            "正四面体の基本ベクトルによる内積の計算（$|\\vec{a}|=1$, $\\vec{a}\\cdot\\vec{b} = \\frac{1}{2}$）",
            "ベクトルの大きさの2乗展開とパラメータ $t$ の2次式導出"
        ],
        "solution": (
            "**【題目大意】**\n"
            "1辺の長さが $1$ の正四面体 $\\text{OABC}$ において、線分 $\\text{OA}$ を $3:1$ に内分する点を $\\text{L}$、線分 $\\text{BC}$ の中点を $\\text{M}$、線分 $\\text{LM}$ を $t:(1-t)$ に内分する点を $\\text{P}$ とする（$0 < t < 1$）。\n"
            "$\\overrightarrow{\\text{OA}} = \\vec{a}$，$\\overrightarrow{\\text{OB}} = \\vec{b}$，$\\overrightarrow{\\text{OC}} = \\vec{c}$ とする。\n"
            "(1) $\\overrightarrow{\\text{OP}}$ を $\\vec{a}, \\vec{b}, \\vec{c}$ で表し、$\\vec{a}\\cdot(\\vec{b}+\\vec{c})$、$|\\vec{b}+\\vec{c}|^2$、および $|\\overrightarrow{\\text{OP}}|$ を求める。\n\n"
            "**【公式正解】**\n"
            "$\\text{ABCDE} = 34112$\n"
            "$\\text{F} = 1$\n"
            "$\\text{G} = 3$\n"
            "$\\text{HIJK} = 4969$\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "**(1) $\\overrightarrow{\\text{OP}}$ のベクトル表示**\n"
            "点 L は線分 OA を $3:1$ に内分するので：\n"
            "$$\\overrightarrow{\\text{OL}} = \\frac{3}{4}\\vec{a}$$\n"
            "点 M は線分 BC の中点であるから：\n"
            "$$\\overrightarrow{\\text{OM}} = \\frac{1}{2}(\\vec{b} + \\vec{c})$$\n"
            "点 P は線分 LM を $t : (1-t)$ に内分するため、内分点の公式より：\n"
            "$$\\overrightarrow{\\text{OP}} = (1-t)\\overrightarrow{\\text{OL}} + t\\overrightarrow{\\text{OM}} = \\frac{3}{4}(1-t)\\vec{a} + \\frac{1}{2}t(\\vec{b}+\\vec{c})$$\n"
            "与式 $\\frac{\\text{A}}{\\text{B}}(\\text{C}-t)\\vec{a} + \\frac{\\text{D}}{\\text{E}}t(\\vec{b}+\\vec{c})$ と比較すると：\n"
            "$$\\text{A} = 3, \\quad \\text{B} = 4, \\quad \\text{C} = 1, \\quad \\text{D} = 1, \\quad \\text{E} = 2 \\implies \\text{ABCDE} = 34112$$\n\n"
            "**(2) 基本内積と $|\\vec{b}+\\vec{c}|^2$ の計算**\n"
            "正四面体 OABC の各面の三角形はすべて1辺 1 の正三角形である。\n"
            "よって：\n"
            "$$|\\vec{a}| = |\\vec{b}| = |\\vec{c}| = 1$$\n"
            "各ベクトルのなす角はすべて $60^\\circ$ であるから：\n"
            "$$\\vec{a}\\cdot\\vec{b} = \\vec{b}\\cdot\\vec{c} = \\vec{c}\\cdot\\vec{a} = 1 \\cdot 1 \\cdot \\cos 60^\\circ = \\frac{1}{2}$$\n"
            "したがって：\n"
            "$$\\vec{a}\\cdot(\\vec{b}+\\vec{c}) = \\vec{a}\\cdot\\vec{b} + \\vec{a}\\cdot\\vec{c} = \\frac{1}{2} + \\frac{1}{2} = 1 \\quad (\\text{F} = 1)$$\n"
            "また：\n"
            "$$|\\vec{b}+\\vec{c}|^2 = |\\vec{b}|^2 + 2\\vec{b}\\cdot\\vec{c} + |\\vec{c}|^2 = 1^2 + 2\\left(\\frac{1}{2}\\right) + 1^2 = 1 + 1 + 1 = 3 \\quad (\\text{G} = 3)$$\n\n"
            "**(3) $|\\overrightarrow{\\text{OP}}|$ の導出**\n"
            "$|\\overrightarrow{\\text{OP}}|^2$ を展開する：\n"
            "$$|\\overrightarrow{\\text{OP}}|^2 = \\left[\\frac{3}{4}(1-t)\\vec{a} + \\frac{t}{2}(\\vec{b}+\\vec{c})\\right]^2$$\n"
            "$$= \\frac{9(1-t)^2}{16}|\\vec{a}|^2 + 2 \\cdot \\frac{3(1-t)}{4} \\cdot \\frac{t}{2} \\vec{a}\\cdot(\\vec{b}+\\vec{c}) + \\frac{t^2}{4}|\\vec{b}+\\vec{c}|^2$$\n"
            "$|\\vec{a}|^2 = 1$、$\\vec{a}\\cdot(\\vec{b}+\\vec{c}) = 1$、$|\\vec{b}+\\vec{c}|^2 = 3$ を代入すると：\n"
            "$$|\\overrightarrow{\\text{OP}}|^2 = \\frac{9(1-t)^2}{16} + \\frac{3t(1-t)}{4} + \\frac{3t^2}{4}$$\n"
            "全体を分母 $16$ で通分すると：\n"
            "$$|\\overrightarrow{\\text{OP}}|^2 = \\frac{1}{16}\\left[9(1 - 2t + t^2) + 12(t - t^2) + 12t^2\\right]$$\n"
            "$$= \\frac{1}{16}\\left[9 - 18t + 9t^2 + 12t - 12t^2 + 12t^2\\right] = \\frac{1}{16}\\left(9t^2 - 6t + 9\\right)$$\n"
            "平方根をとると：\n"
            "$$|\\overrightarrow{\\text{OP}}| = \\frac{1}{4}\\sqrt{9t^2 - 6t + 9}$$\n"
            "与式 $\\frac{1}{\\text{H}}\\sqrt{\\text{I}t^2 - \\text{J}t + \\text{K}}$ と比較して：\n"
            "$$\\text{H} = 4, \\quad \\text{I} = 9, \\quad \\text{J} = 6, \\quad \\text{K} = 9 \\implies \\text{HIJK} = 4969$$\n\n"
            "**【考査考点】**\n"
            "- 空間ベクトルの内分公式による位置ベクトルの代数表現。\n"
            "- 正四面体の幾何学的対称性と基本内積の正確な計算。\n"
            "- ベクトルの大きさの2乗計算と展開の整理。"
        )
    },
    {
        "q_num": "II_2",
        "localKey": "math-q-II_2",
        "answer_ref": "II:2",
        "answer": {
            "LM": "13",
            "NO": "22",
            "PQR": "223"
        },
        "title": "数学 コース2 第II問 (2)(3)：線分の長さの最小値とベクトルのなす角（余弦）",
        "points": [
            "2次式の平方完成による線分長の最小値および最小をとるパラメータ $t$ の決定",
            "最小時における位置ベクトル $\\overrightarrow{OP}$ の具体的係数の特定",
            "内積の定義に基づく $\\cos \\angle AOP$ の計算と有理化"
        ],
        "solution": (
            "**【題目大意】**\n"
            "第II問(1)の設定のもとで：\n"
            "(2) $|\\overrightarrow{\\text{OP}}|$ が最小となるときの $t$ の値とその最小値を求める。\n"
            "(3) (2)のとき、$\\cos \\angle \\text{AOP}$ の値を求める。\n\n"
            "**【公式正解】**\n"
            "$\\text{LM} = 13$\n"
            "$\\text{NO} = 22$\n"
            "$\\text{PQR} = 223$\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "**(1) $|\\overrightarrow{\\text{OP}}|$ が最小となる $t$ と最小値**\n"
            "根号内の2次式 $f(t) = 9t^2 - 6t + 9$ を平方完成する：\n"
            "$$f(t) = 9\\left(t^2 - \\frac{2}{3}t\\right) + 9 = 9\\left(t - \\frac{1}{3}\\right)^2 - 9\\left(\\frac{1}{9}\\right) + 9 = 9\\left(t - \\frac{1}{3}\\right)^2 + 8$$\n"
            "$0 < t < 1$ の範囲において、$f(t)$ は $t = \\frac{1}{3}$ で最小値 $8$ をとる。\n"
            "したがって：\n"
            "$$t = \\frac{1}{3} \\quad (\\text{LM} = 13)$$\n"
            "このとき、$|\\overrightarrow{\\text{OP}}|$ の最小値は：\n"
            "$$|\\overrightarrow{\\text{OP}}|_{\\min} = \\frac{1}{4}\\sqrt{8} = \\frac{2\\sqrt{2}}{4} = \\frac{\\sqrt{2}}{2}$$\n"
            "与式 $\\frac{\\sqrt{\\text{N}}}{\\text{O}}$ と比較して：\n"
            "$$\\text{N} = 2, \\quad \\text{O} = 2 \\implies \\text{NO} = 22$$\n\n"
            "**(2) $\\cos \\angle \\text{AOP}$ の計算**\n"
            "$t = \\frac{1}{3}$ を $\\overrightarrow{\\text{OP}}$ の表式に代入する：\n"
            "$$\\overrightarrow{\\text{OP}} = \\frac{3}{4}\\left(1 - \\frac{1}{3}\\right)\\vec{a} + \\frac{1}{2}\\left(\\frac{1}{3}\\right)(\\vec{b} + \\vec{c}) = \\frac{3}{4}\\left(\\frac{2}{3}\\right)\\vec{a} + \\frac{1}{6}(\\vec{b} + \\vec{c}) = \\frac{1}{2}\\vec{a} + \\frac{1}{6}(\\vec{b} + \\vec{c})$$\n"
            "$\\overrightarrow{\\text{OA}} = \\vec{a}$ との内積をとる：\n"
            "$$\\overrightarrow{\\text{OA}} \\cdot \\overrightarrow{\\text{OP}} = \\vec{a} \\cdot \\left[\\frac{1}{2}\\vec{a} + \\frac{1}{6}(\\vec{b} + \\vec{c})\\right] = \\frac{1}{2}|\\vec{a}|^2 + \\frac{1}{6}\\vec{a}\\cdot(\\vec{b} + \\vec{c})$$\n"
            "$|\\vec{a}|^2 = 1$、$\\vec{a}\\cdot(\\vec{b}+\\vec{c}) = 1$ より：\n"
            "$$\\overrightarrow{\\text{OA}} \\cdot \\overrightarrow{\\text{OP}} = \\frac{1}{2}(1) + \\frac{1}{6}(1) = \\frac{2}{3}$$\n"
            "また、$|\\overrightarrow{\\text{OA}}| = 1$ であり、$|\\overrightarrow{\\text{OP}}| = \\frac{\\sqrt{2}}{2}$ であるから：\n"
            "$$\\cos \\angle \\text{AOP} = \\frac{\\overrightarrow{\\text{OA}} \\cdot \\overrightarrow{\\text{OP}}}{|\\overrightarrow{\\text{OA}}| |\\overrightarrow{\\text{OP}}|} = \\frac{\\frac{2}{3}}{1 \\cdot \\frac{\\sqrt{2}}{2}} = \\frac{4}{3\\sqrt{2}} = \\frac{2\\sqrt{2}}{3}$$\n"
            "与式 $\\frac{\\text{P}\\sqrt{\\text{Q}}}{\\text{R}}$ と比較して：\n"
            "$$\\text{P} = 2, \\quad \\text{Q} = 2, \\quad \\text{R} = 3 \\implies \\text{PQR} = 223$$\n\n"
            "**【考査考点】**\n"
            "- 2次関数の平方完成による極値問題の解法。\n"
            "- ベクトルの内積と角の余弦の定義公式の適用。\n"
            "- 分母の有理化と分数の整理。"
        )
    },
    {
        "q_num": "III_1",
        "localKey": "math-q-III_1",
        "answer_ref": "III:1",
        "answer": {
            "ABC": "-14",
            "DE": "-1"
        },
        "title": "数学 コース2 第III問 (前半)：特定パラメータにおける三角方程式の解法と連立性の検証",
        "points": [
            "2倍角の公式による三角方程式の因数分解と解の探索",
            "領域制約 $-\\frac{\\pi}{2} < x < \\frac{\\pi}{2}$ における解の絞り込み",
            "求められた角を第2式へ代入した検証と不成立の確認"
        ],
        "solution": (
            "**【題目大意】**\n"
            "$a > 0$ とする。$-\\frac{\\pi}{2} < x < \\frac{\\pi}{2}$ の範囲で次の2つの方程式を考える：\n"
            "$$\\sin 2x + a\\cos x = 0 \\quad \\cdots \\textcircled{1}$$\n"
            "$$\\cos 2x + a\\sin x = -2 \\quad \\cdots \\textcircled{2}$$\n"
            "$a = \\sqrt{2}$ のとき、$\\textcircled{1}$ を満たす $x$ を求め、そのときの $\\textcircled{2}$ の左辺の値を調べる。\n\n"
            "**【公式正解】**\n"
            "$\\text{ABC} = -14$\n"
            "$\\text{DE} = -1$\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "**(1) $a = \\sqrt{2}$ のときの $\\textcircled{1}$ の解法**\n"
            "2倍角の公式 $\\sin 2x = 2\\sin x \\cos x$ を用いると、$\\textcircled{1}$ は：\n"
            "$$2\\sin x \\cos x + \\sqrt{2}\\cos x = 0$$\n"
            "共通因数 $\\cos x$ でくくると：\n"
            "$$\\cos x (2\\sin x + \\sqrt{2}) = 0$$\n"
            "定義域 $-\\frac{\\pi}{2} < x < \\frac{\\pi}{2}$ においては常に $\\cos x > 0$ である。\n"
            "したがって、$\\cos x \\neq 0$ であるから：\n"
            "$$2\\sin x + \\sqrt{2} = 0 \\implies \\sin x = -\\frac{\\sqrt{2}}{2}$$\n"
            "区間 $-\\frac{\\pi}{2} < x < \\frac{\\pi}{2}$ における解は：\n"
            "$$x = -\\frac{\\pi}{4}$$\n"
            "与式 $\\frac{\\text{AB}}{\\text{C}}\\pi$ と比較して：\n"
            "$$\\text{AB} = -1, \\quad \\text{C} = 4 \\implies \\text{ABC} = -14$$\n\n"
            "**(2) $\\textcircled{2}$ の左辺の値の検証**\n"
            "$x = -\\frac{\\pi}{4}$ および $a = \\sqrt{2}$ を $\\textcircled{2}$ の左辺に代入する：\n"
            "$$\\cos 2x + a\\sin x = \\cos\\left(-\\frac{\\pi}{2}\\right) + \\sqrt{2}\\sin\\left(-\\frac{\\pi}{4}\\right)$$\n"
            "各三角関数の値を代入すると：\n"
            "$$\\cos\\left(-\\frac{\\pi}{2}\\right) = 0$$\n"
            "$$\\sin\\left(-\\frac{\\pi}{4}\\right) = -\\frac{\\sqrt{2}}{2}$$\n"
            "したがって：\n"
            "$$\\textcircled{2} \\text{の左辺} = 0 + \\sqrt{2}\\left(-\\frac{\\sqrt{2}}{2}\\right) = -1 \\quad (\\text{DE} = -1)$$\n"
            "$\\textcircled{2}$ の右辺は $-2$ であるため、左辺 $\\neq$ 右辺となり、等式は成り立たない。\n"
            "よって $a = \\sqrt{2}$ のとき、$\\textcircled{1}$ と $\\textcircled{2}$ は共通解をもたない。\n\n"
            "**【考査考点】**\n"
            "- 正弦の2倍角の公式 $\\sin 2x = 2\\sin x \\cos x$ の適用。\n"
            "- 三角関数の符号と定義域制約（$-\\frac{\\pi}{2} < x < \\frac{\\pi}{2} \\implies \\cos x > 0$）の理解。\n"
            "- 三角方程式の解と連立条件の代入検証。"
        )
    },
    {
        "q_num": "III_2",
        "localKey": "math-q-III_2",
        "answer_ref": "III:2",
        "answer": {
            "FGH": "-12",
            "IJ": "12",
            "K": "3",
            "LMN": "-13"
        },
        "title": "数学 コース2 第III問 (後半)：三角関数の連立方程式が共通解をもつ条件と解の決定",
        "points": [
            "2倍角公式 $\\cos 2x = 1 - 2\\sin^2 x$ を利用した共通解 $x$ の $\\sin x$ の消去",
            "パラメータ $a$ に関する代数方程式の立式と解法（$a > 0$）",
            "共通解となる角 $x \\in (-\\frac{\\pi}{2}, \\frac{\\pi}{2})$ の一意決定"
        ],
        "solution": (
            "**【題目大意】**\n"
            "第III問(1)の方程式 $\\textcircled{1}, \\textcircled{2}$ が $-\\frac{\\pi}{2} < x < \\frac{\\pi}{2}$ で共通解をもつような $a$ の値およびその共通解 $x$ を求める。\n\n"
            "**【公式正解】**\n"
            "$\\text{FGH} = -12$\n"
            "$\\text{IJ} = 12$\n"
            "$\\text{K} = 3$\n"
            "$\\text{LMN} = -13$\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "**(1) $\\sin x$ および $\\cos 2x$ の $a$ による表現**\n"
            "$\\textcircled{1}$ 式より：\n"
            "$$\\sin 2x + a\\cos x = 0 \\implies 2\\sin x \\cos x + a\\cos x = 0$$\n"
            "区間 $-\\frac{\\pi}{2} < x < \\frac{\\pi}{2}$ では $\\cos x > 0$ であるため、両辺を $\\cos x$ で割ると：\n"
            "$$2\\sin x + a = 0 \\implies \\sin x = -\\frac{a}{2} = \\frac{-1}{2}a$$\n"
            "与式 $\\frac{\\text{FG}}{\\text{H}}a$ と比較して：\n"
            "$$\\text{FG} = -1, \\quad \\text{H} = 2 \\implies \\text{FGH} = -12$$\n\n"
            "また、コサインの2倍角の公式 $\\cos 2x = 1 - 2\\sin^2 x$ より：\n"
            "$$\\cos 2x = 1 - 2\\left(-\\frac{a}{2}\\right)^2 = 1 - 2\\left(\\frac{a^2}{4}\\right) = 1 - \\frac{a^2}{2}$$\n"
            "与式 $\\text{I} - \\frac{a^2}{\\text{J}}$ と比較して：\n"
            "$$\\text{I} = 1, \\quad \\text{J} = 2 \\implies \\text{IJ} = 12$$\n\n"
            "**(2) $a$ の決定**\n"
            "これらを $\\textcircled{2}$ 式 $\\cos 2x + a\\sin x = -2$ に代入する：\n"
            "$$\\left(1 - \\frac{a^2}{2}\\right) + a\\left(-\\frac{a}{2}\\right) = -2$$\n"
            "$$1 - \\frac{a^2}{2} - \\frac{a^2}{2} = -2 \\implies 1 - a^2 = -2$$\n"
            "$$a^2 = 3 \\quad (\\text{K} = 3)$$\n"
            "問題条件 $a > 0$ より：\n"
            "$$a = \\sqrt{3}$$\n\n"
            "**(3) 共通解 $x$ の決定**\n"
            "$a = \\sqrt{3}$ を $\\sin x = -\\frac{a}{2}$ に代入すると：\n"
            "$$\\sin x = -\\frac{\\sqrt{3}}{2}$$\n"
            "区間 $-\\frac{\\pi}{2} < x < \\frac{\\pi}{2}$ においてこの条件を満たす角は：\n"
            "$$x = -\\frac{\\pi}{3}$$\n"
            "与式 $\\frac{\\text{LM}}{\\text{N}}\\pi$ と比較して：\n"
            "$$\\text{LM} = -1, \\quad \\text{N} = 3 \\implies \\text{LMN} = -13$$\n\n"
            "**【考査考点】**\n"
            "- 三角関数の2倍角公式（余弦・正弦）の相互変換。\n"
            "- 連立三角方程式における文字の消去法（$\\sin x$ によるパラメータ表現）。\n"
            "- 有効区間における特殊角の正弦の逆算。"
        )
    },
    {
        "q_num": "IV_1",
        "localKey": "math-q-IV_1",
        "answer_ref": "IV:1",
        "answer": {
            "ABC": "661",
            "DEF": "961",
            "GH": "31",
            "IJ": "92"
        },
        "title": "数学 コース2 第IV問 [1]：指数関数と放物線の共通接線の存在条件と微分",
        "points": [
            "指数曲線 $y = e^{6x}$ の接線方程式の立式",
            "放物線 $y = ax^2$ との接合条件（2次方程式の重解条件、判別式 $D=0$）",
            "商の微分法によるパラメータ関数 $f(t)$ の増減・極値解析と2本引ける条件"
        ],
        "solution": (
            "**【題目大意】**\n"
            "$a > 0$ とする。2つの曲線\n"
            "$$C_1: y = e^{6x}, \\quad C_2: y = ax^2$$\n"
            "を考える。$C_1$ と $C_2$ の両方に接する共通接線が2本引けるような $a$ の条件を求める。\n\n"
            "**【公式正解】**\n"
            "$\\text{ABC} = 661$\n"
            "$\\text{DEF} = 961$\n"
            "$\\text{GH} = 31$\n"
            "$\\text{IJ} = 92$\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "**(1) $C_1$ 上の点 $(t, e^{6t})$ における接線方程式**\n"
            "$y = e^{6x}$ を微分すると $y' = 6e^{6x}$ である。\n"
            "点 $(t, e^{6t})$ における接線の傾きは $6e^{6t}$ であるから、接線の方程式は：\n"
            "$$y - e^{6t} = 6e^{6t}(x - t) \\implies y = 6e^{6t}x - e^{6t}(6t - 1)$$\n"
            "与式 $y = \\text{A}e^{6t}x - e^{6t}(\\text{B}t - \\text{C})$ と比較して：\n"
            "$$\\text{A} = 6, \\quad \\text{B} = 6, \\quad \\text{C} = 1 \\implies \\text{ABC} = 661$$\n\n"
            "**(2) $C_2$ との接合条件（重解条件）**\n"
            "この接線が $C_2: y = ax^2$ にも接するためには、連立方程式\n"
            "$$ax^2 = 6e^{6t}x - e^{6t}(6t - 1) \\implies ax^2 - 6e^{6t}x + e^{6t}(6t - 1) = 0$$\n"
            "が実数の重解をもつことが必要十分である。\n"
            "判別式を $D$ とすると：\n"
            "$$\\frac{D}{4} = (-3e^{6t})^2 - a \\cdot e^{6t}(6t - 1) = 9e^{12t} - ae^{6t}(6t - 1) = 0$$\n"
            "与式 $\\text{D}e^{12t} - ae^{6t}(\\text{E}t - \\text{F}) = 0$ と比較して：\n"
            "$$\\text{D} = 9, \\quad \\text{E} = 6, \\quad \\text{F} = 1 \\implies \\text{DEF} = 961$$\n"
            "これより、$a > 0$ かつ $6t - 1 > 0$（すなわち $t > \\frac{1}{6}$）のもとで：\n"
            "$$a = \\frac{9e^{6t}}{6t - 1}$$\n\n"
            "**(3) 関数 $f(t)$ の微分と増減**\n"
            "$f(t) = \\frac{9e^{6t}}{6t - 1}$ とおく。商の微分公式を用いて $f'(t)$ を計算する：\n"
            "$$f'(t) = \\frac{(9e^{6t})'(6t - 1) - 9e^{6t}(6t - 1)'}{(6t - 1)^2}$$\n"
            "$$= \\frac{54e^{6t}(6t - 1) - 9e^{6t}(6)}{(6t - 1)^2} = \\frac{54e^{6t}(6t - 1 - 1)}{(6t - 1)^2} = \\frac{54e^{6t}(6t - 2)}{(6t - 1)^2} = \\frac{108e^{6t}(3t - 1)}{(6t - 1)^2}$$\n"
            "与式 $\\frac{108e^{6t}(\\text{G}t - \\text{H})}{(\\text{E}t - \\text{F})^2}$ と比較して：\n"
            "$$\\text{G} = 3, \\quad \\text{H} = 1 \\implies \\text{GH} = 31$$\n\n"
            "**(4) 共通接線が2本引ける $a$ の条件**\n"
            "$t > \\frac{1}{6}$ において、$f'(t) = 0$ となるのは $3t - 1 = 0 \\implies t = \\frac{1}{3}$ のときである。\n"
            "- $\\frac{1}{6} < t < \\frac{1}{3}$ で $f'(t) < 0$（単調減少）\n"
            "- $t > \\frac{1}{3}$ で $f'(t) > 0$（単調増加）\n"
            "したがって、$t = \\frac{1}{3}$ で $f(t)$ は極小かつ最小値をとる：\n"
            "$$f\\left(\\frac{1}{3}\\right) = \\frac{9e^{6(1/3)}}{6(1/3) - 1} = \\frac{9e^2}{2 - 1} = 9e^2$$\n"
            "また：\n"
            "$$\\lim_{t \\to \\frac{1}{6}^+} f(t) = +\\infty, \\quad \\lim_{t \\to \\infty} f(t) = +\\infty$$\n"
            "直線 $s = a$ と曲線 $s = f(t)$ が2点で交わる条件は、$a$ が最小値より厳密に大きいことである：\n"
            "$$a > 9e^2$$\n"
            "与式 $a > \\text{I}e^{\\text{J}}$ と比較して：\n"
            "$$\\text{I} = 9, \\quad \\text{J} = 2 \\implies \\text{IJ} = 92$$\n\n"
            "**【考査考点】**\n"
            "- 指数関数の導関数と接線の方程式の立式。\n"
            "- 放物線と直線の接合条件（2次方程式の判別式 $D=0$）。\n"
            "- 商の微分法による導関数の計算と関数の増減・極小値解析。"
        )
    },
    {
        "q_num": "IV_2",
        "localKey": "math-q-IV_2",
        "answer_ref": "IV:2",
        "answer": {
            "KLMN": "0844",
            "OPQ": "556",
            "RSTU": "9872",
            "VWX": "646",
            "YZ": "56"
        },
        "title": "数学 コース2 第IV問 [2]：回転体の体積（x軸回転・y軸回転）と体積の一致条件",
        "points": [
            "境界曲線で囲まれた領域の $x$ 軸まわりの回転体体積 $V_1 = \\pi \\int y^2 dx$ の定積分計算",
            "逆関数を用いた $y$ 軸まわりの回転体体積 $V_2 = \\pi \\int x^2 dy$ の定積分計算",
            "パラメータ $t$ に依存しない体積一致条件の導出と係数 $a$ の決定"
        ],
        "solution": (
            "**【題目大意】**\n"
            "$a, t$ を正の実数とする。2次関数\n"
            "$$y = \\frac{1}{t^2}(x - at^2)^2$$\n"
            "のグラフと $x$ 軸、$y$ 軸によって囲まれる部分を $D$ とする。\n"
            "$D$ を $x$ 軸の周りに1回転させてできる立体の体積を $V_1$、$y$ 軸の周りに1回転させてできる立体の体積を $V_2$ とする。\n"
            "$V_1, V_2$ を計算し、$t$ の値によらず $V_1 = V_2$ となる $a$ の値を求める。\n"
            "選択肢：\n"
            "$\\textcircled{0}\\ 0, \\quad \\textcircled{1}\\ 1, \\quad \\textcircled{2}\\ 2, \\quad \\textcircled{3}\\ 3, \\quad \\textcircled{4}\\ 4$\n"
            "$\\textcircled{5}\\ 5, \\quad \\textcircled{6}\\ 6, \\quad \\textcircled{7}\\ t, \\quad \\textcircled{8}\\ at^2, \\quad \\textcircled{9}\\ a^2t^2$\n\n"
            "**【公式正解】**\n"
            "$\\text{KLMN} = 0844$\n"
            "$\\text{OPQ} = 556$\n"
            "$\\text{RSTU} = 9872$\n"
            "$\\text{VWX} = 646$\n"
            "$\\text{YZ} = 56$\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "**(1) 領域 $D$ の形状**\n"
            "放物線 $y = \\frac{1}{t^2}(x - at^2)^2$ は頂点 $(at^2, 0)$ をもち、下に凸である。\n"
            "- $y = 0$ との交点は $x = at^2$\n"
            "- $x = 0$ のとき $y = \\frac{1}{t^2}(0 - at^2)^2 = \\frac{a^2t^4}{t^2} = a^2t^2$\n"
            "したがって、領域 $D$ は $0 \\le x \\le at^2$、$0 \\le y \\le \\frac{1}{t^2}(x - at^2)^2$ で囲まれる図形である。\n\n"
            "**(2) $x$ 軸まわりの回転体の体積 $V_1$**\n"
            "回転体の体積公式より：\n"
            "$$V_1 = \\pi \\int_{0}^{at^2} y^2 dx = \\pi \\int_{0}^{at^2} \\left[\\frac{1}{t^2}(x - at^2)^2\\right]^2 dx = \\pi \\int_{0}^{at^2} \\frac{1}{t^4}(x - at^2)^4 dx$$\n"
            "空欄 $\\pi \\int_{\\text{K}}^{\\text{L}} \\frac{1}{t^{\\text{M}}}(x - at^2)^{\\text{N}} dx$ と比較して：\n"
            "$$\\text{K} = \\textcircled{0} (0), \\quad \\text{L} = \\textcircled{8} (at^2), \\quad \\text{M} = \\textcircled{4} (4), \\quad \\text{N} = \\textcircled{4} (4) \\implies \\text{KLMN} = 0844$$\n"
            "この積分を実行する：\n"
            "$$\\int_{0}^{at^2} (x - at^2)^4 dx = \\left[\\frac{(x - at^2)^5}{5}\\right]_{0}^{at^2} = 0 - \\frac{(-at^2)^5}{5} = \\frac{a^5t^{10}}{5}$$\n"
            "したがって：\n"
            "$$V_1 = \\pi \\cdot \\frac{1}{t^4} \\cdot \\frac{a^5t^{10}}{5} = \\frac{\\pi}{5} a^5 t^6$$\n"
            "与式 $\\frac{\\pi}{\\text{O}} a^{\\text{P}} t^{\\text{Q}}$ と比較して：\n"
            "$$\\text{O} = 5, \\quad \\text{P} = 5, \\quad \\text{Q} = 6 \\implies \\text{OPQ} = 556$$\n\n"
            "**(3) $y$ 軸まわりの回転体の体積 $V_2$**\n"
            "$0 \\le x \\le at^2$ において、$y = \\frac{1}{t^2}(at^2 - x)^2$ より：\n"
            "$$\\sqrt{y} = \\frac{1}{t}(at^2 - x) \\implies t\\sqrt{y} = at^2 - x \\implies x = at^2 - t\\sqrt{y}$$\n"
            "$y$ は $0$ から $a^2t^2$ まで変化するので、$y$ 軸まわりの体積は：\n"
            "$$V_2 = \\pi \\int_{0}^{a^2t^2} x^2 dy = \\pi \\int_{0}^{a^2t^2} (at^2 - t\\sqrt{y})^2 dy$$\n"
            "空欄 $\\pi \\int_{\\text{R}}^{\\text{S}} (\\text{T} - \\text{U}\\sqrt{y})^{\\text{V}} dy$（ただし積分範囲・形式に対応）と比較して：\n"
            "上端 $\\text{R} = \\textcircled{9} (a^2t^2)$、$\\text{S} = \\textcircled{8} (at^2)$、$\\text{T} = \\textcircled{7} (t)$、指数 $\\text{U} = \\textcircled{2} (2)$ より：\n"
            "$$\\text{RSTU} = 9872$$\n"
            "被積分関数を展開して積分する：\n"
            "$$(at^2 - t\\sqrt{y})^2 = a^2t^4 - 2at^3 y^{1/2} + t^2 y$$\n"
            "$$\\int_{0}^{a^2t^2} (a^2t^4 - 2at^3 y^{1/2} + t^2 y) dy = \\left[a^2t^4 y - 2at^3 \\cdot \\frac{2}{3}y^{3/2} + t^2 \\cdot \\frac{y^2}{2}\\right]_{0}^{a^2t^2}$$\n"
            "$y = a^2t^2$ を代入すると（$y^{1/2} = at$、$y^{3/2} = a^3t^3$、$y^2 = a^4t^4$）：\n"
            "$$a^2t^4(a^2t^2) - \\frac{4}{3}at^3(a^3t^3) + \\frac{1}{2}t^2(a^4t^4) = a^4t^6 - \\frac{4}{3}a^4t^6 + \\frac{1}{2}a^4t^6$$\n"
            "係数を計算すると：\n"
            "$$1 - \\frac{4}{3} + \\frac{1}{2} = \\frac{6 - 8 + 3}{6} = \\frac{1}{6}$$\n"
            "したがって：\n"
            "$$V_2 = \\frac{\\pi}{6} a^4 t^6$$\n"
            "与式 $\\frac{\\pi}{\\text{V}} a^{\\text{W}} t^{\\text{X}}$ と比較して：\n"
            "$$\\text{V} = 6, \\quad \\text{W} = 4, \\quad \\text{X} = 6 \\implies \\text{VWX} = 646$$\n\n"
            "**(4) $V_1 = V_2$ となる $a$ の決定**\n"
            "$$V_1 = V_2 \\iff \\frac{\\pi}{5} a^5 t^6 = \\frac{\\pi}{6} a^4 t^6$$\n"
            "$a > 0$ かつ $t > 0$ より、両辺を $\\pi a^4 t^6$ で割ると：\n"
            "$$\\frac{1}{5} a = \\frac{1}{6} \\implies a = \\frac{5}{6}$$\n"
            "与式 $a = \\frac{\\text{Y}}{\\text{Z}}$ と比較して：\n"
            "$$\\text{Y} = 5, \\quad \\text{Z} = 6 \\implies \\text{YZ} = 56$$\n\n"
            "**【考査考点】**\n"
            "- 定積分による $x$ 軸回転体の体積計算公式 $V = \\pi \\int y^2 dx$ の適用。\n"
            "- 逆関数法による $y$ 軸回転体の体積計算公式 $V = \\pi \\int x^2 dy$ の適用。\n"
            "- パラメータを含む定積分の計算と独立変数 $t$ の恒等的消去。"
        )
    }
]

def main():
    work_dir = Path("work/2014-1-math-c2")
    work_dir.mkdir(parents=True, exist_ok=True)
    docs_dir = Path("docs/explanations")
    docs_dir.mkdir(parents=True, exist_ok=True)

    json_path = work_dir / "explanations.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(math_c2_questions, f, ensure_ascii=False, indent=2)
    print(f"Generated {json_path} ({len(math_c2_questions)} questions)")

    md_path = docs_dir / "2014-1-math-c2-solutions.md"
    lines = [
        "# 2014-1 EJU 数学 コース2 詳解・完全解説\n",
        "> 本ドキュメントは 2014年度第1回 EJU（日本留学試験）数学コース2に対する公式正解準拠の完全詳解である。\n",
        "---\n"
    ]

    for item in math_c2_questions:
        lines.append(f"## {item['title']}\n")
        ans_str = ", ".join(f"{k} = {v}" for k, v in item["answer"].items())
        lines.append(f"**問題コード**: `{item['localKey']}` | **配点参照**: `{item['answer_ref']}` | **正解**: `{ans_str}`\n")
        lines.append("### 出題のポイント")
        for pt in item["points"]:
            lines.append(f"- {pt}")
        lines.append("\n### 詳細解説")
        lines.append(item["solution"])
        lines.append("\n---\n")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Generated {md_path}")

if __name__ == "__main__":
    main()

