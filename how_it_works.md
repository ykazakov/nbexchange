# How the NBExchange service works

nbexchange is an extension to [nbgrader](https://github.com/jupyter/nbgrader) which provides a mechanism for assignments to transferred in a _distributed_ Jupyter Notebooks environment. (See https://nbgrader.readthedocs.io/en/stable/exchange/exchange_api.html for documentation on how nbgrader expects to operate.)

Configuration documentation is in the [README.md](README.md)

<!-- TOC -->
- [How the NBExchange service works](#how-the-nbexchange-service-works)
  - [It's all about the `actions`](#its-all-about-the-actions)
    - [The calls](#the-calls)
      - [list](#list)
      - [release-assignment](#release-assignment)
      - [fetch-assignment](#fetch-assignment)
      - [submit](#submit)
      - [collect](#collect)
      - [release-feedback](#release-feedback)
      - [fetch-feedback](#fetch-feedback)
- [API Specification for the NBExchange service](#api-specification-for-the-nbexchange-service)
  - [Assignments](#assignments)
  - [Assignment](#assignment)
  - [Submission](#submission)
  - [Collections](#collections)
  - [Collection](#collection)
  - [Feedback](#feedback)

<!-- /TOC -->

## It's all about the `actions`

Fundamentally, the exchange revolves around `action` table - this is where we record who does what, and the location of the file is held.

The location follows a standard format:

    path.join(
        base_storage_location,
        org_id,
        action,
        course_code,
        assignment_code,
        time.now(),
        filename
    )


### The calls

Lets follow an assignment cycle, and see how the exchange records everything

In all cases, the user is _authenticated_ using the `get_current_user` method, and _subscribed_ to the `course` with the `role` defined in that call.

All calls check that the user is subscribed to the course given in the parameter
#### list

    GET /assignments?course_id=$cid)

Get list of all _assignments_ associated with that course. We return a list of all `released` assignments.

#### release-assignment

    POST /assignment?course_id=$cid&assignment_id=$aid, files = _zip-file_

We verify the user is an `instructor`, and subscribed to the course.

1. Create the assignment and link it to the course,
2. Grab the first uploaded file (we use `.zip` files for assignments) and store it in a _location_,
3. Create an `action` record, noting `action=released`, the assignment, file location, who did the action, and add a timestamp

#### fetch-assignment

    GET /assignment?course_id=$cid&assignment_id=$aid

1. Find the `released` _action_ for that assignment, and download the file from the given `location`
2. Create an `action` record, noting `action=fetched`, the assignment, file location, who did the action, and add a timestamp

#### submit

    POST /submission?course_id=$cid&assignment_id=$aid, files = _zip-file_

1. Grab the first uploaded file (we use `.zip` files for assignments) and store it in a _location_,
2. Create an `action` record, noting `action=submitted`, the assignment, file location, who did the action, and add a timestamp

#### collect

We verify the user is an `instructor`, and subscribed to the course.

Get a list of _all_ available submissions (GET `/collections?course_id=$cid&assignment_id=$aid` - optional `&user_id=$uid`)

For each submission listed:
1. Download the file from the given `location`
2. Create an `action` record, noting `action=collected`, the assignment, file location, who did the action, and add a timestamp

#### release-feedback

We verify the user is an `instructor`, and subscribed to the course.

Each autograded `.ipynb` file has a matching `.html` file - For each `.html` file:

1. Grab the first uploaded file (POST `/feedback?course_id=$cid&assignment_id=$aid&notebook=$nb&student=$sid&timestamp=$ts&checksum=$cs`, files = _text-file_), and store it in a _location_,
    - `timestamp ($ts)`, in this instance, it the timestamp recorded from the student _submission_. 
2. Record the details, noting the notebook, the instructor (this.user), the student ($sid), and the given timestamp ($ts)
3. Create an `action` record, noting `action=feedback_released`, the assignment, file location, who did the action, and add a timestamp

#### fetch-feedback

    GET /feedback?course_id=$cid&assignment_id=$aid

Download all the feedback for the current user, for the given course & assignment.

Note that the (`.html`) feedback files are held as `base64-encoded` content in the returned data-object.

Create an `action` record, noting `action=feedback_fetched`, the assignment, file location, who did the action, and add a timestamp

# API Specification for the NBExchange service

All URLs relative to `/services/nbexchange`

## Assignments

    .../assignments?course_id=$course_code

**GET**: returns list of assignments

Returns 

    {"success": True,
        "value": [{
            "assignment_id": "$assignment_code",
            "course_id": "$course_code",
            "student_id": Int
            "status": Str,
            "path": path,
            "notebooks": [
                { "notebook_id": x.name,
                  "has_exchange_feedback": False,
                  "feedback_updated": False,
                  "feedback_timestamp": None, } for x in assignment.notebooks],
            "timestamp": action.timestamp.strftime(
                "%Y-%m-%d %H:%M:%S.%f %Z"
            ),
        },
        {},..
        ]}
or

    {"success": False, "note": $note}


## Assignment

    .../assignment?course_id=$course_code&assignment_id=$assignment_code

**GET**: downloads assignment

Returns binary data or raises Exception (which is returned as a `503` error)
     
**POST**: (role=instructor, with file): Add ("release") an assignment
returns

    {"success": True, "note": "Released"}

or raises Exception (which is returned as a `503` error)

**DELETE**:  (role=instructor, with file): Remove an assignment.

Marks an asiignment as ``active: False``, and forgets any associated notebooks. Returns

    {"success": True, "note": "Assignment '$assignment_code' on course '$course_code' marked as unreleased by user $user" 

Takes as *optional* parameter ``purge``. This will delete the notebooks, the assignment,
and any associated data (``actions``, ``feedback``, etc). Returns

    {"success": True, "note": "Assignment '$assignment_code' on course '$course_code' deleted and purged from the database by user $user"}

If there are permission issues, returns

    {"success": False, "note": $note}

## Submission

    .../submission?course_id=$course_code&assignment_id=$assignment_code

**POST**: stores the submission for that user
returns

    {"success": True, "note": "Released"}

or raises Exception (which is returned as a `503` error)

## Collections


    .../collections?course_id=$course_code&assignment_id=$assignment_code

**GET**: gets a list of submitted items
Return: same as `Assignments <#assignments>`

## Collection

    .../collections?course_id=$course_code&assignment_id=$assignment_code&path=$url_encoded_path

**GET**: downloads submitted assignment
Return: same as `Assignment <#assignment>`

## Feedback

**GET**: downloads feedback

    .../feedback?course_id=$course_code&assignment_id=$assignment_code

Optional parameter

    user_id=$user_id

Return: Returns a data structure similar to the above, except `value` is a list of feedback items:

    {"success": True,
        "value": [{
                "content": base64-encoded html file
                "filename": notebook-name.html
                "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S.%f %Z")
                "checksum": checksum
        },
        {},..
        ]}

**POST**: uploads feedback (one notebook at a time)

    .../feedback?course_id=$course_code&assignment_id=$assignment_code&notebook=$nb_name&student=$sid&timestamp=$ts&checksum=$abc123

If there are permission issues, returns

    {"success": False, "note": $note}

else

    {"success": True, "note": "Feedback released"}

or raises an error - should be a 404 or 412.