import React, { useEffect, useState } from 'react';
import { getChallengeRFPs, runChallengePipeline } from '../services/api';
import { RefreshCw, FileText, CheckCircle2, AlertTriangle, DollarSign, Download } from 'lucide-react';
import { Card, CardBody, CardHeader, CardTitle, Badge, Button } from '../components/UI';

const ChallengeFlow = () => {
  const [rfps, setRfps] = useState([]);
  const [selected, setSelected] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadRfps();
  }, []);

  const loadRfps = async () => {
    const data = await getChallengeRFPs();
    setRfps(data.rfps || []);
    if (data.rfps?.length) {
      setSelected(data.rfps[0]);
      runPipeline(data.rfps[0].id);
    }
  };

  const runPipeline = async (rfpId) => {
    setLoading(true);
    try {
      const data = await runChallengePipeline(rfpId);
      setResult(data);
    } catch (err) {
      console.error('Pipeline error', err);
    } finally {
      setLoading(false);
    }
  };

  const renderMatchTable = (match) => {
    const specs = ["voltage_kv", "conductor_size_sqmm", "core_count", "insulation", "armoring", "standard"];
    return (
      <div className="space-y-3">
        <div className="grid grid-cols-3 gap-3">
          {match.matches.map((m, idx) => (
            <Card key={idx}>
              <CardHeader>
                <CardTitle className="text-sm">#{idx + 1} — {m.product.name}</CardTitle>
              </CardHeader>
              <CardBody className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-400">SKU</span>
                  <span className="text-sm font-semibold text-white">{m.product.sku}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-400">Score</span>
                  <Badge variant={idx === 0 ? 'success' : 'warning'}>{(m.score * 100).toFixed(1)}%</Badge>
                </div>
              </CardBody>
            </Card>
          ))}
        </div>
        <div className="overflow-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr>
                <th className="px-2 py-1 text-left text-gray-400">Spec</th>
                <th className="px-2 py-1 text-left text-gray-400">Requirement</th>
                {match.matches.map((m, idx) => (
                  <th key={idx} className="px-2 py-1 text-left text-gray-400">Product {idx + 1}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {specs.map((spec) => (
                <tr key={spec} className="border-t border-dark-700/50">
                  <td className="px-2 py-1 capitalize text-gray-300">{spec.replace('_', ' ')}</td>
                  <td className="px-2 py-1 text-white">{match.item.requirements[spec]}</td>
                  {match.matches.map((m, idx) => {
                    const det = m.details.find(d => d.spec === spec);
                    const status = det?.status || 'unknown';
                    const color = status === 'match' ? 'text-green-400' : status === 'mismatch' ? 'text-red-400' : 'text-gray-400';
                    return (
                      <td key={idx} className="px-2 py-1">
                        <span className={color}>{det?.product ?? '-'}</span>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  const renderPricing = () => {
    if (!result?.pricing) return null;
    const { materials, tests, totals } = result.pricing;
    return (
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Material Pricing</CardTitle>
          </CardHeader>
          <CardBody>
            <div className="space-y-2">
              {materials.map((m) => (
                <div key={m.item_id} className="flex items-center justify-between p-3 bg-dark-800 rounded-lg">
                  <div>
                    <p className="font-semibold text-white">{m.description}</p>
                    <p className="text-xs text-gray-400">{m.sku}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-gray-400">{m.quantity} m @ ₹{m.unit_price.toLocaleString()}</p>
                    <p className="text-lg font-bold text-green-400">₹{m.total.toLocaleString()}</p>
                  </div>
                </div>
              ))}
            </div>
          </CardBody>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Test Pricing</CardTitle>
          </CardHeader>
          <CardBody className="space-y-3">
            {tests.map((t) => (
              <div key={t.test_code} className="flex items-center justify-between">
                <div>
                  <p className="text-white font-semibold">{t.name}</p>
                  <p className="text-xs text-gray-400">{t.quantity} x ₹{t.unit_price.toLocaleString()}</p>
                </div>
                <p className="text-sm font-bold text-green-400">₹{t.total.toLocaleString()}</p>
              </div>
            ))}
            <div className="pt-3 border-t border-dark-700/50 space-y-1 text-sm">
              <div className="flex justify-between text-gray-300">
                <span>Materials</span>
                <span>₹{totals.materials.toLocaleString()}</span>
              </div>
              <div className="flex justify-between text-gray-300">
                <span>Tests</span>
                <span>₹{totals.tests.toLocaleString()}</span>
              </div>
              <div className="flex justify-between text-white font-bold">
                <span>Grand Total</span>
                <span>₹{totals.grand_total.toLocaleString()}</span>
              </div>
            </div>
          </CardBody>
        </Card>
      </div>
    );
  };

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Challenge IV – End-to-End Demo</h1>
          <p className="text-gray-400 mt-1">Scan → Match → Price → Consolidate</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={loadRfps}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh RFPs
          </Button>
          <Button onClick={() => selected && runPipeline(selected.id)} disabled={!selected || loading}>
            <FileText className="w-4 h-4 mr-2" />
            {loading ? 'Running...' : 'Run Pipeline'}
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>RFP Identification</CardTitle>
        </CardHeader>
        <CardBody className="space-y-3">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {rfps.map((r) => (
              <button
                key={r.id}
                onClick={() => { setSelected(r); runPipeline(r.id); }}
                className={`p-4 rounded-lg border transition-all text-left ${selected?.id === r.id ? 'border-primary-500 bg-primary-500/10' : 'border-dark-700/50 bg-dark-800'}`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-white">{r.title}</span>
                  <Badge variant={r.strategic_fit === 'high' ? 'success' : 'warning'}>{r.strategic_fit}</Badge>
                </div>
                <p className="text-xs text-gray-400 mt-2">Due: {new Date(r.due_date).toLocaleDateString()}</p>
                <p className="text-xs text-gray-400">Value: ₹{(r.estimated_value / 1e7).toFixed(2)} Cr</p>
              </button>
            ))}
          </div>
        </CardBody>
      </Card>

      {result && (
        <>
          <Card>
            <CardHeader>
              <CardTitle>Technical Matching</CardTitle>
            </CardHeader>
            <CardBody className="space-y-6">
              {result.matches.map((m) => (
                <div key={m.item.item_id} className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-white font-semibold">{m.item.description}</p>
                      <p className="text-xs text-gray-400">{m.item.quantity} {m.item.unit}</p>
                    </div>
                    <Badge variant="success">Best: {(m.best_score * 100).toFixed(1)}%</Badge>
                  </div>
                  {renderMatchTable(m)}
                </div>
              ))}
            </CardBody>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Pricing & Consolidation</CardTitle>
            </CardHeader>
            <CardBody className="space-y-4">
              {renderPricing()}
              <div className="flex items-center gap-3 p-4 bg-dark-800 rounded-lg">
                <DollarSign className="w-5 h-5 text-green-400" />
                <div>
                  <p className="text-white font-semibold">Summary</p>
                  <p className="text-sm text-gray-400">
                    Avg spec match {Math.round(result.summary.avg_spec_match * 100)}% · Time 2h · Complete package ready for submission
                  </p>
                </div>
                <div className="ml-auto flex gap-2">
                  <Button variant="primary">
                    <CheckCircle2 className="w-4 h-4 mr-2" />
                    Finalize
                  </Button>
                  <Button variant="outline">
                    <Download className="w-4 h-4 mr-2" />
                    Download JSON
                  </Button>
                </div>
              </div>
            </CardBody>
          </Card>
        </>
      )}

      {!result && !loading && (
        <div className="p-6 bg-dark-800 rounded-lg border border-dark-700/50 flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-yellow-400" />
          <p className="text-gray-300">Select an RFP to run the pipeline.</p>
        </div>
      )}
    </div>
  );
};

export default ChallengeFlow;

