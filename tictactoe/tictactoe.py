from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.properties import (ListProperty, NumericProperty)
from kivy.uix.modalview import ModalView
from kivy.uix.button import Label
from kivy.uix.screenmanager import ScreenManager, Screen
import numpy as np


class GridEntry(Button):
   coords = ListProperty([0, 0])


class TicTacToePlayerLayout (GridLayout):
    status = ListProperty([0, 0, 0, 0, 0, 0, 0, 0, 0])
    current_player = NumericProperty(1)
    # Create player symbol and colour lookups
    playerSymbol = {1: 'O', -1: 'X'}
    boxColour = {1: (1, 1, 1, 1), -1: (0, 0, 0, 1)}  # (r, g, b, a)
    symbolColour = {-1: (1, 1, 1, 1), 1: (0, 0, 0, 1)}  # (r, g, b, a)

    def __init__(self, *args, **kwargs):
        super(TicTacToePlayerLayout, self).__init__()
        for row in range(3):
            for column in range(3):
                grid_entry = GridEntry(
                    coords=(row, column),
                    id = 'GE')
                grid_entry.bind(on_release=self.button_pressed)
                self.add_widget(grid_entry)

    def button_pressed(self, button):
        row, column = button.coords  # The pressed button is automatically
        # passed as an argument

        # Convert 2D grid coordinates to 1D status index
        status_index = 3 * row + column
        already_played = self.status[status_index]

        # If nobody has played here yet, make a new move
        if not already_played:
            self.make_a_move(status_index, button)
            self.check_status(self.status)

    def make_a_move(self, status_index, button):
        self.status[status_index] = self.current_player
        self.mark_move(button)
        self.current_player *= -1  # Switch current player

    def mark_move(self, button):
        button.text = self.playerSymbol[self.current_player]
        button.color = self.boxColour[self.current_player]
        button.background_color = self.symbolColour[self.current_player]

    def check_status(self, new_value):
        status = new_value

        sums = [sum(status[0:3]),  # rows
                sum(status[3:6]), sum(status[6:9]), sum(status[0::3]),  # columns
                sum(status[1::3]), sum(status[2::3]), sum(status[::4]),  # diagonals
                sum(status[2:-2:2])]

        winner = None
        if -3 in sums:
            winner = "Xs win!"
        elif 3 in sums:
            winner = "Os win!"
        elif 0 not in self.status:
            winner = "Draw!"

        if winner:
            popup = ModalView(size_hint=(0.75, 0.5))
            victory_label = Label(text=winner, font_size=50)
            popup.add_widget(victory_label)
            popup.bind(on_dismiss=self.reset)
            popup.open()
        return winner

    def reset(self, *args):
        self.status = [0 for _ in range(9)]

        # self.children is a list containing all child widgets
        for child in self.children:
            child.text = ''
            child.background_color = (1, 1, 1, 1)

        self.current_player = 1


