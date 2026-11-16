import React, { useState } from 'react';

/**
 * SpacerAuthSlider Component
 * Senior Frontend UI/UX Developer & Spesialis UI Layout & Component Design
 * 
 * Sesuai Spesifikasi & Referensi Gambar:
 * 1. Proporsi & Tata Letak: Berada di tengah layar, sudut rounded-3xl (28px), responsive container
 *    berukuran proporsional (max-w-[720px] x 440px) tanpa scrollbar / terpotong.
 * 2. Panel Kiri (Informasi & Branding): 'Welcome to', roket melingkar, 'Spacer', deskripsi,
 *    tombol navigasi outline ('Sudah Punya Akun? Sign In ➔'), dan footer 'CREATOR HERE | DESIGNER HERE'.
 * 3. Panel Kanan (Form Input & Aksi): 'Create your account', panduan subjudul, field underline input
 *    (Name, E-mail Adress, Password) dengan tanda centang halus, persetujuan syarat ketentuan,
 *    tombol aksi utama pil biru gradasi penuh, serta teks navigasi 'Sudah punya akun? Masuk di sini'.
 */
export default function SpacerAuthSlider() {
  // State navigasi auth: false = Sign Up (default), true = Sign In
  const [isSignIn, setIsSignIn] = useState(false);

  // State data formulir
  const [signUpForm, setSignUpForm] = useState({ name: '', email: '', password: '', terms: true });
  const [signInForm, setSignInForm] = useState({ email: '', password: '', remember: true });
  const [toastMessage, setToastMessage] = useState('');

  // Validasi real-time
  const isUpNameValid = signUpForm.name.trim().length >= 2;
  const isUpEmailValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(signUpForm.email.trim());
  const isUpPassValid = signUpForm.password.length >= 6;

  const isInEmailValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(signInForm.email.trim());
  const isInPassValid = signInForm.password.length >= 6;

  const triggerToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(''), 3000);
  };

  const handleSignUpSubmit = (e) => {
    e.preventDefault();
    if (!signUpForm.terms) {
      triggerToast('⚠️ Mohon setujui Syarat & Ketentuan.');
      return;
    }
    triggerToast(`🎉 Pendaftaran Akun "${signUpForm.name}" Berhasil!`);
    setTimeout(() => setIsSignIn(true), 1200);
  };

  const handleSignInSubmit = (e) => {
    e.preventDefault();
    triggerToast(`🚀 Login Berhasil! Selamat datang, ${signInForm.email.split('@')[0]}...`);
  };

  return (
    <div className="min-h-screen bg-[#f1f5f9] bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-white via-[#f8fafc] to-[#e2e8f0] flex flex-col items-center justify-center p-3 md:p-6 font-['Poppins',sans-serif] select-none text-slate-800 overflow-x-hidden">
      
      {/* Toast Notification Alert */}
      {toastMessage && (
        <div className="fixed bottom-4 right-4 bg-slate-900/95 backdrop-blur-md text-white border border-slate-700 px-4 py-2 rounded-xl shadow-2xl flex items-center gap-2.5 text-xs z-50 animate-bounce">
          <span className="text-sm">🚀</span>
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Main Split-Card Container (Responsive, Pas, & Bebas Scrollbar) */}
      <div className="relative w-full max-w-[720px] h-[440px] bg-white rounded-[28px] overflow-hidden shadow-[0_25px_60px_-15px_rgba(15,23,42,0.18)] border border-slate-200/80">
        
        {/* ========================================================= */}
        {/* 1. FORM SIGN IN (TERLETAK DI SISI KIRI KARTU PUTIH)       */}
        {/* ========================================================= */}
        <div 
          className={`absolute top-0 left-0 w-1/2 h-full flex flex-col justify-center px-8 lg:px-9 py-6 transition-all duration-700 ease-[cubic-bezier(0.65,0,0.35,1)] z-10 ${
            isSignIn 
              ? 'opacity-100 translate-x-0 pointer-events-auto z-20' 
              : 'opacity-0 -translate-x-10 pointer-events-none'
          }`}
        >
          <div className="text-center mb-3">
            <h3 className="text-xl font-bold text-slate-800 tracking-tight">Welcome Back</h3>
            <p className="text-[11px] text-slate-400 mt-0.5">Masuk untuk mengakses akun Spacer Anda</p>
          </div>

          <form onSubmit={handleSignInSubmit} className="max-w-[250px] mx-auto w-full space-y-3">
            <div>
              <label className="block text-[11px] font-semibold text-slate-700 mb-0.5">E-mail Adress</label>
              <div className="relative flex items-center">
                <input
                  type="email"
                  required
                  placeholder="Enter your mail"
                  value={signInForm.email}
                  onChange={(e) => setSignInForm({ ...signInForm, email: e.target.value })}
                  className="w-full border border-slate-300 focus:border-blue-600 focus:ring-2 focus:ring-blue-100 outline-none py-1.5 px-2.5 rounded-lg text-xs text-slate-800 pr-7 transition-all bg-white placeholder:text-slate-400 shadow-sm"
                />
                <span className={`absolute right-2 text-xs font-bold transition-all ${isInEmailValid ? 'text-blue-500 opacity-100 scale-110' : 'text-slate-300 opacity-20'}`}>✓</span>
              </div>
            </div>

            <div>
              <div className="flex justify-between items-center mb-0.5">
                <label className="text-[11px] font-semibold text-slate-700">Password</label>
                <button type="button" onClick={() => triggerToast('Fitur pemulihan kata sandi')} className="text-[10.5px] text-blue-600 hover:underline">Lupa?</button>
              </div>
              <div className="relative flex items-center">
                <input
                  type="password"
                  required
                  placeholder="Enter your password"
                  value={signInForm.password}
                  onChange={(e) => setSignInForm({ ...signInForm, password: e.target.value })}
                  className="w-full border border-slate-300 focus:border-blue-600 focus:ring-2 focus:ring-blue-100 outline-none py-1.5 px-2.5 rounded-lg text-xs text-slate-800 pr-7 transition-all bg-white placeholder:text-slate-400 shadow-sm"
                />
                <span className={`absolute right-2 text-xs font-bold transition-all ${isInPassValid ? 'text-blue-500 opacity-100 scale-110' : 'text-slate-300 opacity-20'}`}>✓</span>
              </div>
            </div>

            <div className="pt-0.5">
              <label className="flex items-center gap-1.5 cursor-pointer text-[10.5px] text-slate-600 select-none">
                <input
                  type="checkbox"
                  checked={signInForm.remember}
                  onChange={(e) => setSignInForm({ ...signInForm, remember: e.target.checked })}
                  className="w-3.5 h-3.5 rounded text-blue-600 border-slate-300 focus:ring-0 cursor-pointer"
                />
                <span>Ingat saya di perangkat ini</span>
              </label>
            </div>

            <div className="pt-1.5">
              <button
                type="submit"
                className="w-full bg-gradient-to-r from-[#175cf2] to-[#1046c4] hover:from-[#1b64ff] hover:to-[#1752de] text-white text-xs font-black uppercase tracking-wider py-2.5 rounded-full shadow-lg shadow-blue-600/40 transition-all duration-200 hover:-translate-y-0.5 active:translate-y-0"
              >
                Sign In
              </button>
            </div>
          </form>

          <div className="text-center mt-3">
            <span className="text-[11px] text-slate-400">
              Belum memiliki akun?{' '}
              <button 
                type="button" 
                onClick={() => setIsSignIn(false)} 
                className="text-blue-600 font-semibold hover:underline"
              >
                Daftar sekarang
              </button>
            </span>
          </div>
        </div>

        {/* ========================================================= */}
        {/* 2. FORM SIGN UP (TERLETAK DI SISI KANAN KARTU PUTIH)      */}
        {/* ========================================================= */}
        <div 
          className={`absolute top-0 right-0 w-1/2 h-full flex flex-col justify-center px-8 lg:px-9 py-6 transition-all duration-700 ease-[cubic-bezier(0.65,0,0.35,1)] z-10 ${
            !isSignIn 
              ? 'opacity-100 translate-x-0 pointer-events-auto z-20' 
              : 'opacity-0 translate-x-10 pointer-events-none'
          }`}
        >
          <div className="text-center mb-3">
            <h3 className="text-xl font-bold text-slate-800 tracking-tight">Create your account</h3>
            <p className="text-[11px] text-slate-400 mt-0.5">Lengkapi data untuk pendaftaran akun</p>
          </div>

          <form onSubmit={handleSignUpSubmit} className="max-w-[250px] mx-auto w-full space-y-2.5">
            <div>
              <label className="block text-[11px] font-semibold text-slate-700 mb-0.5">Name</label>
              <div className="relative flex items-center">
                <input
                  type="text"
                  required
                  placeholder="Enter your name"
                  value={signUpForm.name}
                  onChange={(e) => setSignUpForm({ ...signUpForm, name: e.target.value })}
                  className="w-full border border-slate-300 focus:border-blue-600 focus:ring-2 focus:ring-blue-100 outline-none py-1.5 px-2.5 rounded-lg text-xs text-slate-800 pr-7 transition-all bg-white placeholder:text-slate-400 shadow-sm"
                />
                <span className={`absolute right-2 text-xs font-bold transition-all ${isUpNameValid ? 'text-blue-500 opacity-100 scale-110' : 'text-slate-300 opacity-20'}`}>✓</span>
              </div>
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-slate-700 mb-0.5">E-mail Adress</label>
              <div className="relative flex items-center">
                <input
                  type="email"
                  required
                  placeholder="Enter your mail"
                  value={signUpForm.email}
                  onChange={(e) => setSignUpForm({ ...signUpForm, email: e.target.value })}
                  className="w-full border border-slate-300 focus:border-blue-600 focus:ring-2 focus:ring-blue-100 outline-none py-1.5 px-2.5 rounded-lg text-xs text-slate-800 pr-7 transition-all bg-white placeholder:text-slate-400 shadow-sm"
                />
                <span className={`absolute right-2 text-xs font-bold transition-all ${isUpEmailValid ? 'text-blue-500 opacity-100 scale-110' : 'text-slate-300 opacity-20'}`}>✓</span>
              </div>
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-slate-700 mb-0.5">Password</label>
              <div className="relative flex items-center">
                <input
                  type="password"
                  required
                  placeholder="Enter your password"
                  value={signUpForm.password}
                  onChange={(e) => setSignUpForm({ ...signUpForm, password: e.target.value })}
                  className="w-full border border-slate-300 focus:border-blue-600 focus:ring-2 focus:ring-blue-100 outline-none py-1.5 px-2.5 rounded-lg text-xs text-slate-800 pr-7 transition-all bg-white placeholder:text-slate-400 shadow-sm"
                />
                <span className={`absolute right-2 text-xs font-bold transition-all ${isUpPassValid ? 'text-blue-500 opacity-100 scale-110' : 'text-slate-300 opacity-20'}`}>✓</span>
              </div>
            </div>

            <div className="pt-0.5">
              <label className="flex items-start gap-1.5 cursor-pointer text-[10px] text-slate-600 select-none">
                <input
                  type="checkbox"
                  checked={signUpForm.terms}
                  onChange={(e) => setSignUpForm({ ...signUpForm, terms: e.target.checked })}
                  className="mt-0.5 w-3 h-3 rounded text-blue-600 border-slate-300 focus:ring-0 cursor-pointer"
                />
                <span>By Signing Up, I agree with <span className="text-slate-700 font-medium underline">Terms & Conditions</span></span>
              </label>
            </div>

            <div className="pt-1">
              <button
                type="submit"
                className="w-full bg-gradient-to-r from-[#175cf2] to-[#124bce] hover:from-[#1b64ff] hover:to-[#1752de] text-white text-xs font-semibold py-2 rounded-full shadow-md shadow-blue-500/35 transition-all duration-200 hover:-translate-y-0.5 active:translate-y-0"
              >
                Sign Up
              </button>
            </div>
          </form>

          <div className="text-center mt-2.5">
            <span className="text-[11px] text-slate-400">
              Sudah memiliki akun?{' '}
              <button 
                type="button" 
                onClick={() => setIsSignIn(true)} 
                className="text-blue-600 font-semibold hover:underline"
              >
                Masuk di sini
              </button>
            </span>
          </div>
        </div>

        {/* ========================================================================================= */}
        {/* 3. SLIDING BRAND OVERLAY (PANEL BIRU DENGAN AWAN BERGERAK MENYILANG KIRI <-> KANAN)      */}
        {/* ========================================================================================= */}
        <div 
          className={`absolute top-0 left-0 w-1/2 h-full bg-gradient-to-br from-[#1056e8] via-[#1a58eb] to-[#0d42bf] text-white z-30 transition-transform duration-700 ease-[cubic-bezier(0.65,0,0.35,1)] overflow-hidden ${
            isSignIn ? 'translate-x-full' : 'translate-x-0'
          }`}
        >
          {/* Cloud Divider Sisi Kanan (Aktif saat Overlay berada di Kiri pada Mode Sign Up) */}
          <div 
            className={`absolute -right-6 top-0 bottom-0 w-12 z-30 pointer-events-none transition-opacity duration-300 ${
              !isSignIn ? 'opacity-100' : 'opacity-0'
            }`}
          >
            <svg className="w-full h-full" viewBox="0 0 100 500" preserveAspectRatio="none">
              <path d="M 100,0 L 52,0 Q 8,60 48,125 Q 0,185 42,250 Q 6,325 50,385 Q 16,445 62,500 L 100,500 Z" fill="#60a5fa" opacity="0.45" />
              <path d="M 100,0 L 68,0 Q 28,65 62,135 Q 18,205 58,275 Q 24,345 68,405 Q 34,465 78,500 L 100,500 Z" fill="#93c5fd" opacity="0.65" />
              <path d="M 100,0 L 82,0 Q 45,70 78,145 Q 35,225 72,295 Q 38,365 82,425 Q 52,485 88,500 L 100,500 Z" fill="#ffffff" />
            </svg>
          </div>

          {/* Cloud Divider Sisi Kiri (Aktif saat Overlay berada di Kanan pada Mode Sign In, scale-X mirrored) */}
          <div 
            className={`absolute -left-6 top-0 bottom-0 w-12 z-30 pointer-events-none transition-opacity duration-300 scale-x-[-1] ${
              isSignIn ? 'opacity-100' : 'opacity-0'
            }`}
          >
            <svg className="w-full h-full" viewBox="0 0 100 500" preserveAspectRatio="none">
              <path d="M 100,0 L 52,0 Q 8,60 48,125 Q 0,185 42,250 Q 6,325 50,385 Q 16,445 62,500 L 100,500 Z" fill="#60a5fa" opacity="0.45" />
              <path d="M 100,0 L 68,0 Q 28,65 62,135 Q 18,205 58,275 Q 24,345 68,405 Q 34,465 78,500 L 100,500 Z" fill="#93c5fd" opacity="0.65" />
              <path d="M 100,0 L 82,0 Q 45,70 78,145 Q 35,225 72,295 Q 38,365 82,425 Q 52,485 88,500 L 100,500 Z" fill="#ffffff" />
            </svg>
          </div>

          {/* Konten Overlay A: Mode Sign Up (Overlay di Kiri) */}
          <div 
            className={`absolute inset-5 flex flex-col justify-between items-center text-center transition-all duration-500 ${
              !isSignIn ? 'opacity-100 translate-x-0' : 'opacity-0 -translate-x-10 pointer-events-none'
            }`}
          >
            <div className="text-[11px] font-light text-blue-100 pt-1 tracking-wide">Welcome to</div>

            <div className="flex flex-col items-center my-auto">
              <div className="w-14 h-14 rounded-full bg-white flex items-center justify-center shadow-md shadow-blue-950/20 mb-2.5 transition-transform hover:scale-105 duration-300">
                <svg className="w-7 h-7 text-[#155dfc]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"/>
                  <path d="m12 15-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"/>
                  <path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0"/>
                  <path d="M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5"/>
                </svg>
              </div>
              <h2 className="text-xl font-bold tracking-tight text-white mb-1">Spacer</h2>
              <p className="text-[10.5px] leading-relaxed text-blue-100/85 font-light max-w-[190px] mb-3.5">
                Bergabunglah dengan ekosistem analisis finansial pintar Spacer.
              </p>
              <button
                type="button"
                onClick={() => setIsSignIn(true)}
                className="px-4 py-1.5 rounded-full border border-white/75 text-white text-[11px] font-semibold hover:bg-white hover:text-blue-600 transition-all duration-200 flex items-center gap-1.5 shadow-sm hover:shadow-md"
              >
                <span>Sudah Punya Akun?</span>
                <span className="font-bold">Sign In ➔</span>
              </button>
            </div>

            <div className="text-[9px] font-medium text-blue-200/90 tracking-wider pb-1">
              CREATOR HERE &nbsp;|&nbsp; DESIGNER HERE
            </div>
          </div>

          {/* Konten Overlay B: Mode Sign In (Overlay di Kanan) */}
          <div 
            className={`absolute inset-5 flex flex-col justify-between items-center text-center transition-all duration-500 ${
              isSignIn ? 'opacity-100 translate-x-0' : 'opacity-0 translate-x-10 pointer-events-none'
            }`}
          >
            <div className="text-[11px] font-light text-blue-100 pt-1 tracking-wide">Welcome Back!</div>

            <div className="flex flex-col items-center my-auto">
              <div className="w-14 h-14 rounded-full bg-white flex items-center justify-center shadow-md shadow-blue-950/20 mb-2.5 transition-transform hover:scale-105 duration-300">
                <svg className="w-7 h-7 text-[#155dfc]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"/>
                  <path d="m12 15-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"/>
                  <path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0"/>
                  <path d="M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5"/>
                </svg>
              </div>
              <h2 className="text-xl font-bold tracking-tight text-white mb-1">Halo, Pengguna!</h2>
              <p className="text-[10.5px] leading-relaxed text-blue-100/85 font-light max-w-[190px] mb-3.5">
                Masuk kembali untuk mengakses pengujian emiten, evaluasi XGBoost & Altman Z'', dan histori prediksi.
              </p>
              <button
                type="button"
                onClick={() => setIsSignIn(false)}
                className="px-4 py-1.5 rounded-full border border-white/75 text-white text-[11px] font-semibold hover:bg-white hover:text-blue-600 transition-all duration-200 flex items-center gap-1.5 shadow-sm hover:shadow-md"
              >
                <span>⬅ Belum Ada Akun?</span>
                <span className="font-bold">Sign Up</span>
              </button>
            </div>

            <div className="text-[9px] font-medium text-blue-200/90 tracking-wider pb-1">
              SECURE AUTHENTICATION SYSTEM
            </div>
          </div>

        </div>

      </div>

    </div>
  );
}
