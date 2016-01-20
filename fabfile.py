import os
from fabric.api import cd, run, sudo
from fabric.contrib.files import exists, upload_template

DEPLOY_REPO_URL = os.environ['DEPLOY_REPO_URL']
DEPLOY_TARGET = os.environ['DEPLOY_TARGET']
DEPLOY_VENV_PATH = os.environ['DEPLOY_VENV_PATH']
DEPLOY_VENV_NAME = os.environ['DEPLOY_VENV_NAME']
DEPLOY_DEBUG = os.environ['DEPLOY_DEBUG']
DEPLOY_PORT = os.environ['DEPLOY_PORT']
DEPLOY_DATABASE_URL = os.environ['DEPLOY_DATABASE_URL']
DEPLOY_SECRET_KEY = os.environ['DEPLOY_SECRET_KEY']
DEPLOY_CSRF_COOKIE_SECURE = os.environ['DEPLOY_CSRF_COOKIE_SECURE']
DEPLOY_SESSION_COOKIE_SECURE = os.environ['DEPLOY_SESSION_COOKIE_SECURE']
KMI_PASSWORD = os.environ['KMI_PASSWORD']
DEPLOY_USER = os.environ['DEPLOY_USER']
DEPLOY_DB_NAME = os.environ['DEPLOY_DB_NAME']
DEPLOY_DB_USER = os.environ['DEPLOY_DB_USER']
DEPLOY_SUPERUSER_USERNAME = os.environ['DEPLOY_SUPERUSER_USERNAME']
DEPLOY_SUPERUSER_EMAIL = os.environ['DEPLOY_SUPERUSER_EMAIL']
DEPLOY_SUPERUSER_PASSWORD = os.environ['DEPLOY_SUPERUSER_PASSWORD']
DEPLOY_SUPERVISOR_NAME = os.environ['DEPLOY_SUPERVISOR_NAME']


def _get_latest_source():
    run('mkdir -p {}'.format(DEPLOY_TARGET))
    if exists(os.path.join(DEPLOY_TARGET, '.git')):
        run('cd {} && git pull'.format(DEPLOY_TARGET))
    else:
        run('git clone {} {}'.format(DEPLOY_REPO_URL, DEPLOY_TARGET))
        run('cd {} && git checkout master'.format(DEPLOY_TARGET))


def _create_dirs():
    # Ensure that required directories exist.
    with cd(DEPLOY_TARGET):
        run('mkdir -p log && mkdir -p media')


def _update_venv():
    # Assumes that virtualenv is installed system-wide.
    with cd(DEPLOY_VENV_PATH):
        if not exists('{}/bin/pip'.format(DEPLOY_VENV_NAME)):
            run('virtualenv {}'.format(DEPLOY_VENV_NAME))
        run('{}/bin/pip install -r {}/requirements.txt'.format(DEPLOY_VENV_NAME, DEPLOY_TARGET))


def _setup_env():
    with cd(DEPLOY_TARGET):
        context = {
            'DEPLOY_DEBUG': DEPLOY_DEBUG,
            'DEPLOY_PORT': DEPLOY_PORT,
            'DEPLOY_DATABASE_URL': DEPLOY_DATABASE_URL,
            'DEPLOY_SECRET_KEY': DEPLOY_SECRET_KEY,
            'DEPLOY_CSRF_COOKIE_SECURE': DEPLOY_CSRF_COOKIE_SECURE,
            'DEPLOY_SESSION_COOKIE_SECURE': DEPLOY_SESSION_COOKIE_SECURE,
            'KMI_PASSWORD': KMI_PASSWORD,
        }
        if not exists('.env'):
            upload_template('biosys/templates/env.jinja', '.env', context,
                            use_jinja=True, backup=False)


