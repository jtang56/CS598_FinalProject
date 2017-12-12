import json
import pprint
import ast

with open('dump.txt') as results:
    lines = results.readlines()
for line in lines:
    line = line.strip()
    line = line[1:-1]
    line = line.replace("u\'", "\'")
    log_dict = ast.literal_eval(str(line))
    if 'text' in log_dict.keys() and ('Total Facts Read' in log_dict['text']):# or 'Facts Read' in log_dict['text']):
        #print(str(log_dict['ts']))
        print(str(log_dict['ts']) + "\n" + log_dict['text'] + "\n")
