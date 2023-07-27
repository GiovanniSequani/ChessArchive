This is Flask server which I used to review my chess games, in particular which moves I played and which moves played the opponent.

You need to download an engine, such as stockfish 15, before running the code.
You also have to donwload the .pgn files containing the games you want to add to the archive.
Put those .pgn files into the directory 'downloaded'.

Run 'server.py' and open 'http://127.0.0.1:5000' where the server is running.

There is one error: the site doesn't display correctly the board, but if you select a move or reverse the board it is displayed without errors.

Once you correctly runned 'server.py' and opened 'http://127.0.0.1:5000' in the folder should have appeared two new files:
- 'all_games.pgn': contains all the games in the archive
- 'arc.pkl': a .pkl file of the istance from the class 'Archivio'

If you add computer moves in the archive, those will be saved in a file called 'compmoves.pkl' which will appear in the folder.
