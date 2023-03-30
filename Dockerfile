FROM python:3.11.2
ADD pyproject.toml /

RUN pip install poetry

RUN poetry config virtualenvs.create false
RUN poetry install

WORKDIR /pipelines

COPY poetry.lock pyproject.toml ./

COPY ./db /pipelines/db
COPY ./example_pipeline/ /pipelines
COPY ./example_pipeline/pipeline.py /pipelines/example_pipeline/
COPY ./pipelines /pipelines/pipelines
COPY ./README.md /pipelines
COPY ./.env /pipelines

RUN pip install -e .

CMD ["python", "example_pipeline/pipeline.py"]

#docker build -t python-pipelines .
#docker run python-pipelines   