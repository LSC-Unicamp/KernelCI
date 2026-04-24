FROM debian:bookworm
RUN apt-get update && apt-get install -y --no-install-recommends \
    git ca-certificates build-essential bc bison flex make rsync ccache \
    libssl-dev libelf-dev libncurses-dev dwarves python3 python3-pip \
    gcc-riscv64-linux-gnu g++-riscv64-linux-gnu clang lld llvm \
    device-tree-compiler kmod xz-utils tar curl wget file && \
    rm -rf /var/lib/apt/lists/*
ENV CCACHE_DIR=/ccache
WORKDIR /work
COPY build-kernel.sh /usr/local/bin/build-kernel.sh
RUN chmod +x /usr/local/bin/build-kernel.sh
