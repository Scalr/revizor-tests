# coding: utf-8
"""
Created on 07.08.18
@author: Eugeny Kurkovich
"""

import re

import inspect
import pytest
import requests

from api.utils.helpers import uniq_uuid, remove_empty_values
from api.utils.consts import Platform, COST_PROJECT_ID, ENV_ID


class Setup(object):

    api = None
    env_id = ENV_ID
    cost_project_id = COST_PROJECT_ID
    role_id = 57039

    def init_api(self, api):
        if not self.__class__.api:
            self.__class__.api = api
        return self.__class__.api

    def create_farm(self, farm_tpl=None, **kwargs):
        body = farm_tpl or dict(
            name=self.uniq_farm_name,
            project={"id": self.cost_project_id},
            **kwargs
        )
        resp = self.api.create(
            "/api/v1beta0/user/envId/farms/",
            params=dict(envId=self.env_id),
            body=body)
        return resp.json_data.data

    def add_role_to_farm(self, farm_id, role_id,
                         alias, platform,
                         location=None, instance_type=None,
                         network=None, zone=None,
                         folder=None, compute_resource=None,
                         resource_pool=None, data_store=None,
                         host=None, subnet=None,
                         resource_group=None, storage_account=None, **kwargs):

        cloud_features = None
        networks = []
        if not isinstance(network, list):
            network = [network]
        for n in network:
            networks.append({'id': n})
        # azure farm role settings
        if platform.is_azure:
            network = {
                'networks': networks,
                'subnets': [{'id': subnet}]}
            cloud_features = {
                "resourceGroup": resource_group,
                "storageAccount": storage_account}
            zone = [zone]
        else:
            network = {'networks': networks}
        # vmware farm role settings
        if platform.is_vmware:
            cloud_features = {
                'folder': folder,
                'computeResource': compute_resource,
                'hosts': [host],
                'resourcePool': resource_pool,
                'dataStore': data_store}
        # gce farm role settings
        if platform.is_gce:
            zone = [zone]

        body = dict(
            alias='{}-{}'.format(alias, platform),
            cloudLocation=location,
            cloudPlatform=platform,
            instanceType={'id': instance_type},
            availabilityZones=zone,
            role={'id': role_id},
            networking=network,
            cloudFeatures=cloud_features,
            **kwargs
        )

        resp = self.api.create(
            "/api/v1beta0/user/envId/farms/farmId/farm-roles/",
            params=dict(
                envId=self.env_id,
                farmId=farm_id
            ),
            body=remove_empty_values(body))
        return resp.json_data.data

    def gen_farm_template(self, farm_id, farm_name=None):
        tpl = self.api.generate_template(
            "/api/v1beta0/user/envId/farms/farmId/actions/generate-template/",
            params=dict(
                envId=self.env_id,
                farmId=farm_id
            )).json_data.data
        if farm_name:
            tpl.farm.name = farm_name
        return tpl

    def get_farm(self, farm_id):
        resp = self.api.get(
            "/api/v1beta0/user/envId/farms/farmId/",
            params=dict(
                envId=self.env_id,
                farmId=farm_id
            )
        )
        return resp.json_data.data

    def get_role(self, role_id):
        resp = self.api.get(
            "/api/v1beta0/user/envId/roles/roleId/",
            params=dict(
                envId=self.env_id,
                roleId=role_id
            )
        )
        return resp.json_data.data

    def get_farm_roles(self, farm_id):
        resp = self.api.list(
            "/api/v1beta0/user/envId/farms/farmId/farm-roles/",
            params=dict(
                envId=self.env_id,
                farmId=farm_id
            )
        )
        return resp.json_data.data

    def get_farm_role_details(self, farm_role_id):
        resp = self.api.get(
            "/api/v1beta0/user/envId/farm-roles/farmRoleId/",
            params=dict(
                envId=self.env_id,
                farmRoleId=farm_role_id
            )
        )
        return resp.json_data.data

    @property
    def uniq_farm_name(self):
        return "tmp-api-%s" % uniq_uuid()


