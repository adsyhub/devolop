# 2013-1 EJU 数学 コース2 詳解

## 数学 コース2 第I問 [1]：2次関数の決定と指定区間における単調増加条件

**【題目大意】**
$x$ の2次関数 $y = ax^2 + bx + c$ が，条件【*】「$x = -1$ で $y = -8$，$x = 3$ で $y = 16$ であり，区間 $-1 \le x \le 3$ において $x$ の値が増加すると共に $y$ の値も増加する」を満たすとき，$a, b, c$ の関係式および $a$ のとり得る範囲を求める。

**【公式正解】**
- $b = \boxed{\text{AB}} a + \boxed{\text{C}} \implies b = -2a + 6$ （$\text{ABC} = -26$）
- $c = \boxed{\text{DE}} a - \boxed{\text{F}} \implies c = -3a - 2$ （$\text{DEF} = -32$）
- 軸の方程式：$x = \boxed{\text{G}} - \frac{\boxed{\text{H}}}{a} \implies x = 1 - \frac{3}{a}$ （$\text{GH} = 13$）
- $a$ の範囲：$0 < a \le \frac{\boxed{\text{I}}}{\boxed{\text{J}}} \implies 0 < a \le \frac{3}{2}$ （$\text{IJ} = 32$） または $\frac{\boxed{\text{KL}}}{\boxed{\text{M}}} \le a < 0 \implies -\frac{3}{2} \le a < 0$ （$\text{KLM} = -32$）

**【詳細推導・解答プロセス】**
1. **2点を通る条件からの $b, c$ の表式**：
$y = ax^2 + bx + c$ に対し：
- $x = -1$ のとき：$a(-1)^2 + b(-1) + c = -8 \implies a - b + c = -8 \quad \textcircled{A}$
- $x = 3$ のとき：$a(3)^2 + b(3) + c = 16 \implies 9a + 3b + c = 16 \quad \textcircled{B}$
$\textcircled{B} - \textcircled{A}$ より：
$$8a + 4b = 24 \implies 2a + b = 6 \implies b = -2a + 6$$
よって，$\boxed{\text{AB}} = -2, \; \boxed{\text{C}} = 6$（$\text{ABC} = -26$）である。

これを $\textcircled{A}$ に代入すると：
$$c = -8 - a + b = -8 - a + (-2a + 6) = -3a - 2$$
形式 $c = \boxed{\text{DE}} a - \boxed{\text{F}}$ より：
$$\boxed{\text{DE}} = -3, \; \boxed{\text{F}} = 2 \implies \text{DEF} = -32$$

2. **放物線の軸の方程式**：
$$y = a\left(x + \frac{b}{2a}\right)^2 + c - \frac{b^2}{4a}$$
軸の方程式は：
$$x = -\frac{b}{2a} = -\frac{-2a + 6}{2a} = 1 - \frac{3}{a}$$
したがって，$\boxed{\text{G}} = 1, \; \boxed{\text{H}} = 3$（$\text{GH} = 13$）である。

3. **区間 $[-1, 3]$ で単調増加する条件**：
- **$a > 0$（下に凸）のとき**：
軸が区間の左端以下にあればよい：
$$\text{軸} \le -1 \implies 1 - \frac{3}{a} \le -1 \implies \frac{3}{a} \ge 2 \implies a \le \frac{3}{2}$$
$a > 0$ と合わせて：$0 < a \le \frac{3}{2}$（$\text{IJ} = 32$）。

- **$a < 0$（上に凸）のとき**：
軸が区間の右端以上にあればよい：
$$\text{軸} \ge 3 \implies 1 - \frac{3}{a} \ge 3 \implies -\frac{3}{a} \ge 2 \implies a \ge -\frac{3}{2}$$
$a < 0$ と合わせて：$-\frac{3}{2} \le a < 0$（$\text{KLM} = -32$）。

**【考査考点】**
2次関数の決定，軸の方程式，閉区間における2次関数の単調性の条件分岐。

---

## 数学 コース2 第I問 [2]：区間の集合演算（共通部分・和集合・補集合）と2次不等式

**【題目大意】**
$a < b < c < d$ に対し，$A = [a, c], B = [b, d]$ とする。$A \cap B = \{x \mid x^2 - 4x + 3 \le 0\}$ が与えられたとき，(1) $A \cup B$ および (2) $A \cap \overline{B}, \overline{A} \cap B$ の条件から $a, b, c, d$ の値を求める。

