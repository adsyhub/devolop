# 2023年度 第1回（2023-1）EJU 日本留学試験 数学（コース2）全問詳細解説

- **試験科目**：数学（コース2 / Mathematics Course 2）
- **対象試験**：2023年度第1回（令和5年6月実施）
- **形式コード**：`MATHEMATICS_COURSE_2_JA`
- **問題構成**：大問 I ～ IV（計4大問、8設問ブロック）
- **解答形式**：マーク式（数値・符号・アルファベット選択）

---

## 数学（コース2）公式正解一覧表

| 大問 | 設問 | 解答記号 | 公式正解 | 考査分野・要点 |
| :--- | :--- | :--- | :--- | :--- |
| **I** | 問1 | ABC | **634** | 2次関数の交点条件 |
| | | DE | **33** | グラフの交点連立方程式 |
| | | F | **2** | 定数 $b$ の消去決定 |
| | | GHI | **916** | 最大値と最小値の差 |
| | | JK, L | **23**, **2** | $a = -2/3, c = 2$ |
| | 問2 | M | **0** ($8/81$) | 3箱からの抽出確率（$a=b\neq c$） |
| | | N | **2** ($56/81$) | 3数相異なる確率 |
| | | OP | **24** ($2 \le b \le 4$) | 不等式 $a > 2b > 3c$ の範囲 |
| | | Q | **9** ($10/729$) | 不等式を満たす確率 $p$ |
| | | R | **4** ($25/126$) | 5枚中奇数4枚偶数1枚 |
| | | S | **7** ($125/126$) | 余事象（少なくとも1枚奇数） |
| **II** | 問1 | AB | **32** ($3/2$) | 内積 $\vec{c} \cdot \vec{a}$ の計算 |
| | | C, D | **4**, **2** | 垂直条件による内積 $\vec{a} \cdot \vec{b}, \vec{b} \cdot \vec{c}$ |
| | | EFG | **838** | $\vec{a}$ との内積式 $8s + 3t = 8$ |
| | | HI | **34** | $\vec{c}$ との内積式 $3s + 4t = 4$ |
| | | J, K | **2**, **0** | 基底係数 $s = 20/23, t = 8/23$ |
| | | L | **5** ($23/28$) | 対角線交点比 $\overrightarrow{OD} = \frac{23}{28}\vec{b}$ |
| | 問2 | M | **0** | $a = 0$（直線ABとBCが垂直） |
| | | N | **3** | $b = 0$（直線ABとBCが同一直線） |
| | | OP | **-8** | 三角関数の極形式商と偏角 $-A+B+C$ |
| | | Q | **0** | 直角の頂点 $A = \pi/2$ |
| | | RS | **-1** | 実部 $a = -1$ |
| | | TU, V | **23**, **2** | 偏角 $\theta = 2\pi/3$、絶対値 $2$ |
| | | W, X, Y | **2**, **3**, **6** | 直角三角形の内角 $\pi/2, \pi/3, \pi/6$ |
| **III** | | A, BCD | **2**, **103** | 端点値 $S(-2) = 2, S(0) = 10/3$ |
| | | E, F | **0**, **0** | 外側領域での単調性と不等号 $<$ |
| | | GHIJK | **-1322** | $S(a) = -\frac{1}{3}a^3 - 2a^2 - 2a + \frac{10}{3}$ |
| | | LMN | **103** | 定数項 $10/3$ |
| | | OP | **42** | 導関数 $S'(a) = -a^2 - 4a - 2$ |
| | | QR | **22** | 極大値を与える $a = -2 + \sqrt{2}$ |
| | | ST | **22** | 最大値を与える $a = -2 + \sqrt{2}$ |
| | | UVWX | **2423** | 最大値 $2 + \frac{4\sqrt{2}}{3}$ |
| **IV** | | A | **4** | 極値条件より $a = 4$ |
| | | BCD | **512** | 別の極値点 $x = \frac{5}{12}\pi$ |
| | | EFG | **124** | 被積分関数の変形 $1 - 2\cos 4t$ |
| | | HI | **12** | 2次項係数 $1/2$ |
| | | JKL | **124** | $x\sin 4x$ の係数 $1/2$ |
| | | MNO, PQ | **184**, **18** | $\cos 4x$ 係数 $1/8$、定数項 $1/8$ |
| | | RST | **972** | 最大値 $\frac{25}{288}\pi^2 + \frac{5\sqrt{3}}{48}\pi + \frac{1}{16}$ |
| | | UVW | **382** | 接線 $y = \frac{3}{4}\pi x - \frac{5}{32}\pi^2 + \frac{1}{4}$ |

---

## 逐問詳細推導与解説


---

## 第I問 問1：2次関数の交点条件・最大値と最小値の差

**【考査考点】**：2次関数の交点条件と代数連立方程式, 平方完成による頂点座標と極値（最大値・最小値）の決定, 代数方程式による係数消元と二次方程式の解法

### 【第I問 問1】詳細解答と解説

#### (1) グラフの交点条件による関係式の導出
与えられた2つの2次関数は
$$f(x) = \frac{1}{3}x^2 + ax - b, \quad g(x) = -x^2 + cx + b$$
条件(A)より、$y = f(x)$ と $y = g(x)$ は 2 直線 $x = -1, x = 3$ 上で交わるため、$f(-1) = g(-1)$ かつ $f(3) = g(3)$ が成り立つ。

