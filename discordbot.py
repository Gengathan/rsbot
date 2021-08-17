import json
import os
import random

import asyncio
import discord
import osrs_highscores

from dotenv import load_dotenv

## UPDATE LEVEL UP MESSAGE TO INCLUDE ACHIEVEMENT WHEN LEVEL REACHED ##


## automated reaction upon new screenshot functions ##

def images_to_post(where=os.path.join(os.path.dirname(__file__), 'image_paths.txt')):

    screenshot_dir = 'C:\\Users\\GITGUDPC\\.runelite\\screenshots\\'

    if not os.path.isfile(where):
        starting_images = get_images_in_dir(screenshot_dir)
        with open(where, 'w') as o:
            o.write('\n'.join(starting_images))
        return set()

    else:
        with open(where, 'r') as f:
            previous_images = set(f.read().split('\n'))
        current_images = set(get_images_in_dir(screenshot_dir))
        new_images = current_images.difference(previous_images)

        with open(where, 'w') as o:
            o.write('\n'.join(current_images))

        directories_to_skip = ['Boss Kills', 'Chest Loot']
        new_images = [image for image in new_images if any(dir in image for dir in directories_to_skip) != True]
        num_current_images = len(current_images)
        if len(new_images) > 0:
            print(f'{len(new_images)} new images detected, current image count: {num_current_images}')
        else:
            print(f'no new images detected, current image count: {num_current_images}')
        return new_images


def get_images_in_dir(dirpath):

    paths = []
    for dr, subdrs, files in os.walk(dirpath):
        for f in files:
            if f.endswith('.png'):
                paths.append(os.path.join(dr, f))
    return paths


def generate_image_message(image):

    image_folder = os.path.split(os.path.dirname(image))[-1]
    image_name = os.path.basename(image)

    if image_folder == 'Clue Scroll Rewards':
        level = image_name.split('(')[0].lower()
        number = image_name.split('(')[1].split(')')[0]
        message = f'A clue scroll of difficulty {level} was just completed. That makes number {number}! Hope the rewards weren\'t crap :smile:'

    elif image_folder == 'Deaths':
        message = 'Uh oh, guess who died... AGAIN. What a dumbass :rolling_eyes: Better hurry and get your gear back :scream:'

    elif image_folder == 'Kingdom Rewards':
        message = 'Know those gps you put all that effort in to collect? Well, they\'re gone now! Hope you\'re happy with what your subjects produced :seedling:'
        
    elif image_folder == 'Collection Log':
        item = image_name.split('(')[1].split(')')[0]
        message = f'Look at this, I just found the "{item}"! A completely new item to add to the collection log :bookmark: :eyes: '


    elif image_folder == 'Levels':
        skill = image_name.split('(')[0]
        level = image_name.split('(')[1].split(')')[0]

        message = []

        # check for 69
        if level != '69':
            message.append(f'Sorcerer2125\'s {skill} level just reached level {level}!')
        else:
            message.append(f'IT\'S THE NUMBEEEER!!! Sorcerer2125\'s {skill} level just reached level {level}! :smirk:')

        # check skill progress
        message.append(check_goal_req_progress(skill, level))

#        # check quest cape progress
#        message.append(check_main_goal_req_progress('quest', skill, level))

        # check diary cape progress
        message.append(check_main_goal_req_progress('diary', skill, level))

        message.append('The grind continues!')
        
        message = '\n'.join(message)

    elif image_folder == 'Quests':
        name = image_name.split('(')[1].split(')')[0]
        message = f'Quest completed! "{name}" can be scratched from the TODO list!'

    elif image_folder == 'Boss Kills':
        boss_name = image_name.split('(')[0]
        number = image_name.split('(')[1].split(')')[0]
        message = f'Did you see that finishing hit?! Sorcerer2125 just defeated {boss_name} {number} time(s), what a total badass!!! :sunglasses:'

    elif image_folder == 'Chest Loot':
        name = ' '.join(image_name.split(' ')[:-1])
        message = f'A chest from {name} was just looted! Look at those amazing rewards :eyes:!'

    else:
        message = 'I have no idea what just happened, but my human must have thought it important enough to make me post it. Silly humans :robot:'

    return message


def check_main_goal_req_progress(goal, skill, level):

    skill = skill.capitalize()

    assert goal in ['quest', 'diary']

    req_file = f'E:\\Bestanden\\Programming\\discordbot\\{goal}_lvl_reqs.txt'
    with open(req_file, 'r') as f:
        data = f.read().splitlines()

    req_dict = {}
    for line in data:
        req_skill, req_level = line.split()
        req_dict[req_skill] = req_level

    req_diff = int(req_dict[skill]) - int(level)

    if req_diff > 0:
        message = f'Only {req_diff} levels to go until the level required to get the {goal.capitalize()} cape.'
    elif req_diff == 0:
        message = f':partying_face: :partying_face: Sorcerer2125 just achieved the required {level} {skill} for the {goal.capitalize()} cape!!! :partying_face: :partying_face:'
    else:
        message = f'You\'ll never believe it, but the {skill} requirement for the {goal.capitalize()} cape has already been achieved.. Go grind something else!'

    return message


## bot answer to message query functions ##

