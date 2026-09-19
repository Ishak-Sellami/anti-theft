package com.antisarika.agent.background

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.IBinder
import androidx.core.app.NotificationCompat
import com.antisarika.agent.AntiSarikaApp
import com.antisarika.agent.core.logging.SafeLogger
import com.antisarika.agent.core.model.SecurityState
import kotlinx.coroutines.*

class AgentForegroundService : Service() {

    companion object {
        private const val TAG = "AgentForegroundService"
        private const val CHANNEL_ID = "anti_sarika_service_channel"
        private const val NOTIFICATION_ID = 9001

        fun startService(context: Context) {
            val intent = Intent(context, AgentForegroundService::class.java)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                context.startForegroundService(intent)
            } else {
                context.startService(intent)
            }
        }

        fun stopService(context: Context) {
            val intent = Intent(context, AgentForegroundService::class.java)
            context.stopService(intent)
        }
    }

    private val serviceScope = CoroutineScope(Dispatchers.IO + SupervisorJob())
    private var trackingJob: Job? = null

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
        startForeground(NOTIFICATION_ID, buildNotification("Anti-Sarika Security Protection Active"))
        startEscalatedLoop()
    }

    private fun startEscalatedLoop() {
        val app = applicationContext as? AntiSarikaApp ?: return
        trackingJob = serviceScope.launch {
            while (isActive) {
                try {
                    val secState = app.stateManager.compositeState.value.securityState
                    val pwrState = app.stateManager.compositeState.value.powerState
                    val policy = app.policyEngine.getCurrentPowerPolicy(pwrState)

                    // Record snapshot & sync
                    app.storeAndForwardEngine.recordTelemetrySnapshot()
                    app.storeAndForwardEngine.syncPendingTelemetry()
                    app.securityEventDetector.dispatchPendingEvents()
                    app.commandManager.pollAndProcessPendingCommands()

                    // If in STOLEN mode, trigger evidence capture periodically
                    if (secState == SecurityState.STOLEN) {
                        app.evidenceCaptureManager.captureEvidence(
                            captureType = com.antisarika.agent.core.model.EvidenceType.AMBIENT_RF,
                            notes = "Background STOLEN periodic sweep"
                        )
                    }

                    val interval = policy.locationIntervalMs.coerceAtLeast(5000L)
                    delay(interval)
                } catch (e: Exception) {
                    SafeLogger.e(TAG, "Error in escalated foreground loop", e)
                    delay(15000L)
                }
            }
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        trackingJob?.cancel()
        serviceScope.cancel()
        SafeLogger.i(TAG, "AgentForegroundService destroyed")
    }

    override fun onBind(intent: Intent?): IBinder? = null

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "Anti-Sarika Protection",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "Background protection and recovery services"
            }
            val manager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
            manager.createNotificationChannel(channel)
        }
    }

    private fun buildNotification(text: String): Notification {
        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("Device Protection Active")
            .setContentText(text)
            .setSmallIcon(android.R.drawable.ic_lock_lock)
            .setOngoing(true)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .build()
    }
}
