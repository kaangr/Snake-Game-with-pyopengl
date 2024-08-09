import sys
import random
import pygame
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from PIL import Image  # Added the PIL library

# Global variables
window_width, window_height = 1000, 1000   # Specifies the width and height of the game window in pixels.
map_size = 20                              # Specifies the size of the game map.
cell_size = 1                              # Specifies the size of each cell.
snake = [(5, 5)]                           # A list that holds the positions of the snake. Each cell of the snake is represented as a coordinate pair (x, y). Initially set to [(5, 5)].
snake_dir = (1, 0)                         # Specifies the direction of the snake's movement. (Initially moving to the right)
game_over = False                          # A flag indicating whether the game is over
angle = -20                                # Adjusts the angle of the surface the snake is navigating
speed = 130                                # Sets the speed of the snake (in milliseconds)
button_pos = (-0.32, -0.5, 0.4, -0.3)      # Specifies the position of the "RESTART" button. (x1, y1, x2, y2)
main_window = None                         # Variable defining the main game window.
game_over_window = None                    # Variable defining the game over window.
score = 0                                  # Variable to hold the player's score

# Positions of apples (initially random positions) (Generates numbers between 0 and 19. Since map_size = 20, this separates the edges of the map)
red_apple = (random.randint(0, map_size-1), random.randint(0, map_size-1))
bomb_apples = [(random.randint(0, map_size-1), random.randint(0, map_size-1)) for _ in range(4)]
diamond_apple = (random.randint(0, map_size-1), random.randint(0, map_size-1))
stone_apple = (random.randint(0, map_size-1), random.randint(0, map_size-1))
gold_apple = (random.randint(0, map_size-1), random.randint(0, map_size-1))

# Textures for the apples
snake_tail_texture = None
snake_head_texture = None
red_texture = None
bomb_texture = None
diamond_texture = None
stone_texture = None
gold_texture = None

# Timers for the apples, duration in milliseconds
diamond_apple_timeout = 6000
stone_apple_timeout = 6000
bomb_apple_timeout = 10000

# Load PNG file as texture
"""
    This function loads an image using the given filename, 
    flips it, converts it to a byte array, and sets it as a texture using OpenGL. 
    These operations are necessary for using 2D textures in graphics applications or games.
""" 
def load_texture(filename):
    try:
        image = Image.open(filename)                            # Opens the image file using Pillow library.
        flipped_image = image.transpose(Image.FLIP_TOP_BOTTOM)  # Flips the image along the horizontal axis. This is necessary because OpenGL may interpret image corner coordinates differently.
        ix = flipped_image.size[0]                              # Gets the width of the image (ix)
        iy = flipped_image.size[1]                              # Gets the height of the image (iy)
        image = flipped_image.tobytes("raw", "RGB")             # Converts the image to a byte array.
        glClearColor(0.0, 0.0, 0.0, 0.0)                       # Sets the background color (black)

        texture_id = glGenTextures(1)                           # Generates a new texture ID.
        glBindTexture(GL_TEXTURE_2D, texture_id)                # Binds this ID as the current texture
        # Sets texture parameters
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)                        # Specifies how the texture wraps in the horizontal (S) direction. GL_REPEAT causes the texture to repeat.
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)                        # Specifies how the texture wraps in the vertical (T) direction
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)                    # Filtering for texture magnification, GL_LINEAR provides smoother images through linear interpolation.
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)                    # Filtering for texture minification
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, ix, iy, 0, GL_RGB, GL_UNSIGNED_BYTE, image)  # glTexImage2D function loads the texture data into OpenGL.
        glEnable(GL_TEXTURE_2D)                                                             # Enables 2D texturing.
        return texture_id
    except IOError as e:
        print(f"Error loading texture: {e}")
        return -1

# The part where textures for everything in the game are set. Uses the load_texture function.
def load_textures():
    global red_texture, bomb_texture, diamond_texture, stone_texture, gold_texture, snake_head_texture, snake_tail_texture
    red_texture = load_texture("apple.png")
    bomb_texture = load_texture("bomb.jpg")
    diamond_texture = load_texture("diamond_apple.png")
    stone_texture = load_texture("stone_apple.png")
    gold_texture = load_texture("gold_apple.jpg")
    snake_head_texture = load_texture("snake1.jpeg")
    snake_tail_texture = load_texture("snake.JPG")

    # Print error messages if textures could not be loaded
    if red_texture == -1 or bomb_texture == -1 or diamond_texture == -1 or stone_texture == -1 or gold_texture == -1:
        print("Texture loading failed. Check if the files exist and are in the correct format.")
  
# Sound effects are loaded using the pygame library.
def load_sounds():
    global eat_sound, bomb_sound, stone_sound, game_over_sound
    pygame.mixer.init()
    eat_sound = pygame.mixer.Sound("eat.wav")
    bomb_sound = pygame.mixer.Sound("bomb_sound.wav")
    stone_sound = pygame.mixer.Sound("stone_sound.wav")
    game_over_sound = pygame.mixer.Sound("game_over_sound.wav")

