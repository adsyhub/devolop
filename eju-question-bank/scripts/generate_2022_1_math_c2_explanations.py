#!/usr/bin/env python3
"""Generate comprehensive explanations for 2022-1 EJU Mathematics Course 2."""

import json
from pathlib import Path

explanations = {
    "session": "2022-1",
    "subject": "MATHEMATICS",
    "course": "COURSE_2",
    "formCode": "MATHEMATICS_COURSE_2_JA",
    "sections": [
        {
            "sectionId": "I_1",
            "localKey": "math-q-I_1",
            "sectionTitle": "第I問 問1：2次関数の頂点の軌跡と区間線分上の制約条件・2次式の値域",
            "points": [
                "2次関数の平方完成と頂点座標の決定",
                "線分上の点であることによるパラメータの範囲制約（動く頂点）",
                "パラメータ $a$ による2次関数の平方完成と閉区間における最大値・最小値"
            ],
            "officialAnswers": {
                "AB": "24",
                "CD": "64",
                "E": "4",
                "FGH": "315",
                "IJK": "212",
                "LM": "35"
            },
            "detailedSolution": (
                "### 【第I問 問1】詳細解答と解説\n\n"
                "#### (1) 放物線の頂点 P の座標\n"
                "与えられた2次関数は $f(x) = x^2 + ax + b$ である。平方完成を行うと：\n"
                "$$f(x) = \\left(x + \\frac{a}{2}\\right)^2 - \\frac{a^2}{4} + b$$\n"
                "したがって、放物線 $y = f(x)$ の頂点 P の座標は：\n"
                "$$\\text{P}\\left(-\\frac{a}{\\mathbf{2}}, -\\frac{a^2}{\\mathbf{4}} + b\\right)$$\n"
                "よって、$\\mathbf{A = 2, B = 4}$（解答番号 $\\mathbf{AB = 24}$）。\n\n"
                "#### (2) 点 P が線分 AB 上にある条件と $a, b$ の関係式\n"
                "1次関数 $h(x) = -2x$ のグラフと直線 $x = 3$ との交点は $\\text{A}(3, -6)$、直線 $x = -2$ との交点は $\\text{B}(-2, 4)$ である。\n"
                "線分 AB は直線 $y = -2x$ 上の $-2 \\le x \\le 3$ の部分である。\n"
                "頂点 P の $x$ 座標 $-\\frac{a}{2}$ がこの区間内にあるため：\n"
                "$$-2 \\le -\\frac{a}{2} \\le 3 \\iff -6 \\le a \\le 4$$\n"
                "問題文の形式 $-C \\le a \\le D$ と比較して：\n"
                "$$\\mathbf{C = 6, D = 4}\\quad(\\text{解答番号 } \\mathbf{CD = 64})$$\n"
                "また、点 P は直線 $y = -2x$ 上にあるため、その座標を代入すると：\n"
                "$$-\\frac{a^2}{4} + b = -2\\left(-\\frac{a}{2}\\right) = a \\implies b = \\frac{a^2}{\\mathbf{4}} + a$$\n"
                "よって、$\\mathbf{E = 4}$。\n\n"
                "#### (3) $L$ の $a$ による表現と値の範囲\n"
                "定義式 $L = \\{f(3) - h(3)\\} + \\{f(-2) - h(-2)\\}$ を計算する。\n"
                "差の関数 $f(x) - h(x)$ は：\n"
                "$$f(x) - h(x) = x^2 + ax + b - (-2x) = x^2 + (a + 2)x + b$$\n"
                "各値を代入すると：\n"
                "- $f(3) - h(3) = 3^2 + (a + 2)\\cdot 3 + b = 9 + 3a + 6 + b = 3a + b + 15$\n"
                "- $f(-2) - h(-2) = (-2)^2 + (a + 2)(-2) + b = 4 - 2a - 4 + b = -2a + b$\n"
                "したがって：\n"
                "$$L = (3a + b + 15) + (-2a + b) = a + 2b + 15$$\n"
                "$b = \\frac{a^2}{4} + a$ を代入すると：\n"
                "$$L = a + 2\\left(\\frac{a^2}{4} + a\\right) + 15 = a + \\frac{a^2}{2} + 2a + 15 = \\frac{1}{2}a^2 + \\mathbf{3}a + \\mathbf{15}$$\n"
                "よって、$\\mathbf{F = 3, GH = 15}$（解答番号 $\\mathbf{FGH = 315}$）。\n\n"
                "定義域 $-6 \\le a \\le 4$ における $L(a)$ の増減を調べるため、$L(a)$ を平方完成する：\n"
                "$$L(a) = \\frac{1}{2}(a^2 + 6a) + 15 = \\frac{1}{2}\\left((a + 3)^2 - 9\\right) + 15 = \\frac{1}{2}(a + 3)^2 + \\frac{21}{2}$$\n"
                "- 軸は $a = -3$ であり、これは定義域 $[-6, 4]$ の内部にある。\n"
                "- 下に凸であるから、頂点 $a = -3$ で最小値をとる：\n"
                "  $$L_{\\min} = L(-3) = \\frac{21}{2}$$\n"
                "- 最大値は軸 $a = -3$ から最も遠い端点 $a = 4$ でとる（軸からの距離：$|-6 - (-3)| = 3$ に対し $|4 - (-3)| = 7$）：\n"
                "  $$L_{\\max} = L(4) = \\frac{1}{2}(4 + 3)^2 + \\frac{21}{2} = \\frac{49}{2} + \\frac{21}{2} = \\frac{70}{2} = 35$$\n"
                "したがって、$L$ のとり得る値の範囲は：\n"
                "$$\\frac{\\mathbf{21}}{\\mathbf{2}} \\le L \\le \\mathbf{35}$$\n"
                "よって、$\\mathbf{IJ = 21, K = 2}$（解答番号 $\\mathbf{IJK = 212}$）、$\\mathbf{LM = 35}$ である。"
            )
        },
        {
            "sectionId": "I_2",
            "localKey": "math-q-I_2",
            "sectionTitle": "第I問 問2：カードの置換操作と確率・反復試行と条件付き確率",
            "points": [
                "順列・置換の互換操作",
                "全事象 $\\binom{9}{2} = 36$ 通りにおける偶数末尾の分類討論",
                "操作履歴（非復元抽出型制約）による条件付き確率の計算"
            ],
            "officialAnswers": {
                "NOP": "781",
                "QRSTU": "35324",
                "VWX": "736",
                "YZ": "29"
            },
            "detailedSolution": (
                "### 【第I問 問2】詳細解答と解説\n\n"
                "#### 問題の設定\n"
                "1から9までの数字が書かれた9枚のカードが左から昇順 $[1, 2, 3, 4, 5, 6, 7, 8, 9]$ で並んでいる。\n"
                "9桁の整数が偶数になるための必要十分条件は、**最下位（第9番目・末尾）のカードが偶数（2, 4, 6, 8 のいずれか）** であることである。\n"
                "偶数カードは 4 枚、奇数カードは 5 枚（1, 3, 5, 7, 9）である。初期状態では第9位は「9」（奇数）である。\n\n"
                "#### (1) 1回目・2回目ともに9枚の中から2枚を選んで入れ換える場合\n"
                "全事象の選び方は各回 $\\binom{9}{2} = 36$ 通りである。\n\n"
                "**(i) 1回目に「9」以外のカードを入れ換える場合**\n"
                "- 1回目に「9」以外の8枚から2枚を選ぶ方法は $\\binom{8}{2} = 28$ 通り。\n"
                "- この操作後、第9位は依然として「9」のままである。また偶数4枚は依然として第1～8位のいずれかにある。\n"
                "- 2回目の操作で第9位を偶数にするには、第9位の「9」と偶数4枚のいずれかを入れ換える必要があるため、選び方は 4 通り。\n"
                "したがって、この事象が起こる確率は：\n"
                "$$P = \\frac{28}{36} \\times \\frac{4}{36} = \\frac{7}{9} \\times \\frac{1}{9} = \\frac{\\mathbf{7}}{\\mathbf{81}}$$\n"
                "よって、$\\mathbf{N = 7, OP = 81}$（解答番号 $\\mathbf{NOP = 781}$）。\n\n"
                "**(ii) 1回目に「9」の書かれたカードを他のカードと入れ換える場合**\n"
                "1回目に「9」と他のカードを入れ換える方法は $8$ 通り。\n"
                "- **Subcase A（「9」と偶数カードを交換）**：選び方は 4 通り。\n"
                "  1回目の操作後、第9位は偶数となる。2回目の操作後も第9位が偶数であり続けるためには：\n"
                "  1. 第9位を含まない8枚から2枚を選ぶ：$\\binom{8}{2} = 28$ 通り。\n"
                "  2. 第9位の偶数と、第1～8位にある他の偶数（3枚）のいずれかを入れ換える：$3$ 通り。\n"
                "  よって適する選び方は $28 + 3 = 31$ 通り。\n"
                "  確率は $\\frac{4}{36} \\times \\frac{31}{36} = \\frac{124}{1296}$。\n"
                "- **Subcase B（「9」と他の奇数 1, 3, 5, 7 を交換）**：選び方は 4 通り。\n"
                "  1回目の操作後、第9位は別の奇数となる。第1～8位には偶数4枚がすべて残っている。\n"
                "  2回目で第9位を偶数にするには、第9位とその偶数4枚のいずれかを入れ換える必要があり、選び方は 4 通り。\n"
                "  確率は $\\frac{4}{36} \\times \\frac{4}{36} = \\frac{16}{1296}$。\n"
                "両者を合算すると：\n"
                "$$P = \\frac{124 + 16}{1296} = \\frac{140}{1296} = \\frac{\\mathbf{35}}{\\mathbf{324}}$$\n"
                "よって、$\\mathbf{QR = 35, STU = 324}$（解答番号 $\\mathbf{QRSTU = 35324}$）。\n\n"
                "したがって、(1)において2回の操作で偶数になる全確率は (i) と (ii) の和である：\n"
                "$$P_{\\text{全}} = \\frac{7}{81} + \\frac{35}{324} = \\frac{28 + 35}{324} = \\frac{63}{324} = \\frac{\\mathbf{7}}{\\mathbf{36}}$$\n"
                "よって、$\\mathbf{V = 7, WX = 36}$（解答番号 $\\mathbf{VWX = 736}$）。\n\n"
                "#### (2) 2回目は1回目で選んだ2枚を除く残りの7枚から選ぶ場合\n"
                "2回目の選び方は $\\binom{7}{2} = 21$ 通りである。\n"
                "- **Case 1: 1回目に第9位の「9」と偶数カードを入れ換えた場合（4通り）**\n"
                "  1回目の操作後、第9位は偶数となる。2回目の操作対象となる7枚には第9位のカードが含まれないため、第9位は変更されず必ず偶数のまま保たれる。\n"
                "  したがって、2回目のどのような選び方（21通りすべて）でも条件を満たす。\n"
                "  この確率成分は：$\\frac{4}{36} \\times \\frac{21}{21} = \\frac{4}{36}$。\n"
                "- **Case 2: 1回目に第9位以外のカードを入れ換えた場合（$\\binom{8}{2} = 28$ 通り）**\n"
                "  第9位は「9」のままであり、1回目で操作されていないため、2回目の7枚の中に第9位（「9」）が必ず含まれる。\n"
                "  2回目で偶数にするには、第9位と残り7枚の中にある偶数を入れ換えなければならない。\n"
                "  1回目で操作された2枚に含まれる偶数の枚数で場合分けする：\n"
                "  - 奇数2枚を交換（$\\binom{4}{2} = 6$ 通り）：残り7枚に偶数は 4 枚 $\\implies$ 選び方は 4 通り。\n"
                "  - 奇数1枚・偶数1枚を交換（$4 \\times 4 = 16$ 通り）：残り7枚に偶数は 3 枚 $\\implies$ 選び方は 3 通り。\n"
                "  - 偶数2枚を交換（$\\binom{4}{2} = 6$ 通り）：残り7枚に偶数は 2 枚 $\\implies$ 選び方は 2 通り。\n"
                "  2回目に条件を満たす総数は $6 \\times 4 + 16 \\times 3 + 6 \\times 2 = 24 + 48 + 12 = 84$ 通り。\n"
                "  この確率成分は：$\\frac{84}{36 \\times 21} = \\frac{4}{36}$。\n"
                "以上より、求める確率は：\n"
                "$$P = \\frac{4}{36} + \\frac{4}{36} = \\frac{8}{36} = \\frac{\\mathbf{2}}{\\mathbf{9}}$$\n"
                "よって、$\\mathbf{Y = 2, Z = 9}$（解答番号 $\\mathbf{YZ = 29}$）。"
            )
        },
        {
            "sectionId": "II_1",
            "localKey": "math-q-II_1",
            "sectionTitle": "第II問 問1：平面ベクトルの一次結合と点の存在範囲・三角形内部のパラメータ条件",
            "points": [
                "始点を A とする位置ベクトルへの統一変換",
                "係数の和を 1 にする直線のベクトル方程式の変形（定比分点）",
                "点 P が三角形の内部に存在するためのパラメータ $k$ の不等式評価"
            ],
            "officialAnswers": {
                "ABC": "415",
                "DEF": "215",
                "GH": "25",
                "I": "1",
                "JK": "23",
                "LM": "42"
            },
            "detailedSolution": (
                "### 【第II問 問1】詳細解答と解説\n\n"
                "#### (1) $\\overrightarrow{AP}$ の $\\overrightarrow{AB}, \\overrightarrow{AC}$ による表現\n"
                "与えられたベクトル方程式は：\n"
                "$$9\\overrightarrow{PA} + 4\\overrightarrow{PB} + 2\\overrightarrow{PC} = k\\overrightarrow{BC}$$\n"
                "点 A を始点とするベクトルに統一するため、$\\overrightarrow{PX} = \\overrightarrow{AX} - \\overrightarrow{AP}$ を代入する：\n"
                "$$9(-\\overrightarrow{AP}) + 4(\\overrightarrow{AB} - \\overrightarrow{AP}) + 2(\\overrightarrow{AC} - \\overrightarrow{AP}) = k(\\overrightarrow{AC} - \\overrightarrow{AB})$$\n"
                "$$-(9 + 4 + 2)\\overrightarrow{AP} + 4\\overrightarrow{AB} + 2\\overrightarrow{AC} = -k\\overrightarrow{AB} + k\\overrightarrow{AC}$$\n"
                "$$-15\\overrightarrow{AP} = -(4 + k)\\overrightarrow{AB} - (2 - k)\\overrightarrow{AC}$$\n"
                "両辺を $15$ で割ると：\n"
                "$$\\overrightarrow{AP} = \\left( \\frac{\\mathbf{4} + k}{\\mathbf{15}} \\right)\\overrightarrow{AB} + \\left( \\frac{\\mathbf{2} - k}{\\mathbf{15}} \\right)\\overrightarrow{AC}$$\n"
                "問題文の形式 $\\left(\\frac{A+k}{BC}\\right)\\overrightarrow{AB} + \\left(\\frac{D-k}{EF}\\right)\\overrightarrow{AC}$ と比較して：\n"
                "$$\\mathbf{A = 4, BC = 15}\\quad(\\text{解答番号 } \\mathbf{ABC = 415})$$\n"
                "$$\\mathbf{D = 2, EF = 15}\\quad(\\text{解答番号 } \\mathbf{DEF = 215})$$\n\n"
                "#### (2) 点 P の存在範囲（軌跡）の幾何学的特定\n"
                "係数の分子の和に着目すると、$(4 + k) + (2 - k) = 6$（定数）である。\n"
                "そこで $\\frac{1}{15}$ から $\\frac{6}{15} = \\frac{2}{5}$ を括り出し、括弧内の係数の和を 1 にする：\n"
                "$$\\overrightarrow{AP} = \\frac{\\mathbf{2}}{\\mathbf{5}} \\left\\{ \\left( \\frac{4 + k}{6} \\right)\\overrightarrow{AB} + \\left( \\frac{2 - k}{6} \\right)\\overrightarrow{AC} \\right\\}$$\n"
                "問題文の形式 $\\frac{G}{H} \\{ \\cdots \\}$ と比較して、$\\mathbf{G = 2, H = 5}$（解答番号 $\\mathbf{GH = 25}$）。\n"
                "また、係数の和は：\n"
                "$$\\frac{4 + k}{6} + \\frac{2 - k}{6} = \\frac{6}{6} = \\mathbf{1} \\quad (\\mathbf{I = 1})$$\n"
                "したがって、括弧内のベクトルは線分 BC 上の動点を表す。\n"
                "これに定数倍 $\\frac{2}{5}$ がかかっているため：\n"
                "- 辺 AB 上で $\\overrightarrow{AQ} = \\frac{2}{5}\\overrightarrow{AB}$ を満たす点 Q は、辺 AB を $2 : (5 - 2) = 2 : 3$ に内分する点である。\n"
                "- 辺 AC 上で $\\overrightarrow{AR} = \\frac{2}{5}\\overrightarrow{AC}$ を満たす点 R は、辺 AC を $2 : 3$ に内分する点である。\n"
                "よって、点 P の存在範囲は **2点 Q, R を通る直線（QR // BC）** である。\n"
                "したがって、$\\mathbf{J = 2, K = 3}$（解答番号 $\\mathbf{JK = 23}$）。\n\n"
                "#### (3) 点 P が三角形 ABC の内部にあるための $k$ の条件\n"
                "$\\overrightarrow{AP} = s\\overrightarrow{AB} + t\\overrightarrow{AC}$ において、点 P が $\\triangle ABC$ の内部（周を含まない）にあるための必要十分条件は：\n"
                "$$s > 0, \\quad t > 0, \\quad s + t < 1$$\n"
                "ここで $s + t = \\frac{4+k}{15} + \\frac{2-k}{15} = \\frac{6}{15} = \\frac{2}{5} < 1$ は $k$ に依らず常に満たされる。\n"
                "したがって、$s > 0$ かつ $t > 0$ より：\n"
                "- $s = \\frac{4+k}{15} > 0 \\implies k > -4$\n"
                "- $t = \\frac{2-k}{15} > 0 \\implies k < 2$\n"
                "よって、求める $k$ の範囲は：\n"
                "$$-\\mathbf{4} < k < \\mathbf{2}$$\n"
                "問題文の形式 $-L < k < M$ と比較して、$\\mathbf{L = 4, M = 2}$（解答番号 $\\mathbf{LM = 42}$）。"
            )
        },
        {
            "sectionId": "II_2",
            "localKey": "math-q-II_2",
            "sectionTitle": "第II問 問2：複素数平面における直角三角形の幾何変換と重心・極限の評価",
            "points": [
                "複素数の比 $\\frac{\\gamma-1}{\\beta-1}$ による直角三角形の辺比と偏角の表現",
                "重心が原点（$1 + \\beta + \\gamma = 0$）である条件による一次方程式の求解",
                "線分長 $BG, CG$ の陽な関数表示と極限値 $\\theta \\to 0, \\frac{\\pi}{2}$ の計算"
            ],
            "officialAnswers": {
                "N": "1",
                "O": "5",
                "P": "8",
                "Q": "3",
                "R": "0",
                "S": "9",
                "T": "8",
                "U": "5",
                "V": "1",
                "W": "5",
                "X": "2",
                "Y": "8"
            },
            "detailedSolution": (
                "### 【第II問 問2】詳細解答と解説\n\n"
                "#### (1) 直角三角形の複素数による定式化\n"
                "直角三角形 ABC において、$\\angle ABC = \\frac{\\pi}{2}$、$\\angle BAC = \\theta$ である。\n"
                "点 A を表す複素数は $1$、点 B, C を表す複素数は $\\beta, \\gamma$ である。\n"
                "- 斜辺 AC と隣辺 AB の長さの比は：\n"
                "  $$\\left| \\frac{\\gamma - 1}{\\beta - 1} \\right| = \\frac{AC}{AB} = \\frac{1}{\\cos\\theta}$$\n"
                "  選択肢 $\\textcircled{1}$「$\\frac{1}{\\cos\\theta}$」が適する。よって、$\\mathbf{N = 1}$。\n"
                "- ベクトル AB から AC への回転角を調べる。$\\beta$ の虚部が正の配置では、点 A から見て B から C への回転角は $-\\theta$ または $+\\theta$ である。\n"
                "  商を展開すると：\n"
                "  $$\\frac{\\gamma - 1}{\\beta - 1} = \\frac{1}{\\cos\\theta}(\\cos\\theta + i\\sin\\theta) = 1 + i\\tan\\theta$$\n"
                "  選択肢 $\\textcircled{5}$「$1 + i\\tan\\theta$」が適する。よって、$\\mathbf{O = 5}$。\n"
                "- これより分母を払うと：\n"
                "  $$\\gamma - 1 = (1 + i\\tan\\theta)(\\beta - 1) = (1 + i\\tan\\theta)\\beta - 1 - i\\tan\\theta$$\n"
                "  $$(1 + i\\tan\\theta)\\beta - \\gamma - i\\tan\\theta = 0$$\n"
                "  選択肢 $\\textcircled{8}$ が適する。よって、$\\mathbf{P = 8}$。\n\n"
                "#### (2) $\\tan\\theta = t$ による $\\beta, \\gamma$ および線分長の導出\n"
                "重心 G が原点にあることから：\n"
                "$$\\frac{1 + \\beta + \\gamma}{3} = 0 \\implies 1 + \\beta + \\gamma = 0 \\implies \\gamma = -1 - \\beta$$\n"
                "これを関係式 P に代入する（$t = \\tan\\theta$）：\n"
                "$$(1 + ti)\\beta - (-1 - \\beta) - ti = 0 \\implies (2 + ti)\\beta + 1 - ti = 0$$\n"
                "$$(2 + ti)\\beta = -1 + ti \\implies \\beta = \\frac{-1 + ti}{2 + ti}$$\n"
                "選択肢 $\\textcircled{3}$「$\\frac{-1+ti}{2+ti}$」が適する。よって、$\\mathbf{Q = 3}$。\n\n"
                "次に $\\gamma$ を求める：\n"
                "$$\\gamma = -1 - \\frac{-1 + ti}{2 + ti} = \\frac{-(2 + ti) - (-1 + ti)}{2 + ti} = \\frac{-1 - 2ti}{2 + ti} = -\\frac{1 + 2ti}{2 + ti}$$\n"
                "選択肢 $\\textcircled{0}$「$-\\frac{1+2ti}{2+ti}$」が適する。よって、$\\mathbf{R = 0}$。\n\n"
                "線分長 $BG, CG$ は重心が原点であるため $|\\beta|, |\\gamma|$ に等しい：\n"
                "- $BG = |\\beta| = \\frac{|-1 + ti|}{|2 + ti|} = \\frac{\\sqrt{(-1)^2 + t^2}}{\\sqrt{2^2 + t^2}} = \\sqrt{\\frac{1 + t^2}{4 + t^2}}$\n"
                "  選択肢 $\\textcircled{9}$ が適する。よって、$\\mathbf{S = 9}$。\n"
                "- $CG = |\\gamma| = \\frac{|-(1 + 2ti)|}{|2 + ti|} = \\frac{\\sqrt{1^2 + (2t)^2}}{\\sqrt{2^2 + t^2}} = \\sqrt{\\frac{1 + 4t^2}{4 + t^2}}$\n"
                "  選択肢 $\\textcircled{8}$ が適する。よって、$\\mathbf{T = 8}$。\n\n"
                "#### (3) 極限の計算と $BG = 2/3$ のときの $CG$\n"
                "$\\theta \\to +0$ のとき $t = \\tan\\theta \\to 0$、$\\theta \\to \\frac{\\pi}{2} - 0$ のとき $t \\to \\infty$ である。\n"
                "1. $\\lim_{\\theta \\to +0} BG = \\lim_{t \\to 0} \\sqrt{\\frac{1+t^2}{4+t^2}} = \\sqrt{\\frac{1}{4}} = \\frac{1}{2}$（選択肢 $\\textcircled{5}$）$\\implies \\mathbf{U = 5}$。\n"
                "2. $\\lim_{\\theta \\to \\frac{\\pi}{2}-0} BG = \\lim_{t \\to \\infty} \\sqrt{\\frac{1/t^2 + 1}{4/t^2 + 1}} = \\sqrt{1} = 1$（選択肢 $\\textcircled{1}$）$\\implies \\mathbf{V = 1}$。\n"
                "3. $\\lim_{\\theta \\to +0} CG = \\lim_{t \\to 0} \\sqrt{\\frac{1+4t^2}{4+t^2}} = \\sqrt{\\frac{1}{4}} = \\frac{1}{2}$（選択肢 $\\textcircled{5}$）$\\implies \\mathbf{W = 5}$。\n"
                "4. $\\lim_{\\theta \\to \\frac{\\pi}{2}-0} CG = \\lim_{t \\to \\infty} \\sqrt{\\frac{1/t^2 + 4}{4/t^2 + 1}} = \\sqrt{4} = 2$（選択肢 $\\textcircled{2}$）$\\implies \\mathbf{X = 2}$。\n\n"
                "また、$BG = \\frac{2}{3}$ のとき：\n"
                "$$\\sqrt{\\frac{1 + t^2}{4 + t^2}} = \\frac{2}{3} \\implies \\frac{1 + t^2}{4 + t^2} = \\frac{4}{9}$$\n"
                "$$9(1 + t^2) = 4(4 + t^2) \\implies 9 + 9t^2 = 16 + 4t^2 \\implies 5t^2 = 7 \\implies t^2 = \\frac{7}{5}$$\n"
                "このとき $CG$ の値を求めると：\n"
                "$$CG = \\sqrt{\\frac{1 + 4t^2}{4 + t^2}} = \\sqrt{\\frac{1 + 4\\left(\\frac{7}{5}\\right)}{4 + \\frac{7}{5}}} = \\sqrt{\\frac{\\frac{33}{5}}{\\frac{27}{5}}} = \\sqrt{\\frac{33}{27}} = \\sqrt{\\frac{11}{9}} = \\frac{\\sqrt{11}}{3}$$\n"
                "選択肢 $\\textcircled{8}$「$\\frac{\\sqrt{11}}{3}$」が適する。よって、$\\mathbf{Y = 8}$。"
            )
        },
        {
            "sectionId": "III_1",
            "localKey": "math-q-III_1",
            "sectionTitle": "第III問 [1]：対数関数の底の変換と真数条件・多項式関数の導関数と停留点",
            "points": [
                "真数条件と共通定義域 $2 < x < 3$ の決定",
                "底の変換公式による底 $\\frac{1}{3}$ への統合と真数多項式 $g(x)$ の因数分解",
                "積の微分法または置換 $u = x^2 - 4x$ による導関数 $g'(x)$ の因数分解と零点の決定"
            ],
            "officialAnswers": {
                "AB": "23",
                "CDEF": "1322",
                "GHIJK": "22287",
                "LMN": "422",
                "O": "1",
                "P": "0"
            },
            "detailedSolution": (
                "### 【第III問 [1]】詳細解答と解説\n\n"
                "#### (1) 対数関数の真数条件と定義域\n"
                "与えられた関数は：\n"
                "$$f(x) = 2 \\log_{\\frac{1}{3}} \\frac{x-2}{\\sqrt{x-1}} + \\log_{\\frac{\\sqrt{3}}{3}} \\left(-x^2 + 4x - 3\\right) + \\log_9 (x-3)^2$$\n"
                "真数が正である条件を求める：\n"
                "1. $\\frac{x-2}{\\sqrt{x-1}} > 0$ かつ根号内 $x - 1 > 0$ より $x > 2$ かつ $x > 1 \\implies x > 2$。\n"
                "2. $-x^2 + 4x - 3 > 0 \\iff -(x - 1)(x - 3) > 0 \\iff 1 < x < 3$。\n"
                "3. $(x - 3)^2 > 0 \\iff x \\neq 3$。\n"
                "これらすべての共通範囲をとると：\n"
                "$$\\mathbf{2} < x < \\mathbf{3}$$\n"
                "よって、$\\mathbf{A = 2, B = 3}$（解答番号 $\\mathbf{AB = 23}$）。\n\n"
                "#### (2) 底の変換による関数の統合と $g(x)$ の導出\n"
                "すべて底を $\\frac{1}{3}$ に統一する：\n"
                "- $2 \\log_{\\frac{1}{3}} \\frac{x-2}{\\sqrt{x-1}} = \\log_{\\frac{1}{3}} \\left(\\frac{x-2}{\\sqrt{x-1}}\\right)^2 = \\log_{\\frac{1}{3}} \\frac{(x-2)^2}{x-1}$\n"
                "- 底 $\\frac{\\sqrt{3}}{3} = \\frac{1}{\\sqrt{3}} = \\left(\\frac{1}{3}\\right)^{\\frac{1}{2}}$ より：\n"
                "  $$\\log_{\\frac{\\sqrt{3}}{3}} Y = \\frac{\\log_{\\frac{1}{3}} Y}{1/2} = 2 \\log_{\\frac{1}{3}} Y = \\log_{\\frac{1}{3}} Y^2$$\n"
                "  ここで $Y = -x^2 + 4x - 3 = (x-1)(3-x)$ であるから：\n"
                "  $$Y^2 = (x-1)^2 (3-x)^2 = (x-1)^2 (x-3)^2$$\n"
                "- 底 $9 = 3^2 = \\left(\\frac{1}{3}\\right)^{-2}$ より：\n"
                "  $$\\log_9 (x-3)^2 = \\frac{\\log_{\\frac{1}{3}} (x-3)^2}{-2} = -\\log_{\\frac{1}{3}} |x-3| = \\log_{\\frac{1}{3}} \\frac{1}{|x-3|}$$\n"
                "  $2 < x < 3$ において $|x-3| = 3-x$ である。\n"
                "これらを合算すると、真数は積になる：\n"
                "$$g(x) = \\frac{(x-2)^2}{x-1} \\times (x-1)^2 (3-x)^2 \\times \\frac{1}{3-x} = (x-2)^2 (x-1)(3-x)$$\n"
                "符号を整理すると：\n"
                "$$g(x) = - (x - \\mathbf{1})(x - \\mathbf{3})(x - \\mathbf{2})^{\\mathbf{2}}$$\n"
                "問題文の形式 $-(x - C)(x - D)(x - E)^F$（$C < D$）と比較して：\n"
                "$$\\mathbf{C = 1, D = 3, E = 2, F = 2}\\quad(\\text{解答番号 } \\mathbf{CDEF = 1322})$$\n\n"
                "#### (3) $g(x)$ の微分と停留点\n"
                "$g(x) = -(x^2 - 4x + 3)(x^2 - 4x + 4)$ と因数分解できる。\n"
                "$u = x^2 - 4x$ とおくと、$g(x) = -(u + 3)(u + 4) = -(u^2 + 7u + 12)$ である。\n"
                "合成関数の微分法により：\n"
                "$$g'(x) = -(2u + 7) \\cdot u' = -\\{2(x^2 - 4x) + 7\\}(2x - 4) = -2(x - 2)(2x^2 - 8x + 7)$$\n"
                "問題文の形式 $-\\square G (x - \\square H)(\\square I x^2 - \\square J x + \\square K)$ と比較して：\n"
                "$$\\mathbf{G = 2, H = 2, I = 2, J = 8, K = 7}\\quad(\\text{解答番号 } \\mathbf{GHIJK = 22287})$$\n\n"
                "$g'(x) = 0$ の解を求める：\n"
                "- $x - 2 = 0 \\implies x = 2$（定義域の外）\n"
                "- $2x^2 - 8x + 7 = 0$ の解は：\n"
                "  $$x = \\frac{8 \\pm \\sqrt{(-8)^2 - 4(2)(7)}}{2 \\times 2} = \\frac{8 \\pm \\sqrt{64 - 56}}{4} = \\frac{8 \\pm \\sqrt{8}}{4} = \\frac{4 \\pm \\sqrt{2}}{2}$$\n"
                "  $\\frac{4 - \\sqrt{2}}{2} \\approx \\frac{2.586}{2} = 1.293 < 2$（定義域外）。\n"
                "  $\\frac{4 + \\sqrt{2}}{2} \\approx \\frac{5.414}{2} = 2.707 \\in (2, 3)$（定義域内！）。\n"
                "したがって、$2 < x < 3$ の範囲で $g'(x) = 0$ となる唯一の点は：\n"
                "$$x = \\frac{\\mathbf{4} + \\sqrt{\\mathbf{2}}}{\\mathbf{2}}$$\n"
                "よって、$\\mathbf{L = 4, M = 2, N = 2}$（解答番号 $\\mathbf{LMN = 422}$）。\n\n"
                "また、$2 < x < \\frac{4+\\sqrt{2}}{2}$ のとき $g'(x) > 0$（選択肢 $\\textcircled{1}$）$\\implies \\mathbf{O = 1}$。\n"
                "$\\frac{4+\\sqrt{2}}{2} < x < 3$ のとき $g'(x) < 0$（選択肢 $\\textcircled{0}$）$\\implies \\mathbf{P = 0}$。"
            )
        },
        {
            "sectionId": "III_2",
            "localKey": "math-q-III_2",
            "sectionTitle": "第III問 [2]：増減表の作成と底が1未満の対数関数の最大・最小値の反転",
            "points": [
                "真数関数 $g(x)$ の極大値の計算（$u = -7/2$ の代入）",
                "開区間における端点の極限（$g(x) \\to 0^+$）と最小値の非存在性",
                "底 $\\frac{1}{3} < 1$ による単調減少性：真数の極大が全体の極小に対応する反転関係"
            ],
            "officialAnswers": {
                "QR": "32",
                "ST": "14",
                "UV": "23",
                "WX": "34"
            },
            "detailedSolution": (
                "### 【第III問 [2]】詳細解答と解説\n\n"
                "#### (1) 真数関数 $g(x)$ の最大値と最小値の判定\n"
                "$2 < x < 3$ における $g(x)$ の増減表は以下の通りである：\n\n"
                "| $x$ | $(2)$ | $\\cdots$ | $\\frac{4+\\sqrt{2}}{2}$ | $\\cdots$ | $(3)$ |\n"
                "| :---: | :---: | :---: | :---: | :---: | :---: |\n"
                "| $g'(x)$ | | $+$ | $0$ | $-$ | |\n"
                "| $g(x)$ | $(0)$ | $\\nearrow$ | 極大 | $\\searrow$ | $(0)$ |\n\n"
                "- $x \\to 2+0$ および $x \\to 3-0$ で $g(x) \\to 0$ であるが、開区間であるため値 $0$ に到達せず、**最小値は存在しない**。\n"
                "  選択肢 $\\textcircled{3}$「最小」が適する。よって、$\\mathbf{Q = 3}$。\n"
                "- $x = \\frac{4+\\sqrt{2}}{2}$ で $g(x)$ は **最大値** をとる。\n"
                "  選択肢 $\\textcircled{2}$「最大」が適する。よって、$\\mathbf{R = 2}$。\n\n"
                "その最大値を計算する：\n"
                "$2x^2 - 8x + 7 = 0$ より $2(x^2 - 4x) + 7 = 0 \\implies u = x^2 - 4x = -\\frac{7}{2}$ である。\n"
                "$$g\\left(\\frac{4+\\sqrt{2}}{2}\\right) = -(u + 3)(u + 4) = -\\left(-\\frac{7}{2} + 3\\right)\\left(-\\frac{7}{2} + 4\\right) = -\\left(-\\frac{1}{2}\\right)\\left(\\frac{1}{2}\\right) = \\frac{\\mathbf{1}}{\\mathbf{4}}$$\n"
                "よって、$\\mathbf{S = 1, T = 4}$（解答番号 $\\mathbf{ST = 14}$）。\n\n"
                "#### (2) 対数関数 $f(x)$ の最大値・最小値の決定\n"
                "$f(x) = \\log_{\\frac{1}{3}} g(x)$ について、底が $\\frac{1}{3} < 1$ であるため、$f(x)$ は $g(x)$ の **単調減少関数** である：\n"
                "- $g(x) \\to 0^+$ のとき $f(x) \\to +\\infty$ となるため、$f(x)$ は **最大値をもたない**。\n"
                "  選択肢 $\\textcircled{2}$「最大」が適する。よって、$\\mathbf{U = 2}$。\n"
                "- $g(x)$ が最大値をとる $x = \\frac{4+\\sqrt{2}}{2}$ において、$f(x)$ は **最小値** をとる。\n"
                "  選択肢 $\\textcircled{3}$「最小」が適する。よって、$\\mathbf{V = 3}$。\n\n"
                "その最小値は：\n"
                "$$f_{\\min} = \\log_{\\frac{1}{3}} \\left(\\frac{1}{4}\\right) = -\\log_3 \\left(4^{-1}\\right) = \\log_{\\mathbf{3}} \\mathbf{4}$$\n"
                "問題文の形式 $\\log_W X$ と比較して：\n"
                "$$\\mathbf{W = 3, X = 4}\\quad(\\text{解答番号 } \\mathbf{WX = 34})$$ である。"
            )
        },
        {
            "sectionId": "IV_1",
            "localKey": "math-q-IV_1",
            "sectionTitle": "第IV問 [1]：三角関数の差の因数分解と方程式の実数解条件",
            "points": [
                "3倍角の公式または和積・3乗の和の因数分解公式の適用",
                "差の関数 $f(x) - g(x) = (\\sin x + \\cos x)(3 - a + \\frac{a}{2}\\sin 2x)$ の導出",
                "定義域 $[0, 2\\pi/3]$ における $\\sin 2x$ の値域と正の整数パラメータ $a$ の不等式評価"
            ],
            "officialAnswers": {
                "AB": "32",
                "C": "3"
            },
            "detailedSolution": (
                "### 【第IV問 [1]】詳細解答と解説\n\n"
                "#### (1) 差の関数 $f(x) - g(x)$ の因数分解\n"
                "与えられた関数は：\n"
                "$$f(x) = 3\\cos x - a\\sin^3 x, \\quad g(x) = a\\cos^3 x - 3\\sin x$$\n"
                "差をとると：\n"
                "$$f(x) - g(x) = 3(\\cos x + \\sin x) - a(\\sin^3 x + \\cos^3 x)$$\n"
                "3乗の和の因数分解公式 $A^3 + B^3 = (A + B)(A^2 - AB + B^2)$ を適用する：\n"
                "$$\\sin^3 x + \\cos^3 x = (\\sin x + \\cos x)(\\sin^2 x - \\sin x \\cos x + \\cos^2 x) = (\\sin x + \\cos x)\\left(1 - \\frac{1}{2}\\sin 2x\\right)$$\n"
                "共通因数 $(\\sin x + \\cos x)$ で括ると：\n"
                "$$f(x) - g(x) = (\\sin x + \\cos x)\\left[ 3 - a\\left(1 - \\frac{1}{2}\\sin 2x\\right) \\right] = (\\sin x + \\cos x)\\left( \\mathbf{3} - a + \\frac{a}{\\mathbf{2}}\\sin 2x \\right)$$\n"
                "問題文の形式 $(\\sin x + \\cos x)\\left(A - a + \\frac{a}{B}\\sin 2x\\right)$ と比較して：\n"
                "$$\\mathbf{A = 3, B = 2}\\quad(\\text{解答番号 } \\mathbf{AB = 32})$$\n\n"
                "#### (2) 方程式が解をもつための $a$ の範囲\n"
                "方程式 $3 - a + \\frac{a}{2}\\sin 2x = 0$ より：\n"
                "$$\\sin 2x = \\frac{2(a - 3)}{a} = 2 - \\frac{6}{a}$$\n"
                "定義域は $0 \\le x \\le \\frac{2\\pi}{3}$ であるから、角 $2x$ の範囲は：\n"
                "$$0 \\le 2x \\le \\frac{4\\pi}{3}$$\n"
                "この区間において、$\\sin 2x$ のとり得る値の範囲は：\n"
                "$$-\\frac{\\sqrt{3}}{2} \\le \\sin 2x \\le 1$$\n"
                "$a$ は正の整数であるから、$\\sin 2x = 2 - \\frac{6}{a} \\ge 0$ となる範囲に着目すると：\n"
                "$$0 \\le 2 - \\frac{6}{a} \\le 1 \\iff -2 \\le -\\frac{6}{a} \\le -1 \\iff 1 \\le \\frac{6}{a} \\le 2 \\iff 3 \\le a \\le 6$$\n"
                "問題文の形式 $C \\le a \\le C + 3$ と比較して：\n"
                "$$\\mathbf{C = 3}$$（$3 \\le a \\le 3 + 3 = 6$）。"
            )
        },
        {
            "sectionId": "IV_2",
            "localKey": "math-q-IV_2",
            "sectionTitle": "第IV問 [2]：$a=4$ における極値の分析と2曲線で囲まれた面積の定積分",
            "points": [
                "合成関数の導関数の因数分解 $f'(x), g'(x)$",
                "極小値・極大値を与える $x$ 座標の特定",
                "交点座標の特定と 3倍角の公式 $\\sin 3x - \\cos 3x$ による被積分関数の大幅簡略化"
            ],
            "officialAnswers": {
                "DEF": "312",
                "GHI": "712",
                "JKL": "312",
                "M": "2",
                "NOP": "712",
                "QR": "12",
                "STU": "512",
                "VWX": "223"
            },
            "detailedSolution": (
                "### 【第IV問 [2]】詳細解答と解説\n\n"
                "#### (1) $a = 4$ における $f'(x), g'(x)$ と極値\n"
                "$a = 4$ のとき：\n"
                "$$f(x) = 3\\cos x - 4\\sin^3 x, \\quad g(x) = 4\\cos^3 x - 3\\sin x$$\n"
                "1. **$f(x)$ の導関数**：\n"
                "   $$f'(x) = -3\\sin x - 12\\sin^2 x \\cos x = -3\\sin x(1 + 4\\sin x \\cos x) = -\\mathbf{3}\\sin x(\\mathbf{1} + \\mathbf{2}\\sin 2x)$$\n"
                "   よって、$\\mathbf{D = 3, E = 1, F = 2}$（解答番号 $\\mathbf{DEF = 312}$）。\n"
                "   $0 < x < \\frac{2\\pi}{3}$ において $\\sin x > 0$ である。\n"
                "   $1 + 2\\sin 2x = 0 \\iff \\sin 2x = -\\frac{1}{2}$。\n"
                "   $0 \\le 2x \\le \\frac{4\\pi}{3}$ より $2x = \\frac{7\\pi}{6} \\implies x = \\frac{7\\pi}{12}$。\n"
                "   この前後で $f'(x)$ の符号は負から正に変わるため、$x = \\frac{\\mathbf{7}\\pi}{\\mathbf{12}}$ で極小値をとる。\n"
                "   よって、$\\mathbf{GHI = 712}$。\n\n"
                "2. **$g(x)$ の導関数**：\n"
                "   $$g'(x) = 12\\cos^2 x(-\\sin x) - 3\\cos x = -3\\cos x(1 + 4\\sin x \\cos x) = -\\mathbf{3}\\cos x(\\mathbf{1} + \\mathbf{2}\\sin 2x)$$\n"
                "   よって、$\\mathbf{J = 3, K = 1, L = 2}$（解答番号 $\\mathbf{JKL = 312}$）。\n"
                "   停留点は $\\cos x = 0 \\implies x = \\frac{\\pi}{\\mathbf{2}}$、および $\\sin 2x = -\\frac{1}{2} \\implies x = \\frac{\\mathbf{7}\\pi}{\\mathbf{12}}$ である。\n"
                "   増減を調べると：\n"
                "   - $x = \\frac{\\pi}{2}$ で極小値をとる $\\implies \\mathbf{M = 2}$。\n"
                "   - $x = \\frac{7\\pi}{12}$ で極大値をとる $\\implies \\mathbf{NOP = 712}$。\n\n"
                "#### (2) 2曲線の交点と囲まれた部分の面積 $S$\n"
                "$f(x) - g(x) = 0$ の交点の $x$ 座標を求める：\n"
                "$$f(x) - g(x) = (\\sin x + \\cos x)(3 - 4 + 2\\sin 2x) = (\\sin x + \\cos x)(2\\sin 2x - 1) = 0$$\n"
                "$0 \\le x \\le \\frac{2\\pi}{3}$ において $\\sin x + \\cos x = \\sqrt{2}\\sin\\left(x + \\frac{\\pi}{4}\\right) > 0$ であるから：\n"
                "$$2\\sin 2x - 1 = 0 \\iff \\sin 2x = \\frac{1}{2}$$\n"
                "$0 \\le 2x \\le \\frac{4\\pi}{3}$ より：\n"
                "$$2x = \\frac{\\pi}{6}, \\; \\frac{5\\pi}{6} \\implies x = \\frac{\\pi}{\\mathbf{12}}, \\; \\frac{\\mathbf{5}\\pi}{\\mathbf{12}}$$\n"
                "よって、$\\mathbf{QR = 12, STU = 512}$。\n\n"
                "この区間 $\\left[\\frac{\\pi}{12}, \\frac{5\\pi}{12}\\right]$ において $f(x) \\ge g(x)$ である。\n"
                "被積分関数について、3倍角の公式 $\\sin 3x = 3\\sin x - 4\\sin^3 x, \\cos 3x = 4\\cos^3 x - 3\\cos x$ を用いると：\n"
                "$$f(x) - g(x) = (3\\sin x - 4\\sin^3 x) + (3\\cos x - 4\\cos^3 x) = \\sin 3x - \\cos 3x$$\n"
                "したがって、面積 $S$ は：\n"
                "$$S = \\int_{\\frac{\\pi}{12}}^{\\frac{5\\pi}{12}} (\\sin 3x - \\cos 3x) \\, dx = \\left[ -\\frac{1}{3}\\cos 3x - \\frac{1}{3}\\sin 3x \\right]_{\\frac{\\pi}{12}}^{\\frac{5\\pi}{12}} = -\\frac{1}{3} \\left[ \\cos 3x + \\sin 3x \\right]_{\\frac{\\pi}{12}}^{\\frac{5\\pi}{12}}$$\n"
                "上下端の値を代入する：\n"
                "- $x = \\frac{5\\pi}{12}$ のとき $3x = \\frac{5\\pi}{4}$：\n"
                "  $$\\cos\\frac{5\\pi}{4} + \\sin\\frac{5\\pi}{4} = -\\frac{\\sqrt{2}}{2} - \\frac{\\sqrt{2}}{2} = -\\sqrt{2}$$\n"
                "- $x = \\frac{\\pi}{12}$ のとき $3x = \\frac{\\pi}{4}$：\n"
                "  $$\\cos\\frac{\\pi}{4} + \\sin\\frac{\\pi}{4} = \\frac{\\sqrt{2}}{2} + \\frac{\\sqrt{2}}{2} = \\sqrt{2}$$\n"
                "したがって：\n"
                "$$S = -\\frac{1}{3}\\left(-\\sqrt{2} - \\sqrt{2}\\right) = -\\frac{1}{3}\\left(-2\\sqrt{2}\\right) = \\frac{\\mathbf{2}\\sqrt{\\mathbf{2}}}{\\mathbf{3}}$$\n"
                "問題文の形式 $\\frac{V\\sqrt{W}}{X}$ と比較して：\n"
                "$$\\mathbf{V = 2, W = 2, X = 3}\\quad(\\text{解答番号 } \\mathbf{VWX = 223})$$ である。"
            )
        }
    ]
}

