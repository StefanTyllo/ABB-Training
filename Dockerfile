FROM python:3.12.15-slim-bookworm@sha256:2ed6491b93cd49272ee6de2b5a38440c3448360322c089fc23e370722d74179d AS runtime
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 \
    CHROME_BINARY=/opt/abb/browser/chrome-linux64/chrome \
    CHROMEDRIVER=/opt/abb/browser/chromedriver-linux64/chromedriver \
    PATH=/opt/abb/node/bin:/opt/abb/node/node_modules/.bin:$PATH \
    ABB_RUNS_DIR=/workspace/runs
RUN rm /etc/apt/sources.list.d/debian.sources && printf '%s\n' \
    'deb [check-valid-until=no] https://snapshot.debian.org/archive/debian/20261014T000000Z bookworm main' \
    'deb [check-valid-until=no] https://snapshot.debian.org/archive/debian-security/20261014T000000Z bookworm-security main' \
    > /etc/apt/sources.list && apt-get update && apt-get install -y --no-install-recommends \
    bash ca-certificates git gcc libc6-dev unzip xz-utils util-linux \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
    libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 \
    libasound2 libpango-1.0-0 libcairo2 fonts-liberation libglib2.0-0 \
    && mkdir -p /opt/abb/runtime && dpkg-query -W > /opt/abb/runtime/os-packages.lock \
    && rm -rf /var/lib/apt/lists/*
COPY docker/runtime.lock.json docker/download.py /opt/abb/runtime/
RUN python /opt/abb/runtime/download.py
COPY docker/requirements.lock /opt/abb/runtime/
RUN pip install --no-cache-dir --require-hashes -r /opt/abb/runtime/requirements.lock
COPY docker/package.json docker/package-lock.json /opt/abb/node/
RUN cd /opt/abb/node && npm ci --no-audit --no-fund && npm cache clean --force
COPY docker/playwright.json /opt/abb/runtime/playwright.json
COPY docker/abb /usr/local/bin/abb
RUN chmod 755 /usr/local/bin/abb && useradd --create-home --uid 1000 --shell /bin/bash learner \
    && mkdir -p /workspace/work /workspace/runs /workspace/export \
    && chown -R learner:learner /workspace
WORKDIR /workspace
USER learner
CMD ["sleep", "infinity"]

FROM runtime AS materials
USER root
COPY training_kit /opt/abb/materials
RUN rm -rf /opt/abb/materials/firmware/instructor /opt/abb/materials/hardware/instructor \
    /opt/abb/materials/test_team/author_checks /opt/abb/materials/hardware/tests \
    && chmod -R a-w /opt/abb/materials && ln -s /opt/abb/materials /workspace/materials
USER learner

FROM materials AS learner

FROM materials AS facilitator
USER root
COPY . /opt/abb/repo
RUN chmod -R a-w /opt/abb/repo
USER learner
