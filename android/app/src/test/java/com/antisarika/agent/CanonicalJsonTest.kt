package com.antisarika.agent

import com.antisarika.agent.core.crypto.CanonicalJson
import org.junit.Assert.assertEquals
import org.junit.Test

class CanonicalJsonTest {

    @Test
    fun testCanonicalJsonSortingAndFormatting() {
        val map = mapOf(
            "z_field" to "last",
            "a_field" to "first",
            "m_field" to 123,
            "nested" to mapOf(
                "beta" to true,
                "alpha" to listOf("one", "two")
            )
        )

        val canonicalBytes = CanonicalJson.canonicalize(map)
        val canonicalStr = String(canonicalBytes, Charsets.UTF_8)

        val expected = """{"a_field":"first","m_field":123,"nested":{"alpha":["one","two"],"beta":true},"z_field":"last"}"""
        assertEquals(expected, canonicalStr)
    }

    @Test
    fun testCanonicalJsonWithNulls() {
        val map = mapOf(
            "b" to null,
            "a" to "hello"
        )
        val canonicalBytes = CanonicalJson.canonicalize(map)
        val canonicalStr = String(canonicalBytes, Charsets.UTF_8)

        val expected = """{"a":"hello","b":null}"""
        assertEquals(expected, canonicalStr)
    }
}
