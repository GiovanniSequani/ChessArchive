import pandas as pd
import pickle as pkl
import os
from copy import deepcopy
import io
import chess, chess.pgn, chess.engine, chess.svg
from preprocessing import unique_games, refresh_from_dir, df_to_pgn, get_fen

class Archivio:
    char = "abcdefghNBQKRxO=+#012345678-"

    def __init__(self, df=None, white=None, black=None, result=None, computermovespath="compmoves.pkl") -> None:
        if df is None:
            self.data = pd.DataFrame(columns=["event", "site", "date", "round", "white", "black", "result", "whiteelo", "blackelo", "timecontrol", "endtime", "termination", "moves", "fen"])
        else:
            self.data = df
            self.data["fen"] = get_fen(self.data) # fen in posizione 13 (14esima colonna)

        self.data["sepmoves"] = "" # posizione 14 (15esima colonna)
        for ind, row in self.data.iterrows():
            self.data.loc[ind, "sepmoves"] = self._sep_moves(row.moves)

        self.select_data(white, black, result)
        self.moves = []
        self.current_move = 0
        self.fen = ["rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq -"]
        self.chessboard = chess.Board()
        self.computermovespath = computermovespath
        if os.path.exists(self.computermovespath):
            with open(computermovespath, "rb") as file:
                self.computermoves = pkl.load(file)
        else:
            self.computermoves = {}

    def show_moves(self, by_fen=False) -> None:
        cond = []
        if by_fen:
            currentfen = self.fen[-1]
            for ind, row in self.games.iterrows():
                cond.append(currentfen in row["fen"])
        else:
            for ind, row in self.games.iterrows():
                cond.append(row["sepmoves"][:len(self.moves)]==self.moves)

        results2 = {}
        moves = []
        results = []

        terminations = ("12-12", "10", "01")

        for ind, game in self.games[cond].iterrows():
            move = game["sepmoves"][self.current_move]
            if move in results2.keys() and not move in terminations:
                results2[move].append(game["result"])
            elif not move in terminations:
                results2[move] = [game["result"]]
        if len(self.games) == 0:
            print("Nessuna partita in archivio")
            return pd.DataFrame()
        elif len(results2) == 0:
            print("Nessuna partita nell'archivio contiene questa mossa")
            self.go_back()
            return pd.DataFrame()
        else:
            return self._value_counts(results2, by_fen)
    
    def get_compmove(self):
        try:
            return self.computermoves[self.fen[-1]]
        except:
            return ""

    def move(self, move) -> None:
        self.chessboard.push_san(move)
        self.fen.append(self.chessboard.fen()[:-(len(str(self.chessboard.halfmove_clock)) + len(str(self.chessboard.fullmove_number)) + 2)])
        self.moves.append(move)
        self.current_move += 1
    
    def go_back(self) -> None:
        self.moves = self.moves[:-1]
        self.fen = self.fen[:-1]
        self.current_move -= 1
        self.chessboard.pop()

    def annulla_mosse(self) -> None:
        self.moves = []
        self.chessboard = chess.Board()
        self.fen = ["rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq -"]
        self.current_move = 0

    def _sep_moves(self, row: str) -> list:
        sep_moves = []
        move = ""
        for c in row:
            if c in self.char:
                move += c
            elif c == ".":
                move = ""
            elif c == " " and len(move) > 0:
                sep_moves.append(move)
                move = ""
        return sep_moves

    def _value_counts(self, results2, by_fen) -> None:
        wins = []
        draws = []
        losses = []
        freq = []
        moves = []
        for move, results in results2.items():
            moves.append(move)

            self.move(move)
            stats = self.stats(by_fen)
            self.go_back()

            freq.append(stats[0])
            wins.append(round(stats[1]*100/stats[0],1))
            draws.append(round(stats[3]*100/stats[0],1))
            losses.append(round(stats[2]*100/stats[0],1))
        
        result = pd.DataFrame({"freq":freq,  "1-0":wins, "0.5-0.5":draws, "0-1":losses}, index=moves)
        return result.sort_values(by="freq", ascending=False)

    def stats(self, by_fen=False) -> None:
        cond = []
        wins = []
        loss = []
        draw = []
        if by_fen:
            currentfen = self.fen[-1]
            for ind, row in self.games.iterrows():
                cond.append(currentfen in row["fen"])
                wins.append(currentfen in row["fen"] and row["result"] == "1-0")
                loss.append(currentfen in row["fen"] and row["result"] == "0-1")
                draw.append(currentfen in row["fen"] and row["result"] == "1/2-1/2")
        else:
            for ind, row in self.games.iterrows():
                cond.append(row["sepmoves"][:len(self.moves)] == self.moves)
                wins.append(row["sepmoves"][:len(self.moves)] == self.moves and row["result"] == "1-0")
                loss.append(row["sepmoves"][:len(self.moves)] == self.moves and row["result"] == "0-1")
                draw.append(row["sepmoves"][:len(self.moves)] == self.moves and row["result"] == "1/2-1/2")

        return [len(self.games[cond]), len(self.games[wins]), len(self.games[loss]), len(self.games[draw])]
    
    def add_computermove(self, move) -> None:
        self.computermoves[self.fen[-1]] = move
        with open(self.computermovespath, "wb") as file:
            pkl.dump(self.computermoves, file)   

    def to_pickle(self, path) -> None:
        with open(path, "wb") as file:
            pkl.dump(self,file)

    def select_data(self, white=None, black=None, result=None) -> None:
        self.white = white
        self.black = black
        self.result = result

        if not white is None:
            self.white = white
        if not black is None:
            self.black = black
        if not result is None:
            self.result = result

        if not white is None:
            self.games = deepcopy(self.data.loc[self.data["white"]==self.white])
        if not black is None:
            self.games = deepcopy(self.data.loc[self.data["black"]==self.black])
        if white is None and black is None:
            self.games = self.data
        if not self.result is None:
            self.games = deepcopy(self.games.loc[self.games["result"]==self.result])

    def delete_data(self,) -> None:
        self.data = None
    
    def add_newdata(self, newdata, unique=True, select=True) -> None:
        olddata_dict = self.data.to_dict("records")
        """newdata["fen"] = get_fen(newdata)
        newdata["sepmoves"] = ""

        for ind, row in newdata.iterrows():
            newdata.loc[ind, "sepmoves"] = self._sep_moves(row.moves)"""

        newdata_dict = newdata.to_dict("records")
        data_dict = olddata_dict + newdata_dict
        
        if unique:
            self.data = unique_games(data_dict)
        else:
            self.data = pd.DataFrame(data_dict)

        if len(self.data) > 0:
            self.data = self.data.sort_values(by=["date","endtime"])
            self.data.index = list(range(1,len(self.data.index)+1))

        if select:
            self.select_data(self.white, self.black, self.result)
    
    def get_games(self, by_fen=False):
        cond = []
        if by_fen:
            currentfen = self.fen[-1]
            for ind, row in self.games.iterrows():
                cond.append(currentfen in row["fen"])
        else:
            for ind, row in self.games.iterrows():
                cond.append(row["sepmoves"][:len(self.moves)]==self.moves)

        return self.games[cond]

