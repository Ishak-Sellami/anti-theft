package com.antisarika.agent.ui

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.viewModels
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.antisarika.agent.core.model.SecurityState
import com.antisarika.agent.ui.theme.AntiSarikaTheme

class MainActivity : ComponentActivity() {

    private val viewModel: DashboardViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            AntiSarikaTheme {
                val uiState by viewModel.uiState.collectAsState()

                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    if (uiState.isEnrolled) {
                        DashboardScreen(
                            uiState = uiState,
                            onRefresh = { viewModel.refreshDashboard() },
                            onManualSync = { viewModel.triggerManualSync() }
                        )
                    } else {
                        EnrollmentScreen(
                            uiState = uiState,
                            onEnroll = { token, name, pubKey, server ->
                                viewModel.enrollDevice(token, name, pubKey, server)
                            }
                        )
                    }
                }
            }
        }
    }
}

@Composable
fun DashboardScreen(
    uiState: DashboardUiState,
    onRefresh: () -> Unit,
    onManualSync: () -> Unit
) {
    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        item {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "Anti-Sarika Agent",
                    style = MaterialTheme.typography.headlineMedium,
                    fontWeight = FontWeight.Bold,
                    color = MaterialTheme.colorScheme.primary
                )
                Button(onClick = onManualSync) {
                    Text("Sync Now")
                }
            }
        }

        // Security State Indicator Card
        item {
            val secState = uiState.compositeState?.securityState ?: SecurityState.NORMAL
            val stateColor = when (secState) {
                SecurityState.NORMAL -> Color(0xFF10B981)
                SecurityState.PROTECTED -> Color(0xFF3B82F6)
                SecurityState.STOLEN -> Color(0xFFEF4444)
                SecurityState.RECOVERY -> Color(0xFFF59E0B)
            }

            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(containerColor = stateColor.copy(alpha = 0.15f)),
                shape = RoundedCornerShape(12.dp)
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text("CURRENT SECURITY STATE", fontSize = 12.sp, fontWeight = FontWeight.SemiBold, color = stateColor)
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        text = secState.name,
                        fontSize = 28.sp,
                        fontWeight = FontWeight.Black,
                        color = stateColor
                    )
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        text = "Connectivity: ${uiState.compositeState?.connectivityState?.name ?: "UNKNOWN"}  •  Power: ${uiState.compositeState?.powerState?.name ?: "UNKNOWN"} (${uiState.batteryLevel ?: 0}%)",
                        fontSize = 13.sp,
                        color = MaterialTheme.colorScheme.onSurface
                    )
                }
            }
        }

        // Device Identity Card
        item {
            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                shape = RoundedCornerShape(12.dp)
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text("DEVICE IDENTITY", fontWeight = FontWeight.Bold, fontSize = 14.sp)
                    Spacer(modifier = Modifier.height(8.dp))
                    Text("Device Name: ${uiState.deviceName}", fontSize = 13.sp)
                    Text("Device ID: ${uiState.deviceId}", fontSize = 12.sp, fontFamily = FontFamily.Monospace)
                    Spacer(modifier = Modifier.height(4.dp))
                    Text("Public Key Fingerprint:", fontSize = 12.sp)
                    Text(uiState.fingerprint, fontSize = 11.sp, fontFamily = FontFamily.Monospace, color = MaterialTheme.colorScheme.primary)
                }
            }
        }

        // Device Owner & DPC Status Card
        item {
            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                shape = RoundedCornerShape(12.dp)
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text("MANAGEMENT & POLICIES", fontWeight = FontWeight.Bold, fontSize = 14.sp)
                    Spacer(modifier = Modifier.height(8.dp))
                    Text("Device Owner: ${if (uiState.isDeviceOwner) "ACTIVE (Full Enforcement)" else "INACTIVE (App Mode)"}", fontSize = 13.sp)
                    Text("Device Admin: ${if (uiState.isDeviceAdmin) "ENABLED" else "DISABLED"}", fontSize = 13.sp)
                    Text("Active Policy ID: ${uiState.activePolicyId}", fontSize = 13.sp)
                    Text("Offline Telemetry Queue: ${uiState.pendingTelemetryCount} records pending", fontSize = 13.sp)
                }
            }
        }

        // Recent Audit Activity
        item {
            Text("RECENT SECURITY AUDIT TRAIL", fontWeight = FontWeight.Bold, fontSize = 14.sp, modifier = Modifier.padding(top = 8.dp))
        }

        items(uiState.recentLogs) { log ->
            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface.copy(alpha = 0.6f)),
                shape = RoundedCornerShape(8.dp)
            ) {
                Column(modifier = Modifier.padding(12.dp)) {
                    Text("${log.action} (${log.actor})", fontWeight = FontWeight.SemiBold, fontSize = 12.sp)
                    Text(log.details, fontSize = 11.sp, color = Color.Gray)
                }
            }
        }
    }
}

@Composable
fun EnrollmentScreen(
    uiState: DashboardUiState,
    onEnroll: (token: String, name: String, pubKey: String, server: String) -> Unit
) {
    var serverUrl by remember { mutableStateOf("http://10.0.2.2:8000") }
    var deviceName by remember { mutableStateOf("Android Agent") }
    var enrollmentToken by remember { mutableStateOf("") }
    var backendPublicKeyPem by remember { mutableStateOf("") }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(24.dp),
        verticalArrangement = Arrangement.Center
    ) {
        Text("Anti-Sarika Agent", fontSize = 24.sp, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.primary)
        Text("Device Enrollment & Onboarding", fontSize = 14.sp, color = Color.Gray)
        Spacer(modifier = Modifier.height(20.dp))

        OutlinedTextField(
            value = serverUrl,
            onValueChange = { serverUrl = it },
            label = { Text("Control Plane Server URL") },
            modifier = Modifier.fillMaxWidth()
        )
        Spacer(modifier = Modifier.height(10.dp))

        OutlinedTextField(
            value = deviceName,
            onValueChange = { deviceName = it },
            label = { Text("Device Name") },
            modifier = Modifier.fillMaxWidth()
        )
        Spacer(modifier = Modifier.height(10.dp))

        OutlinedTextField(
            value = enrollmentToken,
            onValueChange = { enrollmentToken = it },
            label = { Text("Pairing / Enrollment Token") },
            modifier = Modifier.fillMaxWidth()
        )
        Spacer(modifier = Modifier.height(10.dp))

        OutlinedTextField(
            value = backendPublicKeyPem,
            onValueChange = { backendPublicKeyPem = it },
            label = { Text("Backend Public Key PEM") },
            modifier = Modifier.fillMaxWidth(),
            minLines = 3
        )
        Spacer(modifier = Modifier.height(20.dp))

        if (uiState.enrollmentError != null) {
            Text("Error: ${uiState.enrollmentError}", color = Color.Red, fontSize = 12.sp)
            Spacer(modifier = Modifier.height(10.dp))
        }

        Button(
            onClick = { onEnroll(enrollmentToken, deviceName, backendPublicKeyPem, serverUrl) },
            enabled = !uiState.enrollmentInProgress && enrollmentToken.isNotBlank(),
            modifier = Modifier.fillMaxWidth()
        ) {
            if (uiState.enrollmentInProgress) {
                CircularProgressIndicator(modifier = Modifier.size(20.dp), color = Color.White)
            } else {
                Text("Complete Enrollment")
            }
        }
    }
}
