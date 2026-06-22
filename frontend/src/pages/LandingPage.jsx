import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import logo from '../assets/logo.png';

/* ── Particle canvas background ──────────────────────────── */
function ParticleCanvas() {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    let animId;
    let W, H, particles;

    function resize() {
      W = canvas.width = canvas.offsetWidth;
      H = canvas.height = canvas.offsetHeight;
      particles = Array.from({ length: 80 }, () => ({
        x: Math.random() * W,
        y: Math.random() * H,
        r: Math.random() * 1.5 + 0.3,
        vx: (Math.random() - 0.5) * 0.35,
        vy: (Math.random() - 0.5) * 0.35,
        alpha: Math.random() * 0.5 + 0.15,
      }));
    }
    resize();
    window.addEventListener('resize', resize);

    function draw() {
      ctx.clearRect(0, 0, W, H);
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x;
          const dy = particles[i].y - particles[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 130) {
            ctx.beginPath();
            ctx.strokeStyle = `rgba(255,255,255,${0.04 * (1 - dist / 130)})`;
            ctx.lineWidth = 0.5;
            ctx.moveTo(particles[i].x, particles[i].y);
            ctx.lineTo(particles[j].x, particles[j].y);
            ctx.stroke();
          }
        }
      }
      for (const p of particles) {
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(255,255,255,${p.alpha})`;
        ctx.fill();
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < 0) p.x = W;
        if (p.x > W) p.x = 0;
        if (p.y < 0) p.y = H;
        if (p.y > H) p.y = 0;
      }
      animId = requestAnimationFrame(draw);
    }
    draw();
    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener('resize', resize);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'absolute', inset: 0, width: '100%', height: '100%',
        display: 'block', pointerEvents: 'none',
      }}
    />
  );
}

/* ── Main landing page (Minimal) ────────────────────────── */
export default function LandingPage() {
  const navigate = useNavigate();
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 50);
    window.addEventListener('scroll', onScroll);
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <div className="landing-root">
      {/* ── Navbar ── */}
      <nav className={`landing-nav${scrolled ? ' scrolled' : ''}`}>
        <div className="landing-nav-inner">
          <div className="landing-nav-logo">
            <img src={logo} alt="Biznes logo" className="landing-logo-img" />
            <span className="landing-nav-brand">DataNarrate</span>
          </div>
          <button
            className="landing-nav-cta"
            onClick={() => navigate('/app')}
          >
            Launch App →
          </button>
        </div>
      </nav>

      {/* ── Hero ── */}
      <section className="landing-hero">
        <ParticleCanvas />

        <div className="landing-orb landing-orb-1" />
        <div className="landing-orb landing-orb-2" />

        <div className="landing-hero-content">
          <div className="landing-hero-badge">✦ AI-Powered Data Storytelling</div>

          <img src={logo} alt="Biznes / DataNarrate" className="landing-hero-logo" />

          <h1 className="landing-hero-h1">
            Turn Your Data<br />
            <span className="landing-gradient-text">Into a Narrated Video</span>
          </h1>

          <p className="landing-hero-sub">
            Upload any CSV or Excel file. Our AI profiles your data, discovers
            key insights, writes a script, generates voice narration, and
            renders a broadcast-quality video — automatically.
          </p>

          <div className="landing-hero-actions">
            <button
              className="landing-btn-primary"
              onClick={() => navigate('/app')}
            >
              Start Analysing Free →
            </button>
          </div>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="landing-footer">
        <div className="landing-footer-inner">
          <div className="landing-footer-logo">
            <img src={logo} alt="logo" className="landing-logo-img" />
            <span>DataNarrate</span>
          </div>
          <p>Built with FastAPI · React · Remotion · Edge-TTS</p>
        </div>
      </footer>
    </div>
  );
}
