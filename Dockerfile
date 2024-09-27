FROM python:3.11.7

# https://python-poetry.org/docs#ci-recommendations
ENV POETRY_VERSION=1.8.3 \
    POETRY_HOME=/opt/poetry \
    POETRY_VENV=/opt/poetry-venv \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/opt/.cache

RUN pip install --upgrade pip && pip install poetry==${POETRY_VERSION}

WORKDIR /project-x-be
COPY pyproject.toml poetry.lock ./

RUN poetry install --no-root && rm -rf ${POETRY_CACHE_DIR}

COPY . /project-x-be