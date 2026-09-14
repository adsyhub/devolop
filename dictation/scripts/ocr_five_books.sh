#!/usr/bin/env bash
# OCR the five JLPT reference books in sequence, one GPU at a time.
#
# Safe to re-run at any point: pdf_ocr caches every finished page under
# out/<slug>/pages/, so a second run skips what is already done and only
# transcribes the gap. That is the intended recovery path if this is
# interrupted -- just run the script again.
#
# The `boxes` second pass is deliberately NOT run here. It exists for the
# floated grammar-connection panels of the N2 対策 book; in these five the boxed
# content IS the body text, so a box pass would only add over-capture noise.

set -u
cd "$(dirname "$0")/.." || exit 1
PY=.venv-ocr/Scripts/python.exe
export PYTHONIOENCODING=utf-8

run_book() {
    local slug="$1" pdf="$2"
    echo ""
    echo "=============================================================="
    echo "  $slug  <-  $pdf"
    echo "  started $(date '+%F %T')"
    echo "=============================================================="
    (cd src && "../$PY" -m pdf_ocr run "../dist/$pdf" -o "../out/$slug" \
        --prompt doc-no-ruby --mark-ruby-lines) 2>&1 \
        | grep -vE "Loading checkpoint|image processor|generation flags"
    echo "  finished $slug at $(date '+%F %T')"
}

run_book N1-kanji   "N1级汉字.pdf"
run_book N1-vocab   "N1级词汇.pdf"
run_book N1-grammar "N1级语法.pdf"
run_book N2-kanji   "新完全掌握日语能力考试N2级汉字.pdf"
run_book N2-vocab   "新完全掌握日语能力考试N2级词汇.pdf"

echo ""
echo "ALL FIVE BOOKS DONE at $(date '+%F %T')"
