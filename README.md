# AVA-chess-engine
AVA is a simple chess engine for lichess.org. You can play against it on [lichess](https://lichess.org/?user=ava-chess-engine#friend).<br>
Bot uses [Lichess-bot](https://github.com/ShailChoksi/lichess-bot). A bridge between [Lichess Bot API](https://lichess.org/api#tag/Bot) and bots.

## Algorithm
Bot uses a *minimax algorithm*. It recursively goes through tree of legal moves evaluating the position to determine the best next move. Using *Alpha-Beta Pruning* it cuts off branches in the game tree	which need not be searched because a better move is already available.
## Installation
 **NOTE: Only Python 3.7 or later is supported!**
1. Clone [lichess-bot](https://github.com/ShailChoksi/lichess-bot/edit/master/README.md#how-to-install) installation giude to install lichess-bot
```
$ git clone https://github.com/ShailChoksi/lichess-bot.git
$ cd lichess-bot
```
2. Create virtual environment and install all dependencies
```
$ python3 -m venv venv # If this fails you probably need to add Python3 to your PATH.
$ virtualenv venv -p python3 # If this fails you probably need to add Python3 to your PATH.
$ source ./venv/bin/activate
$ python3 -m pip install -r requirements.txt
```
3. Copy `config.yml.default` to `config.yml`
4. Add python scrpits from this repo to `engines` directory
  - `main.py`
  - `bonuses.py`
5. In `strategies.py` import `play` from `main.py` and add
```python
class AVAChessEngine(MinimalEngine):
    def search(self, board, *args):
        return PlayResult(play(board), None)
```
6. In the `config.yml`, change the engine protocol to `homemade`
7. In the `config.yml`, change the name from `engine_name` to the name of your class
    - In this case, you could change it to:
        `name: "AVAChessEngine"`
## Usage
### Activating bot
After activating the virtual environment created in the installation steps (the `source` line for Linux and Macs or the `activate` script for Windows), run
```
$ python3 lichess-bot.py
```
The working directory for the engine execution will be the lichess-bot directory. If your engine requires files located elsewhere, make sure they are specified by absolute path or copy the files to an appropriate location inside the lichess-bot directory.

To output more information (including your engine's thinking output and debugging information), the `-v` option can be passed to lichess-bot:
```
$ python3 lichess-bot.py -v
```
## Playing against bot
Create a [challenge](https://lichess.org/?user=AVA-chess-engine#friend) and enjoy!

## Contributing

All bugs, feature requests, pull requests, feedback, etc., are welcome. [Create an issue](https://github.com/SerhiiStets/AVA-chess-engine/issues)
