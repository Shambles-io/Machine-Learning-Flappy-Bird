import os
import random
import time

import neat
import pygame
from gevent import config

pygame.font.init()

#Load in images and set screen dimension
WIN_WIDTH = 500
WIN_HEIGHT = 800

#GENERATIONS
GEN = 0

#transform.scale2x - command to make an image 2x bigger
#image.load - loads an image
BIRD_IMGS = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird1.png"))),
    pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird2.png"))),
    pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird3.png")))]
PIPE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "pipe.png")))
BASE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "base.png")))
BG_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bg.png")))

#Fonts
STAT_FONT = pygame.font.SysFont("comicsans", 50)

#Creating bird class
class Bird:
    #Making bird images easier to reference (using self.imgs)
    IMGS = BIRD_IMGS
    #How much the bird tilts when ascending/descending
    MAX_ROTATION = 25
    #How much we rotate on each frame, or how much we move the bird
    ROT_VEL = 20
    #How long we show each bird animation (Large vs small number reflects in speed of wings flapping)
    ANIMATION_TIME = 5

    def __init__(self, x, y):
        #Represents starting position of the bird
        self.x = x
        self.y = y
        #Each bird will have a tilt, this shows how much image is tilted, 
        # so we know how to draw it on the screen
        #Starts at 0 because game begins with bird looking flat across (Directly horizontal)
        self.tilt = 0
        #Use to aid in the physics of our bird while jumping/falling
        self.tick_count = 0
        #Velocity of bird - initialize at zero because it's not moving
        self.vel = 0
        #Height is equal to the y-location of the bird
        self.height = self.y
        #So we know which bird image we are currently showing - keeps track of which animation is shown
        self.img_count = 0
        #References BIRD_IMGS -> BIRD_IMGS[0] is bird1.png, and so on
        self.img = self.IMGS[0]
    
    #Defining the method to be called when we want the bird to jump (upwards)
    def jump(self):
        #Velocity is NEGATIVE because it is moving upward
        #Consider that our windows top-left corder is the (0,0) position, so downwards is POSITIVE
        #Might also help to consider gravity is a downwards force in this situation
        self.vel = -10.5
        #tick_count essentially keeps tract of when we last jumped
        #Reset backj to zero because we need to keep tract of when we are changing directions
        #  or velocities for our physics formulas to work
        self.tick_count = 0
        #Set height to keep track of where bird came from - where it originall started moving from
        self.height = self.y

    #Defining move method
    #We call move every single frame to move our bird
    def move(self):
        #Increments when a tick happens (frame passes)
        self.tick_count += 1

        #Displacement calculations - how many pixels we have moved up or down this frame
        #Note: Below is a kinematics position vs velocity equation (oh, the fun),
        # here, self.tick_count is used as a time variable
        # EX: (-10.5 * 1) + 1.5 * 1^2 => d = -9 (pixels upwards)
        d = self.vel*self.tick_count + 1.5*self.tick_count**2

        #Fail safe to ensure we don't have a velocity moving too far up or down
        #Essentially, d cannot exceed 16
        if d >= 16:
            d = 16

        #If we are moving upwards, let's just move up a little more
        #Better fine-tunes our jumping movement
        if d < 0:
            d -= 2

        #Changing y-position based on the displacement
        self.y = self.y + d

        #Actually tilting the bird
        #We do this inside move because when we determine whether we are moving
        # up or down, that also tells us if we are tilting up or down
        #Checking if we're tilting upwards -> d < 0 means moving up,
        # OR if birds current position is ABOVE the previous
        if (d < 0) or (self.y < self.height + 50):
            #Rather than slowly increment the bird tilt rotation, we just set the tilt to 25 (Degrees)
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION

        #Else: we are tilting the bird downwards
        else:
            if self.tilt > -90:
                #How much we are rotating the bird (downwards)
                #Note: here, we CAN rotate bird 90 (degrees),
                #  because as it moves down, it is a sense nose-dives to the ground
                self.tilt -= self.ROT_VEL

    #Draw Method
    #Note: win is the Window we are drawing the bird onto
    def draw(self, win):
        #To animate the bird, we must keep track of how many ticks we have shown a current image for
        #The tick refers to how many times our main game loop (while True loop) has run
        self.img_count += 1
        #Checking what image we should show, absed on the current image count (self.img_count)
        if self.img_count < self.ANIMATION_TIME:
            #If image count < 5 --> display first bird image
            self.img = self.IMGS[0]
        elif self.img_count < self.ANIMATION_TIME*2:
            #If image count < 10 --> display second bird image
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME*3:
            #If image count < 15 --> display last bird image
            self.img = self.IMGS[2]
        elif self.img_count < self.ANIMATION_TIME*4:
            #If image count < 20 --> display second bird image (again)
            self.img = self.IMGS[1]
        elif self.img_count == self.ANIMATION_TIME*4 + 1:
            #If image count = 21 --> display first bird image (again)
            self.img = self.IMGS[0]
            #Reset image count --> This gives us the flapping wings animation
            self.img_count = 0

        #When bird is tilted downwards, we do not want it to flat wings (changing image)
        if self.tilt <= -80:
            #When nose-diving down, we set the bird image to the (second) straight-wing image
            self.img = self.IMGS[1]
            #When we jump back up, it does not skip frame(s)
            self.img_count = self.ANIMATION_TIME*2

        #Drawing rotated image around its center
        #Note: This function will rotate an image, but by default the pivot point
        # is the top-left corner (of bird images)
        rotated_image = pygame.transform.rotate(self.img, self.tilt)
        #Making the birds pivot point at the center of bird
        new_rect = rotated_image.get_rect(center=self.img.get_rect(topleft = (self.x, self.y)).center)
        #Blit rotated image around new_rect (center pivot point)
        win.blit(rotated_image, new_rect.topleft)

    #Method for what is done when there is object collision(s)
    def get_mask(self):
        return pygame.mask.from_surface(self.img)


