FROM python:3.10

LABEL maintainer="cativo23.kt@gmail.com"

ARG UID
ARG GID

ENV UID=${UID}
ENV GID=${GID}

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./ /code/

RUN groupadd --force -g ${GID} myths
RUN useradd -ms /bin/bash --no-user-group -g ${GID} -u ${UID} myths

RUN chown -R myths:myths /code

ENV PYTHONPATH=/code

EXPOSE 80

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80", "--reload"]
