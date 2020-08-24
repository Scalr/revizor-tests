import time

import pytest
from selene.api import s, be, have

from ui.utils.components import tooltip
from ui.utils.datagenerator import generate_name
from ui.pages.terraform.vcs import EditVCSForm, DeleteConfirmationModal
from ui.utils.mixins.vcs import VCSMixin


class TestVCSProviders(VCSMixin):
    @pytest.fixture(autouse=True)
    def prepare_env(self, tf_dashboard, loggined_vcs):
        self.dashboard = tf_dashboard
        self.vcs_provider = loggined_vcs
        self._created_oauth = []
        yield
        for name in self._created_oauth:
            self.vcs_provider.delete_oauth(name)

    def test_add_provider(self):
        vcs_name = generate_name('test')
        vcs_page = self.add_provider(vcs_name)
        edit_form = EditVCSForm()
        assert edit_form.name.get_attribute('value') == vcs_name
        edit_form.reauthorize_button.should(be.visible)
        assert len(vcs_page.providers) == 1
        assert vcs_page.providers[0].name == vcs_name
        assert vcs_page.providers[0].usage == 'Not used'

    def test_delete_provider(self):
        vcs_name = generate_name('test')
        vcs_page = self.add_provider(vcs_name)
        vcs_page.providers[0].toggle()
        vcs_page.delete_button.click()
        confirm = DeleteConfirmationModal()
        confirm.visible()
        confirm.delete_button.click()
        tip = tooltip('VCS provider successfully deleted.')
        tip.element.should(be.visible)
        tip.close()
        for provider in vcs_page.providers:
            assert provider.name != vcs_name, f'Provider {provider.name} is exist!'

    def test_add_exist_name(self):
        vcs_name = generate_name('test')
        vcs_page = self.add_provider(vcs_name)
        vcs_page.new_vcs_button.click()
        new_form = vcs_page.new_vcs_form
        new_form.vcs_type.set_value(self.vcs_provider.name)
        new_form.name.set(vcs_name)
        new_form.client_id.set('dsfsdfs')
        new_form.client_secret.set('sdsadasd')
        new_form.create_button.click()
        new_form.name.should(have.css_class('x-form-invalid-field'))
        new_form.name.parent_element.following_sibling.hover()
        s('div#ext-form-error-tip-body').should(be.visible)\
            .should(have.text('VCS Provider name must be unique within current scope.'))

    def test_reauthorize(self):
        vcs_name = generate_name('test')
        self.add_provider(vcs_name)
        edit_form = EditVCSForm()
        edit_form.reauthorize_button.click()
        tip = tooltip('Successfully Authorized.')
        tip.element.should(be.visible, timeout=20)

    def test_add_client_id_twice(self):
        vcs_name = generate_name('test')
        vcs_page = self.add_provider(vcs_name)
        vcs_page.new_vcs_button.click()
        new_form = vcs_page.new_vcs_form
        new_form.vcs_type.set_value(self.vcs_provider.name)
        new_form.name.set(generate_name('test'))
        settings = self.vcs_provider.get_app_settings(vcs_name)
        new_form.client_id.set(settings['key'])
        new_form.client_secret.set('sdsadasd')
        new_form.create_button.click()
        new_form.client_id.should(have.css_class('x-form-invalid-field'))
        new_form.client_id.parent_element.following_sibling.hover()
        s('div#ext-form-error-tip-body').should(be.visible) \
            .should(have.text('VCS Provider with same Client ID already exist.'))

    def test_add_invalid_secret(self):
        err_msgs = dict(
            GitLab="Client authentication failed",
            GitHub="incorrect_client_credentials"
        )
        vcs_name = generate_name('test')
        vcs_page = self.add_provider(vcs_name, 'invalidsecret', wait_message=False)
        provider = vcs_page.providers[0]
        provider.element.s('img.x-icon-colored-status-failed').should(be.visible)
        edit_page = EditVCSForm()
        edit_page.error.should(be.visible).should(have.text(err_msgs[self.vcs_provider.name]))

    def test_search(self):
        vcs_name = generate_name('test')
        vcs_name2 = generate_name('test')
        self.add_provider(vcs_name)
        vcs_page = self.add_provider(vcs_name2)
        vcs_page.clean_search_field()
        vcs_page.search.set(vcs_name)
        time.sleep(1)
        assert len(vcs_page.providers) == 1
        assert vcs_page.providers[0].name == vcs_name
        vcs_page.clean_search_field()
        vcs_page.search.set(vcs_name2)
        # s(by.xpath('//div[text()="Loading..."]')).should_be(visible).should_not_be(visible)
        time.sleep(1)
        assert len(vcs_page.providers) == 1
        assert vcs_page.providers[0].name == vcs_name2
