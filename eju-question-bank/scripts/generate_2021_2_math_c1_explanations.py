#!/usr/bin/env python3
"""Generate comprehensive explanations for 2021-2 EJU Mathematics Course 1."""

import json
from pathlib import Path

explanations = {
    "session": "2021-2",
    "subject": "MATHEMATICS",
    "course": "COURSE_1",
    "formCode": "MATHEMATICS_COURSE_1_JA",
    "sections": [
        {
            "localKey": "math-q-I_1",
            "sectionId": "I_1",
            "sectionTitle": "第I問 問1：2次関数の頂点・軸の場合分けと閉区間における最大値条件",
            "points": [
                "2次関数の平方完成 $f(x) = a(x-p)^2 + q$ と頂点の導出",
                "定義域 $1 \\le x \\le 4$ に対する対称軸 $x = a+1$ の位置による場合分け",
                "区間の端点および頂点における最大値方程式の解法"
            ],
            "officialAnswers": {
                "A": "1",
                "B": "2",
                "C": "0",
                "D": "4",
                "E": "4",
                "F": "3",
                "GH": "86",
                "IJKLM": "40126"
            },
            "detailedSolution": (
                "### 【第I問 問1】詳細解答と解説\n\n"
                "#### 1. 平方完成と頂点座標の決定\n"
                "与えられた2次関数は：\n"
                "$$f(x) = -2x^2 + 4(a+1)x - a^2 - 5a$$\n"
                "平方完成を行う：\n"
                "$$f(x) = -2\\left[x^2 - 2(a+1)x\\right] - a^2 - 5a$$\n"
                "$$= -2\\left[(x - (a+1))^2 - (a+1)^2\\right] - a^2 - 5a$$\n"
                "$$= -2(x - (a+1))^2 + 2(a^2 + 2a + 1) - a^2 - 5a$$\n"
                "$$= -2(x - (a+1))^2 + a^2 - a + 2$$\n"
                "したがって、放物線 $y = f(x)$ の頂点の座標は：\n"
                "$$\\left(a + 1,\\, a^2 - a + 2\\right)$$\n"
                "となり、$\\mathbf{A = 1},\\, \\mathbf{B = 2}$ である。\n"
                "また、対称軸の方程式は $x = a + 1$ である。\n\n"
                "#### 2. 軸の位置による場合分けと最大値条件\n"
                "放物線は上に凸（$x^2$ の係数が $-2 < 0$）であるから、閉区間 $1 \\le x \\le 4$ における最大値は軸の位置によって次のように場合分けされる。\n\n"
                "**(i) 軸が定義域の左外側にある場合（$a+1 \\le 1 \\iff a \\le 0$）：**\n"
                "このとき $\\mathbf{C = 0}$ である。\n"
                "関数は区間 $1 \\le x \\le 4$ で単調減少するため、最大値は左端 $x = 1$ でとる。\n"
                "$$f(1) = -2(1)^2 + 4(a+1)(1) - a^2 - 5a = -2 + 4a + 4 - a^2 - 5a = -a^2 - a + 2$$\n"
                "条件より最大値が 2 であるから：\n"
                "$$-a^2 - a + 2 = 2 \\implies a^2 + a = 0 \\implies a(a+1) = 0$$\n"
                "よって $a = 0$ または $a = -1$。いずれも $a \\le 0$ を満たす。\n"
                "- $a = 0$ のとき：\n"
                "  $$f(x) = -2x^2 + 4(0+1)x - 0 = -2x^2 + 4x$$\n"
                "  よって $\\mathbf{D = 4}$ である。\n"
                "- $a = -1$ のとき：\n"
                "  $$f(x) = -2x^2 + 4(0)x - (1 - 5) = -2x^2 + 4$$\n"
                "  よって $\\mathbf{E = 4}$ である。\n\n"
                "**(ii) 軸が定義域の内部にある場合（$1 < a+1 \\le 4 \\iff 0 < a \\le 3$）：**\n"
                "このとき $\\mathbf{F = 3}$ である。\n"
                "最大値は頂点でとり、その値は頂点の $y$ 座標 $a^2 - a + 2$ である。\n"
                "$$a^2 - a + 2 = 2 \\implies a^2 - a = 0 \\implies a(a-1) = 0$$\n"
                "$0 < a \\le 3$ より $a = 1$ である。\n"
                "$a = 1$ を代入すると：\n"
                "$$f(x) = -2x^2 + 4(2)x - (1 + 5) = -2x^2 + 8x - 6$$\n"
                "よって、$\\mathbf{G = 8},\\, \\mathbf{H = 6}$（解答番号 $\\mathbf{GH = 86}$）である。\n\n"
                "**(iii) 軸が定義域の右外側にある場合（$a+1 > 4 \\iff a > 3$）：**\n"
                "関数は区間 $1 \\le x \\le 4$ で単調増加するため、最大値は右端 $x = 4$ でとる。\n"
                "$$f(4) = -2(4)^2 + 4(a+1)(4) - a^2 - 5a = -32 + 16a + 16 - a^2 - 5a = -a^2 + 11a - 16$$\n"
                "条件より最大値が 2 であるから：\n"
                "$$-a^2 + 11a - 16 = 2 \\implies a^2 - 11a + 18 = 0$$\n"
                "$$(a - 2)(a - 9) = 0$$\n"
                "$a > 3$ であるから $a = 9$ と定まる。\n"
                "$a = 9$ を代入すると：\n"
                "$$4(a+1) = 4(10) = 40$$\n"
                "$$-a^2 - 5a = -81 - 45 = -126$$\n"
                "したがって、求める関数は：\n"
                "$$f(x) = -2x^2 + 40x - 126$$\n"
                "よって、$\\mathbf{IJ = 40},\\, \\mathbf{KLM = 126}$（解答番号 $\\mathbf{IJKLM = 40126}$）である。"
            )
        },
        {
            "localKey": "math-q-I_2",
            "sectionId": "I_2",
            "sectionTitle": "第I問 問2：球と箱の順列・重複度と条件付き配置の場合の数",
            "points": [
                "異なる球の異なる箱への順列 $P(n, r)$",
                "同一箱に入る球の選択と箱の割当て",
                "奇数・偶数番号の箱への条件付き配置と積の法則"
            ],
            "officialAnswers": {
                "NOP": "840",
                "QRS": "168",
                "TU": "16",
                "V": "9",
                "WXY": "144"
            },
            "detailedSolution": (
                "### 【第I問 問2】詳細解答と解説\n\n"
                "赤・黄・緑・青の異なる4個の球と、1から7までの番号がついた7個の異なる箱がある。\n\n"
                "#### (1) 4個の球を7個の箱に1個ずつ入れる入れ方\n"
                "7個の異なる箱から4個を選び、4個の異なる球を順序をつけて対応させる順列である：\n"
                "$$P(7, 4) = 7 \\times 6 \\times 5 \\times 4 = 840$$\n"
                "よって、$\\mathbf{NOP = 840}$ 通りである。\n\n"
                "#### (2) 4個のうち3個の球を同じ1つの箱に入れ、残りの1個を他の箱に入れる入れ方\n"
                "1. 同じ箱に入る3個の球の選び方：$\\binom{4}{3} = 4$ 通り。\n"
                "2. その3個の球を入れる箱の選び方：7通り。\n"
                "3. 残った1個の球を入れる箱の選び方：残りの6個の箱から1個選ぶので 6通り。\n"
                "積の法則より：\n"
                "$$4 \\times 7 \\times 6 = 168$$\n"
                "よって、$\\mathbf{QRS = 168}$ 通りである。\n\n"
                "#### (3) 奇数番号箱と偶数番号箱への条件付き配置\n"
                "1から7までの番号のうち：\n"
                "- 奇数番号の箱：1, 3, 5, 7 の計4個。\n"
                "- 偶数番号の箱：2, 4, 6 の計3個。\n\n"
                "1. **赤色と黄色の球の入れ方**：\n"
                "   赤と黄の2個の球を4個の奇数番号の箱に入れる。各球について4つの箱のいずれを選んでもよいため：\n"
                "   $$4 \\times 4 = 16$$\n"
                "   よって、$\\mathbf{TU = 16}$ 通り。\n"
                "2. **緑色と青色の球の入れ方**：\n"
                "   緑と青の2個の球を3個の偶数番号の箱に入れる。各球について3つの箱のいずれを選んでもよいため：\n"
                "   $$3 \\times 3 = 9$$\n"
                "   よって、$\\mathbf{V = 9}$ 通り。\n"
                "3. **全体の入れ方**：\n"
                "   積の法則により：\n"
                "   $$16 \\times 9 = 144$$\n"
                "   よって、$\\mathbf{WXY = 144}$ 通りである。"
            )
        },
        {
            "localKey": "math-q-II_1",
            "sectionId": "II_1",
            "sectionTitle": "第II問 問1：分母の有理化・対称式の計算および高次多項式の値",
            "points": [
                "無理数の有理化と基本対称式 $x + \\frac{1}{x}$ の計算",
                "分数式の相反的変形と対称式の応用",
                "2次関係式 $x^2 - 5x + 1 = 0$ を用いた高次式の因数分解と値の導出"
            ],
            "officialAnswers": {
                "AB": "52",
                "C": "5",
                "DEFG": "1929",
                "HI": "-1",
                "JKL": "105"
            },
            "detailedSolution": (
                "### 【第II問 問1】詳細解答と解説\n\n"
                "#### (1) 分母の有理化\n"
                "$$x = \\frac{2}{5 - \\sqrt{21}}$$\n"
                "分子・分母に共役な数 $5 + \\sqrt{21}$ を掛ける：\n"
                "$$x = \\frac{2(5 + \\sqrt{21})}{(5 - \\sqrt{21})(5 + \\sqrt{21})} = \\frac{2(5 + \\sqrt{21})}{25 - 21} = \\frac{2(5 + \\sqrt{21})}{4} = \\frac{5 + \\sqrt{21}}{2}$$\n"
                "よって、$\\mathbf{A = 5},\\, \\mathbf{B = 2}$（解答番号 $\\mathbf{AB = 52}$）である。\n\n"
                "#### (2) 基本対称式と分数式の値\n"
                "$x$ の逆数 $\\frac{1}{x}$ は：\n"
                "$$\\frac{1}{x} = \\frac{5 - \\sqrt{21}}{2}$$\n"
                "したがって：\n"
                "$$x + \\frac{1}{x} = \\frac{5 + \\sqrt{21}}{2} + \\frac{5 - \\sqrt{21}}{2} = \\frac{10}{2} = 5$$\n"
                "よって、$\\mathbf{C = 5}$ である。\n\n"
                "また、平方の関係から：\n"
                "$$x^2 + \\frac{1}{x^2} = \\left(x + \\frac{1}{x}\\right)^2 - 2 = 5^2 - 2 = 23$$\n"
                "与えられた分数式の分子・分母をともに $x^2$ で割る：\n"
                "$$\\frac{1 - x + x^2 - x^3 + x^4}{1 + x + x^2 + x^3 + x^4} = \\frac{\\left(x^2 + \\frac{1}{x^2}\\right) - \\left(x + \\frac{1}{x}\\right) + 1}{\\left(x^2 + \\frac{1}{x^2}\\right) + \\left(x + \\frac{1}{x}\\right) + 1}$$\n"
                "数値を代入すると：\n"
                "$$= \\frac{23 - 5 + 1}{23 + 5 + 1} = \\frac{19}{29}$$\n"
                "よって、$\\mathbf{DE = 19},\\, \\mathbf{FG = 29}$（解答番号 $\\mathbf{DEFG = 1929}$）である。\n\n"
                "#### (3) 2次関係式と多項式の値\n"
                "$x = \\frac{5 + \\sqrt{21}}{2} \\implies 2x - 5 = \\sqrt{21}$。\n"
                "両辺を2乗すると：\n"
                "$$4x^2 - 20x + 25 = 21 \\implies 4x^2 - 20x + 4 = 0 \\implies x^2 - 5x + 1 = 0$$\n"
                "したがって：\n"
                "$$x^2 - 5x = -1$$\n"
                "よって、$\\mathbf{HI = -1}$ である。\n\n"
                "次に、与えられた6次多項式を因数分解して $x^2 - 5x$ を含むペアに組み替える：\n"
                "$$P = (x^2 - 1)(x^2 - 7x + 12)(x^2 - 8x + 12)$$\n"
                "各2次式を1次式に因数分解すると：\n"
                "$$x^2 - 1 = (x - 1)(x + 1)$$\n"
                "$$x^2 - 7x + 12 = (x - 3)(x - 4)$$\n"
                "$$x^2 - 8x + 12 = (x - 2)(x - 6)$$\n"
                "和が 5 になるように組み合わせる：\n"
                "- $(x - 1)(x - 4) = x^2 - 5x + 4$\n"
                "- $(x - 2)(x - 3) = x^2 - 5x + 6$\n"
                "- $(x + 1)(x - 6) = x^2 - 5x - 6$\n"
                "したがって：\n"
                "$$P = (x^2 - 5x + 4)(x^2 - 5x + 6)(x^2 - 5x - 6)$$\n"
                "$x^2 - 5x = -1$ を代入すると：\n"
                "$$P = (-1 + 4)(-1 + 6)(-1 - 6) = 3 \\times 5 \\times (-7) = -105$$\n"
                "題意は $-JKL$ であるから、$\\mathbf{JKL = 105}$ である。"
            )
        },
        {
            "localKey": "math-q-II_2",
            "sectionId": "II_2",
            "sectionTitle": "第II問 問2：パラメータを含む連立2次不等式の解と共通解の存在条件",
            "points": [
                "2次不等式の因数分解と解の表現",
                "パラメータ $a$ の値による根の大小関係の分類",
                "連立不等式が共通解をもつための区間交差条件"
            ],
            "officialAnswers": {
                "MNO": "-12",
                "P": "1",
                "Q": "6",
                "R": "9",
                "S": "0",
                "TU": "34",
                "VW": "32"
            },
            "detailedSolution": (
                "### 【第II問 問2】詳細解答と解説\n\n"
                "2つの関数：\n"
                "$$f(x) = 2x^2 + (1 - 2a^2)x - a^2$$\n"
                "$$g(x) = x^2 + (a + 1)x - 2a^2 + 5a - 2$$\n"
                "に関する連立不等式 $f(x) < 0$ かつ $g(x) < 0$ を考える。\n\n"
                "#### (1) 不等式 $f(x) < 0$ の解\n"
                "$f(x)$ を因数分解する：\n"
                "$$f(x) = 2x^2 - 2a^2 x + x - a^2 = 2x(x - a^2) + 1(x - a^2) = (2x + 1)(x - a^2)$$\n"
                "方程式 $f(x) = 0$ の2根は $x = -\\frac{1}{2}$ と $x = a^2$ である。\n"
                "実数 $a$ に対し $a^2 \\ge 0 > -\\frac{1}{2}$ であるから、不等式 $f(x) < 0$ の解は常に：\n"
                "$$-\\frac{1}{2} < x < a^2$$\n"
                "よって、$\\mathbf{MNO = -12}$（$\\frac{-1}{2} < x < a^2$）である。\n\n"
                "#### (2) 不等式 $g(x) < 0$ の解と $a$ による場合分け\n"
                "$g(x)$ の定数項を整理する：\n"
                "$$-2a^2 + 5a - 2 = -(2a^2 - 5a + 2) = -(2a - 1)(a - 2) = (1 - 2a)(a - 2)$$\n"
                "また、$(a - 2) + (1 - 2a) = -a - 1$ となり、$x$ の係数 $a+1$ と符号が逆転する。\n"
                "したがって、$g(x)$ は次のように因数分解できる：\n"
                "$$g(x) = (x - (a - 2))(x - (1 - 2a))$$\n"
                "2根は $x_1 = a - 2$ と $x_2 = 1 - 2a$ である。\n"
                "これらの大小を比較する：\n"
                "$$(a - 2) - (1 - 2a) = 3a - 3 = 3(a - 1)$$\n"
                "したがって、分岐点となる値は $a = 1$ であり、$\\mathbf{P = 1}$ である。\n\n"
                "- **$a < 1$ のとき**：$a - 2 < 1 - 2a$ であるから：\n"
                "  $$a - 2 < x < -2a + 1$$\n"
                "  これは選択肢 $\\textcircled{6}$ に対応する。よって $\\mathbf{Q = 6}$。\n"
                "- **$a = 1$ のとき**：2根が一致し、$g(x) = (x + 1)^2$ となる。\n"
                "  実数 $x$ に対し $(x+1)^2 < 0$ を満たす解は存在しない（解はない）。\n"
                "  これは選択肢 $\\textcircled{9}$ に対応する。よって $\\mathbf{R = 9}$。\n"
                "- **$a > 1$ のとき**：$1 - 2a < a - 2$ であるから：\n"
                "  $$-2a + 1 < x < a - 2$$\n"
                "  これは選択肢 $\\textcircled{0}$ に対応する。よって $\\mathbf{S = 0}$。\n\n"
                "#### (3) 連立不等式が解をもつ $a$ の範囲\n"
                "連立不等式が解をもつためには、区間 $\\left(-\\frac{1}{2}, a^2\\right)$ と $g(x) < 0$ の解の区間が共通部分をもつ必要がある。\n\n"
                "1. **$a < 1$ のとき**：\n"
                "   $g(x) < 0$ の解は $a - 2 < x < -2a + 1$。\n"
                "   共通部分をもつ条件は、左側の区間の下限が右側の区間の上限より小さく、かつ左側の区間の上限が右側の区間の下限より大きいことである。\n"
                "   - 下限条件：$a - 2 < a^2 \\iff a^2 - a + 2 > 0$（判別式 $D = 1 - 8 < 0$ より全ての実数 $a$ で常に成立）。\n"
                "   - 上限条件：$-2a + 1 > -\\frac{1}{2} \\iff 2a < \\frac{3}{2} \\iff a < \\frac{3}{4}$。\n"
                "   $a < 1$ との共通範囲は $a < \\frac{3}{4}$ である。\n"
                "   よって、$\\mathbf{TU = 34}$。\n\n"
                "2. **$a > 1$ のとき**：\n"
                "   $g(x) < 0$ の解は $-2a + 1 < x < a - 2$。\n"
                "   共通部分をもつ条件は：\n"
                "   - $a - 2 > -\\frac{1}{2} \\iff a > \\frac{3}{2}$。\n"
                "   - また、$-2a + 1 < a^2 \\iff a^2 + 2a - 1 > 0$ であるが、$a > \\frac{3}{2}$ では明らかに成立する。\n"
                "   $a > 1$ との共通範囲は $a > \\frac{3}{2}$ である。\n"
                "   よって、$\\mathbf{VW = 32}$。\n\n"
                "以上より、求める範囲は $a < \\frac{3}{4},\\, a > \\frac{3}{2}$ である。"
            )
        },
        {
            "localKey": "math-q-III_1",
            "sectionId": "III_1",
            "sectionTitle": "第III問（前半）：素因数分解と最大公約数・最小公倍数による自然数の構造決定",
            "points": [
                "自然数 2520 の素因数分解",
                "2数ずつの最大公約数条件から各数の因数倍数条件の導出",
                "互いに素の条件に基づくパラメータ表示"
            ],
            "officialAnswers": {
                "ABCD": "3327",
                "EF": "72",
                "G": "5",
                "H": "7",
                "IJ": "90",
                "K": "7",
                "LMN": "120",
                "O": "7"
            },
            "detailedSolution": (
                "### 【第III問 前半】詳細解答と解説\n\n"
                "3つの自然数 $a, b, c$ の最小公倍数は 2520 であり、次の条件を満たす：\n"
                "- (i) $\\gcd(a, b) = 18 = 2 \\times 3^2$\n"
                "- (ii) $\\gcd(b, c) = 30 = 2 \\times 3 \\times 5$\n"
                "- (iii) $\\gcd(c, a) = 24 = 2^3 \\times 3$\n\n"
                "#### 1. 2520 の素因数分解\n"
                "$$2520 = 2^3 \\times 3^2 \\times 5 \\times 7$$\n"
                "問題文の形式 $2^A \\cdot B^C \\cdot 5 \\cdot D$ に照らすと：\n"
                "$$2^3 \\cdot 3^2 \\cdot 5 \\cdot 7$$\n"
                "よって、$\\mathbf{A = 3},\\, \\mathbf{B = 3},\\, \\mathbf{C = 2},\\, \\mathbf{D = 7}$（解答番号 $\\mathbf{ABCD = 3327}$）である。\n\n"
                "#### 2. $a$ の因数構造の決定\n"
                "条件 (i) より $a$ は 18 の倍数、条件 (iii) より $a$ は 24 の倍数である。\n"
                "したがって、$a$ は $\\operatorname{lcm}(18, 24) = 72 = 2^3 \\times 3^2$ の倍数である。\n"
                "よって、$\\mathbf{EF = 72}$ である。\n\n"
                "一方、$\\gcd(b, c) = 30$ は素因数 5 を含むが、$\\gcd(a, b) = 18$ および $\\gcd(c, a) = 24$ はともに 5 を含まない。\n"
                "よって、$a$ は 5 を素因数にもたず、$a$ と 5 は互いに素である。したがって $\\mathbf{G = 5}$。\n"
                "2520 の残る素因数は 7 であり、$a$ は 7 を因数にもつかもたないかのいずれかである：\n"
                "$$a = 72m \\quad (m = 1 \\text{ または } m = 7)$$\n"
                "よって、$\\mathbf{H = 7}$ である。\n\n"
                "#### 3. $b$ および $c$ の因数構造の決定\n"
                "1. **$b$ について**：\n"
                "   条件 (i) より $b$ は 18 の倍数、条件 (ii) より $b$ は 30 の倍数である。\n"
                "   したがって、$b$ は $\\operatorname{lcm}(18, 30) = 90 = 2 \\times 3^2 \\times 5$ の倍数である。\n"
                "   よって、$\\mathbf{IJ = 90}$ である。\n"
                "   $b$ の素因数 2 の指数は $\\gcd(a, b)=18$ より 1 で確定しており、$b$ がとりうる残りの素因数は 7 のみである：\n"
                "   $$b = 90n \\quad (n = 1 \\text{ または } n = 7)$$\n"
                "   よって、$\\mathbf{K = 7}$ である。\n\n"
                "2. **$c$ について**：\n"
                "   条件 (ii) より $c$ は 30 の倍数、条件 (iii) より $c$ は 24 の倍数である。\n"
                "   したがって、$c$ は $\\operatorname{lcm}(30, 24) = 120 = 2^3 \\times 3 \\times 5$ の倍数である。\n"
                "   よって、$\\mathbf{LMN = 120}$ である。\n"
                "   同様に $c$ がとりうる残りの素因数は 7 のみである：\n"
                "   $$c = 120\\ell \\quad (\\ell = 1 \\text{ または } \\ell = 7)$$\n"
                "   よって、$\\mathbf{O = 7}$ である。"
            )
        },
        {
            "localKey": "math-q-III_2",
            "sectionId": "III_2",
            "sectionTitle": "第III問（後半）：組の総数の決定と大小関係を満たす自然数組の特定",
            "points": [
                "最小公倍数の素因数 7 の分配と組の総数",
                "大小関係 $a < b < c$ に基づく解の組の一意決定"
            ],
            "officialAnswers": {
                "P": "3",
                "QR": "72",
                "ST": "90",
                "UVW": "840"
            },
            "detailedSolution": (
                "### 【第III問 後半】詳細解答と解説\n\n"
                "#### 1. 条件を満たす組 $(a, b, c)$ の総数\n"
                "前半で得られた表現は：\n"
                "$$a = 72m,\\quad b = 90n,\\quad c = 120\\ell \\quad (m, n, \\ell \\in \\{1, 7\\})$$\n"
                "3数の最小公倍数が 2520 であるためには、素因数 7 が $a, b, c$ の少なくとも1つに含まれなければならない。\n"
                "一方で、条件 (i) $\\gcd(a, b) = 18$、(ii) $\\gcd(b, c) = 30$、(iii) $\\gcd(c, a) = 24$ はいずれも 7 で割り切れない。\n"
                "したがって、2数以上が同時に 7 を因数にもつことはできない。\n"
                "ゆえに、$m, n, \\ell$ のうち**ちょうど1つだけが 7 で、残り2つは 1** でなければならない。\n"
                "この組み合わせは：\n"
                "$$(m, n, \\ell) \\in \\{(7, 1, 1), (1, 7, 1), (1, 1, 7)\\}$$\n"
                "の全部で **3組** である。\n"
                "よって、$\\mathbf{P = 3}$ である。\n\n"
                "#### 2. 大小関係 $a < b < c$ を満たす組の決定\n"
                "各場合における $(a, b, c)$ の値を計算する：\n"
                "1. $(m, n, \\ell) = (7, 1, 1)$ のとき：\n"
                "   $$a = 72 \\times 7 = 504,\\quad b = 90,\\quad c = 120$$\n"
                "   $a > b$ となり不適。\n"
                "2. $(m, n, \\ell) = (1, 7, 1)$ のとき：\n"
                "   $$a = 72,\\quad b = 90 \\times 7 = 630,\\quad c = 120$$\n"
                "   $b > c$ となり不適。\n"
                "3. $(m, n, \\ell) = (1, 1, 7)$ のとき：\n"
                "   $$a = 72 \\times 1 = 72$$\n"
                "   $$b = 90 \\times 1 = 90$$\n"
                "   $$c = 120 \\times 7 = 840$$\n"
                "   このとき $72 < 90 < 840$ であり、$a < b < c$ を満たす。\n\n"
                "したがって、求める組は：\n"
                "$$(a, b, c) = (72, 90, 840)$$\n"
                "よって、$\\mathbf{QR = 72},\\, \\mathbf{ST = 90},\\, \\mathbf{UVW = 840}$ である。"
            )
        },
        {
            "localKey": "math-q-IV_1",
            "sectionId": "IV_1",
            "sectionTitle": "第IV問（前半）：三角形の面積・余弦定理と外接円の半径",
            "points": [
                "三角形の面積公式 $S = \\frac{1}{2}ab\\sin C$",
                "余弦定理による対辺長の算出",
                "正弦定理による外接円の半径の導出"
            ],
            "officialAnswers": {
                "A": "1",
                "BC": "10",
                "D": "5"
            },
            "detailedSolution": (
                "### 【第IV問 前半】詳細解答と解説\n\n"
                "$\\triangle \\text{ABC}$ において、$\\text{AB} = 2,\\, \\text{AC} = \\sqrt{2},\\, \\angle \\text{BAC} = 135^\\circ$ である。\n\n"
                "#### 1. 三角形 ABC の面積\n"
                "三角形の面積公式より：\n"
                "$$S = \\frac{1}{2} \\times \\text{AB} \\times \\text{AC} \\times \\sin 135^\\circ = \\frac{1}{2} \\times 2 \\times \\sqrt{2} \\times \\frac{\\sqrt{2}}{2} = 1$$\n"
                "よって、三角形 ABC の面積は $\\mathbf{A = 1}$ である。\n\n"
                "#### 2. 辺 BC の長さと外接円の半径\n"
                "余弦定理より：\n"
                "$$\\text{BC}^2 = \\text{AB}^2 + \\text{AC}^2 - 2 \\times \\text{AB} \\times \\text{AC} \\times \\cos 135^\\circ$$\n"
                "$$= 2^2 + (\\sqrt{2})^2 - 2 \\times 2 \\times \\sqrt{2} \\times \\left(-\\frac{\\sqrt{2}}{2}\\right)$$\n"
                "$$= 4 + 2 + 4 = 10$$\n"
                "したがって、$\\text{BC} = \\sqrt{10}$ である。\n"
                "よって、$\\mathbf{BC = 10}$ である。\n\n"
                "外接円の半径を $R$ とすると、正弦定理より：\n"
                "$$\\frac{\\text{BC}}{\\sin 135^\\circ} = 2R \\implies 2R = \\frac{\\sqrt{10}}{\\frac{\\sqrt{2}}{2}} = 2\\sqrt{5} \\implies R = \\sqrt{5}$$\n"
                "よって、外接円の半径は $\\sqrt{D}$ より $\\mathbf{D = 5}$ である。"
            )
        },
        {
            "localKey": "math-q-IV_2",
            "sectionId": "IV_2",
            "sectionTitle": "第IV問（後半）：角の3等分線・三角比と分割された各三角形の面積",
            "points": [
                "正弦定理による $\\sin\\theta, \\tan\\theta$ の導出",
                "直角三角形における線分比の決定",
                "角の二等分線定理と高さ共通の三角形の面積比"
            ],
            "officialAnswers": {
                "E": "2",
                "FGHI": "1010",
                "JK": "13",
                "LM": "23",
                "NO": "13",
                "PQ": "23",
                "RS": "12",
                "TU": "16",
                "VW": "13"
            },
            "detailedSolution": (
                "### 【第IV問 後半】詳細解答と解説\n\n"
                "#### 1. $\\angle ABC = \\theta$ の三角比と線分 AE の長さ\n"
                "$\\angle \\text{BAC} = 135^\\circ$ の3等分線を引くと：\n"
                "$$\\angle \\text{BAD} = \\angle \\text{DAE} = \\angle \\text{EAC} = 45^\\circ$$\n"
                "したがって：\n"
                "$$\\angle \\text{BAE} = \\angle \\text{BAD} + \\angle \\text{DAE} = 45^\\circ + 45^\\circ = 90^\\circ$$\n"
                "すなわち $\\triangle \\text{ABE}$ は $\\angle \\text{BAE} = 90^\\circ$ の直角三角形である。\n\n"
                "$\\triangle \\text{ABC}$ において正弦定理を適用すると：\n"
                "$$\\frac{\\text{AC}}{\\sin\\theta} = 2R = 2\\sqrt{5} \\implies \\sin\\theta = \\frac{\\sqrt{2}}{2\\sqrt{5}} = \\frac{1}{\\sqrt{10}} = \\frac{\\sqrt{10}}{10}$$\n"
                "よって、$\\mathbf{FG = 10},\\, \\mathbf{HI = 10}$（解答番号 $\\mathbf{FGHI = 1010}$）である。\n\n"
                "$\\theta$ は鋭角であるから：\n"
                "$$\\cos\\theta = \\sqrt{1 - \\sin^2\\theta} = \\sqrt{1 - \\frac{1}{10}} = \\frac{3}{\\sqrt{10}}$$\n"
                "したがって：\n"
                "$$\\tan\\theta = \\frac{\\sin\\theta}{\\cos\\theta} = \\frac{1/\\sqrt{10}}{3/\\sqrt{10}} = \\frac{1}{3}$$\n"
                "よって、$\\mathbf{JK = 13}$（$\\frac{1}{3}$）である。\n\n"
                "直角三角形 ABE において、$\\text{AE} = \\text{AB} \\tan\\theta = 2 \\tan\\theta$ であるから（$\\mathbf{E = 2}$）：\n"
                "$$\\text{AE} = 2 \\times \\frac{1}{3} = \\frac{2}{3}$$\n"
                "よって、$\\mathbf{LM = 23}$（$\\frac{2}{3}$）である。\n\n"
                "#### 2. 各三角形の面積比と面積の決定\n"
                "直角三角形 ABE の面積は：\n"
                "$$\\triangle \\text{ABE} = \\frac{1}{2} \\times \\text{AB} \\times \\text{AE} = \\frac{1}{2} \\times 2 \\times \\frac{2}{3} = \\frac{2}{3}$$\n"
                "よって、$\\mathbf{PQ = 23}$（$\\frac{2}{3}$）である。\n\n"
                "線分 AD は $\\angle \\text{BAE} = 90^\\circ$ の二等分線（$\\angle \\text{BAD} = \\angle \\text{DAE} = 45^\\circ$）であるから、角の二等分線定理より：\n"
                "$$\\text{BD} : \\text{DE} = \\text{AB} : \\text{AE} = 2 : \\frac{2}{3} = 3 : 1$$\n"
                "$\\triangle \\text{ABD}$ と $\\triangle \\text{ADE}$ は頂点 A を共有し底辺が直線 BE 上にあるため、面積比は底辺の比に等しい：\n"
                "$$\\frac{\\triangle \\text{ADE}}{\\triangle \\text{ABD}} = \\frac{\\text{DE}}{\\text{BD}} = \\frac{1}{3}$$\n"
                "よって、$\\mathbf{NO = 13}$（$\\frac{1}{3}$）である。\n\n"
                "したがって：\n"
                "$$\\triangle \\text{ABD} = \\frac{3}{3 + 1} \\triangle \\text{ABE} = \\frac{3}{4} \\times \\frac{2}{3} = \\frac{1}{2}$$\n"
                "よって、$\\mathbf{RS = 12}$（$\\frac{1}{2}$）である。\n\n"
                "$$\\triangle \\text{ADE} = \\frac{1}{3 + 1} \\triangle \\text{ABE} = \\frac{1}{4} \\times \\frac{2}{3} = \\frac{1}{6}$$\n"
                "よって、$\\mathbf{TU = 16}$（$\\frac{1}{6}$）である。\n\n"
                "最後に、全体の面積 $\\triangle \\text{ABC} = 1$ より：\n"
                "$$\\triangle \\text{AEC} = \\triangle \\text{ABC} - \\triangle \\text{ABE} = 1 - \\frac{2}{3} = \\frac{1}{3}$$\n"
                "よって、$\\mathbf{VW = 13}$（$\\frac{1}{3}$）である。"
            )
        }
    ]
}

def main():
    out_json = Path("work/2021-2-math-c1/explanations.json")
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(explanations, ensure_ascii=False, indent=2), encoding="utf-8")

    md_content = f"# {explanations['session']} EJU 数学（コース1）詳細解答・解説\n\n"
    for s in explanations["sections"]:
        md_content += f"\n---\n\n## {s['sectionTitle']}\n\n"
        md_content += f"**【考査考点】**：{', '.join(s['points'])}\n\n"
        md_content += s["detailedSolution"] + "\n"

    out_md = Path("docs/explanations/2021-2-math-c1-solutions.md")
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(md_content, encoding="utf-8")

    print(f"Generated {out_md} and {out_json} successfully with {len(explanations['sections'])} sections.")

if __name__ == "__main__":
    main()
