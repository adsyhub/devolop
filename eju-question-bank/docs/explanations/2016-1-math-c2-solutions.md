# 2016年第1回 EJU 数学コース2 解答解説 (Authoritative Solutions)

> 本ドキュメントは公式解答および厳密な数学的推導に基づく完全解答解説です。

## 大問I 問1：2次関数の頂点軌跡・最大値および接線条件による値域
- **Local Key**: `math-q-I_1`
- **Answer Ref**: `MATH_C2:I_1`
- **公式正解**: `{'A': '4', 'B': '2', 'CDEF': '-241', 'G': '1', 'H': '3', 'IJ': '18'}`

**【題目大意】**
2次関数 $y = -\frac{1}{8}x^2 + ax + b$ $\textcircled{1}$ のグラフの頂点を $(p, q)$ とし、(1) 頂点が直線 $x + y = 1$ 上を動くときの $8a + b$ の最大値、および (2) グラフが $x$ 軸に接するときの $a + b$ のとり得る値の範囲を求める。

**【公式正解】**
- $\text{A} = 4, \text{B} = 2$ ($p = 4a, q = 2a^2 + b$)
- $\text{CDEF} = -241$ ($b = -2a^2 - 4a + 1$)
- $\text{G} = 1, \text{H} = 3$ ($a = 1$ で最大値 3)
- $\text{IJ} = 18$ ($a + b \leq \frac{1}{8}$)

**【詳細推導・解答プロセス】**
**(1) 頂点の座標の算出**
関数 $\textcircled{1}$ を平方完成する：
$$y = -\frac{1}{8}(x^2 - 8ax) + b = -\frac{1}{8}(x - 4a)^2 + 2a^2 + b$$
したがって、グラフの頂点の座標 $(p, q)$ は：
$$p = 4a, \quad q = 2a^2 + b$$
よって、$\text{A} = 4, \text{B} = 2$ である。

**(2) 頂点が直線 $x + y = 1$ 上にある条件と最大値**
点 $(p, q)$ が直線 $x + y = 1$ 上にあるので、代入すると：
$$4a + (2a^2 + b) = 1 \implies b = -2a^2 - 4a + 1$$
したがって、$\text{CD} = -2, \text{E} = 4, \text{F} = 1$ (CDEF = -241) である。
このとき、$8a + b$ を $a$ の式として表すと：
$$8a + b = 8a + (-2a^2 - 4a + 1) = -2a^2 + 4a + 1$$
これを平方完成すると：
$$-2(a^2 - 2a) + 1 = -2(a - 1)^2 + 2 + 1 = -2(a - 1)^2 + 3$$
したがって、$a = 1$ のとき最大値 3 をとる。
よって、$\text{G} = 1, \text{H} = 3$ である。

**(3) グラフが $x$ 軸に接する条件**
放物線 $\textcircled{1}$ が $x$ 軸に接するとき、頂点の $y$ 座標 $q$ は 0 であるから：
$$2a^2 + b = 0 \implies b = -2a^2$$
このとき、$a + b$ は：
$$a + b = a - 2a^2 = -2\left(a^2 - \frac{1}{2}a\right) = -2\left(a - \frac{1}{4}\right)^2 + \frac{1}{8}$$
したがって、$a + b$ は $a = \frac{1}{4}$ で最大値 $\frac{1}{8}$ をとる。
よって、とり得る値の範囲は：
$$a + b \leq \frac{1}{8}$$
すなわち、$\text{I} = 1, \text{J} = 8$ (IJ = 18) である。

**【考査考点】**
- 2次関数の標準形への変形（平方完成）と頂点座標の特定。
- 条件式を用いた多変数関数の1変数化と2次関数の最大値の計算。
- 放物線が $x$ 軸に接する幾何学的条件（判別式 $D=0$ または頂点 $y=0$）の理解と活用。

---

## 大問I 問2：格子点上の3点による三角形形成の場合の数
- **Local Key**: `math-q-I_2`
- **Answer Ref**: `MATH_C2:I_2`
- **公式正解**: `{'KLM': '220', 'N': '3', 'O': '8', 'PQ': '12', 'R': '8', 'STU': '200', 'VW': '48'}`

**【題目大意】**
座標平面上に $4 \times 3$ の長方形状に並んだ12個の格子点 $(x, y)$ ($x \in \{1, 2, 3, 4\}, y \in \{1, 2, 3\}$) がある。これらから3個の点を選んで三角形を作る。全体の三角形の個数、および線分 $AB$ ($A(1, 1), B(4, 1)$) 上に2頂点をもつ三角形の個数を求める。

**【公式正解】**
- $\text{KLM} = 220$ (選び出し総数 220 通り)
- $\text{N} = 3$ (4点を通る直線 3 本)
- $\text{O} = 8$ (3点を通る直線 8 本)
- $\text{PQ} = 12$ (4点直線上の非三角形 12 通り)
- $\text{R} = 8$ (3点直線上の非三角形 8 通り)
- $\text{STU} = 200$ (作られる三角形 200 個)
- $\text{VW} = 48$ (線分 $AB$ 上に2頂点をもつ三角形 48 個)

