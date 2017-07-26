import logging

from revizor2.conf import CONF
from revizor2.consts import Platform


LOG = logging.getLogger(__name__)


class StorageConfigError(Exception):
    pass


class Defaults(object):

    @classmethod
    def get_config_additional_storages(cls, platform, *volumes):
        platform = CONF.feature.driver.current_cloud
        dist = CONF.feature.dist

        storages = AdditionalStorages()
        storages.append(Volume())
        storages.append(Volume(volume_type="raid.ebs", mount_point="/media/raidmount", level=10, volumes_count=4))
        storages.append(Volume(mount_point="/media/partition"))
        return storages


class Ec2Defaults(object):
    volume_types = ['ebs', 'raid.ebs']

env_defaults = {
    Platform.EC2: Ec2Defaults
}

class AdditionalStorages():

    def __init__(self):
        self.volumes = []

    def append(self, volume):
        self.volumes.append(volume)

    def get_config(self):
        return { 'configs': [v.get_config() for v in self.volumes] }

    def __repr__(self):
        return repr(self.volumes)


class Volume(object):

    def __init__(self,
                 id=None,
                 volume_type='ebs',
                 fs='ext3',
                 mount=True,
                 mount_point='/media/diskmount',
                 reuse=True,
                 status='',
                 rebuild=True,
                 size=1,
                 type='standard',
                 snapshot=None,
                 level=None,
                 volumes_count=None):
        self.id = id
        self.type = volume_type
        self.fs = fs
        self.mount = mount
        self.mountPoint = mount_point
        self.reUse = reuse
        self.status = status
        self.rebuild = rebuild
        self.settings = VolumeSettings(size, type, snapshot, level, volumes_count)

    def validate(self):
        platform = CONF.feature.driver.current_cloud
        defaults = env_defaults[platform]
        if not self.type in defaults.volume_types:
            raise StorageConfigError("%s does not support %s volume type" % (platform, self.type))


    def get_config(self):
        self.validate()
        config = self.__dict__.copy()
        config['settings'] = config['settings'].get_config()
        return config

    def __repr__(self):
        return repr(self.get_config())


class VolumeSettings(object):

    def __init__(self,
                 size=1,
                 type='standard',
                 snapshot=None,
                 level=None,
                 volumes_count=None):
        self.size = size
        self.type = type
        self.snapshot = snapshot
        self.level = level
        self.volumes_count = volumes_count

    def get_config(self):
        config = {
            "ebs.size": self.size,
            "ebs.type": self.type,
            "ebs.snapshot": self.snapshot
        }
        if self.level:
            config["raid.level"] = self.level
        if self.volumes_count:
            config["raid.volumes_count"] = self.volumes_count


    def __repr__(self):
        return repr(self.__dict__)


class Snapshot(object):

    def __init__(self, id):
        self.id = id


