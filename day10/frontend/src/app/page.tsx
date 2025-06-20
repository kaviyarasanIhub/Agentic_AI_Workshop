'use client';
import { useState } from 'react';
import CodeUpload from '../components/CodeUpload';
import IssueReport from '../components/IssueReport';
import FixPreview from '../components/FixPreview';
import ApprovalDashboard from '../components/ApprovalDashboard';
import AuditLog from '../components/AuditLog';

export default function Home() {
  const [submissionId, setSubmissionId] = useState<string | null>(null);
  const [issues, setIssues] = useState<any[]>([]);
  const [fixes, setFixes] = useState<any[]>([]);
  const [dashboard, setDashboard] = useState<any>(null);
  const [auditLog, setAuditLog] = useState<any[]>([]);
  const [approvalMessage, setApprovalMessage] = useState<string | null>(null);

  async function handleAnalyze(data: any) {
    // Call FastAPI backend directly
    const res = await fetch('http://127.0.0.1:8000/api/bug-fix', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ input_data: data })
    });
    if (!res.ok) {
      alert('Failed to analyze code.');
      return;
    }
    const result = await res.json();
    // Handle approval required response
    if (result.result?.status === 'pending' && result.result?.message) {
      setApprovalMessage(result.result.message);
      setFixes([]);
      setIssues([]);
      setDashboard(null);
      setSubmissionId(null);
      return;
    }
    setApprovalMessage(null);
    setFixes(result.result?.dashboard?.diff_views || []);
    setIssues(result.result?.issues || []);
    setDashboard(result.result?.dashboard || null);
    setSubmissionId(result.result?.submission_id || null);
  }

  async function handleApproval(approved: boolean) {
    if (!submissionId) return;
    // Simulate approval API (implement if backend supports)
    const approval = {
      timestamp: new Date().toISOString(),
      status: approved ? 'approved' : 'rejected',
      approver: 'user1',
      comments: approved ? 'Approved by user' : 'Rejected by user',
    };
    setAuditLog(logs => [...logs, approval]);
    setDashboard(null);
  }

  return (
    <main className="max-w-4xl mx-auto p-6 bg-card rounded-lg shadow-lg mt-8">
      <h1 className="text-3xl font-extrabold text-primary mb-6">Agentic AI Bug Fixer</h1>
      <CodeUpload onSubmit={handleAnalyze} />
      {approvalMessage && (
        <div className="my-4 p-4 bg-yellow-100 border-l-4 border-yellow-500 text-yellow-700 rounded">
          {approvalMessage}
        </div>
      )}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-8">
        <IssueReport issues={issues} />
        <FixPreview diffs={fixes} />
      </div>
      <ApprovalDashboard dashboard={dashboard} onApprove={handleApproval} />
      <AuditLog logs={auditLog} />
    </main>
  );
}