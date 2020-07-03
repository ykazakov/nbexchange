import logging
import os
import shutil
from os.path import basename
from shutil import copyfile

import pytest

from mock import patch

from nbexchange.plugin import ExchangeList, Exchange
from nbgrader.coursedir import CourseDirectory

from nbexchange.tests.utils import get_feedback_file
from nbgrader.exchange import ExchangeError
from nbgrader.utils import make_unique_key, notebook_hash


logger = logging.getLogger(__file__)
logger.setLevel(logging.ERROR)


feedback1_filename = os.path.join(
    os.path.dirname(__file__), "data", "assignment-0.6.html"
)
feedback1_file = get_feedback_file(feedback1_filename)
feedback2_filename = os.path.join(
    os.path.dirname(__file__), "data", "assignment-0.6-wrong.html"
)
feedback12_file = get_feedback_file(feedback1_filename)

notebook1_filename = os.path.join(
    os.path.dirname(__file__), "data", "assignment-0.6.ipynb"
)
notebook1_file = get_feedback_file(notebook1_filename)
notebook2_filename = os.path.join(
    os.path.dirname(__file__), "data", "assignment-0.6-wrong.ipynb"
)
notebook2_file = get_feedback_file(notebook2_filename)


@pytest.mark.gen_test
def test_list_normal(plugin_config, tmpdir):
    plugin_config.CourseDirectory.course_id = "no_course"

    plugin = ExchangeList(
        coursedir=CourseDirectory(config=plugin_config), config=plugin_config
    )

    def api_request(*args, **kwargs):
        assert args[0] == ("assignments?course_id=no_course")
        assert "method" not in kwargs or kwargs.get("method").lower() == "get"
        return type(
            "Request",
            (object,),
            {
                "status_code": 200,
                "json": (
                    lambda: {
                        "success": True,
                        "value": [
                            {
                                "assignment_id": "assign_1_1",
                                "student_id": "1",
                                "course_id": "no_course",
                                "status": "released",
                                "path": "",
                                "notebooks": [
                                    {
                                        "name": "assignment-0.6",
                                        "has_exchange_feedback": False,
                                        "feedback_updated": False,
                                        "feedback_timestamp": False,
                                    }
                                ],
                                "timestamp": "2020-01-01 00:00.0 UTC",
                            }
                        ],
                    }
                ),
            },
        )

    with patch.object(Exchange, "api_request", side_effect=api_request):
        called = plugin.start()
        assert called == [
            {
                "assignment_id": "assign_1_1",
                "course_id": "no_course",
                "student_id": "1",
                "status": "released",
                "notebooks": [
                    {
                        "feedback_timestamp": False,
                        "feedback_updated": False,
                        "has_exchange_feedback": False,
                        "name": "assignment-0.6",
                    }
                ],
                "path": "",
                "timestamp": "2020-01-01 00:00.0 UTC",
            }
        ]


@pytest.mark.gen_test
def test_list_several_normal(plugin_config, tmpdir):
    plugin_config.CourseDirectory.course_id = "no_course"

    plugin = ExchangeList(
        coursedir=CourseDirectory(config=plugin_config), config=plugin_config
    )

    def api_request(*args, **kwargs):
        assert args[0] == ("assignments?course_id=no_course")
        assert "method" not in kwargs or kwargs.get("method").lower() == "get"
        return type(
            "Request",
            (object,),
            {
                "status_code": 200,
                "json": (
                    lambda: {
                        "success": True,
                        "value": [
                            {
                                "assignment_id": "assign_1_1",
                                "student_id": "1",
                                "course_id": "no_course",
                                "status": "released",
                                "path": "",
                                "notebooks": [
                                    {
                                        "name": "assignment-0.6",
                                        "has_exchange_feedback": False,
                                        "feedback_updated": False,
                                        "feedback_timestamp": False,
                                    }
                                ],
                                "timestamp": "2020-01-01 00:00.0 UTC",
                            },
                            {
                                "assignment_id": "assign_1_2",
                                "student_id": "1",
                                "course_id": "no_course",
                                "status": "released",
                                "path": "",
                                "notebooks": [
                                    {
                                        "name": "assignment-0.6-wrong",
                                        "has_exchange_feedback": False,
                                        "feedback_updated": False,
                                        "feedback_timestamp": False,
                                    }
                                ],
                                "timestamp": "2020-01-01 00:00.1 UTC",
                            },
                        ],
                    }
                ),
            },
        )

    with patch.object(Exchange, "api_request", side_effect=api_request):
        called = plugin.start()
        assert called == [
            {
                "assignment_id": "assign_1_1",
                "course_id": "no_course",
                "student_id": "1",
                "status": "released",
                "notebooks": [
                    {
                        "feedback_timestamp": False,
                        "feedback_updated": False,
                        "has_exchange_feedback": False,
                        "name": "assignment-0.6",
                    }
                ],
                "path": "",
                "timestamp": "2020-01-01 00:00.0 UTC",
            },
            {
                "assignment_id": "assign_1_2",
                "course_id": "no_course",
                "student_id": "1",
                "status": "released",
                "notebooks": [
                    {
                        "feedback_timestamp": False,
                        "feedback_updated": False,
                        "has_exchange_feedback": False,
                        "name": "assignment-0.6-wrong",
                    }
                ],
                "path": "",
                "timestamp": "2020-01-01 00:00.1 UTC",
            },
        ]


