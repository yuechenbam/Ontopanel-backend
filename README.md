# Ontopanel-backend

## What is Ontopanel?

Ontopanel is a plugin in diagrams.net that helps domain experts to build ontologies and method graph visually.

It is designed within the framework of the [Materials Open Laboratory (MatOLab)](https://github.com/Mat-O-Lab) by [Bundesanstalt für Materialforschung und -prüfung (BAM)](https://www.bam.de/Navigation/DE/Home/home.html) to solve the problems encountered by domain experts when building ontologies graphically using diagrames.net, such as ontology reuse, ontology transformation and data mapping.

It consist of three tools, their applications can be found in [Ontopanel video tutorials](https://github.com/yuechenbam/yuechenbam.github.io):

### Library

Ontopanel-Library is a XML library for ontology conceptualization that provides a set of shapes to represent each element of the OWL specification. It is based on Chowlk library.

### EntityManager

EntityManager is a tool that allows user to upload their ontologies and export entities in graphs in diagrams.net.

### Convertor:

Convertor is a tool that validates current graph and convert it into diagrams.net into OWL. It can also realize data mapping -- to combine experimental dataset with the method graph.

## Backend

This project is the backend of Ontopanel and communicates with [Ontopanel-frontend](). Diagrams.net provides permission to add plugins so that users can load the Ontopanel interface. Please follow the tutorial of [Ontopanel-frontend](https://github.com/yuechenbam/Ontopanel-frontend) to set up the frontend.

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
SECRET_KEY="your secret key value"
DEBUG=1 # 1 is True, 0 is False

# Send mail server configuration, used for user password change
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

[Ontopanel-fontend](https://github.com/yuechenbam/Ontopanel-frontend) - Ontopanel's frontend source code.

## Documentation

[Swagger API documentation](https://ontopanel.herokuapp.com/swagger)

## Publications

[Ontopanel: A Tool for Domain Experts Facilitating Visual Ontology Development and Mapping for FAIR Data Sharing in Materials Testing](https://link.springer.com/article/10.1007/s40192-022-00279-y)

## Contact

Yue Chen (yue.chen@bam.de)

Markus Schilling (Markus.Schilling@bam.de)
