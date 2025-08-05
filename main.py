import easyocr
import pymupdf

pdf_path = "input/VendraSampleQuote-01.pdf"

doc = pymupdf.open(pdf_path)
zoom = 4
mat = pymupdf.Matrix(zoom, zoom)
count = 0

for p in doc:
    count += 1

for i in range(count):
    val = f"output/image_{i+1}.png"
    page = doc.load_page(i)
    pix = page.get_pixmap(matrix=mat)
    pix.save(val)

    reader = easyocr.Reader(['en'])
    result = reader.readtext(val, detail=0)

    print(result)

doc.close()