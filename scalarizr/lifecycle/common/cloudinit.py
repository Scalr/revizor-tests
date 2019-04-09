from revizor2.cloud import ExtendedNode
from revizor2.conf import CONF


def assert_cloudinit_installed(node: ExtendedNode):
    cmd = 'coreos-cloudinit --version' if CONF.feature.dist.id == 'coreos' else 'cloud-init -v'
    with node.remote_connection() as conn:
        out = conn.run(cmd).status_code
        if out != 0:
            if CONF.feature.dist.is_centos:
                conn.run('yum -y install cloud-init')
            else:
                conn.run('sudo apt-get install cloud-init -y')
            out = conn.run('cloud-init -v').status_code
            if out != 0:
                raise AssertionError('Cloud-init is not installed!')
