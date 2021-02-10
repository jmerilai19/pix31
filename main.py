import pyglet
import pyglet.gl as gl
import math
import export
import palette

# Zooming constants
ZOOM_IN_FACTOR = 2
ZOOM_OUT_FACTOR = 1/ZOOM_IN_FACTOR

# Window start size
START_W = 960
START_H = 540

project = {
    "name": "Untitled"                              # Name of the project
}

canvas = {
    "origin": [0, 0],                               # Origin point of canvas in world coordinates
    "beginning_pos": (0, 0),                        # Beginning position for potential line draw
    "mouse_pos": (0, 0),                            # Mouse position on canvas
    "width": 64,                                    # Canvas width in pixels
    "height": 64,                                   # canvas height in pixels
    "background_color": (245, 245, 245, 255),       # Canvas background color
    "matrix": [],                                   # Matrix for color values of each pixel
    "batch_matrix": []                              # Matrix for drawable pixels
}

options = {
    "started": False,                               # Has the app started
    "mouse_pos": [0, 0],                            # Mouse position on window
    "primary_color":  (0, 0, 0, 255),               # Primary color (left)
    "secondary_color": (255, 255, 255, 255),        # Secondary color (right)
    "palette_colors": [],                           # Color values of the toolbar palette
    "draw_mode": 0,                                 # Draw mode number
    "grid_on": False,                               # Is grid on?
    "font": ["Arial", 11, False],                   # Default font
    "saved": False                                  # Has the image been saved?
}

