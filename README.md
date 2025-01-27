A dockerised service that replaces the defaukt nbgrader Exchange.

<!-- TOC -->

- [What is nbexchange](#what-is-nbexchange)
- [Why nbexchange](#why-nbexchange)
  - [Compatibility](#compatibility)
- [Documentation](#documentation)
  - [Database relationships](#database-relationships)
- [Installing](#installing)
  - [nbexchange service](#nbexchange-service)
    - [Helm](#helm)
  - [nbgrader plugin](#nbgrader-plugin)
- [Configuration](#configuration)
  - [Configuring the `nbexchange` service](#configuring-the-nbexchange-service)
    - [**`user_plugin_class`** revisited](#user_plugin_class-revisited)
  - [Configuring `nbgrader` to use the alternative exchange](#configuring-nbgrader-to-use-the-alternative-exchange)
- [Contributing](#contributing)
  - [Releasing new versions](#releasing-new-versions)

<!-- /TOC -->

# What is nbexchange

nbexchange is an extension to [nbgrader](https://github.com/jupyter/nbgrader) which provides a mechanism for assignments to transferred in a _distributed_ Jupyter Notebooks environment.

The default for nbgrader is to assume all users are on the same computer, and files are copied from one directory to another - thus:
![exchange mechanism on a single filesystem](file_exchange.png)

When using jupyter notebooks in a distributed [dockerised] system, there is no common filesystem - so an alternative mechanism is
needed - something that allows files to be transfered via some independant service - eg: 
![exchange mechanism in a dockerised environment](dockerised_exchange.png) 

nbexchange provides both that intermediate filestore, and the plugins for nbgrader to use it.

# Why nbexchange

From [nbgrader](https://github.com/jupyter/nbgrader): _Assignments_ are `created`, `generated`, `released`, `fetched`, `submitted`, `collected`, `graded`. Then `feedback` can be `generated`, `released`, and `fetched`.

The exchange is responsible for recieving _release_/_fetch_ path, and _submit_/_collect_ cycle. It also allows _feedback_ to be transferred from instructor to student.

In doing this, the exchange is the authoritative place to get a list of what's what.

`nbexchange` is an external exchange plugin, designed to be run as a docker instance (probably inside a K8 cluster)

It's provides an external store for released & submitted assignments, and the feeback cycle.

Following the lead of other Jupyter services, it is a `tornado` application.

## Compatibility

This version installs `nbgrader`  0.9.1 (which makes it compatible with JupyterLab & Notebook 7)

# Documentation

This exchange has some assumptions because of the environment required it.

There are the following assumptions:

- You have an API for authenticating users who connect to the exchange (possibly Jupyterhub, but not always)
- Usernames will be unique across the whole system 
- Internal storage is in two parts:
  - An sql database for metadata, and
  - A filesystem for, well, files.
- There will always be a `course_code`
  - There may be multiple assignments under one course,
  - `assignment_code`s will be unique to a course
  - `assignment_code`s may be repeated in different  `organisation_id`
  - Note that default nbgrader does not distinguish `assignment_code`s across different `course_codes`, within the same `gradebook` database.
- There will always be an `organisation_id`
  - `course_code`s must be uniqie within an `organisation_id`,
  - `course_code`s may be repeated in different `organisation_id`

## Database relationships

![Diagram of table relationships](table_relationships.png)

# Installing

nbexchange is a two-part system: it requires
1. the `nbexchange` service to be running (in a docker container)
2. the plugins to be installed in the jupyter notebook (which will also install `nbgrader`)

## nbexchange service

The nbexchange is designed to be run as a docker instance, possibly in a kubernetes cluster

See the `Dockerfile` / `docker-compose.yml` files for creating the service.

### Helm

The service can be deployed via `helm`, ie

```
helm install --name nbexchange --namespace default ./chart -f myconfiguration.yaml
```

## nbgrader plugin

Installing nbexchange in a jupyter notebook will automatically install nbgrader.

nbexchange is not released to Pypy or anaconda, however you can install direct from GitHub - eg:

```
pip install https://github.com/edina/nbexchange/archive/v1.4.0.tar.gz
....
```

Note that nbgrader installs and enables the jupyter extensions automatically - you may wish to switch *off* `formgrader` and `create_assignment` for non-teachers: YMMV

# Configuration

## Configuring the `nbexchange` service

The exchange uses `nbexchange_config.py` for configuration.

This is an example config file:

```python
from nbexchange.handlers.auth.user_handler import BaseUserHandler

class MyUserHandler(BaseUserHandler):

    def get_current_user(self, request):
        return {
          "name": "username",
          "full_name": "Joe Bloggs",
          "course_id": "cool_course_id",
          "course_title": "cool course",
          "course_role": "Student",
          "org_id": 1,
          "cust_id": 2,
    }


c.NbExchange.user_plugin_class = MyUserHandler

c.NbExchange.base_url = /services/exchange
c.NbExchange.base_storage_location = /var/data/exchange/storage
c.NbExchange.db_url = mysql://username:password@my.msql.server.host:3306/db_name
```

- **`user_plugin_class`**

For the exchange to work it needs some details about the user connecting to it. This parameter defines the class that provides the `get_current_user` method.

See below for more details on that.

- **`base_url`**

This is the _service_ url used by jupyterhub, and defaults to `/services/nbexchange/`

Can also be defined in the environment variable `JUPYTERHUB_SERVICE_PREFIX`

- **`base_storage_location`**

This is where the exchange will store the files uploaded, and defaults to `/tmp/courses`

Can also be defined in the environment variable `NBEX_BASE_STORE`

- **`db_url`**

This is the database connector, and defaults to an in-memory SQLite (`sqlite:///:memory:`)

Can also be defined in the environment variable `NBEX_DB_URL`

- **`db_kwargs`** 

Where to include any kwargs to pass to the database connection.

- **`max_buffer_size`**

The service will limit the size of uploads. The figure is bytes

By default, upload sizes are limited to 5GB (5253530000)

- **`upgrade_db`**, **`reset_db`**, **`debug_db`**  

Do stuff to the db... see the code for what these do

### **`user_plugin_class`** revisited

For the exchange to work, it needs some details about the user connecting to it - specifically, it needs 7 pieces of information:

- `name`: The username of the person (eg `perllaghu`).
  - In our system, we prefix the persons login username with the org_id for where their from (eg `1_perllaghu`.)
- `full_name`: The optional full name, if supplied by the remote authenticator.
  - The full name appears in the `formgrader` UI.
- `course_id`: The course code as used in nbgrader (eg `cool_course`).
  - This is `course_id` not `course_code`, as nbgrader uses `course_id` for this piece of data.
- `course_title`: A long name for the course (eg `A course of understanding thermondynamics in bulk refrigerant transport").
- `course_role`: The role of the user, normally `Student` or `Instructor`. (currently only `Instructor` get privilaged actions).
- `org_id`: As mentioned above, nbexchange divides courses and users across organisations. This is an id (numeric) for the org_id for the user.
- `cust_id`: Whilst most of the exchange is keyed on the `org_id`, knowing _customer_ can be useful. This is an id (numeric) for the org_id for the user.

## Configuring `nbgrader` to use the alternative exchange

The primary reference for this should be the `nbgrader` documentation - but in short:

1. Use the `nbgrader` code-base that supports the external exchange (nbgrader 0.7 and later)
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

These plugins will also check the size of _releases_ & _submissions_

`c.Exchange.max_buffer_size = 204800  # 200KB`

By default, upload sizes are limited to 5GB (5253530000)
The figure is bytes

# Contributing

See [how_it_works.md](how_it_works.md) for an extended explanation as to how the exchange works, internally

See [Contributing.md](CONTRIBUTING.md) for details on how to extend/contribute to the code.

## Releasing new versions

* Update `pyproject.toml` and `nbexchange/__init__.py` to change to the new version
* Create a new git tag doing `git tag -a vx.y.z` to match the version above
