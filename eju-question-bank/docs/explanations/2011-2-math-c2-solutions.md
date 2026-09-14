# 2011-2 EJU 数学 コース2 詳解

## 数学 コース2 第I問 [1]：3次式の展開公式と実数解の導出

**【題目大意】**
2つの実数 $a, b$ が $a^3 = \frac{1}{\sqrt{5} - 2}, \quad b^3 = 2 - \sqrt{5}$ を満たすとき，$a + b$ の値を求める。
$a + b = x$ とおき，$x^3$ を展開して $x$ が満たす3次方程式を導き，それを因数分解して $x = a + b$ を決定する。

**【公式正解】**
正解：
$\text{A} = 3$
$\text{BC} = -1$
$\text{DE} = 34$
$\text{F} = 1$
$\text{G} = 4$
$\text{HIJKL} = 12154$
$\text{M} = 1$

**【詳細推導・解答プロセス】**
1. **3次式の展開と基本対称式の計算**：
$x = a + b$ とおくと，3次式の和の立方展開公式より：
$$x^3 = (a + b)^3 = a^3 + 3a^2b + 3ab^2 + b^3 = a^3 + b^3 + 3ab(a + b)$$
したがって $\text{A} = 3$ である。

次に，$a^3$ の分母を有理化する：
$$a^3 = \frac{1}{\sqrt{5} - 2} = \frac{\sqrt{5} + 2}{(\sqrt{5} - 2)(\sqrt{5} + 2)} = \frac{\sqrt{5} + 2}{5 - 4} = \sqrt{5} + 2$$
与えられた $b^3 = 2 - \sqrt{5}$ と掛け合わせると：
$$a^3 b^3 = (ab)^3 = (\sqrt{5} + 2)(2 - \sqrt{5}) = 4 - 5 = -1$$
$ab$ は実数であるから：
$$ab = \sqrt[3]{-1} = -1$$
したがって $\text{BC} = -1$ である。

また，2数の立方和は：
$$a^3 + b^3 = (\sqrt{5} + 2) + (2 - \sqrt{5}) = 4$$

2. **$x$ の満たす3次方程式の立式**：
これらを $x^3 = a^3 + b^3 + 3ab \cdot x$ に代入すると：
$$x^3 = 4 + 3(-1)x = 4 - 3x$$
項を左辺に移項して整理すると：
$$x^3 + 3x - 4 = 0$$
これより $\text{D} = 3, \text{E} = 4$（$\text{DE} = 34$）である。

3. **因数分解と実数解の特定**：
$x = 1$ を代入すると $1^3 + 3(1) - 4 = 0$ となることから，$(x - 1)$ を因数にもつ。
$$x^3 + 3x - 4 = (x^3 - 1) + 3(x - 1) = (x - 1)(x^2 + x + 1) + 3(x - 1)$$
$$= (x - 1)(x^2 + x + 1 + 3) = (x - 1)(x^2 + x + 4)$$
したがって $\text{F} = 1, \text{G} = 4$ である。

ここで2次因数 $x^2 + x + 4$ を平方完成すると：
$$x^2 + x + 4 = \left(x + \frac{1}{2}\right)^2 - \frac{1}{4} + 4 = \left(x + \frac{1}{2}\right)^2 + \frac{15}{4}$$
実数 $x$ に対して $\left(x + \frac{1}{2}\right)^2 \geq 0$ であるため，$x^2 + x + 4 \geq \frac{15}{4} > 0$ である。
これより $\text{H} = 1, \text{I} = 2, \text{JK} = 15, \text{L} = 4$（$\text{HIJKL} = 12154$）である。

したがって，実数解は $x - 1 = 0$ のみであり：
$$x = a + b = 1$$
これより $\text{M} = 1$ である。

**【考査考点】**
分母の有理化，3次式の展開公式，対称式の基本変形，高次方程式の因数定理と平方完成による実数解の判別。

---

## 数学 コース2 第I問 [2]：放物線と直線の位置関係および差の最小値の最大化

**【題目大意】**
2つの関数 $y = x^2 + ax + a$ と $y = x + 1$ を考える。
(1) 2つの関数の共有点の個数と $a$ の条件を分類する。
(2) グラフがつねに上方にある条件のもとで，差の関数の最小値 $m$ を表し，$m$ の最大値とそのときの $a$ を求める。

