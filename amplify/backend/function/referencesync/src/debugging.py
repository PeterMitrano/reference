import os
from logging import getLogger

logger = getLogger(__name__)

REMOTE_DEBUG_ENABLED = os.environ.get('REMOTE_DEBUG_ENABLED')
REMOTE_DEBUG_HOST = os.environ.get('REMOTE_DEBUG_HOST')
REMOTE_DEBUG_PORT = os.environ.get('REMOTE_DEBUG_PORT')


class RemoteDebugSession:
    def __init__(self):
        self.active = False
        if not self.is_available():
            logger.warning(f"Remote debugging is not available")
            return

        try:
            # pydevd_pycharm exposes only settrace() from pydevd, import pydevd directly instead
            # import pydevd_pycharm
            import pydevd
            self.pydevd = pydevd
        except Exception as e:
            logger.warning(f"Remote debugging is unavailable")
            logger.warning(e)
            self.pydevd = None

    def __enter__(self):
        if not self.is_available() or self.pydevd is None:
            return

        self.pydevd.settrace(REMOTE_DEBUG_HOST, port=REMOTE_DEBUG_PORT,
                             suspend=False,
                             stdoutToServer=True,
                             stderrToServer=True)

        logger.warning("Starting remote dubugging session")
        self.active = True

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self.active:
            return

        if exc_type or exc_val or exc_tb:
            logger.warning(
                f"Remote debugging on {REMOTE_DEBUG_HOST}:{REMOTE_DEBUG_HOST} failed")
            logger.warning(exc_type)
            logger.warning(exc_val)
            logger.warning(exc_tb)
        else:
            logger.warning(f"Remote debugging on {REMOTE_DEBUG_HOST}:{REMOTE_DEBUG_HOST} closed")

        self.pydevd.stoptrace()

    @staticmethod
    def is_available():
        return REMOTE_DEBUG_ENABLED and REMOTE_DEBUG_HOST and REMOTE_DEBUG_PORT
