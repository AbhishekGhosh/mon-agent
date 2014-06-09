import logging

from . import Plugin, find_process_name, watch_process
from monsetup import agent_config

log = logging.getLogger(__name__)


class MySQL(Plugin):
    """Detect MySQL daemons and setup configuration to monitor them.
        This plugin needs user/pass infor for mysql setup, this is best placed in /root/.mysql.cnf
    """

    def _detect(self):
        """Run detection, set self.available True if the service is detected."""
        if find_process_name('mysqld') is not None:
            self.available = True

    def build_config(self):
        """Build the config as a Plugins object and return.
        """
        config = agent_config.Plugins()
        # First watch the process
        config.update(watch_process(['mysqld']))
        log.info("\tWatching the mysqld process.")

        # Attempt login, requires either an empty root password from localhost or relying on a configured .mysql.cnf
        if self.dependencies_installed():  # ensures MySQLdb is available
            import MySQLdb
            import _mysql_exceptions
            try:
                MySQLdb.connect(read_default_file='/root/.mysql.cnf')
            except _mysql_exceptions.MySQLError:
                pass
            else:
                log.info("\tConfiguring MySQL plugin to connect with auth settings from /root/.mysql.cnf")
                config['mysql'] = {'init_config': None, 'instances':
                                   [{'server': 'localhost', 'user': 'root', 'defaults_file': '/root/.mysql.cnf'}]}

            if not 'mysql' in config:
                try:
                    MySQLdb.connect(host='localhost', port=3306, user='root')
                except _mysql_exceptions.MySQLError:
                    pass
                else:
                    log.info("\tConfiguring MySQL plugin to connect with user root.")
                    config['mysql'] = {'init_config': None, 'instances':
                                       [{'server': 'localhost', 'user': 'root', 'pass': 'password', 'port': 3306}]}

        if not 'mysql' in config:
            log.warn('Unable to log into the mysql database, the mysql plugin is not configured.')

        return config

    def dependencies_installed(self):
        try:
            import MySQLdb
        except ImportError:
            return False

        return True
