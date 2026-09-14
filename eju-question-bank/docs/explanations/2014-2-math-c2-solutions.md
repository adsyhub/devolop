# 2014-2 EJU 数学 コース2 詳解・完全解説

> 本ドキュメントは 2014年度第2回 EJU（日本留学試験）数学コース2に対する公式正解準拠の完全詳解である。

---

## 数学 コース2 第I問 [1]：2次関数の頂点・最小値と連立方程式の重解条件

**問題コード**: `math-q-I_1` | **配点参照**: `I:1` | **正解**: `A = 3, BC = 45, DEFG = 4410, H = 2, IJ = -4, K = 3`

### 出題のポイント
- 平方完成による2次関数の最小値の決定
- 2つの放物線の交点方程式と接合条件（判別式 $D=0$）
- 正の実数条件 $a>0$ に基づく係数と接点 $x$ の一意決定

### 詳細解説
**【題目大意】**
$a, b$ は実数であり、$a > 0$ とする。2つの2次関数
$$f(x) = 2x^2 - 4x + 5, \quad g(x) = x^2 + ax + b$$
を考える。$g(x)$ が次の2つの条件を満たすとき、$a, b$ の値を求める。
(i) $g(x)$ の最小値は $f(x)$ の最小値より $8$ だけ小さい
(ii) $f(x) = g(x)$ を満たす $x$ がただ1つ存在する

**【公式正解】**
$\text{A} = 3$
$\text{BC} = 45$ （$b = \frac{a^2}{4} - 5$）
$\text{DEFG} = 4410$ （$x^2 - (a + 4)x - \frac{a^2}{4} + 10 = 0$）
$\text{H} = 2$
$\text{IJ} = -4$
$\text{K} = 3$

**【詳細推導・解答プロセス】**
**(1) $f(x)$ と $g(x)$ の最小値と条件 (i)**
$f(x)$ を平方完成すると：
$$f(x) = 2(x^2 - 2x) + 5 = 2(x - 1)^2 + 3$$
したがって、$f(x)$ の最小値は **3** である（$\text{A} = 3$）。

$g(x)$ を平方完成すると：
$$g(x) = \left(x + \frac{a}{2}\right)^2 + b - \frac{a^2}{4}$$
したがって、$g(x)$ の最小値は $b - \frac{a^2}{4}$ である。
条件 (i)「$g(x)$ の最小値は $f(x)$ の最小値より8だけ小さい」より：
$$b - \frac{a^2}{4} = 3 - 8 = -5 \implies b = \frac{a^2}{4} - 5$$
これより、$b = \frac{a^2}{\text{B}} - \text{C}$ の空欄は $\text{BC} = 45$ である。

**(2) 交点方程式と条件 (ii)**
$f(x) = g(x)$ を満たす $x$ を求める方程式は：
$$2x^2 - 4x + 5 = x^2 + ax + b \iff x^2 - (a + 4)x + (5 - b) = 0$$
ここに $b = \frac{a^2}{4} - 5$ を代入すると、定数項は：
$$5 - b = 5 - \left(\frac{a^2}{4} - 5\right) = -\frac{a^2}{4} + 10$$
よって、方程式は：
$$x^2 - (a + 4)x - \frac{a^2}{4} + 10 = 0$$
となり、$\text{D} = 4$、$\text{E} = 4$、$\text{FG} = 10$（合わせて $\text{DEFG} = 4410$）を得る。

条件 (ii)「解がただ1つ存在する」より、この2次方程式の判別式 $D_0$ は $0$ でなければならない：
$$D_0 = [-(a + 4)]^2 - 4 \cdot 1 \cdot \left(-\frac{a^2}{4} + 10\right) = 0$$
$$(a^2 + 8a + 16) + a^2 - 40 = 0$$
$$2a^2 + 8a - 24 = 0 \iff a^2 + 4a - 12 = 0$$
$$(a + 6)(a - 2) = 0$$
$a > 0$ であるから：
$$a = 2 \quad (\text{H} = 2)$$
このとき、$b$ の値は：
$$b = \frac{2^2}{4} - 5 = 1 - 5 = -4 \quad (\text{IJ} = -4)$$
また、$a = 2$ のときの方程式は：
$$x^2 - 6x + 9 = 0 \iff (x - 3)^2 = 0$$
より、解は重解 $x = 3$（$\text{K} = 3$）である。

**【考査考点】**
- 2次関数の標準形への変形（平方完成）と頂点の座標・最小値の決定。
- 2つの放物線の共有点と2次方程式の判別式（重解条件 $D=0$）。

---

## 数学 コース2 第I問 [2]：集合と命題（必要十分条件）およびド・モルガンの法則による要素数計算