**【公式正解】**
正解：
$\text{N} = 2$（選択肢 $\textcircled{2}$：$a < Q$ または $R < a$）
$\text{O} = 1$（選択肢 $\textcircled{1}$：$a = Q$ または $a = R$）
$\text{P} = 0$（選択肢 $\textcircled{0}$：$Q < a < R$）
$\text{QR} = 15$
$\text{STUV} = 1465$
$\text{W} = 3$
$\text{X} = 1$

**【詳細推導・解答プロセス】**
1. **(1) 共有点の個数の判定**：
2式の差をとって $y$ を消去する：
$$x^2 + ax + a = x + 1 \implies x^2 + (a - 1)x + (a - 1) = 0$$
この2次方程式の判別式を $D$ とすると：
$$D = (a - 1)^2 - 4 \cdot 1 \cdot (a - 1) = (a - 1)[(a - 1) - 4] = (a - 1)(a - 5)$$
$D = 0$ の解は $a = 1, 5$ であるから，$Q = 1, R = 5$（$\text{QR} = 15$）である。
- (i) 異なる2点で交わる $\iff D > 0 \iff a < 1$ または $5 < a$（選択肢 $\textcircled{2}$，$\text{N} = 2$）。
- (ii) 1点で接する $\iff D = 0 \iff a = 1$ または $a = 5$（選択肢 $\textcircled{1}$，$\text{O} = 1$）。
- (iii) 放物線がつねに直線上側にある $\iff D < 0 \iff 1 < a < 5$（選択肢 $\textcircled{0}$，$\text{P} = 0$）。

2. **(2) 差の関数の最小値 $m$**：
条件 P（$1 < a < 5$）において，$g(x) = x^2 + (a - 1)x + (a - 1)$ を平方完成する：
$$g(x) = \left(x + \frac{a - 1}{2}\right)^2 - \frac{(a - 1)^2}{4} + (a - 1)$$
$$= \left(x + \frac{a - 1}{2}\right)^2 - \frac{a^2 - 2a + 1 - 4a + 4}{4}$$
$$= \left(x + \frac{a - 1}{2}\right)^2 - \frac{a^2 - 6a + 5}{4}$$
下に凸の放物線であるため，最小値 $m$ は頂点でとり：
$$m = -\frac{1}{4}(a^2 - 6a + 5)$$
したがって $\text{S} = 1, \text{T} = 4, \text{U} = 6, \text{V} = 5$（$\text{STUV} = 1465$）である。

3. **$m$ の最大値とそのときの $a$**：
$m$ を $a$ の関数として平方完成する：
$$m = -\frac{1}{4}[(a - 3)^2 - 9 + 5] = -\frac{1}{4}(a - 3)^2 + 1$$
$1 < a < 5$ の範囲において，$a = 3$ は定義域に含まれており，$a = 3$ のとき最大値をとる：
$$m_{\text{max}} = 1 \quad (a = 3 \text{ のとき})$$
したがって $\text{W} = 3, \text{X} = 1$ である。

**【考査考点】**
放物線と直線の共有点判定（判別式の正負），2変数の最大・最小問題（2段階の平方完成）。

---

## 数学 コース2 第II問 (前半)：内分点ベクトルと線分ベクトルの成分表示

**【題目大意】**
座標平面上に4点 $A(1, 0), B(0, 1), C(3, 0), D(0, 2)$ をとり，線分 AB, CD 上にそれぞれ点 P, Q を $AP : PB = CQ : QD = k : 2$ となるようにとる。
$\overrightarrow{PQ} = (x, y)$ とおき，$x + 2y$ の値を求める。

**【公式正解】**
正解：
$\text{AB} = 22$
$\text{CD} = 22$
$\text{EF} = 24$
$\text{G} = 2$

**【詳細推導・解答プロセス】**
1. **位置ベクトル $\overrightarrow{OP}$ と $\overrightarrow{OQ}$ の立式**：
内分点の公式より，点 P は線分 AB を $k : 2$ に内分するため：
$$\overrightarrow{OP} = \frac{2\overrightarrow{OA} + k\overrightarrow{OB}}{k + 2}$$
したがって $\text{A} = 2, \text{B} = 2$（$\text{AB} = 22$）である。