**【公式正解】**
- (1) $a = -3, b = 1, c = 3, d = 8$ （$\text{NO} = -3, \text{P} = 1, \text{Q} = 3, \text{R} = 8$）
- (2) $a = -6, b = 1, c = 3, d = 6$ （$\text{ST} = -6, \text{U} = 1, \text{V} = 3, \text{W} = 6$）

**【詳細推導・解答プロセス】**
1. **共通部分の同定**：
$$A \cap B = [b, c] = \{x \mid x^2 - 4x + 3 \le 0\} = [1, 3]$$
したがって，直ちに $b = 1, c = 3$ である。

2. **(1) 和集合**：
$$A \cup B = [a, d] = \{x \mid x^2 - 5x - 24 \le 0\} = [-3, 8]$$
したがって，$a = -3, d = 8$ である。
$\boxed{\text{NO}} = -3, \; \boxed{\text{P}} = 1, \; \boxed{\text{Q}} = 3, \; \boxed{\text{R}} = 8$ となる。

3. **(2) 差集合・補集合**：
- $A \cap \overline{B} = [a, b) = [a, 1) = \{x \mid x^2 + 5x - 6 \le 0 \text{ かつ } x \neq 1\} = [-6, 1)$
  したがって，$a = -6$ である。
- $\overline{A} \cap B = (c, d] = (3, d] = \{x \mid x^2 - 9x + 18 \le 0 \text{ かつ } x \neq 3\} = (3, 6]$
  したがって，$d = 6$ である。
$\boxed{\text{ST}} = -6, \; \boxed{\text{U}} = 1, \; \boxed{\text{V}} = 3, \; \boxed{\text{W}} = 6$ となる。

**【考査考点】**
実数直線の区間表現，集合演算（共通部分・和集合・補集合），2次不等式の解。

---

## 数学 コース2 第II問 (1)：単位球面上直交ベクトルと底面三角形の計量

**【題目大意】**
原点 O を中心とする半径 1 の球面上に 3 点 A, B, C があり，$\vec{OA} \cdot \vec{OB} = \vec{OB} \cdot \vec{OC} = \vec{OC} \cdot \vec{OA} = 0$ を満たしている。(1) $\vec{AB} \cdot \vec{AC}, |\vec{AB}|, \cos \angle \text{BAC}$ および三角形 ABC の面積を求める。

**【公式正解】**
- $\vec{AB} \cdot \vec{AC} = \boxed{\text{A}} = 1$
- $|\vec{AB}| = \sqrt{\boxed{\text{B}}} = \sqrt{2}$
- $\cos \angle \text{BAC} = \frac{\boxed{\text{C}}}{\boxed{\text{D}}} = \frac{1}{2}$
- 三角形 ABC の面積：$\frac{\sqrt{\boxed{\text{E}}}}{\boxed{\text{F}}} = \frac{\sqrt{3}}{2}$

**【詳細推導・解答プロセス】**
条件より，$\vec{OA}, \vec{OB}, \vec{OC}$ は互いに直交する単位ベクトルである：
$$|\vec{OA}| = |\vec{OB}| = |\vec{OC}| = 1, \quad \vec{OA} \cdot \vec{OB} = \vec{OB} \cdot \vec{OC} = \vec{OC} \cdot \vec{OA} = 0$$

1. **$\vec{AB} \cdot \vec{AC}$ の計算**：
$$\vec{AB} = \vec{OB} - \vec{OA}, \quad \vec{AC} = \vec{OC} - \vec{OA}$$
$$\vec{AB} \cdot \vec{AC} = (\vec{OB} - \vec{OA}) \cdot (\vec{OC} - \vec{OA}) = \vec{OB} \cdot \vec{OC} - \vec{OB} \cdot \vec{OA} - \vec{OA} \cdot \vec{OC} + |\vec{OA}|^2$$
直交性と単位ベクトルより：
$$\vec{AB} \cdot \vec{AC} = 0 - 0 - 0 + 1^2 = 1$$
したがって，$\boxed{\text{A}} = 1$ である。

2. **$|\vec{AB}|$ の計算**：
$$|\vec{AB}|^2 = |\vec{OB} - \vec{OA}|^2 = |\vec{OB}|^2 - 2\vec{OA} \cdot \vec{OB} + |\vec{OA}|^2 = 1 - 0 + 1 = 2$$
$$|\vec{AB}| = \sqrt{2}$$
同様に，対称性より $|\vec{AC}| = |\vec{BC}| = \sqrt{2}$ である。
したがって，$\boxed{\text{B}} = 2$ である。

