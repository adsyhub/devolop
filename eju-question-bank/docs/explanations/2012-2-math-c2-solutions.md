# 2012-2 EJU 数学 コース2 詳解

## 数学 コース2 第I問 [1]：2次関数の原点対称移動と指定区間における最大・最小値

**【題目大意】**
$a \neq 0$ とする。2次関数 $y = ax^2 - 4x - 4a$ $\cdots\textcircled{1}$ のグラフと原点 $(0, 0)$ に関して対称な曲線を $G$ とする。
(1) $\textcircled{1}$ の頂点の座標を求める。
(2) 曲線 $G$ を表す2次関数を選択肢の中から選ぶ。
(3) $G$ と $\textcircled{1}$ の交点の座標を求める。
(4) $a = 2$ のとき，区間 $DE \leq x \leq G$ における $G$ の最大値と最小値を求める。

**【公式正解】**
正解：
$\text{AB} = 24$
$\text{C} = 4$
$\text{DEF} = -28$
$\text{GHI} = 2-8$
$\text{JK} = 10$
$\text{LM} = -8$

**【詳細推導・解答プロセス】**
1. **(1) 頂点座標の算出**：
与えられた2次関数の式を変形（平方完成）する：
$$y = a\left(x^2 - \frac{4}{a}x\right) - 4a = a\left(x - \frac{2}{a}\right)^2 - a \cdot \frac{4}{a^2} - 4a = a\left(x - \frac{2}{a}\right)^2 - \frac{4}{a} - 4a$$
したがって，頂点の座標は：
$$\left(\frac{2}{a}, -\frac{4}{a} - 4a\right)$$
これより，$\text{A} = 2, \text{B} = 4$（$\text{AB} = 24$）である。

2. **(2) 原点対称移動による曲線 $G$ の方程式**：
点 $(x, y)$ を原点に関して対称移動させると $(-x, -y)$ に移る。
元の関数 $y = ax^2 - 4x - 4a$ の $x$ を $-x$ に，$y$ を $-y$ に置き換えると：
$$-y = a(-x)^2 - 4(-x) - 4a = ax^2 + 4x - 4a$$
両辺に $-1$ を掛けて整理すると：
$$y = -ax^2 - 4x + 4a$$
これは選択肢 $\textcircled{4}$ に一致する。したがって $\text{C} = 4$ である。

3. **(3) 2つの放物線の交点座標**：
$\textcircled{1}$ と $G$ の連立方程式を解く：
$$ax^2 - 4x - 4a = -ax^2 - 4x + 4a$$
両辺の $-4x$ を消去し，移行して整理すると：
$$2ax^2 = 8a$$
$a \neq 0$ より，両辺を $2a$ で割ると：
$$x^2 = 4 \implies x = \pm 2$$
- $x = -2$ のとき：
  $$y = a(-2)^2 - 4(-2) - 4a = 4a + 8 - 4a = 8$$
  交点は $(-2, 8)$ である。これより $\text{DE} = -2, \text{F} = 8$（$\text{DEF} = -28$）。
- $x = 2$ のとき：
  $$y = a(2)^2 - 4(2) - 4a = 4a - 8 - 4a = -8$$
  交点は $(2, -8)$ である。これより $\text{G} = 2, \text{HI} = -8$（$\text{GHI} = 2-8$）。

4. **(4) $a=2$ のときの区間 $[-2, 2]$ における最大値・最小値**：
$a = 2$ のとき，曲線 $G$ の方程式は：
$$y = -2x^2 - 4x + 8 = -2(x^2 + 2x) + 8 = -2(x + 1)^2 + 10$$
これは上に凸の放物線であり，軸は $x = -1$ である。
指定された区間は $-2 \leq x \leq 2$ である：
- 軸 $x = -1$ は区間 $[-2, 2]$ の内部に含まれるため，最大値は頂点でとり：
  $$y_{\text{max}} = 10 \quad (x = -1 \text{ のとき})$$
  これより $\text{JK} = 10$ である。
