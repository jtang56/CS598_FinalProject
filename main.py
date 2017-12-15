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
import json
import copy
import random
from slackclient import SlackClient
from collections import Counter
import json

# bot's ID as an environment variable
BOT_ID = os.environ.get("BOT_ID")

# instantiate Slack clients
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))

################
# GLOBALS
################
EXCITING_WORDS = ["Great!", "Fantastic!", "Awesome!", "Cool!"]
TOTAL_CHANNEL_FACTS_READ = 0
TOTAL_CHANNEL_JOKES_READ = 0
TOTAL_QUIZZES_GIVEN = 0
TOTAL_QUIZZES_CORRECT = 0

############
# SCORES
############

def handle_command(commandtype, command, channel, user):
    global TOTAL_CHANNEL_FACTS_READ, TOTAL_CHANNEL_JOKES_READ, TOTAL_QUIZZES_CORRECT, TOTAL_QUIZZES_GIVEN
    should_handle_badges = False
    if commandtype == 'posted_text_participation':
        response = "<@" + user + "> Hi! You said *" + command + "*"
    elif commandtype == 'stats':
        response = "*Total Facts Read:* " + str(TOTAL_CHANNEL_FACTS_READ) + "\n" + \
                   "*Total Jokes Read:* " + str(TOTAL_CHANNEL_JOKES_READ) + "\n" + \
                   "*Avg Facts Read:* " + str(TOTAL_CHANNEL_FACTS_READ / num_users) + "\n" + \
                   "*Avg Jokes Read:* " + str(TOTAL_CHANNEL_JOKES_READ / num_users) + "\n" + \
                   "*Total Questions Administered:* " + str(TOTAL_QUIZZES_GIVEN) + "\n" + \
                   "*Total Questions Answered Correct:* " + str(TOTAL_QUIZZES_CORRECT)
    elif commandtype == 'individstats':
        response = ""
        for user in users.keys():
            response += "*" + users[user] + "*\n"
            response += "\t Facts Read: " + str(users_facts_read[user]) + "\n"
            response += "\t Jokes Read: " + str(users_jokes_read[user]) + "\n"
            response += "\t Questions Given: " + str(users_questions_given[user]) + "\n"
            response += "\t Questions Correct: " + str(users_questions_correct[user]) + "\n"
    elif commandtype == 'interesting_DM_post':
        response = "Yeah, it really is"
    elif commandtype == 'DM_fact_post' or (commandtype == 'DM_confirmation_no_post' and users_currently_confirmation[user]):
        should_handle_badges = True
        if users_facts[user] == []:
            response = "WOW!!!!!!!! You've read all the facts we have! Great Job!"
        else:
            fact = random.choice(users_facts[user])
            response = random.choice(EXCITING_WORDS) + " Here's a really cool fact: \n\n" + fact[0]
            users_facts[user].remove(fact)
            users_facts_test[user].append(fact)
            users_facts_read[user] += 1
            TOTAL_CHANNEL_FACTS_READ += 1
    elif commandtype == 'DM_joke_post':
        users_currently_confirmation[user] = True
        response = "Are you sure you want to hear a joke (\"yes\"\\\"no\")?"
    elif commandtype == 'DM_confirmation_yes_post' and users_currently_confirmation[user]:
        joke = random.choice(users_jokes[user])
        response = "Here's a joke: \n\n" + joke
        users_jokes_read[user] += 1
        TOTAL_CHANNEL_JOKES_READ += 1
        if users_jokes_read[user] >= 5 and users_jokes_read[user] % 5 == 0:
            response += "\n*You've read " + str(users_jokes_read[user]) + " jokes.*"
    elif commandtype == 'DM_post':
        response = "Hello, " + users[user] + "\ntype *fact* for a cool fact \n type *joke* for a joke"
    elif commandtype == 'not_DM_post':
        response = "Thanks for mentioning me, " + "<@" + user + ">"
    elif commandtype == 'quiz_mode':
        if command.upper() == current_quiz_question[user][2].upper():
            response = "Correct! Congratulations on passing this quiz."
            TOTAL_QUIZZES_CORRECT += 1
            users_questions_correct[user] += 1
            quiz_mode[user] = False
        else:
            if users_facts_read[user] < 5:
                response = "Incorrect! Try harder next time."
                quiz_mode[user] = False
            else:
                response = "Incorrect! Please answer again.\n *~~~~~~~~~~~~~~~Please answer this quick quiz question on the facts you've seen so far!~~~~~~~~~~~~~~* \n" + current_quiz_question[user][1]
                users_questions_given[user] += 1
                TOTAL_QUIZZES_GIVEN += 1
    else:
        response = ""

    # Posts a directed message to the user.
    slack_client.api_call("chat.postMessage", channel=channel, text=response, as_user=True)
    if should_handle_badges:
        if handle_badges(channel, user):
            quiz_mode[user] = True
            post_quiz_question(channel, user)

    # You can also post a private directed message that only that user will see. 
    # slack_client.api_call("chat.postEphemeral", channel=channel,
    #                       text=response, as_user=True, user=user)

