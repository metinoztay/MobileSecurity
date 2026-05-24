import { useState, useRef, useEffect } from 'react'

function App() {
  const [isScanning, setIsScanning] = useState(false)
  const [logs, setLogs] = useState([])
  const [finalReport, setFinalReport] = useState(null)
  const [rawFindings, setRawFindings] = useState([])
  const [selectedFile, setSelectedFile] = useState(null)
  const [useMockData, setUseMockData] = useState(true)
  const [sourceCode, setSourceCode] = useState(null)
  const [activeFile, setActiveFile] = useState(null)
  const consoleEndRef = useRef(null)
  const eventSourceRef = useRef(null)

  const scrollToBottom = () => {
    consoleEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [logs])

  const startScan = async () => {
    if (!useMockData && !selectedFile) {
      alert("Lütfen bir APK dosyası seçin veya Mock Veri seçeneğini işaretleyin.")
      return
    }

    setIsScanning(true)
    setLogs([])
    setFinalReport(null)
    setRawFindings([])
    setSourceCode(null)
    setActiveFile(null)

    try {
      // 1. Start the scan via POST
      const formData = new FormData()
      formData.append('use_mock', useMockData ? "true" : "false")
      if (selectedFile && !useMockData) {
        formData.append('file', selectedFile)
      }

      const res = await fetch('http://localhost:8000/api/scan', {
        method: 'POST',
        body: formData
      })
      const data = await res.json()
      
      if (!data.scan_id) {
        throw new Error('Scan ID alınamadı.')
      }

      // 2. Connect to SSE stream
      const eventSource = new EventSource(`http://localhost:8000/api/stream/${data.scan_id}`)
      eventSourceRef.current = eventSource
      
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
          if (parsed.details.source_code) {
            setSourceCode(parsed.details.source_code)
            const keys = Object.keys(parsed.details.source_code)
            if (keys.length > 0 && !activeFile) {
              setActiveFile(keys[0])
            }
          }
        }

        if (parsed.type === 'done' || parsed.type === 'error') {
          eventSource.close()
          eventSourceRef.current = null
          setIsScanning(false)
        }
      }

      eventSource.onerror = (error) => {
        console.error("SSE Error:", error)
        eventSource.close()
        eventSourceRef.current = null
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

  const stopScan = () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
    }
    setIsScanning(false)
    setLogs(prev => [...prev, { 
      time: new Date().toLocaleTimeString('tr-TR', { hour12: false }), 
      type: 'info', 
      message: 'Tarama kullanıcı tarafından durduruldu.' 
    }])
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
          
          <div 
            className="upload-area" 
            style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', position: 'relative' }}
            onClick={() => document.getElementById('file-upload').click()}
          >
            <span className="upload-icon">📦</span>
            <p style={{ color: 'var(--text-main)', marginBottom: '0.5rem', fontWeight: '600' }}>
              APK Dosyası Yükleyin
            </p>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              Seçmek için bu alana tıklayın
            </p>
            <input 
              id="file-upload"
              type="file" 
              accept=".apk" 
              onChange={(e) => {
                 setSelectedFile(e.target.files[0])
                 setUseMockData(false)
              }} 
              style={{ display: 'none' }}
            />
            {selectedFile && (
              <div style={{ marginTop: '1rem', background: 'rgba(0, 255, 157, 0.1)', border: '1px solid var(--accent-color)', borderRadius: '8px', padding: '0.5rem 1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span style={{color: 'var(--accent-color)', fontSize: '0.9rem', fontWeight: 'bold'}}>✓ {selectedFile.name}</span>
              </div>
            )}
          </div>
          
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem', background: '#111827', padding: '1rem', borderRadius: '12px', border: '1px solid #1f2937' }}>
            <div>
              <h4 style={{ fontSize: '0.95rem', color: '#e2e8f0', marginBottom: '0.2rem' }}>Hızlı Test Modu (Mock Veri)</h4>
              <p style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Dosya yüklemeden sistemi örnek verilerle test et</p>
            </div>
            <label style={{ position: 'relative', display: 'inline-block', width: '44px', height: '24px' }}>
              <input 
                type="checkbox" 
                checked={useMockData} 
                onChange={(e) => {
                   setUseMockData(e.target.checked)
                   if(e.target.checked) setSelectedFile(null)
                }} 
                style={{ opacity: 0, width: 0, height: 0 }}
              />
              <span style={{
                position: 'absolute',
                cursor: 'pointer',
                top: 0, left: 0, right: 0, bottom: 0,
                backgroundColor: useMockData ? 'var(--accent-color)' : '#334155',
                transition: '.4s',
                borderRadius: '24px'
              }}>
                <span style={{
                  position: 'absolute',
                  content: '""',
                  height: '16px',
                  width: '16px',
                  left: useMockData ? '24px' : '4px',
                  bottom: '4px',
                  backgroundColor: useMockData ? '#000' : '#fff',
                  transition: '.4s',
                  borderRadius: '50%',
                  boxShadow: '0 2px 4px rgba(0,0,0,0.2)'
                }} />
              </span>
            </label>
          </div>

          <div style={{ display: 'flex', gap: '1rem' }}>
            {!isScanning ? (
              <button 
                className="btn-primary" 
                onClick={startScan}
                style={{ flex: 1 }}
              >
                Sistemi Başlat
              </button>
            ) : (
              <button 
                className="btn-danger" 
                onClick={stopScan}
                style={{ flex: 1 }}
              >
                Durdur
              </button>
            )}
          </div>

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
        <>
          {finalReport.static_report && (
            <div className="panel" style={{ marginTop: '2rem' }}>
              <h2><span className="icon">📊</span> Statik Analiz Raporu</h2>
              <p style={{ color: 'var(--text-muted)', marginBottom: '2rem' }}>
                {finalReport.static_report.executive_summary}
              </p>
              
              <h3>OWASP Top 10 Eşleşmeleri (Statik)</h3>
              <div style={{ display: 'grid', gap: '1rem', marginTop: '1rem' }}>
                {finalReport.static_report.mapped_findings.map((finding, idx) => (
                  <div key={`static-${idx}`} style={{ 
                    background: 'rgba(0,0,0,0.3)', 
                    padding: '1.5rem', 
                    borderRadius: '8px',
                    borderLeft: `4px solid ${finding.severity === 'High' ? 'var(--danger)' : 'var(--warning)'}`,
                    minWidth: 0
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
                    {finding.code_snippet && (
                      <div style={{ marginTop: '0.75rem', marginBottom: '0.75rem' }}>
                        <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginBottom: '0.25rem' }}>
                          <strong>Kod Parçacığı (Snippet)</strong> {finding.line_number && <span>- Satır: {finding.line_number}</span>}
                        </div>
                        <pre style={{ 
                          background: '#020617', 
                          padding: '0.75rem', 
                          borderRadius: '4px', 
                          overflowX: 'auto',
                          fontSize: '0.8rem',
                          color: '#e2e8f0',
                          border: '1px solid #1e293b'
                        }}>
                          <code>{finding.code_snippet}</code>
                        </pre>
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

          {finalReport.dynamic_report && (
            <div className="panel" style={{ marginTop: '2rem' }}>
              <h2><span className="icon">🚀</span> Dinamik Analiz Raporu</h2>
              <p style={{ color: 'var(--text-muted)', marginBottom: '2rem' }}>
                {finalReport.dynamic_report.executive_summary}
              </p>
              
              <h3>OWASP Top 10 Eşleşmeleri (Dinamik)</h3>
              <div style={{ display: 'grid', gap: '1rem', marginTop: '1rem' }}>
                {finalReport.dynamic_report.mapped_findings.map((finding, idx) => (
                  <div key={`dynamic-${idx}`} style={{ 
                    background: 'rgba(0,0,0,0.3)', 
                    padding: '1.5rem', 
                    borderRadius: '8px',
                    borderLeft: `4px solid ${finding.severity === 'High' ? 'var(--danger)' : 'var(--warning)'}`,
                    minWidth: 0
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
                    {finding.code_snippet && (
                      <div style={{ marginTop: '0.75rem', marginBottom: '0.75rem' }}>
                        <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginBottom: '0.25rem' }}>
                          <strong>Kod Parçacığı (Snippet)</strong> {finding.line_number && <span>- Satır: {finding.line_number}</span>}
                        </div>
                        <pre style={{ 
                          background: '#020617', 
                          padding: '0.75rem', 
                          borderRadius: '4px', 
                          overflowX: 'auto',
                          fontSize: '0.8rem',
                          color: '#e2e8f0',
                          border: '1px solid #1e293b'
                        }}>
                          <code>{finding.code_snippet}</code>
                        </pre>
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

          {!finalReport.static_report && !finalReport.dynamic_report && finalReport.executive_summary && (
            <div className="panel" style={{ marginTop: '2rem' }}>
              <h2><span className="icon">📊</span> Yönetici Özeti (Executive Summary)</h2>
              <p style={{ color: 'var(--text-muted)', marginBottom: '2rem' }}>
                {finalReport.executive_summary}
              </p>
              
              <h3>OWASP Top 10 Eşleşmeleri</h3>
              <div style={{ display: 'grid', gap: '1rem', marginTop: '1rem' }}>
                {finalReport.mapped_findings?.map((finding, idx) => (
                  <div key={`fallback-${idx}`} style={{ 
                    background: 'rgba(0,0,0,0.3)', 
                    padding: '1.5rem', 
                    borderRadius: '8px',
                    borderLeft: `4px solid ${finding.severity === 'High' ? 'var(--danger)' : 'var(--warning)'}`,
                    minWidth: 0
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
                    {finding.code_snippet && (
                      <div style={{ marginTop: '0.75rem', marginBottom: '0.75rem' }}>
                        <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginBottom: '0.25rem' }}>
                          <strong>Kod Parçacığı (Snippet)</strong> {finding.line_number && <span>- Satır: {finding.line_number}</span>}
                        </div>
                        <pre style={{ 
                          background: '#020617', 
                          padding: '0.75rem', 
                          borderRadius: '4px', 
                          overflowX: 'auto',
                          fontSize: '0.8rem',
                          color: '#e2e8f0',
                          border: '1px solid #1e293b'
                        }}>
                          <code>{finding.code_snippet}</code>
                        </pre>
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
        </>
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
                borderLeft: `4px solid ${finding.severity === 'High' ? 'var(--danger)' : finding.severity === 'Medium' ? 'var(--warning)' : 'var(--accent-color)'}`,
                minWidth: 0
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
                {finding.code_snippet && (
                  <div style={{ marginTop: '0.75rem', marginBottom: '0.75rem' }}>
                    <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginBottom: '0.25rem' }}>
                      <strong>Kod Parçacığı (Snippet)</strong> {finding.line_number && <span>- Satır: {finding.line_number}</span>}
                    </div>
                    <pre style={{ 
                      background: '#020617', 
                      padding: '0.75rem', 
                      borderRadius: '4px', 
                      overflowX: 'auto',
                      fontSize: '0.8rem',
                      color: '#e2e8f0',
                      border: '1px solid #1e293b'
                    }}>
                      <code>{finding.code_snippet}</code>
                    </pre>
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

      {/* Source Code Panel */}
      {sourceCode && Object.keys(sourceCode).length > 0 && (
        <div className="panel" style={{ marginTop: '2rem' }}>
          <h2><span className="icon">📂</span> Çıkarılan Dosyalar (Decompiled Files)</h2>
          <p style={{ color: 'var(--text-muted)', marginBottom: '1rem' }}>
            APK içerisinden ayrıştırılan ve ajanların analizine sunulan kritik dosyalar.
          </p>
          
          <div style={{ display: 'flex', gap: '1rem', border: '1px solid #334155', borderRadius: '8px', overflow: 'hidden' }}>
            {/* File List */}
            <div style={{ width: '250px', background: '#0f172a', borderRight: '1px solid #334155', display: 'flex', flexDirection: 'column' }}>
              {Object.keys(sourceCode).map(filename => (
                <button 
                  key={filename}
                  onClick={() => setActiveFile(filename)}
                  style={{
                    padding: '1rem',
                    textAlign: 'left',
                    background: activeFile === filename ? '#1e293b' : 'transparent',
                    border: 'none',
                    borderBottom: '1px solid #1e293b',
                    color: activeFile === filename ? 'var(--accent-color)' : '#cbd5e1',
                    cursor: 'pointer',
                    fontSize: '0.85rem',
                    transition: 'all 0.2s'
                  }}
                >
                  {filename.split('/').pop()}
                </button>
              ))}
            </div>
            
            {/* File Content */}
            <div style={{ flex: 1, padding: '1rem', background: '#020617', maxHeight: '500px', overflowY: 'auto' }}>
              <div style={{ fontSize: '0.8rem', color: '#64748b', marginBottom: '0.5rem' }}>{activeFile}</div>
              <pre style={{ 
                margin: 0, 
                color: '#e2e8f0', 
                fontSize: '0.85rem', 
                fontFamily: 'monospace',
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-all'
              }}>
                {sourceCode[activeFile]}
              </pre>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
