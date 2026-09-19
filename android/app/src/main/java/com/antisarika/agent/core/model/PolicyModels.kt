package com.antisarika.agent.core.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class PowerStatePolicy(
    @SerialName("location_interval_ms") val locationIntervalMs: Long,
    @SerialName("location_fastest_interval_ms") val locationFastestIntervalMs: Long,
    @SerialName("location_accuracy") val locationAccuracy: String = "HIGH_ACCURACY",
    @SerialName("heartbeat_interval_ms") val heartbeatIntervalMs: Long,
    @SerialName("telemetry_batch_size") val telemetryBatchSize: Int = 1,
    @SerialName("enable_ble_beacon") val enableBleBeacon: Boolean = false
)

@Serializable
data class RetryConfig(
    @SerialName("initial_retry_interval_ms") val initialRetryIntervalMs: Long = 5000L,
    @SerialName("max_retry_interval_ms") val maxRetryIntervalMs: Long = 300000L,
    @SerialName("backoff_multiplier") val backoffMultiplier: Double = 2.0,
    @SerialName("max_jitter_ms") val maxJitterMs: Long = 1000L
)

@Serializable
data class StorageLimits(
    @SerialName("offline_queue_max_records") val offlineQueueMaxRecords: Int = 10000,
    @SerialName("eviction_strategy") val evictionStrategy: String = "DROP_OLDEST_UNIMPORTANT"
)

@Serializable
data class RecoveryPolicyConfig(
    @SerialName("policy_version") val policyVersion: Int = 1,
    @SerialName("policy_id") val policyId: String,
    @SerialName("security_state") val securityState: String,
    @SerialName("power_state_overrides") val powerStateOverrides: Map<String, PowerStatePolicy>,
    @SerialName("retry_config") val retryConfig: RetryConfig = RetryConfig(),
    @SerialName("storage_limits") val storageLimits: StorageLimits = StorageLimits()
)