3. **$\cos \angle \text{BAC}$ の計算**：
$$\cos \angle \text{BAC} = \frac{\vec{AB} \cdot \vec{AC}}{|\vec{AB}||\vec{AC}|} = \frac{1}{\sqrt{2} \times \sqrt{2}} = \frac{1}{2}$$
（これにより $\angle \text{BAC} = 60^\circ$，すなわち $\triangle \text{ABC}$ は 1 辺 $\sqrt{2}$ の正三角形である）。
したがって，$\boxed{\text{C}} = 1, \; \boxed{\text{D}} = 2$ である。

4. **三角形 ABC の面積**：
$$\sin \angle \text{BAC} = \sin 60^\circ = \frac{\sqrt{3}}{2}$$
$$S_{\triangle \text{ABC}} = \frac{1}{2} |\vec{AB}||\vec{AC}| \sin \angle \text{BAC} = \frac{1}{2} \times \sqrt{2} \times \sqrt{2} \times \frac{\sqrt{3}}{2} = \frac{\sqrt{3}}{2}$$
したがって，$\boxed{\text{E}} = 3, \; \boxed{\text{F}} = 2$ である。

**【考査考点】**
空間ベクトルの内積計算，単位直交基底の性質，三角形の面積公式。

---

## 数学 コース2 第II問 (2)：三角形の重心・球面上の点と四面体の体積

**【題目大意】**
三角形 ABC の重心を G，半直線 OG と球面 S の交点を P とするとき，$\vec{OG}, |\vec{OG}|, |\vec{PG}|, \vec{AG} \cdot \vec{PG}$ および四面体 PABC の体積を求める。

**【公式正解】**
- $\vec{OG} = \frac{\boxed{\text{G}}}{\boxed{\text{H}}}(\vec{OA} + \vec{OB} + \vec{OC}) \implies \frac{1}{3}(\vec{OA} + \vec{OB} + \vec{OC})$ （$\text{GH} = 13$）
- $|\vec{OG}| = \frac{\sqrt{\boxed{\text{I}}}}{\boxed{\text{J}}} = \frac{\sqrt{3}}{3}$ （$\text{IJ} = 33$）
- $|\vec{PG}| = \frac{\boxed{\text{K}} - \sqrt{\boxed{\text{L}}}}{\boxed{\text{M}}} = \frac{3 - \sqrt{3}}{3}$ （$\text{KLM} = 333$）
- $\vec{AG} \cdot \vec{PG} = \boxed{\text{N}} = 0$
- 四面体 PABC の体積：$\frac{\sqrt{\boxed{\text{O}}} - \boxed{\text{P}}}{\boxed{\text{Q}}} = \frac{\sqrt{3} - 1}{6}$ （$\text{OPQ} = 316$）

**【詳細推導・解答プロセス】**
1. **重心ベクトル $\vec{OG}$ とその大きさ**：
重心の定義より：
$$\vec{OG} = \frac{1}{3}\left(\vec{OA} + \vec{OB} + \vec{OC}\right)$$
したがって，$\boxed{\text{G}} = 1, \; \boxed{\text{H}} = 3$ である。
その大きさの2乗は：
$$|\vec{OG}|^2 = \frac{1}{9}|\vec{OA} + \vec{OB} + \vec{OC}|^2 = \frac{1}{9}\left(|\vec{OA}|^2 + |\vec{OB}|^2 + |\vec{OC}|^2 + 2(0 + 0 + 0)\right) = \frac{1}{9}(1 + 1 + 1) = \frac{3}{9} = \frac{1}{3}$$
$$|\vec{OG}| = \frac{1}{\sqrt{3}} = \frac{\sqrt{3}}{3}$$
したがって，$\boxed{\text{I}} = 3, \; \boxed{\text{J}} = 3$ である。

2. **$|\vec{PG}|$ の計算**：
P は半直線 OG 上で球面 S（半径 1）上にあるため，$|\vec{OP}| = 1$ である。
G は線分 OP 上にあるから：
$$|\vec{PG}| = |\vec{OP}| - |\vec{OG}| = 1 - \frac{\sqrt{3}}{3} = \frac{3 - \sqrt{3}}{3}$$
したがって，$\boxed{\text{K}} = 3, \; \boxed{\text{L}} = 3, \; \boxed{\text{M}} = 3$ である。

