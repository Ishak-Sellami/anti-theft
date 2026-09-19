package com.antisarika.agent.background

import android.content.Context
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import com.antisarika.agent.AntiSarikaApp
import com.antisarika.agent.core.logging.SafeLogger

class TelemetrySyncWorker(
    appContext: Context,
    workerParams: WorkerParameters
) : CoroutineWorker(appContext, workerParams) {

    companion object {
        private const val TAG = "TelemetrySyncWorker"
    }

    override suspend fun doWork(): Result {
        val app = applicationContext as? AntiSarikaApp ?: return Result.failure()
        return try {
            // 1. Record snapshot
            app.storeAndForwardEngine.recordTelemetrySnapshot()

            // 2. Sync pending telemetry queue
            val synced = app.storeAndForwardEngine.syncPendingTelemetry()

            // 3. Sync pending security events
            app.securityEventDetector.dispatchPendingEvents()

            // 4. Poll and execute pending commands
            app.commandManager.pollAndProcessPendingCommands()

            SafeLogger.i(TAG, "TelemetrySyncWorker completed. Synced $synced records.")
            Result.success()
        } catch (e: Exception) {
            SafeLogger.e(TAG, "Error in TelemetrySyncWorker", e)
            Result.retry()
        }
    }
}
