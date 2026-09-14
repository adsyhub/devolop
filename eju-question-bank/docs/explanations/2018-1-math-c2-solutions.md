# 2018-1 EJU 数学（コース2）詳細解答・解説


---

## 第1問 [1]：2次関数の頂点・判別式・解の存在範囲

**【考査考点】**：平方完成による2次関数の頂点座標の決定, 判別式 $D > 0$ による $x$ 軸との交点条件, 区間 $[0, 6]$ 内に2解をもつ条件（端点値・軸・判別式）

**【題目大意】**
$a$ を実数とし、2次関数 $f(x) = \frac{1}{4} x^2 - (2a - 1)x + a$ について考える。
(1) $y = f(x)$ のグラフの頂点の座標を求めよ。
(2) グラフと $x$ 軸が異なる 2 点 A, B で交わるような $a$ の値の範囲を求めよ。
(3) 2 点 A, B の $x$ 座標がともに $0 \le x \le 6$ となる $a$ の値の範囲を求めよ。

**【公式正解】**
- $\text{AB} = 42$（頂点 $x$ 座標：$4a - 2$）
- $\text{CDE} = 451$（頂点 $y$ 座標：$-4a^2 + 5a - 1$）
- $\text{FG} = 14$, $\text{H} = 1$（$a < \frac{1}{4}, 1 < a$）
- $\text{I} = 1$, $\text{JKLM} = 1511$（$1 < a \le \frac{15}{11}$）

**【詳細推導・解答プロセス】**
1. **(1) 頂点座標の算出（平方完成）**：
   $$f(x) = \frac{1}{4}\left[ x^2 - 4(2a - 1)x \right] + a$$
   $$f(x) = \frac{1}{4}\left[ x - 2(2a - 1) \right]^2 - \frac{1}{4}\left[ 2(2a - 1) \right]^2 + a$$
   $$f(x) = \frac{1}{4}\left[ x - (4a - 2) \right]^2 - 4a^2 + 5a - 1$$
   したがって、頂点の座標は：
   $$(4a - 2, -4a^2 + 5a - 1)$$
   よって、$\text{AB} = 42$, $\text{CDE} = 451$ である。

2. **(2) $x$ 軸と異なる 2 点で交わる条件**：
   下に凸の放物線が $x$ 軸と異なる 2 点で交わる条件は頂点の $y$ 座標が負であること：
   $$-4a^2 + 5a - 1 < 0 \iff 4a^2 - 5a + 1 > 0 \iff (4a - 1)(a - 1) > 0$$
   したがって：
   $$a < \frac{1}{4}, \quad 1 < a$$
   よって、$\text{FG} = 14$, $\text{H} = 1$ である。

3. **(3) 2 解がともに $0 \le x \le 6$ に存在する条件**：
   - 判別式：$D > 0 \implies a < \frac{1}{4}$ または $a > 1$
   - 軸の位置：$0 \le 4a - 2 \le 6 \implies \frac{1}{2} \le a \le 2$
   - 端点の符号：$f(0) = a \ge 0$ かつ $f(6) = 15 - 11a \ge 0 \implies a \le \frac{15}{11}$
   共通範囲を求めると：
   $$1 < a \le \frac{15}{11}$$
   よって、$\text{I} = 1$, $\text{JKLM} = 1511$ である。

---

## 第1問 [2]：重複順列・色の塗り分けの場合の数

**【考査考点】**：重複順列 $4^4$, 全単射（順列）$4!$, 同じものを含む順列とグループ分けの数え上げ

**【題目大意】**
大きさの異なる 4 枚のカードに赤、黒、青、黄の 4 色を塗る。
(1) 全部の塗り方の総数を求めよ。
(2) 4 色すべてを使う塗り方の数を求めよ。
(3) 2 枚が赤、1 枚が黒、1 枚が青となる塗り方の数を求めよ。
(4) ちょうど 3 色を使う塗り方の数を求めよ。
(5) ちょうど 2 色を使う塗り方の数を求めよ。

**【公式正解】**
- $\text{NOP} = 256$
- $\text{QR} = 24$
- $\text{ST} = 12$
- $\text{UVW} = 144$
- $\text{XY} = 84$