**問題コード**: `math-q-I_2` | **配点参照**: `I:2` | **正解**: `L = 2, M = 1, N = 3, O = 0, PQ = 92, RS = 67`

### 出題のポイント
- 倍数集合における包含関係と命題の必要条件・十分条件の判定
- ド・モルガンの法則：$\overline{A} \cup \overline{B} = \overline{A \cap B}$ および $\overline{A} \cap \overline{B} = \overline{A \cup B}$
- 包含と排除の原理による補集合の要素数 $|\overline{A} \cap C|$ 等の計算

### 詳細解説
**【題目大意】**
自然数の部分集合 $A = \{4m \mid m \in \mathbb{N}\}$（4の倍数集合）、$B = \{6m \mid m \in \mathbb{N}\}$（6の倍数集合）を考える。
(1) 自然数 $n$ に対する各命題の必要・十分条件を判定する。
(2) $C = \{1, 2, \dots, 100\}$ に対し、$(\overline{A} \cup \overline{B}) \cap C$ および $\overline{A} \cap \overline{B} \cap C$ の要素の個数を求める。

**【公式正解】**
$\text{L} = 2$ （十分条件であるが，必要条件ではない）
$\text{M} = 1$ （必要条件であるが，十分条件ではない）
$\text{N} = 3$ （必要条件でも十分条件でもない）
$\text{O} = 0$ （必要十分条件である）
$\text{PQ} = 92$
$\text{RS} = 67$

**【詳細推導・解答プロセス】**
**(1) 必要・十分条件の判定**
- (i) $n \in A$（$n$ は4の倍数） $\implies$ $n$ は2で割り切れる（真）。一方、$n$ が2で割り切れる（例：$n=2$） $\implies$ $n \in A$（偽）。よって、十分条件であるが，必要条件ではない（$\text{L} = 2$）。
- (ii) $n \in B$（$n$ は6の倍数） $\Longleftarrow$ $n$ が24で割り切れる（真）。一方、$n \in B$（例：$n=6$） $\implies$ $n$ が24で割り切れる（偽）。よって、必要条件であるが，十分条件ではない（$\text{M} = 1$）。
- (iii) $n \in A \cup B$（$n$ は4の倍数または6の倍数）。$n=4 \in A \cup B$ は3で割り切れない（十分条件ではない）。また、$n=3$ は3で割り切れるが $A \cup B$ に属さない（必要条件ではない）。よって、必要条件でも十分条件でもない（$\text{N} = 3$）。
- (iv) $n \in A \cap B$ は「$n$ は4の倍数かつ6の倍数」であり、$\text{lcm}(4, 6) = 12$ より「$n$ は12の倍数」と同値である。よって、必要十分条件である（$\text{O} = 0$）。

**(2) 集合の要素の個数計算**
$C = \{1, 2, \dots, 100\}$ において、要素の総数は $|C| = 100$ である。
- $|A \cap C| = \lfloor 100 / 4 \rfloor = 25$
- $|B \cap C| = \lfloor 100 / 6 \rfloor = 16$
- $|A \cap B \cap C| = \lfloor 100 / 12 \rfloor = 8$

ド・モルガンの法則より：
$$\overline{A} \cup \overline{B} = \overline{A \cap B}$$
したがって：
$$|(\overline{A} \cup \overline{B}) \cap C| = |C| - |(A \cap B) \cap C| = 100 - 8 = 92 \quad (\text{PQ} = 92)$$

また：
$$\overline{A} \cap \overline{B} = \overline{A \cup B}$$
包除原理より：
$$|(A \cup B) \cap C| = |A \cap C| + |B \cap C| - |A \cap B \cap C| = 25 + 16 - 8 = 33$$
したがって：
$$|(\overline{A} \cap \overline{B}) \cap C| = |C| - |(A \cup B) \cap C| = 100 - 33 = 67 \quad (\text{RS} = 67)$$

**【考査考点】**
- 命題と論理（必要条件・十分条件・必要十分条件）の正確な識別。
- 集合の演算（和集合・共通部分・補集合）とド・モルガンの法則。
- 有限集合の要素の個数の計算（ガウス記号による倍数カウントと包除原理）。

---

## 数学 コース2 第II問 [1]：円に内接する三角形のベクトル表現・外分点と内積の関係式

**問題コード**: `math-q-II_1` | **配点参照**: `II:1` | **正解**: `ABC = 212, DE = 32, FGHI = 9454`

