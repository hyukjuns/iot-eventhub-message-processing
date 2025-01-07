FROM python:3.11-slim

# Container User
# -m: create home -s: login shell, Group is auto created
RUN useradd -ms /bin/bash -u 1001 python

# Setting Home
USER 1001
WORKDIR /home/python

# Package
COPY requirements.txt /home/python
RUN pip install -r requirements.txt

# Setting PATH
ENV PATH="/home/python/.local/bin:$PATH"

# Application File
COPY eventhub_receive_data-conn-str.py /home/python

# Worker Count = 1, run by uvicorn
CMD ["python", "eventhub_receive_data-conn-str.py"]