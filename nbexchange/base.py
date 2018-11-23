from nbexchange import orm

from tornado import gen, web

from jupyterhub.handlers import BaseHandler as JupyterHubBaseHandler
from jupyterhub.services.auth import HubAuthenticated
from jupyterhub.utils import url_path_join


class BaseHandler(HubAuthenticated, JupyterHubBaseHandler):
    """An nbexchange base handler"""

    # register URL patterns
    urls = []

    # Root location for data to be written to
    base_storage_location = "/tmp"

    @property
    def nbex_user(self):

        hub_user = self.get_current_user()
        hub_name = hub_user.get("name")

        ### Bodge.
        items = self._bodge_course_details()
        current_course = items[0]
        current_role = items[1] if items[1] else None
        course_title = items[2] if items[2] else None

        if not (current_course and current_role):
            return

        # TODO: this puts a hard restriction on the usernames having an underscore in them, which we do not want
        # THe solution is to get the organisation id from the user state stored in jupyterhub instead of deriving it
        # from the username
        org_id, name = hub_user.get("name").split("_", 1)  # we only want the first part
        org_id = 1 if org_id is None else org_id
        self.org_id = org_id

        user = orm.User.find_by_name(db=self.db, name=hub_name, log=self.log)
        if user is None:
            self.log.info(
                "New user details: name:{}, org_id:{}".format(hub_name, org_id)
            )
            user = orm.User(name=hub_name, org_id=org_id)
            self.db.add(user)

        course = orm.Course.find_by_code(
            db=self.db, code=current_course, org_id=org_id, log=self.log
        )
        if course is None:
            self.log.info(
                "New course details: code:{}, org_id:{}".format(current_course, org_id)
            )
            course = orm.Course(org_id=org_id, course_code=current_course)
            if course_title:
                self.log.info("Adding title {}".format(course_title))
                course.course_title = course_title
            self.db.add(course)

        # Check to see if we have a subscription (for this course)
        self.log.info(
            "Looking for subscription for: user:{}, course:{}, role:{} ".format(
                user.id, course.id, current_role
            )
        )

        subscription = orm.Subscription.find_by_set(
            db=self.db, user_id=user.id, course_id=course.id, role=current_role
        )
        if subscription is None:
            self.log.info(
                "New subscription details: user:{}, course:{}, role:{} ".format(
                    user.id, course.id, current_role
                )
            )
            subscription = orm.Subscription(
                user_id=user.id, course_id=course.id, role=current_role
            )
            self.db.add(subscription)

        self.db.commit()

        courses = {}
        actions = {}
        for subscription in user.courses:
            if not subscription.course.course_code in courses:
                courses[subscription.course.course_code] = {}
            courses[subscription.course.course_code][subscription.role] = 1

        model = {
            "kind": "user",
            "ormUser": user,
            "name": user.name,
            "org_id": user.org_id,
            "current_course": current_course,
            "current_role": current_role,
            "courses": courses
        }
        return model

    def _bodge_course_details(self):
        # A bodge: a list of course/role dictionaries
        courses = [
            {
                "course_code": "course_1",
                "role": "student",
                "course_title": "Their funky course",
            },
            {
                "course_code": "course_2",
                "role": "instructor",
                "course_title": "My weird course",
            },
            {"course_code": "course_2", "role": "student", "course_title": None},
            {"course_code": "course_3", "role": "student", "course_title": None},
        ]
        import random

        course = random.choice(courses)
        return course["course_code"], course["role"], course["course_title"]

    @property
    def hub_auth(self):
        return self.settings.get("hub_auth")

    @property
    def csp_report_uri(self):
        return self.settings.get(
            "csp_report_uri",
            url_path_join(
                self.settings.get("hub_base_url", "/hub"), "security/csp-report"
            ),
        )

    @property
    def template_namespace(self):
        user = self.get_current_user()
        return dict(
            prefix=self.base_url,
            user=user,
            login_url=self.settings["login_url"],
            logout_url=self.settings["logout_url"],
            static_url=self.static_url,
            version_hash=self.version_hash,
        )

    def finish(self, *args, **kwargs):
        return super(JupyterHubBaseHandler, self).finish(*args, **kwargs)


class Template404(BaseHandler):
    """Render nbexchange's 404 template"""

    urls = [".*"]

    def prepare(self):
        raise web.HTTPError(404)
