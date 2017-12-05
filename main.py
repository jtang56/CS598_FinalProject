############################## HELPFUL URLs #########################################
# https://www.fullstackpython.com/blog/build-first-slack-bot-python.html
# https://slackapi.github.io/python-slackclient/
#####################

######################### STEPS Before starting modifying your bot-code here ###########################
# install slackclient. Use "conda install -c conda-forge slackclient"  OR "pip install slackclient"

# Give a unique name to your bot. <BOTNAME>

# Send me <BOTNAME> via email at de5@illinois.edu or direct message in Slack. 
#   1. I will integrate your bot with our slack channel and generate API token for your bot. 
#   2. I will send you API token 'token'. This is required in subsequent steps. 

# In your python environment, do "export SLACK_BOT_TOKEN='token' "
# Use print_bot_id.py to obtained 'bot_id'
# In your python environment, do "export BOT_ID='bot_id' "
#####################

import os
import time
from slackclient import SlackClient
from collections import Counter

# bot's ID as an environment variable
BOT_ID = os.environ.get("BOT_ID")


# instantiate Slack clients
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))

################
# GLOBALS
################
topic_list = ["graph", "graphs", "social", "network", "networks", "information", "data", "economic", "behavior", "behaviors", "behavioral", "edge", "edges", "node", "nodes", "game", "games", "theory", "theories", "algorithm", "algorithms", "directed", "undirected", "resource", "resources", "constraint", "constraints", "mp", "mps", "homework", "homeworks", "exam", "truthful", "incentive", "compatible", "welfare", "maximize", "maximizes", "open", "problem", "research", "paper", "academic", "integrity", "computer", "science", "decision", "decisions", "making", "rational", "irrational", "human", "project", "final"]

post_archive_list = []

# Map storing binaries of all users whether they have posted content
participation_map = {}

# Prerequisites binary
prerequisites_met = False

############
# SCORES
############
MAX_PARTICIPATION_SCORE = 1
MAX_QUALITY_SCORE = 4
prereq_percentage = 0.7
text_post_score = 0.05
text_receive_score = 0.06
reply_post_score = 0.03
unique_word_score = 0.01
emoji_post_score = 0.01
emoji_receive_score = 0     # initialized in create_participation_map
pinned_starred_score = 0.5
reply_only_participation_points = 0.01
text_only_participation_points = 0.01

def handle_command(commandtype, command, channel, user):
    """
        Receives commands/contents generated.
        Currenly, prints a directed message to the user containing the same content.
    """

    # Participation
    if commandtype == 'posted_text_participation':
        response = "<@" + user + "> Hi! You said *" + command + "*"
    elif commandtype == 'posted_reaction':
        response = "<@" + user + "> Hi! You posted *" + command + "*"
    elif commandtype == 'posted_reply':
        response = "<@" + user + "> Hi! You replied *" + command + "*"

    # Quality
    elif commandtype == 'posted_text_quality':
        response = "<@" + user + "> Hi! You posted something of quality"
    elif commandtype == 'received_reaction':
        response = "<@" + user + "> Hi! You received *" + command + "*"
    elif commandtype == 'received_reply':
        response = "<@" + user + "> Hi! You received a reply for your post *" + command + "*"
    elif commandtype == 'received_pin':
        response = "<@" + user + "> Hi! Your post just got *pinned*"

    # Bad behavior
    elif commandtype == 'text_not_truthful':
        response = "<@" + user + "> Hi! Your post is not a good quality post (consolation points)"
    elif commandtype == 'reply_not_truthful':
        response = "<@" + user + "> Hi! Your reply is not a good quality reply (consolation points)"
    elif commandtype == 'received_bad_reaction':
        response = "<@" + user + "> Hi! You received *" + command + "* which is not a good reaction (no points)"
    elif commandtype == 'text_copied':
        response = "<@" + user + "> Hi! You posted a copied post (no points)"
    else:
        response = ""
 
    # Posts a directed message to the user.
    slack_client.api_call("chat.postMessage", channel=channel,
                          text=response, as_user=True)

    # You can also post a private directed message that only that user will see. 
    # slack_client.api_call("chat.postEphemeral", channel=channel,
    #                       text=response, as_user=True, user=user)

################
# SETUP
################
def create_participation_map():
    global emoji_receive_score
    """
        Initializes participation_map with all IDs
    """
    user_info = slack_client.api_call("users.list")
    for user in user_info['members']:
        if user['id'] != 'USLACKBOT':
            participation_map[user['id']] = False

    emoji_receive_score = 0.1 / len(participation_map.keys())

    return

