package com.antisarika.agent.core.model

import kotlinx.serialization.Serializable

@Serializable
enum class SecurityState {
    NORMAL,
    PROTECTED,
    STOLEN,
    RECOVERY
}

@Serializable
enum class ConnectivityState {
    ONLINE,
    DEGRADED,
    OFFLINE
}

@Serializable
enum class PowerState {
    NORMAL,
    LOW,
    CRITICAL
}

@Serializable
data class DeviceCompositeState(
    val securityState: SecurityState,
    val connectivityState: ConnectivityState,
    val powerState: PowerState
)
