import clr

clr.AddReference('IronPython.Modules.dll')
import os
import codecs
import json
import time

# ---------------------------------------
#   [Required]  Script Information
# ---------------------------------------
ScriptName = "tic-tac-toe"
Website = "https://www.twitch.tv/mi_thom"
Description = "play tic tac toe in chat/on stream"
Creator = "mi_thom + mathiasAC"
Version = "0.0.1"

# ---------------------------------------
# Other global settings
# ---------------------------------------
m_settings_file = os.path.join(os.path.dirname(__file__), "tictactoeSettings.json")
m_playfield_file = os.path.join(os.path.dirname(__file__), "playfield.txt")
ScriptSettings = None
m_moderator_permission = "Moderator"
m_game = None
m_current_challenges = {}
m_player_1 = None
m_player_2 = None
m_current_player = None


# ---------------------------------------
# Classes
# ---------------------------------------
class Settings(object):
    """ Load in saved settings file if available else set default values. """

    def __init__(self, settingsfile=None):
        try:
            with codecs.open(settingsfile, encoding="utf-8-sig", mode="r") as f:
                self.__dict__ = json.load(f, encoding="utf-8")
        except:
            self.play_command = "!play"
            self.start_command = "!tictactoe"
            self.start_cost = 1
            self.win_reward = 2
            self.challenge_time = 30
            self.currency_name = "points"
            self.spam_chat = False

    def reload(self, jsondata):
        """ Reload settings from Chatbot user interface by given json data. """
        self.__dict__ = json.loads(jsondata, encoding="utf-8")
        return

    def save(self, settingsfile):
        """ Save settings contained within to .json and .js settings files. """
        try:
            with codecs.open(settingsfile, encoding="utf-8-sig", mode="w+") as f:
                json.dump(self.__dict__, f, encoding="utf-8")
            with codecs.open(settingsfile.replace("json", "js"), encoding="utf-8-sig", mode="w+") as f:
                f.write("var settings = {0};".format(json.dumps(self.__dict__, encoding='utf-8')))
        except:
            Parent.Log(ScriptName, "Failed to save settings to file.")
        return


# ---------------------------------------
# obligated functions
# ---------------------------------------
def Init():
    global ScriptSettings
    ScriptSettings = Settings(m_settings_file)


def Execute(data):
    if not data.IsFromDiscord() and data.IsChatMessage():
        p_count = data.GetParamCount()
        if p_count == 2:
            param0 = data.GetParam(0)
            param1 = data.GetParam(1)
            if param0 == ScriptSettings.start_command:
                start_game_command(data.User, param1)
        elif p_count == 3:
            param0 = data.GetParam(0)
            if param0 == ScriptSettings.play_command:
                param1 = data.GetParam(1)
                param2 = data.GetParam(2)
                play_turn(data.User, param1, param2)


def Unload():
    ScriptSettings.save(m_settings_file)


def ReloadSettings(json_data):
    ScriptSettings.reload(json_data)


def Tick():
    remove_old_challenges()


# ---------------------------------------
# Chatbot adaption
# ---------------------------------------
def play_turn(user, row, col):
    username = Parent.GetDisplayName(user)
    players = [m_player_2, m_player_1]
    if m_game is not None:
        if username == m_current_player:
            if row.isdigit() and col.isdigit():
                row = convert_input_to_coordinate(int(row))
                col = convert_input_to_coordinate(int(col))
                if check_space_empty(m_game, row, col):
                    add_piece(username, row, col)
                    print_and_save_game()
                    switch_player()
                    winner = check_winner()
                    if winner is not None or not moves_exist():
                        display_winner(winner)
        elif username in players:
            Parent.SendStreamMessage(
                "it is not your turn %s, please wait for %s to continue" % (username, players[players.index(username) - 1]))
        else:
            Parent.SendStreamMessage("you are not in the current game, %s" % username)

#     # go on forever
#     while winner == 0 and moves_exist(game):
#         Parent.SendStreamMessage("Currently player: " + str(player))
#         available = False
#         while not available:
#             row = convert_input_to_coordinate(int(input("Which row? (start with 1) ")))
#             column = convert_input_to_coordinate(int(input("Which column? (start with 1) ")))
#             available = check_space_empty(game, row, column)
#         game = add_piece(game, player, row, column)
#         display_game(game)
#         player = switch_player(player)
#         winner = check_winner(game)
#     display_winner(winner)


