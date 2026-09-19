package com.antisarika.agent.core.storage

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase
import com.antisarika.agent.core.storage.dao.AuditLogDao
import com.antisarika.agent.core.storage.dao.CommandDao
import com.antisarika.agent.core.storage.dao.DeviceConfigDao
import com.antisarika.agent.core.storage.dao.EvidenceDao
import com.antisarika.agent.core.storage.dao.SecurityEventDao
import com.antisarika.agent.core.storage.dao.TelemetryDao
import com.antisarika.agent.core.storage.entities.AuditLogEntity
import com.antisarika.agent.core.storage.entities.CommandEntity
import com.antisarika.agent.core.storage.entities.DeviceConfigEntity
import com.antisarika.agent.core.storage.entities.EvidenceEntity
import com.antisarika.agent.core.storage.entities.SecurityEventEntity
import com.antisarika.agent.core.storage.entities.TelemetryEntity

@Database(
    entities = [
        DeviceConfigEntity::class,
        TelemetryEntity::class,
        SecurityEventEntity::class,
        CommandEntity::class,
        EvidenceEntity::class,
        AuditLogEntity::class
    ],
    version = 1,
    exportSchema = false
)
abstract class AntiSarikaDatabase : RoomDatabase() {
    abstract fun deviceConfigDao(): DeviceConfigDao
    abstract fun telemetryDao(): TelemetryDao
    abstract fun securityEventDao(): SecurityEventDao
    abstract fun commandDao(): CommandDao
    abstract fun evidenceDao(): EvidenceDao
    abstract fun auditLogDao(): AuditLogDao

    companion object {
        @Volatile
        private var INSTANCE: AntiSarikaDatabase? = null

        fun getInstance(context: Context): AntiSarikaDatabase {
            return INSTANCE ?: synchronized(this) {
                val instance = Room.databaseBuilder(
                    context.applicationContext,
                    AntiSarikaDatabase::class.java,
                    "anti_sarika_agent.db"
                ).build()
                INSTANCE = instance
                instance
            }
        }
    }
}