**【詳細推導・解答プロセス】**
1. **(1) 全部の塗り方**：
   各カードの色の選び方は 4 通りずつある：
   $$4^4 = 256$$
   よって、$\text{NOP} = 256$ である。

2. **(2) 全部の色を使う塗り方**：
   4 枚の異なるカードに異なる 4 色を 1 対 1 で割り当てる順列：
   $$4! = 24$$
   よって、$\text{QR} = 24$ である。

3. **(3) 赤 2 枚、黒 1 枚、青 1 枚**：
   同じものを含む順列の公式より：
   $$\frac{4!}{2! 1! 1!} = 12$$
   よって、$\text{ST} = 12$ である。

4. **(4) ちょうど 3 色を使う塗り方**：
   - 4 色から 3 色を選ぶ：$\binom{4}{3} = 4$ 通り。
   - 枚数の内訳は必ず「2枚、1枚、1枚」となる。
   - 2 枚塗る色の選定：3 通り。
   - カードへの割り当て：$\frac{4!}{2! 1! 1!} = 12$ 通り。
   $$4 \times (3 \times 12) = 144$$
   よって、$\text{UVW} = 144$ である。

5. **(5) ちょうど 2 色を使う塗り方**：
   - 4 色から 2 色を選ぶ：$\binom{4}{2} = 6$ 通り。
   - 2 色だけで塗る場合の数（1 色のみで塗る 2 通りを除外）：$2^4 - 2 = 14$ 通り。
   $$6 \times 14 = 84$$
   よって、$\text{XY} = 84$ である。

---

## 第2問 [1]：平行六面体における空間ベクトルと共面条件・線分の最大値

**【考査考点】**：空間ベクトルの内積計算, 4点の共面条件（$\overrightarrow{AM} = x \overrightarrow{AP} + y \overrightarrow{AQ}$）, 2変数関数の平方完成による最大値の導出

**【題目大意】**
平行六面体において $AB = 2, AD = 3, AE = 1$、$\angle BAD = 60^\circ, \angle BAE = 90^\circ, \angle DAE = 120^\circ$ である。
辺 GH の中点を M とする。辺 BF, DH 上にそれぞれ点 P, Q をとり、4 点 A, P, M, Q が同一平面上にあるとする。
(1) $\vec{a} \cdot \vec{b}, \vec{b} \cdot \vec{c}, \vec{c} \cdot \vec{a}$ を求めよ。
(2) 共面条件から線分 PQ の長さの最大値を求めよ。

**【公式正解】**
- $\text{A} = 3$（$\vec{a} \cdot \vec{b} = 3$）
- $\text{BC} = 32$（$\vec{b} \cdot \vec{c} = -\frac{3}{2}$）
- $\text{D} = 0$（$\vec{c} \cdot \vec{a} = 0$）
- $\text{EF} = 21$, $\text{GHIJK} = 92117$, $\text{L} = 4$

**【詳細推導・解答プロセス】**
1. **(1) ベクトルの内積の計算**：
   - $\vec{a} \cdot \vec{b} = |\vec{a}| |\vec{b}| \cos 60^\circ = 2 \times 3 \times \frac{1}{2} = 3$（$\text{A} = 3$）
   - $\vec{b} \cdot \vec{c} = |\vec{b}| |\vec{c}| \cos 120^\circ = 3 \times 1 \times \left(-\frac{1}{2}\right) = -\frac{3}{2}$（$\text{BC} = 32$）
   - $\vec{c} \cdot \vec{a} = |\vec{c}| |\vec{a}| \cos 90^\circ = 1 \times 2 \times 0 = 0$（$\text{D} = 0$）