1. **$x = -1$ での交点条件**：
$$f(-1) = \frac{1}{3}(-1)^2 + a(-1) - b = \frac{1}{3} - a - b$$
$$g(-1) = -(-1)^2 + c(-1) + b = -1 - c + b$$
これらが等しいので：
$$\frac{1}{3} - a - b = -1 - c + b \implies a + 2b - c = \frac{4}{3}$$
両辺に 3 を掛けて整数係数に整理すると：
$$3a + 6b - 3c = 4 \quad \cdots \textcircled{1}$$
問題文の形式 $3a + \text{A}b - \text{B}c = \text{C}$ と比較して：
$$\mathbf{A = 6, B = 3, C = 4} \implies \mathbf{ABC = 634}$$

2. **$x = 3$ での交点条件**：
$$f(3) = \frac{1}{3}(3)^2 + a(3) - b = 3 + 3a - b$$
$$g(3) = -(3)^2 + c(3) + b = -9 + 3c + b$$
これらが等しいので：
$$3 + 3a - b = -9 + 3c + b \implies 3a - 2b - 3c = -12 \quad \cdots \textcircled{2}$$
問題文の形式 $\text{D}a - 2b - \text{E}c = -12$ と比較して：
$$\mathbf{D = 3, E = 3} \implies \mathbf{DE = 33}$$

3. **定数 $b$ の決定**：
$\textcircled{1} - \textcircled{2}$ を計算すると、$a$ と $c$ の項が同時に消去される：
$$(3a + 6b - 3c) - (3a - 2b - 3c) = 4 - (-12)$$
$$8b = 16 \implies b = 2$$
よって、$\mathbf{F = 2}$。

#### (2) 最大値と最小値の差から $a, c$ の決定
$b = 2$ を各関数に代入し、平方完成を行う：
- $g(x) = -x^2 + cx + 2 = -\left(x - \frac{c}{2}\right)^2 + \frac{c^2}{4} + 2$
  上に凸の放物線であるから、最大値は $\frac{c^2}{4} + 2$。
- $f(x) = \frac{1}{3}x^2 + ax - 2 = \frac{1}{3}\left(x^2 + 3ax\right) - 2 = \frac{1}{3}\left(x + \frac{3}{2}a\right)^2 - \frac{3}{4}a^2 - 2$
  下に凸の放物線であるから、最小値は $-\frac{3}{4}a^2 - 2$。

条件(B)「$g(x)$ の最大値と $f(x)$ の最小値の差が $\frac{16}{3}$」より：
$$\left(\frac{c^2}{4} + 2\right) - \left(-\frac{3}{4}a^2 - 2\right) = \frac{16}{3}$$
$$\frac{3}{4}a^2 + \frac{c^2}{4} + 4 = \frac{16}{3}$$
両辺に 12 を掛けると：
$$9a^2 + 3c^2 + 48 = 64 \implies 9a^2 + 3c^2 = 16$$
問題文の形式 $\text{G}a^2 + 3c^2 = \text{HI}$ と比較して：
$$\mathbf{G = 9, HI = 16} \implies \mathbf{GHI = 916}$$

さらに、$b = 2$ を $\textcircled{1}$ に代入すると：
$$3a + 12 - 3c = 4 \implies 3a - 3c = -8 \implies a = c - \frac{8}{3}$$
これを $9a^2 + 3c^2 = 16$ に代入する：
$$9\left(c - \frac{8}{3}\right)^2 + 3c^2 = 16$$
$$9\left(c^2 - \frac{16}{3}c + \frac{64}{9}\right) + 3c^2 = 16$$
$$9c^2 - 48c + 64 + 3c^2 = 16 \implies 12c^2 - 48c + 48 = 0$$
両辺を 12 で割ると：
$$c^2 - 4c + 4 = 0 \implies (c - 2)^2 = 0 \implies c = 2$$
したがって：
$$a = c - \frac{8}{3} = 2 - \frac{8}{3} = -\frac{2}{3}$$
問題文の形式 $a = -\frac{\text{J}}{\text{K}}, c = \text{L}$ より：
$$\mathbf{J = 2, K = 3} \implies \mathbf{JK = 23}, \quad \mathbf{L = 2}$$

**【解法テクニック・易錯点】**
- $x = -1$ と $x = 3$ の 2 点での条件式を作った際、引き算により $a$ と $c$ の係数が同じ比率（$3: -3$）になっていることに気付けば、直ちに $b$ が一発で求まります。
- $f(x)$ の平方完成時に、二次の係数が $\frac{1}{3}$ であるため、$\frac{1}{3}(x^2 + 3ax)$ と括り出した後の半分 $\frac{3}{2}a$ の二乗展開で係数ミスをしないよう注意しましょう。

---

## 第I問 問2：カードの抽出確率・条件付き不等式と余事象

**【考査考点】**：同様に確からしい事象と独立抽出の積の法則, 不等式制約条件 $a > 2b > 3c$ を満たす整数の組の分類探索, 奇数・偶数の組合せ確率と余事象の活用

### 【第I問 問2】詳細解答と解説

#### (1) 箱 A, B, C から各 1 枚取り出す試行
3つの箱 A, B, C にはそれぞれ 1 から 9 のカードが 9 枚入っている。
各箱から 1 枚ずつ取り出す事象の全事象の総数は：
$$N = 9 \times 9 \times 9 = 729$$

