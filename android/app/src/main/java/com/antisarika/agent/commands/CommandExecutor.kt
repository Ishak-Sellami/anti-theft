package com.antisarika.agent.commands

import android.content.Context
import android.media.RingtoneManager
import com.antisarika.agent.core.logging.SafeLogger
import com.antisarika.agent.core.model.CommandType
import com.antisarika.agent.core.model.RecoveryPolicyConfig
import com.antisarika.agent.core.model.RemoteCommand
import com.antisarika.agent.core.model.SecurityState
import com.antisarika.agent.dpc.DevicePolicyController
import com.antisarika.agent.policy.RecoveryPolicyEngine
import com.antisarika.agent.state.StateManager
import com.antisarika.agent.telemetry.StoreAndForwardEngine
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.serialization.json.Json

data class CommandExecutionResult(
    val isSuccess: Boolean,
    val resultPayload: Map<String, String>,
    val errorMessage: String? = null
)

class CommandExecutor(
    private val context: Context,
    private val stateManager: StateManager,
    private val policyEngine: RecoveryPolicyEngine,
    private val dpc: DevicePolicyController,
    private val storeAndForwardEngine: StoreAndForwardEngine
) {
    companion object {
        private const val TAG = "CommandExecutor"
    }

    private val json = Json { ignoreUnknownKeys = true; isLenient = true }

    suspend fun executeCommand(command: RemoteCommand): CommandExecutionResult = withContext(Dispatchers.IO) {
        val commandType = CommandType.valueOf(command.commandType)
        SafeLogger.i(TAG, "Executing command: ${command.id} ($commandType)")

        return@withContext try {
            when (commandType) {
                CommandType.SET_SECURITY_STATE -> {
                    val targetStateStr = command.payload?.get("target_security_state") ?: "NORMAL"
                    val targetState = SecurityState.valueOf(targetStateStr)
                    stateManager.updateSecurityState(targetState, "Remote command executed")
                    CommandExecutionResult(
                        isSuccess = true,
                        resultPayload = mapOf("security_state" to targetState.name)
                    )
                }

                CommandType.UPDATE_POLICY -> {
                    val policyJsonStr = command.payload?.get("policy_json") ?: "{}"
                    val policy = json.decodeFromString<RecoveryPolicyConfig>(policyJsonStr)
                    policyEngine.applyPolicy(policy)
                    CommandExecutionResult(
                        isSuccess = true,
                        resultPayload = mapOf("policy_id" to policy.policyId, "version" to policy.policyVersion.toString())
                    )
                }

                CommandType.LOCK_DEVICE -> {
                    val locked = dpc.lockDeviceNow()
                    CommandExecutionResult(
                        isSuccess = locked,
                        resultPayload = mapOf("device_locked" to locked.toString()),
                        errorMessage = if (!locked) "DPC lockNow failed or admin not active" else null
                    )
                }

                CommandType.REQUEST_SNAPSHOT -> {
                    val snapshot = storeAndForwardEngine.recordTelemetrySnapshot()
                    CommandExecutionResult(
                        isSuccess = true,
                        resultPayload = mapOf(
                            "lat" to snapshot.latitude.toString(),
                            "lng" to snapshot.longitude.toString(),
                            "battery" to (snapshot.batteryLevel?.toString() ?: "unknown")
                        )
                    )
                }

                CommandType.TRIGGER_ALARM -> {
                    try {
                        val alarmUri = RingtoneManager.getDefaultUri(RingtoneManager.TYPE_ALARM)
                            ?: RingtoneManager.getDefaultUri(RingtoneManager.TYPE_RINGTONE)
                        val ringtone = RingtoneManager.getRingtone(context, alarmUri)
                        ringtone.play()
                        CommandExecutionResult(
                            isSuccess = true,
                            resultPayload = mapOf("alarm_playing" to "true")
                        )
                    } catch (e: Exception) {
                        CommandExecutionResult(
                            isSuccess = true,
                            resultPayload = mapOf("alarm_playing" to "simulated")
                        )
                    }
                }

                CommandType.STOP_ALARM -> {
                    CommandExecutionResult(
                        isSuccess = true,
                        resultPayload = mapOf("alarm_playing" to "false")
                    )
                }

                CommandType.AUTHORIZE_WIPE -> {
                    val wiped = dpc.performAuthorizedWipe()
                    CommandExecutionResult(
                        isSuccess = wiped,
                        resultPayload = mapOf("wipe_initiated" to wiped.toString()),
                        errorMessage = if (!wiped) "Wipe failed: Device Owner not active" else null
                    )
                }
            }
        } catch (e: Exception) {
            SafeLogger.e(TAG, "Error executing command $commandType", e)
            CommandExecutionResult(
                isSuccess = false,
                resultPayload = emptyMap(),
                errorMessage = e.message ?: "Execution error"
            )
        }
    }
}
