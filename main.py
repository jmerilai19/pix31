import math
import pyglet
import pyglet.gl as gl

import algorithms as algo
import constants as const
import export as exp
import palette_manager as palet

class Artist():
    def __init__(self) -> None:
        self.primaryColor = (0, 0, 0, 255)
        self.secondaryColor = (255, 0, 0, 255)
        self.mode = "pencil"
        self.palette = palet.read_hex_to_rgb("./palette_default.hex")

class Canvas():
    def __init__(self, width, height) -> None:
        self.width = width
        self.height = height
        self.origin = [0, 0]
        self.backgroundColor = (255, 255, 255, 255)

        self.pixelMatrix = []
        self.pixelBatchMatrix = []
        self.previewMatrix = []
        self.previewBatchMatrix = []

        self.mousePos = [0, 0]      # mouse coordinates on canvas
        self.beginningPos = [0, 0]  # beginning coordinates of action
        self.endPos = [0, 0]        # end coordinates of action

        self.gridOn = False

    def add_pixel(self, pos, color, matrix, batch):
        if matrix == "pixel":
            matrixPosY = len(self.pixelMatrix) - 1 - pos[1]

            if 0 <= matrixPosY < const.CANVAS_SIZE_Y and 0 <= pos[0] < const.CANVAS_SIZE_X:
                self.add_pixel_to_batch((pos[0], matrixPosY), color, matrix, batch)
                self.pixelMatrix[matrixPosY][pos[0]] = color
        elif matrix == "preview":
            matrixPosY = len(self.previewMatrix) - 1 - pos[1]

            if 0 <= matrixPosY < const.CANVAS_SIZE_Y and 0 <= pos[0] < const.CANVAS_SIZE_X:
                self.add_pixel_to_batch((pos[0], matrixPosY), color, matrix, batch)
                self.previewMatrix[matrixPosY][pos[0]] = color

    def add_pixel_to_batch(self, pos, color, matrix, batch):
        x = pos[0] + self.origin[0]                              # convert pixel position to canvas position
        y = (self.height - pos[1]) + self.origin[1]

        if matrix == "pixel":
            if not self.pixelBatchMatrix[pos[1]][pos[0]] == None:                              
                self.pixelBatchMatrix[pos[1]][pos[0]].delete()   # delete pixel from batch before replacing it                 
            
            self.pixelBatchMatrix[pos[1]][pos[0]] = batch.add(4, pyglet.gl.GL_QUADS, None,   # add a pixel to the batch
                ('v2f', [x, 
                        y - 1, 
                        x + 1, 
                        y - 1, 
                        x + 1, 
                        y, 
                        x, 
                        y]),
                ('c4B', (color[0], color[1], color[2], color[3], 
                        color[0], color[1], color[2], color[3], 
                        color[0], color[1], color[2], color[3], 
                        color[0], color[1], color[2], color[3])))
        elif matrix == "preview":
            #color = (0, 255, 0, 0) # debug color for testing batch transfer
            if not self.previewBatchMatrix[pos[1]][pos[0]] == None:                              
                self.previewBatchMatrix[pos[1]][pos[0]].delete()   # delete pixel from batch before replacing it                 
            
            self.previewBatchMatrix[pos[1]][pos[0]] = batch.add(4, pyglet.gl.GL_QUADS, None,   # add a pixel to the batch
                ('v2f', [x, 
                        y - 1, 
                        x + 1, 
                        y - 1, 
                        x + 1, 
                        y, 
                        x, 
                        y]),
                ('c4B', (color[0], color[1], color[2], color[3], 
                        color[0], color[1], color[2], color[3], 
                        color[0], color[1], color[2], color[3], 
                        color[0], color[1], color[2], color[3])))

    def color_pick(self, pos, artist, button):
        matrixPosY = len(self.pixelMatrix) - 1 - pos[1]
        if not self.pixelMatrix[matrixPosY][pos[0]] == (-1, -1, -1, -1):
            if button == 0:
                artist.primaryColor = self.pixelMatrix[matrixPosY][pos[0]]
            elif button == 1:
                artist.secondaryColor = self.pixelMatrix[matrixPosY][pos[0]]

    def delete_pixel(self, pos):
        matrixPosY = len(self.pixelMatrix) - 1 - pos[1]

        if 0 <= matrixPosY < const.CANVAS_SIZE_Y and 0 <= pos[0] < const.CANVAS_SIZE_X:
            if not self.pixelBatchMatrix[matrixPosY][pos[0]] == None:                              
                self.pixelBatchMatrix[matrixPosY][pos[0]].delete()
                self.pixelBatchMatrix[matrixPosY][pos[0]] = None
                self.pixelMatrix[matrixPosY][pos[0]] = (-1, -1, -1, -1)

    def draw_ellipse(self, color, batch):
        pixels = algo.ellipse(self.beginningPos, self.endPos)
        for pixel in pixels:
            self.add_pixel(pixel, color, "preview", batch)

    def draw_point(self, color, batch):
        self.add_pixel(self.mousePos, color, "preview", batch)

    def draw_line(self, color, batch):
        pixels = algo.bresenham_line(self.beginningPos, self.endPos)
        for pixel in pixels:
            self.add_pixel(pixel, color, "preview", batch)

    def draw_rectangle(self, color, batch):
        pixels = algo.rectangle(self.beginningPos, self.endPos)
        for pixel in pixels:
            self.add_pixel(pixel, color, "preview", batch)

    def erase_point(self):
        self.delete_pixel(self.mousePos)

    def erase_line(self):
        pixels = algo.bresenham_line(self.beginningPos, self.endPos)
        for pixel in pixels:
            self.delete_pixel(pixel)

    def fill(self, color, batch):
        pixels = algo.flood_fill(self.mousePos, self.pixelMatrix)
        for pixel in pixels:
            self.add_pixel(pixel, color, "pixel", batch)

    def is_mouse_on_canvas(self, x, y):
        wWd2, wHd2 = const.WINDOW_START_WIDTH/2, const.WINDOW_START_HEIGHT/2
        if wWd2 - self.width/2 < x < wWd2 + self.width/2 and wHd2 - self.height/2 < y < wHd2 + self.height/2:
            return True
        return False

    def update_background(self):
        self.canvasBgImage = pyglet.image.SolidColorImagePattern(self.backgroundColor).create_image(self.width, self.height)

        # remove gl interpolation for sharp canvas edges when zoomed
        canvasBgTexture = self.canvasBgImage.get_texture()
        gl.glBindTexture(gl.GL_TEXTURE_2D, canvasBgTexture.id)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)

        self.canvasBgSprite = pyglet.sprite.Sprite(self.canvasBgImage, x=self.origin[0], y=self.origin[1])

        self.background = self.canvasBgSprite

