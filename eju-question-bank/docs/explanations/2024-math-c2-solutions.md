# 2024年度 日本留学試験（EJU）数学コース2 詳細解答と解説

## 正解一覧

| 大問 | 小問 | 解答番号 | 正解 | 備考・要約 |
| :--- | :--- | :--- | :--- | :--- |
| **第I問** | 問1 (1) | A | **3** | 頂点 $x$ 座標 |
| | | BC | **92** | 頂点 $y$ 座標 $-9a+2b$ |
| | (2) | D | **1** | $a>0$ 最大値をとる $x$ |
| | | E | **3** | $a>0$ 最小値をとる $x$ |
| | | F | **2** | $a = 2$ |
| | | G | **8** | $b = 8$ |
| | (3) | H | **3** | $a<0$ 最大値をとる $x$ |
| | | I | **1** | $a<0$ 最小値をとる $x$ |
| | | JK | **-2** | $a = -2$ |
| | | LM | **-6** | $b = -6$ |
| | (4) | N | **4** | $y$ 軸方向の平行移動量 |
| | 問2 (1) | OPQ | **584** | 同色の確率 $5/84$ |
| | | RS | **27** | 異色の確率 $24/84 = 2/7$ |
| | (2) | TUV | **121** | 数の和が10の確率 $4/84 = 1/21$ |
| | (3) | WXYZ | **2328** | 2色以上かつ偶数含有の確率 $23/28$ |
| **第II問** | 問1 (1) | A | **3** | $\vec{DE} = (s-1)\vec{a}-s\vec{b}+t\vec{c}$ |
| | | B | **8** | $13s-2t-9 = 0$ |
| | | C | **2** | $s = 2t$ |
| | | DE | **34** | $s = 3/4$ |
| | | FG | **38** | $t = 3/8$ |
| | (2) | HI | **32** | $DE = 3/2$ |
| | | JKL | **345** | $OD = (3/4)\sqrt{5}$ |
| | | M | **5** | $\cos \angle DOE = \sqrt{5}/5$ |
| | 問2 (1) | NO | **31** | $\gamma = \sqrt{3}+(a+1)i$ |
| | | PQR | **313** | $\delta = (1+\sqrt{3})+(a+1-\sqrt{3})i$ |
| | | S | **2** | $|\gamma-\delta| = 2$ |
| | | TU | **23** | $\arg(\gamma-\delta) = 2\pi/3$ |
| | (2) | V | **0** | $w + \bar{w} = 0$ |
| | | WXY | **223** | $a = 2+2\sqrt{3}$ |
| **第III問** | (1) | ABCDEF | **264641** | $g(t) = 2t^3+(a+6)t^2+(4a-b+6)t+4a-1$ |
| | | GH | **62** | $g'(t) = 6t^2+2(a+6)t+4a-b+6$ |
| | | IJ | **-2** | 極大値をとる $t = -2$ |
| | | K | **6** | $b = 6$ |
| | (2) | LMN | **232** | $g'(t) = 2(3t+a)(t+2)$ |
| | | OPQRS | **61219** | $p^3+6p^2+12p-19 = 0$ |
| | (3) | TUVW | **1719** | $(p-1)(p^2+7p+19) = 0$ |
| | | X | **3** | $a = -3$ |
| | | Y | **3** | $k = 3$ |
| **第IV問** | (1) | AB | **22** | $\cos x = \sqrt{2a}/2$ |
| | | CD | **02** | 解の存在範囲 $0 < a < 2$ |
| | (2) | EF | **-1** | 直交条件 $f'(t)g'(t) = -1$ |
| | | GH | **34** | $a = 3/4$ |
| | | IJK | **-12** | $f'(t) = -1/2$ |
| | (3) | L | **2** | $g'(t) = 2$ |
| | | MNOPQR | **185338** | $S = (1/8)(5+3\log(3/8))$ |

---

## 逐問詳細推導と解説


---

## 第I問 問1：2次関数の最大・最小とグラフの対称移動・平行移動

**【考查考点】**：2次関数の頂点・平方完成, 動く係数と定義域における最大値・最小値の決定, 放物線のx軸対称移動とy軸平行移動

### 【第I問 問1】詳細解答と解説

**【題目大意】**
2次関数 $y = ax^2 - 6ax + 2b$ について、定義域 $1 \le x \le 4$ における最大値が $6$、最小値が $-2$ となる定数 $a, b$ を決定する問題。

#### (1) 放物線の頂点座標の算出
与えられた2次関数 $y = ax^2 - 6ax + 2b$ を平方完成する：
$$y = a(x^2 - 6x) + 2b = a((x - 3)^2 - 9) + 2b = a(x - 3)^2 - 9a + 2b$$
したがって、放物線の頂点の座標は **$(3, -9a + 2b)$** である。
問題文の形式 $(\text{A}, -\text{B}a + \text{C}b)$ と照合すると：
$$\mathbf{A = 3, B = 9, C = 2}$$（解答番号 $\mathbf{A = 3, BC = 92}$）。