class Window(pyglet.window.Window):
    def __init__(self, width, height, *args, **kwargs):
        super().__init__(width, height, *args, **kwargs)

        # Set app icon
        self.icon = pyglet.image.load("favicon.ico")
        self.set_icon(self.icon)

        # Set canvas origin point
        canvas["origin"][0] = self.width/2 - canvas["width"]/2
        canvas["origin"][1] = self.height/2 - canvas["width"]/2

        # Create blank canvas
        self.canvas_bg_image = pyglet.image.SolidColorImagePattern(
                    canvas["background_color"]).create_image(
                    canvas["width"],
                    canvas["height"])
        self.canvas_bg_sprite = pyglet.sprite.Sprite(self.canvas_bg_image, x=canvas["origin"][0],
                                                    y=canvas["origin"][1])

        self.pixel_cursor_image = pyglet.image.SolidColorImagePattern(
                    (0,0,0,96)).create_image(
                    1,
                    1)
        self.pixel_cursor_sprite = None

        # Initialize camera values
        self.left   = 0
        self.right  = width
        self.bottom = 0
        self.top    = height
        self.zoom_level = 1
        self.zoomed_width  = width
        self.zoomed_height = height

        # Initialize window values
        self.width  = width
        self.height = height
        self.last_width = 1
        self.last_height = 1

        # Initialize other values
        canvas["beginning_pos"] = None
        self.mouse_on_canvas = False

        # Create palette for toolbar
        self.create_palette()

    def on_resize(self, width, height):
        # Set window values
        self.width  = width
        self.height = height

        # Translate window content to match window resize
        if options["started"] == True:
            fx = self.width/self.last_width
            fy = self.height/self.last_height

            mouse_x = 0.5
            mouse_y = 0.5

            mouse_x_in_world = self.left   + mouse_x*self.zoomed_width
            mouse_y_in_world = self.bottom + mouse_y*self.zoomed_height

            self.zoomed_width  *= fx
            self.zoomed_height *= fy

            self.left   = mouse_x_in_world - mouse_x*self.zoomed_width
            self.right  = mouse_x_in_world + (1 - mouse_x)*self.zoomed_width
            self.bottom = mouse_y_in_world - mouse_y*self.zoomed_height
            self.top    = mouse_y_in_world + (1 - mouse_y)*self.zoomed_height
        else:
            options["started"] = True

        # Store last window values
        self.last_width = self.width
        self.last_height = self.height

        self.update_top_toolbar()

    def on_mouse_press(self, x, y, button, modifiers):
        # Position of the mouse relative to window
        mouse_x = x/self.width
        mouse_y = y/self.height

        # Mouse position in world coordinates
        mouse_x_in_world = self.left   + mouse_x*self.zoomed_width
        mouse_y_in_world = self.bottom + mouse_y*self.zoomed_height

        # If mouse is on canvas
        mouse_on_canvas = False

        x_coord = math.floor(mouse_x_in_world - START_W/2 + canvas["width"]/2)
        y_coord = canvas["height"] - 1 - math.floor(mouse_y_in_world - START_H/2 + canvas["height"]/2)

        if START_W/2 - canvas["width"]/2 < mouse_x_in_world < START_W/2 + canvas["width"]/2 \
        and START_H/2 - canvas["height"]/2 < mouse_y_in_world < START_H/2 + canvas["height"]/2:
            mouse_on_canvas = True

        # Left mouse button
        if button == pyglet.window.mouse.LEFT:
            # Top toolbar
            if y > self.height - 80:
                found = False
                for box in self.palette_colors:
                    if box.x < x < box.x + 16 and self.height - 80 + box.y < y < self.height - 80 + box.y + 16:
                        options["primary_color"] = box.color
                        self.update_top_toolbar()
                        found = True
                        break
                if found == False:
                    for box in self.mode_buttons:
                        if box.x < x < box.x + 24 and self.height - 80 + box.y < y < self.height - 80 + box.y + 24:
                            options["draw_mode"] = box.mode
                            self.update_top_toolbar()
                            found = True
                            break
            # Main area
            elif y > 20:
                # Pencil tool
                if options["draw_mode"] == 0:
                    canvas["beginning_pos"] = (x_coord, y_coord)
                    if mouse_on_canvas:
                        add_pixel((x_coord, y_coord), options["primary_color"])
                # Paint bucket tool
                elif options["draw_mode"] == 1:
                    if mouse_on_canvas:
                        flood_fill((x_coord, y_coord), options["primary_color"])
                # Eraser tool
                elif options["draw_mode"] == 2:
                    canvas["beginning_pos"] = (x_coord, y_coord)
                    if mouse_on_canvas:
                        erase_pixel((x_coord, y_coord))
                # Color picker
                elif options["draw_mode"] == 3:
                    color_pick((x_coord, y_coord), 0)
                    self.update_top_toolbar()
                # Line tool
                elif options["draw_mode"] == 4:
                    canvas["beginning_pos"] = (x_coord, y_coord)
                    if mouse_on_canvas:
                        add_pixel((x_coord, y_coord), options["primary_color"])
        # Right mouse button
        elif button == pyglet.window.mouse.RIGHT:
            # Top toolbar
            if y > self.height - 80:
                for box in self.palette_colors:
                    if box.x < x < box.x + 16 and self.height - 80 + box.y < y < self.height - 80 + box.y + 16:
                        options["secondary_color"] = box.color
                        self.update_top_toolbar()
                        break
            # Main area
            elif y > 20:
                # Pencil tool
                if options["draw_mode"] == 0:
                    canvas["beginning_pos"] = (x_coord, y_coord)
                    if mouse_on_canvas:
                        add_pixel((x_coord, y_coord), options["secondary_color"])
                # Paint bucket tool
                elif options["draw_mode"] == 1:
                    if mouse_on_canvas:
                        flood_fill((x_coord, y_coord), options["secondary_color"])
                # Color picker
                elif options["draw_mode"] == 3:
                    color_pick((x_coord, y_coord), 1)
                    self.update_top_toolbar()

    def on_mouse_release(self, x, y, button, modifiers):
        if button == pyglet.window.mouse.LEFT or button == pyglet.window.mouse.RIGHT:
            canvas["beginning_pos"] = None

    def on_mouse_drag(self, x, y, dx, dy, button, modifiers):
        coordinates_on_canvas(x, y, self)

        # Position of the mouse relative to window
        mouse_x = x/self.width
        mouse_y = y/self.height

        # Mouse position in world coordinates
        mouse_x_in_world = self.left   + mouse_x*self.zoomed_width
        mouse_y_in_world = self.bottom + mouse_y*self.zoomed_height

        x_coord = math.floor(mouse_x_in_world - START_W/2 + canvas["width"]/2)
        y_coord = canvas["height"] - 1 - math.floor(mouse_y_in_world - START_H/2 + canvas["height"]/2)

        # Middle mouse button
        if button == pyglet.window.mouse.MIDDLE:
            if not y > self.height - 80 and not y < 20:
                # Move camera
                if self.left - dx*self.zoom_level < START_W/2 and self.right - dx*self.zoom_level > START_W/2:
                    self.left   -= dx*self.zoom_level
                    self.right  -= dx*self.zoom_level

                if self.top - dy*self.zoom_level > START_H/2 + 80*self.zoom_level and \
                self.bottom - dy*self.zoom_level < START_H/2 - 20*self.zoom_level:
                    self.bottom -= dy*self.zoom_level
                    self.top    -= dy*self.zoom_level
        # Left mouse button
        elif button == pyglet.window.mouse.LEFT:
            if not canvas["beginning_pos"] == None:
                # Pencil tool
                if options["draw_mode"] == 0:
                    if abs(x_coord - canvas["beginning_pos"][0]) > 1 or abs(y_coord - canvas["beginning_pos"][1]) > 1:  # is the distance between positions > 1
                        draw_line(canvas["beginning_pos"], (x_coord, y_coord), 0, options["primary_color"])     # draw a line between positions
                    else:
                        add_pixel((x_coord, y_coord), options["primary_color"])
                    canvas["beginning_pos"] = (x_coord, y_coord)
                elif options["draw_mode"] == 2:
                    if abs(x_coord - canvas["beginning_pos"][0]) > 1 or abs(y_coord - canvas["beginning_pos"][1]) > 1:  # is the distance between positions > 1
                        draw_line(canvas["beginning_pos"], (x_coord, y_coord), 1)     # draw a line between positions
                    else:
                        erase_pixel((x_coord, y_coord))
                    canvas["beginning_pos"] = (x_coord, y_coord)
        # Right mouse button
        elif button == pyglet.window.mouse.RIGHT:
            if not canvas["beginning_pos"] == None:
                if options["draw_mode"] == 0:
                    if abs(x_coord - canvas["beginning_pos"][0]) > 1 or abs(y_coord - canvas["beginning_pos"][1]) > 1:  # is the distance between positions > 1
                        draw_line(canvas["beginning_pos"], (x_coord, y_coord), 0, options["secondary_color"])     # draw a line between positions
                    else:
                        add_pixel((x_coord, y_coord), options["secondary_color"])
                    canvas["beginning_pos"] = (x_coord, y_coord)

    def on_mouse_scroll(self, x, y, dx, dy):
        # Get scale factor
        f = 1
        if dy < 0:
            f = ZOOM_IN_FACTOR
        elif dy > 0:
            f = ZOOM_OUT_FACTOR
        else:
            f = 1

        # If mouse is in main area
        if not y > self.height - 80 and not y < 20:
            # If zoom_level is in the proper range
            if 0.03125 < self.zoom_level*f < 2:
                # Position of the mouse relative to window
                mouse_x = x/self.width
                mouse_y = y/self.height

                # Mouse position in world coordinates
                mouse_x_in_world = self.left   + mouse_x*self.zoomed_width
                mouse_y_in_world = self.bottom + mouse_y*self.zoomed_height

                if dy > 0:
                    if  not (START_W/2 - canvas["width"]/2 < mouse_x_in_world < START_W/2 + canvas["width"]/2 \
                    and START_H/2 - canvas["height"]/2 < mouse_y_in_world < START_H/2 + canvas["height"]/2):
                        mouse_x_in_world = START_W/2
                        mouse_y_in_world = START_H/2
                        mouse_x = (mouse_x_in_world - self.left)/self.zoomed_width
                        mouse_y = (mouse_y_in_world - self.bottom)/self.zoomed_height
                elif dy < 0:
                    if  not (START_W/2 - canvas["width"]/2 < mouse_x_in_world < START_W/2 + canvas["width"]/2 \
                    and START_H/2 - canvas["height"]/2 < mouse_y_in_world < START_H/2 + canvas["height"]/2):
                        mouse_x_in_world = START_W/2
                        mouse_y_in_world = START_H/2
                        mouse_x = (mouse_x_in_world - self.left)/self.zoomed_width
                        mouse_y = (mouse_y_in_world - self.bottom)/self.zoomed_height

                self.zoom_level *= f
                self.zoomed_width  *= f
                self.zoomed_height *= f

                self.left   = mouse_x_in_world - mouse_x*self.zoomed_width
                self.right  = mouse_x_in_world + (1 - mouse_x)*self.zoomed_width
                self.bottom = mouse_y_in_world - mouse_y*self.zoomed_height
                self.top    = mouse_y_in_world + (1 - mouse_y)*self.zoomed_height

    def on_key_press(self, symbol, modifiers):
        # Debug functionalities
        if symbol == pyglet.window.key._0:
            options["grid_on"] = not options["grid_on"]
        elif symbol == pyglet.window.key._1:
            options["draw_mode"] = 0
        elif symbol == pyglet.window.key._2:
            options["draw_mode"] = 1
        elif symbol == pyglet.window.key._3:
            options["draw_mode"] = 2
        elif symbol == pyglet.window.key._4:
            options["draw_mode"] = 3
        elif symbol == pyglet.window.key.Z:
            if pyglet.window.key.MOD_CTRL:
                if pyglet.window.key.MOD_SHIFT and modifiers == 3:
                    print("CTRL-SHIFT-Z", modifiers) #TODO REDO
                elif modifiers == 2:
                    print("CTRL-Z", modifiers) #TODO UNDO
        elif symbol == pyglet.window.key.S:
            if pyglet.window.key.MOD_CTRL and modifiers == 2:
                print("CTRL-S")
                export.export_image(canvas["matrix"], canvas["width"], canvas["height"])

    def on_draw(self):
        self.update_bottom_toolbar()

        # Main area:

        # Window background color
        gl.glClearColor(33/255, 33/255, 33/255, 1)

        # Set viewport
        gl.glViewport(0, 0, self.width, self.height)

        # Initialize Projection matrix
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()

        # Set orthographic projection matrix
        gl.gluOrtho2D(self.left, self.right, self.bottom, self.top)

        # Initialize Modelview matrix
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity()

        # Clear window with ClearColor
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

        # Draw blank canvas
        self.canvas_bg_sprite.draw()

        # Draw pixels
        if pixel_batch:
            pixel_batch.draw()

        # ???
        if holder_patch:
            holder_patch.draw()

        # Draw pixel cursor
        if not self.pixel_cursor_sprite == None:
            self.pixel_cursor_sprite.draw()

        # Draw grid lines
        if options["grid_on"] and self.zoom_level < 0.5:
            draw_grid(self.width, self.height)

        # Bottom toolbar:

        # Set viewport
        gl.glViewport(0, 0, self.width, 20)

        # Initialize Projection matrix
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()

        # Set orthographic projection matrix
        gl.gluOrtho2D(0, self.width, 0,20)

        # Initialize Modelview matrix
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity()

        # Draw bottom toolbar
        self.bottom_toolbar_bg_sprite.draw()
        self.size_label.draw()
        self.zoom_label.draw()
        if self.mouse_on_canvas:
            self.position_label.draw()

        # Top toolbar:

        # Set viewport
        gl.glViewport(0, self.height - 80, self.width, 80)

        # Initialize Projection matrix
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()

        # Set orthographic projection matrix
        gl.gluOrtho2D(0, self.width, 0, 80)

        # Initialize Modelview matrix
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity()

        # Draw background for top toolbar
        self.top_toolbar_bg_sprite.draw()

        # Draw top toolbar palette 
        top_toolbar_batch.draw()

        # Draw color selection displays
        self.palette_colorleft_sprite.draw()
        self.palette_colorright_sprite.draw()
        self.colorleft_label.draw()
        self.colorright_label.draw()

    def run(self):
        # Start the window
        pyglet.app.run()

    def on_mouse_motion(self, x, y, dx, dy):
        coordinates_on_canvas(x, y, self)

    def update_bottom_toolbar(self):
        # Background
        self.bottom_toolbar_bg_image = pyglet.image.SolidColorImagePattern((50,50,50,255)).create_image(self.width, 20)
        self.bottom_toolbar_bg_sprite = pyglet.sprite.Sprite(self.bottom_toolbar_bg_image, x=0, y=0)

        # Canvas size label
        self.size_label = pyglet.text.Label("{} x {} px".format(canvas["width"], canvas["height"]),
                font_name=options["font"][0],
                font_size=options["font"][1],
                x=self.width-4, y=0,
                anchor_x='right', anchor_y='bottom', bold=options["font"][2])

        # Zoom percentage label
        self.zoom_label = pyglet.text.Label("{}%".format(int(1/self.zoom_level*100)),
            font_name=options["font"][0],
            font_size=options["font"][1],
            x=4, y=0,
            anchor_x='left', anchor_y='bottom', bold=options["font"][2])

        # Mouse coordinates label
        self.position_label = pyglet.text.Label("({}, {})".format(canvas["mouse_pos"][0], canvas["mouse_pos"][1]),
                font_name=options["font"][0],
                font_size=options["font"][1],
                x=self.width/2, y=0,
                anchor_x='center', anchor_y='bottom', bold=options["font"][2])

    def update_top_toolbar(self):
        # Background
        self.top_toolbar_bg_image = pyglet.image.SolidColorImagePattern((50,50,50,255)).create_image(self.width, 80)
        self.top_toolbar_bg_sprite = pyglet.sprite.Sprite(self.top_toolbar_bg_image, x=0, y=0)

        # Left color display
        self.palette_colorleft_image = pyglet.image.SolidColorImagePattern(options["primary_color"]).create_image(24, 24)
        self.palette_colorleft_sprite = pyglet.sprite.Sprite(self.palette_colorleft_image, x = 960 - 304, y = 22)

        # Right color display
        self.palette_colorright_image = pyglet.image.SolidColorImagePattern(options["secondary_color"]).create_image(24, 24)
        self.palette_colorright_sprite = pyglet.sprite.Sprite(self.palette_colorright_image, x = 960 - 304 + 38, y = 22)

        self.mode_buttons = []
        cut = 4
        for i in range(0, 8):
            if i < cut:
                self.mode_buttons.append(Mode_button(i, 1, i))
            else:
                self.mode_buttons.append(Mode_button(i-cut, 0, i))

    def update_title(self):
        s = ""
        if options["saved"] == False:
            s = "*"
        self.caption = "{}{} - pix31".format(project["name"], s)
        
    def create_palette(self):
        x, y = self.width - 304, 0
        cut = 11                        # How many palette colors in one row

        # Left color label
        self.colorleft_label = pyglet.text.Label("Left:",
                font_name=options["font"][0],
                font_size=9,
                x=x, y=y+48,
                anchor_x='left', anchor_y='bottom', bold=options["font"][2], batch=top_toolbar_batch)

        # Right color label
        self.colorright_label = pyglet.text.Label("Right:",
                font_name=options["font"][0],
                font_size=9,
                x=x+35, y=y+48,
                anchor_x='left', anchor_y='bottom', bold=options["font"][2], batch=top_toolbar_batch)

        # Initialize palette
        self.palette_colors = []
        for index in range(0, 33):
            # First row
            if index < cut:
                xx = x + 76 + index*16 + index*4
                yy = y + 52
            else:
                # Second row
                if index < 2*cut:
                    xx = x + 76 + (index-cut)*16 + (index-cut)*4
                    yy = y + 32
                # Third row
                else:
                    xx = x + 76 + (index-2*cut)*16 + (index-2*cut)*4
                    yy = y + 12

            self.palette_colors.append(Palette_button(xx, yy, options["palette_colors"][index]))