**(i) $a = b \neq c$ である確率**
- $a$ と $b$ の共通の数値を 1 ～ 9 の中から選ぶ方法は 9 通り。
- $c$ は $a$（$= b$）と異なる数値を選ぶので、残り $9 - 1 = 8$ 通り。
条件を満たす取り出し方の総数は $9 \times 8 = 72$ 通り。
求める確率は：
$$\frac{72}{729} = \frac{8}{81}$$
選択肢一覧より、$\textcircled{0}$ が $\frac{8}{81}$ に該当する。
よって、$\mathbf{M = 0}$。

**(ii) $a, b, c$ の中に同じものがない（すべて異なる）確率**
- $a$ の選び方は 9 通り。
- $b$ の選び方は $a$ 以外の 8 通り。
- $c$ の選び方は $a, b$ 以外の 7 通り。
総数は $9 \times 8 \times 7 = 504$ 通り。
求める確率は：
$$\frac{504}{729} = \frac{56}{81}$$
選択肢一覧より、$\textcircled{2}$ が $\frac{56}{81}$ に該当する。
よって、$\mathbf{N = 2}$。

**(iii) $a > 2b > 3c$ となる確率 $p$**
$a, b, c$ は 1 から 9 の整数である。
- $a \le 9$ より、$2b < a \le 9 \implies 2b \le 8 \implies b \le 4$。
- $c \ge 1$ より、$2b > 3c \ge 3 \implies 2b \ge 4 \implies b \ge 2$。
したがって、条件を満たす組が存在する $b$ の範囲は：
$$2 \le b \le 4$$
よって、$\mathbf{O = 2, P = 4} \implies \mathbf{OP = 24}$。

$b$ の値ごとに $(a, c)$ の組を数え上げる：
1. **$b = 2$ のとき**：
   $2b = 4$。不等式は $a > 4 > 3c$。
   - $3c < 4 \implies c = 1$（1通り）
   - $a > 4 \implies a \in \{5, 6, 7, 8, 9\}$（5通り）
   組の数は $5 \times 1 = 5$ 通り。
2. **$b = 3$ のとき**：
   $2b = 6$。不等式は $a > 6 > 3c$。
   - $3c < 6 \implies c = 1$（1通り）
   - $a > 6 \implies a \in \{7, 8, 9\}$（3通り）
   組の数は $3 \times 1 = 3$ 通り。
3. **$b = 4$ のとき**：
   $2b = 8$。不等式は $a > 8 > 3c$。
   - $3c < 8 \implies c \in \{1, 2\}$（2通り）
   - $a > 8 \implies a = 9$（1通り）
   組の数は $1 \times 2 = 2$ 通り。

以上より、条件を満たす組の総数は $5 + 3 + 2 = 10$ 通り。
したがって、確率 $p$ は：
$$p = \frac{10}{729}$$
選択肢一覧より、$\textcircled{9}$ が $\frac{10}{729}$ に該当する。
よって、$\mathbf{Q = 9}$。

#### (2) A から 3 枚、B から 2 枚、計 5 枚を取り出す試行
各箱のカード 9 枚のうち、奇数は $\{1, 3, 5, 7, 9\}$ の 5 枚、偶数は $\{2, 4, 6, 8\}$ の 4 枚である。
取り出し方の全事象の総数は：
$$N = \binom{9}{3} \times \binom{9}{2} = \frac{9 \times 8 \times 7}{3 \times 2 \times 1} \times \frac{9 \times 8}{2 \times 1} = 84 \times 36 = 3024$$

**(i) 奇数が 4 枚、偶数が 1 枚である確率**
5枚の内訳として、次の 2 つの排反な場合がある：
- **Case 1: A から奇数 3 枚、B から奇数 1 枚・偶数 1 枚**
  $$\binom{5}{3} \times \left(\binom{5}{1} \times \binom{4}{1}\right) = 10 \times (5 \times 4) = 10 \times 20 = 200 \text{ 通り}$$
- **Case 2: A から奇数 2 枚・偶数 1 枚、B から奇数 2 枚**
  $$\left(\binom{5}{2} \times \binom{4}{1}\right) \times \binom{5}{2} = (10 \times 4) \times 10 = 40 \times 10 = 400 \text{ 通り}$$
条件を満たす場合の数は $200 + 400 = 600$ 通り。
求める確率は：
$$\frac{600}{3024} = \frac{25}{126}$$
選択肢一覧より、$\textcircled{4}$ が $\frac{25}{126}$ に該当する。
よって、$\mathbf{R = 4}$。

**(ii) 奇数が少なくとも 1 枚ある確率**
余事象「5枚すべてが偶数である」を考える。
A から偶数 3 枚、B から偶数 2 枚を取り出す方法は：
$$\binom{4}{3} \times \binom{4}{2} = 4 \times 6 = 24 \text{ 通り}$$
余事象の確率は：
$$\frac{24}{3024} = \frac{1}{126}$$
したがって、求める確率は余事象を用いて：
$$1 - \frac{1}{126} = \frac{125}{126}$$
選択肢一覧より、$\textcircled{7}$ が $\frac{125}{126}$ に該当する。
よって、$\mathbf{S = 7}$。

---

## 第II問 問1：平面ベクトルの内積・基底分解と対角線の交点比