class TicTacToeAILayout (TicTacToePlayerLayout):
    QTable = {}
    winner = {'PLAYER_WON': 3, 'AI_WON': 2, 'DRAW': 1}
    gamma = 0.7
    learningRate = 0.9
    epsilon = 0.8
    epoch = 50000

    def __init__(self, *args, **kwargs):
        super(TicTacToePlayerLayout, self).__init__()
        self.train_ai()
        for row in range(3):
            for column in range(3):
                grid_entry = GridEntry(
                    coords=(row, column),
                    id = 'GE')
                grid_entry.bind(on_release=self.button_pressed)
                self.add_widget(grid_entry)

    def button_pressed(self, button):
        # The pressed button is automatically passed as argument
        row, column = button.coords
        # Convert 2D grid coordinates to 1D status index
        status_index = 3 * row + column
        # Check if move is already played
        already_played = self.status[status_index]

        # If the move is not played yet, process it
        if not already_played:
            # Mark the move on the game status
            self.make_a_move(status_index, button)

            if not self.check_winner(self.status):
                # If no one win yet, it's the AI's turn to make a move
                self.AIMove()
            else:
                # someone won, display gameover screen
                self.generate_gameover_screen()

    def generate_gameover_screen(self):
        # Check how is the winner and prepare game end message accordingly
        winner = self.check_winner(self.status)
        if winner == 3:
            winningText = "You win!"
        elif winner == 2:
            winningText = "The AI win!"
        else:
            winningText = "Draw!"

        # Create a pop up to display the winner and reset the game when dismissed
        popup = ModalView(size_hint=(0.75, 0.5))
        victory_label = Label(text=winningText, font_size=50)
        popup.add_widget(victory_label)
        popup.bind(on_dismiss=self.reset)
        popup.open()

    def check_winner(self, currentState):
        winStatus = [sum(currentState[0:3]),  # rows
                sum(currentState[3:6]), sum(currentState[6:9]), sum(currentState[0::3]),  # columns
                sum(currentState[1::3]), sum(currentState[2::3]), sum(currentState[::4]),  # diagonals
                sum(currentState[2:-2:2])]

        if -3 in winStatus:
            return self.winner['AI_WON']
        elif 3 in winStatus:
            return self.winner['PLAYER_WON']
        elif 0 not in currentState:
            return self.winner['DRAW']
        return False

    def AIMove(self):
        AIMove = self.generate_AI_move()

        row = int(AIMove / 3)
        column = AIMove % 3

        for child in self.children:
            if child.coords == [row, column]:
                self.make_a_move(AIMove, child)
        if self.check_winner(self.status):
            self.generate_gameover_screen()

    def generate_AI_move(self):
        possibleMoves = self.generatePossibleMoves(self.status)
        if 4 in possibleMoves:
            AIMove = 4
            return AIMove
        elif 4 not in possibleMoves and possibleMoves.__len__() == 8:
            AIMove = 0
            return AIMove

        currentStateString = str(self.status)
        currentStateRewardArray = self.QTable[currentStateString]
        print(currentStateRewardArray)
        currentStateRewardArray[currentStateRewardArray == 0] = -99
        print(currentStateRewardArray)
        # self.generateAIHeatMap(currentStateRewardArray)
        AIMove = np.argmax(currentStateRewardArray[currentStateRewardArray != 0])
        print(AIMove)
        return AIMove

    def generateAIHeatMap(self, rewardArray):
        heatmap = 1 / (1 + np.exp(-rewardArray))
        while len(heatmap) != 9:
            np.append(heatmap, 0)
        i = 0
        for child in self.children:
            child.background_color = (heatmap[i], 0, 0, 0.5)

    def train_ai(self):
        for i in range(self.epoch):
            self.train_ai_reset()
            print("Epoch: %d" % (i+1))
            self.current_player = 1
            winner = False

            if i == 50000 or i == 100000:
                self.gamma /= 2
                self.learningRate /= 2
                self.epsilon /= 2

            while not winner:
                possibleMoves = self.generatePossibleMoves(self.status)
                currentStatusString = str(self.status)
                if currentStatusString not in self.QTable:
                    self.QTable[currentStatusString] = np.zeros(np.max(possibleMoves) + 1)
                if self.evaluateExplore:
                    move = np.random.choice(possibleMoves)
                else:
                    move = np.argmax(self.QTable[currentStatusString])

                next_state_string, next_state, reward, gameEnd = self.evaluateAction(move)
                if next_state_string not in self.QTable:
                    futurePossibleMoves = self.generatePossibleMoves(next_state)
                    if gameEnd:
                        self.QTable[next_state_string] = reward
                    else:
                        self.QTable[next_state_string] = np.zeros(np.max(futurePossibleMoves) + 1)

                current_Q = self.QTable[currentStatusString][move]
                if np.max(self.QTable[next_state_string]) == 0:
                    next_max = np.min(self.QTable[next_state_string])
                else:
                    next_max = np.max(self.QTable[next_state_string])
                new_value = ((1 - self.learningRate) * current_Q) + (self.learningRate * (reward + (self.gamma * next_max)))
                self.QTable[currentStatusString][move] = new_value

                self.status[move] = self.current_player

                winner = self.check_winner(self.status)
                self.current_player *= -1

        self.train_ai_reset()
        self.current_player = 1

    def evaluateAction(self, move):
        next_state = list.copy(self.status)
        next_state[move] = self.current_player
        next_state_string = str(next_state)
        gameEnd = self.check_winner(next_state)
        reward = 0

        if gameEnd:
            winner = self.check_winner(next_state)
            if winner == 3:
                reward = -1
            elif winner == 2:
                reward = 1
            else:
                reward = 0

        reward += self.evaluateActionInTermsOfPlayer(move)

        return next_state_string, next_state, reward, gameEnd

    def evaluateActionInTermsOfPlayer(self, move):
        next_state = list.copy(self.status)
        next_state[move] = self.current_player * -1
        gameEnd = self.check_winner(next_state)
        reward = 0

        if gameEnd:
            winner = self.check_winner(next_state)
            if winner == 3:
                reward = 1
            elif winner == 2:
                reward = -1
            else:
                reward = 0

        return reward

    def evaluateExplore(self):
        randomInt = np.random.rand()
        if randomInt > self.epsilon:
            return False
        else:
            return True

    def train_ai_reset(self):
        self.status = [0 for _ in range(9)]

    def generatePossibleMoves(self, state):
        possibleMoves = []
        for i in range(9):
            if state[i] == 0:
                possibleMoves.append(i)
        return possibleMoves


class TicTacToePlayerScreen (Screen):

    def __init__(self, *args, **kwargs):
        super(TicTacToePlayerScreen, self).__init__()
        layout = TicTacToePlayerLayout();
        self.add_widget(layout)


class TicTacToeAIScreen (Screen):

    def __init__(self, *args, **kwargs):
        super(TicTacToeAIScreen, self).__init__()
        layout = TicTacToeAILayout();
        self.add_widget(layout)


class IntroScreen (Screen):
    pass


class TicTacToeApp (App):

    def build(self):
        sm = ScreenManager()
        sm.add_widget(IntroScreen(name='Intro'))
        sm.add_widget(TicTacToePlayerScreen(name='TicTacToePlayer'))
        sm.add_widget(TicTacToeAIScreen(name='TicTacToeAI'))
        return sm

tictactoe = TicTacToeApp()
tictactoe.run()