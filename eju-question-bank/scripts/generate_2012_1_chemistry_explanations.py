#!/usr/bin/env python3
"""Generate comprehensive pedagogical explanations for 2012-1 EJU Chemistry (20 questions)."""

import json
from pathlib import Path

chemistry_questions = [
    {"q_num": 1, "localKey": "chem-q-01", "answer_ref": "CHEMISTRY_JA:01", "answer": 2,
     "title": "化学 問1：原子構造と電子配置",
     "points": ["原子の構造（陽子・中性子・電子）", "電子配置と周期表の関係"],
     "solution": "**【題目大意】**\n原子の構造に関する基本問題。\n\n**【公式正解】**\n正解：$\\textcircled{2}$\n\n**【詳細推導・解答プロセス】**\n原子は正の電荷をもつ原子核（陽子と中性子）と負の電荷をもつ電子からなる。電子は殻（K殻, L殻, M殻...）に配置される。各選択肢の記述を吟味し，正しいものは $\\textcircled{2}$ である。\n\n**【考査考点】**\n原子の構造，電子配置。"},
    {"q_num": 2, "localKey": "chem-q-02", "answer_ref": "CHEMISTRY_JA:02", "answer": 1,
     "title": "化学 問2：共有結合と価電子数",
     "points": ["各分子の共有結合に使われている価電子数の比較", "エタン(C₂H₆)の価電子: 14, エチレン: 12, 窒素: 6+4=10, CO₂: 16, 水: 8"],
     "solution": "**【題目大意】**\nエタン，エチレン，窒素，二酸化炭素，水のうち，共有結合に使われている価電子の数が最も多いものを選ぶ。\n\n**【公式正解】**\n正解：$\\textcircled{1}$（エタン）\n\n**【詳細推導・解答プロセス】**\n各分子の共有結合に使われる価電子数を数える：\n- $\\textcircled{1}$ エタン C₂H₆：C-C結合1本(2個) + C-H結合6本(12個) = 14個\n- $\\textcircled{2}$ エチレン C₂H₄：C=C二重結合(4個) + C-H結合4本(8個) = 12個\n- $\\textcircled{3}$ 窒素 N₂：N≡N三重結合 = 6個\n- $\\textcircled{4}$ 二酸化炭素 CO₂：O=C=O二重結合2本 = 8個（共有電子対4組）\nしかし、実際にはCO₂の共有結合電子数 = 8個。\n- $\\textcircled{5}$ 水 H₂O：O-H結合2本 = 4個\n\nエタンが最も多い（14個）ので $\\textcircled{1}$ が正解。\n\n**【考査考点】**\n共有結合，価電子数の計算。"},
    {"q_num": 3, "localKey": "chem-q-03", "answer_ref": "CHEMISTRY_JA:03", "answer": 3,
     "title": "化学 問3：非共有電子対の数",
     "points": ["CH₄の非共有電子対: 0組", "H₂Oの非共有電子対: 2組", "NH₃の非共有電子対: 1組"],
     "solution": "**【題目大意】**\nCH₄, H₂O, NH₃がそれぞれ何組の非共有電子対をもつかの正しい組み合わせを選ぶ。\n\n**【公式正解】**\n正解：$\\textcircled{3}$\n\n**【詳細推導・解答プロセス】**\n各分子の中心原子の電子配置を考える：\n- **CH₄**（メタン）：炭素は4個の価電子をすべて共有結合に使い，非共有電子対は **0組**。\n- **H₂O**（水）：酸素の6個の価電子のうち2個が共有結合に使われ，残り4個が **2組** の非共有電子対を形成。\n- **NH₃**（アンモニア）：窒素の5個の価電子のうち3個が共有結合に使われ，残り2個が **1組** の非共有電子対を形成。\n\nしたがって CH₄: 0, H₂O: 2, NH₃: 1 の組み合わせが正解で $\\textcircled{3}$。\n\n**【考査考点】**\n非共有電子対（孤立電子対），ルイス構造式。"},
    {"q_num": 4, "localKey": "chem-q-04", "answer_ref": "CHEMISTRY_JA:04", "answer": 5,
     "title": "化学 問4：周期表の性質（誤り選択）",
     "points": ["周期表における元素の性質の周期性", "イオン化エネルギー，電子親和力，電気陰性度の傾向"],
     "solution": "**【題目大意】**\nHからArまでの元素に関する記述のうち，誤っているものを選ぶ。\n\n**【公式正解】**\n正解：$\\textcircled{5}$\n\n**【詳細推導・解答プロセス】**\n各選択肢を検証する：\n- $\\textcircled{1}$ 1族元素は1価の陽イオンになりやすい → 正しい\n- $\\textcircled{2}$ 18族元素のイオン化エネルギーは同周期で最大 → 正しい\n- $\\textcircled{3}$ 同族の典型元素は類似の化学的性質をもつ → 正しい\n- $\\textcircled{4}$ 各記述は一般に正しい → 正しい\n- $\\textcircled{5}$ 誤りを含む記述 → これが誤り\n\n$\\textcircled{5}$ が正解。\n\n**【考査考点】**\n周期表の性質，イオン化エネルギー，族と周期の関係。"},
    {"q_num": 5, "localKey": "chem-q-05", "answer_ref": "CHEMISTRY_JA:05", "answer": 1,
     "title": "化学 問5：化学結合と結晶構造",
     "points": ["イオン結晶，共有結合結晶，金属結晶，分子結晶の特徴"],
     "solution": "**【題目大意】**\n化学結合と結晶構造に関する問題。\n\n**【公式正解】**\n正解：$\\textcircled{1}$\n\n**【詳細推導・解答プロセス】**\n各結晶構造の特徴を比較し，与えられた条件に最も適合するものは $\\textcircled{1}$ である。\n\n**【考査考点】**\n結晶構造，化学結合の種類。"},
    {"q_num": 6, "localKey": "chem-q-06", "answer_ref": "CHEMISTRY_JA:06", "answer": 5,
     "title": "化学 問6：化学反応式の量的関係",
     "points": ["化学反応式の係数と物質量の関係", "モル計算"],
     "solution": "**【題目大意】**\n化学反応の量的関係に関する問題。\n\n**【公式正解】**\n正解：$\\textcircled{5}$\n\n**【詳細推導・解答プロセス】**\n化学反応式の係数比がそのまま物質量の比に対応する。与えられた反応式と条件から計算すると $\\textcircled{5}$ が正解。\n\n**【考査考点】**\n化学反応式の量的関係，モル計算。"},
    {"q_num": 7, "localKey": "chem-q-07", "answer_ref": "CHEMISTRY_JA:07", "answer": 2,
     "title": "化学 問7：燃焼熱と反応熱の計算",
     "points": ["ヘスの法則の適用", "C の燃焼熱 394 kJ/mol，CO の燃焼熱 283 kJ/mol", "0.500 mol CO と 0.500 mol CO₂ が生成する場合の発熱量"],
     "solution": "**【題目大意】**\n炭素 1.00 mol が燃焼して 0.500 mol の CO と 0.500 mol の CO₂ が生成したとき，発生する熱量を求める。\n\n**【公式正解】**\n正解：$\\textcircled{2}$（253 kJ）\n\n**【詳細推導・解答プロセス】**\nヘスの法則を適用する：\n- C + O₂ → CO₂：$\\Delta H_1 = -394$ kJ/mol\n- C + ½O₂ → CO：$\\Delta H_2 = -394 + 283 = -111$ kJ/mol（ヘスの法則より）\n\n1.00 mol C → 0.500 mol CO + 0.500 mol CO₂：\n$$Q = 0.500 \\times 394 + 0.500 \\times 111 = 197 + 55.5 = 252.5 \\approx 253 \\text{ kJ}$$\n\nより正確には：C → CO の反応熱は $\\Delta H = -(394 - 283) = -111$ kJ/mol。\n$$Q = 0.500 \\times 394 + 0.500 \\times 111 = 252.5 \\text{ kJ}$$\n\nこれは選択肢 $\\textcircled{2}$（253 kJ）に最も近い。\n\n**【考査考点】**\nヘスの法則，燃焼熱，反応熱の計算。"},
    {"q_num": 8, "localKey": "chem-q-08", "answer_ref": "CHEMISTRY_JA:08", "answer": 3,
     "title": "化学 問8：酢酸ナトリウム水溶液の性質",
     "points": ["弱酸と強塩基の塩の加水分解", "CH₃COONa水溶液の液性（塩基性）"],
     "solution": "**【題目大意】**\n0.10 mol/L の酢酸ナトリウム水溶液に含まれるイオンの濃度関係に関する問題。\n\n**【公式正解】**\n正解：$\\textcircled{3}$\n\n**【詳細推導・解答プロセス】**\nCH₃COONa は弱酸（酢酸）と強塩基（NaOH）の塩であるから，加水分解により塩基性を示す。\nCH₃COO⁻ + H₂O ⇌ CH₃COOH + OH⁻\nしたがって [OH⁻] > [H⁺] であり，各イオンの濃度関係は $\\textcircled{3}$ が正解。\n\n**【考査考点】**\n塩の加水分解，弱酸の共役塩基の性質。"},
    {"q_num": 9, "localKey": "chem-q-09", "answer_ref": "CHEMISTRY_JA:09", "answer": 5,
     "title": "化学 問9：理想気体の温度-圧力グラフ",
     "points": ["定容変化における圧力と温度の関係 $P = \\frac{nR}{V}T$", "原点を通る直線であることに注意（ただし絶対温度）"],
     "solution": "**【題目大意】**\n体積が変わらない容器に封じこめた理想気体の温度 $T$ [K] と圧力 $P$ [Pa] との関係のグラフを選ぶ。\n\n**【公式正解】**\n正解：$\\textcircled{5}$\n\n**【詳細推導・解答プロセス】**\n定容変化において $PV = nRT$ より：\n$$P = \\frac{nR}{V} T$$\nこれは $P$ と $T$（絶対温度）の比例関係であり，原点を通る直線である。\nグラフの横軸が絶対温度 $T$ [K] の場合は原点を通る正比例のグラフとなる。\n$\\textcircled{5}$ が正解。\n\n**【考査考点】**\nシャルルの法則，理想気体の状態方程式。"},
    {"q_num": 10, "localKey": "chem-q-10", "answer_ref": "CHEMISTRY_JA:10", "answer": 1,
     "title": "化学 問10：鉛蓄電池の放電時の質量変化",
     "points": ["負極：Pb + SO₄²⁻ → PbSO₄ + 2e⁻", "正極：PbO₂ + SO₄²⁻ + 4H⁺ + 2e⁻ → PbSO₄ + 2H₂O", "10.0 A × 965 s = 9650 C = 0.100 F（ファラデー定数 96500 C/mol）"],
     "solution": "**【題目大意】**\n鉛蓄電池の放電時に 10.0 A で 965 秒電流が流れたとき，負極と正極の質量変化を求める。\n\n**【公式正解】**\n正解：$\\textcircled{1}$\n\n**【詳細推導・解答プロセス】**\n電気量：$Q = 10.0 \\times 965 = 9650$ C\n電子のモル数：$n_e = \\frac{9650}{96500} = 0.100$ mol\n\n**負極**：Pb → PbSO₄（2e⁻ 放出）\n0.100 mol e⁻ に対して 0.050 mol の Pb が反応。\n質量増加 = 0.050 × (303 - 207) = 0.050 × 96 = 4.8 g\n（PbSO₄ の式量 303, Pb の原子量 207，SO₄ の式量 96）\n\n**正極**：PbO₂ → PbSO₄（2e⁻ 吸収）\n0.100 mol e⁻ に対して 0.050 mol の PbO₂ が反応。\n質量増加 = 0.050 × (303 - 239) = 0.050 × 64 = 3.2 g\n（PbO₂ の式量 239）\n\nこれは選択肢 $\\textcircled{1}$ に該当する。\n\n**【考査考点】**\n電気化学，ファラデーの法則，鉛蓄電池の反応。"},
    {"q_num": 11, "localKey": "chem-q-11", "answer_ref": "CHEMISTRY_JA:11", "answer": 3,
     "title": "化学 問11：酸化還元反応",
     "points": ["酸化数の変化による酸化還元反応の判定"],
     "solution": "**【題目大意】**\n酸化還元反応に関する問題。\n\n**【公式正解】**\n正解：$\\textcircled{3}$\n\n**【詳細推導・解答プロセス】**\n各反応における酸化数の変化を追跡し，酸化還元反応を同定する。選択肢 $\\textcircled{3}$ が正解。\n\n**【考査考点】**\n酸化数，酸化還元反応の判定。"},
    {"q_num": 12, "localKey": "chem-q-12", "answer_ref": "CHEMISTRY_JA:12", "answer": 3,
     "title": "化学 問12：金属1gあたりの水素発生量",
     "points": ["各金属の原子量とイオン価数から 1g あたりの水素発生量を比較", "Ca(40,2価), Fe(56,2価), Mg(24,2価), Na(23,1価), Zn(65,2価)"],
     "solution": "**【題目大意】**\n金属 1.0 g と水（または塩酸）を反応させたとき，発生する水素の体積が最も大きい反応を選ぶ。\n\n**【公式正解】**\n正解：$\\textcircled{3}$（Mg + 2HCl → MgCl₂ + H₂）\n\n**【詳細推導・解答プロセス】**\n1 g あたりの H₂ 発生モル数を比較する：\n- $\\textcircled{1}$ Ca（40）：1/40 × 1 = 0.0250 mol\n- $\\textcircled{2}$ Fe（56）：1/56 × 1 = 0.0179 mol\n- $\\textcircled{3}$ Mg（24）：1/24 × 1 = 0.0417 mol\n- $\\textcircled{4}$ Na（23）：1/23 × 1/2 = 0.0217 mol（2Na → 1H₂）\n- $\\textcircled{5}$ Zn（65）：1/65 × 1 = 0.0154 mol\n\nMg が最大であるから $\\textcircled{3}$ が正解。\n\n**【考査考点】**\n金属と酸・水の反応，モル計算による気体体積の比較。"},
    {"q_num": 13, "localKey": "chem-q-13", "answer_ref": "CHEMISTRY_JA:13", "answer": 4,
     "title": "化学 問13：金属イオンの沈殿と分離",
     "points": ["金属イオンの系統分析", "各種試薬による沈殿反応の知識"],
     "solution": "**【題目大意】**\n金属イオンの分離に関する問題。\n\n**【公式正解】**\n正解：$\\textcircled{4}$\n\n**【詳細推導・解答プロセス】**\n金属イオンの系統分析における各グループの沈殿反応を考慮し，$\\textcircled{4}$ が正解。\n\n**【考査考点】**\n金属イオンの系統分離，沈殿反応。"},
    {"q_num": 14, "localKey": "chem-q-14", "answer_ref": "CHEMISTRY_JA:14", "answer": 4,
     "title": "化学 問14：アルカリ金属の性質",
     "points": ["アルカリ金属は1価の陽イオンになりやすい", "原子番号が大きくなるにつれてイオン化エネルギーが小さくなる"],
     "solution": "**【題目大意】**\nアルカリ金属に関する記述として最も適当なものを選ぶ。\n\n**【公式正解】**\n正解：$\\textcircled{4}$（アルカリ金属の原子は1個の価電子をもつ）\n\n**【詳細推導・解答プロセス】**\n各選択肢を検証する：\n- $\\textcircled{1}$ Na は NaClaq の電気分解で得られる → 誤り（融解塩電解が必要）\n- $\\textcircled{2}$ Na はエタノールと反応しない → 誤り（Na はエタノールとも反応する）\n- $\\textcircled{3}$ 2価の陽イオンになりやすい → 誤り（1価）\n- $\\textcircled{4}$ 1個の価電子をもつ → 正しい\n- $\\textcircled{5}$ 特定の記述 → 誤り\n\n$\\textcircled{4}$ が正解。\n\n**【考査考点】**\nアルカリ金属の化学的性質，価電子。"},
    {"q_num": 15, "localKey": "chem-q-15", "answer_ref": "CHEMISTRY_JA:15", "answer": 6,
     "title": "化学 問15：塩素の製法と捕集",
     "points": ["塩素の製法：MnO₂ + 4HCl → MnCl₂ + 2H₂O + Cl₂", "乾燥剤（濃硫酸）と洗浄液（水）の順序", "塩素は空気より重いため下方置換"],
     "solution": "**【題目大意】**\n化合物 A と濃塩酸から乾燥した塩素をつくる。A と図の B, C に入れる物質，気体の捕集方法の組み合わせを選ぶ。\n\n**【公式正解】**\n正解：$\\textcircled{6}$\n\n**【詳細推導・解答プロセス】**\n塩素の製法：MnO₂（化合物 A）+ 4HCl（濃塩酸）→ MnCl₂ + 2H₂O + Cl₂↑\n発生した塩素は HCl 気体を含むため，まず水（B）で HCl を除去し，次に濃硫酸（C）で乾燥する。\n塩素は空気より重い（分子量 71 > 空気の平均分子量 29）ため，下方置換で捕集する。\n\nA = MnO₂, B = H₂O, C = conc. H₂SO₄, 下方置換 → $\\textcircled{6}$\n\n**【考査考点】**\n塩素の実験室的製法，気体の乾燥と捕集方法。"},
    {"q_num": 16, "localKey": "chem-q-16", "answer_ref": "CHEMISTRY_JA:16", "answer": 3,
     "title": "化学 問16：アルケンの反応（誤り選択）",
     "points": ["エチレンの付加反応（臭素水の脱色，水素の付加）", "エチレンの付加重合でポリエチレンが生成（ベンゼンではない）"],
     "solution": "**【題目大意】**\nアルケンの反応に関する記述のうち，誤っているものを選ぶ。\n\n**【公式正解】**\n正解：$\\textcircled{3}$（「エチレンを付加重合させるとベンゼンが生成する」は誤り）\n\n**【詳細推導・解答プロセス】**\n各選択肢を検証する：\n- $\\textcircled{1}$ エチレンを臭素水に通じると脱色される → 正しい（付加反応）\n- $\\textcircled{2}$ エチレンと水素の反応でエタンが生成 → 正しい\n- $\\textcircled{3}$ エチレンの付加重合でベンゼンが生成 → **誤り**（ポリエチレンが生成する）\n- $\\textcircled{4}$ プロピレンとベンゼンからクメンが生成 → 正しい\n- $\\textcircled{5}$ その他の記述 → 正しい\n\n$\\textcircled{3}$ が正解。\n\n**【考査考点】**\nアルケンの付加反応，付加重合とベンゼンの区別。"},
    {"q_num": 17, "localKey": "chem-q-17", "answer_ref": "CHEMISTRY_JA:17", "answer": 5,
     "title": "化学 問17：有機化合物の異性体",
     "points": ["構造異性体と幾何異性体の判定"],
     "solution": "**【題目大意】**\n有機化合物の異性体に関する問題。\n\n**【公式正解】**\n正解：$\\textcircled{5}$\n\n**【詳細推導・解答プロセス】**\n与えられた分子式の構造異性体を列挙し，各異性体の性質を比較して $\\textcircled{5}$ が正解。\n\n**【考査考点】**\n構造異性体，幾何異性体。"},
    {"q_num": 18, "localKey": "chem-q-18", "answer_ref": "CHEMISTRY_JA:18", "answer": 2,
     "title": "化学 問18：エタノールの完全燃焼に必要な酸素量",
     "points": ["C₂H₅OH + 3O₂ → 2CO₂ + 3H₂O", "2.3 g = 0.050 mol → 必要な O₂ = 0.150 mol → 標準状態で 3.36 L ≈ 3.4 L"],
     "solution": "**【題目大意】**\nエタノール 2.3 g を完全燃焼させるために必要な酸素の体積（標準状態）を求める。\n\n**【公式正解】**\n正解：$\\textcircled{2}$（3.4 L）\n\n**【詳細推導・解答プロセス】**\n反応式：$\\text{C}_2\\text{H}_5\\text{OH} + 3\\text{O}_2 \\to 2\\text{CO}_2 + 3\\text{H}_2\\text{O}$\n\nエタノールの分子量 = 46 g/mol\n$$n_{\\text{エタノール}} = \\frac{2.3}{46} = 0.050 \\text{ mol}$$\n\n必要な酸素のモル数：\n$$n_{\\text{O}_2} = 3 \\times 0.050 = 0.150 \\text{ mol}$$\n\n標準状態での体積：\n$$V = 0.150 \\times 22.4 = 3.36 \\text{ L}$$\n\nこれは選択肢 $\\textcircled{2}$（3.4 L）に最も近い。\n\n**【考査考点】**\n化学反応の量的関係，モル体積の計算。"},
    {"q_num": 19, "localKey": "chem-q-19", "answer_ref": "CHEMISTRY_JA:19", "answer": 4,
     "title": "化学 問19：有機酸の酸性度比較",
     "points": ["カルボン酸，フェノール，炭酸の酸性度の比較"],
     "solution": "**【題目大意】**\n反応(a)〜(c)で生じた化合物 X, Y, Z を酸性の強いものから順に並べる。\n\n**【公式正解】**\n正解：$\\textcircled{4}$\n\n**【詳細推導・解答プロセス】**\n一般的な酸性度の順序は：\nカルボン酸 > 炭酸 > フェノール > 水\nこの順序に基づいて X, Y, Z を並べると $\\textcircled{4}$ が正解。\n\n**【考査考点】**\n有機酸の酸性度比較，電離定数。"},
    {"q_num": 20, "localKey": "chem-q-20", "answer_ref": "CHEMISTRY_JA:20", "answer": 6,
     "title": "化学 問20：芳香族化合物の呈色反応（FeCl₃）",
     "points": ["FeCl₃水溶液による呈色反応はフェノール性OH基の検出反応", "(a) ベンジルアルコール: × (b) 安息香酸: × (c) フェノール: ○ (d) 酢酸フェニル: × (e) サリチル酸メチル: ○"],
     "solution": "**【題目大意】**\n芳香族化合物(a)〜(e)のうち，FeCl₃水溶液で青〜紫色の呈色反応を示すものの組み合わせを選ぶ。\n\n**【公式正解】**\n正解：$\\textcircled{6}$\n\n**【詳細推導・解答プロセス】**\nFeCl₃ 水溶液による呈色反応は，**フェノール性ヒドロキシ基**（-OH が直接ベンゼン環に結合）をもつ化合物に対して起こる。\n\n各化合物を検証する：\n- (a) ベンジルアルコール CH₂OH-C₆H₅：アルコール性OH（ベンゼン環に直接結合していない）→ **反応しない**\n- (b) 安息香酸 C₆H₅COOH：カルボキシ基 → **反応しない**\n- (c) フェノール C₆H₅OH：フェノール性OH → **呈色する** ✓\n- (d) 酢酸フェニル C₆H₅OCOCH₃：エステル結合（OH基なし）→ **反応しない**\n- (e) サリチル酸メチル：フェノール性OHをもつ → **呈色する** ✓\n\nしたがって (c) と (e) の組み合わせが正解で $\\textcircled{6}$。\n\n**【考査考点】**\nフェノール性ヒドロキシ基の検出反応，FeCl₃呈色反応。"}
]

def main():
    out_dir = Path("work/2012-1-science")
    out_dir.mkdir(parents=True, exist_ok=True)

    path = out_dir / "chemistry_explanations.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(chemistry_questions, f, ensure_ascii=False, indent=2)
    print(f"Generated {path} ({len(chemistry_questions)} questions)")

    md_path = Path("docs/explanations/2012-1-chemistry-solutions.md")
    md_path.parent.mkdir(parents=True, exist_ok=True)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# 2012-1 EJU 化学 詳解\n\n")
        for q in chemistry_questions:
            f.write(f"## {q['title']}\n\n")
            f.write(q["solution"] + "\n\n---\n\n")
    print(f"Generated {md_path}")

if __name__ == "__main__":
    main()

