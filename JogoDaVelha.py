# -*- coding: utf-8 -*-
"""
Recriação do Jogo da Velha

@author: Prof. Daniel Cavalcanti Jeronymo
@author: Gabriel Santos Martinelli
"""

import pygame
    
import sys
import os
import traceback
import random
import numpy as np
import copy

class GameConstants:
    #                  R    G    B
    ColorWhite     = (255, 255, 255)
    ColorBlack     = (  0,   0,   0)
    ColorRed       = (255,   0,   0)
    ColorGreen     = (  0, 255,   0)
    ColorBlue     = (  0, 0,   255)
    ColorDarkGreen = (  0, 155,   0)
    ColorDarkGray  = ( 40,  40,  40)
    BackgroundColor = ColorBlack
    
    screenScale = 1
    screenWidth = screenScale*600
    screenHeight = screenScale*600
    
    # grid size in units
    gridWidth = 3
    gridHeight = 3
    
    # grid size in pixels
    gridMarginSize = 5
    gridCellWidth = screenWidth//gridWidth - 2*gridMarginSize
    gridCellHeight = screenHeight//gridHeight - 2*gridMarginSize
    
    randomSeed = 0
    
    FPS = 30
    
    fontSize = 20

class Game:
    class GameState:
        # 0 empty, 1 X, 2 O
        grid = np.zeros((GameConstants.gridHeight, GameConstants.gridWidth))
        currentPlayer = 0
    
    def __init__(self, expectUserInputs=True):
        self.expectUserInputs = expectUserInputs
        
        # Game state list - stores a state for each time step (initial state)
        gs = Game.GameState()
        self.states = [gs]
        
        # Determines if simulation is active or not
        self.alive = True
        
        self.currentPlayer = 1
        
        # Journal of inputs by users (stack)
        self.eventJournal = []
        
        
    def checkObjectiveState(self, gs):
        # Complete line?
        for i in range(3):
            s = set(gs.grid[i, :])
            if len(s) == 1 and min(s) != 0:
                return s.pop()
            
        # Complete column?
        for i in range(3):
            s = set(gs.grid[:, i])
            if len(s) == 1 and min(s) != 0:
                return s.pop()
            
        # Complete diagonal (main)?
        s = set([gs.grid[i, i] for i in range(3)])
        if len(s) == 1 and min(s) != 0:
            return s.pop()
        
        # Complete diagonal (opposite)?
        s = set([gs.grid[-i-1, i] for i in range(3)])
        if len(s) == 1 and min(s) != 0:
            return s.pop()
            
        # nope, not an objective state
        return 0
    
    
    # Implements a game tick
    # Each call simulates a world step
    def update(self):  

        global root
        global player
        # If the game is done or there is no event, do nothing
        if not self.alive or not self.eventJournal:
            return
        
        # Get the current (last) game state
        gs = copy.copy(self.states[-1])
        
        # Switch player turn
        if gs.currentPlayer == 0:
            gs.currentPlayer = 1
        elif gs.currentPlayer == 1:
            gs.currentPlayer = 2
        elif gs.currentPlayer == 2:
            gs.currentPlayer = 1
            
        # Mark the cell clicked by this player if it's an empty cell
        x,y = self.eventJournal.pop()

        # Check if in bounds
        if x < 0 or y < 0 or x >= GameConstants.gridCellHeight or y >= GameConstants.gridCellHeight:
            return

        # Check if cell is empty
        if gs.grid[x][y] == 0 or gs.grid[x][y] == 3:
            gs.grid[x][y] = gs.currentPlayer
            for i in range (GameConstants.gridHeight):
                for j in range (GameConstants.gridWidth):
                    #check if cell is colored in green and clean it
                    if gs.grid[i][j] == 3:
                        gs.grid[i][j] = 0
            #search node that corresponds to the current state of the game
            root = searchNode(root, (gs.currentPlayer, 3*x+y))
            if gs.currentPlayer == 3 - player:
                Oracle(self, player, root)
        else: # invalid move
            return
        
        # Check if end of game
        if self.checkObjectiveState(gs):
            self.alive = False
                
        # Add the new modified state
        self.states += [gs]

def drawGrid(screen, game):
    rects = []

    rects = [screen.fill(GameConstants.BackgroundColor)]
    
    # Get the current game state
    gs = game.states[-1]
    grid = gs.grid
 
    # Draw the grid
    for row in range(GameConstants.gridHeight):
        for column in range(GameConstants.gridWidth):
            color = GameConstants.ColorWhite
            
            if grid[row][column] == 1:
                color = GameConstants.ColorRed
            elif grid[row][column] == 2:
                color = GameConstants.ColorBlue
            elif grid[row][column] == 3:
                color = GameConstants.ColorGreen
            
            m = GameConstants.gridMarginSize
            w = GameConstants.gridCellWidth
            h = GameConstants.gridCellHeight
            rects += [pygame.draw.rect(screen, color, [(2*m+w) * column + m, (2*m+h) * row + m, w, h])]    
    
    return rects

def draw(screen, font, game):
    rects = []
            
    rects += drawGrid(screen, game)

    return rects

