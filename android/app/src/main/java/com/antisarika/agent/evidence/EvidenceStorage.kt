package com.antisarika.agent.evidence

import android.content.Context
import com.antisarika.agent.core.logging.SafeLogger
import java.io.File
import java.io.FileOutputStream
import java.security.MessageDigest

class EvidenceStorage(private val context: Context) {

    companion object {
        private const val TAG = "EvidenceStorage"
        private const val EVIDENCE_DIR_NAME = "stolen_evidence_vault"
    }

    private val evidenceDir: File
        get() {
            val dir = File(context.filesDir, EVIDENCE_DIR_NAME)
            if (!dir.exists()) {
                dir.mkdirs()
            }
            return dir
        }

    fun storeEvidenceBytes(evidenceId: String, data: ByteArray, extension: String = "bin"): File {
        val file = File(evidenceDir, "$evidenceId.$extension")
        FileOutputStream(file).use { fos ->
            fos.write(data)
            fos.flush()
        }
        SafeLogger.d(TAG, "Stored evidence file: ${file.absolutePath} (${data.size} bytes)")
        return file
    }

    fun computeSha256(data: ByteArray): String {
        val digest = MessageDigest.getInstance("SHA-256")
        val hash = digest.digest(data)
        return hash.joinToString("") { "%02x".format(it) }
    }

    fun computeFileSha256(file: File): String {
        return computeSha256(file.readBytes())
    }

    fun removeEvidenceFile(evidenceId: String) {
        val files = evidenceDir.listFiles { _, name -> name.startsWith(evidenceId) }
        files?.forEach { f ->
            if (f.delete()) {
                SafeLogger.d(TAG, "Deleted local evidence copy: ${f.name}")
            }
        }
    }
}