3. **$\vec{AG} \cdot \vec{PG}$ の計算**：
直線 PG は直線 OG と一致する。
ベクトル $\vec{OG}$ と平面 ABC 上の任意のベクトル（例えば $\vec{AB}$）の内積を調べると：
$$\vec{OG} \cdot \vec{AB} = \frac{1}{3}(\vec{OA} + \vec{OB} + \vec{OC}) \cdot (\vec{OB} - \vec{OA}) = \frac{1}{3}(|\vec{OB}|^2 - |\vec{OA}|^2) = \frac{1}{3}(1 - 1) = 0$$
同様に $\vec{OG} \cdot \vec{AC} = 0$ である。
すなわち，直線 OG は平面 ABC の法線ベクトルである。
$\vec{AG}$ は平面 ABC 上のベクトルであるから，法線方向のベクトル $\vec{PG}$ と直交する：
$$\vec{AG} \cdot \vec{PG} = 0$$
したがって，$\boxed{\text{N}} = 0$ である。

4. **四面体 PABC の体積**：
線分 PG は底面 $\triangle \text{ABC}$ に垂直であるから，PG の長さは四面体 PABC の頂点 P から底面 $\triangle \text{ABC}$ に下ろした高さそのものである。
したがって，体積 $V$ は：
$$V = \frac{1}{3} \times S_{\triangle \text{ABC}} \times |\vec{PG}| = \frac{1}{3} \times \frac{\sqrt{3}}{2} \times \frac{3 - \sqrt{3}}{3} = \frac{\sqrt{3}(3 - \sqrt{3})}{18} = \frac{3\sqrt{3} - 3}{18} = \frac{\sqrt{3} - 1}{6}$$
問題文の形式 $\frac{\sqrt{\boxed{\text{O}}} - \boxed{\text{P}}}{\boxed{\text{Q}}}$ より：
$$\boxed{\text{O}} = 3, \; \boxed{\text{P}} = 1, \; \boxed{\text{Q}} = 6$$

**【考査考点】**
空間幾何における重心と法線ベクトルの関係，内積の直交判定，錐体の体積計算。

---

## 数学 コース2 第III問 (1)：楕円上の点の媒介変数表示と三角関数の合成による最大値

**【題目大意】**
実数 $x, y$ が $\frac{x^2}{2} + \frac{y^2}{4} = 1, x \ge 0, y \ge 0$ を満たすとき，$P = x^2 + xy + y^2$ の最大値を求める。

**【公式正解】**
- $y = \boxed{\text{A}} \sin\theta \implies 2\sin\theta$ （$\text{A} = 2$）
- $P = \sqrt{\boxed{\text{B}}} \sin 2\theta - \cos 2\theta + \boxed{\text{C}} \implies \sqrt{2}\sin 2\theta - \cos 2\theta + 3$ （$\text{BC} = 23$）
- $P = \sqrt{\boxed{\text{D}}} \sin(2\theta - \alpha) + \boxed{\text{E}} \implies \sqrt{3}\sin(2\theta - \alpha) + 3$ （$\text{DE} = 33$）
- $\sin\alpha = \frac{\sqrt{\boxed{\text{F}}}}{\boxed{\text{G}}} = \frac{\sqrt{3}}{3}$ （$\text{FG} = 33$），$\cos\alpha = \frac{\sqrt{\boxed{\text{H}}}}{\boxed{\text{I}}} = \frac{\sqrt{6}}{3}$ （$\text{HI} = 63$）
- $P$ の最大値：$\sqrt{\boxed{\text{J}}} + \boxed{\text{K}} = \sqrt{3} + 3$ （$\text{JK} = 33$）

**【詳細推導・解答プロセス】**
1. **媒介変数表示**：
$\frac{x^2}{2} + \frac{y^2}{4} = 1$ において，$x = \sqrt{2}\cos\theta$（$0 \le \theta \le \frac{\pi}{2}$）とおくと：
$$\cos^2\theta + \frac{y^2}{4} = 1 \implies \frac{y^2}{4} = 1 - \cos^2\theta = \sin^2\theta$$
$y \ge 0$ より：
$$y = 2\sin\theta$$
したがって，$\boxed{\text{A}} = 2$ である。

2. **2倍角の公式による整理**：
$$P = x^2 + xy + y^2 = (\sqrt{2}\cos\theta)^2 + (\sqrt{2}\cos\theta)(2\sin\theta) + (2\sin\theta)^2$$
$$P = 2\cos^2\theta + 2\sqrt{2}\sin\theta\cos\theta + 4\sin^2\theta$$
半角・2倍角の公式 $\cos^2\theta = \frac{1 + \cos 2\theta}{2}, \sin^2\theta = \frac{1 - \cos 2\theta}{2}, 2\sin\theta\cos\theta = \sin 2\theta$ を用いると：
$$P = (1 + \cos 2\theta) + \sqrt{2}\sin 2\theta + 2(1 - \cos 2\theta)$$
$$P = \sqrt{2}\sin 2\theta - \cos 2\theta + 3$$
したがって，$\boxed{\text{B}} = 2, \; \boxed{\text{C}} = 3$（$\text{BC} = 23$）である。