**【詳細推導・解答プロセス】**
**(1) 12点から3点を選ぶ場合の数**
12個の相異なる点から3個の点を選び出す組合せ数は：
$$\binom{12}{3} = \frac{12 \times 11 \times 10}{3 \times 2 \times 1} = 220$$
よって、$\text{KLM} = 220$ 通りである。

**(2) 3点以上が一直線上に並ぶ直線の本数**
格子の配置は横4点、縦3点である。
(i) 4点を通る直線：
- 水平線 $y = 1, y = 2, y = 3$ の 3 本のみである。
したがって、$\text{N} = 3$ 本である。

(ii) ちょうど3点を通る直線：
- 垂直線 $x = 1, x = 2, x = 3, x = 4$ の 4 本。
- 傾き 1 の対角線：$(1, 1)-(2, 2)-(3, 3)$ および $(2, 1)-(3, 2)-(4, 3)$ の 2 本。
- 傾き -1 の対角線：$(1, 3)-(2, 2)-(3, 1)$ および $(2, 3)-(3, 2)-(4, 1)$ の 2 本。
合計で $4 + 2 + 2 = 8$ 本ある。
したがって、$\text{O} = 8$ 本である。

**(3) 三角形をなさない3点の組合せ数**
同一直線上にある3点を選ぶと三角形にならない。
- (i) 4点を通る直線 3 本から3点を選ぶ選び方は：
$$3 \times \binom{4}{3} = 3 \times 4 = 12 \text{ 通り}$$
よって、$\text{PQ} = 12$ 通りである。

- (ii) 3点を通る直線 8 本から3点を選ぶ選び方は：
$$8 \times \binom{3}{3} = 8 \times 1 = 8 \text{ 通り}$$
よって、$\text{R} = 8$ 通りである。

**(4) 作成できる三角形の総数**
全体の3点の選び方から、共線となる組合せを引くと：
$$220 - 12 - 8 = 200$$
よって、三角形は全部で $\text{STU} = 200$ 個できる。

**(5) 線分 $AB$ 上に2つの頂点をもつ三角形の個数**
線分 $AB$ は直線 $y = 1$ 上の 4 点 $(1, 1), (2, 1), (3, 1), (4, 1)$ を含む。
この4点から2頂点を選ぶ組合せは：
$$\binom{4}{2} = \frac{4 \times 3}{2} = 6 \text{ 通り}$$
第3の頂点は、同一直線 $y = 1$ 上にない残りの点、すなわち $y = 2$ または $y = 3$ にある点から選べばよい。
直線 $y = 1$ 上にない点は全部で $12 - 4 = 8$ 点ある。
選ばれた2点は $y=1$ 上にあり、第3の点は $y \neq 1$ 上にあるため、これら3点は決して同一直線上に並ばず、必ず三角形を形成する。
したがって、求める三角形の個数は：
$$6 \times 8 = 48$$
よって、$\text{VW} = 48$ 個である。

**【考査考点】**
- 組合せの基本計算 $\binom{n}{r}$。
- 平面格子点における同一直線（水平、垂直、斜め対角線）の網羅的分類と重複のない数え上げ。
- 条件を満たす三角形の形成条件の分析。

---

## 大問II 問1：余弦定理・ベクトルの内積と区分求積法（リーマン和の極限）
- **Local Key**: `math-q-II_1`
- **Answer Ref**: `MATH_C2:II_1`
- **公式正解**: `{'AB': '-6', 'CD': '32', 'EFGH': '4639', 'IJK': '172'}`

**【題目大意】**
$\triangle ABC$ において $AB=2, BC=3, CA=4$ とする。
(1) $\angle ABC = \theta$ とおき、余弦定理を用いてベクトル内積 $\overrightarrow{AB} \cdot \overrightarrow{BC}$ を求める。
(2) 辺 $BC$ を $n$ 等分する分点を $P_0=B, P_1, \dots, P_n=C$ とするとき、内積 $\overrightarrow{AP_{k-1}} \cdot \overrightarrow{AP_k}$ を計算し、極限 $\lim_{n \to \infty} \frac{1}{n} \sum_{k=1}^n \overrightarrow{AP_{k-1}} \cdot \overrightarrow{AP_k}$ を求める。

**【公式正解】**
- $\text{AB} = -6$ ($\overrightarrow{AB} \cdot \overrightarrow{BC} = -6 \cos \theta$)
- $\text{CD} = 32$ ($\overrightarrow{AB} \cdot \overrightarrow{BC} = \frac{3}{2}$)
- $\text{EFGH} = 4639$ ($\overrightarrow{AP_{k-1}} \cdot \overrightarrow{AP_k} = 4 + \frac{6k - 3}{2n} + \frac{9(k^2 - k)}{n^2}$)
- $\text{IJK} = 172$ (極限値 $\frac{17}{2}$)

