package com.antisarika.agent.ui

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.antisarika.agent.AntiSarikaApp
import com.antisarika.agent.core.model.DeviceCompositeState
import com.antisarika.agent.core.model.SecurityState
import com.antisarika.agent.core.storage.entities.AuditLogEntity
import com.antisarika.agent.core.storage.entities.DeviceConfigEntity
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch

data class DashboardUiState(
    val isEnrolled: Boolean = false,
    val deviceId: String = "",
    val deviceName: String = "",
    val fingerprint: String = "",
    val compositeState: DeviceCompositeState? = null,
    val activePolicyId: String = "",
    val batteryLevel: Int? = null,
    val isCharging: Boolean = false,
    val isDeviceAdmin: Boolean = false,
    val isDeviceOwner: Boolean = false,
    val pendingTelemetryCount: Int = 0,
    val recentLogs: List<AuditLogEntity> = emptyList(),
    val enrollmentInProgress: Boolean = false,
    val enrollmentError: String? = null
)

class DashboardViewModel(application: Application) : AndroidViewModel(application) {

    private val app = getApplication<AntiSarikaApp>()
    private val _uiState = MutableStateFlow(DashboardUiState())
    val uiState: StateFlow<DashboardUiState> = _uiState

    init {
        refreshDashboard()
        observeStreams()
    }

    private fun observeStreams() {
        viewModelScope.launch {
            app.stateManager.compositeState.collect { compState ->
                _uiState.value = _uiState.value.copy(compositeState = compState)
            }
        }

        viewModelScope.launch {
            app.database.deviceConfigDao().observeConfig().collect { config ->
                if (config != null) {
                    val keyPair = app.keystoreManager.getOrCreateDeviceKeyPair()
                    val fp = app.keystoreManager.computePublicKeyFingerprint(keyPair.public)
                    _uiState.value = _uiState.value.copy(
                        isEnrolled = config.isEnrolled,
                        deviceId = config.deviceId,
                        deviceName = config.deviceName,
                        fingerprint = fp
                    )
                }
            }
        }
    }

    fun refreshDashboard() {
        viewModelScope.launch {
            val config = app.database.deviceConfigDao().getConfig()
            val health = app.healthMonitor.getHealthSnapshot()
            val keyPair = app.keystoreManager.getOrCreateDeviceKeyPair()
            val fp = app.keystoreManager.computePublicKeyFingerprint(keyPair.public)
            val pendingCount = app.database.telemetryDao().getPendingCount()
            val logs = app.database.auditLogDao().getRecentLogs(10)
            val policy = app.policyEngine.activePolicy.value

            _uiState.value = _uiState.value.copy(
                isEnrolled = config?.isEnrolled ?: false,
                deviceId = config?.deviceId ?: "Not Enrolled",
                deviceName = config?.deviceName ?: "",
                fingerprint = fp,
                compositeState = app.stateManager.compositeState.value,
                activePolicyId = policy.policyId,
                batteryLevel = health.batteryLevel,
                isCharging = health.isCharging,
                isDeviceAdmin = app.dpc.isDeviceAdmin(),
                isDeviceOwner = app.dpc.isDeviceOwner(),
                pendingTelemetryCount = pendingCount,
                recentLogs = logs
            )
        }
    }

    fun enrollDevice(enrollmentToken: String, deviceName: String, backendPublicKeyPem: String, serverUrl: String) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(enrollmentInProgress = true, enrollmentError = null)
            app.apiClient.updateBaseUrl(serverUrl)

            val result = app.enrollmentManager.enrollDevice(
                enrollmentToken = enrollmentToken,
                deviceName = deviceName,
                backendPublicKeyPem = backendPublicKeyPem
            )

            if (result.isSuccess) {
                _uiState.value = _uiState.value.copy(enrollmentInProgress = false)
                refreshDashboard()
            } else {
                _uiState.value = _uiState.value.copy(
                    enrollmentInProgress = false,
                    enrollmentError = result.exceptionOrNull()?.message ?: "Enrollment failed"
                )
            }
        }
    }

    fun triggerManualSync() {
        viewModelScope.launch {
            app.storeAndForwardEngine.recordTelemetrySnapshot()
            app.storeAndForwardEngine.syncPendingTelemetry()
            app.securityEventDetector.dispatchPendingEvents()
            app.commandManager.pollAndProcessPendingCommands()
            refreshDashboard()
        }
    }
}
