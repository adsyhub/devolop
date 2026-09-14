"""Local-VLM OCR pipeline: scanned PDF -> LLM-editable Markdown + JSON.

Built for Japanese study material (JLPT textbooks, past papers) that arrives as
image-only scans. Every page is transcribed by a local vision model; nothing
leaves the machine.

Entry point: ``python -m pdf_ocr``.
"""

__version__ = "0.1.0"