### 出題のポイント
- 単位円上の点に関する位置ベクトルの外分公式（$\overrightarrow{OD}$ の導出）
- 辺の長さの比とベクトルの大きさ（ノルム）の比の関係
- ベクトルの大きさの2乗展開による内積 $\overrightarrow{a} \cdot \overrightarrow{b}$ と $\overrightarrow{a} \cdot \overrightarrow{c}$ の線形関係の導出

### 詳細解説
**【題目大意】**
点 $O$ を中心とする半径1の円 $S$ 上に三角形 $ABC$ があり、$AB : AC = 3 : 2$ を満たす。
辺 $BC$ の延長線上に点 $D$ をとり、$BC : CD = 2 : k$ とする。
$\overrightarrow{OA} = \overrightarrow{a}, \overrightarrow{OB} = \overrightarrow{b}, \overrightarrow{OC} = \overrightarrow{c}$ とおく。
(1) $\overrightarrow{OD}$ を $\overrightarrow{b}, \overrightarrow{c}, k$ で表す。
(2) 内積 $\overrightarrow{a} \cdot \overrightarrow{b}$ を $\overrightarrow{a} \cdot \overrightarrow{c}$ で表す。

**【公式正解】**
$\text{ABC} = 212$ （$\overrightarrow{OD} = (\frac{k}{2} + 1)\overrightarrow{c} - \frac{k}{2}\overrightarrow{b}$）
$\text{DE} = 32$ （$|\overrightarrow{b} - \overrightarrow{a}| = \frac{3}{2}|\overrightarrow{c} - \overrightarrow{a}|$）
$\text{FGHI} = 9454$ （$\overrightarrow{a} \cdot \overrightarrow{b} = \frac{9}{4}\overrightarrow{a} \cdot \overrightarrow{c} - \frac{5}{4}$）

**【詳細推導・解答プロセス】**
単位円 $S$ 上の頂点であるから：
$$|\overrightarrow{a}| = |\overrightarrow{b}| = |\overrightarrow{c}| = 1$$

**(1) $\overrightarrow{OD}$ の導出**
点 $D$ は辺 $BC$ の延長上にあり、$BC : CD = 2 : k$ であるから：
$$\overrightarrow{CD} = \frac{k}{2} \overrightarrow{BC} = \frac{k}{2}(\overrightarrow{c} - \overrightarrow{b})$$
したがって、位置ベクトル $\overrightarrow{OD}$ は：
$$\overrightarrow{OD} = \overrightarrow{OC} + \overrightarrow{CD} = \overrightarrow{c} + \frac{k}{2}(\overrightarrow{c} - \overrightarrow{b}) = \left(\frac{k}{2} + 1\right)\overrightarrow{c} - \frac{k}{2}\overrightarrow{b}$$
与式 $\overrightarrow{OD} = \left(\frac{k}{\text{A}} + \text{B}\right)\overrightarrow{c} - \frac{k}{\text{C}}\overrightarrow{b}$ と比較して：
$$\text{A} = 2, \quad \text{B} = 1, \quad \text{C} = 2 \implies \text{ABC} = 212$$

**(2) 内積の関係式の導出**
$AB = |\overrightarrow{b} - \overrightarrow{a}|$、$AC = |\overrightarrow{c} - \overrightarrow{a}|$ である。
$AB : AC = 3 : 2$ より：
$$|\overrightarrow{b} - \overrightarrow{a}| = \frac{3}{2}|\overrightarrow{c} - \overrightarrow{a}|$$
したがって、$\text{D} = 3, \text{E} = 2$ より $\text{DE} = 32$ である。

両辺を2乗すると：
$$|\overrightarrow{b} - \overrightarrow{a}|^2 = \frac{9}{4}|\overrightarrow{c} - \overrightarrow{a}|^2$$
左辺を展開すると：
$$|\overrightarrow{b}|^2 - 2\overrightarrow{a} \cdot \overrightarrow{b} + |\overrightarrow{a}|^2 = 1 - 2\overrightarrow{a} \cdot \overrightarrow{b} + 1 = 2 - 2\overrightarrow{a} \cdot \overrightarrow{b}$$
右辺を展開すると：
$$\frac{9}{4}(|\overrightarrow{c}|^2 - 2\overrightarrow{a} \cdot \overrightarrow{c} + |\overrightarrow{a}|^2) = \frac{9}{4}(2 - 2\overrightarrow{a} \cdot \overrightarrow{c}) = \frac{9}{2} - \frac{9}{2}\overrightarrow{a} \cdot \overrightarrow{c}$$
等式で結んで移項すると：
$$2 - 2\overrightarrow{a} \cdot \overrightarrow{b} = \frac{9}{2} - \frac{9}{2}\overrightarrow{a} \cdot \overrightarrow{c}$$
$$-2\overrightarrow{a} \cdot \overrightarrow{b} = \frac{5}{2} - \frac{9}{2}\overrightarrow{a} \cdot \overrightarrow{c}$$
$$\overrightarrow{a} \cdot \overrightarrow{b} = \frac{9}{4}\overrightarrow{a} \cdot \overrightarrow{c} - \frac{5}{4}$$
与式 $\overrightarrow{a} \cdot \overrightarrow{b} = \frac{\text{F}}{\text{G}}\overrightarrow{a} \cdot \overrightarrow{c} - \frac{\text{H}}{\text{I}}$ と比較して：
$$\text{F} = 9, \quad \text{G} = 4, \quad \text{H} = 5, \quad \text{I} = 4 \implies \text{FGHI} = 9454$$

