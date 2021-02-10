def read_hex_to_rgb(filename):
    """
    Reads the given hex file and return a list of rgb values.
    """
    palette_colors = []

    with open(filename) as f:
            for _, line in enumerate(f):
                stripped_line = line.strip("\n")
                rgb = tuple(int(stripped_line[i:i+2], 16) for i in (0, 2, 4))
                palette_colors.append((rgb[0], rgb[1], rgb[2], 255))

    return palette_colors