@pytest.mark.gen_test
def test_list_several_ignore_released(plugin_config, tmpdir):
    try:
        plugin_config.CourseDirectory.course_id = "no_course"

        os.makedirs("assign_1_3", exist_ok=True)
        copyfile(
            notebook1_filename, os.path.join("assign_1_3", basename(notebook1_filename))
        )

        plugin = ExchangeList(
            coursedir=CourseDirectory(config=plugin_config), config=plugin_config
        )

        def api_request(*args, **kwargs):
            assert args[0] == ("assignments?course_id=no_course")
            assert "method" not in kwargs or kwargs.get("method").lower() == "get"
            return type(
                "Request",
                (object,),
                {
                    "status_code": 200,
                    "json": (
                        lambda: {
                            "success": True,
                            "value": [
                                {
                                    "assignment_id": "assign_1_1",
                                    "student_id": "1",
                                    "course_id": "no_course",
                                    "status": "released",
                                    "path": "",
                                    "notebooks": [
                                        {
                                            "name": "assignment-0.6",
                                            "has_exchange_feedback": False,
                                            "feedback_updated": False,
                                            "feedback_timestamp": False,
                                        }
                                    ],
                                    "timestamp": "2020-01-01 00:00.0 UTC",
                                },
                                {
                                    "assignment_id": "assign_1_3",
                                    "student_id": "1",
                                    "course_id": "no_course",
                                    "status": "released",
                                    "path": "",
                                    "notebooks": [
                                        {
                                            "name": "assignment-0.6-wrong",
                                            "has_exchange_feedback": False,
                                            "feedback_updated": False,
                                            "feedback_timestamp": False,
                                        }
                                    ],
                                    "timestamp": "2020-01-01 00:00.2 UTC",
                                },
                                {
                                    "assignment_id": "assign_1_3",
                                    "student_id": "1",
                                    "course_id": "no_course",
                                    "status": "fetched",
                                    "path": "",
                                    "notebooks": [
                                        {
                                            "name": "assignment-0.6-wrong",
                                            "has_exchange_feedback": False,
                                            "feedback_updated": False,
                                            "feedback_timestamp": False,
                                        }
                                    ],
                                    "timestamp": "2020-01-01 00:00.2 UTC",
                                },
                            ],
                        }
                    ),
                },
            )

        with patch.object(Exchange, "api_request", side_effect=api_request):
            called = plugin.start()
            assert called == [
                {
                    "assignment_id": "assign_1_1",
                    "course_id": "no_course",
                    "student_id": "1",
                    "status": "released",
                    "notebooks": [
                        {
                            "feedback_timestamp": False,
                            "feedback_updated": False,
                            "has_exchange_feedback": False,
                            "name": "assignment-0.6",
                        }
                    ],
                    "path": "",
                    "timestamp": "2020-01-01 00:00.0 UTC",
                },
                {
                    "assignment_id": "assign_1_3",
                    "course_id": "no_course",
                    "student_id": "1",
                    "status": "fetched",
                    "notebooks": [
                        {
                            "feedback_updated": False,
                            "has_exchange_feedback": False,
                            "has_local_feedback": False,
                            "local_feedback_path": None,
                            "notebook_id": "assignment-0.6",
                            "path": os.path.join(
                                os.getcwd(), "assign_1_3/assignment-0.6.ipynb"
                            ),
                        }
                    ],
                    "path": "",
                    "timestamp": "2020-01-01 00:00.2 UTC",
                },
            ]
    finally:
        shutil.rmtree("assign_1_3")


