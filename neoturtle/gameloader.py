
import os
import importlib
import traceback

from utils import Log

Log = Log()

def load_games():
    games = {}
    for file_name in os.listdir('neoturtle/games'):
        if file_name.endswith('.py'):
            game_name = os.path.splitext(file_name)[0]
            module_path = f"neoturtle.games.{game_name}"
            try:
                module = importlib.import_module(module_path)
                games[game_name] = {
                    'listen': getattr(module, 'listen_game'),
                    'setup_game': getattr(module, 'setup_game'),
                    'use_hint': getattr(module, 'use_hint', None),
                }
            except Exception as e:
                Log.error(f"Error loading game '{game_name}':\n{traceback.format_exc()}")
    return games
