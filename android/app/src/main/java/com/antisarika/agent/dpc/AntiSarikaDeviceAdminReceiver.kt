package com.antisarika.agent.dpc

import android.app.admin.DeviceAdminReceiver
import android.content.Context
import android.content.Intent
import android.widget.Toast
import com.antisarika.agent.core.logging.SafeLogger

class AntiSarikaDeviceAdminReceiver : DeviceAdminReceiver() {

    companion object {
        private const val TAG = "DeviceAdminReceiver"
    }

    override fun onEnabled(context: Context, intent: Intent) {
        super.onEnabled(context, intent)
        SafeLogger.i(TAG, "Anti-Sarika Device Admin / DPC Enabled")
    }

    override fun onDisabled(context: Context, intent: Intent) {
        super.onDisabled(context, intent)
        SafeLogger.w(TAG, "Anti-Sarika Device Admin / DPC Disabled by user/system")
    }

    override fun onLockTaskModeEntering(context: Context, intent: Intent, pkg: String) {
        super.onLockTaskModeEntering(context, intent, pkg)
        SafeLogger.i(TAG, "Entered Lock Task Mode for package: $pkg")
    }

    override fun onLockTaskModeExiting(context: Context, intent: Intent) {
        super.onLockTaskModeExiting(context, intent)
        SafeLogger.i(TAG, "Exited Lock Task Mode")
    }
}
