package com.antisarika.agent.commands

import com.antisarika.agent.core.crypto.DeviceSigner
import com.antisarika.agent.core.logging.SafeLogger
import com.antisarika.agent.core.model.CommandType
import com.antisarika.agent.core.model.RemoteCommand
import com.antisarika.agent.core.storage.AntiSarikaDatabase
import com.antisarika.agent.state.StateManager
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.text.SimpleDateFormat
import java.util.*

sealed class CommandVerificationResult {
    data object Valid : CommandVerificationResult()
    data class Invalid(val reason: String) : CommandVerificationResult()
}

class CommandVerifier(
    private val database: AntiSarikaDatabase,
    private val deviceSigner: DeviceSigner,
    private val stateManager: StateManager
) {
    companion object {
        private const val TAG = "CommandVerifier"
    }

    private val isoFormat = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss", Locale.US).apply {
        timeZone = TimeZone.getTimeZone("UTC")
    }

    suspend fun verifyCommand(command: RemoteCommand): CommandVerificationResult = withContext(Dispatchers.IO) {
        val config = database.deviceConfigDao().getConfig()
            ?: return@withContext CommandVerificationResult.Invalid("Device is not enrolled")

        // 1. Target Device ID check
        if (command.deviceId != config.deviceId) {
            SafeLogger.w(TAG, "Command target device mismatch: ${command.deviceId} != ${config.deviceId}")
            return@withContext CommandVerificationResult.Invalid("Command device_id mismatch")
        }

        // 2. Command Type validity
        val commandType = runCatching { CommandType.valueOf(command.commandType) }.getOrNull()
        if (commandType == null) {
            SafeLogger.w(TAG, "Unknown command type: ${command.commandType}")
            return@withContext CommandVerificationResult.Invalid("Unknown command type: ${command.commandType}")
        }

        // 3. Expiration Check (TTL)
        try {
            val cleanExpires = command.expiresAt.substringBefore(".").substringBefore("Z").substringBefore("+")
            val expiresDate = isoFormat.parse(cleanExpires)
            if (expiresDate != null && expiresDate.before(Date())) {
                SafeLogger.w(TAG, "Command expired at ${command.expiresAt}")
                return@withContext CommandVerificationResult.Invalid("Command has expired")
            }
        } catch (e: Exception) {
            SafeLogger.w(TAG, "Failed to parse expires_at timestamp: ${command.expiresAt}", e)
        }

        // 4. Nonce / Replay Protection
        val existingNonce = database.commandDao().getCommandByNonce(command.nonce)
        if (existingNonce != null) {
            SafeLogger.w(TAG, "Replay attack detected: Nonce ${command.nonce} was already executed")
            return@withContext CommandVerificationResult.Invalid("Nonce has already been used")
        }

        // 5. Backend Cryptographic Signature Verification
        val payloadToVerify = command.toBackendVerificationMap()
        val isSignatureValid = deviceSigner.verifyBackendSignature(
            payload = payloadToVerify,
            signatureB64 = command.signature,
            backendPublicKeyPem = config.backendPublicKeyPem
        )

        if (!isSignatureValid) {
            SafeLogger.w(TAG, "Cryptographic verification failed for command ${command.id}")
            return@withContext CommandVerificationResult.Invalid("Cryptographic signature verification failed")
        }

        SafeLogger.i(TAG, "Command ${command.id} (${command.commandType}) verified successfully.")
        CommandVerificationResult.Valid
    }
}
