'''
https://vaac.meteo.fr
https://vaac.meteo.fr/advisory/2024/

It reads from the webpage https://vaac.meteo.fr the newest folder of the current year and downloads from the latest folder the image and the
csv file.

We execute it from taskmanager or crontab so as to send us an alert.
It sends the files by e-mail, after defining sender account credentials to a list of e-mails.

'''
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os
import logging
from logging.handlers import RotatingFileHandler

logging.basicConfig(
                    handlers=[
                      RotatingFileHandler(
                        './volcano.log',
                        maxBytes=10240000,
                        backupCount=5
                      )
                    ],
                    format='%(asctime)s - %(message)s',
                    level=logging.INFO
                    )


advisories_dict = {}

def get_volcano_info():
  """Fetches volcano information from VAAC website and returns a dictionary.
  Returns:
      A dictionary containing volcano image URL, advisory title and text, or None if unsuccessful.
  """
  year = datetime.now().year
  url = f"https://vaac.meteo.fr/advisory/{year}/"
  try:
    response = requests.get(url, proxies=proxies)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find the latest volcano update
    # latest_update = soup.find_all("td")
    latest_update = soup.find_all("a")
    # print("latest_update: ",latest_update)

    for td in latest_update:
      txt = td.get_text()
      if len(txt) > 5:
        txt_split = txt.split("_")
        if len(txt_split) > 1:
          txt_datetime = txt_split[1].replace("/", "")
          datetime_object = datetime.strptime(txt_datetime, '%Y%m%d%H%M%S')
          advisories_dict[datetime_object] = txt

    maxdate = max((x for x in advisories_dict.keys()))

  

    # Extract image URL (assuming it's the first image in the update)
    new_url = url + advisories_dict[maxdate]
    image_url = new_url  + advisories_dict[maxdate].replace("/", "_vag.png")
    image_name = advisories_dict[maxdate].replace("/", "_vag.png")
    vag_csv = new_url + advisories_dict[maxdate].replace("/", "_vag.csv")
    vag_csv_name = advisories_dict[maxdate].replace("/", "_vag.csv")
    vag_info_json = new_url  + "info.json"
    vag_metas_json = new_url  + "metas.json"

    # Extract advisory title and text
    advisory_title = advisories_dict[maxdate]
    advisory_text = new_url  + advisories_dict[maxdate].replace("/", "_vaa.txt")

    return {
      "image_url": image_url,
      "image_name": image_name,
      "advisory_title": advisory_title,
      "advisory_text": advisory_text,
      "advisory_csv": vag_csv,
      "csv_name": vag_csv_name
    }
  except requests.exceptions.RequestException as e:
    print(f"Error fetching volcano information: {e}")
    logging.error(f"Error fetching volcano information: {e}")
    return None

def generate_html(volcano_info):
  """Generates HTML content based on the provided volcano information.
  Args:
      volcano_info: A dictionary containing volcano information.
  Returns:
      A string containing the generated HTML content.
  """
  if not volcano_info:
    return "<h2>Volcano Information Not Available</h2>"

  html = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Volcano Information</title>
</head>
<body>
  <h1>VAAC - Latest Volcanic Activity</h1>
  """

  if volcano_info["image_url"]:
    html += f'<img src="{volcano_info["image_url"]}" alt="Volcano Image" width="50%">'

  html += f"""
  <h2>{volcano_info["advisory_title"]}</h2>
  <p>{volcano_info["advisory_text"]}</p>
  <embed type="text/html" src={volcano_info["advisory_text"]} title="volcano text" height="400" width="500">
  </body>
  </html>
  """
  return html

def get_items():
  '''
  Args:
    none
  returns:
    none
    Downloads the latest information files
  '''
  if volcano_info["image_url"]:
    print(volcano_info)
    image_req = requests.get(volcano_info["image_url"], allow_redirects=True, proxies=proxies)
    image_name = volcano_info["image_name"]
    advisory_text = volcano_info["csv_name"]
    print(image_name)
    if not os.path.exists(image_name):
      open(image_name, 'wb').write(image_req.content)
      txt = requests.get(volcano_info["advisory_csv"], allow_redirects=True, proxies=proxies)
      open(advisory_text, 'wb').write(txt.content)
      mailer([image_name,advisory_text,"volcano.html"])
      logging.info(volcano_info)
    else:
      print("file already exists")
      logging.warning("file already exists")



def mailer(files_list):
  '''
  Args:
    list of files to send
  returns:
    none
  '''
  # import os
  import sys
  import smtplib
  from email import encoders
  from email.mime.base import MIMEBase
  from email.mime.multipart import MIMEMultipart

  COMMASPACE = ', '
  print(files_list)
  sender = 'sender@gmail.com'
  gmail_password = 'password'
  recipients = [
                'george@mail.com',
                ] # EMAIL ADDRESSES HERE SEPARATED BY COMMAS

  # Create the enclosing (outer) message
  outer = MIMEMultipart()
  outer['Subject'] = 'Volcanic Ash Alert' # EMAIL SUBJECT
  outer['To'] = COMMASPACE.join(recipients)
  outer['From'] = sender
  outer.preamble = 'You will not see this in a MIME-aware mail reader.\n'

  # List of attachments
  attachments = files_list # FULL PATH TO ATTACHMENTS HERE

  # Add the attachments to the message
  for file in attachments:
      try:
          with open(file, 'rb') as fp:
              msg = MIMEBase('application', "octet-stream")
              msg.set_payload(fp.read())
          encoders.encode_base64(msg)
          msg.add_header('Content-Disposition', 'attachment', filename=os.path.basename(file))
          outer.attach(msg)
      except:
          print("Unable to open one of the attachments. Error: ", sys.exc_info()[0])
          logging.error("Unable to open one of the attachments. Error: ", sys.exc_info()[0])
          raise

  composed = outer.as_string()

  # Send the email
  try:
      with smtplib.SMTP('195.251.244.232', 25) as s:
          s.ehlo()
          s.sendmail(sender, recipients, composed)
          s.close()
      print("Email sent!")
      logging.info('Email sent!')
  except:
      print("Unable to send the email. Error: ", sys.exc_info()[0])
      logging.error("Unable to send the email. Error: ", sys.exc_info()[0])
      raise



if __name__ == "__main__":

  # cd to the directory where the script is located
  os.chdir(os.path.dirname(__file__))
  volcano_info = get_volcano_info()
  html_content = generate_html(volcano_info)
  # Creating an HTML file
  Func = open("./volcano.html","w")
  # Adding input data to the HTML file
  Func.write(html_content)
  # Saving the data into the HTML file
  Func.close()
  get_items()
