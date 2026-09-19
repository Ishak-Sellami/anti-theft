# Anti-Sarika Proguard Rules
-keepattributes Signature
-keepattributes *Annotation*
-keep class com.antisarika.agent.core.model.** { *; }
-keep class com.antisarika.agent.core.storage.entities.** { *; }