#Creating pipe class
class Pipe:
    #Defines how much space is between the top and bottom pipe(s)
    GAP = 200
    #Velocity of pipes moving towards bird
    VEL = 5

    def __init__(self, x):
        self.x = x
        self.height = 0

        self.top = 0
        self.bottom = 0
        #Pipe image is going up, so this flips it to have a downward-facing pipe 
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMG, False, True)
        self.PIPE_BOTTOM = PIPE_IMG

        #If the bird has already passed the pipe
        #Used for collision purposes
        self.passed = False
        #Defines where top and bottom of the pipe is AND where the gap is
        self.set_height()

    def set_height(self):
        #Get a random number (within defined range) for where the top of our pipe should be
        self.height = random.randrange(50, 450)
        #To find where the top of our pipe should be, we need to find the top-left corner of
        # the PIPE_TOP image
        self.top = self.height - self.PIPE_TOP.get_height()

        self.bottom = self.height + self.GAP

    def move(self):
        #To move pipes, we only have to change the x position (Left), based on the velocity that
        # the pipes should move (each frame)
        self.x -= self.VEL

    #Draws top and bottom of the pipe
    def draw(self, win):
        #Draws top pipe
        win.blit(self.PIPE_TOP, (self.x, self.top))
        #Draws bottome pipe
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

    #Collision method
    #We use a mask because that tells us where our actual image is (from the pixels) within an image box
    #Using a mask lets us tell if teh actual image pixels collide, instead of their boxes
    #The mask creates a 2D list of where within an image, the image ACTUALLY exists
    def collide(self, bird):
        #Gets mask of bird image
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)

        #Calculates offset - how far away the masks are from each other
        #Offset of bird from the top pipe (mask)
        top_offset = (self.x - bird.x, self.top - round(bird.y))
        #Offset of bird from the bottom pipe (mask)
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        #Calculating if masks collide - Finding point of collision
        #Note: If no collision detected, these return None
        #Point of collision (overlap) between bird mask and bottom pipe (using bottom offset)
        b_point = bird_mask.overlap(bottom_mask, bottom_offset)
        #Point of collision (overlap) between bird mask and top pipe (using top offset)
        t_point = bird_mask.overlap(top_mask, top_offset)

        #If either point returns non-None value, there was a collision
        if t_point or b_point:
            return True
        else:
            return False


#Creating Base class
class Base:
    VEL = 5
    WIDTH = BASE_IMG.get_width()
    IMG = BASE_IMG

    def __init__(self, y):
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):
        self.x1 -= self.VEL
        self.x2 -= self.VEL

        #Here, we have two sets of the base image (Next to each other)
        #As the game plays, they move across the screen at the same rate
        #As soon as the birst image completely exits the screen, it will
        # move behind the second base image. (Think of a conveyor belt) 
        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH

        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    #Drawing base image on the window
    def draw(self, win):
        win.blit(self.IMG, (self.x1, self.y))   
        win.blit(self.IMG, (self.x2, self.y))   


#Function to draw window for the game
def draw_window(win, birds, pipes, base, score, gen):
    #Draws background image (origine point is top-left corner of window)
    win.blit(BG_IMG, (0,0))
    #Draws pipe(s) - like this because they come in as a list
    for pipe in pipes:
        pipe.draw(win)
    #Draw score on window
    text = STAT_FONT.render("Score: " + str(score), 1, (255, 255, 255))
    #In top-right corner we display score. No matter how large score gets, the string will
    # shift to accommodate the score 
    win.blit(text, (WIN_WIDTH - 10 - text.get_width(), 10))
    #In top-right corner we display score. No matter how large score gets, the string will
    # shift to accommodate the score 
    win.blit(text, (10, 10))

    #draw base
    base.draw(win)
    #Draws bird(s) on the screen
    for bird in birds:
        bird.draw(win)

    #Updates display
    pygame.display.update()


