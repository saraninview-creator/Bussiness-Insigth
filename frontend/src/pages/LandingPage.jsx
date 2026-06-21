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
      // Draw connection lines
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
      // Draw particles
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

/* ── Animated counter ─────────────────────────────────────── */
function Counter({ to, suffix = '' }) {
  const [val, setVal] = useState(0);
  useEffect(() => {
    let start = 0;
    const step = to / 60;
    const timer = setInterval(() => {
      start += step;
      if (start >= to) { setVal(to); clearInterval(timer); }
      else setVal(Math.floor(start));
    }, 16);
    return () => clearInterval(timer);
  }, [to]);
  return <>{val.toLocaleString()}{suffix}</>;
}

/* ── Feature card ─────────────────────────────────────────── */
function FeatureCard({ icon, title, desc, delay }) {
  return (
    <div className="landing-feature-card" style={{ animationDelay: delay }}>
      <div className="landing-feature-icon">{icon}</div>
      <h3>{title}</h3>
      <p>{desc}</p>
    </div>
  );
}

/* ── Step badge ───────────────────────────────────────────── */
function StepBadge({ num, title, desc }) {
  return (
    <div className="landing-step">
      <div className="landing-step-num">{num}</div>
      <div className="landing-step-body">
        <strong>{title}</strong>
        <span>{desc}</span>
      </div>
    </div>
  );
}

/* ── Main landing page ────────────────────────────────────── */
export default function LandingPage() {
  const navigate = useNavigate();
  const [scrolled, setScrolled] = useState(false);
  const heroRef = useRef(null);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 50);
    window.addEventListener('scroll', onScroll);
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  // Intersection observer for fade-in-up animations
  useEffect(() => {
    const els = document.querySelectorAll('.landing-animate');
    const obs = new IntersectionObserver(
      (entries) => entries.forEach(e => { if (e.isIntersecting) e.target.classList.add('visible'); }),
      { threshold: 0.12 }
    );
    els.forEach(el => obs.observe(el));
    return () => obs.disconnect();
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
          <div className="landing-nav-links">
            <a href="#features">Features</a>
            <a href="#how">How it works</a>
            <a href="#stats">Stats</a>
          </div>
          <button
            id="landing-cta-nav"
            className="landing-nav-cta"
            onClick={() => navigate('/app')}
          >
            Launch App →
          </button>
        </div>
      </nav>

      {/* ── Hero ── */}
      <section className="landing-hero" ref={heroRef}>
        <ParticleCanvas />

        {/* Glowing orbs */}
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
              id="landing-cta-main"
              className="landing-btn-primary"
              onClick={() => navigate('/app')}
            >
              Start Analysing Free →
            </button>
            <a href="#how" className="landing-btn-ghost">See how it works</a>
          </div>

          <div className="landing-hero-trust">
            <span>✓ No credit card required</span>
            <span>✓ Works on CSV & Excel</span>
            <span>✓ Under 3 minutes</span>
          </div>
        </div>

        <div className="landing-scroll-indicator">
          <span />
        </div>
      </section>

      {/* ── Stats bar ── */}
      <section id="stats" className="landing-stats landing-animate">
        <div className="landing-stats-inner">
          <div className="landing-stat">
            <div className="landing-stat-num"><Counter to={3} suffix="min" /></div>
            <div className="landing-stat-label">Average render time</div>
          </div>
          <div className="landing-stat-divider" />
          <div className="landing-stat">
            <div className="landing-stat-num"><Counter to={100} suffix="%" /></div>
            <div className="landing-stat-label">Local AI — no data leaves your server</div>
          </div>
          <div className="landing-stat-divider" />
          <div className="landing-stat">
            <div className="landing-stat-num"><Counter to={5} /></div>
            <div className="landing-stat-label">Pipeline stages automated</div>
          </div>
          <div className="landing-stat-divider" />
          <div className="landing-stat">
            <div className="landing-stat-num"><Counter to={0} suffix=" config" /></div>
            <div className="landing-stat-label">Zero configuration needed</div>
          </div>
        </div>
      </section>

      {/* ── Features ── */}
      <section id="features" className="landing-section landing-animate">
        <div className="landing-section-inner">
          <div className="landing-section-eyebrow">What's inside</div>
          <h2 className="landing-section-h2">Everything automated for you</h2>
          <p className="landing-section-sub">
            From raw spreadsheet to polished insight video in a single upload.
          </p>
          <div className="landing-features-grid">
            <FeatureCard delay="0s"   icon="📊" title="Smart Data Profiling"    desc="Automatically detects column types, distributions, outliers, and correlations across your entire dataset." />
            <FeatureCard delay="0.05s" icon="🔍" title="AI Findings Engine"     desc="Rule-based statistical analysis discovers insights, flags anomalies, and surfaces actionable suggestions." />
            <FeatureCard delay="0.1s"  icon="🎙️" title="Voice Narration"        desc="Edge-TTS synthesises a natural-sounding narrative from the AI script — no API key required." />
            <FeatureCard delay="0.15s" icon="🎬" title="Remotion Video Render"  desc="React + Remotion assembles animated charts, text overlays, and audio into a broadcast-quality MP4." />
            <FeatureCard delay="0.2s"  icon="💬" title="Interactive Chatbot"    desc="Ask any question about your data. The hybrid AI bot gives instant, context-aware statistical answers." />
            <FeatureCard delay="0.25s" icon="☁️" title="Cloud Sync"            desc="Optional Supabase integration stores jobs and videos in the cloud for team-wide access." />
          </div>
        </div>
      </section>

      {/* ── How it works ── */}
      <section id="how" className="landing-section landing-section-dark landing-animate">
        <div className="landing-section-inner">
          <div className="landing-section-eyebrow">The pipeline</div>
          <h2 className="landing-section-h2">From upload to video in 5 steps</h2>
          <div className="landing-steps">
            <StepBadge num="01" title="Upload your file"         desc="CSV or Excel — drag and drop or browse." />
            <StepBadge num="02" title="Profiling & Findings"     desc="Statistical engine profiles columns and discovers insights automatically." />
            <StepBadge num="03" title="Script generation"        desc="AI writes a concise narration script tuned to your chosen style." />
            <StepBadge num="04" title="Voice & audio synthesis"  desc="Edge-TTS creates the narration audio. Segments are timed frame-perfectly." />
            <StepBadge num="05" title="Video rendering"          desc="Remotion renders animated charts + audio into a polished MP4 you can download." />
          </div>
        </div>
      </section>

      {/* ── CTA ── */}
      <section className="landing-cta-section landing-animate">
        <div className="landing-cta-inner">
          <img src={logo} alt="logo" className="landing-cta-logo" />
          <h2>Ready to narrate your data?</h2>
          <p>No sign-up. No configuration. Just upload and watch the magic happen.</p>
          <button
            id="landing-cta-bottom"
            className="landing-btn-primary"
            onClick={() => navigate('/app')}
          >
            Launch DataNarrate →
          </button>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="landing-footer">
        <div className="landing-footer-inner">
          <div className="landing-footer-logo">
            <img src={logo} alt="logo" className="landing-logo-img" />
            <span>DataNarrate</span>
          </div>
          <p>Built with FastAPI · React · Remotion · Edge-TTS · Supabase</p>
        </div>
      </footer>
    </div>
  );
}
