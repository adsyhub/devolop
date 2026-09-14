# 2017-2 EJU 数学（コース2）詳細解答と徹底解説

**対象試験**：2017年度第2回（2017年11月実施）日本留学試験（EJU）数学コース2  
**大問構成**：大問I（問1, 問2）、大問II（問1, 問2）、大問III、大問IV（全8小問）  
**準拠公式正解**：JASSO 公式正解発表完全準拠

---

## 大問I 問1：2次関数の決定と最大値・最小値問題
- **問題番号**：`math-q-I_1`
- **公式正解**：`{'ABC': '181', 'DE': '-2', 'F': '4', 'G': '0', 'HI': '-1', 'JK': '-1', 'LM': '-3'}`
- **重要論点**：
  - 2次関数の平方完成と頂点座標・最小値のパラメータ表示
  - 不等式条件を満たすパラメータ a の変域の決定
  - 軸の位置に応じた最小値 m(a) の最大値・最小値の評価

**【題目大意】**
2次関数 $f(x) = 2x^2 + ax - 1$ が $f(-1) \geq -3$ かつ $f(2) \geq 3$（条件 $\textcircled{1}$）を満たすとき、$f(x)$ の最小値 $m$ について考える。

**【公式正解】**
- $\text{ABC} = 181$ ($m = -\frac{1}{8}a^2 - 1$)
- $\text{DE} = -2, \text{F} = 4$ ($-2 \leq a \leq 4$)
- $\text{G} = 0, \text{HI} = -1$ (軸 $x = 0$ のとき最大値 $-1$)
- $\text{JK} = -1, \text{LM} = -3$ (軸 $x = -1$ のとき最小値 $-3$)

**【詳細推導・解答プロセス】**
**(1) $f(x)$ の最小値 $m$ の導出**
$f(x)$ を平方完成する：
$$f(x) = 2\left(x^2 + \frac{a}{2}x\right) - 1 = 2\left(x + \frac{a}{4}\right)^2 - \frac{a^2}{8} - 1$$
下に凸の放物線であるから、頂点において最小値をとる。
$$m = -\frac{1}{8}a^2 - 1$$
よって、$\text{A} = 1, \text{B} = 8, \text{C} = 1$ より $\mathbf{ABC = 181}$ である。

**(2) 条件 $\textcircled{1}$ を満たす $a$ の範囲**
条件 $f(-1) \geq -3$ より：
$$f(-1) = 2(-1)^2 + a(-1) - 1 = 1 - a \geq -3 \implies a \leq 4$$
条件 $f(2) \geq 3$ より：
$$f(2) = 2(2)^2 + a(2) - 1 = 2a + 7 \geq 3 \implies 2a \geq -4 \implies a \geq -2$$
したがって、求める $a$ の値の範囲は：
$$-2 \leq a \leq 4$$
よって、$\text{DE} = -2, \text{F} = 4$ である。

**(3) $m$ の最大値と軸の位置**
$m(a) = -\frac{1}{8}a^2 - 1$ は $a = 0$ のとき最大値をとる。
このとき軸は $x = -\frac{a}{4} = 0$ であり、最大値は $m(0) = -1$ である。
よって、$\text{G} = 0, \text{HI} = -1$ である。

**(4) $m$ の最小値と軸の位置**
$-2 \leq a \leq 4$ において $a^2$ が最大となるのは $a = 4$（$a^2 = 16$）である。
$a = 4$ のとき軸は $x = -\frac{4}{4} = -1$ であり、最小値は $m(4) = -\frac{16}{8} - 1 = -3$ である。
よって、$\text{JK} = -1, \text{LM} = -3$ である。

---

## 大問I 問2：サイコロの出目による点の移動と推移行列・確率計算
- **問題番号**：`math-q-I_2`
- **公式正解**：`{'N': '9', 'OPQ': '754', 'RSTUV': '13108', 'WXYZ': '1336'}`
- **重要論点**：
  - 状態遷移規則に基づく各ステップの推移確率
  - 排反な遷移経路の列挙と加法定理
  - 4回以内の累積到達確率の計算