**【詳細推導・解答プロセス】**
**(1) 余弦定理と内積の計算**
ベクトル $\overrightarrow{AB}$ と $\overrightarrow{BC}$ のなす角は $\pi - \theta$ である。
したがって：
$$\overrightarrow{AB} \cdot \overrightarrow{BC} = |\overrightarrow{AB}| |\overrightarrow{BC}| \cos(\pi - \theta) = -|\overrightarrow{AB}| |\overrightarrow{BC}| \cos \theta$$
$AB = 2, BC = 3$ であるから：
$$\overrightarrow{AB} \cdot \overrightarrow{BC} = -(2)(3) \cos \theta = -6 \cos \theta$$
よって、$\text{AB} = -6$ である。

次に、$\triangle ABC$ において余弦定理を適用すると：
$$CA^2 = AB^2 + BC^2 - 2 \, AB \cdot BC \cos \theta$$
$$4^2 = 2^2 + 3^2 - 2(2)(3) \cos \theta$$
$$16 = 13 - 12 \cos \theta \implies 12 \cos \theta = -3 \implies \cos \theta = -\frac{1}{4}$$
これを内積の式に代入すると：
$$\overrightarrow{AB} \cdot \overrightarrow{BC} = -6 \times \left(-\frac{1}{4}\right) = \frac{6}{4} = \frac{3}{2}$$
したがって、$\text{C} = 3, \text{D} = 2$ (CD = 32) である。

**(2) 内積 $\overrightarrow{AP_{k-1}} \cdot \overrightarrow{AP_k}$ の導出**
辺 $BC$ の分点 $P_k$ について、$\overrightarrow{BP_k} = \frac{k}{n} \overrightarrow{BC}$ であるから：
$$\overrightarrow{AP_k} = \overrightarrow{AB} + \overrightarrow{BP_k} = \overrightarrow{AB} + \frac{k}{n} \overrightarrow{BC}$$
同様に：
$$\overrightarrow{AP_{k-1}} = \overrightarrow{AB} + \frac{k-1}{n} \overrightarrow{BC}$$
両者の内積を展開すると：
$$\overrightarrow{AP_{k-1}} \cdot \overrightarrow{AP_k} = \left(\overrightarrow{AB} + \frac{k-1}{n} \overrightarrow{BC}\right) \cdot \left(\overrightarrow{AB} + \frac{k}{n} \overrightarrow{BC}\right)$$
$$= |\overrightarrow{AB}|^2 + \left(\frac{k-1}{n} + \frac{k}{n}\right) \overrightarrow{AB} \cdot \overrightarrow{BC} + \frac{k(k-1)}{n^2} |\overrightarrow{BC}|^2$$
各数値を代入する（$|\overrightarrow{AB}|^2 = 4$、$|\overrightarrow{BC}|^2 = 9$、$\overrightarrow{AB} \cdot \overrightarrow{BC} = \frac{3}{2}$）：
$$= 4 + \frac{2k - 1}{n} \times \frac{3}{2} + \frac{k^2 - k}{n^2} \times 9$$
$$= 4 + \frac{6k - 3}{2n} + \frac{9(k^2 - k)}{n^2}$$
問題の形式 $E + \frac{Fk - G}{2n} + \frac{H(k^2 - k)}{n^2}$ と比較すると：
$$E = 4, \quad F = 6, \quad G = 3, \quad H = 9$$
したがって、$\text{EFGH} = 4639$ である。

**(3) 極限値の計算（区分求積法）**
求める極限は：
$$\lim_{n \to \infty} \frac{1}{n} \sum_{k=1}^n \overrightarrow{AP_{k-1}} \cdot \overrightarrow{AP_k}$$
$$= \lim_{n \to \infty} \frac{1}{n} \sum_{k=1}^n \left[ 4 + 3 \cdot \frac{k}{n} - \frac{3}{2n} + 9 \left(\frac{k}{n}\right)^2 - \frac{9k}{n^2} \right]$$
区分求積法（$\lim_{n \to \infty} \frac{1}{n} \sum_{k=1}^n f(k/n) = \int_0^1 f(x)dx$）を適用する。
$\frac{1}{n}$ 次の微小項 $\frac{3}{2n}$ や $\frac{9k}{n^2}$ は極限で 0 に収束するため：
$$= \int_0^1 4 \, dx + \int_0^1 3x \, dx + \int_0^1 9x^2 \, dx$$
それぞれ定積分を計算すると：
- $\int_0^1 4 \, dx = 4$
- $\int_0^1 3x \, dx = \left[ \frac{3}{2}x^2 \right]_0^1 = \frac{3}{2}$
- $\int_0^1 9x^2 \, dx = \left[ 3x^3 \right]_0^1 = 3$
したがって、合計は：
$$4 + \frac{3}{2} + 3 = 7 + \frac{3}{2} = \frac{17}{2}$$
よって、$\text{IJK} = 172$ である。