- 最小値は軸 $x = -1$ から最も遠い端点 $x = 2$ でとり：
  $$y_{\text{min}} = -2(2+1)^2 + 10 = -18 + 10 = -8 \quad (x = 2 \text{ のとき})$$
  これより $\text{LM} = -8$ である。

**【考査考点】**
2次関数の平方完成，図形の原点対称移動，2次方程式による共有点の算出，定義域制限下の2次関数の最大・最小値問題。

---

## 数学 コース2 第I問 [2]：絶対値を含む1次方程式の解法と整数解条件

**【題目大意】**
$a$ を定数とし，$x$ の方程式 $|ax - 11| = 4x - 10$ $\cdots\textcircled{1}$ を考える。
(1) 絶対値の記号を使わない形に変形する。
(2) $a = \sqrt{7}$ のときの方程式の解を求める。
(3) $a$ が正の整数のとき，方程式が正の整数解をもつような $a$ とその解 $x$ を求める。

**【公式正解】**
正解：
$\text{NO} = 41$
$\text{PQR} = 421$
$\text{STUV} = 7473$
$\text{W} = 3$
$\text{X} = 3$

**【詳細推導・解答プロセス】**
1. **(1) 絶対値の解除**：
絶対値の中身の正負によって場合分けする：
- $ax - 11 \geq 0$，すなわち $ax \geq 11$ のとき：
  $$ax - 11 = 4x - 10 \implies (a - 4)x = 1$$
  これより $\text{N} = 4, \text{O} = 1$（$\text{NO} = 41$）。
- $ax - 11 < 0$，すなわち $ax < 11$ のとき：
  $$-(ax - 11) = 4x - 10 \implies -ax + 11 = 4x - 10 \implies (a + 4)x = 21$$
  これより $\text{P} = 4, \text{QR} = 21$（$\text{PQR} = 421$）。

2. **(2) $a = \sqrt{7}$ のときの解**：
右辺 $4x - 10$ は絶対値と等しいため，$4x - 10 \geq 0 \implies x \geq \frac{5}{2} = 2.5$ でなければならない。
- もし $ax \geq 11$ の場合：
  $(\sqrt{7} - 4)x = 1 \implies x = \frac{1}{\sqrt{7} - 4} < 0$ となり，不適。
- したがって $ax < 11$ の場合である：
  $$(\sqrt{7} + 4)x = 21 \implies x = \frac{21}{4 + \sqrt{7}}$$
  分母を有理化すると：
  $$x = \frac{21(4 - \sqrt{7})}{(4 + \sqrt{7})(4 - \sqrt{7})} = \frac{21(4 - \sqrt{7})}{16 - 7} = \frac{21(4 - \sqrt{7})}{9} = \frac{7(4 - \sqrt{7})}{3}$$
  この値について確認すると：
  $\sqrt{7} \approx 2.646$ より $4 - \sqrt{7} \approx 1.354$ であり，$x = \frac{7 \times 1.354}{3} \approx 3.16 > 2.5$ である。
  また $ax = \sqrt{7} \times 3.16 \approx 8.36 < 11$ を満たす。
  したがって，$x = \frac{7(4 - \sqrt{7})}{3}$ である。
  これより $\text{S} = 7, \text{T} = 4, \text{U} = 7, \text{V} = 3$（$\text{STUV} = 7473$）。

3. **(3) $a$ が正の整数で正の整数解をもつ条件**：
$x$ が正の整数であるとき，方程式の解の候補を吟味する：
- **場合 1**：$ax \geq 11$ のとき，$(a - 4)x = 1$
  $a, x$ は整数であるから，$a - 4$ と $x$ は 1 の約数である。
  $x > 0$ より $x = 1, a - 4 = 1 \implies a = 5$。
  このとき $ax = 5 \times 1 = 5$ であるが，前提条件 $ax \geq 11$ に反するため不適。