@pytest.mark.gen_test
def test_list_several_latest_only(plugin_config, tmpdir):
    try:
        plugin_config.CourseDirectory.course_id = "no_course"

        os.makedirs("assign_1_3", exist_ok=True)
        copyfile(
            notebook1_filename, os.path.join("assign_1_3", basename(notebook1_filename))
        )

        plugin = ExchangeList(
            coursedir=CourseDirectory(config=plugin_config), config=plugin_config
        )

        def api_request(*args, **kwargs):
            assert args[0] == ("assignments?course_id=no_course")
            assert "method" not in kwargs or kwargs.get("method").lower() == "get"
            return type(
                "Request",
                (object,),
                {
                    "status_code": 200,
                    "json": (
                        lambda: {
                            "success": True,
                            "value": [
                                {
                                    "assignment_id": "assign_1_1",
                                    "student_id": "1",
                                    "course_id": "no_course",
                                    "status": "released",
                                    "path": "",
                                    "notebooks": [
                                        {
                                            "name": "assignment-0.6",
                                            "has_exchange_feedback": False,
                                            "feedback_updated": False,
                                            "feedback_timestamp": False,
                                        }
                                    ],
                                    "timestamp": "2020-01-01 00:00.0 UTC",
                                },
                                {
                                    "assignment_id": "assign_1_3",
                                    "student_id": "1",
                                    "course_id": "no_course",
                                    "status": "released",
                                    "path": "",
                                    "notebooks": [
                                        {
                                            "name": "assignment-0.6-wrong",
                                            "has_exchange_feedback": False,
                                            "feedback_updated": False,
                                            "feedback_timestamp": False,
                                        }
                                    ],
                                    "timestamp": "2020-01-01 00:00.2 UTC",
                                },
                                {
                                    "assignment_id": "assign_1_3",
                                    "student_id": "1",
                                    "course_id": "no_course",
                                    "status": "fetched",
                                    "path": "",
                                    "notebooks": [
                                        {
                                            "name": "assignment-0.6-wrong",
                                            "has_exchange_feedback": False,
                                            "feedback_updated": False,
                                            "feedback_timestamp": False,
                                        }
                                    ],
                                    "timestamp": "2020-01-01 00:00.2 UTC",
                                },
                                {
                                    "assignment_id": "assign_1_3",
                                    "student_id": "1",
                                    "course_id": "no_course",
                                    "status": "fetched",
                                    "path": "",
                                    "notebooks": [
                                        {
                                            "name": "assignment-0.6-wrong",
                                            "has_exchange_feedback": False,
                                            "feedback_updated": False,
                                            "feedback_timestamp": False,
                                        }
                                    ],
                                    "timestamp": "2020-01-01 00:00.3 UTC",
                                },
                            ],
                        }
                    ),
                },
            )

        with patch.object(Exchange, "api_request", side_effect=api_request):
            called = plugin.start()
            assert called == [
                {
                    "assignment_id": "assign_1_1",
                    "course_id": "no_course",
                    "student_id": "1",
                    "status": "released",
                    "notebooks": [
                        {
                            "feedback_timestamp": False,
                            "feedback_updated": False,
                            "has_exchange_feedback": False,
                            "name": "assignment-0.6",
                        }
                    ],
                    "path": "",
                    "timestamp": "2020-01-01 00:00.0 UTC",
                },
                {
                    "assignment_id": "assign_1_3",
                    "course_id": "no_course",
                    "student_id": "1",
                    "status": "fetched",
                    "notebooks": [
                        {
                            "feedback_updated": False,
                            "has_exchange_feedback": False,
                            "has_local_feedback": False,
                            "local_feedback_path": None,
                            "notebook_id": "assignment-0.6",
                            "path": os.path.join(
                                os.getcwd(), "assign_1_3/assignment-0.6.ipynb"
                            ),
                        }
                    ],
                    "path": "",
                    "timestamp": "2020-01-01 00:00.3 UTC",
                },
            ]
    finally:
        shutil.rmtree("assign_1_3")


@pytest.mark.gen_test
def test_list_several_normal_different(plugin_config, tmpdir):
    try:
        plugin_config.CourseDirectory.course_id = "no_course"

        os.makedirs("assign_1_3", exist_ok=True)
        copyfile(
            notebook1_filename, os.path.join("assign_1_3", basename(notebook1_filename))
        )

        plugin = ExchangeList(
            coursedir=CourseDirectory(config=plugin_config), config=plugin_config
        )

        def api_request(*args, **kwargs):
            assert args[0] == ("assignments?course_id=no_course")
            assert "method" not in kwargs or kwargs.get("method").lower() == "get"
            return type(
                "Request",
                (object,),
                {
                    "status_code": 200,
                    "json": (
                        lambda: {
                            "success": True,
                            "value": [
                                {
                                    "assignment_id": "assign_1_1",
                                    "student_id": "1",
                                    "course_id": "no_course",
                                    "status": "released",
                                    "path": "",
                                    "notebooks": [
                                        {
                                            "name": "assignment-0.6",
                                            "has_exchange_feedback": False,
                                            "feedback_updated": False,
                                            "feedback_timestamp": False,
                                        }
                                    ],
                                    "timestamp": "2020-01-01 00:00.0 UTC",
                                },
                                {
                                    "assignment_id": "assign_1_2",
                                    "student_id": "1",
                                    "course_id": "no_course",
                                    "status": "released",
                                    "path": "",
                                    "notebooks": [
                                        {
                                            "name": "assignment-0.6-wrong",
                                            "has_exchange_feedback": False,
                                            "feedback_updated": False,
                                            "feedback_timestamp": False,
                                        }
                                    ],
                                    "timestamp": "2020-01-01 00:00.1 UTC",
                                },
                                {
                                    "assignment_id": "assign_1_3",
                                    "student_id": "1",
                                    "course_id": "no_course",
                                    "status": "fetched",
                                    "path": "",
                                    "notebooks": [
                                        {
                                            "name": "assignment-0.6-wrong",
                                            "has_exchange_feedback": False,
                                            "feedback_updated": False,
                                            "feedback_timestamp": False,
                                        }
                                    ],
                                    "timestamp": "2020-01-01 00:00.2 UTC",
                                },
                            ],
                        }
                    ),
                },
            )

        with patch.object(Exchange, "api_request", side_effect=api_request):
            called = plugin.start()
            assert called == [
                {
                    "assignment_id": "assign_1_1",
                    "course_id": "no_course",
                    "student_id": "1",
                    "status": "released",
                    "notebooks": [
                        {
                            "feedback_timestamp": False,
                            "feedback_updated": False,
                            "has_exchange_feedback": False,
                            "name": "assignment-0.6",
                        }
                    ],
                    "path": "",
                    "timestamp": "2020-01-01 00:00.0 UTC",
                },
                {
                    "assignment_id": "assign_1_2",
                    "course_id": "no_course",
                    "student_id": "1",
                    "status": "released",
                    "notebooks": [
                        {
                            "feedback_timestamp": False,
                            "feedback_updated": False,
                            "has_exchange_feedback": False,
                            "name": "assignment-0.6-wrong",
                        }
                    ],
                    "path": "",
                    "timestamp": "2020-01-01 00:00.1 UTC",
                },
                {
                    "assignment_id": "assign_1_3",
                    "course_id": "no_course",
                    "student_id": "1",
                    "status": "fetched",
                    "notebooks": [
                        {
                            "feedback_updated": False,
                            "has_exchange_feedback": False,
                            "has_local_feedback": False,
                            "local_feedback_path": None,
                            "notebook_id": "assignment-0.6",
                            "path": os.path.join(
                                os.getcwd(), "assign_1_3/assignment-0.6.ipynb"
                            ),
                        }
                    ],
                    "path": "",
                    "timestamp": "2020-01-01 00:00.2 UTC",
                },
            ]
    finally:
        shutil.rmtree("assign_1_3")


