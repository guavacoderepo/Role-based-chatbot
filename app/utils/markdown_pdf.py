import markdown
from weasyprint import HTML
import tempfile
import os


def markdown_pdf(markdown_txt:str)->str:
    # Convert markdown to HTML
    html_content = markdown.markdown(markdown_txt, extensions=["tables"])

    # Inject CSS for table styling with grid lines
    css_styles = """
    <style>
        h1 {
            color: green;
            font-weight: bold;
            text-align: center;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        table, th, td {
            border: 1px solid #444;
        }
        th, td {
            padding: 8px;
            text-align: left;
        }
        th {
            background-color: #f2f2f2;
        }
    </style>
    """

    # Add company name and merge everything into the final HTML
    full_html = f"{css_styles}<h1>FinSolve Technologies</h1>{html_content}"

    # Create a temporary file for the PDF
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
        pdf_path = tmp_pdf.name
        # Render HTML content to PDF
        HTML(string=full_html).write_pdf(pdf_path)

    return pdf_path


md = "# Hello World\nThis is a **markdown** to PDF example."
pdf_path = markdown_pdf(md)
print(f"PDF generated at: {pdf_path}")
