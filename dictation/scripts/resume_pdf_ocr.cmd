@echo off
REM Resume the N2 grammar book OCR.
REM
REM Safe to run at any time and any number of times: src/pdf_ocr caches every
REM finished page to out\N2-grammar\pages\page-NNNN.json, so this skips whatever
REM is already done and only transcribes what is missing. If the book is already
REM complete it just rewrites document.md / document.json and exits.
REM
REM Registered as scheduled task "ResumePdfOcrN2" (see docs/PDF_OCR.md).
REM Remove it with:  schtasks /delete /tn ResumePdfOcrN2 /f

setlocal
set ROOT=C:\Users\cribug\OneDrive\Desktop\dictation
set PY=%ROOT%\.venv-ocr\Scripts\python.exe
set PDF=%ROOT%\dist\N2语法  新日语能力考试考前对策_12684449.pdf
set OUT=%ROOT%\out\N2-grammar

set PYTHONIOENCODING=utf-8
cd /d "%ROOT%\src"

echo [%date% %time%] resuming pdf_ocr >> "%OUT%\resume.log"
"%PY%" -m pdf_ocr run "%PDF%" -o "%OUT%" --prompt doc-no-ruby --max-pixels 3211264 --batch-size 1 --mark-ruby-lines >> "%OUT%\resume.log" 2>&1
echo [%date% %time%] exit %ERRORLEVEL% >> "%OUT%\resume.log"
endlocal