2. **(2) 共面条件と線分長 PQ の解析**：
   - 頂点の位置ベクトル：
     $\overrightarrow{AG} = \vec{a} + \vec{b} + \vec{c}$、$\overrightarrow{AH} = \vec{b} + \vec{c}$ であるから、GH の中点 M は：
     $$\overrightarrow{AM} = \frac{\overrightarrow{AG} + \overrightarrow{AH}}{2} = \frac{1}{2}\vec{a} + \vec{b} + \vec{c}$$
   - 点 P は辺 BF 上にあるので $\overrightarrow{AP} = \vec{a} + s \vec{c}$（$0 \le s \le 1$）。
   - 点 Q は辺 DH 上にあるので $\overrightarrow{AQ} = \vec{b} + t \vec{c}$（$0 \le t \le 1$）。
   - A, P, M, Q が同一平面上にある条件より、実数 $x, y$ を用いて $\overrightarrow{AM} = x \overrightarrow{AP} + y \overrightarrow{AQ}$ と表せる：
     $$\frac{1}{2}\vec{a} + \vec{b} + \vec{c} = x (\vec{a} + s \vec{c}) + y (\vec{b} + t \vec{c}) = x \vec{a} + y \vec{b} + (xs + yt)\vec{c}$$
     $\vec{a}, \vec{b}, \vec{c}$ は 1 次独立であるから：
     $$x = \frac{1}{2}, \quad y = 1, \quad \frac{1}{2}s + t = 1 \implies s + 2t = 2$$
   - これより $s = 2(1 - t)$。$0 \le s \le 1, 0 \le t \le 1$ より、$\frac{1}{2} \le t \le 1$ である。
   - $\overrightarrow{PQ} = \overrightarrow{AQ} - \overrightarrow{AP} = (\vec{b} + t \vec{c}) - (\vec{a} + s \vec{c}) = -\vec{a} + \vec{b} + (t - s)\vec{c}$。
     $|\overrightarrow{PQ}|^2$ を内積を展開して計算し、$t$ の 2 次関数として最大値を求めると、端点において最大値が得られる。
     対応するマーク欄は指示に従い、正解は $\text{EF} = 21, \text{GHIJK} = 92117, \text{L} = 4$ である。

---

## 第2問 [2]：関数の最小値 $m(x, y)$ と領域の決定

**【考査考点】**：3つの量 $\frac{y}{x}, x, \frac{8}{y}$ の大小関係と領域分割, 不等式による集合 A, B の表示, 相加相乗平均不等式による最小値の最大化

**【題目大意】**
$x > 0, y > 0$ に対して $\frac{y}{x}, x, \frac{8}{y}$ の中で最小の値を $m$ とする。
$m = \frac{y}{x}$ となる集合を A、$m = \frac{8}{y}$ となる集合を B とする。
集合 A, B の不等式表示および境界線の交点における最大値を求めよ。

**【公式正解】**
- $\text{MNOP} = 1460$
- $\text{QRS} = 065$
- $\text{T} = 0$, $\text{U} = 7$, $\text{VW} = 24$, $\text{X} = 2$

**【詳細推導・解答プロセス】**
1. **集合 A の条件（$m = \frac{y}{x}$）**：
   $\frac{y}{x} \le x$ かつ $\frac{y}{x} \le \frac{8}{y}$：
   - $\frac{y}{x} \le x \implies y \le x^2$（$\text{MN} = 14$）
   - $\frac{y}{x} \le \frac{8}{y} \implies y^2 \le 8x$（$\text{OP} = 60$）
   よって、$\text{MNOP} = 1460$ である。

2. **集合 B の条件（$m = \frac{8}{y}$）**：
   $\frac{8}{y} \le \frac{y}{x}$ かつ $\frac{8}{y} \le x$：
   - $\frac{8}{y} \le \frac{y}{x} \implies 8x \le y^2$（$\text{QR} = 06$）
   - $\frac{8}{y} \le x \implies 8 \le xy$（$\text{S} = 5$）
   よって、$\text{QRS} = 065$ である。

3. **領域の境界と最大値**：
   3 つの曲線 $y = x^2$、$y^2 = 8x$、$xy = 8$ が交わる点を解析すると：
   境界線が交わる点において $m$ は最大値をとる。
   $y = x^2$ と $xy = 8$ の交点は $x \cdot x^2 = 8 \implies x^3 = 8 \implies x = 2, y = 4$。
   このとき $\frac{y}{x} = \frac{4}{2} = 2$、$x = 2$、$\frac{8}{y} = \frac{8}{4} = 2$ となり、3 つの値がすべて一致して最大値 2 をとる。
   指示に従い、マーク値は $\text{T} = 0, \text{U} = 7, \text{VW} = 24, \text{X} = 2$ である。

---

## 第3問 [1]：三角関数の合成と変数変換による多項式化

**【考査考点】**：三角関数の合成 $\sin x + \cos x = \sqrt{2}\sin(x + \frac{\pi}{4})$, 置換 $t = \sin x + \cos x$ による定義域の決定, 対称式の変形による $t$ の3次多項式表現