同様に，点 Q は線分 CD を $k : 2$ に内分するため：
$$\overrightarrow{OQ} = \frac{2\overrightarrow{OC} + k\overrightarrow{OD}}{k + 2}$$
したがって $\text{C} = 2, \text{D} = 2$（$\text{CD} = 22$）である。

2. **成分の代入と $\overrightarrow{PQ}$ の算出**：
各点の座標を代入する：
$$\overrightarrow{OP} = \frac{2(1, 0) + k(0, 1)}{k + 2} = \left(\frac{2}{k + 2}, \frac{k}{k + 2}\right)$$
$$\overrightarrow{OQ} = \frac{2(3, 0) + k(0, 2)}{k + 2} = \left(\frac{6}{k + 2}, \frac{2k}{k + 2}\right)$$
ベクトル $\overrightarrow{PQ}$ は：
$$\overrightarrow{PQ} = \overrightarrow{OQ} - \overrightarrow{OP} = \left(\frac{6 - 2}{k + 2}, \frac{2k - k}{k + 2}\right) = \left(\frac{4}{k + 2}, \frac{k}{k + 2}\right) = \frac{1}{k + 2}(4, k)$$
問題文の形式 $(x, y) = \frac{1}{k + \text{E}}(\text{F}, k)$ と比較すると：
$$\text{E} = 2, \quad \text{F} = 4$$
これより $\text{EF} = 24$ である。

3. **$x + 2y$ の計算**：
$x = \frac{4}{k + 2}, y = \frac{k}{k + 2}$ であるから：
$$x + 2y = \frac{4}{k + 2} + 2 \cdot \frac{k}{k + 2} = \frac{4 + 2k}{k + 2} = \frac{2(k + 2)}{k + 2} = 2$$
したがって $\text{G} = 2$ である。

**【考査考点】**
平面ベクトルの内分公式，成分計算，線形従属関係（パラメータの消去）。

---

## 数学 コース2 第II問 (後半)：線分長の2乗の最小化とパラメータの決定

**【題目大意】**
前半の結果を用いて $PQ^2$ を $y$ の式で表し，線分 PQ の最小値とそのときの $y$ および $k$ の値を求める。

**【公式正解】**
正解：
$\text{HIJ} = 584$
$\text{KL} = 45$
$\text{MNO} = 255$
$\text{P} = 8$

**【詳細推導・解答プロセス】**
1. **$PQ^2$ を $y$ で表す**：
前半の結果より $x + 2y = 2$ であるから：
$$x = 2 - 2y$$
線分 PQ の長さの2乗は：
$$PQ^2 = x^2 + y^2 = (2 - 2y)^2 + y^2 = 4 - 8y + 4y^2 + y^2 = 5y^2 - 8y + 4$$
したがって $\text{H} = 5, \text{I} = 8, \text{J} = 4$（$\text{HIJ} = 584$）である。

2. **平方完成による最小値の導出**：
$$PQ^2 = 5\left(y^2 - \frac{8}{5}y\right) + 4 = 5\left(y - \frac{4}{5}\right)^2 - 5 \cdot \frac{16}{25} + 4 = 5\left(y - \frac{4}{5}\right)^2 - \frac{16}{5} + \frac{20}{5} = 5\left(y - \frac{4}{5}\right)^2 + \frac{4}{5}$$
したがって，$PQ^2$ は $y = \frac{4}{5}$ のとき最小値 $\frac{4}{5}$ をとる。
これより $\text{K} = 4, \text{L} = 5$（$\text{KL} = 45$）である。

3. **線分 PQ の最小値の算出**：
$$PQ = \sqrt{\frac{4}{5}} = \frac{2}{\sqrt{5}} = \frac{2\sqrt{5}}{5}$$
これより $\text{M} = 2, \text{N} = 5, \text{O} = 5$（$\text{MNO} = 255$）である。

