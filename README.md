# RedditArchiver

<p align="center"><img src="https://github.com/ailothaen/RedditArchiver/blob/main/github/logo.png?raw=true" alt="RedditArchiver logo" width="500"></p>

redditarchiver is a web application that lets you download Reddit submissions on your device to keep a copy of them for archival purposes.
Downloaded submissions are included in a html file with formatting and navigation features. (You can see an example with the file [example.html](https://github.com/ailothaen/RedditArchiver/blob/main/github/example.html))

ℹ️ Looking for RedditArchiver without the web server, which consists only of a Python script? Check [RedditArchiver-standalone](https://github.com/ailothaen/RedditArchiver-standalone)

## Screenshots

<p align="center">
<img src="https://github.com/ailothaen/RedditArchiver/blob/main/github/screenshot1.png?raw=true" alt="RedditArchiver logo" width="200">
<img src="https://github.com/ailothaen/RedditArchiver/blob/main/github/screenshot2.png?raw=true" alt="RedditArchiver logo" width="200">
<img src="https://github.com/ailothaen/RedditArchiver/blob/main/github/screenshot3.png?raw=true" alt="RedditArchiver logo" width="200">
<img src="https://github.com/ailothaen/RedditArchiver/blob/main/github/screenshot4.png?raw=true" alt="RedditArchiver logo" width="200">
</p>

## How does it work

When someone requests the download of a submission, the application uses in background the Reddit API to "download" the full content of the thread. Then, the content is put in a HTML file and served to requesting user.


## Why do I have to allow RedditArchiver to "read through my account"?

Each user, when interacting with Reddit API, has a "speed limit" of how much submissions/comments they are allowed to read. 
If everyone was using the name of RedditArchiver to read submissions, this speed would be reached quickly.

Therefore, RedditArchiver reads Reddit **on behalf of the requesting user**, and not on its own behalf, to avoid running into rate limiting issues. Please note that, when you allow RedditArchiver to "read through your account", you **only allow it** to **read public submissions on your behalf**: RedditArchiver is not able to see your upvoted/saved posts, your user information, or your password, because the "read" permission does not cover this. It is not even able to see your Reddit username.


## Configuration

For configuration reference, see [CONFIG.md](https://github.com/ailothaen/RedditArchiver/blob/main/CONFIG.md).


## Host your own instance

If you want to host your own instance on a little server of yours (and you should!), here is a guide on how to proceed (that may require some small changes depending on your exact environment):

### Install system dependencies

```bash
# apt install python3-pip python3-venv
```

It is strongly advised to create a system user dedicated to the app:

```bash
# adduser redditarchiver
```

### Create the Reddit app

Go to https://www.reddit.com/prefs/apps and create a new app. The type should be "web app" and the redirect URI should be `<your endpoint>/token`. So for example, if your app is going to be accessible on `https://redditarchiver.example.com`, it should be `https://redditarchiver.example.com/token`. (You are not forced to expose the app on the Internet – a private IP address also works)

Take note of the app ID and the app secret.

### Install the app

Drop all the content of `src` in a directory on your server.

Make sure the running user has write access to directories `data`, `logs`, `output` and `run`, and can run `run.sh`.

```bash
# chown redditarchiver: . -R
# chmod 444 * -R
# chmod 544 static templates -R
# chmod 744 run.sh data run logs output -R
```

Switch to the dedicated user, create a Python virtualenv and activate it:

```bash
# su redditarchiver
$ python3 -m venv env
$ source env/bin/activate
```

Install Python dependencies:

```bash
(env) $ pip install -r requirements.txt
```

Switch back to root.

Edit the config file (`config.yml.example`), then rename it to `config.yml`.

Copy `redditarchiver.service` into `/etc/systemd/system`. Do not forget to change directories and users in the file.

Then
```bash
# systemctl daemon-reload
# systemctl enable redditarchiver
# systemctl start redditarchiver
```

### Setup reverse proxy

The app needs a reverse proxy (such as Apache or nginx) in front of it to work. You may use the following Apache configuration for example:

```
<Location />
    ProxyPass unix:/srv/redditarchiver/gunicorn.sock|http://127.0.0.1/
    ProxyPassReverse unix:/srv/redditarchiver/gunicorn.sock|http://127.0.0.1/
</Location>
```

Do not forget to enable mod_proxy and mod_proxy_http on Apache.

You also need to give appropriate rights to the Apache user on `run` directory:

```
# chgrp www-data run
# chmod 2774 run -R
```

Restart both Apache and RedditArchiver.


### Docker Compose

To set up and run RedditArchiver using Docker Compose, follow these steps: 

1. Ensure you have Docker and Docker Compose installed
2. Make sure you have a Reddit app set up as described above, but use `http://localhost/token` as the redirect URI.
3. Make sure to have the REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET environment variables set in your shell.
4. Build and run the services:
```bash
docker compose up --build
```
5. The app should now be accessible on `http://localhost`


## Licensing

This software is licensed [with MIT license](https://github.com/ailothaen/RedditArchiver/blob/main/LICENSE).
