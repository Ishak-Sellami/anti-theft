import React, { useEffect, useState } from 'react';
import { policyService } from '../services/policies';
import { RecoveryPolicy } from '../types';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Spinner } from '../components/common/Spinner';
import { Badge } from '../components/common/Badge';
import { PolicyEditorModal } from '../components/policy/PolicyEditorModal';
import { Sliders, Edit3, Shield, Zap, RefreshCw } from 'lucide-react';

export const RecoveryPolicyPage: React.FC = () => {
  const [policies, setPolicies] = useState<RecoveryPolicy[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedPolicy, setSelectedPolicy] = useState<RecoveryPolicy | null>(null);
  const [isEditorOpen, setIsEditorOpen] = useState(false);

  const loadPolicies = async () => {
    try {
      const list = await policyService.listPolicies();
      setPolicies(list);
    } catch (e) {
      console.error('Failed to load policies', e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadPolicies();
  }, []);

  const handleEdit = (policy: RecoveryPolicy) => {
    setSelectedPolicy(policy);
    setIsEditorOpen(true);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-100 uppercase tracking-wide">
            Recovery Policies
          </h1>
          <p className="text-xs text-slate-400">
            Dynamic telemetry rate, battery conservation, and storage limit policies
          </p>
        </div>

        <Button variant="secondary" size="sm" onClick={loadPolicies} icon={<RefreshCw size={14} />}>
          Refresh Policies
        </Button>
      </div>

      {isLoading ? (
        <div className="py-20 flex justify-center">
          <Spinner size="lg" />
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {policies.map((p) => {
            const config = p.config;
            const overrides = config.powerStateOverrides || {};

            return (
              <Card key={p.id} className="space-y-4 border-slate-800">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2.5 rounded-xl bg-primary/10 border border-primary/20 text-primary">
                      <Sliders size={20} />
                    </div>
                    <div>
                      <h3 className="font-bold text-base text-slate-100">{p.name}</h3>
                      <div className="text-xs text-slate-400 font-mono">ID: {p.policy_id} (v{config.policy_version})</div>
                    </div>
                  </div>
                  <Badge variant="purple">{p.security_state}</Badge>
                </div>

                <div className="space-y-3 text-xs bg-background/50 p-3.5 rounded-xl border border-slate-800 font-mono">
                  <div className="font-sans font-bold text-slate-300 text-[11px] uppercase tracking-wider">
                    Power State Rate Overrides:
                  </div>
                  {Object.entries(overrides).map(([powerState, policy]) => (
                    <div key={powerState} className="flex justify-between border-b border-slate-800/60 pb-1.5">
                      <span className="text-slate-400">{powerState}:</span>
                      <span className="text-slate-200">
                        Loc: {policy.locationIntervalMs / 1000}s • Ping: {policy.heartbeatIntervalMs / 1000}s
                      </span>
                    </div>
                  ))}
                  <div className="flex justify-between pt-1">
                    <span className="text-slate-400">Offline Queue Limit:</span>
                    <span className="text-emerald-400">
                      {config.storage_limits?.offlineQueueMaxRecords || 10000} records
                    </span>
                  </div>
                </div>

                <div className="flex justify-end pt-2">
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => handleEdit(p)}
                    icon={<Edit3 size={14} />}
                  >
                    Edit Policy
                  </Button>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      <PolicyEditorModal
        isOpen={isEditorOpen}
        onClose={() => setIsEditorOpen(false)}
        policy={selectedPolicy}
        onSuccess={loadPolicies}
      />
    </div>
  );
};