**【考査考点】**
- 線分の内分・外分のベクトル方程式。
- ベクトルのノルムの2乗計算と単位ベクトルの性質（$|\overrightarrow{a}|^2=1$）。
- 内積の線形変換と代数操作。

---

## 数学 コース2 第II問 [2]：円の接線条件と直交条件（内積＝0）による比パラメータ $k$ の決定

**問題コード**: `math-q-II_2` | **配点参照**: `II:2` | **正解**: `JK = 85`

### 出題のポイント
- 円の接線の幾何学的性質：半径 $\overrightarrow{OA}$ と接線方向ベクトル $\overrightarrow{AD}$ の直交性（$\overrightarrow{AD} \cdot \overrightarrow{a} = 0$）
- 内積の等式代入による $\overrightarrow{a} \cdot \overrightarrow{c}$ の因数分解と未知数 $k$ の決定

### 詳細解説
**【題目大意】**
点 $A$ における円 $S$ の接線が点 $D$ を通るとき、$k$ の値を求める。

**【公式正解】**
$\text{JK} = 85$ （$k = \frac{8}{5}$）

**【詳細推導・解答プロセス】**
点 $A$ における円 $S$ の接線は、半径 $OA$（ベクトル $\overrightarrow{a}$）に垂直である。
接線が点 $D$ を通るため、ベクトル $\overrightarrow{AD}$ は $\overrightarrow{a}$ と直交する：
$$\overrightarrow{AD} \perp \overrightarrow{a} \iff \overrightarrow{AD} \cdot \overrightarrow{a} = 0$$
$\overrightarrow{AD} = \overrightarrow{OD} - \overrightarrow{a}$ であるから：
$$(\overrightarrow{OD} - \overrightarrow{a}) \cdot \overrightarrow{a} = 0 \iff \overrightarrow{OD} \cdot \overrightarrow{a} = |\overrightarrow{a}|^2 = 1$$

前問 (1) で求めた $\overrightarrow{OD} = \left(\frac{k}{2} + 1\right)\overrightarrow{c} - \frac{k}{2}\overrightarrow{b}$ を代入すると：
$$\left(\frac{k}{2} + 1\right)(\overrightarrow{a} \cdot \overrightarrow{c}) - \frac{k}{2}(\overrightarrow{a} \cdot \overrightarrow{b}) = 1$$

ここに前問 (2) で求めた関係式 $\overrightarrow{a} \cdot \overrightarrow{b} = \frac{9}{4}\overrightarrow{a} \cdot \overrightarrow{c} - \frac{5}{4}$ を代入する：
$$\left(\frac{k}{2} + 1\right)(\overrightarrow{a} \cdot \overrightarrow{c}) - \frac{k}{2}\left(\frac{9}{4}\overrightarrow{a} \cdot \overrightarrow{c} - \frac{5}{4}\right) = 1$$
$\overrightarrow{a} \cdot \overrightarrow{c}$ の係数をまとめると：
$$\left[\left(\frac{k}{2} + 1\right) - \frac{9k}{8}\right](\overrightarrow{a} \cdot \overrightarrow{c}) + \frac{5k}{8} = 1$$
$$\left(1 - \frac{5k}{8}\right)(\overrightarrow{a} \cdot \overrightarrow{c}) + \frac{5k}{8} - 1 = 0$$
$$\left(1 - \frac{5k}{8}\right)(\overrightarrow{a} \cdot \overrightarrow{c} - 1) = 0$$

ここで、$A, C$ は円周上の異なる点であるため、$\overrightarrow{a} \ne \overrightarrow{c}$ であり、単位ベクトル同士の内積は $\overrightarrow{a} \cdot \overrightarrow{c} < 1$（$\overrightarrow{a} \cdot \overrightarrow{c} \ne 1$）である。
したがって：
$$1 - \frac{5k}{8} = 0 \implies \frac{5k}{8} = 1 \implies k = \frac{8}{5}$$
与式 $k = \frac{\text{J}}{\text{K}}$ より、$\text{JK} = 85$ である。

