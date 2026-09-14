# 2017-1 EJU 数学（コース2）詳細解答と徹底解説

**対象試験**：2017年度第1回（2017年6月実施）日本留学試験（EJU）数学コース2  
**大問構成**：大問I（問1, 問2）、大問II（問1, 問2）、大問III（問1, 問2）、大問IV（問1, 問2）（全8小問）  
**準拠公式正解**：JASSO 公式正解発表完全準拠

---

## 大問I 問1：2次関数の平行移動と対称移動・共有点問題
- **問題番号**：`math-q-I_1`
- **公式正解**：`{'ABCDE': '31214', 'F': '2', 'G': '8', 'HIJ': '326', 'K': '1', 'LM': '15'}`
- **重要論点**：
  - 2次関数の平行移動による係数決定と標準形への変形
  - 直線 y = c に関する線対称移動の式変形
  - 2つの放物線の共有点がただ1つとなる判別式重解条件の適用

**【題目大意】**
2次関数 $y = 3x^2 - 6$ を平行移動して2点 $(1, 5)$, $(4, 14)$ を通る放物線 $\textcircled{1}$ と、直線 $y = c$ に関して対称移動した放物線 $\textcircled{2}$ について、その方程式および $\textcircled{1}$ と $\textcircled{2}$ がただ1つの共有点をもつときの条件を求める。

**【公式正解】**
- $\text{ABCDE} = 31214$ ($y = 3x^2 - 12x + 14$)
- $\text{F} = 2, \text{G} = 8$ ($x$ 軸方向に 2、$y$ 軸方向に 8 平行移動)
- $\text{HIJ} = 326$ ($y = -3x^2 + 2c + 6$)
- $\text{K} = 1$ ($c = 1$)
- $\text{LM} = 15$ (共有点の座標 $(1, 5)$)

**【詳細推導・解答プロセス】**
**(1) 平行移動した放物線の方程式と平行移動量の特定**
$y = 3x^2 - 6$ のグラフを平行移動した放物線は、$x^2$ の係数が 3 のままであるから、$y = 3x^2 + bx + c'$ とおくことができる。
このグラフが 2 点 $(1, 5)$, $(4, 14)$ を通ることから：
$$
\begin{cases}
3(1)^2 + b(1) + c' = 5 \implies b + c' = 2 \\
3(4)^2 + b(4) + c' = 14 \implies 48 + 4b + c' = 14 \implies 4b + c' = -34
\end{cases}
$$
下の式から上の式を引くと：
$$3b = -36 \implies b = -12$$
これより $c' = 2 - (-12) = 14$ となる。
したがって、放物線の方程式は：
$$y = 3x^2 - 12x + 14$$
よって、$\text{A} = 3, \text{BC} = 12, \text{DE} = 14$ より $\mathbf{ABCDE = 31214}$ である。

次に平行移動量を求めるため、平方完成を行う：
$$y = 3(x^2 - 4x) + 14 = 3(x - 2)^2 - 12 + 14 = 3(x - 2)^2 + 2$$
元の放物線 $y = 3x^2 - 6$ の頂点は $(0, -6)$、移動後の放物線の頂点は $(2, 2)$ である。
したがって、$x$ 軸方向への移動量は $2 - 0 = 2$、
$y$ 軸方向への移動量は $2 - (-6) = 8$ である。
よって、$\mathbf{F = 2}, \mathbf{G = 8}$ である。

**(2) 直線 $y = c$ に関する対称移動と共有点の決定**
点 $(x, y)$ を直線 $y = c$ に関して対称移動した点を $(X, Y)$ とすると：
$$X = x, \quad \frac{y + Y}{2} = c \implies Y = 2c - y$$
元の放物線 $y = 3x^2 - 6$ に代入すると：
$$2c - y = 3x^2 - 6 \implies y = -3x^2 + 2c + 6$$
よって、$\text{H} = 3, \text{I} = 2, \text{J} = 6$ より $\mathbf{HIJ = 326}$ である。

2つの放物線 $\textcircled{1}$ と $\textcircled{2}$ が共有点を 1 つだけもつ条件を考える。
$$3x^2 - 12x + 14 = -3x^2 + 2c + 6$$
整理すると：
$$6x^2 - 12x + (8 - 2c) = 0 \iff 3x^2 - 6x + (4 - c) = 0$$
共有点が 1 つだけ存在するためには、この 2 次方程式が重解をもてばよい。
判別式を $D$ とすると：
$$D/4 = (-3)^2 - 3(4 - c) = 9 - 12 + 3c = 3c - 3 = 0 \implies c = 1$$
よって、$\mathbf{K = 1}$ である。

$c = 1$ のとき、方程式は：
$$3x^2 - 6x + 3 = 0 \iff 3(x - 1)^2 = 0 \implies x = 1$$
このときの $y$ 座標は：
$$y = 3(1)^2 - 12(1) + 14 = 5$$
したがって、共有点の座標は $(1, 5)$ である。
よって、$\text{L} = 1, \text{M} = 5$ より $\mathbf{LM = 15}$ である。