- **場合 2**：$ax < 11$ のとき，$(a + 4)x = 21$
  $a$ は正の整数（$a \geq 1$）であるから，$a + 4 \geq 5$ である。
  21 の正の約数は $1, 3, 7, 21$ であるから，$a + 4$ の候補は $7$ または $21$ である。
  - $a + 4 = 7$ のとき：$a = 3$
    このとき $x = \frac{21}{7} = 3$ である。
    条件 $ax < 11$ を確認すると $3 \times 3 = 9 < 11$ を満たし，適する。
  - $a + 4 = 21$ のとき：$a = 17$
    このとき $x = 1$ であるが，$ax = 17 \times 1 = 17 > 11$ となり条件 $ax < 11$ に反するため不適。
したがって，求める値は $a = 3, x = 3$ である。
これより $\text{W} = 3, \text{X} = 3$ である。

**【考査考点】**
絶対値の定義による場合分け，無理数の有理化，約数を用いた整数の不定方程式の整数解の絞り込み。

---

## 数学 コース2 第II問 (前半)：円に内接する三角形のベクトル方程式と共線条件

**【題目大意】**
半径 2 の円 O に内接する三角形 ABC が $3\overrightarrow{OA} + 4\overrightarrow{OB} + 2\overrightarrow{OC} = \vec{0}$ $\cdots\textcircled{1}$ を満たしている。
直線 AO と線分 BC の交点を D とおく。
(1) $\overrightarrow{OD} = k\overrightarrow{OA}$ とおくとき，$\overrightarrow{OD}$ を $\overrightarrow{OB}, \overrightarrow{OC}$ で表し，3点 B, C, D が一直線上にあることから $k$ を求め，線分 OD および AD の長さを求める。

**【公式正解】**
正解：
$\text{ABCD} = 4323$
$\text{EFG} = -12$
$\text{H} = 1$
$\text{I} = 3$

**【詳細推導・解答プロセス】**
1. **$\overrightarrow{OD}$ の基底分解**：
条件式 $\textcircled{1}$ より：
$$3\overrightarrow{OA} = -4\overrightarrow{OB} - 2\overrightarrow{OC} \implies \overrightarrow{OA} = -\frac{4}{3}\overrightarrow{OB} - \frac{2}{3}\overrightarrow{OC}$$
$\overrightarrow{OD} = k\overrightarrow{OA}$ であるから：
$$\overrightarrow{OD} = -\frac{4}{3}k\overrightarrow{OB} - \frac{2}{3}k\overrightarrow{OC}$$
したがって，$\text{A} = 4, \text{B} = 3, \text{C} = 2, \text{D} = 3$（$\text{ABCD} = 4323$）である。

2. **共線条件による $k$ の決定**：
点 D は直線 BC 上にあるため，$\overrightarrow{OB}$ と $\overrightarrow{OC}$ の係数の和は 1 に等しい：
$$-\frac{4}{3}k - \frac{2}{3}k = 1$$
$$-\frac{6}{3}k = 1 \implies -2k = 1 \implies k = -\frac{1}{2}$$
したがって，$k = \frac{-1}{2}$ であり，$\text{EF} = -1, \text{G} = 2$（$\text{EFG} = -12$）である。

3. **線分 OD および AD の長さ**：
円 O の半径が 2 であるから，$|\overrightarrow{OA}| = 2$ である。
$\overrightarrow{OD} = -\frac{1}{2}\overrightarrow{OA}$ より：
$$OD = |\overrightarrow{OD}| = \left|-\frac{1}{2}\right| |\overrightarrow{OA}| = \frac{1}{2} \times 2 = 1$$
これより $\text{H} = 1$ である。
また，$\overrightarrow{AD} = \overrightarrow{OD} - \overrightarrow{OA} = -\frac{1}{2}\overrightarrow{OA} - \overrightarrow{OA} = -\frac{3}{2}\overrightarrow{OA}$ であるから：
$$AD = |\overrightarrow{AD}| = \frac{3}{2} |\overrightarrow{OA}| = \frac{3}{2} \times 2 = 3$$
これより $\text{I} = 3$ である。

**【考査考点】**
平面ベクトルの1次結合表示，3点の共線条件（係数の和＝1），位置ベクトルと線分比・距離の計算。

