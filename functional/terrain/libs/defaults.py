import json
import logging

from revizor2.conf import CONF
from revizor2.consts import Platform

LOG = logging.getLogger(__name__)


class _Property(object):
    def __init__(self, key, default, constraint=None):
        self.key = key
        self.default = default
        self.constraint = constraint


class _EnvDefaults(object):
    template = {}
    size_constraints = {}
    volumes_count_constraints = {}

    @classmethod
    def _get_prop_config(cls, volume, prop_name):
        prop = cls.template[volume.category]["settings"].get(prop_name, None)
        if not prop:
            return {}, None
        value = volume.volume_settings.get(prop_name, None)
        if value is None:
            value = prop.default
        cls._validate_property(prop, value)
        return {prop.key: value}, value

    @classmethod
    def _validate_property(cls, prop, value):
        if prop.constraint and value not in prop.constraint:
            raise StorageConfigError(
                "Invalid %s '%s'. Available values are: %s" %
                (prop.key, value, _repr_seq(prop.constraint)))

    @classmethod
    def get_config(cls, volume):
        if volume.category not in cls.template:
            raise StorageConfigError(
                "Unknown storage category '%s'. Allowed values for %s platform are: %s." %
                (volume.category, volume.platform, ", ".join(cls.template.keys())))

        config = {
            "type": cls.template[volume.category]["engine"],
            "reUse": volume.reuse,
            "rebuild": volume.rebuild,
            "mount": volume.mount,
            "mountPoint": volume.mount_point,
            "fs": volume.file_system,
            "settings": {}
        }

        tpl_settings = cls.template[volume.category]["settings"]

        cfg, type_value = cls._get_prop_config(volume, "type")
        config["settings"].update(cfg)

        if type_value and type_value in cls.size_constraints:
            tpl_settings["size"].default = cls.size_constraints[type_value][0] if cls.size_constraints[type_value] else 1
            tpl_settings["size"].constraint = cls.size_constraints[type_value]

        cfg, _ = cls._get_prop_config(volume, "size")
        config["settings"].update(cfg)

        if type_value == "io1":
            cfg, _ = cls._get_prop_config(volume, "iops")
            config["settings"].update(cfg)

        cfg, _ = cls._get_prop_config(volume, "snapshot")
        config["settings"].update(cfg)

        cfg, _ = cls._get_prop_config(volume, "encrypted")
        config["settings"].update(cfg)

        cfg, level_value = cls._get_prop_config(volume, "level")
        config["settings"].update(cfg)

        if level_value is not None:
            tpl_settings["volumes_count"].default = cls.volumes_count_constraints[level_value][0]
            tpl_settings["volumes_count"].constraint = cls.volumes_count_constraints[level_value]

        cfg, _ = cls._get_prop_config(volume, "volumes_count")
        config["settings"].update(cfg)

        for key, value in volume.volume_settings.items():
            if key not in tpl_settings:
                LOG.warning("Unknown %s volume setting: '%s', skipping" % (volume.category, key))

        return config


class _Ec2Defaults(_EnvDefaults):
    template = {
        "persistent": {
            "engine": "ebs",
            "settings": {
                "type": _Property("ebs.type", "standard", ["standard", "gp2", "io1", "st1", "sc1"]),
                "size": _Property("ebs.size", 1, range(1, 1025)),
                "iops": _Property("ebs.iops", 100, range(100, 20001)),
                "snapshot": _Property("ebs.snapshot", None),
                "encrypted": _Property("ebs.encrypted", False, [True, False])
            }
        },
        "raid": {
            "engine": "raid.ebs",
            "settings": {
                "type": _Property("ebs.type", "standard", ["standard", "gp2", "io1", "st1", "sc1"]),
                "size": _Property("ebs.size", 1, range(1, 1025)),
                "iops": _Property("ebs.iops", 100, range(100, 20001)),
                "level": _Property("raid.level", 10, [0, 1, 5, 10]),
                "volumes_count": _Property("raid.volumes_count", 4, [4, 6, 8])
            }
        }
    }

    size_constraints = {
        "standard": range(1, 1025),
        "gp2": range(1, 16385),
        "io1": range(4, 16385),
        "st1": range(500, 16385),
        "sc1": range(500, 16385)
    }

    volumes_count_constraints = {
        0: range(2, 9),
        1: [2],
        5: range(3, 9),
        10: [4, 6, 8]
    }


class _GceDefaults(_EnvDefaults):
    template = {
        "persistent": {
            "engine": "gce_persistent",
            "settings": {
                "type": _Property("gce_persistent.type", "pd-standard", ["pd-standard", "pd-ssd"]),
                "size": _Property("gce_persistent.size", 1, None)
            }
        },
        "eph": {
            "engine": "gce_ephemeral",
            "settings": {
                "name": _Property("gce_ephemeral.name", "google-local-ssd-0",
                                  ["google-local-ssd-%s" % n for n in range(0, 4)]),
                "size": _Property("gce_ephemeral.size", 375, [375])
            }
        }
    }


