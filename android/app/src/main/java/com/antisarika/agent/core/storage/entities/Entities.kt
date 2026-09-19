package com.antisarika.agent.core.storage.entities

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "device_config")
data class DeviceConfigEntity(
    @PrimaryKey val key: String = "current_config",
    val deviceId: String,
    val ownerId: String,
    val deviceName: String,
    val backendPublicKeyPem: String,
    val securityState: String = "NORMAL",
    val connectivityState: String = "ONLINE",
    val powerState: String = "NORMAL",
    val activePolicyJson: String,
    val lastHeartbeatTime: Long = 0L,
    val isEnrolled: Boolean = true
)

@Entity(tableName = "telemetry_queue")
data class TelemetryEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val latitude: Double,
    val longitude: Double,
    val altitude: Double?,
    val accuracy: Float?,
    val speed: Float?,
    val bearing: Float?,
    val provider: String?,
    val batteryLevel: Int?,
    val powerState: String,
    val securityState: String,
    val connectivityState: String,
    val networkMetadataJson: String,
    val recordedAt: String,
    val isSynced: Boolean = false
)

@Entity(tableName = "security_events_queue")
data class SecurityEventEntity(
    @PrimaryKey val eventId: String,
    val eventType: String,
    val severity: String,
    val stateBefore: String,
    val stateAfter: String,
    val payloadJson: String,
    val timestamp: String,
    val nonce: String,
    val isSynced: Boolean = false
)

@Entity(tableName = "command_history")
data class CommandEntity(
    @PrimaryKey val commandId: String,
    val commandType: String,
    val payloadJson: String,
    val nonce: String,
    val expiresAt: String,
    val status: String,
    val resultJson: String?,
    val errorMessage: String?,
    val createdAt: String,
    val executedAt: Long? = null
)

@Entity(tableName = "evidence_queue")
data class EvidenceEntity(
    @PrimaryKey val evidenceId: String,
    val eventId: String?,
    val captureType: String,
    val integrityHash: String,
    val localFilePath: String,
    val mimeType: String,
    val fileSizeBytes: Long,
    val notes: String?,
    val timestamp: String,
    val nonce: String,
    val isSynced: Boolean = false
)

@Entity(tableName = "local_audit_log")
data class AuditLogEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val actor: String,
    val action: String,
    val details: String,
    val timestamp: Long = System.currentTimeMillis()
)
