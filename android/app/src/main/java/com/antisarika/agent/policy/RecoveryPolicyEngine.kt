package com.antisarika.agent.policy

import com.antisarika.agent.core.logging.SafeLogger
import com.antisarika.agent.core.model.PowerState
import com.antisarika.agent.core.model.PowerStatePolicy
import com.antisarika.agent.core.model.RecoveryPolicyConfig
import com.antisarika.agent.core.model.SecurityState
import com.antisarika.agent.core.storage.AntiSarikaDatabase
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import kotlinx.serialization.json.Json

class RecoveryPolicyEngine(
    private val database: AntiSarikaDatabase,
    private val scope: CoroutineScope
) {
    companion object {
        private const val TAG = "RecoveryPolicyEngine"

        fun createDefaultStolenPolicy(): RecoveryPolicyConfig {
            return RecoveryPolicyConfig(
                policyVersion = 1,
                policyId = "pol_stolen_default_v1",
                securityState = "STOLEN",
                powerStateOverrides = mapOf(
                    "NORMAL" to PowerStatePolicy(
                        locationIntervalMs = 15000L,
                        locationFastestIntervalMs = 10000L,
                        locationAccuracy = "HIGH_ACCURACY",
                        heartbeatIntervalMs = 30000L,
                        telemetryBatchSize = 1,
                        enableBleBeacon = false
                    ),
                    "LOW" to PowerStatePolicy(
                        locationIntervalMs = 60000L,
                        locationFastestIntervalMs = 30000L,
                        locationAccuracy = "BALANCED_POWER",
                        heartbeatIntervalMs = 120000L,
                        telemetryBatchSize = 5,
                        enableBleBeacon = false
                    ),
                    "CRITICAL" to PowerStatePolicy(
                        locationIntervalMs = 300000L,
                        locationFastestIntervalMs = 180000L,
                        locationAccuracy = "PRIORITIZE_CELL_WIFI",
                        heartbeatIntervalMs = 600000L,
                        telemetryBatchSize = 10,
                        enableBleBeacon = false
                    )
                )
            )
        }
    }

    private val json = Json { ignoreUnknownKeys = true; isLenient = true }
    private val _activePolicy = MutableStateFlow(createDefaultStolenPolicy())
    val activePolicy: StateFlow<RecoveryPolicyConfig> = _activePolicy

    init {
        scope.launch(Dispatchers.IO) {
            val config = database.deviceConfigDao().getConfig()
            if (config != null && config.activePolicyJson.isNotEmpty()) {
                try {
                    val loaded = json.decodeFromString<RecoveryPolicyConfig>(config.activePolicyJson)
                    _activePolicy.value = loaded
                    SafeLogger.i(TAG, "Loaded policy from DB: ${loaded.policyId}")
                } catch (e: Exception) {
                    SafeLogger.w(TAG, "Failed to parse stored policy, keeping default", e)
                }
            }
        }
    }

    fun applyPolicy(policy: RecoveryPolicyConfig) {
        if (!validatePolicy(policy)) {
            SafeLogger.w(TAG, "Rejecting invalid RecoveryPolicy: ${policy.policyId}")
            return
        }
        _activePolicy.value = policy
        SafeLogger.i(TAG, "Applied new RecoveryPolicy: ${policy.policyId} (v${policy.policyVersion})")

        scope.launch(Dispatchers.IO) {
            val config = database.deviceConfigDao().getConfig()
            if (config != null) {
                val policyString = json.encodeToString(RecoveryPolicyConfig.serializer(), policy)
                database.deviceConfigDao().updateConfig(config.copy(activePolicyJson = policyString))
            }
        }
    }

    fun getCurrentPowerPolicy(powerState: PowerState): PowerStatePolicy {
        val overrides = _activePolicy.value.powerStateOverrides
        return overrides[powerState.name] ?: overrides["NORMAL"] ?: PowerStatePolicy(
            locationIntervalMs = 30000L,
            locationFastestIntervalMs = 15000L,
            heartbeatIntervalMs = 60000L
        )
    }

    fun validatePolicy(policy: RecoveryPolicyConfig): Boolean {
        if (policy.policyId.isBlank()) return false
        for ((_, pwr) in policy.powerStateOverrides) {
            if (pwr.locationIntervalMs < 1000L || pwr.locationFastestIntervalMs < 500L) return false
            if (pwr.heartbeatIntervalMs < 5000L) return false
        }
        return true
    }
}