@pytest.mark.gen_test
def test_list_delete(plugin_config, tmpdir):
    plugin_config.CourseDirectory.course_id = "no_course"
    plugin_config.CourseDirectory.assignment_id = "assign_1_1"
    plugin_config.ExchangeList.remove = True

    plugin = ExchangeList(
        coursedir=CourseDirectory(config=plugin_config), config=plugin_config
    )

    def api_request(*args, **kwargs):
        assert args[0] == ("assignment?course_id=no_course&assignment_id=assign_1_1")
        assert "method" not in kwargs or kwargs.get("method").lower() == "delete"
        return type("Request", (object,), {"status_code": 200})

    with patch.object(Exchange, "api_request", side_effect=api_request):
        called = plugin.start()


@pytest.mark.gen_test
def test_list_inbound_one(plugin_config, tmpdir):
    plugin_config.CourseDirectory.course_id = "no_course"
    plugin_config.ExchangeList.inbound = True

    plugin = ExchangeList(
        coursedir=CourseDirectory(config=plugin_config), config=plugin_config
    )

    def api_request(*args, **kwargs):
        assert args[0] == ("assignments?course_id=no_course")
        assert "method" not in kwargs or kwargs.get("method").lower() == "get"
        return type(
            "Request",
            (object,),
            {
                "status_code": 200,
                "json": (
                    lambda: {
                        "success": True,
                        "value": [
                            {
                                "assignment_id": "assign_1_1",
                                "student_id": "1",
                                "course_id": "no_course",
                                "status": "submitted",
                                "path": "",
                                "notebooks": [
                                    {
                                        "name": "assignment-0.6",
                                        "has_exchange_feedback": False,
                                        "feedback_updated": False,
                                        "feedback_timestamp": False,
                                    }
                                ],
                                "timestamp": "2020-01-01 00:00.0 UTC",
                            }
                        ],
                    }
                ),
            },
        )

    with patch.object(Exchange, "api_request", side_effect=api_request):
        called = plugin.start()
        assert called == [
            {
                "assignment_id": "assign_1_1",
                "course_id": "no_course",
                "student_id": "1",
                "status": "submitted",
                "submissions": [
                    {
                        "assignment_id": "assign_1_1",
                        "course_id": "no_course",
                        "feedback_updated": False,
                        "has_exchange_feedback": False,
                        "has_local_feedback": False,
                        "path": "",
                        "status": "submitted",
                        "student_id": "1",
                        "local_feedback_path": "assign_1_1/feedback/False",
                        "notebooks": [
                            {
                                "feedback_timestamp": False,
                                "feedback_updated": False,
                                "has_exchange_feedback": False,
                                "has_local_feedback": False,
                                "local_feedback_path": "assign_1_1/feedback/False/assignment-0.6.html",
                                "name": "assignment-0.6",
                            }
                        ],
                        "timestamp": "2020-01-01 00:00.0 UTC",
                    }
                ],
            }
        ]


@pytest.mark.gen_test
def test_list_inbound_several_same(plugin_config, tmpdir):
    plugin_config.CourseDirectory.course_id = "no_course"
    plugin_config.ExchangeList.inbound = True

    plugin = ExchangeList(
        coursedir=CourseDirectory(config=plugin_config), config=plugin_config
    )

    def api_request(*args, **kwargs):
        assert args[0] == ("assignments?course_id=no_course")
        assert "method" not in kwargs or kwargs.get("method").lower() == "get"
        return type(
            "Request",
            (object,),
            {
                "status_code": 200,
                "json": (
                    lambda: {
                        "success": True,
                        "value": [
                            {
                                "assignment_id": "assign_1_1",
                                "student_id": "1",
                                "course_id": "no_course",
                                "status": "submitted",
                                "path": "",
                                "notebooks": [
                                    {
                                        "name": "assignment-0.6",
                                        "has_exchange_feedback": False,
                                        "feedback_updated": False,
                                        "feedback_timestamp": False,
                                    }
                                ],
                                "timestamp": "2020-01-01 00:00.0 UTC",
                            },
                            {
                                "assignment_id": "assign_1_1",
                                "student_id": "1",
                                "course_id": "no_course",
                                "status": "submitted",
                                "path": "",
                                "notebooks": [
                                    {
                                        "name": "assignment-0.6-wrong",
                                        "has_exchange_feedback": False,
                                        "feedback_updated": False,
                                        "feedback_timestamp": False,
                                    }
                                ],
                                "timestamp": "2020-01-01 00:00.1 UTC",
                            },
                        ],
                    }
                ),
            },
        )

    with patch.object(Exchange, "api_request", side_effect=api_request):
        called = plugin.start()
        assert called == [
            {
                "assignment_id": "assign_1_1",
                "course_id": "no_course",
                "student_id": "1",
                "status": "submitted",
                "submissions": [
                    {
                        "assignment_id": "assign_1_1",
                        "course_id": "no_course",
                        "feedback_updated": False,
                        "has_exchange_feedback": False,
                        "has_local_feedback": False,
                        "path": "",
                        "status": "submitted",
                        "student_id": "1",
                        "local_feedback_path": "assign_1_1/feedback/False",
                        "notebooks": [
                            {
                                "feedback_timestamp": False,
                                "feedback_updated": False,
                                "has_exchange_feedback": False,
                                "has_local_feedback": False,
                                "local_feedback_path": "assign_1_1/feedback/False/assignment-0.6.html",
                                "name": "assignment-0.6",
                            }
                        ],
                        "timestamp": "2020-01-01 00:00.0 UTC",
                    },
                    {
                        "assignment_id": "assign_1_1",
                        "course_id": "no_course",
                        "feedback_updated": False,
                        "has_exchange_feedback": False,
                        "has_local_feedback": False,
                        "path": "",
                        "status": "submitted",
                        "student_id": "1",
                        "local_feedback_path": "assign_1_1/feedback/False",
                        "notebooks": [
                            {
                                "feedback_timestamp": False,
                                "feedback_updated": False,
                                "has_exchange_feedback": False,
                                "has_local_feedback": False,
                                "local_feedback_path": "assign_1_1/feedback/False/assignment-0.6-wrong.html",
                                "name": "assignment-0.6-wrong",
                            }
                        ],
                        "timestamp": "2020-01-01 00:00.1 UTC",
                    },
                ],
            }
        ]


