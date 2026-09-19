import React, { useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle, Polyline, useMap } from 'react-leaflet';
import L from 'leaflet';
import { LocationTelemetry } from '../../types';

// Custom SVG map marker
const createCustomIcon = (isStolen: boolean) => {
  const color = isStolen ? '#EF4444' : '#38BDF8';
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="${color}" width="32" height="32">
      <path d="M12 0C7.58 0 4 3.58 4 8c0 5.25 8 16 8 16s8-10.75 8-16c0-4.42-3.58-8-8-8zm0 11c-1.66 0-3-1.34-3-3s1.34-3 3-3 3 1.34 3 3-1.34 3-3 3z"/>
    </svg>
  `;
  return L.divIcon({
    html: svg,
    className: 'custom-map-marker',
    iconSize: [32, 32],
    iconAnchor: [16, 32],
    popupAnchor: [0, -32],
  });
};

function ChangeMapView({ coords }: { coords: [number, number] }) {
  const map = useMap();
  useEffect(() => {
    if (coords[0] !== 0 && coords[1] !== 0) {
      map.setView(coords, map.getZoom() || 15);
    }
  }, [coords, map]);
  return null;
}

interface LiveMapProps {
  currentLocation?: {
    latitude: number;
    longitude: number;
    accuracy?: number;
    recordedAt?: string;
    battery?: number;
  } | null;
  history?: LocationTelemetry[];
  isStolen?: boolean;
  className?: string;
}

export const LiveMap: React.FC<LiveMapProps> = ({
  currentLocation,
  history = [],
  isStolen = false,
  className = 'h-[400px]',
}) => {
  const defaultCenter: [number, number] = [52.52, 13.405]; // Berlin default fallback
  const center: [number, number] =
    currentLocation && currentLocation.latitude && currentLocation.longitude
      ? [currentLocation.latitude, currentLocation.longitude]
      : history.length > 0
      ? [history[0].latitude, history[0].longitude]
      : defaultCenter;

  const polylineCoords: [number, number][] = history
    .filter((h) => h.latitude && h.longitude && (h.latitude !== 0 || h.longitude !== 0))
    .map((h) => [h.latitude, h.longitude]);

  return (
    <div className={`relative w-full rounded-2xl overflow-hidden border border-slate-800 shadow-xl ${className}`}>
      <MapContainer
        center={center}
        zoom={15}
        scrollWheelZoom={true}
        style={{ height: '100%', width: '100%', backgroundColor: '#0B1120' }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        <ChangeMapView coords={center} />

        {/* Trail polyline */}
        {polylineCoords.length > 1 && (
          <Polyline
            positions={polylineCoords}
            pathOptions={{
              color: isStolen ? '#EF4444' : '#38BDF8',
              weight: 4,
              opacity: 0.7,
              dashArray: isStolen ? '6, 6' : undefined,
            }}
          />
        )}

        {/* Current Location Marker & Accuracy Circle */}
        {currentLocation && currentLocation.latitude && currentLocation.longitude && (
          <>
            <Marker
              position={[currentLocation.latitude, currentLocation.longitude]}
              icon={createCustomIcon(isStolen)}
            >
              <Popup className="custom-popup">
                <div className="p-1 space-y-1 font-sans text-xs">
                  <div className="font-bold text-slate-900">
                    {isStolen ? '🚨 STOLEN DEVICE LOCATION' : 'Device Location'}
                  </div>
                  <div>
                    GPS: {currentLocation.latitude.toFixed(5)}, {currentLocation.longitude.toFixed(5)}
                  </div>
                  {currentLocation.accuracy && (
                    <div>Accuracy: ±{currentLocation.accuracy.toFixed(1)}m</div>
                  )}
                  {currentLocation.battery !== undefined && (
                    <div>Battery: {currentLocation.battery}%</div>
                  )}
                  {currentLocation.recordedAt && (
                    <div className="text-[10px] text-slate-500">
                      Fix time: {new Date(currentLocation.recordedAt).toLocaleString()}
                    </div>
                  )}
                </div>
              </Popup>
            </Marker>

            {currentLocation.accuracy && (
              <Circle
                center={[currentLocation.latitude, currentLocation.longitude]}
                radius={currentLocation.accuracy}
                pathOptions={{
                  color: isStolen ? '#EF4444' : '#38BDF8',
                  fillColor: isStolen ? '#EF4444' : '#38BDF8',
                  fillOpacity: 0.15,
                  weight: 1,
                }}
              />
            )}
          </>
        )}
      </MapContainer>
    </div>
  );
};