################
# SETUP
################
def handle_badges(channel, user):
    badges_data = json.load(open('badges.json'))
    if str(users_facts_read[user]) in badges_data["badges"].keys():
        response = badges_data["badges"][str(users_facts_read[user])]
        slack_client.api_call("chat.postMessage", channel=channel, text=response, as_user=True)
        response = " \n"
        slack_client.api_call("chat.postMessage", channel=channel, text=response, as_user=True)
        slack_client.api_call("chat.postMessage", channel=channel, text=response, as_user=True)
        slack_client.api_call("chat.postMessage", channel=channel, text=response, as_user=True)
        general_response = "*" + users[user] + "* received " + badges_data["badges"][str(users_facts_read[user])] + "\n" + users[user] + " has answered " + str(users_questions_correct[user]) + " questions correctly out of a total of " + str(users_questions_given[user]) +" questions."

##############################################################################
##############################################################################
##############################################################################
##############################################################################
##############################################################################
##############################################################################
##############################################################################
#TODO: CHANGE #general to #networksclassf2017 ################################
##############################################################################
##############################################################################
##############################################################################
##############################################################################
##############################################################################
##############################################################################
##############################################################################
##############################################################################
##############################################################################
##############################################################################
        slack_client.api_call("chat.postMessage", channel="#general", text=general_response, as_user=True)
        if users_facts_read[user] >= 3:
            return True
    else:
        num_facts = users_facts_read[user]
        avg_facts = TOTAL_CHANNEL_FACTS_READ / num_users
        if num_facts > avg_facts:
            response = "*You've read more facts than the class average! Keep going!*"
        else:
            response = "*You've read fewer facts than the class average. Read a few more!*"
        slack_client.api_call("chat.postMessage", channel=channel, text=response, as_user=True)
    return False

def post_quiz_question(channel, user):
    global TOTAL_QUIZZES_GIVEN
    TOTAL_QUIZZES_GIVEN += 1
    users_questions_given[user] += 1
    current_quiz_question[user] = random.choice(users_facts_test[user])
    response = "\n *~~~~~~~~~~~~~~~Please answer this quick quiz question on the facts you've seen so far!~~~~~~~~~~~~~~*~ \n" + current_quiz_question[user][1]
    slack_client.api_call("chat.postMessage", channel=channel, text=response, as_user=True) 