**【題目大意】**
三角形 ABC の頂点 A に置かれた球について、サイコロを投げて以下の規則で動かす：
- A にあるとき：目 1 が出れば B へ移動（確率 $\frac{1}{6}$）、その他は動かない（確率 $\frac{5}{6}$）。
- B にあるとき：目 4 以下が出れば C へ移動（確率 $\frac{4}{6} = \frac{2}{3}$）、その他は動かない（確率 $\frac{2}{6} = \frac{1}{3}$）。
- C に到達すれば試行終了。
4回以内に C に到達する確率を求める。

**【公式正解】**
- $\text{N} = 9$ (2回目に到達する確率 $\frac{1}{9}$)
- $\text{OPQ} = 754$ (3回目に到達する確率 $\frac{7}{54}$)
- $\text{RSTUV} = 13108$ (4回目に到達する確率 $\frac{13}{108}$)
- $\text{WXYZ} = 1336$ (4回以内に到達する合計確率 $\frac{13}{36}$)

**【詳細推導・解答プロセス】**
**(1) 2回目に C に到達する確率**
経路は $A \rightarrow B \rightarrow C$：
$$P(2) = \frac{1}{6} \times \frac{2}{3} = \frac{1}{9}$$
よって、$\mathbf{N = 9}$ である。

**(2) 3回目に C に到達する確率**
経路は $A \rightarrow A \rightarrow B \rightarrow C$ または $A \rightarrow B \rightarrow B \rightarrow C$：
$$P(3) = \frac{5}{6} \times \frac{1}{6} \times \frac{2}{3} + \frac{1}{6} \times \frac{1}{3} \times \frac{2}{3} = \frac{5}{54} + \frac{2}{54} = \frac{7}{54}$$
よって、$\mathbf{OPQ = 754}$ である。

**(3) 4回目に C に到達する確率**
経路は以下の3つの排反事象の和：
- $A \rightarrow A \rightarrow A \rightarrow B \rightarrow C$：$(\frac{5}{6})^2 \times \frac{1}{6} \times \frac{2}{3} = \frac{25}{324}$
- $A \rightarrow A \rightarrow B \rightarrow B \rightarrow C$：$\frac{5}{6} \times \frac{1}{6} \times \frac{1}{3} \times \frac{2}{3} = \frac{10}{324}$
- $A \rightarrow B \rightarrow B \rightarrow B \rightarrow C$：$\frac{1}{6} \times (\frac{1}{3})^2 \times \frac{2}{3} = \frac{4}{324}$
$$P(4) = \frac{25 + 10 + 4}{324} = \frac{39}{324} = \frac{13}{108}$$
よって、$\mathbf{RSTUV = 13108}$ である。

**(4) 4回以内の合計確率**
$$P(\leq 4) = \frac{1}{9} + \frac{7}{54} + \frac{13}{108} = \frac{12 + 14 + 13}{108} = \frac{39}{108} = \frac{13}{36}$$
よって、$\mathbf{WXYZ = 1336}$ である。

---

## 大問II 問1：非斉次隣接2項間漸化式と等比数列への帰着
- **問題番号**：`math-q-II_1`
- **公式正解**：`{'A': '3', 'B': '6', 'CD': '43', 'EF': '14', 'G': '5', 'H': '4', 'IJKL': '3541'}`
- **重要論点**：
  - 指数項を含む非斉次漸化式における適切な置換 bn = an / A^n の選択
  - 定数係数隣接2項間漸化式の特性方程式による等比数列型変形
  - 一般項 an の完全決定

**【題目大意】**
漸化式 $a_1 = 18, a_{n+1} - 12a_n + 3^{n+2} = 0$ ($n = 1, 2, \dots$) で定まる数列 $\{a_n\}$ について、$b_n = \frac{a_n}{A^n}$ と置くことで一般項 $a_n$ を求める。

**【公式正解】**
- $\text{A} = 3$ ($b_n = \frac{a_n}{3^n}$)
- $\text{B} = 6$ ($b_1 = 6$)
- $\text{CD} = 43$ ($b_{n+1} - 4b_n + 3 = 0$)
- $\text{EF} = 14$ ($b_{n+1} - 1 = 4(b_n - 1)$)
- $\text{G} = 5, \text{H} = 4$ ($c_n$ は初項 $5$、公比 $4$)
- $\text{IJKL} = 3541$ ($a_n = 3^n (5 \cdot 4^{n-1} + 1)$)

