import logging
from pathlib import Path

import pytest

from pages.global_scope import EditCcPanelBase
from pages.login import LoginPage
from revizor2.conf import CONF
from revizor2.helpers.cloud_credentials import CloudCredential

USER = CONF.credentials.testenv.accounts.admin['username']
PASSWORD = CONF.credentials.testenv.accounts.admin['password']

LOG = logging.getLogger(__name__)


class TestCloudCredentials:
    @pytest.fixture(autouse=True)
    def prepare_env(self, selenium_driver, testenv):
        self.driver = selenium_driver
        self.driver.implicitly_wait(10)
        login_page = LoginPage(
            self.driver,
            'http://%s.test-env.scalr.com' % testenv.te_id).open()
        self.admin_dashboard = login_page.login(USER, PASSWORD)

    @pytest.fixture(scope='class')
    def default_credentials(self, testenv):
        return CloudCredential.load(testenv)

    def validate_required_fields(self, cc_editor: EditCcPanelBase):
        cc_editor.save()
        for field in cc_editor.required_fields:
            assert 'x-form-invalid-field' in field.classes
            assert 'This field is required' in field.errors

    def test_aws_required_fields(self):
        ccs_page = self.admin_dashboard.go_to_cloud_credentials()
        edit_ccs_panel = ccs_page.add('AWS')

        self.validate_required_fields(edit_ccs_panel)

    def test_aws_add_valid(self, default_credentials):
        aws_creds: CloudCredential = [cc for cc in default_credentials.values()
                                      if cc.name == 'global-ec2 (PAID)'
                                      and cc.cloud == 'ec2'][0]

        ccs_page = self.admin_dashboard.go_to_cloud_credentials()
        edit_cc_panel = ccs_page.add('AWS')
        edit_cc_panel.fill(name='test_aws_add_valid',
                           access_key_id=aws_creds.properties['access_key'].value,
                           access_key_secret=aws_creds.properties['secret_key'].value,
                           account_type='Regular')
        edit_cc_panel.save()

        assert edit_cc_panel.id_field.visible()
        assert edit_cc_panel.id_field.text
        assert any([cc for cc in ccs_page.list()
                    if cc['Cloud'] == 'AWS'
                    and cc['Credentials'] == 'test_aws_add_valid'])

    def test_aws_add_invalid(self):
        ccs_page = self.admin_dashboard.go_to_cloud_credentials()
        edit_cc_panel = ccs_page.add('AWS')
        edit_cc_panel.fill(name='test_aws_add_invalid',
                           access_key_id='key_id',
                           access_key_secret='key_secret',
                           account_type='Regular')
        edit_cc_panel.save()

        assert not edit_cc_panel.id_field.visible()
        assert 'x-form-invalid-field' in edit_cc_panel.access_key_secret_field.classes
        assert any([e for e in edit_cc_panel.access_key_secret_field.errors
                    if 'Failed to verify your EC2 access key and secret key' in e])
        assert not any([cc for cc in ccs_page.list() if cc['Credentials'] == 'test_aws_add_invalid'])

    def test_aws_add_detailed(self, default_credentials):
        aws_creds: CloudCredential = [cc for cc in default_credentials.values()
                                      if cc.name == 'global-ec2 (PAID)'
                                      and cc.cloud == 'ec2'][0]

        ccs_page = self.admin_dashboard.go_to_cloud_credentials()
        edit_cc_panel = ccs_page.add('AWS')
        edit_cc_panel.fill(name='test_aws_add_detailed',
                           access_key_id=aws_creds.properties['access_key'].value,
                           access_key_secret=aws_creds.properties['secret_key'].value,
                           account_type='Regular')
        edit_cc_panel.fill_detailed_billing(aws_creds.properties['detailed_billing.bucket'].value)
        edit_cc_panel.save()

        assert edit_cc_panel.id_field.visible()
        assert edit_cc_panel.id_field.text
        assert edit_cc_panel.cm_tags_grid.visible()
        assert edit_cc_panel.cm_tags_grid.is_empty
        assert any([cc for cc in ccs_page.list()
                    if cc['Cloud'] == 'AWS'
                    and cc['Credentials'] == 'test_aws_add_detailed'])

    def test_aws_edit(self, default_credentials):
        aws_creds: CloudCredential = [cc for cc in default_credentials.values()
                                      if cc.name == 'global-ec2 (PAID)'
                                      and cc.cloud == 'ec2'][0]

        ccs_page = self.admin_dashboard.go_to_cloud_credentials()
        edit_cc_panel = ccs_page.add('AWS')
        edit_cc_panel.fill(name='test_aws_edit',
                           access_key_id=aws_creds.properties['access_key'].value,
                           access_key_secret=aws_creds.properties['secret_key'].value)
        edit_cc_panel.save()

        edit_cc_panel = ccs_page.select('test_aws_edit')
        edit_cc_panel.fill(name='test_aws_edited')
        edit_cc_panel.save()

        assert any([cc for cc in ccs_page.list()
                    if cc['Cloud'] == 'AWS'
                    and cc['Credentials'] == 'test_aws_edited'])

    def test_aws_delete(self, default_credentials):
        aws_creds: CloudCredential = [cc for cc in default_credentials.values()
                                      if cc.name == 'global-ec2 (PAID)'
                                      and cc.cloud == 'ec2'][0]

        ccs_page = self.admin_dashboard.go_to_cloud_credentials()
        add_ccs_panel = ccs_page.add('AWS')
        add_ccs_panel.fill(name='test_aws_delete',
                           access_key_id=aws_creds.properties['access_key'].value,
                           access_key_secret=aws_creds.properties['secret_key'].value)
        add_ccs_panel.save()

        add_ccs_panel = ccs_page.select('test_aws_delete')
        add_ccs_panel.delete()

        assert not any([cc for cc in ccs_page.list()
                        if cc['Credentials'] == 'test_aws_delete'])

    def test_cloudstack_required_fields(self):
        ccs_page = self.admin_dashboard.go_to_cloud_credentials()
        edit_cc_panel = ccs_page.add('Cloudstack')

        self.validate_required_fields(edit_cc_panel)

    def test_cloudstack_add_valid(self, default_credentials):
        cloudstack_creds: CloudCredential = [cc for cc in default_credentials.values()
                                             if cc.name == 'cloudstack-leaseweb (FREE)'
                                             and cc.cloud == 'cloudstack'][0]

        ccs_page = self.admin_dashboard.go_to_cloud_credentials()
        edit_cc_panel = ccs_page.add('Cloudstack')
        edit_cc_panel.fill(name='test_cloudstack_add_valid',
                           api_url=cloudstack_creds.properties['api_url'].value,
                           api_key=cloudstack_creds.properties['api_key'].value,
                           secret_key=cloudstack_creds.properties['secret_key'].value)
        edit_cc_panel.save()

        assert edit_cc_panel.id_field.visible()
        assert edit_cc_panel.id_field.text
        assert any([cc for cc in ccs_page.list()
                    if cc['Cloud'] == 'Cloudstack'
                    and cc['Credentials'] == 'test_cloudstack_add_valid'])

    def test_cloudstack_add_invalid(self, default_credentials):
        cloudstack_creds: CloudCredential = [cc for cc in default_credentials.values()
                                             if cc.name == 'cloudstack-leaseweb (FREE)'
                                             and cc.cloud == 'cloudstack'][0]

        ccs_page = self.admin_dashboard.go_to_cloud_credentials()
        edit_cc_panel = ccs_page.add('Cloudstack')
        edit_cc_panel.fill(name='test_cloudstack_add_invalid',
                           api_url=cloudstack_creds.properties['api_url'].value,
                           api_key='api_key',
                           secret_key='secret_key')
        edit_cc_panel.save()

        assert not edit_cc_panel.id_field.visible()
        assert 'CloudStack error. unable to verify user credentials' in ccs_page.page_message.text
        assert not any([cc for cc in ccs_page.list() if cc['Credentials'] == 'test_cloudstack_add_invalid'])

    def test_cloudstack_edit(self, default_credentials):
        cloudstack_creds: CloudCredential = [cc for cc in default_credentials.values()
                                             if cc.name == 'cloudstack-leaseweb (FREE)'
                                             and cc.cloud == 'cloudstack'][0]

        ccs_page = self.admin_dashboard.go_to_cloud_credentials()
        edit_cc_panel = ccs_page.add('Cloudstack')
        edit_cc_panel.fill(name='test_cloudstack_edit',
                           api_url=cloudstack_creds.properties['api_url'].value,
                           api_key=cloudstack_creds.properties['api_key'].value,
                           secret_key=cloudstack_creds.properties['secret_key'].value)
        edit_cc_panel.save()

        edit_cc_panel = ccs_page.select('test_cloudstack_edit')
        edit_cc_panel.fill(name='test_cloudstack_edited')
        edit_cc_panel.save()

        assert any([cc for cc in ccs_page.list()
                    if cc['Cloud'] == 'Cloudstack'
                    and cc['Credentials'] == 'test_cloudstack_edited'])

    def test_cloudstack_delete(self, default_credentials):
        cloudstack_creds: CloudCredential = [cc for cc in default_credentials.values()
                                             if cc.name == 'cloudstack-leaseweb (FREE)'
                                             and cc.cloud == 'cloudstack'][0]

        ccs_page = self.admin_dashboard.go_to_cloud_credentials()
        edit_cc_panel = ccs_page.add('Cloudstack')
        edit_cc_panel.fill(name='test_cloudstack_delete',
                           api_url=cloudstack_creds.properties['api_url'].value,
                           api_key=cloudstack_creds.properties['api_key'].value,
                           secret_key=cloudstack_creds.properties['secret_key'].value)
        edit_cc_panel.save()

        add_ccs_panel = ccs_page.select('test_cloudstack_delete')
        add_ccs_panel.delete()

        assert not any([cc for cc in ccs_page.list()
                        if cc['Credentials'] == 'test_cloudstack_delete'])

    def test_openstack_required_fields(self):
        ccs_page = self.admin_dashboard.go_to_cloud_credentials()
        edit_cc_panel = ccs_page.add('Openstack')

        self.validate_required_fields(edit_cc_panel)

    def test_openstack_add_v3_valid(self, default_credentials):
        openstack_creds: CloudCredential = [cc for cc in default_credentials.values()
                                            if cc.name == 'openstack-labs-v3 (FREE)'
                                            and cc.cloud == 'openstack'][0]

        ccs_page = self.admin_dashboard.go_to_cloud_credentials()
        edit_cc_panel = ccs_page.add('Openstack')
        edit_cc_panel.fill(name='test_openstack_add_v3_valid',
                           keystone_url=openstack_creds.properties['keystone_url'].value,
                           username=openstack_creds.properties['username'].value,
                           password=openstack_creds.properties['password'].value,
                           tenant_name=openstack_creds.properties['tenant_name'].value,
                           domain_name=openstack_creds.properties['domain_name'].value,
                           ssl_verification=False)
        edit_cc_panel.ssl_verification_checkbox.check()  # temporary
        edit_cc_panel.save()

        assert edit_cc_panel.id_field.visible()
        assert edit_cc_panel.id_field.text
        assert any([cc for cc in ccs_page.list()
                    if cc['Cloud'] == 'Openstack'
                    and cc['Credentials'] == 'test_openstack_add_v3_valid'])

    def test_openstack_add_v3_invalid(self, default_credentials):
        openstack_creds: CloudCredential = [cc for cc in default_credentials.values()
                                            if cc.name == 'openstack-labs-v3 (FREE)'
                                            and cc.cloud == 'openstack'][0]

        ccs_page = self.admin_dashboard.go_to_cloud_credentials()
        edit_cc_panel = ccs_page.add('Openstack')
        edit_cc_panel.fill(name='test_openstack_add_v3_invalid',
                           keystone_url=openstack_creds.properties['keystone_url'].value,
                           username='username',
                           password='password',
                           tenant_name='tenant_name',
                           domain_name='domain_name',
                           ssl_verification=False)
        edit_cc_panel.ssl_verification_checkbox.check()  # temporary
        edit_cc_panel.save()

        assert not edit_cc_panel.id_field.visible()
        assert 'OpenStack error. The request you have made requires authentication.' in ccs_page.page_message.text
        assert not any([cc for cc in ccs_page.list() if cc['Credentials'] == 'test_openstack_add_v3_invalid'])

    def test_openstack_edit(self, default_credentials):
        openstack_creds: CloudCredential = [cc for cc in default_credentials.values()
                                            if cc.name == 'openstack-labs-v3 (FREE)'
                                            and cc.cloud == 'openstack'][0]

        ccs_page = self.admin_dashboard.go_to_cloud_credentials()
        edit_cc_panel = ccs_page.add('Openstack')
        edit_cc_panel.fill(name='test_openstack_edit',
                           keystone_url=openstack_creds.properties['keystone_url'].value,
                           username=openstack_creds.properties['username'].value,
                           password=openstack_creds.properties['password'].value,
                           tenant_name=openstack_creds.properties['tenant_name'].value,
                           domain_name=openstack_creds.properties['domain_name'].value,
                           ssl_verification=False)
        edit_cc_panel.ssl_verification_checkbox.check()  # temporary
        edit_cc_panel.save()

        edit_cc_panel = ccs_page.select('test_openstack_edit')
        edit_cc_panel.fill(name='test_openstack_edited')
        edit_cc_panel.save()

        assert any([cc for cc in ccs_page.list()
                    if cc['Cloud'] == 'Openstack'
                    and cc['Credentials'] == 'test_openstack_edited'])

    def test_openstack_delete(self, default_credentials):
        openstack_creds: CloudCredential = [cc for cc in default_credentials.values()
                                            if cc.name == 'openstack-labs-v3 (FREE)'
                                            and cc.cloud == 'openstack'][0]

        ccs_page = self.admin_dashboard.go_to_cloud_credentials()
        edit_cc_panel = ccs_page.add('Openstack')
        edit_cc_panel.fill(name='test_openstack_delete',
                           keystone_url=openstack_creds.properties['keystone_url'].value,
                           username=openstack_creds.properties['username'].value,
                           password=openstack_creds.properties['password'].value,
                           tenant_name=openstack_creds.properties['tenant_name'].value,
                           domain_name=openstack_creds.properties['domain_name'].value,
                           ssl_verification=False)
        edit_cc_panel.ssl_verification_checkbox.check()  # temporary
        edit_cc_panel.save()

        add_ccs_panel = ccs_page.select('test_openstack_delete')
        add_ccs_panel.delete()

        assert not any([cc for cc in ccs_page.list()
                        if cc['Credentials'] == 'test_openstack_delete'])

    def test_vmware_required_fields(self):
        ccs_page = self.admin_dashboard.go_to_cloud_credentials()
        edit_cc_panel = ccs_page.add('VMware vSphere')
        self.validate_required_fields(edit_cc_panel)

    def test_vmware_add_valid(self, default_credentials):
        vmware_creds: CloudCredential = [cc for cc in default_credentials.values()
                                         if cc.name == 'vmware-labs-vcenter1 (FREE)'
                                         and cc.cloud == 'vmware'][0]

        ccs_page = self.admin_dashboard.go_to_cloud_credentials()
        edit_cc_panel = ccs_page.add('VMware vSphere')
        edit_cc_panel.fill(name='test_vmware_add_valid',
                           url=vmware_creds.properties['url'].value,
                           username=vmware_creds.properties['username'].value,
                           password=vmware_creds.properties['password'].value,
                           ssl_verification=False)
        edit_cc_panel.ssl_verification_checkbox.check()  # temporary
        edit_cc_panel.save()

        assert edit_cc_panel.id_field.visible()
        assert edit_cc_panel.id_field.text
        assert any([cc for cc in ccs_page.list()
                    if cc['Cloud'] == 'VMware vSphere'
                    and cc['Credentials'] == 'test_vmware_add_valid'])

    def test_vmware_add_invalid(self, default_credentials):
        vmware_creds: CloudCredential = [cc for cc in default_credentials.values()
                                         if cc.name == 'vmware-labs-vcenter1 (FREE)'
                                         and cc.cloud == 'vmware'][0]

        ccs_page = self.admin_dashboard.go_to_cloud_credentials()
        edit_cc_panel = ccs_page.add('VMware vSphere')
        edit_cc_panel.fill(name='test_vmware_add_invalid',
                           url=vmware_creds.properties['url'].value,
                           username='username',
                           password='password',
                           ssl_verification=False)
        edit_cc_panel.ssl_verification_checkbox.check()  # temporary
        edit_cc_panel.save()

        assert not edit_cc_panel.id_field.visible()
        assert 'Cannot complete login due to an incorrect user name or password.' in ccs_page.page_message.text
        assert not any([cc for cc in ccs_page.list() if cc['Credentials'] == 'test_vmware_add_invalid'])

    def test_vmware_add_detailed(self, default_credentials):
        vmware_creds: CloudCredential = [cc for cc in default_credentials.values()
                                         if cc.name == 'vmware-labs-vcenter1 (FREE)'
                                         and cc.cloud == 'vmware'][0]

        ccs_page = self.admin_dashboard.go_to_cloud_credentials()
        edit_cc_panel = ccs_page.add('VMware vSphere')
        edit_cc_panel.fill(name='test_vmware_add_detailed',
                           url=vmware_creds.properties['url'].value,
                           username=vmware_creds.properties['username'].value,
                           password=vmware_creds.properties['password'].value,
                           ssl_verification=False)
        edit_cc_panel.ssl_verification_checkbox.check()  # temporary
        edit_cc_panel.enable_detailed_billing()
        edit_cc_panel.save()

        assert edit_cc_panel.id_field.visible()
        assert edit_cc_panel.id_field.text
        assert edit_cc_panel.cm_tags_grid.visible()
        assert edit_cc_panel.cm_tags_grid.is_empty
        assert any([cc for cc in ccs_page.list()
                    if cc['Cloud'] == 'VMware vSphere'
                    and cc['Credentials'] == 'test_vmware_add_detailed'])

    def test_vmware_edit(self, default_credentials):
        vmware_creds: CloudCredential = [cc for cc in default_credentials.values()
                                         if cc.name == 'vmware-labs-vcenter1 (FREE)'
                                         and cc.cloud == 'vmware'][0]

        ccs_page = self.admin_dashboard.go_to_cloud_credentials()
        edit_cc_panel = ccs_page.add('VMware vSphere')
        edit_cc_panel.fill(name='test_vmware_edit',
                           url=vmware_creds.properties['url'].value,
                           username=vmware_creds.properties['username'].value,
                           password=vmware_creds.properties['password'].value,
                           ssl_verification=False)
        edit_cc_panel.ssl_verification_checkbox.check()  # temporary
        edit_cc_panel.save()

        edit_cc_panel = ccs_page.select('test_vmware_edit')
        edit_cc_panel.fill(name='test_vmware_edited')
        edit_cc_panel.save()

        assert any([cc for cc in ccs_page.list()
                    if cc['Cloud'] == 'VMware vSphere'
                    and cc['Credentials'] == 'test_vmware_edited'])

    def test_vmware_delete(self, default_credentials):
        vmware_creds: CloudCredential = [cc for cc in default_credentials.values()
                                         if cc.name == 'vmware-labs-vcenter1 (FREE)'
                                         and cc.cloud == 'vmware'][0]

        ccs_page = self.admin_dashboard.go_to_cloud_credentials()
        edit_cc_panel = ccs_page.add('VMware vSphere')
        edit_cc_panel.fill(name='test_vmware_delete',
                           url=vmware_creds.properties['url'].value,
                           username=vmware_creds.properties['username'].value,
                           password=vmware_creds.properties['password'].value,
                           ssl_verification=False)
        edit_cc_panel.ssl_verification_checkbox.check()  # temporary
        edit_cc_panel.save()

        add_ccs_panel = ccs_page.select('test_vmware_delete')
        add_ccs_panel.delete()

        assert not any([cc for cc in ccs_page.list()
                        if cc['Credentials'] == 'test_vmware_delete'])

    def test_gce_required_fields(self):
        ccs_page = self.admin_dashboard.go_to_cloud_credentials()
        edit_cc_panel = ccs_page.add('Google Compute Engine')
        self.validate_required_fields(edit_cc_panel)

    def test_gce_add_valid(self, default_credentials, tmpdir):
        gce_creds: CloudCredential = [cc for cc in default_credentials.values()
                                      if cc.name == 'global-gce-scalr-labs (PAID)'
                                      and cc.cloud == 'gce'][0]
        json_key_file = Path(tmpdir) / 'key.json'
        json_key_file.write_text(gce_creds.properties['json_key'].value)

        ccs_page = self.admin_dashboard.go_to_cloud_credentials()
        edit_cc_panel = ccs_page.add('Google Compute Engine')
        edit_cc_panel.fill(name='test_gce_add_valid',
                           config_type='Upload JSON key',
                           project_id=gce_creds.properties['project_id'].value,
                           json_key_path=str(json_key_file))
        edit_cc_panel.save()

        assert edit_cc_panel.id_field.visible()
        assert edit_cc_panel.id_field.text
        assert any([cc for cc in ccs_page.list()
                    if cc['Cloud'] == 'Google Compute Engine'
                    and cc['Credentials'] == 'test_gce_add_valid'])

    def test_gce_add_invalid(self, default_credentials, tmpdir):
        gce_creds: CloudCredential = [cc for cc in default_credentials.values()
                                      if cc.name == 'global-gce-scalr-labs (PAID)'
                                      and cc.cloud == 'gce'][0]
        json_key_file = Path(tmpdir) / 'key.json'
        json_key_file.write_text('json_key')

        ccs_page = self.admin_dashboard.go_to_cloud_credentials()
        edit_cc_panel = ccs_page.add('Google Compute Engine')
        edit_cc_panel.fill(name='test_gce_add_invalid',
                           config_type='Upload JSON key',
                           project_id=gce_creds.properties['project_id'].value,
                           json_key_path=str(json_key_file))
        edit_cc_panel.save()

        assert not edit_cc_panel.id_field.visible()
        assert 'x-form-invalid-field' in edit_cc_panel.project_id_field.classes
        assert any([e for e in edit_cc_panel.project_id_field.errors
                    if 'Provided GCE credentials are incorrect' in e])
        assert not any([cc for cc in ccs_page.list() if cc['Credentials'] == 'test_gce_add_invalid'])

    def test_gce_add_detailed(self, default_credentials, tmpdir):
        gce_creds: CloudCredential = [cc for cc in default_credentials.values()
                                      if cc.name == 'global-gce-scalr-labs (PAID)'
                                      and cc.cloud == 'gce'][0]
        json_key_file = Path(tmpdir) / 'key.json'
        json_key_file.write_text(gce_creds.properties['json_key'].value)

        ccs_page = self.admin_dashboard.go_to_cloud_credentials()
        edit_cc_panel = ccs_page.add('Google Compute Engine')
        edit_cc_panel.fill(name='test_gce_add_detailed',
                           config_type='Upload JSON key',
                           project_id=gce_creds.properties['project_id'].value,
                           json_key_path=str(json_key_file))
        edit_cc_panel.save()
        edit_cc_panel.fill_detailed_billing(dataset_name='billing')
        edit_cc_panel.save()

        assert edit_cc_panel.id_field.visible()
        assert edit_cc_panel.id_field.text
        assert edit_cc_panel.cm_tags_grid.visible()
        assert edit_cc_panel.cm_tags_grid.is_empty
        assert any([cc for cc in ccs_page.list()
                    if cc['Cloud'] == 'Google Compute Engine'
                    and cc['Credentials'] == 'test_gce_add_detailed'])

    def test_gce_edit(self, default_credentials, tmpdir):
        gce_creds: CloudCredential = [cc for cc in default_credentials.values()
                                      if cc.name == 'global-gce-scalr-labs (PAID)'
                                      and cc.cloud == 'gce'][0]
        json_key_file = Path(tmpdir) / 'key.json'
        json_key_file.write_text(gce_creds.properties['json_key'].value)

        ccs_page = self.admin_dashboard.go_to_cloud_credentials()
        edit_cc_panel = ccs_page.add('Google Compute Engine')
        edit_cc_panel.fill(name='test_gce_edit',
                           config_type='Upload JSON key',
                           project_id=gce_creds.properties['project_id'].value,
                           json_key_path=str(json_key_file))
        edit_cc_panel.save()

        edit_cc_panel = ccs_page.select('test_gce_edit')
        edit_cc_panel.fill(name='test_gce_edited')
        edit_cc_panel.save()

        assert any([cc for cc in ccs_page.list()
                    if cc['Cloud'] == 'Google Compute Engine'
                    and cc['Credentials'] == 'test_gce_edited'])

    def test_gce_delete(self, default_credentials, tmpdir):
        gce_creds: CloudCredential = [cc for cc in default_credentials.values()
                                      if cc.name == 'global-gce-scalr-labs (PAID)'
                                      and cc.cloud == 'gce'][0]
        json_key_file = Path(tmpdir) / 'key.json'
        json_key_file.write_text(gce_creds.properties['json_key'].value)

        ccs_page = self.admin_dashboard.go_to_cloud_credentials()
        edit_cc_panel = ccs_page.add('Google Compute Engine')
        edit_cc_panel.fill(name='test_gce_delete',
                           config_type='Upload JSON key',
                           project_id=gce_creds.properties['project_id'].value,
                           json_key_path=str(json_key_file))
        edit_cc_panel.save()

        add_ccs_panel = ccs_page.select('test_gce_delete')
        add_ccs_panel.delete()

        assert not any([cc for cc in ccs_page.list()
                        if cc['Credentials'] == 'test_gce_delete'])

    def test_azure_required_fields(self):
        ccs_page = self.admin_dashboard.go_to_cloud_credentials()
        edit_cc_panel = ccs_page.add('Azure')
        edit_cc_panel.app_client_id_field.write('')
        edit_cc_panel.app_secret_key_field.write('')
        edit_cc_panel.next()

        for field in edit_cc_panel.required_fields:
            assert 'x-form-invalid-field' in field.classes
            assert 'This field is required' in field.errors

    def test_azure_add_valid(self, default_credentials):
        azure_creds: CloudCredential = [cc for cc in default_credentials.values()
                                        if cc.name == 'azure (Paid)'
                                        and cc.cloud == 'azure'][0]

        ccs_page = self.admin_dashboard.go_to_cloud_credentials()
        edit_cc_panel = ccs_page.add('Azure')
        edit_cc_panel.fill(name='test_azure_add_valid',
                           account_type='Public',
                           app_client_id=azure_creds.properties['app_client_id'].value,
                           app_secret_key=azure_creds.properties['app_secret_key'].value,
                           tenant_id=azure_creds.properties['tenant_id'].value)
        edit_cc_panel.next()
        edit_cc_panel.select_subscription(azure_creds.properties['subscription_id'].value)
        edit_cc_panel.save()

        assert edit_cc_panel.id_field.visible()
        assert edit_cc_panel.id_field.text
        assert any([cc for cc in ccs_page.list()
                    if cc['Cloud'] == 'Azure'
                    and cc['Credentials'] == 'test_azure_add_valid'])

    def test_azure_add_invalid(self, default_credentials):
        azure_creds: CloudCredential = [cc for cc in default_credentials.values()
                                        if cc.name == 'azure (Paid)'
                                        and cc.cloud == 'azure'][0]

        ccs_page = self.admin_dashboard.go_to_cloud_credentials()
        edit_cc_panel = ccs_page.add('Azure')
        edit_cc_panel.fill(name='test_azure_add_invalid',
                           account_type='Public',
                           app_client_id=azure_creds.properties['app_client_id'].value,
                           app_secret_key='app_secret_key',
                           tenant_id=azure_creds.properties['tenant_id'].value)
        edit_cc_panel.next()

        assert not edit_cc_panel.id_field.visible()
        assert 'Azure error.' in ccs_page.page_message.text
        assert not any([cc for cc in ccs_page.list() if cc['Credentials'] == 'test_azure_add_invalid'])

    def test_azure_add_detailed(self, default_credentials):
        azure_creds: CloudCredential = [cc for cc in default_credentials.values()
                                        if cc.name == 'azure (Paid)'
                                        and cc.cloud == 'azure'][0]

        ccs_page = self.admin_dashboard.go_to_cloud_credentials()
        edit_cc_panel = ccs_page.add('Azure')
        edit_cc_panel.fill(name='test_azure_add_detailed',
                           account_type='Public',
                           app_client_id=azure_creds.properties['app_client_id'].value,
                           app_secret_key=azure_creds.properties['app_secret_key'].value,
                           tenant_id=azure_creds.properties['tenant_id'].value)
        edit_cc_panel.next()
        edit_cc_panel.select_subscription(azure_creds.properties['subscription_id'].value)
        edit_cc_panel.enable_detailed_billing()
        edit_cc_panel.save()

        assert edit_cc_panel.id_field.visible()
        assert edit_cc_panel.id_field.text
        assert edit_cc_panel.cm_tags_grid.visible()
        assert edit_cc_panel.cm_tags_grid.is_empty
        assert any([cc for cc in ccs_page.list()
                    if cc['Cloud'] == 'Azure'
                    and cc['Credentials'] == 'test_azure_add_detailed'])

    def test_azure_edit(self, default_credentials, tmpdir):
        azure_creds: CloudCredential = [cc for cc in default_credentials.values()
                                        if cc.name == 'azure (Paid)'
                                        and cc.cloud == 'azure'][0]

        ccs_page = self.admin_dashboard.go_to_cloud_credentials()
        edit_cc_panel = ccs_page.add('Azure')
        edit_cc_panel.fill(name='test_azure_edit',
                           account_type='Public',
                           app_client_id=azure_creds.properties['app_client_id'].value,
                           app_secret_key=azure_creds.properties['app_secret_key'].value,
                           tenant_id=azure_creds.properties['tenant_id'].value)
        edit_cc_panel.next()
        edit_cc_panel.select_subscription(azure_creds.properties['subscription_id'].value)
        edit_cc_panel.save()

        edit_cc_panel = ccs_page.select('test_azure_edit')
        edit_cc_panel.fill(name='test_azure_edited')
        edit_cc_panel.save()

        assert any([cc for cc in ccs_page.list()
                    if cc['Cloud'] == 'Azure'
                    and cc['Credentials'] == 'test_azure_edited'])

    def test_azure_delete(self, default_credentials, tmpdir):
        azure_creds: CloudCredential = [cc for cc in default_credentials.values()
                                        if cc.name == 'azure (Paid)'
                                        and cc.cloud == 'azure'][0]

        ccs_page = self.admin_dashboard.go_to_cloud_credentials()
        edit_cc_panel = ccs_page.add('Azure')
        edit_cc_panel.fill(name='test_azure_delete',
                           account_type='Public',
                           app_client_id=azure_creds.properties['app_client_id'].value,
                           app_secret_key=azure_creds.properties['app_secret_key'].value,
                           tenant_id=azure_creds.properties['tenant_id'].value)
        edit_cc_panel.next()
        edit_cc_panel.select_subscription(azure_creds.properties['subscription_id'].value)
        edit_cc_panel.save()

        add_ccs_panel = ccs_page.select('test_azure_delete')
        add_ccs_panel.delete()

        assert not any([cc for cc in ccs_page.list()
                        if cc['Credentials'] == 'test_azure_delete'])

    def test_bulk_delete(self, default_credentials):
        cc_names = ['test_bulk_delete_1', 'test_bulk_delete_2', 'test_bulk_delete_3']
        aws_creds: CloudCredential = [cc for cc in default_credentials.values()
                                      if cc.name == 'global-ec2 (PAID)'
                                      and cc.cloud == 'ec2'][0]

        ccs_page = self.admin_dashboard.go_to_cloud_credentials()
        for name in cc_names:
            add_ccs_panel = ccs_page.add('AWS')
            add_ccs_panel.fill(name=name,
                               access_key_id=aws_creds.properties['access_key'].value,
                               access_key_secret=aws_creds.properties['secret_key'].value)
            add_ccs_panel.save()

        actual_names = [cc['Credentials'] for cc in ccs_page.list()]

        assert all([name in actual_names for name in cc_names])

        ccs_page.check(cc_names)
        ccs_page.delete()

        assert not any([cc for cc in ccs_page.list()
                        if cc['Credentials'] in cc_names])

    def test_delete_all(self, default_credentials):
        cc_names = ['test_delete_all_1', 'test_delete_all_2']
        aws_creds: CloudCredential = [cc for cc in default_credentials.values()
                                      if cc.name == 'global-ec2 (PAID)'
                                      and cc.cloud == 'ec2'][0]

        ccs_page = self.admin_dashboard.go_to_cloud_credentials()
        for name in cc_names:
            add_ccs_panel = ccs_page.add('AWS')
            add_ccs_panel.fill(name=name,
                               access_key_id=aws_creds.properties['access_key'].value,
                               access_key_secret=aws_creds.properties['secret_key'].value)
            add_ccs_panel.save()

        unused_names = [cc['Credentials'] for cc in ccs_page.list() if cc['Usage'] == 'Not used']
        ccs_page.check_all()
        ccs_page.delete()

        assert not any([cc for cc in ccs_page.list()
                        if cc['Credentials'] in unused_names])