def post_is_DM(slack_rtm_output):
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'user' in output and 'text' in output and str(output["type"]) == 'message' and output["channel"][0] == 'D' and not output['user'] == BOT_ID:
                if quiz_mode[output['user']]:
                    return 'quiz_mode', \
                           output['text'], \
                           output['channel'], \
                           output['user']
                elif "getStats" == output['text']:
                    return 'stats', \
                           output['text'], \
                           output['channel'], \
                           output['user']
                elif "getStatsIndividual" == output['text']:
                    return 'individstats', \
                           output['text'], \
                           output['channel'], \
                           output['user']
                elif "cool" in output['text'].lower() or "interesting" in output['text'].lower() or "amazing" in output['text'].lower():
                    return 'interesting_DM_post', \
                           output['text'], \
                           output['channel'], \
                           output['user']
                elif "fact" in output['text'].lower():
                    return 'DM_fact_post', \
                           output['text'], \
                           output['channel'], \
                           output['user']
                elif "joke" in output['text'].lower():
                    return 'DM_joke_post', \
                           output['text'], \
                           output['channel'], \
                           output['user']
                elif "yes" in output['text'].lower().split():
                    return 'DM_confirmation_yes_post', \
                           output['text'], \
                           output['channel'], \
                           output['user']
                elif "no" in output['text'].lower().split():
                    return 'DM_confirmation_no_post', \
                           output['text'], \
                           output['channel'], \
                           output['user']
                else:
                    return 'DM_post', \
                           output['text'], \
                           output['channel'], \
                           output['user']
    #### Returns null if it is not a valid output.            
    return None, None, None, None

def post_is_not_DM(slack_rtm_output):
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'user' in output and 'text' in output and str(output["type"]) == 'message' and not output["channel"][0] == 'D' and not output['user'] == BOT_ID:
                if "<@" + BOT_ID + ">" in output['text']:
                    print("BOT HAS BEEN MENTIONED")
                    return 'not_DM_post', \
                           output['text'], \
                           output['channel'], \
                           output['user']
    #### Returns null if it is not a valid output.            
    return None, None, None, None

################
# MAIN
################
if __name__ == "__main__":
    facts_list = []
    jokes_list = []
    fact_data = json.load(open('facts.json'))
    for fact in fact_data["facts"]:
        facts_list.append(fact)

    jokes_data = json.load(open('jokes.json'))
    for joke in jokes_data["jokes"]:
        jokes_list.append(joke)

    users = {}
    users_facts = {}
    users_facts_read = {}
    users_facts_test = {}
    users_jokes = {}
    users_jokes_read = {}
    users_currently_confirmation = {}
    quiz_mode = {}
    current_quiz_question = {}
    users_questions_given = {}
    users_questions_correct = {}
    channel_info = slack_client.api_call("channels.list")
    channel = channel_info['channels'][0]['id']
    user_info = slack_client.api_call("users.list")
    for user in user_info['members']:
        if not user['is_bot'] and user['id'] != 'USLACKBOT':
            users[user['id']] = user['name']
            users_facts[user['id']] = copy.copy(facts_list)
            users_facts_read[user['id']] = 0
            users_facts_test[user['id']] = []
            users_jokes[user['id']] = copy.copy(jokes_list)
            users_jokes_read[user['id']] = 0
            users_currently_confirmation = False
            users_questions_given[user['id']] = 0
            users_questions_correct[user['id']] = 0
            quiz_mode[user['id']] = False
            current_quiz_question[user['id']] = None
            num_users = len(users.keys())        

    scoreMap = {}

    if slack_client.rtm_connect():
        print("StarterBot connected and running!")

        while True:
            current_state = slack_client.rtm_read()
            if current_state == None or len(current_state) <= 0:
                continue
            print (current_state)

            ### PARTICIPATION ###
            scoretype = 'participation'

            # Detect a Direct Message to the bot # 
            commandtype, command, channel, user = post_is_DM(current_state)
            if commandtype and command and channel and user:
                handle_command(commandtype, command, channel, user) 

            commandtype, command, channel, user = post_is_not_DM(current_state)
            if commandtype and command and channel and user:
                handle_command(commandtype, command, channel, user)

        else:
            print("Connection failed.")