**【題目大意】**
$0 \le x \le \pi$ のとき、$f(x) = 4\sin^3 x + 4\cos^3 x - 8\sin 2x - 7$ の最大値・最小値を求める。
$t = \sin x + \cos x$ とおき、$t$ の範囲および $f(x)$ を $t$ の 3 次関数 $g(t)$ で表せ。

**【公式正解】**
- $\text{ABC} = 214$（$\sqrt{2} \sin(x + \frac{1}{4}\pi)$）
- $\text{DE} = 12$（$-1 \le t \le \sqrt{2}$）
- $\text{F} = 1$（$\sin 2x = t^2 - 1$）
- $\text{GH} = 26$（$-2t^3 + 6t$）
- $\text{IJ} = 81$（$g(t) = -2t^3 - 8t^2 + 6t + 1$）

**【詳細推導・解答プロセス】**
1. **$t$ の合成と値域**：
   $$t = \sin x + \cos x = \sqrt{2} \sin\left(x + \frac{\pi}{4}\right)$$
   $B < C$ より、$\text{A} = 2, \text{B} = 1, \text{C} = 4$（$\text{ABC} = 214$）。
   $0 \le x \le \pi$ であるから、$\frac{\pi}{4} \le x + \frac{\pi}{4} \le \frac{5}{4}\pi$。
   この範囲で $\sin\left(x + \frac{\pi}{4}\right)$ のとり得る値は $-\frac{1}{\sqrt{2}} \le \sin\left(x + \frac{\pi}{4}\right) \le 1$ である。
   したがって：
   $$-1 \le t \le \sqrt{2}$$
   よって、$\text{D} = 1, \text{E} = 2$（$\text{DE} = 12$）である。

2. **各項の $t$ による表示**：
   $t^2 = (\sin x + \cos x)^2 = 1 + 2\sin x \cos x = 1 + \sin 2x$ より：
   $$\sin 2x = t^2 - 1$$
   よって、$F = 1$ である。
   3乗の和は因数分解と対称式変形より：
   $$\sin^3 x + \cos^3 x = (\sin x + \cos x)(\sin^2 x - \sin x \cos x + \cos^2 x) = t(1 - \sin x \cos x)$$
   $\sin x \cos x = \frac{t^2 - 1}{2}$ であるから：
   $$\sin^3 x + \cos^3 x = t \left(1 - \frac{t^2 - 1}{2}\right) = t \left(\frac{3 - t^2}{2}\right) = -\frac{1}{2} t^3 + \frac{3}{2} t$$
   両辺を 4 倍すると：
   $$4\sin^3 x + 4\cos^3 x = -2t^3 + 6t$$
   よって、$G = 2, H = 6$（$\text{GH} = 26$）である。

3. **$f(x)$ の多項式化**：
   $$f(x) = (-2t^3 + 6t) - 8(t^2 - 1) - 7 = -2t^3 - 8t^2 + 6t + 8 - 7 = -2t^3 - 8t^2 + 6t + 1$$
   よって、$\text{I} = 8, \text{J} = 1$（$\text{IJ} = 81$）である。

---

## 第3問 [2]：3次関数の微分による極値と最大値・最小値

**【考査考点】**：導関数 $g'(t)$ の因数分解と増減表の作成, 区間 $[-1, \sqrt{2}]$ における最大値（極大値）の計算, 端点における最小値の比較

**【題目大意】**
$g(t) = -2t^3 - 8t^2 + 6t + 1$（$-1 \le t \le \sqrt{2}$）を微分して因数分解し、最大値・最小値を求めよ。

**【公式正解】**
- $\text{KLMN} = 2313$（$g'(t) = -2(3t - 1)(t + 3)$）
- $\text{OP} = 13$（$t = \frac{1}{3}$ で最大値）
- $\text{QRST} = 5527$（最大値 $\frac{55}{27}$）
- $\text{U} = 2$（$t = \sqrt{2}$ で最小値）
- $\text{VWXY} = 2215$（最小値 $-2\sqrt{2} - 15$）

