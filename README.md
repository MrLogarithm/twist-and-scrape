# Twist and Scrape

_We'll scrape it up, baby, now!_

Simple Python utility for scraping and archiving a Twist workspace.

## Installation

Clone the repo:
```bash
$ git clone https://github.com/MrLogarithm/twist-and-scrape.git
```

Install Python dependencies:
```bash
$ pip install pyyaml requests
```

## Usage

1. Follow the instructions under https://developer.twist.com/v3/#oauth-2 to obtain an oauth2 test token for your workspace. In `config.yaml`, replace `token: none` with `token: <your test token>`.

2. Open your Twist workspace in a browser and make note of the workspace id: this is the number in the URL, e.g. twist.com/a/**123456**. In `config.yaml`, replace `workspace_id: none` with `workspace_id: <your workspace id>`.

3. Run the script:
```bash
$ python twist-and-scrape.py
```

4. The script will create a directory named `output/` containing your archived workspace.
- `channels/` includes a subdirectory for each channel in your workspace. Each contains a plaintext dump of every thread in that channel.
- `archive_<workspace name>.json` is a JSON object recording all of the users, channels, threads, and comments from your workspace. See https://developer.twist.com/v3/ for details about the keys and values.
- `attachments.html` is an HTML file with links to download the attachments from every post. Cloudflare prevents `twist-and-scrape` from downloading these automatically, so you will have to manually follow the links in this file if you want to preserve attachments.

## Notes

This script only archives threads and the public-facing part of user profiles: PMs and private user details are not included. (Note that users' names and emails are part of their public profile.)

Attachments must be downloaded manually (see point #4 above).

This has only been lightly tested and there are likely some uncaught bugs.
