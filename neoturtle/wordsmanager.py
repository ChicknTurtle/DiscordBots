
import os
import json
import traceback

from utils import *

Log = Log()

def load_wordlists():
    wordlists = {}
    for root, _, files in os.walk('assets/wordlists/'):
        for file in files:
            file_path = os.path.join(root, file)
            name = os.path.relpath(file_path, 'assets/wordlists/')
            name = os.path.splitext(name)[0]
            file_ext = os.path.splitext(file)[1].lower()
            try:
                # Load text file
                if file_ext == '.txt':
                    with open(file_path, 'r') as f:
                        wordlists[name] = f.read().splitlines()
                # Load json file
                elif file_ext == '.json':
                    with open(file_path, 'r') as f:
                        wordlists[name] = json.load(f)
                        wordlists[name] = list(wordlists[name].keys())
            except Exception as e:
                Log.error(f"Error loading wordlist '{file_path}':\n{traceback.format_exc()}")
    return wordlists

def load_anagrams(dictionary: list, words: list[str]):
    dictionary_set = set(dictionary)
    dictionary_set.update(words)

    anagrams_dict = {}
    for word in dictionary_set:
        sorted_word = ''.join(sorted(word))
        anagrams_dict.setdefault(sorted_word, []).append(word)

    result = {}
    for word in words:
        sorted_word = ''.join(sorted(word))
        anagram_list = anagrams_dict.get(sorted_word, [])
        
        # Move original word to beginning
        if anagram_list and anagram_list[0] != word:
            anagram_list.remove(word)
            anagram_list.insert(0, word)
        
        result[sorted_word] = anagram_list
    return result

class WordsManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        # Load wordlists
        Log.log("Loading wordlists...")
        self.wordlists = load_wordlists()
        # Load anagrams
        Log.log("Loading anagrams...")
        self.anagrams = {
            'main': load_anagrams(self.wordlists['dictionary'], self.wordlists['unscramble/main']),
            'halloween': load_anagrams(self.wordlists['dictionary'], self.wordlists['unscramble/halloween']),
            'christmas': load_anagrams(self.wordlists['dictionary'], self.wordlists['unscramble/christmas'])
        }

