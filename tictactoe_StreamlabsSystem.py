import clr

clr.AddReference('IronPython.Modules.dll')
import os
import codecs
import json
import time
import cStringIO

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
            self.border_thickness = 3
            self.border_color = "rgba(0,0,0,255)"
            self.field_color = "rgba(255,255,255,255)"

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
    Parent.BroadcastWsEvent("EVENT_RELOAD_SETTINGS_TICTACTOE", json_data)


def Tick():
    remove_old_challenges()


# ---------------------------------------
# Chatbot adaption
# ---------------------------------------
def play_turn(user, row, col):
    username = Parent.GetDisplayName(user)
    players = [m_player_2, m_player_1]
    if m_game is not None:
        if user == m_current_player:
            if row.isdigit() and col.isdigit():
                row = convert_input_to_coordinate(int(row))
                col = convert_input_to_coordinate(int(col))
                if check_space_empty(m_game, row, col):
                    add_piece(user, row, col)
                    print_and_save_game()
                    switch_player()
                    winner = check_winner()
                    if winner is not None or not moves_exist():
                        display_winner(winner)
                else:
                    Parent.SendStreamMessage("that position was not free %s" % username)
        elif user in players:
            Parent.SendStreamMessage(
                "it is not your turn %s, please wait for %s to continue" % (
                    username, Parent.GetDisplayName(players[players.index(user) - 1])))
        else:
            Parent.SendStreamMessage("you are not in the current game, %s" % username)


def start_game_command(user, username2):
    if m_game is None:
        username1 = Parent.GetDisplayName(user)
        if username1 in m_current_challenges.keys():
            Parent.SendStreamMessage("/me %s is already challenging somebody" % username1)
        elif m_current_challenges.get(username2, [None])[0] == username1:
            user1_points = Parent.GetPoints(user)
            user2 = m_current_challenges[username2][2]
            user2_points = Parent.GetPoints(m_current_challenges[username2][2])
            if user1_points > ScriptSettings.start_cost:
                if user2_points > ScriptSettings.start_cost:
                    Parent.RemovePoints(user, username1, ScriptSettings.start_cost)
                    Parent.RemovePoints(user2, username2, ScriptSettings.start_cost)
                    Parent.SendStreamMessage(
                        "/me challenge accepted, %s and %s have started their game" % (username1, username2))
                    start_game(user2, user)
                    print_and_save_game()
                else:
                    Parent.SendStreamMessage("/me %s doesn't have enough %s, he needs %s" % (
                        username2, ScriptSettings.currency_name, ScriptSettings.start_cost))
            else:
                Parent.SendStreamMessage("/me %s doesn't have enough %s, you need %s" % (
                    username1, ScriptSettings.currency_name, ScriptSettings.start_cost))
        else:
            m_current_challenges[username1] = [username2, time.time(), user]
            Parent.SendStreamMessage(
                '/me {0} has challenged {1},to accept challenge type: !tictactoe {0}'.format(username1, username2))


def remove_old_challenges():
    global m_current_challenges
    # no iteritems() so we can delete items without error
    if m_game is not None and len(m_current_challenges) > 0:
        m_current_challenges = {}
    for challenge, [_, time_stamp, _] in m_current_challenges.items():
        if time.time() - time_stamp > ScriptSettings.challenge_time:
            Parent.SendStreamMessage("%s, your challenge has expired" % challenge)
            del m_current_challenges[challenge]


def print_and_save_game():
    if m_game is not None:
        lines = display_game()
        with open(m_playfield_file, mode="w") as f:
            f.writelines(lines)
        # write_board()
    else:
        with open(m_playfield_file, mode="w") as f:
            f.write("")


# ---------------------------------------
# Game Logic
# ---------------------------------------
def display_winner(player):
    end_game()
    print_and_save_game()
    if player is None:
        Parent.SendStreamMessage("Tie")
    else:
        Parent.SendStreamMessage("Player " + Parent.GetDisplayName(player) + " wins!")


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
            return players[winner - 1]


def start_game(user1, user2):
    global m_game, m_player_1, m_player_2, m_current_player
    m_game = [[0, 0, 0] for x in range(3)]
    m_player_1 = user1
    m_player_2 = user2
    m_current_player = user2
    Parent.BroadcastWsEvent("EVENT_START_TICTACTOE", "")


def end_game():
    global m_player_2, m_player_1, m_game, m_current_player
    m_game = None
    m_player_1 = None
    m_player_2 = None
    m_current_player = None
    Parent.BroadcastWsEvent("EVENT_END_TICTACTOE", "")


def display_game():
    d = {2: "O", 1: "X", 0: "_"}
    lines = []
    for row_num in range(3):
        new_row = []
        for col_num in range(3):
            new_row.append(d[m_game[row_num][col_num]])
        to_send = "|" + "|".join(new_row) + "|"
        if ScriptSettings.spam_chat:
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
    m_game[row][column] = players.index(player) + 1
    Parent.BroadcastWsEvent("EVENT_ADD_PIECE_TICTACTOE",
                            json.dumps({"column": column, "row": row, "player": players.index(player) + 1}))


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


# ---------------------------------------
# drawing the overlay
# ---------------------------------------


def write_board():
    fp = os.path.join(os.path.dirname(__file__), "overlay.html")
    html_code = HTML(HEAD(LINK(rel="stylesheet", type="text/css", href="style.css")) +
                     SCRIPT("function reload(){location.href=location.href}; setInterval('reload()',100);") +
                     BODY(TABLE(Sum(TR(Sum(TD(get_inner_html(row, col)) for col in xrange(3))) for row in xrange(3)))))
    with open(fp, "w") as f:
        f.write(str(html_code))