**【考査考点】**：垂直条件 $\vec{u} \perp \vec{v} \iff \vec{u} \cdot \vec{v} = 0$ による内積の導出, ベクトルの大きさの 2 乗展開による内積 $\vec{c} \cdot \vec{a}$ の決定, 一次独立な基底への分解と連立方程式による係数決定, 同一直線上の点（共線条件）による対角線の交点比の計算

### 【第II問 問1】詳細解答と解説

四角形 $OABC$ において、$\angle OAB = 90^\circ, \angle OCB = 90^\circ$ である。
辺の長さは $OA = 2, OC = \sqrt{2}$、対角線 $AC = \sqrt{3}$。
$\overrightarrow{OA} = \vec{a}, \overrightarrow{OB} = \vec{b}, \overrightarrow{OC} = \vec{c}$ とおく。
大きさは $|\vec{a}| = 2 \implies |\vec{a}|^2 = 4$、$|\vec{c}| = \sqrt{2} \implies |\vec{c}|^2 = 2$ である。

#### (1) 内積 $\vec{c} \cdot \vec{a}$ の計算
$\overrightarrow{AC} = \vec{c} - \vec{a}$ であるから、その大きさの 2 乗を計算する：
$$|\overrightarrow{AC}|^2 = |\vec{c} - \vec{a}|^2 = |\vec{c}|^2 - 2\vec{c} \cdot \vec{a} + |\vec{a}|^2$$
与えられた数値を代入すると：
$$(\sqrt{3})^2 = 2 - 2\vec{c} \cdot \vec{a} + 4$$
$$3 = 6 - 2\vec{c} \cdot \vec{a} \implies 2\vec{c} \cdot \vec{a} = 3 \implies \vec{c} \cdot \vec{a} = \frac{3}{2}$$
問題文の形式 $\frac{\text{A}}{\text{B}}$ より：
$$\mathbf{A = 3, B = 2} \implies \mathbf{AB = 32}$$

#### (2) 内積 $\vec{a} \cdot \vec{b}$ と $\vec{b} \cdot \vec{c}$ の計算
1. $\angle OAB = 90^\circ$ より $\overrightarrow{OA} \perp \overrightarrow{AB}$ である。
   $$\vec{a} \cdot (\vec{b} - \vec{a}) = 0 \implies \vec{a} \cdot \vec{b} - |\vec{a}|^2 = 0 \implies \vec{a} \cdot \vec{b} = |\vec{a}|^2 = 4$$
   よって、$\mathbf{C = 4}$。
2. $\angle OCB = 90^\circ$ より $\overrightarrow{OC} \perp \overrightarrow{CB}$ である。
   $$\vec{c} \cdot (\vec{b} - \vec{c}) = 0 \implies \vec{c} \cdot \vec{b} - |\vec{c}|^2 = 0 \implies \vec{b} \cdot \vec{c} = |\vec{c}|^2 = 2$$
   よって、$\mathbf{D = 2}$。

#### (3) $\vec{b}$ を $\vec{a}$ と $\vec{c}$ で表す（係数 $s, t$ の決定）
$\vec{b} = s\vec{a} + t\vec{c}$ とおく。
1. 両辺と $\vec{a}$ の内積をとる：
   $$\vec{a} \cdot \vec{b} = s|\vec{a}|^2 + t(\vec{a} \cdot \vec{c})$$
   $$4 = 4s + \frac{3}{2}t$$
   両辺に 2 を掛けると：
   $$8s + 3t = 8$$
   問題文の形式 $\text{E}s + \text{F}t = \text{G}$ と比較して：
   $$\mathbf{E = 8, F = 3, G = 8} \implies \mathbf{EFG = 838}$$
2. 両辺と $\vec{c}$ の内積をとる：
   $$\vec{b} \cdot \vec{c} = s(\vec{a} \cdot \vec{c}) + t|\vec{c}|^2$$
   $$2 = \frac{3}{2}s + 2t$$
   両辺に 2 を掛けると：
   $$3s + 4t = 4$$
   問題文の形式 $\text{H}s + \text{I}t = 4$ と比較して：
   $$\mathbf{H = 3, I = 4} \implies \mathbf{HI = 34}$$

連立方程式を解く：
$$\begin{cases} 8s + 3t = 8 & \times 4 \implies 32s + 12t = 32 \\ 3s + 4t = 4 & \times 3 \implies 9s + 12t = 12 \end{cases}$$
引き算すると：$23s = 20 \implies s = \frac{20}{23}$。
代入して：$4t = 4 - 3\left(\frac{20}{23}\right) = \frac{92 - 60}{23} = \frac{32}{23} \implies t = \frac{8}{23}$。
選択肢一覧より：
- $s = \frac{20}{23}$ は $\textcircled{2}$ に対応。よって、$\mathbf{J = 2}$。
- $t = \frac{8}{23}$ は $\textcircled{0}$ に対応。よって、$\mathbf{K = 0}$。