3. **三角関数の合成**：
係数 $\sqrt{2}$ と $-1$ を合成する：
$$\sqrt{(\sqrt{2})^2 + (-1)^2} = \sqrt{2 + 1} = \sqrt{3}$$
$$P = \sqrt{3}\left(\sin 2\theta \cdot \frac{\sqrt{2}}{\sqrt{3}} - \cos 2\theta \cdot \frac{1}{\sqrt{3}}\right) + 3$$
加法定理 $\sin(2\theta - \alpha) = \sin 2\theta \cos\alpha - \cos 2\theta \sin\alpha$ と比較すると：
$$P = \sqrt{3}\sin(2\theta - \alpha) + 3$$
ここで $\alpha$ は：
$$\cos\alpha = \frac{\sqrt{2}}{\sqrt{3}} = \frac{\sqrt{6}}{3}, \quad \sin\alpha = \frac{1}{\sqrt{3}} = \frac{\sqrt{3}}{3} \quad \left(0 < \alpha < \frac{\pi}{2}\right)$$
したがって，$\boxed{\text{D}} = 3, \; \boxed{\text{E}} = 3$（$\text{DE} = 33$），$\boxed{\text{F}} = 3, \; \boxed{\text{G}} = 3$（$\text{FG} = 33$），$\boxed{\text{H}} = 6, \; \boxed{\text{I}} = 3$（$\text{HI} = 63$）である。

4. **最大値の決定**：
$0 \le \theta \le \frac{\pi}{2}$ より $0 \le 2\theta \le \pi$ であるから：
$$-\alpha \le 2\theta - \alpha \le \pi - \alpha$$
$0 < \alpha < \frac{\pi}{2}$ であるため，角 $\frac{\pi}{2}$ はこの区間内に含まれる。
したがって，$\sin(2\theta - \alpha)$ は最大値 $1$ をとることができる。
よって，$P$ の最大値は：
$$P_{\text{max}} = \sqrt{3}(1) + 3 = \sqrt{3} + 3$$
これより，$\boxed{\text{J}} = 3, \; \boxed{\text{K}} = 3$（$\text{JK} = 33$）である。

**【考査考点】**
2次曲線の媒介変数表示，2倍角の公式，三角関数の合成と変域における最大値決定。

---

## 数学 コース2 第III問 (2)：最大値を与える偏角における三角比の決定

**【題目大意】**
$P$ の値が最大になるときの $\theta$ を $\theta_0$ とするとき，$2\theta_0$ の表式および $\sin 2\theta_0, \cos 2\theta_0$ の値を求める。

**【公式正解】**
- $2\theta_0 = \alpha + \frac{\pi}{\boxed{\text{L}}} \implies \alpha + \frac{\pi}{2}$ （$\text{L} = 2$）
- $\sin 2\theta_0 = \frac{\sqrt{\boxed{\text{M}}}}{\boxed{\text{N}}} = \frac{\sqrt{6}}{3}$ （$\text{MN} = 63$）
- $\cos 2\theta_0 = -\frac{\sqrt{\boxed{\text{O}}}}{\boxed{\text{P}}} = -\frac{\sqrt{3}}{3}$ （$\text{OP} = 33$）

**【詳細推導・解答プロセス】**
1. **$2\theta_0$ の導出**：
$P = \sqrt{3}\sin(2\theta - \alpha) + 3$ が最大値をとるのは，正弦関数の偏角が $\frac{\pi}{2}$ となるときである：
$$2\theta_0 - \alpha = \frac{\pi}{2} \implies 2\theta_0 = \alpha + \frac{\pi}{2}$$
問題文の形式 $2\theta_0 = \alpha + \frac{\pi}{\boxed{\text{L}}}$ より：
$$\boxed{\text{L}} = 2$$

2. **$\sin 2\theta_0$ および $\cos 2\theta_0$ の計算**：
三角関数の加法定理（または位相シフトの公式）を用いる：
- $\sin 2\theta_0 = \sin\left(\alpha + \frac{\pi}{2}\right) = \cos\alpha$
  前半で求めた $\cos\alpha = \frac{\sqrt{6}}{3}$ を代入すると：
  $$\sin 2\theta_0 = \frac{\sqrt{6}}{3}$$
  したがって，$\boxed{\text{M}} = 6, \; \boxed{\text{N}} = 3$（$\text{MN} = 63$）である。

