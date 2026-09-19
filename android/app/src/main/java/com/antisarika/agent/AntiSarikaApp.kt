package com.antisarika.agent

import android.app.Application
import androidx.work.*
import com.antisarika.agent.background.AgentForegroundService
import com.antisarika.agent.background.HeartbeatWorker
import com.antisarika.agent.background.TelemetrySyncWorker
import com.antisarika.agent.commands.CommandExecutor
import com.antisarika.agent.commands.CommandManager
import com.antisarika.agent.commands.CommandVerifier
import com.antisarika.agent.core.crypto.DeviceSigner
import com.antisarika.agent.core.crypto.KeystoreManager
import com.antisarika.agent.core.logging.SafeLogger
import com.antisarika.agent.core.model.SecurityState
import com.antisarika.agent.core.network.ApiClient
import com.antisarika.agent.core.network.NetworkMonitor
import com.antisarika.agent.core.network.WebSocketManager
import com.antisarika.agent.core.storage.AntiSarikaDatabase
import com.antisarika.agent.dpc.DevicePolicyController
import com.antisarika.agent.enrollment.EnrollmentManager
import com.antisarika.agent.evidence.EvidenceCaptureManager
import com.antisarika.agent.evidence.EvidenceStorage
import com.antisarika.agent.policy.RecoveryPolicyEngine
import com.antisarika.agent.securityevents.SecurityEventDetector
import com.antisarika.agent.state.StateManager
import com.antisarika.agent.telemetry.HealthMonitor
import com.antisarika.agent.telemetry.LocationTracker
import com.antisarika.agent.telemetry.StoreAndForwardEngine
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch
import java.util.concurrent.TimeUnit

class AntiSarikaApp : Application() {

    companion object {
        private const val TAG = "AntiSarikaApp"
    }

    val appScope = CoroutineScope(Dispatchers.IO + SupervisorJob())

    lateinit var database: AntiSarikaDatabase
    lateinit var keystoreManager: KeystoreManager
    lateinit var deviceSigner: DeviceSigner
    lateinit var apiClient: ApiClient
    lateinit var webSocketManager: WebSocketManager
    lateinit var networkMonitor: NetworkMonitor
    lateinit var dpc: DevicePolicyController
    lateinit var stateManager: StateManager
    lateinit var policyEngine: RecoveryPolicyEngine
    lateinit var locationTracker: LocationTracker
    lateinit var healthMonitor: HealthMonitor
    lateinit var storeAndForwardEngine: StoreAndForwardEngine
    lateinit var commandVerifier: CommandVerifier
    lateinit var commandExecutor: CommandExecutor
    lateinit var commandManager: CommandManager
    lateinit var securityEventDetector: SecurityEventDetector
    lateinit var evidenceStorage: EvidenceStorage
    lateinit var evidenceCaptureManager: EvidenceCaptureManager
    lateinit var enrollmentManager: EnrollmentManager

    override fun onCreate() {
        super.onCreate()
        SafeLogger.i(TAG, "Initializing Anti-Sarika Agent Application...")

        // 1. Storage & Crypto
        database = AntiSarikaDatabase.getInstance(this)
        keystoreManager = KeystoreManager(this)
        deviceSigner = DeviceSigner(keystoreManager)

        // 2. Network & DPC
        apiClient = ApiClient()
        webSocketManager = WebSocketManager()
        networkMonitor = NetworkMonitor(this)
        dpc = DevicePolicyController(this)

        // 3. State & Policies
        stateManager = StateManager(database, appScope)
        policyEngine = RecoveryPolicyEngine(database, appScope)

        // 4. Telemetry & Hardware Monitors
        locationTracker = LocationTracker(this)
        healthMonitor = HealthMonitor(this)
        storeAndForwardEngine = StoreAndForwardEngine(
            database = database,
            apiClient = apiClient,
            deviceSigner = deviceSigner,
            stateManager = stateManager,
            policyEngine = policyEngine,
            locationTracker = locationTracker,
            healthMonitor = healthMonitor
        )

        // 5. Commands
        commandVerifier = CommandVerifier(database, deviceSigner, stateManager)
        commandExecutor = CommandExecutor(this, stateManager, policyEngine, dpc, storeAndForwardEngine)
        commandManager = CommandManager(database, apiClient, deviceSigner, commandVerifier, commandExecutor)

        // 6. Security Events & Evidence
        securityEventDetector = SecurityEventDetector(database, apiClient, deviceSigner, stateManager)
        evidenceStorage = EvidenceStorage(this)
        evidenceCaptureManager = EvidenceCaptureManager(
            database = database,
            apiClient = apiClient,
            deviceSigner = deviceSigner,
            stateManager = stateManager,
            evidenceStorage = evidenceStorage,
            locationTracker = locationTracker,
            healthMonitor = healthMonitor
        )

        // 7. Enrollment Manager
        enrollmentManager = EnrollmentManager(
            apiClient = apiClient,
            keystoreManager = keystoreManager,
            deviceSigner = deviceSigner,
            database = database,
            dpc = dpc
        )

        // Observe network state and update StateManager
        appScope.launch {
            networkMonitor.networkState.collect { connState ->
                stateManager.updateConnectivityState(connState)
                if (connState == com.antisarika.agent.core.model.ConnectivityState.ONLINE) {
                    storeAndForwardEngine.syncPendingTelemetry()
                    securityEventDetector.dispatchPendingEvents()
                    commandManager.pollAndProcessPendingCommands()
                }
            }
        }

        // Observe SecurityState and manage Foreground Service
        appScope.launch {
            stateManager.compositeState.collect { state ->
                if (state.securityState == SecurityState.STOLEN || state.securityState == SecurityState.RECOVERY) {
                    AgentForegroundService.startService(this@AntiSarikaApp)
                }
            }
        }

        // Schedule periodic background sync workers
        scheduleBackgroundWorkers()
    }

    private fun scheduleBackgroundWorkers() {
        val workManager = WorkManager.getInstance(this)

        val heartbeatWork = PeriodicWorkRequestBuilder<HeartbeatWorker>(15, TimeUnit.MINUTES)
            .setConstraints(Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build())
            .build()

        val telemetrySyncWork = PeriodicWorkRequestBuilder<TelemetrySyncWorker>(15, TimeUnit.MINUTES)
            .build()

        workManager.enqueueUniquePeriodicWork(
            "anti_sarika_heartbeat",
            ExistingPeriodicWorkPolicy.KEEP,
            heartbeatWork
        )

        workManager.enqueueUniquePeriodicWork(
            "anti_sarika_telemetry_sync",
            ExistingPeriodicWorkPolicy.KEEP,
            telemetrySyncWork
        )
    }
}