#### (4) 対角線の交点 $D$ と $\overrightarrow{OD}$
交点 $D$ は線分 $AC$ 上にあるため、実数 $u$ を用いて次のように表せる：
$$\overrightarrow{OD} = (1 - u)\vec{a} + u\vec{c}$$
また、$D$ は線分 $OB$ 上にあるため、実数 $k$ を用いて：
$$\overrightarrow{OD} = k\vec{b} = k(s\vec{a} + t\vec{c}) = ks\vec{a} + kt\vec{c}$$
$\vec{a}$ と $\vec{c}$ は一次独立であるから、係数を比較すると：
$$ks = 1 - u, \quad kt = u$$
2 式を加えると：
$$k(s + t) = 1 \implies k = \frac{1}{s + t}$$
求めた $s, t$ の値を代入すると：
$$s + t = \frac{20}{23} + \frac{8}{23} = \frac{28}{23}$$
$$k = \frac{1}{\frac{28}{23}} = \frac{23}{28}$$
したがって、$\overrightarrow{OD} = \frac{23}{28}\vec{b}$ である。
選択肢一覧より、$\frac{23}{28}$ は $\textcircled{5}$ に対応する。
よって、$\mathbf{L = 5}$。

---

## 第II問 問2：複素数平面上の商の幾何学的意味・三角形の形状決定

**【考査考点】**：複素数の商 $\frac{z_3 - z_2}{z_2 - z_1}$ の偏角と直交・共線条件, オイラーの公式・極形式を用いた三角関数の積の簡約化, 直角三角形の角の決定と複素数の偏角・絶対値の幾何的同定

### 【第II問 問2】詳細解答と解説

複素数平面上の異なる 3 点 $A(z_1), B(z_2), C(z_3)$ に対して：
$$\frac{z_3 - z_2}{z_2 - z_1} = a + bi$$
とおく。

#### (1) 実部・虚部が 0 のときの幾何学的性質
$\frac{z_3 - z_2}{z_2 - z_1}$ の偏角 $\theta = \arg\left(\frac{z_3 - z_2}{z_2 - z_1}\right)$ は、ベクトル $\overrightarrow{BA}$ から $\overrightarrow{BC}$ への回転角を表す。
1. **$a = 0$ のとき**：
   商は純虚数 $bi$ となるため、偏角は $\pm \frac{\pi}{2}$ である。
   したがって、直線 $AB$ と直線 $BC$ は垂直となる。
   選択肢 $\textcircled{0}$「直線 ABと直線 BCは垂直」が適する。
   よって、$\mathbf{M = 0}$。
2. **$b = 0$ のとき**：
   商は実数 $a$ となるため、偏角は $0$ または $\pi$ である。
   したがって、$A, B, C$ は一直線上にあり、直線 $AB$ と直線 $BC$ は同一直線となる。
   選択肢 $\textcircled{3}$「直線 ABと直線 BCは同一直線」が適する。
   よって、$\mathbf{N = 3}$。

#### (2) 三角関数の複素数表現と角の決定
与えられた $a$ の式は：
$$a = \frac{(i\cos A + \sin A)(i\cos B - \sin B)}{\cos C - i\sin C}$$
各因数をオイラーの公式または極形式に変形する：
- $i\cos A + \sin A = i(\cos A - i\sin A) = i e^{-iA}$
- $i\cos B - \sin B = i(\cos B + i\sin B) = i e^{iB}$
分子の積は：
$$(i e^{-iA})(i e^{iB}) = i^2 e^{i(B - A)} = -e^{i(B - A)}$$
分母は：
$$\cos C - i\sin C = e^{-iC}$$
したがって、商は：
$$\frac{-e^{i(B - A)}}{e^{-iC}} = -e^{i(B - A + C)} = -(\cos(-A + B + C) + i\sin(-A + B + C))$$
問題文の形式 $-(\cos P + i\sin P)$ より、先頭の符号は負（$-$）で、偏角の中身は $-A + B + C$ である。
選択肢一覧より、$\textcircled{8}$ が $(-A + B + C)$ に対応する。
よって、$\mathbf{O = -, P = 8} \implies \mathbf{OP = -8}$。

$a$ は実数であるから、虚部が 0 でなければならない：
$$\sin(-A + B + C) = 0$$
三角形の内角の和は $A + B + C = \pi$ であるから、$-A + B + C = \pi - 2A$ と表せる。
$$\sin(\pi - 2A) = \sin 2A = 0$$
$A$ は三角形の内角なので $0 < A < \pi \implies 0 < 2A < 2\pi$。
したがって：
$$2A = \pi \implies A = \frac{\pi}{2}$$
したがって、$\triangle ABC$ は $A = \frac{\pi}{2}$ の直角三角形である。
選択肢 $\textcircled{0}$ が $A$ に該当する。よって、$\mathbf{Q = 0}$。

このとき、$-A + B + C = \pi - 2A = 0$ となるため：
$$a = -\cos 0 = -1$$
問題文の形式 $a = \text{RS}$ より：
$$\mathbf{R = -, S = 1} \implies \mathbf{RS = -1}$$

#### (3) 偏角と辺の比・三角形の内角の決定
$a = -1, b = \sqrt{3}$ であるから：
$$\frac{z_3 - z_2}{z_2 - z_1} = -1 + \sqrt{3}i = 2\left(-\frac{1}{2} + \frac{\sqrt{3}}{2}i\right) = 2\left(\cos\frac{2}{3}\pi + i\sin\frac{2}{3}\pi\right)$$
したがって：
- 偏角 $\theta = \frac{2}{3}\pi \implies \mathbf{T = 2, U = 3} \implies \mathbf{TU = 23}$。
- 絶対値 $\left|\frac{z_3 - z_2}{z_2 - z_1}\right| = 2 \implies \mathbf{V = 2}$。