**【考査考点】**
- ベクトルの幾何学的定義（始点を揃えたときのなす角と内積の符号）。
- 余弦定理を用いた三角形の内角の余弦の決定。
- 分点ベクトルの線形結合表現および内積展開。
- リーマン和（区分求積法）による定積分への帰着と極限計算。

---

## 大問II 問2：複素数平面上の円領域と直線の交線上の絶対値の最大・最小
- **Local Key**: `math-q-II_2`
- **Answer Ref**: `MATH_C2:II_2`
- **公式正解**: `{'LM': '12', 'NO': '25', 'PQR': '101', 'STU': '102', 'VWXY': '1212'}`

**【題目大意】**
複素数 $z$ が条件 $z\bar{z} - (1 - 2i)z - (1 + 2i)\bar{z} \leq 15$ $\textcircled{1}$ を満たす。
(1) 不等式 $\textcircled{1}$ が表す円の中心と半径を求める。
(2) 直線 $(1 - i)z - (1 + i)\bar{z} = 2i$ 上にあり、不等式 $\textcircled{1}$ を満たす $z$ のうち、$|z|$ が最大となる $z_1$ と最小となる $z_2$ を求める。

**【公式正解】**
- $\text{LM} = 12$ (中心 $1 + 2i$)
- $\text{NO} = 25$ (半径 $2\sqrt{5}$)
- $\text{PQR} = 101, \text{STU} = 102$ ($z_1 = \sqrt{10} + 1 + (\sqrt{10} + 2)i$)
- $\text{VWXY} = 1212$ ($z_2 = -\frac{1}{2} + \frac{1}{2}i$)

**【詳細推導・解答プロセス】**
**(1) 円の方程式の導出**
$\alpha = 1 + 2i$ とおくと、$\bar{\alpha} = 1 - 2i$ である。
条件式 $\textcircled{1}$ の左辺を平方完成する：
$$z\bar{z} - \bar{\alpha}z - \alpha\bar{z} = (z - \alpha)(\bar{z} - \bar{\alpha}) - \alpha\bar{\alpha} = |z - \alpha|^2 - |\alpha|^2$$
ここで $|\alpha|^2 = 1^2 + 2^2 = 5$ であるから：
$$|z - (1 + 2i)|^2 - 5 \leq 15 \implies |z - (1 + 2i)|^2 \leq 20$$
両辺の平方根をとると：
$$|z - (1 + 2i)| \leq \sqrt{20} = 2\sqrt{5}$$
したがって、中心は $1 + 2i$、半径は $2\sqrt{5}$ である。
よって、$\text{L} = 1, \text{M} = 2$ (LM = 12)、$\text{N} = 2, \text{O} = 5$ (NO = 25) である。

**(2) 直線の方程式の実部・虚部による表現**
$z = x + yi$ ($x, y$ は実数) とおくと、$\bar{z} = x - yi$ である。
与えられた直線の方程式は：
$$(1 - i)(x + yi) - (1 + i)(x - yi) = 2i$$
左辺を展開・整理する：
$$(x + y + i(y - x)) - (x + y + i(x - y)) = 2i(y - x)$$
したがって：
$$2i(y - x) = 2i \implies y - x = 1 \implies y = x + 1$$
すなわち、直線の方程式は $y = x + 1$ である。

**(3) 円領域との共通部分（線分）**
円領域は $(x - 1)^2 + (y - 2)^2 \leq 20$ である。
$y = x + 1$ を代入すると、$y - 2 = x - 1$ となるので：
$$(x - 1)^2 + (x - 1)^2 \leq 20 \implies 2(x - 1)^2 \leq 20 \implies (x - 1)^2 \leq 10$$
$$-\sqrt{10} \leq x - 1 \leq \sqrt{10} \implies 1 - \sqrt{10} \leq x \leq 1 + \sqrt{10}$$
媒介変数 $t = x - 1$ ($-\sqrt{10} \leq t \leq \sqrt{10}$) を用いると：
$$x = 1 + t, \quad y = 2 + t$$

**(4) $|z|$ の最大値・最小値の導出**
$|z|^2 = x^2 + y^2$ を $t$ で表すと：
$$|z|^2 = (1 + t)^2 + (2 + t)^2 = 2t^2 + 6t + 5 = 2\left(t + \frac{3}{2}\right)^2 + 5 - \frac{9}{2} = 2\left(t + \frac{3}{2}\right)^2 + \frac{1}{2}$$
-$|z|$ の最大値：
軸 $t = -\frac{3}{2}$ から最も遠い端点は $t = \sqrt{10}$ である。
このとき：
$$x = 1 + \sqrt{10}, \quad y = 2 + \sqrt{10}$$
したがって：
$$z_1 = (1 + \sqrt{10}) + (2 + \sqrt{10})i = \sqrt{10} + 1 + (\sqrt{10} + 2)i$$
問題の形 $z_1 = \sqrt{PQ} + R + (\sqrt{ST} + U)i$ と比較すると：
$$PQ = 10, \quad R = 1, \quad ST = 10, \quad U = 2$$
よって、$\text{PQR} = 101, \text{STU} = 102$ である。

