import os


def pytest_configure(config):
    """
    Allow plugins and conftest files to perform initial configuration.

    This hook is called for every plugin and initial conftest file after command line options have been parsed.

    After that, the hook is called for other conftest files as they are imported.
    """


def pytest_collection(session):
    """
    Called for performing the test collection.
    """
    os.environ["PYTEST_COLLECTION"] = "True"


def pytest_unconfigure(config):
    """
    Called before test process is exited.
    """
    os.environ.pop("PYTEST_COLLECTION", None)


def pytest_sessionstart(session):
    """
    Called after the Session object has been created and
    before performing collection and entering the run test loop.
    """


def pytest_sessionfinish(session, exitstatus):
    """
    Called after whole test run finished, right before
    returning the exit status to the system.
    """