#### (2) $a > 0$ の場合（下に凸の放物線）
放物線の軸は $x = 3$ であり、定義域 $1 \le x \le 4$ の内部に含まれる。
- 軸 $x = 3$ からの距離を比較すると、左端 $x = 1$ までの距離は $|1 - 3| = 2$、右端 $x = 4$ までの距離は $|4 - 3| = 1$。
- $a > 0$ のときグラフは下に凸であるため、軸から最も遠い左端 $x = 1$ で最大値をとり、頂点 $x = 3$ で最小値をとる。
よって：
$$\mathbf{D = 1, E = 3}$$

条件より最大値が $6$、最小値が $-2$ であるから：
$$y(1) = a(1)^2 - 6a(1) + 2b = -5a + 2b = 6 \quad \cdots (\text{i})$$
$$y(3) = -9a + 2b = -2 \quad \cdots (\text{ii})$$
$(\text{i}) - (\text{ii})$ より：
$$(-5a + 2b) - (-9a + 2b) = 6 - (-2) \implies 4a = 8 \implies \mathbf{a = 2}$$
これを $(\text{ii})$ に代入して：
$$-9(2) + 2b = -2 \implies 2b = 16 \implies \mathbf{b = 8}$$
$a = 2 > 0$ を満たすので適する。
よって、$\mathbf{F = 2, G = 8}$ である。

#### (3) $a < 0$ の場合（上に凸の放物線）
$a < 0$ のときグラフは上に凸であるため：
- 頂点 $x = 3$ で最大値をとり、軸から最も遠い左端 $x = 1$ で最小値をとる。
よって：
$$\mathbf{H = 3, I = 1}$$

条件より最大値が $6$、最小値が $-2$ であるから：
$$y(3) = -9a + 2b = 6 \quad \cdots (\text{iii})$$
$$y(1) = -5a + 2b = -2 \quad \cdots (\text{iv})$$
$(\text{iv}) - (\text{iii})$ より：
$$(-5a + 2b) - (-9a + 2b) = -2 - 6 \implies 4a = -8 \implies \mathbf{a = -2}$$
これを $(\text{iv})$ に代入して：
$$-5(-2) + 2b = -2 \implies 10 + 2b = -2 \implies 2b = -12 \implies \mathbf{b = -6}$$
$a = -2 < 0$ を満たすので適する。
よって、$\mathbf{JK = -2, LM = -6}$ である。

#### (4) グラフの対称移動と平行移動の関係
(2) で求めた2次関数は $f(x) = 2x^2 - 12x + 16$。
(3) で求めた2次関数は $g(x) = -2x^2 + 12x - 12$。
$f(x)$ のグラフを $x$ 軸に関して対称移動した放物線の方程式は：
$$y = -f(x) = -(2x^2 - 12x + 16) = -2x^2 + 12x - 16$$
この放物線を $y$ 軸方向に $N$ だけ平行移動すると：
$$y = -2x^2 + 12x - 16 + N$$
これが $g(x) = -2x^2 + 12x - 12$ に一致するためには：
$$-16 + N = -12 \implies \mathbf{N = 4}$$
よって、$\mathbf{N = 4}$ である。

---

## 第I問 問2：3色カードの同時抽出・確率と余事象の計算

**【考查考点】**：組合せの総数 $\binom{n}{r}$, 同色・異色の確率計算, 条件を満たす整数の和の組合せ, 余事象と包除原理の応用

### 【第I問 問2】詳細解答と解説

**【題目大意】**
袋の中に白色カード2枚（1, 2）、赤色カード3枚（3, 4, 5）、青色カード4枚（6, 7, 8, 9）の計9枚が入っている。
この袋から同時に3枚のカードを取り出す試行を行う。すべての取り出し方の総数は：
$$N = \binom{9}{3} = \frac{9 \times 8 \times 7}{3 \times 2 \times 1} = 84$$

#### (1) 同色および全異色の確率
1. **3枚とも同じ色である事象**：
   - 白色は2枚しかないため、白色3枚はあり得ない。
   - 赤色3枚を取り出す方法：$\binom{3}{3} = 1$ 通り。
   - 青色3枚を取り出す方法：$\binom{4}{3} = 4$ 通り。
   合計 $1 + 4 = 5$ 通り。
   したがって、確率は $\frac{5}{84}$ である。よって $\mathbf{OPQ = 584}$。

2. **3枚とも異なる色である事象**：
   白色から1枚、赤色から1枚、青色から1枚を取り出す方法：
   $$\binom{2}{1} \times \binom{3}{1} \times \binom{4}{1} = 2 \times 3 \times 4 = 24 \text{ 通り}$$
   したがって、確率は $\frac{24}{84} = \frac{2}{7}$ である。よって $\mathbf{RS = 27}$。

