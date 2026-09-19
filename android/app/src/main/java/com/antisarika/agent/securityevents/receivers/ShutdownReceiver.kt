package com.antisarika.agent.securityevents.receivers

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import com.antisarika.agent.AntiSarikaApp
import com.antisarika.agent.core.logging.SafeLogger
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

class ShutdownReceiver : BroadcastReceiver() {
    companion object {
        private const val TAG = "ShutdownReceiver"
    }

    override fun onReceive(context: Context, intent: Intent) {
        SafeLogger.w(TAG, "Device shutdown intent intercepted: ${intent.action}")

        val app = context.applicationContext as? AntiSarikaApp ?: return
        val pendingResult = goAsync()

        CoroutineScope(Dispatchers.IO).launch {
            try {
                // 1. Capture emergency final snapshot
                app.storeAndForwardEngine.recordTelemetrySnapshot()

                // 2. Record and dispatch priority POWER_OFF_ATTEMPT event
                app.securityEventDetector.recordAndDispatchEvent(
                    eventType = "POWER_OFF_ATTEMPT",
                    severity = "CRITICAL",
                    payload = mapOf(
                        "trigger" to "ACTION_SHUTDOWN",
                        "intent_action" to (intent.action ?: "unknown")
                    ),
                    autoShiftToStolen = true
                )
            } catch (e: Exception) {
                SafeLogger.e(TAG, "Error handling shutdown event", e)
            } finally {
                pendingResult.finish()
            }
        }
    }
}
