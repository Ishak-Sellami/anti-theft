package com.antisarika.agent.core.network

import android.content.Context
import android.net.ConnectivityManager
import android.net.Network
import android.net.NetworkCapabilities
import android.net.NetworkRequest
import com.antisarika.agent.core.logging.SafeLogger
import com.antisarika.agent.core.model.ConnectivityState
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow

class NetworkMonitor(context: Context) {
    companion object {
        private const val TAG = "NetworkMonitor"
    }

    private val connectivityManager = context.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
    private val _networkState = MutableStateFlow(getCurrentConnectivityState())
    val networkState: StateFlow<ConnectivityState> = _networkState

    init {
        val request = NetworkRequest.Builder()
            .addCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET)
            .build()

        connectivityManager.registerNetworkCallback(request, object : ConnectivityManager.NetworkCallback() {
            override fun onAvailable(network: Network) {
                SafeLogger.i(TAG, "Network became available -> ONLINE")
                _networkState.value = ConnectivityState.ONLINE
            }

            override fun onLost(network: Network) {
                SafeLogger.w(TAG, "Network lost -> evaluating state")
                _networkState.value = getCurrentConnectivityState()
            }

            override fun onCapabilitiesChanged(network: Network, networkCapabilities: NetworkCapabilities) {
                val hasInternet = networkCapabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET)
                val isValidated = networkCapabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_VALIDATED)
                if (hasInternet && isValidated) {
                    _networkState.value = ConnectivityState.ONLINE
                } else if (hasInternet) {
                    _networkState.value = ConnectivityState.DEGRADED
                }
            }
        })
    }

    fun getCurrentConnectivityState(): ConnectivityState {
        val activeNetwork = connectivityManager.activeNetwork ?: return ConnectivityState.OFFLINE
        val caps = connectivityManager.getNetworkCapabilities(activeNetwork) ?: return ConnectivityState.OFFLINE
        return when {
            caps.hasCapability(NetworkCapabilities.NET_CAPABILITY_VALIDATED) -> ConnectivityState.ONLINE
            caps.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET) -> ConnectivityState.DEGRADED
            else -> ConnectivityState.OFFLINE
        }
    }
}
