import os

from PIL import Image

def export_image(matrix, width, height):
    img = Image.new('RGBA', (width, height), 255)

    # add pixels from the canvas matrix to the PNG
    for y in range(0, height):
        for x in range(0, width):
            img.putpixel((x, y), matrix[y][x])

    fCount = 0
    for f in os.listdir("."):
        if f.startswith("image"):      # check if filename already exists
            fCount += 1                # calculate a number to filename if duplicate names

    if fCount == 0:
        fCount = ""

    img.save("./images/image{}.png".format(fCount), "PNG")
