#!/bin/bash
# One N2 listening course through the manual-enrichment pipeline.
#   scripts/n2_course.sh <slug>          -> write batches + prompts, list what is unanswered
#   scripts/n2_course.sh <slug> install  -> merge replies, build the ZIP, install into courses/
# --no-normalize is deliberate: the opencc pass rewrites the Japanese kanji quoted
# inside hand-written explanations (開ける -> 开ける), and the replies are already
# Simplified Chinese, so there is nothing for it to convert.
set -u
slug="$1"; action="${2:-batches}"
year=${slug%%-*}; rest=${slug#*-}; month=${rest%%-*}
mnum=$((10#$month))
audio="dist/N2 听力音频 2010-2021/${year}年${mnum}月N2.mp3"
wd="n2-jingting-work/$slug"
[ -f "$audio" ] || { echo "missing audio: $audio"; exit 1; }

PYTHONIOENCODING=utf-8 python -u src/build_course.py \
  --audio "$audio" --title "JLPT N2 听力 ${year}年${mnum}月" --language ja \
  --kind manual --handoff-dir "$wd/handoff" --batch-size 25 \
  --work-dir "$wd" --out "$wd/course.zip" --force --resume --no-normalize \
  2>&1 | grep -vE "^\[[0-9]+/[0-9]+\] (generating|reuse)"
rc=${PIPESTATUS[0]}

if [ "$action" = "install" ]; then
  [ $rc -eq 0 ] || { echo "build failed ($rc); not installing"; exit $rc; }
  PYTHONIOENCODING=utf-8 python src/install_course.py "$wd/course.zip" --name "$slug"
fi