@pytest.mark.gen_test
def test_list_inbound_several_students(plugin_config, tmpdir):
    plugin_config.CourseDirectory.course_id = "no_course"
    plugin_config.ExchangeList.inbound = True

    plugin = ExchangeList(
        coursedir=CourseDirectory(config=plugin_config), config=plugin_config
    )

    def api_request(*args, **kwargs):
        assert args[0] == ("assignments?course_id=no_course")
        assert "method" not in kwargs or kwargs.get("method").lower() == "get"
        return type(
            "Request",
            (object,),
            {
                "status_code": 200,
                "json": (
                    lambda: {
                        "success": True,
                        "value": [
                            {
                                "assignment_id": "assign_1_1",
                                "student_id": "1",
                                "course_id": "no_course",
                                "status": "submitted",
                                "path": "",
                                "notebooks": [
                                    {
                                        "name": "assignment-0.6",
                                        "has_exchange_feedback": False,
                                        "feedback_updated": False,
                                        "feedback_timestamp": False,
                                    }
                                ],
                                "timestamp": "2020-01-01 00:00.0 UTC",
                            },
                            {
                                "assignment_id": "assign_1_1",
                                "student_id": "1",
                                "course_id": "no_course",
                                "status": "submitted",
                                "path": "",
                                "notebooks": [
                                    {
                                        "name": "assignment-0.6-wrong",
                                        "has_exchange_feedback": False,
                                        "feedback_updated": False,
                                        "feedback_timestamp": False,
                                    }
                                ],
                                "timestamp": "2020-01-01 00:00.1 UTC",
                            },
                            {
                                "assignment_id": "assign_1_1",
                                "student_id": "2",
                                "course_id": "no_course",
                                "status": "submitted",
                                "path": "",
                                "notebooks": [
                                    {
                                        "name": "assignment-0.6-wrong",
                                        "has_exchange_feedback": False,
                                        "feedback_updated": False,
                                        "feedback_timestamp": False,
                                    }
                                ],
                                "timestamp": "2020-01-01 00:00.3 UTC",
                            },
                        ],
                    }
                ),
            },
        )

    with patch.object(Exchange, "api_request", side_effect=api_request):
        called = plugin.start()
        assert called == [
            {
                "assignment_id": "assign_1_1",
                "course_id": "no_course",
                "student_id": "1",
                "status": "submitted",
                "submissions": [
                    {
                        "assignment_id": "assign_1_1",
                        "course_id": "no_course",
                        "feedback_updated": False,
                        "has_exchange_feedback": False,
                        "has_local_feedback": False,
                        "path": "",
                        "status": "submitted",
                        "student_id": "1",
                        "local_feedback_path": "assign_1_1/feedback/False",
                        "notebooks": [
                            {
                                "feedback_timestamp": False,
                                "feedback_updated": False,
                                "has_exchange_feedback": False,
                                "has_local_feedback": False,
                                "local_feedback_path": "assign_1_1/feedback/False/assignment-0.6.html",
                                "name": "assignment-0.6",
                            }
                        ],
                        "timestamp": "2020-01-01 00:00.0 UTC",
                    },
                    {
                        "assignment_id": "assign_1_1",
                        "course_id": "no_course",
                        "feedback_updated": False,
                        "has_exchange_feedback": False,
                        "has_local_feedback": False,
                        "path": "",
                        "status": "submitted",
                        "student_id": "1",
                        "local_feedback_path": "assign_1_1/feedback/False",
                        "notebooks": [
                            {
                                "feedback_timestamp": False,
                                "feedback_updated": False,
                                "has_exchange_feedback": False,
                                "has_local_feedback": False,
                                "local_feedback_path": "assign_1_1/feedback/False/assignment-0.6-wrong.html",
                                "name": "assignment-0.6-wrong",
                            }
                        ],
                        "timestamp": "2020-01-01 00:00.1 UTC",
                    },
                ],
            },
            {
                "assignment_id": "assign_1_1",
                "course_id": "no_course",
                "student_id": "2",
                "status": "submitted",
                "submissions": [
                    {
                        "assignment_id": "assign_1_1",
                        "course_id": "no_course",
                        "feedback_updated": False,
                        "has_exchange_feedback": False,
                        "has_local_feedback": False,
                        "path": "",
                        "status": "submitted",
                        "student_id": "2",
                        "local_feedback_path": "assign_1_1/feedback/False",
                        "notebooks": [
                            {
                                "feedback_timestamp": False,
                                "feedback_updated": False,
                                "has_exchange_feedback": False,
                                "has_local_feedback": False,
                                "local_feedback_path": "assign_1_1/feedback/False/assignment-0.6-wrong.html",
                                "name": "assignment-0.6-wrong",
                            }
                        ],
                        "timestamp": "2020-01-01 00:00.3 UTC",
                    }
                ],
            },
        ]


