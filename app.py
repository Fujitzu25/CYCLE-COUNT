import os
from flask import Flask, render_template_string, request, send_file, io
from barcode import Code128
from barcode.writer import ImageWriter
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

app = Flask(__name__)

# HTML Template for your private local browser interface
HTML_TEMPLATE = """
<!xltype html>
<html>
<head>
    <title>Private Shelftag & Barcode Generator</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background-color: #f4f7f6; color: #333; }
        .container { max-width: 500px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
        h2 { text-align: center; color: #0056b3; margin-bottom: 20px; }
        label { font-weight: bold; display: block; margin-top: 15px; }
        input[type="text"] { width: 100%; padding: 10px; margin-top: 5px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
        input[type="submit"] { width: 100%; background-color: #0056b3; color: white; padding: 12px; margin-top: 25px; border: none; border-radius: 4px; font-size: 16px; cursor: pointer; font-weight: bold; }
        input[type="submit"]:hover { background-color: #004085; }
        .footer { text-align: center; margin-top: 20px; font-size: 12px; color: #777; }
    </style>
</head>
<body>
    <div class="container">
        <h2>🏷️ Private Tag Generator</h2>
        <form method="POST" action="/generate">
            <label>Product Name:</label>
            <input type="text" name="product_name" placeholder="e.g., Wireless Mouse" required>
            
            <label>Price ($):</label>
            <input type="text" name="price" placeholder="e.g., 29.99" required>
            
            <label>SKU / Barcode Data:</label>
            <input type="text" name="sku" placeholder="e.g., 12345678" required>
            
            <input type="submit" value="Generate & Download Tag">
        </form>
        <div class="footer">Running locally &bull; 100% Private</div>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/generate', methods=['POST'])
def generate():
    prod_name = request.form.get('product_name')
    price = f"${request.form.get('price')}"
    sku = request.form.get('sku')
    
    # 1. Generate the Barcode image in memory
    barcode_buffer = io.BytesIO()
    my_code = Code128(sku, writer=ImageWriter())
    my_code.write(barcode_buffer, options={"write_text": False, "quiet_zone": 1.0})
    barcode_buffer.seek(0)
    
    # 2. Build a single ready-to-print PDF Shelftag
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=(3.5 * inch, 2.5 * inch),
                            rightMargin=0.1*inch, leftMargin=0.1*inch, topMargin=0.1*inch, bottomMargin=0.1*inch)
    
    styles = getSampleStyleSheet()
    name_style = ParagraphStyle('ProdName', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=12, leading=14)
    price_style = ParagraphStyle('Price', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=22, leading=24, textColor=colors.HexColor("#d9534f"), alignment=2)
    sku_style = ParagraphStyle('SKU', parent=styles['Normal'], fontName='Helvetica', fontSize=9, alignment=1)
    
    from reportlab.platypus import Image as RLImage
    barcode_img = RLImage(barcode_buffer, width=2.0*inch, height=0.6*inch)
    
    # Grid Layout for the retail tag
    data = [
        [Paragraph(prod_name, name_style), Paragraph(price, price_style)],
        [barcode_img, ''],
        [Paragraph(sku, sku_style), '']
    ]
    
    table = Table(data, colWidths=[2.1*inch, 1.2*inch])
    table.setStyle(TableStyle([
        ('SPAN', (0, 1), (1, 1)), # Span barcode across rows
        ('SPAN', (0, 2), (1, 2)), # Span text SKU across rows
        ('ALIGN', (0, 1), (1, 1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    
    story = [table]
    doc.build(story)
    pdf_buffer.seek(0)
    
    return send_file(pdf_buffer, mimetype='application/pdf', as_attachment=True, download_name=f"tag_{sku}.pdf")

if __name__ == '__main__':
    # Runs locally only on your device
    app.run(host='127.0.0.1', port=5000, debug=True)