def get_inner_html(row, col):
    if m_game[row][col] == 0:
        return ""
    elif m_game[row][col] == 1:
        return IMG(src="cross.png", height="100%", width="100%")
    else:
        return IMG(src="circle.png", height="100%", width="100%")


"""
<= addChild
Sum()
BR() + BR()
HEAD(..)
"""


class TAG:
    """Generic class for tags"""

    def __init__(self, inner_HTML="", **attrs):
        self.tag = self.__class__.__name__
        self.inner_HTML = inner_HTML
        self.attrs = attrs
        self.children = []
        self.brothers = []

    def __str__(self):
        res = cStringIO.StringIO()
        w = res.write
        if self.tag != "TEXT":
            w("<%s" % self.tag)
            # attributes which will produce arg = "val"
            attr1 = [k for k in self.attrs
                     if not isinstance(self.attrs[k], bool)]
            w("".join([' %s="%s"'
                       % (k.replace('_', '-'), self.attrs[k]) for k in attr1]))
            # attributes with no argument
            # if value is False, don't generate anything
            attr2 = [k for k in self.attrs if self.attrs[k] is True]
            w("".join([' %s' % k for k in attr2]))
            w(">")
        if self.tag in ONE_LINE:
            w('\n')
        w(str(self.inner_HTML))
        for child in self.children:
            w(str(child))
        if self.tag in CLOSING_TAGS:
            w("</%s>" % self.tag)
        if self.tag in LINE_BREAK_AFTER:
            w('\n')
        if hasattr(self, "brothers"):
            for brother in self.brothers:
                w(str(brother))
        return res.getvalue()

    def __le__(self, other):
        """Add a child"""
        if isinstance(other, str):
            other = TEXT(other)
        self.children.append(other)
        other.parent = self
        return self

    def __add__(self, other):
        """Return a new instance : concatenation of self and another tag"""
        res = TAG()
        res.tag = self.tag
        res.inner_HTML = self.inner_HTML
        res.attrs = self.attrs
        res.children = self.children
        res.brothers = self.brothers + [other]
        return res

    def __radd__(self, other):
        """Used to add a tag to a string"""
        if isinstance(other, str):
            return TEXT(other) + self
        else:
            raise ValueError, "Can't concatenate %s and instance" % other

    def __mul__(self, n):
        """Replicate self n times, with tag first : TAG * n"""
        res = TAG()
        res.tag = self.tag
        res.inner_HTML = self.inner_HTML
        res.attrs = self.attrs
        for i in range(n - 1):
            res += self
        return res

    def __rmul__(self, n):
        """Replicate self n times, with n first : n * TAG"""
        return self * n


# list of tags, from the HTML 4.01 specification

CLOSING_TAGS = ['A', 'ABBR', 'ACRONYM', 'ADDRESS', 'APPLET',
                'B', 'BDO', 'BIG', 'BLOCKQUOTE', 'BUTTON',
                'CAPTION', 'CENTER', 'CITE', 'CODE',
                'DEL', 'DFN', 'DIR', 'DIV', 'DL',
                'EM', 'FIELDSET', 'FONT', 'FORM', 'FRAMESET',
                'H1', 'H2', 'H3', 'H4', 'H5', 'H6',
                'I', 'IFRAME', 'INS', 'KBD', 'LABEL', 'LEGEND',
                'MAP', 'MENU', 'NOFRAMES', 'NOSCRIPT', 'OBJECT',
                'OL', 'OPTGROUP', 'PRE', 'Q', 'S', 'SAMP',
                'SCRIPT', 'SELECT', 'SMALL', 'SPAN', 'STRIKE',
                'STRONG', 'STYLE', 'SUB', 'SUP', 'TABLE',
                'TEXTAREA', 'TITLE', 'TT', 'U', 'UL',
                'VAR', 'BODY', 'COLGROUP', 'DD', 'DT', 'HEAD',
                'HTML', 'LI', 'P', 'TBODY', 'OPTION',
                'TD', 'TFOOT', 'TH', 'THEAD', 'TR']

NON_CLOSING_TAGS = ['AREA', 'BASE', 'BASEFONT', 'BR', 'COL', 'FRAME',
                    'HR', 'IMG', 'INPUT', 'ISINDEX', 'LINK',
                    'META', 'PARAM']

# create the classes
for tag in CLOSING_TAGS + NON_CLOSING_TAGS + ['TEXT']:
    exec ("class %s(TAG): pass" % tag)


def Sum(iterable):
    """Return the concatenation of the instances in the iterable
    Can't use the built-in sum() on non-integers"""
    it = [item for item in iterable]
    if it:
        return reduce(lambda x, y: x + y, it)
    else:
        return ''


# whitespace-insensitive tags, determines pretty-print rendering
LINE_BREAK_AFTER = NON_CLOSING_TAGS + ['HTML', 'HEAD', 'BODY',
                                       'FRAMESET', 'FRAME',
                                       'TITLE', 'SCRIPT',
                                       'TABLE', 'TR', 'TD', 'TH', 'SELECT', 'OPTION',
                                       'FORM',
                                       'H1', 'H2', 'H3', 'H4', 'H5', 'H6',
                                       ]
# tags whose opening tag should be alone in its line
ONE_LINE = ['HTML', 'HEAD', 'BODY',
            'FRAMESET'
            'SCRIPT',
            'TABLE', 'TR', 'TD', 'TH', 'SELECT', 'OPTION',
            'FORM',
            ]