class TestEmptyFarm(Setup):

    @pytest.fixture(autouse=True)
    def bootstrap(self, api):
        self.api = super().init_api(api)
        # create empty Farm
        self.farm = self.create_farm()
        # gen tpl from Farm
        self.farm_tpl = self.gen_farm_template(
            farm_id=self.farm.id)
        self.role = self.get_role(self.role_id)

    def test_deploy_empty_farm(self):
        farm_tpl = self.farm_tpl.copy()
        farm_tpl.farm.name = self.uniq_farm_name
        # create Farm from template
        farm = self.create_farm(
            farm_tpl=farm_tpl.to_dict()
        )
        # check Farm created
        assert farm_tpl.farm.name == self.get_farm(farm_id=farm.id).name

    def test_deploy_farm_add_farm_role(self):
        farm_tpl = self.farm_tpl.copy()
        # modify farm template
        farm_tpl.farm.name = self.uniq_farm_name
        # add role to farm template
        role_params = dict(
            cloudLocation=Platform.GCE.location,
            cloudPlatform=Platform.GCE,
            instanceType={'id': Platform.GCE.instance_type},
            role=dict(id=self.role.id),
            alias=self.role.name,
            availabilityZones=[Platform.GCE.zone],
            networking={'networks': [{'id': Platform.GCE.network}]}
        )
        farm_tpl.roles.append(role_params)
        # create Farm from template
        farm = self.create_farm(
            farm_tpl=farm_tpl.to_dict()
        )
        # check Farm created
        assert farm_tpl.farm.name == self.get_farm(farm_id=farm.id).name
        assert self.get_farm_roles(farm.id)

    def test_deploy_existing_farm(self):
        # create Farm from template
        exc_message = "'FarmTemplate.farm.name' ({farm_name}) already exists. " \
                      "The 'id' is ({farm_id})".format(
            farm_name=self.farm.name,
            farm_id=self.farm.id
        )
        with pytest.raises(requests.exceptions.HTTPError) as e:
            self.create_farm(
                farm_tpl=self.farm_tpl.to_dict())
        assert exc_message in e.value.args[0]


