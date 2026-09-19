package com.antisarika.agent.core.crypto

import android.util.Base64
import com.antisarika.agent.core.logging.SafeLogger
import java.security.KeyFactory
import java.security.PublicKey
import java.security.Signature
import java.security.spec.X509EncodedKeySpec

class DeviceSigner(private val keystoreManager: KeystoreManager) {

    companion object {
        private const val TAG = "DeviceSigner"
    }

    /**
     * Serializes payload to canonical JSON bytes and signs with Keystore device private key.
     */
    fun signPayload(payload: Map<String, Any?>): String {
        val canonicalBytes = CanonicalJson.canonicalize(payload)
        return keystoreManager.sign(canonicalBytes)
    }

    /**
     * Verifies that a base64 signature over canonical JSON matches the given backend public key PEM.
     */
    fun verifyBackendSignature(
        payload: Map<String, Any?>,
        signatureB64: String,
        backendPublicKeyPem: String
    ): Boolean {
        return try {
            val canonicalBytes = CanonicalJson.canonicalize(payload)
            val signatureBytes = Base64.decode(signatureB64, Base64.DEFAULT)
            val publicKey = parsePublicKeyFromPem(backendPublicKeyPem)

            val verifier = Signature.getInstance("SHA256withECDSA")
            verifier.initVerify(publicKey)
            verifier.update(canonicalBytes)
            val isValid = verifier.verify(signatureBytes)
            if (!isValid) {
                SafeLogger.w(TAG, "Backend signature verification failed (invalid signature)")
            }
            isValid
        } catch (e: Exception) {
            SafeLogger.e(TAG, "Error verifying backend signature", e)
            false
        }
    }

    private fun parsePublicKeyFromPem(pem: String): PublicKey {
        val cleanPem = pem
            .replace("-----BEGIN PUBLIC KEY-----", "")
            .replace("-----END PUBLIC KEY-----", "")
            .replace("\\s+".toRegex(), "")
        val derBytes = Base64.decode(cleanPem, Base64.DEFAULT)
        val spec = X509EncodedKeySpec(derBytes)
        val kf = KeyFactory.getInstance("EC")
        return kf.generatePublic(spec)
    }
}