---

## 数学 コース2 第II問 (後半)：ベクトルの内積と内接円・線分長の決定

**【題目大意】**
前半の結果を用いて，内積 $\overrightarrow{OB} \cdot \overrightarrow{OC}$ を求め，線分 BC および線分 BD の長さを求める。

**【公式正解】**
正解：
$\text{JK} = 13$
$\text{LM} = 82$
$\text{NO} = 36$
$\text{PQRS} = -114$
$\text{TUV} = 362$
$\text{WX} = 62$

**【詳細推導・解答プロセス】**
1. **$BD$ と $BC$ の比**：
$k = -\frac{1}{2}$ を代入すると：
$$\overrightarrow{OD} = -\frac{4}{3}\left(-\frac{1}{2}\right)\overrightarrow{OB} - \frac{2}{3}\left(-\frac{1}{2}\right)\overrightarrow{OC} = \frac{2}{3}\overrightarrow{OB} + \frac{1}{3}\overrightarrow{OC}$$
これは点 D が線分 BC を $1 : 2$ に内分していることを示す。
したがって：
$$BD = \frac{1}{3} BC$$
これより $\text{J} = 1, \text{K} = 3$（$\text{JK} = 13$）である。

2. **$BC^2$ と内積の関係**：
$\overrightarrow{BC} = \overrightarrow{OC} - \overrightarrow{OB}$ より：
$$BC^2 = |\overrightarrow{OC} - \overrightarrow{OB}|^2 = |\overrightarrow{OC}|^2 + |\overrightarrow{OB}|^2 - 2\overrightarrow{OB} \cdot \overrightarrow{OC}$$
点 B, C は半径 2 の円周上にあるため，$|\overrightarrow{OB}| = |\overrightarrow{OC}| = 2$ である。
したがって：
$$BC^2 = 2^2 + 2^2 - 2\overrightarrow{OB} \cdot \overrightarrow{OC} = 8 - 2\overrightarrow{OB} \cdot \overrightarrow{OC}$$
これより $\text{L} = 8, \text{M} = 2$（$\text{LM} = 82$）である。

3. **内積 $\overrightarrow{OB} \cdot \overrightarrow{OC}$ の計算**：
条件式 $\textcircled{1}$ より：
$$4\overrightarrow{OB} + 2\overrightarrow{OC} = -3\overrightarrow{OA}$$
両辺の大きさの 2 乗をとると：
$$|4\overrightarrow{OB} + 2\overrightarrow{OC}|^2 = |-3\overrightarrow{OA}|^2 = 9 |\overrightarrow{OA}|^2 = 9 \times 2^2 = 36$$
これより $\text{NO} = 36$ である。
左辺を展開すると：
$$16|\overrightarrow{OB}|^2 + 16\overrightarrow{OB} \cdot \overrightarrow{OC} + 4|\overrightarrow{OC}|^2 = 36$$
$$16(4) + 16\overrightarrow{OB} \cdot \overrightarrow{OC} + 4(4) = 36$$
$$64 + 16\overrightarrow{OB} \cdot \overrightarrow{OC} + 16 = 36$$
$$80 + 16\overrightarrow{OB} \cdot \overrightarrow{OC} = 36 \implies 16\overrightarrow{OB} \cdot \overrightarrow{OC} = -44$$
$$\overrightarrow{OB} \cdot \overrightarrow{OC} = -\frac{44}{16} = -\frac{11}{4}$$
したがって，$\text{PQR} = -11, \text{S} = 4$（$\text{PQRS} = -114$）である。

4. **線分 BC および BD の長さの算出**：
$$BC^2 = 8 - 2\left(-\frac{11}{4}\right) = 8 + \frac{11}{2} = \frac{27}{2}$$
$$BC = \sqrt{\frac{27}{2}} = \frac{3\sqrt{3}}{\sqrt{2}} = \frac{3\sqrt{6}}{2}$$
これより $\text{T} = 3, \text{U} = 6, \text{V} = 2$（$\text{TUV} = 362$）である。
したがって，線分 BD の長さは：
$$BD = \frac{1}{3} BC = \frac{1}{3} \times \frac{3\sqrt{6}}{2} = \frac{\sqrt{6}}{2}$$
これより $\text{W} = 6, \text{X} = 2$（$\text{WX} = 62$）である。