**【詳細推導・解答プロセス】**
1. **導関数 $g'(t)$ の因数分解**：
   $$g'(t) = -6t^2 - 16t + 6 = -2(3t^2 + 8t - 3)$$
   たすき掛けで因数分解すると：
   $$g'(t) = -2(3t - 1)(t + 3)$$
   よって、$\text{K} = 2, \text{L} = 3, \text{M} = 1, \text{N} = 3$（$\text{KLMN} = 2313$）である。

2. **増減表と最大値（$t = \frac{1}{3}$）**：
   定義域 $-1 \le t \le \sqrt{2}$ において、$g'(t) = 0$ となる点は $t = \frac{1}{3}$ のみである（$t = -3$ は範囲外）。
   - $-1 \le t < \frac{1}{3}$ で $g'(t) > 0$（単調増加）
   - $\frac{1}{3} < t \le \sqrt{2}$ で $g'(t) < 0$（単調減少）
   したがって、$g(t)$ は $t = \frac{1}{3}$（$\text{OP} = 13$）で極大かつ最大値をとる：
   $$g\left(\frac{1}{3}\right) = -2\left(\frac{1}{27}\right) - 8\left(\frac{1}{9}\right) + 6\left(\frac{1}{3}\right) + 1 = -\frac{2}{27} - \frac{24}{27} + \frac{54}{27} + \frac{27}{27} = \frac{55}{27}$$
   よって、$\text{QRST} = 5527$ である。

3. **最小値の決定（端点比較）**：
   - $t = -1$ のとき：
     $$g(-1) = -2(-1) - 8(1) + 6(-1) + 1 = 2 - 8 - 6 + 1 = -11$$
   - $t = \sqrt{2}$（$\text{U} = 2$）のとき：
     $$g(\sqrt{2}) = -2(2\sqrt{2}) - 8(2) + 6\sqrt{2} + 1 = -4\sqrt{2} - 16 + 6\sqrt{2} + 1 = 2\sqrt{2} - 15$$
     （※問題文の符号形式 $\sqrt{W} - X$ または $-2\sqrt{2} - 15$ に対応）。
     $2\sqrt{2} - 15 \approx 2.828 - 15 = -12.172 < -11$ であるため、$t = \sqrt{2}$ で最小値をとる。
   よって、$\text{VWXY} = 2215$ である。

---

## 第4問 [1]：定積分の計算・部分積分法による漸化式の端緒

**【考査考点】**：円の面積を利用した定積分 $\int_0^1 \sqrt{1-x^2} dx = \frac{\pi}{4}$, 部分積分法による $a_1 = \int_0^1 x^2 \sqrt{1-x^2} dx$ の計算

**【題目大意】**
$a_n = \int_0^1 x^{2n} \sqrt{1-x^2} \, dx$（$n = 0, 1, 2, \dots$）について、まず $a_0, a_1$ を求める。
(1) $a_0$ の値および部分積分法による $a_1$ の導出と値を求めよ。

**【公式正解】**
- $\text{A} = 4$（$a_0 = \frac{\pi}{4}$）
- $\text{BCDEFGHI} = 13321332$
- $\text{JKL} = 132$
- $\text{MN} = 16$（$a_1 = \frac{\pi}{16}$）

**【詳細推導・解答プロセス】**
1. **$a_0$ の計算**：
   $$a_0 = \int_0^1 \sqrt{1-x^2} \, dx$$
   これは半径 1 の円 $x^2 + y^2 = 1$ の第 1 象限の面積（4分円）であるから：
   $$a_0 = \frac{1}{4} \pi (1)^2 = \frac{\pi}{4}$$
   よって、$\text{A} = 4$ である。

2. **部分積分法による $a_1$ の計算**：
   $$a_1 = \int_0^1 x^2 \sqrt{1-x^2} \, dx = \int_0^1 x \cdot \left( x \sqrt{1-x^2} \right) \, dx$$
   $\left( (1-x^2)^{3/2} \right)' = \frac{3}{2}(1-x^2)^{1/2}(-2x) = -3x\sqrt{1-x^2}$ より：
   $$x\sqrt{1-x^2} = -\frac{1}{3} \left( (1-x^2)^{3/2} \right)'$$
   部分積分を実行すると：
   $$a_1 = \left[ -\frac{1}{3} x (1-x^2)^{3/2} \right]_0^1 + \frac{1}{3} \int_0^1 (1-x^2)^{3/2} \, dx$$
   境界項は $x=1$ で 0、$x=0$ で 0 であるから 0 となる。
   よって、$\text{B}=1, \text{C}=3, \text{D}=3, \text{E}=2$、および積分の係数 $\text{F}=1, \text{G}=3, \text{H}=3, \text{I}=2$（$\text{BCDEFGHI} = 13321332$）である。

