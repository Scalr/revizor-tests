from lettuce import world, step


@step('I set proxy for ([\w\d,]+) in Scalr to ([\w\d]+)')
def configure_scalr_proxy(step, clouds, proxy_as):
    clouds = [c.strip().lower() for c in clouds.split(',')]
    server = getattr(world, proxy_as)
    params = [
        {'name': 'scalr.connections.proxy.host', 'value': str(server.public_ip)},
        {'name': 'scalr.connections.proxy.port', 'value': 3128},
        {'name': 'scalr.connections.proxy.user', 'value': 'testuser'},
        {'name': 'scalr.connections.proxy.pass', 'value': 'p@ssw0rd'},
        {'name': 'scalr.connections.proxy.type', 'value': 0},
        {'name': 'scalr.connections.proxy.authtype', 'value': 1},
        {'name': 'scalr.connections.proxy.use_on', 'value': 'scalr'}
    ]
    for cloud in clouds:
        params.append(
            {'name': 'scalr.%s.use_proxy' % cloud, 'value': True}
        )
    world.update_scalr_config(params)


@step('Scalr services( .+)? are in (\w+) state')
def check_scalr_service_status(step, services, state):
    services = services.split(',') if services else ['all']
    for service in services:
        statuses = world.testenv.get_service_status(name=service)
        for status in statuses:
            if status['state'].lower() != state.lower():
                raise AssertionError("Service %s status is %s. Expected status - %s" % (service, status, state))
