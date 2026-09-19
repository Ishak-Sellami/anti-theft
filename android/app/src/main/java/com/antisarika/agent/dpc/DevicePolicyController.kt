package com.antisarika.agent.dpc

import android.app.admin.DevicePolicyManager
import android.content.ComponentName
import android.content.Context
import android.os.Build
import android.os.UserManager
import com.antisarika.agent.core.logging.SafeLogger

class DevicePolicyController(private val context: Context) {

    companion object {
        private const val TAG = "DevicePolicyController"
    }

    private val dpm: DevicePolicyManager =
        context.getSystemService(Context.DEVICE_POLICY_SERVICE) as DevicePolicyManager
    val adminComponent: ComponentName =
        ComponentName(context, AntiSarikaDeviceAdminReceiver::class.java)

    fun isDeviceAdmin(): Boolean {
        return dpm.isAdminActive(adminComponent)
    }

    fun isDeviceOwner(): Boolean {
        return dpm.isDeviceOwnerApp(context.packageName)
    }

    fun isProfileOwner(): Boolean {
        return dpm.isProfileOwnerApp(context.packageName)
    }

    /**
     * Enforces or relaxes factory reset restrictions using UserManager.DISALLOW_FACTORY_RESET.
     * Requires Device Owner mode.
     */
    fun setFactoryResetBlocked(blocked: Boolean): Boolean {
        return try {
            if (isDeviceOwner()) {
                if (blocked) {
                    dpm.addUserRestriction(adminComponent, UserManager.DISALLOW_FACTORY_RESET)
                    SafeLogger.i(TAG, "Applied UserManager.DISALLOW_FACTORY_RESET")
                } else {
                    dpm.clearUserRestriction(adminComponent, UserManager.DISALLOW_FACTORY_RESET)
                    SafeLogger.i(TAG, "Cleared UserManager.DISALLOW_FACTORY_RESET")
                }
                true
            } else {
                SafeLogger.w(TAG, "Cannot modify factory reset restriction: not Device Owner (PLATFORM_LIMITATION)")
                false
            }
        } catch (e: Exception) {
            SafeLogger.e(TAG, "Failed to update factory reset restriction", e)
            false
        }
    }

    /**
     * Prevents uninstalling Anti-Sarika agent APK.
     * Requires Device Owner mode.
     */
    fun setUninstallBlocked(blocked: Boolean): Boolean {
        return try {
            if (isDeviceOwner()) {
                dpm.setUninstallBlocked(adminComponent, context.packageName, blocked)
                SafeLogger.i(TAG, "Uninstall blocked state set to: $blocked")
                true
            } else {
                SafeLogger.w(TAG, "Cannot set uninstall blocked: not Device Owner (PLATFORM_LIMITATION)")
                false
            }
        } catch (e: Exception) {
            SafeLogger.e(TAG, "Failed to set uninstall blocked", e)
            false
        }
    }

    /**
     * Disables Keyguard Quick Settings / Status Bar pulldown to hinder Airplane Mode toggling while locked.
     */
    fun setKeyguardStatusBarDisabled(disabled: Boolean): Boolean {
        return try {
            if (isDeviceAdmin()) {
                val flags = if (disabled) DevicePolicyManager.KEYGUARD_DISABLE_STATUS_BAR else 0
                dpm.setKeyguardDisabledFeatures(adminComponent, flags)
                SafeLogger.i(TAG, "Keyguard status bar disabled: $disabled")
                true
            } else {
                false
            }
        } catch (e: Exception) {
            SafeLogger.e(TAG, "Failed to update keyguard disabled features", e)
            false
        }
    }

    /**
     * Immediately locks device screen.
     */
    fun lockDeviceNow(): Boolean {
        return try {
            if (isDeviceAdmin()) {
                dpm.lockNow()
                SafeLogger.i(TAG, "Device locked via DPC lockNow()")
                true
            } else {
                SafeLogger.w(TAG, "Cannot lock device: not Device Admin")
                false
            }
        } catch (e: Exception) {
            SafeLogger.e(TAG, "Failed to lock device", e)
            false
        }
    }

    /**
     * Wipes device data upon verified legitimate owner authorization.
     */
    fun performAuthorizedWipe(): Boolean {
        return try {
            if (isDeviceOwner()) {
                SafeLogger.w(TAG, "Executing authorized device wipe via DPC wipeData(0)...")
                dpm.wipeData(0)
                true
            } else {
                SafeLogger.w(TAG, "Cannot perform wipe: not Device Owner")
                false
            }
        } catch (e: Exception) {
            SafeLogger.e(TAG, "Failed to execute wipeData", e)
            false
        }
    }

    /**
     * Returns a capability matrix mapping platform management features to their availability.
     */
    fun getSupportedCapabilities(): Map<String, Boolean> {
        val isDO = isDeviceOwner()
        val isDA = isDeviceAdmin()
        return mapOf(
            "IS_DEVICE_ADMIN" to isDA,
            "IS_DEVICE_OWNER" to isDO,
            "BLOCK_SETTINGS_FACTORY_RESET" to isDO,
            "BLOCK_UNINSTALL" to isDO,
            "LOCK_KEYGUARD_STATUS_BAR" to isDA,
            "REMOTE_LOCK" to isDA,
            "REMOTE_WIPE" to isDO,
            "BLOCK_HARDWARE_RECOVERY_WIPE" to false, // PLATFORM_LIMITATION: Requires OEM bootloader lock / Knox Guard
            "BLOCK_HARD_SHUTDOWN" to false // PLATFORM_LIMITATION: Hardware PMIC long-press cannot be blocked by OS
        )
    }
}