**【考査考点】**
内積の定義と性質，ベクトルの大きさの2乗展開，外接円の半径と幾何学的線分長の定量的計算。

---

## 数学 コース2 第III問 (前半)：対数方程式の円の方程式への変形

**【題目大意】**
正の数 $x, y$ が $(\log_2 x)^2 + (\log_2 y)^2 = \log_2 \frac{8x^2}{y^2}$ $\cdots\textcircled{1}$ を満たす。
$X = \log_2 x, Y = \log_2 y$ とおくとき，方程式を変形して円の方程式 $(X - D)^2 + (Y + E)^2 = F$ の形に表す。

**【公式正解】**
正解：
$\text{ABC} = 223$
$\text{DEF} = 115$

**【詳細推導・解答プロセス】**
1. **右辺の対数変形**：
対数の基本性質 $\log_a \frac{M}{N} = \log_a M - \log_a N$ および $\log_a M^p = p\log_a M$ を用いる：
$$\log_2 \frac{8x^2}{y^2} = \log_2 8 + \log_2 x^2 - \log_2 y^2 = 3 + 2\log_2 x - 2\log_2 y$$
整理すると：
$$\log_2 \frac{8x^2}{y^2} = 2\log_2 x - 2\log_2 y + 3$$
したがって，$\text{A} = 2, \text{B} = 2, \text{C} = 3$（$\text{ABC} = 223$）である。

2. **円の方程式への変形**：
$X = \log_2 x, Y = \log_2 y$ を与式 $\textcircled{1}$ に代入する：
$$X^2 + Y^2 = 2X - 2Y + 3$$
すべての項を左辺に移項して整理する：
$$X^2 - 2X + Y^2 + 2Y = 3$$
平方完成を行う：
$$(X - 1)^2 - 1 + (Y + 1)^2 - 1 = 3$$
$$(X - 1)^2 + (Y + 1)^2 = 5$$
したがって，$\text{D} = 1, \text{E} = 1, \text{F} = 5$（$\text{DEF} = 115$）である。

これは $XY$ 平面において，中心 $(1, -1)$，半径 $\sqrt{5}$ の円を表す。

**【考査考点】**
対数の演算公式，対数変数変換による非線形方程式の幾何学的表現（円の方程式）への帰着。

---

## 数学 コース2 第III問 (後半)：線形計画法（円と直線の接点条件）による xy^2 の最大化

**【題目大意】**
$\log_2 xy^2 = k$ とおくとき，$k$ の最大値，および $xy^2$ の最大値と，そのときの $x, y$ の値を求める。

**【公式正解】**
正解：
$\text{G} = 2$
$\text{H} = 4$
$\text{IJ} = 16$
$\text{K} = 4$
$\text{L} = 2$

**【詳細推導・解答プロセス】**
1. **直線の方程式**：
$\log_2 xy^2 = \log_2 x + 2\log_2 y = X + 2Y$ であるから：
$$k = X + 2Y \implies X + 2Y - k = 0$$
したがって $\text{G} = 2$ である。

2. **円と直線の共有点条件（接点における最大値）**：
円 $(X - 1)^2 + (Y + 1)^2 = 5$ の中心 $(1, -1)$ と直線 $X + 2Y - k = 0$ の距離を $d$ とする。
点と直線の距離公式より：
$$d = \frac{|1 \cdot 1 + 2(-1) - k|}{\sqrt{1^2 + 2^2}} = \frac{|1 - 2 - k|}{\sqrt{5}} = \frac{|-k - 1|}{\sqrt{5}} = \frac{|k + 1|}{\sqrt{5}}$$
直線が円と共有点をもつ条件は $d \leq \sqrt{5}$ である：
$$\frac{|k + 1|}{\sqrt{5}} \leq \sqrt{5} \implies |k + 1| \leq 5$$
$$-5 \leq k + 1 \leq 5 \implies -6 \leq k \leq 4$$
したがって，$k$ の最大値は：
$$k = 4$$
これより $\text{H} = 4$ である。
このとき：
$$xy^2 = 2^k = 2^4 = 16$$
これより $\text{IJ} = 16$ である。

