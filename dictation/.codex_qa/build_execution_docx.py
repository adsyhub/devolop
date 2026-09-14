import argparse
import math
import shutil
import subprocess
import tempfile
from pathlib import Path

import pythoncom
import win32com.client


WD_ALIGN_LEFT = 0
WD_ALIGN_CENTER = 1
WD_ALIGN_RIGHT = 2
WD_ALIGN_JUSTIFY = 3
WD_BREAK_PAGE = 7
WD_COLLAPSE_END = 0
WD_COLOR_AUTOMATIC = -16777216
WD_EXPORT_FORMAT_PDF = 17
WD_EXPORT_FORMAT_XPS = 18
WD_FIELD_PAGE = 33
WD_HEADER_FOOTER_PRIMARY = 1
WD_HEADER_FOOTER_FIRST_PAGE = 2
WD_LINE_SPACE_SINGLE = 0
WD_LINE_SPACE_MULTIPLE = 5
WD_ORIENT_PORTRAIT = 0
WD_OUTLINE_LEVEL_BODY_TEXT = 10
WD_PAPER_LETTER = 2
WD_PREFERRED_WIDTH_POINTS = 3
WD_ROW_HEIGHT_AUTO = 0
WD_STYLE_NORMAL = -1
WD_STYLE_HEADING_1 = -2
WD_STYLE_HEADING_2 = -3
WD_STYLE_HEADING_3 = -4
WD_STYLE_HEADING_4 = -5
WD_STYLE_TITLE = -63
WD_STYLE_SUBTITLE = -75
WD_VERTICAL_ALIGNMENT_CENTER = 1


def rgb(hex_value: str) -> int:
    value = hex_value.lstrip("#")
    red, green, blue = (int(value[index : index + 2], 16) for index in (0, 2, 4))
    return red + green * 256 + blue * 65536


def set_font(font, *, name="Calibri", east_asia="Microsoft YaHei", size=None, color=None, bold=None):
    font.Name = name
    try:
        font.NameAscii = name
        font.NameOther = name
        font.NameFarEast = east_asia
    except Exception:
        pass
    if size is not None:
        font.Size = size
    if color is not None:
        font.Color = rgb(color)
    if bold is not None:
        font.Bold = -1 if bold else 0


def clean_text(value: str) -> str:
    return str(value or "").replace("\r", "").replace("\x07", "").strip()


def paragraph_text(paragraph) -> str:
    return clean_text(paragraph.Range.Text)


def style_name(document, built_in_id: int) -> str:
    return str(document.Styles(built_in_id).NameLocal)


def configure_styles(document) -> None:
    normal = document.Styles(WD_STYLE_NORMAL)
    set_font(normal.Font, size=11, color="#1F2933")
    normal.ParagraphFormat.Alignment = WD_ALIGN_LEFT
    normal.ParagraphFormat.SpaceBefore = 0
    normal.ParagraphFormat.SpaceAfter = 6
    normal.ParagraphFormat.LineSpacingRule = WD_LINE_SPACE_MULTIPLE
    normal.ParagraphFormat.LineSpacing = 13.75
    normal.ParagraphFormat.WidowControl = -1

    heading_tokens = {
        WD_STYLE_HEADING_1: (16, "#2E74B5", 18, 10),
        WD_STYLE_HEADING_2: (13, "#2E74B5", 14, 7),
        WD_STYLE_HEADING_3: (12, "#1F4D78", 10, 5),
    }
    for style_id, (size, color, before, after) in heading_tokens.items():
        style = document.Styles(style_id)
        set_font(style.Font, size=size, color=color, bold=True)
        style.ParagraphFormat.Alignment = WD_ALIGN_LEFT
        style.ParagraphFormat.SpaceBefore = before
        style.ParagraphFormat.SpaceAfter = after
        style.ParagraphFormat.LineSpacingRule = WD_LINE_SPACE_SINGLE
        style.ParagraphFormat.KeepWithNext = -1
        style.ParagraphFormat.KeepTogether = -1
        style.ParagraphFormat.WidowControl = -1

    title = document.Styles(WD_STYLE_TITLE)
    set_font(title.Font, size=28, color="#0B2545", bold=True)
    title.ParagraphFormat.Alignment = WD_ALIGN_CENTER
    title.ParagraphFormat.SpaceBefore = 96
    title.ParagraphFormat.SpaceAfter = 16
    title.ParagraphFormat.LineSpacingRule = WD_LINE_SPACE_SINGLE

    subtitle = document.Styles(WD_STYLE_SUBTITLE)
    set_font(subtitle.Font, size=13, color="#1F4D78", bold=False)
    subtitle.ParagraphFormat.Alignment = WD_ALIGN_CENTER
    subtitle.ParagraphFormat.SpaceBefore = 0
    subtitle.ParagraphFormat.SpaceAfter = 20
    subtitle.ParagraphFormat.LineSpacingRule = WD_LINE_SPACE_SINGLE


