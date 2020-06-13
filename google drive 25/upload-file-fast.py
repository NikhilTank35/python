from __future__ import print_function
import os
import httplib2
import smtplib
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
# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/drive-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/drive'
CLIENT_SECRET_FILE = 'credentials.json'

APPLICATION_NAME = 'Drive API Python Quickstart'
try:
    import auth
    authInst = auth.auth(SCOPES, CLIENT_SECRET_FILE, APPLICATION_NAME)
    credentials = authInst.getCredentials()

    http = credentials.authorize(httplib2.Http())
    drive_service = discovery.build('drive', 'v3', http=http)
except Exception as e:
    sendMail(e)

def listFolder(folder_name,parent_id):
    try:
        folder_list = {}
        if parent_id == None:
            response = drive_service.files().list(q="mimeType='application/vnd.google-apps.folder'",
                                            spaces='drive',
                                            fields='nextPageToken, files(id, name)',
                                            pageToken=None).execute()
        else:
            response = drive_service.files().list(q="mimeType='application/vnd.google-apps.folder' and '" + parent_id +"' in parents",
                                            spaces='drive',
                                            fields='nextPageToken, files(id, name)',
                                            pageToken=None).execute()
        for file in response.get('files', []):
            # Process change
            if folder_name == file.get('name'):
                return file.get('id')
        return None
    except Exception as e:
        sendMail(e)
def listFiles():
    try:
        file_list=[]
        page_token = None
        while True:
            response = drive_service.files().list(q="mimeType='application/x-7z-compressed' or mimeType='text/plain'",
                                                spaces='drive',
                                                fields='nextPageToken, files(id, name)',
                                                pageToken=page_token).execute()
            for file in response.get('files', []):
               file_list.append(str(file.get('name')))
            page_token = response.get('nextPageToken', None)
            if page_token is None:
                break
        return file_list
    except Exception as e:
        sendMail(e)


def uploadFile(filename, filepath, mimetype, folder_id):
    try:
        file_metadata = {'name': filename , 'parents': [folder_id]}
        media = MediaFileUpload(filepath+"/"+filename,chunksize=1024*1024*1024*1024*1024*1024,
                            mimetype='application/x-7z-compressed',resumable=True)
        file = drive_service.files().create(body=file_metadata,
                                        media_body=media,
                                        fields='id').execute()
        print(filepath,'/' ,filename ," is uploaded succesfully.")
        
    except Exception as e:
        sendMail(e)

def createFolder(year, month, day):
    try:
        yearID = listFolder(year,None)
        if yearID == None:
            # Year folder
            file_metadata = {
                'name': year,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            file = drive_service.files().create(body=file_metadata,
                                                fields='id').execute()
            parentID = file.get('id')
        else:
            parentID = yearID

        monthID = listFolder(month,parentID)
        if monthID == None:
            # Month Folder
            file_metadata = {
                'name': month,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parentID]
            }
            file = drive_service.files().create(body=file_metadata,
                                                fields='id').execute()
            parentID = file.get('id')
        else:
            parentID = monthID

        dayID = listFolder(day,parentID)
        if(dayID == None):
            # Day Folder
            file_metadata = {
                'name': day,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parentID]
            }
            file = drive_service.files().create(body=file_metadata,
                                                fields='id').execute()
            return file.get('id')
        else:
            return dayID
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
        msg['To'] ='nikhiltank35@gmail.com'
        mail = smtplib.SMTP('smtp.praction.in',25)
        mail.ehlo()
        mail.starttls()
        mail.login('info@praction.in','Chauhan_1988')
        mail.send_message(msg)
        mail.quit()

    except Exception as e:
        print("Exception Occured due to sending Mail.")                

try:
    #path = r'/var/dummy'
    if(not os.path.isdir(path)):
        raise ValueError("path is wrong")
    files = []
    # r=root, d=directories, f = files
    for r, d, f in os.walk(path):
        for file in f:
            if '.7z' in file:
                files.append(file)

    file_list = listFiles()
    months = ['', 'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
            'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
#raise Exception('I know Python!')
    for f in files:
        x = f.split("-")
        # print(x)
        ip = x[0]
        year = x[1]
        month = x[2]
        day = x[3]
        if(len(year)!=4):
            x = f.split("_")
            ip = x[0]
            y = x[1].split("-")
            year = y[0]
            month = y[1]
            day = y[2]
        
        # print(year,month,day)
        folder_id = createFolder(
            year, months[int(month)]+'-'+year, day+'-'+month+'-'+year)
        flag = 0
        for i in file_list:
            if str(f).strip()  == str(i).strip():
                print(path,'/' ,f ," is skiped.")
                flag = 1
                break
        if flag == 0:
            uploadFile(f,path, 'application/x-7z-compressed', folder_id)
                
except ValueError as e:
    print(e)
except Exception as e:
    sendMail(e)
