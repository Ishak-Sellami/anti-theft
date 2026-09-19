package com.antisarika.agent.core.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.JsonObject

@Serializable
enum class CommandType {
    SET_SECURITY_STATE,
    UPDATE_POLICY,
    TRIGGER_ALARM,
    STOP_ALARM,
    REQUEST_SNAPSHOT,
    LOCK_DEVICE,
    AUTHORIZE_WIPE
}

@Serializable
enum class CommandStatus {
    PENDING,
    DELIVERED,
    ACKNOWLEDGED,
    EXECUTED,
    FAILED,
    EXPIRED
}

@Serializable
data class RemoteCommand(
    val id: String,
    @SerialName("device_id") val deviceId: String,
    @SerialName("issued_by") val issuedBy: String,
    @SerialName("command_type") val commandType: String,
    val payload: Map<String, String>? = emptyMap(),
    val nonce: String,
    val status: String,
    @SerialName("expires_at") val expiresAt: String,
    val signature: String,
    @SerialName("created_at") val createdAt: String
) {
    fun toBackendVerificationMap(): Map<String, Any?> {
        return mapOf(
            "command_id" to id,
            "device_id" to deviceId,
            "command_type" to commandType,
            "payload" to (payload ?: emptyMap<String, String>()),
            "nonce" to nonce,
            "expires_at" to expiresAt,
            "created_at" to createdAt
        )
    }
}

@Serializable
data class CommandAckRequest(
    @SerialName("command_id") val commandId: String,
    @SerialName("device_id") val deviceId: String,
    val status: String,
    @SerialName("result_payload") val resultPayload: Map<String, String>? = emptyMap(),
    @SerialName("error_message") val errorMessage: String? = null,
    val nonce: String,
    val timestamp: String,
    val signature: String
)
