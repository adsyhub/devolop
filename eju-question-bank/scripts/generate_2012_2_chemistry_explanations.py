#!/usr/bin/env python3
"""Generate comprehensive pedagogical explanations for 2012-2 EJU Chemistry (20 questions)."""

import json
from pathlib import Path

chemistry_questions = [
    {
        "q_num": 1,
        "localKey": "chem-q-01",
        "answer_ref": "CHEMISTRY:1",
        "answer": 4,
        "title": "化学 問1：同位体・イオンの構成粒子数（陽子・中性子・電子）の比較",
        "points": [
            "質量数 $A$ と原子番号 $Z$（陽子数）の関係 $A = Z + N$（$N$：中性子数）の理解",
            "同位体における中性子数の計算（$^{2}\\text{H}$：$2 - 1 = 1$，$^{4}\\text{He}$：$4 - 2 = 2$）",
            "閉殻電子配置（$\\text{Ca}^{2+}, \\text{F}^-$，$\\text{He}, \\text{Li}^+$）における最外殻・総電子数の同定"
        ],
        "solution": (
            "**【題目大意】**\n"
            "原子やイオンにおける陽子数，中性子数，最外殻電子数，総電子数に関する2つの数の比較において，互いに値が異なる組み合わせを一つ選ぶ。\n\n"
            "**【公式正解】**\n"
            "正解：$\\textcircled{4}$ （$^{2}\\text{H}$ の中性子数と $^{4}\\text{He}$ の中性子数）\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "各選択肢の構成粒子数を精査する：\n"
            "- $\\textcircled{1}$：$^{12}\\text{C}$ の陽子数と中性子数\n"
            "  炭素の原子番号は $6$ であるため，陽子数は $6$。中性子数は $12 - 6 = 6$ であり，互いに等しい（$6 = 6$）。\n"
            "- $\\textcircled{2}$：$^{12}\\text{C}$ の陽子数と $^{13}\\text{C}$ の陽子数\n"
            "  同位体であるため原子番号（陽子数）はともに $6$ で等しい（$6 = 6$）。\n"
            "- $\\textcircled{3}$：$\\text{Ca}^{2+}$ の最外殻電子数と $\\text{F}^-$ の最外殻電子数\n"
            "  カルシウム（原子番号 20，電子配置：K2 L8 M8 N2）が2価の陽イオンとなると $\\text{Ca}^{2+}$ はアルゴン $\\text{Ar}$ と同一配置（最外殻 M殻に8個）となる。\n"
            "  フッ素（原子番号 9，電子配置：K2 L7）が1価の陰イオンとなると $\\text{F}^-$ はネオン $\\text{Ne}$ と同一配置（最外殻 L殻に8個）となる。\n"
            "  最外殻電子数はともに $8$ で等しい（$8 = 8$）。\n"
            "- $\\textcircled{4}$：$^{2}\\text{H}$ の中性子数と $^{4}\\text{He}$ の中性子数\n"
            "  重水素 $^{2}\\text{H}$（原子番号 1，質量数 2）の中性子数は $2 - 1 = 1$ 個である。\n"
            "  ヘリウム $^{4}\\text{He}$（原子番号 2，質量数 4）の中性子数は $4 - 2 = 2$ 個である。\n"
            "  中性子数は $1$ と $2$ で互いに異なる。\n"
            "- $\\textcircled{5}$：$\\text{He}$ の電子の総数と $\\text{Li}^+$ の電子の総数\n"
            "  ヘリウム原子（原子番号 2）の電子総数は $2$。\n"
            "  リチウムイオン $\\text{Li}^+$（原子番号 3，1電子放出）の電子総数は $3 - 1 = 2$ であり，互いに等しい（$2 = 2$）。\n\n"
            "したがって，互いに異なる組み合わせは $\\textcircled{4}$ である。\n\n"
            "**【考査考点】**\n"
            "原子の構造，同位体，イオン化に伴う電子配置，質量数と中性子数の関係。"
        )
    },
    {
        "q_num": 2,
        "localKey": "chem-q-02",
        "answer_ref": "CHEMISTRY:2",
        "answer": 3,
        "title": "化学 問2：元素の周期表における分類と領域配置の判定",
        "points": [
            "典型元素（1, 2族および12〜18族）と遷移元素（3〜11族）の区分",
            "スズ（Sn：第5周期14族）が典型元素であることの理解",
            "鉄（Fe：遷移元素）とスズ（Sn：典型元素）の周期表上の位置の相違判定"
        ],
        "solution": (
            "**【題目大意】**\n"
            "元素の周期表をアルカリ金属，アルカリ土類金属，遷移元素，典型元素，ハロゲンなどの領域 (a)～(h) に区分した図に基づき，記述として誤っているものを一つ選ぶ。\n\n"
            "**【公式正解】**\n"
            "正解：$\\textcircled{3}$ （Fe、Snは両方とも(d)の領域にある）\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "周期表の各領域と元素の分類を検討する：\n"
            "- 領域 (d) は3族から11族を中心とする「遷移元素」の領域である。\n"
            "- 鉄 $\\text{Fe}$（原子番号 26，第4周期8族）は遷移元素であり，領域 (d) に属する。\n"
            "- スズ $\\text{Sn}$（原子番号 50，第5周期14族，炭素同族元素）は「典型元素（金属）」であり，周期表右側の典型元素領域（pブロック）に位置する。\n"
            "- したがって，スズ $\\text{Sn}$ は領域 (d) には属さず，記述 $\\textcircled{3}$ は誤りである。\n\n"
            "他の選択肢の妥当性：\n"
            "- $\\textcircled{1}$：領域 (b) は1族元素（水素を除くアルカリ金属）であり正しい。\n"
            "- $\\textcircled{2}$：$\\text{Ca}$（第4周期2族），$\\text{Mg}$（第3周期2族）はともに2族アルカリ土類金属領域 (c) に属し正しい。\n"
            "- $\\textcircled{4}$：領域 (e) は典型金属元素であり正しい。\n"
            "- $\\textcircled{5}$：(f), (g) は16族，17族の非金属元素領域であり正しい。\n"
            "- $\\textcircled{6}$：領域 (g) は17族ハロゲン元素であり正しい。\n\n"
            "したがって，正しくない記述は $\\textcircled{3}$ である。\n\n"
            "**【考査考点】**\n"
            "元素の周期表，典型元素と遷移元素の境界，族と周期による元素の分類。"
        )
    },
    {
        "q_num": 3,
        "localKey": "chem-q-03",
        "answer_ref": "CHEMISTRY:3",
        "answer": 3,
        "title": "化学 問3：水分子（H₂O）の構造・電子対・極性・水素結合",
        "points": [
            "水分子の価電子配置（共有電子対2組・非共有電子対2組）の把握",
            "非共有電子対の反発による折れ線形構造（結合角約 $104.5^\\circ$）と直線形の誤り判定",
            "電気陰性度の差による永久双極子モーメント（極性分子）と分子間水素結合の形成"
        ],
        "solution": (
            "**【題目大意】**\n"
            "水分子 $\\text{H}_2\\text{O}$ に関する記述のうち，正しくないものを一つ選ぶ。\n\n"
            "**【公式正解】**\n"
            "正解：$\\textcircled{3}$ （分子構造は直線形である）\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "水分子の化学的構造と性質を各項目ごとに評価する：\n"
            "- $\\textcircled{1}$：水分子の中心原子である酸素原子は，2つの水素原子とそれぞれ単結合（共有結合）を形成している。共有電子対が2組あるため，共有結合に関わる電子の総数は $2 \\times 2 = 4$ 個である（正しい）。\n"
            "- $\\textcircled{2}$：酸素原子の価電子は6個であり，そのうち2個が共有結合に用いられ，残り4個は2組の非共有電子対（孤立電子対）として存在する（正しい）。\n"
            "- $\\textcircled{3}$：水分子の電子対配置は四面体型（$\\text{sp}^3$ 混成軌道）を基本とし，非共有電子対が2組存在するため，原子の配列（分子構造）は「折れ線形（bent shape）」（結合角は約 $104.5^\\circ$）となる。「直線形」とする記述は明白な誤りである。\n"
            "- $\\textcircled{4}$：O-H 結合の極性（酸素の大きな電気陰性度）と折れ線形構造により，電荷の偏りが打ち消されず，分子全体として大きな双極子モーメントをもつ極性分子である（正しい）。\n"
            "- $\\textcircled{5}$：O原子上の非共有電子対および水素原子は，電気陰性度の大きい原子（F, O, N）と水素結合を形成できるため，フッ化水素 $\\text{HF}$ やメタノール $\\text{CH}_3\\text{OH}$ と水素結合をつくる（正しい）。\n\n"
            "したがって，誤っている記述は $\\textcircled{3}$ である。\n\n"
            "**【考査考点】**\n"
            "分子の幾何構造，VSEPR理論，極性と結合の電子配置，水素結合の成立条件。"
        )
    },
    {
        "q_num": 4,
        "localKey": "chem-q-04",
        "answer_ref": "CHEMISTRY:4",
        "answer": 6,
        "title": "化学 問4：アンモニア水溶液のモル濃度の計算",
        "points": [
            "アンモニアのモル質量 $M(\\text{NH}_3) = 14.0 + 3 \\times 1.0 = 17.0\\text{ g/mol}$ の算出",
            "溶解したアンモニアの物質量 $n = \\frac{3.4\\text{ g}}{17.0\\text{ g/mol}} = 0.20\\text{ mol}$ の計算",
            "モル濃度 $C = \\frac{n}{V} = \\frac{0.20\\text{ mol}}{0.025\\text{ L}} = 8.0\\text{ mol/L}$ の導出"
        ],
        "solution": (
            "**【題目大意】**\n"
            "水に $3.4\\text{ g}$ のアンモニア $\\text{NH}_3$ を溶かして $25\\text{ mL}$ の水溶液を調製した。\n"
            "この水溶液のモル濃度 $[\\text{mol/L}]$ として最も適当な値を求める。\n\n"
            "**【公式正解】**\n"
            "正解：$\\textcircled{6}$ （$8.0\\text{ mol/L}$）\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "1. **アンモニアの物質量 $n$ の算出**：\n"
            "与えられた原子量 $\\text{H} = 1.0$，$\\text{N} = 14$ より，アンモニア $\\text{NH}_3$ の分子量は：\n"
            "$$M = 14.0 + 1.0 \\times 3 = 17.0\\text{ g/mol}$$\n"
            "溶解させたアンモニアの質量は $3.4\\text{ g}$ であるから，その物質量は：\n"
            "$$n = \\frac{3.4\\text{ g}}{17.0\\text{ g/mol}} = 0.20\\text{ mol}$$\n\n"
            "2. **溶液の体積 $V$ の単位換算**：\n"
            "溶液の体積は $25\\text{ mL}$ であるから，リットル（$\\text{L}$）に換算すると：\n"
            "$$V = \\frac{25}{1000}\\text{ L} = 0.025\\text{ L}$$\n\n"
            "3. **モル濃度 $C$ の算出**：\n"
            "$$C = \\frac{n}{V} = \\frac{0.20\\text{ mol}}{0.025\\text{ L}} = \\frac{0.20}{\\frac{1}{40}} = 0.20 \\times 40 = 8.0\\text{ mol/L}$$\n\n"
            "したがって，選択肢 $\\textcircled{6}$ が正解である。\n\n"
            "**【考査考点】**\n"
            "分子量の計算，物質量（モル）の定義，溶液のモル濃度の基本計算。"
        )
    },
    {
        "q_num": 5,
        "localKey": "chem-q-05",
        "answer_ref": "CHEMISTRY:5",
        "answer": 5,
        "title": "化学 問5：共有結合の多重度と二重結合をもつ分子の同定",
        "points": [
            "各分子のルイス構造式と結合次数の分析",
            "エチレン（$\\text{H}_2\\text{C}=\\text{CH}_2$）および二酸化炭素（$\\text{O}=\\text{C}=\\text{O}$）における二重結合の存在確認",
            "アセチレン（三重結合），窒素（三重結合），塩化水素・塩素・アンモニア（単結合）の分別"
        ],
        "solution": (
            "**【題目大意】**\n"
            "与えられた分子 (a)～(g) のうち，分子内に「二重結合」をもつものの組み合わせとして正しいものを選ぶ。\n"
            "(a) アセチレン $\\text{C}_2\\text{H}_2$　(b) アンモニア $\\text{NH}_3$　(c) エチレン $\\text{C}_2\\text{H}_4$\n"
            "(d) 塩化水素 $\\text{HCl}$　(e) 塩素 $\\text{Cl}_2$　(f) 窒素 $\\text{N}_2$　(g) 二酸化炭素 $\\text{CO}_2$\n\n"
            "**【公式正解】**\n"
            "正解：$\\textcircled{5}$ （c, g）\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "各分子の構造式と結合様式を精査する：\n"
            "- (a) アセチレン $\\text{C}_2\\text{H}_2$：$\\text{H}-\\text{C}\\equiv\\text{C}-\\text{H}$（炭素間は「三重結合」）\n"
            "- (b) アンモニア $\\text{NH}_3$：3本の $\\text{N}-\\text{H}$「単結合」\n"
            "- (c) エチレン $\\text{C}_2\\text{H}_4$：$\\text{H}_2\\text{C}=\\text{CH}_2$（炭素間に「二重結合」を1つもつ）\n"
            "- (d) 塩化水素 $\\text{HCl}$：$\\text{H}-\\text{Cl}$「単結合」\n"
            "- (e) 塩素 $\\text{Cl}_2$：$\\text{Cl}-\\text{Cl}$「単結合」\n"
            "- (f) 窒素 $\\text{N}_2$：$\\text{N}\\equiv\\text{N}$（「三重結合」）\n"
            "- (g) 二酸化炭素 $\\text{CO}_2$：$\\text{O}=\\text{C}=\\text{O}$（炭素-酸素間に「二重結合」を2つもつ）\n\n"
            "二重結合をもつ分子は (c) エチレン と (g) 二酸化炭素 の2つである。\n"
            "したがって，組み合わせは c, g であり，選択肢 $\\textcircled{5}$ が正解である。\n\n"
            "**【考査考点】**\n"
            "ルイス構造式，単結合・二重結合・三重結合の結合様式，代表的無機・有機分子の電子配置。"
        )
    },
    {
        "q_num": 6,
        "localKey": "chem-q-06",
        "answer_ref": "CHEMISTRY:6",
        "answer": 2,
        "title": "化学 問6：理想気体のシャルルの法則と体積-セルシウス温度グラフ",
        "points": [
            "理想気体の状態方程式 $V = \\frac{nR}{P}(t + 273.15)$ の適用",
            "セルシウス温度軸における外挿点（絶対零度 $-273^\\circ\\text{C}$ で $V=0$）の一致",
            "一定圧力下での傾き $\\frac{nR}{P}$ の比較（$P_1 < P_2$ より $P_1$ の直線の傾きが大きい）"
        ],
        "solution": (
            "**【題目大意】**\n"
            "理想気体 $1\\text{ mol}$ を一定圧力 $P_1$ または $P_2\\,(P_1 < P_2)$ に保ちながら温度 $t\\,[^\\circ\\text{C}]$ を変化させたときの，体積 $V\\,[\\text{L}]$ と $t$ の関係を表すグラフを選ぶ。\n\n"
            "**【公式正解】**\n"
            "正解：$\\textcircled{2}$\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "1. **シャルルの法則と数式表現**：\n"
            "気体のモル数を $n = 1\\text{ mol}$，絶対温度を $T = t + 273.15\\,[\\text{K}]$ とする。\n"
            "理想気体の状態方程式 $P V = n R T$ より：\n"
            "$$V = \\left( \\frac{nR}{P} \\right) (t + 273.15)$$\n"
            "- $V$ と $t$ の関係は直線（一次関数）である。\n"
            "- $V = 0$ となるセルシウス温度は $t = -273.15^\\circ\\text{C}$（絶対零度）であり，圧力 $P$ の値によらずすべての直線は横軸上の点 $(-273^\\circ\\text{C}, 0)$ から放射状に伸びる。\n\n"
            "2. **直線の傾きの比較**：\n"
            "直線の傾きは $k = \\frac{nR}{P}$ である。\n"
            "問題条件より $P_1 < P_2$ であるから：\n"
            "$$\\frac{nR}{P_1} > \\frac{nR}{P_2}$$\n"
            "すなわち，同一温度 $t$ において，低圧 $P_1$ の気体の体積の方が高圧 $P_2$ の気体の体積よりも大きくなり，$P_1$ の直線の方が急な傾きをもつ。\n\n"
            "3. **グラフの照合**：\n"
            "横軸 $-273^\\circ\\text{C}$ を起点とし，傾きが $P_1 > P_2$ となっているグラフは $\\textcircled{2}$ である。\n\n"
            "したがって，選択肢 $\\textcircled{2}$ が正解である。\n\n"
            "**【考査考点】**\n"
            "シャルルの法則，絶対温度とセルシウス温度の変換，気体の状態方程式における圧力と体積の反比例関係。"
        )
    },
    {
        "q_num": 7,
        "localKey": "chem-q-07",
        "answer_ref": "CHEMISTRY:7",
        "answer": 5,
        "title": "化学 問7：ヘスの法則を用いたグルコースのエタノール発酵反応熱の計算",
        "points": [
            "与えられた3つの生成熱の熱化学方程式の整理",
            "反応熱の計算公式 $Q = \\sum (\\text{生成物の生成熱}) - \\sum (\\text{反応物の生成熱})$ の適用",
            "反応熱 $Q = 2(277) + 2(394) - 1273 = 69\\text{ kJ}$ の導出"
        ],
        "solution": (
            "**【題目大意】**\n"
            "$\\text{CO}_2$（気），$\\text{C}_2\\text{H}_5\\text{OH}$（液），$\\text{C}_6\\text{H}_{12}\\text{O}_6$（固）の生成熱はそれぞれ $394\\text{ kJ/mol}$，$277\\text{ kJ/mol}$，$1273\\text{ kJ/mol}$ である。\n"
            "グルコースからエタノールと二酸化炭素を生成する反応：\n"
            "$$\\text{C}_6\\text{H}_{12}\\text{O}_6\\text{（固）} = 2\\text{C}_2\\text{H}_5\\text{OH}\\text{（液）} + 2\\text{CO}_2\\text{（気）} + Q\\,\\text{kJ}$$\n"
            "における反応熱 $Q$ の値を求める。\n\n"
            "**【公式正解】**\n"
            "正解：$\\textcircled{5}$ （$69\\text{ kJ}$）\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "1. **生成熱に基づく反応熱の計算原理（ヘスの法則）**：\n"
            "化学反応における反応熱 $Q$ は，生成物の生成熱の総和から反応物の生成熱の総和を差し引くことで求まる：\n"
            "$$Q = \\sum (\\text{生成物の生成熱}) - \\sum (\\text{反応物の生成熱})$$\n\n"
            "2. **各物質の生成熱の代入**：\n"
            "- 生成物：\n"
            "  - エタノール $\\text{C}_2\\text{H}_5\\text{OH}$（液）：$2\\text{ mol} \\times 277\\text{ kJ/mol} = 554\\text{ kJ}$\n"
            "  - 二酸化炭素 $\\text{CO}_2$（気）：$2\\text{ mol} \\times 394\\text{ kJ/mol} = 788\\text{ kJ}$\n"
            "  - 生成熱の和 $= 554 + 788 = 1342\\text{ kJ}$\n"
            "- 反応物：\n"
            "  - グルコース $\\text{C}_6\\text{H}_{12}\\text{O}_6$（固）：$1\\text{ mol} \\times 1273\\text{ kJ/mol} = 1273\\text{ kJ}$\n\n"
            "3. **反応熱 $Q$ の算出**：\n"
            "$$Q = 1342 - 1273 = 69\\text{ kJ}$$\n\n"
            "したがって，選択肢 $\\textcircled{5}$ が正解である。\n\n"
            "**【考査考点】**\n"
            "ヘスの法則（総熱量保存則），生成熱の定義，熱化学方程式の加減法による反応熱の導出。"
        )
    },
    {
        "q_num": 8,
        "localKey": "chem-q-08",
        "answer_ref": "CHEMISTRY:8",
        "answer": 4,
        "title": "化学 問8：ルシャトリエの原理によるアンモニア電離平衡の移動とイオン濃度制御",
        "points": [
            "弱塩基の電離平衡 $\\text{NH}_3 + \\text{H}_2\\text{O} \\rightleftharpoons \\text{NH}_4^+ + \\text{OH}^-$ の確認",
            "水酸化物イオン濃度 $[\\text{OH}^-]$ の増加による平衡の左方移動（共通イオン効果）",
            "強塩基 $\\text{NaOH}$ の添加による $[\\text{NH}_4^+]$ の減少判定"
        ],
        "solution": (
            "**【題目大意】**\n"
            "アンモニア水溶液の電離平衡：\n"
            "$$\\text{NH}_3 + \\text{H}_2\\text{O} \\rightleftharpoons \\text{NH}_4^+ + \\text{OH}^-$$\n"
            "において，アンモニウムイオン $\\text{NH}_4^+$ の濃度を減らすために加えるべき最も適当な化合物を選択する。\n\n"
            "**【公式正解】**\n"
            "正解：$\\textcircled{4}$ （$\\text{NaOH}$）\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "1. **電離平衡とルシャトリエの原理**：\n"
            "アンモニウムイオン $\\text{NH}_4^+$ の濃度を減少させるには，電離平衡を「左向き（$\\leftarrow$）」に移動させる必要がある。\n"
            "ルシャトリエの原理によれば，生成物側にある水酸化物イオン $\\text{OH}^-$ の濃度を増加させれば，それを減少させる左向きに平衡が移動する。\n\n"
            "2. **各選択肢の添加効果**：\n"
            "- $\\textcircled{1}$ $\\text{C}_2\\text{H}_5\\text{OH}$（エタノール）：中性の非電解質であり，平衡移動に寄与しない。\n"
            "- $\\textcircled{2}$ $\\text{CH}_3\\text{COOH}$（酢酸）：酸であり $\\text{H}^+$ を供給して $\\text{OH}^-$ を中和消費するため，平衡は右向きに移動して $\\text{NH}_4^+$ 濃度は増加する。\n"
            "- $\\textcircled{3}$ $\\text{NaCl}$（塩化ナトリウム）：中性の強電解質であり，平衡を大きく移動させない。\n"
            "- $\\textcircled{4}$ $\\text{NaOH}$（水酸化ナトリウム）：強塩基であり，水中で完全に電離して多量の $\\text{OH}^-$ を生じる。共通イオン効果により平衡は強く左向きに移動し，$\\text{NH}_4^+$ の濃度は減少する。\n"
            "- $\\textcircled{5}$ $\\text{NH}_4\\text{Cl}$（塩化アンモニウム）：直接 $\\text{NH}_4^+$ を大量に加えるため，$\\text{NH}_4^+$ 濃度は著しく増加する。\n\n"
            "したがって，最も適当な物質は $\\text{NaOH}$ であり，選択肢 $\\textcircled{4}$ が正解である。\n\n"
            "**【考査考点】**\n"
            "ルシャトリエの原理，弱電解質の電離平衡，共通イオン効果による解離抑制。"
        )
    },
    {
        "q_num": 9,
        "localKey": "chem-q-09",
        "answer_ref": "CHEMISTRY:9",
        "answer": 3,
        "title": "化学 問9：強酸・強塩基の中和熱と限界反応物に基づく発熱量の計算",
        "points": [
            "強酸と強塩基の中和反応における本質 $\\text{H}^+ + \\text{OH}^- \\longrightarrow \\text{H}_2\\text{O} + 56\\text{ kJ}$ の把握",
            "実験1における中和反応量 $0.010\\text{ mol}$ と発熱量 $0.56\\text{ kJ}$ からの中和熱確認",
            "実験2における限界反応物（$\\text{H}^+ = 0.020\\text{ mol}$）の完全消費に伴う発熱量 $Q = 1.1\\text{ kJ}$ の導出"
        ],
        "solution": (
            "**【題目大意】**\n"
            "$0.40\\text{ mol/L}$ の塩酸 $50\\text{ mL}$ に $0.10\\text{ mol/L}$ の水酸化ナトリウム水溶液 $100\\text{ mL}$ を加えると $0.56\\text{ kJ}$ の熱が発生した。\n"
            "$0.40\\text{ mol/L}$ の塩酸 $50\\text{ mL}$ に $0.30\\text{ mol/L}$ の水酸化ナトリウム水溶液 $100\\text{ mL}$ を加えた場合に発生する熱量 $[\\text{kJ}]$ を求める。\n\n"
            "**【公式正解】**\n"
            "正解：$\\textcircled{3}$ （$1.1\\text{ kJ}$）\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "1. **1回目の混合実験の物質量解析**：\n"
            "- 塩酸中の $\\text{H}^+$ の物質量：\n"
            "  $$n(\\text{H}^+) = 0.40\\text{ mol/L} \\times \\frac{50}{1000}\\text{ L} = 0.020\\text{ mol}$$\n"
            "- 水酸化ナトリウム水溶液中の $\\text{OH}^-$ の物質量：\n"
            "  $$n(\\text{OH}^-) = 0.10\\text{ mol/L} \\times \\frac{100}{1000}\\text{ L} = 0.010\\text{ mol}$$\n"
            "- 反応式 $\\text{H}^+ + \\text{OH}^- \\longrightarrow \\text{H}_2\\text{O}$ より，$\\text{OH}^-$ が限界反応物となり，生成する水は $0.010\\text{ mol}$ である。\n"
            "- このとき発生した熱量が $0.56\\text{ kJ}$ であるから，強酸・強塩基の中和熱 $Q_{\\text{neut}}$ は：\n"
            "  $$Q_{\\text{neut}} = \\frac{0.56\\text{ kJ}}{0.010\\text{ mol}} = 56\\text{ kJ/mol}$$\n\n"
            "2. **2回目の混合実験の物質量解析**：\n"
            "- 塩酸中の $\\text{H}^+$ の物質量：\n"
            "  $$n(\\text{H}^+) = 0.40\\text{ mol/L} \\times \\frac{50}{1000}\\text{ L} = 0.020\\text{ mol}$$\n"
            "- 水酸化ナトリウム水溶液中の $\\text{OH}^-$ の物質量：\n"
            "  $$n(\\text{OH}^-) = 0.30\\text{ mol/L} \\times \\frac{100}{1000}\\text{ L} = 0.030\\text{ mol}$$\n"
            "- この場合，$\\text{H}^+$ の方が少ないため $\\text{H}^+$ が限界反応物となり，中和する量は $0.020\\text{ mol}$ である（$\\text{OH}^-$ は $0.010\\text{ mol}$ 過剰に残る）。\n\n"
            "3. **発生熱量の算出**：\n"
            "$$Q = 0.020\\text{ mol} \\times 56\\text{ kJ/mol} = 1.12\\text{ kJ} \\approx 1.1\\text{ kJ}$$\n\n"
            "したがって，選択肢 $\\textcircled{3}$ が正解である。\n\n"
            "**【考査考点】**\n"
            "中和熱の定義，化学量論比と限界反応物の判定，発熱量と物質量の比例関係。"
        )
    },
    {
        "q_num": 10,
        "localKey": "chem-q-10",
        "answer_ref": "CHEMISTRY:10",
        "answer": 3,
        "title": "化学 問10：鉛蓄電池の充電反応に伴う正極・負極の質量変化",
        "points": [
            "充電時（放電の逆反応）の正極・負極の半反応式の立式",
            "正極：$\\text{PbSO}_4\\,(303) \\to \\text{PbO}_2\\,(239)$ による質量減少",
            "負極：$\\text{PbSO}_4\\,(303) \\to \\text{Pb}\\,(207)$ による質量減少"
        ],
        "solution": (
            "**【題目大意】**\n"
            "鉛蓄電池を充電したとき，正極と負極の質量はそれぞれどのように変化するか，適当な組み合わせを選ぶ。\n\n"
            "**【公式正解】**\n"
            "正解：$\\textcircled{3}$ （正極：減る，負極：減る）\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "1. **鉛蓄電池の電極反応の整理**：\n"
            "鉛蓄電池の放電および充電の全反応式は以下の通りである：\n"
            "$$\\text{Pb} + \\text{PbO}_2 + 2\\text{H}_2\\text{SO}_4 \\underset{\\text{充電}}{\\overset{\\text{放電}}{\\rightleftharpoons}} 2\\text{PbSO}_4 + 2\\text{H}_2\\text{O}$$\n\n"
            "2. **充電時における各極の反応と質量変化**：\n"
            "- **正極（充電反応）**：\n"
            "  放電で生じた硫酸鉛 $\\text{PbSO}_4$ が酸化鉛(IV) $\\text{PbO}_2$ に戻る：\n"
            "  $$\\text{PbSO}_4 + 2\\text{H}_2\\text{O} \\longrightarrow \\text{PbO}_2 + \\text{SO}_4^{2-} + 4\\text{H}^+ + 2e^-$$\n"
            "  式量変化：$\\text{PbSO}_4\\,(303) \\longrightarrow \\text{PbO}_2\\,(239)$\n"
            "  電極に付着している固体の質量は $1\\text{ mol}$ あたり $303 - 239 = 64\\text{ g}$ 減少する（減る）。\n\n"
            "- **負極（充電反応）**：\n"
            "  放電で生じた硫酸鉛 $\\text{PbSO}_4$ が鉛 $\\text{Pb}$ に戻る：\n"
            "  $$\\text{PbSO}_4 + 2e^- \\longrightarrow \\text{Pb} + \\text{SO}_4^{2-}$$\n"
            "  式量変化：$\\text{PbSO}_4\\,(303) \\longrightarrow \\text{Pb}\\,(207)$\n"
            "  電極に付着している固体の質量は $1\\text{ mol}$ あたり $303 - 207 = 96\\text{ g}$ 減少する（減る）。\n\n"
            "3. **結論**：\n"
            "正極の質量は「減る」，負極の質量も「減る」。\n"
            "したがって，選択肢 $\\textcircled{3}$ が正解である。\n\n"
            "**【考査考点】**\n"
            "鉛蓄電池の電極反応式，充電と放電における可逆的物質移動，電極質量の増減計算。"
        )
    },
    {
        "q_num": 11,
        "localKey": "chem-q-11",
        "answer_ref": "CHEMISTRY:11",
        "answer": 5,
        "title": "化学 問11：金属の反応性と不動態形成（Feと濃硝酸）",
        "points": [
            "金属のイオン化傾向と酸化性酸（濃硝酸・熱濃硫酸・王水）に対する溶解性の整理",
            "鉄 $\\text{Fe}$，アルミニウム $\\text{Al}$，ニッケル $\\text{Ni}$ における不動態形成の理解",
            "鉄が濃硝酸に対して緻密な酸化皮膜を形成し不溶となる現象の同定"
        ],
        "solution": (
            "**【題目大意】**\n"
            "金属の化学的性質に関する記述のうち，最も適当なものを一つ選ぶ。\n\n"
            "**【公式正解】**\n"
            "正解：$\\textcircled{5}$ （鉄 Fe は，濃硝酸に溶けない）\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "各選択肢の金属の反応性を検討する：\n"
            "- $\\textcircled{1}$：銀 $\\text{Ag}$ は水素よりイオン化傾向が小さいが，強力な酸化作用をもつ濃硝酸には溶けて硝酸銀となり，一酸化窒素または二酸化窒素を発生する（誤り）。\n"
            "- $\\textcircled{2}$：アルミニウム $\\text{Al}$ は両性金属であり，強塩基である水酸化ナトリウム水溶液 $\\text{NaOH aq}$ にテトラヒドロキシドアルミン酸ナトリウム $[\\text{Na}[\\text{Al(OH)}_4]]$ を生じて水素を発生しながら溶ける（誤り）。\n"
            "- $\\textcircled{3}$：金 $\\text{Au}$ は極めてイオン化傾向が小さく，濃硫酸や濃硝酸などの単独の強酸には溶けない（王水にのみ溶ける）（誤り）。\n"
            "- $\\textcircled{4}$：銅 $\\text{Cu}$ は水素よりイオン化傾向が小さいため，非酸化性の酸である希塩酸 $\\text{dil. HCl}$ には溶けない（誤り）。\n"
            "- $\\textcircled{5}$：鉄 $\\text{Fe}$ は強酸化性の濃硝酸と接触すると，表面に極めて緻密な酸化皮膜（$\\text{Fe}_3\\text{O}_4$ など）を瞬時に形成して内部が保護される「不動態（passivity）」となるため，それ以上溶けない（正しい）。\n\n"
            "したがって，最も適当な記述は $\\textcircled{5}$ である。\n\n"
            "**【考査考点】**\n"
            "金属のイオン化傾向，酸化性酸と非酸化性酸の反応性の違い，両性金属の性質，不動態の概念。"
        )
    },
    {
        "q_num": 12,
        "localKey": "chem-q-12",
        "answer_ref": "CHEMISTRY:12",
        "answer": 2,
        "title": "化学 問12：無機陽イオン・陰イオンの系統分離と定性検出反応",
        "points": [
            "$\\text{Fe}^{3+}$ に水酸化ナトリウムを加えたときの水酸化鉄(III) $\\text{Fe(OH)}_3$ 赤褐色沈殿の生成",
            "過剰の $\\text{NaOH}$ を加えても再溶解しないことの看破（両性金属との対比）",
            "塩化銀白色沈殿，過マンガン酸脱色，ナトリウム炎色反応，硫酸バリウム沈殿の確認"
        ],
        "solution": (
            "**【題目大意】**\n"
            "水溶液中の各種イオンの検出操作と結果を示した表の中から，結果が正しくないものを一つ選ぶ。\n\n"
            "**【公式正解】**\n"
            "正解：$\\textcircled{2}$ （$\\text{Fe}^{3+}$ に $\\text{NaOH}$ を加えたときの沈殿溶解）\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "各イオンの検出反応と結果を検証する：\n"
            "- $\\textcircled{1}$：$\\text{Ag}^+$ に塩酸 $\\text{HCl aq}$ を加えると，水に難溶な塩化銀の白色沈殿が生じる：\n"
            "  $$\\text{Ag}^+ + \\text{Cl}^- \\longrightarrow \\text{AgCl} \\downarrow \\text{（白）}$$\n"
            "  （正しい）。\n"
            "- $\\textcircled{2}$：$\\text{Fe}^{3+}$ に水酸化ナトリウム水溶液を加えると，水酸化鉄(III)の赤褐色沈殿を生じる：\n"
            "  $$\\text{Fe}^{3+} + 3\\text{OH}^- \\longrightarrow \\text{Fe(OH)}_3 \\downarrow \\text{（赤褐色）}$$\n"
            "  過剰の $\\text{NaOH aq}$ に溶解するのは両性金属（$\\text{Al}, \\text{Zn}, \\text{Sn}, \\text{Pb}$）の水酸化物であり，鉄の水酸化物は錯イオンを作らず過剰の強塩基にも「溶解しない」。したがって「沈殿が溶解した」とする記述は誤りである。\n"
            "- $\\textcircled{3}$：$\\text{MnO}_4^-$（赤紫色）は硫酸酸性中でシュウ酸 $(\\text{COOH})_2$ によって還元され，ほぼ無色の $\\text{Mn}^{2+}$ になるため脱色する（正しい）。\n"
            "- $\\textcircled{4}$：$\\text{Na}^+$ の炎色反応は特徴的な強い「黄色」である（正しい）。\n"
            "- $\\textcircled{5}$：$\\text{SO}_4^{2-}$ に硝酸バリウム $\\text{Ba(NO}_3)_2$ を加えると，硫酸バリウムの白色沈殿を生じる：\n"
            "  $$\\text{Ba}^{2+} + \\text{SO}_4^{2-} \\longrightarrow \\text{BaSO}_4 \\downarrow \\text{（白）}$$\n"
            "  （正しい）。\n\n"
            "したがって，正しくない結果は $\\textcircled{2}$ である。\n\n"
            "**【考査考点】**\n"
            "無機イオンの定性分析，金属水酸化物の沈殿色，両性金属と遷移金属の錯形成能の違い，酸化還元滴定の終点指示。"
        )
    },
    {
        "q_num": 13,
        "localKey": "chem-q-13",
        "answer_ref": "CHEMISTRY:13",
        "answer": 1,
        "title": "化学 問13：無機化合物の沈殿・分解・気体発生反応と化学反応式",
        "points": [
            "硫酸銅(II)と水酸化ナトリウムの複分解による水酸化銅(II)沈殿反応の正確性確認",
            "炭酸水素ナトリウムの熱分解における炭酸ナトリウム生成（$2\\text{NaHCO}_3 \\to \\text{Na}_2\\text{CO}_3 + \\text{H}_2\\text{O} + \\text{CO}_2$）",
            "アンモニア発生反応における遊離反応機構（$\\text{NH}_4\\text{OH}$ ではなく $\\text{NH}_3 + \\text{H}_2\\text{O}$）"
        ],
        "solution": (
            "**【題目大意】**\n"
            "各操作で起こる化学反応を表す反応式として正しいものを一つ選ぶ。\n\n"
            "**【公式正解】**\n"
            "正解：$\\textcircled{1}$ （$\\text{CuSO}_4 + 2\\text{NaOH} \\longrightarrow \\text{Cu(OH)}_2 + \\text{Na}_2\\text{SO}_4$）\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "各反応式の正誤を検討する：\n"
            "- $\\textcircled{1}$：硫酸銅(II)水溶液に水酸化ナトリウム水溶液を加えると，青白色の水酸化銅(II)の沈殿が生じる：\n"
            "  $$\\text{CuSO}_4 + 2\\text{NaOH} \\longrightarrow \\text{Cu(OH)}_2 \\downarrow + \\text{Na}_2\\text{SO}_4$$\n"
            "  化学量論比，生成物ともに完全に正しい。\n"
            "- $\\textcircled{2}$：炭酸水素ナトリウムを加熱すると，炭酸ナトリウム，水，二酸化炭素に熱分解する：\n"
            "  $$2\\text{NaHCO}_3 \\longrightarrow \\text{Na}_2\\text{CO}_3 + \\text{H}_2\\text{O} + \\text{CO}_2$$\n"
            "  選択肢の式 $\\text{NaHCO}_3 \\to \\text{NaOH} + \\text{CO}_2$ は生成物が誤りである。\n"
            "- $\\textcircled{3}$：硝酸銀水溶液にアンモニア水を少量加えると酸化銀(I) $\\text{Ag}_2\\text{O}$ の褐色沈殿が生じるが，反応式表記において過剰添加時のアンモニア錯イオン形成や電離平衡の表記等で選択肢 $\\textcircled{1}$ が最も標準的かつ明瞭である。\n"
            "- $\\textcircled{4}$：塩化アンモニウムに水酸化カルシウムを加えて加熱するアンモニア発生反応は，弱塩基の遊離により気体のアンモニア $\\text{NH}_3$ が発生する：\n"
            "  $$2\\text{NH}_4\\text{Cl} + \\text{Ca(OH)}_2 \\longrightarrow \\text{CaCl}_2 + 2\\text{H}_2\\text{O} + 2\\text{NH}_3 \\uparrow$$\n"
            "  選択肢の式にある $2\\text{NH}_4\\text{OH}$ という化学種表記は誤りである。\n\n"
            "したがって，正しい反応式は $\\textcircled{1}$ である。\n\n"
            "**【考査考点】**\n"
            "沈殿生成反応，炭酸水素塩の熱分解反応，弱塩基の遊離反応とアンモニアの発生。"
        )
    },
    {
        "q_num": 14,
        "localKey": "chem-q-14",
        "answer_ref": "CHEMISTRY:14",
        "answer": 5,
        "title": "化学 問14：酸化数の変化による酸化還元反応の識別",
        "points": [
            "各反応における構成元素の酸化数の追跡",
            "硫化水素と二酸化硫黄の酸化還元反応（自己酸化還元・酸化還元共存）の特定",
            "$\\text{SO}_2$ の硫黄（$+4 \\to 0$：還元）と $\\text{H}_2\\text{S}$ の硫黄（$-2 \\to 0$：酸化）の同定"
        ],
        "solution": (
            "**【題目大意】**\n"
            "与えられた化学反応式 $\\textcircled{1}\\sim\\textcircled{5}$ のうち，酸化還元反応であるものを一つ選ぶ。\n\n"
            "**【公式正解】**\n"
            "正解：$\\textcircled{5}$ （$\\text{SO}_2 + 2\\text{H}_2\\text{S} \\longrightarrow 3\\text{S} + 2\\text{H}_2\\text{O}$）\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "各反応における元素の酸化数の変化を調査する：\n"
            "- $\\textcircled{1}$ $\\text{CaCO}_3 + 2\\text{HCl} \\longrightarrow \\text{CaCl}_2 + \\text{H}_2\\text{O} + \\text{CO}_2$：\n"
            "  弱酸の遊離反応である。$\\text{Ca}(+2), \\text{C}(+4), \\text{O}(-2), \\text{H}(+1), \\text{Cl}(-1)$ であり，酸化数の変化はない。\n"
            "- $\\textcircled{2}$ $\\text{FeCl}_3 + 3\\text{NaOH} \\longrightarrow \\text{Fe(OH)}_3 + 3\\text{NaCl}$：\n"
            "  沈殿生成（複分解）反応である。$\\text{Fe}(+3), \\text{Cl}(-1), \\text{Na}(+1), \\text{O}(-2), \\text{H}(+1)$ であり，酸化数の変化はない。\n"
            "- $\\textcircled{3}$ $\\text{Na}_2\\text{O} + \\text{H}_2\\text{O} \\longrightarrow 2\\text{NaOH}$：\n"
            "  塩基性酸化物と水の反応である。$\\text{Na}(+1), \\text{O}(-2), \\text{H}(+1)$ であり，酸化数の変化はない。\n"
            "- $\\textcircled{4}$ $2\\text{NH}_3 + \\text{H}_2\\text{SO}_4 \\longrightarrow (\\text{NH}_4)_2\\text{SO}_4$：\n"
            "  中和反応である。$\\text{N}(-3), \\text{H}(+1), \\text{S}(+6), \\text{O}(-2)$ であり，酸化数の変化はない。\n"
            "- $\\textcircled{5}$ $\\text{SO}_2 + 2\\text{H}_2\\text{S} \\longrightarrow 3\\text{S} + 2\\text{H}_2\\text{O}$：\n"
            "  - $\\text{SO}_2$ 中の $\\text{S}$ の酸化数は $+4$ であり，生成物の単体 $\\text{S}$（$0$）に減少している（還元）。\n"
            "  - $\\text{H}_2\\text{S}$ 中の $\\text{S}$ の酸化数は $-2$ であり，生成物の単体 $\\text{S}$（$0$）に増加している（酸化）。\n"
            "  電子の授受を伴う明瞭な酸化還元反応である。\n\n"
            "したがって，酸化還元反応は $\\textcircled{5}$ である。\n\n"
            "**【考査考点】**\n"
            "酸化数の決定規則，酸化還元反応と非酸化還元反応（中和，沈殿，弱酸・弱塩基遊離）の判別。"
        )
    },
    {
        "q_num": 15,
        "localKey": "chem-q-15",
        "answer_ref": "CHEMISTRY:15",
        "answer": 4,
        "title": "化学 問15：オストワルト法によるアンモニアからの硝酸合成の物質量計算",
        "points": [
            "全反応式 $\\text{NH}_3 + 2\\text{O}_2 \\longrightarrow \\text{HNO}_3 + \\text{H}_2\\text{O}$ の化学量論比（$1:1$）の把握",
            "アンモニア $17\\text{ kg}$ の物質量 $n = \\frac{17 \\times 10^3\\text{ g}}{17\\text{ g/mol}} = 1.0 \\times 10^3\\text{ mol}$ の計算",
            "生成する硝酸の質量 $m = 1.0 \\times 10^3\\text{ mol} \\times 63\\text{ g/mol} = 63\\text{ kg}$ の決定"
        ],
        "solution": (
            "**【題目大意】**\n"
            "アンモニアから硝酸を工業的に合成するオストワルト法の全反応式：\n"
            "$$\\text{NH}_3 + 2\\text{O}_2 \\longrightarrow \\text{HNO}_3 + \\text{H}_2\\text{O}$$\n"
            "において，$17\\text{ kg}$ のアンモニアから得られる硝酸の質量 $[\\text{kg}]$ を求める。\n\n"
            "**【公式正解】**\n"
            "正解：$\\textcircled{4}$ （$63\\text{ kg}$）\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "1. **各物質のモル質量の算出**：\n"
            "- アンモニア $\\text{NH}_3$：\n"
            "  $$M(\\text{NH}_3) = 14.0 + 1.0 \\times 3 = 17.0\\text{ g/mol}$$\n"
            "- 硝酸 $\\text{HNO}_3$：\n"
            "  $$M(\\text{HNO}_3) = 1.0 + 14.0 + 16.0 \\times 3 = 63.0\\text{ g/mol}$$\n\n"
            "2. **アンモニアの物質量**：\n"
            "$$n(\\text{NH}_3) = \\frac{17 \\times 10^3\\text{ g}}{17.0\\text{ g/mol}} = 1.0 \\times 10^3\\text{ mol}$$\n\n"
            "3. **生成する硝酸の質量の算出**：\n"
            "全反応式より，$\\text{NH}_3$ と $\\text{HNO}_3$ の係数比は $1 : 1$ である。\n"
            "したがって，理論上生成する $\\text{HNO}_3$ の物質量も $1.0 \\times 10^3\\text{ mol}$ である。\n"
            "得られる硝酸の質量は：\n"
            "$$m(\\text{HNO}_3) = 1.0 \\times 10^3\\text{ mol} \\times 63.0\\text{ g/mol} = 63 \\times 10^3\\text{ g} = 63\\text{ kg}$$\n\n"
            "したがって，選択肢 $\\textcircled{4}$ が正解である。\n\n"
            "**【考査考点】**\n"
            "オストワルト法の全反応式，化学量論計算，物質量と質量のキログラム換算。"
        )
    },
    {
        "q_num": 16,
        "localKey": "chem-q-16",
        "answer_ref": "CHEMISTRY:16",
        "answer": 1,
        "title": "化学 問16：有機化合物の組成式（実験式）の一致判定",
        "points": [
            "組成式（最も簡単な整数比で表した原子比）の定義の理解",
            "酢酸（$\\text{C}_2\\text{H}_4\\text{O}_2 \\implies \\text{CH}_2\\text{O}$）とホルムアルデヒド（$\\text{CH}_2\\text{O}$）の組成式一致の確認",
            "他の組の分子式・組成式の系統的比較"
        ],
        "solution": (
            "**【題目大意】**\n"
            "示された化合物の組み合わせのうち，2つの化合物の組成式（実験式）が互いに等しいものを選ぶ。\n\n"
            "**【公式正解】**\n"
            "正解：$\\textcircled{1}$ （酢酸 と ホルムアルデヒド）\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "各選択肢の分子式および組成式（原子比の最小整数比）を求める：\n"
            "- $\\textcircled{1}$：\n"
            "  - 酢酸 $\\text{CH}_3\\text{COOH}$：分子式は $\\text{C}_2\\text{H}_4\\text{O}_2$ であり，比率は $\\text{C} : \\text{H} : \\text{O} = 2 : 4 : 2 = 1 : 2 : 1$。組成式は $\\text{CH}_2\\text{O}$。\n"
            "  - ホルムアルデヒド $\\text{HCHO}$：分子式は $\\text{CH}_2\\text{O}$ であり，組成式も $\\text{CH}_2\\text{O}$。\n"
            "  両者の組成式は完全に同一である。\n"
            "- $\\textcircled{2}$：酢酸（$\\text{CH}_2\\text{O}$）と ギ酸 $\\text{HCOOH}$（分子式 $\\text{CH}_2\\text{O}_2$，組成式 $\\text{CH}_2\\text{O}_2$）$\implies$ 異なる。\n"
            "- $\\textcircled{3}$：アセトン $\\text{CH}_3\\text{COCH}_3$（$\\text{C}_3\\text{H}_6\\text{O}$）と 酢酸エチル $\\text{CH}_3\\text{COOC}_2\\text{H}_5$（$\\text{C}_4\\text{H}_8\\text{O}_2 \\implies \\text{C}_2\\text{H}_4\\text{O}$）$\implies$ 異なる。\n"
            "- $\\textcircled{4}$：アセチルサリチル酸 $\\text{C}_9\\text{H}_8\\text{O}_4$ と サリチル酸メチル $\\text{C}_8\\text{H}_8\\text{O}_3$ $\implies$ 異なる。\n"
            "- $\\textcircled{5}$：エチレングリコール $\\text{C}_2\\text{H}_6\\text{O}_2 \\implies \\text{CH}_3\\text{O}$ と グリセリン $\\text{C}_3\\text{H}_8\\text{O}_3$ $\implies$ 異なる。\n\n"
            "したがって，組成式が同じ組み合わせは $\\textcircled{1}$ である。\n\n"
            "**【考査考点】**\n"
            "分子式と組成式（実験式）の関係，カルボン酸・アルデヒドの元素構成比。"
        )
    },
    {
        "q_num": 17,
        "localKey": "chem-q-17",
        "answer_ref": "CHEMISTRY:17",
        "answer": 2,
        "title": "化学 問17：有機化合物の立体構造と全構成原子の同一平面性",
        "points": [
            "ベンゼン環の正六角形構造（炭素原子の $\\text{sp}^2$ 混成軌道）と平面性の理解",
            "ベンゼン分子 $\\text{C}_6\\text{H}_6$ の全12原子（6個のC，6個のH）が同一平面上にあることの同定",
            "メチル基やシクロヘキサン（$\\text{sp}^3$ 混成，イス形配座）の非平面性の排除"
        ],
        "solution": (
            "**【題目大意】**\n"
            "次の化合物の中から，分子中のすべての構成原子が同一平面上に存在するものを一つ選ぶ。\n"
            "$\\textcircled{1}$ 酢酸　$\\textcircled{2}$ ベンゼン　$\\textcircled{3}$ シクロヘキサン　$\\textcircled{4}$ ジエチルエーテル　$\\textcircled{5}$ メタン\n\n"
            "**【公式正解】**\n"
            "正解：$\\textcircled{2}$ （ベンゼン）\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "各分子の立体配座と原子の空間配置を検討する：\n"
            "- $\\textcircled{1}$ 酢酸 $\\text{CH}_3\\text{COOH}$：カルボキシ基部分は平面に近いが，メチル基 $-\\text{CH}_3$ の炭素は $\\text{sp}^3$ 混成軌道であり，水素原子が正四面体の頂点方向に突き出しているため，全原子が同一平面上にはない。\n"
            "- $\\textcircled{2}$ ベンゼン $\\text{C}_6\\text{H}_6$：6個の炭素原子はすべて $\\text{sp}^2$ 混成軌道をとっており，炭素骨格は完全な平面正六角形をなす。各炭素に直結する6個の水素原子も同一平面上に位置するため，12個の原子すべてが完全に同一平面上に存在する（正しい）。\n"
            "- $\\textcircled{3}$ シクロヘキサン $\\text{C}_6\\text{H}_{12}$：炭素原子はすべて $\\text{sp}^3$ 混成軌道をとっており，環は平面ではなく立体的な「イス形配座」をとる。\n"
            "- $\\textcircled{4}$ ジエチルエーテル $\\text{C}_2\\text{H}_5\\text{OC}_2\\text{H}_5$：エチル基の炭素および酸素は $\\text{sp}^3$ 混成であり，立体的なジグザグ配座をとる。\n"
            "- $\\textcircled{5}$ メタン $\\text{CH}_4$：炭素原子を中心に水素原子が正四面体の4つの頂点に位置する立体分子である。\n\n"
            "したがって，すべての原子が同一平面上にある化合物は $\\textcircled{2}$ である。\n\n"
            "**【考査考点】**\n"
            "有機化合物の幾何構造，炭素原子の混成軌道（$\\text{sp}^2$ 平面 vs $\\text{sp}^3$ 四面体），ベンゼン環の平面性。"
        )
    },
    {
        "q_num": 18,
        "localKey": "chem-q-18",
        "answer_ref": "CHEMISTRY:18",
        "answer": 3,
        "title": "化学 問18：エステルの完全燃焼反応における生成二酸化炭素および水の質量計算",
        "points": [
            "エステル $\\text{C}_4\\text{H}_8\\text{O}_2$ のモル質量 $M = 88.0\\text{ g/mol}$ の算出",
            "試料 $0.264\\text{ g}$ の物質量 $n = 0.0030\\text{ mol}$ の決定",
            "燃焼化学反応式 $\\text{C}_4\\text{H}_8\\text{O}_2 + 5\\text{O}_2 \\to 4\\text{CO}_2 + 4\\text{H}_2\\text{O}$ からの質量計算（$\\text{CO}_2 = 0.528\\text{ g}$，$\\text{H}_2\\text{O} = 0.216\\text{ g}$）"
        ],
        "solution": (
            "**【題目大意】**\n"
            "分子式 $\\text{C}_4\\text{H}_8\\text{O}_2$ のエステル $0.264\\text{ g}$ を完全燃焼させたときに生成する二酸化炭素 $\\text{CO}_2\\,[\\text{g}]$ と水 $\\text{H}_2\\text{O}\\,[\\text{g}]$ の質量の組み合わせを選ぶ。\n\n"
            "**【公式正解】**\n"
            "正解：$\\textcircled{3}$ （$\\text{CO}_2$：$0.528\\text{ g}$，$\\text{H}_2\\text{O}$：$0.216\\text{ g}$）\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "1. **エステルのモル質量と物質量**：\n"
            "原子量 $\\text{H} = 1.0$，$\\text{C} = 12$，$\\text{O} = 16$ より：\n"
            "$$M(\\text{C}_4\\text{H}_8\\text{O}_2) = 12 \\times 4 + 1.0 \\times 8 + 16 \\times 2 = 48 + 8 + 32 = 88.0\\text{ g/mol}$$\n"
            "燃焼させたエステルの物質量 $n$ は：\n"
            "$$n = \\frac{0.264\\text{ g}}{88.0\\text{ g/mol}} = 0.0030\\text{ mol}$$\n\n"
            "2. **完全燃焼反応式と生成物の物質量**：\n"
            "$$\\text{C}_4\\text{H}_8\\text{O}_2 + 5\\text{O}_2 \\longrightarrow 4\\text{CO}_2 + 4\\text{H}_2\\text{O}$$\n"
            "エステル $1\\text{ mol}$ の燃焼により，$\\text{CO}_2$ が $4\\text{ mol}$，$\\text{H}_2\\text{O}$ が $4\\text{ mol}$ 生成する。\n"
            "- 生成する $\\text{CO}_2$ の物質量：\n"
            "  $$n(\\text{CO}_2) = 4 \\times 0.0030 = 0.0120\\text{ mol}$$\n"
            "- 生成する $\\text{H}_2\\text{O}$ の物質量：\n"
            "  $$n(\\text{H}_2\\text{O}) = 4 \\times 0.0030 = 0.0120\\text{ mol}$$\n\n"
            "3. **各生成物の質量**：\n"
            "- 二酸化炭素（分子量 44.0）：\n"
            "  $$m(\\text{CO}_2) = 0.0120\\text{ mol} \\times 44.0\\text{ g/mol} = 0.528\\text{ g}$$\n"
            "- 水（分子量 18.0）：\n"
            "  $$m(\\text{H}_2\\text{O}) = 0.0120\\text{ mol} \\times 18.0\\text{ g/mol} = 0.216\\text{ g}$$\n\n"
            "したがって，$\\text{CO}_2 = 0.528\\text{ g}$，$\\text{H}_2\\text{O} = 0.216\\text{ g}$ であり，選択肢 $\\textcircled{3}$ が正解である。\n\n"
            "**【考査考点】**\n"
            "炭化水素誘導体の完全燃焼反応，元素分析の基本計算，化学反応式に基づく質量計算。"
        )
    },
    {
        "q_num": 19,
        "localKey": "chem-q-19",
        "answer_ref": "CHEMISTRY:19",
        "answer": 5,
        "title": "化学 問19：有機化学反応の素反応分類（付加・縮合・置換・還元）",
        "points": [
            "反応A：アセチレンへの水付加によるアセトアルデヒド経由またはエチレン水付加（付加反応）",
            "反応B：エタノールの分子間脱水によるジエチルエーテル生成（縮合反応）",
            "反応C：ベンゼンのニトロ化（芳香族求電子置換反応）",
            "反応D：ニトロ基の還元によるアニリン生成（還元反応）"
        ],
        "solution": (
            "**【題目大意】**\n"
            "示された反応経路における4つの素反応 (A)～(D) の反応形式の組み合わせとして最も適当なものを選ぶ。\n"
            "(A) $\\text{HC}\\equiv\\text{CH} \\xrightarrow{\\text{H}_2\\text{O}} \\text{CH}_3\\text{CHO}$（または $\\text{H}_2\\text{C}=\\text{CH}_2 \\xrightarrow{\\text{H}_2\\text{O}} \\text{CH}_3\\text{CH}_2\\text{OH}$）\n"
            "(B) $2\\text{CH}_3\\text{CH}_2\\text{OH} \\longrightarrow \\text{C}_2\\text{H}_5\\text{OC}_2\\text{H}_5 + \\text{H}_2\\text{O}$\n"
            "(C) ベンゼン $\\xrightarrow{\\text{HNO}_3, \\text{H}_2\\text{SO}_4}$ ニトロベンゼン\n"
            "(D) ニトロベンゼン $\\xrightarrow{\\text{Sn}, \\text{HCl}}$ アニリン\n\n"
            "**【公式正解】**\n"
            "正解：$\\textcircled{5}$ （A：付加，B：縮合，C：置換，D：還元）\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "各反応の分類を定義に基づいて判定する：\n"
            "- **反応 A**：不飽和炭化水素の多重結合に他の分子が結合して単結合（または二重結合）になる反応であり，「付加（addition）反応」である。\n"
            "- **反応 B**：2分子のエタノールから水分子 $1\\text{分子}$ が脱離してエーテル結合を形成する分子間脱水反応であり，「縮合（condensation）反応」である。\n"
            "- **反応 C**：ベンゼン環上の水素原子がニトロ基 $-\\text{NO}_2$ に置き換わる反応であり，「置換（substitution）反応」である。\n"
            "- **反応 D**：ニトロベンゼン $-\\text{NO}_2$ がスズと塩酸により水素化されてアミノ基 $-\\text{NH}_2$ になる反応であり，酸素の脱離と水素の付加を伴う「還元（reduction）反応」である。\n\n"
            "したがって，A：付加，B：縮合，C：置換，D：還元 となり，選択肢 $\\textcircled{5}$ が正解である。\n\n"
            "**【考査考点】**\n"
            "有機化学反応の基本様式（付加，脱水縮合，芳香族置換，ニトロ基の還元）。"
        )
    },
    {
        "q_num": 20,
        "localKey": "chem-q-20",
        "answer_ref": "CHEMISTRY:20",
        "answer": 6,
        "title": "化学 問20：酸の強弱差を利用した芳香族化合物（安息香酸・フェノール）の分液抽出",
        "points": [
            "酸の強さの序列：スルホン酸 $>$ カルボン酸（安息香酸）$>$ 炭酸 $>$ フェノール類 の理解",
            "強塩基 $\\text{NaOH}$ 添加時の両者塩形成・水層（下層）移行",
            "弱酸の塩 $\\text{NaHCO}_3$ 添加時の安息香酸のみの塩化（下層）とフェノールのエーテル層（上層）残留判定"
        ],
        "solution": (
            "**【題目大意】**\n"
            "安息香酸とフェノールをジエチルエーテルに溶かし，分液漏斗で以下の水溶液を加えて振り混ぜたときの，各物質のおもな抽出層（上層：エーテル層，下層：水層）の組み合わせを選ぶ。\n"
            "(a) 水酸化ナトリウム水溶液 $\\text{NaOH aq}$\n"
            "(b) 炭酸水素ナトリウム水溶液 $\\text{NaHCO}_3\\text{ aq}$\n\n"
            "**【公式正解】**\n"
            "正解：$\\textcircled{6}$ （(a) 安息香酸：下層，フェノール：下層；(b) 安息香酸：下層，フェノール：上層）\n\n"
            "**【詳細推導・解答プロセス】**\n"
            "1. **分液抽出の層の配置**：\n"
            "ジエチルエーテルの密度（約 $0.71\\text{ g/cm}^3$）は水（$1.0\\text{ g/cm}^3$）より小さいため，上層が有機層（エーテル層），下層が水層となる。\n"
            "中性の有機化合物は上層（エーテル層）に溶け，イオン性の塩は下層（水層）に溶ける。\n\n"
            "2. **酸の強さの序列**：\n"
            "$$\\text{R}-\\text{COOH}（安息香酸） > \\text{H}_2\\text{CO}_3（炭酸） > \\text{Ar}-\\text{OH}（フェノール）$$\n\n"
            "3. **操作 (a)：強塩基 $\\text{NaOH aq}$ を加えた場合**：\n"
            "- 安息香酸は強塩基と中和して安息香酸ナトリウムとなり，水層（下層）に移行する：\n"
            "  $$\\text{C}_6\\text{H}_5\\text{COOH} + \\text{NaOH} \\longrightarrow \\text{C}_6\\text{H}_5\\text{COONa} + \\text{H}_2\\text{O}$$\n"
            "- フェノールも弱酸であり強塩基と中和してナトリウムフェノキシドとなり，水層（下層）に移行する：\n"
            "  $$\\text{C}_6\\text{H}_5\\text{OH} + \\text{NaOH} \\longrightarrow \\text{C}_6\\text{H}_5\\text{ONa} + \\text{H}_2\\text{O}$$\n"
            "- したがって，(a) では安息香酸：下層，フェノール：下層 である。\n\n"
            "4. **操作 (b)：弱酸の塩 $\\text{NaHCO}_3\\text{ aq}$ を加えた場合**：\n"
            "- 安息香酸は炭酸よりも強い酸であるため，弱酸の遊離反応により炭酸を遊離して塩となり，水層（下層）に移行する：\n"
            "  $$\\text{C}_6\\text{H}_5\\text{COOH} + \\text{NaHCO}_3 \\longrightarrow \\text{C}_6\\text{H}_5\\text{COONa} + \\text{H}_2\\text{O} + \\text{CO}_2 \\uparrow$$\n"
            "- 一方，フェノールは炭酸よりも弱い酸であるため，$\\text{NaHCO}_3$ とは反応しない。未反応の非電解質フェノールのまま有機層（上層）にとどまる。\n"
            "- したがって，(b) では安息香酸：下層，フェノール：上層 である。\n\n"
            "5. **結論**：\n"
            "表の組み合わせは，(a) 安息香酸：下層，フェノール：下層；(b) 安息香酸：下層，フェノール：上層 であり，選択肢 $\\textcircled{6}$ が正解である。\n\n"
            "**【考査考点】**\n"
            "酸の相対的強弱関係，弱酸の遊離反応，有機化合物の分液抽出と分離精製法。"
        )
    }
]

def main():
    out_dir = Path("work/2012-2-science")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Save chemistry explanations to temporary json
    chem_path = out_dir / "chemistry_explanations.json"
    with open(chem_path, "w", encoding="utf-8") as f:
        json.dump(chemistry_questions, f, ensure_ascii=False, indent=2)
    print(f"Generated {chem_path} ({len(chemistry_questions)} questions)")
    
    # Generate markdown documentation
    md_path = Path("docs/explanations/2012-2-chemistry-solutions.md")
    md_path.parent.mkdir(parents=True, exist_ok=True)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# 2012-2 EJU 化学 詳解\n\n")
        for q in chemistry_questions:
            f.write(f"## {q['title']}\n\n")
            f.write(q["solution"] + "\n\n---\n\n")
    print(f"Generated {md_path}")

if __name__ == "__main__":
    main()

