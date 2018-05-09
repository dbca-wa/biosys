FROM ubuntu:17.10
ADD . /app/
WORKDIR /app/
RUN apt-get update && \
    apt-get install --assume-yes \
      libsasl2-dev \
      libldap2-dev \
      gdal-bin \
      python3 \
      python3-pip \
      python3-dev \
      gcc && \
    pip3 install -r requirements.txt && \
    bash -c 'echo DJANGO_SETTINGS_MODULE="biosys.settings"                 > /app/.env' && \
    bash -c 'echo DEBUG=True                                              >> /app/.env' && \
    bash -c 'echo DATABASE_URL="postgis://postgres:pass@pg:5432/postgres" >> /app/.env' && \
    bash -c 'echo SECRET_KEY="ThisIsASecretKey"                           >> /app/.env' && \
    bash -c 'echo CSRF_COOKIE_SECURE=False                                >> /app/.env' && \
    bash -c 'echo SESSION_COOKIE_SECURE=False                             >> /app/.env' && \
    bash -c 'echo "from django.contrib.auth.models import User"                 >> create-user.py' && \
    bash -c "echo \"User.objects.create_superuser('admin', 'a@b.c', 'admin')\"  >> create-user.py" && \
    bash -c 'echo "#!/bin/bash"                                        >> /app/entrypoint.sh' && \
    bash -c 'echo "echo waiting \$3 seconds for postgres to start"     >> /app/entrypoint.sh' && \
    # TODO a better wait for PG method https://stackoverflow.com/a/42225536/1410035
    bash -c 'echo "sleep \$3"                                          >> /app/entrypoint.sh' && \
    bash -c 'echo "/usr/bin/python3 manage.py migrate --noinput"       >> /app/entrypoint.sh' && \
    bash -c 'echo "if [ ! -f .user-created ] ; then"                   >> /app/entrypoint.sh' && \
    bash -c 'echo "  cat create-user.py | python3 manage.py shell"     >> /app/entrypoint.sh' && \
    bash -c 'echo "  touch .user-created"                              >> /app/entrypoint.sh' && \
    bash -c 'echo "fi"                                                 >> /app/entrypoint.sh' && \
    bash -c 'echo "/usr/bin/python3 manage.py runserver 0.0.0.0:8080"  >> /app/entrypoint.sh' && \
    chmod +x entrypoint.sh && \
    apt-get purge --assume-yes \
      gcc && \
    apt-get autoremove --assume-yes && \
    apt-get --assume-yes clean && \
    rm -rf \
      /var/lib/apt/lists/* \
      /tmp/* \
      /var/tmp/*
EXPOSE 8080
CMD 10
ENTRYPOINT [ "/app/entrypoint.sh" ]