**【考査考点】**
2次関数の決定（未定係数法）、放物線の頂点座標と平行移動の関係、直線 $y = c$ に関する対称移動の幾何的代数化、2次方程式の判別式による接点条件（重解条件）の分析。

---

## 大問I 問2：カードの順列・組合せと非復元抽出の確率
- **問題番号**：`math-q-I_2`
- **公式正解**：`{'NO': '90', 'PQ': '12', 'RS': '33', 'TUV': '415', 'WXYZ': '1330'}`
- **重要論点**：
  - 白4枚・赤3枚・黒3枚の計10枚の相異なるカードの分配
  - 同色・異色を取り出す組合せと余事象の活用
  - 非復元抽出における条件付き事象の確率計算

**【題目大意】**
白4枚、赤3枚、黒3枚の計10枚のカード（すべて相異なる数字が記されている）からカードを選び、箱に入れたり非復元抽出したりするときの順列・組合せおよび確率を求める。

**【公式正解】**
- $\text{NO} = 90$ (全部で 90 通り)
- $\text{PQ} = 12$ (同色 12 通り)
- $\text{RS} = 33$ (異色 33 通り)
- $\text{TUV} = 415$ (同色である確率 $\frac{4}{15}$)
- $\text{WXYZ} = 1330$ (条件を満たす確率 $\frac{13}{30}$)

**【詳細推導・解答プロセス】**
**(1) 10枚から2枚を選び、箱A, Bに1枚ずつ入れる方法**
異なる10枚から相異なる2枚を選んで順序をつけて箱A, Bに入れる順列の総数は：
$$_{10}\text{P}_2 = 10 \times 9 = 90$$
よって、$\mathbf{NO = 90}$ である。

**(2) 2枚とも同じ色、および異なる色の選び方**
10枚から2枚を選ぶ組合せについて：
- 2枚とも白である選び方：$_4\text{C}_2 = \frac{4 \times 3}{2} = 6$ 通り
- 2枚とも赤である選び方：$_3\text{C}_2 = 3$ 通り
- 2枚とも黒である選び方：$_3\text{C}_2 = 3$ 通り
これらは互いに排反であるから、2枚とも同じ色となる選び方は：
$$6 + 3 + 3 = 12 \text{ 通り}$$
よって、$\mathbf{PQ = 12}$ である。

10枚から2枚を選ぶすべての組合せは：
$$_{10}\text{C}_2 = \frac{10 \times 9}{2} = 45 \text{ 通り}$$
したがって、2枚の色が異なるような選び方は余事象より：
$$45 - 12 = 33 \text{ 通り}$$
よって、$\mathbf{RS = 33}$ である。

**(3) 取り出した2枚が同じ色である確率**
同様に確からしい全事象は $_{10}\text{C}_2 = 45$ 通りであり、2枚が同じ色である事象は 12 通りであるから：
$$P = \frac{12}{45} = \frac{4}{15}$$
よって、$\text{T} = 4, \text{UV} = 15$ より $\mathbf{TUV = 415}$ である。

**(4) 1枚目が白か赤、かつ2枚目が赤か黒である確率**
1枚目に取り出す事象によって排反に場合分けする：
- **場合 1：1枚目が「白」のとき**
  1枚目に白を取り出す確率は $\frac{4}{10}$。
  白が1枚減り、残りは白3枚、赤3枚、黒3枚の計9枚となる。
  この中から2枚目に赤または黒（計6枚）を取り出す確率は $\frac{6}{9}$。
  $$P_1 = \frac{4}{10} \times \frac{6}{9} = \frac{24}{90}$$
- **場合 2：1枚目が「赤」のとき**
  1枚目に赤を取り出す確率は $\frac{3}{10}$。
  赤が1枚減り、残りは白4枚、赤2枚、黒3枚の計9枚となる。
  この中から2枚目に赤または黒（計 $2 + 3 = 5$ 枚）を取り出す確率は $\frac{5}{9}$。
  $$P_2 = \frac{3}{10} \times \frac{5}{9} = \frac{15}{90}$$
これら2つの場合は排反であるから、求める確率は：
$$P = P_1 + P_2 = \frac{24 + 15}{90} = \frac{39}{90} = \frac{13}{30}$$
よって、$\text{WX} = 13, \text{YZ} = 30$ より $\mathbf{WXYZ = 1330}$ である。

**【考査考点】**
場合の数（順列・組合せ）、余事象の考え方、非復元抽出における確率の乗法定理と排反事象の加法定理。

---