- $\cos 2\theta_0 = \cos\left(\alpha + \frac{\pi}{2}\right) = -\sin\alpha$
  前半で求めた $\sin\alpha = \frac{\sqrt{3}}{3}$ を代入すると：
  $$\cos 2\theta_0 = -\frac{\sqrt{3}}{3}$$
  問題文の形式 $-\frac{\sqrt{\boxed{\text{O}}}}{\boxed{\text{P}}}$ より：
  $$\boxed{\text{O}} = 3, \; \boxed{\text{P}} = 3 \implies \text{OP} = 33$$

**【考査考点】**
三角関数の最大条件と偏角，加法定理および $\frac{\pi}{2}$ シフトの公式。

---

## 数学 コース2 第IV問 [1]：積分の不等式評価による級数の発散証明と区分求積法

**【題目大意】**
数列 $S_n = \sum_{k=1}^n \frac{1}{\sqrt{k}}$ について，(1) 不等式評価による $\lim_{n \to \infty} S_n = \infty$ の証明，および (2) 区分求積法による $\lim_{n \to \infty} \frac{S_{2n} - S_n}{\sqrt{n}}$ の計算を行う。

**【公式正解】**
- (1) $y' = -\frac{\boxed{\text{A}}}{2\sqrt{x}^{\boxed{\text{B}}}} \implies -\frac{1}{2\sqrt{x}^3}$ （$\text{AB} = 13$）
- 関数 $y$ は：$\textcircled{9}$ （単調減少）
- 不等式：$\frac{1}{\sqrt{k}} \; \boxed{\text{D}} \; \int_k^{k+1} \frac{1}{\sqrt{x}} dx \implies >$ （$\text{D} = 7$）
- 和の不等式：$S_n \; \boxed{\text{E}} \; \int_{\boxed{\text{F}}}^{\boxed{\text{G}}} \frac{1}{\sqrt{x}} dx = \boxed{\text{H}}(\sqrt{\boxed{\text{G}}} - 1) \implies S_n > \int_1^{n+1} \frac{1}{\sqrt{x}} dx = 2(\sqrt{n+1} - 1)$ （$\text{E} = 7, \text{FG} = 15, \text{H} = 2$）
- 極限：$\lim_{n \to \infty} S_n = \boxed{\text{I}} \implies \infty$ （$\text{I} = 0$）
- (2) $S_{2n} - S_n = \sum_{k=1}^n \frac{1}{\sqrt{\boxed{\text{J}}}} \implies \frac{1}{\sqrt{n+k}}$ （$\text{J} = 7$）
- 区分求積：$\frac{1}{\boxed{\text{K}}} \sum_{k=1}^n \frac{1}{\sqrt{\boxed{\text{L}} + \frac{k}{n}}} \implies \frac{1}{n} \sum_{k=1}^n \frac{1}{\sqrt{1 + \frac{k}{n}}}$ （$\text{KL} = 41$）
- 定積分：$\int_{\boxed{\text{M}}}^{\boxed{\text{N}}} \frac{1}{\sqrt{1+x}} dx = \int_0^1 \frac{1}{\sqrt{1+x}} dx$ （$\text{MN} = 01$）
- 極限値：$\boxed{\text{O}}(\sqrt{\boxed{\text{P}}} - 1) = 2(\sqrt{2} - 1)$ （$\text{OP} = 22$）

**【詳細推導・解答プロセス】**
1. **(1) 不等式評価と $S_n$ の発散**：
$y = \frac{1}{\sqrt{x}} = x^{-1/2}$ を微分すると：
$$y' = -\frac{1}{2} x^{-3/2} = -\frac{1}{2\sqrt{x^3}} = -\frac{1}{2\sqrt{x}^3}$$
したがって，$\boxed{\text{A}} = 1, \; \boxed{\text{B}} = 3$（$\text{AB} = 13$）である。
$x > 0$ において $y' < 0$ であるから，関数 $y$ は**単調減少**（$\textcircled{9}$，$\boxed{\text{C}} = 9$）である。

区間 $[k, k+1]$ において，$k \le x \le k+1$ より $\frac{1}{\sqrt{k}} \ge \frac{1}{\sqrt{x}}$（等号は $x=k$ のみ）であるから：
$$\int_k^{k+1} \frac{1}{\sqrt{x}} dx < \int_k^{k+1} \frac{1}{\sqrt{k}} dx = \frac{1}{\sqrt{k}}$$
すなわち $\frac{1}{\sqrt{k}} > \int_k^{k+1} \frac{1}{\sqrt{x}} dx$ である（$\textcircled{7}$，$\boxed{\text{D}} = 7$）。