**【考査考点】**
- 円の接線と法線ベクトルの直交条件（$\overrightarrow{AD} \cdot \overrightarrow{OA} = 0$）。
- ベクトルの内積等式の連立と因数分解による解法。

---

## 数学 コース2 第III問 (1)：指数方程式の2次方程式への帰着と解と係数の関係（対数の底の変換）

**問題コード**: `math-q-III_1` | **配点参照**: `III:1` | **正解**: `AB = 16, CDEF = 1213`

### 出題のポイント
- 置換 $t = e^x$ による超越方程式の代数方程式化
- 解と係数の関係：積 $b = t_1 t_2$ および和 $a = t_1 + t_2$
- 対数の底の変換公式（$\log_{q^2} p = \frac{1}{2}\log_q p$、$\log_{p^3} q = \frac{1}{3}\log_p q$）の適用

### 詳細解説
**【題目大意】**
$p > 1, q > 1$ とする。方程式 $e^{2x} - a e^x + b = 0$ において $t = e^x$ とおくとき、$t$ に関する2次方程式 $t^2 - at + b = 0$ が2解 $\log_{q^2} p$ と $\log_{p^3} q$ をもつとする。
(1) 定数 $b$ の値、および $a$ の対数表現を求める。

**【公式正解】**
$\text{AB} = 16$ （$b = \frac{1}{6}$）
$\text{CDEF} = 1213$ （$a = \frac{1}{2}\log_q p + \frac{1}{3}\log_p q$）

**【詳細推導・解答プロセス】**
2次方程式 $t^2 - at + b = 0$ の2つの解を $t_1, t_2$ とおく：
$$t_1 = \log_{q^2} p, \quad t_2 = \log_{p^3} q$$

底の変換公式より：
$$t_1 = \log_{q^2} p = \frac{\log_q p}{\log_q (q^2)} = \frac{1}{2}\log_q p$$
$$t_2 = \log_{p^3} q = \frac{\log_p q}{\log_p (p^3)} = \frac{1}{3}\log_p q = \frac{1}{3} \cdot \frac{1}{\log_q p}$$

解と係数の関係より、2解の積 $b = t_1 t_2$ は：
$$b = \left(\frac{1}{2}\log_q p\right) \left(\frac{1}{3} \cdot \frac{1}{\log_q p}\right) = \frac{1}{2} \times \frac{1}{3} = \frac{1}{6}$$
したがって、$b = \frac{\text{A}}{\text{B}}$ より、$\text{AB} = 16$ である。

また、2解の和 $a = t_1 + t_2$ は：
$$a = \frac{1}{2}\log_q p + \frac{1}{3}\log_p q$$
したがって、$a = \frac{\text{C}}{\text{D}}\log_q p + \frac{\text{E}}{\text{F}}\log_p q$ より、$\text{CDEF} = 1213$ である。

**【考査考点】**
- 指数・対数方程式の置換法と2次方程式の解と係数の関係。
- 対数の底の変換公式 $\log_{a^n} b = \frac{1}{n}\log_a b$ および逆数関係 $\log_a b = \frac{1}{\log_b a}$。

---

## 数学 コース2 第III問 (2)：相加・相乗平均の不等式による最小値の決定と指数方程式の解

**問題コード**: `math-q-III_2` | **配点参照**: `III:2` | **正解**: `G = 0, HI = 63, JK = 62, LMN = 126`

### 出題のポイント
- 底と真数が1より大のときの対数の正値条件（$\log_p q > 0$）
- 相加・相乗平均の不等式 $a + b \ge 2\sqrt{ab}$ の適用と等号成立条件
- 重解時の $t$ の値から $x$ の自然対数表現（$x = -\frac{1}{2}\log_e 6$）の決定

### 詳細解説
**【題目大意】**
$p > 1, q > 1$ のとき、(1) で求めた $a$ の最小値とそのときの $\log_p q$、およびそのときの方程式 $\textcircled{1}$ の解 $x$ を求める。

**【公式正解】**
$\text{G} = 0$ （$\log_p q > 0$）
$\text{HI} = 63$ （$a$ の最小値は $\frac{\sqrt{6}}{3}$）
$\text{JK} = 62$ （$\log_p q = \frac{\sqrt{6}}{2}$）
$\text{LMN} = 126$ （$x = -\frac{1}{2}\log_e 6$）