@pytest.mark.gen_test
def test_list_inbound_several_assignments(plugin_config, tmpdir):
    plugin_config.CourseDirectory.course_id = "no_course"
    plugin_config.ExchangeList.inbound = True

    plugin = ExchangeList(
        coursedir=CourseDirectory(config=plugin_config), config=plugin_config
    )

    def api_request(*args, **kwargs):
        assert args[0] == ("assignments?course_id=no_course")
        assert "method" not in kwargs or kwargs.get("method").lower() == "get"
        return type(
            "Request",
            (object,),
            {
                "status_code": 200,
                "json": (
                    lambda: {
                        "success": True,
                        "value": [
                            {
                                "assignment_id": "assign_1_1",
                                "student_id": "1",
                                "course_id": "no_course",
                                "status": "submitted",
                                "path": "",
                                "notebooks": [
                                    {
                                        "name": "assignment-0.6",
                                        "has_exchange_feedback": False,
                                        "feedback_updated": False,
                                        "feedback_timestamp": False,
                                    }
                                ],
                                "timestamp": "2020-01-01 00:00.0 UTC",
                            },
                            {
                                "assignment_id": "assign_1_1",
                                "student_id": "1",
                                "course_id": "no_course",
                                "status": "submitted",
                                "path": "",
                                "notebooks": [
                                    {
                                        "name": "assignment-0.6-wrong",
                                        "has_exchange_feedback": False,
                                        "feedback_updated": False,
                                        "feedback_timestamp": False,
                                    }
                                ],
                                "timestamp": "2020-01-01 00:00.1 UTC",
                            },
                            {
                                "assignment_id": "assign_1_1",
                                "student_id": "2",
                                "course_id": "no_course",
                                "status": "submitted",
                                "path": "",
                                "notebooks": [
                                    {
                                        "name": "assignment-0.6-wrong",
                                        "has_exchange_feedback": False,
                                        "feedback_updated": False,
                                        "feedback_timestamp": False,
                                    }
                                ],
                                "timestamp": "2020-01-01 00:00.3 UTC",
                            },
                            {
                                "assignment_id": "assign_1_2",
                                "student_id": "2",
                                "course_id": "no_course",
                                "status": "submitted",
                                "path": "",
                                "notebooks": [
                                    {
                                        "name": "assignment-0.6-wrong",
                                        "has_exchange_feedback": False,
                                        "feedback_updated": False,
                                        "feedback_timestamp": False,
                                    }
                                ],
                                "timestamp": "2020-01-01 00:00.4 UTC",
                            },
                        ],
                    }
                ),
            },
        )

    with patch.object(Exchange, "api_request", side_effect=api_request):
        called = plugin.start()
        assert called == [
            {
                "assignment_id": "assign_1_1",
                "course_id": "no_course",
                "student_id": "1",
                "status": "submitted",
                "submissions": [
                    {
                        "assignment_id": "assign_1_1",
                        "course_id": "no_course",
                        "feedback_updated": False,
                        "has_exchange_feedback": False,
                        "has_local_feedback": False,
                        "path": "",
                        "status": "submitted",
                        "student_id": "1",
                        "local_feedback_path": "assign_1_1/feedback/False",
                        "notebooks": [
                            {
                                "feedback_timestamp": False,
                                "feedback_updated": False,
                                "has_exchange_feedback": False,
                                "has_local_feedback": False,
                                "local_feedback_path": "assign_1_1/feedback/False/assignment-0.6.html",
                                "name": "assignment-0.6",
                            }
                        ],
                        "timestamp": "2020-01-01 00:00.0 UTC",
                    },
                    {
                        "assignment_id": "assign_1_1",
                        "course_id": "no_course",
                        "feedback_updated": False,
                        "has_exchange_feedback": False,
                        "has_local_feedback": False,
                        "path": "",
                        "status": "submitted",
                        "student_id": "1",
                        "local_feedback_path": "assign_1_1/feedback/False",
                        "notebooks": [
                            {
                                "feedback_timestamp": False,
                                "feedback_updated": False,
                                "has_exchange_feedback": False,
                                "has_local_feedback": False,
                                "local_feedback_path": "assign_1_1/feedback/False/assignment-0.6-wrong.html",
                                "name": "assignment-0.6-wrong",
                            }
                        ],
                        "timestamp": "2020-01-01 00:00.1 UTC",
                    },
                ],
            },
            {
                "assignment_id": "assign_1_1",
                "course_id": "no_course",
                "student_id": "2",
                "status": "submitted",
                "submissions": [
                    {
                        "assignment_id": "assign_1_1",
                        "course_id": "no_course",
                        "feedback_updated": False,
                        "has_exchange_feedback": False,
                        "has_local_feedback": False,
                        "path": "",
                        "status": "submitted",
                        "student_id": "2",
                        "local_feedback_path": "assign_1_1/feedback/False",
                        "notebooks": [
                            {
                                "feedback_timestamp": False,
                                "feedback_updated": False,
                                "has_exchange_feedback": False,
                                "has_local_feedback": False,
                                "local_feedback_path": "assign_1_1/feedback/False/assignment-0.6-wrong.html",
                                "name": "assignment-0.6-wrong",
                            }
                        ],
                        "timestamp": "2020-01-01 00:00.3 UTC",
                    }
                ],
            },
            {
                "assignment_id": "assign_1_2",
                "course_id": "no_course",
                "student_id": "2",
                "status": "submitted",
                "submissions": [
                    {
                        "assignment_id": "assign_1_2",
                        "course_id": "no_course",
                        "feedback_updated": False,
                        "has_exchange_feedback": False,
                        "has_local_feedback": False,
                        "path": "",
                        "status": "submitted",
                        "student_id": "2",
                        "local_feedback_path": "assign_1_2/feedback/False",
                        "notebooks": [
                            {
                                "feedback_timestamp": False,
                                "feedback_updated": False,
                                "has_exchange_feedback": False,
                                "has_local_feedback": False,
                                "local_feedback_path": "assign_1_2/feedback/False/assignment-0.6-wrong.html",
                                "name": "assignment-0.6-wrong",
                            }
                        ],
                        "timestamp": "2020-01-01 00:00.4 UTC",
                    }
                ],
            },
        ]


