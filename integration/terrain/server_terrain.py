from lettuce import world, step


@step(r'save system log status for server ([\w\d]+)$')
def save_system_log_status(step, serv_as):
    server = getattr(world, serv_as)
    ids = [log.id for log in server.logs]
    setattr(world, '%s_system_log_ids' % serv_as, ids)


@step(r"system log hasn't new messages for server ([\w\d]+)")
def system_log_without_changes_for_server(step, serv_as):
    server = getattr(world, serv_as)
    old_ids = getattr(world, '%s_system_log_ids' % serv_as)
    server.logs.reload()
    if len(server.logs) != len(old_ids):
        raise AssertionError('System log for server %s has a new messages!' % server.id)


@step(r"system log has new message with body '([\w\d \(\)\:.]+)' for server ([\w\d]+)")
def system_log_has_message_with_body(step, message, serv_as):
    server = getattr(world, serv_as)
    old_ids = getattr(world, '%s_system_log_ids' % serv_as)
    server.logs.reload()
    for log in server.logs:
        if log.id not in old_ids:
            if message in log.message:
                return
    else:
        raise AssertionError('Server %s hasn\'t message in system log with body: "%s"' % (server.id, message))
