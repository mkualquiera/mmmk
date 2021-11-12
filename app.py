# import quart stuff 

from quart import Quart, render_template, url_for, escape, send_from_directory, websocket, redirect, request, jsonify, Response, make_response

from bson import json_util
from feedgen.feed import FeedGenerator

from eth_account.messages import encode_defunct
from web3.auto import w3

import time

from random import choice

from os import path

import data

app = Quart(__name__)

@app.route('/')
@app.route('/index')
async def index():
    episodes_data = data.get_all_episodes_data()
    return await render_template('index.html', episode_data=episodes_data)

@app.route('/episode/<episode_id>')
async def episode(episode_id):
    episode_data = data.get_episode_data(episode_id)
    episode_images = data.get_episode_images(episode_id)
    episode_comments = data.get_episode_comments(episode_id)
    return await render_template('episode.html', episode_data=episode_data, 
                                            episode_images=episode_images,
                                            episode_comments=episode_comments)

def rand_string(length):
    import string
    import random
    return ''.join(random.choice("0123456789abcdef") for i in range(length))

@app.route('/files/images/<episode_id>/<image_filename>')
async def image(episode_id, image_filename):
    # Sanitize the input
    episode_id = escape(episode_id)
    image_filename = escape(image_filename)
    # Send the image as a file download
    directory = path.join(data.DATA_DIR,episode_id,'images')
    return await send_from_directory(directory, image_filename)

@app.route('/first')
async def first():
    episodes_data = data.get_all_episodes_data()
    # Sort by number
    episodes_data = sorted(episodes_data, key=lambda k: int(k['number']))
    first = episodes_data[0]
    # Redirect to the first episode
    return redirect(url_for('episode', episode_id=first['number']))

@app.route('/last')
async def last():
    episodes_data = data.get_all_episodes_data()
    # Sort by number
    episodes_data = sorted(episodes_data, key=lambda k: int(k['number']))
    last = episodes_data[-1]
    # Redirect to the last episode
    return redirect(url_for('episode', episode_id=last['number']))

@app.route('/random')
async def random():
    episodes_data = data.get_all_episodes_data()
    # Sort by number
    # Pick a random episode
    random_episode = choice(episodes_data)
    # Redirect to the random episode
    return redirect(url_for('episode', episode_id=random_episode['number']))

@app.route('/episode/<episode_id>/prev')
async def previous(episode_id):
    episode_data = data.get_episode_data(episode_id)
    # Get the previous episode
    prev_num = int(episode_data['number']) - 1
    # Find a previous episode with that number
    for other in data.get_all_episodes_data():
        if int(other['number']) == prev_num:
            return redirect(url_for('episode', episode_id=other['number']))
    # If there is no previous episode, redirect to the first episode
    return redirect(url_for('first'))

@app.route('/episode/<episode_id>/next')
async def next(episode_id):
    episode_data = data.get_episode_data(episode_id)
    # Get the next episode
    next_num = int(episode_data['number']) + 1
    # Find a next episode with that number
    for other in data.get_all_episodes_data():
        if int(other['number']) == next_num:
            return redirect(url_for('episode', episode_id=other['number']))
    # If there is no next episode, redirect to the last episode
    return redirect(url_for('last'))

# Websocket endpoint
@app.websocket('/api/v1/ws')
async def websocket_endpoint():
    print("aaa")

    message = await websocket.receive()
    msg_data = json_util.loads(message)

    if msg_data['type'] != 'meta':
        await websocket.send(json_util.dumps({'type':'posted', 
            'error':'Expected a message of type meta'}))
        return

    print(msg_data)

    episode = msg_data["episode"]
    text = msg_data["text"]
    address = msg_data["address"][2:]

    # Get the current time and date string with timezone
    time_str = time.strftime("%Y-%m-%d %H:%M:%S %Z", time.localtime())
    timestamp = int(time.time())
    
    if address == '0':
        # Anonymous comment
        nickname = 'Anonymous'
        address = "0000000000000000000000000000000000000000"
        signature = rand_string(64) + "(unsigned)"
        text_to_sign = rand_string(64) + "(unsigned)"
        data.post_comment(episode, text, address, nickname, text_to_sign,
            signature, time_str, timestamp)
        await websocket.send(json_util.dumps({'type': 'posted', 'success':True}))
        return
    

    # Check if address has a nickname
    nickname = data.get_addr_nickname(address)
    if not nickname:
        await websocket.send(json_util.dumps({'type': 'nickname'}))
        nickname_response = await websocket.receive()
        nickname_data = json_util.loads(nickname_response)

        if nickname_data['type'] != 'nickname':
            await websocket.send(json_util.dumps({'type':'posted', 
                'error':'Expected a message of type nickname'}))
            return

        nickname = nickname_data['nickname']
        data.set_addr_nickname(address, nickname)
    else:
        nickname = nickname["nickname"]

    # Build the text to be signed
    text_to_sign = f'mmmk({episode})@{time_str}:{text}:{nickname}:{address}'

    # Sign the text
    await websocket.send(json_util.dumps({'type': 'sign', 'text': text_to_sign}))

    signature_response = await websocket.receive()
    signature_data = json_util.loads(signature_response)

    if signature_data['type'] != 'signature':
        await websocket.send(json_util.dumps({'type':'posted', 
            'error':'Expected a message of type signature'}))
        return

    signature = signature_data['signature'][2:]
    
    encoded_text = encode_defunct(text=text_to_sign)

    recovered = w3.eth.account.recover_message(encoded_text, signature=signature)[2:].lower()

    if recovered == address:
        data.post_comment(episode, text, address, nickname, text_to_sign,
            signature, time_str, timestamp)
        await websocket.send(json_util.dumps({'type': 'posted', 'success':True}))
    else:
        await websocket.send(json_util.dumps({'type': 'posted', 'error':
            "Unable to verify the message signature"}))

@app.route('/rss')
async def rss():
    fg = FeedGenerator()
    fg.title("mmmk")
    fg.description("mmmk: the webcomic by mkualquiera")
    fg.link(href="http://mmmk.huestudios.xyz/")

    for episode in data.get_all_episodes_data():
        fe = fg.add_entry()
        fe.title(episode['title'])
        fe.guid(episode['number'])
        fe.link(href=f"http://mmmk.huestudios.xyz/episode/{episode['number']}")
        fe.description(f"{episode['description']}")
        fe.pubDate(episode['when_written'])
        fe.author(name='mkualquiera',email='ozjuanpa@gmail.com')

    response = make_response(fg.rss_str(pretty=True))
    response.headers.set('Content-Type','application/rss+xml')
    return response
            
app.run("0.0.0.0", debug=True, port=81)