-$|z|$ の最小値：
頂点 $t = -\frac{3}{2}$ は区間 $[-\sqrt{10}, \sqrt{10}]$ (約 $[-3.16, 3.16]$) に含まれる。
したがって、$t = -\frac{3}{2}$ のとき $|z|^2$ は最小値 $\frac{1}{2}$ をとる。
このとき：
$$x = 1 - \frac{3}{2} = -\frac{1}{2}, \quad y = 2 - \frac{3}{2} = \frac{1}{2}$$
したがって：
$$z_2 = -\frac{1}{2} + \frac{1}{2}i$$
問題の形 $z_2 = -\frac{V}{W} + \frac{X}{Y}i$ と比較すると：
$$V = 1, \quad W = 2, \quad X = 1, \quad Y = 2$$
よって、$\text{VWXY} = 1212$ である。

**【考査考点】**
- 複素数と共役複素数の性質を用いた円の方程式の決定。
- 複素数表現の直線から実数直交座標方程式への変換。
- 媒介変数を用いた線分上の点と原点からの距離 $|z|$ の2次関数解析（最大値・最小値）。

---

## 大問III [1]：条件を満たす円弧の幾何学的特徴と一次結合 $t = x + y$ の値域
- **Local Key**: `math-q-III_1`
- **Answer Ref**: `MATH_C2:III_1`
- **公式正解**: `{'AB': '23', 'CD': '66', 'E': '0', 'FG': '26'}`

**【題目大意】**
実数 $x, y, t, u$ が $y \geq |x|$ $\textcircled{1}$、$x + y = t$ $\textcircled{2}$、$x^2 + y^2 = 12$ $\textcircled{3}$、$x^3 + y^3 = u$ $\textcircled{4}$ を満たす。
点 $(x, y)$ がなす円弧の半径と両端点の座標を求め、$t$ がとり得る値の範囲を決定する。

**【公式正解】**
- $\text{AB} = 23$ (半径 $2\sqrt{3}$)
- $\text{CD} = 66$ (端点の座標 $(\sqrt{6}, \sqrt{6})$, $(-\sqrt{6}, \sqrt{6})$)
- $\text{E} = 0, \text{FG} = 26$ ($0 \leq t \leq 2\sqrt{6}$)

**【詳細推導・解答プロセス】**
**(1) 円弧の特定と半径・端点の導出**
$\textcircled{3}$ より、点 $(x, y)$ は原点を中心とする円 $x^2 + y^2 = 12$ 上にある。
この円の半径は：
$$r = \sqrt{12} = 2\sqrt{3}$$
したがって、$\text{AB} = 23$ である。

次に、$\textcircled{1}$ は $y \geq x$ かつ $y \geq -x$ を意味し、直線 $y = x$ と $y = -x$ の間の上側領域を表す。
円 $x^2 + y^2 = 12$ とこの境界線との交点を求める。
-$y = x$ との交点（第1象限）：
$$x^2 + x^2 = 12 \implies 2x^2 = 12 \implies x^2 = 6$$
$y \geq 0$ より $x = \sqrt{6}, y = \sqrt{6}$。
-$y = -x$ との交点（第2象限）：
$$x^2 + (-x)^2 = 12 \implies 2x^2 = 12 \implies x = -\sqrt{6}, y = \sqrt{6}$。
偏角 $\theta$ で見ると、$\frac{\pi}{4} \leq \theta \leq \frac{3\pi}{4}$ の範囲の四分円の弧（中心角 $\frac{\pi}{2}$）をなしている。
したがって、弧の両端点の座標は：
$$\left(\sqrt{6}, \sqrt{6}\right), \quad \left(-\sqrt{6}, \sqrt{6}\right)$$
よって、$\text{CD} = 66$ である。

