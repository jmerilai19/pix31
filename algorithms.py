def bresenham_line(origin, pos):
    line = []

    x0, y0 = origin[0], origin[1]
    x1, y1 = pos[0], pos[1]

    dx = abs(x1 - x0)
    dy = abs(y1 - y0)

    x, y = x0, y0
    sx = -1 if x0 > x1 else 1
    sy = -1 if y0 > y1 else 1

    if dx > dy:
        err = dx / 2.0
        while x != x1:
            line.append((x, y))
            err -= dy
            if err < 0:
                y += sy
                err += dx
            x += sx
    else:
        err = dy / 2.0
        while y != y1:
            line.append((x, y))
            err -= dx
            if err < 0:
                x += sx
                err += dy
            y += sy
    line.append((x, y))

    return line



def ellipse(origin, end):
    path = []

    mid = (round((end[0]-origin[0])/2), round((end[1]-origin[1])/2))

    rx, ry = abs(mid[0]), abs(mid[1])
    xc, yc = origin[0] + mid[0], origin[1] + mid[1]
    x = 0
    y = ry
    
    if ry == 0:
        left = min(origin[0], end[0])
        right = max(origin[0], end[0])
        for i in range(left, right):
            path.append((i, origin[1] + mid[1]))
    else:
        d1 = ((ry * ry) - (rx * rx * ry) + (0.25 * rx * rx))
        dx = 2 * ry * ry * x
        dy = 2 * rx * rx * y

        while (dx < dy):
            path.append((x + xc, y + yc))
            path.append((-x + xc, y + yc))
            path.append((x + xc, -y + yc))
            path.append((-x + xc, -y + yc))

            if (d1 < 0):
                x += 1
                dx = dx + (2 * ry * ry)
                d1 = d1 + dx + (ry * ry)
            else:
                x += 1
                y -= 1
                dx = dx + (2 * ry * ry)
                dy = dy - (2 * rx * rx)
                d1 = d1 + dx - dy + (ry * ry)

        d2 = (((ry * ry) * ((x + 0.5) * (x + 0.5))) + ((rx * rx) * ((y - 1) * (y - 1))) - (rx * rx * ry * ry))

        while (y >= 0):
            path.append((x + xc, y + yc))
            path.append((-x + xc, y + yc))
            path.append((x + xc, -y + yc))
            path.append((-x + xc, -y + yc))

            if (d2 > 0):
                y -= 1
                dy = dy - (2 * rx * rx)
                d2 = d2 + (rx * rx) - dy
            else:
                y -= 1
                x += 1
                dx = dx + (2 * ry * ry)
                dy = dy - (2 * rx * rx)
                d2 = d2 + dx - dy + (rx * rx)

    return path

def flood_fill(origin, canvas):
    """
    "Paint bucket tool"
    """
    area = []

    posList = []                                                    # a list for possible fillable positions
    canvasCopy = canvas.copy()
    posList.append((origin[0], len(canvasCopy) - 1 - origin[1]))    # add the clicked position to the list
    prevColor = canvasCopy[origin[1]][origin[0]]                    # check the original color that will be recolored
    newColor = [x+1 for x in prevColor]

    while posList:
        pos = posList.pop()   # take one position out of the list
        if canvasCopy[pos[1]][pos[0]] == prevColor:
            area.append((pos[0], len(canvasCopy) - 1 - pos[1]))
            canvasCopy[pos[1]][pos[0]] = newColor

            # check pos from upside
            x, y = pos[0], pos[1] - 1
            if y >= 0 and x >= 0 and y < len(canvasCopy) and x < len(canvasCopy[pos[1]]):
                if canvasCopy[y][x] == prevColor:
                    posList.append((x, y))

            # check pos from downside
            y = pos[1] + 1
            if y >= 0 and x >= 0 and y < len(canvasCopy) and x < len(canvasCopy[pos[1]]):
                if canvasCopy[y][x] == prevColor:
                    posList.append((x, y))

            # check pos from left side
            x, y = pos[0] - 1, pos[1]
            if y >= 0 and x >= 0 and y < len(canvasCopy) and x < len(canvasCopy[pos[1]]):
                if canvasCopy[y][x] == prevColor:
                    posList.append((x, y))

            # check pos from right side
            x = pos[0] + 1
            if y >= 0 and x >= 0 and y < len(canvasCopy) and x < len(canvasCopy[pos[1]]):
                if canvasCopy[y][x] == prevColor:
                    posList.append((x, y))

    return area

def rectangle(origin, end):
    path = []

    corners = [(origin[0], origin[1]), (end[0], end[1]), (origin[0], end[1]), (end[0], origin[1])]

    x0 = min(corners, key = lambda t: t[0])[0]
    y0 = max(corners, key = lambda t: t[1])[1]
    
    x1 = max(corners, key = lambda t: t[0])[0]
    y1 = min(corners, key = lambda t: t[1])[1]

    for i in range(x0, x1+1):
        path.append((i, y0))
        path.append((i, y1))

    for j in range(y1+1, y0):
        path.append((x0, j))
        path.append((x1, j))

    return path