class _CloudStackDefaults(_EnvDefaults):
    template = {
        "persistent": {
            "engine": "csvol",
            "settings": {
                "type": _Property("csvol.disk_offering_type", "custom", ["custom", "fixed"]),
                "size": _Property("csvol.size", 1, None),
                "snapshot": _Property("csvol.snapshot_id", None)
            }
        },
        "raid": {
            "engine": "raid.csvol",
            "settings": {
                "type": _Property("csvol.disk_offering_type", "custom", ["custom", "fixed"]),
                "size": _Property("csvol.size", 1, None),
                "snapshot": _Property("csvol.snapshot_id", None),
                "level": _Property("raid.level", 10, [0, 1, 5, 10]),
                "volumes_count": _Property("raid.volumes_count", 4, [4, 6, 8])
            }
        }
    }

    size_constraints = {
        "custom": None,
        "fixed": [5, 20, 100]
    }

    volumes_count_constraints = {
        0: range(2, 9),
        1: [2],
        5: range(3, 9),
        10: [4, 6, 8]
    }


class Snapshot(object):
    def __init__(self, snapshot_id):
        self.id = snapshot_id


class Volume(object):
    def __init__(self,
                 platform=None,
                 category="persistent",
                 reuse=True,
                 rebuild=False,
                 mount=True,
                 mount_point="/media/diskmount",
                 file_system="ext3",
                 **volume_settings):
        self.platform = platform or CONF.feature.driver.current_cloud
        self.category = category
        self.reuse = reuse
        self.rebuild = rebuild
        self.mount = mount
        self.mount_point = mount_point
        self.file_system = file_system
        self.volume_settings = volume_settings

    def get_config(self):
        return _env_defaults[self.platform].get_config(self)


class Defaults(object):
    @classmethod
    def get_additional_storages(cls, platform=None, *volumes):
        platform = platform or CONF.feature.driver.current_cloud
        # dist = CONF.feature.dist

        if volumes:
            return AdditionalStorages(*volumes)

        # Populate with default storages for platform
        storages = AdditionalStorages()
        if platform == Platform.EC2:
            storages.append(Volume(platform))
            storages.append(Volume(platform, category="raid", mount_point="/media/raidmount"))
            storages.append(Volume(platform, mount_point="/media/partition"))
        elif platform == Platform.GCE:
            storages.append(Volume(platform))
            storages.append(Volume(platform, mount_point="/media/raidmount", type="pd-ssd"))
            storages.append(Volume(platform, mount_point="/media/partition"))
        elif platform == Platform.CLOUDSTACK:
            storages.append(Volume(platform))
            storages.append(Volume(platform, category="raid", mount_point="/media/raidmount"))
            storages.append(Volume(platform, mount_point="/media/partition"))
        return storages


class AdditionalStorages(object):
    def __init__(self, *volumes):
        self.volumes = []
        self.volumes.extend(volumes)

    def append(self, volume):
        self.volumes.append(volume)

    def get_config(self):
        return {"configs": [v.get_config() for v in self.volumes]}

    def __repr__(self):
        return json.dumps(self.get_config(), indent=2)


class StorageConfigError(Exception):
    pass


def _repr_seq(seq):
    if len(seq) < 10:
        return repr(seq)
    else:
        return "[%s, ..., %r]" % (", ".join(map(str, seq[:3])), seq[-1])


_env_defaults = {
    Platform.EC2: _Ec2Defaults,
    Platform.GCE: _GceDefaults,
    Platform.CLOUDSTACK: _CloudStackDefaults
}

# for debugging purpose
if __name__ == "__main__":
    # using get_additional_storages without volumes info returns default storages list for environment
    default_storages_ec2 = Defaults.get_additional_storages(Platform.EC2)
    default_storages_gce = Defaults.get_additional_storages(Platform.GCE)
    default_storages_cs = Defaults.get_additional_storages(Platform.CLOUDSTACK)

    # volumes specified
    # only parameters that differ from default values are passed
    storages_ec2 = Defaults.get_additional_storages(Platform.EC2,
                                                    Volume(Platform.EC2, snapshot="snapshot_id"),
                                                    Volume(Platform.EC2, category="raid",
                                                           mount_point="/media/raidmount", type="io1",
                                                           level=5, snapshot="snapshot_id"))
    storages_gce = Defaults.get_additional_storages(Platform.GCE,
                                                    Volume(Platform.GCE),
                                                    Volume(Platform.GCE, category="eph", mount_point="/media/ephmount"))
    storages_cs = Defaults.get_additional_storages(Platform.CLOUDSTACK,
                                                   Volume(Platform.CLOUDSTACK, snapshot="snapshot_id"),
                                                   Volume(Platform.CLOUDSTACK, category="raid",
                                                          mount_point="/media/raidmount", type="fixed", size=20,
                                                          level=5))

    print("=== EC2 defaults")
    print(default_storages_ec2)
    print("=== GCE defaults")
    print(default_storages_gce)
    print("=== CS defaults")
    print(default_storages_cs)
    print("=== EC2 custom")
    print(storages_ec2)
    print("=== GCE custom")
    print(storages_gce)
    print("=== CS custom")
    print(storages_cs)

    # invalid volume specification
    # invalid_1 = Defaults.get_additional_storages(Platform.EC2,
    #                                              Volume(type="std")).get_config()
    invalid_2 = Defaults.get_additional_storages(Platform.EC2,
                                                 Volume(category="raid", mount_point="/media/raidmount", type="io1",
                                                        level=5, volumes_count=2)).get_config()
