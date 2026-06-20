import React, { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';

export default function Dashboard() {
  const { jobId } = useParams();
  
  // Chatbot State
  const [messages, setMessages] = useState([
    { role: 'assistant', text: "Hello! I'm your DataNarrate AI Assistant. Ask me anything about your uploaded dataset, or adjust the parameters in the What-If Simulator to forecast changes!" }
  ]);
  const [inputText, setInputText] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const messagesEndRef = useRef(null);

  // Simulator State
  const [conversionRate, setConversionRate] = useState(2.3);
  const [marketingBudget, setMarketingBudget] = useState(15000);

  // Automatically scroll to latest message smoothly
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Construct our underlying backend routing API efficiently.
  const API_URL = (import.meta.env?.VITE_API_URL || import.meta.env?.NEXT_PUBLIC_API_URL || '').replace(/\/+$/, '');

  const sendQuery = async () => {
    if (!inputText.trim()) return;
    
    const newMsg = { role: 'user', text: inputText };
    setMessages(prev => [...prev, newMsg]);
    setInputText('');
    setChatLoading(true);

    try {
      const res = await fetch(`${API_URL}/api/chat/${jobId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: newMsg.text })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed resolving AI operation.");
      
      setMessages(prev => [...prev, { role: 'assistant', text: data.response }]);
    } catch (e) {
      setMessages(prev => [...prev, { role: 'assistant', text: `⚠ Connection Error: ${e.message}` }]);
    } finally {
      setChatLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 p-6 font-sans">
      <header className="mb-8">
        <h1 className="text-3xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-emerald-400">
          DataNarrate Dashboard
        </h1>
        <p className="text-gray-400 text-sm mt-1">Job Context: {jobId}</p>
      </header>

      {/* Tailwind 2-Column Responsive Layout Mapping */}
      <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* COLUMN 1: Visual Outputs & Simulators */}
        <div className="flex flex-col gap-6">
          
          {/* Active Video Analytics Render Component */}
          <div className="bg-gray-900 border border-gray-800 rounded-2xl overflow-hidden shadow-2xl">
            <div className="bg-gray-800/60 p-4 border-b border-gray-700/50">
              <h2 className="text-lg font-semibold text-gray-200">Narrated Insight Render</h2>
            </div>
            <div className="aspect-video bg-black flex items-center justify-center relative">
              <video 
                className="w-full h-full object-cover" 
                controls 
                autoPlay 
                src={`${API_URL}/videos/${jobId}/video.mp4`}
              >
                Your browser fails validating HTML5 visual streams.
              </video>
            </div>
          </div>

          {/* Real-time What-If Simulation Component */}
          <div className="bg-gray-900 border border-gray-800 rounded-2xl shadow-xl flex flex-col overflow-hidden">
             <div className="bg-gray-800/60 p-4 border-b border-gray-700/50">
                <h2 className="text-lg font-semibold text-emerald-400">What-If Simulator</h2>
             </div>
             <div className="p-6 space-y-6">
                <div>
                  <div className="flex justify-between mb-2">
                    <label className="text-sm font-medium text-gray-300">Conversion Rate</label>
                    <span className="text-sm font-bold text-blue-400">{conversionRate.toFixed(1)}%</span>
                  </div>
                  <input 
                    type="range" min="0.1" max="15.0" step="0.1"
                    value={conversionRate} 
                    onChange={e => setConversionRate(parseFloat(e.target.value))}
                    className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-500" 
                  />
                </div>
                
                <div>
                  <div className="flex justify-between mb-2">
                    <label className="text-sm font-medium text-gray-300">Target Marketing Budget</label>
                    <span className="text-sm font-bold text-emerald-400">${marketingBudget.toLocaleString()}</span>
                  </div>
                  <input 
                    type="range" min="1000" max="100000" step="500"
                    value={marketingBudget} 
                    onChange={e => setMarketingBudget(parseInt(e.target.value))}
                    className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-emerald-500" 
                  />
                </div>
                
                <div className="pt-4 border-t border-gray-800">
                    <p className="text-xs text-gray-500">
                      Modifying these variables instantly recalculates potential throughput in connected datasets.
                    </p>
                </div>
             </div>
          </div>
        </div>

        {/* COLUMN 2: Hybrid Conversational Assistant Chatbot */}
        <div className="bg-gray-900 border border-gray-800 rounded-2xl shadow-xl flex flex-col h-[750px]">
          <div className="bg-gray-800/60 p-4 border-b border-gray-700/50 flex items-center justify-between">
             <h2 className="text-lg font-semibold text-blue-400">DataNarrate AI Assistant</h2>
             <span className="text-xs font-medium px-2.5 py-0.5 rounded bg-blue-900/40 text-blue-300 border border-blue-800/60">
               Hybrid Engine Active
             </span>
          </div>

          {/* Internal Stream Body */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((msg, idx) => (
              <div key={idx} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                <div className={`
                  max-w-[85%] px-4 py-3 rounded-2xl text-sm leading-relaxed
                  ${msg.role === 'user' 
                    ? 'bg-blue-600 text-white rounded-br-none' 
                    : 'bg-gray-800 text-gray-200 border border-gray-700 rounded-bl-none'
                  }
                `}>
                  {/* Safely inject response texts - replace standard breaks temporarily with <br/> locally */}
                  {msg.text.split('\n').map((line, i) => <span key={i}>{line}<br /></span>)}
                </div>
              </div>
            ))}
            {chatLoading && (
              <div className="flex items-start">
                 <div className="bg-gray-800 border border-gray-700 text-gray-400 max-w-[85%] px-4 py-3 rounded-2xl rounded-bl-none text-sm animate-pulse">
                   AI is analyzing...
                 </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Form Command Window Layer */}
          <div className="p-4 bg-gray-900 border-t border-gray-800">
             <form 
              onSubmit={(e) => { e.preventDefault(); sendQuery(); }}
              className="flex gap-3"
             >
               <input
                 type="text"
                 value={inputText}
                 onChange={e => setInputText(e.target.value)}
                 disabled={chatLoading}
                 placeholder="Calculate average sales or ask for key market trends..."
                 className="flex-1 bg-gray-800 text-white border border-gray-700 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
               />
               <button
                 type="submit"
                 disabled={chatLoading || !inputText.trim()}
                 className="bg-blue-600 hover:bg-blue-500 text-white font-semibold px-6 py-3 rounded-xl transition duration-200 shadow-lg disabled:opacity-50"
               >
                 Send
               </button>
             </form>
          </div>

        </div>

      </div>
    </div>
  );
}