#### (2) 取り出された3枚のカードの数の和が10である確率
取り出せるカードの数は 1 から 9 までの相異なる3数である。
和が 10 となる 3 数の組合せ $(x < y < z)$ を辞書式に漏れなく列挙する：
- $x = 1$ のとき：$y + z = 9$ かつ $1 < y < z$ より：
  - $(1, 2, 7)$
  - $(1, 3, 6)$
  - $(1, 4, 5)$
- $x = 2$ のとき：$y + z = 8$ かつ $2 < y < z$ より：
  - $(2, 3, 5)$
- $x \ge 3$ のとき：最小の和は $3 + 4 + 5 = 12 > 10$ となり存在しない。
該当する組合せは上記の **4通り** のみである。
各カードはすべて数字が異なるため、それぞれ1通りずつ取り出せる。
したがって、和が 10 となる確率は：
$$\frac{4}{84} = \frac{1}{21}$$
よって、$\mathbf{TUV = 121}$ である。

#### (3) 異なる色のカードが少なくとも2枚含まれ、かつ偶数が少なくとも1枚含まれる確率
全事象 $U$（$|U| = 84$）において、条件を満たさない事象の余事象を考える。
- 事象 $A$：「3枚のカードがすべて同じ色である」
- 事象 $B$：「3枚のカードがすべて奇数である」
求める事象は $\overline{A} \cap \overline{B} = \overline{A \cup B}$ である。

1. **$|A|$ の要素数**：
   (1) より、すべて同色となるのは 5 通り（赤3枚：{3,4,5}、青3枚：{6,7,8}, {6,7,9}, {6,8,9}, {7,8,9}）。
   この 5 通りにはいずれも少なくとも 1 枚の偶数（赤なら4、青なら6または8）が含まれている。
2. **$|B|$ の要素数（すべて奇数）**：
   カードの中の奇数は {1, 3, 5, 7, 9} の計 5 枚（白1枚、赤2枚、青2枚）。
   この 5 枚から 3 枚を取り出す方法の総数は：
   $$|B| = \binom{5}{3} = 10 \text{ 通り}$$
3. **$A \cap B$ の要素数（同色かつすべて奇数）**：
   同色で3枚取り出すには赤または青でなければならないが、赤の奇数は2枚（3,5）、青の奇数は2枚（7,9）しかなく、3枚の奇数を同じ色から取ることはできない。
   したがって、$A \cap B = \emptyset$（空集合、0通り）である。

よって、包除原理より：
$$|A \cup B| = |A| + |B| - |A \cap B| = 5 + 10 - 0 = 15 \text{ 通り}$$
求める事象の要素数は：
$$84 - 15 = 69 \text{ 通り}$$
したがって、求める確率は：
$$\frac{69}{84} = \frac{23}{28}$$
よって、$\mathbf{WXYZ = 2328}$ である。

---

## 第II問 問1：四面体の空間ベクトル・共通垂線と内積計算

**【考查考点】**：空間ベクトルの内分点表現, 共通垂線条件 $\vec{DE} \perp \vec{AB}$ かつ $\vec{DE} \perp \vec{OC}$, ベクトルの内積と長さ・$\cos \theta$ の計算

### 【第II問 問1】詳細解答と解説

**【題目大意】**
四面体 $OABC$ において：
$$OA = 3, \quad OB = OC = 2$$
$$\angle AOB = \angle AOC = \frac{\pi}{2}, \quad \angle BOC = \frac{\pi}{3}$$
辺 $AB$ 上の点 $D$ と辺 $OC$ 上の点 $E$ が、$\vec{DE} \perp \vec{AB}$ かつ $\vec{DE} \perp \vec{OC}$ を満たすとき、点 $D, E$ の位置および線分の長さを求める。

#### (1) 基本内積の準備と $\vec{DE}$ のベクトル表示
$\vec{a} = \overrightarrow{OA}, \vec{b} = \overrightarrow{OB}, \vec{c} = \overrightarrow{OC}$ とおく。
与えられた条件より：
- $|\vec{a}|^2 = 3^2 = 9, \quad |\vec{b}|^2 = 2^2 = 4, \quad |\vec{c}|^2 = 2^2 = 4$
- $\vec{a} \cdot \vec{b} = |\vec{a}||\vec{b}|\cos \frac{\pi}{2} = 0$
- $\vec{a} \cdot \vec{c} = |\vec{a}||\vec{c}|\cos \frac{\pi}{2} = 0$
- $\vec{b} \cdot \vec{c} = |\vec{b}||\vec{c}|\cos \frac{\pi}{3} = 2 \times 2 \times \frac{1}{2} = 2$

