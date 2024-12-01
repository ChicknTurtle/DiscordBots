
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

def load_anagrams2(dictionary:list, words:list[str]):

    # Make sure all words are also in dictionary
    for word in words:
        if word not in dictionary:
            dictionary.append(word)
    
    # Remove duplicate anagrams from words
    words2 = {}
    for word in words:
        key = ''.join(sorted(word))
        if key not in words2:
            words2[key] = word
    words = list(words2.values())

    # Create a dictionary where the key is the sorted word and the value is a list of anagrams
    anagrams_dict = {}
    for dict_word in dictionary:
        sorted_word = ''.join(sorted(dict_word))
        if sorted_word not in anagrams_dict:
            anagrams_dict[sorted_word] = []
        anagrams_dict[sorted_word].append(dict_word)

    # Find anagrams for each word in 'words'
    result = {}
    for word in words:
        sorted_key = ''.join(sorted(word))
        result[sorted_key] = anagrams_dict.get(sorted_key, [])

    return result

def load_anagrams(dictionary: list, words: list[str]):
    # Ensure all words are in the dictionary
    dictionary_set = set(dictionary)  # Set for O(1) lookup
    dictionary_set.update(words)  # Add words to dictionary

    # Create a dictionary where the key is the sorted word and the value is a list of anagrams
    anagrams_dict = {}
    for word in dictionary_set:
        sorted_word = ''.join(sorted(word))  # Sort the word to form a key
        anagrams_dict.setdefault(sorted_word, []).append(word)

    # Create the result based on the words
    result = {''.join(sorted(word)): anagrams_dict.get(''.join(sorted(word)), []) for word in words}

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