**【詳細推導・解答プロセス】**
漸化式は次のように書ける：
$$a_{n+1} = 12a_n - 3^{n+2} = 12a_n - 9 \cdot 3^n$$
両辺を $3^{n+1}$ で割る：
$$\frac{a_{n+1}}{3^{n+1}} = \frac{12}{3} \cdot \frac{a_n}{3^n} - \frac{9 \cdot 3^n}{3^{n+1}} = 4 \cdot \frac{a_n}{3^n} - 3$$
したがって、$b_n = \frac{a_n}{3^n}$ と置けばよいから、$\mathbf{A = 3}$ である。
初項は：
$$b_1 = \frac{a_1}{3^1} = \frac{18}{3} = 6$$
よって、$\mathbf{B = 6}$ である。
また、$\{b_n\}$ の漸化式は：
$$b_{n+1} - 4b_n + 3 = 0$$
よって、$\mathbf{CD = 43}$ である。

この漸化式を変形する：特性方程式 $x - 4x + 3 = 0 \implies x = 1$ より：
$$b_{n+1} - 1 = 4(b_n - 1)$$
よって、$\mathbf{EF = 14}$ である。

$c_n = b_n - 1$ とおくと、$\{c_n\}$ は公比 $4$ の等比数列であり、初項は：
$$c_1 = b_1 - 1 = 6 - 1 = 5$$
よって、初項 $\mathbf{G = 5}$、公比 $\mathbf{H = 4}$ である。

したがって：
$$c_n = 5 \cdot 4^{n-1} \implies b_n = 5 \cdot 4^{n-1} + 1$$
$a_n = 3^n b_n$ であるから：
$$a_n = 3^n \left(5 \cdot 4^{n-1} + 1\right)$$
形式 $a_n = \text{I}^n (\text{J} \cdot \text{K}^{n-1} + \text{L})$ と比較すると：
$$\text{I} = 3, \quad \text{J} = 5, \quad \text{K} = 4, \quad \text{L} = 1$$
よって、$\mathbf{IJKL = 3541}$ である。

---

## 大問II 問2：二等辺三角形の直線方程式と内接円半径・頂点座標の決定
- **問題番号**：`math-q-II_2`
- **公式正解**：`{'M': '5', 'NO': '33', 'PQ': '11', 'RSTU': '2411', 'VW': '14', 'XYZ': '203'}`
- **重要論点**：
  - 傾きと通過点による2等辺の直線方程式の導出（対称性による傾きの反転）
  - 点と直線の距離公式による内接円半径 r の定式化
  - 半径条件からパラメータ a の決定と頂点 A の座標算出

**【題目大意】**
$xy$ 平面上において、底辺 BC が $x$ 軸上にあり、$AB = AC$ である二等辺三角形 ABC を考える。辺 AB（直線 $\ell_1$）は点 $P(-1, 5)$ を通り傾き $a$、辺 AC（直線 $\ell_2$）は点 $Q(3, 3)$ を通る。
(1) $\ell_1, \ell_2$ の方程式を求める。
(2) 内接円の中心 $I$ の座標および半径 $r$ を $a$ で表す。
(3) $r = \frac{5}{2}$ のときの頂点 A の座標を求める。

**【公式正解】**
- $\text{M} = 5$ ($\\ell_1: y = ax + a + 5$)
- $\text{NO} = 33$ ($\\ell_2: y = -ax + 3a + 3$)
- $\text{PQ} = 11$ ($I\left(1 - \frac{1}{a}, r\right)$)
- $\text{RSTU} = 2411$ ($r = \frac{2a + 4}{1 + \sqrt{a^2 + 1}}$)
- $\text{VW} = 14, \text{XYZ} = 203$ ($A\left(\frac{1}{4}, \frac{20}{3}\right)$)

**【詳細推導・解答プロセス】**
**(1) 直線 $\ell_1, \ell_2$ の方程式**
$\ell_1$ は傾き $a$ で点 $P(-1, 5)$ を通るから：
$$y - 5 = a(x - (-1)) \implies y = ax + a + 5$$
よって、$\mathbf{M = 5}$ である。