$k = 1$ から $k = n$ まで足し合わせると：
$$S_n = \sum_{k=1}^n \frac{1}{\sqrt{k}} > \sum_{k=1}^n \int_k^{k+1} \frac{1}{\sqrt{x}} dx = \int_1^{n+1} \frac{1}{\sqrt{x}} dx$$
したがって，不等号は $>$（$\textcircled{7}$，$\boxed{\text{E}} = 7$），積分区間は $1$ から $n+1$（$\boxed{\text{F}} = 1, \; \boxed{\text{G}} = n+1 \implies \textcircled{5}$，$\text{FG} = 15$）。
定積分を計算すると：
$$\int_1^{n+1} x^{-1/2} dx = \left[2\sqrt{x}\right]_1^{n+1} = 2\left(\sqrt{n+1} - 1\right)$$
よって $\boxed{\text{H}} = 2$ である。
$n \to \infty$ のとき $2(\sqrt{n+1} - 1) \to \infty$ であるから，追い出しの原理（比較判定法）より：
$$\lim_{n \to \infty} S_n = \infty \quad (\textcircled{0}, \; \boxed{\text{I}} = 0)$$

2. **(2) 区分求積法による極限計算**：
$$S_{2n} - S_n = \sum_{j=n+1}^{2n} \frac{1}{\sqrt{j}}$$
$j = n + k$（$k = 1, 2, \dots, n$）とおくと：
$$S_{2n} - S_n = \sum_{k=1}^n \frac{1}{\sqrt{n+k}}$$
したがって，$\boxed{\text{J}} = n+k$（$\textcircled{7}$）である。

両辺を $\sqrt{n}$ で割ると：
$$\frac{S_{2n} - S_n}{\sqrt{n}} = \sum_{k=1}^n \frac{1}{\sqrt{n}\sqrt{n+k}} = \sum_{k=1}^n \frac{1}{n\sqrt{1 + \frac{k}{n}}} = \frac{1}{n}\sum_{k=1}^n \frac{1}{\sqrt{1 + \frac{k}{n}}}$$
したがって，$\boxed{\text{K}} = n$（$\textcircled{4}$），$\boxed{\text{L}} = 1$（$\textcircled{1}$）より $\text{KL} = 41$ である。

区分求積法の公式 $\lim_{n \to \infty} \frac{1}{n}\sum_{k=1}^n f\left(\frac{k}{n}\right) = \int_0^1 f(x) dx$ より：
$$\lim_{n \to \infty} \frac{S_{2n} - S_n}{\sqrt{n}} = \int_0^1 \frac{1}{\sqrt{1+x}} dx$$
したがって，積分範囲は $0$ から $1$（$\boxed{\text{M}} = 0, \; \boxed{\text{N}} = 1 \implies \text{MN} = 01$）である。

定積分を計算する：
$$\int_0^1 (1+x)^{-1/2} dx = \left[2\sqrt{1+x}\right]_0^1 = 2\left(\sqrt{2} - \sqrt{1}\right) = 2(\sqrt{2} - 1)$$
形式 $\boxed{\text{O}}(\sqrt{\boxed{\text{P}}} - 1)$ より：
$$\boxed{\text{O}} = 2, \; \boxed{\text{P}} = 2 \implies \text{OP} = 22$$

**【考査考点】**
積分の不等式評価を用いた無限級数の発散証明，区分求積法の基本変形と定積分計算。

---

## 数学 コース2 第IV問 [2]：積分方程式・微分方程式の解法とネイピア数の定義による極限

**【題目大意】**
微分可能な関数 $f(x)$ が等式
$$\int_0^x f(t) dt = (1 + e^{-x}) f(x) + 2x - 4\log 2 \quad \textcircled{1}$$
を満たすとき，$f(x)$ を求め，さらに極限値 $\lim_{x \to \infty} f(x)$ を求める。

