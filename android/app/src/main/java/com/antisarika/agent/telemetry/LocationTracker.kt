package com.antisarika.agent.telemetry

import android.annotation.SuppressLint
import android.content.Context
import android.location.Location
import android.location.LocationManager
import com.antisarika.agent.core.logging.SafeLogger
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

data class LocationFix(
    val latitude: Double,
    val longitude: Double,
    val altitude: Double?,
    val accuracy: Float?,
    val speed: Float?,
    val bearing: Float?,
    val provider: String,
    val timeMillis: Long
)

class LocationTracker(private val context: Context) {

    companion object {
        private const val TAG = "LocationTracker"
    }

    private val locationManager = context.getSystemService(Context.LOCATION_SERVICE) as LocationManager

    @SuppressLint("MissingPermission")
    suspend fun getLastKnownLocation(): LocationFix? = withContext(Dispatchers.IO) {
        return@withContext try {
            val providers = listOf(
                LocationManager.GPS_PROVIDER,
                LocationManager.NETWORK_PROVIDER,
                LocationManager.PASSIVE_PROVIDER
            )

            var bestLocation: Location? = null
            for (provider in providers) {
                if (locationManager.isProviderEnabled(provider)) {
                    val loc = locationManager.getLastKnownLocation(provider)
                    if (loc != null) {
                        if (bestLocation == null || loc.accuracy < bestLocation.accuracy) {
                            bestLocation = loc
                        }
                    }
                }
            }

            bestLocation?.let { loc ->
                LocationFix(
                    latitude = loc.latitude,
                    longitude = loc.longitude,
                    altitude = if (loc.hasAltitude()) loc.altitude else null,
                    accuracy = if (loc.hasAccuracy()) loc.accuracy else null,
                    speed = if (loc.hasSpeed()) loc.speed else null,
                    bearing = if (loc.hasBearing()) loc.bearing else null,
                    provider = loc.provider ?: "unknown",
                    timeMillis = loc.time
                )
            }
        } catch (e: SecurityException) {
            SafeLogger.w(TAG, "Location permission missing (PLATFORM_LIMITATION)")
            null
        } catch (e: Exception) {
            SafeLogger.e(TAG, "Error acquiring location", e)
            null
        }
    }
}
