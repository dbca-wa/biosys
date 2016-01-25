import confy
import os
from fabric.api import cd, run, sudo
from fabric.colors import green, yellow, red
from fabric.contrib.files import exists, upload_template

confy.read_environment_file()
e = **os.environ

def _get_latest_source():
    run('mkdir -p {}'.format(DEPLOY_TARGET))
    if exists(os.path.join(DEPLOY_TARGET, '.git')):
        run('cd {DEPLOY_TARGET} && git pull'.format(e))
    else:
        run('git clone {DEPLOY_REPO_URL} {DEPLOY_TARGET}'.format(e))
        run('cd {DEPLOY_TARGET} && git checkout master'.format(e))


def _create_dirs():
    # Ensure that required directories exist.
    with cd(e["DEPLOY_TARGET"]):
        run('mkdir -p log && mkdir -p media')


def _update_venv():
    # Assumes that virtualenv is installed system-wide.
    with cd(e["DEPLOY_VENV_PATH"]):
        if not exists('DEPLOY_VENV_NAME{}/bin/pip'.format(e)):
            run('virtualenv {DEPLOY_VENV_NAME}'.format(e))
        run('{DEPLOY_VENV_NAME}/bin/pip install -r {DEPLOY_TARGET}/requirements.txt'.format(e))


def _setup_env():
    with cd(e["DEPLOY_TARGET"]):
        if exists('.env'):
            print(yellow("The existing .env file will be used."))
        else:
            upload_template('biosys/templates/env.jinja', '.env', e, use_jinja=True, backup=False)


def _setup_supervisor_conf():
    with cd(e["DEPLOY_TARGET"]):
        if exists('{DEPLOY_TARGET}/{DEPLOY_SUPERVISOR_NAME}.conf'.format(e)):
            print(yellow("The existing supervisor config file"+\
                    " {DEPLOY_TARGET}/{DEPLOY_SUPERVISOR_NAME}.conf will be used.".format(e)))
        else:
            upload_template(
                'biosys/templates/supervisor.jinja',
                '{DEPLOY_TARGET}/{DEPLOY_SUPERVISOR_NAME}.conf'.format(e),
                context, use_jinja=True, backup=False)


def _chown():
    # Assumes that the DEPLOY_USER user exists on the target server.
    sudo('chown -R {DEPLOY_USER}:{DEPLOY_USER} {DEPLOY_TARGET}'.format(e))


def _collectstatic():
    with cd(e["DEPLOY_TARGET"]):
        run("source {DEPLOY_VENV_PATH}/{DEPLOY_VENV_NAME}/bin/activate".format(e) +\
            " && honcho run python manage.py collectstatic --noinput", shell='/bin/bash')


def _create_db():
    # This script assumes that PGHOST and PGUSER are set.
    sql = '''CREATE DATABASE {DEPLOY_DB_NAME} OWNER {DEPLOY_DB_USER};
    \c {DEPLOY_DB_NAME}'''.format(e)
    run('echo "{}" | psql -d postgres'.format(sql))


def _migrate():
    with cd(e["DEPLOY_TARGET"]):
        run("source {DEPLOY_VENV_PATH}/{DEPLOY_VENV_NAME}".format(e) +\
            "/bin/activate && honcho run python manage.py migrate", shell="/bin/bash")


def _create_superuser():
    script = """from django.contrib.auth.models import User;
User.objects.create_superuser('{DEPLOY_SUPERUSER_USERNAME}',
'{DEPLOY_SUPERUSER_EMAIL}', '{DEPLOY_SUPERUSER_PASSWORD}')""".format(e)
    with cd(["DEPLOY_TARGET"]):
        run('source {DEPLOY_VENV_PATH}/{DEPLOY_VENV_NAME}/bin/activate &&'.format(e) +\
            ' echo "{script}" | honcho run python manage.py shell'.format(e), shell='/bin/bash')


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
        with cd(e["DEPLOY_TARGET"]):
            run("source {DEPLOY_VENV_PATH}/{DEPLOY_VENV_NAME}/bin/activate".format(e) +\
            " && honcho run python manage.py loaddata biosys/apps/{f}".format(f), shell='/bin/bash')


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
