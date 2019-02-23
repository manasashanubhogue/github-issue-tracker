# github-issue-tracker
Given github public url, fetch issues based on filters

## Developer Guide
### Clone project

```bash
$  git clone git@github.com:manasashanubhogue/github-issue-tracker.git
```

### Setup virtual environment

```bash
$ virtualenv venv
$ source venv/bin/activate
```

### Install dependencies

```bash
$ pip install -r requirements.txt
```

Migrate, create post-deletion fallback entries, create a superuser and run the server:

```bash
$ python manage.py migrate
$ python manage.py createsuperuser
$ python manage.py runserver
```

## Solution
Given public github url : Fetch the number of open issues using github API's . Based on filters (days), using datetime lib, filter the data.

## Edge Cases:
1. Public/ Private or invalid repo : Appropriate message
2. API limit exceeded
