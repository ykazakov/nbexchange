![Linted](https://github.com/edina/nbexchange/workflows/Linted/badge.svg?branch=prepare_for_public_release)
[![codecov](https://codecov.io/gh/edina/nbexchange/branch/prepare_for_public_release/graph/badge.svg)](https://codecov.io/gh/edina/nbexchange)

A Jupyterhub service that replaces the nbgrader Exchange.

<!-- TOC -->

- [Highlights of nbexchange](#highlights-of-nbexchange)
    - [Compatibility](#compatibility)
- [Documentation](#documentation)
    - [Database relationships](#database-relationships)
- [Installing](#installing)
- [Contributing](#contributing)
- [Configuration](#configuration)
    - [Configuring `nbexchange`](#configuring-nbexchange)
    - [Configuring `nbgrader`](#configuring-nbgrader)
- [Know To-Do stuff](#know-to-do-stuff)

<!-- /TOC -->

# Highlights of nbexchange


From [nbgrader](https://github.com/jupyter/nbgrader): _Assignments_ are `created`, `generated`, `released`, `fetched`, `submitted`, `collected`, `graded`. Then `feedback` can be `generated`, `released`, and `fetched`.

The exchange is responsible for recieving *release*/*fetch* path, and *submit*/*collect* cycle. It also allows *feedback* to be transferred from instructor to student.

In doing this, the exchange is the authoritative place to get a list of what's what.

`nbexchange` is an external exchange plugin, designed to be run as a docker instance (probably inside a K8 cluster)

It's provides an external store for released & submitted assignments, and [soon] the feeback cycle.

Following the lead of other Jupyter services, it is a `tornado` application.

## Compatibility

This version is compatible with `nbgrader` 0.5

# Documentation

This exchange has some fundamental design decisions driven by the environment which drove its creation.

There are the following assumptions:
* You have an API for authenticating users who connect to the exchange (probably Jupyterhub, but not always)
* Usernames will be unique across the whole system
* Internal storage is in two parts:
    * An sql database for metadata, and
    * A filesystem for, well, files.
* There will always be a course_code
    * There may be multiple assignments under one course,
    * `assignment_code`s will be unique to a course
    * `assignment_code`s may be repeated in different `organisation_id`
* There will always be an `organisation_id`
    * `course_code`s must be uniqie within an `organisation_id`,
    * `course_code`s may be repeated in different `organisation_id`

All code should have `docstrings`.

Documentation currently in [docs/](docs/) - should be in readthedocs

## Database relationships

![Diagram of table relationships](table_relationships.png)

# Installing

The exchange is designed to be deployed as a docker instance - either directly on a server, or in a K8 cluster (which is where it was originally developed for)

`nbgrader` requires a plugin (code included) for the 

# Contributing

See [Contributing.md](CONTRIBUTING.md)

# Configuration

There are two parts to configuring `nbexchange`:

* Configure `nbexchange` itself
* Configure `nbgrader` to use `nbexchange`

## Configuring `nbexchange`

The exchange uses `nbexchange_config.py` for configuration.

```python
from nbexchange.handlers.auth.user_handler import BaseUserHandler

class MyUserHandler(BaseUserHandler):
    
    def get_current_user(self, request):
        return {
          "name": "myname",
          "course_id": "cool_course_id",
          "course_title": "cool course",
          "course_role": "Student",
          "org_id": 1,
    }


c.NbExchange.user_plugin_class = MyUserHandler

c.NbExchange.base_url = /services/exchange
c.NbExchange.base_storage_location = /var/data/exchange/storage
c.NbExchange.db_url = mysql://username:password@my.msql.server.host:3306/db_name
```

* **`base_url`**

This is the _service_ url for jupyterhub, and defaults to `/services/nbexchange/`

Can also be defined in the environment variable `JUPYTERHUB_SERVICE_PREFIX`

* **`base_storage_location`**

This is where the exchange will store the files uploaded, and defaults to `/tmp/courses`

Can also be defined in the environment variable `NBEX_BASE_STORE`

* **`db_url`**

This is the database connector, and defaults to an in-memory SQLite (`sqlite:///:memory:`)

Can also be defined in the environment variable `NBEX_DB_URL`

* **`user_plugin_class`**

This is a class that defines how `get_current_user` works.

For the exchange to work, it needs some details about the user connecting to it - specifically, it needs 5 pieces of information:

* `name`: The username of the person (eg `perllaghu`),
* `course_id`: The course code as used in nbgrader (eg `cool_course`),
* `course_title`: A long name for the course (eg `A course of understanding thermondynamics in bulk refrigerant transport"),
* `course_role`: The role of the user, normally `Student` or `Instructor`. (currently only `Instructor` get privilaged actions),
* `org_id`: As mentioned above, nbexchange divides courses and users across organisations. This is an id (numeric) for the org_id for the user.

## Configuring `nbgrader`

The primary reference for this should be the `nbgrader` documentation - but in short:

1. Use the `nbgrader` code-base that supports the external exchange
2. Install the code from `nbexchange/plugin` into `nbgrader`
3. Include the following in your `nbgrader_config.py` file:

```python
## A plugin for collecting assignments.
c.ExchangeFactory.collect = 'nbexchange.plugin.ExchangeCollect'
## A plugin for exchange.
c.ExchangeFactory.exchange = 'nbexchange.plugin.Exchange'
## A plugin for fetching assignments.
c.ExchangeFactory.fetch_assignment = 'nbexchange.plugin.ExchangeFetchAssignment'
## A plugin for fetching feedback.
c.ExchangeFactory.fetch_feedback = 'nbexchange.plugin.ExchangeFetchFeedback'
## A plugin for listing exchange files.
c.ExchangeFactory.list = 'nbexchange.plugin.ExchangeList'
## A plugin for releasing assignments.
c.ExchangeFactory.release_assignment = 'nbexchange.plugin.ExchangeReleaseAssignment'
## A plugin for releasing feedback.
c.ExchangeFactory.release_feedback = 'nbexchange.plugin.ExchangeReleaseFeedback'
## A plugin for submitting assignments.
c.ExchangeFactory.submit = 'nbexchange.plugin.ExchangeSubmit'
```

# Know To-Do stuff

* ~~Get the initial code up~~
* Get a master-branch established
* Get proper install method for `nbgrader` external-exchange plugin
* Get a `handlers/auth/user_handler` to get details from jupyterhub (users, courses, and assignments should all be in the config file)
* ~Get travis? CI integration working~
* Get an external sanity-check for the code
* Get docs to ReadTheDocs