## 大問II 問1：平面ベクトルと重心・共線条件・内積計算
- **問題番号**：`math-q-II_1`
- **公式正解**：`{'ABC': '214', 'DE': '32', 'FG': '56', 'HI': '16', 'JKL': '396'}`
- **重要論点**：
  - 交点 D の位置ベクトルの導出と共線条件（係数の和が 1）の利用
  - 三角形の重心 G の位置ベクトルの線形表現
  - 内積の定義とベクトルの大きさの計算（余弦定理的展開）

**【題目大意】**
1辺 $OA$ を共有する $\triangle OAB$ と $\triangle OAC$ において、$\overrightarrow{OC} = x\overrightarrow{OA} + \frac{1}{2}\overrightarrow{OB}$ であり、$\triangle OAC$ の重心 $G$ が線分 $AB$ 上にあるとき、$x$ の値を求め、$\overrightarrow{OG}$ および $OG$ の長さを計算する。

**【公式正解】**
- $\text{ABC} = 214$ ($\overrightarrow{OD} = \frac{x}{2}\overrightarrow{OA} + \frac{1}{4}\overrightarrow{OB}$)
- $\text{DE} = 32$ ($x = \frac{3}{2}$)
- $\text{FG} = 56, \text{HI} = 16$ ($\overrightarrow{OG} = \frac{5}{6}\overrightarrow{OA} + \frac{1}{6}\overrightarrow{OB}$)
- $\text{JKL} = 396$ ($OG = \frac{\sqrt{39}}{6}$)

**【詳細推導・解答プロセス】**
**(1) 交点 $D$ の位置ベクトルと $x$ の決定**
線分 $OC$ と線分 $AB$ の交点を $D$ とする。
$D$ は直線 $OC$ 上にあるから、実数 $k$ を用いて $\overrightarrow{OD} = k\overrightarrow{OC}$ と表せる。
問題文の形式 $\overrightarrow{OD} = \frac{x}{\text{A}}\overrightarrow{OA} + \frac{\text{B}}{\text{C}}\overrightarrow{OB}$ に着目すると：
$\overrightarrow{OC} = x\overrightarrow{OA} + \frac{1}{2}\overrightarrow{OB}$ より、両辺に $k = \frac{1}{2}$ を掛けると：
$$\overrightarrow{OD} = \frac{x}{2}\overrightarrow{OA} + \frac{1}{4}\overrightarrow{OB}$$
よって、$\text{A} = 2, \text{B} = 1, \text{C} = 4$ より $\mathbf{ABC = 214}$ である。

点 $D$ は線分 $AB$ 上にあるから、$\overrightarrow{OA}$ と $\overrightarrow{OB}$ の係数の和は 1 である：
$$\frac{x}{2} + \frac{1}{4} = 1 \implies \frac{x}{2} = \frac{3}{4} \implies x = \frac{3}{2}$$
よって、$\text{D} = 3, \text{E} = 2$ より $\mathbf{DE = 32}$ である。

**(2) 重心 $G$ の位置ベクトルの表現**
$\triangle OAC$ の頂点は $O(0), A, C$ であるから、重心 $G$ の位置ベクトルは：
$$\overrightarrow{OG} = \frac{\overrightarrow{OO} + \overrightarrow{OA} + \overrightarrow{OC}}{3} = \frac{\overrightarrow{OA} + \left(x\overrightarrow{OA} + \frac{1}{2}\overrightarrow{OB}\right)}{3} = \frac{1 + x}{3}\overrightarrow{OA} + \frac{1}{6}\overrightarrow{OB}$$
$x = \frac{3}{2}$ を代入すると：
$$\frac{1 + \frac{3}{2}}{3} = \frac{\frac{5}{2}}{3} = \frac{5}{6}$$
したがって：
$$\overrightarrow{OG} = \frac{5}{6}\overrightarrow{OA} + \frac{1}{6}\overrightarrow{OB}$$
よって、$\text{FG} = 56, \text{HI} = 16$ である。
（なお、係数の和 $\frac{5}{6} + \frac{1}{6} = 1$ より、条件(ii)「$G$ が線分 $AB$ 上にある」ことと完全に整合している）

**(3) $OG$ の大きさの計算**
$OA = 1, OB = 2, \angle AOB = 60^\circ$ のとき：
$$\overrightarrow{OA} \cdot \overrightarrow{OB} = |\overrightarrow{OA}| |\overrightarrow{OB}| \cos 60^\circ = 1 \times 2 \times \frac{1}{2} = 1$$
$$|\overrightarrow{OG}|^2 = \left|\frac{5}{6}\overrightarrow{OA} + \frac{1}{6}\overrightarrow{OB}\right|^2 = \frac{1}{36}\left(25|\overrightarrow{OA}|^2 + 10\overrightarrow{OA} \cdot \overrightarrow{OB} + |\overrightarrow{OB}|^2\right)$$
$$= \frac{1}{36}\left(25 \times 1^2 + 10 \times 1 + 2^2\right) = \frac{25 + 10 + 4}{36} = \frac{39}{36}$$
したがって：
$$OG = \frac{\sqrt{39}}{6}$$
よって、$\text{J} = 3, \text{K} = 9, \text{L} = 6$ より $\mathbf{JKL = 396}$ である。

