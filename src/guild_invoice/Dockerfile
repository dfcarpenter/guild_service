# pull official base image
FROM ubuntu:20.04 AS builder-image

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install --no-install-recommends -y python3.10 python3.10-dev libpq-dev python3.10-venv python3-pip python3-wheel build-essential git && \
	apt-get clean && rm -rf /tmp/* /var/tmp/* /var/lib/apt/lists/*

# RUN apt-get install -y git

RUN python3.9 -m venv /home/guild_invoice/venv
ENV PATH="/home/guild_invoice/venv/bin:$PATH"

# install requirements
COPY requirements/requirements.txt .
RUN pip3 install --no-cache-dir wheel
RUN pip3 install --no-cache-dir -r requirements.txt

FROM ubuntu:20.04 AS runner-image
RUN apt-get update && apt-get install --no-install-recommends -y python3.10 postgresql-client python3-venv && \
	apt-get clean && rm -rf /tmp/* /var/tmp/* /var/lib/apt/lists/*

#RUN useradd --create-home qrcode
RUN mkdir -p /home/guild_invoice
COPY --from=builder-image /home/guild_invoice/venv /home/guild_invoice/venv

#USER barcode
RUN mkdir /home/guild_invoice/app
WORKDIR /home/guild_invoice/app
COPY . .


# make sure all messages always reach console
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# activate virtual environment
ENV VIRTUAL_ENV=/home/barcode/venv
ENV PATH="/home/barcode/venv/bin:$PATH"