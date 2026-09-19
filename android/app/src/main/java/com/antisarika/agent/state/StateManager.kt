package com.antisarika.agent.state

import com.antisarika.agent.core.logging.SafeLogger
import com.antisarika.agent.core.model.ConnectivityState
import com.antisarika.agent.core.model.DeviceCompositeState
import com.antisarika.agent.core.model.PowerState
import com.antisarika.agent.core.model.SecurityState
import com.antisarika.agent.core.storage.AntiSarikaDatabase
import com.antisarika.agent.core.storage.entities.AuditLogEntity
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch

class StateManager(
    private val database: AntiSarikaDatabase,
    private val scope: CoroutineScope
) {
    companion object {
        private const val TAG = "StateManager"
    }

    private val _compositeState = MutableStateFlow(
        DeviceCompositeState(
            securityState = SecurityState.NORMAL,
            connectivityState = ConnectivityState.OFFLINE,
            powerState = PowerState.NORMAL
        )
    )
    val compositeState: StateFlow<DeviceCompositeState> = _compositeState

    init {
        scope.launch(Dispatchers.IO) {
            val config = database.deviceConfigDao().getConfig()
            if (config != null) {
                val secState = runCatching { SecurityState.valueOf(config.securityState) }.getOrDefault(SecurityState.NORMAL)
                val connState = runCatching { ConnectivityState.valueOf(config.connectivityState) }.getOrDefault(ConnectivityState.OFFLINE)
                val pwrState = runCatching { PowerState.valueOf(config.powerState) }.getOrDefault(PowerState.NORMAL)

                _compositeState.value = DeviceCompositeState(secState, connState, pwrState)
                SafeLogger.i(TAG, "Restored state from database: $secState + $connState + $pwrState")
            }
        }
    }

    fun updateSecurityState(newState: SecurityState, reason: String? = null) {
        val current = _compositeState.value
        if (current.securityState == newState) return

        SafeLogger.i(TAG, "Transitioning SecurityState: ${current.securityState} -> $newState (reason: $reason)")
        _compositeState.value = current.copy(securityState = newState)

        scope.launch(Dispatchers.IO) {
            val config = database.deviceConfigDao().getConfig()
            if (config != null) {
                database.deviceConfigDao().updateConfig(config.copy(securityState = newState.name))
                database.auditLogDao().insertLog(
                    AuditLogEntity(
                        actor = "DEVICE",
                        action = "SECURITY_STATE_CHANGED",
                        details = "From: ${current.securityState} To: $newState Reason: $reason"
                    )
                )
            }
        }
    }

    fun updateConnectivityState(newState: ConnectivityState) {
        val current = _compositeState.value
        if (current.connectivityState == newState) return

        _compositeState.value = current.copy(connectivityState = newState)
        scope.launch(Dispatchers.IO) {
            val config = database.deviceConfigDao().getConfig()
            if (config != null) {
                database.deviceConfigDao().updateConfig(config.copy(connectivityState = newState.name))
            }
        }
    }

    fun updatePowerState(batteryLevel: Int?, isCharging: Boolean) {
        val calculatedPowerState = when {
            isCharging || batteryLevel == null -> PowerState.NORMAL
            batteryLevel < 10 -> PowerState.CRITICAL
            batteryLevel <= 20 -> PowerState.LOW
            else -> PowerState.NORMAL
        }

        val current = _compositeState.value
        if (current.powerState != calculatedPowerState) {
            SafeLogger.i(TAG, "PowerState shifted: ${current.powerState} -> $calculatedPowerState (battery: $batteryLevel%)")
            _compositeState.value = current.copy(powerState = calculatedPowerState)
            scope.launch(Dispatchers.IO) {
                val config = database.deviceConfigDao().getConfig()
                if (config != null) {
                    database.deviceConfigDao().updateConfig(config.copy(powerState = calculatedPowerState.name))
                }
            }
        }
    }
}