class Palette_button():
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color

        self.image = pyglet.image.SolidColorImagePattern(self.color).create_image(16, 16)
        self.sprite = pyglet.sprite.Sprite(self.image, x=x, y=y, batch=top_toolbar_batch)

    def draw(self):
        self.sprite.draw()

class Mode_button():
    def __init__(self, x, y, mode = 0):
        self.x = 14 + x * 28
        self.y = 14 + y * 28
        self.mode = mode
        self.hover = False
        self.default_color = (128, 128, 128, 255)
        self.hover_color = (0, 0, 0, 255)
        self.color = self.default_color

        self.image = pyglet.image.SolidColorImagePattern(self.color).create_image(24, 24)
        self.sprite = pyglet.sprite.Sprite(self.image, x=self.x, y=self.y, batch=top_toolbar_batch)

    def draw(self):
        self.sprite.draw()

def color_pick(pos, button):
    """
    Sets the current color to the one that the clicked pixel is.
    """
    if not canvas["matrix"][pos[1]][pos[0]] == (0, 0, 0, 0):
        if button == 0:
            options["primary_color"] = canvas["matrix"][pos[1]][pos[0]]
        elif button == 1:
            options["secondary_color"] = canvas["matrix"][pos[1]][pos[0]]

def coordinates_on_canvas(x, y, self):
    options["mouse_pos"] = (x, y)
    # Position of the mouse relative to window
    mouse_x = x/self.width
    mouse_y = y/self.height

    # Mouse position in world coordinates
    mouse_x_in_world = self.left   + mouse_x*self.zoomed_width
    mouse_y_in_world = self.bottom + mouse_y*self.zoomed_height

    x_coord = math.floor(mouse_x_in_world - START_W/2 + canvas["width"]/2)
    y_coord = math.floor(mouse_y_in_world - START_H/2 + canvas["height"]/2)

    if 0 <= x_coord < canvas["width"] and 0 <= y_coord < canvas["height"]:
        canvas["mouse_pos"] = (x_coord, y_coord)
        self.mouse_on_canvas = True
        self.pixel_cursor_sprite = pyglet.sprite.Sprite(self.pixel_cursor_image, x=canvas["origin"][0]+x_coord,
                                            y=canvas["origin"][1]+y_coord)
    else:
        self.mouse_on_canvas = False
        self.pixel_cursor_sprite = None

    return x_coord, y_coord