def start_game_command(user, user2):
    if m_game is None:
        username1 = Parent.GetDisplayName(user)
        username2 = Parent.GetDisplayName(user2)
        if username1 in m_current_challenges.keys():
            Parent.SendStreamMessage("/me %s is already challenging somebody" % username1)
        elif m_current_challenges.get(username2, [None])[0] == username1:
            user1_points = Parent.GetPoints(user)
            user2_points = Parent.GetPoints(user)
            if user1_points > ScriptSettings.start_cost:
                if user2_points > ScriptSettings.start_cost:
                    Parent.RemovePoints(user, username1, ScriptSettings.start_cost)
                    Parent.RemovePoints(user2, username2, ScriptSettings.start_cost)
                    Parent.SendStreamMessage(
                        "/me challenge accepted, %s and %s have started their game" % (username1, username2))
                    start_game(user2, user)
                    print_and_save_game()
                else:
                    Parent.SendStreamMessage("/me %s doesn't have enough %s, you need %s" % (
                        username2, ScriptSettings.currency_name, ScriptSettings.start_cost))
            else:
                Parent.SendStreamMessage("/me %s doesn't have enough %s, you need %s" % (
                    username1, ScriptSettings.currency_name, ScriptSettings.start_cost))
        else:
            m_current_challenges[username1] = [username2, time.time()]
            Parent.SendStreamMessage(
                '/me {0} has challenged {1},to accept challenge type: !tictactoe {0}'.format(username1, username2))


def remove_old_challenges():
    global m_current_challenges
    # no iteritems() so we can delete items without error
    if m_game is not None and len(m_current_challenges) > 0:
        m_current_challenges = {}
    for challenge, [_, time_stamp] in m_current_challenges.items():
        if time.time() - time_stamp > ScriptSettings.challenge_time:
            Parent.SendStreamMessage("%s, your challenge has expired" % challenge)
            del m_current_challenges[challenge]


def print_and_save_game():
    if m_game is not None:
        if ScriptSettings.spam_chat:
            lines = display_game()
        with open(m_playfield_file, mode="w") as f:
            f.writelines(lines)
    else:
        with open(m_playfield_file, mode="w") as f:
            f.write("")


# ---------------------------------------
# Game Logic
# ---------------------------------------
def draw_line(width, edge, filling):
    Parent.SendStreamMessage(filling.join([edge] * (width + 1)))


def display_winner(player):
    end_game()
    print_and_save_game()
    if player is None:
        Parent.SendStreamMessage("Tie")
    else:
        Parent.SendStreamMessage("Player " + str(player) + " wins!")


def check_row_winner(row):
    """
    Return the player number that wins for that row.
    If there is no winner, return 0.
    """
    if row[0] == row[1] and row[1] == row[2]:
        return row[0]
    return 0


def get_col(game, col_number):
    return [game[x][col_number] for x in range(3)]


def get_row(game, row_number):
    return game[row_number]


def check_winner():
    game_slices = []
    for index in range(3):
        game_slices.append(get_row(m_game, index))
        game_slices.append(get_col(m_game, index))

    # check diagonals
    down_diagonal = [m_game[x][x] for x in range(3)]
    up_diagonal = [m_game[0][2], m_game[1][1], m_game[2][0]]
    game_slices.append(down_diagonal)
    game_slices.append(up_diagonal)
    players = [m_player_2, m_player_1]

    for game_slice in game_slices:
        winner = check_row_winner(game_slice)
        if winner != 0:
            return players[winner-1]


def start_game(user1, user2):
    global m_game, m_player_1, m_player_2, m_current_player
    m_game = [[0, 0, 0] for x in range(3)]
    m_player_1 = user1
    m_player_2 = user2
    m_current_player = user2


def end_game():
    global m_player_2, m_player_1, m_game, m_current_player
    m_game = None
    m_player_1 = None
    m_player_2 = None
    m_current_player = None


def display_game():
    d = {2: "O", 1: "X", 0: "_"}
    draw_line(3, " ", "_")
    lines = []
    for row_num in range(3):
        new_row = []
        for col_num in range(3):
            new_row.append(d[m_game[row_num][col_num]])
        to_send = "|" + "|".join(new_row) + "|"
        Parent.SendStreamMessage(to_send)
        lines.append(to_send + "\n")
    return lines


def add_piece(player, row, column):
    global m_game
    """
    player: player number
    row: 0-index row
    column: 0-index column
    """
    players = [m_player_2, m_player_1]
    m_game[row][column] = players.index(player)+1


def check_space_empty(game, row, column):
    return game[row][column] == 0


def convert_input_to_coordinate(user_input):
    return user_input - 1


def switch_player():
    global m_current_player
    if m_current_player == m_player_1:
        m_current_player = m_player_2
    else:
        m_current_player = m_player_1


def moves_exist():
    for row_num in range(3):
        for col_num in range(3):
            if m_game[row_num][col_num] == 0:
                return True
    return False
