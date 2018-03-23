from lettuce import world

import platform


available_platforms = {
    'ec2': platform.Ec2ServicePlatform,
    'azure': platform.AzureServicePlatform
}


@world.absorb
def csg_verify_service(platform_name, service_name, request_id, secret, status='active'):
    if platform_name not in available_platforms:
        raise NotImplementedError('Platform %s is not supported' % platform_name)
    service_platform = available_platforms[platform_name](request_id, secret)
    service_platform.configure()
    if status == 'active':
        service_platform.verify(service_name)
    else:
        service_platform.verify_denied(service_name, status)


@world.absorb
def csg_get_service_log_records(platform_name, service_name):
    """Returns list of Squid log entries for specified service"""
    return available_platforms[platform_name].get_service(service_name).log_records