def check_prerequisites(output_list):
    """
        Checks if prerequisites are met and updates prerequisites_met 
    """
    global prerequisites_met

    # PREREQUISITE: All users must have posted at least once.
    # Check if user posted. If so, update participation_map and set True to user.
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'user' in output and not('bot_id' in output):
                participation_map[output['user']] = True
    if list(participation_map.values()).count(True) * 1.0 >= prereq_percentage * len(list(participation_map.keys())):
        return True
    print(list(participation_map.values()).count(True))
    return False

    #prerequisites_met = all(list(participation_map.values()))

################
# TRUTHFULNESS
################
def post_is_copied(text_post):
    if text_post in post_archive_list:
        return True
    return False    

def post_is_topic_related(text_post):
    for word in text_post.split():
        if word.lower() in topic_list:
            return True
    return False

def post_is_truthful(text_post):
    return post_is_topic_related(text_post) and not post_is_copied(text_post)

################
# PARTICIPATION
################

def text_posted_participation(slack_rtm_output):
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'user' in output and 'text' in output and str(output["type"]) == 'message' and not('bot_id' in output) and not('attachments' in output):
                if not 'thread_ts' in output and not post_is_copied(output['text']):
                    credit = text_post_score
                    return 'posted_text_participation', \
                           output['text'], \
                           output['channel'], \
                           output['user'], \
                           credit
                elif not 'thread_ts' in output:
                    return 'text_copied', \
                           output['text'], \
                           output['channel'], \
                           output['user'], \
                           0
    #### Returns null if it is not a valid output.            
    return None, None, None, None, -1

# Gives points to the person who posts an emoji
def emoji_posted(slack_rtm_output):
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'user' in output and 'reaction' in output and not('bot_id' in output):
                if str(output["type"]) == "reaction_added" :
                    credit = 0.001 
                    return 'posted_reaction', \
                           output['reaction'], \
                           output['item']['channel'], \
                           output['user'], \
                           credit
    return None, None, None, None, -1

# Gives points to the person who posts a reply
def reply_posted(slack_rtm_output):
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'user' in output and 'text' in output and not('bot_id' in output):
                if 'thread_ts' in output and post_is_truthful(output['text']):
                    credit = reply_post_score + score_unique_words(output['text'])
                    post_archive_list.append(output['text'])
                    return 'posted_reply', \
                           output['text'], \
                           output['channel'], \
                           output['user'], \
                           credit
                elif 'thread_ts' in output:
                    return 'reply_not_truthful', \
                           output['text'], \
                           output['channel'], \
                           output['user'], \
                           reply_only_participation_points
    return None, None, None, None, -1

################
# QUALITY
################
def score_unique_words(text_post):
    unique_word_count = int(len(Counter(text_post.split()).keys()))
    credit = unique_word_count * unique_word_score
    return credit

# Gives points to the person who posts text
def text_posted_quality(slack_rtm_output):
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'user' in output and 'text' in output and str(output["type"]) == 'message' and not('bot_id' in output) and not('attachments' in output):
                # output contains field 'thread_ts' if it is a comment on a previous post, otherwise not
                if not 'thread_ts' in output and post_is_truthful(output['text']):
                    credit = score_unique_words(output['text'])
                    post_archive_list.append(output['text'])

                    return 'posted_text_quality', \
                           output['text'], \
                           output['channel'], \
                           output['user'], \
                           credit
                elif not 'thread_ts' in output and not post_is_copied(output['text']):
                    return 'text_not_truthful', \
                           output['text'], \
                           output['channel'], \
                           output['user'], \
                           0
    #### Returns null if it is not a valid output.            
    return None, None, None, None, -1

# Gives points to the person who receives an emoji
def emoji_received(slack_rtm_output):
    output_list = slack_rtm_output
    bad_emojis = ["frown", "angry", "cry", "frown", "unamused", "disappoint", "rage", "horror", "disgust", "shame"]
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'user' in output and 'reaction' in output and not('bot_id' in output):
                user_info = slack_client.api_call("users.list")
                num_users = len(user_info['members'])
                if str(output["type"]) == "reaction_added":
                    emoji_counter = emoji_receive_score
                    
                    if (output["reaction"] in bad_emojis):
                        return 'received_bad_reaction', \
                           output['reaction'], \
                           output['item']['channel'], \
                           output['item_user'], \
                           0.0

                    return 'received_reaction', \
                           output['reaction'], \
                           output['item']['channel'], \
                           output['item_user'], \
                           emoji_counter
    return None, None, None, None, -1

# Gives points to the person who receives a reply
def replies_received(slack_rtm_output):
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'message' in output and not('bot_id' in output):
                if 'message_replied' in output['subtype']:
                    credit = text_receive_score 

                    return 'received_reply', \
                           output['message']['text'], \
                           output['channel'], \
                           output['message']['user'], \
                           credit
    return None, None, None, None, -1

