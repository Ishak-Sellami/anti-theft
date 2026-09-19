package com.antisarika.agent.core.logging

import android.util.Log

object SafeLogger {
    private const val TAG = "AntiSarika"

    private val SENSITIVE_PATTERNS = listOf(
        Regex("(?i)bearer\\s+[a-zA-Z0-9._\\-]+"),
        Regex("(?i)password[\"']?\\s*[:=]\\s*[\"']?[^\"',\\s]+"),
        Regex("(?i)private_?key"),
        Regex("(?i)secret")
    )

    fun d(subsystem: String, message: String) {
        val sanitized = sanitize(message)
        Log.d(TAG, "[$subsystem] $sanitized")
    }

    fun i(subsystem: String, message: String) {
        val sanitized = sanitize(message)
        Log.i(TAG, "[$subsystem] $sanitized")
    }

    fun w(subsystem: String, message: String, throwable: Throwable? = null) {
        val sanitized = sanitize(message)
        Log.w(TAG, "[$subsystem] $sanitized", throwable)
    }

    fun e(subsystem: String, message: String, throwable: Throwable? = null) {
        val sanitized = sanitize(message)
        Log.e(TAG, "[$subsystem] $sanitized", throwable)
    }

    private fun sanitize(input: String): String {
        var result = input
        for (pattern in SENSITIVE_PATTERNS) {
            result = result.replace(pattern, "[REDACTED]")
        }
        return result
    }
}
