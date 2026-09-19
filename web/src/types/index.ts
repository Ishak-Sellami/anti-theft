export type UserRole = 'OWNER' | 'ADMIN' | 'INVESTIGATOR';

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export type SecurityState = 'NORMAL' | 'PROTECTED' | 'STOLEN' | 'RECOVERY';
export type ConnectivityState = 'ONLINE' | 'DEGRADED' | 'OFFLINE';
export type PowerState = 'NORMAL' | 'LOW' | 'CRITICAL';

export interface Device {
  id: string;
  owner_id: string;
  device_name: string;
  device_model?: string;
  os_version?: string;
  agent_version?: string;
  public_key_pem: string;
  public_key_fingerprint: string;
  security_state: SecurityState;
  connectivity_state: ConnectivityState;
  power_state: PowerState;
  battery_level?: number;
  is_charging: boolean;
  last_heartbeat_at?: string;
  last_known_latitude?: number;
  last_known_longitude?: number;
  last_known_accuracy?: number;
  last_known_location_at?: string;
  active_policy_id?: string;
  created_at: string;
  updated_at: string;
}

export interface EnrollmentInitiateResponse {
  enrollment_token: string;
  nonce: string;
  backend_public_key_pem: string;
  expires_at: string;
}

export interface LocationTelemetry {
  id: number;
  device_id: string;
  latitude: number;
  longitude: number;
  altitude?: number;
  accuracy?: number;
  speed?: number;
  bearing?: number;
  provider?: string;
  battery_level?: number;
  power_state?: PowerState;
  security_state?: SecurityState;
  connectivity_state?: ConnectivityState;
  network_metadata?: Record<string, any>;
  recorded_at: string;
  received_at: string;
}

export type CommandType =
  | 'SET_SECURITY_STATE'
  | 'UPDATE_POLICY'
  | 'TRIGGER_ALARM'
  | 'STOP_ALARM'
  | 'REQUEST_SNAPSHOT'
  | 'LOCK_DEVICE'
  | 'AUTHORIZE_WIPE';

export type CommandStatus =
  | 'PENDING'
  | 'DELIVERED'
  | 'ACKNOWLEDGED'
  | 'EXECUTED'
  | 'FAILED'
  | 'EXPIRED';

export interface DeviceCommand {
  id: string;
  device_id: string;
  issued_by: string;
  command_type: CommandType;
  payload?: Record<string, any>;
  nonce: string;
  status: CommandStatus;
  result_payload?: Record<string, any>;
  error_message?: string;
  expires_at: string;
  acknowledged_at?: string;
  executed_at?: string;
  signature: string;
  created_at: string;
}

export interface PowerStatePolicy {
  location_interval_ms: number;
  location_fastest_interval_ms: number;
  location_accuracy: string;
  heartbeat_interval_ms: number;
  telemetry_batch_size: number;
  enable_ble_beacon: boolean;
}

export interface RetryConfig {
  initial_retry_interval_ms: number;
  max_retry_interval_ms: number;
  backoff_multiplier: number;
  max_jitter_ms: number;
}

export interface StorageLimits {
  offline_queue_max_records: number;
  eviction_strategy: string;
}

export interface RecoveryPolicyConfig {
  policy_version: number;
  policy_id: string;
  security_state: SecurityState;
  power_state_overrides: Record<string, PowerStatePolicy>;
  retry_config?: RetryConfig;
  storage_limits?: StorageLimits;
}

export interface RecoveryPolicy {
  id: string;
  policy_id: string;
  name: string;
  security_state: SecurityState;
  config: RecoveryPolicyConfig;
  created_at: string;
  updated_at: string;
}

export type Severity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export interface SecurityEvent {
  id: string;
  device_id: string;
  event_type: string;
  severity: Severity;
  security_state_before: SecurityState;
  security_state_after: SecurityState;
  payload?: Record<string, any>;
  device_timestamp: string;
  received_at: string;
}

export type EvidenceType = 'SNAPSHOT' | 'AMBIENT_RF' | 'NETWORK_BEACONS' | 'SENSOR_BURST';

export interface EvidenceMetadata {
  id: string;
  device_id: string;
  event_id?: string;
  capture_type: EvidenceType;
  integrity_hash: string;
  storage_ref: string;
  mime_type: string;
  file_size_bytes?: string;
  chain_of_custody_notes?: string;
  device_timestamp: string;
  received_at: string;
}

export interface AuditLog {
  id: number;
  actor_type: string;
  actor_id: string;
  action: string;
  resource_type: string;
  resource_id: string;
  details?: Record<string, any>;
  prev_hash?: string;
  entry_hash: string;
  timestamp: string;
}

export interface WebSocketMessage {
  type: string;
  data?: any;
  device_id?: string;
  event_type?: string;
  timestamp?: string;
}
