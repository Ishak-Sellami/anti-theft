package com.antisarika.agent.telemetry

import com.antisarika.agent.core.crypto.DeviceSigner
import com.antisarika.agent.core.logging.SafeLogger
import com.antisarika.agent.core.model.ConnectivityState
import com.antisarika.agent.core.model.TelemetryItem
import com.antisarika.agent.core.network.ApiClient
import com.antisarika.agent.core.storage.AntiSarikaDatabase
import com.antisarika.agent.core.storage.entities.TelemetryEntity
import com.antisarika.agent.policy.RecoveryPolicyEngine
import com.antisarika.agent.state.StateManager
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.text.SimpleDateFormat
import java.util.*

class StoreAndForwardEngine(
    private val database: AntiSarikaDatabase,
    private val apiClient: ApiClient,
    private val deviceSigner: DeviceSigner,
    private val stateManager: StateManager,
    private val policyEngine: RecoveryPolicyEngine,
    private val locationTracker: LocationTracker,
    private val healthMonitor: HealthMonitor
) {
    companion object {
        private const val TAG = "StoreAndForwardEngine"
    }

    private val isoFormat = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss.SSSSSS'Z'", Locale.US).apply {
        timeZone = TimeZone.getTimeZone("UTC")
    }

    /**
     * Captures current telemetry snapshot and queues it in local encrypted Room database.
     */
    suspend fun recordTelemetrySnapshot(): TelemetryEntity = withContext(Dispatchers.IO) {
        val state = stateManager.compositeState.value
        val health = healthMonitor.getHealthSnapshot()
        val loc = locationTracker.getLastKnownLocation()

        val recordedAt = isoFormat.format(Date())
        val entity = TelemetryEntity(
            latitude = loc?.latitude ?: 0.0,
            longitude = loc?.longitude ?: 0.0,
            altitude = loc?.altitude,
            accuracy = loc?.accuracy,
            speed = loc?.speed,
            bearing = loc?.bearing,
            provider = loc?.provider ?: "health_only",
            batteryLevel = health.batteryLevel,
            powerState = state.powerState.name,
            securityState = state.securityState.name,
            connectivityState = state.connectivityState.name,
            networkMetadataJson = "{}",
            recordedAt = recordedAt,
            isSynced = false
        )

        // Check storage limits from policy
        val maxRecords = policyEngine.activePolicy.value.storageLimits.offlineQueueMaxRecords
        val currentCount = database.telemetryDao().getPendingCount()
        if (currentCount >= maxRecords) {
            val evictCount = (currentCount - maxRecords) + 10
            SafeLogger.w(TAG, "Queue limit reached ($currentCount >= $maxRecords). Evicting $evictCount oldest records.")
            database.telemetryDao().evictOldest(evictCount)
        }

        database.telemetryDao().insertTelemetry(entity)
        SafeLogger.d(TAG, "Recorded telemetry: lat=${entity.latitude}, lng=${entity.longitude}, batt=${entity.batteryLevel}%")
        entity
    }

    /**
     * Synchronizes queued telemetry batches with the backend.
     */
    suspend fun syncPendingTelemetry(): Int = withContext(Dispatchers.IO) {
        val config = database.deviceConfigDao().getConfig() ?: return@withContext 0
        if (!config.isEnrolled) return@withContext 0

        val powerPolicy = policyEngine.getCurrentPowerPolicy(stateManager.compositeState.value.powerState)
        val batchSize = powerPolicy.telemetryBatchSize.coerceAtLeast(1).coerceAtMost(50)

        val pending = database.telemetryDao().getPendingTelemetry(batchSize)
        if (pending.isEmpty()) return@withContext 0

        SafeLogger.i(TAG, "Attempting to sync batch of ${pending.size} telemetry records...")

        val itemsForPayload = pending.map { entity ->
            val item = TelemetryItem(
                latitude = entity.latitude,
                longitude = entity.longitude,
                altitude = entity.altitude,
                accuracy = entity.accuracy,
                speed = entity.speed,
                bearing = entity.bearing,
                provider = entity.provider,
                batteryLevel = entity.batteryLevel,
                powerState = entity.powerState,
                securityState = entity.securityState,
                connectivityState = entity.connectivityState,
                networkMetadata = emptyMap(),
                recordedAt = entity.recordedAt
            )
            item.toPayloadMap()
        }

        val nonce = "telem_nonce_" + UUID.randomUUID().toString().replace("-", "").take(16)
        val nowIso = isoFormat.format(Date())

        val payloadToSign = mapOf(
            "device_id" to config.deviceId,
            "items" to itemsForPayload,
            "nonce" to nonce,
            "timestamp" to nowIso
        )

        val signature = deviceSigner.signPayload(payloadToSign)

        val result = apiClient.submitTelemetryBatch(
            deviceId = config.deviceId,
            items = itemsForPayload,
            nonce = nonce,
            timestamp = nowIso,
            signature = signature
        )

        if (result.isSuccess) {
            val idsToDelete = pending.map { it.id }
            database.telemetryDao().deleteSynced(idsToDelete)
            SafeLogger.i(TAG, "Successfully synchronized and cleared ${idsToDelete.size} telemetry records from queue.")
            return@withContext idsToDelete.size
        } else {
            SafeLogger.w(TAG, "Failed to sync telemetry batch: ${result.exceptionOrNull()?.message}")
            return@withContext 0
        }
    }
}
