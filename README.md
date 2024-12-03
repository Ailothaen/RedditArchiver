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

~~Each user, when interacting with Reddit API, has a "speed limit" of how much submissions/comments they are allowed to read. If everyone was using the name of RedditArchiver to read submissions, this speed would be reached quickly.~~

~~Therefore, RedditArchiver reads Reddit **on behalf of the requesting user**, and not on its own behalf, to avoid running into rate limiting issues. Please note that, when you allow RedditArchiver to "read through your account", you **only allow it** to **read public submissions on your behalf**: RedditArchiver is not able to see your upvoted/saved posts, your user information, or your password, because the "read" permission does not cover this. It is not even able to see your Reddit username.~~

**Update:** Because of the Reddit API policy changes in 2023, this is no longer true: rate limiting is now done on app basis and no longer on user+app basis, which makes that "query saving" feature useless. The account link is still required because some features rely on it, but it may be removed in a future update, as it is now irrelevant.


## Configuration

For configuration reference, see [CONFIG.md](https://github.com/ailothaen/RedditArchiver/blob/main/CONFIG.md).


## Host your own instance (without Docker)

If you want to host your own instance on a little server of yours (and you should!), here is a guide on how to proceed (that may require some small changes depending on your exact environment):

### Install system dependencies

```bash
apt install python3-pip python3-venv
```

It is strongly advised to create a system user dedicated to the app:

```bash
adduser redditarchiver
```

### Create the Reddit app

Go to https://www.reddit.com/prefs/apps and create a new app. The type should be "web app" and the redirect URI should be `<your endpoint>/token`. So for example, if your app is going to be accessible on `https://redditarchiver.example.com`, it should be `https://redditarchiver.example.com/token`. (You are not forced to expose the app on the Internet – a private IP address also works)

Take note of the app ID and the app secret.

### Install the app

Drop all the content of `src` in a directory on your server.

Make sure the running user has write access to directories `data`, `logs`, `output` and `run`, and can run `run.sh`.

```bash
chown redditarchiver: . -R
chmod 444 * -R
chmod 544 static templates -R
chmod 744 run.sh data run logs output -R
```

Switch to the dedicated user, create a Python virtualenv and activate it:

```bash
su redditarchiver
python3 -m venv env
source env/bin/activate
```

Install Python dependencies:

```bash
(env) pip install -r requirements.txt
```

Switch back to root.

Edit the config file (`config.yml.example`), then rename it to `config.yml`.

Copy `redditarchiver.service` into `/etc/systemd/system`. Do not forget to change directories and users in the file.

Then
```bash
systemctl daemon-reload
systemctl enable redditarchiver
systemctl start redditarchiver
```

### Setup reverse proxy

The app needs a reverse proxy (such as Apache or nginx) in front of it to work. You may use the following Apache configuration for example:

```apache
<Location />
    ProxyPass unix:/srv/redditarchiver/gunicorn.sock|http://127.0.0.1/
    ProxyPassReverse unix:/srv/redditarchiver/gunicorn.sock|http://127.0.0.1/
</Location>
```

Do not forget to enable mod_proxy and mod_proxy_http on Apache.

You also need to give appropriate rights to the Apache user on `run` directory:

```bash
chgrp www-data run
chmod 2774 run -R
```

Restart both Apache and RedditArchiver.


## Host your own instance (with Docker)

(Thank you for [your help](https://github.com/Ailothaen/RedditArchiver/issues/1), @dan1elt0m)

### Create the Reddit app

Go to https://www.reddit.com/prefs/apps and create a new app. The type should be "web app" and the redirect URI should be `<your endpoint>/token`. So for example, if your app is going to be accessible on `https://redditarchiver.example.com`, it should be `https://redditarchiver.example.com/token`. (You are not forced to expose the app on the Internet – a private IP address also works)

Take note of the app ID and the app secret.


### Build the Docker container

Clone this Git directory (or copy all its content) somewhere.

In the `src` directory, edit the config file (`config-docker.yml.example`), then rename it to `config-docker.yml`.

Then, make sure you are in the main directory (the one where you see the Dockerfile), and build the container:

```bash
docker build . -t RedditArchiver
```

### Run the Docker container

```bash
docker run -d -p 8080:80 RedditArchiver
```

This command should run RedditArchiver on the port 8080 on your host.

It is strongly advised to run the container behind a web server container (Apache, nginx...), especially if you expose the service publicly.

It can be useful – though not mandatory – as well to create volumes, for easy access to generated files and logs:

```bash
docker volume create ra_output
docker volume create ra_logs

# then you can pass the volumes in the docker run command
docker run -d -p 8080:80 -v ra_output:/app/output -v ra_logs:/app/logs RedditArchiver
```

Be reminded that the `only-allow-from` feature of the configuration file is not available in a Docker deployment. If you want to restrict access to the service, I would recommend setting the restriction upstream, for example in your apache/nginx/whatever container (that you should already have, right? 😇)


## Licensing

This software is licensed [with MIT license](https://github.com/ailothaen/RedditArchiver/blob/main/LICENSE).
