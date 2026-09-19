package com.antisarika.agent

import com.antisarika.agent.core.model.PowerState
import com.antisarika.agent.core.model.PowerStatePolicy
import com.antisarika.agent.core.model.RecoveryPolicyConfig
import com.antisarika.agent.policy.RecoveryPolicyEngine
import org.junit.Assert.*
import org.junit.Test

class RecoveryPolicyTest {

    @Test
    fun testDefaultPolicyCreation() {
        val policy = RecoveryPolicyEngine.createDefaultStolenPolicy()
        assertEquals("pol_stolen_default_v1", policy.policyId)
        assertEquals("STOLEN", policy.securityState)
        assertTrue(policy.powerStateOverrides.containsKey("NORMAL"))
        assertTrue(policy.powerStateOverrides.containsKey("LOW"))
        assertTrue(policy.powerStateOverrides.containsKey("CRITICAL"))

        val normalPower = policy.powerStateOverrides["NORMAL"]!!
        assertEquals(15000L, normalPower.locationIntervalMs)
        assertEquals(10000L, normalPower.locationFastestIntervalMs)

        val criticalPower = policy.powerStateOverrides["CRITICAL"]!!
        assertEquals(300000L, criticalPower.locationIntervalMs)
    }

    @Test
    fun testPolicyValidation() {
        val validPolicy = RecoveryPolicyEngine.createDefaultStolenPolicy()
        assertTrue(validPolicy.policyId.isNotBlank())
        assertTrue(validPolicy.powerStateOverrides["NORMAL"]!!.locationIntervalMs >= 1000L)

        val invalidPolicy = validPolicy.copy(policyId = "")
        assertFalse(invalidPolicy.policyId.isNotBlank())
    }
}