def add_pixel(pos, color = (0, 0, 0, 255)):
    """
    Adds the pixel to the canvas matrix and calls a function to add the pixel to the batch.
    """
    if pos[0] >= 0 and pos[0] < canvas["width"]:                # check if x position inside canvas
        if pos[1] >= 0 and pos[1] < canvas["height"]:           # check if y position inside canvas
            add_pixel_to_batch(pos, color)
            canvas["matrix"][pos[1]][pos[0]] = color

def erase_pixel(pos):
    """
    Adds a transparent pixel to the canvas matrix and deletes the pixel from the batch.
    """
    if pos[0] >= 0 and pos[0] < canvas["width"]:                # check if x position inside canvas
        if pos[1] >= 0 and pos[1] < canvas["height"]:           # check if y position inside canvas
            canvas["matrix"][pos[1]][pos[0]] = (0, 0, 0, 0)
            if not canvas["batch_matrix"][pos[1]][pos[0]] == None:
                canvas["batch_matrix"][pos[1]][pos[0]].delete()
                canvas["batch_matrix"][pos[1]][pos[0]] = None

def flood_fill(pos, color):
    """
    The "paint bucket tool". Fills an area with color.
    """
    pos_list = []                                       # a list for possible fillable positions
    pos_list.append(pos)                                # add the clicked position to the list
    area_color = canvas["matrix"][pos[1]][pos[0]]       # check what the color, that will be recolored, is

    if not area_color == color:
        while pos_list:
            pixel = pos_list.pop()                      # take one position out of the list
            if canvas["matrix"][pixel[1]][pixel[0]] == area_color:
                add_pixel(pixel, color)

                # Check pixel from upside
                xx = pixel[0]
                yy = pixel[1] - 1
                if yy >= 0 and xx >= 0 and yy < len(canvas["matrix"]) and xx < len(canvas["matrix"][pixel[1]]):
                    if canvas["matrix"][yy][xx] == area_color :
                        pos_list.append((xx, yy))

                # Check pixel from downside
                yy = pixel[1] + 1
                if yy >= 0 and xx >= 0 and yy < len(canvas["matrix"]) and xx < len(canvas["matrix"][pixel[1]]):
                    if canvas["matrix"][yy][xx] == area_color:
                        pos_list.append((xx, yy))

                # Check pixel from left side
                xx = pixel[0] - 1
                yy = pixel[1]
                if yy >= 0 and xx >= 0 and yy < len(canvas["matrix"]) and xx < len(canvas["matrix"][pixel[1]]):
                    if canvas["matrix"][yy][xx] == area_color:
                        pos_list.append((xx, yy))

                # Check pixel from right side
                xx = pixel[0] + 1
                if yy >= 0 and xx >= 0 and yy < len(canvas["matrix"]) and xx < len(canvas["matrix"][pixel[1]]):
                    if canvas["matrix"][yy][xx] == area_color:
                        pos_list.append((xx, yy))