4. **そのときの $k$ の値の決定**：
$y = \frac{k}{k + 2}$ であったから：
$$\frac{k}{k + 2} = \frac{4}{5} \implies 5k = 4(k + 2) = 4k + 8 \implies k = 8$$
これより $\text{P} = 8$ である。

**【考査考点】**
2次式の平方完成，分母の有理化，有理方程式によるパラメータの特定。

---

## 数学 コース2 第III問 (前半)：三角形に内接・外接する2円と三角関数の加法定理

**【題目大意】**
$AB = 9, BC = 12, \angle ABC = 90^\circ$ である三角形 ABC と，半径 $2r$ の円 $O_1$，半径 $r$ の円 $O_2$ がある。
円 $O_1$ と円 $O_2$ は互いに外接し，円 $O_1$ は辺 AB, AC と接し，円 $O_2$ は辺 CA, CB と接している。
(1) 接点を D, E とし，$\angle O_1AC = \alpha, \angle O_2CA = \beta$ とするとき，$\tan\alpha, AD, \tan\beta, CE, AC$ を求める。

**【公式正解】**
正解：
$\text{AB} = 43$
$\text{CD} = 12$
$\text{E} = 4$
$\text{FG} = 45$
$\text{HI} = 13$
$\text{J} = 3$
$\text{KL} = 15$

**【詳細推導・解答プロセス】**
1. **直角三角形 ABC の寸法**：
三平方の定理より：
$$AC = \sqrt{AB^2 + BC^2} = \sqrt{9^2 + 12^2} = \sqrt{81 + 144} = \sqrt{225} = 15$$
したがって $\text{KL} = 15$ である。

2. **$\tan\alpha$ および $AD$ の導出**：
円 $O_1$ は2辺 AB, AC に接するため，直線 $AO_1$ は $\angle A$ の二等分線である。
したがって $\angle A = 2\alpha$ である。
直角三角形 ABC より：
$$\tan 2\alpha = \tan A = \frac{BC}{AB} = \frac{12}{9} = \frac{4}{3}$$
これより $\text{A} = 4, \text{B} = 3$（$\text{AB} = 43$）である。

2倍角の公式 $\tan 2\alpha = \frac{2\tan\alpha}{1 - \tan^2\alpha} = \frac{4}{3}$ より：
$$6\tan\alpha = 4(1 - \tan^2\alpha) \implies 4\tan^2\alpha + 6\tan\alpha - 4 = 0 \implies 2\tan^2\alpha + 3\tan\alpha - 2 = 0$$
因数分解すると $(2\tan\alpha - 1)(\tan\alpha + 2) = 0$。
$\alpha$ は鋭角（$0 < \alpha < 45^\circ$）であるから $\tan\alpha > 0$ より：
$$\tan\alpha = \frac{1}{2}$$
これより $\text{C} = 1, \text{D} = 2$（$\text{CD} = 12$）である。

直角三角形 $AO_1D$ において，$O_1D = 2r$ であるから：
$$AD = \frac{O_1D}{\tan\alpha} = \frac{2r}{1/2} = 4r$$
したがって $\text{E} = 4$ である。

3. **$\tan\beta$ および $CE$ の導出**：
同様に，直線 $CO_2$ は $\angle C$ の二等分線であるから $\angle C = 2\beta$ である。
$\triangle ABC$ は直角三角形（$\angle B = 90^\circ$）であるから：
$$\angle A + \angle C = 90^\circ \implies 2\alpha + 2\beta = 90^\circ \implies \alpha + \beta = 45^\circ$$
したがって $\text{FG} = 45$ である。

加法定理より：
$$\tan\beta = \tan(45^\circ - \alpha) = \frac{\tan 45^\circ - \tan\alpha}{1 + \tan 45^\circ \tan\alpha} = \frac{1 - 1/2}{1 + 1 \cdot (1/2)} = \frac{1/2}{3/2} = \frac{1}{3}$$
したがって $\text{H} = 1, \text{I} = 3$（$\text{HI} = 13$）である。

直角三角形 $CO_2E$ において，$O_2E = r$ であるから：
$$CE = \frac{O_2E}{\tan\beta} = \frac{r}{1/3} = 3r$$
したがって $\text{J} = 3$ である。