def _setup_supervisor_conf():
    with cd(DEPLOY_TARGET):
        context = {
            'DEPLOY_SUPERVISOR_NAME': DEPLOY_SUPERVISOR_NAME,
            'DEPLOY_USER': DEPLOY_USER,
            'DEPLOY_TARGET': DEPLOY_TARGET,
            'DEPLOY_VENV_PATH': DEPLOY_VENV_PATH,
            'DEPLOY_VENV_NAME': DEPLOY_VENV_NAME,
        }
        upload_template(
            'biosys/templates/supervisor.jinja', '{}/{}.conf'.format(
            DEPLOY_TARGET, DEPLOY_SUPERVISOR_NAME),
            context, use_jinja=True, backup=False)


def _chown():
    # Assumes that the DEPLOY_USER user exists on the target server.
    sudo('chown -R {0}:{0} {1}'.format(DEPLOY_USER, DEPLOY_TARGET))


def _collectstatic():
    with cd(DEPLOY_TARGET):
        run_str = 'source {}/{}/bin/activate && honcho run python manage.py collectstatic --noinput'
        run(run_str.format(DEPLOY_VENV_PATH, DEPLOY_VENV_NAME), shell='/bin/bash')


def _create_db():
    # This script assumes that PGHOST and PGUSER are set.
    db = {
        'NAME': os.environ['DEPLOY_DB_NAME'],
        'USER': os.environ['DEPLOY_DB_USER'],
    }
    sql = '''CREATE DATABASE {NAME} OWNER {USER};
        \c {NAME}'''.format(**db)
    run('echo "{}" | psql -d postgres'.format(sql))


def _migrate():
    with cd(DEPLOY_TARGET):
        run_str = 'source {}/{}/bin/activate && honcho run python manage.py migrate'
        run(run_str.format(DEPLOY_VENV_PATH, DEPLOY_VENV_NAME), shell='/bin/bash')


def _create_superuser():
    un = os.environ['DEPLOY_SUPERUSER_USERNAME']
    em = os.environ['DEPLOY_SUPERUSER_EMAIL']
    pw = os.environ['DEPLOY_SUPERUSER_PASSWORD']
    script = """from django.contrib.auth.models import User;
User.objects.create_superuser('{}', '{}', '{}')""".format(un, em, pw)
    with cd(DEPLOY_TARGET):
        run_str = 'source {}/{}/bin/activate && echo "{}" | honcho run python manage.py shell'
        run(run_str.format(DEPLOY_VENV_PATH, DEPLOY_VENV_NAME, script), shell='/bin/bash')


# --------------------------------------------------
# BioSys-specific scripts
# --------------------------------------------------
def _load_fixtures():
    # Fixture files to load, in order.
    fixtures = [
        'main/fixtures/groups.json',
        'main/fixtures/main-lookups.json',
        'animals/fixtures/animals-lookups.json',
        'vegetation/fixtures/vegetation-lookups.json']
    for f in fixtures:
        with cd(DEPLOY_TARGET):
            run_str = 'source {}/{}/bin/activate && honcho run python manage.py loaddata biosys/apps/{}'
            run(run_str.format(DEPLOY_VENV_PATH, DEPLOY_VENV_NAME, f), shell='/bin/bash')


def deploy_env():
    """Normally used to deploy a new environment. Won't harm an existing one.
    Example usage: honcho run fab deploy_env --user=root --host=aws-oim-001
    """
    _get_latest_source()
    _create_dirs()
    _update_venv()
    _setup_env()
    _chown()
    _setup_supervisor_conf()  # After the _chown step.
    _collectstatic()


def deploy_db():
    """Normally used to deploy a new database. Won't harm an existing one.
    Example usage: honcho run fab deploy_db --user=root --host=aws-oim-001
    """
    _create_db()
    _migrate()
    _create_superuser()
    _load_fixtures()


def deploy_all():
    """Deploy to a new environment in one step. Non-desctructive, but will
    raise lots of errors for an existing environment.
    """
    deploy_env()
    deploy_db()


def update_repo():
    """Update only: pulls repo changes, runs migrations, runs collectstatic.
    """
    _get_latest_source()
    _migrate()
    _collectstatic()