class ModeButton():
    def __init__(self, x, y, baseBatch, batch, index = 0):
        self.x = 14 + x * 28
        self.y = 14 + y * 28
        self.mode = ""
        self.index = index
        self.hover = False
        self.color = (120, 120, 120, 255)

        self.image = pyglet.image.SolidColorImagePattern(self.color).create_image(24, 24)
        self.sprite = pyglet.sprite.Sprite(self.image, x=self.x, y=self.y, batch=baseBatch)

        if self.index == 0:
            self.mode = "pencil"
            img = pyglet.image.load('./icons/pencil.png')
            self.icon = pyglet.sprite.Sprite(img, x=self.x+4, y=self.y+4, batch=batch)
        elif self.index == 1:
            self.mode = "eraser"
            img = pyglet.image.load('./icons/eraser.png')
            self.icon = pyglet.sprite.Sprite(img, x=self.x+4, y=self.y+4, batch=batch)
        elif self.index == 2:
            self.mode = "dropper"
            img = pyglet.image.load('./icons/dropper.png')
            self.icon = pyglet.sprite.Sprite(img, x=self.x+4, y=self.y+4, batch=batch)
        elif self.index == 3:
            self.mode = "line"
            img = pyglet.image.load('./icons/line.png')
            self.icon = pyglet.sprite.Sprite(img, x=self.x+4, y=self.y+4, batch=batch)
        elif self.index == 5:
            self.mode = "rectangle"
            img = pyglet.image.load('./icons/rect.png')
            self.icon = pyglet.sprite.Sprite(img, x=self.x+4, y=self.y+4, batch=batch)
        elif self.index == 6:
            self.mode = "ellipse"
            img = pyglet.image.load('./icons/ellipse.png')
            self.icon = pyglet.sprite.Sprite(img, x=self.x+4, y=self.y+4, batch=batch)
        elif self.index == 7:
            self.mode = "fill"
            img = pyglet.image.load('./icons/paint-bucket.png')
            self.icon = pyglet.sprite.Sprite(img, x=self.x+4, y=self.y+4, batch=batch)

