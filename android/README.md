# Anti-Sarika Android Agent (v0.1)

The Anti-Sarika Android Agent is a security-hardened device agent designed to maximize device recoverability during complex theft scenarios.

---

## Key Capabilities

1. **Hardware-Backed Cryptographic Identity**:
   - `ECDSA SecP256r1` (`SHA256withECDSA`) managed via `AndroidKeyStore` (Hardware TEE / StrongBox).
   - Generates deterministic, canonical JSON payloads (`CanonicalJson`) matching the backend control plane.
   - Public key export formatted as PEM with SHA-256 fingerprinting.

2. **Three-Dimensional State Engine**:
   - **Security State**: `NORMAL`, `PROTECTED`, `STOLEN`, `RECOVERY`
   - **Connectivity State**: `ONLINE`, `DEGRADED`, `OFFLINE`
   - **Power State**: `NORMAL`, `LOW`, `CRITICAL`

3. **Store-and-Forward Telemetry**:
   - Encrypted Room SQLite local persistence for location fixes, battery levels, network identifiers, and timestamps.
   - Queue size limits with automatic LRU eviction of unessential records.
   - Automatic batch sync with device-signed payloads upon network reconnection.

4. **Remote Command Engine**:
   - 7-step verification: Target Device ID, Supported Type, TTL expiration, Replay nonce prevention, Backend signature verification, State constraints.
   - Device-signed execution receipts (`CommandAckRequest`).

5. **Device Policy Controller (DPC / Device Owner)**:
   - Blocks factory reset attempts via `UserManager.DISALLOW_FACTORY_RESET`.
   - Prevents uninstallation via `DevicePolicyManager.setUninstallBlocked`.
   - Disables keyguard status bar / quick settings pulldown in protected modes.
   - Handles remote lock and authorized owner-initiated wipe.

6. **Anti-Theft STOLEN Mode Evidence Capture**:
   - Activated **ONLY** when `Security State == STOLEN` or `RECOVERY`.
   - Generates SHA-256 integrity hash before storage/transmission.
   - Ingests metadata and chain-of-custody records to `/api/v1/evidence`.
   - Backend access is strictly restricted to verified device owners (`403 Forbidden` for non-owners).

7. **Lifecycle & Boot Recovery**:
   - `BootReceiver` restores background workers and queues after device restart.
   - `ShutdownReceiver` intercepts `ACTION_SHUTDOWN` to capture emergency telemetry and dispatch priority `POWER_OFF_ATTEMPT` alerts.

---

## Device Owner Provisioning (via ADB)

To set Anti-Sarika as Device Owner on a fresh or test device:

```bash
adb shell dpm set-device-owner com.antisarika.agent/.dpc.AntiSarikaDeviceAdminReceiver
```
