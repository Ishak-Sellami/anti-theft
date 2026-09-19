package com.antisarika.agent.core.storage.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Update
import com.antisarika.agent.core.storage.entities.AuditLogEntity
import com.antisarika.agent.core.storage.entities.CommandEntity
import com.antisarika.agent.core.storage.entities.DeviceConfigEntity
import com.antisarika.agent.core.storage.entities.EvidenceEntity
import com.antisarika.agent.core.storage.entities.SecurityEventEntity
import com.antisarika.agent.core.storage.entities.TelemetryEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface DeviceConfigDao {
    @Query("SELECT * FROM device_config WHERE `key` = 'current_config' LIMIT 1")
    suspend fun getConfig(): DeviceConfigEntity?

    @Query("SELECT * FROM device_config WHERE `key` = 'current_config' LIMIT 1")
    fun observeConfig(): Flow<DeviceConfigEntity?>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun saveConfig(config: DeviceConfigEntity)

    @Update
    suspend fun updateConfig(config: DeviceConfigEntity)
}

@Dao
interface TelemetryDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertTelemetry(item: TelemetryEntity): Long

    @Query("SELECT * FROM telemetry_queue WHERE isSynced = 0 ORDER BY id ASC LIMIT :limit")
    suspend fun getPendingTelemetry(limit: Int): List<TelemetryEntity>

    @Query("DELETE FROM telemetry_queue WHERE id IN (:ids)")
    suspend fun deleteSynced(ids: List<Long>)

    @Query("SELECT COUNT(*) FROM telemetry_queue WHERE isSynced = 0")
    suspend fun getPendingCount(): Int

    @Query("DELETE FROM telemetry_queue WHERE id IN (SELECT id FROM telemetry_queue ORDER BY id ASC LIMIT :count)")
    suspend fun evictOldest(count: Int)
}

@Dao
interface SecurityEventDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertEvent(event: SecurityEventEntity)

    @Query("SELECT * FROM security_events_queue WHERE isSynced = 0 ORDER BY timestamp ASC")
    suspend fun getPendingEvents(): List<SecurityEventEntity>

    @Query("DELETE FROM security_events_queue WHERE eventId IN (:eventIds)")
    suspend fun deleteSynced(eventIds: List<String>)
}

@Dao
interface CommandDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertCommand(command: CommandEntity)

    @Query("SELECT * FROM command_history WHERE nonce = :nonce LIMIT 1")
    suspend fun getCommandByNonce(nonce: String): CommandEntity?

    @Query("SELECT * FROM command_history WHERE commandId = :commandId LIMIT 1")
    suspend fun getCommandById(commandId: String): CommandEntity?

    @Update
    suspend fun updateCommand(command: CommandEntity)

    @Query("SELECT * FROM command_history ORDER BY createdAt DESC LIMIT :limit")
    suspend fun getRecentCommands(limit: Int): List<CommandEntity>
}

@Dao
interface EvidenceDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertEvidence(evidence: EvidenceEntity)

    @Query("SELECT * FROM evidence_queue WHERE isSynced = 0 ORDER BY timestamp ASC")
    suspend fun getPendingEvidence(): List<EvidenceEntity>

    @Query("UPDATE evidence_queue SET isSynced = 1 WHERE evidenceId = :evidenceId")
    suspend fun markSynced(evidenceId: String)
}

@Dao
interface AuditLogDao {
    @Insert
    suspend fun insertLog(log: AuditLogEntity)

    @Query("SELECT * FROM local_audit_log ORDER BY id DESC LIMIT :limit")
    suspend fun getRecentLogs(limit: Int): List<AuditLogEntity>
}
