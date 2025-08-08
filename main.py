import cv2
import easyocr
import json
import matplotlib.pyplot as plt
import pymupdf
import re

def draw_bounding_boxes(image, detections):
    for box_coords, text in detections:
        cv2.rectangle(image, tuple(map(int, box_coords[0])), tuple(map(int, box_coords[2])), (0, 0, 255), 5)
        cv2.putText(image, text, tuple(map(int, box_coords[0])), cv2.FONT_HERSHEY_COMPLEX_SMALL, 2, (255, 0, 0), 2)

def find_y_delta(detection):
    coords, _ = detection
    return abs(int(coords[0][1]) - int(coords[2][1]))

def find_midpt(detection):
    coords, _ = detection
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


print('\n\n')
pdf = input("Place PDF in Upload folder and enter filename (including .pdf extension):\t")

pdf_path = f"Uplaod/{pdf}"

description_set = ["description"]
quantity_set = ["moq", "quantity", "qty"]
price_set = ["unit price", "price", "rate"]
cost_set = ["amount", "total"]

search_multiplier = 5
x_shift = 200
padding = 10
scaling_fac = 1/40

while True:
    try:
        pdf_path = f"Upload/{pdf}"
        doc = pymupdf.open(pdf_path)
        zoom = 4
        mat = pymupdf.Matrix(zoom, zoom)
        count = 0
        result = []
        break
    except:
        pdf = input("PDF could not be found, please try again (including .pdf extension):\t")

output_name = pdf_path[6:]
output_name = output_name[:-4]

# Uses OCR (easyocr) to read from pdf
# Reads entire page and sets var result to a list of the words and the coordinates or rectangle points
output_src = f"Intermediate/{output_name}.png"
page = doc.load_page(0)
pix = page.get_pixmap(matrix=mat)
pix.save(output_src)

reader = easyocr.Reader(['en'])
result = reader.readtext(output_src, paragraph=True, ycenter_ths=1, width_ths=0.7, add_margin=0.0255, y_ths=0.20)

contains_desc = False
contains_qty = False
contains_price = False
contains_cost = False
contains_dollar = False

# Fills word_dict with key: word, value: (x at midpt, y at midpt, x_delta)
for detected in result:
    coord, word = detected
    word = word.lower()

    for w in description_set:
        if w in word:
            contains_desc = True
            desc_x, desc_y = find_midpt(detected)
            desc_x_range = (int(coord[0][0]), int(coord[1][0]))
            desc_y_delta = find_y_delta(detected)
            break

    for w in quantity_set:
        if w in word:
            contains_qty = True
            qty_x, qty_y = find_midpt(detected)
            qty_x_range = (int(coord[0][0]), int(coord[1][0]))
            qty_y_delta = find_y_delta(detected)
            break


    for w in price_set:
        if w in word:
            contains_price = True
            price_x, price_y = find_midpt(detected)
            price_x_range = (int(coord[0][0]), int(coord[1][0]))
            price_y_delta = find_y_delta(detected)
            break

    for w in cost_set:
        if w in word:
            contains_cost = True
            cost_x, cost_y = find_midpt(detected)
            cost_x_range = (int(coord[0][0]), int(coord[1][0]))
            cost_y_delta = find_y_delta(detected)
            break
    
    if contains_desc and contains_qty and contains_price and contains_cost:
        break

result = reader.readtext(output_src, paragraph=True, ycenter_ths=1, width_ths=0.7, add_margin=(0.0255*desc_y_delta*scaling_fac), y_ths=(0.20*desc_y_delta*scaling_fac))


# Checks if there is a dollar sign in the PDF, if so I note it for removal from the beginning of each price
# I wrote this outside of the previous for loop, for some reason it breaks some of the logic later in the script
for _, text in result:
    if "$" in text:
        contains_dollar = True

# Error check
if not contains_desc:
    raise ValueError("Missing Contains.")
if not contains_qty:
    raise ValueError("Missing Quantity.")
if not contains_price:
    raise ValueError("Missing Price.")
if not contains_cost:
    raise ValueError("Missing Cost.")