@pytest.mark.gen_test
def test_list_inbound_ignore_outbound(plugin_config, tmpdir):
    plugin_config.CourseDirectory.course_id = "no_course"
    plugin_config.ExchangeList.inbound = True

    plugin = ExchangeList(
        coursedir=CourseDirectory(config=plugin_config), config=plugin_config
    )

    def api_request(*args, **kwargs):
        assert args[0] == ("assignments?course_id=no_course")
        assert "method" not in kwargs or kwargs.get("method").lower() == "get"
        return type(
            "Request",
            (object,),
            {
                "status_code": 200,
                "json": (
                    lambda: {
                        "success": True,
                        "value": [
                            {
                                "assignment_id": "assign_1_1",
                                "student_id": "1",
                                "course_id": "no_course",
                                "status": "submitted",
                                "path": "",
                                "notebooks": [
                                    {
                                        "name": "assignment-0.6",
                                        "has_exchange_feedback": False,
                                        "feedback_updated": False,
                                        "feedback_timestamp": False,
                                    }
                                ],
                                "timestamp": "2020-01-01 00:00.0 UTC",
                            },
                            {
                                "assignment_id": "assign_1_1",
                                "student_id": "1",
                                "course_id": "no_course",
                                "status": "submitted",
                                "path": "",
                                "notebooks": [
                                    {
                                        "name": "assignment-0.6-wrong",
                                        "has_exchange_feedback": False,
                                        "feedback_updated": False,
                                        "feedback_timestamp": False,
                                    }
                                ],
                                "timestamp": "2020-01-01 00:00.1 UTC",
                            },
                            {
                                "assignment_id": "assign_1_4",
                                "student_id": "1",
                                "course_id": "no_course",
                                "status": "fetched",
                                "path": "",
                                "notebooks": [
                                    {
                                        "name": "assignment-0.6",
                                        "has_exchange_feedback": False,
                                        "feedback_updated": False,
                                        "feedback_timestamp": False,
                                    }
                                ],
                                "timestamp": "2020-01-01 00:00.44 UTC",
                            },
                            {
                                "assignment_id": "assign_13",
                                "student_id": "1",
                                "course_id": "no_course",
                                "status": "released",
                                "path": "",
                                "notebooks": [
                                    {
                                        "name": "assignment-0.6-wrong",
                                        "has_exchange_feedback": False,
                                        "feedback_updated": False,
                                        "feedback_timestamp": False,
                                    }
                                ],
                                "timestamp": "2020-01-01 00:00.23 UTC",
                            },
                            {
                                "assignment_id": "assign_1_1",
                                "student_id": "2",
                                "course_id": "no_course",
                                "status": "submitted",
                                "path": "",
                                "notebooks": [
                                    {
                                        "name": "assignment-0.6-wrong",
                                        "has_exchange_feedback": False,
                                        "feedback_updated": False,
                                        "feedback_timestamp": False,
                                    }
                                ],
                                "timestamp": "2020-01-01 00:00.3 UTC",
                            },
                            {
                                "assignment_id": "assign_1_2",
                                "student_id": "2",
                                "course_id": "no_course",
                                "status": "submitted",
                                "path": "",
                                "notebooks": [
                                    {
                                        "name": "assignment-0.6-wrong",
                                        "has_exchange_feedback": False,
                                        "feedback_updated": False,
                                        "feedback_timestamp": False,
                                    }
                                ],
                                "timestamp": "2020-01-01 00:00.4 UTC",
                            },
                        ],
                    }
                ),
            },
        )

    with patch.object(Exchange, "api_request", side_effect=api_request):
        called = plugin.start()
        assert called == [
            {
                "assignment_id": "assign_1_1",
                "course_id": "no_course",
                "student_id": "1",
                "status": "submitted",
                "submissions": [
                    {
                        "assignment_id": "assign_1_1",
                        "course_id": "no_course",
                        "feedback_updated": False,
                        "has_exchange_feedback": False,
                        "has_local_feedback": False,
                        "path": "",
                        "status": "submitted",
                        "student_id": "1",
                        "local_feedback_path": "assign_1_1/feedback/False",
                        "notebooks": [
                            {
                                "feedback_timestamp": False,
                                "feedback_updated": False,
                                "has_exchange_feedback": False,
                                "has_local_feedback": False,
                                "local_feedback_path": "assign_1_1/feedback/False/assignment-0.6.html",
                                "name": "assignment-0.6",
                            }
                        ],
                        "timestamp": "2020-01-01 00:00.0 UTC",
                    },
                    {
                        "assignment_id": "assign_1_1",
                        "course_id": "no_course",
                        "feedback_updated": False,
                        "has_exchange_feedback": False,
                        "has_local_feedback": False,
                        "path": "",
                        "status": "submitted",
                        "student_id": "1",
                        "local_feedback_path": "assign_1_1/feedback/False",
                        "notebooks": [
                            {
                                "feedback_timestamp": False,
                                "feedback_updated": False,
                                "has_exchange_feedback": False,
                                "has_local_feedback": False,
                                "local_feedback_path": "assign_1_1/feedback/False/assignment-0.6-wrong.html",
                                "name": "assignment-0.6-wrong",
                            }
                        ],
                        "timestamp": "2020-01-01 00:00.1 UTC",
                    },
                ],
            },
            {
                "assignment_id": "assign_1_1",
                "course_id": "no_course",
                "student_id": "2",
                "status": "submitted",
                "submissions": [
                    {
                        "assignment_id": "assign_1_1",
                        "course_id": "no_course",
                        "feedback_updated": False,
                        "has_exchange_feedback": False,
                        "has_local_feedback": False,
                        "path": "",
                        "status": "submitted",
                        "student_id": "2",
                        "local_feedback_path": "assign_1_1/feedback/False",
                        "notebooks": [
                            {
                                "feedback_timestamp": False,
                                "feedback_updated": False,
                                "has_exchange_feedback": False,
                                "has_local_feedback": False,
                                "local_feedback_path": "assign_1_1/feedback/False/assignment-0.6-wrong.html",
                                "name": "assignment-0.6-wrong",
                            }
                        ],
                        "timestamp": "2020-01-01 00:00.3 UTC",
                    }
                ],
            },
            {
                "assignment_id": "assign_1_2",
                "course_id": "no_course",
                "student_id": "2",
                "status": "submitted",
                "submissions": [
                    {
                        "assignment_id": "assign_1_2",
                        "course_id": "no_course",
                        "feedback_updated": False,
                        "has_exchange_feedback": False,
                        "has_local_feedback": False,
                        "path": "",
                        "status": "submitted",
                        "student_id": "2",
                        "local_feedback_path": "assign_1_2/feedback/False",
                        "notebooks": [
                            {
                                "feedback_timestamp": False,
                                "feedback_updated": False,
                                "has_exchange_feedback": False,
                                "has_local_feedback": False,
                                "local_feedback_path": "assign_1_2/feedback/False/assignment-0.6-wrong.html",
                                "name": "assignment-0.6-wrong",
                            }
                        ],
                        "timestamp": "2020-01-01 00:00.4 UTC",
                    }
                ],
            },
        ]


