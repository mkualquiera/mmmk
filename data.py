# import pymongo stuff
from pymongo import MongoClient

# import yaml stuff
from yaml import load, dump, FullLoader

import os

# connect to the database
CLIENT = MongoClient()

# Make sure to get path relative to this file
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

def get_episode_data(episode_id):
    episode = {}
    episode["number"] = episode_id
    # meta.yaml is the file that contains the episode metadata
    with open(os.path.join(DATA_DIR, episode_id, 'meta.yaml')) as f:
        episode.update(load(f, Loader=FullLoader))

    return episode

def get_episode_images(episode_id):
    # The images are in the data/<episode>/images folder    
    images = []
    for image_file in os.listdir(os.path.join(DATA_DIR, episode_id, 'images')):
        images.append(os.path.join(image_file))
    # sort the images by filename
    images.sort()
    return images


def get_all_episodes_data():
    # Each folder in the data folder is an episode
    episodes = []
    for episode_folder in os.listdir(DATA_DIR):
        episode = get_episode_data(episode_folder)
        episodes.append(episode)
    
    # sort by number
    episodes.sort(key=lambda x: x["number"])

    return episodes

def get_episode_comments(episode_number):
    # The comments are on the mongo database
    comments = list(CLIENT.mmmk.comments.find(
        {"episode": episode_number}
    ))
    # Sort descending by timestamp
    comments.sort(key=lambda x: x["timestamp"], reverse=True)
    return comments

def get_addr_nickname(address):
    return CLIENT.mmmk.nicknames.find_one({"address": address})

def set_addr_nickname(address, nickname):
    CLIENT.mmmk.nicknames.insert_one({"address": address, "nickname": nickname})

def post_comment(episode, text, address, nickname, signed, signature, 
    time_str, timestamp):
    CLIENT.mmmk.comments.insert_one({
        "episode": episode,
        "text": text,
        "address": address,
        "nickname": nickname,
        "signed": signed,
        "signature": signature,
        "time_str": time_str,
        "timestamp": timestamp
    })