3. **そのときの $x, y$ の値**：
$k = 4$ のとき，直線は円と接する。
直線の法線ベクトルは $\vec{n} = (1, 2)$ であるから，中心 $(1, -1)$ から半径 $\sqrt{5}$ だけ法線方向に進んだ接点の座標 $(X, Y)$ は：
$$(X, Y) = (1, -1) + \frac{\sqrt{5}}{\sqrt{1^2+2^2}}(1, 2) = (1, -1) + (1, 2) = (2, 1)$$
（確認：$2 + 2(1) = 4 = k$，$(2-1)^2 + (1+1)^2 = 1 + 4 = 5$ で円周上にある）
したがって：
- $X = \log_2 x = 2 \implies x = 2^2 = 4 \implies \text{K} = 4$
- $Y = \log_2 y = 1 \implies y = 2^1 = 2 \implies \text{L} = 2$

**【考査考点】**
線形計画法（領域と境界線の幾何学的解析），点と直線の距離公式，対数関数の最大・最小問題。

---

## 数学 コース2 第IV問 [1]：三角関数の導関数の因数分解と区間内の最大・最小値

**【題目大意】**
$a$ を定数とする。関数 $f(x) = 2\sin^3 x + a\sin 2x + \frac{9}{2}\cos 2x - 9\cos x - 2ax + 6$ が $x = \frac{\pi}{3}$ で極値をもつ。
(1) $a$ の値を求め，導関数 $f'(x)$ を因数分解する。
(2) 区間 $0 \leq x \leq \frac{\pi}{2}$ における最大値・最小値をとる $x$ の値を求める。

**【公式正解】**
正解：
$\text{AB} = 34$
$\text{CDE} = 323$
$\text{F} = 0$
$\text{G} = 3$

**【詳細推導・解答プロセス】**
1. **(1) 導関数 $f'(x)$ の計算と $a$ の決定**：
各項を $x$ で微分する：
- $(2\sin^3 x)' = 6\sin^2 x \cos x$
- $(a\sin 2x)' = 2a\cos 2x$
- \left(\frac{9}{2}\cos 2x\right)' = -9\sin 2x = -18\sin x \cos x$
- $(-9\cos x)' = 9\sin x$
- $(-2ax + 6)' = -2a$
したがって：
$$f'(x) = 6\sin^2 x \cos x + 2a\cos 2x - 9\sin 2x + 9\sin x - 2a$$
$x = \frac{\pi}{3}$ で極値をもつため，$f'\left(\frac{\pi}{3}\right) = 0$ である。
$\sin\frac{\pi}{3} = \frac{\sqrt{3}}{2},\; \cos\frac{\pi}{3} = \frac{1}{2},\; \sin\frac{2\pi}{3} = \frac{\sqrt{3}}{2},\; \cos\frac{2\pi}{3} = -\frac{1}{2}$ を代入すると：
$$f'\left(\frac{\pi}{3}\right) = 6\left(\frac{3}{4}\right)\left(\frac{1}{2}\right) + 2a\left(-\frac{1}{2}\right) - 9\left(\frac{\sqrt{3}}{2}\right) + 9\left(\frac{\sqrt{3}}{2}\right) - 2a = 0$$
$$\frac{9}{4} - a - 2a = 0 \implies 3a = \frac{9}{4} \implies a = \frac{3}{4}$$
したがって，$\text{A} = 3, \text{B} = 4$（$\text{AB} = 34$）である。

