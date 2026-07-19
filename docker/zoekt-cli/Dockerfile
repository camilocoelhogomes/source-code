# Zoekt index CLI sidecar (T36) — linux/amd64 only (ENG-006).
# Provides ``zoekt-index`` missing from sourcegraph/zoekt:latest webserver image.
# syntax=docker/dockerfile:1.7
FROM --platform=linux/amd64 golang:1.26-alpine AS builder

ENV GOTOOLCHAIN=auto \
    CGO_ENABLED=0

RUN apk add --no-cache ca-certificates git

WORKDIR /src
RUN git clone --depth 1 https://github.com/sourcegraph/zoekt.git .

RUN go build -trimpath -ldflags "-s -w" -o /out/zoekt-index ./cmd/zoekt-index

FROM --platform=linux/amd64 alpine:3.20

RUN apk add --no-cache ca-certificates git

COPY --from=builder /out/zoekt-index /usr/local/bin/zoekt-index

USER nobody
WORKDIR /home/nobody

CMD ["sleep", "infinity"]