# Initializes OpenGL
def init():
    glEnable(GL_DEPTH_TEST)                                     # Enables depth testing in 3D objects
    glEnable(GL_LIGHTING)                                       # Enables lighting
    glEnable(GL_LIGHT0)                                         # Adds a light source
    glEnable(GL_COLOR_MATERIAL)                                 # Sets the colors of the objects according to the lighting
    glColorMaterial(GL_FRONT, GL_AMBIENT_AND_DIFFUSE)           # Defines material color properties.
    # GL_FRONT specifies that the color properties are valid only for the front faces.
    # GL_AMBIENT_AND_DIFFUSE indicates that the material color will be affected by ambient and diffuse light components.
    glShadeModel(GL_SMOOTH)                                     # Sets the shading model.
    # GL_SMOOTH provides smooth color transitions between edges
    gluPerspective(55, window_width / window_height, 1, 100)    # Defines the perspective projection matrix.
    glTranslatef(-map_size / 2, -map_size / 2, -map_size * 1.09)  # Translates the model view matrix along a vector.
    # -map_size * 1.09 is the amount of translation along the z-axis. This places the scene at a specific distance from the viewer, making the entire scene visible.
    
# Draws the grid on the game surface
"""
This function draws a grid of a certain size depending on the map_size variable. 
This grid is often used as a reference point for a game or 3D scene. 
Each line of the grid is drawn in white color and is placed on the ground (z = 0).
"""
def draw_grid():
    glColor3f(1.0, 1.0, 1.0)         # Sets the color for the next drawing operations
    glBegin(GL_LINES)                # Starts drawing mode.GL_LINES draws a straight line between two points
    for x in range(map_size + 1):    # Used to draw vertical lines on the x-axis.
        glVertex3f(x, 0, 0)          # Sets the starting point of the line.
        glVertex3f(x, map_size, 0)   # Sets the ending point of the line.
    for y in range(map_size + 1):    # Used to draw vertical lines on the y-axis.
        glVertex3f(0, y, 0)
        glVertex3f(map_size, y, 0)
    glEnd()

# Draws a cube with the given position and texture (the map is made up of 20x20 squares. Each cube fits into one square.)
def draw_cube(position, texture_id):
    x, y = position
    glBindTexture(GL_TEXTURE_2D, texture_id)   # Specifies the texture to be used

    half_depth = -0.5                          # Half depth of the cube

    # Front face
    glBegin(GL_QUADS)                          # Starts drawing mode
    glTexCoord2f(0, 0)                         # Specifies which part of the texture will be used
    glVertex3f(x, y, -half_depth)              # Sets the coordinates for a vertex.
    glTexCoord2f(1, 0)
    glVertex3f(x + 1, y,

 -half_depth)
    glTexCoord2f(1, 1)
    glVertex3f(x + 1, y + 1, -half_depth)
    glTexCoord2f(0, 1)
    glVertex3f(x, y + 1, -half_depth)

    # Back face
    glTexCoord2f(0, 0)
    glVertex3f(x, y, half_depth)
    glTexCoord2f(1, 0)
    glVertex3f(x + 1, y, half_depth)
    glTexCoord2f(1, 1)
    glVertex3f(x + 1, y + 1, half_depth)
    glTexCoord2f(0, 1)
    glVertex3f(x, y + 1, half_depth)

    # Left face
    glTexCoord2f(0, 0)
    glVertex3f(x, y, half_depth)
    glTexCoord2f(1, 0)
    glVertex3f(x, y, -half_depth)
    glTexCoord2f(1, 1)
    glVertex3f(x, y + 1, -half_depth)
    glTexCoord2f(0, 1)
    glVertex3f(x, y + 1, half_depth)

    # Right face
    glTexCoord2f(0, 0)
    glVertex3f(x + 1, y, half_depth)
    glTexCoord2f(1, 0)
    glVertex3f(x + 1, y, -half_depth)
    glTexCoord2f(1, 1)
    glVertex3f(x + 1, y + 1, -half_depth)
    glTexCoord2f(0, 1)
    glVertex3f(x + 1, y + 1, half_depth)

    # Top face
    glTexCoord2f(0, 0)
    glVertex3f(x, y + 1, -half_depth)
    glTexCoord2f(1, 0)
    glVertex3f(x + 1, y + 1, -half_depth)
    glTexCoord2f(1, 1)
    glVertex3f(x + 1, y + 1, half_depth)
    glTexCoord2f(0, 1)
    glVertex3f(x, y + 1, half_depth)

    # Bottom face
    glTexCoord2f(0, 0)
    glVertex3f(x, y, -half_depth)
    glTexCoord2f(1, 0)
    glVertex3f(x + 1, y, -half_depth)
    glTexCoord2f(1, 1)
    glVertex3f(x + 1, y, half_depth)
    glTexCoord2f(0, 1)
    glVertex3f(x, y, half_depth)
    glEnd()