# Write JSON
out_json = Path("work/2022-1-math-c2/explanations.json")
out_json.parent.mkdir(parents=True, exist_ok=True)
out_json.write_text(json.dumps(explanations, ensure_ascii=False, indent=2), encoding="utf-8")

# Write Markdown
md_content = r"""# 2022年度 第1回（2022-1）EJU 日本留学試験 数学コース2 全問詳細解説

- **試験科目**：数学（コース2 / Mathematics Course 2）
- **対象試験**：2022年度第1回（令和4年6月実施）
- **形式コード**：`MATHEMATICS_COURSE_2_JA`
- **問題構成**：第I問 ～ 第IV問（計8問 / 8大問・小問ユニット）
- **解答形式**：マーク式（数字・符号・選択肢選択）

---

## 数学コース2 公式正解一覧表

| 大問 | 設問 | 解答記号 | 公式正解 | 考査分野・配点項目 |
| :--- | :--- | :--- | :--- | :--- |
| **第I問** | 問1 | AB | **24** | 放物線の頂点座標 $(-\\frac{a}{2}, -\\frac{a^2}{4}+b)$ |
| | | CD | **64** | 線分AB上の制約 $-6 \\le a \\le 4$ |
| | | E | **4** | 頂点の軌跡条件 $b = \\frac{a^2}{4} + a$ |
| | | FGH | **315** | $L = \\frac{1}{2}a^2 + 3a + 15$ |
| | | IJK | **212** | 最小値 $\\frac{21}{2}$ ($a = -3$) |
| | | LM | **35** | 最大値 $35$ ($a = 4$) |
| | 問2 | NOP | **781** | (1)(i) 9以外のカード置換 $\\frac{7}{81}$ |
| | | QRSTU | **35324** | (1)(ii) 9を含むカード置換 $\\frac{35}{324}$ |
| | | VWX | **736** | (1) 全確率 $\\frac{7}{36}$ |
| | | YZ | **29** | (2) 非復元選択確率 $\\frac{2}{9}$ |
| **第II問** | 問1 | ABC | **415** | ベクトル係数 $\\frac{4+k}{15}$ |
| | | DEF | **215** | ベクトル係数 $\\frac{2-k}{15}$ |
| | | GH | **25** | 直線方程式比率 $\\frac{2}{5}$ |
| | | I | **1** | 内分係数の和 $1$ |
| | | JK | **23** | 内分比 $2 : 3$ |
| | | LM | **42** | 三角形内部の存在範囲 $-4 < k < 2$ |
| | 問2 | N | **1** | 辺比 $\\frac{1}{\\cos\\theta}$ |
| | | O | **5** | 複素数商 $1 + i\\tan\\theta$ |
| | | P | **8** | 一次関係式 $(1+i\\tan\\theta)\\beta - \\gamma - i\\tan\\theta = 0$ |
| | | Q | **3** | $\\beta = \\frac{-1+ti}{2+ti}$ |
| | | R | **0** | $\\gamma = -\\frac{1+2ti}{2+ti}$ |
| | | S | **9** | $BG = \\sqrt{\\frac{1+t^2}{4+t^2}}$ |
| | | T | **8** | $CG = \\sqrt{\\frac{1+4t^2}{4+t^2}}$ |
| | | U | **5** | $\\lim_{\\theta \\to 0} BG = 1/2$ |
| | | V | **1** | $\\lim_{\\theta \\to \\pi/2} BG = 1$ |
| | | W | **5** | $\\lim_{\\theta \\to 0} CG = 1/2$ |
| | | X | **2** | $\\lim_{\\theta \\to \\pi/2} CG = 2$ |
| | | Y | **8** | $BG=2/3$ のときの $CG = \\frac{\\sqrt{11}}{3}$ |
| **第III問** | [1] | AB | **23** | 定義域 $2 < x < 3$ |
| | | CDEF | **1322** | $g(x) = -(x-1)(x-3)(x-2)^2$ |
| | | GHIJK | **22287** | $g'(x) = -2(x-2)(2x^2-8x+7)$ |
| | | LMN | **422** | 停留点 $x = \\frac{4+\\sqrt{2}}{2}$ |
| | | O | **1** | 区間(i)の導関数符号 $>$ |
| | | P | **0** | 区間(ii)の導関数符号 $<$ |
| | [2] | QR | **32** | $g(x)$ は最小なし・最大あり |
| | | ST | **14** | $g(x)$ の最大値 $1/4$ |
| | | UV | **23** | $f(x)$ は最大なし・最小あり |
| | | WX | **34** | $f(x)$ の最小値 $\\log_3 4$ |
| **第IV問** | [1] | AB | **32** | $f(x)-g(x) = (\\sin x+\\cos x)(3-a+\\frac{a}{2}\\sin 2x)$ |
| | | C | **3** | 実数解存在条件 $3 \\le a \\le 6$ |
| | [2] | DEF | **312** | $f'(x) = -3\\sin x(1+2\\sin 2x)$ |
| | | GHI | **712** | $f(x)$ 極小点 $x = \\frac{7\\pi}{12}$ |
| | | JKL | **312** | $g'(x) = -3\\cos x(1+2\\sin 2x)$ |
| | | M | **2** | $g(x)$ 極小点 $x = \\pi/2$ |
| | | NOP | **712** | $g(x)$ 極大点 $x = \\frac{7\\pi}{12}$ |
| | | QR | **12** | 曲線交点1 $x = \\frac{\\pi}{12}$ |
| | | STU | **512** | 曲線交点2 $x = \\frac{5\\pi}{12}$ |
| | | VWX | **223** | 囲まれた面積 $S = \\frac{2\\sqrt{2}}{3}$ |

---

## 逐問詳細推導与解説

"""

for s in explanations["sections"]:
    md_content += "\n---\n\n## " + s["sectionTitle"] + "\n\n"
    points_str = ", ".join(s["points"])
    md_content += f"**【考査考点】**：{points_str}\n\n"
    md_content += s["detailedSolution"] + "\n"

out_md = Path("docs/explanations/2022-1-math-c2-solutions.md")
out_md.parent.mkdir(parents=True, exist_ok=True)
out_md.write_text(md_content, encoding="utf-8")
print(f"Generated {out_json} and {out_md} successfully.")