二等辺三角形 $AB = AC$ の底辺が $x$ 軸上にあるため、対称軸は $x$ 軸に垂直な直線である。
したがって、直線 $\ell_2$ の傾きは $\ell_1$ の傾き $a$ の符号を反転させた $-a$ である。
$\ell_2$ は点 $Q(3, 3)$ を通るから：
$$y - 3 = -a(x - 3) \implies y = -ax + 3a + 3$$
よって、$\mathbf{NO = 33}$ である。

**(2) 内接円の中心 $I$ と半径 $r$**
頂点 A は $\ell_1$ と $\ell_2$ の交点である：
$$ax + a + 5 = -ax + 3a + 3 \implies 2ax = 2a - 2 \implies x_A = 1 - \frac{1}{a}$$
$$y_A = a\left(1 - \frac{1}{a}\right) + a + 5 = 2a + 4$$
二等辺三角形の対称軸は $x = 1 - \frac{1}{a}$ である。内接円の中心 $I$ もこの対称軸上にあり、底辺が $x$ 軸（$y = 0$）に接するため、中心の $y$ 座標は半径 $r$ に等しい：
$$I = \left(1 - \frac{1}{a}, r\right)$$
形式 $\left(P - \frac{Q}{a}, r\right)$ と比較して、$\mathbf{PQ = 11}$ である。

中心 $I$ から直線 $\ell_1: ax - y + a + 5 = 0$ までの距離は $r$ である：
$$\frac{|a(1 - 1/a) - r + a + 5|}{\sqrt{a^2 + (-1)^2}} = r$$
$$|a - 1 - r + a + 5| = |2a + 4 - r| = r\sqrt{a^2 + 1}$$
$I$ は三角形の内部にあり、$r < y_A = 2a + 4$ であるから、$2a + 4 - r > 0$。
$$2a + 4 - r = r\sqrt{a^2 + 1} \implies r\left(1 + \sqrt{a^2 + 1}\right) = 2a + 4$$
$$r = \frac{2a + 4}{1 + \sqrt{a^2 + 1}}$$
形式 $\frac{R a + S}{T + \sqrt{a^2 + U}}$ と比較すると：
$$\text{R} = 2, \quad \text{S} = 4, \quad \text{T} = 1, \quad \text{U} = 1$$
よって、$\mathbf{RSTU = 2411}$ である。

**(3) $r = \frac{5}{2}$ のときの頂点 A の座標**
$$\frac{2a + 4}{1 + \sqrt{a^2 + 1}} = \frac{5}{2} \implies 4a + 8 = 5 + 5\sqrt{a^2 + 1} \implies 4a + 3 = 5\sqrt{a^2 + 1}$$
両辺を2乗して整理する：
$$(4a + 3)^2 = 25(a^2 + 1) \implies 16a^2 + 24a + 9 = 25a^2 + 25$$
$$9a^2 - 24a + 16 = 0 \implies (3a - 4)^2 = 0 \implies a = \frac{4}{3}$$
頂点 A の座標は：
$$x_A = 1 - \frac{1}{4/3} = 1 - \frac{3}{4} = \frac{1}{4}$$
$$y_A = 2\left(\frac{4}{3}\right) + 4 = \frac{8}{3} + \frac{12}{3} = \frac{20}{3}$$
よって、$\mathbf{VW = 14}, \mathbf{XYZ = 203}$ である。

---

## 大問III 前半：対数不等式の同値変形と導関数の導出
- **問題番号**：`math-q-III_1`
- **公式正解**：`{'A': '3', 'B': '6', 'CD': '13'}`
- **重要論点**：
  - 対数の性質を用いた不等式の分離と同値変形
  - 商の微分法および合成関数の微分法による g'(x) の算出
  - 極値候補となる停留点（g'(x) = 0）の決定

**【題目大意】**
すべての正の実数 $x$ に対して、不等式 $\frac{\log 3x}{4x+1} \leq \log\left(\frac{2kx}{4x+1}\right)$ …… $\textcircled{1}$ が成り立つような正の実数 $k$ の範囲を求める。
(1) $\textcircled{1}$ を $\log k \geq g(x)$ の形に変形し、$g'(x)$ を計算する。

