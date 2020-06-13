from __future__ import print_function
import os
import httplib2
import os
import io

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from apiclient.http import MediaFileUpload, MediaIoBaseDownload

path = r'/NAT-LOGS/zipped'

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

try:
    import auth
    # If modifying these scopes, delete your previously saved credentials
    # at ~/.credentials/drive-python-quickstart.json
    SCOPES = 'https://www.googleapis.com/auth/drive'
    CLIENT_SECRET_FILE = 'credentials.json'
    APPLICATION_NAME = 'Drive API Python Quickstart'
    authInst = auth.auth(SCOPES, CLIENT_SECRET_FILE, APPLICATION_NAME)
    credentials = authInst.getCredentials()

    http = credentials.authorize(httplib2.Http())
    drive_service = discovery.build('drive', 'v3', http=http)
except  Exception as e:
    sendMail(e)

def listFiles():
    try:
        file_list=[]
        response = drive_service.files().list(q="mimeType='application/x-7z-compressed'",
                                            spaces='drive',
                                            fields='nextPageToken, files(id, name)',
                                            pageToken=None).execute()
        for file in response.get('files', []):
            # Process change
            file_list.append(file.get('name'))
        return file_list
    except Exception as e:
        sendMail(e)

def sendMail(massage):
    try:
        #https://stackoverflow.com/questions/16512592/login-credentials-not-working-with-gmail-smtp
        import smtplib
        from email.message import EmailMessage
        msg = EmailMessage()
        msg.set_content(str(massage))
        msg['Subject'] = f'Error Occured in Upload File.py'
        msg['From'] = 'info@praction.in'
        msg['To'] ='akshay.kumar@praction.in'
        mail = smtplib.SMTP('smtp.praction.in',25)
        mail.ehlo()
        mail.starttls()
        mail.login('info@praction.in','Chauhan_1988')
        mail.send_message(msg)
        mail.quit()
    except Exception as e:
        print("error occur while sending email.")

try:
    if(not os.path.isdir(path)):
        raise ValueError("path is wrong.")

    files = []
    # r=root, d=directories, f = files
    for r, d, f in os.walk(path):
        for file in f:
            if '.7z' in file:
                files.append(file)

    file_list = listFiles()
    months = ['', 'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
            'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']

    for f in files:
        if f in file_list:
            if os.path.exists(path+r"/"+f):
                    os.remove(path+r"/"+f)
                    print(path,'/' ,f ," is deleted.")
                    flag = 1
                    break
        else:
            print(path,'/' ,f," is skiped.")
except ValueError as e:
    print(e)
except Exception as e:
    sendMail(e)