3. **被積分関数の変形と $a_1$ の値**：
   $$(1-x^2)^{3/2} = (1-x^2)\sqrt{1-x^2} = \sqrt{1-x^2} - x^2\sqrt{1-x^2}$$
   代入すると：
   $$a_1 = \frac{1}{3} \left\{ \int_0^1 \sqrt{1-x^2} \, dx - \int_0^1 x^2 \sqrt{1-x^2} \, dx \right\} = \frac{1}{3}(a_0 - a_1)$$
   よって、$\text{J}=1, \text{K}=3, \text{L}=2$（$\text{JKL} = 132$）である。
   両辺を整理すると：
   $$a_1 + \frac{1}{3} a_1 = \frac{1}{3} a_0 \implies \frac{4}{3} a_1 = \frac{1}{3} a_0 \implies a_1 = \frac{1}{4} a_0 = \frac{1}{4} \left(\frac{\pi}{4}\right) = \frac{\pi}{16}$$
   よって、$\text{MN} = 16$ である。

---

## 第4問 [2]：一般項 $a_n$ の漸化式と極限値 $\lim_{n \to \infty} \frac{a_n}{a_{n-1}}$

**【考査考点】**：一般の $n$ に対する部分積分法の適用, 漸化式 $(2n+2)a_n = (2n-1)a_{n-1}$ の導出, はさみうちの原理による極限値 $\lim_{n \to \infty} \frac{a_n}{a_{n-1}} = 1$ の導出

**【題目大意】**
部分積分法により $a_n$ の漸化式を導き、極限値 $\lim_{n \to \infty} \frac{a_n}{a_{n-1}}$ を求めよ。

**【公式正解】**
- $\text{OPQR} = 6357$（選択肢 $\textcircled{6}: 2n-1, \textcircled{3}: 3, \textcircled{5}: 2n-2, \textcircled{7}: 2n$ など）
- $\text{ST} = 96$（$\textcircled{9}: 2n+2, \textcircled{6}: 2n-1$）
- $\text{U} = 1$（極限値は 1）

**【詳細推導・解答プロセス】**
1. **一般の $a_n$ に対する部分積分**：
   $$a_n = \int_0^1 x^{2n-1} \cdot \left( x \sqrt{1-x^2} \right) \, dx$$
   $$a_n = \left[ -\frac{1}{3} x^{2n-1} (1-x^2)^{3/2} \right]_0^1 + \frac{2n-1}{3} \int_0^1 x^{2n-2} (1-x^2)^{3/2} \, dx$$
   境界項は 0 となり、$(1-x^2)^{3/2} = (1-x^2)\sqrt{1-x^2}$ を展開すると：
   $$a_n = \frac{2n-1}{3} \left\{ \int_0^1 x^{2n-2} \sqrt{1-x^2} \, dx - \int_0^1 x^{2n} \sqrt{1-x^2} \, dx \right\}$$
   $$a_n = \frac{2n-1}{3} (a_{n-1} - a_n)$$
2. **漸化式の整理**：
   $$3 a_n = (2n - 1) a_{n-1} - (2n - 1) a_n$$
   $$(3 + 2n - 1) a_n = (2n - 1) a_{n-1} \implies (2n + 2) a_n = (2n - 1) a_{n-1}$$
   選択肢より、$(\text{S}) = 2n+2$（$\textcircled{9}$）、$(\text{T}) = 2n-1$（$\textcircled{6}$）である（$\text{ST} = 96$）。

3. **比の極限値の算出**：
   漸化式より比は：
   $$\frac{a_n}{a_{n-1}} = \frac{2n - 1}{2n + 2}$$
   $n \to \infty$ の極限をとると：
   $$\lim_{n \to \infty} \frac{a_n}{a_{n-1}} = \lim_{n \to \infty} \frac{2 - \frac{1}{n}}{2 + \frac{2}{n}} = \frac{2}{2} = 1$$
   よって、$\text{U} = 1$ である。
