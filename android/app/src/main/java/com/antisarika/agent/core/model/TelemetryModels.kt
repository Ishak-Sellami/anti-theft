package com.antisarika.agent.core.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.JsonObject

@Serializable
data class TelemetryItem(
    val latitude: Double,
    val longitude: Double,
    val altitude: Double? = null,
    val accuracy: Float? = null,
    val speed: Float? = null,
    val bearing: Float? = null,
    val provider: String? = "fused",
    @SerialName("battery_level") val batteryLevel: Int? = null,
    @SerialName("power_state") val powerState: String? = null,
    @SerialName("security_state") val securityState: String? = null,
    @SerialName("connectivity_state") val connectivityState: String? = null,
    @SerialName("network_metadata") val networkMetadata: Map<String, String>? = emptyMap(),
    @SerialName("recorded_at") val recordedAt: String
) {
    fun toPayloadMap(): Map<String, Any?> {
        val map = mutableMapOf<String, Any?>(
            "latitude" to latitude,
            "longitude" to longitude,
            "recorded_at" to recordedAt
        )
        altitude?.let { map["altitude"] = it }
        accuracy?.let { map["accuracy"] = it.toDouble() }
        speed?.let { map["speed"] = it.toDouble() }
        bearing?.let { map["bearing"] = it.toDouble() }
        provider?.let { map["provider"] = it }
        batteryLevel?.let { map["battery_level"] = it }
        powerState?.let { map["power_state"] = it }
        securityState?.let { map["security_state"] = it }
        connectivityState?.let { map["connectivity_state"] = it }
        networkMetadata?.let { map["network_metadata"] = it }
        return map
    }
}

@Serializable
data class TelemetryBatchRequest(
    @SerialName("device_id") val deviceId: String,
    val items: List<TelemetryItem>,
    val nonce: String,
    val timestamp: String,
    val signature: String
)

@Serializable
data class TelemetryBatchResponse(
    @SerialName("ingested_count") val ingestedCount: Int,
    @SerialName("latest_recorded_at") val latestRecordedAt: String,
    @SerialName("server_time") val serverTime: String
)
