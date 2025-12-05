FROM python:3.13.5

ENV PIP_ROOT_USER_ACTION=ignore

ARG DEV=false

RUN apt-get update && \
    apt-get install -y bash-completion && \
	if [ "$DEV" = "true" ] ; then apt-get install -y graphviz ; fi && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY requirementsDev.txt .
# Install Python dev dependencies
RUN if [ "$DEV" = "true" ] ; then \
        pip install --no-cache-dir -r requirementsDev.txt ; \
    fi

ENV PATH="/Bloop/Share:${PATH}"
ENV PYTHONPATH "/Bloop/Source:/Bloop/Build/CythonModules"
RUN activate-global-python-argcomplete

COPY Share/RunStagesWrapper.sh /usr/local/bin/bloop
RUN chmod +x /usr/local/bin/bloop
RUN register-python-argcomplete bloop > /etc/bash_completion.d/bloop

# Source the completion file in bashrc
RUN echo 'source /etc/bash_completion.d/python-argcomplete' >> /root/.bashrc

