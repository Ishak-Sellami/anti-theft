package com.antisarika.agent.commands

import com.antisarika.agent.core.crypto.DeviceSigner
import com.antisarika.agent.core.logging.SafeLogger
import com.antisarika.agent.core.model.RemoteCommand
import com.antisarika.agent.core.network.ApiClient
import com.antisarika.agent.core.storage.AntiSarikaDatabase
import com.antisarika.agent.core.storage.entities.AuditLogEntity
import com.antisarika.agent.core.storage.entities.CommandEntity
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.text.SimpleDateFormat
import java.util.*

class CommandManager(
    private val database: AntiSarikaDatabase,
    private val apiClient: ApiClient,
    private val deviceSigner: DeviceSigner,
    private val commandVerifier: CommandVerifier,
    private val commandExecutor: CommandExecutor
) {
    companion object {
        private const val TAG = "CommandManager"
    }

    private val isoFormat = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss.SSSSSS'Z'", Locale.US).apply {
        timeZone = TimeZone.getTimeZone("UTC")
    }

    suspend fun pollAndProcessPendingCommands(): Int = withContext(Dispatchers.IO) {
        val config = database.deviceConfigDao().getConfig() ?: return@withContext 0
        if (!config.isEnrolled) return@withContext 0

        val pendingResult = apiClient.pollPendingCommands(config.deviceId)
        if (pendingResult.isFailure) {
            SafeLogger.w(TAG, "Failed to poll commands: ${pendingResult.exceptionOrNull()?.message}")
            return@withContext 0
        }

        val commands = pendingResult.getOrThrow()
        SafeLogger.i(TAG, "Found ${commands.size} pending commands for device ${config.deviceId}")

        var processedCount = 0
        for (command in commands) {
            processCommand(command)
            processedCount++
        }
        processedCount
    }

    suspend fun processCommand(command: RemoteCommand): Boolean = withContext(Dispatchers.IO) {
        val config = database.deviceConfigDao().getConfig() ?: return@withContext false

        // 1. Verify Command
        val verification = commandVerifier.verifyCommand(command)
        if (verification is CommandVerificationResult.Invalid) {
            SafeLogger.w(TAG, "Rejecting command ${command.id}: ${verification.reason}")
            // Log security failure
            database.auditLogDao().insertLog(
                AuditLogEntity(
                    actor = "DEVICE",
                    action = "COMMAND_VERIFICATION_REJECTED",
                    details = "CommandId: ${command.id}, Type: ${command.commandType}, Reason: ${verification.reason}"
                )
            )
            // Acknowledge failure back to backend if possible
            acknowledgeExecution(
                commandId = command.id,
                deviceId = config.deviceId,
                status = "FAILED",
                resultPayload = null,
                errorMessage = verification.reason
            )
            return@withContext false
        }

        // 2. Record Command in local DB before execution (for nonce replay tracking)
        val commandEntity = CommandEntity(
            commandId = command.id,
            commandType = command.commandType,
            payloadJson = JSONObject(command.payload ?: emptyMap<String, String>()).toString(),
            nonce = command.nonce,
            expiresAt = command.expiresAt,
            status = "DELIVERED",
            resultJson = null,
            errorMessage = null,
            createdAt = command.createdAt
        )
        database.commandDao().insertCommand(commandEntity)

        // 3. Execute
        val executionResult = commandExecutor.executeCommand(command)
        val status = if (executionResult.isSuccess) "EXECUTED" else "FAILED"

        // 4. Update local DB
        database.commandDao().updateCommand(
            commandEntity.copy(
                status = status,
                resultJson = JSONObject(executionResult.resultPayload).toString(),
                errorMessage = executionResult.errorMessage,
                executedAt = System.currentTimeMillis()
            )
        )

        // 5. Send signed acknowledgement
        acknowledgeExecution(
            commandId = command.id,
            deviceId = config.deviceId,
            status = status,
            resultPayload = executionResult.resultPayload,
            errorMessage = executionResult.errorMessage
        )

        // 6. Audit log
        database.auditLogDao().insertLog(
            AuditLogEntity(
                actor = "DEVICE",
                action = "COMMAND_EXECUTED",
                details = "CommandId: ${command.id}, Type: ${command.commandType}, Status: $status"
            )
        )

        executionResult.isSuccess
    }

    private suspend fun acknowledgeExecution(
        commandId: String,
        deviceId: String,
        status: String,
        resultPayload: Map<String, String>?,
        errorMessage: String?
    ) {
        val nowIso = isoFormat.format(Date())
        val ackNonce = "ack_nonce_" + UUID.randomUUID().toString().replace("-", "").take(16)

        val payloadToSign = mutableMapOf<String, Any?>(
            "command_id" to commandId,
            "device_id" to deviceId,
            "status" to status,
            "result_payload" to (resultPayload ?: emptyMap<String, String>()),
            "error_message" to errorMessage,
            "nonce" to ackNonce,
            "timestamp" to nowIso
        )

        val signature = deviceSigner.signPayload(payloadToSign)

        apiClient.acknowledgeCommand(
            commandId = commandId,
            deviceId = deviceId,
            status = status,
            resultPayload = resultPayload,
            errorMessage = errorMessage,
            nonce = ackNonce,
            timestamp = nowIso,
            signature = signature
        )
    }
}