#Main function --> Runs main loop of the game
def main(genomes, config):
    global GEN
    GEN += 1

    #Keep tract of bird that each neural network is controlling (position in the screen)
    nets = []

    #Keep track of genomes - Change fitness based on how far they move or pipe collisions
    ge = []

    #Create bird object - Starting position is (200, 200)
    #bird = Bird(230,350) - #Only for one bird
    birds = []

    #Setup a neural network (NN) for that genome and give it a bird to keep track of it in a list
    for _, g in genomes:
        #Setup genome NN
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        birds.append(Bird(230, 350))
        #Set initial fitness of our birds to be 0
        g.fitness = 0
        ge.append(g)
        

    #Create base object - Height set to 700 (Remember, 700 is towards the bottom of the screen)
    base = Base(730)
    #Create pipes(list) - Distance between set to 600
    pipes = [Pipe(600)]
    #Create pygame window
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    #Set the frame (tick) rate for while loop speed - want consistant rate
    clock = pygame.time.Clock()

    #Score variable
    score = 0

    #Main game (while) loop
    run = True
    while run:
        # At MOST, we do 30 ticks every second
        clock.tick(30)
        #PyGame event loop - Keeps track of in-hgame events (clicks, collisions, etc.)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                #User clickes red x (close window) , ren set to False, which quits the game
                run = False
                pygame.quit()
                #quit program
                quit()
                break

        #Moving the birds based on their NN
        pipe_ind = 0
        if len(birds) > 0:
            #If our bird(s) have passed the first pipe, then the next pipe is the second in our list
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                pipe_ind = 1
        else:
            #If all birds die, we want to quit game early
            run = False
            break

        for x, bird in enumerate(birds):
            bird.move()
            #Adding fitness to out bird - Encouraging it to move forward (and stay alive)
            ge[x].fitness += 0.1

            #Activate a NN with our input
            output = nets[x].activate((bird.y, abs(bird.y - pipes[pipe_ind].height), abs(bird.y - pipes[pipe_ind].bottom)))

            if output[0] > 0.5:
                bird.jump()


        #Function call for our bird to move every frame (Every tiem while loop iterates, the bird moves)
        #bird.move()
        #Initialize add_pipe variable
        add_pipe = False
        #Create a list of the removed pipe(s)
        rem = []
        #Function call to move our pipe object(s) across the screen
        for pipe in pipes:
            for x, bird in enumerate(birds):
                #Check (every) pipe collides with (every) bird
                if pipe.collide(bird):
                    #Every time a bird hits a pipe, its fitness score is subtracted by 1
                    #Encourages birds that can move BETWEEN pipes
                    ge[x].fitness-= 1
                    #Removing birds that collide with the pipe(s)
                    birds.pop(x)
                    nets.pop(x)
                    ge.pop(x)
            
                #Checks if birds have passed by the pipe
                if not pipe.passed and pipe.x < bird.x:
                    pipe.passed = True
                    add_pipe = True


            #Checks if pipe is completely off the screen, we remove that pipe
            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                #Adding the removed pipe to rem (removed) list
                rem.append(pipe)
            
            #Function call to move our pipe object(s) across the screen
            pipe.move()

        #Every time we successfully pass a pipe, score increases by 1
        if add_pipe:
            score += 1
            #Increasing fitness score of birds - Want to encourage tehm to make it THROUGH
            # the pipe - not the ones that just ram into the pipe (lolol)
            for g in ge:
                g.fitness += 5

            #Adding new pipe to the screen (with same x-position 700)
            pipes.append(Pipe(600))
        
        #Removing the pipes that were removed from the screen
        for r in rem:
            pipes.remove(r)
        
        #Check if the bird(s) have hit the ground OR jump too high (out of screen)
        for x, bird in enumerate(birds):
            if bird.y + bird.img.get_height() >= 730 or bird.y < 0:
                #Removing birds that hit the ground
                birds.pop(x)
                nets.pop(x)
                ge.pop(x)

        #Function call to move our base object(s) across the screen
        base.move()
        
        #Function call to draw our window and bird
        draw_window(win, birds, pipes, base, score, GEN)


def run(config_path):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
     neat.DefaultSpeciesSet, neat.DefaultStagnation, config_path)

    p = neat.Population(config)

    #Gives us detailed statistics of each generation
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    #How many generations we are going to run the fitness function
    #This calls the main function 50 times and passes it all of the Genomes,
    # as well as the configuration file every time
    winner = p.run(main, 50)

if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "config-feedforward.txt")
    run(config_path)
