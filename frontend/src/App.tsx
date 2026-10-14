import React, { useState, useEffect, useRef } from 'react';
import { 
  Upload, Camera, History, 
  CheckCircle2, AlertTriangle, Download, Trash2, 
  RefreshCw, Play, Square, Layers, Eye, EyeOff
} from 'lucide-react';

interface InspectionResult {
  request_id: string;
  status: string;
  model_name: string;
  category: string;
  prediction: 'NORMAL' | 'ANOMALY' | 'UNCERTAIN';
  anomaly_score_raw: number;
  display_score: number;
  threshold: number;
  inference_ms: number;
  image_width: number;
  image_height: number;
  heatmap_png_base64: string;
  created_at: string;
}

interface AgentStatus {
  agent_id: string;
  online: boolean;
  status: string;
  model_name?: string;
  category?: string;
  hardware_device?: string;
  queue_length: number;
}

export default function App() {
  const [activeTab, setActiveTab] = useState<'inspect' | 'history'>('inspect');
  const [agentStatus, setAgentStatus] = useState<AgentStatus | null>(null);
  
  // Inspect states
  const [inspectMode, setInspectMode] = useState<'upload' | 'camera' | 'live'>('upload');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [inspecting, setInspecting] = useState(false);
  const [currentResult, setCurrentResult] = useState<InspectionResult | null>(null);
  const [inspectError, setInspectError] = useState<string | null>(null);
  const [opacity, setOpacity] = useState<number>(0.65);
  const [showHeatmap, setShowHeatmap] = useState<boolean>(true);

  // Camera & Live preview
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const [isCameraActive, setIsCameraActive] = useState(false);
  const [isLiveRunning, setIsLiveRunning] = useState(false);
  const liveIntervalRef = useRef<number | null>(null);

  // History states
  const [historyItems, setHistoryItems] = useState<any[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  // Poll agent status
  const fetchStatus = () => {
    fetch('/api/v1/status')
      .then(res => res.json())
      .then(data => setAgentStatus(data))
      .catch(() => setAgentStatus({ agent_id: 'unknown', online: false, status: 'offline', queue_length: 0 }));
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  // Fetch History
  const fetchHistory = () => {
    setLoadingHistory(true);
    fetch('/api/v1/inspections')
      .then(res => res.json())
      .then(data => {
        setHistoryItems(data.items || []);
        setLoadingHistory(false);
      })
      .catch(() => setLoadingHistory(false));
  };

  useEffect(() => {
    if (activeTab === 'history') {
      fetchHistory();
    }
  }, [activeTab]);

  // Handle File Selection
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setCurrentResult(null);
      setInspectError(null);
    }
  };

  // Perform Inference Request
  const performInference = async (imageBlob: Blob) => {
    setInspecting(true);
    setInspectError(null);

    const formData = new FormData();
    formData.append('file', imageBlob, 'inspection.jpg');

    try {
      const res = await fetch('/api/v1/inferences', {
        method: 'POST',
        body: formData,
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail?.error?.message || 'Inference error');
      }

      setCurrentResult(data);
    } catch (err: any) {
      setInspectError(err.message || 'Kiểm tra thất bại.');
    } finally {
      setInspecting(false);
    }
  };

  // Start Camera
  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 } });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play();
      }
      setIsCameraActive(true);
    } catch (err) {
      alert('Không thể kết nối webcam: ' + err);
    }
  };

  // Stop Camera
  const stopCamera = () => {
    if (videoRef.current && videoRef.current.srcObject) {
      const stream = videoRef.current.srcObject as MediaStream;
      stream.getTracks().forEach(track => track.stop());
      videoRef.current.srcObject = null;
    }
    setIsCameraActive(false);
    stopLive();
  };

  // Live Preview Loop (Throttled 1 FPS)
  const startLive = () => {
    setIsLiveRunning(true);
    if (!isCameraActive) {
      startCamera();
    }
    liveIntervalRef.current = window.setInterval(() => {
      if (videoRef.current && !inspecting) {
        const canvas = document.createElement('canvas');
        canvas.width = videoRef.current.videoWidth || 640;
        canvas.height = videoRef.current.videoHeight || 480;
        const ctx = canvas.getContext('2d');
        if (ctx) {
          ctx.drawImage(videoRef.current, 0, 0);
          canvas.toBlob((blob) => {
            if (blob) {
              performInference(blob);
            }
          }, 'image/jpeg', 0.85);
        }
      }
    }, 1200); // 1.2s per frame throttle
  };

  const stopLive = () => {
    if (liveIntervalRef.current) {
      clearInterval(liveIntervalRef.current);
      liveIntervalRef.current = null;
    }
    setIsLiveRunning(false);
  };

  // Delete History Record
  const deleteRecord = async (id: string) => {
    await fetch(`/api/v1/inspections/${id}`, { method: 'DELETE' });
    fetchHistory();
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Top Header */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur px-6 py-4 flex items-center justify-between sticky top-0 z-50">
        <div className="flex items-center space-x-3">
          <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-500/20">
            LI
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
              LiveInspectAI
              <span className="text-xs font-semibold px-2 py-0.5 bg-indigo-500/20 text-indigo-300 rounded-md border border-indigo-500/30">
                PatchCore MVP
              </span>
            </h1>
            <p className="text-xs text-slate-400">Hệ thống kiểm tra bất thường thị giác trực thơi gian thực</p>
          </div>
        </div>

        {/* Navigation & Status */}
        <div className="flex items-center space-x-4">
          <div className="flex bg-slate-800 p-1 rounded-lg border border-slate-700">
            <button
              onClick={() => setActiveTab('inspect')}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all ${
                activeTab === 'inspect' ? 'bg-indigo-600 text-white shadow' : 'text-slate-400 hover:text-white'
              }`}
            >
              Kiểm Tra (Inspect)
            </button>
            <button
              onClick={() => setActiveTab('history')}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all ${
                activeTab === 'history' ? 'bg-indigo-600 text-white shadow' : 'text-slate-400 hover:text-white'
              }`}
            >
              Lịch Sử (History)
            </button>
          </div>

          <div className="flex items-center space-x-2 text-sm bg-slate-800/90 px-3.5 py-1.5 rounded-full border border-slate-700">
            <span className={`h-2.5 w-2.5 rounded-full ${agentStatus?.online ? 'bg-emerald-400 shadow-sm shadow-emerald-400 animate-pulse' : 'bg-rose-500'}`} />
            <span className="text-slate-300 font-medium text-xs">
              {agentStatus?.online 
                ? `Agent Online (${agentStatus.hardware_device || 'GPU'})` 
                : 'Agent Offline (Máy tính cá nhân)'}
            </span>
          </div>
        </div>
      </header>

      {/* Main Body */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6 space-y-6">
        {activeTab === 'inspect' ? (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Left Control & Input Panel (5 cols) */}
            <div className="lg:col-span-5 space-y-5">
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-sm space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <h2 className="font-semibold text-white flex items-center gap-2">
                    <Camera className="w-5 h-5 text-indigo-400" />
                    Chế độ kiểm tra
                  </h2>
                  <span className="text-xs bg-slate-800 text-indigo-300 font-mono px-2 py-0.5 rounded border border-slate-700">
                    Category: screw
                  </span>
                </div>

                {/* Mode Selector */}
                <div className="grid grid-cols-3 gap-2 p-1 bg-slate-950 rounded-xl border border-slate-800">
                  <button
                    onClick={() => { setInspectMode('upload'); stopCamera(); }}
                    className={`py-2 text-xs font-medium rounded-lg transition-all ${
                      inspectMode === 'upload' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    Tải ảnh lên
                  </button>
                  <button
                    onClick={() => { setInspectMode('camera'); startCamera(); }}
                    className={`py-2 text-xs font-medium rounded-lg transition-all ${
                      inspectMode === 'camera' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    Chụp webcam
                  </button>
                  <button
                    onClick={() => { setInspectMode('live'); startCamera(); }}
                    className={`py-2 text-xs font-medium rounded-lg transition-all ${
                      inspectMode === 'live' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    Live Preview
                  </button>
                </div>

                {/* Upload Mode Box */}
                {inspectMode === 'upload' && (
                  <div className="space-y-4">
                    <label className="border-2 border-dashed border-slate-700 hover:border-indigo-500 rounded-xl p-6 flex flex-col items-center justify-center cursor-pointer transition-colors bg-slate-950/50">
                      <Upload className="w-8 h-8 text-indigo-400 mb-2" />
                      <span className="text-sm font-medium text-slate-200">Chọn ảnh kiểm tra (JPG, PNG, WebP)</span>
                      <span className="text-xs text-slate-500 mt-1">Hỗ trợ ảnh ốc vít cơ khí MVTec AD</span>
                      <input type="file" accept="image/jpeg,image/png,image/webp" onChange={handleFileChange} className="hidden" />
                    </label>

                    {selectedFile && (
                      <button
                        onClick={() => selectedFile && performInference(selectedFile)}
                        disabled={inspecting || !agentStatus?.online}
                        className="w-full py-3 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 disabled:text-slate-500 text-white font-semibold rounded-xl transition-all flex items-center justify-center gap-2 shadow-lg shadow-indigo-600/20"
                      >
                        {inspecting ? (
                          <>
                            <RefreshCw className="w-4 h-4 animate-spin" />
                            Đang xử lý PatchCore trên GPU...
                          </>
                        ) : (
                          <>
                            <Play className="w-4 h-4" />
                            Bắt đầu kiểm tra ảnh
                          </>
                        )}
                      </button>
                    )}
                  </div>
                )}

                {/* Camera / Live Mode Box */}
                {(inspectMode === 'camera' || inspectMode === 'live') && (
                  <div className="space-y-4">
                    <div className="relative aspect-video bg-black rounded-xl overflow-hidden border border-slate-800">
                      <video ref={videoRef} className="w-full h-full object-cover" autoPlay playsInline muted />
                      {!isCameraActive && (
                        <div className="absolute inset-0 flex items-center justify-center bg-slate-950 text-slate-400 text-xs">
                          Camera chưa kích hoạt
                        </div>
                      )}
                    </div>

                    <div className="flex gap-2">
                      {inspectMode === 'camera' && (
                        <button
                          onClick={() => {
                            if (videoRef.current) {
                              const canvas = document.createElement('canvas');
                              canvas.width = videoRef.current.videoWidth || 640;
                              canvas.height = videoRef.current.videoHeight || 480;
                              const ctx = canvas.getContext('2d');
                              if (ctx) {
                                ctx.drawImage(videoRef.current, 0, 0);
                                setPreviewUrl(canvas.toDataURL('image/jpeg'));
                                canvas.toBlob((blob) => {
                                  if (blob) performInference(blob);
                                }, 'image/jpeg');
                              }
                            }
                          }}
                          disabled={!isCameraActive || inspecting || !agentStatus?.online}
                          className="flex-1 py-3 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 text-white font-semibold rounded-xl transition-all flex items-center justify-center gap-2"
                        >
                          <Camera className="w-4 h-4" />
                          Chụp & Kiểm tra
                        </button>
                      )}

                      {inspectMode === 'live' && (
                        <button
                          onClick={isLiveRunning ? stopLive : startLive}
                          disabled={!agentStatus?.online}
                          className={`flex-1 py-3 font-semibold rounded-xl transition-all flex items-center justify-center gap-2 ${
                            isLiveRunning ? 'bg-rose-600 hover:bg-rose-500 text-white' : 'bg-emerald-600 hover:bg-emerald-500 text-white'
                          }`}
                        >
                          {isLiveRunning ? (
                            <>
                              <Square className="w-4 h-4" />
                              Dừng Live Stream
                            </>
                          ) : (
                            <>
                              <Play className="w-4 h-4" />
                              Bắt đầu Live Preview (1 FPS)
                            </>
                          )}
                        </button>
                      )}

                      <button
                        onClick={stopCamera}
                        className="px-4 py-3 bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium rounded-xl transition-all"
                      >
                        Tắt Cam
                      </button>
                    </div>
                  </div>
                )}

                {/* Error Banner */}
                {inspectError && (
                  <div className="p-3.5 bg-rose-950/50 border border-rose-800 rounded-xl text-rose-300 text-xs flex items-center gap-2.5">
                    <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
                    <span>{inspectError}</span>
                  </div>
                )}
              </div>
            </div>

            {/* Right Display & Anomaly Heatmap (7 cols) */}
            <div className="lg:col-span-7 space-y-5">
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-sm space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <h2 className="font-semibold text-white flex items-center gap-2">
                    <Layers className="w-5 h-5 text-indigo-400" />
                    Trực quan hóa kết quả (Heatmap Overlay)
                  </h2>
                  {currentResult && (
                    <div className="flex items-center gap-3">
                      <button
                        onClick={() => setShowHeatmap(!showHeatmap)}
                        className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-white"
                      >
                        {showHeatmap ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
                        {showHeatmap ? 'Ẩn Heatmap' : 'Hiện Heatmap'}
                      </button>
                      <input
                        type="range"
                        min="0.1"
                        max="1"
                        step="0.05"
                        value={opacity}
                        onChange={(e) => setOpacity(parseFloat(e.target.value))}
                        className="w-20 accent-indigo-500"
                        title="Độ mờ lớp phủ"
                      />
                    </div>
                  )}
                </div>

                {/* Canvas / Image Display */}
                <div className="relative aspect-video max-h-[460px] bg-slate-950 rounded-xl overflow-hidden border border-slate-800 flex items-center justify-center">
                  {previewUrl ? (
                    <div className="relative w-full h-full flex items-center justify-center overflow-hidden">
                      {/* Original Base Image */}
                      <img src={previewUrl} alt="Inspection Source" className="max-w-full max-h-full object-contain" />
                      {/* Anomaly Heatmap Mask Overlay */}
                      {showHeatmap && currentResult?.heatmap_png_base64 && (
                        <img
                          src={`data:image/png;base64,${currentResult.heatmap_png_base64}`}
                          alt="Anomaly Heatmap"
                          style={{ opacity }}
                          className="absolute inset-0 max-w-full max-h-full object-contain mix-blend-screen pointer-events-none filter hue-rotate-180 contrast-200"
                        />
                      )}
                    </div>
                  ) : (
                    <div className="text-center p-6 text-slate-500">
                      <p className="text-sm font-medium">Chưa có ảnh được chọn</p>
                      <p className="text-xs mt-1">Tải ảnh lên hoặc chụp từ camera để xem lớp phủ lỗi</p>
                    </div>
                  )}
                </div>

                {/* Results Indicator Bar */}
                {currentResult && (
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-2">
                    <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800">
                      <span className="text-xs text-slate-400 block mb-1">Kết luận</span>
                      <div className="flex items-center gap-2">
                        {currentResult.prediction === 'NORMAL' ? (
                          <>
                            <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                            <span className="text-base font-bold text-emerald-400">NORMAL</span>
                          </>
                        ) : (
                          <>
                            <AlertTriangle className="w-5 h-5 text-rose-400" />
                            <span className="text-base font-bold text-rose-400">DEFECT (ANOMALY)</span>
                          </>
                        )}
                      </div>
                    </div>

                    <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800">
                      <span className="text-xs text-slate-400 block mb-1">Điểm bất thường (Score)</span>
                      <span className="text-lg font-bold text-white">
                        {currentResult.anomaly_score_raw.toFixed(2)}
                      </span>
                      <span className="text-[11px] text-slate-500 block">Ngưỡng: {currentResult.threshold}</span>
                    </div>

                    <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800">
                      <span className="text-xs text-slate-400 block mb-1">Thời gian Inference</span>
                      <span className="text-lg font-bold text-indigo-400">
                        {currentResult.inference_ms.toFixed(1)} ms
                      </span>
                      <span className="text-[11px] text-slate-500 block">GTX 1660 Ti</span>
                    </div>

                    <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800">
                      <span className="text-xs text-slate-400 block mb-1">Mô hình</span>
                      <span className="text-sm font-bold text-slate-200 block truncate">
                        {currentResult.model_name}
                      </span>
                      <span className="text-[11px] text-slate-500 block">v{currentResult.category}</span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        ) : (
          /* History Table Tab */
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-sm space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <h2 className="text-lg font-bold text-white flex items-center gap-2">
                  <History className="w-5 h-5 text-indigo-400" />
                  Nhật ký kiểm tra (Inspection History)
                </h2>
                <p className="text-xs text-slate-400 mt-0.5">Dữ liệu kiểm tra thực tế lưu trong cơ sở dữ liệu SQLite</p>
              </div>

              <div className="flex items-center gap-3">
                <a
                  href="/api/v1/inspections/export.csv"
                  download
                  className="px-3.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-lg border border-slate-700 flex items-center gap-2 transition-all"
                >
                  <Download className="w-3.5 h-3.5" />
                  Xuất file CSV
                </a>
                <button
                  onClick={fetchHistory}
                  className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800"
                >
                  <RefreshCw className="w-4 h-4" />
                </button>
              </div>
            </div>

            {loadingHistory ? (
              <div className="text-center py-12 text-slate-500">Đang tải lịch sử...</div>
            ) : historyItems.length === 0 ? (
              <div className="text-center py-12 text-slate-500">Chưa có lần kiểm tra nào được ghi lại.</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs text-slate-300">
                  <thead className="bg-slate-950 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
                    <tr>
                      <th className="px-4 py-3">Thời gian</th>
                      <th className="px-4 py-3">Kết luận</th>
                      <th className="px-4 py-3">Raw Score</th>
                      <th className="px-4 py-3">Ngưỡng</th>
                      <th className="px-4 py-3">Inference (ms)</th>
                      <th className="px-4 py-3">Kích thước</th>
                      <th className="px-4 py-3 text-right">Thao tác</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono">
                    {historyItems.map((item: any) => (
                      <tr key={item.id} className="hover:bg-slate-800/40 transition-colors">
                        <td className="px-4 py-3 font-sans text-slate-400">
                          {new Date(item.created_at).toLocaleString()}
                        </td>
                        <td className="px-4 py-3">
                          <span
                            className={`px-2 py-0.5 rounded font-sans font-semibold text-[11px] ${
                              item.prediction === 'NORMAL'
                                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                                : 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                            }`}
                          >
                            {item.prediction}
                          </span>
                        </td>
                        <td className="px-4 py-3">{item.anomaly_score_raw?.toFixed(2)}</td>
                        <td className="px-4 py-3">{item.threshold}</td>
                        <td className="px-4 py-3 text-indigo-300">{item.inference_ms?.toFixed(1)} ms</td>
                        <td className="px-4 py-3 text-slate-500">{item.image_width}x{item.image_height}</td>
                        <td className="px-4 py-3 text-right">
                          <button
                            onClick={() => deleteRecord(item.id)}
                            className="p-1 hover:text-rose-400 text-slate-500 transition-colors"
                            title="Xóa bản ghi"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
