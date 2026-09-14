import argparse
import json
import zipfile
from pathlib import Path

from lxml import etree


W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
CP = "http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
DC = "http://purl.org/dc/elements/1.1/"
EP = "http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
NS = {"w": W, "cp": CP, "dc": DC, "ep": EP}


def qn(name: str) -> str:
    prefix, local = name.split(":", 1)
    return f"{{{NS[prefix]}}}{local}"


def text_of(element) -> str:
    pieces = []
    for node in element.iter():
        if node.tag == qn("w:t"):
            pieces.append(node.text or "")
        elif node.tag == qn("w:tab"):
            pieces.append("\t")
        elif node.tag == qn("w:br"):
            pieces.append("\n")
    return "".join(pieces).replace("\xa0", " ").strip()


def read_xml(package: zipfile.ZipFile, name: str):
    try:
        return etree.fromstring(package.read(name))
    except KeyError:
        return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("output")
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(input_path) as package:
        document = read_xml(package, "word/document.xml")
        styles_xml = read_xml(package, "word/styles.xml")
        core = read_xml(package, "docProps/core.xml")
        app = read_xml(package, "docProps/app.xml")

        styles = {}
        if styles_xml is not None:
            for style in styles_xml.xpath("//w:style", namespaces=NS):
                style_id = style.get(qn("w:styleId"), "")
                name_nodes = style.xpath("./w:name/@w:val", namespaces=NS)
                styles[style_id] = name_nodes[0] if name_nodes else style_id

        body = document.find("w:body", NS)
        blocks = []
        paragraphs = []
        tables = []
        page = 1
        paragraph_index = 0
        table_index = 0

        for child in body:
            if child.tag == qn("w:p"):
                paragraph_index += 1
                for _ in child.xpath(".//w:lastRenderedPageBreak | .//w:br[@w:type='page']", namespaces=NS):
                    page += 1
                pstyle = child.xpath("./w:pPr/w:pStyle/@w:val", namespaces=NS)
                style_id = pstyle[0] if pstyle else ""
                text = text_of(child)
                record = {
                    "type": "paragraph",
                    "index": paragraph_index,
                    "page": page,
                    "style_id": style_id,
                    "style": styles.get(style_id, style_id),
                    "text": text,
                }
                if text:
                    paragraphs.append(record)
                    blocks.append(record)
            elif child.tag == qn("w:tbl"):
                table_index += 1
                rows = []
                for tr in child.xpath("./w:tr", namespaces=NS):
                    cells = []
                    for tc in tr.xpath("./w:tc", namespaces=NS):
                        cell_paragraphs = [text_of(p) for p in tc.xpath("./w:p", namespaces=NS)]
                        cells.append("\n".join(x for x in cell_paragraphs if x))
                    rows.append(cells)
                record = {
                    "type": "table",
                    "index": table_index,
                    "page": page,
                    "rows": rows,
                }
                tables.append(record)
                blocks.append(record)

        title_nodes = core.xpath("//dc:title/text()", namespaces=NS) if core is not None else []
        author_nodes = core.xpath("//dc:creator/text()", namespaces=NS) if core is not None else []
        page_nodes = app.xpath("//ep:Pages/text()", namespaces=NS) if app is not None else []
        payload = {
            "path": str(input_path),
            "title": title_nodes[0] if title_nodes else "",
            "author": author_nodes[0] if author_nodes else "",
            "pages_metadata": int(page_nodes[0]) if page_nodes and page_nodes[0].isdigit() else None,
            "pages_rendered_breaks": page,
            "paragraphs": paragraphs,
            "tables": tables,
            "blocks": blocks,
        }

    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