**【公式正解】**
- $\text{A} = 3$ (選択肢 $\textcircled{3}$：$g(x) = \frac{\log 3x}{4x+1} + \log(4x+1) - \log 2x$)
- $\text{B} = 6$ (選択肢 $\textcircled{6}$：$g'(x) = -\frac{4\log 3x}{(4x+1)^2}$)
- $\text{CD} = 13$ (停留点 $x = \frac{1}{3}$)

**【詳細推導・解答プロセス】**
対数の真数の商・積の法則を展開する：
$$\log\left(\frac{2kx}{4x+1}\right) = \log(2kx) - \log(4x+1) = \log k + \log 2x - \log(4x+1)$$
不等式 $\textcircled{1}$ に代入する：
$$\frac{\log 3x}{4x+1} \leq \log k + \log 2x - \log(4x+1)$$
$\log k$ について解くと：
$$\log k \geq \frac{\log 3x}{4x+1} + \log(4x+1) - \log 2x$$
これは選択肢 $\textcircled{3}$ に一致する。よって、$\mathbf{A = 3}$ である。

次に、$g(x) = \frac{\log 3x}{4x+1} + \log(4x+1) - \log 2x$ を $x$ で微分する：
1. 第1項の微分：
   $$\left(\frac{\log 3x}{4x+1}\right)' = \frac{\frac{1}{x}(4x+1) - (\log 3x)(4)}{(4x+1)^2} = \frac{4 + \frac{1}{x} - 4\log 3x}{(4x+1)^2}$$
2. 第2項・第3項の微分：
   $$(\log(4x+1) - \log 2x)' = \frac{4}{4x+1} - \frac{1}{x} = \frac{4x - (4x+1)}{x(4x+1)} = -\frac{1}{x(4x+1)}$$
通分してまとめる：
$$g'(x) = \frac{4 + \frac{1}{x} - 4\log 3x}{(4x+1)^2} - \frac{4x+1}{x(4x+1)^2} = \frac{4 + \frac{1}{x} - 4\log 3x - 4 - \frac{1}{x}}{(4x+1)^2} = -\frac{4\log 3x}{(4x+1)^2}$$
これは選択肢 $\textcircled{6}$ に一致する。よって、$\mathbf{B = 6}$ である。

$g'(x) = 0$ となる $x$ は：
$$\log 3x = 0 \implies 3x = 1 \implies x = \frac{1}{3}$$
よって、$\mathbf{CD = 13}$ である。

---

## 大問III 後半：関数の増減表と最大値に基づく成立条件
- **問題番号**：`math-q-III_2`
- **公式正解**：`{'EFG': '012', 'HI': '72'}`
- **重要論点**：
  - g'(x) の符号変化による増減表の作成
  - 区間における最大値の計算
  - 全正実数に対する不等式成立条件 k >= max(exp(g(x))) の導出

**【題目大意】**
$g(x)$ の増減を調べ、$x = \frac{1}{3}$ における極大値（最大値）を求めて、$k$ のとり得る値の範囲を決定する。

**【公式正解】**
- $\text{EFG} = 012$ ($0 < x < \frac{1}{3}$ で増加 $\textcircled{0}$、$\frac{1}{3} < x$ で減少 $\textcircled{1}$、$x = \frac{1}{3}$ で最大 $\textcircled{2}$)
- $\text{HI} = 72$ ($k \geq \frac{7}{2}$)

**【詳細推導・解答プロセス】**
$g'(x) = -\frac{4\log 3x}{(4x+1)^2}$ において、分母 $(4x+1)^2 > 0$ である。
- $0 < x < \frac{1}{3}$ のとき：$3x < 1$ より $\log 3x < 0$、したがって $g'(x) > 0$ となり、$g(x)$ は **増加**（$\textcircled{0}$）する（$\text{E} = 0$）。
- $\frac{1}{3} < x$ のとき：$3x > 1$ より $\log 3x > 0$、したがって $g'(x) < 0$ となり、$g(x)$ は **減少**（$\textcircled{1}$）する（$\text{F} = 1$）。
したがって、$g(x)$ は $x = \frac{1}{3}$ で **最大**（$\textcircled{2}$）となる（$\text{G} = 2$）。
よって、$\mathbf{EFG = 012}$ である。

$x = \frac{1}{3}$ における最大値を計算する：
$$\log\left(3 \cdot \frac{1}{3}\right) = \log 1 = 0$$
$$g\left(\frac{1}{3}\right) = 0 + \log\left(4 \cdot \frac{1}{3} + 1\right) - \log\left(2 \cdot \frac{1}{3}\right) = \log\left(\frac{7}{3}\right) - \log\left(\frac{2}{3}\right) = \log\left(\frac{7/3}{2/3}\right) = \log\left(\frac{7}{2}\right)$$
すべての正の実数 $x$ に対して $\log k \geq g(x)$ が成り立つための必要十分条件は：
$$\log k \geq \max_{x > 0} g(x) = \log\left(\frac{7}{2}\right)$$
底 $e > 1$ であるから：
$$k \geq \frac{7}{2}$$
よって、$\mathbf{HI = 72}$ である。

---

## 大問IV 前半：媒介変数表示と三角方程式による2曲線の交点決定
- **問題番号**：`math-q-IV_1`
- **公式正解**：`{'ABC': '212', 'DEF': '112', 'GHI': '512', 'JKL': '512', 'MNO': '112'}`
- **重要論点**：
  - 円の媒介変数表示 x = cos θ, y = sin θ の代入
  - 2倍角の公式 2 sin θ cos θ = sin 2θ による三角方程式の立式
  - 交点における偏角 θ および x 座標 p, q の決定

**【題目大意】**
第1象限の2曲線 $x^2 + y^2 = 1$ …… $\textcircled{1}$ と $4xy = 1$ …… $\textcircled{2}$ の交点 P, Q（$x$ 座標 $p < q$）を三角関数を用いて求める。

**【公式正解】**
- $\text{ABC} = 212$ ($\sin 2\theta = \frac{1}{2}$)
- $\text{DEF} = 112, \text{GHI} = 512$ ($\theta = \frac{1}{12}\pi, \frac{5}{12}\pi$)
- $\text{JKL} = 512$ ($p = \cos\frac{5}{12}\pi$)
- $\text{MNO} = 112$ ($q = \cos\frac{1}{12}\pi$)

**【詳細推導・解答プロセス】**
第1象限の単位円 $\textcircled{1}$ 上の点は $x = \cos\theta, y = \sin\theta$ ($0 < \theta < \frac{\pi}{2}$) と表せる。
これを $\textcircled{2}$ に代入する：
$$4xy = 4\cos\theta\sin\theta = 2(2\sin\theta\cos\theta) = 2\sin 2\theta = 1$$
したがって：
$$\sin 2\theta = \frac{1}{2}$$
形式 $\sin A\theta = \frac{B}{C}$ より、$\mathbf{ABC = 212}$ である。

$0 < \theta < \frac{\pi}{2}$ より $0 < 2\theta < \pi$ であるから：
$$2\theta = \frac{\pi}{6}, \quad \frac{5\pi}{6} \implies \theta = \frac{\pi}{12}, \quad \frac{5\pi}{12}$$
小さい順に答えるので：
$$\theta = \frac{1}{12}\pi, \quad \frac{5}{12}\pi$$
よって、$\mathbf{DEF = 112}, \mathbf{GHI = 512}$ である。

区間 $(0, \frac{\pi}{2})$ において $\cos\theta$ は単調減少関数である。
$p < q$ であるから、大きい偏角 $\theta = \frac{5}{12}\pi$ が小さい $x$ 座標 $p$ に対応し、小さい偏角 $\theta = \frac{1}{12}\pi$ が大きい $x$ 座標 $q$ に対応する：
$$p = \cos\frac{5}{12}\pi, \quad q = \cos\frac{1}{12}\pi$$
よって、$\mathbf{JKL = 512}, \mathbf{MNO = 112}$ である。

---

## 大問IV 後半：置換積分と対数関数による囲まれた図形の面積計算
- **問題番号**：`math-q-IV_2`
- **公式正解**：`{'PQ': '16', 'RS': '23', 'TU': '14'}`
- **重要論点**：
  - 定積分による囲まれた図形の面積 S の立式
  - 置換積分 x = cos θ による円弧下面積 I の算出
  - 反比例関数の対数積分 J の計算および有理化による簡約化

**【題目大意】**
2曲線の囲む面積 $S = \int_p^q \left(\sqrt{1 - x^2} - \frac{1}{4x}\right) dx = I - \frac{1}{4}J$ を計算する。

**【公式正解】**
- $\text{PQ} = 16$ ($I = \frac{1}{6}\pi$)
- $\text{RS} = 23$ ($J = \log(2 + \sqrt{3})$)
- $\text{TU} = 14$ ($S = \frac{1}{6}\pi - \frac{1}{4}\log(2 + \sqrt{3})$)

**【詳細推導・解答プロセス】**
**(1) 積分 $I = \int_p^q \sqrt{1 - x^2} dx$ の計算**
$x = \cos\theta$ と置換する。$dx = -\sin\theta d\theta$。
$x$ が $p = \cos\frac{5\pi}{12}$ から $q = \cos\frac{\pi}{12}$ まで変化するとき、$\theta$ は $\frac{5\pi}{12}$ から $\frac{\pi}{12}$ まで変化する。
$$I = \int_{5\pi/12}^{\pi/12} \sqrt{1 - \cos^2\theta} (-\sin\theta) d\theta = \int_{\pi/12}^{5\pi/12} \sin^2\theta d\theta$$
半角の公式 $\sin^2\theta = \frac{1 - \cos 2\theta}{2}$ を適用する：
$$I = \left[\frac{\theta}{2} - \frac{\sin 2\theta}{4}\right]_{\pi/12}^{5\pi/12} = \frac{1}{2}\left(\frac{5\pi}{12} - \frac{\pi}{12}\right) - \frac{1}{4}\left(\sin\frac{5\pi}{6} - \sin\frac{\pi}{6}\right)$$
$$\sin\frac{5\pi}{6} = \frac{1}{2}, \quad \sin\frac{\pi}{6} = \frac{1}{2} \implies \sin\frac{5\pi}{6} - \sin\frac{\pi}{6} = 0$$
したがって：
$$I = \frac{1}{2}\left(\frac{4\pi}{12}\right) = \frac{\pi}{6} = \frac{1}{6}\pi$$
よって、$\mathbf{PQ = 16}$ である。

**(2) 積分 $J = \int_p^q \frac{1}{x} dx$ の計算**
$$J = [\log x]_p^q = \log q - \log p = \log\left(\frac{q}{p}\right) = \log\left(\frac{\cos(\pi/12)}{\cos(5\pi/12)}\right)$$
加法定理より：
$$\cos\frac{\pi}{12} = \cos(45^\circ - 30^\circ) = \cos 45^\circ \cos 30^\circ + \sin 45^\circ \sin 30^\circ = \frac{\sqrt{6} + \sqrt{2}}{4}$$
$$\cos\frac{5\pi}{12} = \cos(45^\circ + 30^\circ) = \cos 45^\circ \cos 30^\circ - \sin 45^\circ \sin 30^\circ = \frac{\sqrt{6} - \sqrt{2}}{4}$$
比を計算し分母を有理化する：
$$\frac{q}{p} = \frac{\sqrt{6} + \sqrt{2}}{\sqrt{6} - \sqrt{2}} = \frac{(\sqrt{6} + \sqrt{2})^2}{6 - 2} = \frac{6 + 2\sqrt{12} + 2}{4} = \frac{8 + 4\sqrt{3}}{4} = 2 + \sqrt{3}$$
したがって：
$$J = \log(2 + \sqrt{3})$$
よって、$\mathbf{RS = 23}$ である。

**(3) 面積 $S$ の導出**
$$S = I - \frac{1}{4}J = \frac{1}{6}\pi - \frac{1}{4}\log(2 + \sqrt{3})$$
形式 $S = \frac{P}{Q}\pi - \frac{T}{U}\log(R + \sqrt{S})$ より、$\mathbf{TU = 14}$ である。

---