class PaletteButton():
    def __init__(self, x, y, color, batch):
        self.x = x
        self.y = y
        self.color = color

        self.image = pyglet.image.SolidColorImagePattern(self.color).create_image(16, 16)
        self.sprite = pyglet.sprite.Sprite(self.image, x=x, y=y, batch=batch)

class Window(pyglet.window.Window):
    def __init__(self, width, height, canvas, artist, *args, **kwargs):
        super().__init__(width, height, *args, **kwargs)
        self.width  = width
        self.height = height
        self.lastWidth  = width
        self.lastHeight = height

        self.mousePos = [0, 0] # mouse coordinates on window

        self.init_canvas(canvas)

        self.pixelBatch = pyglet.graphics.Batch()
        self.previewBatch = pyglet.graphics.Batch()
        self.topToolbarBatch = pyglet.graphics.Batch()
        self.topToolbarIconBatch = pyglet.graphics.Batch()

        self.modeButtons = []
        self.init_modebuttons()

        # pixel cursor
        self.pixelCursorImage = pyglet.image.SolidColorImagePattern(
                    (0,0,0,96)).create_image(
                    1,
                    1)
        self.pixelCursorSprite = None

        # shadow for pressing mode buttons
        self.buttonShadowImage = pyglet.image.SolidColorImagePattern((0, 0, 0, 96)).create_image(24, 24)
        self.buttonShadowSprite = pyglet.sprite.Sprite(self.buttonShadowImage, x=14, y=42)

        # shadow for palette
        self.paletteShadowImage = pyglet.image.SolidColorImagePattern((0, 0, 0, 96)).create_image(16, 16)
        self.paletteShadowSprite = pyglet.sprite.Sprite(self.paletteShadowImage, x=0, y=100) 

        for y in range(0, const.CANVAS_SIZE_Y):
            self.canvas.pixelMatrix.append([])
            self.canvas.pixelBatchMatrix.append([])
            self.canvas.previewMatrix.append([])
            self.canvas.previewBatchMatrix.append([])
            for _ in range(0, const.CANVAS_SIZE_X):
                self.canvas.pixelMatrix[y].append((-1, -1, -1, -1))
                self.canvas.pixelBatchMatrix[y].append(None)
                self.canvas.previewMatrix[y].append((-1, -1, -1, -1))
                self.canvas.previewBatchMatrix[y].append(None)

        self.init_artist(artist)
        self.init_camera()
        self.init_toolbar_backgrounds()
        self.init_palette()
        self.set_color_display()
        self.set_app_icon()
        self.set_window_background_color()
        self.update_zoom_percentage_label()
        self.update_canvas_size_label()

    def apply_preview(self):
        for y in range(len(self.canvas.previewMatrix)):
            for x in range(len(self.canvas.previewMatrix[y])):
                if not self.canvas.previewMatrix[y][x] == (-1, -1, -1, -1):
                    self.canvas.pixelMatrix[y][x] = self.canvas.previewMatrix[y][x]
                    self.canvas.previewMatrix[y][x] = (-1, -1, -1, -1)

                    canvasY = len(self.canvas.previewMatrix[y]) - 1 - y
                    self.canvas.add_pixel((x, canvasY), self.canvas.pixelMatrix[y][x], "pixel", self.pixelBatch)
                    self.canvas.previewBatchMatrix[y][x].delete()
                    self.canvas.previewBatchMatrix[y][x] = None

    def clear_preview(self):
        for y in range(len(self.canvas.previewMatrix)):
            for x in range(len(self.canvas.previewMatrix[y])):
                if not self.canvas.previewMatrix[y][x] == (-1, -1, -1, -1):
                    self.canvas.previewMatrix[y][x] = (-1, -1, -1, -1)

                    canvasY = len(self.canvas.previewMatrix[y]) - 1 - y
                    self.canvas.previewBatchMatrix[y][x].delete()
                    self.canvas.previewBatchMatrix[y][x] = None

    def convert_mouse_to_canvas_coordinates(self, x, y):
        # position of the mouse relative to window (0.0-1.0)
        mouseX = x/self.width
        mouseY = y/self.height

        # mouse position in world coordinates
        mouseWorldX = self.left   + mouseX*self.zoomedWidth
        mouseWorldY = self.bottom + mouseY*self.zoomedHeight

        # mouse position on canvas
        mouseCanvasX = math.floor(mouseWorldX - const.WINDOW_START_WIDTH/2 + self.canvas.width/2)
        mouseCanvasY = math.floor(mouseWorldY - const.WINDOW_START_HEIGHT/2 + self.canvas.height/2)

        return mouseCanvasX, mouseCanvasY

    def draw_bottom_toolbar_background(self):
        # set gl stuff
        gl.glViewport(0, 0, self.width, 20)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        gl.gluOrtho2D(0, self.width, 0, 20)
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity()

        # draw background
        self.bottomToolbarBgSprite.draw()

    def draw_grid():
        pass

    def draw_main_area(self):
        # set gl stuff
        gl.glViewport(0, 0, self.width, self.height)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        gl.gluOrtho2D(self.left, self.right, self.bottom, self.top)
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity()

        # clear window with ClearColor
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

        # draw blank canvas
        self.canvas.background.draw()

        self.pixelBatch.draw()
        self.previewBatch.draw()

    def draw_top_toolbar_background(self):
        # set gl stuff
        gl.glViewport(0, self.height - 80, self.width, 80)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        gl.gluOrtho2D(0, self.width, 0, 80)
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity()

        # draw background
        self.topToolbarBgSprite.draw()

    def draw_top_toolbar_icons(self):
        self.topToolbarBatch.draw()
        self.topToolbarIconBatch.draw()

    def init_artist(self, artist):
        self.artist = artist

    def init_camera(self):
        self.left   = 0
        self.right  = self.width
        self.bottom = 0
        self.top    = self.height
        self.zoomLevel = 1 # 1 = normal
        self.zoomedWidth  = self.width
        self.zoomedHeight = self.height

    def init_canvas(self, canvas):
        self.canvas = canvas

        self.canvas.origin[0] = self.width/2 - self.canvas.width/2
        self.canvas.origin[1] = self.height/2 - self.canvas.height/2

        self.canvas.update_background()

    def init_modebuttons(self):
        cut = 5
        for i in range(0, 10):
            if i < cut:
                self.modeButtons.append(ModeButton(i, 1, self.topToolbarBatch, self.topToolbarIconBatch, i))
            else:
                self.modeButtons.append(ModeButton(i-cut, 0, self.topToolbarBatch, self.topToolbarIconBatch, i))

    def init_palette(self):
        x, y = 180, 0
        cut = 11   # how many palette colors in one row

        # left color label
        self.colorleft_label = pyglet.text.Label("Left:",
                font_name=const.FONT_NAME,
                font_size=9,
                x=x, y=y+48,
                anchor_x='left', anchor_y='bottom', bold=const.FONT_BOLD, batch=self.topToolbarBatch)

        # right color label
        self.colorright_label = pyglet.text.Label("Right:",
                font_name=const.FONT_NAME,
                font_size=9,
                x=x+35, y=y+48,
                anchor_x='left', anchor_y='bottom', bold=const.FONT_BOLD, batch=self.topToolbarBatch)

        self.palette = []
        self.paletteColors = []

        for index in range(0, 33):
            # first row
            if index < cut:
                xx = x + 92 + index*16 + index*4
                yy = y + 52
            else:
                # second row
                if index < 2*cut:
                    xx = x + 92 + (index-cut)*16 + (index-cut)*4
                    yy = y + 32
                # third row
                else:
                    xx = x + 92 + (index-2*cut)*16 + (index-2*cut)*4
                    yy = y + 12

            self.paletteColors.append(PaletteButton(xx, yy, self.artist.palette[index], self.topToolbarBatch))


    def init_toolbar_backgrounds(self):
        bgCol = const.WINDOW_TOOLBAR_COLOR

        # top
        self.topToolbarBgImage = pyglet.image.SolidColorImagePattern((bgCol[0], bgCol[1], bgCol[2], bgCol[3])).create_image(
            self.width, const.WINDOW_TOP_TOOLBAR_HEIGHT)
        self.topToolbarBgSprite = pyglet.sprite.Sprite(self.topToolbarBgImage, x=0, y=0)

        # bottom
        self.bottomToolbarBgImage = pyglet.image.SolidColorImagePattern((bgCol[0], bgCol[1], bgCol[2], bgCol[3])).create_image(
            self.width, const.WINDOW_BOTTOM_TOOLBAR_HEIGHT)
        self.bottomToolbarBgSprite = pyglet.sprite.Sprite(self.bottomToolbarBgImage, x=0, y=0)

    def on_draw(self):
        self.draw_main_area()

        if not self.pixelCursorSprite == None:
            self.pixelCursorSprite.draw()

        if self.canvas.gridOn and self.zoomLevel < 0.5:
            self.draw_grid()

        self.draw_bottom_toolbar_background()
        self.zoomLabel.draw()
        self.sizeLabel.draw()
        if self.canvas.is_mouse_on_canvas(self.mousePos[0], self.mousePos[1]):
            self.positionLabel.draw()

        self.draw_top_toolbar_background()
        self.draw_top_toolbar_icons()
        self.paletteLeftColorSprite.draw()
        self.paletteRightColorSprite.draw()
        self.buttonShadowSprite.draw()
        self.paletteShadowSprite.draw()
        

    def on_key_press(self, symbol, modifiers):
        if symbol == pyglet.window.key._0:   # debug export
            exp.export_image(self.canvas.pixelMatrix, const.CANVAS_SIZE_X, const.CANVAS_SIZE_Y)

    def on_mouse_drag(self, x, y, dx, dy, button, modifiers):
        self.set_mouse_coordinates(x, y)
        self.update_pixel_cursor_position()
        self.canvas.endPos[0], self.canvas.endPos[1] = self.convert_mouse_to_canvas_coordinates(x, y)

        if abs(self.canvas.endPos[0] - self.canvas.beginningPos[0]) > 0 \
        or abs(self.canvas.endPos[1] - self.canvas.beginningPos[1]) > 0:
            if self.artist.mode == "pencil":
                if button == pyglet.window.mouse.LEFT:
                    self.canvas.draw_line(self.artist.primaryColor, self.previewBatch)
                elif button == pyglet.window.mouse.RIGHT:
                    self.canvas.draw_line(self.artist.secondaryColor, self.previewBatch)
                self.canvas.beginningPos[0], self.canvas.beginningPos[1] = self.canvas.endPos[0], self.canvas.endPos[1]
            elif self.artist.mode == "eraser":
                if button == pyglet.window.mouse.LEFT:
                    self.canvas.erase_line()
                self.canvas.beginningPos[0], self.canvas.beginningPos[1] = self.canvas.endPos[0], self.canvas.endPos[1]
            elif self.artist.mode == "line":
                self.clear_preview()
                if button == pyglet.window.mouse.LEFT:
                    self.canvas.draw_line(self.artist.primaryColor, self.previewBatch)
                elif button == pyglet.window.mouse.RIGHT:
                    self.canvas.draw_line(self.artist.secondaryColor, self.previewBatch)
            elif self.artist.mode == "rectangle":
                self.clear_preview()
                if button == pyglet.window.mouse.LEFT:
                    self.canvas.draw_rectangle(self.artist.primaryColor, self.previewBatch)
                elif button == pyglet.window.mouse.RIGHT:
                    self.canvas.draw_rectangle(self.artist.secondaryColor, self.previewBatch)
            elif self.artist.mode == "ellipse":
                self.clear_preview()
                if button == pyglet.window.mouse.LEFT:
                    self.canvas.draw_ellipse(self.artist.primaryColor, self.previewBatch)
                elif button == pyglet.window.mouse.RIGHT:
                    self.canvas.draw_ellipse(self.artist.secondaryColor, self.previewBatch)

    def on_mouse_press(self, x, y, button, modifiers):
        self.set_mouse_coordinates(x, y)
        if 48 < y < self.height - 80:   # inside main area
            if self.canvas.is_mouse_on_canvas(self.mousePos[0], self.mousePos[1]):   # inside canvas
                self.canvas.beginningPos[0], self.canvas.beginningPos[1] = self.canvas.mousePos[0], self.canvas.mousePos[1]
                if self.artist.mode == "pencil":
                    if button == pyglet.window.mouse.LEFT:
                        self.canvas.draw_point(self.artist.primaryColor, self.previewBatch)
                    elif button == pyglet.window.mouse.RIGHT:
                        self.canvas.draw_point(self.artist.secondaryColor, self.previewBatch)
                elif self.artist.mode == "eraser":
                    if button == pyglet.window.mouse.LEFT:
                        self.canvas.erase_point()
                elif self.artist.mode == "line":
                    if button == pyglet.window.mouse.LEFT:
                        self.canvas.draw_point(self.artist.primaryColor, self.previewBatch)
                    elif button == pyglet.window.mouse.RIGHT:
                        self.canvas.draw_point(self.artist.secondaryColor, self.previewBatch)
                elif self.artist.mode == "dropper":
                    if button == pyglet.window.mouse.LEFT:
                        self.canvas.color_pick(self.canvas.mousePos, self.artist, 0)
                    elif button == pyglet.window.mouse.RIGHT:
                        self.canvas.color_pick(self.canvas.mousePos, self.artist, 1)
                    self.set_color_display()
                elif self.artist.mode == "rectangle":
                    if button == pyglet.window.mouse.LEFT:
                        self.canvas.draw_point(self.artist.primaryColor, self.previewBatch)
                    elif button == pyglet.window.mouse.RIGHT:
                        self.canvas.draw_point(self.artist.secondaryColor, self.previewBatch)
                elif self.artist.mode == "fill":
                    if button == pyglet.window.mouse.LEFT:
                        self.canvas.fill(self.artist.primaryColor, self.pixelBatch)
                    elif button == pyglet.window.mouse.RIGHT:
                        self.canvas.fill(self.artist.secondaryColor, self.pixelBatch)
        else:
            if y > self.height - 80:   # inside top toolbar
                found = False
                for box in self.paletteColors:
                    if box.x < x < box.x + 16 and self.height - 80 + box.y < y < self.height - 80 + box.y + 16:
                        if button == pyglet.window.mouse.LEFT:
                            self.artist.primaryColor = box.color
                        elif button == pyglet.window.mouse.RIGHT:
                            self.artist.secondaryColor = box.color

                        # draw shadow on clicked item
                        self.paletteShadowSprite.x = box.x
                        self.paletteShadowSprite.y = box.y

                        self.set_color_display()
                        found = True
                        break
                if found == False:
                    for box in self.modeButtons:
                        if box.x < x < box.x + 24 and self.height - 80 + box.y < y < self.height - 80 + box.y + 24:
                            self.artist.mode = box.mode

                            # draw shadow on clicked item
                            self.buttonShadowSprite.x=box.x
                            self.buttonShadowSprite.y=box.y

                            found = True
                            break

    def on_mouse_motion(self, x, y, dx, dy):
        self.set_mouse_coordinates(x, y)
        self.update_pixel_cursor_position()
        if self.canvas.is_mouse_on_canvas(self.mousePos[0], self.mousePos[1]):
            self.update_coordinates_label()

    def on_mouse_release(self, x, y, button, modifiers):
        # apply preview layer to image layer
        self.apply_preview()

        # remove shadow from palette item
        self.paletteShadowSprite.x = 0
        self.paletteShadowSprite.y = 100

    def on_mouse_scroll(self, x, y, dx, dy):
        self.zoom(x, y, dy)
        self.update_zoom_percentage_label()

    def on_resize(self, width, height):
        self.resize_content(width, height)
    
    def resize_content(self, width, height):
        fx = width/self.lastWidth
        fy = height/self.lastHeight

        mouseX = 0.5
        mouseY = 0.5

        mouseXInWorld = self.left   + mouseX*self.zoomedWidth
        mouseYInWorld = self.bottom + mouseY*self.zoomedHeight

        self.zoomedWidth  *= fx
        self.zoomedHeight *= fy

        self.left   = mouseXInWorld - mouseX*self.zoomedWidth
        self.right  = mouseXInWorld + (1 - mouseX)*self.zoomedWidth
        self.bottom = mouseYInWorld - mouseY*self.zoomedHeight
        self.top    = mouseYInWorld + (1 - mouseY)*self.zoomedHeight

        # store last window values
        self.lastWidth = width
        self.lastHeight = height

        # resize toolbars to match new window size
        self.init_toolbar_backgrounds()

    def run(self):
        # start the window
        pyglet.app.run()

    def set_app_icon(self):
        self.icon = pyglet.image.load(const.APP_ICON_PATH)
        self.set_icon(self.icon)

    def set_color_display(self):
        # left color display
        self.paletteLeftColorImage = pyglet.image.SolidColorImagePattern(self.artist.primaryColor).create_image(24, 24)
        self.paletteLeftColorSprite = pyglet.sprite.Sprite(self.paletteLeftColorImage, x = 180, y = 22)

        # right color display
        self.paletteRightColorImage = pyglet.image.SolidColorImagePattern(self.artist.secondaryColor).create_image(24, 24)
        self.paletteRightColorSprite = pyglet.sprite.Sprite(self.paletteRightColorImage, x = 180 + 38, y = 22)

    def set_mouse_coordinates(self, x, y):
        # position of the mouse relative to window (0.0-1.0)
        mouseX = x/self.width
        mouseY = y/self.height

        # mouse position in world coordinates
        self.mousePos[0] = self.left   + mouseX*self.zoomedWidth
        self.mousePos[1] = self.bottom + mouseY*self.zoomedHeight

        # mouse position on canvas
        self.canvas.mousePos[0] = math.floor(self.mousePos[0] - const.WINDOW_START_WIDTH/2 + self.canvas.width/2)
        self.canvas.mousePos[1] = math.floor(self.mousePos[1] - const.WINDOW_START_HEIGHT/2 + self.canvas.height/2)

    def set_window_background_color(self):
        bg = const.WINDOW_BACKGROUND_COLOR
        gl.glClearColor(bg[0], bg[1], bg[2], bg[3])

    def update_coordinates_label(self):
        # set mouse coordinates label
        self.positionLabel = pyglet.text.Label(f"({self.canvas.mousePos[0]}, {self.canvas.mousePos[1]})",
                font_name=const.FONT_NAME,
                font_size=const.FONT_SIZE,
                x=self.width/2, y=0,
                anchor_x='center', anchor_y='bottom', bold=const.FONT_BOLD)

    def update_canvas_size_label(self):
        self.sizeLabel = pyglet.text.Label(f"{self.canvas.width} x {self.canvas.height} px",
                font_name=const.FONT_NAME,
                font_size=const.FONT_SIZE,
                x=self.width-4, y=0,
                anchor_x='right', anchor_y='bottom', bold=const.FONT_BOLD)

    def update_pixel_cursor_position(self):
        if self.canvas.is_mouse_on_canvas(self.mousePos[0], self.mousePos[1]):
            self.pixelCursorSprite = pyglet.sprite.Sprite(self.pixelCursorImage, x=self.canvas.origin[0]+self.canvas.mousePos[0],
                                                        y=self.canvas.origin[1]+self.canvas.mousePos[1])
        else:
            self.pixelCursorSprite = None

    def update_zoom_percentage_label(self):
        self.zoomLabel = pyglet.text.Label(f"{int(1/self.zoomLevel*100)}%",
            font_name=const.FONT_NAME,
            font_size=const.FONT_SIZE,
            x=4, y=0,
            anchor_x='left', anchor_y='bottom', bold=const.FONT_BOLD)

    def zoom(self, x, y, dy):
        # get scale factor based on which direction the scroll was
        factor = 1
        if dy < 0:
            factor = const.ZOOM_IN_FACTOR
        elif dy > 0:
            factor = const.ZOOM_OUT_FACTOR

        # if mouse is in main area
        if not y > self.height - 80 and not y < 20:
            # if zoomLevel is in the proper range
            if const.ZOOM_LIMIT_LOW <= self.zoomLevel * factor <= const.ZOOM_LIMIT_HIGH:
                # position of the mouse relative to window
                mouseX = x/self.width
                mouseY = y/self.height

                # mouse position in world coordinates
                mouseXInWorld = self.left   + mouseX*self.zoomedWidth
                mouseYInWorld = self.bottom + mouseY*self.zoomedHeight

                # ??? TODO: clean-up
                if dy > 0:
                    if  not (const.WINDOW_START_WIDTH/2 - self.canvas.width/2 < mouseXInWorld < const.WINDOW_START_WIDTH/2 \
                    + self.canvas.width/2 and const.WINDOW_START_HEIGHT/2 - self.canvas.height/2 < mouseYInWorld \
                    < const.WINDOW_START_HEIGHT/2 + self.canvas.height/2):
                        mouseXInWorld = const.WINDOW_START_WIDTH/2
                        mouseYInWorld = const.WINDOW_START_HEIGHT/2
                        mouseX = (mouseXInWorld - self.left)/self.zoomedWidth
                        mouseY = (mouseYInWorld - self.bottom)/self.zoomedHeight
                elif dy < 0:
                    if  not (const.WINDOW_START_WIDTH/2 - self.canvas.width/2 < mouseXInWorld < const.WINDOW_START_WIDTH/2 \
                    + self.canvas.width/2 and const.WINDOW_START_HEIGHT/2 - self.canvas.height/2 < mouseYInWorld \
                    < const.WINDOW_START_HEIGHT/2 + self.canvas.height/2):
                        mouseXInWorld = const.WINDOW_START_WIDTH/2
                        mouseYInWorld = const.WINDOW_START_HEIGHT/2
                        mouseX = (mouseXInWorld - self.left)/self.zoomedWidth
                        mouseY = (mouseYInWorld - self.bottom)/self.zoomedHeight

                # set zoom
                self.zoomLevel *= factor
                self.zoomedWidth  *= factor
                self.zoomedHeight *= factor

                self.left   = mouseXInWorld - mouseX*self.zoomedWidth
                self.right  = mouseXInWorld + (1 - mouseX)*self.zoomedWidth
                self.bottom = mouseYInWorld - mouseY*self.zoomedHeight
                self.top    = mouseYInWorld + (1 - mouseY)*self.zoomedHeight

if __name__ == "__main__":
    appArtist = Artist()
    appCanvas = Canvas(
        const.CANVAS_SIZE_X, const.CANVAS_SIZE_Y)
    appWindow = Window(
        const.WINDOW_START_WIDTH, const.WINDOW_START_HEIGHT, appCanvas, appArtist, resizable=True, caption=const.APP_NAME).run()
