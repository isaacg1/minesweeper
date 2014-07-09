# Minesweeper solver
# Class just contains partially revealed boards that all look the same
# from the outside

# This is a branch, that uses strings.

# Boards have every cell revealed.
# Revealed is partially revealed. Boards must match revealed on every
# cell that is revealed.

# Meanings:
# '0'-'8': Safe square with that # of surrounding mines
# '*'    : Mine
# '_'    : Unrevealed
import copy
import itertools
import time
import pickle
import random
import math
import cProfile
import sys

class Position:
    def __init__(self, dimensions, revealed, boards):
        self.dim_r,self.dim_c=dimensions
        self.rev=revealed
        self.boards=boards
        assert len(revealed)==self.dim_r*self.dim_c
    
    def click(self,loc):
        # Takes a location, returns all possible revealed positions, with boards
        # split up accordingly
        try:
            assert self.rev[loc]=='_'
        except AssertionError:
            print(self,loc,self.rev)
            assert self.rev[loc]=='_'
        # Create all possible new boards, split up by revealed item.
        board_dict={}
        for board in self.boards:
            clicked_cell=board[loc]
            if clicked_cell in board_dict:
                board_dict[clicked_cell].append(board)
            else:
                board_dict[clicked_cell]=[board]
        new_positions=[]            
        for rev_cell in board_dict.keys():
            # Make the new board withot copying
            new_rev=''.join([self.rev[:loc],rev_cell,self.rev[loc+1:]])
            new_pos=Position((self.dim_r,self.dim_c),new_rev,board_dict[rev_cell])
            new_positions.append(new_pos)
        return new_positions
        
    def someBestClick(self):
        click_list=[]
        # Set of boards is all we know when outputting, may be smaller than
        # complete set
        # If we've clicked on a bomb, no way to win, no best click.
        if '*' in self.rev:
            return 0,[]
        unrevealed = [loc for loc in range(len(self.rev)) if self.rev[loc]=='_']
        # If there is only 1 possible board, you're done. The click list is every
        # unrevealed square on the board without a bomb under it.
        if len(self.boards)==1:
            return 1,[loc for loc in unrevealed if self.boards[0][loc]!='*']
        
        # If there is an unrevaled locaiton on the board that is bomb free in
        # every sub-board, use it.
        for loc in unrevealed:
            if all(board[loc]!='*' for board in self.boards):
                return sum(pos.memoBestClick()[0] for pos in self.click(loc)),[loc]

        # The broadest test - try everywhere.
        click_list=[]
        most_wins=0
        for loc in unrevealed:
            wins=sum(pos.memoBestClick()[0] for pos in self.click(loc) if pos.rev[loc]!='*')
            if wins>=most_wins:
                if wins>most_wins:
                    click_list=[]
                    most_wins=wins
                click_list.append(loc)
        return most_wins,click_list
        
    def memoBestClick(self):
        global memo
        global memo_counter
        memo_counter +=1
        if not self.rev in memo:
            # These lines check for mirror images of the board being in the memo table
            
            vert_reversed_memo_str=                                         \
            ''.join([self.rev[y*self.dim_c:(y+1)*self.dim_c]
                     for y in range(self.dim_r)][::-1])
            
            if vert_reversed_memo_str in memo:
                vert_reversed_output=memo[vert_reversed_memo_str]
                return vert_reversed_output[0],                             \
                        [(self.dim_r-1-loc//self.dim_c)*self.dim_c+loc%self.dim_c
                         for loc in vert_reversed_output[1]]
            
            horiz_reversed_memo_str=                                        \
            ''.join(self.rev[y*self.dim_c:(y+1)*self.dim_c][::-1]
                    for y in range(self.dim_r))
            
            if horiz_reversed_memo_str in memo:
                horiz_reversed_output=memo[horiz_reversed_memo_str]
                return horiz_reversed_output[0],                            \
                        [(loc//self.dim_c)*self.dim_c+
                         (self.dim_c-1-(loc%self.dim_c))
                         for loc in horiz_reversed_output[1]]
            
            both_reversed_memo_str=self.rev[::-1]
            if both_reversed_memo_str in memo:
                both_reversed_output=memo[both_reversed_memo_str]
                return both_reversed_output[0],                             \
                        [len(self.rev)-1-loc
                         for loc in both_reversed_output[1]]
            
            global restart_counter
            global restart_memo
                
            if len(self.rev)-self.rev.count('_') <= restart_max:
                restart_memo[self.rev]=self.someBestClick()
                memo[self.rev]=restart_memo[self.rev]
                return restart_memo[self.rev]
            # Needed because of memory issues
            if len(memo)>5*10**6:
                memo=copy.deepcopy(restart_memo)
                restart_counter+=1
            memo[self.rev]=self.someBestClick()
        return memo[self.rev]

         
def makeBlankPosition(dimensions,mines):
    dim_r,dim_c=dimensions
    # Makes all locations on the board
    all_loc=itertools.product(range(dim_c),range(dim_r))
    # Makes all possible distributions of mines
    all_mine_layouts=itertools.combinations(all_loc,mines)
    boards=[]
    for mine_layout in all_mine_layouts:
        boards.append(makeBoardFromMines(dimensions,mine_layout))
    return Position(dimensions, '_'*dim_c*dim_r, boards)

def makeBoardFromMines(dimensions,mine_layout):
    dim_r,dim_c=dimensions
    def mineNum(loc):
        if (loc%dim_c,loc//dim_c) in mine_layout:
            return '*'
        return str(sum(((loc%dim_c+dif[0],loc//dim_c+dif[1]) in mine_layout) for dif in
                   [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]))
    return ''.join(map(mineNum,(loc for loc in range(dim_r*dim_c))))

def makePosition(dimensions,mines,revealed):
    blank_pos=makeBlankPosition(dimensions,mines)
    boards_subset=[]
    for board in blank_pos.boards:
        if all(revealed[cell_num]==board[cell_num] or revealed[cell_num]=='_' for cell_num in range(len(board))):
            boards_subset.append(board)
    return Position(dimensions, revealed, boards_subset)

def winRate(dimensions,mines,revealed):
    pos=makePosition(dimensions,mines,revealed)
    global memo
    memo={}
    wins=pos.memoBestClick()
    return wins[0],len(pos.boards),wins[1],memo


global memo_counter
memo_counter=0
global restart_counter
restart_counter=0
global restart_memo
restart_memo={}
global restart_max
restart_max=6
dimensions, mines, revealed = eval(input())
wins, total_boards, moves, memo = winRate(dimensions, mines, revealed)
move_points=[(move//dimensions[1],move%dimensions[1]) for move in moves]
print("Best moves are %s.\n%i wins out of %i boards. Ratio of %f. %i positions searched."%(move_points, wins, total_boards, wins/total_boards, len(memo)))
