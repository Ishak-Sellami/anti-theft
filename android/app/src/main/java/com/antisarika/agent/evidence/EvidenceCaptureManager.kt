package com.antisarika.agent.evidence

import com.antisarika.agent.core.crypto.DeviceSigner
import com.antisarika.agent.core.logging.SafeLogger
import com.antisarika.agent.core.model.EvidenceType
import com.antisarika.agent.core.model.SecurityState
import com.antisarika.agent.core.network.ApiClient
import com.antisarika.agent.core.storage.AntiSarikaDatabase
import com.antisarika.agent.core.storage.entities.AuditLogEntity
import com.antisarika.agent.core.storage.entities.EvidenceEntity
import com.antisarika.agent.state.StateManager
import com.antisarika.agent.telemetry.HealthMonitor
import com.antisarika.agent.telemetry.LocationTracker
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.text.SimpleDateFormat
import java.util.*

class EvidenceCaptureManager(
    private val database: AntiSarikaDatabase,
    private val apiClient: ApiClient,
    private val deviceSigner: DeviceSigner,
    private val stateManager: StateManager,
    private val evidenceStorage: EvidenceStorage,
    private val locationTracker: LocationTracker,
    private val healthMonitor: HealthMonitor
) {
    companion object {
        private const val TAG = "EvidenceCaptureManager"
    }

    private val isoFormat = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss.SSSSSS'Z'", Locale.US).apply {
        timeZone = TimeZone.getTimeZone("UTC")
    }

    /**
     * Captures an evidence artifact.
     * Enforces STRICT policy check: Must ONLY capture when SecurityState is STOLEN or RECOVERY.
     */
    suspend fun captureEvidence(
        captureType: EvidenceType,
        eventId: String? = null,
        notes: String? = null
    ): EvidenceEntity? = withContext(Dispatchers.IO) {
        val currentState = stateManager.compositeState.value.securityState
        if (currentState != SecurityState.STOLEN && currentState != SecurityState.RECOVERY) {
            SafeLogger.w(TAG, "Evidence capture blocked: Device is not in STOLEN/RECOVERY mode (current: $currentState)")
            return@withContext null
        }

        val config = database.deviceConfigDao().getConfig() ?: return@withContext null
        if (!config.isEnrolled) return@withContext null

        val evidenceId = "ev_" + UUID.randomUUID().toString()
        val loc = locationTracker.getLastKnownLocation()
        val health = healthMonitor.getHealthSnapshot()
        val nowIso = isoFormat.format(Date())

        // Collect forensic evidence bundle
        val evidencePayload = JSONObject().apply {
            put("evidence_id", evidenceId)
            put("device_id", config.deviceId)
            put("capture_type", captureType.name)
            put("timestamp", nowIso)
            put("latitude", loc?.latitude ?: 0.0)
            put("longitude", loc?.longitude ?: 0.0)
            put("accuracy", loc?.accuracy)
            put("battery_level", health.batteryLevel)
            put("is_charging", health.isCharging)
            put("uptime_seconds", health.uptimeSeconds)
            put("notes", notes ?: "Auto-captured during STOLEN recovery")
        }

        val rawBytes = evidencePayload.toString().toByteArray(Charsets.UTF_8)
        val integrityHash = evidenceStorage.computeSha256(rawBytes)
        val storedFile = evidenceStorage.storeEvidenceBytes(evidenceId, rawBytes, "json")

        val nonce = "ev_nonce_" + UUID.randomUUID().toString().replace("-", "").take(16)
        val storageRef = "local://${storedFile.absolutePath}"

        val entity = EvidenceEntity(
            evidenceId = evidenceId,
            eventId = eventId,
            captureType = captureType.name,
            integrityHash = integrityHash,
            localFilePath = storedFile.absolutePath,
            mimeType = "application/json",
            fileSizeBytes = rawBytes.size.toLong(),
            notes = notes,
            timestamp = nowIso,
            nonce = nonce,
            isSynced = false
        )

        database.evidenceDao().insertEvidence(entity)
        SafeLogger.i(TAG, "Captured evidence [$captureType] hash=$integrityHash (${rawBytes.size} bytes)")

        database.auditLogDao().insertLog(
            AuditLogEntity(
                actor = "DEVICE",
                action = "EVIDENCE_CAPTURED",
                details = "Type: $captureType, Hash: $integrityHash, StorageRef: $storageRef"
            )
        )

        // Attempt metadata dispatch to backend
        syncPendingEvidence()
        entity
    }

    suspend fun syncPendingEvidence(): Int = withContext(Dispatchers.IO) {
        val config = database.deviceConfigDao().getConfig() ?: return@withContext 0
        val pending = database.evidenceDao().getPendingEvidence()
        if (pending.isEmpty()) return@withContext 0

        SafeLogger.i(TAG, "Syncing ${pending.size} pending evidence records...")
        var syncedCount = 0

        for (item in pending) {
            val payloadToSign = mutableMapOf<String, Any?>(
                "device_id" to config.deviceId,
                "event_id" to item.eventId,
                "capture_type" to item.captureType,
                "integrity_hash" to item.integrityHash,
                "storage_ref" to item.localFilePath,
                "mime_type" to item.mimeType,
                "device_timestamp" to item.timestamp,
                "nonce" to item.nonce
            )

            val signature = deviceSigner.signPayload(payloadToSign)

            val result = apiClient.submitEvidenceMetadata(
                deviceId = config.deviceId,
                eventId = item.eventId,
                captureType = item.captureType,
                integrityHash = item.integrityHash,
                storageRef = item.localFilePath,
                mimeType = item.mimeType,
                fileSizeBytes = item.fileSizeBytes,
                notes = item.notes,
                timestamp = item.timestamp,
                nonce = item.nonce,
                signature = signature
            )

            if (result.isSuccess) {
                database.evidenceDao().markSynced(item.evidenceId)
                syncedCount++
                SafeLogger.i(TAG, "Evidence metadata synced successfully: ${item.evidenceId}")
            } else {
                SafeLogger.w(TAG, "Failed to sync evidence metadata: ${result.exceptionOrNull()?.message}")
            }
        }
        syncedCount
    }
}
