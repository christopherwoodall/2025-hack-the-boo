# Wire Whispered

## Setup

### Step 1
Update Wireshark to version v4.6.0+ or higher. Open the pcap and go to `Edit` -> `Preferences` -> `Protocols` -> `TLS` and set the `(Pre)-Master-Secret log filename` to the provided `tls-lsa.log` file.

### Step 2
Export the RDP stream by going to `File` -> `Export PDUs to file` -> select `OSI Layer 7` -> `Ok`. Then save the new stream as pdu.pcap.

Or in BASH:

```bash
tshark -r capture.pcap -o "tls.keylog_file:$(pwd)/tls-lsa.log" -U "OSI layer 7" -w pdu.pcap 2>&1
```

### Step 3
Install PyRDP from the git repository:

```bash
git clone https://github.com/GoSecure/pyrdp.git
cd pyrdp
pip install -e ".[all]"
```

### Step 4
Run PyRDP with the exported pdu.pcap file:

```bash
pyrdp-convert -s tls-lsa.log -o ./out pdu.pcap
```

### Step 5
Replaye the RDP session:

```bash
pyrdp-replay -d ./out
```

---

## Flags

1. What is the username affected by the spray?
**ANSWER:** `stoneheart_keeper52` (packet 3992)
2. What is the password for that username
**ANSWER:** `Mlamp!J1`
3. What is the website the victim is currently browsing. (TLD only: google.com)
**ANSWER:** thedfirreport.com
4. What is the username:password combination for website `http://barrowick.htb`
**ANSWER:** candle_eyed:AshWitness_99@Tomb

---

![solve](solve.png)
