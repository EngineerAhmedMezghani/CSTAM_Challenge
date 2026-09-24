from docling.document_converter import DocumentConverter

converter = DocumentConverter()
result = converter.convert("data_collector_for_rag_agent/Annual accounts of OLIVE-SOFT/OLIVE-SOFT - Comptes sociaux 2022.pdf")

print(result.document.export_to_markdown())
