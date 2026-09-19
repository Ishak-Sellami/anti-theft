package com.antisarika.agent.securityevents.receivers

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import com.antisarika.agent.AntiSarikaApp
import com.antisarika.agent.core.logging.SafeLogger
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

class BootReceiver : BroadcastReceiver() {
    companion object {
        private const val TAG = "BootReceiver"
    }

    override fun onReceive(context: Context, intent: Intent) {
        val action = intent.action
        SafeLogger.i(TAG, "Received broadcast intent: $action")

        val app = context.applicationContext as? AntiSarikaApp ?: return
        CoroutineScope(Dispatchers.IO).launch {
            try {
                // Trigger boot security event
                app.securityEventDetector.recordAndDispatchEvent(
                    eventType = "DEVICE_BOOT_COMPLETED",
                    severity = "LOW",
                    payload = mapOf("intent_action" to (action ?: "unknown")),
                    autoShiftToStolen = false
                )
                // Sync pending telemetry & commands
                app.storeAndForwardEngine.syncPendingTelemetry()
                app.commandManager.pollAndProcessPendingCommands()
            } catch (e: Exception) {
                SafeLogger.e(TAG, "Error handling boot recovery", e)
            }
        }
    }
}