**【詳細推導・解答プロセス】**
**(1) $a$ の最小値の導出**
$p > 1, q > 1$ であるから、$\log_p q > 0$ である（$\text{G} = 0$）。
$u = \log_p q > 0$ とおくと、$\log_q p = \frac{1}{u}$ であるから：
$$a = \frac{1}{2u} + \frac{u}{3}$$
$\frac{1}{2u} > 0$ かつ $\frac{u}{3} > 0$ であるから、相加平均・相乗平均の大小関係（AM-GM不等式）を適用できる：
$$a = \frac{1}{2u} + \frac{u}{3} \ge 2\sqrt{\frac{1}{2u} \cdot \frac{u}{3}} = 2\sqrt{\frac{1}{6}} = \frac{2}{\sqrt{6}} = \frac{2\sqrt{6}}{6} = \frac{\sqrt{6}}{3}$$
したがって、$a$ の最小値は $\frac{\sqrt{6}}{3}$ である（$\text{HI} = 63$）。

等号が成立するのは：
$$\frac{1}{2u} = \frac{u}{3} \iff 2u^2 = 3 \iff u^2 = \frac{3}{2}$$
$u > 0$ より：
$$u = \log_p q = \sqrt{\frac{3}{2}} = \frac{\sqrt{6}}{2}$$
したがって、$\log_p q = \frac{\sqrt{\text{J}}}{\text{K}}$ より、$\text{JK} = 62$ である。

**(2) 方程式 $\textcircled{1}$ の解 $x$ の決定**
等号成立時、2解 $t_1, t_2$ は等しくなり、2次方程式は重解をもつ：
$$t = \frac{a}{2} = \frac{\sqrt{6}/3}{2} = \frac{\sqrt{6}}{6} = \frac{1}{\sqrt{6}}$$
$t = e^x$ であるから：
$$e^x = \frac{1}{\sqrt{6}} = 6^{-1/2}$$
両辺の自然対数をとると：
$$x = \log_e (6^{-1/2}) = -\frac{1}{2}\log_e 6$$
与式 $x = -\frac{\text{L}}{\text{M}}\log_e \text{N}$ と比較して：
$$\text{L} = 1, \quad \text{M} = 2, \quad \text{N} = 6 \implies \text{LMN} = 126$$

**【考査考点】**
- 対数の基本的性質（真数・底の範囲と符号）。
- 相加相乗平均の不等式による極値問題の解法と等号成立条件。
- 自然対数による指数方程式の厳密解の導出。

---

## 数学 コース2 第IV問 [1]：3次関数の接線方程式・交点座標と囲まれる図形の面積比

**問題コード**: `math-q-IV_1` | **配点参照**: `IV:1` | **正解**: `ABCD = 3223, E = 2, FGHI = 2744, JKLM = 2744, N = 1`

### 出題のポイント
- 3次関数 $y=ax^3$ の微分と接線方程式の立式
- 接線と曲線の交点（因数定理・組立除法による $x = -2t$ の導出）
- 定積分による面積 $S_1, S_2$ の計算と普遍的な面積比 $\frac{S_1}{S_2} = 1$ の証明

### 詳細解説
**【題目大意】**
$a, t > 0$ とする。曲線 $C: y = ax^3$ 上の点 $P(t, at^3)$ における接線 $l$ が $C$ と再び交わる点を $Q$ とする。
$P$ を通り $x$ 軸に平行な直線 $p$ と、$Q$ を通り $y$ 軸に平行な直線 $q$ の交点を $R$ とする。
曲線 $C$ と直線 $p, q$ で囲まれる面積を $S_1$、$C$ と接線 $l$ で囲まれる面積を $S_2$ とするとき、面積および比 $\frac{S_1}{S_2}$ を求める。

**【公式正解】**
$\text{ABCD} = 3223$ （$y = 3at^2 x - 2at^3$）
$\text{E} = 2$ （点 $Q$ の $x$ 座標は $-2t$）
$\text{FGHI} = 2744$ （$S_1 = \frac{27}{4}at^4$）
$\text{JKLM} = 2744$ （$S_2 = \frac{27}{4}at^4$）
$\text{N} = 1$ （$\frac{S_1}{S_2} = 1$）

**【詳細推導・解答プロセス】**
**(1) 接線 $l$ の方程式と点 $Q$ の座標**
$y = ax^3$ より $y' = 3ax^2$ である。
点 $P(t, at^3)$ における接線の傾きは $3at^2$ であるから、接線 $l$ の方程式は：
$$y - at^3 = 3at^2(x - t) \iff y = 3at^2 x - 2at^3$$
したがって、$y = \text{A}at^\text{B}x - \text{C}at^\text{D}$ より、$\text{ABCD} = 3223$ である。