# Gives points to the person whos post gets pinned
def pinned_received(slack_rtm_output):
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'user' in output and not('bot_id' in output):
                if str(output["type"]) == "pin_added" and str(output['user']) != str(output['item_user']):
                    credit = pinned_starred_score
                    return 'received_pin', \
                           "Unused", \
                           output['item']['channel'], \
                           output['item_user'], \
                           credit
    return None, None, None, None, -1

################
# CREDITS
################
def updateAndPrintCredit(scoreMap, user, scoretype, credit, doPrint=True):
    """
        Updates and prints the current credit score of all users who have generated some content
    """
    if scoretype == 'quality':
        max_score = MAX_QUALITY_SCORE
    else:
        max_score = MAX_PARTICIPATION_SCORE

    if user in scoreMap:
        scoreMap[user][scoretype] = scoreMap[user][scoretype] + credit
        if scoreMap[user][scoretype] > max_score:
            scoreMap[user][scoretype] = max_score
    else:
        scoreMap[user] = {'quality': 0.0, 'participation': 0.0}
        scoreMap[user][scoretype] = credit

    if doPrint:
        for usr, cred in scoreMap.items():
            response1 = "<@" + usr + ">" + " your score is " + str(round(cred['quality'], 3)) + " out of " + str(MAX_QUALITY_SCORE) + " for quality, "         
            response2 = "and " + str(round(cred['participation'], 3)) + " out of " + str(MAX_PARTICIPATION_SCORE) + " for participation, "
            response3 = "for a total of " + str(round(cred['quality'] + cred['participation'], 3)) + " points "
            response = response1 + response2 + response3
            slack_client.api_call("chat.postMessage", channel=channel,
                text=response, as_user=True)

    # Returning updated credit map
    return scoreMap

################
# MAIN
################
if __name__ == "__main__":
    READ_WEBSOCKET_DELAY = 1 # second delay between reading from firehose

    # Update participation map
    create_participation_map()

    ##### Map storing the scores of all users who have contributed some content
    scoreMap = {}

    if slack_client.rtm_connect():
        print("StarterBot connected and running!")

        # Cannot start scoring until prerequisites are met
        while not prerequisites_met:
             print("Prerequisites not met!")
             print(participation_map)
             prerequisites_met = check_prerequisites(slack_client.rtm_read())
             time.sleep(READ_WEBSOCKET_DELAY)

        while True:
            current_state = slack_client.rtm_read()
            if current_state == None or len(current_state) <= 0:
                continue
            print (current_state)

            ### PARTICIPATION ###
            scoretype = 'participation'
            # POSTING text
            commandtype, command, channel, user, credit = text_posted_participation(current_state)
            if commandtype and command and channel and user:
                # Handles current output
                handle_command(commandtype, command, channel, user)
                # Updates credit of users
                scoreMap = updateAndPrintCredit(scoreMap, user, scoretype, credit, False)

            # POSTING emojis
            commandtype, command, channel, user, credit = emoji_posted(current_state)
            if commandtype and command and channel and user:
                # Handles current output
                handle_command(commandtype, command, channel, user)
                # Updates credit of users
                scoreMap = updateAndPrintCredit(scoreMap, user, scoretype, credit)

            # POSTING replies
            commandtype, command, channel, user, credit = reply_posted(current_state)
            if commandtype and command and channel and user:
                # Handles current output
                handle_command(commandtype, command, channel, user)
                # Updates credit of users
                scoreMap = updateAndPrintCredit(scoreMap, user, scoretype, credit)

            ### QUALITY ###
            scoretype = 'quality'
            # UNIQUE WORDS
            commandtype, command, channel, user, credit = text_posted_quality(current_state)
            if commandtype and command and channel and user:
                # Handles current output
                handle_command(commandtype, command, channel, user)
                # Updates credit of users
                scoreMap = updateAndPrintCredit(scoreMap, user, scoretype, credit)

            # GET GOOD EMOJIS
            commandtype, command, channel, user, credit = emoji_received(current_state)
            if commandtype and command and channel and user:
                # Handles current output
                handle_command(commandtype, command, channel, user)
                # Updates credit of users
                scoreMap = updateAndPrintCredit(scoreMap, user, scoretype, credit)

            # GET REPLIES
            commandtype, command, channel, user, credit = replies_received(current_state)
            if commandtype and command and channel and user:
                # Handles current output
                handle_command(commandtype, command, channel, user)
                # Updates credit of users
                scoreMap = updateAndPrintCredit(scoreMap, user, scoretype, credit)

            # GET POST PINNED
            commandtype, command, channel, user, credit = pinned_received(current_state)
            if commandtype and command and channel and user:
                # Handles current output
                handle_command(commandtype, command, channel, user)
                # Updates credit of users
                scoreMap = updateAndPrintCredit(scoreMap, user, scoretype, credit)

            # End.
            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print("Connection failed. Invalid Slack token or bot ID?")