class TestSimpleFarm(Setup):

    def change_role_deprecated_state(self, role_id, deprecated=True):
        body = dict(deprecate=deprecated)
        resp = self.api.deprecate(
            "/api/v1beta0/user/envId/roles/roleId/actions/deprecate/",
            params=dict(
                envId=self.env_id,
                roleId=role_id),
            body=body)
        return resp.json_data.data


    @pytest.fixture(autouse=True)
    def bootstrap(self, api):
        self.api = super().init_api(api)
        self.role = self.get_role(self.role_id)
        # create empty Farm
        self.farm = self.create_farm()
        # add GCE role to farm by api call
        self.add_role_to_farm(
            farm_id=self.farm.id,
            role_id=self.role.id,
            alias=self.role.name,
            location=Platform.GCE.location,
            platform=Platform.GCE,
            instance_type=Platform.GCE.instance_type,
            zone=Platform.GCE.zone,
            network=Platform.GCE.network
        )
        # gen tpl from Farm
        self.farm_tpl = self.gen_farm_template(
            farm_id=self.farm.id)

    def test_deploy_farm_invalid_tpl_structure(self):
        exc_message = "InvalidStructure: 'Farm.data' does not exist."
        farm_tpl = {'data': self.farm_tpl.copy()}
        with pytest.raises(requests.exceptions.HTTPError) as e:
            self.create_farm(farm_tpl=farm_tpl)
        assert exc_message == e.value.args[0]

    def test_deploy_farm_invalid_cost_project_id(self):
        exc_message = "ObjectNotFound: 'FarmTemplate.farm.project.id' ({project_id}) was not found."
        farm_tpl = self.farm_tpl.copy()
        # set invalid project id
        farm_tpl.farm.project.id = uniq_uuid()
        with pytest.raises(requests.exceptions.HTTPError) as e:
            self.create_farm(farm_tpl=farm_tpl.to_dict())
        assert exc_message.format(project_id=farm_tpl.farm.project.id) == e.value.args[0]

    def test_deploy_farm_invalid_role_id(self):
        exc_message = "ObjectNotFound: 'FarmTemplate.roles.id' ({role_id}) was not found " \
                      "or isn't in scope for the current Environment."
        farm_tpl = self.farm_tpl.copy()
        # set invalid role id
        farm_tpl.roles[0].role.id = uniq_uuid()
        with pytest.raises(requests.exceptions.HTTPError) as e:
            self.create_farm(farm_tpl=farm_tpl.to_dict())
        assert exc_message.format(role_id=farm_tpl.roles[0].role.id) == e.value.args[0]

    def test_deploy_farm_invalid_role_name(self):
        exc_message = "ObjectNotFound: 'FarmTemplate.roles.name' ({role_name}) was not found " \
                      "or isn't in scope for the current Environment."
        farm_tpl = self.farm_tpl.copy()
        # set invalid role name
        farm_tpl.roles[0].role.name = uniq_uuid()
        with pytest.raises(requests.exceptions.HTTPError) as e:
            self.create_farm(farm_tpl=farm_tpl.to_dict())
        assert exc_message.format(role_name=farm_tpl.roles[0].role.name) == e.value.args[0]

    def test_deploy_farm_deprecated_role(self):
        exc_message = "Deprecated: 'FarmTemplate.roles.role.id' ({role_id}) is deprecated."
        # set role deprecated
        self.change_role_deprecated_state(self.role.id)
        farm_tpl = self.farm_tpl.copy()
        with pytest.raises(requests.exceptions.HTTPError) as e:
            self.create_farm(farm_tpl=farm_tpl.to_dict())
        assert exc_message.format(role_id=self.role.id) == e.value.args[0]
        # unset role deprecated
        self.change_role_deprecated_state(self.role.id, deprecated=False)

    def test_deploy_farm_invalid_cloud_platform(self):
        exc_message = "InvalidValue: 'FarmTemplate.roles.cloudPlatform ({platform}) is invalid."
        farm_tpl = self.farm_tpl.copy()
        farm_tpl.roles[0].cloudPlatform = Platform.INVALID
        with pytest.raises(requests.exceptions.HTTPError) as e:
            self.create_farm(farm_tpl=farm_tpl.to_dict())
        assert exc_message.format(platform=Platform.INVALID) == e.value.args[0]

    def test_deploy_farm_invalid_cloud_location(self):
        exc_message = "InvalidValue: 'FarmTemplate.roles.cloudLocation' ({location}) is invalid " \
                      "for 'FarmRole.alias' ({name})."
        farm_tpl = self.farm_tpl.copy()
        farm_tpl.farm.name = self.uniq_farm_name
        farm_tpl.roles[0].cloudLocation = Platform.INVALID.location
        with pytest.raises(requests.exceptions.HTTPError) as e:
            self.create_farm(farm_tpl=farm_tpl.to_dict())
        assert exc_message.format(location=Platform.INVALID.location, name=farm_tpl.roles[0].alias) == e.value.args[0]

    def test_deploy_farm_invalid_zone(self):
        exc_message = "ObjectNotFoundOnCloud: 'FarmTemplate.roles.availabilityZones' ({zone}) was not found in the cloud."
        farm_tpl = self.farm_tpl.copy()
        farm_tpl.farm.name = self.uniq_farm_name
        farm_tpl.roles[0].availabilityZones[0] = Platform.INVALID.zone
        with pytest.raises(requests.exceptions.HTTPError) as e:
            self.create_farm(farm_tpl=farm_tpl.to_dict())
        assert exc_message.format(zone=Platform.INVALID.zone) in e.value.args[0]

    def test_deploy_farm_invalid_instance_type(self):
        exc_message = "InvalidValue: 'FarmTemplate.roles.instanceType.id' ({type}) is invalid."
        farm_tpl = self.farm_tpl.copy()
        farm_tpl.farm.name = self.uniq_farm_name
        farm_tpl.roles[0].instanceType.id = Platform.INVALID.instance_type
        with pytest.raises(requests.exceptions.HTTPError) as e:
            self.create_farm(farm_tpl=farm_tpl.to_dict())
        assert exc_message.format(type=Platform.INVALID.instance_type) == e.value.args[0]

    def test_deploy_farm_invalid_instance_cpu_count(self):
        exc_message = "InvalidValue: Custom 'FarmTemplate.roles.instanceType' ({cpu}) CPU count 0 is invalid."
        custom_cpu = 'custom-0-0'
        farm_tpl = self.farm_tpl.copy()
        farm_tpl.farm.name = self.uniq_farm_name
        farm_tpl.roles[0].instanceType.id = custom_cpu
        with pytest.raises(requests.exceptions.HTTPError) as e:
            self.create_farm(farm_tpl=farm_tpl.to_dict())
        assert exc_message.format(cpu=custom_cpu) in e.value.args[0]

    def test_deploy_farm_invalid_instance_memory_size(self):
        exc_message = "InvalidValue: Custom 'FarmTemplate.roles.instanceType' ({ram}) memory size 0 is invalid."
        custom_ram = 'custom-1-0'
        farm_tpl = self.farm_tpl.copy()
        farm_tpl.farm.name = self.uniq_farm_name
        farm_tpl.roles[0].instanceType.id = custom_ram
        with pytest.raises(requests.exceptions.HTTPError) as e:
            self.create_farm(farm_tpl=farm_tpl.to_dict())
        assert exc_message.format(ram=custom_ram) in e.value.args[0]