**【考査考点】**
平面ベクトルの線形独立性と一次結合、線分の交点ベクトルの導出、共線条件（係数の和が 1）、三角形の重心の公式、ベクトルの内積とノルムの計算。

---

## 大問II 問2：複素数平面上の三角形の面積と二等辺三角形の条件
- **問題番号**：`math-q-II_2`
- **公式正解**：`{'M': '2', 'N': '7', 'OP': '12', 'Q': '3', 'RS': '12', 'TU': '16'}`
- **重要論点**：
  - 絶対値 |z| = 2 を満たす複素数の極形式表現
  - 複素数平面上の原点を含む三角形の面積公式と最大値の決定
  - 二等辺三角形条件（OA = OB）の幾何的・代数的導出と偏角 arg の決定

**【題目大意】**
$|z| = 2$ を満たす複素数 $z$ について、$A(1 + z)$, $B(1 - \frac{1}{2}z)$ とおく。$z$ の極形式表示、$\triangle OAB$ の面積 $S$ の式および最大値、そして $\triangle OAB$ が $OA = OB$ の二等辺三角形となるときの辺長および各点の偏角を求める。

**【公式正解】**
- $\text{M} = 2$ ($z = 2(\cos\theta + i\sin\theta)$)
- $\text{N} = 7$ ($S = \frac{3}{2}|\sin\theta|$、選択肢 $\textcircled{7}$)
- $\text{OP} = 12$ (最大となるのは $\theta = \pm \frac{1}{2}\pi$)
- $\text{Q} = 3$ ($|1 + z| = |1 - \frac{1}{2}z| = \sqrt{3}$)
- $\text{RS} = 12$ ($\arg(1 + z) = \pm \frac{1}{2}\pi$)
- $\text{TU} = 16$ ($\arg(1 - \frac{1}{2}z) = \mp \frac{1}{6}\pi$)

**【詳細推導・解答プロセス】**
**(1) 極形式と $\triangle OAB$ の面積**
$|z| = 2$ より、$z$ は極形式で次のように表される：
$$z = 2(\cos\theta + i\sin\theta) \quad (-\pi \leq \theta < \pi)$$
よって、$\mathbf{M = 2}$ である。

各点の座標を $(x, y)$ で表すと：
- 点 $A$ は $1 + z = (1 + 2\cos\theta) + i(2\sin\theta)$ より：$A(1 + 2\cos\theta, 2\sin\theta)$
- 点 $B$ は $1 - \frac{1}{2}z = (1 - \cos\theta) - i(\sin\theta)$ より：$B(1 - \cos\theta, -\sin\theta)$
原点 $O$ と 2 点 $A(x_A, y_A), B(x_B, y_B)$ がつくる三角形の面積公式は：
$$S = \frac{1}{2} |x_A y_B - x_B y_A|$$
行列式（たすき掛け）を計算すると：
$$x_A y_B - x_B y_A = (1 + 2\cos\theta)(-\sin\theta) - (1 - \cos\theta)(2\sin\theta)$$
$$= -\sin\theta - 2\sin\theta\cos\theta - 2\sin\theta + 2\sin\theta\cos\theta = -3\sin\theta$$
したがって、面積は：
$$S = \frac{1}{2} |-3\sin\theta| = \frac{3}{2} |\sin\theta|$$
これは選択肢 $\textcircled{7}$ であるから、$\mathbf{N = 7}$ である。

$S$ が最大となるのは $|\sin\theta| = 1$、すなわち $\theta = \pm \frac{1}{2}\pi$ のときである。
よって、$\text{O} = 1, \text{P} = 2$ より $\mathbf{OP = 12}$ である。

**(2) 二等辺三角形 $OA = OB$ の条件と偏角**
$OA = OB \iff |1 + z|^2 = \left|1 - \frac{1}{2}z\right|^2$ である。
複素数の絶対値の 2 乗を計算する：
$$|1 + z|^2 = (1 + 2\cos\theta)^2 + (2\sin\theta)^2 = 1 + 4\cos\theta + 4\cos^2\theta + 4\sin^2\theta = 5 + 4\cos\theta$$
$$\left|1 - \frac{1}{2}z\right|^2 = (1 - \cos\theta)^2 + (-\sin\theta)^2 = 1 - 2\cos\theta + \cos^2\theta + \sin^2\theta = 2 - 2\cos\theta$$
両者が等しいので：
$$5 + 4\cos\theta = 2 - 2\cos\theta \implies 6\cos\theta = -3 \implies \cos\theta = -\frac{1}{2}$$
このとき：
$$|1 + z|^2 = 5 + 4\left(-\frac{1}{2}\right) = 5 - 2 = 3$$
したがって、$|1 + z| = \left|1 - \frac{1}{2}z\right| = \sqrt{3}$ である。
よって、$\mathbf{Q = 3}$ である。

