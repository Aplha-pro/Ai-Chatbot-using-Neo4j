from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login
from py2neo import Node, Graph, Relationship
from neo4j import Driver, GraphDatabase
from nltk.tokenize import word_tokenize
from django.shortcuts import redirect
from django.http import HttpResponse
from django.shortcuts import render
from django.contrib import messages
from nltk.corpus import stopwords
from nltk.corpus import wordnet
from nltk.chunk import ne_chunk
from .models import CustomUser
from bs4 import BeautifulSoup
from .forms import LoginForm
from nltk.tag import pos_tag
from pyswip import Prolog
from py2neo import Graph
from glob import glob
import requests
import datetime
import string
import socket
import spacy
import aiml
import time
import aiml
import nltk
import re
import os


# Set up the connection parameters
uri = "bolt://localhost:7687"
user = "neo4j"
password = "12345678"

# Establish a connection to Neo4j
driver = GraphDatabase.driver(uri, auth=(user, password))



def home(request):
    return render(request, 'home.html')

def signup(request):
    if request.method == 'POST':
        fullname = request.POST['fullname']
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm-password']

        create_user_credentials(fullname, username, email, password)
        ip_address = getip()
        create_user_credentials('IP Address', 'NULL', 'NULL', ip_address)
        create_relationship(fullname, 'IP Address', 'has_IP_Address')

        if password != confirm_password:
            return render(request, 'signup.html', {'error': 'Passwords do not match'})
        return redirect('login')
    return render(request, 'signup.html')

def login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('chatbox')  # Replace 'chatbox' with the appropriate URL or view name for the chatbox page
            else:
                error_message = 'Invalid username or password'
                return render(request, 'login.html', {'form': form, 'error_message': error_message})
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})


def create_relationship(person1, person2, relationship):
        with driver.session() as session:
            session.run(
                "MATCH (p1:User), (p2:User) "
                "WHERE p1.full_name = $person1 AND p2.full_name = $person2 "
                "CREATE (p1)-[r:" + str(relationship) + "]->(p2)",
                person1=person1,
                person2=person2,
                relationship=relationship
            )

def create_user_credentials(full_name, username, email, password):
    with driver.session() as session:
        # Create the user node and set attributes
        session.run(
            "CREATE (u:User {full_name: $full_name, username: $username, email: $email, password: $password})",
            full_name=full_name,
            username=username,
            email=email,
            password=password
        )


def contact(request):
    return render(request, 'contact.html')


def chatbox(request):
    return render(request, 'chatbox.html')


def get_word_definition(word):
    synsets = wordnet.synsets(word)
    if synsets:
        definition = synsets[0].definition()
        return definition
    else:
        return "sorry"


def getip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    return s.getsockname()[0]



def process_input(input_text):
    tokens = word_tokenize(input_text.lower())
    filtered_tokens = [token for token in tokens if token.isalnum() and token not in stopwords.words('english')]
    word_frequency = nltk.FreqDist(filtered_tokens)
    exclude_words = ['meant', 'meaning', 'definition', 'mean', 'define', 'procedure', 'what is a', 'what is an', 'tell', 'about', 'yourself']
    filtered_frequency = [(word, freq) for word, freq in word_frequency.items() if word not in exclude_words]
    if len(filtered_frequency) > 0:
        word_to_define = max(filtered_frequency, key=lambda item: item[1])[0]
    else:
        return "sorry"
    definition = get_word_definition(word_to_define)
    response = f"The definition of '{word_to_define}' is: {definition}"
    if definition == 'sorry':
        return 'sorry'
    return response


def scrape_wikipedia(query, num_sentences=3):
    url = f"https://en.wikipedia.org/wiki/{query.replace(' ', '_')}"
    try:
        # Send a GET request to the Wikipedia page
        response = requests.get(url)
        response.raise_for_status()
        # Parse the HTML response
        soup = BeautifulSoup(response.text, "html.parser")
        # Find the main content element
        content_div = soup.find(id="mw-content-text")
        if content_div:
            # Find the paragraphs within the content element
            paragraphs = content_div.find_all("p")
            if paragraphs:
                # Extract the text from the paragraphs
                text = " ".join([paragraph.get_text() for paragraph in paragraphs])
                # Remove citations and references
                text = re.sub(r"\[\d+\]", "", text)
                # Extract the desired number of sentences
                sentences = re.split(r"(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s", text)
                shortened_text = ". ".join(sentences[:num_sentences])
                return shortened_text
            else:
                return "No information found on Wikipedia."
        else:
            return "No information found on Wikipedia."
    except requests.exceptions.HTTPError:
        return "Failed to retrieve information from Wikipedia."
    except requests.exceptions.RequestException:
        return "Error occurred while retrieving information from Wikipedia."

target_words = ['meant', 'meaning', 'definition', 'mean', 'explain', 'explaination', 'tell', 'define', 'procedure', 'what is a', 'what is an']



def getresponse(request):
    kernel = aiml.Kernel()
    for filename in os.listdir(("aimlfiles")):
        if filename.endswith(".aiml"):
            kernel.learn("aimlfiles/" + filename)
    user_message = request.GET.get('msg')
    target = 'wikipedia'
    if target.lower() in user_message:
        query = user_message.replace('what wikipedia say about', '').strip()
        bot_response = scrape_wikipedia(query)
        return HttpResponse(bot_response, content_type='text/plain')
    for word in target_words:
        if word in user_message:
            bot_response = process_input(user_message)
            if bot_response == 'sorry':
                break
            return HttpResponse(bot_response, content_type='text/plain')
    target = 'ip'
    if target.lower() in user_message:
        bot_response =getip()
        return HttpResponse(bot_response, content_type='text/plain')
    if 'likes' in user_message:
        tokens = user_message.split()
        p1 = tokens[0]
        p2 = tokens[2]
        relation = tokens[1]
        print('I know that', p1, relation, p2)
        create_user_credentials(p1, 'NULL', 'NULL', 'NULL')
        create_user_credentials(p2, 'NULL', 'NULL', 'NULL')
        create_relationship(p1, p2, relation)
        bot_response = 'Thanks for telling me!'
        return HttpResponse(bot_response, content_type='text/plain')

    else:
        bot_response = kernel.respond(user_message)
    return HttpResponse(bot_response, content_type='text/plain')
