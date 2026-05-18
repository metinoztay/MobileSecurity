import { useState, useRef, useEffect } from 'react'

function App() {
  const [isScanning, setIsScanning] = useState(false)
  const [logs, setLogs] = useState([])
  const [finalReport, setFinalReport] = useState(null)
  const [rawFindings, setRawFindings] = useState([])
  const consoleEndRef = useRef(null)

  const scrollToBottom = () => {
    consoleEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [logs])

  const startScan = async () => {
    setIsScanning(true)
    setLogs([])
    setFinalReport(null)
    setRawFindings([])

    try {
      // 1. Start the scan via POST
      const res = await fetch('http://localhost:8000/api/scan', {
        method: 'POST',
      })
      const data = await res.json()
      
      if (!data.scan_id) {
        throw new Error('Scan ID alınamadı.')
      }

      // 2. Connect to SSE stream
      const eventSource = new EventSource(`http://localhost:8000/api/stream/${data.scan_id}`)
      
      eventSource.onmessage = (event) => {
        const parsed = JSON.parse(event.data)
        const timeString = new Date().toLocaleTimeString('tr-TR', { hour12: false })
        
        setLogs(prev => [...prev, { time: timeString, ...parsed }])

        if (parsed.type === 'agent_update') {
          if (parsed.details.final_report) {
            try {
              setFinalReport(JSON.parse(parsed.details.final_report))
            } catch (e) {
              // final_report henüz JSON formatında olmayabilir, yoksay
            }
          }
          if (parsed.details.raw_findings) {
            setRawFindings(parsed.details.raw_findings)
          }
        }

        if (parsed.type === 'done' || parsed.type === 'error') {
          eventSource.close()
          setIsScanning(false)
        }
      }

      eventSource.onerror = (error) => {
        console.error("SSE Error:", error)
        eventSource.close()
        setIsScanning(false)
        setLogs(prev => [...prev, { 
          time: new Date().toLocaleTimeString('tr-TR', { hour12: false }), 
          type: 'error', 
          message: 'Bağlantı koptu veya sunucu hatası.' 
        }])
      }

    } catch (error) {
      console.error(error)
      setIsScanning(false)
      setLogs(prev => [...prev, { 
        time: new Date().toLocaleTimeString('tr-TR', { hour12: false }), 
        type: 'error', 
        message: error.message 
      }])
    }
  }

  return (
    <div className="app-container">
      <header>
        <h1>Agentic Security Scanner</h1>
        <p>Otonom LLM Ajanları ile Derinlemesine Mobil Uygulama Analizi</p>
      </header>

      <div className="dashboard">
        {/* Left Panel: Controls */}
        <div className="panel">
          <h2><span className="icon">🎯</span> Görev Kontrol</h2>
          
          <div className="upload-area">
            <span className="upload-icon">📦</span>
            <p style={{ color: 'var(--text-muted)', marginBottom: '1rem' }}>
              Analiz edilecek APK dosyasını sürükleyin veya seçin.
            </p>
            <p style={{ fontSize: '0.8rem', color: '#64748b' }}>(Şu an mock veri kullanılacaktır)</p>
          </div>

          <button 
            className="btn-primary" 
            onClick={startScan}
            disabled={isScanning}
          >
            {isScanning ? 'Analiz Sürüyor...' : 'Sistemi Başlat'}
          </button>

          {isScanning && (
            <div style={{ textAlign: 'center' }}>
              <div className="status-badge status-running">Sistem Aktif</div>
            </div>
          )}
        </div>

        {/* Right Panel: Live Console */}
        <div className="panel">
          <h2><span className="icon">⚡</span> Canlı Ajan İzleme (Live Stream)</h2>
          
          <div className="console">
            {logs.length === 0 && (
              <div style={{ color: '#4b5563', fontStyle: 'italic' }}>
                Sistem beklemede. Tarama başlatıldığında ajan iletişimleri burada akacaktır...
              </div>
            )}
            {logs.map((log, index) => (
              <div key={index} className={`log-entry log-type-${log.type}`}>
                <span className="log-time">[{log.time}]</span>
                {log.agent ? (
                  <>
                    <span style={{ color: 'var(--accent-color)' }}>{log.agent}</span>: {log.details.message}
                  </>
                ) : (
                  <span>{log.message}</span>
                )}
              </div>
            ))}
            <div ref={consoleEndRef} />
          </div>
        </div>
      </div>

      {/* Results Panel */}
      {finalReport && (
        <div className="panel" style={{ marginTop: '2rem' }}>
          <h2><span className="icon">📊</span> Yönetici Özeti (Executive Summary)</h2>
          <p style={{ color: 'var(--text-muted)', marginBottom: '2rem' }}>
            {finalReport.executive_summary}
          </p>
          
          <h3>OWASP Top 10 Eşleşmeleri</h3>
          <div style={{ display: 'grid', gap: '1rem', marginTop: '1rem' }}>
            {finalReport.mapped_findings.map((finding, idx) => (
              <div key={idx} style={{ 
                background: 'rgba(0,0,0,0.3)', 
                padding: '1.5rem', 
                borderRadius: '8px',
                borderLeft: `4px solid ${finding.severity === 'High' ? 'var(--danger)' : 'var(--warning)'}`
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                  <h4 style={{ color: '#fff' }}>{finding.vulnerability_name}</h4>
                  <span style={{ color: finding.severity === 'High' ? 'var(--danger)' : 'var(--warning)', fontWeight: 'bold' }}>
                    {finding.severity}
                  </span>
                </div>
                <div style={{ color: 'var(--accent-color)', fontSize: '0.9rem', marginBottom: '0.5rem' }}>
                  {finding.owasp_category}
                </div>
                <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>{finding.description}</p>
                <div style={{ marginTop: '1rem', fontSize: '0.85rem', color: '#94a3b8', background: '#111827', padding: '0.75rem', borderRadius: '4px' }}>
                  <strong>Çözüm:</strong> {finding.remediation}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Raw Findings Panel */}
      {rawFindings && rawFindings.length > 0 && (
        <div className="panel" style={{ marginTop: '2rem' }}>
          <h2><span className="icon">🔍</span> Ajanların Detaylı Bulguları (Raw Findings)</h2>
          <p style={{ color: 'var(--text-muted)', marginBottom: '2rem' }}>
            Aşağıdaki liste, sistemdeki tüm analiz ajanlarının (statik ve dinamik) herhangi bir OWASP filtrelemesinden geçmemiş ham bulgularını göstermektedir.
          </p>
          
          <div style={{ display: 'grid', gap: '1rem' }}>
            {rawFindings.map((finding, idx) => (
              <div key={idx} style={{ 
                background: 'rgba(0,0,0,0.3)', 
                padding: '1.5rem', 
                borderRadius: '8px',
                borderLeft: `4px solid ${finding.severity === 'High' ? 'var(--danger)' : finding.severity === 'Medium' ? 'var(--warning)' : 'var(--accent-color)'}`
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                  <h4 style={{ color: '#fff' }}>{finding.vulnerability_name}</h4>
                  <div style={{display: 'flex', gap: '1rem', alignItems: 'center'}}>
                    <span style={{ color: '#cbd5e1', fontSize: '0.75rem', background: '#334155', padding: '4px 8px', borderRadius: '12px' }}>
                      Agent: {finding.source_agent || 'Unknown'}
                    </span>
                    <span style={{ color: finding.severity === 'High' ? 'var(--danger)' : finding.severity === 'Medium' ? 'var(--warning)' : 'var(--accent-color)', fontWeight: 'bold' }}>
                      {finding.severity}
                    </span>
                  </div>
                </div>
                <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>{finding.description}</p>
                {finding.affected_files && finding.affected_files.length > 0 && (
                  <div style={{ marginTop: '0.5rem', fontSize: '0.85rem', color: '#94a3b8' }}>
                    <strong>Etkilenen Dosyalar:</strong> {finding.affected_files.join(', ')}
                  </div>
                )}
                <div style={{ marginTop: '1rem', fontSize: '0.85rem', color: '#94a3b8', background: '#111827', padding: '0.75rem', borderRadius: '4px' }}>
                  <strong>Çözüm:</strong> {finding.remediation}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default App
