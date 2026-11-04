# Toolchain for the Pico SDK experiments (F-000, F-001). Built by tools/build; the experiments compile with --network none.
FROM debian:bookworm-slim@sha256:99c0b25c46d0214d5a2091092e7908907dcaecd6a962cde0ac700acee222b6f3
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
      cmake make gcc-arm-none-eabi libnewlib-arm-none-eabi libstdc++-arm-none-eabi-newlib \
      build-essential git ca-certificates python3 pkg-config \
    && rm -rf /var/lib/apt/lists/*
# Pico SDK at a fixed tag, with TinyUSB (the only submodule the experiments need).
ARG PICO_SDK_TAG=2.3.1
RUN git clone --quiet --depth 1 --branch "$PICO_SDK_TAG" https://github.com/raspberrypi/pico-sdk.git /opt/pico-sdk \
    && git -C /opt/pico-sdk submodule update --init --depth 1 lib/tinyusb
ENV PICO_SDK_PATH=/opt/pico-sdk
# picotool at the same tag, installed system-wide so the SDK finds it instead of fetching it at configure time
# (the experiments build without network). Without libusb: it only post-processes binaries, never flashes.
RUN git clone --quiet --depth 1 --branch "$PICO_SDK_TAG" https://github.com/raspberrypi/picotool.git /tmp/picotool \
    && cmake -S /tmp/picotool -B /tmp/picotool/build -DPICOTOOL_NO_LIBUSB=1 -DPICOTOOL_FLAT_INSTALL=0 >/dev/null \
    && cmake --build /tmp/picotool/build -j"$(nproc)" >/dev/null \
    && cmake --install /tmp/picotool/build --prefix /usr/local >/dev/null \
    && rm -rf /tmp/picotool
WORKDIR /src
