import yaml
import requests
import json
import os
from pathlib import Path
import logging

##################################################
# Logging

log = logging.getLogger()
log.setLevel(logging.INFO)

##################################################
# Config

with open("config.yaml") as fp:
    config = yaml.full_load(fp)
if config['token'] == "none"  or config['workspace_id'] == "none":
    logging.error("Please enter your test token and workspace id in config.yaml")
    logging.error("The test token should look like 'oauth2:<numbers and letters>'. Follow the instructions at https://developer.twist.com/v3/#oauth-2 to obtain it.")
    logging.error("When you access Twist in the browser, the workspace id is the number in the URL, e.g. 123456 in https://twist.com/a/123456")
    exit(-1)
AUTH_HEADER = {"Authorization": f"Bearer {config['token']}"}

##################################################
# Containers for extracted data

archive = {
    "workspace": None,
    "channels": [],
    "threads": dict(),
    "comments": dict(),
    "conversations": dict(),
    "users": dict(),
}
attachments = []

##################################################
# Scraping

def handle_attachment(channel=None, thread=None, comment=None, attachment=None):
    if config["download_attachments"]:
        # TODO Can we download the file programmatically?
        # I think curl and headless chromium fail to retrieve
        # the file because some JS fails to run (and so some
        # redirects don't happen correctly). 
        raise Exception(
            "Attachment download is not supported. " + \
            "Open attachments.html to see a list of " + \
            "attachments which can be manually downloaded."
        )
        # dest_dir = os.path.join(
            #*list(map(str, ["files", "by_channel", channel["id"], thread["id"], comment["id"]]))
        #)
        # mkdir(dest_dir)
        # download_file(attachment["url"], dest_dir)
    attachments.append((channel, thread, comment, attachment))

#### Workspace ###############
url = config["api"] + "/workspaces/getone"
workspace = requests.get(
    url,
    headers=AUTH_HEADER,
    params={
        "id": config["workspace_id"]
    }
)
workspace = workspace.json()
archive["workspace"] = workspace
logging.info(f"Scraping workspace {workspace['name']}")

#### Users ###################
logging.info(f"Scraping list of users")
url = config["api"].replace("v3", "v4") + "/workspace_users/get"
users = requests.get(
    url,
    headers=AUTH_HEADER,
    params={
        "id": config["workspace_id"]
    }
)
for user in users.json():
    logging.info(f"Found user {user['name']}")
    archive["users"][user['id']] = user

#### Channels ################
def mkdir(path):
    try:
        Path(path).mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        logging.error(f"File or folder already exists: {path}")
        exit(-1)
mkdir(os.path.join("output", "channels"))
url = config["api"] + "/channels/get"
channels = requests.get(
    url,
    headers=AUTH_HEADER,
    params={
        "workspace_id": config["workspace_id"]
    }
)
for channel in channels.json():
    logging.info(f"Scraping channel {channel['name']}")
    archive["channels"].append(channel)
    archive["threads"][channel["id"]] = []
    mkdir(os.path.join("output", "channels", f"{channel['name']}"))

    #### Threads #################
    url = config["api"] + "/threads/get"
    threads = requests.get(
        url,
        headers=AUTH_HEADER,
        params={
            "workspace_id": config["workspace_id"],
            "channel_id": channel["id"],
        }
    )
    for thread in threads.json():
        logging.info(f"Scraping thread {thread['title']}")
        archive["threads"][channel["id"]].append(thread)
        archive["comments"][thread["id"]] = []
        def format_post(post):
            output = ""
            userid = post['creator']
            username = archive['users'][userid]['name']
            output += f"Post by {username} at {post['posted_ts']}:\n"
            output += f"{post['content']}\n"
            for attachment in post['attachments']:
                output += f"Attachment: {attachment['file_name']} hosted at {attachment['url']}\n"
            output += "="*10 + "\n\n"
            return output
        for attachment in thread['attachments']:
            handle_attachment(channel=channel, thread=thread, comment=None, attachment=attachment)
        with open(os.path.join("output", "channels", f"{channel['name']}", f"{thread['title']}"), "a+") as thread_fp:
            thread_fp.write(format_post(thread))

        #### Comments ################
        url = config["api"] + "/comments/get"
        comments = requests.get(
            url,
            headers=AUTH_HEADER,
            params={
                "workspace_id": config["workspace_id"],
                "channel_id": channel["id"],
                "thread_id": thread["id"],
            }
        )
        for comment in comments.json():
            archive["comments"][thread["id"]].append(comment)
            # TODO Twist API does not guarantee that
            # comments are returned in chronological
            # order, but in practice they seem to be.
            # Sort and output comments at the end of
            # the scrape if that ever changes.
            with open(os.path.join("output", "channels", f"{channel['name']}", f"{thread['title']}"), "a+") as thread_fp:
                thread_fp.write(format_post(comment))

            #### Attachments #############
            for attachment in comment["attachments"]:
                for attachment in thread['attachments']:
                    handle_attachment(channel=channel, thread=thread, comment=comment, attachment=attachment)

##################################################
# Output to file

#### Attachments ########
OPENING_HTML = "<html><body><ul>"
CLOSING_HTML = "</ul></body></html>"
def format_dl_link(channel, thread, comment, attachment):
    return f"""
    <li>
      {comment['id']}:
      <a href='{attachment['url']}'>
        {attachment['title']}
      </a>
    </li>"""

headers = [None, None]
with open(os.path.join("output", "attachments.html"), "w") as fp:
    fp.write(OPENING_HTML)
    for channel, thread, comment, attachment in attachments:
        if channel != headers[0]:
            headers[0] = channel
            fp.write(f"</ul><h1>{channel['name']}</h1><ul>")
        if thread != headers[1]:
            headers[1] = thread 
            fp.write(f"</ul><h2>{thread['title']}</h2><ul>")
        fp.write(format_dl_link(channel, thread, comment, attachment))
    fp.write(CLOSING_HTML)

logging.info(f"Printing attachments to {os.path.join(os.getcwd(),'attachments.html')}")
logging.info("Follow the links in that file to download message attachments.")

#### Raw JSON ###########
clean_name = ''.join(char for char in archive['workspace']['name'] if char.isalnum())
archive_filename = f"archive_{clean_name}.json"
logging.info(f"Saving raw archive to {archive_filename}")
with open(os.path.join("output", archive_filename), "w") as fp:
    json.dump(archive, fp, ensure_ascii=True, indent=2)

logging.info("It is finished.")
