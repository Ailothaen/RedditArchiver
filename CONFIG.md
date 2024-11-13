There are two config files:
- `config.yml` is to be used in standard deployments
- `config-docker.yml` is to be used in Docker deployments
Both files have an `.example` appended to it, make sure you remove it on one of them when you set up the app.

Here is an example of what a full `config.yml` file would look like:

```
app:
  name: Reddit Archiver
  url: "https://redditarchiver.example.com"
  only-allow-from:
    - '1.2.3.5/32'
    - '3401:722::0119::/64'
  disable-recursion-limit: false
reddit:
  client-id: c66425afb0f54a27905b74c2f8449d8f
  client-secret: 4747072335d74e2b8ac8-e4fbec152dca
  root: 'https://www.reddit.com'
paths:
  output: output
defaults:
  dateformat: '%a %Y-%m-%d at %H:%M'
```

|Value|Meaning|
|---|---|
|app.name|Name of the app, as it appears on the frontend.|
|app.url|URL of the main endpoint of the app, where it will be accessible to the users. Do not include a trailing slash.|
|app.only-allow-from|A list of IP ranges you want to restrict the app access to. If you want to allow everyone to access the app, remove this property. **Not available in Docker deployments**|
|app.disable-recursion-limit|If the level of nested replies in a thread is *very* high (about 1000+, which is very rare), the generating process will fail because of Python's recursion limit. Setting this property to `true` disables the limit. However, please note that this may lead to higher resource usage, and might potentially crash the app.|
|reddit.client-id|Client ID of your Reddit app, as shown in https://www.reddit.com/prefs/apps|
|reddit.client-secret|Client secret of your Reddit app, as shown in https://www.reddit.com/prefs/apps|
|reddit.root|Main endpoint of Reddit. You should not have to edit this value.|
|paths.output|Where the saved HTML files will be stored. You should not have to edit this value. **Not available in Docker deployments**|
|defaults.dateformat|The default date format that will be used in output files. Format is strftime syntax in Python.|