# Search for quantities
descriptions = []
quantities = []
prices = []
costs = []

for detected in result:
    coords, word = detected
    x, y = find_midpt(detected)

    if ((abs(x - desc_x) < x_shift or within_category(coords, desc_x_range)) and abs(y - desc_y) < (desc_y_delta * search_multiplier)) and y > desc_y:
        descriptions.append(word)
        desc_x_range = (min(desc_x_range[0], coords[0][0]) - padding, max(desc_x_range[1], coords[1][0]) + padding)
        desc_x = x
        desc_y = y

    if ((abs(x - qty_x) < x_shift or within_category(coords, qty_x_range)) and abs(y - qty_y) < (qty_y_delta * search_multiplier)) and y > qty_y:
        quantities.append(word)
        qty_x_range = (min(qty_x_range[0], coords[0][0]) - padding, max(qty_x_range[1], coords[1][0]) + padding)
        qty_x = x
        qty_y = y

    if ((abs(x - price_x) < x_shift or within_category(coords, price_x_range)) and abs(y - price_y) < (price_y_delta * search_multiplier)) and y > price_y:
        prices.append(word)
        price_x_range = (min(price_x_range[0], coords[0][0]) - padding, max(price_x_range[1], coords[1][0]) + padding)
        price_x = x
        price_y = y

    if ((abs(x - cost_x) < x_shift or within_category(coords, cost_x_range)) and abs(y - cost_y) < (cost_y_delta * search_multiplier)) and y > cost_y:
        costs.append(word)
        cost_x_range = (min(cost_x_range[0], coords[0][0]) - padding, max(cost_x_range[1], coords[1][0]) + padding)
        cost_x = x
        cost_y = y


# Split up prices and costs they may have merged by easyocr settings
prices = [x for item in prices for x in item.split()]
costs = [x for item in costs for x in item.split()]

# Keep only elements in arr that contain numbers
prices = [re.sub(r'[^0-9$,.Ss-]', '', s) for s in prices if re.search(r'\d', s)]
costs = [re.sub(r'[^0-9$,.Ss-]', '', s) for s in costs if re.search(r'\d', s)]

# Remove the extraneous char if quote used dollar signs
if contains_dollar:
    prices = [s[1:] for s in prices if len(s) > 0]
    costs  = [s[1:] for s in costs  if len(s) > 0]

# Handle capturing quote total by OCR. Assumption: one of these values should be the true count of line items.
# Taking min should be correct as long as OCR scans properly.
max_len = min(len(quantities), len(prices), len(costs))

while len(prices) > max_len:
    prices.pop()

while len(costs) > max_len:
    costs.pop()


## Print to console, testing
# print('\n\n\n')
# for item in descriptions:
#     print(item)
# print('\n\n\n')
# for item in quantities:
#     print(item)
# print('\n\n\n')
# for item in prices:
#     print(item)
# print('\n\n\n')
# for item in costs:
#     print(item)

# print(descriptions)
# print(quantities)
# print(prices)
# print(costs)
            
# # Display a picture of how OCR is generating text boxes.
# img = cv2.imread(output_src)
# draw_bounding_boxes(img, result)
# plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGBA))
# plt.show()

json_items = []
quantity = 0
total = 0

for i in range(len(descriptions)):
    item = json.dumps({
        "description": descriptions[i],
        "quantity": quantities[i],
        "unitPrice": prices[i],
        "cost": costs[i]
    })

    json_items.append(item)

    quantities[i] = quantities[i].replace(",", "").strip()
    costs[i] = costs[i].replace(",", "").strip()

    quantity += float(quantities[i])
    total += float(costs[i])

build_json = '{' + f'"quantity": "{int(quantity)}", ' + f'"totalPrice": "{("%.2f" % float(total))}", ' + '"lineItems": ['

for s in json_items:
    build_json = build_json + s + ', '
build_json = build_json[:-2] + ']}'

data = json.loads(build_json)
# print(data)

json_str = json.dumps(data, indent=4)
with open(f"Output/{output_name}.json", "w") as f:
    f.write(json_str)

# print("raw json string:\n", build_json)

doc.close()