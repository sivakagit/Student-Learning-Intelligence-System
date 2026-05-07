import React, { useState, useEffect, useCallback } from 'react';

const API = 'https://student-learning-intelligence-system.onrender.com';

/* ── Global CSS ───────────────────────────────────────────────────── */
const globalCSS = `
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg:        #090e1a;
    --bg2:       #0f1729;
    --bg3:       #162040;
    --border:    #1e2d50;
    --border2:   #2a3f6f;
    --text:      #c8d8f0;
    --text2:     #7a92b8;
    --text3:     #4a6080;
    --accent:    #f5a623;
    --accent2:   #e8891a;
    --safe:      #2dd4a0;
    --risk:      #f06060;
    --risk-bg:   rgba(240,96,96,0.08);
    --safe-bg:   rgba(45,212,160,0.07);
    --blue:      #4a90d9;
    --mono:      'DM Mono', monospace;
    --sans:      'DM Sans', sans-serif;
    --display:   'Syne', sans-serif;
  }

  html, body { height: 100%; background: var(--bg); color: var(--text); font-family: var(--sans); }

  ::-webkit-scrollbar { width: 4px; }
  ::-webkit-scrollbar-track { background: var(--bg2); }
  ::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 2px; }

  @keyframes fadeUp {
    from { opacity: 0; transform: translateY(12px); }
    to   { opacity: 1; transform: translateY(0); }
  }
  @keyframes pulse {
    0%, 100% { opacity: 1; } 50% { opacity: 0.4; }
  }
  .fade-up { animation: fadeUp 0.35s ease both; }
`;

/* ── Helpers ──────────────────────────────────────────────────────── */
const fmt = (n, d = 1) => (typeof n === 'number' ? n.toFixed(d) : '—');
const pct = (n) => (typeof n === 'number' ? (n * 100).toFixed(1) + '%' : '—');
const riskColor = (r) => (r ? 'var(--risk)' : 'var(--safe)');

/* ── Sub-components ───────────────────────────────────────────────── */

function Badge({ risk }) {
  return (
    <span style={{
      fontFamily: 'var(--mono)', fontSize: 10, fontWeight: 500,
      padding: '2px 8px', borderRadius: 3,
      background: risk ? 'rgba(240,96,96,0.15)' : 'rgba(45,212,160,0.12)',
      color: riskColor(risk), border: `1px solid ${risk ? 'rgba(240,96,96,0.3)' : 'rgba(45,212,160,0.25)'}`,
      letterSpacing: '0.06em', textTransform: 'uppercase',
    }}>
      {risk ? 'At-Risk' : 'On-Track'}
    </span>
  );
}

function StatCard({ label, value, sub, accent }) {
  return (
    <div style={{
      background: 'var(--bg2)', border: '1px solid var(--border)',
      borderRadius: 8, padding: '20px 24px',
      borderTop: accent ? `2px solid ${accent}` : '1px solid var(--border)',
    }}>
      <div style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--text3)', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 10 }}>{label}</div>
      <div style={{ fontFamily: 'var(--display)', fontSize: 32, fontWeight: 700, color: accent || 'var(--text)', lineHeight: 1 }}>{value}</div>
      {sub && <div style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--text2)', marginTop: 6 }}>{sub}</div>}
    </div>
  );
}

