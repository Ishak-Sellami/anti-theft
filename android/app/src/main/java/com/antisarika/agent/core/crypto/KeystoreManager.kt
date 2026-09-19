package com.antisarika.agent.core.crypto

import android.content.Context
import android.content.pm.PackageManager
import android.os.Build
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyInfo
import android.security.keystore.KeyProperties
import android.util.Base64
import com.antisarika.agent.core.logging.SafeLogger
import java.security.KeyFactory
import java.security.KeyPair
import java.security.KeyPairGenerator
import java.security.KeyStore
import java.security.MessageDigest
import java.security.PrivateKey
import java.security.PublicKey
import java.security.Signature
import java.security.spec.ECGenParameterSpec

class KeystoreManager(private val context: Context) {

    companion object {
        const val KEY_ALIAS = "anti_sarika_device_key"
        private const val ANDROID_KEYSTORE = "AndroidKeyStore"
        private const val TAG = "KeystoreManager"
    }

    private val keyStore: KeyStore = KeyStore.getInstance(ANDROID_KEYSTORE).apply {
        load(null)
    }

    /**
     * Ensures an ECDSA SecP256r1 keypair exists in AndroidKeyStore.
     * Generates a new keypair if not present, preferring StrongBox / TEE.
     */
    @Synchronized
    fun getOrCreateDeviceKeyPair(): KeyPair {
        if (keyStore.containsAlias(KEY_ALIAS)) {
            val privateKey = keyStore.getKey(KEY_ALIAS, null) as? PrivateKey
            val certificate = keyStore.getCertificate(KEY_ALIAS)
            val publicKey = certificate?.publicKey
            if (privateKey != null && publicKey != null) {
                return KeyPair(publicKey, privateKey)
            }
        }
        return generateDeviceKeyPair()
    }

    private fun generateDeviceKeyPair(): KeyPair {
        SafeLogger.i(TAG, "Generating new device keypair in AndroidKeyStore...")
        val kpg = KeyPairGenerator.getInstance(KeyProperties.KEY_ALGORITHM_EC, ANDROID_KEYSTORE)

        val hasStrongBox = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
            context.packageManager.hasSystemFeature(PackageManager.FEATURE_STRONGBOX_KEYSTORE)
        } else {
            false
        }

        val builder = KeyGenParameterSpec.Builder(
            KEY_ALIAS,
            KeyProperties.PURPOSE_SIGN or KeyProperties.PURPOSE_VERIFY
        )
            .setAlgorithmParameterSpec(ECGenParameterSpec("secp256r1"))
            .setDigests(KeyProperties.DIGEST_SHA256)
            .setUserAuthenticationRequired(false)

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P && hasStrongBox) {
            try {
                builder.setIsStrongBoxBacked(true)
            } catch (e: Exception) {
                SafeLogger.w(TAG, "Failed to enable StrongBox, falling back to standard TEE", e)
            }
        }

        try {
            kpg.initialize(builder.build())
            val keyPair = kpg.generateKeyPair()
            SafeLogger.i(TAG, "Device keypair generated successfully. Hardware-backed: ${isHardwareBacked(keyPair.private)}")
            return keyPair
        } catch (e: Exception) {
            SafeLogger.w(TAG, "StrongBox generation failed, retrying with standard TEE KeyGenParameterSpec", e)
            val fallbackBuilder = KeyGenParameterSpec.Builder(
                KEY_ALIAS,
                KeyProperties.PURPOSE_SIGN or KeyProperties.PURPOSE_VERIFY
            )
                .setAlgorithmParameterSpec(ECGenParameterSpec("secp256r1"))
                .setDigests(KeyProperties.DIGEST_SHA256)
                .setUserAuthenticationRequired(false)

            kpg.initialize(fallbackBuilder.build())
            return kpg.generateKeyPair()
        }
    }

    fun isHardwareBacked(privateKey: PrivateKey): Boolean {
        return try {
            val factory = KeyFactory.getInstance(privateKey.algorithm, ANDROID_KEYSTORE)
            val keyInfo = factory.getKeySpec(privateKey, KeyInfo::class.java)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                keyInfo.securityLevel == KeyProperties.SECURITY_LEVEL_TRUSTED_ENVIRONMENT ||
                        keyInfo.securityLevel == KeyProperties.SECURITY_LEVEL_STRONGBOX
            } else {
                keyInfo.isInsideSecureHardware
            }
        } catch (e: Exception) {
            false
        }
    }

    /**
     * Exports the device public key formatted as PEM standard string.
     */
    fun getPublicKeyPem(publicKey: PublicKey): String {
        val derBytes = publicKey.encoded
        val base64 = Base64.encodeToString(derBytes, Base64.NO_WRAP)
        return "-----BEGIN PUBLIC KEY-----\n$base64\n-----END PUBLIC KEY-----\n"
    }

    /**
     * Calculates canonical SHA-256 fingerprint hex string of the public key DER bytes.
     */
    fun computePublicKeyFingerprint(publicKey: PublicKey): String {
        val digest = MessageDigest.getInstance("SHA-256")
        val hashBytes = digest.digest(publicKey.encoded)
        return hashBytes.joinToString("") { "%02x".format(it) }
    }

    /**
     * Signs data bytes with the Keystore private key using SHA256withECDSA.
     * Returns Base64-encoded ASN.1 signature string.
     */
    fun sign(data: ByteArray): String {
        val keyPair = getOrCreateDeviceKeyPair()
        val signer = Signature.getInstance("SHA256withECDSA")
        signer.initSign(keyPair.private)
        signer.update(data)
        val signatureBytes = signer.sign()
        return Base64.encodeToString(signatureBytes, Base64.NO_WRAP)
    }
}
