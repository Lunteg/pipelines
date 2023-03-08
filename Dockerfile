FROM python:3.11.2
ADD pyproject.toml /

RUN pip install poetry
RUN poetry install

WORKDIR .
COPY pipelines pipelines
COPY example_pipeline example_pipeline

RUN poetry add pipelines

CMD ["python", "example_pipeline/pipeline.py"]

#docker build -t python-pipelines .
#docker run python-pipelines   