次に偏角を求める。
$\cos\theta = -\frac{1}{2}$ より、$\sin\theta = \pm \frac{\sqrt{3}}{2}$ である。
- **$\sin\theta = \frac{\sqrt{3}}{2}$（$\theta = \frac{2\pi}{3}$）のとき**：
  $$1 + z = 1 + 2\left(-\frac{1}{2} + i\frac{\sqrt{3}}{2}\right) = 1 - 1 + i\sqrt{3} = i\sqrt{3}$$
  純虚数で虚部が正であるから：
  $$\arg(1 + z) = \frac{\pi}{2} = \frac{1}{2}\pi$$
  また：
  $$1 - \frac{1}{2}z = 1 - \left(-\frac{1}{2} + i\frac{\sqrt{3}}{2}\right) = \frac{3}{2} - i\frac{\sqrt{3}}{2} = \sqrt{3}\left(\frac{\sqrt{3}}{2} - \frac{1}{2}i\right)$$
  したがって：
  $$\arg\left(1 - \frac{1}{2}z\right) = -\frac{\pi}{6} = -\frac{1}{6}\pi$$
- **$\sin\theta = -\frac{\sqrt{3}}{2}$（$\theta = -\frac{2\pi}{3}$）のとき**：
  同様に対称性より：
  $$\arg(1 + z) = -\frac{\pi}{2} = -\frac{1}{2}\pi, \quad \arg\left(1 - \frac{1}{2}z\right) = \frac{\pi}{6} = \frac{1}{6}\pi$$
複号同順でまとめると：
$$\arg(1 + z) = \pm \frac{1}{2}\pi, \quad \arg\left(1 - \frac{1}{2}z\right) = \mp \frac{1}{6}\pi$$
よって、$\text{R} = 1, \text{S} = 2$ より $\mathbf{RS = 12}$、$\text{T} = 1, \text{U} = 6$ より $\mathbf{TU = 16}$ である。

**【考査考点】**
複素数の極形式、複素数平面上の座標変換と三角形の面積公式、複素数の絶対値の性質、二等辺三角形条件の解析、偏角 arg の決定。

---

## 大問III 問1：指数関数の導関数と最小値問題
- **問題番号**：`math-q-III_1`
- **公式正解**：`{'ABC': '235', 'DEFG': '3222'}`
- **重要論点**：
  - 指数関数の商の微分法および対数微分法の適用
  - 導関数の符号変化と極小値（最小値）の決定
  - 底の変換公式を用いた常用対数表現への書き換え

**【題目大意】**
関数 $y = \frac{2^{x^2}}{5^{3x}}$ ($x \geq 0$) について、導関数 $\frac{dy}{dx}$ を求め、$y$ が最小値をとるときの $x$ の値を常用対数を用いて表す。

**【公式正解】**
- $\text{ABC} = 235$ ($\frac{dy}{dx} = \frac{2^{x^2}}{5^{3x}} (2x\log_e 2 - 3\log_e 5)$)
- $\text{DEFG} = 3222$ ($x = \frac{3(1 - \log_{10} 2)}{2\log_{10} 2}$)

**【詳細推導・解答プロセス】**
**(1) 導関数の計算**
$y > 0$ であるから、両辺の自然対数をとる：
$$\log_e y = \log_e \left(\frac{2^{x^2}}{5^{3x}}\right) = \log_e (2^{x^2}) - \log_e (5^{3x}) = x^2 \log_e 2 - 3x \log_e 5$$
両辺を $x$ で微分すると：
$$\frac{1}{y} \frac{dy}{dx} = 2x \log_e 2 - 3 \log_e 5$$
両辺に $y = \frac{2^{x^2}}{5^{3x}}$ を掛けると：
$$\frac{dy}{dx} = \frac{2^{x^2}}{5^{3x}} \left(2x \log_e 2 - 3 \log_e 5\right)$$
したがって、$\text{A} = 2, \text{B} = 3, \text{C} = 5$ より $\mathbf{ABC = 235}$ である。

**(2) $y$ が最小になる $x$ の決定**
$\frac{2^{x^2}}{5^{3x}} > 0$ であるから、$\frac{dy}{dx} = 0$ となるのは：
$$2x \log_e 2 - 3 \log_e 5 = 0 \implies x = \frac{3 \log_e 5}{2 \log_e 2}$$
この前後で導関数の符号は負から正に変わるため、この $x$ において $y$ は最小となる。
ここで底の変換公式（底を 10 とする常用対数）を用いる：
$$\frac{\log_e 5}{\log_e 2} = \frac{\frac{\log_{10} 5}{\log_{10} e}}{\frac{\log_{10} 2}{\log_{10} e}} = \frac{\log_{10} 5}{\log_{10} 2}$$
さらに $\log_{10} 5 = \log_{10}\left(\frac{10}{2}\right) = \log_{10} 10 - \log_{10} 2 = 1 - \log_{10} 2$ であるから：
$$x = \frac{3(1 - \log_{10} 2)}{2 \log_{10} 2}$$
問題文の形式 $x = \frac{\text{D}(1 - \log_{10} \text{E})}{\text{F} \log_{10} \text{G}}$ と比較すると：
$\text{D} = 3, \text{E} = 2, \text{F} = 2, \text{G} = 2$
したがって、$\mathbf{DEFG = 3222}$ である。

