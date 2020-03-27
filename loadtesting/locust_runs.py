import time
from revizor2.api import IMPL
from revizor2.utils import generate_name
from revizor2.helpers.vcs import create_vcs
from revizor2.conf import CONF
from locust import Locust, TaskSequence, task, between, seq_task, events

from ui.utils import vcs


VCS_SETTINGS = {
    'id': None,
    'name': None,
    'org_id': None,
    'provider': None
}


class RunsTaskSet(TaskSequence):
    wait_time = between(1, 10)

    def on_start(self):
        """
        Create API key and create workspace
        """
        self.workspace_name = generate_name()
        self.workspace_id = None

    def _wait_cv_uploaded(self):
        start_time = time.time()
        status = None
        while status != 'uploaded':
            time.sleep(10)
            status = IMPL.workspace.get(self.workspace_id)['cv_status']
        total_time = int((time.time() - start_time) * 1000)
        events.request_success.fire(request_type='wait', name='conf-version', response_time=total_time,
                                    response_length=0)

    def _plan_run(self):
        try:
            IMPL.workspace.update_variable(self.workspace_id, 'run_id', generate_name())
        except Exception as e:
            time.sleep(1)
            self._plan_run()
        start_time = time.time()
        try:
            IMPL.run.create(self.workspace_id)
        except Exception as e:
            total_time = int((time.time() - start_time) * 1000)
            events.request_failure.fire(request_type='wait', name='plan-run', response_time=total_time, exception=e,
                                        response_length=0)
            time.sleep(1)
            self._plan_run()
        status = None
        while status != 'cost_estimated':
            time.sleep(10)
            status = IMPL.workspace.get(self.workspace_id)['status']
        total_time = int((time.time() - start_time) * 1000)
        events.request_success.fire(request_type='wait', name='plan-run', response_time=total_time, response_length=0)

    def _approve_run(self):
        start_time = time.time()
        try:
            IMPL.run.apply(
                IMPL.workspace.get(self.workspace_id)['run_id']
            )
        except Exception as e:
            total_time = int((time.time() - start_time) * 1000)
            events.request_failure.fire(request_type='approve', name='run', response_time=total_time, exception=e,
                                        response_length=0)
            time.sleep(1)
            self._approve_run()
        total_time = int((time.time() - start_time) * 1000)
        events.request_success.fire(request_type='approve', name='run', response_time=total_time, response_length=0)

    def _wait_run(self):
        start_time = time.time()
        status = None
        while status not in ('applied', 'errored'):
            time.sleep(10)
            status = IMPL.workspace.get(self.workspace_id)['status']
        total_time = int((time.time() - start_time) * 1000)
        events.request_success.fire(request_type='wait', name='applied-run', response_time=total_time, response_length=0)

    @seq_task(1)
    def create_workspace(self):
        start_time = time.time()
        try:
            self.workspace_id = IMPL.workspace.create(
                name=self.workspace_name,
                terraform_version='0.12.19',
                auto_apply=False,
                provider=VCS_SETTINGS['id'],
                repository='Scalr/tf-revizor-fixtures',
                branch='master',
                path='local_wait'
            )
        except Exception as e:
            total_time = int((time.time() - start_time) * 1000)
            events.request_failure.fire(request_type='create', name='workspace', response_time=total_time, exception=e,
                                        response_length=0)
            time.sleep(2)
            self.create_workspace()
        IMPL.workspace.add_variable(self.workspace_id, 'run_id', generate_name())
        total_time = int((time.time() - start_time) * 1000)
        events.request_success.fire(request_type='create', name='workspace', response_time=total_time, response_length=0)
        self._wait_cv_uploaded()

    @seq_task(2)
    @task(10)
    def create_run(self):
        """
        Start run and wait it finished
        """

        self._plan_run()
        self._approve_run()
        self._wait_run()


class APIUserRuns(Locust):
    task_set = RunsTaskSet

    def setup(self):
        """Create a VCS and save org-id"""
        provider = vcs.VCSGithub()
        provider.login(CONF.credentials.github.username, CONF.credentials.github.password)
        VCS_SETTINGS['name'] = create_vcs(provider)['name']
        VCS_SETTINGS['id'] = list(filter(lambda x: x['name'] == VCS_SETTINGS['name'], IMPL.vcs.list()))[0]['id']
        VCS_SETTINGS['provider'] = provider
        VCS_SETTINGS['org_id'] = IMPL.get_session('terraform').get('/guest/xInit')['initParams']['context']['user']['organizationId']

    def teardown(self):
        VCS_SETTINGS['provider'].delete_oauth(VCS_SETTINGS['name'])