DEFAULT_ADDITIONAL_STORAGES = {
    Platform.EC2: [
        {
            "id": None,
            "type": "ebs",
            "fs": "ext3",
            "settings": {
                "ebs.size": "1",
                "ebs.type": "standard",
                "ebs.snapshot": None,
            },
            "mount": True,
            "mountPoint": "/media/diskmount",
            "reUse": True,
            "status": "",
            "rebuild": True
        },
        {
            "id": None,
            "type": "raid.ebs",
            "fs": "ext3",
            "settings": {
                "raid.level": "10",
                "raid.volumes_count": 4,
                "ebs.size": "1",
                "ebs.type": "standard",
                "ebs.snapshot": None,
            },
            "mount": True,
            "mountPoint": "/media/raidmount",
            "reUse": True,
            "status": "",
        },
        {
            "id": None,
            "type": "ebs",
            "fs": "ext3",
            "settings": {
                "ebs.size": "1",
                "ebs.type": "standard",
                "ebs.snapshot": None,
            },
            "mount": True,
            "mountPoint": "/media/partition",
            "reUse": True,
            "status": "",
            "rebuild": True
        }
    ],

    Platform.GCE: [
        {
            "reUse": True,
            "settings": {
                "gce_persistent.size": "1",
                "gce_persistent.type": "pd-standard"
            },
            "status": "",
            "type": "gce_persistent",
            "fs": "ext3",
            "mount": True,
            "mountPoint": "/media/diskmount",
            "rebuild": True
        },
        {
            "reUse": True,
            "settings": {
                "gce_persistent.size": "1",
                "gce_persistent.type": "pd-ssd"
            },
            "status": "",
            "type": "gce_persistent",
            "fs": "ext3",
            "mount": True,
            "mountPoint": "/media/raidmount",
            "rebuild": True
        },
        {
            "reUse": True,
            "settings": {
                "gce_persistent.size": "1",
                "gce_persistent.type": "pd-standard"
            },
            "status": "",
            "type": "gce_persistent",
            "fs": "ext3",
            "mount": True,
            "mountPoint": "/media/partition",
            "rebuild": True
        },
    ],
    # Platform.VMWARE: [
    #     {
    #         "reUse": False,
    #         "type": "vmdk",
    #         "status": "",
    #         "isRoot": 0,
    #         "readOnly": False,
    #         "category": " Persistent storage",
    #         "fs": "ext3",
    #         "mount": True,
    #         "mountPoint": "/media/diskmount",
    #         "mountOptions": "",
    #         "rebuild": False,
    #         "settings": {
    #             "vmdk.id": "",
    #             "vmdk.provisioning": 0,
    #             "vmdk.size": "1"
    #         }
    #     },
    #     {
    #         "reUse": False,
    #         "type": "vmdk",
    #         "status": "",
    #         "isRoot": 0,
    #         "readOnly": False,
    #         "category": " Persistent storage",
    #         "fs": "ext4",
    #         "mount": True,
    #         "mountPoint": "/media/raidmount",
    #         "mountOptions": "",
    #         "rebuild": False,
    #         "settings": {
    #             "vmdk.id": "",
    #             "vmdk.provisioning": 2,
    #             "vmdk.size": "1"
    #         }
    #     },
    #     {
    #         "reUse": False,
    #         "type": "vmdk",
    #         "status": "",
    #         "isRoot": 0,
    #         "readOnly": False,
    #         "category": " Persistent storage",
    #         "fs": "ext3",
    #         "mount": True,
    #         "mountPoint": "/media/partition",
    #         "mountOptions": "",
    #         "rebuild": False,
    #         "settings": {
    #             "vmdk.id": "",
    #             "vmdk.provisioning": 0,
    #             "vmdk.size": "1"
    #         }
    #     }
    # ],
    Platform.CLOUDSTACK: [
        {
            "id": None,
            "type": "csvol",
            "fs": "ext3",
            "settings": {
                "csvol.size": "1",
            },
            "mount": True,
            "mountPoint": "/media/diskmount",
            "reUse": True,
            "status": "",
            "rebuild": True
        },
        {
            "id": None,
            "type": "raid.csvol",
            "fs": "ext3",
            "settings": {
                "raid.level": "10",
                "raid.volumes_count": 4,
                "csvol.size": "1",
            },
            "mount": True,
            "mountPoint": "/media/raidmount",
            "reUse": True,
            "status": "",
        },
        {
            "id": None,
            "type": "csvol",
            "fs": "ext3",
            "settings": {
                "csvol.size": "1",
            },
            "mount": True,
            "mountPoint": "/media/partition",
            "reUse": True,
            "status": "",
            "rebuild": True
        }
    ],
    # Platform.RACKSPACE_US: [
    #     {
    #         "reUse": True,
    #         "status": "",
    #         "type": "cinder",
    #         "fs": "ext4",
    #         "mount": True,
    #         "mountPoint": "/media/diskmount",
    #         "rebuild": True,
    #         "settings": {
    #             "cinder.volume_type": "d5f9242f-aeca-4b11-abbd-6dc497d2d27a",
    #             "cinder.size": "75"
    #         }
    #     },
    #     {
    #         "reUse": True,
    #         "status": "",
    #         "isRootDevice": False,
    #         "readOnly": False,
    #         "type": "raid.cinder",
    #         "fs": "ext3",
    #         "mount": True,
    #         "mountPoint": "/media/raidmount",
    #         "rebuild": True,
    #         "settings": {
    #             "raid.level": "10",
    #             "raid.volumes_count": 4,
    #             "cinder.volume_type": "d5f9242f-aeca-4b11-abbd-6dc497d2d27a",
    #             "cinder.size": "75"
    #         }
    #     }
    # ],

    # Platform.OPENSTACK: [
    #     {
    #         "reUse": True,
    #         "status": "",
    #         "isRootDevice": False,
    #         "readOnly": False,
    #         "type": "cinder",
    #         "fs": "ext4",
    #         "mount": True,
    #         "mountPoint": "/media/diskmount",
    #         "rebuild": True,
    #         "settings": {
    #             "cinder.volume_type": "d893f896-b0be-40cb-b020-9049ebc94a2f",  # TODO: move this to config
    #             "cinder.size": "1"
    #         }
    #     },
    #     {
    #         "reUse": True,
    #         "status": "",
    #         "isRootDevice": False,
    #         "readOnly": False,
    #         "type": "raid.cinder",
    #         "fs": "ext3",
    #         "mount": True,
    #         "mountPoint": "/media/raidmount",
    #         "rebuild": True,
    #         "settings": {
    #             "raid.level": "10",
    #             "raid.volumes_count": 4,
    #             "cinder.volume_type": "d893f896-b0be-40cb-b020-9049ebc94a2f",
    #             "cinder.size": "1"
    #         }
    #     }
    # ]
}