def shift_heading_levels(document, title_text: str) -> None:
    names = {
        1: style_name(document, WD_STYLE_HEADING_1),
        2: style_name(document, WD_STYLE_HEADING_2),
        3: style_name(document, WD_STYLE_HEADING_3),
        4: style_name(document, WD_STYLE_HEADING_4),
    }
    paragraphs = [document.Paragraphs(index) for index in range(1, document.Paragraphs.Count + 1)]
    for paragraph in paragraphs:
        text = paragraph_text(paragraph)
        if text == title_text:
            paragraph.Style = document.Styles(WD_STYLE_TITLE)
            continue
        current_name = str(paragraph.Range.Style.NameLocal)
        if current_name == names[4]:
            paragraph.Style = document.Styles(WD_STYLE_HEADING_3)
        elif current_name == names[3]:
            paragraph.Style = document.Styles(WD_STYLE_HEADING_2)
        elif current_name == names[2]:
            paragraph.Style = document.Styles(WD_STYLE_HEADING_1)


def style_cover(document, title_text: str) -> None:
    metadata_prefixes = (
        "版本：",
        "日期：",
        "适用读者：",
        "分析输入：",
        "明确排除：",
    )
    for index in range(1, document.Paragraphs.Count + 1):
        paragraph = document.Paragraphs(index)
        text = paragraph_text(paragraph)
        if text == title_text:
            paragraph.Style = document.Styles(WD_STYLE_TITLE)
        elif text.startswith("副标题："):
            paragraph.Style = document.Styles(WD_STYLE_SUBTITLE)
        elif text.startswith(metadata_prefixes):
            paragraph.Alignment = WD_ALIGN_CENTER
            paragraph.Format.SpaceBefore = 0
            paragraph.Format.SpaceAfter = 5
            paragraph.Format.LineSpacingRule = WD_LINE_SPACE_SINGLE
            set_font(paragraph.Range.Font, size=10, color="#5E6C7B", bold=False)


def configure_lists(document) -> None:
    for index in range(1, document.Paragraphs.Count + 1):
        paragraph = document.Paragraphs(index)
        try:
            list_type = int(paragraph.Range.ListFormat.ListType)
        except Exception:
            list_type = 0
        if list_type == 0:
            continue
        paragraph.Format.LeftIndent = 27
        paragraph.Format.FirstLineIndent = -13.5
        paragraph.Format.SpaceBefore = 0
        paragraph.Format.SpaceAfter = 4
        paragraph.Format.LineSpacingRule = WD_LINE_SPACE_MULTIPLE
        paragraph.Format.LineSpacing = 13.75
        paragraph.Format.WidowControl = -1


def column_widths(table, total_width: float) -> list[float]:
    count = table.Columns.Count
    if count <= 0:
        return []
    weights = []
    compact_headers = {"ID", "级别", "优先级", "估算", "决策", "阶段", "证据", "主责"}
    for column_index in range(1, count + 1):
        lengths = []
        for row_index in range(1, min(table.Rows.Count, 30) + 1):
            try:
                lengths.append(len(clean_text(table.Cell(row_index, column_index).Range.Text)))
            except Exception:
                pass
        maximum = max(lengths, default=8)
        header = ""
        try:
            header = clean_text(table.Cell(1, column_index).Range.Text)
        except Exception:
            pass
        weight = max(2.2, math.sqrt(min(maximum, 120)))
        if header in compact_headers:
            weight = min(weight, 3.0)
        weights.append(weight)
    minimum = 36 if count >= 5 else 42 if count == 4 else 54 if count == 3 else 84
    available = max(0, total_width - minimum * count)
    weight_total = sum(weights)
    widths = [minimum + available * weight / weight_total for weight in weights]
    correction = total_width - sum(widths)
    widths[-1] += correction
    return widths