曲線 $C$ と接線 $l$ の交点の $x$ 座標を求める：
$$ax^3 = 3at^2 x - 2at^3 \iff a(x^3 - 3t^2 x + 2t^3) = 0$$
$x = t$ は接点であるから $(x - t)^2$ で割り切れる：
$$a(x - t)^2(x + 2t) = 0$$
したがって、もう1つの交点 $Q$ の $x$ 座標は $-2t$ である（$\text{E} = 2$）。

**(2) 面積 $S_1$ の計算**
直線 $p$ の方程式は $y = at^3$、直線 $q$ の方程式は $x = -2t$ である。
$-2t \le x \le t$ において、$at^3 \ge ax^3$ であるから、曲線 $C$ と直線 $p, q$ で囲まれる面積 $S_1$ は：
$$S_1 = \int_{-2t}^t (at^3 - ax^3) \, dx = a \left[ t^3 x - \frac{x^4}{4} \right]_{-2t}^t$$
上端 $x = t$ を代入すると：
$$t^4 - \frac{t^4}{4} = \frac{3}{4}t^4$$
下端 $x = -2t$ を代入すると：
$$t^3(-2t) - \frac{(-2t)^4}{4} = -2t^4 - 4t^4 = -6t^4$$
差をとると：
$$S_1 = a \left( \frac{3}{4}t^4 - (-6t^4) \right) = \frac{27}{4}at^4$$
したがって、$S_1 = \frac{\text{FG}}{\text{H}}at^\text{I}$ より、$\text{FGHI} = 2744$ である。

**(3) 面積 $S_2$ および比 $\frac{S_1}{S_2}$**
直角三角形 $PQR$ において：
- 点 $P(t, at^3)$、点 $Q(-2t, -8at^3)$、点 $R(-2t, at^3)$
- 底辺 $PR = t - (-2t) = 3t$
- 高さ $QR = at^3 - (-8at^3) = 9at^3$
三角形 $PQR$ の面積は：
$$\text{Area}(\triangle PQR) = \frac{1}{2} \times 3t \times 9at^3 = \frac{27}{2}at^4$$
図形の包含関係より、$S_2$ は三角形 $PQR$ の面積から $S_1$ を引いたものに等しい：
$$S_2 = \frac{27}{2}at^4 - \frac{27}{4}at^4 = \frac{27}{4}at^4$$
したがって、$S_2 = \frac{\text{JK}}{\text{L}}at^\text{M}$ より、$\text{JKLM} = 2744$ である。

よって、面積比は：
$$\frac{S_1}{S_2} = \frac{\frac{27}{4}at^4}{\frac{27}{4}at^4} = 1 \quad (\text{N} = 1)$$

**【考査考点】**
- 3次関数の微分と接線方程式の決定。
- 接点（重解）を利用した交点 $x$ 座標の素早い因数分解。
- 定積分による図形の面積計算と幾何学的対称性・相似性。

---

## 数学 コース2 第IV問 [2]：極限値の未定係数決定と三角関数の定積分・区分求積法

**問題コード**: `math-q-IV_2` | **配点参照**: `IV:2` | **正解**: `O = 2, PQ = 72, RS = 12, T = 1, UV = 22, WXY = 121, Z = 4`

### 出題のポイント
- $\lim_{x \to 0} \frac{g(x)}{\sin^n x}$ の存在条件とテイラー展開・多項式の次数比較
- 置換積分法による三角関数の定積分 $I_n = \int_0^{\pi/2} \sin^n x \sin 2x \, dx$ の導出
- 区分求積法 $\lim_{n \to \infty} \frac{1}{n} \sum f(k/n) = \int_0^1 f(x) \, dx$ による級数和の極限値計算

### 詳細解説
**【題目大意】**
$f_n(x) = \sin^n x$ とする。
(1) $\lim_{x \to 0} \frac{a - x^2 - (b - x^2)^2}{f_n(x)} = c$ が成り立つとき：
  (i) $a$ と $b$ の関係式、$n=2$ のときの $b$、$n=4$ のときの $b, c$ を求める。
(2) $I_n = \int_0^{\frac{\pi}{2}} f_n(x) \sin 2x \, dx$ を計算し、$\lim_{n \to \infty} (I_{n-1} + I_n + \dots + I_{2n-2})$ の値を区分求積法により求める。

**【公式正解】**
$\text{O} = 2$ （$a = b^2$）
$\text{PQ} = 72$ （$b = \frac{7}{2}$）
$\text{RS} = 12$ （$b = \frac{1}{2}$）
$\text{T} = 1$ （$c = -1$）
$\text{UV} = 22$ （$I_n = \frac{2}{n + 2}$）
$\text{WXY} = 121$ （$\int_0^1 \frac{2}{1 + x} \, dx$）
$\text{Z} = 4$ （$= \log 4$）