def check_goal_req_progress(skill, level):

    message = []

    skill = skill.capitalize()
    goals_json = read_goals()

    level_goals = goals_json['Levels']
    skill_goal = level_goals[skill]
    level_goals = sorted(list(skill_goal.keys()))

    if level in level_goals:
        message.append(f':partying_face: Huzzah! The following {skill} goal has been obtained: {skill_goal[level]}! :partying_face:')

    next_level_goal = [target_level for target_level in level_goals if int(target_level) > int(level)][0]
    skill_req_diff = int(next_level_goal) - int(level)

    if skill != "Firemaking":
        message.append(f'Only {skill_req_diff} {skill} levels to go until the level required for "{skill_goal[next_level_goal]}".')
    else:
        message.append("But whyyyyy?")

    return '\n'.join(message)


def summarize_goals(target, current_level):

    target = target.capitalize()
    goals_json = read_goals()

    message = []
    for goal_type in goals_json: # example: levels or bosses
        if goal_type == 'Levels':
            for skill in goals_json[goal_type]: # example: slayer or farming
                if skill == target:
                    message.append(f'{target}:')
                    for specific_goal_level in goals_json[goal_type][target]:
                        if specific_goal_level <= current_level:
                            continue
                        else:
                            specific_goal_unlock = goals_json[goal_type][target][specific_goal_level]
                            message.append(f'\tLevel {specific_goal_level} for "{specific_goal_unlock}".')
            break

    if message == []:
        raise KeyError

    return '\n'.join(message)


def read_goals():

    goals_file = os.path.join(os.path.dirname(__file__), 'goals.json')
    with open(goals_file) as json_file:
        goals_json = json.load(json_file)
    return goals_json


def parse_text(message):

    message_text = message.content.lower()
    answer = []

    fixed_reactions = {
        'hail to': ['Our robot overlady!', 'Lizzy :heart_eyes:'],
        'lizzy': [':heart_eyes:', ':anatomical_heart:', 'Liz is the best'],
        'skills': ['The RuneScape skills are: Agility, Attack, Construction, Cooking, Crafting, Defence, Farming, Firemaking, Fishing, Fletching, Herblore, Hitpoints, Hunter, Magic, Mining, Prayer, Ranged, Runecraft, Slayer, Smithing, Strength, Thieving, Woodcutting']
    }

    if 'rsbot' not in message_text:
        if 'hail to' in message_text:
            answer.append(random.choice(fixed_reactions['hail to']))

        if 'lizzy' in message_text:
            answer.append(random.choice(fixed_reactions['lizzy']))

    elif 'rsbot' == message_text:

            answer.append('Hi! I\'m your favourite RuneScapeProgressBot!')
            answer.append('To get my attention, mention **rsbot** anywhere in your message.')
            answer.append('If you also want to get some useful information out of me, mention any of the following keywords: "**goals**, **progress**, **current**, **quest**" together with the name of one or more skills.')
            answer.append('If you want to know what the RuneScape skills are, mention the word **skills** somewhere (like I just did - see?).')

    elif 'rsbot' in message_text:

        user = osrs_highscores.Highscores("sorcerer2125", target="ironman")
        words = sorted(list(set([word.replace(',', '') for word in message_text.split(' ')])))

        for word in words:
            if word in fixed_reactions:
                answer.append(random.choice(fixed_reactions[word]))

        if 'goals' in words or 'goal' in words:
            answer.append('**Goals:**')
            for word in words:
                try:
                    answer.append(summarize_goals(word, user.__dict__[word].level))
                except KeyError:
                    continue

        if 'progress' in words:
            answer.append('**Progress:**')
            for word in words:
                try:
                    answer.append(check_goal_req_progress(word, user.__dict__[word].level))
                except KeyError:
                    continue

        if 'current' in words:
            answer.append('**Current progress:**')
            for word in words:
                if word in user.__dict__:
                    current_word = user.__dict__[word]
                    answer.append(f'{word.capitalize()}:')
                    for item, value  in current_word.items():
                        answer.append(f'\t{item.capitalize()} is {value}.')

        if 'quest' in words:
            answer.append('**Quest progress:**')
            for word in words:
                try:
                    answer.append(check_main_goal_req_progress('quest', word, user.__dict__[word].level))
                except KeyError:
                    continue

        if 'diary' in words:
            answer.append('**Diary progress:**')
            for word in words:
                try:
                    answer.append(check_main_goal_req_progress('diary', word, user.__dict__[word].level))
                except KeyError:
                    continue
                    
    if len(answer) > 0:
        return '\n'.join(answer)
    else:
        return


if __name__ == "__main__":
    
    load_dotenv()
    TOKEN = os.getenv('DISCORD_TOKEN')
    CHANNEL_ID = os.getenv('DISCORD_CHANNEL_ID')
    client = discord.Client()

    profile_picture_path = 'E:\\Bestanden\\Programming\\discordbot\\1200px-Quests.png'
    profile_picture = open(profile_picture_path, 'rb').read()

    @client.event
    async def on_ready():
        print(f'We have logged in as {client.user}')
        await client.user.edit(avatar=profile_picture)

    @client.event
    async def on_message(read_message):
        write_message = parse_text(read_message)
        if write_message != None:
            await read_message.channel.send(write_message)

    async def check_progress_background_task():
        await client.wait_until_ready()

        channel = client.get_channel(int(CHANNEL_ID))

        while not client.is_closed():
            #try:
            images = images_to_post()
            for image in images:
                message = generate_image_message(image)
                await channel.send(message)
                await channel.send(file=discord.File(image))
            await asyncio.sleep(5)
            #except Exception as e:
            #    print(str(e))
            #    await asyncio.sleep(5)

    client.loop.create_task(check_progress_background_task())
    client.run(TOKEN)