def configure_tables(document) -> None:
    # 6.5-inch text block minus the prescribed 6-point table indent.
    content_width = 462.0
    border_color = rgb("#C9D4E1")
    header_fill = rgb("#E8EEF5")
    for table_index in range(1, document.Tables.Count + 1):
        table = document.Tables(table_index)
        table.AllowAutoFit = False
        table.PreferredWidthType = WD_PREFERRED_WIDTH_POINTS
        table.PreferredWidth = content_width
        table.LeftPadding = 6
        table.RightPadding = 6
        table.TopPadding = 4
        table.BottomPadding = 4
        try:
            table.Rows.LeftIndent = 6
        except Exception:
            pass
        try:
            table.Rows.AllowBreakAcrossPages = -1
            table.Rows.HeightRule = WD_ROW_HEIGHT_AUTO
            table.Rows(1).HeadingFormat = -1
        except Exception:
            pass

        widths = column_widths(table, content_width)
        for column_index, width in enumerate(widths, start=1):
            try:
                table.Columns(column_index).SetWidth(width, 0)
            except Exception:
                try:
                    table.Columns(column_index).Width = width
                except Exception:
                    pass

        for border_index in range(-6, -1):
            try:
                border = table.Borders(border_index)
                border.LineStyle = 1
                border.LineWidth = 4
                border.Color = border_color
            except Exception:
                pass

        for row_index in range(1, table.Rows.Count + 1):
            row = table.Rows(row_index)
            for cell_index in range(1, row.Cells.Count + 1):
                cell = row.Cells(cell_index)
                cell.VerticalAlignment = WD_VERTICAL_ALIGNMENT_CENTER
                if row_index == 1:
                    cell.Shading.BackgroundPatternColor = header_fill
                for paragraph_index in range(1, cell.Range.Paragraphs.Count + 1):
                    paragraph = cell.Range.Paragraphs(paragraph_index)
                    paragraph.Format.SpaceBefore = 0
                    paragraph.Format.SpaceAfter = 2
                    paragraph.Format.LineSpacingRule = WD_LINE_SPACE_SINGLE
                    paragraph.Format.WidowControl = -1
                    set_font(
                        paragraph.Range.Font,
                        size=9.2,
                        color="#1F2933",
                        bold=(row_index == 1),
                    )


def configure_page_breaks(document) -> None:
    major_starts = (
        "6. Phase 0",
        "7. Phase 1",
        "8. Phase 2",
        "9. Phase 3",
        "10. Phase 4",
        "12. 可执行 Backlog",
        "15. 前 10 个工作日",
        "17. 证据索引",
        "18. 最终建议",
    )
    for index in range(1, document.Paragraphs.Count + 1):
        paragraph = document.Paragraphs(index)
        text = paragraph_text(paragraph)
        paragraph.Format.WidowControl = -1
        if text.startswith(major_starts):
            paragraph.Format.PageBreakBefore = -1


def insert_toc(document) -> None:
    marker = None
    for index in range(1, document.Paragraphs.Count + 1):
        paragraph = document.Paragraphs(index)
        if paragraph_text(paragraph) == "[[TOC]]":
            marker = paragraph
            break
    if marker is None:
        return

    start = marker.Range.Start
    marker.Range.Text = "目录\r"
    heading = document.Range(start, start + len("目录")).Paragraphs(1)
    heading.Range.ParagraphFormat.PageBreakBefore = -1
    heading.Range.ParagraphFormat.OutlineLevel = WD_OUTLINE_LEVEL_BODY_TEXT
    heading.Range.ParagraphFormat.SpaceBefore = 0
    heading.Range.ParagraphFormat.SpaceAfter = 14
    set_font(heading.Range.Font, size=20, color="#0B2545", bold=True)

    toc_range = document.Range(start + len("目录") + 1, start + len("目录") + 1)
    toc = document.TablesOfContents.Add(
        Range=toc_range,
        UseHeadingStyles=True,
        UpperHeadingLevel=1,
        LowerHeadingLevel=3,
        IncludePageNumbers=True,
        RightAlignPageNumbers=True,
        UseHyperlinks=True,
    )
    after = document.Range(toc.Range.End, toc.Range.End)
    after.InsertBreak(WD_BREAK_PAGE)


