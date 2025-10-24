# Sandboxing in the Gemini CLI: A Deep Dive

Sandboxing in the Gemini CLI is a crucial security feature that isolates potentially risky operations from your host system. This guide breaks down how it works, from the high-level concepts to the nitty-gritty details in the source code.

## 🚀 Overview of Sandboxing

The primary goal of sandboxing is to create a secure barrier between the AI's operations and your local environment. This provides several key benefits:

* **Security**: Prevents accidental system damage or data loss.
* **Isolation**: Limits file system access to the project directory, protecting the rest of your system.
* **Consistency**: Ensures a reproducible environment, so commands behave the same way across different machines.
* **Safety**: Reduces the risk of working with untrusted or experimental code.

---

## 🛠️ Sandboxing Methods

The Gemini CLI employs two distinct sandboxing methods, chosen based on your operating system and configuration:

1.  **macOS Seatbelt**: A lightweight, native macOS sandboxing solution that uses the `sandbox-exec` command.
2.  **Container-based (Docker/Podman)**: A cross-platform method that offers complete process isolation by running commands inside a container, providing the highest level of security.

---

## ⚙️ How it Works: Under the Hood

When you execute a `gemini` command with sandboxing enabled, a series of steps are taken to create and manage the secure environment. The core logic for this is found in `packages/cli/src/utils/sandbox.ts`.

### In-Depth Breakdown

1.  **Activation**: Sandboxing is triggered by the `-s`/`--sandbox` flag, the `GEMINI_SANDBOX` environment variable, or a setting in `settings.json`.

2.  **Platform Detection**: The CLI checks your operating system to determine which sandboxing method to use.

3.  **Container-Based Sandboxing**:
    * **Image Verification**: The CLI ensures the required Docker or Podman image (e.g., `gemini-cli-sandbox`) is available locally. If it's missing, it attempts to pull it. This is handled by the `ensureSandboxImageIsPresent` function.
    * The **CLI defaults** to the production image when it's not in local development mode. To override this, butild your image locally and set the `GEMINI_SANDBOX_IMAGE` environment variable to your custom image name.
    * **Command Construction**: A `docker run` or `podman run` command is dynamically built with specific arguments to create the isolated environment:
        * `--rm` & `--init`: To ensure the container is removed after use and that processes are handled correctly.
        * `--workdir`: To set the container's working directory to your current project's directory.
        * `--volume`: To mount your project directory, user settings (`~/.gemini`), and other necessary paths into the container.
        * `--env`: To securely pass in environment variables like API keys and proxy settings.
    * **User Permissions on Linux**: The `shouldUseCurrentUserInSandbox` function checks if the system is Debian/Ubuntu-based. If so, it creates a user inside the container with the same UID/GID as the host user to prevent file permission errors.
    * **Execution**: The original `gemini` command is then re-executed inside this fully configured container, with the entrypoint constructed by the `entrypoint` function.

4.  **macOS Seatbelt Sandboxing**:
    * This method uses `sandbox-exec` to wrap the `gemini` command in a security profile.
    * These profiles are defined in `.sb` files and control permissions for file access and network connections. The profile is selected based on the `SEATBELT_PROFILE` environment variable.

## macOS Seatbelt Profiles

macOS users can choose from several built-in profiles by setting the `SEATBELT_PROFILE` environment variable. Each offers a different level of security:

* `permissive-open` (Default): Restricts writes outside the project directory but allows network access.
* `permissive-closed`: Same write restrictions, but **blocks all outbound network traffic**.
* `permissive-proxied`: Allows network traffic only through a local proxy at `localhost:8877`.
* `restrictive-open`: Denies most actions by default, but explicitly allows file reads and network access.
* `restrictive-closed`: The most secure profile, denying almost everything by default and **blocking all outbound network traffic**.
* `restrictive-proxied`: The same strict defaults, but allows network traffic only through a local proxy.

## 🔧 Configuration

You can enable and customize sandboxing in order of precedence:

1.  **Command Flag**: `-s` or `--sandbox`
2.  **Environment Variable**: `GEMINI_SANDBOX=true|docker|podman|sandbox-exec`
3.  **Settings File**: `"sandbox": true` in your `settings.json`

Advanced customization is available through environment variables like `SANDBOX_FLAGS` (for Docker/Podman) and `SEATBELT_PROFILE` (for macOS).

---

## Sandboxing Workflow Diagram

```mermaid
graph TD
    A[Start: gemini -s command] --> B{Sandbox enabled?};
    B -- Yes --> C{Detect OS};
    B -- No --> D[Execute command directly on host];
    C -- macOS --> E[Use macOS Seatbelt];
    C -- Linux/Windows/Other --> F[Use Container Docker/Podman];
    E --> G{SEATBELT_PROFILE set?};
    G -- Yes --> H[Load specified .sb profile];
    G -- No --> I[Load default 'permissive-open' .sb profile];
    H --> J[Run command with sandbox-exec];
    I --> J;
    F --> K{Sandbox image present?};
    K -- No --> L[Pull image from registry];
    K -- Yes --> M[Construct container command];
    L --> M;
    M --> N[Mount volumes: project dir, settings, etc.];
    N --> O[Pass environment variables: API keys, proxy, etc.];
    O --> P[Execute command inside container];
    J --> Q[End];
    P --> Q;
    D --> Q;
    ```