@pytest.mark.gen_test
def test_list_inbound_no_inbound(plugin_config, tmpdir):
    plugin_config.CourseDirectory.course_id = "no_course"
    plugin_config.ExchangeList.inbound = True

    plugin = ExchangeList(
        coursedir=CourseDirectory(config=plugin_config), config=plugin_config
    )

    def api_request(*args, **kwargs):
        assert args[0] == ("assignments?course_id=no_course")
        assert "method" not in kwargs or kwargs.get("method").lower() == "get"
        return type(
            "Request",
            (object,),
            {
                "status_code": 200,
                "json": (
                    lambda: {
                        "success": True,
                        "value": [
                            {
                                "assignment_id": "assign_1_4",
                                "student_id": "1",
                                "course_id": "no_course",
                                "status": "fetched",
                                "path": "",
                                "notebooks": [
                                    {
                                        "name": "assignment-0.6",
                                        "has_exchange_feedback": False,
                                        "feedback_updated": False,
                                        "feedback_timestamp": False,
                                    }
                                ],
                                "timestamp": "2020-01-01 00:00.44 UTC",
                            },
                            {
                                "assignment_id": "assign_13",
                                "student_id": "1",
                                "course_id": "no_course",
                                "status": "released",
                                "path": "",
                                "notebooks": [
                                    {
                                        "name": "assignment-0.6-wrong",
                                        "has_exchange_feedback": False,
                                        "feedback_updated": False,
                                        "feedback_timestamp": False,
                                    }
                                ],
                                "timestamp": "2020-01-01 00:00.23 UTC",
                            },
                        ],
                    }
                ),
            },
        )

    with patch.object(Exchange, "api_request", side_effect=api_request):
        called = plugin.start()
        assert called == []