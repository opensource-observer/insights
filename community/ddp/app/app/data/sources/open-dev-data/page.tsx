import MarimoIframe from '@/components/MarimoIframe';

export default function OpenDevData() {
  return (
    <div className="h-full w-full">
      <MarimoIframe notebookName="notebooks/data/sources/open-dev-data" />
    </div>
  );
}