def configure_header_footer(document) -> None:
    for section_index in range(1, document.Sections.Count + 1):
        section = document.Sections(section_index)
        page_setup = section.PageSetup
        page_setup.PaperSize = WD_PAPER_LETTER
        page_setup.Orientation = WD_ORIENT_PORTRAIT
        page_setup.TopMargin = 72
        page_setup.BottomMargin = 72
        page_setup.LeftMargin = 72
        page_setup.RightMargin = 72
        page_setup.HeaderDistance = 35.424
        page_setup.FooterDistance = 35.424
        page_setup.DifferentFirstPageHeaderFooter = -1

        header = section.Headers(WD_HEADER_FOOTER_PRIMARY)
        header.Range.Text = "Miraa 技术规格吸收分析与执行方案\tv1.0 · 2026-08-19"
        header.Range.ParagraphFormat.Alignment = WD_ALIGN_LEFT
        header.Range.ParagraphFormat.TabStops.ClearAll()
        header.Range.ParagraphFormat.TabStops.Add(468, 2)
        header.Range.ParagraphFormat.SpaceAfter = 0
        set_font(header.Range.Font, size=8.5, color="#6B7785", bold=False)

        first_header = section.Headers(WD_HEADER_FOOTER_FIRST_PAGE)
        first_header.Range.Text = ""

        footer = section.Footers(WD_HEADER_FOOTER_PRIMARY)
        footer.Range.Text = "执行参考  ·  第 "
        footer.Range.ParagraphFormat.Alignment = WD_ALIGN_RIGHT
        footer.Range.ParagraphFormat.SpaceBefore = 0
        footer.Range.ParagraphFormat.SpaceAfter = 0
        set_font(footer.Range.Font, size=8.5, color="#6B7785", bold=False)
        field_range = footer.Range.Duplicate
        field_range.Collapse(WD_COLLAPSE_END)
        footer.Range.Fields.Add(field_range, WD_FIELD_PAGE)
        end_range = footer.Range.Duplicate
        end_range.Collapse(WD_COLLAPSE_END)
        end_range.InsertAfter(" 页")

        first_footer = section.Footers(WD_HEADER_FOOTER_FIRST_PAGE)
        first_footer.Range.Text = ""


def postprocess(base_docx: Path, output_docx: Path, xps_path: Path | None, pdf_path: Path | None) -> None:
    title_text = "Miraa 技术规格可吸收能力分析与现有项目改进执行方案"
    pythoncom.CoInitialize()
    word = win32com.client.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0
    document = None
    try:
        document = word.Documents.Open(str(base_docx.resolve()), ReadOnly=False, AddToRecentFiles=False)
        document.BuiltInDocumentProperties("Title").Value = title_text
        document.BuiltInDocumentProperties("Subject").Value = "dictation 项目非商业能力吸收与执行路线"
        document.BuiltInDocumentProperties("Author").Value = "OpenAI Codex"
        document.BuiltInDocumentProperties("Keywords").Value = "Miraa, dictation, 字幕, Echo, 本地优先, 执行方案"

        configure_header_footer(document)
        shift_heading_levels(document, title_text)
        configure_styles(document)
        style_cover(document, title_text)
        configure_lists(document)
        configure_tables(document)
        configure_page_breaks(document)
        insert_toc(document)
        for toc_index in range(1, document.TablesOfContents.Count + 1):
            document.TablesOfContents(toc_index).Update()
        document.Fields.Update()
        document.Repaginate()

        output_docx.parent.mkdir(parents=True, exist_ok=True)
        document.SaveAs2(str(output_docx.resolve()), FileFormat=16)
        if xps_path is not None:
            xps_path.parent.mkdir(parents=True, exist_ok=True)
            document.ExportAsFixedFormat(str(xps_path.resolve()), WD_EXPORT_FORMAT_XPS)
        if pdf_path is not None:
            pdf_path.parent.mkdir(parents=True, exist_ok=True)
            document.ExportAsFixedFormat(str(pdf_path.resolve()), WD_EXPORT_FORMAT_PDF)
    finally:
        if document is not None:
            document.Close(False)
        word.Quit()
        pythoncom.CoUninitialize()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("markdown")
    parser.add_argument("output")
    parser.add_argument("--xps")
    parser.add_argument("--pdf")
    args = parser.parse_args()

    markdown = Path(args.markdown).resolve()
    output = Path(args.output).resolve()
    pandoc = shutil.which("pandoc")
    if not pandoc:
        raise SystemExit("pandoc not found")

    with tempfile.TemporaryDirectory(prefix="dictation-docx-") as temp_dir:
        base_docx = Path(temp_dir) / "base.docx"
        subprocess.run(
            [
                pandoc,
                str(markdown),
                "--from=gfm",
                "--to=docx",
                "--output",
                str(base_docx),
            ],
            check=True,
        )
        postprocess(
            base_docx,
            output,
            Path(args.xps).resolve() if args.xps else None,
            Path(args.pdf).resolve() if args.pdf else None,
        )


if __name__ == "__main__":
    main()