**(2) $t = x + y$ のとり得る値の範囲**
直線 $x + y = t$ とこの円弧 $\frac{\pi}{4} \leq \theta \leq \frac{3\pi}{4}$ が共有点をもつ $t$ の範囲を調べる。
点 $(x, y)$ は $x = \sqrt{12}\cos \theta, y = \sqrt{12}\sin \theta$ と表せるので：
$$t = x + y = \sqrt{12}(\cos \theta + \sin \theta) = \sqrt{12} \cdot \sqrt{2} \sin\left(\theta + \frac{\pi}{4}\right) = \sqrt{24} \sin\left(\theta + \frac{\pi}{4}\right) = 2\sqrt{6} \sin\left(\theta + \frac{\pi}{4}\right)$$
$\theta \in \left[\frac{\pi}{4}, \frac{3\pi}{4}\right]$ より、$\theta + \frac{\pi}{4} \in \left[\frac{\pi}{2}, \pi\right]$ である。
この区間において：
-最大値：$\theta + \frac{\pi}{4} = \frac{\pi}{2}$（すなわち $\theta = \frac{\pi}{4}$、端点 $(\sqrt{6}, \sqrt{6})$）のとき、
$$\sin\left(\frac{\pi}{2}\right) = 1 \implies t = 2\sqrt{6}$$
-最小値：$\theta + \frac{\pi}{4} = \pi$（すなわち $\theta = \frac{3\pi}{4}$、端点 $(-\sqrt{6}, \sqrt{6})$）のとき、
$$\sin(\pi) = 0 \implies t = 0$$
したがって、$t$ のとり得る値の範囲は：
$$0 \leq t \leq 2\sqrt{6} \quad \textcircled{5}$$
よって、$\text{E} = 0, \text{FG} = 26$ である。

**【考査考点】**
- 円と絶対値不等式が定める領域の境界（円弧）の同定。
- 円弧の端点座標の幾何学的計算。
- 三角関数の合成法を用いた線形和 $x + y$ のとり得る値域の導出。

---

## 大問III [2]：対称式の変数変換・微分法による3次式の値域決定
- **Local Key**: `math-q-III_2`
- **Answer Ref**: `MATH_C2:III_2`
- **公式正解**: `{'HIJK': '1212', 'LMNO': '1236', 'PQRS': '3212', 'T': '0', 'UVW': '243'}`

**【題目大意】**
$x + y = t$、 $x^2 + y^2 = 12$、$x^3 + y^3 = u$ のもとで、$xy$ および $u$ を $t$ の式で表し、導関数 $\frac{du}{dt}$ を求めて、$0 \leq t \leq 2\sqrt{6}$ における $u$ のとり得る値の範囲を決定する。

**【公式正解】**
- $\text{HIJK} = 1212$ ($xy = \frac{1}{2}(t^2 - 12)$)
- $\text{LMNO} = 1236$ ($u = \frac{1}{2}(36t - t^3)$)
- $\text{PQRS} = 3212$ ($\frac{du}{dt} = \frac{3}{2}(12 - t^2)$)
- $\text{T} = 0, \text{UVW} = 243$ ($0 \leq u \leq 24\sqrt{3}$)

**【詳細推導・解答プロセス】**
**(1) $xy$ を $t$ で表す**
$(x + y)^2 = x^2 + 2xy + y^2$ より：
$$t^2 = 12 + 2xy \implies xy = \frac{1}{2}(t^2 - 12)$$
問題の形 $xy = \frac{H}{I}(t^2 - JK)$ と比較すると：
$$H = 1, \quad I = 2, \quad JK = 12$$
したがって、$\text{HIJK} = 1212$ である。

**(2) $u$ を $t$ で表す**
3次対称式の展開公式 $x^3 + y^3 = (x + y)^3 - 3xy(x + y)$ を用いる：
$$u = t^3 - 3 \left[\frac{1}{2}(t^2 - 12)\right] t = t^3 - \frac{3}{2}t^3 + 18t = 18t - \frac{1}{2}t^3 = \frac{1}{2}(36t - t^3)$$
問題の形 $u = \frac{L}{M}(NO \, t - t^3)$ と比較すると：
$$L = 1, \quad M = 2, \quad NO = 36$$
したがって、$\text{LMNO} = 1236$ である。

**(3) 導関数 $\frac{du}{dt}$ の計算**
$u = 18t - \frac{1}{2}t^3$ を $t$ で微分すると：
$$\frac{du}{dt} = 18 - \frac{3}{2}t^2 = \frac{3}{2}(12 - t^2)$$
問題の形 $\frac{du}{dt} = \frac{P}{Q}(RS - t^2)$ と比較すると：
$$P = 3, \quad Q = 2, \quad RS = 12$$
したがって、$\text{PQRS} = 3212$ である。

**(4) $u$ の増減ととり得る値の範囲**
$0 \leq t \leq 2\sqrt{6}$ において、$\frac{du}{dt} = 0$ となるのは：
$$t^2 = 12 \implies t = \sqrt{12} = 2\sqrt{3}$$
増減表を作成する：

| $t$ | $0$ | $\dots$ | $2\sqrt{3}$ | $\dots$ | $2\sqrt{6}$ |
| :---: | :---: | :---: | :---: | :---: | :---: |
| $\frac{du}{dt}$ | | $+$ | $0$ | $-$ | |
| $u$ | $0$ | $\nearrow$ | 極大 | $\searrow$ | $12\sqrt{6}$ |

