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
from slackclient import SlackClient
from collections import Counter
import json

# bot's ID as an environment variable
BOT_ID = os.environ.get("BOT_ID")
FACT_JOKE_MESSAGE = ""
# instantiate Slack clients
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))

################
# GLOBALS
################


############
# SCORES
############

def handle_command(commandtype, command, channel, user):
    """
        Receives commands/contents generated.
        Currenly, prints a directed message to the user containing the same content.
        """

    # Participation
    if commandtype == 'posted_text_participation':
        response = "<@" + user + "> Hi! You said *" + command + "*"
    elif commandtype == 'DM_fact_post':
        response = "You chose a fact"
    elif commandtype == 'DM_joke_post':
        response = "You chose a joke"
    elif commandtype == 'DM_post':
        response = "Hello, " + users[user] + "type \"fact\" for a cool fact \n type \"joke\" for a funny joke"
        #attachments = FACT_JOKE_MESSAGE["attachments"]
        #slack_client.api_call("chat.postMessage", attachments=attachments, channel=channel, text=response, as_user=True)
    elif commandtype == 'not_DM_post':
        response = "*" + command + "*" + " was posted in a public channel"
    else:
        response = ""

    # Posts a directed message to the user.
    slack_client.api_call("chat.postMessage", channel=channel, text=response, as_user=True)

    # You can also post a private directed message that only that user will see. 
    # slack_client.api_call("chat.postEphemeral", channel=channel,
    #                       text=response, as_user=True, user=user)

################
# SETUP
################
def post_is_DM(slack_rtm_output):
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'user' in output and 'text' in output and str(output["type"]) == 'message' and output["channel"][0] == 'D' and not output['user'] == BOT_ID:
                if "fact" in output['text']:
                    return 'DM_fact_post', \
                    output['text'], \
                    output['channel'], \
                    output['user']
                elif "joke" in output['text']:
                    return 'DM_joke_post', \
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
                return 'not_DM_post', \
                output['text'], \
                output['channel'], \
                output['user']
#### Returns null if it is not a valid output.            
return None, None, None, None
################
# PARTICIPATION
################

def text_posted_participation(slack_rtm_output):
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'user' in output and 'text' in output and str(output["type"]) == 'message' and not('bot_id' in output) and not('attachments' in output):
                if not 'thread_ts' in output:
                    credit = 0.1
                    return 'posted_text_participation', \
                    output['text'], \
                    output['channel'], \
                    output['user']
                elif not 'thread_ts' in output:
                    return 'text_copied', \
                    output['text'], \
                    output['channel'], \
                    output['user']
    #### Returns null if it is not a valid output.            
    return None, None, None, None

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

    facts_list = {}
    jokes_list = {}
    fact_data = json.load(open('facts.json'))
    for fact in fact_data["facts"]:
        facts_list[fact] = False

        jokes_data = json.load(open('jokes.json'))
        for joke in jokes_data["jokes"]:
            jokes_list[joke] = False

            users = {}
            channel_info = slack_client.api_call("channels.list")
            channel = channel_info['channels'][0]['id']
            user_info = slack_client.api_call("users.list")
            for user in user_info['members']:
                if not user['is_bot'] and user['id'] != 'USLACKBOT':
                    users[user['id']] = user['name']
                    num_users = len(users.keys())        

                    with open('message.json') as json_data:
                        FACT_JOKE_MESSAGE = json.load(json_data)

##########FOR DIRECT MESSAGES##########
    #for user in users.keys():
        #response = "Hi " + users[user] + ", I am Green Lantern Bot"
        #slack_client.api_call("chat.postMessage", channel="@"+user, text=response, as_user=True)  
#######################################
    #message = "Hello world! The number of people in this channel is " + str(num_users)
    #TODO
    #CHANGE channel to #networksclassf2017
    #slack_client.api_call("chat.postMessage", channel="#general", text=message, as_user=True)
    ##### Map storing the scores of all users who have contributed some content
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

            # POSTING text
            #commandtype, command, channel, user = text_posted_participation(current_state)
            #if commandtype and command and channel and user:
                # Handles current output
                #handle_command(commandtype, command, channel, user)
                # Updates credit of users
                #scoreMap = updateAndPrintCredit(scoreMap, user, scoretype, credit, False)

            # End.
            time.sleep(READ_WEBSOCKET_DELAY)
        else:
            print("Connection failed.")