function ScoreBar({ label, value, max = 100, color }) {
  return (
    <div style={{ marginBottom: 10 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
        <span style={{ fontFamily: 'var(--sans)', fontSize: 12, color: 'var(--text2)' }}>{label}</span>
        <span style={{ fontFamily: 'var(--mono)', fontSize: 12, color: color || 'var(--text)' }}>{fmt(value)}%</span>
      </div>
      <div style={{ height: 4, background: 'var(--bg3)', borderRadius: 2, overflow: 'hidden' }}>
        <div style={{
          height: '100%', width: `${Math.min(100, value)}%`,
          background: color || 'var(--blue)', borderRadius: 2,
          transition: 'width 0.6s ease',
        }} />
      </div>
    </div>
  );
}

function PriorityDot({ priority }) {
  const colors = { Critical: 'var(--risk)', High: 'var(--accent)', Medium: 'var(--blue)', Info: 'var(--safe)' };
  return (
    <span style={{
      display: 'inline-block', width: 7, height: 7, borderRadius: '50%',
      background: colors[priority] || 'var(--text3)', marginRight: 8, flexShrink: 0, marginTop: 5,
    }} />
  );
}

/* ── Student Detail Panel ─────────────────────────────────────────── */
function StudentPanel({ studentId, onClose }) {
  const [student, setStudent]     = useState(null);
  const [recs, setRecs]           = useState(null);
  const [loading, setLoading]     = useState(true);
  const [tab, setTab]             = useState('overview');
  const [aiText, setAiText]       = useState(null);
  const [aiLoading, setAiLoading] = useState(false);

  useEffect(() => {
    if (!studentId) return;
    setLoading(true);
    setStudent(null);
    setRecs(null);
    setAiText(null);
    setTab('overview');
    console.log("API =", API);
    console.log("Student =", studentId);
    Promise.all([
      fetch(`${API}/students/${studentId}`)
        .then(r => r.json())
        .catch(err => {
          console.error("Student fetch failed:", err);
          return null;
        }),
      fetch(`${API}/recommendations/${studentId}`)
        .then(r => r.json())
        .catch(err => {
          console.error("Recommendations fetch failed:", err);
          return { rule_based: [] };
        }),
    ])
      .then(([s, r]) => {
        console.log("Student data:", s);
        console.log("Recommendations:", r);
        setStudent(s);
        setRecs(r);
        setLoading(false);
      })
      .catch(err => {
        console.error("Promise.all failed:", err);
        setLoading(false);
      });
  }, [studentId]);

  const fetchAI = () => {
    setAiLoading(true);
    fetch(`${API}/recommendations/${studentId}?use_ai=true`)
      .then(r => r.json())
      .then(r => { setAiText(r.ai_powered); setAiLoading(false); })
      .catch(() => { setAiText('Error fetching AI recommendations.'); setAiLoading(false); });
  };

  const overlay = {
    position: 'fixed', inset: 0, background: 'rgba(9,14,26,0.85)',
    backdropFilter: 'blur(4px)', zIndex: 100, display: 'flex', alignItems: 'flex-start', justifyContent: 'flex-end',
  };
  const panel = {
    width: 520, height: '100vh', background: 'var(--bg2)',
    borderLeft: '1px solid var(--border2)', overflowY: 'auto',
    animation: 'fadeUp 0.2s ease',
    display: 'flex', flexDirection: 'column',
  };

  if (!studentId) return null;

  return (
    <div style={overlay} onClick={onClose}>
      <div style={panel} onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div style={{ padding: '20px 24px 16px', borderBottom: '1px solid var(--border)', position: 'sticky', top: 0, background: 'var(--bg2)', zIndex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--text3)' }}>{studentId}</span>
            <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--text3)', cursor: 'pointer', fontSize: 18, lineHeight: 1 }}>✕</button>
          </div>
          {loading ? (
            <div style={{ fontFamily: 'var(--display)', fontSize: 20, color: 'var(--text3)', marginTop: 4, animation: 'pulse 1.2s infinite' }}>Loading…</div>
          ) : (
            <>
              <div style={{ fontFamily: 'var(--display)', fontSize: 22, fontWeight: 700, marginTop: 4 }}>{student?.name}</div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: 8 }}>
                <Badge risk={student?.at_risk} />
                <span style={{ fontFamily: 'var(--sans)', fontSize: 12, color: 'var(--text2)' }}>{student?.department}</span>
                <span style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--text3)' }}>·  {student?.enrollment_year}</span>
              </div>
            </>
          )}
        </div>

        {!loading && student && (
          <>
            {/* Tabs */}
            <div style={{ display: 'flex', borderBottom: '1px solid var(--border)', padding: '0 24px' }}>
              {['overview', 'recommendations'].map(t => (
                <button key={t} onClick={() => setTab(t)} style={{
                  background: 'none', border: 'none', borderBottom: tab === t ? '2px solid var(--accent)' : '2px solid transparent',
                  color: tab === t ? 'var(--accent)' : 'var(--text2)', fontFamily: 'var(--mono)',
                  fontSize: 11, letterSpacing: '0.08em', textTransform: 'uppercase',
                  padding: '12px 0', marginRight: 20, cursor: 'pointer',
                }}>{t}</button>
              ))}
            </div>

            <div style={{ padding: 24, flex: 1 }}>
              {tab === 'overview' && (
                <div className="fade-up">
                  {/* Key metrics */}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 24 }}>
                    {[
                      { label: 'Attendance', value: pct(student.attendance_rate), color: student.attendance_rate < 0.65 ? 'var(--risk)' : 'var(--safe)' },
                      { label: 'Avg Score', value: fmt(student.avg_score) + '%', color: student.avg_score < 45 ? 'var(--risk)' : 'var(--safe)' },
                      { label: 'Predicted', value: fmt(student.predicted_score) + '%', color: 'var(--blue)' },
                      { label: 'Risk Prob', value: fmt(student.risk_probability * 100) + '%', color: student.risk_probability > 0.5 ? 'var(--risk)' : 'var(--safe)' },
                    ].map(m => (
                      <div key={m.label} style={{ background: 'var(--bg3)', borderRadius: 6, padding: '14px 16px', border: '1px solid var(--border)' }}>
                        <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--text3)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 6 }}>{m.label}</div>
                        <div style={{ fontFamily: 'var(--mono)', fontSize: 22, fontWeight: 500, color: m.color }}>{m.value}</div>
                      </div>
                    ))}
                  </div>

                  {/* Score bars */}
                  <div style={{ marginBottom: 20 }}>
                    <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--text3)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 12 }}>Academic Profile</div>
                    <ScoreBar label="Average Score" value={student.avg_score} color={student.avg_score < 45 ? 'var(--risk)' : 'var(--blue)'} />
                    <ScoreBar label="Min Score" value={student.min_score} color="var(--text2)" />
                    <ScoreBar label="Attendance Rate" value={student.attendance_rate * 100} color={student.attendance_rate < 0.65 ? 'var(--risk)' : 'var(--safe)'} />
                  </div>

                  {/* Engagement stats */}
                  <div style={{ background: 'var(--bg3)', borderRadius: 6, border: '1px solid var(--border)', padding: 16, marginBottom: 20 }}>
                    <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--text3)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 12 }}>Engagement</div>
                    {[
                      ['Platform Sessions', student.total_sessions],
                      ['Total Study Minutes', Math.round(student.total_minutes)],
                      ['Unique Active Days', student.unique_days_active],
                    ].map(([k, v]) => (
                      <div key={k} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid var(--border)' }}>
                        <span style={{ fontFamily: 'var(--sans)', fontSize: 13, color: 'var(--text2)' }}>{k}</span>
                        <span style={{ fontFamily: 'var(--mono)', fontSize: 13, color: 'var(--text)' }}>{v}</span>
                      </div>
                    ))}
                  </div>

                  {/* Weak subjects */}
                  {student.weak_subjects?.length > 0 && (
                    <div>
                      <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--text3)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 10 }}>Weak Subjects</div>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                        {student.weak_subjects.map(s => (
                          <span key={s} style={{
                            fontFamily: 'var(--mono)', fontSize: 11, padding: '3px 10px',
                            background: 'rgba(240,96,96,0.1)', border: '1px solid rgba(240,96,96,0.25)',
                            color: 'var(--risk)', borderRadius: 3,
                          }}>{s}</span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {tab === 'recommendations' && recs && (
                <div className="fade-up">
                  {/* Rule-based */}
                  <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--text3)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 14 }}>
                    Rule-Based — {recs.rule_based?.length} items
                  </div>
                  {recs.rule_based?.map((r, i) => (
                    <div key={i} style={{
                      display: 'flex', gap: 10, marginBottom: 12,
                      background: 'var(--bg3)', border: '1px solid var(--border)',
                      borderRadius: 6, padding: '12px 14px',
                    }}>
                      <PriorityDot priority={r.priority} />
                      <div>
                        <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--text3)', marginBottom: 4 }}>{r.priority} · {r.category}</div>
                        <div style={{ fontFamily: 'var(--sans)', fontSize: 13, color: 'var(--text)', lineHeight: 1.5 }}>{r.message}</div>
                      </div>
                    </div>
                  ))}

                  {/* AI recommendations section */}
                  <div style={{ marginTop: 24, borderTop: '1px solid var(--border)', paddingTop: 20 }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
                      <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--text3)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
                        AI Advisor · Gemini
                      </div>
                      {!aiText && (
                        <button onClick={fetchAI} disabled={aiLoading} style={{
                          fontFamily: 'var(--mono)', fontSize: 11, letterSpacing: '0.06em',
                          padding: '6px 14px', borderRadius: 4, cursor: aiLoading ? 'wait' : 'pointer',
                          background: aiLoading ? 'var(--bg3)' : 'rgba(245,166,35,0.12)',
                          border: '1px solid rgba(245,166,35,0.35)',
                          color: aiLoading ? 'var(--text3)' : 'var(--accent)',
                          transition: 'all 0.2s',
                        }}>
                          {aiLoading ? 'Asking Gemini…' : '✦ Generate AI Advice'}
                        </button>
                      )}
                    </div>

                    {aiLoading && (
                      <div style={{ fontFamily: 'var(--mono)', fontSize: 12, color: 'var(--text3)', padding: 14, background: 'var(--bg3)', borderRadius: 6, border: '1px solid var(--border)', animation: 'pulse 1.2s infinite' }}>
                        Consulting Gemini…
                      </div>
                    )}

                    {aiText && (
                      <div style={{ background: 'rgba(245,166,35,0.05)', border: '1px solid rgba(245,166,35,0.2)', borderRadius: 6, padding: 16 }}>
                        <div style={{ fontFamily: 'var(--sans)', fontSize: 13, color: 'var(--text)', lineHeight: 1.7, whiteSpace: 'pre-wrap' }}>{aiText}</div>
                        <button onClick={() => { setAiText(null); }} style={{
                          marginTop: 12, fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--text3)',
                          background: 'none', border: 'none', cursor: 'pointer', letterSpacing: '0.06em',
                        }}>↺ Regenerate</button>
                      </div>
                    )}

                    {!aiText && !aiLoading && (
                      <div style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--text3)', padding: '10px 14px', background: 'var(--bg3)', borderRadius: 6, border: '1px solid var(--border)' }}>
                        Requires <code style={{ color: 'var(--accent)' }}>GEMINI_API_KEY</code> in .env
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

/* ── Student Row ──────────────────────────────────────────────────── */
function StudentRow({ s, onClick, idx }) {
  return (
    <tr onClick={onClick} style={{
      cursor: 'pointer', borderBottom: '1px solid var(--border)',
      animation: `fadeUp 0.25s ease ${idx * 0.02}s both`,
      transition: 'background 0.15s',
    }}
      onMouseEnter={e => e.currentTarget.style.background = 'var(--bg3)'}
      onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
    >
      <td style={{ padding: '11px 16px', fontFamily: 'var(--mono)', fontSize: 12, color: 'var(--text3)' }}>{s.student_id}</td>
      <td style={{ padding: '11px 16px', fontFamily: 'var(--sans)', fontSize: 13, fontWeight: 500 }}>{s.name}</td>
      <td style={{ padding: '11px 16px', fontFamily: 'var(--sans)', fontSize: 12, color: 'var(--text2)' }}>{s.department}</td>
      <td style={{ padding: '11px 16px', fontFamily: 'var(--mono)', fontSize: 12, color: s.attendance_rate < 0.65 ? 'var(--risk)' : 'var(--text)' }}>{pct(s.attendance_rate)}</td>
      <td style={{ padding: '11px 16px', fontFamily: 'var(--mono)', fontSize: 12, color: s.avg_score < 45 ? 'var(--risk)' : 'var(--text)' }}>{fmt(s.avg_score)}%</td>
      <td style={{ padding: '11px 16px' }}><Badge risk={s.at_risk} /></td>
    </tr>
  );
}

/* ── Main App ─────────────────────────────────────────────────────── */
export default function App() {
  const [summary, setSummary]       = useState(null);
  const [students, setStudents]     = useState([]);
  const [loading, setLoading]       = useState(true);
  const [selected, setSelected]     = useState(null);
  const [filter, setFilter]         = useState('all');
  const [search, setSearch]         = useState('');
  const [sortKey, setSortKey]       = useState('student_id');
  const [sortDir, setSortDir]       = useState('asc');

  useEffect(() => {
    fetch(`${API}/dashboard/summary`).then(r => r.json()).then(setSummary);
    fetch(`${API}/students`).then(r => r.json()).then(d => { setStudents(d); setLoading(false); });
  }, []);

  const toggleSort = useCallback((key) => {
    setSortKey(k => { setSortDir(d => k === key ? (d === 'asc' ? 'desc' : 'asc') : 'asc'); return key; });
  }, []);

  const visible = students
    .filter(s => filter === 'all' || (filter === 'risk' ? s.at_risk : !s.at_risk))
    .filter(s => !search || s.name.toLowerCase().includes(search.toLowerCase()) || s.student_id.toLowerCase().includes(search.toLowerCase()))
    .sort((a, b) => {
      const v = sortDir === 'asc' ? 1 : -1;
      return a[sortKey] > b[sortKey] ? v : a[sortKey] < b[sortKey] ? -v : 0;
    });

  const SortTh = ({ label, k }) => (
    <th onClick={() => toggleSort(k)} style={{
      padding: '10px 16px', fontFamily: 'var(--mono)', fontSize: 10, color: sortKey === k ? 'var(--accent)' : 'var(--text3)',
      textTransform: 'uppercase', letterSpacing: '0.1em', textAlign: 'left',
      cursor: 'pointer', userSelect: 'none', whiteSpace: 'nowrap',
      background: 'var(--bg3)', borderBottom: '1px solid var(--border2)',
    }}>
      {label} {sortKey === k ? (sortDir === 'asc' ? '↑' : '↓') : ''}
    </th>
  );

  return (
    <>
      <style>{globalCSS}</style>

      {/* Sidebar */}
      <div style={{ display: 'flex', minHeight: '100vh' }}>
        <aside style={{
          width: 220, background: 'var(--bg2)', borderRight: '1px solid var(--border)',
          display: 'flex', flexDirection: 'column', flexShrink: 0,
          position: 'sticky', top: 0, height: '100vh',
        }}>
          <div style={{ padding: '24px 20px 20px', borderBottom: '1px solid var(--border)' }}>
            <div style={{ fontFamily: 'var(--mono)', fontSize: 9, color: 'var(--accent)', letterSpacing: '0.2em', textTransform: 'uppercase', marginBottom: 6 }}>SLIS v1.0</div>
            <div style={{ fontFamily: 'var(--display)', fontSize: 15, fontWeight: 700, lineHeight: 1.3, color: 'var(--text)' }}>Student Learning<br />Intelligence</div>
          </div>

          <nav style={{ padding: '16px 12px', flex: 1 }}>
            {[
              { label: 'All Students', val: 'all', count: students.length },
              { label: 'At-Risk', val: 'risk', count: students.filter(s => s.at_risk).length, color: 'var(--risk)' },
              { label: 'On-Track', val: 'safe', count: students.filter(s => !s.at_risk).length, color: 'var(--safe)' },
            ].map(f => (
              <button key={f.val} onClick={() => setFilter(f.val)} style={{
                width: '100%', display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                padding: '9px 10px', borderRadius: 5, border: 'none', cursor: 'pointer',
                background: filter === f.val ? 'var(--bg3)' : 'transparent',
                color: filter === f.val ? (f.color || 'var(--text)') : 'var(--text2)',
                fontFamily: 'var(--sans)', fontSize: 13, marginBottom: 2,
                transition: 'all 0.15s',
              }}>
                <span>{f.label}</span>
                <span style={{ fontFamily: 'var(--mono)', fontSize: 11, opacity: 0.7 }}>{f.count}</span>
              </button>
            ))}
          </nav>

          {summary && (
            <div style={{ padding: '16px 16px 20px', borderTop: '1px solid var(--border)' }}>
              <div style={{ fontFamily: 'var(--mono)', fontSize: 9, color: 'var(--text3)', letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: 10 }}>Cohort Stats</div>
              {[
                ['Avg Score', fmt(summary.avg_score) + '%'],
                ['Avg Attendance', pct(summary.avg_attendance)],
                ['At-Risk Rate', summary.at_risk_pct + '%'],
              ].map(([k, v]) => (
                <div key={k} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                  <span style={{ fontFamily: 'var(--sans)', fontSize: 11, color: 'var(--text3)' }}>{k}</span>
                  <span style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--text2)' }}>{v}</span>
                </div>
              ))}
            </div>
          )}
        </aside>

        {/* Main */}
        <main style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
          {/* Top bar */}
          <div style={{ padding: '20px 28px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: 16, background: 'var(--bg)', position: 'sticky', top: 0, zIndex: 10 }}>
            <div style={{ flex: 1 }}>
              <div style={{ fontFamily: 'var(--display)', fontSize: 20, fontWeight: 700 }}>
                {filter === 'all' ? 'All Students' : filter === 'risk' ? 'At-Risk Students' : 'On-Track Students'}
              </div>
              <div style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--text3)', marginTop: 2 }}>{visible.length} records</div>
            </div>

            <input
              placeholder="Search name or ID…"
              value={search}
              onChange={e => setSearch(e.target.value)}
              style={{
                background: 'var(--bg2)', border: '1px solid var(--border2)',
                color: 'var(--text)', fontFamily: 'var(--mono)', fontSize: 12,
                padding: '8px 14px', borderRadius: 5, outline: 'none', width: 220,
              }}
            />
          </div>

          {/* Summary cards */}
          {summary && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, padding: '20px 28px 0' }}>
              <StatCard label="Total Students" value={summary.total_students} accent="var(--blue)" />
              <StatCard label="At-Risk" value={summary.at_risk_count} sub={summary.at_risk_pct + '% of cohort'} accent="var(--risk)" />
              <StatCard label="Avg Score" value={fmt(summary.avg_score) + '%'} accent="var(--accent)" />
              <StatCard label="Avg Attendance" value={pct(summary.avg_attendance)} accent="var(--safe)" />
            </div>
          )}

          {/* Table */}
          <div style={{ padding: '20px 28px 40px', overflow: 'auto' }}>
            {loading ? (
              <div style={{ textAlign: 'center', color: 'var(--text3)', fontFamily: 'var(--mono)', padding: 60, animation: 'pulse 1.2s infinite' }}>Loading students…</div>
            ) : (
              <table style={{ width: '100%', borderCollapse: 'collapse', background: 'var(--bg2)', borderRadius: 8, overflow: 'hidden', border: '1px solid var(--border)' }}>
                <thead>
                  <tr>
                    <SortTh label="ID" k="student_id" />
                    <SortTh label="Name" k="name" />
                    <SortTh label="Department" k="department" />
                    <SortTh label="Attendance" k="attendance_rate" />
                    <SortTh label="Avg Score" k="avg_score" />
                    <th style={{ padding: '10px 16px', fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--text3)', textTransform: 'uppercase', letterSpacing: '0.1em', textAlign: 'left', background: 'var(--bg3)', borderBottom: '1px solid var(--border2)' }}>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {visible.map((s, i) => (
                    <StudentRow key={s.student_id} s={s} idx={i} onClick={() => setSelected(s.student_id)} />
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </main>
      </div>

      <StudentPanel studentId={selected} onClose={() => setSelected(null)} />
    </>
  );
}