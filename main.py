import cv2
import easyocr
import matplotlib.pyplot as plt
import pymupdf

def draw_bounding_boxes(image, detections):
    for box_coords, text, score in detections:
        cv2.rectangle(image, tuple(map(int, box_coords[0])), tuple(map(int, box_coords[2])), (0, 0, 255), 5)
        cv2.putText(image, text, tuple(map(int, box_coords[0])), cv2.FONT_HERSHEY_COMPLEX_SMALL, 2, (255, 0, 0), 2)

def find_y_delta(detection):
    coords, _, _ = detection
    return abs(int(coords[0][1]) - int(coords[2][1]))

def find_midpt(detection):
    coords, _, _ = detection
    x = (int(coords[0][0]) + int(coords[1][0])) / 2
    y = (int(coords[0][1]) + int(coords[2][1])) / 2
    return (x, y)

def within_category(coords: list, range: tuple):
    coord_list = []
    for coord in coords:
        if coord[0] >= range[0] and coord[0] <= range[1]:
            return True
        else:
            coord_list.append(coord[0])

    min_x = min(coord_list)
    max_x = max(coord_list)
    return (range[0] > min_x and range[1] < max_x)


pdf_path = "Input/VendraSampleQuote-01.pdf"
output_name = pdf_path[6:]
output_name = output_name[:-4]

description_set = ["description"]
quantity_set = ["moq", "quantity", "qty"]
unit_price_set = ["unit price", "price", "rate"]
cost_set = ["amount", "total"]

search_multiplier = 4.5
x_shift = 200

doc = pymupdf.open(pdf_path)
zoom = 4
mat = pymupdf.Matrix(zoom, zoom)
count = 0
result = []


# Uses OCR (easyocr) to read from pdf
# Reads entire page and sets var result to a list of the words and the coordinates or rectangle points
output_src = f"Output/{output_name}.png"
page = doc.load_page(0)
pix = page.get_pixmap(matrix=mat)
pix.save(output_src)

reader = easyocr.Reader(['en'])
result += reader.readtext(output_src, ycenter_ths=1, width_ths=0.7, add_margin=0.2)

# print(result)

contains_desc = False
contains_qty = False
contains_price = False
contains_cost = False

# Fills word_dict with key: word, value: (x at midpt, y at midpt, x_delta)
for detected in result:
    coord, word, _ = detected
    word = word.lower()

    if word in description_set:
        contains_desc = True
        desc_x, desc_y = find_midpt(detected)
        desc_x_range = (int(coord[0][0]), int(coord[1][0]))
        desc_y_delta = find_y_delta(detected)

    elif word in quantity_set:
        contains_qty = True
        qty_x, qty_y = find_midpt(detected)
        qty_x_range = (int(coord[0][0]), int(coord[1][0]))
        qty_y_delta = find_y_delta(detected)

    elif word in unit_price_set:
        contains_price = True
        price_x, price_y = find_midpt(detected)
        price_x_range = (int(coord[0][0]), int(coord[1][0]))
        price_y_delta = find_y_delta(detected)

    elif word in cost_set:
        contains_cost = True
        cost_x, cost_y = find_midpt(detected)
        cost_x_range = (int(coord[0][0]), int(coord[1][0]))
        cost_y_delta = find_y_delta(detected)
    
    if contains_desc and contains_qty and contains_price and contains_cost:
        break

# Error check
if (not contains_desc) or (not contains_qty) or (not contains_price) or (not contains_cost):
    raise ValueError("Missing Invoice Field.")



# Search for quantities
descriptions = []
quantities = []
unit_prices = []
costs = []

for detected in result:
    coords, word, _ = detected
    x, y = find_midpt(detected)

    if ((abs(x - desc_x) < x_shift or within_category(coords, desc_x_range)) and abs(y - desc_y) < (desc_y_delta * search_multiplier)) and y > desc_y:
        descriptions.append(word)
        desc_x_range = (min(desc_x_range[0], coords[0][0]), max(desc_x_range[1], coords[1][0]))
        desc_x = x
        desc_y = y

    if ((abs(x - qty_x) < x_shift or within_category(coords, qty_x_range)) and abs(y - qty_y) < (qty_y_delta * search_multiplier)) and y > qty_y:
        quantities.append(word)
        qty_x_range = (min(qty_x_range[0], coords[0][0]), max(qty_x_range[1], coords[1][0]))
        qty_x = x
        qty_y = y

    if ((abs(x - price_x) < x_shift or within_category(coords, price_x_range)) and abs(y - price_y) < (price_y_delta * search_multiplier)) and y > price_y:
        unit_prices.append(word)
        price_x_range = (min(price_x_range[0], coords[0][0]), max(price_x_range[1], coords[1][0]))
        price_x = x
        price_y = y

    if ((abs(x - cost_x) < x_shift or within_category(coords, cost_x_range)) and abs(y - cost_y) < (cost_y_delta * search_multiplier)) and y > cost_y:
        costs.append(word)
        cost_x_range = (min(cost_x_range[0], coords[0][0]), max(cost_x_range[1], coords[1][0]))
        cost_x = x
        cost_y = y


# Handle capturing quote total by OCR. Assumption: one of these values should be the true count of line items.
# Taking min should be correct as long as OCR scans properly.
max_len = min(len(quantities), len(unit_prices), len(costs))

while len(unit_prices) > max_len:
    unit_prices.pop()

while len(costs) > max_len:
    costs.pop()




print('\n\n\n')

for item in descriptions:
    print(item)

print('\n\n\n')

for item in quantities:
    print(item)

print('\n\n\n')

for item in unit_prices:
    print(item)

print('\n\n\n')

for item in costs:
    print(item)
            
# Generate 



img = cv2.imread(output_src)
draw_bounding_boxes(img, result)
plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGBA))
plt.show()

doc.close()