2. **$f'(x)$ の因数分解**：
$a = \frac{3}{4}$ を代入し，$\cos 2x = 1 - 2\sin^2 x$ を用いると：
$$2a\cos 2x - 2a = 2a(\cos 2x - 1) = \frac{3}{2}(-2\sin^2 x) = -3\sin^2 x$$
また，$-9\sin 2x = -18\sin x \cos x$ であるから：
$$f'(x) = 6\sin^2 x \cos x - 3\sin^2 x - 18\sin x \cos x + 9\sin x$$
$$f'(x) = 3\sin^2 x (2\cos x - 1) - 9\sin x (2\cos x - 1)$$
$$f'(x) = 3\sin x (2\cos x - 1)(\sin x - 3)$$
したがって，$\text{C} = 3, \text{D} = 2, \text{E} = 3$（$\text{CDE} = 323$）である。

3. **(2) 区間 $[0, \pi/2]$ における最大・最小値の判定**：
区間 $0 < x < \frac{\pi}{2}$ において各因数の符号を調べる：
- $3\sin x > 0$
- $\sin x \leq 1$ であるから，常に $\sin x - 3 < 0$
- $2\cos x - 1$ の符号：
  - $0 < x < \frac{\pi}{3}$ のとき，$\cos x > \frac{1}{2} \implies 2\cos x - 1 > 0$
    このとき $f'(x) = (+) \cdot (+) \cdot (-) < 0$（単調減少）
  - $\frac{\pi}{3} < x < \frac{\pi}{2}$ のとき，$\cos x < \frac{1}{2} \implies 2\cos x - 1 < 0$
    このとき $f'(x) = (+) \cdot (-) \cdot (-) > 0$（単調増加）
したがって，増減表より：
- 最小値は $x = \frac{\pi}{3}$（選択肢 $\textcircled{3}$）でとる $\implies \text{G} = 3$。
- 最大値の候補は端点 $x = 0$ または $x = \frac{\pi}{2}$ である：
  $$f(0) = 0 + 0 + \frac{9}{2}(1) - 9(1) - 0 + 6 = \frac{3}{2} = 1.5$$
  $$f\left(\frac{\pi}{2}\right) = 2(1) + 0 + \frac{9}{2}(-1) - 0 - 2\left(\frac{3}{4}\right)\left(\frac{\pi}{2}\right) + 6 = 8 - 4.5 - \frac{3\pi}{4} = 3.5 - 0.75\pi \approx 3.5 - 2.356 = 1.144$$
  $f(0) > f(\pi/2)$ であるから，最大値は $x = 0$（選択肢 $\textcircled{0}$）でとる $\implies \text{F} = 0$。

**【考査考点】**
三角関数の導関数の計算，極値条件による未定係数の決定，因数分解と符号解析，閉区間における増減表と端点比較。

---

## 数学 コース2 第IV問 [2]：定積分漸化式・級数の和およびはさみうちの原理による極限

**【題目大意】**
数列 $\{a_n\}$ を $a_n = \int_0^{\frac{1}{4}} x^n e^{-x} dx$ で定める。
(1) $a_1$ および $a_{n+1}$ の漸化式を求め，$\sum_{k=1}^n ka_k$ の和の式を導く。
(2) 不等式評価によって $\lim_{n \to \infty} a_n$ を求め，$\lim_{n \to \infty} \sum_{k=1}^n ka_k$ の値を求める。

**【公式正解】**
正解：
$\text{HIJKL} = 54-14$
$\text{MNO} = 141$
$\text{PQRST} = 11214$
$\text{U} = 1$
$\text{V} = 4$
$\text{W} = 0$
$\text{XY} = 43$

**【詳細推導・解答プロセス】**
1. **$a_1$ の計算（部分積分法）**：
$$a_1 = \int_0^{\frac{1}{4}} x e^{-x} dx = \left[-x e^{-x}\right]_0^{\frac{1}{4}} + \int_0^{\frac{1}{4}} e^{-x} dx = -\frac{1}{4}e^{-\frac{1}{4}} + \left[-e^{-x}\right]_0^{\frac{1}{4}}$$
$$a_1 = -\frac{1}{4}e^{-\frac{1}{4}} - e^{-\frac{1}{4}} + 1 = -\frac{5}{4}e^{-\frac{1}{4}} + 1$$
したがって，$\text{H} = 5, \text{I} = 4, \text{JK} = -1, \text{L} = 4$（$\text{HIJKL} = 54-14$）である。