点 $D$ は辺 $AB$ を $s : (1-s)$ に内分するので：
$$\overrightarrow{OD} = (1-s)\vec{a} + s\vec{b}$$
点 $E$ は辺 $OC$ を $t : (1-t)$ に内分するので：
$$\overrightarrow{OE} = t\vec{c}$$
したがって、$\overrightarrow{DE} = \overrightarrow{OE} - \overrightarrow{OD}$ は：
$$\overrightarrow{DE} = t\vec{c} - ((1-s)\vec{a} + s\vec{b}) = (s-1)\vec{a} - s\vec{b} + t\vec{c}$$
選択肢一覧の $\textcircled{3}$「$(s-1)\vec{a} - s\vec{b} + t\vec{c}$」に一致する。よって $\mathbf{A = 3}$ である。

#### (2) 垂直条件による $s, t$ の決定
1. $\overrightarrow{DE} \perp \overrightarrow{AB}$：
   $\overrightarrow{AB} = \vec{b} - \vec{a}$ であるから：
   $$\overrightarrow{DE} \cdot \overrightarrow{AB} = ((s-1)\vec{a} - s\vec{b} + t\vec{c}) \cdot (\vec{b} - \vec{a}) = 0$$
   展開すると：
   $$-(s-1)|\vec{a}|^2 - s|\vec{b}|^2 + t(\vec{b} \cdot \vec{c}) = 0$$
   $$-9(s-1) - 4s + 2t = 0 \implies 9 - 9s - 4s + 2t = 0 \implies 9 - 13s + 2t = 0$$
   符号を反転して $13s - 2t - 9 = 0$。
   これは選択肢 $\textcircled{8}$「$13s - 2t - 9$」に一致する。よって $\mathbf{B = 8}$ である。

2. $\overrightarrow{DE} \perp \overrightarrow{OC}$：
   $\overrightarrow{OC} = \vec{c}$ であるから：
   $$\overrightarrow{DE} \cdot \vec{c} = ((s-1)\vec{a} - s\vec{b} + t\vec{c}) \cdot \vec{c} = 0$$
   $$-s(\vec{b} \cdot \vec{c}) + t|\vec{c}|^2 = 0 \implies -2s + 4t = 0 \implies s = 2t$$
   問題文の $s = \text{C}t$ より $\mathbf{C = 2}$ である。

3. $s, t$ の値を解く：
   $s = 2t$ を $13s - 2t - 9 = 0$ に代入すると：
   $$13(2t) - 2t - 9 = 0 \implies 24t = 9 \implies t = \frac{9}{24} = \frac{3}{8}$$
   $$s = 2 \times \frac{3}{8} = \frac{3}{4}$$
   したがって、$\mathbf{DE = 34, FG = 38}$ である。

#### (3) 線分 DE の長さと $\cos \angle DOE$ の計算
$s = \frac{3}{4}, t = \frac{3}{8}$ より、$\overrightarrow{DE} = -\frac{1}{4}\vec{a} - \frac{3}{4}\vec{b} + \frac{3}{8}\vec{c}$。
$$|\overrightarrow{DE}|^2 = \left(-\frac{1}{4}\right)^2 |\vec{a}|^2 + \left(-\frac{3}{4}\right)^2 |\vec{b}|^2 + \left(\frac{3}{8}\right)^2 |\vec{c}|^2 + 2\left(-\frac{3}{4}\right)\left(\frac{3}{8}\right)(\vec{b} \cdot \vec{c})$$
$$= \frac{9}{16} + \frac{36}{16} + \frac{36}{64} - \frac{36}{32} = \frac{45}{16} + \frac{9}{16} - \frac{18}{16} = \frac{36}{16} = \frac{9}{4}$$
したがって、$DE = \sqrt{\frac{9}{4}} = \frac{3}{2}$（$\mathbf{HI = 32}$）。

次に、$\overrightarrow{OD} = \frac{1}{4}\vec{a} + \frac{3}{4}\vec{b}$ より：
$$|\overrightarrow{OD}|^2 = \frac{1}{16}|\vec{a}|^2 + \frac{9}{16}|\vec{b}|^2 = \frac{9}{16} + \frac{36}{16} = \frac{45}{16} \implies OD = \frac{3\sqrt{5}}{4}$$
問題文の形式 $\frac{\text{J}}{\text{K}}\sqrt{\text{L}}$ と照合して $\mathbf{JKL = 345}$。

また、$\overrightarrow{DE} \perp \overrightarrow{OC}$ であるから、$\triangle ODE$ は $\angle OED = \frac{\pi}{2}$ の直角三角形である。
直角三角形において：
$$\cos \angle DOE = \frac{OE}{OD} = \frac{t |\vec{c}|}{OD} = \frac{\frac{3}{8} \times 2}{\frac{3\sqrt{5}}{4}} = \frac{\frac{3}{4}}{\frac{3\sqrt{5}}{4}} = \frac{1}{\sqrt{5}} = \frac{\sqrt{5}}{5}$$
したがって、$\mathbf{M = 5}$ である。

