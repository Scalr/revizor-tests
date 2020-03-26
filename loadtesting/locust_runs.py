import time
from revizor2.api import IMPL
from revizor2.utils import generate_name
from revizor2.helpers.vcs import create_vcs
from revizor2.conf import CONF
from locust import Locust, TaskSequence, task, between, seq_task, events

from ui.utils import vcs


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
        start_time = time.time()
        IMPL.workspace.update_variable(self.workspace_id, 'run_id', generate_name())
        IMPL.run.create(self.workspace_id)
        status = None
        while status != 'cost_estimated':
            time.sleep(10)
            status = IMPL.workspace.get(self.workspace_id)['status']
        total_time = int((time.time() - start_time) * 1000)
        events.request_success.fire(request_type='wait', name='plan-run', response_time=total_time, response_length=0)

    def _approve_run(self):
        start_time = time.time()
        IMPL.run.apply(
            IMPL.workspace.get(self.workspace_id)['run_id']
        )
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
        self.workspace_id = IMPL.workspace.create(
            name=self.workspace_name,
            terraform_version='0.12.19',
            auto_apply=False,
            provider=self.parent.vcs_id,
            repository='Scalr/tf-revizor-fixtures',
            branch='master',
            path='local_wait'
        )
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
        self.vcs_name = create_vcs(provider)['name']
        self.vcs_id = list(filter(lambda x: x['name'] == self.vcs_name, IMPL.vcs.list()))[0]['id']
        self.provider = provider
        self.org_id = IMPL.get_session('terraform').get('/guest/xInit')['initParams']['context']['user']['organizationId']

    def teardown(self):
        self.provider.delete_oauth(self.vcs_name)
