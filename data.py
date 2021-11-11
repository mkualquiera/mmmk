# import pymongo stuff
from pymongo import MongoClient

# import yaml stuff
from yaml import load, dump, FullLoader

import os

# connect to the database
CLIENT = MongoClient()

DATA_DIR = 'data'

def get_episode_data():
    # Each folder in the data folder is an episode
    episodes = []
    for episode_folder in os.listdir(DATA_DIR):
        episode = {}
        episode["number"] = int(episode_folder)
        # meta.yaml is the file that contains the episode metadata
        with open(os.path.join(DATA_DIR, episode_folder, 'meta.yaml')) as f:
            episode.update(load(f, Loader=FullLoader))
        # all image files are in the images folder
        # they should be sorted by number
        episode["images"] = []
        for image_file in os.listdir(os.path.join(DATA_DIR, episode_folder, 
                                                'images')):
            episode["images"].append(os.path.join(DATA_DIR, episode_folder, 
                                    'images', image_file))
        episodes.append(episode)

    return episodes

def get_episode_comments(episode_number):
    # The comments are on the mongo database
    comments = list(CLIENT.comments.comments.find(
        {"episode": episode_number}
    ))
