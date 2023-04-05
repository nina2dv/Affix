import requests
import ety
import streamlit as st
import json
import textwrap
from string import ascii_lowercase
import re
from random import randint


class Word:
    def __init__(self, name):
        self.name = name
        self.definitions = []

def getWord():
    with open("wordsList.txt", "r") as read_file:
        advanced_words = read_file.read().split()   #taken from "https://svnweb.freebsd.org/csrg/share/dict/words?revision=61569&view=co"
        common_words = open("commonWords.txt").read().split()  #list of common words that we users would already know
    while True:
        num = randint(0, len(advanced_words))
        chosen_word = advanced_words[num]
        if chosen_word not in common_words and not chosen_word[0].isupper():
            return chosen_word

def getDefinition(word):
    KEY = st.secrets["KEY"] #used in API call
    requestURL = 'https://www.dictionaryapi.com/api/v3/references/collegiate/json/'+ str(word) +'?key=' + KEY # str(chosen_word)
    apiResponse = requests.get(requestURL) #http GET request of URL using requests library
    return json.loads(apiResponse.content)

def parseInfo(word_entry):
    word_dict = {}
    definition_dict = {}
    # print(word_entry)
    try:
        word_dict['class'] = word_entry['fl']  #fl is the functional label aka class of the word
        # print(word_entry['fl'])
    except Exception as e:
        word_dict['class'] = 'No Class Type Specified'
    for index, definition in enumerate(word_entry['shortdef']):
        definition_dict[index+1] = definition
    word_dict['definition'] = definition_dict
    return(word_dict)

def generateWordAndDefenition():
    chosen_word = getWord()
    word_info = getDefinition(chosen_word)
    ety_origin = " - "
    if not any(isinstance(info, dict) for info in word_info): #if the api response isn't a dictionary, that means it couldn't find the word and we need a new one
        ourWord, date, ety_list, ety_background = generateWordAndDefenition()
    else:
        ourWord = Word(chosen_word)
        definitions_list = []
        if 'hom' in word_info[0]: #if there are multiple homonym print them, otherwise just print the main definition
            definitions_list = [parseInfo(entry) for entry in word_info if entry.get('shortdef') and entry.get('hom')] #.get() checks that the hom and shortdef 1) exist and 2) are not null
            ourWord.definitions = definitions_list
        elif word_info[0].get('shortdef'):
            definitions_list  = [parseInfo(word_info[0])]
            ourWord.definitions = definitions_list
        else:    #if the chosen word didn't have a usable definition, get another
            ourWord, date, ety_origin, ety_background = generateWordAndDefenition()

        if word_info[0].get('date'):
            date = re.sub(r"{.*?}", "",word_info[0].get('date'))
        else:
            ourWord, date, ety_origin, ety_background = generateWordAndDefenition()
        if word_info[0].get('et'):
            ety_list = word_info[0]['et'][0][1:]
            for x in ety_list:
                ety_word = re.sub(r"{.*?}", "", x)
                replaceText(ety_word, chosen_word)
                ety_word = textwrap.fill(ety_word, 80)
                ety_origin += ety_word
            if len(ety_origin) <= 6:
                ourWord, date, ety_origin, ety_background = generateWordAndDefenition()
            ety_background = replaceText(str(ety.tree(chosen_word)), chosen_word)
            if ety_background == "":
                ourWord, date, ety_origin, ety_background = generateWordAndDefenition()
        else:
            ourWord, date, ety_origin, ety_background = generateWordAndDefenition()

    return ourWord, date, ety_origin, ety_background

def formatDefinitions(class_definitions):
    formatted_definitions = ''
    for index, definition in enumerate(class_definitions):
        formatted_definitions += "{}) ".format(ascii_lowercase[index])
        longtext = textwrap.wrap(class_definitions[definition], 80)
        for text in longtext:
            formatted_definitions += "{} \n".format(text)
    return formatted_definitions

def listingPrint(m, chosenWord):
    for p in m:
        st.text("\t > " + replaceText(str(p), chosenWord))


def replaceText(text, name):
    newText = re.sub(rf"\b{name}\b", "******", text)
    return str(newText)

def form_callback(word):
    st.session_state.word = word
    # st.session_state.guess

st.set_page_config(page_title="Affix", page_icon="❓")
st.title("Affix")
form = st.form(key='my_form')
word, date, ety_list, ety_background = generateWordAndDefenition()
text1 = word.name  # the word
form.write("First known use: %s" % date)
form.write("Origins: ")
form.markdown(f"""{ety_list}""")
form.text(r"{}".format(ety_background))
text2 = ''  # the definition
classNum = ''  # for words with multiple classes (nouns, adjectives, etc.)
for i in range(len(word.definitions)):
    if len(word.definitions) > 1:
        classNum = f'{i + 1}: '
    text2 += (
        f'{classNum}{word.definitions[i]["class"]}\n{formatDefinitions(word.definitions[i]["definition"])}\n')

form.text(replaceText(text2, text1))

generatedWordLength = len(text1)
coverWord = "-" * generatedWordLength
search = " "
# search = form.text_input(label='Guess the word', key='guess').lower()
submit_button = form.form_submit_button(label='Refresh')

if submit_button and search is not None:
    if form_callback(text1):
        form.success("Correct")
        pass
    elif search == "hint" and coverWord.count("-") != 0:
        randIndexLetter = randint(0, generatedWordLength - 1)
        while coverWord[randIndexLetter] != "-":
            randIndexLetter = randint(0, generatedWordLength - 1)
        coverWord = coverWord[:randIndexLetter] + text1[randIndexLetter] + coverWord[randIndexLetter + 1:]
        form.write(coverWord)
    elif search == "hint" and coverWord.count("-") == 0:
        form.warning("No more hints!")
    elif search == "skip":
        pass
    else:
        pass
        # form.warning("Incorrect")

with form.expander('Answer', expanded=False):
    st.success(text1)
