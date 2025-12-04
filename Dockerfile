FROM python:3.13.5

ENV PIP_ROOT_USER_ACTION=ignore

COPY requirements.txt .
COPY requirementsDev.txt .
ARG DEV=false

RUN pip install --no-cache-dir -r requirements.txt

RUN if [ "$DEV" = "true" ] ; then \
        apt-get update && \
        apt-get install -y graphviz && \
        rm -rf /var/lib/apt/lists/* && \
        pip install --no-cache-dir -r requirementsDev.txt ; \
    fi

ENV PATH="/Bloop/Share:${PATH}"
ENV PYTHONPATH "/Bloop/Source:/Bloop/Build/CythonModules"
