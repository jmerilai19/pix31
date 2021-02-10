from PIL import Image
import os

def export_image(matrix, width, height):
    """
    Creates a PNG image out of the pixel matrix
    """
    img = Image.new('RGBA', (width, height), 255)

    # add pixels from the canvas matrix to the PNG
    for y in range(0, height):
        for x in range(0, width):
            img.putpixel((x, y), matrix[y][x])

    f_count = 0
    for f in os.listdir("."):
        if f.startswith("image"):       # check if filename already exists
            f_count += 1                # calculate a number to filename if duplicate names

    if f_count == 0:
        f_count = ""

    img.save("image{}.png".format(f_count), "PNG")