---

## 第II問 問2：複素数平面における回転移動・絶対値・偏角と直交条件

**【考查考点】**：複素数の極形式と回転移動公式 $z' - z_0 = (z - z_0)e^{i\theta}$, 複素数の絶対値と偏角 $\arg(z)$, 純虚数条件 $w + \overline{w} = 0$ による直線直交の決定

### 【第II問 問2】詳細解答と解説

**【題目大意】**
複素数平面上に 2点 $A(ai), B((a+2)i)$ をとる（$a \in \mathbb{R}$）。
- 点 $B$ を点 $A$ を中心として $-\frac{\pi}{3}$ だけ回転させた点を $C(\gamma)$ とする。
- 点 $A$ を点 $C$ を中心として $\frac{\pi}{2}$ だけ回転させた点を $D(\delta)$ とする。
このとき、$\gamma - \delta$ の絶対値と偏角、および直線 $AD$ と $OC$ が直交する実数 $a$ の値を求める。

#### (1) $\gamma, \delta$ の表示と差の絶対値・偏角
1. **点 $C(\gamma)$ の算出**：
   点 $A(ai)$ 中心の $-\frac{\pi}{3}$ 回転より：
   $$\gamma - ai = ((a+2)i - ai) \left(\cos\left(-\frac{\pi}{3}\right) + i\sin\left(-\frac{\pi}{3}\right)\right)$$
   $$\gamma - ai = 2i \left(\frac{1}{2} - i\frac{\sqrt{3}}{2}\right) = i + \sqrt{3}$$
   したがって：
   $$\gamma = \sqrt{3} + (a + 1)i$$
   問題文の形式 $\sqrt{\text{N}} + (a + \text{O})i$ と照合して $\mathbf{NO = 31}$。

2. **点 $D(\delta)$ の算出**：
   点 $A$ を点 $C$ を中心として $\frac{\pi}{2}$ 回転させた点が $D$ であるから：
   $$\delta - \gamma = (ai - \gamma) \left(\cos\frac{\pi}{2} + i\sin\frac{\pi}{2}\right) = (ai - \gamma) i$$
   $$\delta = \gamma + (ai - \gamma)i = \gamma(1 - i) - a$$
   $\gamma = \sqrt{3} + (a+1)i$ を代入して整理する：
   $$\delta - \gamma = (ai - (\sqrt{3} + (a+1)i))i = (-\sqrt{3} - i)i = -\sqrt{3}i + 1 = 1 - \sqrt{3}i$$
   したがって：
   $$\delta = \gamma + (1 - \sqrt{3}i) = \sqrt{3} + (a+1)i + 1 - \sqrt{3}i = (1 + \sqrt{3}) + (a + 1 - \sqrt{3})i$$
   問題文の形式 $1 + \sqrt{\text{P}} + (a + \text{Q} - \sqrt{\text{R}})i$ と照合して：
   $$\mathbf{P = 3, Q = 1, R = 3}$$（解答番号 $\mathbf{PQR = 313}$）。

3. **$\gamma - \delta$ の絶対値と偏角**：
   $$\gamma - \delta = -(1 - \sqrt{3}i) = -1 + \sqrt{3}i$$
   絶対値：
   $$|\gamma - \delta| = \sqrt{(-1)^2 + (\sqrt{3})^2} = \sqrt{1 + 3} = 2$$
   したがって $\mathbf{S = 2}$ である。
   偏角（$0 \le \arg < 2\pi$）：
   $$-1 + \sqrt{3}i = 2\left(-\frac{1}{2} + i\frac{\sqrt{3}}{2}\right) = 2\left(\cos\frac{2\pi}{3} + i\sin\frac{2\pi}{3}\right)$$
   したがって、$\arg(\gamma - \delta) = \frac{2}{3}\pi$（$\mathbf{TU = 23}$）。

#### (2) 直線 $AD$ と $OC$ の直交条件と $a$ の決定
直線 $AD$ を表すベクトルは $\delta - ai = (1 + \sqrt{3}) + (1 - \sqrt{3})i$。
直線 $OC$ を表すベクトルは $\gamma - 0 = \sqrt{3} + (a + 1)i$。
$AD \perp OC$ であるとき、その商 $w = \frac{\delta - ai}{\gamma}$ は純虚数となる。
複素数が純虚数であるための必要十分条件は $w + \overline{w} = 0$（かつ $w \neq 0$）であるから：
$$w + \overline{w} = 0 \implies \mathbf{V = 0}$$

