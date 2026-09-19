# Anti-Sarika Backend Control Plane (v0.1)

The Anti-Sarika Backend is the trusted control plane of the Anti-Sarika device recovery and anti-theft platform.

---

## 1. Features & Capabilities

- **User Authentication & Authorization:** Multi-role access control (`OWNER`, `ADMIN`, `AUDITOR`, `INVESTIGATOR`), secure bcrypt password hashing, and signed JWT access tokens.
- **Cryptographic Device Identity:** Asymmetric key registration (`ECDSA SecP256r1` / `Ed25519`), device public key fingerprinting (`SHA-256`), and digital signature verification for proof of private key possession.
- **Three-Dimensional Device State Model:** Independent, orthogonal tracking of:
  - **Security State:** `NORMAL`, `PROTECTED`, `STOLEN`, `RECOVERY`
  - **Connectivity State:** `ONLINE`, `DEGRADED`, `OFFLINE`
  - **Power State:** `NORMAL`, `LOW`, `CRITICAL`
- **Replay Attack & Timestamp Protection:** Per-request cryptographic nonces and clock-skew tolerance validation preventing replay or duplicate execution.
- **Dynamic RecoveryPolicy Engine:** Multi-tier telemetry configuration (location interval, fastest interval, accuracy mode, heartbeat rate, battery thresholds, storage limits) dynamically managed per power/security state.
- **Store-and-Forward Telemetry Ingestion:** Batch location ingestion preserving device-side `recorded_at` timestamps alongside server `received_at` timestamps for offline buffering.
- **Security Events & Threat Escalation:** Signed security event ingestion (`POWER_OFF_ATTEMPT`, `FACTORY_RESET_ATTEMPT`, `SIM_SWAP`, etc.) with automatic state escalation to `STOLEN`.
- **Remote Command System:** Cryptographically signed remote commands with nonces, expiration TTL, and signed execution receipts (`PENDING`, `ACKNOWLEDGED`, `EXECUTED`, `FAILED`, `EXPIRED`).
- **Tamper-Evident Audit Trail:** Append-only hash-chained activity log with $prev\_hash \rightarrow entry\_hash$ verification.
- **Evidence Metadata Foundation:** Storage of metadata, SHA-256 integrity hashes, and chain-of-custody notes for authorized forensic captures.
- **Real-Time WebSocket Updates:** Authenticated WebSocket bridge (`/api/v1/ws`) for instant dashboard notifications of state changes, security alerts, and live locations.

---

## 2. Quick Start

### Prerequisites
- Python 3.12+ (tested on Python 3.14)
- SQLite (default for development/tests) or PostgreSQL 16+

### Installation
```bash
cd backend
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

### Running Migrations
```bash
alembic upgrade head
```

### Starting Development Server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Interactive API documentation will be available at:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`
- **OpenAPI JSON:** `http://localhost:8000/openapi.json`

---

## 3. Running Automated Tests

```bash
pytest
```

---

## 4. API Endpoints Reference

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/auth/register` | Register new user account | No |
| `POST` | `/api/v1/auth/login` | Authenticate and obtain JWT token | No |
| `GET` | `/api/v1/auth/me` | Get authenticated user profile | Bearer JWT |
| `POST` | `/api/v1/devices/enroll/initiate` | Generate pairing token & get backend public key | Bearer JWT |
| `POST` | `/api/v1/devices/enroll/complete` | Complete device enrollment with signed payload | Device Sig |
| `GET` | `/api/v1/devices` | List owned devices | Bearer JWT |
| `GET` | `/api/v1/devices/{id}` | Get detailed device status | Bearer JWT |
| `PATCH` | `/api/v1/devices/{id}/security-state` | Update device security state dimension | Bearer JWT |
| `POST` | `/api/v1/devices/heartbeat` | Submit signed periodic heartbeat | Device Sig |
| `POST` | `/api/v1/telemetry/batch` | Ingest batch telemetry (online or buffered) | Device Sig |
| `GET` | `/api/v1/telemetry/{id}/history` | Query location history | Bearer JWT |
| `POST` | `/api/v1/events` | Ingest signed security event | Device Sig |
| `GET` | `/api/v1/events/{id}` | Query device security events | Bearer JWT |
| `POST` | `/api/v1/commands` | Issue signed remote command | Bearer JWT |
| `POST` | `/api/v1/commands/ack` | Submit signed command execution result | Device Sig |
| `GET` | `/api/v1/commands/{id}/pending` | Poll unexpired pending commands | None / Device |
| `GET` | `/api/v1/policies` | List RecoveryPolicies | Bearer JWT |
| `POST` | `/api/v1/policies` | Create custom RecoveryPolicy | Admin JWT |
| `POST` | `/api/v1/evidence` | Ingest evidence metadata & SHA-256 hash | Device Sig |
| `GET` | `/api/v1/evidence/{id}` | Query chain-of-custody evidence records | Bearer JWT |
| `GET` | `/api/v1/audit` | System-wide tamper-evident audit logs | Admin JWT |
| `GET` | `/api/v1/audit/device/{id}` | Device-scoped audit logs | Bearer JWT |
| `WS` | `/api/v1/ws` | Authenticated real-time WebSocket channel | Token Query |