幾何学的に、$\overrightarrow{BA}$ から $\overrightarrow{BC}$ への角が $\frac{2}{3}\pi = 120^\circ$ の外角に相当するため、内角 $B$ は：
$$B = \pi - \frac{2}{3}\pi = \frac{\pi}{3} \implies X = 3$$
$A = \frac{\pi}{2} \implies W = 2$。
残る内角 $C$ は：
$$C = \pi - A - B = \pi - \frac{\pi}{2} - \frac{\pi}{3} = \frac{\pi}{6} \implies Y = 6$$
よって、$\mathbf{W = 2, X = 3, Y = 6}$。

---

## 第III問：分段関数の定積分・微積分学の基本定理と最大値問題

**【考査考点】**：分段関数の定積分の定義と区間分割による積分の計算, パラメータ $a$ の動く区間における関数の単調性と不等式評価, 微分積分学の基本定理 $S'(a) = f(a+2) - f(a)$ による増減表と極値決定, 高次式の次数下げによる最大値の有理化・根号計算

### 【第III問】詳細解答と解説

与えられた関数は：
$$f(x) = \begin{cases} x + 2 & (x < 0) \\ -x^2 + x + 2 & (x \ge 0) \end{cases}$$
積分区間の幅が 2 の関数 $S(a) = \int_{a}^{a+2} f(x) \, dx$ を考える。

#### (1) 端点 $a = -2$ および $a = 0$ での積分値
1. **$a = -2$ のとき**：積分区間は $[-2, 0]$ であり、常に $x \le 0$ である：
   $$S(-2) = \int_{-2}^0 (x + 2) \, dx = \left[\frac{x^2}{2} + 2x\right]_{-2}^0 = 0 - \left(\frac{4}{2} - 4\right) = -(-2) = 2$$
   よって、$\mathbf{A = 2}$。
2. **$a = 0$ のとき**：積分区間は $[0, 2]$ であり、常に $x \ge 0$ である：
   $$S(0) = \int_0^2 (-x^2 + x + 2) \, dx = \left[-\frac{x^3}{3} + \frac{x^2}{2} + 2x\right]_0^2 = -\frac{8}{3} + 2 + 4 = \frac{10}{3}$$
   よって、$\mathbf{BCD = 103}$。

#### (2) 外側領域での単調性と不等式評価
- $a < -2$ のとき：区間 $[a, a+2] \subset (-\infty, 0)$ である。
  $x < 0$ において $f(x) = x + 2$ は単調増加関数であるから、区間を左にずらすほど被積分関数は小さくなる。
  したがって、$a < -2$ のとき $S(a) < S(-2)$ である。
  選択肢 $\textcircled{0}$（$<$）が適する。よって、$\mathbf{E = 0}$。
- $a > 0$ のとき：区間 $[a, a+2] \subset (0, \infty)$ である。
  $f(x) = -x^2 + x + 2$ は $x \ge \frac{1}{2}$ で単調減少する。
  $a > 0$ では右にずらすほど $f(x)$ の値は急速に減少するため、$S(a) < S(0)$ である。
  選択肢 $\textcircled{0}$（$<$）が適する。よって、$\mathbf{F = 0}$。

#### (3) $-2 \le a \le 0$ における $S(a)$ の導出と導関数
このとき、積分区間 $[a, a+2]$ は $x = 0$ をまたぐため、2 つの区間に分割する：
$$S(a) = \int_a^0 (x + 2) \, dx + \int_0^{a+2} (-x^2 + x + 2) \, dx$$
それぞれの積分を計算する：
1. $\int_a^0 (x + 2) \, dx = \left[\frac{x^2}{2} + 2x\right]_a^0 = -\left(\frac{a^2}{2} + 2a\right) = -\frac{1}{2}a^2 - 2a$
2. $\int_0^{a+2} (-x^2 + x + 2) \, dx = \left[-\frac{x^3}{3} + \frac{x^2}{2} + 2x\right]_0^{a+2} = -\frac{(a+2)^3}{3} + \frac{(a+2)^2}{2} + 2(a+2)$
展開して合算すると：
$$-\frac{a^3 + 6a^2 + 12a + 8}{3} + \frac{a^2 + 4a + 4}{2} + 2a + 4$$
$$= -\frac{1}{3}a^3 + \left(-2 + \frac{1}{2}\right)a^2 + (-4 + 2 + 2)a + \left(-\frac{8}{3} + 2 + 4\right) = -\frac{1}{3}a^3 - \frac{3}{2}a^2 + \frac{10}{3}$$
これに第 1 区間の $-\frac{1}{2}a^2 - 2a$ を加えると：
$$S(a) = -\frac{1}{3}a^3 - 2a^2 - 2a + \frac{10}{3}$$
問題文の形式 $\frac{\text{GH}}{\text{I}}a^3 - \text{J}a^2 - \text{K}a + \frac{\text{LM}}{\text{N}}$ と比較して：
$$\mathbf{GHIJK = -1322, \quad LMN = 103}$$

