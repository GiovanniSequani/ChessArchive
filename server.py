from flask import Flask, render_template, request, make_response
import os
import functions

app = Flask(__name__)

by_fen = True # set and change by_fen from here
pathEngine = 'C:/Users/.../stockfish15/stockfish-windows-2022-x86-64-avx2.exe' # set the path to the engine (for example stockfish15)

orientation = "WHITE"


@app.route('/')
def index():
    global by_fen
    functions.crea_archivio()
    print("Archivio creato.")
    mosse = functions.show_moves(by_fen)
    mossacomputer = functions.get_computer_move()
    ngames = functions.get_len_archivio()
    partite = functions.get_numero_partite(by_fen)
    board = functions.showBoard()
    return render_template('index.html', mosse=mosse, mossacomputer=mossacomputer, ngames=ngames, partite=partite, board=board)

@app.route('/api/aggiungi-dati')
def aggiungi_dati():
    functions.aggiungi_dati(dirpath = "downloaded", filename = "all_games")
    return ""


@app.route('/api/seleziona-partite')
def seleziona_partite():
    bianco = request.args.get('bianco') if request.args.get('bianco') != "" else None
    nero = request.args.get('nero') if request.args.get('nero') != "" else None
    risultato = request.args.get('risultato') if request.args.get('risultato') != "" else None
    
    functions.seleziona_partite(bianco, nero, risultato)
    print("Partite selezionate.")
    return ""

@app.route('/api/aggiungi-mossa-computer')
def aggiungi_mossa_computer():
    nuovamossacomputer = request.args.get('nuovamossacomputer')
    functions.aggiungi_mossa_computer(nuovamossacomputer)
    print("Mossa aggiunta.")
    return nuovamossacomputer

@app.route('/api/mostra-mossa-computer')
def mostra_mossa_computer():
    return functions.get_computer_move()

@app.route('/api/mosse-giocate')
def mosse_giocate():
    global by_fen
    mosse = functions.show_moves(by_fen)
    return render_template("_mosse_giocate.html", mosse=mosse)

@app.route('/api/muovi')
def muovi():
    global by_fen
    mossa  = request.args.get('mossa')
    functions.muovi(mossa)
    mosse = functions.show_moves(by_fen)
    return render_template("_mosse_giocate.html", mosse=mosse)

@app.route('/api/go-back')
def goBack():
    global by_fen
    mosse = functions.get_moves()
    if len(mosse) > 0:
        functions.goBack()
    mosse = functions.show_moves(by_fen)
    return render_template("_mosse_giocate.html", mosse=mosse)

@app.route('/api/annulla-tutto')
def annullaTutto():
    global by_fen
    mosse = functions.get_moves()
    if len(mosse) > 0:
        functions.annullaTutto()
    mosse = functions.show_moves(by_fen)
    return render_template("_mosse_giocate.html", mosse=mosse)

@app.route('/api/mosse-fatte')
def mosse_fatte():
    moves = functions.get_moves()

    if len(moves) == 0:
        return "Ancora nessuna mossa fatta"

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
    return txt

@app.route("/api/get-n-games")
def get_n_games():
    return functions.get_len_archivio()

@app.route("/api/get-numero-partite")
def get_numero_partite():
    global by_fen
    return str(functions.get_numero_partite(by_fen))

@app.route("/api/evaluate-pos")
def evaluatePos():
    global pathEngine
    time = request.args.get('time')

    return str(functions.evaluate(float(time), pathEngine))

@app.route("/api/best-move")
def best_move():
    global pathEngine
    time = request.args.get('timebestmove')

    return functions.calcMove(float(time), pathEngine)

@app.route("/api/show-board")
def showBoard():
    if orientation == "BLACK":
        return functions.showBoardReverse()
    return functions.showBoard()

@app.route("/api/get-file")
def createFile():
    global by_fen
    functions.creaFile(by_fen)
    with open("temp.pgn", "rb") as f:
        data = f.read()
    os.remove("temp.pgn")
    response = make_response(data)
    response.headers.set("Content-Disposition", "attachment", filename="partite.pgn")
    response.headers.set("Content-Type", "application/octet-stream")
    return response

@app.route("/api/reverse")
def reverse():
    global orientation
    if orientation == "WHITE":
        orientation = "BLACK"
        return functions.showBoardReverse()
    orientation = "WHITE"
    return functions.showBoard()


if __name__ == '__main__':
    app.run(debug=True)