これは $\text{Re}((\delta - ai)\overline{\gamma}) = 0$ と同値である：
$$(\delta - ai)\overline{\gamma} = [((1 + \sqrt{3}) + (1 - \sqrt{3})i)] [\sqrt{3} - (a+1)i]$$
その実部は：
$$\text{Re} = (1 + \sqrt{3})\sqrt{3} + (1 - \sqrt{3})(a + 1) = 0$$
展開すると：
$$\sqrt{3} + 3 + (1 - \sqrt{3})a + 1 - \sqrt{3} = 0$$
$$4 + (1 - \sqrt{3})a = 0 \implies (\sqrt{3} - 1)a = 4$$
有理化して $a$ を求める：
$$a = \frac{4}{\sqrt{3} - 1} = \frac{4(\sqrt{3} + 1)}{3 - 1} = 2(\sqrt{3} + 1) = 2 + 2\sqrt{3}$$
問題文の形式 $a = \text{W} + \text{X}\sqrt{\text{Y}}$ と照合して：
$$\mathbf{W = 2, X = 2, Y = 3}$$（解答番号 $\mathbf{WXY = 223}$）。

---

## 第III問（前半）：対数関数の三次関数置換と導関数・極値条件

**【考查考点】**：底の変換公式と対数計算, 変数変換 $t = \log_3 x$ による3次関数の導入, 極値の必要条件 $g'(-2) = 0$ による未定係数 $b$ の決定

### 【第III問 前半】詳細解答と解説

**【題目大意】**
関数 $f(x) = 2(\log_3 3x)^3 + a(\log_3 9x)^2 + b\log_{\frac{1}{3}}x + \log_{\frac{1}{3}}27$ が $x = \frac{1}{9}$ で極大値をとり、$x = k$ で極小値 $-20$ をとる条件から定数 $a, b, k$ を決定する。

#### (1) $t = \log_3 x$ による式の多項式化
各対数項を $t = \log_3 x$ で表す：
- $\log_3 3x = \log_3 3 + \log_3 x = 1 + t = t + 1$
  $(\log_3 3x)^3 = (t + 1)^3 = t^3 + 3t^2 + 3t + 1$
  $2(\log_3 3x)^3 = 2t^3 + 6t^2 + 6t + 2$
- $\log_3 9x = \log_3 9 + \log_3 x = 2 + t = t + 2$
  $(\log_3 9x)^2 = (t + 2)^2 = t^2 + 4t + 4$
  $a(\log_3 9x)^2 = at^2 + 4at + 4a$
- $\log_{\frac{1}{3}}x = \frac{\log_3 x}{\log_3 3^{-1}} = -t \implies b\log_{\frac{1}{3}}x = -bt$
- $\log_{\frac{1}{3}}27 = \frac{\log_3 3^3}{\log_3 3^{-1}} = \frac{3}{-1} = -3$

すべてを合算して $t$ について降べきの順に整理する：
$$g(t) = 2t^3 + (6 + a)t^2 + (6 + 4a - b)t + (2 + 4a - 3)$$
$$g(t) = 2t^3 + (a + 6)t^2 + (4a - b + 6)t + 4a - 1$$
問題文の形式 $\text{A}t^3 + (a + \text{B})t^2 + (\text{C}a - b + \text{D})t + \text{E}a - \text{F}$ と照合して：
$$\mathbf{A = 2, B = 6, C = 4, D = 6, E = 4, F = 1}$$
解答番号 $\mathbf{ABCDEF = 264641}$ である。

#### (2) 導関数 $g'(t)$ の算出と極大値条件
$g(t)$ を $t$ で微分すると：
$$g'(t) = 6t^2 + 2(a + 6)t + 4a - b + 6$$
問題文の形式 $\text{G}t^2 + \text{H}(a + \text{B})t + \text{C}a - b + \text{D}$ と比較して：
$$\mathbf{G = 6, H = 2}$$
解答番号 $\mathbf{GH = 62}$ である。

$f(x)$ が $x = \frac{1}{9}$ で極大値をとるとき、$t = \log_3 \frac{1}{9} = -2$ で $g(t)$ は極大値をとる。
したがって、解答番号 $\mathbf{IJ = -2}$ である。
極値をとる必要条件として $g'(-2) = 0$ が成り立つ：
$$g'(-2) = 6(-2)^2 + 2(a + 6)(-2) + 4a - b + 6 = 0$$
$$24 - 4(a + 6) + 4a - b + 6 = 0$$
$$24 - 4a - 24 + 4a - b + 6 = 0 \implies 6 - b = 0 \implies \mathbf{b = 6}$$
したがって、解答番号 $\mathbf{K = 6}$ である。

---

## 第III問（後半）：因数分解・極小値条件と三次方程式の有理解・定数決定

**【考查考点】**：導関数の因数分解, 3次方程式の因数定理による解法, 極値の符号判定と定数 $a, k$ の確定

### 【第III問 後半】詳細解答と解説