**【考査考点】**
対数微分法、合成関数の微分、増減表に基づく最小値の判定、常用対数の底の変換公式、$\log_{10} 5 = 1 - \log_{10} 2$ の恒等変形。

---

## 大問III 問2：指数不等式の対数化と整数解の評価
- **問題番号**：`math-q-III_2`
- **公式正解**：`{'HIJKL': '22353', 'MNOP': '7892', 'Q': '9'}`
- **重要論点**：
  - 不等式 y > 1000 の常用対数による2次不等式への帰着
  - 近似値 log_{10} 2 = 0.3 を適用した2次方程式の解の公式の計算
  - 平方根の数値評価による不等式を満たす最小の正の整数の決定

**【題目大意】**
不等式 $\frac{2^{x^2}}{5^{3x}} > 1000$ を常用対数を用いて変形し、$\log_{10} 2 \approx 0.3$ を用いて不等式を解くことで、不等式を満たす最小の正の整数 $x$ を求める。

**【公式正解】**
- $\text{HIJKL} = 22353$ ($x^2 \log_{10} 2 - 3x \log_{10} 5 - 3 > 0$)
- $\text{MNOP} = 7892$ ($x > \frac{7 + \sqrt{89}}{2}$)
- $\text{Q} = 9$ (最小の正の整数 $x = 9$)

**【詳細推導・解答プロセス】**
**(1) 常用対数による不等式の変形**
不等式 $\frac{2^{x^2}}{5^{3x}} > 1000$ の両辺の常用対数をとると：
$$\log_{10}\left(\frac{2^{x^2}}{5^{3x}}\right) > \log_{10} 1000$$
左辺を展開し、右辺は $\log_{10} 10^3 = 3$ であるから：
$$x^2 \log_{10} 2 - 3x \log_{10} 5 > 3 \iff x^2 \log_{10} 2 - 3x \log_{10} 5 - 3 > 0$$
問題文の形式 $x^{\text{H}} \log_{10} \text{I} - \text{J} x \log_{10} \text{K} - \text{L} > 0$ と比較すると：
$\text{H} = 2, \text{I} = 2, \text{J} = 3, \text{K} = 5, \text{L} = 3$
したがって、$\mathbf{HIJKL = 22353}$ である。

**(2) 不等式の近似計算と解の導出**
$\log_{10} 2 = 0.3$ を用いると：
$$\log_{10} 5 = 1 - \log_{10} 2 = 1 - 0.3 = 0.7$$
これを不等式に代入する：
$$0.3 x^2 - 3(0.7)x - 3 > 0 \iff 0.3 x^2 - 2.1 x - 3 > 0$$
両辺を 10 倍して：
$$3x^2 - 21x - 30 > 0$$
両辺を 3 で割ると：
$$x^2 - 7x - 10 > 0$$
2次方程式 $x^2 - 7x - 10 = 0$ の解は：
$$x = \frac{7 \pm \sqrt{(-7)^2 - 4(1)(-10)}}{2} = \frac{7 \pm \sqrt{49 + 40}}{2} = \frac{7 \pm \sqrt{89}}{2}$$
$x \geq 0$ であるから、不等式の解は：
$$x > \frac{7 + \sqrt{89}}{2}$$
したがって、$\text{M} = 7, \text{N} = 8, \text{O} = 9, \text{P} = 2$ より $\mathbf{MNOP = 7892}$ である。

**(3) 最小の正の整数 $x$ の特定**
$\sqrt{89}$ の大きさを評価する：
$$9^2 = 81 < 89 < 100 = 10^2 \implies 9 < \sqrt{89} < 10$$
より精密には、$9.4^2 = 88.36 < 89 < 9.5^2 = 90.25$ より $\sqrt{89} \approx 9.43$ である。
したがって：
$$\frac{7 + \sqrt{89}}{2} \approx \frac{7 + 9.43}{2} = \frac{16.43}{2} = 8.215$$
$x > 8.215$ を満たす最小の正の整数は $x = 9$ である。
よって、$\mathbf{Q = 9}$ である。

**【考査考点】**
指数不等式の対数変換、常用対数の近似計算、2次不等式の解法と解の公式の活用、無理数の近似評価と整数解の同定。

---

