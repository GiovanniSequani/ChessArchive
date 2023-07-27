import pandas as pd
import os
import io
import chess
import json

def getcont(line):
    start = False
    end = False
    for i in range(len(line)):
        if line[i]=='"':
            if start is False:
                start = i+1
            else:
                end = i
                return line[start:end]
    return line[start:]

def pgn_to_dict(pgn):
    with open("temp.pgn", "w") as file:
        file.write(pgn)
    file = open("temp.pgn", "r")
    data = []
    labels = ["event", "site", "date", "round", "white", "black", "result", "whiteelo", "blackelo", "timecontrol", "endtime", "termination", "fen", "sepmoves"]
    line = file.readline()

    while True:
        if not line:
            file.close()
            os.remove("temp.pgn")
            return data
        while line == "\n":
            line = file.readline()
            if not line:
                file.close()
                os.remove("temp.pgn")
                return data
        game = {}
        for label in labels:
            cont = getcont(line)
            if label == "fen" or label == "sepmoves":
                cont = cont.replace("'", '"')
                cont = json.loads(cont)
            game[label] = cont
            line = file.readline()

        game["moves"] = ""
        nextchar = False
        line = file.readline()
        while line != "\n":
            if not line:
                data.append(game)
                file.close()
                os.remove("temp.pgn")
                return data
            line = remove_graffe(line, nextchar)
            game["moves"] += line[0].rstrip()+" "
            nextchar = line[1]
            line = file.readline()
        data.append(game)
        line = file.readline()

def pgn_to_dict2(pgn):
    with open("temp.pgn", "w") as file:
        file.write(pgn)
    file = open("temp.pgn", "r")
    data = []
    labels = ["event", "site", "date", "round", "white", "black", "result", "whiteelo", "blackelo", "timecontrol", "endtime", "termination"]
    line = file.readline()

    while True:
        if not line:
            file.close()
            os.remove("temp.pgn")
            return data
        while line == "\n":
            line = file.readline()
            if not line:
                file.close()
                os.remove("temp.pgn")
                return data
        game = {}
        for label in labels:
            cont = getcont(line)
            game[label] = cont
            line = file.readline()

        game["moves"] = ""
        nextchar = False
        line = file.readline()
        while line != "\n":
            if not line:
                data.append(game)
                file.close()
                os.remove("temp.pgn")
                return data
            line = remove_graffe(line, nextchar)
            nextchar = line[1]
            game["moves"] += line[0].rstrip()+" "

            line = file.readline()
        data.append(game)
        line = file.readline()

def remove_graffe(riga, next):
    nextfalse = False
    risultato = ""
    for i in range(len(riga)):
        if nextfalse:
            next = False
            nextfalse = False
        if riga[i] == "{":
            next = True
        elif riga[i] == "}":
            next = True
            nextfalse = True
        if not next:
            risultato = risultato + riga[i]
    
    return [risultato, next]

   
def df_to_pgn(df, destination_path="partite"):
    try:
        os.remove(destination_path+".pgn")
    except FileNotFoundError:
        pass
    file = open(destination_path+".pgn", "x")
    for ind, row in df.iterrows():
        txt = f'[Event "{row[0]}"]\n[Site "{row[1]}"]\n[Date "{row[2]}"]\n[Round "{row[3]}"]\n[White "{row[4]}"]'
        txt += f'\n[Black "{row[5]}"]\n[Result "{row[6]}"]\n[WhiteElo "{row[7]}"]\n[BlackElo "{row[8]}"]'
        txt += f'\n[TimeControl "{row[9]}"]\n[EndTime "{row[10]}"]\n[Termination "{row[11]}"]'
        txt += f'\n[Fen "{row[12]}"]\n[Sepmoves "{row[13]}"]\n\n{row[14]}\n\n'
        file.write(txt)
    file.close()

def unique_games(dict):
    #dates = set()
    #endtimes = set()
    dates_endtime = set()
    games = []
    for game in dict:
        if not (game["date"], game["endtime"]) in dates_endtime: # (game["date"] in dates and game["endtime"] in endtimes) :
            games.append(game)
        #dates.add(game["date"])
        #endtimes.add(game["endtime"])
        dates_endtime.add((game["date"], game["endtime"]))

    toreturn = pd.DataFrame(games)

    return toreturn

def refresh_from_dir(dirpath="downloaded", destinationpath="all_games", save=False):

    # legge il contuenuto del file di destinazione se esiste
    if os.path.exists(destinationpath+".pgn"):
        with open(destinationpath+".pgn", "r") as file:
            firstpgn = file.read() + "\n"
    else:
        firstpgn = ""

    # aggiunge il contenuto di ogni file nella cartella passata come parametro
    newtxt = ""
    listdir = os.listdir(dirpath)
    for filename in listdir:
        with open(f"{dirpath}\{filename}", "r") as file:
            content = file.read()
            newtxt += content + "\n"

    # crea un pgn temporaneo per ottenere il df con le partite non doppiate e poi lo elimina
    if len(newtxt) > 1:
        dict = pgn_to_dict2(newtxt)
        newdf = pd.DataFrame(dict)
        newdf.insert(12, "fen", get_fen(newdf)) # posizione 12
        newdf.insert(13, "sepmoves", sep_moves(newdf.moves)) # posizione 13
        finaldict = pgn_to_dict(firstpgn) + newdf.to_dict("records")
    else:
        finaldict = pgn_to_dict(firstpgn)
    
    df = unique_games(finaldict)

    # elimina tutti i file dalla cartella passata come parametro
    listfile = os.listdir(dirpath)
    for file in listfile:
        os.remove(dirpath+"/"+file)

    # salva il df come pgn 
    if save:
        df_to_pgn(df, destinationpath)

    return df

def get_fen(data):
    l = []
    for ind, row in data.iterrows():
        pgn = io.StringIO(row["moves"])
        game = chess.pgn.read_game(pgn)
        board = game.board()
        l.append(["rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq -"])
        for move in game.mainline_moves():
            board.push(move)
            l[-1].append(board.fen()[:-(len(str(board.halfmove_clock)) + len(str(board.fullmove_number)) + 2)])

    return pd.Series(l)

def sep_moves(moves):
    lista = []
    for row in moves:
        sep_moves = []
        move = ""
        for c in row:
            if c in "abcdefghNBQKRxO=+#012345678-":
                move += c
            elif c == ".":
                move = ""
            elif c == " " and len(move) > 0:
                sep_moves.append(move)
                move = ""
        lista.append(sep_moves)
    
    return pd.Series(lista)