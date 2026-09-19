package com.antisarika.agent.core.network

import com.antisarika.agent.core.logging.SafeLogger
import com.antisarika.agent.core.model.*
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.logging.HttpLoggingInterceptor
import org.json.JSONArray
import org.json.JSONObject
import java.io.IOException
import java.util.concurrent.TimeUnit

class ApiClient(
    private var baseUrl: String = "http://10.0.2.2:8000"
) {
    companion object {
        private const val TAG = "ApiClient"
        private val JSON_MEDIA_TYPE = "application/json; charset=utf-8".toMediaType()
    }

    private val json = Json {
        ignoreUnknownKeys = true
        isLenient = true
        encodeDefaults = true
    }

    private val okHttpClient: OkHttpClient = OkHttpClient.Builder()
        .connectTimeout(15, TimeUnit.SECONDS)
        .readTimeout(20, TimeUnit.SECONDS)
        .writeTimeout(20, TimeUnit.SECONDS)
        .addInterceptor(HttpLoggingInterceptor { msg -> SafeLogger.d("HTTP", msg) }.apply {
            level = HttpLoggingInterceptor.Level.BASIC
        })
        .build()

    fun updateBaseUrl(newUrl: String) {
        this.baseUrl = newUrl.trimEnd('/')
    }

    fun getBaseUrl(): String = baseUrl

    suspend fun completeEnrollment(
        enrollmentToken: String,
        publicKeyPem: String,
        deviceName: String,
        deviceModel: String?,
        osVersion: String?,
        agentVersion: String?,
        nonce: String,
        timestamp: String,
        signature: String
    ): Result<JSONObject> = withContext(Dispatchers.IO) {
        val payload = JSONObject().apply {
            put("enrollment_token", enrollmentToken)
            put("public_key_pem", publicKeyPem)
            put("device_name", deviceName)
            deviceModel?.let { put("device_model", it) }
            osVersion?.let { put("os_version", it) }
            agentVersion?.let { put("agent_version", it) }
            put("nonce", nonce)
            put("timestamp", timestamp)
            put("signature", signature)
        }
        post("/api/v1/devices/enroll/complete", payload)
    }

    suspend fun sendHeartbeat(
        deviceId: String,
        batteryLevel: Int?,
        isCharging: Boolean,
        connectivityState: ConnectivityState,
        nonce: String,
        timestamp: String,
        signature: String
    ): Result<JSONObject> = withContext(Dispatchers.IO) {
        val payload = JSONObject().apply {
            put("device_id", deviceId)
            batteryLevel?.let { put("battery_level", it) }
            put("is_charging", isCharging)
            put("connectivity_state", connectivityState.name)
            put("nonce", nonce)
            put("timestamp", timestamp)
            put("signature", signature)
        }
        post("/api/v1/devices/heartbeat", payload)
    }

    suspend fun submitTelemetryBatch(
        deviceId: String,
        items: List<Map<String, Any?>>,
        nonce: String,
        timestamp: String,
        signature: String
    ): Result<JSONObject> = withContext(Dispatchers.IO) {
        val payload = JSONObject().apply {
            put("device_id", deviceId)
            val jsonArray = JSONArray()
            for (item in items) {
                jsonArray.put(JSONObject(item))
            }
            put("items", jsonArray)
            put("nonce", nonce)
            put("timestamp", timestamp)
            put("signature", signature)
        }
        post("/api/v1/telemetry/batch", payload)
    }

    suspend fun submitSecurityEvent(
        deviceId: String,
        eventType: String,
        severity: String,
        stateBefore: String,
        stateAfter: String,
        eventPayload: Map<String, Any?>,
        timestamp: String,
        nonce: String,
        signature: String
    ): Result<JSONObject> = withContext(Dispatchers.IO) {
        val payload = JSONObject().apply {
            put("device_id", deviceId)
            put("event_type", eventType)
            put("severity", severity)
            put("security_state_before", stateBefore)
            put("security_state_after", stateAfter)
            put("payload", JSONObject(eventPayload))
            put("device_timestamp", timestamp)
            put("nonce", nonce)
            put("signature", signature)
        }
        post("/api/v1/events", payload)
    }

    suspend fun pollPendingCommands(deviceId: String): Result<List<RemoteCommand>> = withContext(Dispatchers.IO) {
        try {
            val url = "$baseUrl/api/v1/commands/$deviceId/pending"
            val request = Request.Builder().url(url).get().build()
            val response = okHttpClient.newCall(request).execute()
            val body = response.body?.string() ?: "[]"
            if (response.isSuccessful) {
                val list = json.decodeFromString<List<RemoteCommand>>(body)
                Result.success(list)
            } else {
                Result.failure(IOException("Failed to poll commands: ${response.code} $body"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun acknowledgeCommand(
        commandId: String,
        deviceId: String,
        status: String,
        resultPayload: Map<String, String>?,
        errorMessage: String?,
        nonce: String,
        timestamp: String,
        signature: String
    ): Result<JSONObject> = withContext(Dispatchers.IO) {
        val payload = JSONObject().apply {
            put("command_id", commandId)
            put("device_id", deviceId)
            put("status", status)
            resultPayload?.let { put("result_payload", JSONObject(it)) }
            errorMessage?.let { put("error_message", it) }
            put("nonce", nonce)
            put("timestamp", timestamp)
            put("signature", signature)
        }
        post("/api/v1/commands/ack", payload)
    }

    suspend fun fetchPolicy(policyId: String): Result<RecoveryPolicyConfig> = withContext(Dispatchers.IO) {
        try {
            val url = "$baseUrl/api/v1/policies/$policyId"
            val request = Request.Builder().url(url).get().build()
            val response = okHttpClient.newCall(request).execute()
            val body = response.body?.string() ?: ""
            if (response.isSuccessful) {
                val jsonObject = JSONObject(body)
                val configJson = jsonObject.getJSONObject("config").toString()
                val policy = json.decodeFromString<RecoveryPolicyConfig>(configJson)
                Result.success(policy)
            } else {
                Result.failure(IOException("Failed to fetch policy: ${response.code} $body"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun submitEvidenceMetadata(
        deviceId: String,
        eventId: String?,
        captureType: String,
        integrityHash: String,
        storageRef: String,
        mimeType: String,
        fileSizeBytes: Long?,
        notes: String?,
        timestamp: String,
        nonce: String,
        signature: String
    ): Result<JSONObject> = withContext(Dispatchers.IO) {
        val payload = JSONObject().apply {
            put("device_id", deviceId)
            eventId?.let { put("event_id", it) }
            put("capture_type", captureType)
            put("integrity_hash", integrityHash)
            put("storage_ref", storageRef)
            put("mime_type", mimeType)
            fileSizeBytes?.let { put("file_size_bytes", it.toString()) }
            notes?.let { put("chain_of_custody_notes", it) }
            put("device_timestamp", timestamp)
            put("nonce", nonce)
            put("signature", signature)
        }
        post("/api/v1/evidence", payload)
    }

    private fun post(path: String, jsonPayload: JSONObject): Result<JSONObject> {
        return try {
            val url = "$baseUrl$path"
            val requestBody = jsonPayload.toString().toRequestBody(JSON_MEDIA_TYPE)
            val request = Request.Builder().url(url).post(requestBody).build()
            val response = okHttpClient.newCall(request).execute()
            val responseBody = response.body?.string() ?: "{}"
            if (response.isSuccessful) {
                Result.success(JSONObject(responseBody))
            } else {
                SafeLogger.w(TAG, "Request failed [$path]: HTTP ${response.code} - $responseBody")
                Result.failure(IOException("Server error ${response.code}: $responseBody"))
            }
        } catch (e: Exception) {
            SafeLogger.e(TAG, "Network error on POST $path", e)
            Result.failure(e)
        }
    }
}
