# ---------------------------------------
#   [Required]  Script Information
# ---------------------------------------
ScriptName = "tic-tac-toe"
Website = "https://www.twitch.tv/mathiasAmazingChannel"
Description = "play tic tac toe in chat/on stream"
Creator = "mathiasAC + mi_thom"
Version = "0.0.1"

# ---------------------------------------
# Other global settings
# ---------------------------------------
m_settings_file = "tictactoeSettings.json"
ScriptSettings = None
m_moderator_permission = "moderator"
m_game = None
m_current_challenges = {}


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
# Game Logic
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
                pass


def Unload():
    ScriptSettings.save(m_settings_file)


def ReloadSettings(json_data):
    ScriptSettings.reload(json_data)


def Tick():
    pass


# ---------------------------------------
# Chatbot adaption
# ---------------------------------------
def start_game_command(user, user2):
    if m_game is None:
        if user in m_current_challenges.keys():
            Parent.SendStreamMessage("you are already challenging somebody")
        elif m_current_challenges.get(user2, None) == user:
            Parent.SendStreamMessage("challenge accepted")
            start_game()  # TODO: make player specific
            display_game(m_game)
        else:
            m_current_challenges[user] = user2
            Parent.SendStreamMessage('{0} has challenged {1},to accept challenge type: !tictactoe {0} ')


# ---------------------------------------
# Game Logic
# ---------------------------------------
def draw_line(width, edge, filling):
    Parent.SendStreamMessage(filling.join([edge] * (width + 1)))


def display_winner(player):
    if player == 0:
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


def check_winner(game):
    game_slices = []
    for index in range(3):
        game_slices.append(get_row(game, index))
        game_slices.append(get_col(game, index))

    # check diagonals
    down_diagonal = [game[x][x] for x in range(3)]
    up_diagonal = [game[0][2], game[1][1], game[2][0]]
    game_slices.append(down_diagonal)
    game_slices.append(up_diagonal)

    for game_slice in game_slices:
        winner = check_row_winner(game_slice)
        if winner != 0:
            return winner

    return winner


def start_game():
    global m_game
    m_game = [[0, 0, 0] for x in range(3)]


def display_game():
    d = {2: "O", 1: "X", 0: "_"}
    draw_line(3, " ", "_")
    for row_num in range(3):
        new_row = []
        for col_num in range(3):
            new_row.append(d[m_game[row_num][col_num]])
        Parent.SendStreamMessage("|" + "|".join(new_row) + "|")


def add_piece(game, player, row, column):
    """
    game: game state
    player: player number
    row: 0-index row
    column: 0-index column
    """
    game[row][column] = player
    return game


def check_space_empty(game, row, column):
    return game[row][column] == 0


def convert_input_to_coordinate(user_input):
    return user_input - 1


def switch_player(player):
    if player == 1:
        return 2
    else:
        return 1


def moves_exist(game):
    for row_num in range(3):
        for col_num in range(3):
            if game[row_num][col_num] == 0:
                return True
    return False


if __name__ == '__main__':
    player = 1
    winner = 0  # the winner is not yet defined

    # go on forever
    while winner == 0 and moves_exist(game):
        Parent.SendStreamMessage("Currently player: " + str(player))
        available = False
        while not available:
            row = convert_input_to_coordinate(int(input("Which row? (start with 1) ")))
            column = convert_input_to_coordinate(int(input("Which column? (start with 1) ")))
            available = check_space_empty(game, row, column)
        game = add_piece(game, player, row, column)
        display_game(game)
        player = switch_player(player)
        winner = check_winner(game)
    display_winner(winner)