def initialize():
    random.seed(GameConstants.randomSeed)
    pygame.init()
    game = Game()
    font = pygame.font.SysFont('Courier', GameConstants.fontSize)
    fpsClock = pygame.time.Clock()

    # Create display surface
    screen = pygame.display.set_mode((GameConstants.screenWidth, GameConstants.screenHeight), pygame.DOUBLEBUF)
    screen.fill(GameConstants.BackgroundColor)
        
    return screen, font, game, fpsClock

def handleEvents(game):
    #gs = game.states[-1]
    
    for event in pygame.event.get():
        if event.type == pygame.MOUSEBUTTONUP:
            pos = pygame.mouse.get_pos()
            
            col = pos[0] // (GameConstants.screenWidth // GameConstants.gridWidth)
            row = pos[1] // (GameConstants.screenHeight // GameConstants.gridHeight)
            #print('clicked cell: {}, {}'.format(cellX, cellY))
            
            # send player action to game
            game.eventJournal.append((row, col))
            
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            pygame.quit()
            sys.exit()

class Node:
    def __init__(self, state=None, move=None, value=0):
        self.state = state  # State of the game for this node
        self.move = move    # Move done to reach this state
        self.value = value  # Value that represents who won the game (if not over yet then value = 0)
        self.children = []  # children of the current node

def checkWinOrLoss(state):

    # Complete line?
    for i in range(0, 9, 3):
        if state[i] == state[i+1] == state[i+2] != 0:
            return state[i]
        
    # Complete column?
    for i in range(0, 3):
        if state[i] == state[i+3] == state[i+6] != 0:
            return state[i]
        
    # Complete diagonal (main)?
    if state[0] == state[4] == state[8] != 0:
        return state[0]
    
    # Complete diagonal (opposite)?
    if state[2] == state[4] == state[6] != 0:
        return state[2]
        
    # nope, not an objective state
    return 0

def checkDraw(state):

    if checkWinOrLoss(state) != 0:
        return False

    for position in state:
        if position == 0:
            return False
        
    return True
    
def NextStates(root, depth):

    if checkWinOrLoss(root.state) != 0 or depth == 0:
        return root

    for position in range(0,9):
        if root.state[position] == 0 and checkWinOrLoss(root.state) == 0:

            # switch the current player
            if root.move[0] == 0:
                player = 1
            elif root.move[0] == 1:
                player = 2
            elif root.move[0] == 2:
                player = 1

            current_state = list(root.state)

            current_state[position] = player
        
            child = Node(tuple(current_state), (player, position))

            # check if player won or not after the move
            outcome = checkWinOrLoss(child.state)
            if outcome == 1:
                child.value = 1
            elif outcome == 2:
                child.value = -1
            else:
                child.value = 0

            root.children.append(child)

    for index, child in enumerate(root.children):
        root.children[index] = NextStates(root.children[index], depth-1)

    return root

def Oracle(game, player, root):

    global depth

    def minimax(player, root, depth):

        if root == None:
            return(0, None)
        if checkWinOrLoss(root.state) == 1:
            return (1, root.move)
        elif checkWinOrLoss(root.state) == -1:
            return (-1, root.move)
        if checkDraw(root.state) == True:
            return (0, root.move)
        if depth == 0:
            return(0, root.move)
        
        best_move = None

        if player == 1:
            best_value = -2
            for child in root.children:
                value = minimax(2, child, depth-1)[0]
                if value > best_value:
                    best_value = value
                    best_move = child.move
        elif player == 2:
            best_value = 2
            for child in root.children:
                value = minimax(1, child, depth-1)[0]
                if value < best_value:
                    best_value = value
                    best_move = child.move

        return (best_value, best_move)
    
    best_move = minimax(player, root, depth)[1]

    if best_move is not None:
        row = best_move[1]//3
        column = best_move[1]%3
        if game.states[-1].grid[row][column] == 0:
            game.states[-1].grid[row][column] = 3

def searchNode(root, move):
    if root == None:
        return None
    for index, child in enumerate(root.children):
        if child.move == move:
            return root.children[index]

def mainGamePlayer():
    try:
        # Initialize pygame and etc.
        screen, font, game, fpsClock = initialize()

        global root
        global player
        if game.currentPlayer == player:
            Oracle(game, player, root)
              
        # Main game loop
        while game.alive:
            # Handle events
            handleEvents(game)
                    
            # Update world
            game.update()
            
            # Draw this world frame
            rects = draw(screen, font, game)     
            pygame.display.update(rects)
            
            # Delay for required FPS
            fpsClock.tick(GameConstants.FPS)
            
        # close up shop
        pygame.quit()
    except SystemExit:
        pass
    except Exception as e:
        #print("Unexpected error:", sys.exc_info()[0])
        traceback.print_exc(file=sys.stdout)
        pygame.quit()
        #raise Exception from e

#Set the player whose moves you want to predict
player = 2

# Set the depth of minimax here
depth = 9

# Creates the tree with all game possibilities here (you can choose the depth of the tree, it's the second parameter)
root = Node((0,0,0,0,0,0,0,0,0), (0,0))
root = NextStates(root, 9)

if __name__ == "__main__":
    # Set the working directory (where we expect to find files) to the same
    # directory this .py file is in. You can leave this out of your own
    # code, but it is needed to easily run the examples using "python -m"
    file_path = os.path.dirname(os.path.abspath(__file__))
    os.chdir(file_path)

    game = Game()

    mainGamePlayer()