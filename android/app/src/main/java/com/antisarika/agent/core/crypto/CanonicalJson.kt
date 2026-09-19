package com.antisarika.agent.core.crypto

import org.json.JSONArray
import org.json.JSONObject
import java.nio.charset.StandardCharsets
import java.util.TreeMap

object CanonicalJson {

    /**
     * Serializes any Map / JSONObject / primitive structure into deterministic canonical JSON bytes.
     * Keys are sorted lexicographically, no whitespace around ':' and ','.
     */
    fun canonicalize(data: Map<String, Any?>): ByteArray {
        val sortedString = serializeValue(data)
        return sortedString.toByteArray(StandardCharsets.UTF_8)
    }

    private fun serializeValue(value: Any?): String {
        return when (value) {
            null -> "null"
            is String -> JSONObject.quote(value)
            is Number, is Boolean -> value.toString()
            is Map<*, *> -> {
                val sortedMap = TreeMap<String, Any?>()
                for ((k, v) in value) {
                    if (k != null) {
                        sortedMap[k.toString()] = v
                    }
                }
                val sb = StringBuilder("{")
                var first = true
                for ((k, v) in sortedMap) {
                    if (!first) sb.append(",")
                    sb.append(JSONObject.quote(k)).append(":").append(serializeValue(v))
                    first = false
                }
                sb.append("}")
                sb.toString()
            }
            is Collection<*> -> {
                val sb = StringBuilder("[")
                var first = true
                for (item in value) {
                    if (!first) sb.append(",")
                    sb.append(serializeValue(item))
                    first = false
                }
                sb.append("]")
                sb.toString()
            }
            is Array<*> -> serializeValue(value.toList())
            is JSONObject -> {
                val map = mutableMapOf<String, Any?>()
                val keys = value.keys()
                while (keys.hasNext()) {
                    val key = keys.next()
                    map[key] = value.opt(key)
                }
                serializeValue(map)
            }
            is JSONArray -> {
                val list = mutableListOf<Any?>()
                for (i in 0 until value.length()) {
                    list.add(value.opt(i))
                }
                serializeValue(list)
            }
            else -> JSONObject.quote(value.toString())
        }
    }
}
