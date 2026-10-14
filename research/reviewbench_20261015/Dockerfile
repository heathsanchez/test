FROM golang:1.25-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends python3 git ca-certificates && rm -rf /var/lib/apt/lists/*
COPY reviewer.py /opt/mathgraph-check/reviewer.py
ENTRYPOINT ["python3", "/opt/mathgraph-check/reviewer.py"]