**【公式正解】**
- $(1 + e^{-x})(\boxed{\text{Q}}) = \boxed{\text{R}} \implies (1 + e^{-x})(f(x) - f'(x)) = 2$ （$\text{Q} = 1, \text{R} = 2$）
- $g'(x) = \frac{\boxed{\text{S}}}{1 + e^{-x}} \implies \frac{-2e^{-x}}{1 + e^{-x}}$ （$\text{S} = 7$）
- $g(x) = \boxed{\text{T}}\log(1 + e^{-x}) + C \implies 2\log(1 + e^{-x}) + C$ （$\text{T} = 2$）
- $C = \boxed{\text{U}} = 0$
- $f(x) = \boxed{\text{V}}\log(1 + e^{-x}) \implies 2e^x \log(1 + e^{-x})$ （$\text{V} = 4$）
- $f(x) = \boxed{\text{W}}\log(1 + t)^{1/t} \implies 2\log(1 + t)^{1/t}$ （$\text{W} = 2$）
- 極限：$\lim_{t \to \boxed{\text{X}}} W\log(1 + t)^{1/t} = \boxed{\text{Y}} \implies \lim_{t \to 0} 2\log(1 + t)^{1/t} = 2$ （$\text{X} = 0, \text{Y} = 2$）

**【詳細推導・解答プロセス】**
1. **等式 $\textcircled{1}$ の微分と変形**：
$$\int_0^x f(t) dt = (1 + e^{-x}) f(x) + 2x - 4\log 2$$
両辺を $x$ で微分する：
$$f(x) = \left(-e^{-x}\right)f(x) + (1 + e^{-x})f'(x) + 2$$
左辺に $e^{-x}f(x)$ を移項すると：
$$(1 + e^{-x})f(x) = (1 + e^{-x})f'(x) + 2$$
$$(1 + e^{-x})\left(f(x) - f'(x)\right) = 2 \quad \textcircled{2}$$
選択肢 $\textcircled{1}$ は $f(x) - f'(x)$ であるから，$\boxed{\text{Q}} = 1, \; \boxed{\text{R}} = 2$ である。

2. **変数変換 $f(x) = e^x g(x)$ による解法**：
積の微分法より：
$$f'(x) = e^x g(x) + e^x g'(x)$$
したがって：
$$f(x) - f'(x) = e^x g(x) - \left(e^x g(x) + e^x g'(x)\right) = -e^x g'(x)$$
これを $\textcircled{2}$ に代入すると：
$$(1 + e^{-x})\left(-e^x g'(x)\right) = 2$$
両辺を $-e^x(1 + e^{-x})$ で割ると：
$$g'(x) = \frac{-2}{e^x(1 + e^{-x})} = \frac{-2e^{-x}}{1 + e^{-x}}$$
選択肢 $\textcircled{7}$ は $-2e^{-x}$ であるから，$\boxed{\text{S}} = 7$ である。

3. **$g(x)$ の積分と積分定数 $C$ の決定**：
$$g(x) = \int \frac{-2e^{-x}}{1 + e^{-x}} dx$$
分子は分母の微分 $(1 + e^{-x})' = -e^{-x}$ の $2$ 倍であるから：
$$g(x) = 2\int \frac{(1 + e^{-x})'}{1 + e^{-x}} dx = 2\log(1 + e^{-x}) + C$$
したがって，$\boxed{\text{T}} = 2$ である。

初期条件として，元の等式 $\textcircled{1}$ に $x = 0$ を代入する：
$$\int_0^0 f(t) dt = 0 = (1 + e^0)f(0) + 0 - 4\log 2 = 2f(0) - 4\log 2$$
$$2f(0) = 4\log 2 \implies f(0) = 2\log 2$$
一方，$f(0) = e^0 g(0) = g(0)$ であるから：
$$g(0) = 2\log(1 + e^0) + C = 2\log 2 + C$$
$$2\log 2 + C = 2\log 2 \implies C = 0$$
したがって，$\boxed{\text{U}} = 0$ である。

これより $g(x) = 2\log(1 + e^{-x})$ となり：
$$f(x) = e^x g(x) = 2e^x \log(1 + e^{-x})$$
選択肢 $\textcircled{4}$ は $2e^x$ であるから，$\boxed{\text{V}} = 4$ である。

4. **$x \to \infty$ における極限値の算出**：
$t = e^{-x}$ とおくと，$e^x = \frac{1}{t}$ である。
$$f(x) = 2 \cdot \frac{1}{t} \log(1 + t) = 2\log(1 + t)^{1/t}$$
したがって，$\boxed{\text{W}} = 2$ である。
$x \to \infty$ のとき $t = e^{-x} \to 0$ であるから：
$$\boxed{\text{X}} = 0$$
自然対数の底（ネイピア数）の定義 $\lim_{t \to 0} (1 + t)^{1/t} = e$ より：
$$\lim_{x \to \infty} f(x) = \lim_{t \to 0} 2\log(1 + t)^{1/t} = 2\log e = 2 \times 1 = 2$$
したがって，$\boxed{\text{Y}} = 2$ である。

**【考査考点】**
微分積分学の基本定理を用いた積分方程式の解法，未知関数の変数変換による微分方程式の解法，ネイピア数 $e$ の定義に基づく極限計算。

---