#### (1) $g'(t)$ の因数分解
$b = 6$ を代入すると、定数項は $4a - 6 + 6 = 4a$ となり：
$$g'(t) = 6t^2 + 2(a + 6)t + 4a = 2[3t^2 + (a + 6)t + 2a]$$
たすき掛けにより因数分解する：$3t^2 + (a + 6)t + 2a = (3t + a)(t + 2)$。
したがって：
$$g'(t) = 2(3t + a)(t + 2)$$
問題文の形式 $\text{L}(\text{M}t + a)(t + \text{N})$ と照合して：
$$\mathbf{L = 2, M = 3, N = 2}$$
解答番号 $\mathbf{LMN = 232}$ である。

#### (2) 極小値条件と $p$ の三次方程式
3次関数 $g(t)$ の最高次係数は $2 > 0$ である。
$t = -2$ で極大値をとるため、もう一つの零点 $t = -\frac{a}{3}$ は極小値を与える。
したがって $p = -\frac{a}{3} > -2$ であり、$\mathbf{a = -3p}$（$\mathbf{M = 3}$）である。

$g(p) = -20$ に $a = -3p, b = 6$ を代入して整理する：
$$g(p) = 2p^3 + (-3p + 6)p^2 + (4(-3p) - 6 + 6)p + 4(-3p) - 1$$
$$= 2p^3 - 3p^3 + 6p^2 - 12p^2 - 12p - 1 = -p^3 - 6p^2 - 12p - 1$$
これが $-20$ に等しい：
$$-p^3 - 6p^2 - 12p - 1 = -20 \implies p^3 + 6p^2 + 12p - 19 = 0$$
問題文の形式 $p^3 + \text{O}p^2 + \text{PQ}p - \text{RS} = 0$ と照合して：
$$\mathbf{O = 6, PQ = 12, RS = 19}$$
解答番号 $\mathbf{OPQRS = 61219}$ である。

#### (3) 三次方程式の因数分解と定数の決定
$P(p) = p^3 + 6p^2 + 12p - 19$ とおくと、$P(1) = 1 + 6 + 12 - 19 = 0$。
したがって $p - 1$ を因数にもつ。組立除法を行うと：
$$p^3 + 6p^2 + 12p - 19 = (p - 1)(p^2 + 7p + 19) = 0$$
問題文の形式 $(p - \text{T})(p^2 + \text{U}p + \text{VW}) = 0$ と照合して：
$$\mathbf{T = 1, U = 7, VW = 19}$$
解答番号 $\mathbf{TUVW = 1719}$ である。

$p^2 + 7p + 19 = \left(p + \frac{7}{2}\right)^2 + \frac{27}{4} > 0$ であるから、実数解は $\mathbf{p = 1}$ に限られる。
したがって：
- $a = -3p = -3(1) = -3$ より、$\mathbf{X = 3}$（$a = -\text{X}$）。
- $p = \log_3 k = 1 \implies k = 3^1 = 3$ より、$\mathbf{Y = 3}$ である。

---

## 第IV問（前半）：三角関数曲線の共有点と直交接線の条件

**【考查考点】**：三角方程式の解法 $\sin 2x = a\tan x$, 共有点が存在するパラメータの範囲, 曲線の接線と直交条件 $f'(t)g'(t) = -1$

### 【第IV問 前半】詳細解答と解説

**【題目大意】**
$a > 0$ とし、$0 \le x < \frac{\pi}{2}$ において $C_1: y = \sin 2x$ と $C_2: y = a\tan x$ を考える。
原点以外の共有点が存在する条件、および共有点における2曲線の接線が直交する条件を求める。

#### (1) 原点以外の共有点が存在する $a$ の範囲
方程式 $f(x) = g(x) \iff \sin 2x = a\tan x \quad \cdots \textcircled{1}$。
$0 < x < \frac{\pi}{2}$ の範囲では $\cos x > 0$ かつ $\sin x > 0$ である。
倍角の公式 $\sin 2x = 2\sin x \cos x$ および $\tan x = \frac{\sin x}{\cos x}$ を代入すると：
$$2\sin x \cos x = a \frac{\sin x}{\cos x}$$
両辺を $\sin x > 0$ で割ると：
$$2\cos x = \frac{a}{\cos x} \implies \cos^2 x = \frac{a}{2}$$
$\cos x > 0$ より：
$$\cos x = \sqrt{\frac{a}{2}} = \frac{\sqrt{2a}}{2}$$
問題文の形式 $\frac{\sqrt{\text{A}a}}{\text{B}}$ と照合して $\mathbf{AB = 22}$ である。

$0 < x < \frac{\pi}{2}$ において $0 < \cos x < 1$ であるから、解が存在する必要十分条件は：
$$0 < \frac{\sqrt{2a}}{2} < 1 \iff 0 < \sqrt{2a} < 2 \iff 0 < 2a < 4 \iff 0 < a < 2$$
したがって、$\mathbf{C = 0, D = 2}$（解答番号 $\mathbf{CD = 02}$）である。
このとき、$\cos x$ は区間内で狭義単調減少するため、解はただ1つ存在する。

