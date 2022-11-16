import configparser
from graph import Graph
import plotly.express as px
import pandas as pd

def main():
    print('''
   ____    U _____ u  ____    U  ___ u   ____      _____    _      __   __ 
U |  _"\ u \| ___"|/U|  _"\ u  \/"_ \/U |  _"\ u  |_ " _|  |"|     \ \ / / 
 \| |_) |/  |  _|"  \| |_) |/  | | | | \| |_) |/    | |  U | | u    \ V /  
  |  _ <    | |___   |  __/.-,_| |_| |  |  _ <     /| |\  \| |/__  U_|"|_u 
  |_| \_\   |_____|  |_|    \_)-\___/   |_| \_\   u |_|U   |_____|   |_|   
  //   \\_  <<   >>  ||>>_       \\     //   \\_  _// \\_  //  \\.-,//|(_  
 (__)  (__)(__) (__)(__)__)     (__)   (__)  (__)(__) (__)(_")("_)\_) (__) 

 know your user.
''')

    # Load settings
    config = configparser.ConfigParser()
    config.read(['config.cfg', 'config.dev.cfg'])
    azure_settings = config['azure']

    sus_user = input("Enter UserPrincipalName: ")
    start_date = input("Enter start date: ")
    end_date = input("Enter end date: ")

    graph: Graph = Graph(azure_settings, sus_user, start_date, end_date)

    greet_user(graph)

    choice = -1

    while choice != 0:
        print('Please choose one of the following options:')
        print('0. Exit')
        print('1. Display access token')
        print('2. Create Graph for initiated activities')
        print('3. Create graph for activities performed on the user')
        print('4. Create user sign-in graph')
        print('5. Create a report')

        try:
            choice = int(input())
        except ValueError:
            choice = -1

        if choice == 0:
            print('Goodbye...')
        elif choice == 1:
            display_access_token(graph)
        elif choice == 2:
            call_audit_initiated(graph)
        elif choice == 3:
            call_audit_target(graph)
        elif choice == 4:
            call_signin(graph)
        elif choice == 5:
            create_final_report(graph)
        else:
            print('Invalid choice!\n')

def greet_user(graph: Graph):
    user = graph.get_user()
    print('Hello,', user['displayName'])
    print('Email:', user['mail'] or user['userPrincipalName'], '\n')

def display_access_token(graph: Graph):
    token = graph.get_user_token()
    print('User token:', token, '\n')

def call_audit_initiated(graph: Graph):
    audit = graph.get_audit_initiated()
    if audit == "This user has not performed any action.":
        return audit
    graph.create_graph_initiated()

def call_audit_target(graph: Graph):
    audit = graph.get_audit_target()
    if audit == "No operations have been performed on this user.":
        return audit
    graph.create_graph_target()

def call_signin(graph: Graph):
    audit_fail = graph.get_audit_signIn_failed()
    audit_success = graph.get_audit_signIn_success()
    if audit_fail == "No logs" and audit_success == "No logs":
        return "This user has not logged in."
    graph.create_graph_signin()

def create_final_report(graph:Graph):
    initiated = call_audit_initiated(graph)
    target = call_audit_target(graph)
    signin = call_signin(graph)
    graph.generate_report(initiated, target, signin)
    print("Your report is ready!")

main()
