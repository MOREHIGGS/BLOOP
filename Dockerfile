FROM python:3.13.5
ARG DEV=false

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

RUN apt-get update && \
    apt-get install -y bash-completion && \
    if [ "$DEV" = "true" ] ; then apt-get install -y graphviz ; fi && \
    rm -rf /var/lib/apt/lists/*

COPY Share/.requirements.txt .
RUN uv pip install --system --no-cache -r .requirements.txt

COPY Share/.requirementsDev.txt .
RUN if [ "$DEV" = "true" ] ; then \
        uv pip install --system --no-cache -r .requirementsDev.txt ; \
    fi

ENV PATH="/Bloop/Share:${PATH}"
ENV PYTHONPATH "/Bloop/Source:/Bloop/Build/CythonModules"

RUN activate-global-python-argcomplete

COPY Share/RunStagesWrapper.sh /usr/local/bin/bloop
RUN chmod +x /usr/local/bin/bloop
RUN register-python-argcomplete bloop > /etc/bash_completion.d/bloop

RUN echo 'source /etc/bash_completion.d/python-argcomplete' >> /root/.bashrc
