from lettuce import step, world


@step(r'Scalr file "StatusAdapter.php" modified for test')
def modify_poller_file(step):
    world.testenv.get_file('/opt/scalr-server/e')
