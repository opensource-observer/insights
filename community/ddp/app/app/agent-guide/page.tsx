import MarimoIframe from '@/components/MarimoIframe';

export default function AgentGuide() {
  return (
    <div className="h-full w-full">
      <MarimoIframe notebookName="notebooks/data/agent-workflows" />
    </div>
  );
}
