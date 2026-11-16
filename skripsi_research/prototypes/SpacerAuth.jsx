import React, { useState } from 'react';

/**
 * SpacerAuth Component
 * Implementasi UI/UX Autentikasi "Spacer" sesuai referensi desain
 * Fitur:
 * - Layered Cloud Divider (Vector SVG berjenjang 3 lapis)
 * - Underline Input minimalis dengan ikon validasi centang live
 * - Toggle transisi mulus antara Register & Login (SPA State)
 * - Desain responsif penuh (Desktop Split-Screen & Mobile Vertical Stack)
 */
export default function SpacerAuth() {
  const [isRegister, setIsRegister] = useState(true);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    agreeTerms: true,
  });
  const [toastMessage, setToastMessage] = useState('');

  // Validasi format
  const isNameValid = formData.name.trim().length >= 2;
  const isEmailValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email.trim());
  const isPasswordValid = formData.password.length >= 6;

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const action = isRegister ? 'Pendaftaran Akun' : 'Otentikasi Masuk';
    setToastMessage(`🎉 ${action} Berhasil! Memproses ke sistem...`);
    setTimeout(() => setToastMessage(''), 3500);
  };

  return (
    <div className="min-h-screen bg-[#dcdfe5] flex items-center justify-center p-4 md:p-8 font-['Poppins',sans-serif]">
      
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 bg-slate-900 text-white px-5 py-3 rounded-2xl shadow-xl flex items-center gap-3 z-50 text-xs animate-bounce">
          <span>🚀</span>
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Main Container Card */}
      <div className="w-full max-w-4xl bg-white rounded-[32px] shadow-2xl overflow-hidden grid grid-cols-1 md:grid-cols-12 min-h-[520px] border border-slate-100 relative">
        
        {/* ================= LEFT BRAND PANEL (BLUE GRADIENT) ================= */}
        <div className="md:col-span-5 bg-gradient-to-br from-[#1056e8] via-[#1a58eb] to-[#0d42bf] text-white p-8 flex flex-col justify-between items-center text-center relative overflow-hidden">
          
          {/* Subtle Ambient Glows */}
          <div className="absolute -top-12 -left-12 w-48 h-48 bg-white/10 rounded-full blur-2xl pointer-events-none" />
          <div className="absolute -bottom-12 -right-12 w-48 h-48 bg-blue-400/20 rounded-full blur-2xl pointer-events-none" />

          {/* Top Title */}
          <div className="relative z-10 pt-2">
            <span className="text-sm font-light tracking-wide text-blue-100">Welcome to</span>
          </div>

          {/* Central Rocket & Title */}
          <div className="relative z-10 flex flex-col items-center my-6">
            <div className="w-24 h-24 rounded-full bg-white flex items-center justify-center shadow-lg shadow-blue-950/20 mb-4 transition-transform hover:scale-105 duration-300">
              <svg className="w-12 h-12 text-[#155dfc]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"/>
                <path d="m12 15-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"/>
                <path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0"/>
                <path d="M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5"/>
              </svg>
            </div>

            <h2 className="text-2xl font-bold tracking-tight text-white mb-2">Spacer</h2>

            <p className="text-[11px] leading-relaxed text-blue-100/80 max-w-[210px] font-light">
              Lorem ipsum dolor sit amet, consectetuer adipiscing elit, sed diam nonummy nibh euismod tincidunt ut laoreet dolore magna aliquam erat volutpat.
            </p>
          </div>

          {/* Creator Footer Info */}
          <div className="relative z-10 text-[9px] tracking-wider font-medium text-blue-200/90 flex items-center gap-2">
            <span>CREATOR HERE</span>
            <span className="text-blue-300/50">|</span>
            <span>DESIGNER HERE</span>
          </div>
        </div>

        {/* ================= VERTICAL LAYERED CLOUD DIVIDER (DESKTOP) ================= */}
        <div className="hidden md:block absolute left-[41.666%] top-0 bottom-0 w-16 -ml-8 z-20 pointer-events-none">
          <svg className="w-full h-full" viewBox="0 0 100 500" preserveAspectRatio="none">
            {/* Layer 1: Back Soft Cloud */}
            <path 
              d="M 100,0 L 52,0 Q 8,60 48,125 Q 0,185 42,250 Q 6,325 50,385 Q 16,445 62,500 L 100,500 Z" 
              fill="#60a5fa" 
              opacity="0.45" 
            />
            {/* Layer 2: Mid Light Blue Cloud */}
            <path 
              d="M 100,0 L 68,0 Q 28,65 62,135 Q 18,205 58,275 Q 24,345 68,405 Q 34,465 78,500 L 100,500 Z" 
              fill="#93c5fd" 
              opacity="0.65" 
            />
            {/* Layer 3: Solid White Cloud (Merges into Form) */}
            <path 
              d="M 100,0 L 82,0 Q 45,70 78,145 Q 35,225 72,295 Q 38,365 82,425 Q 52,485 88,500 L 100,500 Z" 
              fill="#ffffff" 
            />
          </svg>
        </div>

        {/* ================= HORIZONTAL LAYERED CLOUD DIVIDER (MOBILE) ================= */}
        <div className="block md:hidden w-full h-8 -mt-1 relative z-20 pointer-events-none">
          <svg className="w-full h-full" viewBox="0 0 300 45" preserveAspectRatio="none">
            <path d="M 0,45 L 0,22 Q 40,2 80,20 Q 120,4 160,22 Q 200,6 240,24 Q 275,10 300,26 L 300,45 Z" fill="#60a5fa" opacity="0.45" />
            <path d="M 0,45 L 0,28 Q 45,10 90,26 Q 135,12 175,28 Q 215,14 255,30 Q 285,18 300,32 L 300,45 Z" fill="#93c5fd" opacity="0.65" />
            <path d="M 0,45 L 0,34 Q 50,18 100,32 Q 150,18 200,35 Q 245,22 280,36 L 300,38 L 300,45 Z" fill="#ffffff" />
          </svg>
        </div>

        {/* ================= RIGHT FORM PANEL (WHITE) ================= */}
        <div className="md:col-span-7 p-8 lg:p-12 flex flex-col justify-center relative bg-white z-10">
          
          <div className="text-center mb-8">
            <h3 className="text-xl lg:text-2xl font-semibold text-slate-800 tracking-tight">
              {isRegister ? 'Create your account' : 'Welcome back'}
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              {isRegister ? 'Lengkapi kredensial untuk mendaftar akun Spacer' : 'Masukkan email dan password untuk masuk'}
            </p>
          </div>

          <form onSubmit={handleSubmit} className="max-w-xs mx-auto w-full space-y-4">
            
            {/* 1. Name Field (Slide & Fade Transition) */}
            <div 
              className={`transition-all duration-300 overflow-hidden ${
                isRegister ? 'max-h-24 opacity-100' : 'max-h-0 opacity-0 pointer-events-none -my-2'
              }`}
            >
              <label className="block text-xs font-semibold text-slate-700 mb-1">Name</label>
              <div className="relative flex items-center">
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  placeholder="Enter your name"
                  className="w-full border-b-[1.5px] border-blue-100 focus:border-blue-600 outline-none py-1.5 text-xs text-slate-700 placeholder:text-slate-300 placeholder:italic pr-8 transition-colors"
                />
                <span className={`absolute right-1 text-sm font-bold transition-all duration-300 ${
                  isNameValid ? 'text-blue-500 opacity-100 scale-110' : 'text-slate-300 opacity-20'
                }`}>
                  ✓
                </span>
              </div>
            </div>

            {/* 2. E-mail Address Field */}
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">E-mail Adress</label>
              <div className="relative flex items-center">
                <input
                  type="email"
                  name="email"
                  required
                  value={formData.email}
                  onChange={handleChange}
                  placeholder="Enter your mail"
                  className="w-full border-b-[1.5px] border-blue-100 focus:border-blue-600 outline-none py-1.5 text-xs text-slate-700 placeholder:text-slate-300 placeholder:italic pr-8 transition-colors"
                />
                <span className={`absolute right-1 text-sm font-bold transition-all duration-300 ${
                  isEmailValid ? 'text-blue-500 opacity-100 scale-110' : 'text-slate-300 opacity-20'
                }`}>
                  ✓
                </span>
              </div>
            </div>

            {/* 3. Password Field */}
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Password</label>
              <div className="relative flex items-center">
                <input
                  type="password"
                  name="password"
                  required
                  value={formData.password}
                  onChange={handleChange}
                  placeholder="Enter your password"
                  className="w-full border-b-[1.5px] border-blue-100 focus:border-blue-600 outline-none py-1.5 text-xs text-slate-700 placeholder:text-slate-300 placeholder:italic pr-8 transition-colors"
                />
                <span className={`absolute right-1 text-sm font-bold transition-all duration-300 ${
                  isPasswordValid ? 'text-blue-500 opacity-100 scale-110' : 'text-slate-300 opacity-20'
                }`}>
                  ✓
                </span>
              </div>
            </div>

            {/* 4. Terms Checkbox */}
            <div className="pt-1">
              <label className="flex items-start gap-2 cursor-pointer select-none">
                <input
                  type="checkbox"
                  name="agreeTerms"
                  checked={formData.agreeTerms}
                  onChange={handleChange}
                  className="mt-0.5 w-3.5 h-3.5 rounded border-slate-300 text-blue-600 focus:ring-0 cursor-pointer"
                />
                <span className="text-[10px] text-slate-600 leading-tight">
                  {isRegister ? (
                    <>
                      By Signing Up, I agree with{' '}
                      <a href="#" className="text-slate-700 font-medium hover:underline">
                        Terms & Conditions
                      </a>
                    </>
                  ) : (
                    'Ingat saya di perangkat ini (Remember Me)'
                  )}
                </span>
              </label>
            </div>

            {/* 5. Action Buttons (Sign Up & Sign In) */}
            <div className="pt-4 flex items-center justify-center gap-3">
              {/* Primary Active Button */}
              <button
                type="submit"
                className="bg-gradient-to-r from-[#175cf2] to-[#124bce] hover:from-[#1b64ff] hover:to-[#1752de] text-white text-xs font-semibold px-7 py-2.5 rounded-full shadow-lg shadow-blue-500/30 transition-all duration-200 hover:-translate-y-0.5 active:translate-y-0 min-w-[100px]"
              >
                {isRegister ? 'Sign Up' : 'Sign In'}
              </button>

              {/* Secondary Outline Button (Toggle Mode) */}
              <button
                type="button"
                onClick={() => setIsRegister(!isRegister)}
                className="bg-white hover:bg-slate-50 text-slate-500 hover:text-slate-800 text-xs font-medium px-7 py-2.5 rounded-full border border-slate-300 hover:border-slate-400 transition-all duration-200 min-w-[100px]"
              >
                {isRegister ? 'Sign In' : 'Sign Up'}
              </button>
            </div>

          </form>

          {/* Quick Switch Text */}
          <div className="text-center mt-6">
            <span className="text-[11px] text-slate-400">
              {isRegister ? 'Sudah punya akun? ' : 'Belum memiliki akun? '}
              <button
                type="button"
                onClick={() => setIsRegister(!isRegister)}
                className="text-blue-600 font-semibold hover:underline"
              >
                {isRegister ? 'Masuk di sini' : 'Daftar sekarang'}
              </button>
            </span>
          </div>

        </div>

      </div>

    </div>
  );
}
