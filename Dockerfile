# Prepare the base environment.
FROM python:3.6.8-slim-stretch as builder_base_biosys
MAINTAINER asi@dbca.wa.gov.au
RUN apt-get update -y \
  && apt-get install --no-install-recommends -y wget git libmagic-dev gcc binutils libproj-dev gdal-bin python3-dev  gcc g++ libsasl2-dev libldap2-dev \
  && rm -rf /var/lib/apt/lists/* \
  && pip install --upgrade pip

# Install Python libs from requirements.txt.
FROM builder_base_biosys as python_libs_biosys
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Install the project.
FROM python_libs_biosys
WORKDIR /app
COPY biosys ./biosys
COPY fabfile.py gunicorn.ini manage.py ./
RUN python manage.py collectstatic --noinput
EXPOSE 8080
CMD ["gunicorn", "biosys.wsgi", "--config", "gunicorn.ini"]
