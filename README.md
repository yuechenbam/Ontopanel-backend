# Ontopanel-backend

## What is Ontopanel?

Ontopanel is a plugin in diagrams.net that helps domain experts to build ontologies and method graph in a simpler way.

It consist of three tools, their applications can be found in [Ontopanel video tutorials ](https://github.com/yuechenbam/yuechenbam.github.io):

### Library

Ontopanel-Library is a XML library for ontology conceptualization that provides a set of shapes to represent each element of the OWL specification. It is based on Chowlk library.

### EntityManager

EntityManager is a tool that allows user to upload their ontologies and export entities in diagrams.net.

### Convertor:

Convertor is a tool that validates current graph and convert it into diagrams.net into OWL.
It can also realize data mapping.

## Installation

### Clone the project

```
git clone https://github.com/yuechenbam/Ontopanel-backend.git

```

### Requirements:

```
pip install -r requirements.txt
```

### Create .env file in root

```
# The variables in settings.py
SECRET_KEY="your key value"
DEBUG=1 # 1 is True, 0 is False

# Send mail server configuration
EMAIL_HOST_USER = your email address
EMAIL_HOST_PASSWORD = your email password
```

### Database connection configuration

```
# change below in setting.py to your own database
DATABASES = {}
if 'test' in sys.argv:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


else:
    DATABASES['default'] = dj_database_url.config(
        conn_max_age=600, ssl_require=True)

```

### Run the app

```
python manage.py runserver
```

## Related repositories and links

[Ontopanel GithubPage repository with tutorials](https://github.com/yuechenbam/yuechenbam.github.io) - repository of Ontopanel online demo.

[Ontopanel online demo](https://yuechenbam.github.io/src/main/webapp/index.html) - diagrams.net, contains the Ontopanel plugin hosted on the GithubPage.

[Ontopanel-fontend]() - Ontopanel's frontend source code.

## Documentation

[API documentation]()

## Contact

Yue Chen (yue.chen@bam.de)
