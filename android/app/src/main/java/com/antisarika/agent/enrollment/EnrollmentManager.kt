package com.antisarika.agent.enrollment

import android.os.Build
import com.antisarika.agent.core.crypto.DeviceSigner
import com.antisarika.agent.core.crypto.KeystoreManager
import com.antisarika.agent.core.logging.SafeLogger
import com.antisarika.agent.core.network.ApiClient
import com.antisarika.agent.core.storage.AntiSarikaDatabase
import com.antisarika.agent.core.storage.entities.AuditLogEntity
import com.antisarika.agent.core.storage.entities.DeviceConfigEntity
import com.antisarika.agent.dpc.DevicePolicyController
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.text.SimpleDateFormat
import java.util.*

class EnrollmentManager(
    private val apiClient: ApiClient,
    private val keystoreManager: KeystoreManager,
    private val deviceSigner: DeviceSigner,
    private val database: AntiSarikaDatabase,
    private val dpc: DevicePolicyController
) {
    companion object {
        private const val TAG = "EnrollmentManager"
        private const val AGENT_VERSION = "0.1.0"
    }

    private val isoFormat = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss.SSSSSS'Z'", Locale.US).apply {
        timeZone = TimeZone.getTimeZone("UTC")
    }

    suspend fun isEnrolled(): Boolean = withContext(Dispatchers.IO) {
        val config = database.deviceConfigDao().getConfig()
        config != null && config.isEnrolled
    }

    suspend fun enrollDevice(
        enrollmentToken: String,
        deviceName: String,
        backendPublicKeyPem: String
    ): Result<DeviceConfigEntity> = withContext(Dispatchers.IO) {
        try {
            SafeLogger.i(TAG, "Starting device enrollment...")
            val keyPair = keystoreManager.getOrCreateDeviceKeyPair()
            val publicKeyPem = keystoreManager.getPublicKeyPem(keyPair.public)
            val fingerprint = keystoreManager.computePublicKeyFingerprint(keyPair.public)

            val nowIso = isoFormat.format(Date())
            val nonce = "enroll_nonce_" + UUID.randomUUID().toString().replace("-", "").take(16)

            val payloadToSign = mapOf(
                "agent_version" to AGENT_VERSION,
                "device_model" to Build.MODEL,
                "device_name" to deviceName,
                "enrollment_token" to enrollmentToken,
                "nonce" to nonce,
                "os_version" to "Android ${Build.VERSION.RELEASE} (API ${Build.VERSION.SDK_INT})",
                "timestamp" to nowIso
            )

            val signature = deviceSigner.signPayload(payloadToSign)

            val responseResult = apiClient.completeEnrollment(
                enrollmentToken = enrollmentToken,
                publicKeyPem = publicKeyPem,
                deviceName = deviceName,
                deviceModel = Build.MODEL,
                osVersion = "Android ${Build.VERSION.RELEASE} (API ${Build.VERSION.SDK_INT})",
                agentVersion = AGENT_VERSION,
                nonce = nonce,
                timestamp = nowIso,
                signature = signature
            )

            if (responseResult.isFailure) {
                val error = responseResult.exceptionOrNull() ?: Exception("Enrollment failed")
                SafeLogger.e(TAG, "Enrollment rejected by backend", error)
                return@withContext Result.failure(error)
            }

            val responseJson = responseResult.getOrThrow()
            val deviceId = responseJson.getString("id")
            val ownerId = responseJson.getString("owner_id")
            val securityState = responseJson.optString("security_state", "NORMAL")
            val connectivityState = responseJson.optString("connectivity_state", "ONLINE")
            val powerState = responseJson.optString("power_state", "NORMAL")
            val activePolicyId = responseJson.optString("active_policy_id", "pol_stolen_default_v1")

            val configEntity = DeviceConfigEntity(
                deviceId = deviceId,
                ownerId = ownerId,
                deviceName = deviceName,
                backendPublicKeyPem = backendPublicKeyPem,
                securityState = securityState,
                connectivityState = connectivityState,
                powerState = powerState,
                activePolicyJson = JSONObject().put("policy_id", activePolicyId).toString(),
                lastHeartbeatTime = System.currentTimeMillis(),
                isEnrolled = true
            )

            database.deviceConfigDao().saveConfig(configEntity)
            database.auditLogDao().insertLog(
                AuditLogEntity(
                    actor = "DEVICE",
                    action = "DEVICE_ENROLLED",
                    details = "Enrolled with deviceId: $deviceId, fingerprint: $fingerprint"
                )
            )

            // If Device Owner is enabled, apply basic factory reset and uninstall protections
            if (dpc.isDeviceOwner()) {
                dpc.setFactoryResetBlocked(true)
                dpc.setUninstallBlocked(true)
                SafeLogger.i(TAG, "Device Owner policies applied automatically post-enrollment.")
            }

            SafeLogger.i(TAG, "Device enrolled successfully with ID: $deviceId")
            Result.success(configEntity)
        } catch (e: Exception) {
            SafeLogger.e(TAG, "Enrollment error", e)
            Result.failure(e)
        }
    }
}
