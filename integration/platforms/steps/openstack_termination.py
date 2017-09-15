import logging

from lettuce import step, world, after

from revizor2.utils import exceptions


LOG = logging.getLogger(__name__)


@step(r'Scalr file "StatusAdapter.php" modified for test')
def modify_poller_file(step):
    LOG.info('Get file "StatusAdapter.php')
    world.files['StatusAdapter.php'] = world.testenv.get_file('/opt/scalr-server/embedded/scalr/'
                                        'app/src/Scalr/Modules/Platforms/Openstack/Adapters/StatusAdapter.php')
    with open(world.files['StatusAdapter.php'], 'r') as php_file:
        content = php_file.readlines()
    method_start_index = None
    method_end_index = None
    for i, line in enumerate(content):
        if line.strip().startswith('public function isFailed()'):
            method_start_index = i+2
        if method_start_index and line.strip() == '}':
            method_end_index = i
        if method_start_index and method_end_index:
            break
    else:
        raise exceptions.NotFound('Function isFailed not found in StatusAdapter.php')

    LOG.debug('Function isFailed from %s to %s' % (method_start_index, method_end_index))
    new_content = content[:method_start_index] + ['        return true;\n'] + content[method_end_index:]

    with open('/tmp/StatusAdapter.php.fixed', 'w+') as fixed_file:
        fixed_file.writelines(new_content)

    LOG.debug('Save modified file')
    world.testenv.put_file(
        '/tmp/StatusAdapter.php.fixed',
        '/opt/scalr-server/embedded/scalr/'
        'app/src/Scalr/Modules/Platforms/Openstack/Adapters/StatusAdapter.php'
    )


@after.each_feature
def return_modified_files():
    world.testenv.put_file(world.files['StatusAdapter.php'],
                           '/opt/scalr-server/embedded/scalr/'
                           'app/src/Scalr/Modules/Platforms/Openstack/Adapters/StatusAdapter.php'
                           )
