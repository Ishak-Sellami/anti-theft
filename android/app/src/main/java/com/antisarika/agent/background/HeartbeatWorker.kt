package com.antisarika.agent.background

import android.content.Context
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import com.antisarika.agent.AntiSarikaApp
import com.antisarika.agent.core.logging.SafeLogger
import java.text.SimpleDateFormat
import java.util.*

class HeartbeatWorker(
    appContext: Context,
    workerParams: WorkerParameters
) : CoroutineWorker(appContext, workerParams) {

    companion object {
        private const val TAG = "HeartbeatWorker"
    }

    private val isoFormat = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss.SSSSSS'Z'", Locale.US).apply {
        timeZone = TimeZone.getTimeZone("UTC")
    }

    override suspend fun doWork(): Result {
        val app = applicationContext as? AntiSarikaApp ?: return Result.failure()
        return try {
            val config = app.database.deviceConfigDao().getConfig() ?: return Result.success()
            if (!config.isEnrolled) return Result.success()

            val health = app.healthMonitor.getHealthSnapshot()
            val state = app.stateManager.compositeState.value

            // Update power state in state manager
            app.stateManager.updatePowerState(health.batteryLevel, health.isCharging)

            val nonce = "hb_nonce_" + UUID.randomUUID().toString().replace("-", "").take(16)
            val nowIso = isoFormat.format(Date())

            val payloadToSign = mutableMapOf<String, Any?>(
                "device_id" to config.deviceId,
                "battery_level" to health.batteryLevel,
                "is_charging" to health.isCharging,
                "connectivity_state" to state.connectivityState.name,
                "nonce" to nonce,
                "timestamp" to nowIso
            )

            val signature = app.deviceSigner.signPayload(payloadToSign)

            val response = app.apiClient.sendHeartbeat(
                deviceId = config.deviceId,
                batteryLevel = health.batteryLevel,
                isCharging = health.isCharging,
                connectivityState = state.connectivityState,
                nonce = nonce,
                timestamp = nowIso,
                signature = signature
            )

            if (response.isSuccess) {
                SafeLogger.i(TAG, "Heartbeat sent successfully.")
                Result.success()
            } else {
                SafeLogger.w(TAG, "Heartbeat delivery failed: ${response.exceptionOrNull()?.message}")
                Result.retry()
            }
        } catch (e: Exception) {
            SafeLogger.e(TAG, "Error executing HeartbeatWorker", e)
            Result.retry()
        }
    }
}