**【詳細推導・解答プロセス】**
**(1) 極限値と係数の決定**
分子を展開して $x^2$ の多項式として整理する：
$$g(x) = a - x^2 - (b^2 - 2bx^2 + x^4) = (a - b^2) + (2b - 1)x^2 - x^4$$
分母は $f_n(x) = \sin^n x$ である。$x \to 0$ のとき $\sin x \sim x$ である。

- **(i) $x \to 0$ で極限値が存在するための定数項の条件**：
  分母 $\to 0$ であるから、極限値が収束するためには分子も $x \to 0$ で $0$ に収束しなければならない：
  $$a - b^2 = 0 \implies a = b^2$$
  したがって、$a = b^\text{O}$ より $\text{O} = 2$ である。

- **(ii) $n = 2$ のとき**：
  分子は $(2b - 1)x^2 - x^4$ となるので：
  $$\lim_{x \to 0} \frac{(2b - 1)x^2 - x^4}{\sin^2 x} = \lim_{x \to 0} \left[ (2b - 1) - x^2 \right] \cdot \left(\frac{x}{\sin x}\right)^2 = 2b - 1$$
  これが $c = 6$ に等しいので：
  $$2b - 1 = 6 \implies 2b = 7 \implies b = \frac{7}{2}$$
  したがって、$b = \frac{\text{P}}{\text{Q}}$ より、$\text{PQ} = 72$ である。

- **(iii) $n = 4$ のとき**：
  分母が $x^4$ のオーダーであるため、有限な極限値をもつには $x^2$ の項の係数も $0$ でなければならない：
  $$2b - 1 = 0 \implies b = \frac{1}{2}$$
  したがって、$b = \frac{\text{R}}{\text{S}}$ より、$\text{RS} = 12$ である。
  このとき、分子は $-x^4$ となり、極限値は：
  $$c = \lim_{x \to 0} \frac{-x^4}{\sin^4 x} = -1$$
  したがって、$c = -\text{T}$ より、$\text{T} = 1$ である。

**(2) 定積分 $I_n$ と区分求積法**
倍角の公式 $\sin 2x = 2\sin x \cos x$ を用いると：
$$I_n = \int_0^{\frac{\pi}{2}} \sin^n x (2\sin x \cos x) \, dx = 2\int_0^{\frac{\pi}{2}} \sin^{n+1} x \cos x \, dx$$
$u = \sin x$ とおくと、$du = \cos x \, dx$、$x: 0 \to \frac{\pi}{2} \implies u: 0 \to 1$ であるから：
$$I_n = 2\int_0^1 u^{n+1} \, du = 2 \left[ \frac{u^{n+2}}{n+2} \right]_0^1 = \frac{2}{n+2}$$
したがって、$I_n = \frac{\text{U}}{n + \text{V}}$ より、$\text{UV} = 22$ である。

次に、和の極限を考える：
$$S_n = I_{n-1} + I_n + I_{n+1} + \dots + I_{2n-2}$$
項数は $(2n - 2) - (n - 1) + 1 = n$ 個である。
各項は $I_k = \frac{2}{k+2}$ であり、$k$ が $n-1$ から $2n-2$ まで動くとき、$k+2$ は $n+1$ から $2n$ まで動く。
したがって：
$$S_n = \sum_{j=1}^n \frac{2}{n+j} = \sum_{j=1}^n \frac{2}{n\left(1 + \frac{j}{n}\right)} = \frac{1}{n} \sum_{j=1}^n \frac{2}{1 + \frac{j}{n}}$$
区分求積法の公式 $\lim_{n \to \infty} \frac{1}{n}\sum_{j=1}^n f\left(\frac{j}{n}\right) = \int_0^1 f(x) \, dx$ を適用すると：
$$\lim_{n \to \infty} S_n = \int_0^1 \frac{2}{1 + x} \, dx$$
与式 $\int_0^\text{W} \frac{\text{X}}{\text{Y} + x} \, dx$ と比較して：
$$\text{W} = 1, \quad \text{X} = 2, \quad \text{Y} = 1 \implies \text{WXY} = 121$$

定積分を計算すると：
$$\int_0^1 \frac{2}{1 + x} \, dx = 2 \left[ \log_e(1 + x) \right]_0^1 = 2(\log_e 2 - \log_e 1) = 2\log_e 2 = \log_e (2^2) = \log_e 4$$
したがって、$= \log \text{Z}$ より、$\text{Z} = 4$ である。

**【考査考点】**
- 関数の極限とロピタルの定理・未定係数の決定法。
- 置換積分法による三角関数の冪乗積分の計算。
- 区分求積法による定積分と数列の和の極限の相互変換。

---