各点での $u$ の値を計算する：
- $t = 0$ のとき：
$$u = \frac{1}{2}(0 - 0) = 0$$
- $t = 2\sqrt{3}$ のとき（極大値）：
$$u = 18(2\sqrt{3}) - \frac{1}{2}(2\sqrt{3})^3 = 36\sqrt{3} - \frac{1}{2}(24\sqrt{3}) = 36\sqrt{3} - 12\sqrt{3} = 24\sqrt{3}$$
- $t = 2\sqrt{6}$ のとき（端点）：
$$u = 18(2\sqrt{6}) - \frac{1}{2}(2\sqrt{6})^3 = 36\sqrt{6} - \frac{1}{2}(48\sqrt{6}) = 36\sqrt{6} - 24\sqrt{6} = 12\sqrt{6}$$
ここで、$24\sqrt{3}$ と $12\sqrt{6}$ の大きさを比較すると：
$$(24\sqrt{3})^2 = 576 \times 3 = 1728$$
$$(12\sqrt{6})^2 = 144 \times 6 = 864$$
より、$24\sqrt{3} > 12\sqrt{6}$ である。
また、区間内の最小値は $t = 0$ のときの $u = 0$ である。
したがって、$u$ のとり得る値の範囲は：
$$0 \leq u \leq 24\sqrt{3}$$
よって、$\text{T} = 0, \text{UVW} = 243$ である。

**【考査考点】**
- 対称式の基本性質と変数変換による次数の整理。
- 微分法による3次関数の増減、極値の判定。
- 閉区間における極大値と端点値の比較による値域（最大値・最小値）の確定。

---

## 大問IV [1]：三角関数で囲まれた図形の面積積分と導関数の定式化
- **Local Key**: `math-q-IV_1`
- **Answer Ref**: `MATH_C2:IV_1`
- **公式正解**: `{'A': '3', 'B': '3', 'CDE': '122'}`

**【題目大意】**
$a > 1$ とする。領域 $0 \leq x \leq \frac{\pi}{6}, 0 \leq y \leq a \cos 3x$ を直線 $y = 1$ で分割し、$y \geq 1$ の面積を $S$、$y \leq 1$ の面積を $T$ とする。
$a \cos 3t = 1$ ($0 \leq t \leq \frac{\pi}{6}$) とおくとき、$S$、$S + T$ を $t$ で表し、$f(t) = T - S$ の導関数 $f'(t)$ を求める。