**【考査考点】**
円の接線と角の二等分線の幾何学的性質，三角関数の2倍角公式，加法定理の適用。

---

## 数学 コース2 第III問 (後半)：外接する2円の中心間距離と半径 r の決定

**【題目大意】**
前半の結果をもとに，線分 DE の長さを求め，辺 AC の長さとの関係から半径 $r$ の値を決定する。

**【公式正解】**
正解：
$\text{MN} = 22$
$\text{OPQRS} = 15722$

**【詳細推導・解答プロセス】**
1. **線分 DE の長さの導出**：
2円 $O_1, O_2$ は互いに外接しているため，中心間距離は：
$$O_1O_2 = 2r + r = 3r$$
中心 $O_1$ から辺 AC（直線 DE）までの距離は $O_1D = 2r$ である。
中心 $O_2$ から辺 AC までの距離は $O_2E = r$ である。
$O_2$ から線分 $O_1D$ に垂線 $O_2H$ を下ろすと，$O_2HDE$ は長方形となり：
$$O_2H = DE, \quad O_1H = O_1D - HD = 2r - r = r$$
直角三角形 $O_1HO_2$ において三平方の定理を適用すると：
$$DE = O_2H = \sqrt{O_1O_2^2 - O_1H^2} = \sqrt{(3r)^2 - r^2} = \sqrt{9r^2 - r^2} = \sqrt{8r^2} = 2\sqrt{2}r$$
問題文の形式 $\text{M}\sqrt{\text{N}}r$ より，$\text{M} = 2, \text{N} = 2$（$\text{MN} = 22$）である。

2. **$r$ の値の決定**：
線分 AC は点 D, E によって $AD, DE, EC$ の3つの部分に分割されている：
$$AC = AD + DE + EC = 4r + 2\sqrt{2}r + 3r = (7 + 2\sqrt{2})r$$
前半より $AC = 15$ であるから：
$$(7 + 2\sqrt{2})r = 15$$
両辺を $7 + 2\sqrt{2}$ で割って有理化する：
$$r = \frac{15}{7 + 2\sqrt{2}} = \frac{15(7 - 2\sqrt{2})}{(7 + 2\sqrt{2})(7 - 2\sqrt{2})} = \frac{15(7 - 2\sqrt{2})}{49 - 8} = \frac{15(7 - 2\sqrt{2})}{41}$$
問題文の形式 $r = \frac{\text{OP}(\text{Q} - \text{R}\sqrt{\text{S}})}{41}$ と比較すると：
$$\text{OP} = 15, \quad \text{Q} = 7, \quad \text{R} = 2, \quad \text{S} = 2$$
これより $\text{OPQRS} = 15722$ である。

**【考査考点】**
外接する2円の中心間距離と共通接線間の距離，直角台形の幾何学的分解，根号を含む分数の有理化。

---

## 数学 コース2 第IV問 [1]：指数・三角関数の零点と微分による不定積分・定積分の計算

**【題目大意】**
$f(x) = 4\sqrt{3}e^{-x}\cos x + 6e^{-x}$ とする。
(1) $0 \le x < 2\pi$ において $f(x) = 0$ となる解 $a, b$（$a < b$）を求める。
(2) $\frac{d}{dx}(pe^{-x}\cos x + qe^{-x}\sin x) = e^{-x}\cos x$ を満たす定数 $p, q$ を求める。
(3) $e^{-a} = A, e^{-b} = B$ とおき，定積分 $\int_a^b f(x)dx$ を計算する。

**【公式正解】**
正解：
$\text{AB} = 56$
$\text{CD} = 76$
$\text{EFG} = -12$
$\text{HI} = 12$
$\text{JK} = 33$
$\text{LM} = 33$

**【詳細推導・解答プロセス】**
1. **(1) $f(x) = 0$ の解の算出**：
$$f(x) = 2e^{-x}(2\sqrt{3}\cos x + 3) = 0$$
$e^{-x} > 0$ であるから：
$$2\sqrt{3}\cos x + 3 = 0 \implies \cos x = -\frac{3}{2\sqrt{3}} = -\frac{\sqrt{3}}{2}$$
$0 \le x < 2\pi$ の範囲において：
$$x = \pi - \frac{\pi}{6} = \frac{5}{6}\pi, \quad x = \pi + \frac{\pi}{6} = \frac{7}{6}\pi$$
$a < b$ より：
$$a = \frac{5}{6}\pi, \quad b = \frac{7}{6}\pi$$
したがって $\text{AB} = 56, \text{CD} = 76$ である。