#### (2) 接線の直交条件と $a$ の決定
共有点 $P$ の $x$ 座標を $t$ とおく。$\cos^2 t = \frac{a}{2}$ が成り立つ。
各関数の導関数を求める：
- $f'(x) = 2\cos 2x = 2(2\cos^2 x - 1)$
  $x = t$ のとき：$f'(t) = 2\left(2 \cdot \frac{a}{2} - 1\right) = 2(a - 1)$
- $g'(x) = \frac{a}{\cos^2 x}$
  $x = t$ のとき：$g'(t) = \frac{a}{a/2} = 2$

接線 $\ell_1, \ell_2$ が直交する条件は：
$$f'(t) g'(t) = -1 \implies \mathbf{EF = -1}$$
代入すると：
$$2(a - 1) \times 2 = -1 \implies 4(a - 1) = -1 \implies 4a - 4 = -1 \implies 4a = 3$$
したがって：
$$a = \frac{3}{4}$$
これは $0 < a < 2$ を満たす。よって $\mathbf{GH = 34}$ である。

このとき、各接線の傾きは：
- $f'(t) = 2\left(\frac{3}{4} - 1\right) = 2\left(-\frac{1}{4}\right) = -\frac{1}{2}$
  問題文の形式 $\frac{\text{IJ}}{\text{K}}$ と照合して $\mathbf{IJK = -12}$。

---

## 第IV問（後半）：接線の傾きと2曲線で囲まれる図形の面積積分

**【考查考点】**：三角関数の接線の傾きの決定, 定積分による面積の計算 $S = \int (f(x) - g(x))dx$, $\tan x$ の不定積分と対数計算

### 【第IV問 後半】詳細解答と解説

#### (1) 接線の傾き $g'(t)$ の決定
前半で求めたように、任意の共有点 $t$ において：
$$g'(t) = \frac{a}{\cos^2 t} = \frac{a}{a/2} = 2$$
したがって、接線 $\ell_2$ の傾きは常に一定値 **$2$** である。
よって、$\mathbf{L = 2}$ である。

#### (2) 2曲線で囲まれる面積 $S$ の定積分
$a = \frac{3}{4}$ のとき、共有点 $t$ について：
$$\cos^2 t = \frac{a}{2} = \frac{3/4}{2} = \frac{3}{8}$$
$0 < x < t$ において、$C_1$ のグラフは $C_2$ のグラフの上側にある（$f(x) \ge g(x)$）。
したがって、囲まれる面積 $S$ は：
$$S = \int_0^t (\sin 2x - a\tan x) \, dx = \int_0^t \left(\sin 2x - \frac{3}{4}\tan x\right) \, dx$$

不定積分を求める：
- $\int \sin 2x \, dx = -\frac{1}{2}\cos 2x$
- $\int \tan x \, dx = -\log|\cos x|$
したがって：
$$\int \left(\sin 2x - \frac{3}{4}\tan x\right) \, dx = -\frac{1}{2}\cos 2x + \frac{3}{4}\log(\cos x)$$

積分区間 $[0, t]$ で評価する：
$$S = \left[ -\frac{1}{2}(2\cos^2 x - 1) + \frac{3}{4}\log(\cos x) \right]_0^t = \left[ -\cos^2 x + \frac{1}{2} + \frac{3}{4}\log(\cos x) \right]_0^t$$
$x = t$ のとき：
$$-\cos^2 t + \frac{1}{2} + \frac{3}{4}\log(\cos t) = -\frac{3}{8} + \frac{1}{2} + \frac{3}{4}\log\sqrt{\frac{3}{8}} = \frac{1}{8} + \frac{3}{8}\log\frac{3}{8}$$
$x = 0$ のとき：
$$-\cos^2 0 + \frac{1}{2} + \frac{3}{4}\log(\cos 0) = -1 + \frac{1}{2} + 0 = -\frac{1}{2}$$
したがって：
$$S = \left(\frac{1}{8} + \frac{3}{8}\log\frac{3}{8}\right) - \left(-\frac{1}{2}\right) = \frac{1}{8} + \frac{4}{8} + \frac{3}{8}\log\frac{3}{8} = \frac{5}{8} + \frac{3}{8}\log\frac{3}{8}$$
これを共通因数 $\frac{1}{8}$ でくくり出すと：
$$S = \frac{1}{8}\left(5 + 3\log\frac{3}{8}\right)$$
問題文の形式 $S = \frac{\text{M}}{\text{N}}\left(\text{O} + \text{P}\log\frac{\text{Q}}{\text{R}}\right)$ と照合すると：
$$\mathbf{M = 1, N = 8, O = 5, P = 3, Q = 3, R = 8}$$
解答番号 $\mathbf{MNOPQR = 185338}$ である。
