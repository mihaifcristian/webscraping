import requests
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from string import Template
from bs4 import BeautifulSoup
from SSHLibrary import SSHLibrary
import time
from datetime import datetime

# VARIABLES USED TO CHECK EVERY SERVER
sat_list = {'sat_i0': 'URL',
            'sat_i2': 'URL',
            'sat_i3': 'URL',
            'sat_i4': 'URL',
            'sat_i5': 'URL',
            'sat_i7': 'URL',
            'sat_i8': 'URL'
            }
html_content_parsed = None
succes_login = None
redirected = None
server_with_problem_list = []
cant_login_servers = []

# SSH Connect to Server
ssh = SSHLibrary()
ssh.open_connection("[server]")
ssh.login("[user]", "[password]")

# EMAIL CREDENTIALS AND SENDERS
MY_ADDRESS = "email"
MY_PASSWORD = "password"
recipient = ['[destination email adress]',
             '[destination email adress]']


def check_server(key, value, iterator=0):
    try:
        res = requests.get(value)
        res_status = res.status_code
        html_content_parsed = BeautifulSoup(res.text, 'html.parser')
        succes_login = html_content_parsed.find("span", class_="L4Blue")
        redirected = html_content_parsed.find("p", class_="error")

        if res_status == 200 and redirected:
            cant_login_servers.append(key)
        elif res_status == 200 and succes_login:
            f'Server {key} is Up and Running'
        elif iterator < 2:  # Try to stop and start broken server
            output, return_code = ssh.execute_command(
                f"admin {key}-stop", return_rc=True, return_stdout=True)
            time.sleep(20)
            output, return_code = ssh.execute_command(
                f"admin {key}-start", return_rc=True, return_stdout=True)
            time.sleep(20)
            iterator += 1
            # print(iterator)  # Just to test
            check_server(key, value, iterator)
        elif iterator == 2:
            server_with_problem_list.append(key)
        iterator = 0
    except(ValueError):
        print(ValueError)
        print("Something went wrong")


# CHECK IF IS MENTENANCE PERIOD AND IF IS NOT CHECK SERVERS
def run_test():
    now = datetime.now()
    current_time = now
    first_time = now.replace(hour=18, minute=00, second=00, microsecond=0)
    last_time = now.replace(hour=22, minute=00, second=00, microsecond=0)

    if current_time > last_time or current_time < first_time:
        for key, value in sat_list.items():
            check_server(key, value)
    if server_with_problem_list:
        for email_address in recipient:
            send_email(email_address, server_with_problem_list)
    elif cant_login_servers:
        send_email('[destination email adress]', cant_login_servers, 1)


# READ FILE FROM TEMPLATE
def get_template(filename):
    with open(filename, 'r', encoding='utf-8') as template_file:
        template_file_content = template_file.read()
    return Template(template_file_content)


# CONFIGURE ALL YOU NEED TO SEND AN EMAIL
def send_email(email_address, servers_list, mailtype=None):
    s = smtplib.SMTP(host='smtp.gmail.com', port=587)
    s.starttls()
    s.login(MY_ADDRESS, MY_PASSWORD)

    # IF WE DON`T PROVIDE A MAIL TYPE HE CREATE THE DEFAULT MAIL TAMPLATE FOR SERVERS DOWN
    if mailtype:
        message_template = get_template(
            "/bodyMessageLogin.txt")
    else:
        message_template = get_template("/bodyMessage.txt")

    msg = MIMEMultipart()  # create a message

    message = message_template.substitute(number=servers_list)

    # setup the parameters of the message
    msg['From'] = MY_ADDRESS
    msg['To'] = email_address
    msg['Subject'] = "BATCH SERVER WARNING"

    # add in the message body
    msg.attach(MIMEText(message, 'plain'))

    # send the message via the server set up earlier.
    s.send_message(msg)

    del msg


# RUN SCRIPT COMMAND
run_test()
