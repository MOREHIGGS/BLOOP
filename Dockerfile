FROM python:3.13.5

ENV PIP_ROOT_USER_ACTION=ignore

COPY pyproject.toml .
COPY . .

RUN pip install --upgrade pip setuptools wheel
RUN pip install -e .

RUN pip install --no-cache-dir line_profiler
RUN pip install --no-cache-dir gprof2dot
RUN apt-get update && apt-get install -y graphviz && rm -rf /var/lib/apt/lists/*
ENV PATH="/Bloop/Share:${PATH}"