# funzioni
def crea_archivio():
    arc = Archivio()
    arc.add_newdata(refresh_from_dir())
    # salva i dati come pgn 
    df_to_pgn(arc.data, "all_games")

    with open("arc.pkl", "wb") as file:
        pkl.dump(arc, file)

def aggiungi_dati(dirpath, filename):
    with open("arc.pkl", "rb") as file:
        arc = pkl.load(file)
    arc.add_newdata(refresh_from_dir(dirpath, filename))
    # salva i dati come pgn 
    df_to_pgn(arc.data, "all_games")

    with open("arc.pkl", "wb") as file:
        pkl.dump(arc, file)

def seleziona_partite(nome_bianco=None, nome_nero=None, result=None):
    with open("arc.pkl", "rb") as file:
        arc = pkl.load(file)

    arc.select_data(white=nome_bianco, black=nome_nero, result=result)

    with open("arc.pkl", "wb") as file:
        pkl.dump(arc, file)

def aggiungi_mossa_computer(mossa):
    with open("arc.pkl", "rb") as file:
        arc = pkl.load(file)
        
    arc.add_computermove(mossa)

    with open("arc.pkl", "wb") as file:
        pkl.dump(arc, file)

def get_numero_partite(by_fen=False):
    with open("arc.pkl", "rb") as file:
        arc = pkl.load(file)

    return arc.stats(by_fen)[0]

def get_len_archivio():
    with open("arc.pkl", "rb") as file:
        arc = pkl.load(file)

    return str(len(arc.data))

def get_moves():
    with open("arc.pkl", "rb") as file:
        arc = pkl.load(file)

    return arc.moves

def show_moves(by_fen=False):
    with open("arc.pkl", "rb") as file:
        arc = pkl.load(file)

    return arc.show_moves(by_fen)

