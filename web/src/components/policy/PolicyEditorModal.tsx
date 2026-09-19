import React, { useState } from 'react';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import { RecoveryPolicy, RecoveryPolicyConfig } from '../../types';
import { policyService } from '../../services/policies';
import { Sliders, AlertCircle } from 'lucide-react';

interface PolicyEditorModalProps {
  isOpen: boolean;
  onClose: () => void;
  policy: RecoveryPolicy | null;
  onSuccess: () => void;
}

export const PolicyEditorModal: React.FC<PolicyEditorModalProps> = ({
  isOpen,
  onClose,
  policy,
  onSuccess,
}) => {
  const [configJson, setConfigJson] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  React.useEffect(() => {
    if (policy) {
      setConfigJson(JSON.stringify(policy.config, null, 2));
      setError(null);
    }
  }, [policy]);

  if (!policy) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      const parsedConfig = JSON.parse(configJson) as RecoveryPolicyConfig;
      if (!parsedConfig.policy_id) {
        throw new Error('policy_id is required');
      }

      await policyService.updatePolicy(policy.policy_id, {
        name: policy.name,
        config: parsedConfig,
      });

      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.message || 'Invalid JSON format or validation failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={`Edit Recovery Policy — ${policy.name}`} maxWidth="xl">
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="p-3 bg-red-950/60 border border-red-800 text-red-300 text-xs rounded-xl flex items-start gap-2">
            <AlertCircle size={16} className="shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        <div>
          <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
            Policy Config JSON (Dynamic Power Overrides & Intervals)
          </label>
          <textarea
            rows={12}
            value={configJson}
            onChange={(e) => setConfigJson(e.target.value)}
            className="w-full p-3 bg-background border border-slate-700 rounded-xl font-mono text-xs text-slate-100 focus:outline-none focus:border-primary"
          />
        </div>

        <div className="flex justify-between items-center pt-3 border-t border-slate-800">
          <span className="text-xs text-slate-500 font-mono">
            Policy: {policy.policy_id} (State: {policy.security_state})
          </span>
          <div className="flex gap-3">
            <Button variant="ghost" type="button" onClick={onClose}>
              Cancel
            </Button>
            <Button variant="primary" type="submit" isLoading={isLoading}>
              Save Changes
            </Button>
          </div>
        </div>
      </form>
    </Modal>
  );
};
