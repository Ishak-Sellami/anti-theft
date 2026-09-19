package com.antisarika.agent.core.network

import com.antisarika.agent.core.logging.SafeLogger
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.SharedFlow
import okhttp3.*
import org.json.JSONObject
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicBoolean

class WebSocketManager(
    private val client: OkHttpClient = OkHttpClient.Builder()
        .readTimeout(0, TimeUnit.MILLISECONDS)
        .pingInterval(20, TimeUnit.SECONDS)
        .build()
) {
    companion object {
        private const val TAG = "WebSocketManager"
    }

    private var webSocket: WebSocket? = null
    private val isConnected = AtomicBoolean(false)
    private var reconnectJob: Job? = null
    private val scope = CoroutineScope(Dispatchers.IO + SupervisorJob())

    private val _incomingMessages = MutableSharedFlow<JSONObject>(extraBufferCapacity = 50)
    val incomingMessages: SharedFlow<JSONObject> = _incomingMessages

    private var currentUrl: String? = null
    private var currentToken: String? = null

    fun connect(serverBaseUrl: String, token: String) {
        val wsBaseUrl = serverBaseUrl.replace("http://", "ws://").replace("https://", "wss://")
        currentUrl = "$wsBaseUrl/api/v1/ws?token=$token"
        currentToken = token
        establishConnection()
    }

    private fun establishConnection() {
        val url = currentUrl ?: return
        SafeLogger.i(TAG, "Connecting to WebSocket: $url (token redacted)")

        val request = Request.Builder().url(url).build()
        webSocket = client.newWebSocket(request, object : WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: Response) {
                SafeLogger.i(TAG, "WebSocket connected successfully")
                isConnected.set(true)
            }

            override fun onMessage(webSocket: WebSocket, text: String) {
                try {
                    val json = JSONObject(text)
                    SafeLogger.d(TAG, "WebSocket received message type: ${json.optString("type")}")
                    _incomingMessages.tryEmit(json)
                } catch (e: Exception) {
                    SafeLogger.w(TAG, "Failed to parse incoming WebSocket message: $text", e)
                }
            }

            override fun onClosing(webSocket: WebSocket, code: Int, reason: String) {
                SafeLogger.i(TAG, "WebSocket closing: $code / $reason")
                isConnected.set(false)
            }

            override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
                SafeLogger.i(TAG, "WebSocket closed: $code / $reason")
                isConnected.set(false)
                scheduleReconnect()
            }

            override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                SafeLogger.w(TAG, "WebSocket failure: ${t.message}", t)
                isConnected.set(false)
                scheduleReconnect()
            }
        })
    }

    private fun scheduleReconnect() {
        if (reconnectJob?.isActive == true) return
        reconnectJob = scope.launch {
            delay(5000) // 5s backoff
            if (!isConnected.get() && currentUrl != null) {
                SafeLogger.i(TAG, "Attempting WebSocket reconnection...")
                establishConnection()
            }
        }
    }

    fun sendPing() {
        webSocket?.send(JSONObject().apply { put("type", "PING") }.toString())
    }

    fun disconnect() {
        reconnectJob?.cancel()
        webSocket?.close(1000, "Agent disconnect")
        webSocket = null
        isConnected.set(false)
    }

    fun isConnectionActive(): Boolean = isConnected.get()
}
