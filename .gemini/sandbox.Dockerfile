# Documentation:
#  - https://github.com/google-gemini/gemini-cli/blob/main/Dockerfile
#  - https://github.com/google-gemini/gemini-cli/blob/main/docs/get-started/configuration.md#sandboxing
FROM us-docker.pkg.dev/gemini-code-dev/gemini-cli/sandbox:0.10.0

# The official image uses `node` as the default user, switch
# to `root` to install packages then switch back later.
USER root

ARG SANDBOX_NAME="gemini-ctf-sandbox"
ENV SANDBOX="$SANDBOX_NAME"

ARG PYTHON_VERSION=3.12

ENV DEBIAN_FRONTEND=noninteractive \
    TZ=UTC \
    LANG=C.UTF-8 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    SHELL=/bin/bash \
    VENV_PATH=/workspace/venv

ENV PATH="$VENV_PATH/bin:$PATH"

WORKDIR /workspace


# This layer is the most stable and will be cached.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        # Add-apt-repository dependencies
        gnupg \
        debian-keyring \
        # Build essentials & core utilities
        build-essential \
        cmake \
        pkg-config \
        git \
        curl \
        wget \
        # Python core
        python3 \
        python3-dev \
        python3-venv \
        python3-pip && \
    # FIX: Add contrib & non-free repos by creating a new sources file. This is more robust.
    echo "deb http://deb.debian.org/debian bookworm main contrib non-free" > /etc/apt/sources.list.d/custom.list && \
    echo "deb http://deb.debian.org/debian-security bookworm-security main contrib non-free" >> /etc/apt/sources.list.d/custom.list && \
    apt-get update


# Each block is a separate layer for better caching and easier debugging.
# If one fails, you only re-run that specific block.

# Install Network Tools
RUN apt-get install -y --no-install-recommends \
    netcat-openbsd \
    nmap \
    socat \
    tcpdump \
    tshark

# Install Archive & Forensics Tools
RUN apt-get install -y --no-install-recommends \
    zip \
    unzip \
    unrar \
    p7zip-full \
    bzip2 \
    gzip \
    tar \
    zstd \
    binutils \
    binwalk \
    exiftool \
    file \
    foremost \
    minimodem \
    qpdf \
    steghide \
    stegsnow \
    xxd

# Install Reverse Engineering & Web Tools
RUN apt-get install -y --no-install-recommends \
    gdb \
    gdb-multiarch \
    ltrace \
    strace \
    icoutils \
    gobuster \
    hashcat \
    john \
    sqlmap \
    openssl \
    sqlite3

# Install Misc Utilities
RUN apt-get install -y --no-install-recommends \
    jq \
    ripgrep \
    fd-find \
    bat \
    htop \
    vim \
    nano \
    less \
    tree \
    git \
    procps \
    sudo \
    fzf \
    zsh \
    man-db \
    dnsutils

# Install radare2 from source to get the latest version
RUN git clone https://github.com/radareorg/radare2 && \
    radare2/sys/install.sh

# Clean up apt cache to reduce image size
RUN apt-get clean && \
    rm -rf /var/lib/apt/lists/*


# Create and activate the Python virtual environment
RUN python3 -m venv $VENV_PATH

# Upgrade pip first
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

COPY . /workspace
RUN pip install -e ".[all]"


# Useful aliases
RUN echo 'alias ll="ls -lah"' >> ~/.bashrc && \
    echo 'alias python="python3"' >> ~/.bashrc && \
    echo 'alias pip="pip3"' >> ~/.bashrc

# # Persist bash history.
# RUN SNIPPET="export PROMPT_COMMAND='history -a' && export HISTFILE=/commandhistory/.bash_history" \
#   && mkdir /commandhistory \
#   && touch /commandhistory/.bash_history \
#   && chown -R $USERNAME /commandhistory

# Set `DEVCONTAINER` environment variable to help with orientation
ENV DEVCONTAINER=true

# Networking
EXPOSE 8000 4444 5555 8080 9000

# Health check to ensure container is responsive
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "print('healthy')" || exit 1

# Switch back to non-root user
# USER node

# Default entrypoint when none specified
CMD ["gemini"]
