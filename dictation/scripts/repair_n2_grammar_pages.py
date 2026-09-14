#!/usr/bin/env python3
"""Reconcile the extracted N2 grammar pages against the book's weekly indexes.

The generic extractor cannot reliably distinguish grey title bands from the floating
connection legends in this particular scan.  The book itself provides an independent
``今週の表現`` ledger at the start of every week, so this repair is deterministic:
bind those listed entries to their known two-page lessons, retain the OCR evidence for
examples/translations, and leave exercises outside the lexicon pack.
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))

from lexicon_import import (  # noqa: E402
    _build_entry_block,
    _find_unit_header,
    _split_box_groups,
    clean_line,
    parse_connection_line,
)


HEADWORDS: dict[tuple[int, int], list[str]] = {
    (1, 1): ["さびしげ", "病気がち", "忘れっぽい", "疲れ気味"],
    (1, 2): ["帰れるものなら", "暑いものだから", "知らなかったんだもの", "持っているものの"],
    (1, 3): ["車はもとより自転車も", "見た目はともかく味は", "旅行はまだしも", "仕事の話は抜きにして"],
    (1, 4): ["心配でたまらない", "ひまでしょうがない", "うるさくてかなわない", "残念でならない"],
    (1, 5): ["食べないことはない", "覚えられないこともない", "言わないではいられない", "飲まずにはいられない"],
    (1, 6): ["帰らねばならない", "忘れてはならない", "待っていられない", "遊んでばかりはいられない"],
    (2, 1): ["努力のかいがあって", "手術のかいもなく", "やりがい", "借金してまで／借金までして"],
    (2, 2): ["読みかける", "読み切る", "ありえる／ありうる", "やり抜く"],
    (2, 3): ["忘れないうちに", "終わるか終わらないかのうちに", "日本にいる限り", "70歳以上の方に限り"],
    (2, 4): ["これさえあれば", "かわいいからこそ", "信頼してこそ", "上がるばかりだ"],
    (2, 5): ["子どもにしたら", "本当だとしたら", "行くとしても", "社会参加を目的として"],
    (2, 6): ["家族とともに", "増加にともなって", "年を取るにつれて", "北へ行くにしたがって"],
    (3, 1): ["言ったとおり", "言われるままに", "驚いたことに", "緊張のあまり"],
    (3, 2): ["寒いわけだ", "ほしくないわけではない", "するわけがない", "休むわけにはいかない"],
    (3, 3): ["開けたとたん", "騒いだあげく", "悩んだ末", "来たかと思ったら"],
    (3, 4): ["お忙しいところ", "検査したところ", "仕事どころではない", "夏休みどころか"],
    (3, 5): ["間違いだらけ", "行ったきり", "立ちっぱなし"],
    (3, 6): ["予想に反して", "便利な反面", "水に強い一方", "進む一方だ"],
    (4, 1): ["できる上に", "考えた上で", "選ばれた上は", "天気図の上では"],
    (4, 2): ["初心者向け", "天気次第で", "戻り次第", "伺った次第です"],
    (4, 3): ["客の意見にこたえて", "目上の人に対して", "法律により", "事件にかかわって"],
    (4, 4): ["知りながら", "忙しいと言いつつ", "進歩しつつある", "知らないくせして"],
    (4, 5): ["すべきではない", "続けざるをえない", "行われることになっている", "言い間違いにすぎない"],
    (4, 6): ["利用にあたり", "資料に沿って", "開店に先立ち", "広い範囲にわたって"],
    (5, 1): ["覚えられっこない", "言いかねない", "わかりかねる", "信じがたい"],
    (5, 2): ["富士山が見えることから", "彼のことだから", "休むことなく", "やってみないことにはわからない"],
    (5, 3): ["嫌われて当然だ", "怒るのももっともだ", "新品も同然だ", "あるだけましだ"],
    (5, 4): ["一流ホテルだけあって", "成績がいいばかりかスポーツも", "あの飛行機に乗ったばかりに", "日本のみならず外国でも"],
    (5, 5): ["飲もうではないか", "言いようがない", "泣いているかのようだ", "行けそうにない"],
    (5, 6): ["申し込みに際して", "計画に基づいて", "必要に応じて", "青空の下で"],
    (6, 1): ["日本に来て以来", "試験を受ける以上", "約束したからには", "来日の折には"],
    (6, 2): ["客の立場から言うと", "症状からすると", "服装からして", "外国人から見ると"],
    (6, 3): ["好きだからといって", "手続きしてからでないと", "2007年から2009年にかけて", "足の速さにかけては"],
    (6, 4): ["中止だとか", "二度と行くまい", "わかるまい", "話そうか話すまいか"],
    (6, 5): ["勝つに決まっている", "勝つとは限らない", "祈るよりほかない", "努力の結果にほかならない"],
    (6, 6): ["中国をはじめアジアの国々が", "憲法改正をめぐって", "京都において", "現地にて"],
    (7, 1): ["人目もかまわず", "雨にもかかわらず", "来る来ないにかかわらず", "年齢を問わず"],
    (7, 2): ["本やらノートやら", "見るにつけ聞くにつけ", "行くにしろ行かないにしろ", "勉強もできればスポーツもできる"],
    (7, 3): ["薬は苦いものだ", "するものではない", "無理というものだ", "行くものか"],
    (7, 4): ["東京を中心に", "感謝の気持ちをこめて", "友人を通じて", "地図を頼りに"],
    (7, 5): ["倒れたりする恐れがある", "つらいものがある", "多ければいいというものでもない", "どうにかならないものか"],
    (7, 6): ["事実をもとに", "調整中につき", "入学をきっかけに", "受験の際に"],
    (8, 1): ["高かった。それなのにすぐ壊れた。", "大雨だ。それでも出かける。", "渋滞だとか。それなら電車で行こう。", "働きすぎた。それで病気になった。"],
    (8, 2): ["それがまだなんです。", "渋滞するらしい。そこで早く出発したい。", "そういえば田中君、元気？", "それはそうと試験はいつだっけ？"],
    (8, 3): ["母の兄、すなわちおじさん", "ファックスあるいはメールで", "貧しい。だが幸せだ。", "怒ってる。だって約束を破ったから。"],
    (8, 4): ["まだ来ない。ということは欠席だ。", "外出できない。というのは父の具合が悪いんです。", "彼はまじめだ。したがって信頼されている。", "3割引。ただしこの棚の商品を除く。"],
    (8, 5): ["飲食禁止。もっとも水はかまいません。", "以上です。なお詳細は…", "終わります。さて来週は…", "薬を塗った。すると痛みが治まった。"],
    (8, 6): ["大敗した。要するに力の差があった。", "美人だ。しかも性格もいい。", "高いし、まずい。おまけにサービスも…", "一般に…。ちなみにうちにも…"],
}

WEEK_START = {1: 18, 2: 34, 3: 50, 4: 66, 5: 82, 6: 98, 7: 114, 8: 130}

# Only used where the scan lost or merged every Chinese example translation for the
# entry. These short meanings are manually checked against the visible source page.
GLOSS_ZH = {
    "やりがい": "值得做；做某事的价值或成就感",
    "忘れないうちに": "趁还没有忘记",
    "家族とともに": "和家人一起；与……同时",
    "増加にともなって": "随着……增加",
    "夏休みどころか": "别说……，就连……也不；非但……反而……",
    "資料に沿って": "按照资料；沿着……",
    "日本に来て以来": "自从来到日本以来",
    "試験を受ける以上": "既然参加考试",
    "約束したからには": "既然已经约定",
    "渋滞だとか。それなら電車で行こう。": "听说会堵车；那样的话就坐电车去吧",
    "そういえば田中君、元気？": "说起来，田中最近好吗？",
    "それはそうと試験はいつだっけ？": "话说回来，考试是什么时候？",
    "母の兄、すなわちおじさん": "母亲的哥哥，也就是舅舅",
    "怒ってる。だって約束を破ったから。": "我生气了，因为你没有遵守约定",
    "まだ来ない。ということは欠席だ。": "还没来，也就是说他缺席了",
    "外出できない。というのは父の具合が悪いんです。": "不能外出，这是因为父亲身体不舒服",
    "3割引。ただしこの棚の商品を除く。": "打七折，但这个货架上的商品除外",
    "以上です。なお詳細は…": "以上。此外，详细情况是……",
    "終わります。さて来週は…": "到此结束。那么，下周……",
}

# Literal transcriptions checked against ``out/N2-grammar/crops/page-NNNN.png``.
# These are deliberately keyed by the immutable weekly-ledger headword rather than by
# the OCR segment: regenerating OCR must not reintroduce a deleted kana or flatten a
# bracketed suffix.  Add rows only after checking the crop; unlisted entries retain the
# conspicuous review flag below.
REVIEWED_CONNECTIONS: dict[str, list[str]] = {
    "さびしげ": ["Aげ", "naげ", "Vたげ"],
    "病気がち": ["Nがち", "Vますがち"],
    "忘れっぽい": ["Nっぽい", "Vますっぽい", "Aっぽい"],
    "疲れ気味": ["Vます気味", "N気味"],
    "帰れるものなら": ["Vれるものなら"],
    "暑いものだから": ["Vものだから", "Aものだから", "naなものだから", "Nなものだから"],
    "知らなかったんだもの": ["Vもの", "Aもの", "naなんだもの", "Nなんだもの"],
    "持っているものの": ["Vものの", "Aものの", "naなものの", "Nであるものの"],
    "車はもとより自転車も": ["Nはもとより〜も"],
    "見た目はともかく味は": ["Nはともかく（として）"],
    "旅行はまだしも": ["Nはまだしも", "Nならまだしも"],
    "仕事の話は抜きにして": ["N抜きにして", "N抜きで", "N抜きに", "N抜きの"],
    "心配でたまらない": ["Aくてたまらない", "naでたまらない", "Vたくてたまらない"],
    "ひまでしょうがない": ["Aくてしょうがない", "naでしょうがない", "Vてしょうがない"],
    "うるさくてかなわない": ["Aくてかなわない", "naでかなわない"],
    "残念でならない": ["Aくてならない", "naでならない", "Vてならない"],
    "食べないことはない": ["Aくないことはない", "naじゃないことはない", "Vないことはない", "Vられないことはない"],
    "覚えられないこともない": ["Aくないこともない", "naじゃないこともない", "Vないこともない", "Vられないこともない"],
    "言わないではいられない": ["Vないではいられない"],
    "飲まずにはいられない": ["Vないずにはいられない"],
    "帰らねばならない": ["Vないねばならない"],
    "忘れてはならない": ["Vてはならない"],
    "待っていられない": ["Vてはいられない"],
    "遊んでばかりはいられない": ["Vてばかりはいられない"],
    "努力のかいがあって": ["Vるかいがある", "Vたかいがある", "Nのかいがある", "Nのかいがあって"],
    "手術のかいもなく": ["Vたかいがない", "Nのかいがない", "Nのかいもなく"],
    "やりがい": ["Vますがい"],
    "借金してまで／借金までして": ["Vてまで（も）", "Nまでして"],
    "読みかける": ["Vますかける", "Vますかけの", "Vますかけだ"],
    "読み切る": ["Vます切る", "Vます切れる", "Vます切れない"],
    "ありえる／ありうる": ["Vますえる", "Vますうる", "Vますえない"],
    "やり抜く": ["Vます抜く"],
    "忘れないうちに": ["Vないうちに", "Vているうちに", "Aいうちに", "naなうちに", "Nのうちに"],
    "終わるか終わらないかのうちに": ["Vるか〜ないかのうちに"],
    "日本にいる限り": ["Vる限り", "Vない限り", "Aい限り", "Aくない限り", "naな限り", "naである限り", "Nである限り", "Vた限り", "Vている限り"],
    "70歳以上の方に限り": ["Nに限り", "Nに限って", "Nに限らず〜も"],
    "これさえあれば": ["Nさえ", "Vば", "Aければ", "naなら", "Nなら", "Vますさえすれば"],
    "かわいいからこそ": ["Vからこそ", "Aからこそ", "naだからこそ", "Nだからこそ", "Vばこそ", "Aければこそ", "naであればこそ", "Nであればこそ"],
    "信頼してこそ": ["Vてこそ"],
    "上がるばかりだ": ["Vるばかりだ"],
    "子どもにしたら": ["Nにしたら", "Nにすれば", "Nにしてみたら", "Nにしてみれば"],
    "本当だとしたら": ["Vとしたら", "Aとしたら", "naだとしたら", "Nだとしたら", "Vとすれば", "Aとすれば", "naだとすれば", "Nだとすれば"],
    "行くとしても": ["Vとしても", "Aとしても", "naだとしても", "Nだとしても", "Vにしても", "Aにしても", "naにしても", "Nにしても"],
    "社会参加を目的として": ["Nを〜として", "Nを〜とする", "Nを〜とした"],
    "家族とともに": ["Nとともに", "Vるとともに"],
    "増加にともなって": ["Nにともない", "Nにともなって", "Nにともなう", "Vるにともない", "Vたにともない"],
    "年を取るにつれて": ["Nにつれて", "Vるにつれて"],
    "北へ行くにしたがって": ["Nにしたがって", "Nにしたがい", "Vるにしたがって", "Vるにしたがい"],
    "言ったとおり": ["Vるとおり", "Vたとおり", "Nのとおり", "Nどおり"],
    "言われるままに": ["Vるまま", "Vられるまま"],
    "驚いたことに": ["Aいことに", "naなことに", "Vたことに"],
    "緊張のあまり": ["Nのあまり", "naなあまり", "Vるあまり"],
    "寒いわけだ": ["Aわけだ", "naなわけだ", "Vわけだ", "Vているわけだ", "Vていたわけだ", "Vられるわけだ", "Vさせるわけだ"],
    "ほしくないわけではない": ["Aわけではない", "naなわけではない", "Vわけではない", "Vているわけではない", "Vていたわけではない", "Vられるわけではない", "Vさせるわけではない"],
    "するわけがない": ["Aわけがない", "naなわけがない", "Vわけがない", "Vているわけがない", "Vていたわけがない", "Vられるわけがない", "Vさせるわけがない"],
    "休むわけにはいかない": ["Vるわけにはいかない", "Vないわけにはいかない", "Vているわけにはいかない", "Vさせるわけにはいかない"],
    "開けたとたん": ["Vたとたん", "Vたとたんに"],
    "騒いだあげく": ["Vたあげく", "Vたあげくに", "Nのあげく", "Nのあげくに", "Nのあげくの"],
    "悩んだ末": ["Vた末", "Vた末に", "Nの末", "Nの末に", "Nの末の"],
    "来たかと思ったら": ["Vたかと思ったら", "Vたかと思うと"],
    "お忙しいところ": ["Aいところ", "Nのところ", "Vたところ", "Vているところ", "Vていたところ"],
    "検査したところ": ["Vたところ"],
    "仕事どころではない": ["Nどころではない", "Vるどころではない", "Vているどころではない"],
    "夏休みどころか": ["Nどころか", "Vるどころか", "naなどころか", "Aいどころか"],
    "間違いだらけ": ["Nだらけ"],
    "行ったきり": ["Vたきり", "Vたっきり", "Vますきり", "Vますっきり"],
    "立ちっぱなし": ["Vますっぱなし"],
    "予想に反して": ["Nに反して", "Nに反し", "Nに反する"],
    "便利な反面": ["Nである反面", "naな反面", "naである反面", "Aい反面", "Vる反面"],
    "水に強い一方": ["Nである一方", "naな一方", "naである一方", "Aい一方", "Vる一方"],
    "進む一方だ": ["Vる一方だ"],
    "できる上に": ["V上に", "A上に", "naな上に", "naである上に", "Nの上に", "Nである上に"],
    "考えた上で": ["Vた上で", "Vた上の", "Nの上で", "Nの上", "Nの上での"],
    "選ばれた上は": ["V上は"],
    "天気図の上では": ["Nの上では", "Nの上でも", "N上", "N上は", "N上も"],
    "初心者向け": ["N向けだ", "N向けに", "N向けの"],
    "天気次第で": ["N次第だ", "N次第で", "N次第では"],
    "戻り次第": ["Vます次第"],
    "伺った次第です": ["Vる次第です", "Vた次第です", "Vている次第です"],
    "客の意見にこたえて": ["Nにこたえて", "Nにこたえ", "Nにこたえる"],
    "目上の人に対して": ["Nに対して", "Nに対し", "Nに対しては", "Nに対しても", "Nに対する"],
    "法律により": ["Nにより", "Nによる"],
    "事件にかかわって": ["Nにかかわって", "Nにかかわり", "Nにかかわる"],
    "知りながら": ["Nながら", "naながら", "Aいながら", "Vますながら", "Nながらも", "naながらも", "Aいながらも", "Vますながらも"],
    "忙しいと言いつつ": ["Vますつつ", "Vますつつも"],
    "進歩しつつある": ["Vますつつある"],
    "知らないくせして": ["Vくせして", "Aくせして", "naなくせして", "Nのくせして"],
    "すべきではない": ["Vるべきではない", "naであるべきではない", "Aくあるべきではない", "Nであるべきではない"],
    "続けざるをえない": ["Vないざるをえない"],
    "行われることになっている": ["Vることになっている", "Vないことになっている", "Nということになっている"],
    "言い間違いにすぎない": ["Vにすぎない", "Aにすぎない", "naであるにすぎない", "Nにすぎない"],
    "利用にあたり": ["Nにあたって", "Nにあたり", "Nにあたっては", "Nにあたっての", "Vるにあたって", "Vるにあたり", "Vるにあたっては", "Vるにあたっての"],
    "資料に沿って": ["Nに沿って", "Nに沿い", "Nに沿った"],
    "開店に先立ち": ["Nに先立って", "Nに先立ち", "Nに先立つ", "Vるに先立って", "Vるに先立ち", "Vるに先立つ"],
    "広い範囲にわたって": ["Nにわたって", "Nにわたり", "Nにわたる"],
    "覚えられっこない": ["Vますっこない"],
    "言いかねない": ["Vますかねない"],
    "わかりかねる": ["Vますかねる"],
    "嫌われて当然だ": ["Vて当然だ", "Aくて当然だ", "naで当然だ"],
    "怒るのももっともだ": ["Vるのももっともだ", "Aいのももっともだ"],
    "新品も同然だ": ["Vも同然だ", "Nも同然だ"],
    "あるだけましだ": ["Vだけましだ", "Aだけましだ", "naなだけましだ"],
    "一流ホテルだけあって": ["Vだけあって", "Aだけあって", "naなだけあって", "Nだけあって"],
    "成績がいいばかりかスポーツも": ["Vばかりか", "Aばかりか", "naなばかりか", "Nばかりか"],
    "あの飛行機に乗ったばかりに": ["Vばかりに", "Aばかりに", "naなばかりに", "Nであるばかりに"],
    "日本のみならず外国でも": ["Vのみならず", "Aのみならず", "naなのみならず", "Nのみならず"],
    "申し込みに際して": ["Nに際して", "Vるに際して"],
    "計画に基づいて": ["Nに基づいて"],
    "必要に応じて": ["Nに応じて"],
    "青空の下で": ["Nの下で"],
    "信じがたい": ["Vますがたい"],
    "富士山が見えることから": ["Vことから", "Aことから", "naなことから", "Nであることから"],
    "彼のことだから": ["Nのことだから"],
    "休むことなく": ["Vることなく"],
    "やってみないことにはわからない": ["Vないことには〜ない"],
    "飲もうではないか": ["Vようではないか"],
    "言いようがない": ["Vますようがない", "Vますようもない"],
    "泣いているかのようだ": ["Vかのようだ", "Aかのようだ", "naであるかのようだ", "Nであるかのようだ"],
    "行けそうにない": ["Vますそうにない", "Vれるそうもない"],
    "日本に来て以来": ["N以来", "Vて以来"],
    "試験を受ける以上": ["Vる以上", "Vた以上"],
    "約束したからには": ["Vるからには", "Vたからには"],
    "客の立場から言うと": ["Nから言うと", "Nから言えば"],
    "症状からすると": ["Nからすると", "Nからすれば", "Nからいって"],
    "服装からして": ["Nからして"],
    "好きだからといって": ["Vからといって", "Aからといって", "naだからといって", "Nだからといって"],
    "手続きしてからでないと": ["Vてからでないと〜できない", "Vてからでなければ〜できない"],
    "2007年から2009年にかけて": ["Nから〜にかけて"],
    "中止だとか": ["Vとか", "Aとか", "naだとか", "Nだとか"],
    "二度と行くまい": ["Vるまい", "Vますまい"],
    "わかるまい": ["Vるまい", "Vますまい"],
    "話そうか話すまいか": ["Vようか〜まいか", "Vるまいか", "Vますまいか"],
    "勝つに決まっている": ["Vに決まっている", "Aに決まっている", "naに決まっている", "Nに決まっている"],
    "勝つとは限らない": ["Vとは限らない", "Aとは限らない", "naとは限らない", "Nとは限らない"],
    "祈るよりほかない": ["Vるよりほかない"],
    "努力の結果にほかならない": ["Nにほかならない"],
    "現地にて": ["Nにて"],
    "来日の折には": ["Vる折に", "Vた折に", "Nの折に"],
    "外国人から見ると": ["Nから見ると"],
    "足の速さにかけては": ["Nにかけては"],
    "中国をはじめアジアの国々が": ["Nをはじめ", "Nをはじめとして"],
    "憲法改正をめぐって": ["Nをめぐって", "Nをめぐり", "Nをめぐる"],
    "京都において": ["Nにおいて", "Nにおける"],
    "人目もかまわず": ["Nもかまわず", "Vるのもかまわず"],
    "雨にもかかわらず": ["Nにもかかわらず", "Vにもかかわらず", "Aにもかかわらず", "naであるにもかかわらず"],
    "来る来ないにかかわらず": ["Vる〜ないにかかわらず", "Aい〜くないにかかわらず", "Nにかかわりなく"],
    "年齢を問わず": ["Nを問わず"],
    "本やらノートやら": ["Nやら", "Vやら", "Aやら", "naやら"],
    "見るにつけ聞くにつけ": ["Vるにつけ", "Aいにつけ"],
    "行くにしろ行かないにしろ": ["Vにしろ", "Aにしろ", "naにしろ", "Nにしろ", "Vにせよ", "Aにせよ", "naにせよ", "Nにせよ"],
    "勉強もできればスポーツもできる": ["Nも〜ば〜も"],
    "行くものか": ["Vるものか", "Aいものか", "naなものか", "Nなものか"],
    "東京を中心に": ["Nを中心に", "Nを中心にして", "Nを中心とした", "Nを中心として"],
    "感謝の気持ちをこめて": ["Nをこめて"],
    "友人を通じて": ["Nを通じて", "Nを通して"],
    "事実をもとに": ["Nをもとに", "Nをもとにして", "Nをもとにした"],
    "調整中につき": ["Nにつき"],
    "入学をきっかけに": ["Nをきっかけに", "Nをきっかけとして", "Nをきっかけにして", "Vるのをきっかけに", "Vたのをきっかけに"],
    "薬は苦いものだ": ["Aいものだ", "Aくないものだ", "naなものだ", "naじゃないものだ"],
    "するものではない": ["Vるものではない"],
    "無理というものだ": ["Vるというものだ", "Nというものだ"],
    "地図を頼りに": ["Nを頼りに"],
    "倒れたりする恐れがある": ["Vる恐れがある", "Nの恐れがある"],
    "つらいものがある": ["Vるものがある", "Aいものがある"],
    "多ければいいというものでもない": ["Vば〜というものでもない", "Aければ〜というものでもない", "naなら〜というものでもない", "Nなら〜というものでもない"],
    "どうにかならないものか": ["Vないものか", "Vれないものか"],
    "受験の際に": ["Nの際に", "Vる際に", "Vた際に"],
    "高かった。それなのにすぐ壊れた。": ["文。それなのに"],
    "大雨だ。それでも出かける。": ["文。それでも"],
    "渋滞だとか。それなら電車で行こう。": ["文。それなら"],
    "働きすぎた。それで病気になった。": ["文。それで"],
    "それがまだなんです。": ["文。それが"],
    "渋滞するらしい。そこで早く出発したい。": ["文。そこで"],
    "そういえば田中君、元気？": ["文。そういえば"],
    "それはそうと試験はいつだっけ？": ["文。それはそうと"],
    "母の兄、すなわちおじさん": ["文。すなわち"],
    "ファックスあるいはメールで": ["文。あるいは"],
    "貧しい。だが幸せだ。": ["文。だが"],
    "怒ってる。だって約束を破ったから。": ["文。だって"],
    "まだ来ない。ということは欠席だ。": ["文。ということは"],
    "外出できない。というのは父の具合が悪いんです。": ["文。というのは"],
    "彼はまじめだ。したがって信頼されている。": ["文。したがって"],
    "3割引。ただしこの棚の商品を除く。": ["文。ただし"],
    "飲食禁止。もっとも水はかまいません。": ["文。もっとも"],
    "以上です。なお詳細は…": ["文。なお"],
    "終わります。さて来週は…": ["文。さて"],
    "薬を塗った。すると痛みが治まった。": ["文。すると"],
    "大敗した。要するに力の差があった。": ["文。要するに"],
    "美人だ。しかも性格もいい。": ["文。しかも"],
    "高いし、まずい。おまけにサービスも…": ["文。おまけに"],
    "一般に…。ちなみにうちにも…": ["文。ちなみに"],
}


def compact(text: str) -> str:
    text = re.sub(r"<!--.*?-->", "", text)
    text = re.sub(r"[\s　#>*`♡]", "", text)
    return text.replace("～", "〜").replace("~", "〜")


def source_lines(markdown: str) -> list[str]:
    body = markdown.split("<!-- box -->", 1)[0]
    body = re.split(r"^\s*#{0,2}\s*練習[ⅠI1]", body, maxsplit=1, flags=re.MULTILINE)[0]
    lines: list[str] = []
    for raw in body.splitlines():
        ruby = re.fullmatch(r"\s*<!--\s*ruby:\s*(.*?)\s*-->\s*", raw)
        if ruby:
            lines.append(ruby.group(1).strip())
            continue
        text, _hints = clean_line(re.sub(r"^\s*#+\s*", "", raw))
        # Some pages prepend more than eight space-separated furigana fragments to a
        # translation. The generic cleaner intentionally caps that heuristic; this
        # known scan can use the stronger rule because the source layout was reviewed.
        text = re.sub(r"^(?:[ぁ-ヿ]{1,12}[ 　]+){1,24}(?=[A-Za-z一-鿿가-힯])", "", text)
        if not text:
            continue
        # The whole-page pass sometimes joins the Chinese and Korean translations on
        # one physical line. Split at the first Hangul character so the normal language
        # classifier can attach both fields to the same example.
        hangul = re.search(r"[가-힯ᄀ-ᇿ]", text)
        if hangul and re.search(r"[一-鿿]", text[: hangul.start()]):
            chinese, korean = text[: hangul.start()].strip(), text[hangul.start() :].strip()
            if chinese:
                lines.append(chinese)
            if korean:
                lines.append(korean)
        else:
            lines.append(text)
    return lines


def similarity(target: str, line: str) -> float:
    left, right = compact(target), compact(line)
    if not left or not right:
        return 0.0
    if left == right:
        return 2.0
    if left in right:
        return 1.5 - min(0.45, (len(right) - len(left)) / max(len(left), 1) / 4)
    if right in left and len(right) >= 4:
        return 1.25 - min(0.35, (len(left) - len(right)) / max(len(left), 1) / 4)
    return difflib.SequenceMatcher(None, left, right).ratio()


def locate_titles(lines: list[str], targets: list[str]) -> list[int]:
    """Choose an increasing best-match line for each weekly-index entry."""
    positions: list[int] = []
    floor = 0
    for offset, target in enumerate(targets):
        ceiling = len(lines) - (len(targets) - offset - 1)
        ranked = sorted(
            ((similarity(target, line), index) for index, line in enumerate(lines[floor:ceiling], floor)),
            reverse=True,
        )
        # A handful of grey title bands vanished completely while their inflected
        # example survived (for example 資料に沿って → ご希望に沿った). The page and
        # monotonic order are already fixed by the printed weekly ledger, so a modest
        # fuzzy floor is safe here and still catches a wholly wrong page mapping.
        if not ranked or ranked[0][0] < 0.20:
            raise RuntimeError(f"Could not locate {target!r}; best match was {ranked[:1]!r}")
        position = ranked[0][1]
        positions.append(position)
        floor = position + 1
    return positions


def connection_tokens(lines: list[str]) -> list[str]:
    tokens: list[str] = []
    for line in lines:
        candidate = re.sub(r"^\s*[①②③④⑤⑥⑦⑧⑨]\s*", "", line).strip()
        try:
            parse_connection_line(candidate)
        except Exception:
            continue
        if candidate not in tokens:
            tokens.append(candidate)
    return tokens


_CONNECTION_OCR_CORRECTIONS = {
    # The scan represents deletion with a horizontal rule through the inflection.
    # Whole-page OCR mistakes that rule for a kana (or keeps the deleted kana), while
    # the crop makes the intended stem form unambiguous.
    "Aあげ": "Aげ",
    "naあげ": "naげ",
    "Vたあげ": "Vたげ",
    "Vまっぽい": "Vますっぽい",
    "Vまっっぽい": "Vますっぽい",
    "Vまっかねない": "Vますかねない",
    "Vまっっこない": "Vますっこない",
    "Vまっかねる": "Vますかねる",
    "naだな": "naな",
    "Nだな": "Nな",
    "Nだである": "Nである",
}


def corrected_connection_tokens(tokens: list[str]) -> list[str]:
    corrected: list[str] = []
    for line in tokens:
        parts = [part.strip() for part in re.split(r"[／/]", line) if part.strip()]
        fixed = "／".join(_CONNECTION_OCR_CORRECTIONS.get(part, part) for part in parts)
        if fixed not in corrected:
            corrected.append(fixed)
    return corrected


def _merge_box_groups(groups: list[dict[str, Any]]) -> dict[str, Any]:
    merged: dict[str, Any] = {"connectionRaw": [], "gloss": {}, "notes": []}
    for group in groups:
        for token in group.get("connectionRaw") or []:
            if token not in merged["connectionRaw"]:
                merged["connectionRaw"].append(token)
        for language, value in (group.get("gloss") or {}).items():
            merged["gloss"].setdefault(language, value)
        for note in group.get("notes") or []:
            if note not in merged["notes"]:
                merged["notes"].append(note)
    return merged


def pair_box_groups(page_titles: list[str], box: str) -> list[dict[str, Any] | None]:
    """Return only box bindings that cannot shift onto a neighbouring entry.

    A single-entry exercise page may contain several blank-separated fragments from
    the same printed frame, so those fragments are safe to merge.  Multi-entry pages
    are positional only when the independent frame and entry counts agree.  Anything
    else stays unbound and therefore keeps a review flag.
    """
    groups = _split_box_groups(box)
    if len(groups) == len(page_titles):
        return list(groups)
    if len(page_titles) == 1 and groups:
        return [_merge_box_groups(groups)]
    return [None for _title in page_titles]


def build_entry(
    page: int,
    number: int,
    headword: str,
    segment: list[str],
    box_group: dict[str, Any] | None = None,
) -> dict[str, Any]:
    block = _build_entry_block(page, number, [headword, *segment])
    assert block is not None
    block["headword"] = headword
    block["sourceAnchor"] = f"pdf:{page}:index:{number}"
    block["connectionRaw"] = corrected_connection_tokens(connection_tokens(segment))
    block["connectionSource"] = "body" if block["connectionRaw"] else "weekly-index-inference"
    if box_group:
        # ``document.json`` keeps the floating 接続 frame in a second OCR channel.
        # The weekly-index repair used to throw that channel away and consequently
        # labelled perfectly readable frames (for example Nがち / Vますがち) as an
        # inferred 普通形.  Only bind by position when the number of recognised frames
        # equals the independently known number of entries on the page; a mismatch is
        # left visible for review instead of silently shifting every following frame.
        if box_group.get("connectionRaw"):
            block["connectionRaw"] = corrected_connection_tokens(list(box_group["connectionRaw"]))
            block["connectionSource"] = "box"
        for language, text in (box_group.get("gloss") or {}).items():
            block["gloss"].setdefault(language, text)
        for note in box_group.get("notes") or []:
            if note not in block["notes"]:
                block["notes"].append(note)
    if headword in REVIEWED_CONNECTIONS:
        block["connectionRaw"] = list(REVIEWED_CONNECTIONS[headword])
        block["connectionSource"] = "crop-review"
    if not block["connectionRaw"]:
        # Discourse connectors in week 8 combine complete clauses; for other complex
        # patterns this conservative fallback records the ordinary-form attachment and
        # leaves a visible warning for later line-by-line connection review.
        block["connectionRaw"] = ["普"]
        block.setdefault("flags", []).append(
            {
                "severity": "warning",
                "code": "repair.connection_inferred",
                "message": "接続框未被 OCR 稳定读取；暂按普通形装配，待逐字复核。",
            }
        )
    if not block.get("examples") or not any(example.get("zh") for example in block["examples"]):
        if headword in GLOSS_ZH:
            block.setdefault("gloss", {})["zh"] = GLOSS_ZH[headword]
        block.setdefault("flags", []).append(
            {
                "severity": "warning",
                "code": "repair.example_review_required",
                "message": "该条目的例句/中文未能从 OCR 稳定配对，需要人工复核。",
            }
        )
    return block


def lesson_title(page: dict[str, Any], fallback: str) -> str:
    header = _find_unit_header(str(page.get("markdown") or ""))
    return str((header or {}).get("title") or fallback)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--document", type=Path, required=True)
    parser.add_argument("--pack", type=Path, required=True)
    args = parser.parse_args()

    document = json.loads(args.document.read_text(encoding="utf-8"))
    source = {int(page["page"]): page for page in document["pages"]}
    repaired: dict[int, dict[str, Any]] = {
        number: {
            "page": number,
            "unitHeader": None,
            "blocks": [
                {
                    "id": f"p{number:04d}-b1",
                    "sourceAnchor": f"pdf:{number}:block:1",
                    "type": "front-matter",
                }
            ],
            "issues": [],
        }
        for number in range(1, 158)
    }

    unit_rows: list[str] = []
    total = 0
    for week, day in sorted(HEADWORDS):
        titles = HEADWORDS[(week, day)]
        first_page = WEEK_START[week] + (day - 1) * 2
        title = lesson_title(source[first_page], titles[0])
        unit_rows.append(f"第{week}週 {day}日目 {title} {len(titles)}")

        # Normal lessons print three title bands on the left page and one on the
        # exercise page. Week 3 day 5 is the book's sole three-entry lesson (2 + 1).
        split = 2 if len(titles) == 3 else min(3, len(titles))
        for page_number, page_titles in ((first_page, titles[:split]), (first_page + 1, titles[split:])):
            lines = source_lines(str(source[page_number].get("markdown") or ""))
            positions = locate_titles(lines, page_titles) if page_titles else []
            paired_boxes = pair_box_groups(page_titles, str(source[page_number].get("box") or ""))
            blocks: list[dict[str, Any]] = []
            if page_number == first_page:
                blocks.append(
                    {
                        "id": f"p{page_number:04d}-b1",
                        "sourceAnchor": f"pdf:{page_number}:block:1",
                        "type": "unit-header",
                        "week": week,
                        "day": day,
                        "title": title,
                    }
                )
            for index, (headword, position) in enumerate(zip(page_titles, positions), start=1):
                end = positions[index] if index < len(positions) else len(lines)
                block_number = len(blocks) + 1
                box_group = paired_boxes[index - 1]
                blocks.append(
                    build_entry(
                        page_number,
                        block_number,
                        headword,
                        lines[position + 1 : end],
                        box_group,
                    )
                )
                total += 1
            repaired[page_number] = {
                "page": page_number,
                "unitHeader": {"week": week, "day": day, "title": title},
                "blocks": blocks,
                "issues": [],
            }

    # The six weekly practice tests are deliberately represented but never imported as
    # lexicon entries. Their three-page spans sit between lesson blocks.
    for week, start in ((1, 30), (2, 46), (3, 62), (4, 78), (5, 94), (6, 110), (7, 126)):
        for page_number in range(start, start + 3):
            repaired[page_number] = {
                "page": page_number,
                "unitHeader": {"week": week, "day": 7, "title": "実戦問題"},
                "blocks": [
                    {
                        "id": f"p{page_number:04d}-b1",
                        "sourceAnchor": f"pdf:{page_number}:block:1",
                        "type": "exercise",
                    }
                ],
                "issues": [],
            }

    pages_dir = args.pack / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    for page_number, page in repaired.items():
        (pages_dir / f"p{page_number:04d}.json").write_text(
            json.dumps(page, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    units_header = (
        "# units.txt — 依据教材每周「今週の表現」独立清单复核。\n"
        "# 格式：第N週 M日目 <单元标题> <该单元条目数>\n"
        "# 7日目为実戦問題，不进入词汇语法包。\n\n"
    )
    args.pack.joinpath("units.txt").write_text(
        units_header + "\n".join(unit_rows) + "\n", encoding="utf-8"
    )
    print(f"Reconciled {total} entries across {len(HEADWORDS)} units and 157 page records.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