導関数 $S'(a)$ は、微積分学の基本定理より：
$$S'(a) = f(a+2) \cdot 1 - f(a) \cdot 1$$
$a+2 \ge 0$ より $f(a+2) = -(a+2)^2 + (a+2) + 2 = -a^2 - 3a$
$a \le 0$ より $f(a) = a + 2$
$$S'(a) = (-a^2 - 3a) - (a + 2) = -a^2 - 4a - 2$$
問題文の形式 $S'(a) = -a^2 - \text{O}a - \text{P}$ より：
$$\mathbf{O = 4, P = 2} \implies \mathbf{OP = 42}$$

#### (4) 極大値および最大値の決定
$S'(a) = 0$ を解くと：
$$a^2 + 4a + 2 = 0 \implies a = \frac{-4 \pm \sqrt{16 - 8}}{2} = -2 \pm \sqrt{2}$$
定義域 $-2 \le a \le 0$ にある解は：
$$a = -2 + \sqrt{2}$$
$S'(a)$ の符号は負から正、そして正から負へと変わるため、$a = -2 + \sqrt{2}$ で極大かつ最大となる。
問題文の形式 $a = -\text{Q} + \sqrt{\text{R}}$ および最大をとる $a = -\text{S} + \sqrt{\text{T}}$ より：
$$\mathbf{QR = 22, \quad ST = 22}$$

$S(-2 + \sqrt{2})$ の最大値を次数下げで計算する：
$a^2 + 4a + 2 = 0 \implies a^2 = -4a - 2$ より：
$$a^3 = a(-4a - 2) = -4a^2 - 2a = -4(-4a - 2) - 2a = 14a + 8$$
これを $S(a)$ に代入すると：
$$S(a) = -\frac{1}{3}(14a + 8) - 2(-4a - 2) - 2a + \frac{10}{3}$$
$$= -\frac{14}{3}a - \frac{8}{3} + 8a + 4 - 2a + \frac{10}{3} = \frac{4}{3}a + \frac{14}{3}$$
$a = -2 + \sqrt{2}$ を代入する：
$$S(-2 + \sqrt{2}) = \frac{4}{3}(-2 + \sqrt{2}) + \frac{14}{3} = -\frac{8}{3} + \frac{14}{3} + \frac{4\sqrt{2}}{3} = 2 + \frac{4\sqrt{2}}{3}$$
問題文の形式 $\text{U} + \frac{\text{V}\sqrt{\text{W}}}{\text{X}}$ と比較して：
$$\mathbf{U = 2, V = 4, W = 2, X = 3} \implies \mathbf{UVWX = 2423}$$

**【解法テクニック・易錯点】**
- 3次式に無理数 $-2+\sqrt{2}$ を直接代入して3乗展開すると計算ミスの温床になります。割り算または関係式 $a^2 = -4a - 2$ による次数下げ（剰余の定理）を用いることで、1次式 $\frac{4}{3}a + \frac{14}{3}$ に落とし込み、瞬時に正確な値を導けます。

---

## 第IV問：定積分で定義された関数・部分積分と曲線の接線

**【考査考点】**：定積分の微分法 $\frac{d}{dx}\int_0^x g(t)dt = g(x)$ による極値条件, 三角関数の半角・倍角公式による被積分関数の変形, 部分積分法 $\int t \cos 4t dt$ による不定積分の厳密計算, 極値の比較による最大値の決定と指定点における接線の方程式

### 【第IV問】詳細解答と解説

与えられた関数は：
$$f(x) = \int_{0}^{x} t(a\sin^2 2t - 1) \, dt \quad \left(0 < x < \frac{\pi}{2}\right)$$

#### (1) 極値条件によるパラメータ $a$ の決定と別の極値
微分積分学の基本定理より：
$$f'(x) = x(a\sin^2 2x - 1)$$
$f(x)$ が $x = \frac{\pi}{12}$ で極値をもつので、$f'\left(\frac{\pi}{12}\right) = 0$ が成り立つ：
$$\frac{\pi}{12} \left(a\sin^2\left(2 \cdot \frac{\pi}{12}\right) - 1\right) = 0$$
$$\sin\frac{\pi}{6} = \frac{1}{2} \implies a\left(\frac{1}{2}\right)^2 - 1 = 0 \implies \frac{a}{4} = 1 \implies a = 4$$
よって、$\mathbf{A = 4}$。

別の極値となる $x$ を求める：
$$f'(x) = x(4\sin^2 2x - 1) = 0$$
$0 < x < \frac{\pi}{2}$ では $x > 0$ であるから：
$$\sin^2 2x = \frac{1}{4} \implies \sin 2x = \frac{1}{2} \quad (\because 0 < 2x < \pi)$$
したがって：
$$2x = \frac{\pi}{6}, \quad \frac{5\pi}{6} \implies x = \frac{\pi}{12}, \quad \frac{5\pi}{12}$$
したがって、別の極値をとる点は $x = \frac{5}{12}\pi$ である。
問題文の形式 $\frac{\text{B}}{\text{CD}}\pi$ より：
$$\mathbf{B = 5, CD = 12} \implies \mathbf{BCD = 512}$$

#### (2) 被積分関数の変形と部分積分による $f(x)$ の決定
半角の公式 $\sin^2 2t = \frac{1 - \cos 4t}{2}$ を代入する：
$$a\sin^2 2t - 1 = 4\left(\frac{1 - \cos 4t}{2}\right) - 1 = 2(1 - \cos 4t) - 1 = 1 - 2\cos 4t$$
問題文の形式 $t(\text{E} - \text{F}\cos \text{G}t)$ と比較して：
$$\mathbf{E = 1, F = 2, G = 4} \implies \mathbf{EFG = 124}$$