# Draws the snake with its head and body
"""
Draws the snake on the grid based on the positions of its segments. 
The head of the snake is drawn separately from the body, 
and the body segments are drawn one by one.
"""
def draw_snake():
    for i, segment in enumerate(snake):
        if i == 0:  # Draw the head of the snake
            glBindTexture(GL_TEXTURE_2D, snake_head_texture)
        else:  # Draw the body of the snake
            glBindTexture(GL_TEXTURE_2D, snake_tail_texture)
        draw_cube(segment, glGetIntegerv(GL_TEXTURE_BINDING_2D))

# Draws different types of apples using their textures
def draw_red_apple():
    glBindTexture(GL_TEXTURE_2D, red_texture)   # Sets the texture to be used for the red apple
    draw_cube(red_apple, red_texture)

def draw_bomb_apples():
    glBindTexture(GL_TEXTURE_2D, bomb_texture)  # Sets the texture to be used for the bomb apple
    for pos in bomb_apples:
        draw_cube(pos, bomb_texture)

def draw_diamond_apple():
    glBindTexture(GL_TEXTURE_2D, diamond_texture)  # Sets the texture to be used for the diamond apple
    draw_cube(diamond_apple, diamond_texture)

def draw_stone_apple():
    glBindTexture(GL_TEXTURE_2D, stone_texture)  # Sets the texture to be used for the stone apple
    draw_cube(stone_apple, stone_texture)

def draw_gold_apple():
    glBindTexture(GL_TEXTURE_2D, gold_texture)  # Sets the texture to be used for the gold apple
    draw_cube(gold_apple, gold_texture)

# Displays the game over screen
def show_game_over_window():
    global game_over_window
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)  # Clears the screen.
    glLoadIdentity()                                    # Loads the identity matrix.
    # Draws a message indicating that the game is over
    glColor3f(1.0, 0.0, 0.0)                           # Sets the color to red
    glRasterPos2f(-0.3, 0)                            # Sets the position for the text
    for c in "GAME OVER":                             # Draws the text character by character
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(c))
    glFlush()

# Handles the snake's movement and updates the game state
def move_snake():
    # Moves the snake based on the current direction
    # Checks for collisions and handles eating apples (not fully provided in the snippet)
    pass

# Handles user input
def special_input(key, x, y):
    global snake_dir
    if key == GLUT_KEY_UP and snake_dir != (0, -1):
        snake_dir = (0, 1)
    elif key == GLUT_KEY_DOWN and snake_dir != (0, 1):
        snake_dir = (0, -1)
    elif key == GLUT_KEY_LEFT and snake_dir != (1, 0):
        snake_dir = (-1, 0)
    elif key == GLUT_KEY_RIGHT and snake_dir != (-1, 0):
        snake_dir = (1, 0)

# Handles keyboard inputs
def keyboard(key, x, y):
    global game_over
    if key == b'q':  # Quit the game
        sys.exit()
    elif key == b'r' and game_over:
        restart_game()

# Updates timers for special apples
def update_apple_timers():
    global diamond_apple_timeout, stone_apple_timeout, bomb_apple_timeout
    if diamond_apple_timeout > 0:
        diamond_apple_timeout -= speed
    if stone_apple_timeout > 0:
        stone_apple_timeout -= speed
    if bomb_apple_timeout > 0:
        bomb_apple_timeout -= speed

# Restart the game
def restart_game():
    global snake, snake_dir, red_apple, bomb_apples, diamond_apple, stone_apple, gold_apple, score, game_over
    snake = [(5, 5)]
    snake_dir = (1, 0)
    red_apple = (random.randint(0, map_size-1), random.randint(0, map_size-1))
    bomb_apples = [(random.randint(0, map_size-1), random.randint(0, map_size-1)) for _ in range(4)]
    diamond_apple = (random.randint(0, map_size-1), random.randint(0, map_size-1))
    stone_apple = (random.randint(0, map_size-1), random.randint(0, map_size-1))
    gold_apple = (random.randint(0, map_size-1), random.randint(0, map_size-1))
    score = 0
    game_over = False

# The main loop of the game
def timer(value):
    global game_over
    if not game_over:
        move_snake()
        update_apple_timers()
        glutPostRedisplay()  # Triggers a redraw of the screen
        glutTimerFunc(speed, timer, 0)  # Calls the timer function repeatedly

# Main function to initialize the game
def main():
    global main_window
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(window_width, window_height)
    glutInitWindowPosition(100, 100)
    main_window = glutCreateWindow("Snake Game")
    init()
    load_textures()
    load_sounds()
    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutSpecialFunc(special_input)
    glutKeyboardFunc(keyboard)
    glutTimerFunc(speed, timer, 0)
    glutMainLoop()

if __name__ == "__main__":
    main()
