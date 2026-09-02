import { useState } from 'react';
import {
  Search,
  Check,
  ArrowRight,
  Code,
  PenTool,
  Megaphone,
  FileText,
  Headphones,
  Calculator,
  Scale,
  Users,
  Wrench,
  Cpu,
  Menu,
  X
} from 'lucide-react';
import SocialProofRating from '../components/ui/demo';
import ImageAutoSlider from '../components/ui/image-auto-slider';

const LandingPage = () => {
  const [activeHeroTab, setActiveHeroTab] = useState('hire');
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  return (
    <div className="min-h-screen bg-white font-sans text-gray-900 selection:bg-blue-200 selection:text-blue-900">
      {/* Navbar */}
      <nav className="sticky top-0 z-50 bg-white border-b border-gray-200 px-3 sm:px-6 py-2.5 sm:py-3 flex items-center justify-between">
        <div className="flex items-center gap-4 sm:gap-6 min-w-0">
          <a href="#" className="inline-flex items-center gap-2 shrink-0">
            <img src="/logo.png" alt="FreelanceFlow" className="w-7 h-7 sm:w-8 sm:h-8 object-contain" />
            <span className="text-xl sm:text-2xl font-black tracking-tight text-gray-900">
              Freelance<span className="text-blue-600">Flow</span>
            </span>
          </a>
          <div className="hidden lg:flex items-center gap-5 text-sm font-medium text-gray-700">
            <a href="/login?role=CLIENT" className="hover:text-blue-600 transition-colors">Hire freelancers</a>
            <a href="/login?role=FREELANCER" className="hover:text-blue-600 transition-colors">Find work</a>
            <a href="#how-it-works" className="hover:text-blue-600 transition-colors">How it works</a>
            <a href="#pricing" className="hover:text-blue-600 transition-colors">Pricing</a>
          </div>
        </div>
        <div className="flex items-center gap-2 sm:gap-4 shrink-0">
          <a href="/login" className="text-sm font-medium text-gray-700 hover:text-blue-600 hidden sm:block transition-colors">Log in</a>
          <a href="/register" className="bg-blue-600 hover:bg-blue-700 text-white text-xs sm:text-sm font-semibold px-3.5 sm:px-5 py-1.5 sm:py-2 rounded-full transition-colors whitespace-nowrap shadow-xs">Get started</a>
          <button className="lg:hidden text-gray-700 p-1 hover:bg-gray-100 rounded-lg transition-colors" onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}>
            {isMobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </nav>

      {/* Mobile Menu */}
      {isMobileMenuOpen && (
        <div className="lg:hidden fixed inset-0 top-[56px] sm:top-[60px] z-40 bg-white border-t border-gray-200 overflow-y-auto">
          <div className="flex flex-col p-6 gap-4 text-base font-medium text-gray-800">
            <a href="/login?role=CLIENT" className="hover:text-blue-600 transition-colors py-2 border-b border-gray-100">Hire freelancers</a>
            <a href="/login?role=FREELANCER" className="hover:text-blue-600 transition-colors py-2 border-b border-gray-100">Find work</a>
            <a href="#how-it-works" onClick={() => setIsMobileMenuOpen(false)} className="hover:text-blue-600 transition-colors py-2 border-b border-gray-100">How it works</a>
            <a href="#pricing" onClick={() => setIsMobileMenuOpen(false)} className="hover:text-blue-600 transition-colors py-2 border-b border-gray-100">Pricing</a>
            <a href="/login" className="hover:text-blue-600 transition-colors py-2 border-b border-gray-100 sm:hidden">Log in</a>
            <a href="/register" className="bg-blue-600 hover:bg-blue-700 text-white text-center py-2.5 px-4 rounded-full font-bold transition-colors mt-2">Get started</a>
          </div>
        </div>
      )}

      {/* Top Banner */}
      <div className="bg-blue-50 text-blue-900 text-center py-2.5 px-4 text-xs sm:text-sm font-medium border-b border-blue-100">
        Stop doing everything. Hire the top 1% of talent on Business Plus. <a href="/register" className="underline hover:text-blue-700 ml-1 inline-flex items-center gap-1 font-semibold">Get started <ArrowRight className="w-3 h-3" /></a>
      </div>

      {/* Hero Section - Full-bleed edge-to-edge with sharp edges */}
      <section className="relative w-full overflow-hidden bg-gray-900 min-h-[540px] sm:min-h-[620px] lg:min-h-[690px] flex flex-col justify-center shadow-lg">
        {/* Background Video */}
        <div className="absolute inset-0">
          <video
            autoPlay
            loop
            muted
            playsInline
            onEnded={(e) => e.target.play()}
            className="w-full h-full object-cover"
          >
            <source src="/images/home%20video.mp4" type="video/mp4" />
          </video>
          <div className="absolute inset-0 bg-gradient-to-r from-gray-900/95 via-gray-900/80 sm:via-gray-900/70 to-gray-900/40"></div>
        </div>
        
        <div className="relative z-10 max-w-[1440px] mx-auto w-full px-6 sm:px-12 md:px-16 lg:px-20 pt-12 sm:pt-16 lg:pt-24 pb-14 sm:pb-18 lg:pb-28">
          <div className="max-w-3xl">
            <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl xl:text-7xl font-extrabold text-white leading-[1.12] sm:leading-[1.08] mb-4 sm:mb-6 tracking-tight">
              {activeHeroTab === 'hire' 
                ? 'Hire the experts your business needs' 
                : 'Find work that fits your skills'}
            </h1>
            <p className="text-sm sm:text-base md:text-lg lg:text-xl text-gray-200 mb-6 sm:mb-8 font-normal sm:font-medium max-w-2xl leading-relaxed">
              {activeHeroTab === 'hire'
                ? 'Access skilled freelancers ready to help you build and scale without the full-time commitment'
                : 'Join thousands of freelancers earning on their own terms, no office, no fixed hours, just real work'}
            </p>
            
            {/* Toggle */}
            <div className="flex bg-white/10 p-1 rounded-full w-fit mb-6 sm:mb-8 backdrop-blur-md border border-white/20">
              <button 
                onClick={() => {
                  setActiveHeroTab('hire');
                  setActiveHowItWorksTab('hiring');
                }}
                className={`px-4 sm:px-6 py-1.5 sm:py-2.5 rounded-full font-semibold text-xs sm:text-sm transition-all ${activeHeroTab === 'hire' ? 'bg-white text-gray-900 shadow-sm' : 'text-white hover:bg-white/10'}`}
              >
                I want to hire
              </button>
              <button 
                onClick={() => {
                  setActiveHeroTab('work');
                  setActiveHowItWorksTab('work');
                }}
                className={`px-4 sm:px-6 py-1.5 sm:py-2.5 rounded-full font-semibold text-xs sm:text-sm transition-all ${activeHeroTab === 'work' ? 'bg-white text-gray-900 shadow-sm' : 'text-white hover:bg-white/10'}`}
              >
                I want to work
              </button>
            </div>
            
            {/* CTA Buttons */}
            <div className="flex flex-row gap-3 sm:gap-4 mb-6 sm:mb-8 max-w-md sm:max-w-xl">
              <a href="/register" className="flex-1 sm:flex-initial bg-blue-600 hover:bg-blue-700 text-white px-5 sm:px-9 py-3 sm:py-4 rounded-full font-bold text-center transition-colors shadow-lg text-xs sm:text-sm md:text-base whitespace-nowrap">
                Get Started - It's Free
              </a>
              <a href="/login" className="flex-1 sm:flex-initial bg-white hover:bg-gray-50 text-gray-900 px-5 sm:px-9 py-3 sm:py-4 rounded-full font-bold text-center transition-colors shadow-lg border-2 border-white text-xs sm:text-sm md:text-base whitespace-nowrap">
                Sign In
              </a>
            </div>
            
            {/* Pills */}
            <div className="flex flex-wrap gap-2.5 sm:gap-3">
              {['Web design', 'AI development', 'Video editing', 'Google Ads'].map(pill => (
                <a key={pill} href="#" className="px-4 sm:px-5 py-1.5 sm:py-2 rounded-full border border-white/30 text-white text-xs sm:text-sm hover:bg-white/20 hover:border-white/50 transition-all backdrop-blur-sm font-medium">
                  {pill}
                </a>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Social Proof & Ratings */}
      <section className="py-8 bg-gray-50/60 border-b border-gray-100 flex items-center justify-center px-4">
        <SocialProofRating />
      </section>

      {/* Find freelancers for every type of work */}
      <section className="px-4 lg:px-8 py-20 max-w-[1440px] mx-auto">
        <h2 className="text-3xl lg:text-4xl font-bold text-gray-900 mb-10 tracking-tight text-center">Find freelancers for every type of work</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-5">
          {[
            { icon: Cpu, label: 'AI Services' },
            { icon: Code, label: 'Development & IT' },
            { icon: PenTool, label: 'Design & Creative' },
            { icon: Megaphone, label: 'Sales & Marketing' },
            { icon: FileText, label: 'Writing & Translation' },
            { icon: Headphones, label: 'Admin & Support' },
            { icon: Calculator, label: 'Finance & Accounting' },
            { icon: Scale, label: 'Legal' },
            { icon: Users, label: 'HR & Training' },
            { icon: Wrench, label: 'Engineering & Architecture' },
          ].map((item, i) => (
            <a key={i} href="#" className="group flex flex-col p-6 rounded-2xl border border-gray-200 hover:shadow-lg hover:border-blue-300 transition-all duration-300 bg-white hover:-translate-y-1">
              <item.icon className="w-8 h-8 text-blue-600 mb-5 group-hover:scale-110 transition-transform duration-300" strokeWidth={1.5} />
              <span className="font-medium text-gray-900">{item.label}</span>
            </a>
          ))}
        </div>
      </section>

      {/* How it works */}
      <section id="how-it-works" className="py-20 overflow-hidden bg-gray-50/50 border-y border-gray-100">
        <div className="px-4 lg:px-8 max-w-[1440px] mx-auto mb-8 text-center">
          <h2 className="text-3xl lg:text-4xl font-extrabold text-gray-900 tracking-tight">How it works</h2>
        </div>
        
        {/* Auto Slider with all 6 Images */}
        <ImageAutoSlider />
      </section>

      {/* Pricing (Choose how you want to hire) */}
      <section id="pricing" className="px-4 lg:px-8 py-24 bg-gradient-to-b from-blue-50/50 to-white relative overflow-hidden">
        <div className="absolute top-0 left-0 w-full h-full bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAiIGhlaWdodD0iMjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGNpcmNsZSBjeD0iMiIgY3k9IjIiIHI9IjIiIGZpbGw9IiNlNWU3ZWIiLz48L3N2Zz4=')] opacity-40"></div>
        
        <div className="relative z-10 max-w-5xl mx-auto">
          <div className="text-center mb-14">
            <h2 className="text-3xl lg:text-4xl font-bold text-gray-900 mb-4 tracking-tight">Choose how you want to hire</h2>
            <p className="text-gray-600 font-medium text-lg">Flexible options designed to fit your hiring needs</p>
          </div>
          
          <div className="grid md:grid-cols-2 gap-6 lg:gap-8">
            {/* Basic Plan */}
            <div className="bg-white rounded-3xl p-8 lg:p-10 border border-gray-200 shadow-sm hover:shadow-md transition-shadow flex flex-col">
              <h3 className="text-3xl font-bold text-gray-900 mb-2">Basic</h3>
              <p className="text-sm text-gray-500 mb-6 font-medium">For occasional hiring and one-off projects</p>
              <p className="text-gray-700 mb-8 font-medium leading-relaxed">Hire skilled freelancers fast without long-term commitments or extra overhead.</p>
              
              <div className="h-px bg-gray-200 w-full mb-8"></div>
              
              <p className="font-bold text-gray-900 mb-6">Basic includes:</p>
              <ul className="space-y-5 mb-10 flex-1">
                {[
                  'Marketplace access - skilled freelancers across thousands of skills',
                  'Talent profiles - portfolios, ratings, and work history',
                  'Hiring tools - proposals and terms in one place',
                  'Project workspace - messages, files, and status in one view',
                  'Protected payments - escrow-backed pay tied to approved work'
                ].map((feature, i) => (
                  <li key={i} className="flex items-start gap-3 text-sm text-gray-700 font-medium">
                    <Check className="w-5 h-5 text-blue-600 shrink-0 mt-0.5" strokeWidth={2.5} />
                    <span className="leading-relaxed">{feature}</span>
                  </li>
                ))}
              </ul>
              
              <a href="/register" className="block w-full py-3.5 rounded-full border-2 border-blue-600 text-blue-600 font-bold hover:bg-blue-50 transition-colors text-center">Get started for free</a>
            </div>
            
            {/* Business Plus Plan */}
            <div className="bg-white rounded-3xl p-8 lg:p-10 border-2 border-blue-300 shadow-xl flex flex-col relative transform md:-translate-y-2">
              <div className="absolute top-0 right-0 bg-blue-100 text-blue-800 text-xs font-bold px-4 py-1.5 rounded-bl-xl rounded-tr-2xl uppercase tracking-widest">Popular</div>
              <h3 className="text-3xl font-bold text-gray-900 mb-2">Business Plus</h3>
              <p className="text-sm text-gray-500 mb-6 font-medium">For ongoing work, repeat hiring, and teams</p>
              <p className="text-gray-700 mb-8 font-medium leading-relaxed">Premium tools, vetted talent, and team controls for running freelance work at scale.</p>
              
              <div className="h-px bg-gray-200 w-full mb-8"></div>
              
              <p className="font-bold text-gray-900 mb-6">Everything in Basic, plus:</p>
              <ul className="space-y-5 mb-10 flex-1">
                {[
                  'Curated shortlists - we surface top matches so you can hire faster',
                  'Expert-Vetted talent - access to the top 1% of FreelanceFlow freelancers',
                  'Team workspace - shared hiring with roles and permissions',
                  'Centralized billing - keep team spend in one place',
                  'Priority support - faster help to keep projects moving'
                ].map((feature, i) => (
                  <li key={i} className="flex items-start gap-3 text-sm text-gray-700 font-medium">
                    <Check className="w-5 h-5 text-blue-600 shrink-0 mt-0.5" strokeWidth={2.5} />
                    <span className="leading-relaxed">{feature}</span>
                  </li>
                ))}
              </ul>
              
              <a href="/register" className="block w-full py-3.5 rounded-full bg-blue-600 text-white font-bold hover:bg-blue-700 transition-colors shadow-md hover:shadow-lg text-center">Get started for free</a>
            </div>
          </div>
          
          <div className="text-center mt-10">
            <a href="#" className="text-blue-600 font-medium hover:underline inline-flex items-center gap-1">Compare features across plans <ArrowRight className="w-4 h-4" /></a>
          </div>
        </div>
      </section>

      {/* Insights (Get insights into freelancer pricing) */}
      <section className="px-4 lg:px-8 py-20 max-w-[1440px] mx-auto">
        <div className="bg-[#111827] rounded-[2.5rem] overflow-hidden flex flex-col lg:flex-row shadow-2xl">
          {/* Left Content */}
          <div className="p-10 lg:p-20 flex-1 flex flex-col justify-center relative z-10">
            <h2 className="text-4xl lg:text-5xl font-bold text-white mb-6 tracking-tight leading-[1.1]">
              Get insights into<br />freelancer pricing
            </h2>
            <p className="text-gray-300 font-medium mb-10 text-lg max-w-md">
              We'll calculate the average cost for freelancers with the skills you need.
            </p>
            
            <div className="flex items-center bg-white rounded-full p-1.5 max-w-md shadow-lg">
              <input type="text" placeholder="To start, describe what you need done." className="flex-1 px-5 py-3 bg-transparent text-gray-900 placeholder-gray-500 focus:outline-none text-sm font-medium" />
              <button className="bg-gray-900 hover:bg-gray-800 text-white px-6 py-3 rounded-full font-medium flex items-center gap-2 transition-colors text-sm">
                Next <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
          
          {/* Right Chart Visualization */}
          <div className="flex-1 relative min-h-[400px] lg:min-h-[500px] flex items-center justify-center p-8 bg-gradient-to-br from-gray-900 to-gray-800 overflow-hidden">
            {/* Abstract glow */}
            <div className="absolute inset-0 bg-blue-500/20 blur-[120px] rounded-full transform translate-x-1/4 translate-y-1/4"></div>
            
            {/* Chart Card */}
            <div className="relative z-10 bg-gray-900/60 backdrop-blur-xl border border-gray-700/50 rounded-3xl p-8 w-full max-w-md shadow-2xl">
              <h3 className="text-white text-center font-medium mb-10 text-lg">Cost estimate</h3>
              
              {/* Simple CSS Chart representation */}
              <div className="relative h-40 flex items-end justify-between px-4">
                {/* Curve line */}
                <svg className="absolute inset-0 w-full h-full" preserveAspectRatio="none" viewBox="0 0 100 100">
                  <path d="M0,100 C20,100 30,20 50,20 C70,20 80,100 100,100" fill="none" stroke="rgba(255,255,255,0.15)" strokeWidth="1" strokeDasharray="4 4" />
                  <path d="M30,50 C40,20 60,20 70,50" fill="none" stroke="#3b82f6" strokeWidth="3" strokeLinecap="round" />
                </svg>
                
                {/* Highlight area */}
                <div className="absolute left-[30%] right-[30%] bottom-0 top-[20%] bg-gradient-to-t from-blue-500/0 to-blue-500/20 rounded-t-xl border-t border-blue-500/30"></div>
                
                {/* Labels */}
                <div className="text-xs font-medium text-gray-500 z-10 pb-2">Affordable</div>
                <div className="text-sm text-white font-bold z-10 flex flex-col items-center justify-end h-full pb-10">
                  Typical
                </div>
                <div className="text-xs font-medium text-gray-500 z-10 pb-2">Experts</div>
                
                {/* Price tags */}
                <div className="absolute left-[22%] top-[25%] bg-gray-900 border border-blue-500 text-white text-xs font-bold px-3 py-1.5 rounded-full z-20 shadow-lg">$30/hr</div>
                <div className="absolute right-[22%] top-[25%] bg-gray-900 border border-blue-500 text-white text-xs font-bold px-3 py-1.5 rounded-full z-20 shadow-lg">$50/hr</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Bottom CTA */}
      {/* Bottom CTA Banner - Full-bleed edge-to-edge */}
      <section className="w-full relative overflow-hidden bg-gradient-to-r from-blue-500 via-blue-600 to-blue-700 py-16 sm:py-20 lg:py-24 text-center">
        {/* Decorative elements */}
        <div className="absolute top-0 left-0 w-full h-full bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAiIGhlaWdodD0iMjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGNpcmNsZSBjeD0iMiIgY3k9IjIiIHI9IjIiIGZpbGw9InJnYmEoMjU1LDI1NSwyNTUsMC4xKSIvPjwvc3ZnPg==')] opacity-30 mix-blend-overlay"></div>
        <div className="absolute -top-24 -right-24 w-96 h-96 bg-blue-400 rounded-full mix-blend-multiply filter blur-3xl opacity-50 animate-blob"></div>
        <div className="absolute -bottom-24 -left-24 w-96 h-96 bg-blue-800 rounded-full mix-blend-multiply filter blur-3xl opacity-50 animate-blob animation-delay-2000"></div>
        
        <div className="relative z-10 max-w-[1440px] mx-auto px-6 sm:px-12 lg:px-20">
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold text-white mb-8 sm:mb-10 tracking-tight max-w-3xl mx-auto leading-tight">
            Find freelancers who can help you build what's next
          </h2>
          <a href="/register" className="inline-block bg-white text-blue-600 hover:bg-gray-50 px-10 py-4 rounded-full font-bold text-base sm:text-lg transition-all transform hover:scale-105 shadow-xl hover:shadow-2xl">
            Explore freelancers
          </a>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-black text-gray-400 py-8 px-4 lg:px-8 border-t border-gray-900">
        <div className="max-w-[1440px] mx-auto flex flex-col sm:flex-row justify-between items-center gap-4 text-xs font-medium">
          <div className="flex items-center gap-2.5">
            <img src="/logo.png" alt="FreelanceFlow" className="w-6 h-6 object-contain" />
            <span className="text-sm font-bold tracking-tight text-white">FreelanceFlow</span>
            <span className="text-gray-700">|</span>
            <span className="text-gray-500">© 2026 FreelanceFlow Inc. All rights reserved.</span>
          </div>
          <div className="flex items-center gap-6 text-gray-400">
            <a href="#" className="hover:text-white transition-colors">Privacy Policy</a>
            <a href="#" className="hover:text-white transition-colors">Terms of Service</a>
            <a href="#" className="hover:text-white transition-colors">Security</a>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
