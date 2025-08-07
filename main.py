import easyocr
import pymupdf

pdf_path = "Input/VendraSampleQuote-03.pdf"
output_name = pdf_path[6:]
output_name = output_name[:-4]

description_set = ["description"]
unit_price_set = ["unit price", ]
quantity_set = ["moq", "quantity", "qty"]
cost_set = ["amount", "total"]

# Generate a superset to help remove header text
super_set = description_set + unit_price_set + quantity_set + cost_set


doc = pymupdf.open(pdf_path)
zoom = 4
mat = pymupdf.Matrix(zoom, zoom)
count = 0
result = []

for p in doc:
    count += 1

# Use OCR to read from pdf
for i in range(count):
    val = f"Output/{output_name}_pg_{i+1}.png"
    page = doc.load_page(i)
    pix = page.get_pixmap(matrix=mat)
    pix.save(val)

    reader = easyocr.Reader(['en'])
    result += reader.readtext(val, detail=0)

    print(result)

print('\n\n\n')

i = 0
header_removed = False
while i < len(result):
    if not header_removed:
        result[i] = result[i].lower()
        for keyword in super_set:
            if keyword in result[i]:
                header_removed = True
        
        if not header_removed:
            result = result[1:]
    else:
        result[i] = result[i].lower()
        i += 1

    
print(result)

doc.close()