def muovi(mossa):
    with open("arc.pkl", "rb") as file:
        arc = pkl.load(file)
    
    arc.move(mossa)

    with open("arc.pkl", "wb") as file:
        pkl.dump(arc, file)

def get_computer_move():
    with open("arc.pkl", "rb") as file:
        arc = pkl.load(file)
    
    return arc.get_compmove()

def goBack():
    with open("arc.pkl", "rb") as file:
        arc = pkl.load(file)

    arc.go_back()

    with open("arc.pkl", "wb") as file:
        pkl.dump(arc, file)

def annullaTutto():
    with open("arc.pkl", "rb") as file:
        arc = pkl.load(file)

    arc.annulla_mosse()

    with open("arc.pkl", "wb") as file:
        pkl.dump(arc, file)


def evaluate(timelimit, pathEngine):
    with open("arc.pkl", "rb") as file:
        arc = pkl.load(file)

    moves = arc.moves
    txt = ""
    n = 0
    for i in range(0, len(moves), 2):
        n += 1
        try:
            txt += f"{n}. {moves[i]} {moves[i+1]} "
        except:
            try:
                txt += f"{n}. {moves[i]}"
            except:
                pass

    if txt == "":
        return 0.0
    
    pgn = io.StringIO(txt)
    game = chess.pgn.read_game(pgn)
    board = game.board()
    for move in game.mainline_moves():
        board.push(move)
    engine = chess.engine.SimpleEngine.popen_uci(pathEngine)
    movetimesec = timelimit
    limit=chess.engine.Limit(time=movetimesec)
    info = engine.analyse(board, limit)
    score = info['score'].white().score(mate_score=1000)
    engine.quit()

    return max(min(score, 1000), -1000)/100

def calcMove(timelimit, pathEngine):
    with open("arc.pkl", "rb") as file:
        arc = pkl.load(file)

    moves = arc.moves

    txt = ""
    n = 0
    for i in range(0, len(moves), 2):
        n += 1
        try:
            txt += f"{n}. {moves[i]} {moves[i+1]} "
        except:
            try:
                txt += f"{n}. {moves[i]}"
            except:
                pass

    if txt == "":
        return "e4"
    
    pgn = io.StringIO(txt)
    game = chess.pgn.read_game(pgn)
    board = game.board()
    for move in game.mainline_moves():
        board.push(move)
    engine = chess.engine.SimpleEngine.popen_uci(pathEngine)
    movetimesec = timelimit
    limit=chess.engine.Limit(time=movetimesec)

    move = engine.play(board, limit=limit)
    engine.quit()

    m = chess.Move.from_uci(str(move.move))

    return board.san(m)


def showBoard():
    with open("arc.pkl", "rb") as file:
        arc = pkl.load(file)

    moves = arc.moves

    txt = ""
    n = 0
    for i in range(0, len(moves), 2):
        n += 1
        try:
            txt += f"{n}. {moves[i]} {moves[i+1]} "
        except:
            try:
                txt += f"{n}. {moves[i]}"
            except:
                pass
    
    if txt == "":
        pgn = io.StringIO("e4")
        game = chess.pgn.read_game(pgn)
        board = game.board()
        return chess.svg.board(board=board)

    pgn = io.StringIO(txt)
    game = chess.pgn.read_game(pgn)
    board = game.board()
    for move in game.mainline_moves():
        board.push(move)

    return chess.svg.board(board=board)

def showBoardReverse():
    with open("arc.pkl", "rb") as file:
        arc = pkl.load(file)

    moves = arc.moves

    txt = ""
    n = 0
    for i in range(0, len(moves), 2):
        n += 1
        try:
            txt += f"{n}. {moves[i]} {moves[i+1]} "
        except:
            try:
                txt += f"{n}. {moves[i]}"
            except:
                pass
    
    if txt == "":
        pgn = io.StringIO("e4")
        game = chess.pgn.read_game(pgn)
        board = game.board()
        return chess.svg.board(board=board, orientation=chess.BLACK)

    pgn = io.StringIO(txt)
    game = chess.pgn.read_game(pgn)
    board = game.board()
    for move in game.mainline_moves():
        board.push(move)

    return chess.svg.board(board=board, orientation=chess.BLACK)

def creaFile(by_fen=False):
    with open("arc.pkl", "rb") as file:
        arc = pkl.load(file)

    df_to_pgn(arc.get_games(by_fen), destination_path="temp")

