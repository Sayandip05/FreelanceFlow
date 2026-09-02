import React from 'react';

export interface SliderItem {
  src: string;
  title: string;
  tag?: string;
}

export interface ImageAutoSliderProps {
  items?: SliderItem[];
}

export const Component: React.FC<ImageAutoSliderProps> = ({ items }) => {
  const defaultItems: SliderItem[] = [
    {
      src: "/images/for hiring 1.png",
      title: "Post your project for free",
      tag: "Step 1 • For Clients",
    },
    {
      src: "/images/for hiring 2.png",
      title: "Review proposals from skilled freelancers",
      tag: "Step 2 • Matching",
    },
    {
      src: "/images/for hiring 3.png",
      title: "Pay securely only when work is approved",
      tag: "Step 3 • Escrow Protection",
    },
    {
      src: "/images/for getting project 1.png",
      title: "Create your profile & showcase skills",
      tag: "Step 1 • For Freelancers",
    },
    {
      src: "/images/for getting project  2.png",
      title: "Browse projects & submit proposals",
      tag: "Step 2 • Proposals",
    },
    {
      src: "/images/for getting project 3.png",
      title: "Get paid reliably as milestones complete",
      tag: "Step 3 • Verified Payouts",
    },
  ];

  const displayItems = items || defaultItems;
  const duplicatedItems = [...displayItems, ...displayItems];

  return (
    <div className="w-full relative overflow-hidden py-2 select-none">
      <style>{`
        @keyframes auto-scroll-hardware {
          0% {
            transform: translate3d(0, 0, 0);
          }
          100% {
            transform: translate3d(-50%, 0, 0);
          }
        }

        .infinite-auto-scroll {
          display: flex;
          width: max-content;
          animation: auto-scroll-hardware 35s linear infinite;
          transform: translate3d(0, 0, 0);
          backface-visibility: hidden;
          perspective: 1000px;
          will-change: transform;
        }

        .infinite-auto-scroll:hover {
          animation-play-state: paused;
        }

        .slider-image-card {
          transform: translateZ(0);
          backface-visibility: hidden;
          contain: layout style paint;
          transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.3s ease;
        }

        .slider-image-card:hover {
          transform: translateY(-4px);
        }
      `}</style>
      
      <div className="relative w-full overflow-hidden">
        <div className="infinite-auto-scroll gap-4 sm:gap-7 py-3 px-2 sm:px-4">
          {duplicatedItems.map((item, index) => (
            <a
              key={index}
              href="/login"
              className="slider-image-card relative flex-shrink-0 w-[290px] sm:w-[380px] md:w-[440px] lg:w-[480px] aspect-[4/3] rounded-2xl overflow-hidden shadow-sm hover:shadow-2xl transition-all duration-300 group block border border-gray-200/80 bg-gray-100"
            >
              {/* Full-Cover Background Image (Taller Aspect Ratio) */}
              <img
                src={item.src}
                alt={item.title}
                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700 ease-out"
                loading={index < 4 ? "eager" : "lazy"}
                decoding="async"
              />

              {/* Top Tag - Frosted Glass Pill */}
              {item.tag && (
                <div className="absolute top-2.5 left-2.5 sm:top-3.5 sm:left-3.5 z-10 bg-black/50 backdrop-blur-md text-white px-2.5 py-0.5 sm:px-3 sm:py-1 rounded-md text-[10px] sm:text-xs font-semibold border border-white/20 shadow-sm">
                  {item.tag}
                </div>
              )}

              {/* Bottom Title - Slim & Low-Blur Glass Bar */}
              <div className="absolute bottom-2.5 left-2.5 right-2.5 sm:bottom-3 sm:left-3 sm:right-3 z-10 bg-white/85 hover:bg-white/92 backdrop-blur-[3px] border border-white/80 rounded-lg py-2 px-3 sm:py-2.5 sm:px-3.5 shadow-sm transition-colors">
                <h3 className="text-xs sm:text-sm font-bold text-gray-950 line-clamp-1 sm:line-clamp-2 leading-snug tracking-tight">
                  {item.title}
                </h3>
              </div>
            </a>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Component;
