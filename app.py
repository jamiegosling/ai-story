from flask import Flask
from flask import render_template
from flask import request
from flask import jsonify

from openai import OpenAI
import shutil
import uuid
import requests
import os
import logging
from logging.config import dictConfig

key=os.environ.get('KEY')
OpenAI.api_key=key
client = OpenAI(
    api_key=key
)

dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    }
})

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/result', methods=['POST'])
def result():
    id = str(uuid.uuid4())
    book_prompt = request.form.get('user_input')
    print(f"User entered: {book_prompt}")
    book_contents = generate_text(book_prompt, id)

    return jsonify({ 'result' : book_contents})

@app.route('/result_image', methods=['POST'])
def result_with_image():
    id = str(uuid.uuid4())
    book_prompt = request.form.get('user_input')
    print(f"User entered: {book_prompt}")
    book_contents = generate_text(book_prompt, id)
    image_url = generate_image(book_contents, id)
    return jsonify({ 'result' : book_contents, 'image_url': image_url})


def generate_text(book_prompt, id):
    try:
        log(book_prompt, id)
        prompt = [ 
            "You are a children's author, writing a three paragraph poem.",
            " each paragraph has four lines, alternate lines rhyming.",
            "you will write a poem based on the user prompt where they will tell you what they like.",
            " where possible you will rhyme the things they tell you they like, and the name they give you.",
            "write a verse for each thing they like"]
        
        completion = client.chat.completions.create(
        model="gpt-4o",

        messages=[
            {"role": "system", "content": ''.join(prompt)},
            {"role": "user", "content": book_prompt }
        ]
        )
    except Exception as e:
        print(e.status_code)
        print(e.response)
    book_contents = completion.choices[0].message.content
    print(book_contents, end='\n')

    with open("result/" + id + ".txt",'a') as f:
        f.write(book_contents)
    
    return book_contents


    
def generate_image(book_prompt, id):
    try:
        print()
        print('getting image')
        response = client.images.generate(
        model="dall-e-3",
        # prompt="a cartoon image using pastel colours which illustrates a short poem, try and include all the items which are in the poem. do not include any words or letters in the image. if there are trains do not give them faces. the poem is about:" + book_prompt,
        # prompt="a cartoon image using pastel colours which illustrates a short story, try and include all the items which are in the story. do not give any inanimate objects faces. . try not to include any words or text. the text of the story is:" + book_prompt,
        prompt="" + book_prompt,
        size="1024x1024",
        quality="standard",
        n=1,
        )
    except Exception as e:
        print(e.status_code)
        print(e.response)

    image_url = response.data[0].url
    print(image_url)
    revised_prompt = response.data[0].revised_prompt
    log(revised_prompt, id)
    local_path = "result/" + id + ".png"
    res = requests.get(image_url, stream = True)
    with open(local_path,'wb') as f:
        shutil.copyfileobj(res.raw, f)
    return image_url

def log(input,id):
    print(input, end='\n')
    with open("result/" +id + ".log", 'a') as f:
        f.write(input + '\n')