2. **漸化式の導出**：
$$a_{n+1} = \int_0^{\frac{1}{4}} x^{n+1} e^{-x} dx = \left[-x^{n+1} e^{-x}\right]_0^{\frac{1}{4}} + (n+1)\int_0^{\frac{1}{4}} x^n e^{-x} dx$$
$$a_{n+1} = -\left(\frac{1}{4}\right)^{n+1} e^{-\frac{1}{4}} + (n+1)a_n$$
したがって，$\text{M} = 1, \text{N} = 4, \text{O} = 1$（$\text{MNO} = 141$）である。

3. **和 $\sum_{k=1}^n ka_k$ の計算**：
漸化式を変形すると：
$$ka_k = a_{k+1} - a_k + \left(\frac{1}{4}\right)^{k+1} e^{-\frac{1}{4}}$$
$k = 1$ から $n$ までの総和をとる：
$$\sum_{k=1}^n ka_k = \sum_{k=1}^n (a_{k+1} - a_k) + e^{-\frac{1}{4}} \sum_{k=1}^n \left(\frac{1}{4}\right)^{k+1}$$
望遠和より $\sum_{k=1}^n (a_{k+1} - a_k) = a_{n+1} - a_1$ である。
幾何級数の和は：
$$\sum_{k=1}^n \left(\frac{1}{4}\right)^{k+1} = \frac{1}{16} \frac{1 - (1/4)^n}{1 - 1/4} = \frac{1}{16} \cdot \frac{4}{3} \left\{1 - \left(\frac{1}{4}\right)^n\right\} = \frac{1}{12}\left\{1 - \left(\frac{1}{4}\right)^n\right\}$$
したがって：
$$\sum_{k=1}^n ka_k = a_{n+1} - a_1 + \frac{1}{12} e^{-\frac{1}{4}} \left\{1 - \left(\frac{1}{4}\right)^n\right\}$$
これより $\text{P} = 1, \text{QR} = 12, \text{S} = 1, \text{T} = 4$（$\text{PQRST} = 11214$）である。

4. **極限の計算**：
$0 \leq x$ において $0 < e^{-x} \leq 1$（$\text{U} = 1$）であるから：
$$0 < a_n < \int_0^{\frac{1}{4}} 1 \cdot x^n dx = \left[\frac{x^{n+1}}{n+1}\right]_0^{\frac{1}{4}} = \frac{1}{(n+1)4^{n+1}}$$
これより $\text{V} = 4$ である。
$n \to \infty$ のとき $\frac{1}{(n+1)4^{n+1}} \to 0$ であるから，はさみうちの原理より：
$$\lim_{n \to \infty} a_n = 0$$
これより $\text{W} = 0$ である。
したがって：
$$\lim_{n \to \infty} \sum_{k=1}^n ka_k = 0 - a_1 + \frac{1}{12} e^{-\frac{1}{4}} (1 - 0)$$
ここで $a_1 = -\frac{5}{4}e^{-\frac{1}{4}} + 1$ を代入すると：
$$\lim_{n \to \infty} \sum_{k=1}^n ka_k = -\left(-\frac{5}{4}e^{-\frac{1}{4}} + 1\right) + \frac{1}{12}e^{-\frac{1}{4}} = \left(\frac{5}{4} + \frac{1}{12}\right)e^{-\frac{1}{4}} - 1 = \frac{16}{12}e^{-\frac{1}{4}} - 1 = \frac{4}{3}e^{-\frac{1}{4}} - 1$$
したがって，$\text{X} = 4, \text{Y} = 3$（$\text{XY} = 43$）である。

**【考査考点】**
部分積分法による定積分漸化式，望遠和・等比級数の和，関数の不等式評価によるはさみうちの原理，無限級数の収束値計算。

---

