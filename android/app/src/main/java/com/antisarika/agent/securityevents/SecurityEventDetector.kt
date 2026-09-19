package com.antisarika.agent.securityevents

import com.antisarika.agent.core.crypto.DeviceSigner
import com.antisarika.agent.core.logging.SafeLogger
import com.antisarika.agent.core.model.SecurityState
import com.antisarika.agent.core.network.ApiClient
import com.antisarika.agent.core.storage.AntiSarikaDatabase
import com.antisarika.agent.core.storage.entities.AuditLogEntity
import com.antisarika.agent.core.storage.entities.SecurityEventEntity
import com.antisarika.agent.state.StateManager
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.text.SimpleDateFormat
import java.util.*

class SecurityEventDetector(
    private val database: AntiSarikaDatabase,
    private val apiClient: ApiClient,
    private val deviceSigner: DeviceSigner,
    private val stateManager: StateManager
) {
    companion object {
        private const val TAG = "SecurityEventDetector"
    }

    private val isoFormat = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss.SSSSSS'Z'", Locale.US).apply {
        timeZone = TimeZone.getTimeZone("UTC")
    }

    suspend fun recordAndDispatchEvent(
        eventType: String,
        severity: String = "HIGH",
        payload: Map<String, Any?> = emptyMap(),
        autoShiftToStolen: Boolean = true
    ): SecurityEventEntity? = withContext(Dispatchers.IO) {
        val config = database.deviceConfigDao().getConfig() ?: return@withContext null
        if (!config.isEnrolled) return@withContext null

        val currentSecState = stateManager.compositeState.value.securityState
        val targetSecState = if (autoShiftToStolen && currentSecState == SecurityState.NORMAL) {
            SecurityState.STOLEN
        } else {
            currentSecState
        }

        val eventId = "evt_" + UUID.randomUUID().toString()
        val nowIso = isoFormat.format(Date())
        val nonce = "evt_nonce_" + UUID.randomUUID().toString().replace("-", "").take(16)

        val entity = SecurityEventEntity(
            eventId = eventId,
            eventType = eventType,
            severity = severity,
            stateBefore = currentSecState.name,
            stateAfter = targetSecState.name,
            payloadJson = JSONObject(payload).toString(),
            timestamp = nowIso,
            nonce = nonce,
            isSynced = false
        )

        database.securityEventDao().insertEvent(entity)
        SafeLogger.i(TAG, "Recorded SecurityEvent [$eventType] severity=$severity (state $currentSecState -> $targetSecState)")

        if (targetSecState != currentSecState) {
            stateManager.updateSecurityState(targetSecState, "Triggered by security event $eventType")
        }

        database.auditLogDao().insertLog(
            AuditLogEntity(
                actor = "DEVICE",
                action = "SECURITY_EVENT_$eventType",
                details = "Severity: $severity, StateAfter: $targetSecState"
            )
        )

        // Attempt immediate dispatch
        dispatchPendingEvents()
        entity
    }

    suspend fun dispatchPendingEvents(): Int = withContext(Dispatchers.IO) {
        val config = database.deviceConfigDao().getConfig() ?: return@withContext 0
        val pending = database.securityEventDao().getPendingEvents()
        if (pending.isEmpty()) return@withContext 0

        SafeLogger.i(TAG, "Dispatching ${pending.size} pending security events...")
        var dispatchedCount = 0

        for (event in pending) {
            val payloadMap = runCatching {
                val json = JSONObject(event.payloadJson)
                val map = mutableMapOf<String, Any?>()
                val keys = json.keys()
                while (keys.hasNext()) {
                    val k = keys.next()
                    map[k] = json.opt(k)
                }
                map
            }.getOrDefault(emptyMap())

            val payloadToSign = mapOf(
                "device_id" to config.deviceId,
                "event_type" to event.eventType,
                "severity" to event.severity,
                "security_state_before" to event.stateBefore,
                "security_state_after" to event.stateAfter,
                "payload" to payloadMap,
                "device_timestamp" to event.timestamp,
                "nonce" to event.nonce
            )

            val signature = deviceSigner.signPayload(payloadToSign)

            val result = apiClient.submitSecurityEvent(
                deviceId = config.deviceId,
                eventType = event.eventType,
                severity = event.severity,
                stateBefore = event.stateBefore,
                stateAfter = event.stateAfter,
                eventPayload = payloadMap,
                timestamp = event.timestamp,
                nonce = event.nonce,
                signature = signature
            )

            if (result.isSuccess) {
                database.securityEventDao().deleteSynced(listOf(event.eventId))
                dispatchedCount++
                SafeLogger.i(TAG, "Successfully dispatched security event ${event.eventId} ($event.eventType)")
            } else {
                SafeLogger.w(TAG, "Failed to dispatch security event ${event.eventId}: ${result.exceptionOrNull()?.message}")
            }
        }
        dispatchedCount
    }
}
