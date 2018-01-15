from integration.terrain.libs.cloud_services.base import CloudServiceBase

__all__ = ['get', 'get_log_records']


def get(platform, name, request_id, secret):
    """Creates and prepares concrete cloud service class instance"""
    instance = CloudServiceBase.get_service(platform, name)(request_id, secret)
    instance.configure()
    return instance


def get_log_records(platform, name):
    """Returns list of Squid log entries for specified service"""
    return CloudServiceBase.get_service(platform, name).log_records