## 大問IV 問1：三角関数の積の接線方程式と接点決定
- **問題番号**：`math-q-IV_1`
- **公式正解**：`{'A': '0', 'BC': '35', 'D': '6'}`
- **重要論点**：
  - 原点を通る接線が満たすべき条件式 f(t) = t f'(t) の立式
  - 積の微分法および合成関数の微分法による導関数の導出
  - 三角方程式の零点解析による接点の x 座標の決定

**【題目大意】**
区間 $0 \leq x \leq \pi$ で関数 $f(x) = x\sin^2 x$ を考える。原点を通る接線 $l$（ただし $x$ 軸ではない）と接点 $(t, f(t))$ について、成り立つ等式、導関数 $f'(t)$、および接点の $x$ 座標 $t$ を求める。

**【公式正解】**
- $\text{A} = 0$ ($f(t) = t f'(t)$、選択肢 $\textcircled{0}$)
- $\text{BC} = 35$ ($f'(t) = \sin^2 t + 2t\sin t\cos t$、B: 選択肢 $\textcircled{3}$、C: 選択肢 $\textcircled{5}$)
- $\text{D} = 6$ ($t = \frac{\pi}{2}$、選択肢 $\textcircled{6}$)

**【詳細推導・解答プロセス】**
**(1) 原点を通る接線が満たす等式**
曲線 $y = f(x)$ 上の点 $(t, f(t))$ における接線 $l$ の方程式は：
$$y - f(t) = f'(t)(x - t)$$
接線 $l$ が原点 $(0, 0)$ を通るので、代入すると：
$$0 - f(t) = f'(t)(0 - t) \iff -f(t) = -t f'(t) \iff f(t) = t f'(t)$$
これは選択肢 $\textcircled{0}$ であるから、$\mathbf{A = 0}$ である。

**(2) 導関数 $f'(t)$ の計算**
$f(x) = x \sin^2 x$ を積の微分法で微分する：
$$f'(x) = (x)' \sin^2 x + x (\sin^2 x)' = 1 \cdot \sin^2 x + x \cdot 2\sin x (\sin x)' = \sin^2 x + 2x \sin x \cos x$$
したがって：
$$f'(t) = \sin^2 t + 2t \sin t \cos t$$
問題文の形式 $f'(t) = \text{B} + 2t \text{C}$ と比較すると：
- $\text{B} = \sin^2 t$（選択肢 $\textcircled{3}$）
- $\text{C} = \sin t \cos t$（選択肢 $\textcircled{5}$）
よって、$\mathbf{BC = 35}$ である。

**(3) 接点の $x$ 座標 $t$ の決定**
$f(t) = t f'(t)$ に代入すると：
$$t \sin^2 t = t\left(\sin^2 t + 2t \sin t \cos t\right)$$
展開して整理すると：
$$t \sin^2 t = t \sin^2 t + 2t^2 \sin t \cos t \iff 2t^2 \sin t \cos t = 0$$
接線 $l$ は $x$ 軸ではないから $t \neq 0$ であり、$0 < t \leq \pi$ の範囲を考える。
もし $\sin t = 0$ ならば $t = \pi$ となり、このとき $f(\pi) = 0, f'(\pi) = 0$ より接線は $y = 0$（$x$ 軸）となって問題の条件に反する。
したがって、$\cos t = 0$ でなければならない。
区間 $0 < t < \pi$ において $\cos t = 0$ を解くと：
$$t = \frac{\pi}{2}$$
これは選択肢 $\textcircled{6}$ であるから、$\mathbf{D = 6}$ である。

**【考査考点】**
微分法による接線方程式の導出、原点通過条件の代数化、積の微分法・合成関数の微分法、三角関数の値の範囲と方程式の解法。

---

## 大問IV 問2：部分積分法と曲線および接線で囲まれる面積
- **問題番号**：`math-q-IV_2`
- **公式正解**：`{'EFG': '089', 'HIJKLM': '116214'}`
- **重要論点**：
  - 半角公式と部分積分法を用いた不定積分 \int x \sin^2 x dx の計算
  - 接線方程式 y = x の導出と関数の上下関係の評価
  - 定積分による囲まれた面積 S = \frac{1}{16}\pi^2 - \frac{1}{4} の完全導出

**【題目大意】**
関数 $f(x) = x\sin^2 x$ の不定積分を求め、曲線 $y = f(x)$ と接線 $l$ で囲まれる部分の面積 $S$ を計算する。

**【公式正解】**
- $\text{EFG} = 089$ (E: $\frac{1}{8}$[選択肢0], F: $\sin 2x$[選択肢8], G: $\cos 2x$[選択肢9])
- $\text{HIJKLM} = 116214$ ($S = \frac{1}{16}\pi^2 - \frac{1}{4}$)

**【詳細推導・解答プロセス】**
**(1) 不定積分の計算**
半角の公式 $\sin^2 x = \frac{1 - \cos 2x}{2}$ を用いて被積分関数を変形する：
$$\int f(x) \, dx = \int x \sin^2 x \, dx = \int x \left(\frac{1 - \cos 2x}{2}\right) dx = \frac{1}{2} \int x \, dx - \frac{1}{2} \int x \cos 2x \, dx$$
第1項は：
$$\frac{1}{2} \int x \, dx = \frac{1}{4} x^2$$
第2項に部分積分法を適用する：
$$\int x \cos 2x \, dx = x \left(\frac{\sin 2x}{2}\right) - \int 1 \cdot \left(\frac{\sin 2x}{2}\right) dx = \frac{1}{2} x \sin 2x - \frac{1}{2} \left(-\frac{\cos 2x}{2}\right) = \frac{1}{2} x \sin 2x + \frac{1}{4} \cos 2x$$
これらを合わせると：
$$\int f(x) \, dx = \frac{1}{4} x^2 - \frac{1}{2}\left(\frac{1}{2} x \sin 2x + \frac{1}{4} \cos 2x\right) + C = \frac{1}{4} x^2 - \frac{1}{4} x \sin 2x - \frac{1}{8} \cos 2x + C$$
全体を $\frac{1}{8}$ でくくり出すと：
$$\int f(x) \, dx = \frac{1}{8} \left(2x^2 - 2x \sin 2x - \cos 2x\right) + C$$
問題文の形式 $\text{E} (2x^2 - 2x \text{F} - \text{G}) + C$ と比較すると：
- $\text{E} = \frac{1}{8}$（選択肢 $\textcircled{0}$）
- $\text{F} = \sin 2x$（選択肢 $\textcircled{8}$）
- $\text{G} = \cos 2x$（選択肢 $\textcircled{9}$）
したがって、$\mathbf{EFG = 089}$ である。

**(2) 面積 $S$ の計算**
接点 $t = \frac{\pi}{2}$ において：
$$f\left(\frac{\pi}{2}\right) = \frac{\pi}{2} \sin^2\left(\frac{\pi}{2}\right) = \frac{\pi}{2} \times 1^2 = \frac{\pi}{2}$$
$$f'\left(\frac{\pi}{2}\right) = \sin^2\left(\frac{\pi}{2}\right) + 2\left(\frac{\pi}{2}\right) \sin\left(\frac{\pi}{2}\right) \cos\left(\frac{\pi}{2}\right) = 1 + \pi \times 1 \times 0 = 1$$
したがって、原点を通る接線 $l$ の方程式は $y = x$ である。
区間 $0 \leq x \leq \frac{\pi}{2}$ において、$0 \leq \sin^2 x \leq 1$ であるから：
$$f(x) = x \sin^2 x \leq x$$
すなわち、この区間で直線 $y = x$ は常に曲線 $y = f(x)$ の上側にある。
したがって、求める面積 $S$ は：
$$S = \int_0^{\pi/2} (x - f(x)) \, dx = \left[ \frac{1}{2} x^2 \right]_0^{\pi/2} - \int_0^{\pi/2} f(x) \, dx$$
まず直線の積分は：
$$\left[ \frac{1}{2} x^2 \right]_0^{\pi/2} = \frac{1}{2} \left(\frac{\pi}{2}\right)^2 = \frac{\pi^2}{8}$$
次に $f(x)$ の定積分を不定積分の結果を用いて計算する：
$$\int_0^{\pi/2} f(x) \, dx = \left[ \frac{1}{8} (2x^2 - 2x \sin 2x - \cos 2x) \right]_0^{\pi/2}$$
- $x = \frac{\pi}{2}$ のとき：
  $$2\left(\frac{\pi}{2}\right)^2 - 2\left(\frac{\pi}{2}\right) \sin\pi - \cos\pi = \frac{\pi^2}{2} - 0 - (-1) = \frac{\pi^2}{2} + 1$$
- $x = 0$ のとき：
  $$2(0)^2 - 2(0) \sin 0 - \cos 0 = -1$$
したがって：
$$\int_0^{\pi/2} f(x) \, dx = \frac{1}{8} \left[ \left(\frac{\pi^2}{2} + 1\right) - (-1) \right] = \frac{1}{8} \left(\frac{\pi^2}{2} + 2\right) = \frac{\pi^2}{16} + \frac{1}{4}$$
これより面積 $S$ は：
$$S = \frac{\pi^2}{8} - \left(\frac{\pi^2}{16} + \frac{1}{4}\right) = \frac{\pi^2}{16} - \frac{1}{4}$$
問題文の形式 $S = \frac{\text{H}}{\text{IJ}} \pi^{\text{K}} - \frac{\text{L}}{\text{M}}$ と比較すると：
$\text{H} = 1, \text{IJ} = 16, \text{K} = 2, \text{L} = 1, \text{M} = 4$
したがって、$\mathbf{HIJKLM = 116214}$ である。

**【考査考点】**
半角の公式と部分積分法、積の定積分の計算技法、曲線の上下関係に基づく面積の立式、三角関数の特殊角における値の正確な代入評価。

---
