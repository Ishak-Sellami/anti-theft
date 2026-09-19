package com.antisarika.agent.core.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
enum class EvidenceType {
    SNAPSHOT,
    AMBIENT_RF,
    NETWORK_BEACONS,
    SENSOR_BURST
}

@Serializable
data class EvidenceMetadataRequest(
    @SerialName("device_id") val deviceId: String,
    @SerialName("event_id") val eventId: String? = null,
    @SerialName("capture_type") val captureType: String,
    @SerialName("integrity_hash") val integrityHash: String,
    @SerialName("storage_ref") val storageRef: String,
    @SerialName("mime_type") val mimeType: String = "application/octet-stream",
    @SerialName("file_size_bytes") val fileSizeBytes: String? = null,
    @SerialName("chain_of_custody_notes") val chainOfCustodyNotes: String? = null,
    @SerialName("device_timestamp") val deviceTimestamp: String,
    val nonce: String,
    val signature: String
)

@Serializable
data class EvidenceMetadataResponse(
    val id: String,
    @SerialName("device_id") val deviceId: String,
    @SerialName("event_id") val eventId: String? = null,
    @SerialName("capture_type") val captureType: String,
    @SerialName("integrity_hash") val integrityHash: String,
    @SerialName("storage_ref") val storageRef: String,
    @SerialName("mime_type") val mimeType: String,
    @SerialName("file_size_bytes") val fileSizeBytes: String? = null,
    @SerialName("chain_of_custody_notes") val chainOfCustodyNotes: String? = null,
    @SerialName("device_timestamp") val deviceTimestamp: String,
    @SerialName("received_at") val receivedAt: String
)
