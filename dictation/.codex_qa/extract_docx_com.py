import argparse
import json
from pathlib import Path

import pythoncom
import win32com.client


def clean(text: str) -> str:
    return text.replace("\r", "").replace("\x07", "").strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("output")
    args = parser.parse_args()

    input_path = str(Path(args.input).resolve())
    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    pythoncom.CoInitialize()
    word = win32com.client.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0
    doc = None
    try:
        doc = word.Documents.Open(
            input_path,
            ReadOnly=True,
            AddToRecentFiles=False,
            ConfirmConversions=False,
        )
        paragraphs = []
        for idx in range(1, doc.Paragraphs.Count + 1):
            paragraph = doc.Paragraphs(idx)
            text = clean(paragraph.Range.Text)
            if not text:
                continue
            try:
                style = str(paragraph.Range.Style)
            except Exception:
                style = ""
            try:
                page = int(paragraph.Range.Information(3))  # wdActiveEndPageNumber
            except Exception:
                page = None
            paragraphs.append(
                {
                    "index": idx,
                    "page": page,
                    "style": style,
                    "text": text,
                }
            )

        tables = []
        for table_idx in range(1, doc.Tables.Count + 1):
            table = doc.Tables(table_idx)
            rows = []
            for row_idx in range(1, table.Rows.Count + 1):
                row = table.Rows(row_idx)
                rows.append([clean(row.Cells(cell_idx).Range.Text) for cell_idx in range(1, row.Cells.Count + 1)])
            try:
                page = int(table.Range.Information(3))
            except Exception:
                page = None
            tables.append({"index": table_idx, "page": page, "rows": rows})

        payload = {
            "path": input_path,
            "title": str(doc.BuiltInDocumentProperties("Title")),
            "author": str(doc.BuiltInDocumentProperties("Author")),
            "pages": int(doc.ComputeStatistics(2)),  # wdStatisticPages
            "paragraphs": paragraphs,
            "tables": tables,
        }
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    finally:
        if doc is not None:
            doc.Close(False)
        word.Quit()
        pythoncom.CoUninitialize()


if __name__ == "__main__":
    main()