被積分関数を展開して定積分を実行する：
$$f(x) = \int_0^x (t - 2t\cos 4t) \, dt = \int_0^x t \, dt - 2\int_0^x t\cos 4t \, dt$$
1. $\int_0^x t \, dt = \frac{1}{2}x^2$
2. $\int_0^x t\cos 4t \, dt$ に部分積分法を用いる：
   $$\int_0^x t\cos 4t \, dt = \left[t \cdot \frac{\sin 4t}{4}\right]_0^x - \int_0^x \frac{\sin 4t}{4} \, dt = \frac{x\sin 4x}{4} - \left[-\frac{\cos 4t}{16}\right]_0^x$$
   $$= \frac{x\sin 4x}{4} + \frac{\cos 4x - 1}{16}$$

これを代入すると：
$$f(x) = \frac{1}{2}x^2 - 2\left(\frac{x\sin 4x}{4} + \frac{\cos 4x - 1}{16}\right) = \frac{1}{2}x^2 - \frac{1}{2}x\sin 4x - \frac{1}{8}\cos 4x + \frac{1}{8}$$
問題文の形式 $\frac{\text{H}}{\text{I}}x^2 - \frac{\text{J}}{\text{K}}x\sin\text{L}x - \frac{\text{M}}{\text{N}}\cos\text{O}x + \frac{\text{P}}{\text{Q}}$ と比較して：
$$\mathbf{HI = 12, \quad JKL = 124, \quad MNO = 184, \quad PQ = 18}$$

#### (3) $f(x)$ の最大値の計算
$f'(x) = x(4\sin^2 2x - 1)$ の増減表を考える：
- $0 < x < \frac{\pi}{12}$ では $f'(x) < 0$（単調減少）
- $\frac{\pi}{12} < x < \frac{5\pi}{12}$ では $f'(x) > 0$（単調増加）
- $\frac{5\pi}{12} < x < \frac{\pi}{2}$ では $f'(x) < 0$（単調減少）
したがって、$f(x)$ は $x = \frac{5\pi}{12}$ で最大値をとる。

$x = \frac{5\pi}{12}$ を代入する：
$$4x = 4 \cdot \frac{5\pi}{12} = \frac{5\pi}{3}$$
$$\sin\frac{5\pi}{3} = -\frac{\sqrt{3}}{2}, \quad \cos\frac{5\pi}{3} = \frac{1}{2}$$
代入して計算すると：
$$f\left(\frac{5\pi}{12}\right) = \frac{1}{2}\left(\frac{5\pi}{12}\right)^2 - \frac{1}{2}\left(\frac{5\pi}{12}\right)\left(-\frac{\sqrt{3}}{2}\right) - \frac{1}{8}\left(\frac{1}{2}\right) + \frac{1}{8}$$
$$= \frac{1}{2} \cdot \frac{25\pi^2}{144} + \frac{5\sqrt{3}\pi}{48} - \frac{1}{16} + \frac{1}{8} = \frac{25}{288}\pi^2 + \frac{5\sqrt{3}}{48}\pi + \frac{1}{16}$$
選択肢一覧より：
- $\frac{25}{288}$ は $\textcircled{9}$
- $\frac{5\sqrt{3}}{48}$ は $\textcircled{7}$
- $\frac{1}{16}$ は $\textcircled{2}$
よって、$\mathbf{R = 9, S = 7, T = 2} \implies \mathbf{RST = 972}$。

#### (4) 点 $\left(\frac{\pi}{4}, f\left(\frac{\pi}{4}\right)\right)$ における接線の方程式
1. **接点の $y$ 座標**：
   $x = \frac{\pi}{4}$ のとき $4x = \pi$ であるから、$\sin\pi = 0, \cos\pi = -1$。
   $$f\left(\frac{\pi}{4}\right) = \frac{1}{2}\left(\frac{\pi}{4}\right)^2 - 0 - \frac{1}{8}(-1) + \frac{1}{8} = \frac{\pi^2}{32} + \frac{1}{4}$$
2. **接線の傾き**：
   $$f'\left(\frac{\pi}{4}\right) = \frac{\pi}{4}\left(4\sin^2\frac{\pi}{2} - 1\right) = \frac{\pi}{4}(4 \cdot 1 - 1) = \frac{3\pi}{4}$$
3. **接線の方程式**：
   $$y - \left(\frac{\pi^2}{32} + \frac{1}{4}\right) = \frac{3\pi}{4}\left(x - \frac{\pi}{4}\right)$$
   $$y = \frac{3}{4}\pi x - \frac{3\pi^2}{16} + \frac{\pi^2}{32} + \frac{1}{4} = \frac{3}{4}\pi x - \frac{5}{32}\pi^2 + \frac{1}{4}$$
問題文の形式 $y = \text{U}\pi x - \text{V}\pi^2 + \text{W}$ より：
- $\text{U}$ は $\frac{3}{4}$ で $\textcircled{3}$
- $\text{V}$ は $\frac{5}{32}$ で $\textcircled{8}$
- $\text{W}$ は $\frac{1}{4}$ で $\textcircled{2}$
よって、$\mathbf{U = 3, V = 8, W = 2} \implies \mathbf{UVW = 382}$。