class TestFarmAllCloudRoles(Setup):

    @pytest.fixture(autouse=True)
    def bootstrap(self, api):
        self.api = super().init_api(api)
        role = self.get_role(self.role_id)
        # create empty Farm
        self.farm = self.create_farm()
        self.platforms = []
        # add role for all cloud to farm by api call
        for attr, _ in inspect.getmembers(Platform):
            if re.match("(^[^Ia-z_\W]+)", attr):
                platform = getattr(Platform, attr)
                self.platforms.append(str(platform))
                role_args = dict([attr for attr in inspect.getmembers(platform)
                     if not attr[0].startswith('_')])
                self.add_role_to_farm(
                    farm_id=self.farm.id,
                    role_id=role.id,
                    alias=role.name,
                    platform=platform,
                    **role_args)
        # gen tpl from Farm
        self.farm_tpl = self.gen_farm_template(
            farm_id=self.farm.id)

    def test_deploy_farm_all_cloud_roles(self):
        farm_tpl = self.farm_tpl.copy()
        farm_tpl.farm.name = self.uniq_farm_name
        farm = self.create_farm(farm_tpl=farm_tpl.to_dict())
        farm_roles_platforms = [fr.cloudPlatform for fr in self.get_farm_roles(farm.id)]
        assert farm_roles_platforms.sort() == self.platforms.sort()

    def test_deploy_farm_aws_invalid_instance_type(self):
        exc_message = "InvalidValue: 'FarmTemplate.roles.instanceType.id' ({type}) is invalid."
        farm_tpl = self.farm_tpl.copy()
        farm_tpl.farm.name = self.uniq_farm_name
        # set invalid aws farm role instance type
        for farm_role in farm_tpl.roles:
            if farm_role.cloudPlatform == Platform.EC2:
                farm_role.instanceType.id = Platform.INVALID.instance_type
                break
        with pytest.raises(requests.exceptions.HTTPError) as e:
            self.create_farm(farm_tpl=farm_tpl.to_dict())
        assert exc_message.format(type=Platform.INVALID.instance_type) == e.value.args[0]

