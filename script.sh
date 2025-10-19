$(PYTHON) -c "from src.code.pdf_to_md import PDFToMarkdown; p=PDFToMarkdown('pdfs/$(FNAME)'); p.run(); print('Converted ->', p.output_filepath)"