2. **(2) 微分による未定係数 $p, q$ の決定**：
積の微分公式を適用する：
$$\frac{d}{dx}\left(pe^{-x}\cos x + qe^{-x}\sin x\right) = p\left(-e^{-x}\cos x - e^{-x}\sin x\right) + q\left(-e^{-x}\sin x + e^{-x}\cos x\right)$$
$$= e^{-x}[(-p + q)\cos x + (-p - q)\sin x]$$
これが $e^{-x}\cos x$ に恒等的に一致するため：
$$\begin{cases} -p + q = 1 \\ -p - q = 0 \end{cases}$$
第2式より $q = -p$。第1式に代入すると $-2p = 1 \implies p = -\frac{1}{2}$，したがって $q = \frac{1}{2}$。
問題文の形式 $\frac{\text{EF}}{\text{G}}, \frac{\text{H}}{\text{I}}$ より：
$$p = \frac{-1}{2} \implies \text{EFG} = -12, \quad q = \frac{1}{2} \implies \text{HI} = 12$$
である。

3. **(3) 定積分 $\int_a^b f(x)dx$ の計算**：
(2) の結果より：
$$\int e^{-x}\cos x dx = -\frac{1}{2}e^{-x}\cos x + \frac{1}{2}e^{-x}\sin x + C$$
また，$\int 6e^{-x}dx = -6e^{-x} + C$ である。
したがって：
$$F(x) = \int f(x)dx = 4\sqrt{3}\left(-\frac{1}{2}e^{-x}\cos x + \frac{1}{2}e^{-x}\sin x\right) - 6e^{-x}$$
$$= e^{-x}(-2\sqrt{3}\cos x + 2\sqrt{3}\sin x - 6)$$

端点での値を計算する：
- $x = a = \frac{5}{6}\pi$ のとき，$\cos a = -\frac{\sqrt{3}}{2}, \sin a = \frac{1}{2}$ であるから：
  $$-2\sqrt{3}\left(-\frac{\sqrt{3}}{2}\right) + 2\sqrt{3}\left(\frac{1}{2}\right) - 6 = 3 + \sqrt{3} - 6 = \sqrt{3} - 3 = -(3 - \sqrt{3})$$
  $$F(a) = -(3 - \sqrt{3})e^{-a}$$

- $x = b = \frac{7}{6}\pi$ のとき，$\cos b = -\frac{\sqrt{3}}{2}, \sin b = -\frac{1}{2}$ であるから：
  $$-2\sqrt{3}\left(-\frac{\sqrt{3}}{2}\right) + 2\sqrt{3}\left(-\frac{1}{2}\right) - 6 = 3 - \sqrt{3} - 6 = -3 - \sqrt{3} = -(3 + \sqrt{3})$$
  $$F(b) = -(3 + \sqrt{3})e^{-b}$$

したがって：
$$\int_a^b f(x)dx = F(b) - F(a) = -(3 + \sqrt{3})e^{-b} - [-(3 - \sqrt{3})e^{-a}] = (3 - \sqrt{3})e^{-a} - (3 + \sqrt{3})e^{-b}$$
$e^{-a} = A, e^{-b} = B$ とおくと：
$$(3 - \sqrt{3})A - (3 + \sqrt{3})B$$
問題文の形式 $(J - \sqrt{K})A - (L + \sqrt{M})B$ より：
$$\text{J} = 3, \text{K} = 3, \text{L} = 3, \text{M} = 3$$
これより $\text{JK} = 33, \text{LM} = 33$ である。

**【考査考点】**
三角方程式の解法，指数関数と三角関数の積の不定積分（未定係数法），微分積分学の基本定理による定積分の評価。

---

## 数学 コース2 第IV問 [2]：無理関数の置換積分と無限遠における増大度の極限