class TestFarmComplexFarmRoleSettings(Setup):

    chef_bootstraping_rule = {
        "bootstrapping": {
            "enabled": True,
            "type": "ChefServerBootstrapConfiguration",
            "server": {"id": 1},
            "runList": '["recipe[memcached::default]", "recipe[revizorenv]"]',
            "attributes": '{"memcached": {"memory": "1024"}}'}}

    scaling_rule = {
        "base_options": {
            "calculatingPeriod": 15,
            "name": "LoadAverages",
            "ruleType": "LoadAveragesScalingRule",
            "scaleDown": 1,
            "scaleUp": 2},
        "rule_details":  {
            "considerSuspendedServers": "running",
            "enabled": True,
            "maxInstances": 2,
            "minInstances": 1,
            "scalingBehavior": "launch-terminate"}}

    storages_configuration = {
        "fromTemplateIfMissing": True,
        "mounting": {
            "enabled": True,
            "fileSystem": "ext3",
            "mountPoint": "/mnt/"},
        "reUse": True,
        "template": {
            "type": "pd-standard",
            "size": 10},
        "type": "PersistentStorageConfiguration"}

    orchestration_config = {
        "events": ["HostInit", "BeforeHostUp", "HostUp"],
        "rule": {"action": {
            "actionType": "ScalrScriptAction",
            "scriptVersion": {
                "script": {"id": 2369},
                "version": -1}},
        "blocking": True,
        "enabled": True,
        "order": 10,
        "runAs": "root",
        "target": {
            "targetType": "TriggeringServerTarget"
        },
        "timeout": 1200,
        "trigger": {
            "event": {"id": None},
            "triggerType": "SpecificEventTrigger"}}}

    ext_vmware_network_id = "network-103"


    def add_scaling_rule(self, farm_role_id, scaling_rule):
        self.api.create_rule(
            "/api/v1beta0/user/envId/farm-roles/farmRoleId/scaling/",
            params=dict(
                envId=self.env_id,
                farmRoleId=farm_role_id
            ),
            body=scaling_rule['base_options'])
        self.api.edit_scaling_configuration(
            "/api/v1beta0/user/envId/farm-roles/farmRoleId/scaling/",
            params=dict(
                envId=self.env_id,
                farmRoleId=farm_role_id
            ),
            body=scaling_rule['rule_details'])

    def add_ext_storage(self, farm_role_id, storage_conf):
        self.api.create(
            "/api/v1beta0/user/envId/farm-roles/farmRoleId/storage/",
            params=dict(
                envId=self.env_id,
                farmRoleId=farm_role_id
            ),
            body=storage_conf
        )

    def add_orchestration_rules(self, farm_role_id, orchestration_config):
        for event in orchestration_config['events']:
            orchestration_config['rule']['trigger']['event']['id'] = event
            self.api.create(
                "/api/v1beta0/user/envId/farm-roles/farmRoleId/orchestration-rules/",
                params=dict(
                    envId=self.env_id,
                    farmRoleId=farm_role_id),
                body=orchestration_config['rule']
            )

    def get_storages(self, farm_role_id):
        resp = self.api.list(
            "/api/v1beta0/user/envId/farm-roles/farmRoleId/storage/",
            params=dict(
                envId=self.env_id,
                farmRoleId=farm_role_id))
        return resp.json_data.data

    def get_orchestration_rules(self, farm_role_id):
        resp = self.api.list(
            "/api/v1beta0/user/envId/farm-roles/farmRoleId/orchestration-rules/",
            params=dict(
                envId=self.env_id,
                farmRoleId=farm_role_id))
        return resp.json_data.data

    @pytest.fixture(autouse=True)
    def bootstrap(self, api):
        platforms = [Platform.GCE, Platform.VMWARE]
        self.api = super().init_api(api)
        role = self.get_role(self.role_id)
        # create empty Farm
        self.farm = self.create_farm()
        for platform in platforms:
            role_args = dict([attr for attr in inspect.getmembers(platform)
                     if not attr[0].startswith('_')])
            if platform.is_gce:
                role_args.update(self.chef_bootstraping_rule)
            elif platform.is_vmware:
                role_args['network'] = [role_args['network'], self.ext_vmware_network_id]
            farm_role = self.add_role_to_farm(
                farm_id=self.farm.id,
                role_id=role.id,
                alias=role.name,
                platform=platform,
                **role_args)
            if platform.is_gce:
                self.add_scaling_rule(
                    farm_role_id=farm_role.id,
                    scaling_rule=self.scaling_rule)
                self.add_ext_storage(
                    farm_role_id=farm_role.id,
                    storage_conf=self.storages_configuration)
                self.add_orchestration_rules(
                    farm_role_id=farm_role.id,
                    orchestration_config=self.orchestration_config)
        # gen tpl from Farm
        self.farm_tpl = self.gen_farm_template(
            farm_id=self.farm.id)

    def test_deploy_complex_farm(self):
        farm_tpl = self.farm_tpl.copy()
        farm_tpl.farm.name = self.uniq_farm_name
        farm = self.create_farm(farm_tpl=farm_tpl.to_dict())
        farm_roles = self.get_farm_roles(farm_id=farm.id)
        for farm_role in farm_roles:
            farm_role_details = self.get_farm_role_details(farm_role.id)
            if farm_role.cloudPlatform == Platform.GCE:
                # get farm role storage list
                farm_role_storage = self.get_storages(farm_role.id)
                # get farm role orchestration rules
                farm_role_orchestraion_rules = self.get_orchestration_rules(farm_role.id)
                # check farm role scalling rules
                assert self.scaling_rule['base_options']['name'] in farm_role_details.scaling.rules \
                       and self.scaling_rule['rule_details']['enabled'] == farm_role_details.scaling.enabled
                # check farm role chef bootstraping config
                assert self.chef_bootstraping_rule['bootstrapping']['runList'] == farm_role_details.bootstrapping.runList
                # check farm role storage
                assert any(self.storages_configuration['type'] == storage.type for storage in farm_role_storage)
                # check farm role orchestration rules
                assert all(orchestration_rule.trigger.event.id in self.orchestration_config['events']
                           for orchestration_rule in farm_role_orchestraion_rules)
            if farm_role.cloudPlatform == Platform.VMWARE:
                assert any(self.ext_vmware_network_id == network.id for network in farm_role_details.networking.networks)



