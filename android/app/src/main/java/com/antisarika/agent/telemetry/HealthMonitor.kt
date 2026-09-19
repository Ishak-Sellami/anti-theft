package com.antisarika.agent.telemetry

import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.BatteryManager
import android.os.Build
import android.os.SystemClock

data class DeviceHealthSnapshot(
    val batteryLevel: Int?,
    val isCharging: Boolean,
    val batteryTemperature: Float?,
    val uptimeSeconds: Long,
    val osVersion: String,
    val manufacturer: String,
    val model: String
)

class HealthMonitor(private val context: Context) {

    fun getHealthSnapshot(): DeviceHealthSnapshot {
        val batteryIntent = context.registerReceiver(
            null,
            IntentFilter(Intent.ACTION_BATTERY_CHANGED)
        )

        val level = batteryIntent?.getIntExtra(BatteryManager.EXTRA_LEVEL, -1) ?: -1
        val scale = batteryIntent?.getIntExtra(BatteryManager.EXTRA_SCALE, -1) ?: -1
        val batteryLevel = if (level >= 0 && scale > 0) (level * 100) / scale else null

        val status = batteryIntent?.getIntExtra(BatteryManager.EXTRA_STATUS, -1) ?: -1
        val isCharging = status == BatteryManager.BATTERY_STATUS_CHARGING ||
                status == BatteryManager.BATTERY_STATUS_FULL

        val tempRaw = batteryIntent?.getIntExtra(BatteryManager.EXTRA_TEMPERATURE, -1) ?: -1
        val batteryTemp = if (tempRaw > 0) tempRaw / 10.0f else null

        val uptimeSec = SystemClock.elapsedRealtime() / 1000

        return DeviceHealthSnapshot(
            batteryLevel = batteryLevel,
            isCharging = isCharging,
            batteryTemperature = batteryTemp,
            uptimeSeconds = uptimeSec,
            osVersion = "Android ${Build.VERSION.RELEASE} (API ${Build.VERSION.SDK_INT})",
            manufacturer = Build.MANUFACTURER,
            model = Build.MODEL
        )
    }
}