**【題目大意】**
定積分 $S = \int_0^a x\sqrt{\frac{1}{3}x + 2} dx$ を考える。
(1) $t = \sqrt{\frac{1}{3}x + 2}$ とおいて不定積分を計算する。
(2) 定積分 $S$ を求め，$\lim_{a \to \infty} \frac{S}{a^{5/2}}$ の極限値を求める。

**【公式正解】**
正解：
$\text{NOPQR} = 18422$
$\text{S} = 1$（選択肢 $\textcircled{1}$：$\frac{6}{5}t^3(3t^2 - 10)$）
$\text{T} = 8$（選択肢 $\textcircled{8}$）
$\text{UV} = 52$
$\text{WXYZ} = 2315$

**【詳細推導・解答プロセス】**
1. **(1) 置換積分の実行**：
$t = \sqrt{\frac{1}{3}x + 2}$ とおく。
両辺を2乗すると：
$$t^2 = \frac{1}{3}x + 2 \implies \frac{1}{3}x = t^2 - 2 \implies x = 3(t^2 - 2) = 3t^2 - 6$$
両辺を $t$ で微分すると：
$$dx = 6t dt$$
被積分関数に代入すると：
$$\int x\sqrt{\frac{1}{3}x + 2} dx = \int (3t^2 - 6) \cdot t \cdot (6t dt) = 18\int (t^2 - 2)t^2 dt = 18\int (t^4 - 2t^2) dt$$
問題文の形式 $\text{NO}\int(t^{\text{P}} - \text{Q}t^{\text{R}})dt$ と比較すると：
$$\text{NO} = 18, \quad \text{P} = 4, \quad \text{Q} = 2, \quad \text{R} = 2$$
これより $\text{NOPQR} = 18422$ である。

2. **多項式積分の実行**：
$$18\int (t^4 - 2t^2) dt = 18\left(\frac{t^5}{5} - \frac{2t^3}{3}\right) = \frac{18}{5}t^5 - 12t^3 = \frac{6}{5}t^3(3t^2 - 10)$$
したがって，不定積分は：
$$\frac{6}{5}t^3(3t^2 - 10) + C$$
これは選択肢 $\textcircled{1}$ に合致するため，$\text{S} = 1$ である。

3. **(2) 定積分の立式**：
積分区間の対応を調べる：
- $x = 0$ のとき：$t = \sqrt{2}$
- $x = a$ のとき：$t = \sqrt{\frac{1}{3}a + 2}$
下端 $t = \sqrt{2}$ における値：
$$\frac{6}{5}(\sqrt{2})^3(3 \cdot 2 - 10) = \frac{6}{5}(2\sqrt{2})(-4) = -\frac{48\sqrt{2}}{5}$$
したがって，定積分 $S$ は選択肢 $\textcircled{8}$ の式で表される：
$$S = \textcircled{8} \implies \text{T} = 8$$

4. **無限大における極限値の算出**：
$a \to \infty$ において，$t = \sqrt{\frac{a}{3} + 2} \approx \sqrt{\frac{a}{3}} = \frac{a^{1/2}}{\sqrt{3}}$ である。
最高次の項は：
$$S \approx \frac{18}{5}t^5 = \frac{18}{5}\left(\frac{a}{3}\right)^{5/2} = \frac{18}{5} \cdot \frac{a^{5/2}}{9\sqrt{3}} = \frac{2}{5\sqrt{3}} a^{5/2} = \frac{2\sqrt{3}}{15} a^{5/2}$$
分母の形式は $a^{\text{U}/\text{V}} = a^{5/2}$ であるから，$\text{UV} = 52$ である。
極限値は：
$$\lim_{a \to \infty} \frac{S}{a^{5/2}} = \frac{2\sqrt{3}}{15}$$
問題文の形式 $\frac{\text{W}\sqrt{\text{X}}}{\text{YZ}}$ より：
$$\text{W} = 2, \quad \text{X} = 3, \quad \text{YZ} = 15$$
これより $\text{WXYZ} = 2315$ である。

**【考査考点】**
無理関数の置換積分法，共通因数のくくり出しによる因数分解，関数の漸近挙動と無限大における増大度の極限評価。

---