**【公式正解】**
- $\text{A} = 3$ ($S = \frac{\sin 3t}{3\cos 3t} - t$)
- $\text{B} = 3$ ($S + T = \frac{1}{3\cos 3t}$)
- $\text{CDE} = 122$ ($f'(t) = \frac{(1 - 2\sin 3t)\sin 3t}{\cos^2 3t}$)

**【詳細推導・解答プロセス】**
**(1) 面積 $S$ および $S + T$ の計算**
条件より $a \cos 3t = 1$ であるから：
$$a = \frac{1}{\cos 3t}$$
区間 $0 \leq x \leq t$ では $a \cos 3x \geq 1$ である。
したがって、$y \geq 1$ の部分の面積 $S$ は：
$$S = \int_0^t (a \cos 3x - 1) \, dx = \left[ \frac{a}{3}\sin 3x - x \right]_0^t = \frac{a}{3}\sin 3t - t$$
$a = \frac{1}{\cos 3t}$ を代入すると：
$$S = \frac{\sin 3t}{3 \cos 3t} - t$$
よって、$\text{A} = 3$ である。

次に、$S + T$ は領域全体の面積、すなわち $0 \leq x \leq \frac{\pi}{6}$ における $y = a \cos 3x$ の定積分である：
$$S + T = \int_0^{\pi/6} a \cos 3x \, dx = \left[ \frac{a}{3}\sin 3x \right]_0^{\pi/6} = \frac{a}{3}\sin\left(\frac{\pi}{2}\right) = \frac{a}{3}$$
$a = \frac{1}{\cos 3t}$ を代入すると：
$$S + T = \frac{1}{3 \cos 3t}$$
よって、$\text{B} = 3$ である。

**(2) $f(t) = T - S$ の導関数の導出**
$T = (S + T) - S$ より：
$$f(t) = T - S = (S + T) - 2S = \frac{1}{3 \cos 3t} - 2\left(\frac{\sin 3t}{3 \cos 3t} - t\right) = \frac{1 - 2\sin 3t}{3 \cos 3t} + 2t$$
これを $t$ で微分する。
第1項 $\frac{1 - 2\sin 3t}{3 \cos 3t}$ の微分には商の微分法を用いる：
$$\frac{d}{dt}\left[\frac{1 - 2\sin 3t}{3 \cos 3t}\right] = \frac{(-6\cos 3t)(3\cos 3t) - (1 - 2\sin 3t)(-9\sin 3t)}{9 \cos^2 3t}$$
$$= \frac{-18 \cos^2 3t + 9 \sin 3t - 18 \sin^2 3t}{9 \cos^2 3t} = \frac{-18(\cos^2 3t + \sin^2 3t) + 9 \sin 3t}{9 \cos^2 3t}$$
$$= \frac{-18 + 9 \sin 3t}{9 \cos^2 3t} = \frac{-2 + \sin 3t}{\cos^2 3t}$$
第2項 $2t$ の微分は $2 = \frac{2\cos^2 3t}{\cos^2 3t} = \frac{2(1 - \sin^2 3t)}{\cos^2 3t}$ である。
したがって、両者を足し合わせると：
$$f'(t) = \frac{-2 + \sin 3t + 2 - 2\sin^2 3t}{\cos^2 3t} = \frac{\sin 3t - 2\sin^2 3t}{\cos^2 3t} = \frac{(1 - 2\sin 3t)\sin 3t}{\cos^2 3t}$$
問題の形 $f'(t) = \frac{(C - D\sin 3t)\sin 3t}{\cos^E 3t}$ と比較すると：
$$C = 1, \quad D = 2, \quad E = 2$$
したがって、$\text{CDE} = 122$ である。

**【考査考点】**
- 三角関数の定積分による面積の計算。
- 方程式の根 $t$ をパラメータとする関数関係の定式化。
- 商の微分法および三角関数の基本恒等式 $\sin^2 \theta + \cos^2 \theta = 1$ を用いた導関数の因数分解。

---

## 大問IV [2]：面積差の最大化・最適パラメータと最大値の導出
- **Local Key**: `math-q-IV_2`
- **Answer Ref**: `MATH_C2:IV_2`
- **公式正解**: `{'FG': '18', 'HIJ': '233', 'K': '9'}`

**【題目大意】**
$f(t) = T - S$ を最大にする $t$ の値、そのときのパラメータ $a$ の値、および $T - S$ の最大値を求める。

**【公式正解】**
- $\text{FG} = 18$ ($t = \frac{\pi}{18}$)
- $\text{HIJ} = 233$ ($a = \frac{2\sqrt{3}}{3}$)
- $\text{K} = 9$ (最大値 $\frac{\pi}{9}$)

**【詳細推導・解答プロセス】**
**(1) $T - S$ を最大にする $t$ の導出**
導関数は：
$$f'(t) = \frac{(1 - 2\sin 3t)\sin 3t}{\cos^2 3t}$$
$0 < t < \frac{\pi}{6}$ において、$0 < 3t < \frac{\pi}{2}$ であるから、$\sin 3t > 0$ かつ $\cos 3t > 0$ である。
したがって、$f'(t)$ の符号は $1 - 2\sin 3t$ の符号と一致する。
$f'(t) = 0$ となるのは：
$$1 - 2\sin 3t = 0 \implies \sin 3t = \frac{1}{2}$$
$0 < 3t < \frac{\pi}{2}$ より：
$$3t = \frac{\pi}{6} \implies t = \frac{\pi}{18}$$
区間 $\left(0, \frac{\pi}{6}\right)$ における増減は以下のようになる：
- $0 < t < \frac{\pi}{18}$ では $\sin 3t < \frac{1}{2}$ なので $f'(t) > 0$（単調増加）。
- $\frac{\pi}{18} < t < \frac{\pi}{6}$ では $\sin 3t > \frac{1}{2}$ なので $f'(t) < 0$（単調減少）。
したがって、$f(t) = T - S$ は $t = \frac{\pi}{18}$ で極大かつ最大となる。
よって、$\text{FG} = 18$ である。

**(2) 最大値を与えるパラメータ $a$ の導出**
$a = \frac{1}{\cos 3t}$ であるから、$t = \frac{\pi}{18}$（すなわち $3t = \frac{\pi}{6}$）を代入すると：
$$a = \frac{1}{\cos(\pi/6)} = \frac{1}{\frac{\sqrt{3}}{2}} = \frac{2}{\sqrt{3}} = \frac{2\sqrt{3}}{3}$$
問題の形 $a = \frac{H\sqrt{I}}{J}$ と比較すると：
$$H = 2, \quad I = 3, \quad J = 3$$
したがって、$\text{HIJ} = 233$ である。

**(3) $T - S$ の最大値の計算**
$t = \frac{\pi}{18}$ のときの $f(t) = \frac{1 - 2\sin 3t}{3\cos 3t} + 2t$ を計算する。
$\sin 3t = \frac{1}{2}$ であるから、第1項の分子は $1 - 2\left(\frac{1}{2}\right) = 0$ となる。
したがって：
$$f\left(\frac{\pi}{18}\right) = 0 + 2\left(\frac{\pi}{18}\right) = \frac{\pi}{9}$$
問題の形 $\frac{\pi}{K}$ と比較すると：
$$K = 9$$
よって、$\text{K} = 9$ である。

**【考査考点】**
- 微分を用いた極値条件の判定と増減表の作成。
- 媒介変数と元の幾何学的パラメータの相互変換。
- 関数の最大値計算における代数的単純化の活用。

---