def add_pixel_to_batch(pos, color):
    """
    Adds a pixel to the batch in order to be drawn on screen
    """
    x = pos[0] + canvas["origin"][0]                            # convert pixel position to canvas position
    y = (canvas["height"] - pos[1]) + canvas["origin"][1]       # convert pixel position to canvas position
    if not canvas["batch_matrix"][pos[1]][pos[0]] == None:                              
        canvas["batch_matrix"][pos[1]][pos[0]].delete()                                 # delete pixel from batch before replacing it                 

    canvas["batch_matrix"][pos[1]][pos[0]] = pixel_batch.add(4, pyglet.gl.GL_QUADS, None,     # add a pixel to the batch
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

def draw_line(pos1, pos2, mode, color = (0, 0, 0, 0)):
    """
    Draws a line between two positions using Bresenham's line algorithm. 
    Mode tells if the line is a line of pixels (0) or a line of pixels to erase (1).
    """
    x0, y0 = pos1[0], pos1[1]
    x1, y1 = pos2[0], pos2[1]
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    x, y = x0, y0
    sx = -1 if x0 > x1 else 1
    sy = -1 if y0 > y1 else 1
    if dx > dy:
        err = dx / 2.0
        while x != x1:
            if mode == 0:
                add_pixel((x, y), color)
            elif mode == 1:
                erase_pixel((x, y))
            err -= dy
            if err < 0:
                y += sy
                err += dx
            x += sx
    else:
        err = dy / 2.0
        while y != y1:
            if mode == 0:
                add_pixel((x, y), color)
            elif mode == 1:
                erase_pixel((x, y))
            err -= dx
            if err < 0:
                x += sx
                err += dy
            y += sy
    if mode == 0:
        add_pixel((x, y), color)
    elif mode == 1:
        erase_pixel((x, y))

def setup():
    """
    Creates a matrix for the pixel grid and another for the batch items.
    Sets up all needed settings for canvas.
    """
    for y in range(0, canvas["height"]):
        canvas["matrix"].append([])
        canvas["batch_matrix"].append([])
        for _ in range(0, canvas["width"]):
            canvas["matrix"][y].append((0, 0, 0, 0))
            canvas["batch_matrix"][y].append(None)

    options["palette_colors"] = palette.read_hex_to_rgb("hexlist.hex")

def draw_grid(width, height):
    """
    Draws grid lines on canvas
    """
    # Draw vertical lines
    for x in range(0, canvas["width"] + 1):
        w = width / 2 - canvas["width"] / 2 + x
        pyglet.graphics.draw(4, pyglet.gl.GL_LINES, 
            ("v2f", (0, 0, 0, 0, 
                    w, 
                    height / 2 + canvas["height"] / 2, 
                    w, 
                    height / 2 - canvas["height"] / 2)),
            ('c3B', (128,128,128, 
                    128,128,128,
                    128,128,128, 
                    128,128,128)))

    # Draw horizontal lines
    for y in range(0, canvas["height"] + 1):
        h = height / 2 - canvas["height"] / 2 + y
        pyglet.graphics.draw(4, pyglet.gl.GL_LINES, 
            ("v2f", (0, 0, 0, 0,
            width / 2 - canvas["width"] / 2, 
            h,
            width / 2 + canvas["width"] / 2, 
            h)),
            ('c3B', (128,128,128, 
                    128,128,128,
                    128,128,128, 
                    128,128,128)))

if __name__ == "__main__":
    setup()
    holder_patch = pyglet.graphics.Batch()
    pixel_batch = pyglet.graphics.Batch()
    top_toolbar_batch = pyglet.graphics.Batch()

    Window(START_W, START_H, resizable=True, caption="pix31").run()