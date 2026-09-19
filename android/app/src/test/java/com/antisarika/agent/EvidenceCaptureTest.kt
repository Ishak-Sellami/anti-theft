package com.antisarika.agent

import org.junit.Assert.assertEquals
import org.junit.Test
import java.security.MessageDigest

class EvidenceCaptureTest {

    @Test
    fun testSha256IntegrityCalculation() {
        val sampleData = "anti_sarika_forensic_evidence_payload_test".toByteArray(Charsets.UTF_8)
        val digest = MessageDigest.getInstance("SHA-256")
        val hashBytes = digest.digest(sampleData)
        val calculatedHash = hashBytes.joinToString("") { "%02x".format(it) }

        assertEquals(64, calculatedHash.length)

        // Verify repeatability
        val hashBytes2 = MessageDigest.getInstance("SHA-256").digest(sampleData)
        val calculatedHash2 = hashBytes2.joinToString("") { "%02x".format(it) }
        assertEquals(calculatedHash, calculatedHash2)
    }
}
